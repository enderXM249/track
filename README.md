# Store Intelligence API

End-to-end implementation for the Store Intelligence challenge: raw CCTV footage becomes structured visitor events, events are ingested into an API, and the API returns live store metrics such as visitors, conversion rate, dwell, funnel, heatmap, anomalies, and health.

The implementation is intentionally production-aware but practical for the challenge window. The API uses FastAPI with SQLite so `docker compose up` is enough to start the system. The detection pipeline can run in two modes:

- `sample`: generates schema-valid events that exercise staff, re-entry, queue, dwell, and abandonment behavior.
- `detect`: uses Ultralytics YOLOE-26 by default (`yoloe-26s-seg.pt`) with a text prompt restricted to `person`.

## Five-Command Setup

```bash
git clone <your-repo-url>
cd store-intelligence
docker compose up --build -d
python scripts/ingest_jsonl.py sample_data/sample_events.jsonl --api-url http://127.0.0.1:8000
curl http://127.0.0.1:8000/stores/ST1008/metrics
```

Then verify:

```bash
curl http://127.0.0.1:8000/stores/ST1008/metrics
curl http://127.0.0.1:8000/stores/ST1008/funnel
curl http://127.0.0.1:8000/stores/ST1008/heatmap
curl http://127.0.0.1:8000/stores/ST1008/anomalies
curl http://127.0.0.1:8000/health
```

On Windows PowerShell, replace `curl` with `Invoke-RestMethod` if needed.

## Running the API Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API stores data in `data/store_intelligence.db` by default. The bundled POS CSV is imported during startup when `POS_CSV_PATH` points to it.

## Running the Detection Pipeline

Generate sample events:

```bash
python -m pipeline.run --mode sample --output sample_data/sample_events.jsonl
```

Run YOLOE-26 detection against a CCTV clip:

```bash
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-pipeline.txt
python -m pipeline.run --mode detect --video "CCTV Footage/CAM 1.mp4" --camera-id CAM_1 --output generated_events_yoloe26.jsonl
```

Process all CCTV clips into one combined event stream:

```bash
python -m pipeline.run_all --video-dir "CCTV Footage" --clip-start 2026-04-10T11:20:00Z --frame-stride 10 --output generated_events_yoloe26.jsonl
```

`run_all` stitches camera-local track IDs into store-level anonymous visitor sessions by default. Use `--no-stitch` only when debugging raw per-camera output.

The default model is `yoloe-26s-seg.pt`. You can choose a different YOLOE-26 size when your machine has enough GPU/CPU budget:

```bash
python -m pipeline.run_all --video-dir "CCTV Footage" --model yoloe-26m-seg.pt --clip-start 2026-04-10T11:20:00Z --frame-stride 10 --output generated_events_yoloe26m.jsonl
```

Compare outputs:

```bash
python scripts/compare_event_files.py generated_events.jsonl generated_events_yoloe26.jsonl
```

The detector adds audit metadata per event: `detector_model`, `detector_family`, `detector_prompt`, `bbox_xyxy`, `center_norm`, `person_role`, `role_confidence`, `role_source`, and `role_signals`. Staff/customer is anonymous role classification, not face identity.

Replay events into the API:

```bash
python -m pipeline.replay --events generated_events_yoloe26.jsonl --api-url http://127.0.0.1:8000
```

The Re-ID/session baseline also preserves `camera_visitor_id`, `pre_stitch_visitor_id`, `session_seq`, and `stitching_method` so reviewer questions can be answered from the event stream.

## Optional Custom Training

The project no longer depends on your weak custom `models/best.pt`; YOLOE-26 is the default production demo detector. The notebook remains useful only if you later want to fine-tune a CCTV-specific model. Open `notebooks/train_yolo_colab.ipynb` in Google Colab. It supports two paths:

- Train from a YOLO-format dataset on Google Drive with `data.yaml`.
- Download a labeled dataset from Roboflow if you have one.

After training, the notebook copies the best model to:

```text
/content/drive/MyDrive/store-intelligence-models/best.pt
```

