#!/usr/bin/env python3
"""
Unified Regeneration Script for Kerykeion Test Data

This script regenerates all test baseline data and SVG files used by the test suite.
It consolidates the functionality of multiple regeneration scripts into one.

Usage:
    python scripts/regenerate_all.py --all              # Regenerate everything
    python scripts/regenerate_all.py --positions        # Regenerate expected positions
    python scripts/regenerate_all.py --aspects          # Regenerate expected aspects
    python scripts/regenerate_all.py --charts           # Regenerate SVG charts
    python scripts/regenerate_all.py --subjects         # Regenerate subject data (legacy)
    python scripts/regenerate_all.py --validate         # Validate current data

Examples:
    # Regenerate all data before switching ephemeris backend
    python scripts/regenerate_all.py --all

    # Regenerate only position data after code changes
    python scripts/regenerate_all.py --positions

    # Quick validation without regeneration
    python scripts/regenerate_all.py --validate
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from pprint import pformat
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from kerykeion import AstrologicalSubjectFactory
from kerykeion.aspects.aspects_factory import AspectsFactory
from kerykeion.schemas import AstrologicalPoint
from typing import get_args


# =============================================================================
# CONFIGURATION
# =============================================================================

OUTPUT_DIR = REPO_ROOT / "tests" / "data"
CHARTS_SCRIPT = REPO_ROOT / "scripts" / "regenerate_test_charts.py"

# Import test subjects matrix
try:
    from tests.data.test_subjects_matrix import (
        TEMPORAL_SUBJECTS,
        GEOGRAPHIC_SUBJECTS,
        SYNASTRY_PAIRS,
        CORE_PLANETS,
        LUNAR_NODES,
        ANGLES,
        HOUSES,
    )
except ImportError:
    # Fallback if running before module is set up
    TEMPORAL_SUBJECTS = []
    GEOGRAPHIC_SUBJECTS = []
    SYNASTRY_PAIRS = []
    CORE_PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
    LUNAR_NODES = ["mean_north_lunar_node", "true_north_lunar_node", "mean_south_lunar_node", "true_south_lunar_node"]
    ANGLES = ["ascendant", "descendant", "medium_coeli", "imum_coeli"]
    HOUSES = [
        f"{n}_house"
        for n in [
            "first",
            "second",
            "third",
            "fourth",
            "fifth",
            "sixth",
            "seventh",
            "eighth",
            "ninth",
            "tenth",
            "eleventh",
            "twelfth",
        ]
    ]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def create_subject_from_data(data: Dict[str, Any]) -> Optional[Any]:
    """Create an AstrologicalSubjectModel from subject data dictionary."""
    try:
        return AstrologicalSubjectFactory.from_birth_data(
            name=data.get("name", data["id"]),
            year=data["year"],
            month=data["month"],
            day=data["day"],
            hour=data["hour"],
            minute=data["minute"],
            lat=data["lat"],
            lng=data["lng"],
            tz_str=data["tz_str"],
            online=False,
            suppress_geonames_warning=True,
        )
    except Exception as e:
        print(f"  Warning: Could not create subject {data['id']}: {e}")
        return None


def extract_point_data(point) -> Dict[str, Any]:
    """Extract relevant data from a KerykeionPointModel."""
    if point is None:
        return {}

    data = {
        "name": point.name,
        "abs_pos": point.abs_pos,
        "position": point.position,
        "sign": point.sign,
        "sign_num": point.sign_num,
        "element": point.element,
        "quality": point.quality,
        "retrograde": getattr(point, "retrograde", None),
    }

    # Add optional attributes if present
    if hasattr(point, "speed") and point.speed is not None:
        data["speed"] = point.speed
    if hasattr(point, "declination") and point.declination is not None:
        data["declination"] = point.declination
    if hasattr(point, "house") and point.house is not None:
        data["house"] = point.house

    return data


def extract_house_data(house) -> Dict[str, Any]:
    """Extract relevant data from a house cusp."""
    if house is None:
        return {}

    return {
        "name": house.name,
        "abs_pos": house.abs_pos,
        "position": house.position,
        "sign": house.sign,
        "sign_num": house.sign_num,
        "element": house.element,
        "quality": house.quality,
    }


def extract_aspect_data(aspect) -> Dict[str, Any]:
    """Extract relevant data from an AspectModel."""
    return {
        "p1_name": aspect.p1_name,
        "p1_owner": aspect.p1_owner,
        "p1_abs_pos": aspect.p1_abs_pos,
        "p2_name": aspect.p2_name,
        "p2_owner": aspect.p2_owner,
        "p2_abs_pos": aspect.p2_abs_pos,
        "aspect": aspect.aspect,
        "orbit": aspect.orbit,
        "aspect_degrees": aspect.aspect_degrees,
        "diff": aspect.diff,
        "p1": aspect.p1,
        "p2": aspect.p2,
        "p1_speed": aspect.p1_speed,
        "p2_speed": aspect.p2_speed,
        "aspect_movement": aspect.aspect_movement,
    }


# =============================================================================
# REGENERATION FUNCTIONS
# =============================================================================


def regenerate_positions() -> None:
    """
    Regenerate expected_positions.py with position data for all test subjects.

    This generates hardcoded position data that tests compare against to ensure
    the ephemeris calculations remain consistent across backend changes.
    """
    print("\n" + "=" * 60)
    print("REGENERATING EXPECTED POSITIONS")
    print("=" * 60)

    positions: Dict[str, Dict[str, Any]] = {}

    # Process temporal subjects
    print(f"\nProcessing {len(TEMPORAL_SUBJECTS)} temporal subjects...")
    for data in TEMPORAL_SUBJECTS:
        subject_id = data["id"]
        print(f"  - {subject_id}...", end=" ")

        subject = create_subject_from_data(data)
        if subject is None:
            print("SKIPPED (ephemeris not available)")
            continue

        positions[subject_id] = {
            "metadata": {
                "name": data.get("name", subject_id),
                "year": data["year"],
                "month": data["month"],
                "day": data["day"],
                "hour": data["hour"],
                "minute": data["minute"],
                "lat": data["lat"],
                "lng": data["lng"],
                "tz_str": data["tz_str"],
                "julian_day": subject.julian_day,
                "generated_at": datetime.now().isoformat(),
            },
            "planets": {},
            "lunar_nodes": {},
            "angles": {},
            "houses": {},
        }

        # Extract planet positions
        for planet in CORE_PLANETS:
            point = getattr(subject, planet, None)
            if point:
                positions[subject_id]["planets"][planet] = extract_point_data(point)

        # Extract lunar nodes
        for node in LUNAR_NODES:
            point = getattr(subject, node, None)
            if point:
                positions[subject_id]["lunar_nodes"][node] = extract_point_data(point)

        # Extract angles
        for angle in ANGLES:
            point = getattr(subject, angle, None)
            if point:
                positions[subject_id]["angles"][angle] = extract_point_data(point)

        # Extract houses
        for house in HOUSES:
            point = getattr(subject, house, None)
            if point:
                positions[subject_id]["houses"][house] = extract_house_data(point)

        # Extract lunar phase
        if subject.lunar_phase:
            positions[subject_id]["lunar_phase"] = subject.lunar_phase.model_dump()

        print("OK")

    # Process geographic subjects (with standard date)
    print(f"\nProcessing {len(GEOGRAPHIC_SUBJECTS)} geographic subjects...")
    for data in GEOGRAPHIC_SUBJECTS:
        subject_id = data["id"]
        print(f"  - {subject_id}...", end=" ")

        # Use standard date for geographic subjects
        full_data = {
            **data,
            "year": 1990,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
        }

        subject = create_subject_from_data(full_data)
        if subject is None:
            print("SKIPPED")
            continue

        positions[subject_id] = {
            "metadata": {
                "name": data.get("name", subject_id),
                "year": 1990,
                "month": 6,
                "day": 15,
                "hour": 12,
                "minute": 0,
                "lat": data["lat"],
                "lng": data["lng"],
                "tz_str": data["tz_str"],
                "julian_day": subject.julian_day,
                "generated_at": datetime.now().isoformat(),
            },
            "planets": {},
            "lunar_nodes": {},
            "angles": {},
            "houses": {},
        }

        # Extract all positions
        for planet in CORE_PLANETS:
            point = getattr(subject, planet, None)
            if point:
                positions[subject_id]["planets"][planet] = extract_point_data(point)

        for node in LUNAR_NODES:
            point = getattr(subject, node, None)
            if point:
                positions[subject_id]["lunar_nodes"][node] = extract_point_data(point)

        for angle in ANGLES:
            point = getattr(subject, angle, None)
            if point:
                positions[subject_id]["angles"][angle] = extract_point_data(point)

        for house in HOUSES:
            point = getattr(subject, house, None)
            if point:
                positions[subject_id]["houses"][house] = extract_house_data(point)

        if subject.lunar_phase:
            positions[subject_id]["lunar_phase"] = subject.lunar_phase.model_dump()

        print("OK")

    # Write output file
    output_path = OUTPUT_DIR / "expected_positions.py"

    content = f'''"""
