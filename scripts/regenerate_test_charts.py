#!/usr/bin/env python3
"""
Regenerate test chart SVGs in tests/data/svg folder

This script creates all types of SVG charts used in tests:
- Natal charts with various configurations (sidereal, house systems, perspectives)
- External natal charts (using external_view parameter)
- Synastry charts
- Transit charts
- Wheel-only charts
- Aspect-grid-only charts
- Charts with different themes (dark, black-and-white)
- Multilingual charts
- Composite charts
- Charts with transparent background

All files are saved to tests/data/svg/. Places come from tests/data/golden_places.py:
a regeneration that resolved city names over the network would bake one day's
answers into every baseline and leave the comparison expecting another day's.
"""

import sys
from functools import partial

from pathlib import Path
from kerykeion.composite_subject.factory import CompositeSubjectFactory
from kerykeion.chart_data.factory import ChartDataFactory
from kerykeion.charts.drawer import ChartDrawer as _ChartDrawer
from kerykeion.charts.utils import make_lunar_phase
from kerykeion.astrological_subject.factory import AstrologicalSubjectFactory
from kerykeion.planetary_returns.factory import PlanetaryReturnFactory
from kerykeion.schemas import KerykeionException
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS, TRADITIONAL_ASTROLOGY_ACTIVE_POINTS

# This script's baselines are CLASSIC-style except where a call passes
# style="modern" explicitly (Section 14; the bulk of the modern baselines live
# in generate_modern_baselines.py). The library default style became "modern"
# in v6, so pin the instance default once here rather than on every one of the
# ChartDrawer calls below. Call-site kwargs still override the partial's.
ChartDrawer = partial(_ChartDrawer, style="classic")


# Two charts, one filename, and the second silently wins. It happened: the
# relationship-score chart was written twice, once with the score on the panel and
# once without, and the comparison test reproduced the loser while the stored
# baseline was the winner. save_svg builds its default name from the SUBJECT's
# name, so a subject named after the variation it demonstrates collides with the
# explicitly-named file for that same variation, and nothing says so.
#
# A regeneration that overwrites its own output is a bug in the regeneration, not
# a policy: refuse it here, where the name is chosen, rather than discovering it in
# a diff months later.
# Guarded at _write_svg_to_disk, which is where the final name is resolved:
# save_svg returns None and its `filename` is None for every default-named chart,
# so the collision is invisible one level up — which is how this one survived.
_WRITTEN: set = set()
_original_write = _ChartDrawer._write_svg_to_disk


def _write_svg_once(self, content, output_path, filename, default_suffix=""):
    written = _original_write(self, content, output_path, filename, default_suffix=default_suffix)
    key = str(written)
    if key in _WRITTEN:
        raise SystemExit(
            f"Two charts write {Path(key).name!r}: this regeneration overwrites its own "
            f"output, so one of the two charts has no baseline and the test that "
            f"reproduces it compares against the other one. Give one of them an explicit "
            f"filename= that names the variation it demonstrates."
        )
    _WRITTEN.add(key)
    return written


_ChartDrawer._write_svg_to_disk = _write_svg_once

# Set output directory for all chart SVGs
# The places the golden charts are cast at, frozen. This script and the tests that
# compare its output must resolve a city the SAME way, or a regeneration bakes one
# answer into 346 files while the comparison expects another — which is what a
# bare city name did, because from_birth_data resolves it over the network.
sys.path.insert(0, str(Path(__file__).parent.parent))
from tests.data.golden_places import golden_place
from tests.data.regeneration_guard import require_library_from_this_checkout, require_the_baseline_backend

require_library_from_this_checkout(__file__)  # noqa: E402
require_the_baseline_backend()  # noqa: E402

OUTPUT_DIR = Path(__file__).parent.parent / "tests" / "data" / "svg"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR_STR = str(OUTPUT_DIR)


def regenerate_lunar_phase_reference_sheet() -> None:
    """Regenerate the reference SVG used by TestLunarPhaseSVG."""
    phase_angles = (0, 45, 90, 135, 180, 225, 270, 315)
    icon_groups: list[str] = []

    for index, angle in enumerate(phase_angles):
        icon_svg = make_lunar_phase(angle, 0.0)
        unique_clip_id = f"moonPhaseCutOffCircle{index}"
        icon_svg = icon_svg.replace("moonPhaseCutOffCircle", unique_clip_id)

        icon_lines = icon_svg.splitlines()
        translated_block = [f'    <g transform="translate({index * 40},0)">']
        translated_block.extend(f"        {line}" for line in icon_lines)
        translated_block.append("    </g>")
        icon_groups.extend(translated_block)

    svg_lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="40" viewBox="0 0 320 40">',
        "    <style>",
        "        :root {",
        "            --kerykeion-chart-color-lunar-phase-0: #000000;",
        "            --kerykeion-chart-color-lunar-phase-1: #ffffff;",
        "        }",
        "    </style>",
    ]
    svg_lines.extend(icon_groups)
    svg_lines.append("</svg>")

    (OUTPUT_DIR / "Moon Phases.svg").write_text("\n".join(svg_lines), encoding="utf-8")


first = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
second = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney", 1942, 6, 18, 15, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)

regenerate_lunar_phase_reference_sheet()

# Internal Natal Chart
natal_chart_data = ChartDataFactory.create_natal_chart_data(first)
internal_natal_chart = ChartDrawer(natal_chart_data)
internal_natal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Black and White Theme Natal Chart
black_and_white_natal_chart = ChartDrawer(natal_chart_data, theme="black-and-white")
black_and_white_natal_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Black and White Theme - Natal Chart - Classic",
)

# External Natal Chart (using external_view parameter)
external_natal_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - ExternalNatal", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
external_natal_chart_data = ChartDataFactory.create_natal_chart_data(external_natal_subject)
external_natal_chart = ChartDrawer(external_natal_chart_data, external_view=True)
external_natal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Synastry Chart
synastry_chart_data = ChartDataFactory.create_synastry_chart_data(first, second)
synastry_chart = ChartDrawer(synastry_chart_data)
synastry_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Synastry Chart without House Comparison grid
synastry_chart_no_house_comparison = ChartDrawer(
    synastry_chart_data,
    show_house_position_comparison=False,
)
synastry_chart_no_house_comparison.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Synastry Chart - No House Comparison",
)

# Synastry Chart with House Comparison only
synastry_chart_house_only = ChartDrawer(
    synastry_chart_data,
    show_house_position_comparison=True,
    show_cusp_position_comparison=False,
)
synastry_chart_house_only.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Synastry Chart - House Comparison Only",
)

# Synastry Chart with Cusp Comparison only
synastry_chart_cusp_only = ChartDrawer(
    synastry_chart_data,
    show_house_position_comparison=False,
    show_cusp_position_comparison=True,
)
synastry_chart_cusp_only.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Synastry Chart - Cusp Comparison Only",
)

# Synastry Chart with both House and Cusp Comparison grids
synastry_chart_house_and_cusp = ChartDrawer(
    synastry_chart_data,
    show_house_position_comparison=True,
    show_cusp_position_comparison=True,
)
synastry_chart_house_and_cusp.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Synastry Chart - House and Cusp Comparison",
)

# Black and White Theme Synastry Chart
black_and_white_synastry_chart = ChartDrawer(synastry_chart_data, theme="black-and-white")
black_and_white_synastry_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Black and White Theme - Synastry Chart - Classic",
)

# Transits Chart
transits_chart_data = ChartDataFactory.create_transit_chart_data(first, second)
transits_chart = ChartDrawer(transits_chart_data)
transits_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Transit Chart without House Comparison grid
transits_chart_no_house_comparison = ChartDrawer(
    transits_chart_data,
    show_house_position_comparison=False,
)
transits_chart_no_house_comparison.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Transit Chart - No House Comparison",
)

# Transit Chart with House Comparison only
transits_chart_house_only = ChartDrawer(
    transits_chart_data,
    show_house_position_comparison=True,
    show_cusp_position_comparison=False,
)
transits_chart_house_only.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Transit Chart - House Comparison Only",
)

# Transit Chart with Cusp Comparison only
transits_chart_cusp_only = ChartDrawer(
    transits_chart_data,
    show_house_position_comparison=False,
    show_cusp_position_comparison=True,
)
transits_chart_cusp_only.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Transit Chart - Cusp Comparison Only",
)

# Transit Chart with both House and Cusp Comparison grids
transits_chart_house_and_cusp = ChartDrawer(
    transits_chart_data,
    show_house_position_comparison=True,
    show_cusp_position_comparison=True,
)
transits_chart_house_and_cusp.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Transit Chart - House and Cusp Comparison",
)

# Black and White Theme Transit Chart
black_and_white_transit_chart = ChartDrawer(transits_chart_data, theme="black-and-white")
black_and_white_transit_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Black and White Theme - Transit Chart - Classic",
)

