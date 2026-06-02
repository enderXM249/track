# CHOICES

## 1. Detection Model Choice

Options considered were YOLOE-26, a custom trained YOLO `best.pt`, RT-DETR, MediaPipe, and a VLM-only approach. YOLOE-26 was selected for the production demo because the first custom model was too weak on the challenge CCTV clips, while YOLOE-26 provides stronger pretrained open-vocabulary person detection through the familiar Ultralytics API. RT-DETR may improve some crowded scenes, but it adds more complexity for a short challenge. MediaPipe is lightweight, but it is less suitable for full-body retail CCTV with occlusion. A VLM-only approach would be too slow and expensive for frame-by-frame processing.

The AI suggestion was to start with YOLOv8 or YOLOv11 and use ByteTrack or DeepSORT for tracking. I chose a YOLOE-compatible path and a simple centroid tracker in this repository, then added a separate cross-camera stitching pass. That tracker is not the final production tracker, but it keeps the submission understandable and runnable. If time allows, the next improvement is to replace the local tracker with ByteTrack or StrongSORT while keeping the event emission and stitching layers unchanged.

The Colab notebook remains as an optional custom-training path, but the main project no longer depends on `models/best.pt`. The pipeline defaults to `yoloe-26s-seg.pt`, sets the class prompt to `person`, and records `detector_model`, `detector_prompt`, and role metadata in every emitted event. Staff/customer identity is handled as anonymous role classification through `is_staff` plus `metadata.person_role`; it does not identify faces.

## 2. Event Schema Design Rationale

The challenge provided a required event shape, so the project keeps that schema directly rather than creating a private internal schema. The Pydantic model validates `event_id`, store, camera, visitor token, event type, timestamp, zone, dwell duration, staff flag, confidence, and metadata. The API accepts low-confidence events instead of suppressing them. This matters because the reviewers evaluate confidence calibration and because downstream metrics can decide how to treat uncertain detections.

The AI suggestion was to split raw detections, tracks, sessions, and business events into separate schemas. That is a good production design, but it is more than the acceptance gate needs. I chose one public event schema for ingest plus internal helper logic for metrics. The trade-off is that the event table stores metadata as JSON instead of fully normalized columns. This makes ingestion flexible and keeps schema changes small while still supporting required metrics like queue depth and session sequence.

The schema is idempotent by `event_id`, replayable through JSONL, and readable in follow-up discussion. It also supports the scoring edge cases: staff exclusion through `is_staff`, re-entry through `REENTRY` under the same `visitor_id`, group handling through one event per track, dwell through repeated 30-second `ZONE_DWELL`, and billing behavior through queue events and POS correlation.

The event metadata intentionally carries audit fields beyond the minimum schema: camera-local visitor ID, pre-stitch visitor ID, bounding box, center point, and stitching method. These make the Re-ID/session baseline easier to debug without changing the required public event fields.

## 3. API Architecture Choice

Options considered were FastAPI with SQLite, FastAPI with PostgreSQL, and Node.js with Express. FastAPI was chosen because the challenge FAQ says Python has the best scoring harness coverage, and Pydantic validation maps naturally to event ingestion. SQLite was chosen for the submitted baseline because it keeps `docker compose up` simple and deterministic. PostgreSQL is better for multi-store production traffic, but it introduces more moving parts for a take-home evaluation.

The AI recommendation was PostgreSQL plus Redis or Kafka for event streaming. I agree with that direction for 40 live stores, but I chose a smaller architecture for this first version. The code still separates ingestion, storage, analytics, and health modules, so scaling later is straightforward: replace SQLite with PostgreSQL, move replay/ingest to a queue, and materialize daily aggregates.

The API computes metrics from stored events rather than returning hardcoded outputs. This is important because the evaluation framework caps scores when outputs do not vary with input. The system also imports POS transactions and correlates them with billing-zone visitors in the five-minute pre-transaction window. Health and structured logs are first-class because the problem statement says `/health` is what an on-call engineer checks first.
