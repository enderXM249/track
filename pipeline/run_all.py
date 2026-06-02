from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from pipeline.detect import DEFAULT_DETECTOR_MODEL, VideoProcessor
from pipeline.enrich_events import enrich_billing_abandonment_file
from pipeline.stitch_sessions import stitch_file


CAMERA_FILES = {
    "CAM_1": "CAM 1.mp4",
    "CAM_2": "CAM 2.mp4",
    "CAM_3": "CAM 3.mp4",
    "CAM_4": "CAM 4.mp4",
    "CAM_5": "CAM 5.mp4",
}


def process_all_cameras(
    *,
    video_dir: Path,
    output: Path,
    layout: Path,
    store_id: str,
    model: Path,
    clip_start: datetime,
    frame_stride: int,
    inference_imgsz: int,
    confidence_threshold: float = 0.05,
    tracking_backend: str = "botsort",
    pos_csv: Path | None = None,
    stitch: bool = True,
) -> dict[str, object]:
    temp_dir = output.parent / "_camera_events"
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_paths: list[Path] = []
    total = 0
    camera_counts: dict[str, int] = {}

    for camera_id, filename in CAMERA_FILES.items():
        video_path = video_dir / filename
        if not video_path.exists():
            camera_counts[camera_id] = 0
            print({"camera_id": camera_id, "skipped": "missing video", "path": str(video_path)})
            continue

        camera_output = temp_dir / f"{camera_id}.jsonl"
        processor = VideoProcessor(
            video_path=video_path,
            output_path=camera_output,
            layout_path=layout,
            store_id=store_id,
            camera_id=camera_id,
            model_path=model,
            clip_start=clip_start,
            frame_stride=frame_stride,
            confidence_threshold=confidence_threshold,
            inference_imgsz=inference_imgsz,
            tracking_backend=tracking_backend,
        )
        count = processor.run()
        output_paths.append(camera_output)
        total += count
        camera_counts[camera_id] = count
        print({"camera_id": camera_id, "events_written": count, "output": str(camera_output)})

    combined_output = output if not stitch else temp_dir / "combined_unstitched.jsonl"
    combined_output.parent.mkdir(parents=True, exist_ok=True)
    with combined_output.open("w", encoding="utf-8") as combined:
        for path in output_paths:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    combined.write(line)

    if not stitch:
        result = {
            "combined_events": total,
            "camera_counts": camera_counts,
            "output": str(output),
            "stitched": False,
        }
    else:
        stitched_count = stitch_file(combined_output, output)
        enriched_count = (
            enrich_billing_abandonment_file(output, output, pos_csv)
            if pos_csv is not None and pos_csv.exists()
            else stitched_count
        )
        result = {
            "combined_events": total,
            "stitched_events": stitched_count,
            "enriched_events": enriched_count,
            "camera_counts": camera_counts,
            "output": str(output),
            "stitched": True,
        }
    print(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Process all CCTV camera clips into one JSONL.")
    parser.add_argument("--video-dir", type=Path, default=Path("sample_data/store-intelligence-videos"))
    parser.add_argument("--output", type=Path, default=Path("generated_events.jsonl"))
    parser.add_argument("--layout", type=Path, default=Path("config/store_layout.json"))
    parser.add_argument("--store-id", default="STORE_BLR_002")
    parser.add_argument(
        "--model",
        type=Path,
        default=Path(DEFAULT_DETECTOR_MODEL),
        help=(
            "Local .pt file or Ultralytics weight name, "
            f"e.g. {DEFAULT_DETECTOR_MODEL}."
        ),
    )
    parser.add_argument("--clip-start", default="2026-04-10T11:30:00Z")
    parser.add_argument("--frame-stride", type=int, default=5)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--conf", type=float, default=0.05)
    parser.add_argument("--tracker", choices=["botsort", "bytetrack", "centroid"], default="botsort")
    parser.add_argument("--pos-csv", type=Path, default=Path("sample_data/sample_pos_transactions.csv"))
    parser.add_argument("--no-stitch", action="store_true")
    args = parser.parse_args()

    clip_start = datetime.fromisoformat(args.clip_start.replace("Z", "+00:00")).astimezone(UTC)
    process_all_cameras(
        video_dir=args.video_dir,
        output=args.output,
        layout=args.layout,
        store_id=args.store_id,
        model=args.model,
        clip_start=clip_start,
        frame_stride=args.frame_stride,
        confidence_threshold=args.conf,
        inference_imgsz=args.imgsz,
        tracking_backend=args.tracker,
        pos_csv=args.pos_csv,
        stitch=not args.no_stitch,
    )


if __name__ == "__main__":
    main()