# Sidereal Birth Chart (Lahiri)
sidereal_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Lahiri",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
    suppress_geonames_warning=True,
)
sidereal_chart_data = ChartDataFactory.create_natal_chart_data(sidereal_subject)
sidereal_chart = ChartDrawer(sidereal_chart_data)
sidereal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (Fagan-Bradley)
sidereal_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Fagan-Bradley",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="FAGAN_BRADLEY",
    suppress_geonames_warning=True,
)
sidereal_chart_data = ChartDataFactory.create_natal_chart_data(sidereal_subject)
sidereal_chart = ChartDrawer(sidereal_chart_data)
sidereal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (DeLuce)
sidereal_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon DeLuce",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="DELUCE",
    suppress_geonames_warning=True,
)
sidereal_chart_data = ChartDataFactory.create_natal_chart_data(sidereal_subject)
sidereal_chart = ChartDrawer(sidereal_chart_data)
sidereal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (J2000)
sidereal_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon J2000",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="J2000",
    suppress_geonames_warning=True,
)
sidereal_chart_data = ChartDataFactory.create_natal_chart_data(sidereal_subject)
sidereal_chart = ChartDrawer(sidereal_chart_data)
sidereal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# House System Morinus
morinus_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Morinus",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="M",
    suppress_geonames_warning=True,
)
morinus_house_chart_data = ChartDataFactory.create_natal_chart_data(morinus_house_subject)
morinus_house_chart = ChartDrawer(morinus_house_chart_data)
morinus_house_chart.save_svg(output_path=OUTPUT_DIR_STR)

## To check all the available house systems uncomment the following code:
# from kerykeion.schemas import HousesSystemIdentifier
# from typing import get_args
# for i in get_args(HousesSystemIdentifier):
#     alternatives_house_subject = AstrologicalSubjectFactory.from_birth_data(f"John Lennon - House System {i}", 1940, 10, 9, 18, 30, "Liverpool", "GB", houses_system=i)
#     alternatives_house_chart_data = ChartDataFactory.create_natal_chart_data(alternatives_house_subject)
#     alternatives_house_chart = ChartDrawer(alternatives_house_chart_data)
#     alternatives_house_chart.save_svg(output_path=OUTPUT_DIR_STR)

# With True Geocentric Perspective
true_geocentric_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - True Geocentric",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    perspective_type="True Geocentric",
    suppress_geonames_warning=True,
)
true_geocentric_chart_data = ChartDataFactory.create_natal_chart_data(true_geocentric_subject)
true_geocentric_chart = ChartDrawer(true_geocentric_chart_data)
true_geocentric_chart.save_svg(output_path=OUTPUT_DIR_STR)

# With Heliocentric Perspective
heliocentric_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Heliocentric",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    perspective_type="Heliocentric",
    suppress_geonames_warning=True,
)
heliocentric_chart_data = ChartDataFactory.create_natal_chart_data(heliocentric_subject)
heliocentric_chart = ChartDrawer(heliocentric_chart_data)
heliocentric_chart.save_svg(output_path=OUTPUT_DIR_STR)

# With Topocentric Perspective
topocentric_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Topocentric",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    perspective_type="Topocentric",
    suppress_geonames_warning=True,
)
topocentric_chart_data = ChartDataFactory.create_natal_chart_data(topocentric_subject)
topocentric_chart = ChartDrawer(topocentric_chart_data)
topocentric_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Minified SVG
minified_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Minified", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
minified_chart_data = ChartDataFactory.create_natal_chart_data(minified_subject)
minified_chart = ChartDrawer(minified_chart_data)
minified_chart.save_svg(output_path=OUTPUT_DIR_STR, minify=True)

# Dark Theme Natal Chart
dark_theme_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Dark Theme", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
dark_theme_natal_chart_data = ChartDataFactory.create_natal_chart_data(dark_theme_subject)
dark_theme_natal_chart = ChartDrawer(dark_theme_natal_chart_data, theme="dark")
dark_theme_natal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Dark Theme External Natal Chart
dark_theme_external_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Dark Theme External", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
dark_theme_external_chart_data = ChartDataFactory.create_natal_chart_data(dark_theme_external_subject)
dark_theme_external_chart = ChartDrawer(dark_theme_external_chart_data, theme="dark", external_view=True)
dark_theme_external_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Dark Theme Synastry Chart
dark_theme_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - DTS", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
dark_theme_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(dark_theme_synastry_subject, second)
dark_theme_synastry_chart = ChartDrawer(dark_theme_synastry_chart_data, theme="dark")
dark_theme_synastry_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Wheel Natal Only Chart
wheel_only_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel Only", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
wheel_only_chart_data = ChartDataFactory.create_natal_chart_data(wheel_only_subject)
wheel_only_chart = ChartDrawer(wheel_only_chart_data)
wheel_only_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel External Natal Only Chart
wheel_external_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel External Only", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
wheel_external_chart_data = ChartDataFactory.create_natal_chart_data(wheel_external_subject)
wheel_external_chart = ChartDrawer(wheel_external_chart_data, external_view=True)
wheel_external_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Synastry Only Chart
wheel_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel Synastry Only", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
wheel_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(wheel_synastry_subject, second)
wheel_synastry_chart = ChartDrawer(wheel_synastry_chart_data)
wheel_synastry_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Transit Only Chart
wheel_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel Transit Only", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
wheel_transit_chart_data = ChartDataFactory.create_transit_chart_data(wheel_transit_subject, second)
wheel_transit_chart = ChartDrawer(wheel_transit_chart_data)
wheel_transit_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Sidereal Birth Chart (Lahiri) Dark Theme
sidereal_dark_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Lahiri - Dark Theme",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
    suppress_geonames_warning=True,
)
sidereal_dark_chart_data = ChartDataFactory.create_natal_chart_data(sidereal_dark_subject)
sidereal_dark_chart = ChartDrawer(sidereal_dark_chart_data, theme="dark")
sidereal_dark_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Only Dark Transparent Natal Chart (Hero Image)
# Uses TRADITIONAL_ASTROLOGY_ACTIVE_POINTS: Sun to Saturn + lunar nodes
wheel_dark_transparent_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel Only Dark Transparent",
    1940,
    10,
    9,
    18,
    30,
    suppress_geonames_warning=True,
    **golden_place("Liverpool", "GB"),
    active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS,
)
wheel_dark_transparent_chart_data = ChartDataFactory.create_natal_chart_data(
    wheel_dark_transparent_subject,
    active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS,
)
wheel_dark_transparent_chart = ChartDrawer(wheel_dark_transparent_chart_data, theme="dark", transparent_background=True)
wheel_dark_transparent_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Only Classic Transparent Natal Chart (Hero Image)
# Uses TRADITIONAL_ASTROLOGY_ACTIVE_POINTS: Sun to Saturn + lunar nodes
wheel_classic_transparent_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel Only Classic Transparent",
    1940,
    10,
    9,
    18,
    30,
    suppress_geonames_warning=True,
    **golden_place("Liverpool", "GB"),
    active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS,
)
wheel_classic_transparent_chart_data = ChartDataFactory.create_natal_chart_data(
    wheel_classic_transparent_subject,
    active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS,
)
wheel_classic_transparent_chart = ChartDrawer(
    wheel_classic_transparent_chart_data, theme="classic", transparent_background=True
)
wheel_classic_transparent_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Only Natal Chart
aspect_grid_only_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid Only", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
aspect_grid_only_chart_data = ChartDataFactory.create_natal_chart_data(aspect_grid_only_subject)
aspect_grid_only_chart = ChartDrawer(aspect_grid_only_chart_data)
aspect_grid_only_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Only Dark Theme Natal Chart
aspect_grid_dark_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid Dark Theme", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
aspect_grid_dark_chart_data = ChartDataFactory.create_natal_chart_data(aspect_grid_dark_subject)
aspect_grid_dark_chart = ChartDrawer(aspect_grid_dark_chart_data, theme="dark")
aspect_grid_dark_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Synastry Chart Aspect Grid Only
aspect_grid_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid Synastry", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
aspect_grid_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(aspect_grid_synastry_subject, second)
aspect_grid_synastry_chart = ChartDrawer(aspect_grid_synastry_chart_data)
aspect_grid_synastry_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Transit Chart Aspect Grid Only
aspect_grid_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid Transit", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
aspect_grid_transit_chart_data = ChartDataFactory.create_transit_chart_data(aspect_grid_transit_subject, second)
aspect_grid_transit_chart = ChartDrawer(aspect_grid_transit_chart_data)
aspect_grid_transit_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Synastry Chart Aspect Grid Only Dark Theme
aspect_grid_dark_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid Dark Synastry", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
aspect_grid_dark_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(
    aspect_grid_dark_synastry_subject, second
)
aspect_grid_dark_synastry_chart = ChartDrawer(aspect_grid_dark_synastry_chart_data, theme="dark")
aspect_grid_dark_synastry_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Synastry Chart With draw_transit_aspect_list table
synastry_chart_with_table_list_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - SCTWL", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
synastry_chart_with_table_list_data = ChartDataFactory.create_synastry_chart_data(
    synastry_chart_with_table_list_subject, second
)
synastry_chart_with_table_list = ChartDrawer(
    synastry_chart_with_table_list_data, double_chart_aspect_grid_type="list", theme="dark"
)
synastry_chart_with_table_list.save_svg(output_path=OUTPUT_DIR_STR)

# Transit Chart With draw_transit_aspect_grid table
transit_chart_with_table_grid_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - TCWTG", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
transit_chart_with_table_grid_data = ChartDataFactory.create_transit_chart_data(
    transit_chart_with_table_grid_subject, second
)
transit_chart_with_table_grid = ChartDrawer(
    transit_chart_with_table_grid_data, double_chart_aspect_grid_type="table", theme="dark"
)
transit_chart_with_table_grid.save_svg(output_path=OUTPUT_DIR_STR)

