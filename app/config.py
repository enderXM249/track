from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Store Intelligence API")
    db_path: Path = Path(os.getenv("APP_DB_PATH", "data/store_intelligence.db"))
    pos_csv_path: Path = Path(
        os.getenv("POS_CSV_PATH", "Brigade_Bangalore_10_April_26 (1)bc6219c.csv")
    )
    store_layout_path: Path = Path(os.getenv("STORE_LAYOUT_PATH", "config/store_layout.json"))
    cctv_dir_path: Path = Path(os.getenv("CCTV_DIR_PATH", "CCTV Footage"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    ingest_batch_limit: int = _int_env("INGEST_BATCH_LIMIT", 500)
    stale_feed_minutes: int = _int_env("STALE_FEED_MINUTES", 10)
    reentry_window_seconds: int = _int_env("REENTRY_WINDOW_SECONDS", 180)
    queue_spike_threshold: int = _int_env("QUEUE_SPIKE_THRESHOLD", 5)


settings = Settings()
