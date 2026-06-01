from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.analytics import compute_anomalies, compute_funnel, compute_heatmap, compute_metrics
from app.config import settings
from app.logging_config import configure_logging, request_logging_middleware
from app.pos_import import import_pos_csv
from app.schemas import EventIn, HealthResponse, IngestError, IngestResponse
from app.storage import (
    check_database,
    init_db,
    insert_events,
    latest_event_timestamp_by_store,
)
from app.time_utils import parse_timestamp


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    init_db()
    import_pos_csv(settings.pos_csv_path)
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.middleware("http")(request_logging_middleware)


@app.exception_handler(sqlite3.Error)
async def sqlite_exception_handler(request: Request, exc: sqlite3.Error) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": "DATABASE_UNAVAILABLE",
            "message": "The analytics database is unavailable.",
            "trace_id": getattr(request.state, "trace_id", None),
        },
    )


def _extract_payload(body: Any) -> list[Any]:
    if isinstance(body, list):
        return body
    if isinstance(body, dict) and isinstance(body.get("events"), list):
        return body["events"]
    raise HTTPException(
        status_code=400,
        detail={
            "error": "INVALID_PAYLOAD",
            "message": "Expected a JSON array or an object with an events array.",
        },
    )


@app.post("/events/ingest", response_model=IngestResponse)
async def ingest_events(request: Request, body: Any = Body(...)) -> IngestResponse:
    payload = _extract_payload(body)
    request.state.event_count = len(payload)
    if payload and isinstance(payload[0], dict):
        request.state.store_id = payload[0].get("store_id")
    if len(payload) > settings.ingest_batch_limit:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "BATCH_TOO_LARGE",
                "message": f"Maximum batch size is {settings.ingest_batch_limit}.",
            },
        )

    valid: list[EventIn] = []
    errors: list[IngestError] = []
    for index, raw_event in enumerate(payload):
        event_id = raw_event.get("event_id") if isinstance(raw_event, dict) else None
        try:
            valid.append(EventIn.model_validate(raw_event))
        except ValidationError as exc:
            first = exc.errors()[0]
            errors.append(
                IngestError(
                    index=index,
                    event_id=event_id,
                    code="INVALID_EVENT",
                    message=f"{'.'.join(str(part) for part in first['loc'])}: {first['msg']}",
                )
            )

    accepted, duplicates = insert_events(valid)
    return IngestResponse(
        accepted=accepted,
        duplicates=duplicates,
        rejected=len(errors),
        errors=errors,
    )


@app.get("/stores/{id}/metrics")
async def metrics(id: str) -> dict[str, Any]:
    return compute_metrics(id)


@app.get("/stores/{id}/funnel")
async def funnel(id: str) -> dict[str, Any]:
    return compute_funnel(id)


@app.get("/stores/{id}/heatmap")
async def heatmap(id: str) -> dict[str, Any]:
    return compute_heatmap(id)


@app.get("/stores/{id}/anomalies")
async def anomalies(id: str) -> dict[str, Any]:
    return compute_anomalies(id)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    db_ok = check_database()
    latest_by_store = latest_event_timestamp_by_store() if db_ok else {}
    warnings: list[dict[str, Any]] = []
    stale_cutoff = datetime.now(UTC) - timedelta(minutes=settings.stale_feed_minutes)
    for store_id, timestamp in latest_by_store.items():
        if timestamp and parse_timestamp(timestamp) < stale_cutoff:
            warnings.append(
                {
                    "store_id": store_id,
                    "code": "STALE_FEED",
                    "message": f"No events received in the last {settings.stale_feed_minutes} minutes.",
                    "last_event_timestamp": timestamp,
                }
            )
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        database="ok" if db_ok else "unavailable",
        last_event_timestamp_per_store=latest_by_store,
        warnings=warnings,
    )
