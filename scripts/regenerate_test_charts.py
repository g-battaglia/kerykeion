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

first = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
second = AstrologicalSubjectFactory.from_birth_data("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB", suppress_geonames_warning=True)

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
external_natal_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - ExternalNatal", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
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

# Black and White Theme Transit Chart
black_and_white_transit_chart = ChartDrawer(transits_chart_data, theme="black-and-white")
black_and_white_transit_chart.save_svg(
    output_path=OUTPUT_DIR_STR,
    filename="John Lennon - Black and White Theme - Transit Chart",
)

# Sidereal Birth Chart (Lahiri)
sidereal_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon Lahiri", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="LAHIRI", suppress_geonames_warning=True)
sidereal_chart_data = ChartDataFactory.create_natal_chart_data(sidereal_subject)
sidereal_chart = ChartDrawer(sidereal_chart_data)
sidereal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (Fagan-Bradley)
sidereal_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon Fagan-Bradley", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY", suppress_geonames_warning=True)
sidereal_chart_data = ChartDataFactory.create_natal_chart_data(sidereal_subject)
sidereal_chart = ChartDrawer(sidereal_chart_data)
sidereal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (DeLuce)
sidereal_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon DeLuce", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="DELUCE", suppress_geonames_warning=True)
sidereal_chart_data = ChartDataFactory.create_natal_chart_data(sidereal_subject)
sidereal_chart = ChartDrawer(sidereal_chart_data)
sidereal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Sidereal Birth Chart (J2000)
sidereal_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon J2000", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="J2000", suppress_geonames_warning=True)
sidereal_chart_data = ChartDataFactory.create_natal_chart_data(sidereal_subject)
sidereal_chart = ChartDrawer(sidereal_chart_data)
sidereal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# House System Morinus
morinus_house_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - House System Morinus", 1940, 10, 9, 18, 30, "Liverpool", "GB", houses_system_identifier="M", suppress_geonames_warning=True)
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
true_geocentric_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - True Geocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", perspective_type="True Geocentric", suppress_geonames_warning=True)
true_geocentric_chart_data = ChartDataFactory.create_natal_chart_data(true_geocentric_subject)
true_geocentric_chart = ChartDrawer(true_geocentric_chart_data)
true_geocentric_chart.save_svg(output_path=OUTPUT_DIR_STR)

# With Heliocentric Perspective
heliocentric_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Heliocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", perspective_type="Heliocentric", suppress_geonames_warning=True)
heliocentric_chart_data = ChartDataFactory.create_natal_chart_data(heliocentric_subject)
heliocentric_chart = ChartDrawer(heliocentric_chart_data)
heliocentric_chart.save_svg(output_path=OUTPUT_DIR_STR)

# With Topocentric Perspective
topocentric_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Topocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", perspective_type="Topocentric", suppress_geonames_warning=True)
topocentric_chart_data = ChartDataFactory.create_natal_chart_data(topocentric_subject)
topocentric_chart = ChartDrawer(topocentric_chart_data)
topocentric_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Minified SVG
minified_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Minified", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
minified_chart_data = ChartDataFactory.create_natal_chart_data(minified_subject)
minified_chart = ChartDrawer(minified_chart_data)
minified_chart.save_svg(output_path=OUTPUT_DIR_STR, minify=True)