# Chinese Language Chart
chinese_subject = AstrologicalSubjectFactory.from_birth_data(
    "Hua Chenyu", 1990, 2, 7, 12, 0, suppress_geonames_warning=True, **golden_place("Hunan", "CN")
)
chinese_chart_data = ChartDataFactory.create_natal_chart_data(chinese_subject)
chinese_chart = ChartDrawer(chinese_chart_data, chart_language="CN")
chinese_chart.save_svg(output_path=OUTPUT_DIR_STR)

# French Language Chart
french_subject = AstrologicalSubjectFactory.from_birth_data(
    "Jeanne Moreau", 1928, 1, 23, 10, 0, suppress_geonames_warning=True, **golden_place("Paris", "FR")
)
french_chart_data = ChartDataFactory.create_natal_chart_data(french_subject)
french_chart = ChartDrawer(french_chart_data, chart_language="FR")
french_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Spanish Language Chart
spanish_subject = AstrologicalSubjectFactory.from_birth_data(
    "Antonio Banderas", 1960, 8, 10, 12, 0, suppress_geonames_warning=True, **golden_place("Malaga", "ES")
)
spanish_chart_data = ChartDataFactory.create_natal_chart_data(spanish_subject)
spanish_chart = ChartDrawer(spanish_chart_data, chart_language="ES")
spanish_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Portuguese Language Chart
portuguese_subject = AstrologicalSubjectFactory.from_birth_data(
    "Cristiano Ronaldo", 1985, 2, 5, 5, 25, suppress_geonames_warning=True, **golden_place("Funchal", "PT")
)
portuguese_chart_data = ChartDataFactory.create_natal_chart_data(portuguese_subject)
portuguese_chart = ChartDrawer(portuguese_chart_data, chart_language="PT")
portuguese_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Italian Language Chart
italian_subject = AstrologicalSubjectFactory.from_birth_data(
    "Sophia Loren", 1934, 9, 20, 2, 0, suppress_geonames_warning=True, **golden_place("Rome", "IT")
)
italian_chart_data = ChartDataFactory.create_natal_chart_data(italian_subject)
italian_chart = ChartDrawer(italian_chart_data, chart_language="IT")
italian_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Russian Language Chart
russian_subject = AstrologicalSubjectFactory.from_birth_data(
    "Mikhail Bulgakov", 1891, 5, 15, 12, 0, suppress_geonames_warning=True, **golden_place("Kiev", "UA")
)
russian_chart_data = ChartDataFactory.create_natal_chart_data(russian_subject)
russian_chart = ChartDrawer(russian_chart_data, chart_language="RU")
russian_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Turkish Language Chart
turkish_subject = AstrologicalSubjectFactory.from_birth_data(
    "Mehmet Oz", 1960, 6, 11, 12, 0, suppress_geonames_warning=True, **golden_place("Istanbul", "TR")
)
turkish_chart_data = ChartDataFactory.create_natal_chart_data(turkish_subject)
turkish_chart = ChartDrawer(turkish_chart_data, chart_language="TR")
turkish_chart.save_svg(output_path=OUTPUT_DIR_STR)

# German Language Chart
german_subject = AstrologicalSubjectFactory.from_birth_data(
    "Albert Einstein", 1879, 3, 14, 11, 30, suppress_geonames_warning=True, **golden_place("Ulm", "DE")
)
german_chart_data = ChartDataFactory.create_natal_chart_data(german_subject)
german_chart = ChartDrawer(german_chart_data, chart_language="DE")
german_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Hindi Language Chart
hindi_subject = AstrologicalSubjectFactory.from_birth_data(
    "Amitabh Bachchan", 1942, 10, 11, 4, 0, suppress_geonames_warning=True, **golden_place("Allahabad", "IN")
)
hindi_chart_data = ChartDataFactory.create_natal_chart_data(hindi_subject)
hindi_chart = ChartDrawer(hindi_chart_data, chart_language="HI")
hindi_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Kanye West Natal Chart
kanye_west_subject = AstrologicalSubjectFactory.from_birth_data(
    "Kanye", 1977, 6, 8, 8, 45, suppress_geonames_warning=True, **golden_place("Atlanta", "US")
)
kanye_west_chart_data = ChartDataFactory.create_natal_chart_data(kanye_west_subject)
kanye_west_chart = ChartDrawer(kanye_west_chart_data)
kanye_west_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Composite Chart
angelina = AstrologicalSubjectFactory.from_birth_data(
    "Angelina Jolie",
    1975,
    6,
    4,
    9,
    9,
    "Los Angeles",
    "US",
    lng=-118.15,
    lat=34.03,
    tz_str="America/Los_Angeles",
    suppress_geonames_warning=True,
)
brad = AstrologicalSubjectFactory.from_birth_data(
    "Brad Pitt",
    1963,
    12,
    18,
    6,
    31,
    "Shawnee",
    "US",
    lng=-96.56,
    lat=35.20,
    tz_str="America/Chicago",
    suppress_geonames_warning=True,
)

composite_subject_factory = CompositeSubjectFactory(angelina, brad)
composite_subject_model = composite_subject_factory.get_midpoint_composite_subject_model()
composite_chart_data = ChartDataFactory.create_composite_chart_data(composite_subject_model)
composite_chart = ChartDrawer(composite_chart_data)
composite_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Black and White Theme Composite Chart
black_and_white_composite_chart = ChartDrawer(composite_chart_data, theme="black-and-white")
black_and_white_composite_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="Angelina Jolie and Brad Pitt Composite Chart - Black and White Theme - Composite Chart - Classic",
)

## TO IMPLEMENT (Or check)

# Solar Return Charts
#
# Deterministic generation of both Dual Return (Natal + Solar Return)
# and Single Wheel Solar Return charts for testing.
# Uses offline Liverpool coordinates to avoid any network dependency.
return_factory = PlanetaryReturnFactory(
    first,
    lng=-2.9833,
    lat=53.4000,
    tz_str="Europe/London",
    online=False,
)

# Fixed starting date for reproducibility
solar_return = return_factory.next_return_from_iso_formatted_time(
    "2025-01-09T18:30:00+01:00",
    return_type="Solar",
)

# Dual Return (Natal + Solar Return)
dual_return_chart_data = ChartDataFactory.create_return_chart_data(first, solar_return)
dual_return_chart = ChartDrawer(dual_return_chart_data)
dual_return_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Dual Return (Solar) without House Comparison grid
dual_return_chart_no_house_comparison = ChartDrawer(
    dual_return_chart_data,
    show_house_position_comparison=False,
)
dual_return_chart_no_house_comparison.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - DualReturnChart Chart - Solar Return - No House Comparison",
)

# Dual Return (Solar) with House Comparison only
dual_return_chart_house_only = ChartDrawer(
    dual_return_chart_data,
    show_house_position_comparison=True,
    show_cusp_position_comparison=False,
)
dual_return_chart_house_only.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - DualReturnChart Chart - Solar Return - House Comparison Only",
)

# Dual Return (Solar) with Cusp Comparison only
dual_return_chart_cusp_only = ChartDrawer(
    dual_return_chart_data,
    show_house_position_comparison=False,
    show_cusp_position_comparison=True,
)
dual_return_chart_cusp_only.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - DualReturnChart Chart - Solar Return - Cusp Comparison Only",
)

# Dual Return (Solar) with both House and Cusp Comparison grids
dual_return_chart_house_and_cusp = ChartDrawer(
    dual_return_chart_data,
    show_house_position_comparison=True,
    show_cusp_position_comparison=True,
)
dual_return_chart_house_and_cusp.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - DualReturnChart Chart - Solar Return - House and Cusp Comparison",
)

# Black and White Theme Dual Return Chart
black_and_white_dual_return_chart = ChartDrawer(dual_return_chart_data, theme="black-and-white")
black_and_white_dual_return_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Black and White Theme - DualReturnChart Chart - Solar Return - Classic",
)

# Single Wheel Solar Return
single_return_chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
single_return_chart = ChartDrawer(single_return_chart_data)
single_return_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Black and White Theme Single Return Chart
black_and_white_single_return_chart = ChartDrawer(single_return_chart_data, theme="black-and-white")
black_and_white_single_return_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon Solar Return - Black and White Theme - SingleReturnChart Chart - Classic",
)

# Lunar Return Charts
lunar_return = return_factory.next_return_from_iso_formatted_time(
    "2025-01-09T18:30:00+01:00",
    return_type="Lunar",
)

# Dual Return (Natal + Lunar Return)
lunar_dual_return_chart_data = ChartDataFactory.create_return_chart_data(first, lunar_return)
lunar_dual_return_chart = ChartDrawer(lunar_dual_return_chart_data)
lunar_dual_return_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Dual Return (Lunar) without House Comparison grid
lunar_dual_return_chart_no_house_comparison = ChartDrawer(
    lunar_dual_return_chart_data,
    show_house_position_comparison=False,
)
lunar_dual_return_chart_no_house_comparison.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - DualReturnChart Chart - Lunar Return - No House Comparison",
)

# Dual Return (Lunar) with House Comparison only
lunar_dual_return_chart_house_only = ChartDrawer(
    lunar_dual_return_chart_data,
    show_house_position_comparison=True,
    show_cusp_position_comparison=False,
)
lunar_dual_return_chart_house_only.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - DualReturnChart Chart - Lunar Return - House Comparison Only",
)

# Dual Return (Lunar) with Cusp Comparison only
lunar_dual_return_chart_cusp_only = ChartDrawer(
    lunar_dual_return_chart_data,
    show_house_position_comparison=False,
    show_cusp_position_comparison=True,
)
lunar_dual_return_chart_cusp_only.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - DualReturnChart Chart - Lunar Return - Cusp Comparison Only",
)

