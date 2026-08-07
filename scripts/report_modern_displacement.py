"""Report how far the modern decluttering moves planets from their true positions.

The collision resolver trades positional truth for legibility: a planet in a
tight cluster is drawn at a ``display_angle`` away from its real longitude, with
a tether line pointing back. This script quantifies that trade on three fixed
charts — the 2000-02-26 stellium, an all-points natal, and an all-points
synastry — so a change to the resolver can be judged by numbers instead of by
eyeballing wheels: run it before and after, compare the tables.

It reads the displacements out of the rendered SVG rather than calling the
resolver directly: every ChartPoint group is rotated by its display angle and
every Indicator group by the true angle, and the two carry the same
``kr:slug``/``kr:horoscope``/``kr:absoluteposition``, so pairing them measures
the whole pipeline — ring configuration, per-ring separations, everything.

Usage::

    python3 scripts/report_modern_displacement.py

@module scripts.report_modern_displacement
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS, DEFAULT_ACTIVE_POINTS
from kerykeion.utilities import wrap_180

#: Below this displacement the renderer draws a straight tick instead of a
#: tether arc (draw_modern._draw_indicator_line).
STRAIGHT_TETHER_THRESHOLD = 0.5

_CHARTPOINT = re.compile(
    r"""<g\s+kr:node=['"]ChartPoint['"](?P<attrs>[^>]*)"""
    r"""transform=['"]rotate\(-(?P<angle>\d+(?:\.\d+)?)\s+50\.0\s+50\.0\)['"]"""
)
_INDICATOR = re.compile(
    r"""<g\s+kr:node=['"]Indicator['"](?P<attrs>[^>]*)"""
    r"""transform=['"]rotate\(-(?P<angle>\d+(?:\.\d+)?)\s+50\.0\s+50\.0\)['"]"""
)
_SLUG = re.compile(r"""kr:slug=['"]([^'"]+)['"]""")
_HOROSCOPE = re.compile(r"""kr:horoscope=['"]([^'"]+)['"]""")


def _keyed_angles(pattern: re.Pattern, svg: str) -> dict[tuple[str, str], float]:
    out: dict[tuple[str, str], float] = {}
    for match in pattern.finditer(svg):
        attrs = match.group("attrs")
        slug = _SLUG.search(attrs)
        if not slug:
            continue
        horoscope = _HOROSCOPE.search(attrs)
        out[(slug.group(1), horoscope.group(1) if horoscope else "0")] = float(match.group("angle"))
    return out


def _subject(name: str, year: int, month: int, day: int, hour: int, minute: int,
             lat: float, lng: float, tz: str, active: list[str]):
    return AstrologicalSubjectFactory.from_birth_data(
        name, year, month, day, hour, minute,
        lat=lat, lng=lng, tz_str=tz, online=False,
        suppress_geonames_warning=True, active_points=active,
    )


def _measure(svg: str) -> dict[str, list[tuple[str, float]]]:
    """ring id -> [(slug, |displacement| in degrees), ...]"""
    displays = _keyed_angles(_CHARTPOINT, svg)
    reals = _keyed_angles(_INDICATOR, svg)
    rings: dict[str, list[tuple[str, float]]] = {}
    for key, display in displays.items():
        real = reals.get(key)
        if real is None:
            continue
        slug, ring = key
        rings.setdefault(ring, []).append((slug, abs(wrap_180(display - real))))
    return rings


def main() -> None:
    stellium_points = DEFAULT_ACTIVE_POINTS + ["True_South_Lunar_Node"]
    stellium = _subject("Stellium", 2000, 2, 26, 12, 0, 51.5, 0.0, "UTC", stellium_points)
    all_natal = _subject("AllPoints", 2000, 2, 26, 12, 0, 51.5, 0.0, "UTC", ALL_ACTIVE_POINTS)
    partner = _subject("Partner", 1993, 9, 12, 8, 30, 41.9, 12.5, "Europe/Rome", ALL_ACTIVE_POINTS)

    charts = [
        ("natal stellium 2000-02-26",
         ChartDataFactory.create_natal_chart_data(stellium, active_points=stellium_points)),
        ("natal all-points",
         ChartDataFactory.create_natal_chart_data(all_natal, active_points=ALL_ACTIVE_POINTS)),
        ("synastry all-points",
         ChartDataFactory.create_synastry_chart_data(all_natal, partner, active_points=ALL_ACTIVE_POINTS)),
    ]

    print(f"{'chart / ring':<38}{'n':>4}{'mean':>8}{'max':>8}{'straight':>10}")
    for label, chart_data in charts:
        svg = ChartDrawer(chart_data=chart_data).generate_wheel_only_svg_string(style="modern")
        for ring, rows in sorted(_measure(svg).items()):
            values = [d for _, d in rows]
            straight = sum(1 for d in values if d < STRAIGHT_TETHER_THRESHOLD)
            worst_slug = max(rows, key=lambda r: r[1])[0]
            print(
                f"{label + ' / ring ' + ring:<38}{len(values):>4}"
                f"{mean(values):>8.3f}{max(values):>8.3f}{straight:>7}/{len(values):<3}"
                f"  worst: {worst_slug}"
            )


if __name__ == "__main__":
    main()
