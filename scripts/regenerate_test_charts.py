#!/usr/bin/env python3
"""
Regenerate test chart SVGs in tests/charts/svg folder

This script creates all types of SVG charts used in tests:
- Natal charts with various configurations (sidereal, house systems, perspectives)
- External natal charts (using external_view parameter)
- Synastry charts
- Transit charts
- Wheel-only charts
- Aspect-grid-only charts
- Charts with different themes (dark, light, high-contrast)
- Multilingual charts
- Composite charts
- Charts with transparent background

All files are saved to tests/charts/svg/ with geonames authentication included.
"""

from pathlib import Path
from kerykeion.composite_subject_factory import CompositeSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion.charts.charts_utils import makeLunarPhase
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

# Set output directory for all chart SVGs
OUTPUT_DIR = Path(__file__).parent.parent / "tests" / "charts" / "svg"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR_STR = str(OUTPUT_DIR)


def regenerate_lunar_phase_reference_sheet() -> None:
    """Regenerate the reference SVG used by TestLunarPhaseSVG."""
    phase_angles = (0, 45, 90, 135, 180, 225, 270, 315)
    icon_groups: list[str] = []

    for index, angle in enumerate(phase_angles):
        icon_svg = makeLunarPhase(angle, 0.0)
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
    "John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
second = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB", suppress_geonames_warning=True
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
    filename="John Lennon - Black and White Theme - Natal Chart",
)

# External Natal Chart (using external_view parameter)
external_natal_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - ExternalNatal", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
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
    filename="John Lennon - Black and White Theme - Synastry Chart",
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
    filename="John Lennon - Black and White Theme - Transit Chart",
)

# Sidereal Birth Chart (Lahiri)
sidereal_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Lahiri",
    1940,
    10,
    9,
    18,
    30,
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
    perspective_type="Topocentric",
    suppress_geonames_warning=True,
)
topocentric_chart_data = ChartDataFactory.create_natal_chart_data(topocentric_subject)
topocentric_chart = ChartDrawer(topocentric_chart_data)
topocentric_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Minified SVG
minified_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Minified", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
minified_chart_data = ChartDataFactory.create_natal_chart_data(minified_subject)
minified_chart = ChartDrawer(minified_chart_data)
minified_chart.save_svg(output_path=OUTPUT_DIR_STR, minify=True)

