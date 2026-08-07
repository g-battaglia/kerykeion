"""Parsers for the ``kr:`` metadata groups the chart SVGs carry.

Every rendered celestial point is a ``<g kr:node="ChartPoint" ...>`` rotated to
its display angle, and every tether line a ``<g kr:node="Indicator" ...>``
rotated to the point's true angle. Downstream code — the displacement report,
the decluttering tests, focus tooling — reads positions back out of the SVG
through those attributes, and for a while each consumer carried its own copy of
the parsing grammar: three regexes that had to change in lockstep whenever the
serializer touched attribute order or angle formatting. This module is the one
copy they now share.

The grammar is deliberately tolerant of attribute order and of single or double
quotes; it is pinned to the one thing all serializer paths guarantee, the
``rotate(-ANGLE 50.0 50.0)`` transform in the wheel-local frame.

@module kerykeion.charts.svg_metadata
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

_CHART_POINT_GROUP = re.compile(
    r"""<g\s+kr:node=['"]ChartPoint['"](?P<attributes>[^>]*)"""
    r"""transform=['"]rotate\(-(?P<angle>\d+(?:\.\d+)?)\s+50\.0\s+50\.0\)['"]"""
)
_INDICATOR_GROUP = re.compile(
    r"""<g\s+kr:node=['"]Indicator['"](?P<attributes>[^>]*)"""
    r"""transform=['"]rotate\(-(?P<angle>\d+(?:\.\d+)?)\s+50\.0\s+50\.0\)['"]"""
)


def _attribute(blob: str, name: str) -> Optional[str]:
    match = re.search(rf"""kr:{name}=['"]([^'"]+)['"]""", blob)
    return match.group(1) if match else None


@dataclass(frozen=True)
class ChartPointTag:
    """One rendered celestial point, as the SVG describes it."""

    slug: str
    horoscope: str  #: owning ring: "0" (single chart / dual inner) or "1" (dual outer)
    display_angle: float  #: wheel angle the point is drawn at, after decluttering
    sign: Optional[str]
    sign_position: Optional[float]
    retrograde: bool


@dataclass(frozen=True)
class IndicatorTag:
    """One tether line, anchored at its point's true wheel angle."""

    slug: str
    horoscope: str
    true_angle: float


def parse_chart_points(svg: str) -> list[ChartPointTag]:
    """Every ChartPoint group in *svg*, in document order."""
    points = []
    for match in _CHART_POINT_GROUP.finditer(svg):
        blob = match.group("attributes")
        slug = _attribute(blob, "slug")
        if slug is None:
            continue
        sign_position = _attribute(blob, "signposition")
        points.append(
            ChartPointTag(
                slug=slug,
                horoscope=_attribute(blob, "horoscope") or "0",
                display_angle=float(match.group("angle")),
                sign=_attribute(blob, "sign"),
                sign_position=float(sign_position) if sign_position is not None else None,
                retrograde=_attribute(blob, "retrograde") == "true",
            )
        )
    return points


def parse_indicators(svg: str) -> list[IndicatorTag]:
    """Every Indicator group in *svg*, in document order."""
    indicators = []
    for match in _INDICATOR_GROUP.finditer(svg):
        blob = match.group("attributes")
        slug = _attribute(blob, "slug")
        if slug is None:
            continue
        indicators.append(
            IndicatorTag(
                slug=slug,
                horoscope=_attribute(blob, "horoscope") or "0",
                true_angle=float(match.group("angle")),
            )
        )
    return indicators
