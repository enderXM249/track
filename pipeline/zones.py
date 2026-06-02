from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Zone:
    zone_id: str
    camera_ids: set[str]
    polygon: list[tuple[float, float]]
    sku_zone: str | None = None


def load_store_layout(path: Path, store_id: str) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        layout = json.load(handle)
    return layout["stores"][store_id]


def load_zones(path: Path, store_id: str) -> list[Zone]:
    store = load_store_layout(path, store_id)
    zones = []
    for raw in store.get("zones", []):
        zones.append(
            Zone(
                zone_id=raw["zone_id"],
                camera_ids=set(raw.get("camera_ids", [])),
                polygon=[tuple(point) for point in raw["polygon"]],
                sku_zone=raw.get("sku_zone"),
            )
        )
    return zones


def point_in_polygon(x: float, y: float, polygon: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(polygon) - 1
    for i, point in enumerate(polygon):
        xi, yi = point
        xj, yj = polygon[j]
        intersects = (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi
        if intersects:
            inside = not inside
        j = i
    return inside


class ZoneMapper:
    def __init__(self, layout_path: Path, store_id: str) -> None:
        self.store = load_store_layout(layout_path, store_id)
        self.zones = load_zones(layout_path, store_id)

    def zone_for_point(self, camera_id: str, x_norm: float, y_norm: float) -> Zone | None:
        for zone in self.zones:
            if camera_id in zone.camera_ids and point_in_polygon(x_norm, y_norm, zone.polygon):
                return zone
        return None

    def entry_line(self, camera_id: str) -> dict[str, Any] | None:
        camera = self.store.get("cameras", {}).get(camera_id, {})
        return camera.get("entry_line")