Expected planetary positions for test validation.

This file is auto-generated by scripts/regenerate_all.py
DO NOT EDIT MANUALLY - regenerate using: python scripts/regenerate_all.py --positions

Generated: {datetime.now().isoformat()}
Total subjects: {len(positions)}
"""

EXPECTED_POSITIONS = {pformat(positions, width=100, sort_dicts=True)}
'''

    output_path.write_text(content)
    print(f"\n✓ Written {len(positions)} subjects to {output_path.relative_to(REPO_ROOT)}")


def regenerate_aspects() -> None:
    """
    Regenerate expected_aspects.py with aspect data for all test subjects.
    """
    print("\n" + "=" * 60)
    print("REGENERATING EXPECTED ASPECTS")
    print("=" * 60)

    natal_aspects: Dict[str, List[Dict[str, Any]]] = {}
    synastry_aspects: Dict[str, List[Dict[str, Any]]] = {}

    # Natal aspects for key subjects
    key_subjects = ["john_lennon_1940", "johnny_depp_1963", "paul_mccartney_1942"]

    print(f"\nGenerating natal aspects for {len(key_subjects)} key subjects...")
    for subject_id in key_subjects:
        # Find subject data
        subject_data = None
        for data in TEMPORAL_SUBJECTS:
            if data["id"] == subject_id:
                subject_data = data
                break

        if not subject_data:
            print(f"  - {subject_id}... NOT FOUND")
            continue

        print(f"  - {subject_id}...", end=" ")
        subject = create_subject_from_data(subject_data)
        if subject is None:
            print("SKIPPED")
            continue

        aspects_result = AspectsFactory.single_chart_aspects(subject)
        natal_aspects[subject_id] = [extract_aspect_data(a) for a in aspects_result.aspects]
        print(f"OK ({len(natal_aspects[subject_id])} aspects)")

    # Synastry aspects
    print(f"\nGenerating synastry aspects for {len(SYNASTRY_PAIRS)} pairs...")
    for first_id, second_id in SYNASTRY_PAIRS:
        pair_key = f"{first_id}__x__{second_id}"
        print(f"  - {first_id} x {second_id}...", end=" ")

        # Find subject data
        first_data = None
        second_data = None
        for data in TEMPORAL_SUBJECTS:
            if data["id"] == first_id:
                first_data = data
            if data["id"] == second_id:
                second_data = data

        if not first_data or not second_data:
            print("NOT FOUND")
            continue

        first_subject = create_subject_from_data(first_data)
        second_subject = create_subject_from_data(second_data)

        if first_subject is None or second_subject is None:
            print("SKIPPED")
            continue

        aspects_result = AspectsFactory.dual_chart_aspects(first_subject, second_subject)
        synastry_aspects[pair_key] = [extract_aspect_data(a) for a in aspects_result.aspects]
        print(f"OK ({len(synastry_aspects[pair_key])} aspects)")

    # Write output file
    output_path = OUTPUT_DIR / "expected_aspects.py"

    content = f'''"""
