"""The ``kr:`` metadata vocabulary the chart SVGs carry — emitters and parsers.

Every rendered celestial point is a ``<g kr:node="ChartPoint" ...>`` rotated to
its display angle, and every tether line a ``<g kr:node="Indicator" ...>``
rotated to the point's true angle. Downstream code — the displacement report,
the decluttering tests, focus tooling, the web frontend — reads positions back
out of the SVG through those attributes, and for a while each consumer carried
its own copy of the parsing grammar: three regexes that had to change in
lockstep whenever the serializer touched attribute order or angle formatting.
This module is the one copy they now share.

It is also where the state attributes are *written*. Three serializers draw
celestial points (classic primary, classic secondary, modern), and an attribute
that only two of them emit is worse than one none of them emit: a consumer
cannot tell a body that has no such state from a chart style that forgot to say
so. ``point_state_attributes`` is the single sentence all three speak.

Attribute names are lowercase letters only, with no separators. Consumers match
them with a general pattern rather than an allow-list — the web frontend
rewrites ``kr:name`` to ``data-kr-name`` through ``/\\bkr:([a-zA-Z]+)=/`` before
sanitizing — so a name carrying an underscore or a digit would be dropped in
silence rather than rejected loudly.

The parsing grammar is deliberately tolerant of attribute order and of single or
double quotes; it is pinned to the one thing all serializer paths guarantee, the
``rotate(-ANGLE 50.0 50.0)`` transform in the wheel-local frame.

@module kerykeion.charts.svg_metadata
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from kerykeion.charts.utils import escape_svg_text

# ``attributes`` spans the whole tag body, transform included, rather than
# stopping at it: the drawer appends chart-level analyses (angularity,
# stellium) to the finished markup, so they land *after* the transform and a
# capture that stopped there would silently miss them.
_CHART_POINT_GROUP = re.compile(
    r"""<g\s+kr:node=['"]ChartPoint['"](?P<attributes>[^>]*"""
    r"""transform=['"]rotate\(-(?P<angle>\d+(?:\.\d+)?)\s+50\.0\s+50\.0\)['"][^>]*)>"""
)
_INDICATOR_GROUP = re.compile(
    r"""<g\s+kr:node=['"]Indicator['"](?P<attributes>[^>]*"""
    r"""transform=['"]rotate\(-(?P<angle>\d+(?:\.\d+)?)\s+50\.0\s+50\.0\)['"][^>]*)>"""
)


def _attribute(blob: str, name: str) -> Optional[str]:
    match = re.search(rf"""kr:{name}=['"]([^'"]+)['"]""", blob)
    return match.group(1) if match else None


def _parse_angularities(value: Optional[str]) -> tuple[tuple[str, float], ...]:
    """``"Ascendant:0.9 Medium_Coeli:4.3"`` back into ordered ``(angle, arc)`` pairs."""
    if not value:
        return ()
    pairs = []
    for token in value.split(" "):
        angle, _, distance = token.rpartition(":")
        if angle:
            pairs.append((angle, float(distance)))
    return tuple(pairs)


# Rounding applied to each numeric state attribute before it reaches the
# markup. Raw floats would carry backend noise into every byte-compared
# baseline downstream for digits no reader will ever use; these keep the
# precision each quantity is actually read at — speed finely enough to show a
# body crawling through a station, declination and magnitude to the precision
# an ephemeris table prints.
_STATE_PRECISION: dict[str, int] = {
    "speed": 6,
    "declination": 4,
    "magnitude": 2,
    "orb": 4,
}


def point_state_attributes(point: object) -> str:
    """The ``kr:`` attributes describing *point*'s physical state.

    Returns a leading-space-prefixed run of attributes ready to splice into a
    ChartPoint tag, or the empty string when the point states none of them.

    An attribute is emitted only when the model actually carries the value:
    silence means "this chart does not compute it" (motion state and
    out-of-bounds are geocentric-only, magnitude belongs to fixed stars),
    which is a different claim from a value of zero or false. ``kr:oob``
    goes further and appears only when the body IS out of bounds, matching
    ``kr:retrograde``: the exception is worth marking, the rule is not.
    """
    attributes: list[str] = []

    motion_state = getattr(point, "motion_state", None)
    if motion_state is not None:
        attributes.append(f'kr:motionstate="{motion_state}"')

    for name, field in (("speed", "speed"), ("declination", "declination")):
        value = getattr(point, field, None)
        if value is not None:
            attributes.append(f'kr:{name}="{round(value, _STATE_PRECISION[name])}"')

    if getattr(point, "is_out_of_bounds", None):
        attributes.append('kr:oob="true"')

    # Fixed stars only: the catalogue brightness, and — for a star surfaced by
    # discovery — which point brought it in and how close it sits.
    magnitude = getattr(point, "magnitude", None)
    if magnitude is not None:
        attributes.append(f'kr:magnitude="{round(magnitude, _STATE_PRECISION["magnitude"])}"')
    near_point = getattr(point, "near_point", None)
    if near_point is not None:
        # Escaped, like every other string this codebase puts in an attribute:
        # chart data can be deserialized or built by a caller, so a name is not
        # a trusted literal. An unescaped quote here would close the attribute
        # and let the rest of the value be read as markup, and a bare apostrophe
        # would be malformed anyway once post-processing swaps the delimiters.
        attributes.append(f'kr:nearpoint="{escape_svg_text(str(near_point))}"')
    orb = getattr(point, "orb", None)
    if orb is not None:
        attributes.append(f'kr:orb="{round(orb, _STATE_PRECISION["orb"])}"')

    return (" " + " ".join(attributes)) if attributes else ""


@dataclass(frozen=True)
class ChartPointTag:
    """One rendered celestial point, as the SVG describes it."""

    slug: str
    horoscope: str  #: owning ring: "0" (single chart / dual inner) or "1" (dual outer)
    display_angle: float  #: wheel angle the point is drawn at, after decluttering
    sign: Optional[str]
    sign_position: Optional[float]
    retrograde: bool
    motion_state: Optional[str] = None
    speed: Optional[float] = None
    declination: Optional[float] = None
    out_of_bounds: bool = False
    #: Every angle the point stands on, closest first, as ``(angle, degrees)``.
    #: Empty when it stands on none — near the poles it can stand on two.
    angularities: tuple[tuple[str, float], ...] = ()
    stellium: Optional[str] = None  #: house whose stellium the point belongs to
    magnitude: Optional[float] = None  #: fixed stars: catalogue brightness
    near_point: Optional[str] = None  #: discovery stars: the point that surfaced it
    orb: Optional[float] = None  #: discovery stars: arc to that point


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
        speed = _attribute(blob, "speed")
        declination = _attribute(blob, "declination")
        magnitude = _attribute(blob, "magnitude")
        orb = _attribute(blob, "orb")
        points.append(
            ChartPointTag(
                slug=slug,
                horoscope=_attribute(blob, "horoscope") or "0",
                display_angle=float(match.group("angle")),
                sign=_attribute(blob, "sign"),
                sign_position=float(sign_position) if sign_position is not None else None,
                retrograde=_attribute(blob, "retrograde") == "true",
                motion_state=_attribute(blob, "motionstate"),
                speed=float(speed) if speed is not None else None,
                declination=float(declination) if declination is not None else None,
                out_of_bounds=_attribute(blob, "oob") == "true",
                angularities=_parse_angularities(_attribute(blob, "angularity")),
                stellium=_attribute(blob, "stellium"),
                magnitude=float(magnitude) if magnitude is not None else None,
                near_point=_attribute(blob, "nearpoint"),
                orb=float(orb) if orb is not None else None,
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