# Dark Theme Natal Chart
dark_theme_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
dark_theme_natal_chart_data = ChartDataFactory.create_natal_chart_data(dark_theme_subject)
dark_theme_natal_chart = ChartDrawer(dark_theme_natal_chart_data, theme="dark")
dark_theme_natal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Dark High Contrast Theme Natal Chart
dark_high_contrast_theme_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Dark High Contrast Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
dark_high_contrast_theme_natal_chart_data = ChartDataFactory.create_natal_chart_data(dark_high_contrast_theme_subject)
dark_high_contrast_theme_natal_chart = ChartDrawer(dark_high_contrast_theme_natal_chart_data, theme="dark-high-contrast")
dark_high_contrast_theme_natal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Light Theme Natal Chart
light_theme_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
light_theme_natal_chart_data = ChartDataFactory.create_natal_chart_data(light_theme_subject)
light_theme_natal_chart = ChartDrawer(light_theme_natal_chart_data, theme="light")
light_theme_natal_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Dark Theme External Natal Chart
dark_theme_external_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Dark Theme External", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
dark_theme_external_chart_data = ChartDataFactory.create_natal_chart_data(dark_theme_external_subject)
dark_theme_external_chart = ChartDrawer(dark_theme_external_chart_data, theme="dark", external_view=True)
dark_theme_external_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Dark Theme Synastry Chart
dark_theme_synastry_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - DTS", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
dark_theme_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(dark_theme_synastry_subject, second)
dark_theme_synastry_chart = ChartDrawer(dark_theme_synastry_chart_data, theme="dark")
dark_theme_synastry_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Wheel Natal Only Chart
wheel_only_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Wheel Only", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
wheel_only_chart_data = ChartDataFactory.create_natal_chart_data(wheel_only_subject)
wheel_only_chart = ChartDrawer(wheel_only_chart_data)
wheel_only_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel External Natal Only Chart
wheel_external_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Wheel External Only", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
wheel_external_chart_data = ChartDataFactory.create_natal_chart_data(wheel_external_subject)
wheel_external_chart = ChartDrawer(wheel_external_chart_data, external_view=True)
wheel_external_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Synastry Only Chart
wheel_synastry_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Wheel Synastry Only", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
wheel_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(wheel_synastry_subject, second)
wheel_synastry_chart = ChartDrawer(wheel_synastry_chart_data)
wheel_synastry_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Transit Only Chart
wheel_transit_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Wheel Transit Only", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
wheel_transit_chart_data = ChartDataFactory.create_transit_chart_data(wheel_transit_subject, second)
wheel_transit_chart = ChartDrawer(wheel_transit_chart_data)
wheel_transit_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Sidereal Birth Chart (Lahiri) Dark Theme
sidereal_dark_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon Lahiri - Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="LAHIRI", suppress_geonames_warning=True)
sidereal_dark_chart_data = ChartDataFactory.create_natal_chart_data(sidereal_dark_subject)
sidereal_dark_chart = ChartDrawer(sidereal_dark_chart_data, theme="dark")
sidereal_dark_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Wheel Sidereal Birth Chart (Fagan-Bradley) Light Theme
sidereal_light_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon Fagan-Bradley - Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY", suppress_geonames_warning=True)
sidereal_light_chart_data = ChartDataFactory.create_natal_chart_data(sidereal_light_subject)
sidereal_light_chart = ChartDrawer(sidereal_light_chart_data, theme="light")
sidereal_light_chart.save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Only Natal Chart
aspect_grid_only_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Only", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
aspect_grid_only_chart_data = ChartDataFactory.create_natal_chart_data(aspect_grid_only_subject)
aspect_grid_only_chart = ChartDrawer(aspect_grid_only_chart_data)
aspect_grid_only_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Only Dark Theme Natal Chart
aspect_grid_dark_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
aspect_grid_dark_chart_data = ChartDataFactory.create_natal_chart_data(aspect_grid_dark_subject)
aspect_grid_dark_chart = ChartDrawer(aspect_grid_dark_chart_data, theme="dark")
aspect_grid_dark_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Aspect Grid Only Light Theme Natal Chart
aspect_grid_light_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
aspect_grid_light_chart_data = ChartDataFactory.create_natal_chart_data(aspect_grid_light_subject)
aspect_grid_light_chart = ChartDrawer(aspect_grid_light_chart_data, theme="light")
aspect_grid_light_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Synastry Chart Aspect Grid Only
aspect_grid_synastry_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Synastry", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
aspect_grid_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(aspect_grid_synastry_subject, second)
aspect_grid_synastry_chart = ChartDrawer(aspect_grid_synastry_chart_data)
aspect_grid_synastry_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Transit Chart Aspect Grid Only
aspect_grid_transit_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Transit", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
aspect_grid_transit_chart_data = ChartDataFactory.create_transit_chart_data(aspect_grid_transit_subject, second)
aspect_grid_transit_chart = ChartDrawer(aspect_grid_transit_chart_data)
aspect_grid_transit_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Synastry Chart Aspect Grid Only Dark Theme
aspect_grid_dark_synastry_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Dark Synastry", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
aspect_grid_dark_synastry_chart_data = ChartDataFactory.create_synastry_chart_data(aspect_grid_dark_synastry_subject, second)
aspect_grid_dark_synastry_chart = ChartDrawer(aspect_grid_dark_synastry_chart_data, theme="dark")
aspect_grid_dark_synastry_chart.save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)