Expected aspects for test validation.

This file is auto-generated by scripts/regenerate_all.py
DO NOT EDIT MANUALLY - regenerate using: python scripts/regenerate_all.py --aspects

Generated: {datetime.now().isoformat()}
Natal subjects: {len(natal_aspects)}
Synastry pairs: {len(synastry_aspects)}
"""

# Natal aspects keyed by subject ID
EXPECTED_NATAL_ASPECTS = {pformat(natal_aspects, width=100, sort_dicts=True)}

# Synastry aspects keyed by "subject1__x__subject2"
EXPECTED_SYNASTRY_ASPECTS = {pformat(synastry_aspects, width=100, sort_dicts=True)}
'''

    output_path.write_text(content)
    print(f"\n✓ Written aspects to {output_path.relative_to(REPO_ROOT)}")


def regenerate_charts() -> None:
    """
    Regenerate all SVG chart baselines.

    This calls the existing regenerate_test_charts.py script.
    """
    print("\n" + "=" * 60)
    print("REGENERATING SVG CHARTS")
    print("=" * 60)

    if not CHARTS_SCRIPT.exists():
        print(f"Error: Chart regeneration script not found at {CHARTS_SCRIPT}")
        return

    print(f"\nRunning {CHARTS_SCRIPT.name}...")
    result = subprocess.run(
        [sys.executable, str(CHARTS_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    if result.returncode == 0:
        print("✓ Charts regenerated successfully")
    else:
        print(f"Error regenerating charts:")
        print(result.stderr)


def regenerate_subjects() -> None:
    """
    Regenerate expected_astrological_subjects.py (legacy format).

    This maintains backward compatibility with existing tests.
    """
    print("\n" + "=" * 60)
    print("REGENERATING LEGACY SUBJECT DATA")
    print("=" * 60)

    # Run the existing script
    legacy_script = REPO_ROOT / "scripts" / "regenerate_expected_subjects.py"
    if legacy_script.exists():
        print(f"\nRunning {legacy_script.name}...")
        subprocess.run([sys.executable, str(legacy_script)], cwd=REPO_ROOT)
    else:
        print(f"Warning: Legacy script not found at {legacy_script}")


def validate_data() -> None:
    """
    Validate current test data without regenerating.

    This checks that:
    1. All required files exist
    2. Data can be loaded without errors
    3. Subject creation works for all matrix entries
    """
    print("\n" + "=" * 60)
    print("VALIDATING TEST DATA")
    print("=" * 60)

    errors = []
    warnings = []

    # Check required files
    required_files = [
        OUTPUT_DIR / "test_subjects_matrix.py",
        OUTPUT_DIR / "__init__.py",
    ]

    optional_files = [
        OUTPUT_DIR / "expected_positions.py",
        OUTPUT_DIR / "expected_aspects.py",
        OUTPUT_DIR / "expected_astrological_subjects.py",
    ]

    print("\nChecking required files...")
    for f in required_files:
        if f.exists():
            print(f"  ✓ {f.relative_to(REPO_ROOT)}")
        else:
            errors.append(f"Missing required file: {f.relative_to(REPO_ROOT)}")
            print(f"  ✗ {f.relative_to(REPO_ROOT)} - MISSING")

    print("\nChecking optional files...")
    for f in optional_files:
        if f.exists():
            print(f"  ✓ {f.relative_to(REPO_ROOT)}")
        else:
            warnings.append(f"Missing optional file: {f.relative_to(REPO_ROOT)}")
            print(f"  ! {f.relative_to(REPO_ROOT)} - NOT GENERATED")

    # Validate subject creation
    print(f"\nValidating temporal subjects ({len(TEMPORAL_SUBJECTS)})...")
    valid_temporal = 0
    for data in TEMPORAL_SUBJECTS:
        subject = create_subject_from_data(data)
        if subject:
            valid_temporal += 1
    print(f"  ✓ {valid_temporal}/{len(TEMPORAL_SUBJECTS)} subjects valid")

    print(f"\nValidating geographic subjects ({len(GEOGRAPHIC_SUBJECTS)})...")
    valid_geographic = 0
    for data in GEOGRAPHIC_SUBJECTS:
        full_data = {**data, "year": 1990, "month": 6, "day": 15, "hour": 12, "minute": 0}
        subject = create_subject_from_data(full_data)
        if subject:
            valid_geographic += 1
    print(f"  ✓ {valid_geographic}/{len(GEOGRAPHIC_SUBJECTS)} subjects valid")

    # Summary
    print("\n" + "-" * 40)
    if errors:
        print(f"ERRORS: {len(errors)}")
        for e in errors:
            print(f"  - {e}")
    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"  - {w}")
    if not errors and not warnings:
        print("All validations passed!")


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Unified regeneration script for Kerykeion test data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Regenerate all test data (positions, aspects, charts, subjects)",
    )
    parser.add_argument(
        "--positions",
        action="store_true",
        help="Regenerate expected_positions.py",
    )
    parser.add_argument(
        "--aspects",
        action="store_true",
        help="Regenerate expected_aspects.py",
    )
    parser.add_argument(
        "--charts",
        action="store_true",
        help="Regenerate SVG chart baselines",
    )
    parser.add_argument(
        "--subjects",
        action="store_true",
        help="Regenerate legacy expected_astrological_subjects.py",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate current test data without regenerating",
    )

    args = parser.parse_args()

    # If no specific option, show help
    if not any([args.all, args.positions, args.aspects, args.charts, args.subjects, args.validate]):
        parser.print_help()
        print("\nNo action specified. Use --all to regenerate everything.")
        return

    print("=" * 60)
    print("KERYKEION TEST DATA REGENERATION")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")

    if args.validate:
        validate_data()
        return

    if args.all or args.positions:
        regenerate_positions()

    if args.all or args.aspects:
        regenerate_aspects()

    if args.all or args.subjects:
        regenerate_subjects()

    if args.all or args.charts:
        regenerate_charts()

    print("\n" + "=" * 60)
    print("REGENERATION COMPLETE")
    print("=" * 60)
    print(f"Finished: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
