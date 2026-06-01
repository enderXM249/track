from __future__ import annotations

from typing import Any


def classify_staff(frame: Any, bbox: tuple[float, float, float, float]) -> tuple[bool, float]:
    """Heuristic staff classifier.

    This keeps the baseline transparent. If uniforms are visually consistent, extend this
    function with store-specific color rules or a trained classifier. Until then, customer
    metrics are protected by returning a low-confidence non-staff label.
    """

    return False, 0.55
