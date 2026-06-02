from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import settings
from app.schemas import EventIn
from app.time_utils import to_iso_z


SCHEMA = """
PRAGMA journal_mode = WAL;
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL,
    camera_id TEXT NOT NULL,
    visitor_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    zone_id TEXT,
    dwell_ms INTEGER NOT NULL,
    is_staff INTEGER NOT NULL,
    confidence REAL NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_events_store_time ON events(store_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_store_visitor_time ON events(store_id, visitor_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_store_type_time ON events(store_id, event_type, timestamp);

CREATE TABLE IF NOT EXISTS pos_transactions (
    transaction_id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    basket_value_inr REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pos_store_time ON pos_transactions(store_id, timestamp);
"""


@contextmanager
def connect(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    path = Path(db_path or settings.db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path | None = None) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)


def check_database(db_path: Path | None = None) -> bool:
    try:
        with connect(db_path) as conn:
            conn.execute("SELECT 1").fetchone()
        return True
    except sqlite3.Error:
        return False


def insert_events(events: list[EventIn], db_path: Path | None = None) -> tuple[int, int]:
    accepted = 0
    duplicates = 0
    with connect(db_path) as conn:
        for event in events:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO events (
                    event_id, store_id, camera_id, visitor_id, event_type, timestamp,
                    zone_id, dwell_ms, is_staff, confidence, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.store_id,
                    event.camera_id,
                    event.visitor_id,
                    event.event_type.value,
                    to_iso_z(event.timestamp),
                    event.zone_id,
                    event.dwell_ms,
                    int(event.is_staff),
                    event.confidence,
                    json.dumps(event.metadata, sort_keys=True),
                ),
            )
            if cursor.rowcount == 0:
                duplicates += 1
            else:
                accepted += 1
    return accepted, duplicates


def fetch_events(
    store_id: str,
    start_ts: str | None = None,
    end_ts: str | None = None,
    db_path: Path | None = None,
) -> list[sqlite3.Row]:
    where = ["store_id = ?"]
    params: list[object] = [store_id]
    if start_ts:
        where.append("timestamp >= ?")
        params.append(start_ts)
    if end_ts:
        where.append("timestamp < ?")
        params.append(end_ts)
    query = f"SELECT * FROM events WHERE {' AND '.join(where)} ORDER BY timestamp ASC"
    with connect(db_path) as conn:
        return list(conn.execute(query, params).fetchall())


def fetch_recent_events(
    store_id: str,
    limit: int = 10,
    db_path: Path | None = None,
) -> list[sqlite3.Row]:
    safe_limit = max(1, min(limit, 100))
    with connect(db_path) as conn:
        return list(
            conn.execute(
                """
                SELECT * FROM events
                WHERE store_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (store_id, safe_limit),
            ).fetchall()
        )


def latest_event_timestamp(store_id: str, db_path: Path | None = None) -> str | None:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT MAX(timestamp) AS timestamp FROM events WHERE store_id = ?",
            (store_id,),
        ).fetchone()
    return row["timestamp"] if row else None


def count_events(store_id: str, db_path: Path | None = None) -> int:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM events WHERE store_id = ?",
            (store_id,),
        ).fetchone()
    return int(row["count"]) if row else 0


def latest_event_timestamp_by_store(db_path: Path | None = None) -> dict[str, str | None]:
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT store_id, MAX(timestamp) AS timestamp FROM events GROUP BY store_id"
        ).fetchall()
    return {row["store_id"]: row["timestamp"] for row in rows}


def list_stores(db_path: Path | None = None) -> list[str]:
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT store_id FROM events
            UNION
            SELECT store_id FROM pos_transactions
            ORDER BY store_id
            """
        ).fetchall()
    return [row["store_id"] for row in rows]


def insert_pos_transactions(
    transactions: list[dict[str, object]], db_path: Path | None = None
) -> tuple[int, int]:
    inserted = 0
    duplicates = 0
    with connect(db_path) as conn:
        for txn in transactions:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO pos_transactions (
                    transaction_id, store_id, timestamp, basket_value_inr
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    str(txn["transaction_id"]),
                    str(txn["store_id"]),
                    str(txn["timestamp"]),
                    float(txn["basket_value_inr"]),
                ),
            )
            if cursor.rowcount == 0:
                duplicates += 1
            else:
                inserted += 1
    return inserted, duplicates


def fetch_pos_transactions(
    store_id: str,
    start_ts: str | None = None,
    end_ts: str | None = None,
    db_path: Path | None = None,
) -> list[sqlite3.Row]:
    where = ["store_id = ?"]
    params: list[object] = [store_id]
    if start_ts:
        where.append("timestamp >= ?")
        params.append(start_ts)
    if end_ts:
        where.append("timestamp < ?")
        params.append(end_ts)
    query = f"SELECT * FROM pos_transactions WHERE {' AND '.join(where)} ORDER BY timestamp ASC"
    with connect(db_path) as conn:
        return list(conn.execute(query, params).fetchall())