# Dual Return (Lunar) with both House and Cusp Comparison grids
lunar_dual_return_chart_house_and_cusp = ChartDrawer(
    lunar_dual_return_chart_data,
    show_house_position_comparison=True,
    show_cusp_position_comparison=True,
)
lunar_dual_return_chart_house_and_cusp.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - DualReturnChart Chart - Lunar Return - House and Cusp Comparison",
)

# Single Wheel Lunar Return
lunar_single_return_chart_data = ChartDataFactory.create_single_wheel_return_chart_data(lunar_return)
lunar_single_return_chart = ChartDrawer(lunar_single_return_chart_data)
lunar_single_return_chart.save_svg(output_path=OUTPUT_DIR_STR)

## Transparent Background
transparent_background_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Transparent Background", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
transparent_background_chart_data = ChartDataFactory.create_natal_chart_data(transparent_background_subject)
transparent_background_chart = ChartDrawer(transparent_background_chart_data, transparent_background=True)
transparent_background_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Natal Chart with ALL_ACTIVE_POINTS
all_points_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - All Active Points",
    1940,
    10,
    9,
    18,
    30,
    suppress_geonames_warning=True,
    **golden_place("Liverpool", "GB"),
    active_points=ALL_ACTIVE_POINTS[0:],
)
all_points_chart_data = ChartDataFactory.create_natal_chart_data(
    all_points_subject,
    active_points=ALL_ACTIVE_POINTS,
)
all_points_chart = ChartDrawer(all_points_chart_data)
all_points_chart.save_svg(output_path=OUTPUT_DIR_STR)
all_points_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)
all_points_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Synastry charts with ALL_ACTIVE_POINTS
all_points_second_subject = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney - All Active Points",
    1942,
    6,
    18,
    15,
    30,
    suppress_geonames_warning=True,
    **golden_place("Liverpool", "GB"),
    active_points=ALL_ACTIVE_POINTS[0:],
)
all_points_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(
    all_points_subject,
    all_points_second_subject,
    active_points=ALL_ACTIVE_POINTS,
)
all_points_synastry_chart = ChartDrawer(all_points_synastry_chart_data)
all_points_synastry_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)
all_points_synastry_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Synastry charts with ALL_ACTIVE_POINTS using list and grid layouts
all_points_synastry_chart_list = ChartDrawer(
    all_points_synastry_chart_data,
    double_chart_aspect_grid_type="list",
)
all_points_synastry_chart_list.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - All Active Points - Synastry Chart - List",
)

all_points_synastry_chart_grid = ChartDrawer(
    all_points_synastry_chart_data,
    double_chart_aspect_grid_type="table",
)
all_points_synastry_chart_grid.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - All Active Points - Synastry Chart - Grid",
)

# Natal Chart without Degree Indicators
natal_chart_no_indicators = ChartDrawer(
    natal_chart_data,
    show_degree_indicators=False,
)
natal_chart_no_indicators.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Natal Chart - No Degree Indicators",
)

# Synastry Chart without Degree Indicators
synastry_chart_no_indicators = ChartDrawer(
    synastry_chart_data,
    show_degree_indicators=False,
)
synastry_chart_no_indicators.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Synastry Chart - No Degree Indicators",
)

# Transit Chart without Degree Indicators
transit_chart_no_indicators = ChartDrawer(
    transits_chart_data,
    show_degree_indicators=False,
)
transit_chart_no_indicators.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Transit Chart - No Degree Indicators",
)

# ============================================================================
# NEW EXTENDED CHART GENERATIONS - Added for comprehensive test coverage
# ============================================================================

# ----------------------------------------------------------------------------
# Section 2: Sidereal Modes (Ayanamsa) - Complete Coverage
# These are the 16 additional sidereal modes not previously generated
# ----------------------------------------------------------------------------

# Sidereal Birth Chart (Raman)
raman_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Raman",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="RAMAN",
    suppress_geonames_warning=True,
)
raman_chart_data = ChartDataFactory.create_natal_chart_data(raman_subject)
ChartDrawer(raman_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (Ushashashi)
ushashashi_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Ushashashi",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="USHASHASHI",
    suppress_geonames_warning=True,
)
ushashashi_chart_data = ChartDataFactory.create_natal_chart_data(ushashashi_subject)
ChartDrawer(ushashashi_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (Krishnamurti)
krishnamurti_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Krishnamurti",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="KRISHNAMURTI",
    suppress_geonames_warning=True,
)
krishnamurti_chart_data = ChartDataFactory.create_natal_chart_data(krishnamurti_subject)
ChartDrawer(krishnamurti_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (Djwhal Khul)
djwhal_khul_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Djwhal Khul",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="DJWHAL_KHUL",
    suppress_geonames_warning=True,
)
djwhal_khul_chart_data = ChartDataFactory.create_natal_chart_data(djwhal_khul_subject)
ChartDrawer(djwhal_khul_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (Yukteshwar)
yukteshwar_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Yukteshwar",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="YUKTESHWAR",
    suppress_geonames_warning=True,
)
yukteshwar_chart_data = ChartDataFactory.create_natal_chart_data(yukteshwar_subject)
ChartDrawer(yukteshwar_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (JN Bhasin)
jn_bhasin_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon JN Bhasin",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="JN_BHASIN",
    suppress_geonames_warning=True,
)
jn_bhasin_chart_data = ChartDataFactory.create_natal_chart_data(jn_bhasin_subject)
ChartDrawer(jn_bhasin_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (Babyl Kugler1)
babyl_kugler1_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Babyl Kugler1",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="BABYL_KUGLER1",
    suppress_geonames_warning=True,
)
babyl_kugler1_chart_data = ChartDataFactory.create_natal_chart_data(babyl_kugler1_subject)
ChartDrawer(babyl_kugler1_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (Babyl Kugler2)
babyl_kugler2_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Babyl Kugler2",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="BABYL_KUGLER2",
    suppress_geonames_warning=True,
)
babyl_kugler2_chart_data = ChartDataFactory.create_natal_chart_data(babyl_kugler2_subject)
ChartDrawer(babyl_kugler2_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (Babyl Kugler3)
babyl_kugler3_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Babyl Kugler3",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="BABYL_KUGLER3",
    suppress_geonames_warning=True,
)
babyl_kugler3_chart_data = ChartDataFactory.create_natal_chart_data(babyl_kugler3_subject)
ChartDrawer(babyl_kugler3_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (Babyl Huber)
babyl_huber_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Babyl Huber",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="BABYL_HUBER",
    suppress_geonames_warning=True,
)
babyl_huber_chart_data = ChartDataFactory.create_natal_chart_data(babyl_huber_subject)
ChartDrawer(babyl_huber_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (Babyl Etpsc)
babyl_etpsc_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Babyl Etpsc",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="BABYL_ETPSC",
    suppress_geonames_warning=True,
)
babyl_etpsc_chart_data = ChartDataFactory.create_natal_chart_data(babyl_etpsc_subject)
ChartDrawer(babyl_etpsc_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (Aldebaran 15Tau)
aldebaran_15tau_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Aldebaran 15Tau",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="ALDEBARAN_15TAU",
    suppress_geonames_warning=True,
)
aldebaran_15tau_chart_data = ChartDataFactory.create_natal_chart_data(aldebaran_15tau_subject)
ChartDrawer(aldebaran_15tau_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (Hipparchos)
hipparchos_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Hipparchos",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="HIPPARCHOS",
    suppress_geonames_warning=True,
)
hipparchos_chart_data = ChartDataFactory.create_natal_chart_data(hipparchos_subject)
ChartDrawer(hipparchos_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (Sassanian)
sassanian_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Sassanian",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="SASSANIAN",
    suppress_geonames_warning=True,
)
sassanian_chart_data = ChartDataFactory.create_natal_chart_data(sassanian_subject)
ChartDrawer(sassanian_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (J1900)
j1900_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon J1900",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="J1900",
    suppress_geonames_warning=True,
)
j1900_chart_data = ChartDataFactory.create_natal_chart_data(j1900_subject)
ChartDrawer(j1900_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (B1950)
b1950_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon B1950",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="B1950",
    suppress_geonames_warning=True,
)
b1950_chart_data = ChartDataFactory.create_natal_chart_data(b1950_subject)
ChartDrawer(b1950_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# ----------------------------------------------------------------------------
# Section 3: House Systems - Complete Coverage (22 additional systems)
# House system M (Morinus) is already generated above
# ----------------------------------------------------------------------------

# House System A (Equal)
equal_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Equal",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="A",
    suppress_geonames_warning=True,
)
equal_house_chart_data = ChartDataFactory.create_natal_chart_data(equal_house_subject)
ChartDrawer(equal_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System B (Alcabitius)
alcabitius_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Alcabitius",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="B",
    suppress_geonames_warning=True,
)
alcabitius_house_chart_data = ChartDataFactory.create_natal_chart_data(alcabitius_house_subject)
ChartDrawer(alcabitius_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System C (Campanus)
campanus_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Campanus",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="C",
    suppress_geonames_warning=True,
)
campanus_house_chart_data = ChartDataFactory.create_natal_chart_data(campanus_house_subject)
ChartDrawer(campanus_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System D (Equal MC)
equal_mc_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Equal MC",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="D",
    suppress_geonames_warning=True,
)
equal_mc_house_chart_data = ChartDataFactory.create_natal_chart_data(equal_mc_house_subject)
ChartDrawer(equal_mc_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System F (Carter poli-equ.)
carter_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Carter",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="F",
    suppress_geonames_warning=True,
)
carter_house_chart_data = ChartDataFactory.create_natal_chart_data(carter_house_subject)
ChartDrawer(carter_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System H (Horizon/azimut)
horizon_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Horizon",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="H",
    suppress_geonames_warning=True,
)
horizon_house_chart_data = ChartDataFactory.create_natal_chart_data(horizon_house_subject)
ChartDrawer(horizon_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System I (Sunshine)
sunshine_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Sunshine",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="I",
    suppress_geonames_warning=True,
)
sunshine_house_chart_data = ChartDataFactory.create_natal_chart_data(sunshine_house_subject)
ChartDrawer(sunshine_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System i (Sunshine/alt.)
sunshine_alt_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Sunshine Alt",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="i",
    suppress_geonames_warning=True,
)
sunshine_alt_house_chart_data = ChartDataFactory.create_natal_chart_data(sunshine_alt_house_subject)
ChartDrawer(sunshine_alt_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System K (Koch)
koch_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Koch",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="K",
    suppress_geonames_warning=True,
)
koch_house_chart_data = ChartDataFactory.create_natal_chart_data(koch_house_subject)
ChartDrawer(koch_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System L (Pullen SD)
pullen_sd_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Pullen SD",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="L",
    suppress_geonames_warning=True,
)
pullen_sd_house_chart_data = ChartDataFactory.create_natal_chart_data(pullen_sd_house_subject)
ChartDrawer(pullen_sd_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System N (Equal/1=Aries)
equal_aries_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Equal Aries",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="N",
    suppress_geonames_warning=True,
)
equal_aries_house_chart_data = ChartDataFactory.create_natal_chart_data(equal_aries_house_subject)
ChartDrawer(equal_aries_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System O (Porphyry)
porphyry_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Porphyry",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="O",
    suppress_geonames_warning=True,
)
porphyry_house_chart_data = ChartDataFactory.create_natal_chart_data(porphyry_house_subject)
ChartDrawer(porphyry_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System P (Placidus - default, but explicit for testing)
placidus_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Placidus",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="P",
    suppress_geonames_warning=True,
)
placidus_house_chart_data = ChartDataFactory.create_natal_chart_data(placidus_house_subject)
ChartDrawer(placidus_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System Q (Pullen SR)
pullen_sr_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Pullen SR",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="Q",
    suppress_geonames_warning=True,
)
pullen_sr_house_chart_data = ChartDataFactory.create_natal_chart_data(pullen_sr_house_subject)
ChartDrawer(pullen_sr_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System R (Regiomontanus)
regiomontanus_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Regiomontanus",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="R",
    suppress_geonames_warning=True,
)
regiomontanus_house_chart_data = ChartDataFactory.create_natal_chart_data(regiomontanus_house_subject)
ChartDrawer(regiomontanus_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System S (Sripati)
sripati_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Sripati",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="S",
    suppress_geonames_warning=True,
)
sripati_house_chart_data = ChartDataFactory.create_natal_chart_data(sripati_house_subject)
ChartDrawer(sripati_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System T (Polich/Page)
polich_page_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Polich Page",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="T",
    suppress_geonames_warning=True,
)
polich_page_house_chart_data = ChartDataFactory.create_natal_chart_data(polich_page_house_subject)
ChartDrawer(polich_page_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System U (Krusinski-Pisa-Goelzer)
krusinski_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Krusinski",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="U",
    suppress_geonames_warning=True,
)
krusinski_house_chart_data = ChartDataFactory.create_natal_chart_data(krusinski_house_subject)
ChartDrawer(krusinski_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System V (Equal/Vehlow)
vehlow_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Vehlow",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="V",
    suppress_geonames_warning=True,
)
vehlow_house_chart_data = ChartDataFactory.create_natal_chart_data(vehlow_house_subject)
ChartDrawer(vehlow_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System W (Equal/Whole Sign)
whole_sign_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Whole Sign",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="W",
    suppress_geonames_warning=True,
)
whole_sign_house_chart_data = ChartDataFactory.create_natal_chart_data(whole_sign_house_subject)
ChartDrawer(whole_sign_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System X (Axial rotation/Meridian)
meridian_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Meridian",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="X",
    suppress_geonames_warning=True,
)
meridian_house_chart_data = ChartDataFactory.create_natal_chart_data(meridian_house_subject)
ChartDrawer(meridian_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# House System Y (APC houses)
apc_house_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System APC",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    houses_system_identifier="Y",
    suppress_geonames_warning=True,
)
apc_house_chart_data = ChartDataFactory.create_natal_chart_data(apc_house_subject)
ChartDrawer(apc_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# ----------------------------------------------------------------------------
# Section 4: Theme + Chart Type Combinations
# ----------------------------------------------------------------------------

# Dark Theme Transit Chart
dark_theme_transit_chart = ChartDrawer(transits_chart_data, theme="dark")
dark_theme_transit_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Dark Theme - Transit Chart - Classic",
)