# Dark Theme Natal Chart
dark_theme_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
dark_theme_natal_chart_data = ChartDataFactory.create_natal_chart_data(dark_theme_subject)
dark_theme_natal_chart = ChartDrawer(dark_theme_natal_chart_data, theme="dark")
dark_theme_natal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Dark High Contrast Theme Natal Chart
dark_high_contrast_theme_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Dark High Contrast Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
dark_high_contrast_theme_natal_chart_data = ChartDataFactory.create_natal_chart_data(dark_high_contrast_theme_subject)
dark_high_contrast_theme_natal_chart = ChartDrawer(
    dark_high_contrast_theme_natal_chart_data, theme="dark-high-contrast"
)
dark_high_contrast_theme_natal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Light Theme Natal Chart
light_theme_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
light_theme_natal_chart_data = ChartDataFactory.create_natal_chart_data(light_theme_subject)
light_theme_natal_chart = ChartDrawer(light_theme_natal_chart_data, theme="light")
light_theme_natal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Dark Theme External Natal Chart
dark_theme_external_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Dark Theme External", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
dark_theme_external_chart_data = ChartDataFactory.create_natal_chart_data(dark_theme_external_subject)
dark_theme_external_chart = ChartDrawer(dark_theme_external_chart_data, theme="dark", external_view=True)
dark_theme_external_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Dark Theme Synastry Chart
dark_theme_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - DTS", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
dark_theme_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(dark_theme_synastry_subject, second)
dark_theme_synastry_chart = ChartDrawer(dark_theme_synastry_chart_data, theme="dark")
dark_theme_synastry_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Wheel Natal Only Chart
wheel_only_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel Only", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
wheel_only_chart_data = ChartDataFactory.create_natal_chart_data(wheel_only_subject)
wheel_only_chart = ChartDrawer(wheel_only_chart_data)
wheel_only_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel External Natal Only Chart
wheel_external_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel External Only", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
wheel_external_chart_data = ChartDataFactory.create_natal_chart_data(wheel_external_subject)
wheel_external_chart = ChartDrawer(wheel_external_chart_data, external_view=True)
wheel_external_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Synastry Only Chart
wheel_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel Synastry Only", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
wheel_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(wheel_synastry_subject, second)
wheel_synastry_chart = ChartDrawer(wheel_synastry_chart_data)
wheel_synastry_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Transit Only Chart
wheel_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel Transit Only", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
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
    "Liverpool",
    "GB",
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
    suppress_geonames_warning=True,
)
sidereal_dark_chart_data = ChartDataFactory.create_natal_chart_data(sidereal_dark_subject)
sidereal_dark_chart = ChartDrawer(sidereal_dark_chart_data, theme="dark")
sidereal_dark_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Sidereal Birth Chart (Fagan-Bradley) Light Theme
sidereal_light_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Fagan-Bradley - Light Theme",
    1940,
    10,
    9,
    18,
    30,
    "Liverpool",
    "GB",
    zodiac_type="Sidereal",
    sidereal_mode="FAGAN_BRADLEY",
    suppress_geonames_warning=True,
)
sidereal_light_chart_data = ChartDataFactory.create_natal_chart_data(sidereal_light_subject)
sidereal_light_chart = ChartDrawer(sidereal_light_chart_data, theme="light")
sidereal_light_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Only Natal Chart
aspect_grid_only_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid Only", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
aspect_grid_only_chart_data = ChartDataFactory.create_natal_chart_data(aspect_grid_only_subject)
aspect_grid_only_chart = ChartDrawer(aspect_grid_only_chart_data)
aspect_grid_only_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Only Dark Theme Natal Chart
aspect_grid_dark_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
aspect_grid_dark_chart_data = ChartDataFactory.create_natal_chart_data(aspect_grid_dark_subject)
aspect_grid_dark_chart = ChartDrawer(aspect_grid_dark_chart_data, theme="dark")
aspect_grid_dark_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Only Light Theme Natal Chart
aspect_grid_light_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
aspect_grid_light_chart_data = ChartDataFactory.create_natal_chart_data(aspect_grid_light_subject)
aspect_grid_light_chart = ChartDrawer(aspect_grid_light_chart_data, theme="light")
aspect_grid_light_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Synastry Chart Aspect Grid Only
aspect_grid_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid Synastry", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
aspect_grid_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(aspect_grid_synastry_subject, second)
aspect_grid_synastry_chart = ChartDrawer(aspect_grid_synastry_chart_data)
aspect_grid_synastry_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Transit Chart Aspect Grid Only
aspect_grid_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid Transit", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
aspect_grid_transit_chart_data = ChartDataFactory.create_transit_chart_data(aspect_grid_transit_subject, second)
aspect_grid_transit_chart = ChartDrawer(aspect_grid_transit_chart_data)
aspect_grid_transit_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Synastry Chart Aspect Grid Only Dark Theme
aspect_grid_dark_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid Dark Synastry", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
aspect_grid_dark_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(
    aspect_grid_dark_synastry_subject, second
)
aspect_grid_dark_synastry_chart = ChartDrawer(aspect_grid_dark_synastry_chart_data, theme="dark")
aspect_grid_dark_synastry_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Synastry Chart With draw_transit_aspect_list table
synastry_chart_with_table_list_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - SCTWL", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
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
    "John Lennon - TCWTG", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
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
    "Hua Chenyu", 1990, 2, 7, 12, 0, "Hunan", "CN", suppress_geonames_warning=True
)
chinese_chart_data = ChartDataFactory.create_natal_chart_data(chinese_subject)
chinese_chart = ChartDrawer(chinese_chart_data, chart_language="CN")
chinese_chart.save_svg(output_path=OUTPUT_DIR_STR)

