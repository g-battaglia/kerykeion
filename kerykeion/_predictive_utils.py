# -*- coding: utf-8 -*-
"""
Shared helpers for predictive factories (midpoints, solar arcs, etc.).

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence

from kerykeion.schemas.kr_models import AstrologicalSubjectModel, KerykeionPointModel
from kerykeion.settings.chart_defaults import DEFAULT_CHART_ASPECTS_SETTINGS, DEFAULT_PREDICTIVE_POINTS


def gather_active_points(
    subject: AstrologicalSubjectModel,
    active_points: Optional[Sequence[str]],
) -> List[tuple[str, float]]:
    """Collect ``(name, abs_pos)`` tuples for the requested active points.

    Skips any point that is missing from the subject (e.g. when the
    subject was built with a reduced ``active_points`` list).
    """
    candidate_names: Iterable[str] = DEFAULT_PREDICTIVE_POINTS if active_points is None else active_points

    gathered: List[tuple[str, float]] = []
    seen: set[str] = set()
    for name in candidate_names:
        attr = name.lower()
        if attr in seen:
            continue
        seen.add(attr)
        point: Optional[KerykeionPointModel] = getattr(subject, attr, None)
        if point is None:
            continue
        gathered.append((point.name, point.abs_pos))
    return gathered


def build_aspect_settings(orb: float, aspect_filter: Optional[Sequence[str]]) -> list[dict]:
    """Materialise an aspects-settings list with a uniform orb override."""
    settings: list[dict] = []
    for aspect in DEFAULT_CHART_ASPECTS_SETTINGS:
        name = aspect["name"]  # type: ignore[index]
        if aspect_filter is not None and name not in aspect_filter:
            continue
        settings.append(
            {
                "degree": aspect["degree"],  # type: ignore[index]
                "name": name,
                "orb": orb,
            }
        )
    return settings