# Dark Theme Composite Chart
dark_theme_composite_chart = ChartDrawer(composite_chart_data, theme="dark")
dark_theme_composite_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="Angelina Jolie and Brad Pitt Composite Chart - Dark Theme - Composite Chart - Classic",
)

# Black and White Theme External Natal Chart
bw_theme_external_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Black and White Theme External",
    1940,
    10,
    9,
    18,
    30,
    suppress_geonames_warning=True,
    **golden_place("Liverpool", "GB"),
)
bw_theme_external_chart_data = ChartDataFactory.create_natal_chart_data(bw_theme_external_subject)
bw_theme_external_chart = ChartDrawer(bw_theme_external_chart_data, theme="black-and-white", external_view=True)
bw_theme_external_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Black and White Theme Dual Lunar Return Chart
bw_lunar_dual_return_chart = ChartDrawer(lunar_dual_return_chart_data, theme="black-and-white")
bw_lunar_dual_return_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Black and White Theme - DualReturnChart Chart - Lunar Return - Classic",
)

# Black and White Theme Single Lunar Return Chart
bw_lunar_single_return_chart = ChartDrawer(lunar_single_return_chart_data, theme="black-and-white")
bw_lunar_single_return_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon Lunar Return - Black and White Theme - SingleReturnChart Chart - Classic",
)

# ----------------------------------------------------------------------------
# Section 5: Wheel Only + Aspect Grid Only Variations with Themes
# ----------------------------------------------------------------------------

# Wheel Only Dark Theme Natal Chart
wheel_only_dark_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel Only Dark", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
wheel_only_dark_chart_data = ChartDataFactory.create_natal_chart_data(wheel_only_dark_subject)
wheel_only_dark_chart = ChartDrawer(wheel_only_dark_chart_data, theme="dark")
wheel_only_dark_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Synastry Dark Theme
wheel_synastry_dark_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel Synastry Dark", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
wheel_synastry_dark_chart_data = ChartDataFactory.create_synastry_chart_data(wheel_synastry_dark_subject, second)
wheel_synastry_dark_chart = ChartDrawer(wheel_synastry_dark_chart_data, theme="dark")
wheel_synastry_dark_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Transit Dark Theme
wheel_transit_dark_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel Transit Dark", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
wheel_transit_dark_chart_data = ChartDataFactory.create_transit_chart_data(wheel_transit_dark_subject, second)
wheel_transit_dark_chart = ChartDrawer(wheel_transit_dark_chart_data, theme="dark")
wheel_transit_dark_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Black and White Natal
aspect_grid_bw_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid BW", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
aspect_grid_bw_chart_data = ChartDataFactory.create_natal_chart_data(aspect_grid_bw_subject)
aspect_grid_bw_chart = ChartDrawer(aspect_grid_bw_chart_data, theme="black-and-white")
aspect_grid_bw_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Black and White Synastry
aspect_grid_bw_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid BW Synastry", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
aspect_grid_bw_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(
    aspect_grid_bw_synastry_subject, second
)
aspect_grid_bw_synastry_chart = ChartDrawer(aspect_grid_bw_synastry_chart_data, theme="black-and-white")
aspect_grid_bw_synastry_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Black and White Transit
aspect_grid_bw_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid BW Transit", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
aspect_grid_bw_transit_chart_data = ChartDataFactory.create_transit_chart_data(aspect_grid_bw_transit_subject, second)
aspect_grid_bw_transit_chart = ChartDrawer(aspect_grid_bw_transit_chart_data, theme="black-and-white")
aspect_grid_bw_transit_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Dark Transit
aspect_grid_dark_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid Dark Transit", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
aspect_grid_dark_transit_chart_data = ChartDataFactory.create_transit_chart_data(
    aspect_grid_dark_transit_subject, second
)
aspect_grid_dark_transit_chart = ChartDrawer(aspect_grid_dark_transit_chart_data, theme="dark")
aspect_grid_dark_transit_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# ----------------------------------------------------------------------------
# Section 6: Composite Chart Variations
# ----------------------------------------------------------------------------

# Composite Chart Wheel Only
composite_chart_wheel_only = ChartDrawer(composite_chart_data)
composite_chart_wheel_only.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Composite Chart Aspect Grid Only
composite_chart_aspect_grid_only = ChartDrawer(composite_chart_data)
composite_chart_aspect_grid_only.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# ----------------------------------------------------------------------------
# Section 7: ChartDrawer Advanced Options
# ----------------------------------------------------------------------------