Download that file and place it here if you deliberately want to compare it with YOLOE:

```text
models/best.pt
```

The raw CCTV challenge footage is not automatically trainable by itself. YOLO training needs labeled person boxes. If you only have raw clips, use the notebook's frame-extraction cell, label the frames in CVAT/Roboflow/Label Studio, export YOLO format, then run the training cells.

For Roboflow annotation rules, follow [docs/ANNOTATION_PROTOCOL.md](docs/ANNOTATION_PROTOCOL.md).

## API Endpoints

### `POST /events/ingest`

Accepts a JSON array or `{ "events": [...] }` batch of up to 500 events. It validates every event independently, deduplicates by `event_id`, and returns partial success.

### `GET /stores/{id}/metrics`

Returns unique visitors, conversion rate, average dwell per zone, queue depth, and abandonment rate. Staff events are excluded.

### `GET /stores/{id}/funnel`

Returns session-based funnel stages: Entry, Zone Visit, Billing Queue, Purchase. Re-entry events do not double count the same `visitor_id`.

### `GET /stores/{id}/heatmap`

Returns zone visit frequency, average dwell, normalized 0-100 score, and a `data_confidence` flag.

### `GET /stores/{id}/anomalies`

Returns active queue spike, conversion drop, and dead zone anomalies with severity and suggested action.

### `GET /health`

Returns service status, database status, last event timestamp by store, and stale feed warnings.

## Tests

```bash
pip install -r requirements.txt
pytest --cov=app --cov=pipeline tests
```

Each test file includes the required `PROMPT` and `CHANGES MADE` block. The tests cover ingest idempotency, schema validation, staff exclusion, zero traffic, zero purchases, re-entry funnel behavior, heatmap confidence, anomaly detection, health data, and sample pipeline event validity.

## Live Dashboard

Docker demo instructions are also available in [DOCKER_LIVE_DEMO.md](DOCKER_LIVE_DEMO.md).

Production-style Docker path:

```powershell
docker compose down
Remove-Item data\store_intelligence.db -Force -ErrorAction SilentlyContinue
docker compose --profile live up --build
```

This starts the API/dashboard and a YOLOE-26 live service that processes the mounted CCTV clips, writes `/data/generated_events_yoloe26.jsonl`, and streams those events into `POST /events/ingest`.

Open the web dashboard:

```text
http://127.0.0.1:8000/dashboard
```

The dashboard shows a CCTV video feed, recent detection boxes from event metadata, live KPIs, funnel, anomalies, heatmap, and latest events.

Run simulated-real-time replay from pipeline-generated events:

```bash
python -m pipeline.live_replay --events generated_events_yoloe26.jsonl --api-url http://127.0.0.1:8000 --speed 12 --batch-size 1
```

The dashboard polls `/stores/ST1008/live` every 1.5 seconds. The replay script posts events through `POST /events/ingest`, so the dashboard changes only when the API stores new events.

For a clean demo, start with a fresh database. With local Uvicorn:

```powershell
Remove-Item data\live_demo.db -Force -ErrorAction SilentlyContinue
$env:APP_DB_PATH="data/live_demo.db"
uvicorn app.main:app --reload
```

If you do not reset the DB, add `--fresh-run` so repeated demos still visibly update metrics:

```bash
python -m pipeline.live_replay --events generated_events_yoloe26.jsonl --api-url http://127.0.0.1:8000 --speed 12 --fresh-run
```

The older terminal dashboard is still available:

```bash
python dashboard/app.py --api-url http://127.0.0.1:8000 --store-id ST1008
```

## Important Files

- `DESIGN.md`: architecture and AI-assisted design notes.
- `CHOICES.md`: required trade-off writeup.
- `PROJECT_PLAN.md`: detailed execution plan.
- `config/store_layout.json`: zone and camera configuration.
- `notebooks/train_yolo_colab.ipynb`: optional Colab notebook for later custom training.
- `models/`: optional local model directory; the default detector is YOLOE-26.