# French Language Chart
french_subject = AstrologicalSubjectFactory.from_birth_data(
    "Jeanne Moreau", 1928, 1, 23, 10, 0, "Paris", "FR", suppress_geonames_warning=True
)
french_chart_data = ChartDataFactory.create_natal_chart_data(french_subject)
french_chart = ChartDrawer(french_chart_data, chart_language="FR")
french_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Spanish Language Chart
spanish_subject = AstrologicalSubjectFactory.from_birth_data(
    "Antonio Banderas", 1960, 8, 10, 12, 0, "Malaga", "ES", suppress_geonames_warning=True
)
spanish_chart_data = ChartDataFactory.create_natal_chart_data(spanish_subject)
spanish_chart = ChartDrawer(spanish_chart_data, chart_language="ES")
spanish_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Portuguese Language Chart
portuguese_subject = AstrologicalSubjectFactory.from_birth_data(
    "Cristiano Ronaldo", 1985, 2, 5, 5, 25, "Funchal", "PT", suppress_geonames_warning=True
)
portuguese_chart_data = ChartDataFactory.create_natal_chart_data(portuguese_subject)
portuguese_chart = ChartDrawer(portuguese_chart_data, chart_language="PT")
portuguese_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Italian Language Chart
italian_subject = AstrologicalSubjectFactory.from_birth_data(
    "Sophia Loren", 1934, 9, 20, 2, 0, "Rome", "IT", suppress_geonames_warning=True
)
italian_chart_data = ChartDataFactory.create_natal_chart_data(italian_subject)
italian_chart = ChartDrawer(italian_chart_data, chart_language="IT")
italian_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Russian Language Chart
russian_subject = AstrologicalSubjectFactory.from_birth_data(
    "Mikhail Bulgakov", 1891, 5, 15, 12, 0, "Kiev", "UA", suppress_geonames_warning=True
)
russian_chart_data = ChartDataFactory.create_natal_chart_data(russian_subject)
russian_chart = ChartDrawer(russian_chart_data, chart_language="RU")
russian_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Turkish Language Chart
turkish_subject = AstrologicalSubjectFactory.from_birth_data(
    "Mehmet Oz", 1960, 6, 11, 12, 0, "Istanbul", "TR", suppress_geonames_warning=True
)
turkish_chart_data = ChartDataFactory.create_natal_chart_data(turkish_subject)
turkish_chart = ChartDrawer(turkish_chart_data, chart_language="TR")
turkish_chart.save_svg(output_path=OUTPUT_DIR_STR)

# German Language Chart
german_subject = AstrologicalSubjectFactory.from_birth_data(
    "Albert Einstein", 1879, 3, 14, 11, 30, "Ulm", "DE", suppress_geonames_warning=True
)
german_chart_data = ChartDataFactory.create_natal_chart_data(german_subject)
german_chart = ChartDrawer(german_chart_data, chart_language="DE")
german_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Hindi Language Chart
hindi_subject = AstrologicalSubjectFactory.from_birth_data(
    "Amitabh Bachchan", 1942, 10, 11, 4, 0, "Allahabad", "IN", suppress_geonames_warning=True
)
hindi_chart_data = ChartDataFactory.create_natal_chart_data(hindi_subject)
hindi_chart = ChartDrawer(hindi_chart_data, chart_language="HI")
hindi_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Kanye West Natal Chart
kanye_west_subject = AstrologicalSubjectFactory.from_birth_data(
    "Kanye", 1977, 6, 8, 8, 45, "Atlanta", "US", suppress_geonames_warning=True
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
    filename="Angelina Jolie and Brad Pitt Composite Chart - Black and White Theme - Composite Chart",
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
    filename="John Lennon - Black and White Theme - DualReturnChart Chart - Solar Return",
)

# Single Wheel Solar Return
single_return_chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
single_return_chart = ChartDrawer(single_return_chart_data)
single_return_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Black and White Theme Single Return Chart
black_and_white_single_return_chart = ChartDrawer(single_return_chart_data, theme="black-and-white")
black_and_white_single_return_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon Solar Return - Black and White Theme - SingleReturnChart Chart",
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
    "John Lennon - Transparent Background", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
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
    "Liverpool",
    "GB",
    suppress_geonames_warning=True,
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
    "Liverpool",
    "GB",
    suppress_geonames_warning=True,
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
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
    "Liverpool",
    "GB",
    houses_system_identifier="Y",
    suppress_geonames_warning=True,
)
apc_house_chart_data = ChartDataFactory.create_natal_chart_data(apc_house_subject)
ChartDrawer(apc_house_chart_data).save_svg(output_path=OUTPUT_DIR_STR)