# Custom Title Natal Chart
custom_title_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Custom Title", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
custom_title_chart_data = ChartDataFactory.create_natal_chart_data(custom_title_subject)
custom_title_chart = ChartDrawer(custom_title_chart_data, custom_title="My Custom Chart Title")
custom_title_chart.save_svg(output_path=OUTPUT_DIR_STR)

# No Aspect Icons Natal Chart
no_aspect_icons_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - No Aspect Icons", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
no_aspect_icons_chart_data = ChartDataFactory.create_natal_chart_data(no_aspect_icons_subject)
no_aspect_icons_chart = ChartDrawer(no_aspect_icons_chart_data, show_aspect_icons=False)
no_aspect_icons_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Auto Size False Natal Chart
auto_size_false_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Auto Size False", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
auto_size_false_chart_data = ChartDataFactory.create_natal_chart_data(auto_size_false_subject)
auto_size_false_chart = ChartDrawer(auto_size_false_chart_data, auto_size=False)
auto_size_false_chart.save_svg(output_path=OUTPUT_DIR_STR)

# No CSS Variables Natal Chart (remove_css_variables=True is used in generate_svg_string)
no_css_vars_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - No CSS Variables", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
no_css_vars_chart_data = ChartDataFactory.create_natal_chart_data(no_css_vars_subject)
no_css_vars_chart = ChartDrawer(no_css_vars_chart_data)
no_css_vars_chart.save_svg(output_path=OUTPUT_DIR_STR, remove_css_variables=True)

# Custom Padding Natal Chart
custom_padding_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Custom Padding", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
custom_padding_chart_data = ChartDataFactory.create_natal_chart_data(custom_padding_subject)
custom_padding_chart = ChartDrawer(custom_padding_chart_data, padding=50)
custom_padding_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Transit Chart with ALL_ACTIVE_POINTS
all_points_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - All Active Points Transit",
    1940,
    10,
    9,
    18,
    30,
    suppress_geonames_warning=True,
    **golden_place("Liverpool", "GB"),
    active_points=ALL_ACTIVE_POINTS,
)
all_points_transit_second_subject = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney - All Active Points Transit",
    1942,
    6,
    18,
    15,
    30,
    suppress_geonames_warning=True,
    **golden_place("Liverpool", "GB"),
    active_points=ALL_ACTIVE_POINTS,
)
all_points_transit_chart_data = ChartDataFactory.create_transit_chart_data(
    all_points_transit_subject,
    all_points_transit_second_subject,
    active_points=ALL_ACTIVE_POINTS,
)
all_points_transit_chart = ChartDrawer(all_points_transit_chart_data)
all_points_transit_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - All Active Points - Transit Chart - Classic",
)

# Solar Return Chart Wheel Only
solar_return_wheel_only_chart = ChartDrawer(single_return_chart_data)
solar_return_wheel_only_chart.save_wheel_only_svg_file(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon Solar Return - Classic Wheel Only",
)

# Solar Return Chart Aspect Grid Only
solar_return_aspect_grid_only_chart = ChartDrawer(single_return_chart_data)
solar_return_aspect_grid_only_chart.save_aspect_grid_only_svg_file(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon Solar Return - Aspect Grid Only",
)

# ----------------------------------------------------------------------------
# Section 8: Multi-Language Chart Types
# English is tested as default, but explicit for completeness
# ----------------------------------------------------------------------------

# English Natal Chart (explicit)
english_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - EN", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
english_chart_data = ChartDataFactory.create_natal_chart_data(english_subject)
english_chart = ChartDrawer(english_chart_data, chart_language="EN")
english_chart.save_svg(output_path=OUTPUT_DIR_STR)

# French Synastry Chart
french_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - FR", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
french_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(french_synastry_subject, second)
french_synastry_chart = ChartDrawer(french_synastry_chart_data, chart_language="FR")
french_synastry_chart.save_svg(output_path=OUTPUT_DIR_STR)

# German Synastry Chart
german_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - DE", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
german_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(german_synastry_subject, second)
german_synastry_chart = ChartDrawer(german_synastry_chart_data, chart_language="DE")
german_synastry_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Chinese Transit Chart
chinese_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - CN", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
chinese_transit_chart_data = ChartDataFactory.create_transit_chart_data(chinese_transit_subject, second)
chinese_transit_chart = ChartDrawer(chinese_transit_chart_data, chart_language="CN")
chinese_transit_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Spanish Transit Chart
spanish_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - ES", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
spanish_transit_chart_data = ChartDataFactory.create_transit_chart_data(spanish_transit_subject, second)
spanish_transit_chart = ChartDrawer(spanish_transit_chart_data, chart_language="ES")
spanish_transit_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Italian Composite Chart
italian_composite_chart = ChartDrawer(composite_chart_data, chart_language="IT")
italian_composite_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="Angelina Jolie and Brad Pitt Composite Chart - IT - Composite Chart - Classic",
)

# Portuguese Composite Chart
portuguese_composite_chart = ChartDrawer(composite_chart_data, chart_language="PT")
portuguese_composite_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="Angelina Jolie and Brad Pitt Composite Chart - PT - Composite Chart - Classic",
)

# Russian Transit Chart
russian_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - RU", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
russian_transit_chart_data = ChartDataFactory.create_transit_chart_data(russian_transit_subject, second)
russian_transit_chart = ChartDrawer(russian_transit_chart_data, chart_language="RU")
russian_transit_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Turkish Synastry Chart
turkish_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - TR", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
turkish_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(turkish_synastry_subject, second)
turkish_synastry_chart = ChartDrawer(turkish_synastry_chart_data, chart_language="TR")
turkish_synastry_chart.save_svg(output_path=OUTPUT_DIR_STR)

# ----------------------------------------------------------------------------
# Section 9: Perspective Types with Different Charts
# ----------------------------------------------------------------------------

# Heliocentric Synastry Chart
heliocentric_synastry_first = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Heliocentric Synastry",
    1940,
    10,
    9,
    18,
    30,
    suppress_geonames_warning=True,
    **golden_place("Liverpool", "GB"),
    perspective_type="Heliocentric",
)
heliocentric_synastry_second = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney - Heliocentric",
    1942,
    6,
    18,
    15,
    30,
    suppress_geonames_warning=True,
    **golden_place("Liverpool", "GB"),
    perspective_type="Heliocentric",
)
heliocentric_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(
    heliocentric_synastry_first, heliocentric_synastry_second
)
heliocentric_synastry_chart = ChartDrawer(heliocentric_synastry_chart_data)
heliocentric_synastry_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Heliocentric - Synastry Chart - Classic",
)

# Topocentric Transit Chart
topocentric_transit_first = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Topocentric Transit",
    1940,
    10,
    9,
    18,
    30,
    suppress_geonames_warning=True,
    **golden_place("Liverpool", "GB"),
    perspective_type="Topocentric",
)
topocentric_transit_second = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney - Topocentric",
    1942,
    6,
    18,
    15,
    30,
    suppress_geonames_warning=True,
    **golden_place("Liverpool", "GB"),
    perspective_type="Topocentric",
)
topocentric_transit_chart_data = ChartDataFactory.create_transit_chart_data(
    topocentric_transit_first, topocentric_transit_second
)
topocentric_transit_chart = ChartDrawer(topocentric_transit_chart_data)
topocentric_transit_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Topocentric - Transit Chart - Classic",
)

# True Geocentric Synastry Chart
true_geocentric_synastry_first = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - True Geocentric Synastry",
    1940,
    10,
    9,
    18,
    30,
    suppress_geonames_warning=True,
    **golden_place("Liverpool", "GB"),
    perspective_type="True Geocentric",
)
true_geocentric_synastry_second = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney - True Geocentric",
    1942,
    6,
    18,
    15,
    30,
    suppress_geonames_warning=True,
    **golden_place("Liverpool", "GB"),
    perspective_type="True Geocentric",
)
true_geocentric_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(
    true_geocentric_synastry_first, true_geocentric_synastry_second
)
true_geocentric_synastry_chart = ChartDrawer(true_geocentric_synastry_chart_data)
true_geocentric_synastry_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - True Geocentric - Synastry Chart - Classic",
)

# ----------------------------------------------------------------------------
# Section 10: Relationship Score Tests
# ----------------------------------------------------------------------------

# Synastry Chart with Relationship Score.
#
# BOTH switches, and they are not the same switch: include_relationship_score
# puts the score in the chart DATA, show_relationship_score puts it on the panel.
# This chart carried only the first, so the file named for the relationship score
# was drawn with two empty text nodes where the score belongs — and a second block
# further down wrote a DIFFERENT chart to the same filename and overwrote it, which
# is the only reason the stored baseline showed a score at all. One chart, one
# filename, and the name now describes what is in it.
relationship_score_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(
    first,
    second,
    include_relationship_score=True,
)
relationship_score_synastry_chart = ChartDrawer(
    relationship_score_synastry_chart_data, show_relationship_score=True
)
relationship_score_synastry_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Relationship Score - Synastry Chart - Classic",
)

# ----------------------------------------------------------------------------
# Section 11: Untested Parameters
# ----------------------------------------------------------------------------

# theme=None (no CSS theme)
theme_none_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - No Theme", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
theme_none_chart_data = ChartDataFactory.create_natal_chart_data(theme_none_subject)
theme_none_chart = ChartDrawer(theme_none_chart_data, theme=None)
theme_none_chart.save_svg(output_path=OUTPUT_DIR_STR)