# Synastry Chart With draw_transit_aspect_list table
synastry_chart_with_table_list_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - SCTWL", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
synastry_chart_with_table_list_data = ChartDataFactory.create_synastry_chart_data(synastry_chart_with_table_list_subject, second)
synastry_chart_with_table_list = ChartDrawer(synastry_chart_with_table_list_data, double_chart_aspect_grid_type="list", theme="dark")
synastry_chart_with_table_list.save_svg(output_path=OUTPUT_DIR_STR)

# Transit Chart With draw_transit_aspect_grid table
transit_chart_with_table_grid_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - TCWTG", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
transit_chart_with_table_grid_data = ChartDataFactory.create_transit_chart_data(transit_chart_with_table_grid_subject, second)
transit_chart_with_table_grid = ChartDrawer(transit_chart_with_table_grid_data, double_chart_aspect_grid_type="table", theme="dark")
transit_chart_with_table_grid.save_svg(output_path=OUTPUT_DIR_STR)

# Chinese Language Chart
chinese_subject = AstrologicalSubjectFactory.from_birth_data("Hua Chenyu", 1990, 2, 7, 12, 0, "Hunan", "CN", suppress_geonames_warning=True)
chinese_chart_data = ChartDataFactory.create_natal_chart_data(chinese_subject)
chinese_chart = ChartDrawer(chinese_chart_data, chart_language="CN")
chinese_chart.save_svg(output_path=OUTPUT_DIR_STR)

# French Language Chart
french_subject = AstrologicalSubjectFactory.from_birth_data("Jeanne Moreau", 1928, 1, 23, 10, 0, "Paris", "FR", suppress_geonames_warning=True)
french_chart_data = ChartDataFactory.create_natal_chart_data(french_subject)
french_chart = ChartDrawer(french_chart_data, chart_language="FR")
french_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Spanish Language Chart
spanish_subject = AstrologicalSubjectFactory.from_birth_data("Antonio Banderas", 1960, 8, 10, 12, 0, "Malaga", "ES", suppress_geonames_warning=True)
spanish_chart_data = ChartDataFactory.create_natal_chart_data(spanish_subject)
spanish_chart = ChartDrawer(spanish_chart_data, chart_language="ES")
spanish_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Portuguese Language Chart
portuguese_subject = AstrologicalSubjectFactory.from_birth_data("Cristiano Ronaldo", 1985, 2, 5, 5, 25, "Funchal", "PT", suppress_geonames_warning=True)
portuguese_chart_data = ChartDataFactory.create_natal_chart_data(portuguese_subject)
portuguese_chart = ChartDrawer(portuguese_chart_data, chart_language="PT")
portuguese_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Italian Language Chart
italian_subject = AstrologicalSubjectFactory.from_birth_data("Sophia Loren", 1934, 9, 20, 2, 0, "Rome", "IT", suppress_geonames_warning=True)
italian_chart_data = ChartDataFactory.create_natal_chart_data(italian_subject)
italian_chart = ChartDrawer(italian_chart_data, chart_language="IT")
italian_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Russian Language Chart
russian_subject = AstrologicalSubjectFactory.from_birth_data("Mikhail Bulgakov", 1891, 5, 15, 12, 0, "Kiev", "UA", suppress_geonames_warning=True)
russian_chart_data = ChartDataFactory.create_natal_chart_data(russian_subject)
russian_chart = ChartDrawer(russian_chart_data, chart_language="RU")
russian_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Turkish Language Chart
turkish_subject = AstrologicalSubjectFactory.from_birth_data("Mehmet Oz", 1960, 6, 11, 12, 0, "Istanbul", "TR", suppress_geonames_warning=True)
turkish_chart_data = ChartDataFactory.create_natal_chart_data(turkish_subject)
turkish_chart = ChartDrawer(turkish_chart_data, chart_language="TR")
turkish_chart.save_svg(output_path=OUTPUT_DIR_STR)

