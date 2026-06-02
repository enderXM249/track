from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from pipeline.detect import DEFAULT_DETECTOR_MODEL
from pipeline.live_replay import live_replay
from pipeline.run_all import process_all_cameras


def wait_for_api(api_url: str, timeout_seconds: int = 90) -> None:
    deadline = time.monotonic() + timeout_seconds
    health_url = f"{api_url.rstrip('/')}/health"
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
                if payload.get("status") in {"ok", "degraded"}:
                    return
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
        time.sleep(2)

    raise RuntimeError(f"API did not become ready at {health_url}: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Docker helper: run YOLOE-26 detection and stream events into the API."
    )
    parser.add_argument("--video-dir", type=Path, default=Path("/app/CCTV Footage"))
    parser.add_argument("--events", type=Path, default=Path("/data/generated_events_yoloe26.jsonl"))
    parser.add_argument("--layout", type=Path, default=Path("/app/config/store_layout.json"))
    parser.add_argument("--store-id", default="ST1008")
    parser.add_argument("--model", type=Path, default=Path(DEFAULT_DETECTOR_MODEL))
    parser.add_argument("--clip-start", default="2026-04-10T11:20:00Z")
    parser.add_argument("--frame-stride", type=int, default=10)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--api-url", default="http://api:8000")
    parser.add_argument("--speed", type=float, default=12.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--fresh-run", action="store_true", default=True)
    parser.add_argument("--skip-generate", action="store_true")
    parser.add_argument("--wait-timeout", type=int, default=90)
    args = parser.parse_args()

    wait_for_api(args.api_url, args.wait_timeout)

    if not args.skip_generate:
        clip_start = datetime.fromisoformat(args.clip_start.replace("Z", "+00:00")).astimezone(
            UTC
        )
        process_all_cameras(
            video_dir=args.video_dir,
            output=args.events,
            layout=args.layout,
            store_id=args.store_id,
            model=args.model,
            clip_start=clip_start,
            frame_stride=args.frame_stride,
            inference_imgsz=args.imgsz,
            stitch=True,
        )

    live_replay(
        path=args.events,
        api_url=args.api_url,
        batch_size=args.batch_size,
        speed=args.speed,
        max_sleep=1.5,
        fresh_run=args.fresh_run,
    )


if __name__ == "__main__":
    main()