# show_degree_indicators=False
no_degree_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - No Degree Indicators", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
no_degree_chart_data = ChartDataFactory.create_natal_chart_data(no_degree_subject)
no_degree_chart = ChartDrawer(no_degree_chart_data, show_degree_indicators=False)
no_degree_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Custom colors_settings
from kerykeion.settings.chart_defaults import (
    DEFAULT_CHART_COLORS,
    DEFAULT_CHART_ASPECTS_SETTINGS,
    DEFAULT_CELESTIAL_POINTS_SETTINGS,
)
import copy

custom_colors = DEFAULT_CHART_COLORS.copy()
custom_colors["paper_0"] = "#ff0000"
custom_colors["paper_1"] = "#00ff00"
custom_colors_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Custom Colors", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
custom_colors_chart_data = ChartDataFactory.create_natal_chart_data(custom_colors_subject)
custom_colors_chart = ChartDrawer(custom_colors_chart_data, colors_settings=custom_colors)
custom_colors_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Custom aspects_settings (custom colors)
custom_aspects = copy.deepcopy(DEFAULT_CHART_ASPECTS_SETTINGS)
for aspect in custom_aspects:
    if aspect["name"] == "conjunction":
        aspect["color"] = "#FF0000"  # Red
    elif aspect["name"] == "opposition":
        aspect["color"] = "#0000FF"  # Blue
custom_aspects_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Custom Aspect Colors", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
custom_aspects_chart_data = ChartDataFactory.create_natal_chart_data(custom_aspects_subject)
custom_aspects_chart = ChartDrawer(custom_aspects_chart_data, aspects_settings=custom_aspects)
custom_aspects_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Custom celestial_points_settings
custom_points = copy.deepcopy(DEFAULT_CELESTIAL_POINTS_SETTINGS)
for point in custom_points:
    if point["name"] == "Sun":
        point["color"] = "#FFD700"
    elif point["name"] == "Moon":
        point["color"] = "#C0C0C0"
custom_points_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Custom Planet Colors", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
custom_points_chart_data = ChartDataFactory.create_natal_chart_data(custom_points_subject)
custom_points_chart = ChartDrawer(custom_points_chart_data, celestial_points_settings=custom_points)
custom_points_chart.save_svg(output_path=OUTPUT_DIR_STR)

# language_pack override
language_pack_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Language Pack", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
language_pack_chart_data = ChartDataFactory.create_natal_chart_data(language_pack_subject)
language_pack_chart = ChartDrawer(
    language_pack_chart_data, chart_language="IT", language_pack={"Sun": "Sole Custom", "Moon": "Luna Custom"}
)
language_pack_chart.save_svg(output_path=OUTPUT_DIR_STR)

# ----------------------------------------------------------------------------
# Section 12: Parameter Combinations
# ----------------------------------------------------------------------------

# Transparent + Dark theme
transparent_dark_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Transparent Dark", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
transparent_dark_chart_data = ChartDataFactory.create_natal_chart_data(transparent_dark_subject)
transparent_dark_chart = ChartDrawer(transparent_dark_chart_data, theme="dark", transparent_background=True)
transparent_dark_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Transparent Synastry
transparent_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Transparent Synastry", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
transparent_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(transparent_synastry_subject, second)
transparent_synastry_chart = ChartDrawer(transparent_synastry_chart_data, transparent_background=True)
transparent_synastry_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Custom title synastry
custom_title_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Custom Title Synastry", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
custom_title_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(custom_title_synastry_subject, second)
custom_title_synastry_chart = ChartDrawer(custom_title_synastry_chart_data, custom_title="Beatles Synastry Analysis")
custom_title_synastry_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Custom title transit
custom_title_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Custom Title Transit", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
custom_title_transit_chart_data = ChartDataFactory.create_transit_chart_data(custom_title_transit_subject, second)
custom_title_transit_chart = ChartDrawer(custom_title_transit_chart_data, custom_title="Transit Analysis 2024")
custom_title_transit_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Zero padding
zero_padding_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Zero Padding", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
zero_padding_chart_data = ChartDataFactory.create_natal_chart_data(zero_padding_subject)
zero_padding_chart = ChartDrawer(zero_padding_chart_data, padding=0)
zero_padding_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Large padding (100px)
large_padding_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Large Padding", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
large_padding_chart_data = ChartDataFactory.create_natal_chart_data(large_padding_subject)
large_padding_chart = ChartDrawer(large_padding_chart_data, padding=100)
large_padding_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Minify + remove CSS variables combined
minify_css_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Minify CSS", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
minify_css_chart_data = ChartDataFactory.create_natal_chart_data(minify_css_subject)
minify_css_chart = ChartDrawer(minify_css_chart_data)
minify_css_svg = minify_css_chart.generate_svg_string(minify=True, remove_css_variables=True)
(OUTPUT_DIR / "John Lennon - Minify CSS - Natal Chart - Classic.svg").write_text(minify_css_svg, encoding="utf-8")

# ----------------------------------------------------------------------------
# Section 13: Edge Cases
# ----------------------------------------------------------------------------

# Very long name
long_name_subject = AstrologicalSubjectFactory.from_birth_data(
    "A" * 100, 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
long_name_chart_data = ChartDataFactory.create_natal_chart_data(long_name_subject)
long_name_chart = ChartDrawer(long_name_chart_data)
long_name_chart.save_svg(output_path=OUTPUT_DIR_STR, filename="Long Name - Natal Chart - Classic")

# Extreme latitude north (Arctic)
arctic_subject = AstrologicalSubjectFactory.from_birth_data(
    "Arctic Subject",
    1990,
    6,
    21,
    12,
    0,
    "Longyearbyen",
    "NO",
    lat=78.22,
    lng=15.65,
    tz_str="Arctic/Longyearbyen",
    suppress_geonames_warning=True,
)
arctic_chart_data = ChartDataFactory.create_natal_chart_data(arctic_subject)
arctic_chart = ChartDrawer(arctic_chart_data)
arctic_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Extreme latitude south (Antarctica)
antarctic_subject = AstrologicalSubjectFactory.from_birth_data(
    "Antarctic Subject",
    1990,
    12,
    21,
    12,
    0,
    "McMurdo Station",
    "AQ",
    lat=-77.85,
    lng=166.67,
    tz_str="Antarctica/McMurdo",
    suppress_geonames_warning=True,
)
antarctic_chart_data = ChartDataFactory.create_natal_chart_data(antarctic_subject)
antarctic_chart = ChartDrawer(antarctic_chart_data)
antarctic_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Historical date (1500) — outside short ephemeris kernels (needs DE441-range
# data); skip with a notice instead of aborting the whole regeneration, the
# same way regenerate_test_charts_extended.py handles its ancient subjects.
# The corresponding test (test_historical_date) auto-skips on short kernels,
# so a stale baseline is harmless there.
try:
    historical_subject = AstrologicalSubjectFactory.from_birth_data(
        "Historical Subject", 1500, 3, 15, 12, 0, suppress_geonames_warning=True, **golden_place("Florence", "IT")
    )
    historical_chart_data = ChartDataFactory.create_natal_chart_data(historical_subject)
    historical_chart = ChartDrawer(historical_chart_data)
    historical_chart.save_svg(output_path=OUTPUT_DIR_STR)
except KerykeionException as e:
    # Out-of-range dates fail loudly with KerykeionException (the luminaries
    # cannot be computed on a short kernel) — that is the expected skip. Any
    # other exception is a real regeneration bug and must not be masked into a
    # stale baseline, so it propagates.
    print(f"  ERROR generating Historical Subject (baseline kept stale): {e}")

# Future date (2100)
future_subject = AstrologicalSubjectFactory.from_birth_data(
    "Future Subject", 2100, 7, 4, 12, 0, suppress_geonames_warning=True, **golden_place("New York", "US")
)
future_chart_data = ChartDataFactory.create_natal_chart_data(future_subject)
future_chart = ChartDrawer(future_chart_data)
future_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Date line crossing (Fiji)
dateline_subject = AstrologicalSubjectFactory.from_birth_data(
    "Date Line Subject",
    1990,
    1,
    1,
    12,
    0,
    "Suva",
    "FJ",
    lat=-18.14,
    lng=178.44,
    tz_str="Pacific/Fiji",
    suppress_geonames_warning=True,
)
dateline_chart_data = ChartDataFactory.create_natal_chart_data(dateline_subject)
dateline_chart = ChartDrawer(dateline_chart_data)
dateline_chart.save_svg(output_path=OUTPUT_DIR_STR)

# ============================================================================
# Section 14: Modern Chart Style
# ============================================================================

# Modern Natal Chart (default theme)
modern_natal_chart = ChartDrawer(natal_chart_data)
modern_natal_chart.save_svg(output_path=OUTPUT_DIR_STR, style="modern")

# Modern Natal Chart - Dark Theme
dark_theme_modern_natal = ChartDrawer(dark_theme_natal_chart_data, theme="dark")
dark_theme_modern_natal.save_svg(output_path=OUTPUT_DIR_STR, style="modern")

# Modern Natal Chart - Black and White Theme
bw_modern_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Black and White Theme", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
bw_modern_natal_data = ChartDataFactory.create_natal_chart_data(bw_modern_subject)
bw_modern_natal = ChartDrawer(bw_modern_natal_data, theme="black-and-white")
bw_modern_natal.save_svg(output_path=OUTPUT_DIR_STR, style="modern")

# Modern Synastry Chart
modern_synastry = ChartDrawer(synastry_chart_data)
modern_synastry.save_svg(output_path=OUTPUT_DIR_STR, style="modern")

# Modern Synastry Chart - Dark Theme
dark_theme_modern_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Dark Theme Synastry", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
dark_theme_modern_synastry_data = ChartDataFactory.create_synastry_chart_data(
    dark_theme_modern_synastry_subject, second
)
dark_theme_modern_synastry = ChartDrawer(dark_theme_modern_synastry_data, theme="dark")
dark_theme_modern_synastry.save_svg(output_path=OUTPUT_DIR_STR, style="modern")

# Modern Transit Chart
modern_transit = ChartDrawer(transits_chart_data)
modern_transit.save_svg(output_path=OUTPUT_DIR_STR, style="modern")

# Modern Transit Chart - Dark Theme
dark_theme_modern_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Dark Theme Transit", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
dark_theme_modern_transit_data = ChartDataFactory.create_transit_chart_data(dark_theme_modern_transit_subject, second)
dark_theme_modern_transit = ChartDrawer(dark_theme_modern_transit_data, theme="dark")
dark_theme_modern_transit.save_svg(output_path=OUTPUT_DIR_STR, style="modern")

# Modern Composite Chart
modern_composite = ChartDrawer(composite_chart_data)
modern_composite.save_svg(output_path=OUTPUT_DIR_STR, style="modern")

# Modern Wheel Only Natal Chart (default theme)
modern_wheel_only = ChartDrawer(natal_chart_data)
modern_wheel_only.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR, style="modern")

# Modern Wheel Only Natal Chart - Dark Theme
dark_modern_wheel_only = ChartDrawer(dark_theme_natal_chart_data, theme="dark")
dark_modern_wheel_only.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR, style="modern")

