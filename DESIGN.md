# DESIGN

## Architecture Overview

This project is built as a complete but pragmatic Store Intelligence system. The detection side processes CCTV footage and emits structured visitor events. The API side validates, stores, and computes business metrics from those events and the POS transaction file. The implementation favors a simple operational path because the evaluation framework gives reviewers only a few minutes to run the system, inspect events, and call endpoints.

The main runtime is a FastAPI service backed by SQLite. SQLite was chosen because the challenge FAQ explicitly allows it and because it makes `docker compose up` reliable without database migrations or a separate PostgreSQL container. The storage layer is still isolated in `app/storage.py`, so moving to PostgreSQL later would mainly require replacing SQL statements and connection handling rather than rewriting analytics logic.

The data flow is:

1. CCTV clips are processed by `pipeline.run_all` using YOLOE-26 person detection.
2. The detection pipeline emits JSONL events using the required schema.
3. `pipeline.live_replay` or the Docker `yoloe-live` service posts those events to `POST /events/ingest`.
4. The API validates each event with Pydantic, deduplicates by `event_id`, and stores accepted events.
5. Analytics modules compute metrics, funnel, heatmap, anomalies, and health directly from stored events and POS rows.

## Detection Design

The detection pipeline supports a real YOLOE-26 path and a sample path. The production demo default is `yoloe-26s-seg.pt`, loaded through Ultralytics YOLOE with the text prompt restricted to `person`. This replaced the weak custom `models/best.pt` path for the main demo while keeping optional custom-model support for later comparisons. Tracking uses a lightweight centroid tracker in this repository. This is intentionally simple and explainable: it assigns stable camera-local track IDs, maps each person to zones, and uses zone transitions to emit `ZONE_ENTER`, `ZONE_EXIT`, and `ZONE_DWELL`.

After all cameras are processed, `pipeline/stitch_sessions.py` converts camera-local visitor IDs such as `VIS_CAM_3_00001` into anonymous store-level session IDs such as `VIS_70594640`. The stitcher uses camera route order, event time gaps, zone context, and track-fragment guards. It preserves the original local ID in event metadata as `pre_stitch_visitor_id` and `camera_visitor_id`, so the reviewer can audit how a session was assembled.

Zone mapping is rule based. The config file defines camera IDs, normalized polygons, and an entry threshold line. A detected person's bottom-center point is mapped into a polygon. This makes the approach auditable and easy to tune for the provided store layout. It also avoids depending on a VLM for every frame, which would be slower, costly, and harder to reproduce during evaluation.

Staff/customer identity is anonymous role classification, not face identity. The detector emits person boxes only; `pipeline/staff.py` adds `person_role`, `role_confidence`, and `role_source` metadata from transparent cues such as purple/magenta uniform-like torso regions, service/billing camera hints, and weak head-region sharpness support. The stitcher uses majority staff evidence rather than allowing one weak staff event to mark an entire session. The intended next step is to replace this with a small crop classifier trained on staff/customer person crops.

## API Design

The ingest endpoint accepts a JSON array or an object containing an `events` array. It validates every event independently and returns accepted, duplicate, and rejected counts. Duplicate event IDs are ignored rather than inserted again, making replay safe. Validation errors are returned as structured partial-success responses instead of crashing the batch.

The metrics endpoint uses the latest ingested event day as the replay business day. This keeps old challenge clips useful even when reviewed on a later date. If events are current, that window is naturally today. Staff events are excluded from all customer metrics.

POS correlation follows the problem statement: a visitor in the billing zone during the five minutes before a POS timestamp counts as converted. Since POS data has no customer ID, the system correlates by store and time window. This is intentionally session-level, not transaction-line-level. The POS importer groups CSV rows by invoice number to avoid counting multiple SKUs in the same receipt as multiple purchases.

## Failure Handling and Observability

Every request is logged as structured JSON with `trace_id`, `store_id`, endpoint, latency, event count, and status code. Database errors are converted to HTTP 503 responses with a structured body. `/health` reports database status, last event timestamp by store, and `STALE_FEED` warnings when the feed is older than the configured threshold.

## AI-Assisted Decisions

AI helped shape three decisions. First, I used it to compare a heavy production stack against a lightweight challenge stack. The suggestion was PostgreSQL plus a worker queue. I overrode that for the first submission because the evaluation gate values clean startup, and SQLite is accepted by the FAQ. The code keeps a storage boundary so PostgreSQL remains a later upgrade.

Second, AI suggested using a VLM for zone classification. I rejected that for the main loop because it would be expensive and hard to reproduce. I chose normalized polygons from `store_layout.json`, which are transparent and fast. A VLM can still be useful offline to validate zone labels or staff uniform patterns.

Third, AI suggested dropping low-confidence detections to improve apparent accuracy. I kept low-confidence events with their confidence values because the problem statement explicitly rewards confidence calibration. Silent suppression would make hidden scoring and debugging worse.