# ----------------------------------------------------------------------------
# Section 4: Theme + Chart Type Combinations
# ----------------------------------------------------------------------------

# Light Theme Synastry Chart
light_theme_synastry_chart = ChartDrawer(synastry_chart_data, theme="light")
light_theme_synastry_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Light Theme - Synastry Chart",
)

# Light Theme Transit Chart
light_theme_transit_chart = ChartDrawer(transits_chart_data, theme="light")
light_theme_transit_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Light Theme - Transit Chart",
)

# Light Theme Composite Chart
light_theme_composite_chart = ChartDrawer(composite_chart_data, theme="light")
light_theme_composite_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="Angelina Jolie and Brad Pitt Composite Chart - Light Theme - Composite Chart",
)

# Light Theme External Natal Chart
light_theme_external_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Light Theme External", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
light_theme_external_chart_data = ChartDataFactory.create_natal_chart_data(light_theme_external_subject)
light_theme_external_chart = ChartDrawer(light_theme_external_chart_data, theme="light", external_view=True)
light_theme_external_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Dark Theme Transit Chart
dark_theme_transit_chart = ChartDrawer(transits_chart_data, theme="dark")
dark_theme_transit_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Dark Theme - Transit Chart",
)

# Dark Theme Composite Chart
dark_theme_composite_chart = ChartDrawer(composite_chart_data, theme="dark")
dark_theme_composite_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="Angelina Jolie and Brad Pitt Composite Chart - Dark Theme - Composite Chart",
)

# Black and White Theme External Natal Chart
bw_theme_external_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Black and White Theme External",
    1940,
    10,
    9,
    18,
    30,
    "Liverpool",
    "GB",
    suppress_geonames_warning=True,
)
bw_theme_external_chart_data = ChartDataFactory.create_natal_chart_data(bw_theme_external_subject)
bw_theme_external_chart = ChartDrawer(bw_theme_external_chart_data, theme="black-and-white", external_view=True)
bw_theme_external_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Black and White Theme Dual Lunar Return Chart
bw_lunar_dual_return_chart = ChartDrawer(lunar_dual_return_chart_data, theme="black-and-white")
bw_lunar_dual_return_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Black and White Theme - DualReturnChart Chart - Lunar Return",
)

# Black and White Theme Single Lunar Return Chart
bw_lunar_single_return_chart = ChartDrawer(lunar_single_return_chart_data, theme="black-and-white")
bw_lunar_single_return_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon Lunar Return - Black and White Theme - SingleReturnChart Chart",
)

# ----------------------------------------------------------------------------
# Section 5: Wheel Only + Aspect Grid Only Variations with Themes
# ----------------------------------------------------------------------------

