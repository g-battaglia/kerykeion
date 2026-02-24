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

    # New configuration-specific regeneration:
    python scripts/regenerate_all.py --house-systems    # All house system configurations
    python scripts/regenerate_all.py --sidereal-modes   # All sidereal mode configurations
    python scripts/regenerate_all.py --perspectives     # All perspective configurations
    python scripts/regenerate_all.py --returns          # Solar/Lunar return data
    python scripts/regenerate_all.py --composite        # Composite chart data
    python scripts/regenerate_all.py --ephemeris        # Ephemeris time range data
    python scripts/regenerate_all.py --configurations   # All configuration fixtures

Examples:
    # Regenerate all data before switching ephemeris backend
    python scripts/regenerate_all.py --all

    # Regenerate only position data after code changes
    python scripts/regenerate_all.py --positions

    # Quick validation without regeneration
    python scripts/regenerate_all.py --validate

    # Regenerate all configuration-specific fixtures
    python scripts/regenerate_all.py --configurations
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from pprint import pformat
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from kerykeion import AstrologicalSubjectFactory
from kerykeion.aspects.aspects_factory import AspectsFactory
from kerykeion.composite_subject_factory import CompositeSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.ephemeris_data_factory import EphemerisDataFactory


# =============================================================================
# CONFIGURATION
# =============================================================================

OUTPUT_DIR = REPO_ROOT / "tests" / "data"
CONFIGURATIONS_DIR = OUTPUT_DIR / "configurations"
CHARTS_SCRIPT = REPO_ROOT / "scripts" / "regenerate_test_charts.py"

