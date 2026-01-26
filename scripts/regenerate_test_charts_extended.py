#!/usr/bin/env python3
"""
Extended SVG Chart Generation Script for Comprehensive Test Coverage

This script generates additional SVG charts beyond the base regenerate_test_charts.py:
- Strawberry theme for all chart types
- Temporal subjects from test_subjects_matrix.py (25 subjects spanning 2700 years)
- Geographic subjects from test_subjects_matrix.py (16 locations)
- Cross-combinations (sidereal modes × themes, house systems × chart types)

Run this after regenerate_test_charts.py to add comprehensive coverage.

Usage:
    python scripts/regenerate_test_charts_extended.py [--all] [--strawberry] [--temporal] [--geographic] [--combinations]
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from kerykeion import AstrologicalSubjectFactory, ChartDrawer, CompositeSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

# Import test subject definitions
from tests.data.test_subjects_matrix import (
    TEMPORAL_SUBJECTS,
    GEOGRAPHIC_SUBJECTS,
    SIDEREAL_MODES,
    HOUSE_SYSTEMS,
)

# Output directory
OUTPUT_DIR = project_root / "tests" / "charts" / "svg"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR_STR = str(OUTPUT_DIR)

# Common birth data for John Lennon and Paul McCartney (used for synastry/transit)
JOHN_LENNON_BIRTH_DATA = (1940, 10, 9, 18, 30, "Liverpool", "GB")
PAUL_MCCARTNEY_BIRTH_DATA = (1942, 6, 18, 15, 30, "Liverpool", "GB")

# Themes to test
THEMES = ["classic", "dark", "light", "black-and-white", "strawberry", "dark-high-contrast"]

# Key sidereal modes for cross-combination testing
KEY_SIDEREAL_MODES = ["LAHIRI", "FAGAN_BRADLEY", "KRISHNAMURTI", "RAMAN", "J2000"]

# Key house systems for chart type combinations
KEY_HOUSE_SYSTEMS = ["K", "W", "R", "C", "O"]  # Koch, Whole Sign, Regiomontanus, Campanus, Porphyry


def create_subject_from_dict(subject_dict: dict, **kwargs):
    """Create an AstrologicalSubjectModel from a subject dictionary."""
    # Geographic subjects don't have year/month/day - use default date
    if "year" not in subject_dict:
        return AstrologicalSubjectFactory.from_birth_data(
            subject_dict["name"],
            1990,  # Default year
            6,
            21,  # Summer solstice
            12,
            0,
            subject_dict["name"],  # city name
            "XX",  # placeholder country
            lat=subject_dict["lat"],
            lng=subject_dict["lng"],
            tz_str=subject_dict["tz_str"],
            suppress_geonames_warning=True,
            **kwargs,
        )
    else:
        return AstrologicalSubjectFactory.from_birth_data(
            subject_dict["name"],
            subject_dict["year"],
            subject_dict["month"],
            subject_dict["day"],
            subject_dict["hour"],
            subject_dict["minute"],
            subject_dict["name"],  # Use name as city for historical subjects
            "XX",  # placeholder country
            lat=subject_dict["lat"],
            lng=subject_dict["lng"],
            tz_str=subject_dict["tz_str"],
            suppress_geonames_warning=True,
            **kwargs,
        )


def generate_strawberry_theme_charts():
    """Generate all chart types with Strawberry theme."""
    print("\n=== Generating Strawberry Theme Charts ===")

    # Create subjects
    first = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "Paul McCartney", *PAUL_MCCARTNEY_BIRTH_DATA, suppress_geonames_warning=True
    )

    # Composite subjects
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

    charts_generated = 0

    # 1. Natal Chart - Strawberry Theme
    strawberry_natal_subject = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon - Strawberry Theme", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
    )
    natal_chart_data = ChartDataFactory.create_natal_chart_data(strawberry_natal_subject)
    ChartDrawer(natal_chart_data, theme="strawberry").save_svg(output_path=OUTPUT_DIR_STR)
    print(f"  Generated: John Lennon - Strawberry Theme - Natal Chart.svg")
    charts_generated += 1

    # 2. External Natal Chart - Strawberry Theme
    strawberry_external_subject = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon - Strawberry Theme External", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
    )
    external_chart_data = ChartDataFactory.create_natal_chart_data(strawberry_external_subject)
    ChartDrawer(external_chart_data, theme="strawberry", external_view=True).save_svg(output_path=OUTPUT_DIR_STR)
    print(f"  Generated: John Lennon - Strawberry Theme External - Natal Chart.svg")
    charts_generated += 1

    # 3. Synastry Chart - Strawberry Theme
    strawberry_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon - Strawberry Theme Synastry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
    )
    synastry_chart_data = ChartDataFactory.create_synastry_chart_data(strawberry_synastry_subject, second)
    ChartDrawer(synastry_chart_data, theme="strawberry").save_svg(output_path=OUTPUT_DIR_STR)
    print(f"  Generated: John Lennon - Strawberry Theme Synastry - Synastry Chart.svg")
    charts_generated += 1

    # 4. Transit Chart - Strawberry Theme
    strawberry_transit_subject = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon - Strawberry Theme Transit", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
    )
    transit_chart_data = ChartDataFactory.create_transit_chart_data(strawberry_transit_subject, second)
    ChartDrawer(transit_chart_data, theme="strawberry").save_svg(output_path=OUTPUT_DIR_STR)
    print(f"  Generated: John Lennon - Strawberry Theme Transit - Transit Chart.svg")
    charts_generated += 1

    # 5. Wheel Only - Strawberry Theme
    wheel_strawberry_subject = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon - Wheel Only Strawberry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
    )
    wheel_chart_data = ChartDataFactory.create_natal_chart_data(wheel_strawberry_subject)
    ChartDrawer(wheel_chart_data, theme="strawberry").save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)
    print(f"  Generated: John Lennon - Wheel Only Strawberry - Natal Chart - Wheel Only.svg")
    charts_generated += 1

    # 6. Aspect Grid Only - Strawberry Theme
    aspect_strawberry_subject = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon - Aspect Grid Strawberry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
    )
    aspect_chart_data = ChartDataFactory.create_natal_chart_data(aspect_strawberry_subject)
    ChartDrawer(aspect_chart_data, theme="strawberry").save_aspect_grid_only_svg_file(output_path=OUTPUT_DIR_STR)
    print(f"  Generated: John Lennon - Aspect Grid Strawberry - Natal Chart - Aspect Grid Only.svg")
    charts_generated += 1

    # 7. Synastry Wheel Only - Strawberry Theme
    synastry_wheel_strawberry_subject = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon - Wheel Synastry Strawberry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
    )
    synastry_wheel_chart_data = ChartDataFactory.create_synastry_chart_data(synastry_wheel_strawberry_subject, second)
    ChartDrawer(synastry_wheel_chart_data, theme="strawberry").save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)
    print(f"  Generated: John Lennon - Wheel Synastry Strawberry - Synastry Chart - Wheel Only.svg")
    charts_generated += 1

    # 8. Synastry Aspect Grid Only - Strawberry Theme
    synastry_aspect_strawberry_subject = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon - Aspect Grid Synastry Strawberry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
    )
    synastry_aspect_chart_data = ChartDataFactory.create_synastry_chart_data(synastry_aspect_strawberry_subject, second)
    ChartDrawer(synastry_aspect_chart_data, theme="strawberry").save_aspect_grid_only_svg_file(
        output_path=OUTPUT_DIR_STR
    )
    print(f"  Generated: John Lennon - Aspect Grid Synastry Strawberry - Synastry Chart - Aspect Grid Only.svg")
    charts_generated += 1

    # 9. Transit Wheel Only - Strawberry Theme
    transit_wheel_strawberry_subject = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon - Wheel Transit Strawberry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
    )
    transit_wheel_chart_data = ChartDataFactory.create_transit_chart_data(transit_wheel_strawberry_subject, second)
    ChartDrawer(transit_wheel_chart_data, theme="strawberry").save_wheel_only_svg_file(output_path=OUTPUT_DIR_STR)
    print(f"  Generated: John Lennon - Wheel Transit Strawberry - Transit Chart - Wheel Only.svg")
    charts_generated += 1

    # 10. Transit Aspect Grid Only - Strawberry Theme
    transit_aspect_strawberry_subject = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon - Aspect Grid Transit Strawberry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
    )
    transit_aspect_chart_data = ChartDataFactory.create_transit_chart_data(transit_aspect_strawberry_subject, second)
    ChartDrawer(transit_aspect_chart_data, theme="strawberry").save_aspect_grid_only_svg_file(
        output_path=OUTPUT_DIR_STR
    )
    print(f"  Generated: John Lennon - Aspect Grid Transit Strawberry - Transit Chart - Aspect Grid Only.svg")
    charts_generated += 1

    # 11. Composite Chart - Strawberry Theme
    composite_factory = CompositeSubjectFactory(angelina, brad)
    composite_model = composite_factory.get_midpoint_composite_subject_model()
    composite_chart_data = ChartDataFactory.create_composite_chart_data(composite_model)
    ChartDrawer(composite_chart_data, theme="strawberry").save_svg(
        output_path=OUTPUT_DIR_STR,
        filename="Angelina Jolie and Brad Pitt Composite Chart - Strawberry Theme - Composite Chart",
    )
    print(f"  Generated: Angelina Jolie and Brad Pitt Composite Chart - Strawberry Theme - Composite Chart.svg")
    charts_generated += 1

    # 12. Solar Return - Strawberry Theme
    return_factory = PlanetaryReturnFactory(
        first,
        lng=-2.9833,
        lat=53.4000,
        tz_str="Europe/London",
        online=False,
    )
    solar_return = return_factory.next_return_from_iso_formatted_time(
        "2025-01-09T18:30:00+01:00",
        return_type="Solar",
    )
    dual_return_chart_data = ChartDataFactory.create_return_chart_data(first, solar_return)
    ChartDrawer(dual_return_chart_data, theme="strawberry").save_svg(
        output_path=OUTPUT_DIR_STR,
        filename="John Lennon - Strawberry Theme - DualReturnChart Chart - Solar Return",
    )
    print(f"  Generated: John Lennon - Strawberry Theme - DualReturnChart Chart - Solar Return.svg")
    charts_generated += 1

    # 13. Single Solar Return - Strawberry Theme
    single_return_chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
    ChartDrawer(single_return_chart_data, theme="strawberry").save_svg(
        output_path=OUTPUT_DIR_STR,
        filename="John Lennon Solar Return - Strawberry Theme - SingleReturnChart Chart",
    )
    print(f"  Generated: John Lennon Solar Return - Strawberry Theme - SingleReturnChart Chart.svg")
    charts_generated += 1

    # 14. Lunar Return - Strawberry Theme
    lunar_return = return_factory.next_return_from_iso_formatted_time(
        "2025-01-09T18:30:00+01:00",
        return_type="Lunar",
    )
    lunar_dual_return_chart_data = ChartDataFactory.create_return_chart_data(first, lunar_return)
    ChartDrawer(lunar_dual_return_chart_data, theme="strawberry").save_svg(
        output_path=OUTPUT_DIR_STR,
        filename="John Lennon - Strawberry Theme - DualReturnChart Chart - Lunar Return",
    )
    print(f"  Generated: John Lennon - Strawberry Theme - DualReturnChart Chart - Lunar Return.svg")
    charts_generated += 1

    print(f"\n  Total Strawberry theme charts: {charts_generated}")
    return charts_generated


def generate_temporal_subject_charts():
    """Generate charts for all temporal subjects from test_subjects_matrix.py."""
    print("\n=== Generating Temporal Subject Charts ===")

    charts_generated = 0

    # Generate natal chart for each temporal subject
    for subject_data in TEMPORAL_SUBJECTS:
        subject_id = subject_data["id"]
        subject_name = subject_data["name"]

        try:
            subject = create_subject_from_dict(subject_data)
            chart_data = ChartDataFactory.create_natal_chart_data(subject)
            chart = ChartDrawer(chart_data)
            chart.save_svg(output_path=OUTPUT_DIR_STR)
            print(f"  Generated: {subject_name} - Natal Chart.svg")
            charts_generated += 1
        except Exception as e:
            print(f"  ERROR generating {subject_name}: {e}")

    # Generate selected combinations for key temporal subjects
    # Ancient subjects with Dark theme
    ancient_ids = ["ancient_500bc", "ancient_200bc", "roman_100ad", "late_antiquity_400", "early_medieval_800"]
    for subject_id in ancient_ids:
        subject_data = next((s for s in TEMPORAL_SUBJECTS if s["id"] == subject_id), None)
        if subject_data:
            try:
                subject = create_subject_from_dict(subject_data)
                subject.name = f"{subject_data['name']} - Dark Theme"
                chart_data = ChartDataFactory.create_natal_chart_data(subject)
                chart = ChartDrawer(chart_data, theme="dark")
                chart.save_svg(output_path=OUTPUT_DIR_STR)
                print(f"  Generated: {subject.name} - Natal Chart.svg")
                charts_generated += 1
            except Exception as e:
                print(f"  ERROR generating {subject_data['name']} dark theme: {e}")

    # Future subjects with Light theme
    future_ids = ["future_2050", "future_2100", "future_2200"]
    for subject_id in future_ids:
        subject_data = next((s for s in TEMPORAL_SUBJECTS if s["id"] == subject_id), None)
        if subject_data:
            try:
                subject = create_subject_from_dict(subject_data)
                subject.name = f"{subject_data['name']} - Light Theme"
                chart_data = ChartDataFactory.create_natal_chart_data(subject)
                chart = ChartDrawer(chart_data, theme="light")
                chart.save_svg(output_path=OUTPUT_DIR_STR)
                print(f"  Generated: {subject.name} - Natal Chart.svg")
                charts_generated += 1
            except Exception as e:
                print(f"  ERROR generating {subject_data['name']} light theme: {e}")

    # Modern subjects with Synastry (John + Yoko, Beatles pairs)
    john_data = next((s for s in TEMPORAL_SUBJECTS if s["id"] == "john_lennon_1940"), None)
    yoko_data = next((s for s in TEMPORAL_SUBJECTS if s["id"] == "yoko_ono_1933"), None)
    paul_data = next((s for s in TEMPORAL_SUBJECTS if s["id"] == "paul_mccartney_1942"), None)

    if john_data and yoko_data:
        try:
            john = create_subject_from_dict(john_data)
            yoko = create_subject_from_dict(yoko_data)
            john.name = "John and Yoko"
            synastry_data = ChartDataFactory.create_synastry_chart_data(john, yoko)
            chart = ChartDrawer(synastry_data)
            chart.save_svg(
                output_path=OUTPUT_DIR_STR,
                filename="John and Yoko - Synastry Chart",
            )
            print(f"  Generated: John and Yoko - Synastry Chart.svg")
            charts_generated += 1
        except Exception as e:
            print(f"  ERROR generating John and Yoko synastry: {e}")

    print(f"\n  Total temporal subject charts: {charts_generated}")
    return charts_generated


def generate_geographic_subject_charts():
    """Generate charts for all geographic subjects from test_subjects_matrix.py."""
    print("\n=== Generating Geographic Subject Charts ===")

    charts_generated = 0

    # Generate natal chart for each geographic subject
    for subject_data in GEOGRAPHIC_SUBJECTS:
        subject_name = subject_data["name"]

        try:
            subject = create_subject_from_dict(subject_data)
            chart_data = ChartDataFactory.create_natal_chart_data(subject)
            chart = ChartDrawer(chart_data)
            chart.save_svg(output_path=OUTPUT_DIR_STR)
            print(f"  Generated: {subject_name} - Natal Chart.svg")
            charts_generated += 1
        except Exception as e:
            print(f"  ERROR generating {subject_name}: {e}")

    # Generate Koch house system variants for all geographic subjects
    for subject_data in GEOGRAPHIC_SUBJECTS:
        subject_name = subject_data["name"]

        try:
            subject = create_subject_from_dict(subject_data, houses_system_identifier="K")
            subject.name = f"{subject_name} - Koch"
            chart_data = ChartDataFactory.create_natal_chart_data(subject)
            chart = ChartDrawer(chart_data)
            chart.save_svg(output_path=OUTPUT_DIR_STR)
            print(f"  Generated: {subject.name} - Natal Chart.svg")
            charts_generated += 1
        except Exception as e:
            print(f"  ERROR generating {subject_name} Koch: {e}")

    # Generate Whole Sign for extreme latitudes
    extreme_lat_ids = [
        "arctic_circle_66n",
        "antarctic_circle_66s",
        "reykjavik_64n",
        "ushuaia_55s",
        "oslo_60n",
        "quito_equator",
        "singapore_1n",
        "nairobi_1s",
    ]
    for subject_id in extreme_lat_ids:
        subject_data = next((s for s in GEOGRAPHIC_SUBJECTS if s["id"] == subject_id), None)
        if subject_data:
            try:
                subject = create_subject_from_dict(subject_data, houses_system_identifier="W")
                subject.name = f"{subject_data['name']} - Whole Sign"
                chart_data = ChartDataFactory.create_natal_chart_data(subject)
                chart = ChartDrawer(chart_data)
                chart.save_svg(output_path=OUTPUT_DIR_STR)
                print(f"  Generated: {subject.name} - Natal Chart.svg")
                charts_generated += 1
            except Exception as e:
                print(f"  ERROR generating {subject_data['name']} Whole Sign: {e}")

    print(f"\n  Total geographic subject charts: {charts_generated}")
    return charts_generated


def generate_cross_combination_charts():
    """Generate cross-combination charts (sidereal × themes, house systems × chart types)."""
    print("\n=== Generating Cross-Combination Charts ===")

    charts_generated = 0

    # Create base subjects
    first = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "Paul McCartney", *PAUL_MCCARTNEY_BIRTH_DATA, suppress_geonames_warning=True
    )

    # Sidereal × Themes combinations
    sidereal_theme_combos = [
        ("LAHIRI", "strawberry"),
        ("LAHIRI", "black-and-white"),
        ("FAGAN_BRADLEY", "dark"),
        ("FAGAN_BRADLEY", "strawberry"),
        ("KRISHNAMURTI", "light"),
        ("KRISHNAMURTI", "strawberry"),
        ("RAMAN", "dark"),
        ("RAMAN", "strawberry"),
        ("J2000", "light"),
        ("J2000", "strawberry"),
    ]

    for sidereal_mode, theme in sidereal_theme_combos:
        try:
            subject = AstrologicalSubjectFactory.from_birth_data(
                f"John Lennon {sidereal_mode} - {theme.title()} Theme",
                *JOHN_LENNON_BIRTH_DATA,
                zodiac_type="Sidereal",
                sidereal_mode=sidereal_mode,
                suppress_geonames_warning=True,
            )
            chart_data = ChartDataFactory.create_natal_chart_data(subject)
            chart = ChartDrawer(chart_data, theme=theme)
            chart.save_svg(output_path=OUTPUT_DIR_STR)
            print(f"  Generated: {subject.name} - Natal Chart.svg")
            charts_generated += 1
        except Exception as e:
            print(f"  ERROR generating {sidereal_mode} {theme}: {e}")

    # House Systems × Synastry combinations
    house_system_names = {
        "K": "Koch",
        "W": "Whole Sign",
        "R": "Regiomontanus",
        "C": "Campanus",
        "O": "Porphyry",
    }

    for house_id, house_name in house_system_names.items():
        try:
            first_hs = AstrologicalSubjectFactory.from_birth_data(
                f"John Lennon - {house_name} Synastry",
                *JOHN_LENNON_BIRTH_DATA,
                houses_system_identifier=house_id,
                suppress_geonames_warning=True,
            )
            second_hs = AstrologicalSubjectFactory.from_birth_data(
                f"Paul McCartney - {house_name}",
                *PAUL_MCCARTNEY_BIRTH_DATA,
                houses_system_identifier=house_id,
                suppress_geonames_warning=True,
            )
            synastry_data = ChartDataFactory.create_synastry_chart_data(first_hs, second_hs)
            chart = ChartDrawer(synastry_data)
            chart.save_svg(
                output_path=OUTPUT_DIR_STR,
                filename=f"John Lennon - {house_name} - Synastry Chart",
            )
            print(f"  Generated: John Lennon - {house_name} - Synastry Chart.svg")
            charts_generated += 1
        except Exception as e:
            print(f"  ERROR generating {house_name} synastry: {e}")

    # House Systems × Transit combinations
    for house_id, house_name in house_system_names.items():
        try:
            first_hs = AstrologicalSubjectFactory.from_birth_data(
                f"John Lennon - {house_name} Transit",
                *JOHN_LENNON_BIRTH_DATA,
                houses_system_identifier=house_id,
                suppress_geonames_warning=True,
            )
            second_hs = AstrologicalSubjectFactory.from_birth_data(
                f"Paul McCartney - {house_name} Transit",
                *PAUL_MCCARTNEY_BIRTH_DATA,
                houses_system_identifier=house_id,
                suppress_geonames_warning=True,
            )
            transit_data = ChartDataFactory.create_transit_chart_data(first_hs, second_hs)
            chart = ChartDrawer(transit_data)
            chart.save_svg(
                output_path=OUTPUT_DIR_STR,
                filename=f"John Lennon - {house_name} - Transit Chart",
            )
            print(f"  Generated: John Lennon - {house_name} - Transit Chart.svg")
            charts_generated += 1
        except Exception as e:
            print(f"  ERROR generating {house_name} transit: {e}")

    # Language × Chart Type combinations (not yet covered)
    language_chart_combos = [
        ("FR", "composite"),
        ("HI", "synastry"),
        ("JP", "transit"),  # Japanese if supported
    ]

    # Composite subjects for language tests
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

    # French Composite
    try:
        composite_factory = CompositeSubjectFactory(angelina, brad)
        composite_model = composite_factory.get_midpoint_composite_subject_model()
        composite_chart_data = ChartDataFactory.create_composite_chart_data(composite_model)
        chart = ChartDrawer(composite_chart_data, chart_language="FR")
        chart.save_svg(
            output_path=OUTPUT_DIR_STR,
            filename="Angelina Jolie and Brad Pitt Composite Chart - FR - Composite Chart",
        )
        print(f"  Generated: Angelina Jolie and Brad Pitt Composite Chart - FR - Composite Chart.svg")
        charts_generated += 1
    except Exception as e:
        print(f"  ERROR generating French composite: {e}")

    # Hindi Synastry
    try:
        hindi_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - HI", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        synastry_data = ChartDataFactory.create_synastry_chart_data(hindi_synastry_subject, second)
        chart = ChartDrawer(synastry_data, chart_language="HI")
        chart.save_svg(output_path=OUTPUT_DIR_STR)
        print(f"  Generated: John Lennon - HI - Synastry Chart.svg")
        charts_generated += 1
    except Exception as e:
        print(f"  ERROR generating Hindi synastry: {e}")

    print(f"\n  Total cross-combination charts: {charts_generated}")
    return charts_generated


def main():
    parser = argparse.ArgumentParser(description="Generate extended SVG charts for comprehensive test coverage")
    parser.add_argument("--all", action="store_true", help="Generate all chart types")
    parser.add_argument("--strawberry", action="store_true", help="Generate Strawberry theme charts")
    parser.add_argument("--temporal", action="store_true", help="Generate temporal subject charts")
    parser.add_argument("--geographic", action="store_true", help="Generate geographic subject charts")
    parser.add_argument("--combinations", action="store_true", help="Generate cross-combination charts")

    args = parser.parse_args()

    # If no specific flags, default to --all
    if not any([args.all, args.strawberry, args.temporal, args.geographic, args.combinations]):
        args.all = True

    total_generated = 0

    print("=" * 60)
    print("Extended SVG Chart Generation")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")

    if args.all or args.strawberry:
        total_generated += generate_strawberry_theme_charts()

    if args.all or args.temporal:
        total_generated += generate_temporal_subject_charts()

    if args.all or args.geographic:
        total_generated += generate_geographic_subject_charts()

    if args.all or args.combinations:
        total_generated += generate_cross_combination_charts()

    print("\n" + "=" * 60)
    print(f"TOTAL CHARTS GENERATED: {total_generated}")
    print("=" * 60)
    print("\nTo run the corresponding tests:")
    print("  pytest tests/charts/test_charts_parametrized.py -v")


if __name__ == "__main__":
    main()