# Wheel Only Dark Theme Natal Chart
wheel_only_dark_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel Only Dark", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
wheel_only_dark_chart_data = ChartDataFactory.create_natal_chart_data(wheel_only_dark_subject)
wheel_only_dark_chart = ChartDrawer(wheel_only_dark_chart_data, theme="dark")
wheel_only_dark_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Only Light Theme Natal Chart
wheel_only_light_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel Only Light", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
wheel_only_light_chart_data = ChartDataFactory.create_natal_chart_data(wheel_only_light_subject)
wheel_only_light_chart = ChartDrawer(wheel_only_light_chart_data, theme="light")
wheel_only_light_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Synastry Dark Theme
wheel_synastry_dark_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel Synastry Dark", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
wheel_synastry_dark_chart_data = ChartDataFactory.create_synastry_chart_data(wheel_synastry_dark_subject, second)
wheel_synastry_dark_chart = ChartDrawer(wheel_synastry_dark_chart_data, theme="dark")
wheel_synastry_dark_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Transit Dark Theme
wheel_transit_dark_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel Transit Dark", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
wheel_transit_dark_chart_data = ChartDataFactory.create_transit_chart_data(wheel_transit_dark_subject, second)
wheel_transit_dark_chart = ChartDrawer(wheel_transit_dark_chart_data, theme="dark")
wheel_transit_dark_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Black and White Natal
aspect_grid_bw_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid BW", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
aspect_grid_bw_chart_data = ChartDataFactory.create_natal_chart_data(aspect_grid_bw_subject)
aspect_grid_bw_chart = ChartDrawer(aspect_grid_bw_chart_data, theme="black-and-white")
aspect_grid_bw_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Black and White Synastry
aspect_grid_bw_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid BW Synastry", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
aspect_grid_bw_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(
    aspect_grid_bw_synastry_subject, second
)
aspect_grid_bw_synastry_chart = ChartDrawer(aspect_grid_bw_synastry_chart_data, theme="black-and-white")
aspect_grid_bw_synastry_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Black and White Transit
aspect_grid_bw_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid BW Transit", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
aspect_grid_bw_transit_chart_data = ChartDataFactory.create_transit_chart_data(aspect_grid_bw_transit_subject, second)
aspect_grid_bw_transit_chart = ChartDrawer(aspect_grid_bw_transit_chart_data, theme="black-and-white")
aspect_grid_bw_transit_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Dark Transit
aspect_grid_dark_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid Dark Transit", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
aspect_grid_dark_transit_chart_data = ChartDataFactory.create_transit_chart_data(
    aspect_grid_dark_transit_subject, second
)
aspect_grid_dark_transit_chart = ChartDrawer(aspect_grid_dark_transit_chart_data, theme="dark")
aspect_grid_dark_transit_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Light Transit
aspect_grid_light_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid Light Transit", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
aspect_grid_light_transit_chart_data = ChartDataFactory.create_transit_chart_data(
    aspect_grid_light_transit_subject, second
)
aspect_grid_light_transit_chart = ChartDrawer(aspect_grid_light_transit_chart_data, theme="light")
aspect_grid_light_transit_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

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
    "John Lennon - Custom Title", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
custom_title_chart_data = ChartDataFactory.create_natal_chart_data(custom_title_subject)
custom_title_chart = ChartDrawer(custom_title_chart_data, custom_title="My Custom Chart Title")
custom_title_chart.save_svg(output_path=OUTPUT_DIR_STR)

# No Aspect Icons Natal Chart
no_aspect_icons_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - No Aspect Icons", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
no_aspect_icons_chart_data = ChartDataFactory.create_natal_chart_data(no_aspect_icons_subject)
no_aspect_icons_chart = ChartDrawer(no_aspect_icons_chart_data, show_aspect_icons=False)
no_aspect_icons_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Auto Size False Natal Chart
auto_size_false_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Auto Size False", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
auto_size_false_chart_data = ChartDataFactory.create_natal_chart_data(auto_size_false_subject)
auto_size_false_chart = ChartDrawer(auto_size_false_chart_data, auto_size=False)
auto_size_false_chart.save_svg(output_path=OUTPUT_DIR_STR)

# No CSS Variables Natal Chart (remove_css_variables=True is used in generate_svg_string)
no_css_vars_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - No CSS Variables", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
no_css_vars_chart_data = ChartDataFactory.create_natal_chart_data(no_css_vars_subject)
no_css_vars_chart = ChartDrawer(no_css_vars_chart_data)
no_css_vars_chart.save_svg(output_path=OUTPUT_DIR_STR, remove_css_variables=True)

# Custom Padding Natal Chart
custom_padding_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Custom Padding", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
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
    "Liverpool",
    "GB",
    suppress_geonames_warning=True,
    active_points=ALL_ACTIVE_POINTS,
)
all_points_transit_second_subject = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney - All Active Points Transit",
    1942,
    6,
    18,
    15,
    30,
    "Liverpool",
    "GB",
    suppress_geonames_warning=True,
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
    filename="John Lennon - All Active Points - Transit Chart",
)