# German Language Chart
german_subject = AstrologicalSubjectFactory.from_birth_data("Albert Einstein", 1879, 3, 14, 11, 30, "Ulm", "DE", suppress_geonames_warning=True)
german_chart_data = ChartDataFactory.create_natal_chart_data(german_subject)
german_chart = ChartDrawer(german_chart_data, chart_language="DE")
german_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Hindi Language Chart
hindi_subject = AstrologicalSubjectFactory.from_birth_data("Amitabh Bachchan", 1942, 10, 11, 4, 0, "Allahabad", "IN", suppress_geonames_warning=True)
hindi_chart_data = ChartDataFactory.create_natal_chart_data(hindi_subject)
hindi_chart = ChartDrawer(hindi_chart_data, chart_language="HI")
hindi_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Kanye West Natal Chart
kanye_west_subject = AstrologicalSubjectFactory.from_birth_data("Kanye", 1977, 6, 8, 8, 45, "Atlanta", "US", suppress_geonames_warning=True)
kanye_west_chart_data = ChartDataFactory.create_natal_chart_data(kanye_west_subject)
kanye_west_chart = ChartDrawer(kanye_west_chart_data)
kanye_west_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Composite Chart
angelina = AstrologicalSubjectFactory.from_birth_data("Angelina Jolie", 1975, 6, 4, 9, 9, "Los Angeles", "US", lng=-118.15, lat=34.03, tz_str="America/Los_Angeles", suppress_geonames_warning=True)
brad = AstrologicalSubjectFactory.from_birth_data("Brad Pitt", 1963, 12, 18, 6, 31, "Shawnee", "US", lng=-96.56, lat=35.20, tz_str="America/Chicago", suppress_geonames_warning=True)

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

# Single Wheel Lunar Return
lunar_single_return_chart_data = ChartDataFactory.create_single_wheel_return_chart_data(lunar_return)
lunar_single_return_chart = ChartDrawer(lunar_single_return_chart_data)
lunar_single_return_chart.save_svg(output_path=OUTPUT_DIR_STR)

## Transparent Background
transparent_background_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Transparent Background", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
transparent_background_chart_data = ChartDataFactory.create_natal_chart_data(transparent_background_subject)
transparent_background_chart = ChartDrawer(transparent_background_chart_data, transparent_background=True)
transparent_background_chart.save_svg(output_path=OUTPUT_DIR_STR)

# Natal Chart with ALL_ACTIVE_POINTS
all_points_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - All Active Points", 1940, 10, 9, 18, 30, "Liverpool", "GB",
    suppress_geonames_warning=True, active_points=ALL_ACTIVE_POINTS[0:]
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
    "Paul McCartney - All Active Points", 1942, 6, 18, 15, 30, "Liverpool", "GB",
    suppress_geonames_warning=True, active_points=ALL_ACTIVE_POINTS[0:]
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

print("All charts regenerated successfully!")