# Modern Wheel Only Synastry Chart
modern_wheel_synastry = ChartDrawer(synastry_chart_data)
modern_wheel_synastry.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR, style="modern")

# Modern Wheel Only Transit Chart
modern_wheel_transit = ChartDrawer(transits_chart_data)
modern_wheel_transit.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR, style="modern")

# Modern Single Return Solar Chart
modern_single_return = ChartDrawer(single_return_chart_data)
modern_single_return.save_svg(output_path=OUTPUT_DIR_STR, style="modern")

# Modern Dual Return Solar Chart
modern_dual_return = ChartDrawer(dual_return_chart_data)
modern_dual_return.save_svg(output_path=OUTPUT_DIR_STR, style="modern")

# ---------------------------------------------------------------------------
# Opt-in chart marks (classic style)
#
# Each subject is chosen so the mark has a real referent: a chart with nothing
# to mark would pin an empty promise. The suffix in the subject name is what
# names the baseline file, as everywhere else in this script.
# ---------------------------------------------------------------------------

# show_motion_state — Mercury turns retrograde on this date
station_subject = AstrologicalSubjectFactory.from_birth_data(
    "Mercury Station - Motion State", 1990, 8, 25, 12, 0, suppress_geonames_warning=True, **golden_place("London", "GB")
)
station_chart_data = ChartDataFactory.create_natal_chart_data(station_subject)
ChartDrawer(station_chart_data, show_motion_state=True).save_svg(output_path=OUTPUT_DIR_STR)

# show_aspect_movement — same sky, separating aspects dashed
movement_subject = AstrologicalSubjectFactory.from_birth_data(
    "Mercury Station - Aspect Movement", 1990, 8, 25, 12, 0, suppress_geonames_warning=True, **golden_place("London", "GB")
)
movement_chart_data = ChartDataFactory.create_natal_chart_data(movement_subject)
ChartDrawer(movement_chart_data, show_aspect_movement=True).save_svg(output_path=OUTPUT_DIR_STR)

# show_out_of_bounds — Uranus sits past the obliquity here
oob_subject = AstrologicalSubjectFactory.from_birth_data(
    "Out Of Bounds", 1990, 1, 1, 12, 0, suppress_geonames_warning=True, **golden_place("London", "GB")
)
oob_chart_data = ChartDataFactory.create_natal_chart_data(oob_subject)
ChartDrawer(oob_chart_data, show_out_of_bounds=True).save_svg(output_path=OUTPUT_DIR_STR)

# show_relationship_score is covered by the Section 10 chart above. It used to be
# covered here too, by a subject NAMED "John Lennon - Relationship Score" — and
# save_svg builds its default filename from the subject's name, so this wrote to
# the same file as Section 10 and silently won. Two charts, one filename, and the
# comparison test reproduced the loser.

# show_ayanamsa_value — the offset in degrees on a sidereal chart
ayanamsa_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Ayanamsa Value",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
    suppress_geonames_warning=True,
)
ayanamsa_chart_data = ChartDataFactory.create_natal_chart_data(ayanamsa_subject)
ChartDrawer(ayanamsa_chart_data, show_ayanamsa_value=True).save_svg(output_path=OUTPUT_DIR_STR)

# show_polar_fallback_note — Placidus is undefined this far north
polar_subject = AstrologicalSubjectFactory.from_birth_data(
    "Polar Fallback",
    1990,
    6,
    15,
    12,
    0,
    "Longyearbyen",
    "SJ",
    lng=15.6,
    lat=78.2,
    tz_str="Arctic/Longyearbyen",
    houses_system_identifier="P",
    suppress_geonames_warning=True,
)
polar_chart_data = ChartDataFactory.create_natal_chart_data(polar_subject)
ChartDrawer(polar_chart_data, show_polar_fallback_note=True).save_svg(output_path=OUTPUT_DIR_STR)

# ---------------------------------------------------------------------------
# Complete charts with every mark switched on
#
# The six baselines above each isolate one mark, which is what a regression on
# that mark needs. These four are the other half of the picture: whole charts
# rendered the way someone who turns the feature on actually sees them, with
# every option enabled at once. A mark stays silent where its subject has no
# referent, so between them these carry the full set without any one of them
# claiming something its own sky does not have.
# ---------------------------------------------------------------------------

ALL_MARKS_ON = dict(
    show_motion_state=True,
    show_out_of_bounds=True,
    show_aspect_movement=True,
    show_relationship_score=True,
    show_ayanamsa_value=True,
    show_polar_fallback_note=True,
)

# Station, out-of-bounds body and separating aspects, in both styles.
all_marks_subject = AstrologicalSubjectFactory.from_birth_data(
    "Mercury Station - All Marks", 1990, 8, 25, 12, 0, suppress_geonames_warning=True, **golden_place("London", "GB")
)
all_marks_chart_data = ChartDataFactory.create_natal_chart_data(all_marks_subject)
ChartDrawer(all_marks_chart_data, **ALL_MARKS_ON).save_svg(output_path=OUTPUT_DIR_STR)
ChartDrawer(all_marks_chart_data, **ALL_MARKS_ON).save_svg(output_path=OUTPUT_DIR_STR, style="modern")

# Sidereal: the ayanamsa offset joins the marks that the sky supports.
all_marks_sidereal = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - All Marks Sidereal",
    1940,
    10,
    9,
    18,
    30,
    **golden_place("Liverpool", "GB"),
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
    suppress_geonames_warning=True,
)
ChartDrawer(
    ChartDataFactory.create_natal_chart_data(all_marks_sidereal), **ALL_MARKS_ON
).save_svg(output_path=OUTPUT_DIR_STR)

# Polar: the domification line admits the substitution.
all_marks_polar = AstrologicalSubjectFactory.from_birth_data(
    "Polar Fallback - All Marks",
    1990,
    6,
    15,
    12,
    0,
    "Longyearbyen",
    "SJ",
    lng=15.6,
    lat=78.2,
    tz_str="Arctic/Longyearbyen",
    houses_system_identifier="P",
    suppress_geonames_warning=True,
)
ChartDrawer(
    ChartDataFactory.create_natal_chart_data(all_marks_polar), **ALL_MARKS_ON
).save_svg(output_path=OUTPUT_DIR_STR)

# Synastry: the score, on a dual wheel that also carries wheel marks.
all_marks_syn_first = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - All Marks Synastry", 1940, 10, 9, 18, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
all_marks_syn_second = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney", 1942, 6, 18, 15, 30, suppress_geonames_warning=True, **golden_place("Liverpool", "GB")
)
all_marks_syn_data = ChartDataFactory.create_synastry_chart_data(all_marks_syn_first, all_marks_syn_second)
ChartDrawer(all_marks_syn_data, **ALL_MARKS_ON).save_svg(output_path=OUTPUT_DIR_STR)
ChartDrawer(all_marks_syn_data, **ALL_MARKS_ON).save_svg(output_path=OUTPUT_DIR_STR, style="modern")

# Three plain natal baselines that had been committed without a generator. No
# test read them and no script wrote them, so they quietly kept a picture of an
# older library — they were still drawing the font-traced Jupiter six commits
# after it was redrawn. The birth data below is read straight off the panels of
# the files they replace, so these regenerate what was there rather than
# redefining it.
for _name, _y, _m, _d, _hh, _mm, _city, _nation in (
    ("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US"),
    ("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB"),
    ("Yoko Ono", 1933, 2, 18, 20, 30, "Tokyo", "JP"),
):
    _subject = AstrologicalSubjectFactory.from_birth_data(
        _name, _y, _m, _d, _hh, _mm, suppress_geonames_warning=True,
        **golden_place(_city, _nation),
    )
    ChartDrawer(ChartDataFactory.create_natal_chart_data(_subject)).save_svg(output_path=OUTPUT_DIR_STR)

print("All charts regenerated successfully!")
