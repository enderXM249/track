from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import settings


@lru_cache(maxsize=4)
def load_layout(path: str | Path | None = None) -> dict[str, Any]:
    layout_path = Path(path or settings.store_layout_path)
    if not layout_path.exists():
        return {"stores": {}}
    with layout_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def zones_for_store(store_id: str, path: str | Path | None = None) -> list[dict[str, Any]]:
    layout = load_layout(path)
    store = layout.get("stores", {}).get(store_id, {})
    return store.get("zones", [])


def billing_zone_ids(store_id: str, path: str | Path | None = None) -> set[str]:
    zones = zones_for_store(store_id, path)
    billing = {
        zone["zone_id"]
        for zone in zones
        if "BILL" in zone.get("zone_id", "").upper()
        or "CASH" in zone.get("zone_id", "").upper()
        or "CHECKOUT" in zone.get("zone_id", "").upper()
    }
    return billing or {"BILLING", "BILLING_COUNTER", "CHECKOUT"}
