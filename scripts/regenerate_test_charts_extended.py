#!/usr/bin/env python3
"""
Extended SVG Chart Generation Script for Comprehensive Test Coverage

This script generates additional SVG charts beyond the base regenerate_test_charts.py:
- Themed variants of the temporal subjects (dark, black-and-white)
- Temporal subjects from test_subjects_matrix.py (25 subjects spanning 2700 years)
- Geographic subjects from test_subjects_matrix.py (16 locations)
- Cross-combinations (sidereal modes × themes, house systems × chart types)

Run this after regenerate_test_charts.py to add comprehensive coverage.

Usage:
    python scripts/regenerate_test_charts_extended.py [--all] [--themes] [--temporal] [--geographic] [--combinations]
"""

import argparse
import sys
from typing import get_args
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from functools import partial

from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory
from kerykeion.schemas.literals import KerykeionChartTheme
from kerykeion import ChartDrawer as _ChartDrawer
from kerykeion.chart_data.factory import ChartDataFactory

# Import test subject definitions
from tests.data.golden_places import golden_place
from tests.data.regeneration_guard import require_library_from_this_checkout

require_library_from_this_checkout(__file__)
from tests.data.test_subjects_matrix import (
    HOUSE_SYSTEM_NAMES,
    SIDEREAL_THEME_COMBOS,
    TEMPORAL_SUBJECTS,
    GEOGRAPHIC_SUBJECTS,
)

# This script regenerates the CLASSIC-style baselines (the modern ones live in
# generate_modern_baselines.py). The library default style became "modern" in
# v6, so pin the instance default once here rather than on every one of the
# ChartDrawer calls below. Call-site kwargs still override the partial's.
ChartDrawer = partial(_ChartDrawer, style="classic")

# Output directory
OUTPUT_DIR = project_root / "tests" / "data" / "svg"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR_STR = str(OUTPUT_DIR)

# Common birth data for John Lennon and Paul McCartney (used for synastry/transit)
# The place is NOT in the tuple: a bare city name is resolved over the network, so
# a regeneration bakes one day's coordinates into the baselines while the
# comparison expects another day's. See tests/data/golden_places.py.
JOHN_LENNON_BIRTH_DATA = (1940, 10, 9, 18, 30)
PAUL_MCCARTNEY_BIRTH_DATA = (1942, 6, 18, 15, 30)
LIVERPOOL = golden_place("Liverpool", "GB")

# Themes to test
THEMES = list(get_args(KerykeionChartTheme))

# Key sidereal modes for cross-combination testing
KEY_SIDEREAL_MODES = ["LAHIRI", "FAGAN_BRADLEY", "KRISHNAMURTI", "RAMAN", "J2000"]

# Key house systems for chart type combinations
KEY_HOUSE_SYSTEMS = ["K", "W", "R", "C", "O"]  # Koch, Whole Sign, Regiomontanus, Campanus, Porphyry


# Subjects that are already covered by the main regenerate_test_charts.py script
# and should be excluded from temporal subject generation to avoid file conflicts.
SUBJECTS_COVERED_BY_MAIN_SCRIPT = {
    "john_lennon_1940",
    "paul_mccartney_1942",
    "johnny_depp_1963",
    "yoko_ono_1933",
}


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


#: Every baseline this run could not draw. A generator that prints its failures
#: and exits 0 reports success for a set it did not produce: the file stays as it
#: was, the comparison test reads the stale one, and nothing is red. This branch
#: has already closed that shape twice — once for baselines that were never
#: generated, once for a house-system list that asked for ten and made three.
FAILURES: list[str] = []