# Solar Return Chart Wheel Only
solar_return_wheel_only_chart = ChartDrawer(single_return_chart_data)
solar_return_wheel_only_chart.save_wheel_only_svg_file(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon Solar Return - Wheel Only",
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
    "John Lennon - EN", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
english_chart_data = ChartDataFactory.create_natal_chart_data(english_subject)
english_chart = ChartDrawer(english_chart_data, chart_language="EN")
english_chart.save_svg(output_path=OUTPUT_DIR_STR)

# French Synastry Chart
french_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - FR", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
french_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(french_synastry_subject, second)
french_synastry_chart = ChartDrawer(french_synastry_chart_data, chart_language="FR")
french_synastry_chart.save_svg(output_path=OUTPUT_DIR_STR)

# German Synastry Chart
german_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - DE", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
german_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(german_synastry_subject, second)
german_synastry_chart = ChartDrawer(german_synastry_chart_data, chart_language="DE")
german_synastry_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Chinese Transit Chart
chinese_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - CN", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
chinese_transit_chart_data = ChartDataFactory.create_transit_chart_data(chinese_transit_subject, second)
chinese_transit_chart = ChartDrawer(chinese_transit_chart_data, chart_language="CN")
chinese_transit_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Spanish Transit Chart
spanish_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - ES", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
spanish_transit_chart_data = ChartDataFactory.create_transit_chart_data(spanish_transit_subject, second)
spanish_transit_chart = ChartDrawer(spanish_transit_chart_data, chart_language="ES")
spanish_transit_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Italian Composite Chart
italian_composite_chart = ChartDrawer(composite_chart_data, chart_language="IT")
italian_composite_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="Angelina Jolie and Brad Pitt Composite Chart - IT - Composite Chart",
)

# Portuguese Composite Chart
portuguese_composite_chart = ChartDrawer(composite_chart_data, chart_language="PT")
portuguese_composite_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="Angelina Jolie and Brad Pitt Composite Chart - PT - Composite Chart",
)

# Russian Transit Chart
russian_transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - RU", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
)
russian_transit_chart_data = ChartDataFactory.create_transit_chart_data(russian_transit_subject, second)
russian_transit_chart = ChartDrawer(russian_transit_chart_data, chart_language="RU")
russian_transit_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Turkish Synastry Chart
turkish_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - TR", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
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
    "Liverpool",
    "GB",
    suppress_geonames_warning=True,
    perspective_type="Heliocentric",
)
heliocentric_synastry_second = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney - Heliocentric",
    1942,
    6,
    18,
    15,
    30,
    "Liverpool",
    "GB",
    suppress_geonames_warning=True,
    perspective_type="Heliocentric",
)
heliocentric_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(
    heliocentric_synastry_first, heliocentric_synastry_second
)
heliocentric_synastry_chart = ChartDrawer(heliocentric_synastry_chart_data)
heliocentric_synastry_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Heliocentric - Synastry Chart",
)

# Topocentric Transit Chart
topocentric_transit_first = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Topocentric Transit",
    1940,
    10,
    9,
    18,
    30,
    "Liverpool",
    "GB",
    suppress_geonames_warning=True,
    perspective_type="Topocentric",
)
topocentric_transit_second = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney - Topocentric",
    1942,
    6,
    18,
    15,
    30,
    "Liverpool",
    "GB",
    suppress_geonames_warning=True,
    perspective_type="Topocentric",
)
topocentric_transit_chart_data = ChartDataFactory.create_transit_chart_data(
    topocentric_transit_first, topocentric_transit_second
)
topocentric_transit_chart = ChartDrawer(topocentric_transit_chart_data)
topocentric_transit_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Topocentric - Transit Chart",
)

# True Geocentric Synastry Chart
true_geocentric_synastry_first = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - True Geocentric Synastry",
    1940,
    10,
    9,
    18,
    30,
    "Liverpool",
    "GB",
    suppress_geonames_warning=True,
    perspective_type="True Geocentric",
)
true_geocentric_synastry_second = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney - True Geocentric",
    1942,
    6,
    18,
    15,
    30,
    "Liverpool",
    "GB",
    suppress_geonames_warning=True,
    perspective_type="True Geocentric",
)
true_geocentric_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(
    true_geocentric_synastry_first, true_geocentric_synastry_second
)
true_geocentric_synastry_chart = ChartDrawer(true_geocentric_synastry_chart_data)
true_geocentric_synastry_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - True Geocentric - Synastry Chart",
)

# ----------------------------------------------------------------------------
# Section 10: Relationship Score Tests
# ----------------------------------------------------------------------------

# Synastry Chart with Relationship Score
relationship_score_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(
    first,
    second,
    include_relationship_score=True,
)
relationship_score_synastry_chart = ChartDrawer(relationship_score_synastry_chart_data)
relationship_score_synastry_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Relationship Score - Synastry Chart",
)

print("All charts regenerated successfully!")
