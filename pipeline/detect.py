from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.schemas import EventType
from pipeline.emit import JsonlEmitter, build_event
from pipeline.staff import classify_staff
from pipeline.tracker import CentroidTracker, Detection
from pipeline.zones import ZoneMapper


@dataclass
class TrackState:
    visitor_id: str
    last_zone_id: str | None = None
    zone_entered_at: datetime | None = None
    last_dwell_emit_at: datetime | None = None
    last_y_norm: float | None = None
    has_entered: bool = False
    session_seq: int = 0
    is_staff: bool = False


@dataclass
class VideoProcessor:
    video_path: Path
    output_path: Path
    layout_path: Path
    store_id: str
    camera_id: str
    model_path: Path
    clip_start: datetime
    frame_stride: int = 5
    confidence_threshold: float = 0.25
    states: dict[int, TrackState] = field(default_factory=dict)

    def run(self) -> int:
        try:
            import cv2
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "Detection requires requirements-pipeline.txt. Install it with "
                "`pip install -r requirements-pipeline.txt` or run pipeline sample mode."
            ) from exc

        model_source = str(self.model_path) if self.model_path.exists() else "yolov8n.pt"
        model = YOLO(model_source)
        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {self.video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 15
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1080
        tracker = CentroidTracker()
        zones = ZoneMapper(self.layout_path, self.store_id)
        emitted = 0

        with JsonlEmitter(self.output_path) as emitter:
            frame_index = -1
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                frame_index += 1
                if frame_index % self.frame_stride != 0:
                    continue

                timestamp = self.clip_start + timedelta(seconds=frame_index / fps)
                detections = self._detect_people(model, frame)
                queue_depth = 0
                tracks = tracker.update(detections)

                for track in tracks:
                    x, y = track.detection.bottom_center
                    x_norm = x / width
                    y_norm = y / height
                    zone = zones.zone_for_point(self.camera_id, x_norm, y_norm)
                    if zone and "BILL" in zone.zone_id.upper():
                        queue_depth += 1

                for track in tracks:
                    for event in self._events_for_track(
                        frame=frame,
                        track_id=track.track_id,
                        detection=track.detection,
                        timestamp=timestamp,
                        width=width,
                        height=height,
                        zones=zones,
                        queue_depth=queue_depth,
                    ):
                        emitter.emit(event)
                        emitted += 1

        cap.release()
        return emitted

    def _detect_people(self, model: Any, frame: Any) -> list[Detection]:
        results = model(frame, classes=[0], conf=self.confidence_threshold, verbose=False)
        detections: list[Detection] = []
        for result in results:
            for box in result.boxes:
                conf = float(box.conf[0])
                x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
                detections.append(Detection(bbox=(x1, y1, x2, y2), confidence=conf))
        return detections

    def _events_for_track(
        self,
        *,
        frame: Any,
        track_id: int,
        detection: Detection,
        timestamp: datetime,
        width: float,
        height: float,
        zones: ZoneMapper,
        queue_depth: int,
    ) -> list[dict[str, Any]]:
        state = self.states.setdefault(
            track_id,
            TrackState(visitor_id=f"VIS_{self.camera_id}_{track_id:05d}"),
        )
        is_staff, staff_conf = classify_staff(frame, detection.bbox)
        state.is_staff = is_staff
        x, y = detection.bottom_center
        x_norm = x / width
        y_norm = y / height
        zone = zones.zone_for_point(self.camera_id, x_norm, y_norm)
        zone_id = zone.zone_id if zone else None
        events: list[dict[str, Any]] = []
        confidence = min(detection.confidence, staff_conf if is_staff else detection.confidence)

        entry_line = zones.entry_line(self.camera_id)
        if entry_line and state.last_y_norm is not None and not state.has_entered:
            line = float(entry_line.get("position", 0.5))
            inbound_down = entry_line.get("inbound_direction", "down") == "down"
            crossed_down = state.last_y_norm < line <= y_norm
            crossed_up = state.last_y_norm > line >= y_norm
            if (inbound_down and crossed_down) or (not inbound_down and crossed_up):
                state.has_entered = True
                events.append(self._event(state, EventType.ENTRY, timestamp, None, 0, confidence))
            elif (inbound_down and crossed_up) or (not inbound_down and crossed_down):
                events.append(self._event(state, EventType.EXIT, timestamp, None, 0, confidence))

        if zone_id != state.last_zone_id:
            if state.last_zone_id is not None:
                dwell_ms = self._dwell_ms(state, timestamp)
                events.append(
                    self._event(
                        state,
                        EventType.ZONE_EXIT,
                        timestamp,
                        state.last_zone_id,
                        dwell_ms,
                        confidence,
                    )
                )
            if zone_id is not None:
                event_type = (
                    EventType.BILLING_QUEUE_JOIN
                    if "BILL" in zone_id.upper() and queue_depth > 0
                    else EventType.ZONE_ENTER
                )
                state.zone_entered_at = timestamp
                state.last_dwell_emit_at = timestamp
                events.append(
                    self._event(
                        state,
                        event_type,
                        timestamp,
                        zone_id,
                        0,
                        confidence,
                        queue_depth=queue_depth if event_type == EventType.BILLING_QUEUE_JOIN else None,
                        sku_zone=zone.sku_zone if zone else None,
                    )
                )
            state.last_zone_id = zone_id

        if zone_id is not None and state.zone_entered_at and state.last_dwell_emit_at:
            if (timestamp - state.last_dwell_emit_at).total_seconds() >= 30:
                dwell_ms = self._dwell_ms(state, timestamp)
                state.last_dwell_emit_at = timestamp
                events.append(
                    self._event(
                        state,
                        EventType.ZONE_DWELL,
                        timestamp,
                        zone_id,
                        dwell_ms,
                        confidence,
                        sku_zone=zone.sku_zone if zone else None,
                    )
                )

        state.last_y_norm = y_norm
        return events

    def _event(
        self,
        state: TrackState,
        event_type: EventType,
        timestamp: datetime,
        zone_id: str | None,
        dwell_ms: int,
        confidence: float,
        queue_depth: int | None = None,
        sku_zone: str | None = None,
    ) -> dict[str, Any]:
        state.session_seq += 1
        return build_event(
            store_id=self.store_id,
            camera_id=self.camera_id,
            visitor_id=state.visitor_id,
            event_type=event_type,
            timestamp=timestamp,
            zone_id=zone_id,
            dwell_ms=dwell_ms,
            is_staff=state.is_staff,
            confidence=confidence,
            metadata={
                "queue_depth": queue_depth,
                "sku_zone": sku_zone,
                "session_seq": state.session_seq,
            },
        )

    @staticmethod
    def _dwell_ms(state: TrackState, timestamp: datetime) -> int:
        if not state.zone_entered_at:
            return 0
        return int((timestamp - state.zone_entered_at).total_seconds() * 1000)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run YOLO-based CCTV event detection.")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("generated_events.jsonl"))
    parser.add_argument("--layout", type=Path, default=Path("config/store_layout.json"))
    parser.add_argument("--store-id", default="ST1008")
    parser.add_argument("--camera-id", default="CAM_1")
    parser.add_argument("--model", type=Path, default=Path("models/best.pt"))
    parser.add_argument("--clip-start", default="2026-04-10T11:30:00Z")
    parser.add_argument("--frame-stride", type=int, default=5)
    args = parser.parse_args()

    clip_start = datetime.fromisoformat(args.clip_start.replace("Z", "+00:00")).astimezone(UTC)
    count = VideoProcessor(
        video_path=args.video,
        output_path=args.output,
        layout_path=args.layout,
        store_id=args.store_id,
        camera_id=args.camera_id,
        model_path=args.model,
        clip_start=clip_start,
        frame_stride=args.frame_stride,
    ).run()
    print({"events_written": count, "output": str(args.output)})


if __name__ == "__main__":
    main()