def generate_temporal_subject_charts():
    """Generate charts for all temporal subjects from test_subjects_matrix.py."""
    print("\n=== Generating Temporal Subject Charts ===")

    charts_generated = 0

    # Generate natal chart for each temporal subject
    # Skip subjects that are already covered by the main regenerate_test_charts.py script
    for subject_data in TEMPORAL_SUBJECTS:
        subject_id = subject_data["id"]
        subject_name = subject_data["name"]

        # Skip subjects covered by main script to avoid file conflicts
        if subject_id in SUBJECTS_COVERED_BY_MAIN_SCRIPT:
            print(f"  Skipping: {subject_name} (covered by main regenerate script)")
            continue

        try:
            subject = create_subject_from_dict(subject_data)
            chart_data = ChartDataFactory.create_natal_chart_data(subject)
            chart = ChartDrawer(chart_data)
            chart.save_svg(output_path=OUTPUT_DIR_STR)
            print(f"  Generated: {subject_name} - Natal Chart - Classic.svg")
            charts_generated += 1
        except Exception as e:
            failure = f"generating {subject_name}: {e}"
            print(f"  ERROR {failure}")
            FAILURES.append(failure)

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
                print(f"  Generated: {subject.name} - Natal Chart - Classic.svg")
                charts_generated += 1
            except Exception as e:
                failure = f"generating {subject_data['name']} dark theme: {e}"
                print(f"  ERROR {failure}")
                FAILURES.append(failure)

    # Future subjects with the Black and White theme. They used to be drawn in a
    # theme called "light", which this library no longer has, and the case went on
    # skipping quietly for a release because no baseline was ever written for it
    # either — a themed case with no file behind it asserts nothing at all.
    future_ids = ["future_2050", "future_2100", "future_2200"]
    for subject_id in future_ids:
        subject_data = next((s for s in TEMPORAL_SUBJECTS if s["id"] == subject_id), None)
        if subject_data:
            try:
                subject = create_subject_from_dict(subject_data)
                subject.name = f"{subject_data['name']} - Black-And-White Theme"
                chart_data = ChartDataFactory.create_natal_chart_data(subject)
                chart = ChartDrawer(chart_data, theme="black-and-white")
                chart.save_svg(output_path=OUTPUT_DIR_STR)
                print(f"  Generated: {subject.name} - Natal Chart - Classic.svg")
                charts_generated += 1
            except Exception as e:
                failure = f"generating {subject_data['name']} black-and-white theme: {e}"
                print(f"  ERROR {failure}")
                FAILURES.append(failure)

    # Modern subjects with Synastry (John + Yoko, Beatles pairs)
    john_data = next((s for s in TEMPORAL_SUBJECTS if s["id"] == "john_lennon_1940"), None)
    yoko_data = next((s for s in TEMPORAL_SUBJECTS if s["id"] == "yoko_ono_1933"), None)

    if john_data and yoko_data:
        try:
            john = create_subject_from_dict(john_data)
            yoko = create_subject_from_dict(yoko_data)
            john.name = "John and Yoko"
            synastry_data = ChartDataFactory.create_synastry_chart_data(john, yoko)
            chart = ChartDrawer(synastry_data)
            chart.save_svg(
                output_path=OUTPUT_DIR_STR,
                filename="John and Yoko - Synastry Chart - Classic",
            )
            print("  Generated: John and Yoko - Synastry Chart - Classic.svg")
            charts_generated += 1
        except Exception as e:
            failure = f"generating John and Yoko synastry: {e}"
            print(f"  ERROR {failure}")
            FAILURES.append(failure)

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
            print(f"  Generated: {subject_name} - Natal Chart - Classic.svg")
            charts_generated += 1
        except Exception as e:
            failure = f"generating {subject_name}: {e}"
            print(f"  ERROR {failure}")
            FAILURES.append(failure)

    # Generate Koch house system variants for all geographic subjects
    for subject_data in GEOGRAPHIC_SUBJECTS:
        subject_name = subject_data["name"]

        try:
            subject = create_subject_from_dict(subject_data, houses_system_identifier="K")
            subject.name = f"{subject_name} - Koch"
            chart_data = ChartDataFactory.create_natal_chart_data(subject)
            chart = ChartDrawer(chart_data)
            chart.save_svg(output_path=OUTPUT_DIR_STR)
            print(f"  Generated: {subject.name} - Natal Chart - Classic.svg")
            charts_generated += 1
        except Exception as e:
            failure = f"generating {subject_name} Koch: {e}"
            print(f"  ERROR {failure}")
            FAILURES.append(failure)

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
                print(f"  Generated: {subject.name} - Natal Chart - Classic.svg")
                charts_generated += 1
            except Exception as e:
                failure = f"generating {subject_data['name']} Whole Sign: {e}"
                print(f"  ERROR {failure}")
                FAILURES.append(failure)

    print(f"\n  Total geographic subject charts: {charts_generated}")
    return charts_generated