# Import test subjects matrix
try:
    from tests.data.test_subjects_matrix import (
        TEMPORAL_SUBJECTS,
        GEOGRAPHIC_SUBJECTS,
        SYNASTRY_PAIRS,
        HOUSE_SYSTEMS,
        SIDEREAL_MODES,
        PERSPECTIVE_TYPES,
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
    HOUSE_SYSTEMS = ["P", "K", "W", "O", "R", "C", "A", "E", "V", "X", "H", "T", "B", "M", "U", "G"]
    SIDEREAL_MODES = [
        "FAGAN_BRADLEY",
        "LAHIRI",
        "DELUCE",
        "RAMAN",
        "USHASHASHI",
        "KRISHNAMURTI",
        "DJWHAL_KHUL",
        "YUKTESHWAR",
        "JN_BHASIN",
        "BABYL_KUGLER1",
        "BABYL_KUGLER2",
        "BABYL_KUGLER3",
        "BABYL_HUBER",
        "BABYL_ETPSC",
        "ALDEBARAN_15TAU",
        "HIPPARCHOS",
        "SASSANIAN",
        "J1900",
        "J2000",
        "B1950",
    ]
    PERSPECTIVE_TYPES = ["Apparent Geocentric", "True Geocentric", "Heliocentric", "Topocentric"]
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

# Key subjects for detailed testing (subset for faster regeneration)
KEY_SUBJECT_IDS = ["john_lennon_1940", "johnny_depp_1963", "paul_mccartney_1942"]

# Years for return calculations
RETURN_YEARS = [2020, 2021, 2022, 2023, 2024, 2025]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def create_subject_from_data(
    data: Dict[str, Any],
    houses_system_identifier: str = "P",
    zodiac_type: str = "Tropical",
    sidereal_mode: Optional[str] = None,
    perspective_type: str = "Apparent Geocentric",
) -> Optional[Any]:
    """Create an AstrologicalSubjectModel from subject data dictionary."""
    try:
        kwargs = {
            "name": data.get("name", data["id"]),
            "year": data["year"],
            "month": data["month"],
            "day": data["day"],
            "hour": data["hour"],
            "minute": data["minute"],
            "lat": data["lat"],
            "lng": data["lng"],
            "tz_str": data["tz_str"],
            "online": False,
            "suppress_geonames_warning": True,
            "houses_system_identifier": houses_system_identifier,
            "zodiac_type": zodiac_type,
            "perspective_type": perspective_type,
        }
        if sidereal_mode and zodiac_type == "Sidereal":
            kwargs["sidereal_mode"] = sidereal_mode

        return AstrologicalSubjectFactory.from_birth_data(**kwargs)
    except Exception as e:
        print(f"  Warning: Could not create subject {data.get('id', 'unknown')}: {e}")
        return None


def get_all_subjects_data() -> List[Dict[str, Any]]:
    """Get combined list of temporal and geographic subjects with full data."""
    all_subjects = list(TEMPORAL_SUBJECTS)

    # Add geographic subjects with standard date
    for data in GEOGRAPHIC_SUBJECTS:
        full_data = {
            **data,
            "year": 1990,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
        }
        all_subjects.append(full_data)

    return all_subjects


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


def extract_full_subject_positions(subject) -> Dict[str, Any]:
    """Extract all position data from a subject using model_dump.

    This approach is future-proof and automatically includes new fields
    like is_diurnal without requiring manual updates.
    """
    # Get the full subject dump, excluding None values and metadata fields
    full_dump = subject.model_dump(exclude_none=True)

    # Metadata fields that should not be in the position data
    metadata_fields = {
        "name",
        "city",
        "nation",
        "tz_str",
        "zodiac_type",
        "houses_system_identifier",
        "houses_system_name",
        "perspective_type",
        "iso_formatted_local_datetime",
        "iso_formatted_utc_datetime",
        "day_of_week",
        "houses_names_list",
        "active_points",
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "julian_day",
        "lat",
        "lng",
    }

    # Fields that are configuration/metadata but not position data
    config_fields = {
        "sidereal_mode",
        "altitude",
    }

    # Core planets
    planets = {}
    for planet in CORE_PLANETS:
        if planet in full_dump and full_dump[planet] is not None:
            planets[planet] = full_dump[planet]

    # Lunar nodes
    lunar_nodes = {}
    for node in LUNAR_NODES:
        if node in full_dump and full_dump[node] is not None:
            lunar_nodes[node] = full_dump[node]

    # Angles
    angles = {}
    for angle in ANGLES:
        if angle in full_dump and full_dump[angle] is not None:
            angles[angle] = full_dump[angle]

    # Houses
    houses = {}
    for house in HOUSES:
        if house in full_dump and full_dump[house] is not None:
            houses[house] = full_dump[house]

    # Build the result with the same structure as before
    positions = {
        "planets": planets,
        "lunar_nodes": lunar_nodes,
        "angles": angles,
        "houses": houses,
    }

    # Add lunar_phase if present
    if "lunar_phase" in full_dump and full_dump["lunar_phase"] is not None:
        positions["lunar_phase"] = full_dump["lunar_phase"]

    # Add is_diurnal if present (new field from sect classification)
    if "is_diurnal" in full_dump and full_dump["is_diurnal"] is not None:
        positions["is_diurnal"] = full_dump["is_diurnal"]

    # Add Arabic Parts if present
    arabic_parts = {}
    arabic_part_names = ["pars_fortunae", "pars_spiritus", "pars_amoris", "pars_fidei"]
    for part in arabic_part_names:
        if part in full_dump and full_dump[part] is not None:
            arabic_parts[part] = full_dump[part]

    if arabic_parts:
        positions["arabic_parts"] = arabic_parts

    return positions


def write_fixture_file(
    output_path: Path,
    variable_name: str,
    data: Dict[str, Any],
    description: str,
    regenerate_command: str,
) -> None:
    """Write a fixture file with standard header."""
    content = f'''"""
{description}

This file is auto-generated by scripts/regenerate_all.py
DO NOT EDIT MANUALLY - regenerate using: python scripts/regenerate_all.py {regenerate_command}

Total entries: {len(data)}
"""

{variable_name} = {pformat(data, width=100, sort_dicts=True)}
'''
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    print(f"  ✓ Written {len(data)} entries to {output_path.relative_to(REPO_ROOT)}")


# =============================================================================
# ORIGINAL REGENERATION FUNCTIONS
# =============================================================================


def regenerate_positions() -> None:
    """
    Regenerate expected_positions.py with position data for all test subjects.
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
            },
            **extract_full_subject_positions(subject),
        }
        print("OK")

    # Process geographic subjects
    print(f"\nProcessing {len(GEOGRAPHIC_SUBJECTS)} geographic subjects...")
    for data in GEOGRAPHIC_SUBJECTS:
        subject_id = data["id"]
        print(f"  - {subject_id}...", end=" ")

        full_data = {**data, "year": 1990, "month": 6, "day": 15, "hour": 12, "minute": 0}
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
            },
            **extract_full_subject_positions(subject),
        }
        print("OK")

    write_fixture_file(
        OUTPUT_DIR / "expected_positions.py",
        "EXPECTED_POSITIONS",
        positions,
        "Expected planetary positions for test validation (default configuration).",
        "--positions",
    )


def regenerate_aspects() -> None:
    """Regenerate expected_aspects.py with aspect data for all test subjects."""
    print("\n" + "=" * 60)
    print("REGENERATING EXPECTED ASPECTS")
    print("=" * 60)

    natal_aspects: Dict[str, List[Dict[str, Any]]] = {}
    synastry_aspects: Dict[str, List[Dict[str, Any]]] = {}

    # Natal aspects for key subjects
    print(f"\nGenerating natal aspects for {len(KEY_SUBJECT_IDS)} key subjects...")
    for subject_id in KEY_SUBJECT_IDS:
        subject_data = next((d for d in TEMPORAL_SUBJECTS if d["id"] == subject_id), None)
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

        first_data = next((d for d in TEMPORAL_SUBJECTS if d["id"] == first_id), None)
        second_data = next((d for d in TEMPORAL_SUBJECTS if d["id"] == second_id), None)

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
    """Regenerate all SVG chart baselines."""
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
        print("Error regenerating charts:")
        print(result.stderr)


def regenerate_subjects() -> None:
    """Regenerate expected_astrological_subjects.py (legacy format)."""
    print("\n" + "=" * 60)
    print("REGENERATING LEGACY SUBJECT DATA")
    print("=" * 60)

    legacy_script = REPO_ROOT / "scripts" / "regenerate_expected_subjects.py"
    if legacy_script.exists():
        print(f"\nRunning {legacy_script.name}...")
        subprocess.run([sys.executable, str(legacy_script)], cwd=REPO_ROOT)
    else:
        print(f"Warning: Legacy script not found at {legacy_script}")


# =============================================================================
# NEW CONFIGURATION-SPECIFIC REGENERATION FUNCTIONS
# =============================================================================


def regenerate_house_systems() -> None:
    """
    Regenerate position fixtures for all house systems.

    Creates one file per house system in tests/data/configurations/house_systems/
    """
    print("\n" + "=" * 60)
    print("REGENERATING HOUSE SYSTEM CONFIGURATIONS")
    print("=" * 60)

    output_base = CONFIGURATIONS_DIR / "house_systems"
    output_base.mkdir(parents=True, exist_ok=True)

    all_subjects_data = get_all_subjects_data()

    for house_system in HOUSE_SYSTEMS:
        print(f"\n--- House System: {house_system} ---")
        positions: Dict[str, Dict[str, Any]] = {}

        for data in all_subjects_data:
            subject_id = data["id"]
            print(f"  - {subject_id}...", end=" ")

            subject = create_subject_from_data(data, houses_system_identifier=house_system)
            if subject is None:
                print("SKIPPED")
                continue

            positions[subject_id] = {
                "metadata": {
                    "name": data.get("name", subject_id),
                    "house_system": house_system,
                },
                **extract_full_subject_positions(subject),
            }
            print("OK")

        write_fixture_file(
            output_base / f"expected_positions_house_{house_system}.py",
            "EXPECTED_POSITIONS",
            positions,
            f"Expected positions for house system {house_system}.",
            "--house-systems",
        )


def regenerate_sidereal_modes() -> None:
    """
    Regenerate position fixtures for all sidereal modes.

    Creates one file per sidereal mode in tests/data/configurations/sidereal_modes/
    """
    print("\n" + "=" * 60)
    print("REGENERATING SIDEREAL MODE CONFIGURATIONS")
    print("=" * 60)

    output_base = CONFIGURATIONS_DIR / "sidereal_modes"
    output_base.mkdir(parents=True, exist_ok=True)

    all_subjects_data = get_all_subjects_data()

    for mode in SIDEREAL_MODES:
        print(f"\n--- Sidereal Mode: {mode} ---")
        positions: Dict[str, Dict[str, Any]] = {}

        for data in all_subjects_data:
            subject_id = data["id"]
            print(f"  - {subject_id}...", end=" ")

            subject = create_subject_from_data(data, zodiac_type="Sidereal", sidereal_mode=mode)
            if subject is None:
                print("SKIPPED")
                continue

            positions[subject_id] = {
                "metadata": {
                    "name": data.get("name", subject_id),
                    "zodiac_type": "Sidereal",
                    "sidereal_mode": mode,
                },
                **extract_full_subject_positions(subject),
            }
            print("OK")

        write_fixture_file(
            output_base / f"expected_positions_sidereal_{mode}.py",
            "EXPECTED_POSITIONS",
            positions,
            f"Expected positions for sidereal mode {mode}.",
            "--sidereal-modes",
        )


def regenerate_perspectives() -> None:
    """
    Regenerate position fixtures for all perspective types.

    Creates one file per perspective in tests/data/configurations/perspectives/
    """
    print("\n" + "=" * 60)
    print("REGENERATING PERSPECTIVE CONFIGURATIONS")
    print("=" * 60)

    output_base = CONFIGURATIONS_DIR / "perspectives"
    output_base.mkdir(parents=True, exist_ok=True)

    all_subjects_data = get_all_subjects_data()

    # Skip default "Apparent Geocentric" as it's already in expected_positions.py
    non_default_perspectives = [p for p in PERSPECTIVE_TYPES if p != "Apparent Geocentric"]

    for perspective in non_default_perspectives:
        perspective_slug = perspective.lower().replace(" ", "_")
        print(f"\n--- Perspective: {perspective} ---")
        positions: Dict[str, Dict[str, Any]] = {}

        for data in all_subjects_data:
            subject_id = data["id"]
            print(f"  - {subject_id}...", end=" ")

            subject = create_subject_from_data(data, perspective_type=perspective)
            if subject is None:
                print("SKIPPED")
                continue

            positions[subject_id] = {
                "metadata": {
                    "name": data.get("name", subject_id),
                    "perspective_type": perspective,
                },
                **extract_full_subject_positions(subject),
            }
            print("OK")

        write_fixture_file(
            output_base / f"expected_positions_{perspective_slug}.py",
            "EXPECTED_POSITIONS",
            positions,
            f"Expected positions for {perspective} perspective.",
            "--perspectives",
        )


def regenerate_returns() -> None:
    """
    Regenerate planetary return fixtures.

    Creates expected_solar_returns.py and expected_lunar_returns.py
    in tests/data/configurations/returns/
    """
    print("\n" + "=" * 60)
    print("REGENERATING PLANETARY RETURNS")
    print("=" * 60)

    output_base = CONFIGURATIONS_DIR / "returns"
    output_base.mkdir(parents=True, exist_ok=True)

    solar_returns: Dict[str, Dict[str, Any]] = {}
    lunar_returns: Dict[str, Dict[str, Any]] = {}

    # Use key subjects for returns
    for subject_id in KEY_SUBJECT_IDS:
        subject_data = next((d for d in TEMPORAL_SUBJECTS if d["id"] == subject_id), None)
        if not subject_data:
            continue

        print(f"\n--- Subject: {subject_id} ---")
        subject = create_subject_from_data(subject_data)
        if subject is None:
            continue

        # Create return factory with offline coordinates
        try:
            factory = PlanetaryReturnFactory(
                subject,
                lat=subject_data["lat"],
                lng=subject_data["lng"],
                tz_str=subject_data["tz_str"],
                online=False,
            )
        except Exception as e:
            print(f"  Could not create factory: {e}")
            continue

        # Solar returns for multiple years
        print("  Generating solar returns...", end=" ")
        solar_returns[subject_id] = {"returns": {}}
        for year in RETURN_YEARS:
            try:
                return_subject = factory.next_return_from_date(year, 1, 1, return_type="Solar")
                solar_returns[subject_id]["returns"][str(year)] = {
                    "iso_datetime": return_subject.iso_formatted_utc_datetime,
                    "julian_day": return_subject.julian_day,
                    **extract_full_subject_positions(return_subject),
                }
            except Exception as e:
                print(f"Year {year} failed: {e}", end=" ")
        print(f"OK ({len(solar_returns[subject_id]['returns'])} years)")

        # Lunar returns for one year (12+ per year)
        print("  Generating lunar returns...", end=" ")
        lunar_returns[subject_id] = {"returns": []}
        try:
            # Get first few lunar returns of 2023
            for month in range(1, 13):
                return_subject = factory.next_return_from_date(2023, month, 1, return_type="Lunar")
                lunar_returns[subject_id]["returns"].append(
                    {
                        "iso_datetime": return_subject.iso_formatted_utc_datetime,
                        "julian_day": return_subject.julian_day,
                        "moon_abs_pos": return_subject.moon.abs_pos,
                        "moon_sign": return_subject.moon.sign,
                    }
                )
        except Exception as e:
            print(f"Failed: {e}", end=" ")
        print(f"OK ({len(lunar_returns[subject_id]['returns'])} returns)")

    write_fixture_file(
        output_base / "expected_solar_returns.py",
        "EXPECTED_SOLAR_RETURNS",
        solar_returns,
        "Expected solar return data for key subjects.",
        "--returns",
    )

    write_fixture_file(
        output_base / "expected_lunar_returns.py",
        "EXPECTED_LUNAR_RETURNS",
        lunar_returns,
        "Expected lunar return data for key subjects.",
        "--returns",
    )


def regenerate_composite() -> None:
    """
    Regenerate composite chart fixtures.

    Creates expected_composite_charts.py in tests/data/configurations/composite/
    """
    print("\n" + "=" * 60)
    print("REGENERATING COMPOSITE CHARTS")
    print("=" * 60)

    output_base = CONFIGURATIONS_DIR / "composite"
    output_base.mkdir(parents=True, exist_ok=True)

    composites: Dict[str, Dict[str, Any]] = {}

    print(f"\nGenerating {len(SYNASTRY_PAIRS)} composite charts...")
    for first_id, second_id in SYNASTRY_PAIRS:
        pair_key = f"{first_id}__x__{second_id}"
        print(f"  - {first_id} x {second_id}...", end=" ")

        first_data = next((d for d in TEMPORAL_SUBJECTS if d["id"] == first_id), None)
        second_data = next((d for d in TEMPORAL_SUBJECTS if d["id"] == second_id), None)

        if not first_data or not second_data:
            print("NOT FOUND")
            continue

        first_subject = create_subject_from_data(first_data)
        second_subject = create_subject_from_data(second_data)

        if first_subject is None or second_subject is None:
            print("SKIPPED")
            continue

        try:
            composite_factory = CompositeSubjectFactory(first_subject, second_subject)
            composite = composite_factory.get_midpoint_composite_subject_model()

            composites[pair_key] = {
                "metadata": {
                    "first_subject": first_id,
                    "second_subject": second_id,
                },
                **extract_full_subject_positions(composite),
            }
            print("OK")
        except Exception as e:
            print(f"FAILED: {e}")

    write_fixture_file(
        output_base / "expected_composite_charts.py",
        "EXPECTED_COMPOSITE_CHARTS",
        composites,
        "Expected composite chart data for synastry pairs.",
        "--composite",
    )


def regenerate_ephemeris() -> None:
    """
    Regenerate ephemeris data fixtures.

    Creates expected_ephemeris_ranges.py in tests/data/configurations/ephemeris/
    """
    print("\n" + "=" * 60)
    print("REGENERATING EPHEMERIS DATA")
    print("=" * 60)

    output_base = CONFIGURATIONS_DIR / "ephemeris"
    output_base.mkdir(parents=True, exist_ok=True)

    ephemeris_data: Dict[str, Dict[str, Any]] = {}

    # Test ranges
    test_ranges = [
        # Daily range for one month
        {
            "id": "daily_2023_jan",
            "start": datetime(2023, 1, 1),
            "end": datetime(2023, 1, 31),
            "step_type": "days",
            "step": 1,
        },
        # Weekly range for one year
        {
            "id": "weekly_2023",
            "start": datetime(2023, 1, 1),
            "end": datetime(2023, 12, 31),
            "step_type": "days",
            "step_value": 7,
        },
        # Hourly range for one day
        {
            "id": "hourly_2023_01_01",
            "start": datetime(2023, 1, 1, 0, 0),
            "end": datetime(2023, 1, 1, 23, 0),
            "step_type": "hours",
            "step": 1,
        },
    ]

    for range_config in test_ranges:
        range_id = range_config["id"]
        print(f"\n--- Range: {range_id} ---")

        try:
            factory = EphemerisDataFactory(
                start_datetime=range_config["start"],
                end_datetime=range_config["end"],
                step_type=range_config["step_type"],
                step=range_config["step"],
                lat=51.5074,  # London
                lng=-0.1278,
                tz_str="Europe/London",
            )

            data = factory.get_ephemeris_data()

            # Store summary and sample data points
            ephemeris_data[range_id] = {
                "metadata": {
                    "start": range_config["start"].isoformat(),
                    "end": range_config["end"].isoformat(),
                    "step_type": range_config["step_type"],
                    "step": range_config["step"],
                    "total_points": len(data),
                },
                "first_point": data[0] if data else None,
                "last_point": data[-1] if data else None,
                "sample_points": data[:: max(1, len(data) // 5)][:5] if data else [],
            }
            print(f"  Generated {len(data)} data points")
        except Exception as e:
            print(f"  FAILED: {e}")

    write_fixture_file(
        output_base / "expected_ephemeris_ranges.py",
        "EXPECTED_EPHEMERIS_RANGES",
        ephemeris_data,
        "Expected ephemeris data for various time ranges.",
        "--ephemeris",
    )


# =============================================================================
# VALIDATION
# =============================================================================


def validate_data() -> None:
    """Validate current test data without regenerating."""
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

    configuration_dirs = [
        CONFIGURATIONS_DIR / "house_systems",
        CONFIGURATIONS_DIR / "sidereal_modes",
        CONFIGURATIONS_DIR / "perspectives",
        CONFIGURATIONS_DIR / "returns",
        CONFIGURATIONS_DIR / "composite",
        CONFIGURATIONS_DIR / "ephemeris",
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

    print("\nChecking configuration directories...")
    for d in configuration_dirs:
        if d.exists():
            file_count = len(list(d.glob("*.py"))) - 1  # Exclude __init__.py
            print(f"  ✓ {d.relative_to(REPO_ROOT)} ({file_count} fixture files)")
        else:
            warnings.append(f"Missing configuration dir: {d.relative_to(REPO_ROOT)}")
            print(f"  ! {d.relative_to(REPO_ROOT)} - NOT GENERATED")

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

    # Original options
    parser.add_argument(
        "--all",
        action="store_true",
        help="Regenerate all test data (positions, aspects, charts, subjects, configurations)",
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

    # New configuration-specific options
    parser.add_argument(
        "--house-systems",
        action="store_true",
        help="Regenerate fixtures for all house systems",
    )
    parser.add_argument(
        "--sidereal-modes",
        action="store_true",
        help="Regenerate fixtures for all sidereal modes",
    )
    parser.add_argument(
        "--perspectives",
        action="store_true",
        help="Regenerate fixtures for all perspective types",
    )
    parser.add_argument(
        "--returns",
        action="store_true",
        help="Regenerate solar/lunar return fixtures",
    )
    parser.add_argument(
        "--composite",
        action="store_true",
        help="Regenerate composite chart fixtures",
    )
    parser.add_argument(
        "--ephemeris",
        action="store_true",
        help="Regenerate ephemeris data fixtures",
    )
    parser.add_argument(
        "--configurations",
        action="store_true",
        help="Regenerate all configuration-specific fixtures (house-systems, sidereal-modes, perspectives, returns, composite, ephemeris)",
    )

    args = parser.parse_args()

    # Check if any option was specified
    all_options = [
        args.all,
        args.positions,
        args.aspects,
        args.charts,
        args.subjects,
        args.validate,
        args.house_systems,
        args.sidereal_modes,
        args.perspectives,
        args.returns,
        args.composite,
        args.ephemeris,
        args.configurations,
    ]

    if not any(all_options):
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

    # Original regeneration
    if args.all or args.positions:
        regenerate_positions()

    if args.all or args.aspects:
        regenerate_aspects()

    if args.all or args.subjects:
        regenerate_subjects()

    if args.all or args.charts:
        regenerate_charts()

    # Configuration-specific regeneration
    if args.all or args.configurations or args.house_systems:
        regenerate_house_systems()

    if args.all or args.configurations or args.sidereal_modes:
        regenerate_sidereal_modes()

    if args.all or args.configurations or args.perspectives:
        regenerate_perspectives()

    if args.all or args.configurations or args.returns:
        regenerate_returns()

    if args.all or args.configurations or args.composite:
        regenerate_composite()

    if args.all or args.configurations or args.ephemeris:
        regenerate_ephemeris()

    print("\n" + "=" * 60)
    print("REGENERATION COMPLETE")
    print("=" * 60)
    print(f"Finished: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