def generate_cross_combination_charts():
    """Generate cross-combination charts (sidereal × themes, house systems × chart types)."""
    print("\n=== Generating Cross-Combination Charts ===")

    charts_generated = 0

    # Create base subjects
    second = AstrologicalSubjectFactory.from_birth_data(
        "Paul McCartney", *PAUL_MCCARTNEY_BIRTH_DATA, suppress_geonames_warning=True, **LIVERPOOL
    )

    # Sidereal × Themes combinations
    # From the same list the test reads, so the two cannot drift again: three
    # pairs were produced here against ten asked for there, and the seven without
    # a file skipped in silence.
    sidereal_theme_combos = SIDEREAL_THEME_COMBOS

    for sidereal_mode, theme in sidereal_theme_combos:
        try:
            subject = AstrologicalSubjectFactory.from_birth_data(
                f"John Lennon {sidereal_mode} - {theme.title()} Theme",
                *JOHN_LENNON_BIRTH_DATA,
                **LIVERPOOL,
                zodiac_type="Sidereal",
                sidereal_mode=sidereal_mode,
                suppress_geonames_warning=True,
            )
            chart_data = ChartDataFactory.create_natal_chart_data(subject)
            chart = ChartDrawer(chart_data, theme=theme)
            chart.save_svg(output_path=OUTPUT_DIR_STR)
            print(f"  Generated: {subject.name} - Natal Chart - Classic.svg")
            charts_generated += 1
        except Exception as e:
            failure = f"generating {sidereal_mode} {theme}: {e}"
            print(f"  ERROR {failure}")
            FAILURES.append(failure)

    # House Systems × Synastry combinations, from the shared matrix the test
    # reads: a second copy here is how the sidereal list came to ask for ten
    # combinations and generate three.
    for house_id, house_name in HOUSE_SYSTEM_NAMES.items():
        try:
            first_hs = AstrologicalSubjectFactory.from_birth_data(
                f"John Lennon - {house_name} Synastry",
                *JOHN_LENNON_BIRTH_DATA,
                **LIVERPOOL,
                houses_system_identifier=house_id,
                suppress_geonames_warning=True,
            )
            second_hs = AstrologicalSubjectFactory.from_birth_data(
                f"Paul McCartney - {house_name}",
                *PAUL_MCCARTNEY_BIRTH_DATA,
                **LIVERPOOL,
                houses_system_identifier=house_id,
                suppress_geonames_warning=True,
            )
            synastry_data = ChartDataFactory.create_synastry_chart_data(first_hs, second_hs)
            chart = ChartDrawer(synastry_data)
            chart.save_svg(
                output_path=OUTPUT_DIR_STR,
                filename=f"John Lennon - {house_name} - Synastry Chart - Classic",
            )
            print(f"  Generated: John Lennon - {house_name} - Synastry Chart - Classic.svg")
            charts_generated += 1
        except Exception as e:
            failure = f"generating {house_name} synastry: {e}"
            print(f"  ERROR {failure}")
            FAILURES.append(failure)

    # House Systems × Transit combinations
    for house_id, house_name in HOUSE_SYSTEM_NAMES.items():
        try:
            first_hs = AstrologicalSubjectFactory.from_birth_data(
                f"John Lennon - {house_name} Transit",
                *JOHN_LENNON_BIRTH_DATA,
                **LIVERPOOL,
                houses_system_identifier=house_id,
                suppress_geonames_warning=True,
            )
            second_hs = AstrologicalSubjectFactory.from_birth_data(
                f"Paul McCartney - {house_name} Transit",
                *PAUL_MCCARTNEY_BIRTH_DATA,
                **LIVERPOOL,
                houses_system_identifier=house_id,
                suppress_geonames_warning=True,
            )
            transit_data = ChartDataFactory.create_transit_chart_data(first_hs, second_hs)
            chart = ChartDrawer(transit_data)
            chart.save_svg(
                output_path=OUTPUT_DIR_STR,
                filename=f"John Lennon - {house_name} - Transit Chart - Classic",
            )
            print(f"  Generated: John Lennon - {house_name} - Transit Chart - Classic.svg")
            charts_generated += 1
        except Exception as e:
            failure = f"generating {house_name} transit: {e}"
            print(f"  ERROR {failure}")
            FAILURES.append(failure)

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
            filename="Angelina Jolie and Brad Pitt Composite Chart - FR - Composite Chart - Classic",
        )
        print("  Generated: Angelina Jolie and Brad Pitt Composite Chart - FR - Composite Chart - Classic.svg")
        charts_generated += 1
    except Exception as e:
        failure = f"generating French composite: {e}"
        print(f"  ERROR {failure}")
        FAILURES.append(failure)

    # Hindi Synastry
    try:
        hindi_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - HI", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True, **LIVERPOOL
        )
        synastry_data = ChartDataFactory.create_synastry_chart_data(hindi_synastry_subject, second)
        chart = ChartDrawer(synastry_data, chart_language="HI")
        chart.save_svg(output_path=OUTPUT_DIR_STR)
        print("  Generated: John Lennon - HI - Synastry Chart - Classic.svg")
        charts_generated += 1
    except Exception as e:
        failure = f"generating Hindi synastry: {e}"
        print(f"  ERROR {failure}")
        FAILURES.append(failure)

    print(f"\n  Total cross-combination charts: {charts_generated}")
    return charts_generated


def main():
    parser = argparse.ArgumentParser(description="Generate extended SVG charts for comprehensive test coverage")
    parser.add_argument("--all", action="store_true", help="Generate all chart types")
    parser.add_argument("--temporal", action="store_true", help="Generate temporal subject charts")
    parser.add_argument("--geographic", action="store_true", help="Generate geographic subject charts")
    parser.add_argument("--combinations", action="store_true", help="Generate cross-combination charts")

    args = parser.parse_args()

    # If no specific flags, default to --all
    if not any([args.all, args.temporal, args.geographic, args.combinations]):
        args.all = True

    total_generated = 0

    print("=" * 60)
    print("Extended SVG Chart Generation")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")


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
    print("  pytest tests/core/test_chart_parametrized.py -v")

    if FAILURES:
        print(f"\n{len(FAILURES)} baseline(s) could not be drawn:")
        for failure in FAILURES:
            print(f"  - {failure}")
        if any("coverage range" in failure for failure in FAILURES):
            print(
                "\nSome of these are the loaded ephemeris not reaching the date, not a "
                "bug in the drawing: the ancient baselines need a tier that covers "
                "their century. Regenerating without it would leave those files as they "
                "are while reporting success, which is why this exits non-zero."
            )
        sys.exit(1)


if __name__ == "__main__":
    main()
