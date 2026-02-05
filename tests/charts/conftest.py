# -*- coding: utf-8 -*-
"""
Shared fixtures, helpers, and constants for chart SVG tests.

This module provides common utilities for all chart test files:
- Birth data constants for test subjects
- Helper function to compare SVG content against baselines
- Subject factory helpers for creating test subjects with different configurations
- Pytest fixtures for commonly used subjects
"""

from pathlib import Path
from typing import Optional, List, Dict, Any

import pytest

from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS, TRADITIONAL_ASTROLOGY_ACTIVE_POINTS

from .compare_svg_lines import compare_svg_lines


# =============================================================================
# CONSTANTS
# =============================================================================

SVG_DIR = Path(__file__).parent / "svg"

# Common birth data constants
# Format: (year, month, day, hour, minute, city, country)
JOHN_LENNON_BIRTH_DATA = (1940, 10, 9, 18, 30, "Liverpool", "GB")
PAUL_MCCARTNEY_BIRTH_DATA = (1942, 6, 18, 15, 30, "Liverpool", "GB")

# House system identifiers with their names
HOUSE_SYSTEM_NAMES = {
    "A": "Equal",
    "B": "Alcabitius",
    "C": "Campanus",
    "D": "Equal MC",
    "F": "Carter",
    "H": "Horizon",
    "I": "Sunshine",
    "i": "Sunshine Alt",
    "K": "Koch",
    "L": "Pullen SD",
    "M": "Morinus",
    "N": "Equal Aries",
    "O": "Porphyry",
    "P": "Placidus",
    "Q": "Pullen SR",
    "R": "Regiomontanus",
    "S": "Sripati",
    "T": "Polich Page",
    "U": "Krusinski",
    "V": "Vehlow",
    "W": "Whole Sign",
    "X": "Meridian",
    "Y": "APC",
}

# Sidereal modes and their display names
SIDEREAL_MODES = {
    "LAHIRI": "Lahiri",
    "FAGAN_BRADLEY": "Fagan-Bradley",
    "DELUCE": "DeLuce",
    "J2000": "J2000",
    "RAMAN": "Raman",
    "USHASHASHI": "Ushashashi",
    "KRISHNAMURTI": "Krishnamurti",
    "DJWHAL_KHUL": "Djwhal Khul",
    "YUKTESHWAR": "Yukteshwar",
    "JN_BHASIN": "JN Bhasin",
    "BABYL_KUGLER1": "Babyl Kugler1",
    "BABYL_KUGLER2": "Babyl Kugler2",
    "BABYL_KUGLER3": "Babyl Kugler3",
    "BABYL_HUBER": "Babyl Huber",
    "BABYL_ETPSC": "Babyl Etpsc",
    "ALDEBARAN_15TAU": "Aldebaran 15Tau",
    "HIPPARCHOS": "Hipparchos",
    "SASSANIAN": "Sassanian",
    "J1900": "J1900",
    "B1950": "B1950",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def compare_chart_svg(file_name: str, chart_svg: str) -> None:
    """
    Compare generated SVG content against a baseline file.

    Args:
        file_name: Name of the baseline SVG file in SVG_DIR.
        chart_svg: Generated SVG string to compare.

    Raises:
        AssertionError: If line counts differ or any line doesn't match.
    """
    chart_svg_lines = chart_svg.splitlines()

    with open(SVG_DIR / file_name, "r", encoding="utf-8") as f:
        file_content = f.read()

    file_content_lines = file_content.splitlines()

    assert len(chart_svg_lines) == len(file_content_lines), (
        f"Line count mismatch in {file_name}: Expected {len(file_content_lines)} lines, got {len(chart_svg_lines)}"
    )

    for expected_line, actual_line in zip(file_content_lines, chart_svg_lines):
        compare_svg_lines(expected_line, actual_line)


def create_john_lennon_subject(
    name_suffix: str = "",
    *,
    zodiac_type: str = "Tropical",
    sidereal_mode: Optional[str] = None,
    houses_system_identifier: str = "P",
    perspective_type: str = "Apparent Geocentric",
    active_points: Optional[list] = None,
):
    """
    Create a John Lennon astrological subject with custom parameters.

    Args:
        name_suffix: Suffix to append to "John Lennon" name.
        zodiac_type: "Tropical" or "Sidereal".
        sidereal_mode: Sidereal mode (e.g., "LAHIRI", "FAGAN_BRADLEY").
        houses_system_identifier: House system letter (e.g., "P" for Placidus).
        perspective_type: Perspective type (e.g., "Heliocentric").
        active_points: List of active points to include.

    Returns:
        AstrologicalSubjectModel: Configured subject for testing.
    """
    name = f"John Lennon{' - ' + name_suffix if name_suffix else ''}"
    kwargs = {
        "suppress_geonames_warning": True,
        "zodiac_type": zodiac_type,
        "houses_system_identifier": houses_system_identifier,
        "perspective_type": perspective_type,
    }
    if sidereal_mode:
        kwargs["sidereal_mode"] = sidereal_mode
    if active_points:
        kwargs["active_points"] = active_points

    return AstrologicalSubjectFactory.from_birth_data(name, *JOHN_LENNON_BIRTH_DATA, **kwargs)


def create_paul_mccartney_subject(
    name_suffix: str = "",
    *,
    perspective_type: str = "Apparent Geocentric",
    houses_system_identifier: str = "P",
    active_points: Optional[list] = None,
):
    """
    Create a Paul McCartney astrological subject with custom parameters.

    Args:
        name_suffix: Suffix to append to "Paul McCartney" name.
        perspective_type: Perspective type (e.g., "Heliocentric").
        houses_system_identifier: House system letter.
        active_points: List of active points to include.

    Returns:
        AstrologicalSubjectModel: Configured subject for testing.
    """
    name = f"Paul McCartney{' - ' + name_suffix if name_suffix else ''}"
    kwargs = {
        "suppress_geonames_warning": True,
        "perspective_type": perspective_type,
        "houses_system_identifier": houses_system_identifier,
    }
    if active_points:
        kwargs["active_points"] = active_points

    return AstrologicalSubjectFactory.from_birth_data(name, *PAUL_MCCARTNEY_BIRTH_DATA, **kwargs)


def create_sidereal_subject(name_suffix: str, sidereal_mode: str):
    """Create a sidereal subject with consistent naming."""
    return AstrologicalSubjectFactory.from_birth_data(
        f"John Lennon {name_suffix}",
        *JOHN_LENNON_BIRTH_DATA,
        zodiac_type="Sidereal",
        sidereal_mode=sidereal_mode,
        suppress_geonames_warning=True,
    )


def create_return_factory(first_subject):
    """Create a PlanetaryReturnFactory for a subject with offline settings."""
    return PlanetaryReturnFactory(
        first_subject,
        lng=-2.9833,
        lat=53.4000,
        tz_str="Europe/London",
        online=False,
    )


# Subjects that are already covered by the main regenerate_test_charts.py script
# and should be excluded from temporal subject tests to avoid test conflicts.
SUBJECTS_COVERED_BY_MAIN_SCRIPT = {
    "john_lennon_1940",
    "paul_mccartney_1942",
    "johnny_depp_1963",
    "yoko_ono_1933",
}


def create_subject_from_dict(subject_dict: Dict[str, Any], **kwargs):
    """Create an AstrologicalSubjectModel from a subject dictionary."""
    # Geographic subjects don't have year/month/day - use default date
    if "year" not in subject_dict:
        return AstrologicalSubjectFactory.from_birth_data(
            subject_dict["name"],
            1990,
            6,
            21,
            12,
            0,
            subject_dict["name"],
            "XX",
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
            subject_dict["name"],
            "XX",
            lat=subject_dict["lat"],
            lng=subject_dict["lng"],
            tz_str=subject_dict["tz_str"],
            suppress_geonames_warning=True,
            **kwargs,
        )


# =============================================================================
# PYTEST FIXTURES
# =============================================================================


@pytest.fixture(scope="module")
def john_lennon():
    """John Lennon - primary test subject."""
    return AstrologicalSubjectFactory.from_birth_data(
        "John Lennon", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
    )


@pytest.fixture(scope="module")
def paul_mccartney():
    """Paul McCartney - secondary test subject."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Paul McCartney", *PAUL_MCCARTNEY_BIRTH_DATA, suppress_geonames_warning=True
    )


@pytest.fixture(scope="module")
def angelina_jolie():
    """Angelina Jolie - for composite chart tests."""
    return AstrologicalSubjectFactory.from_birth_data(
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


@pytest.fixture(scope="module")
def brad_pitt():
    """Brad Pitt - for composite chart tests."""
    return AstrologicalSubjectFactory.from_birth_data(
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


# =============================================================================
# SIDEREAL SUBJECT FIXTURES
# =============================================================================


@pytest.fixture(scope="module")
def lahiri_subject():
    """John Lennon with Lahiri sidereal mode."""
    return create_sidereal_subject("Lahiri", "LAHIRI")


@pytest.fixture(scope="module")
def fagan_bradley_subject():
    """John Lennon with Fagan-Bradley sidereal mode."""
    return create_sidereal_subject("Fagan-Bradley", "FAGAN_BRADLEY")


@pytest.fixture(scope="module")
def deluce_subject():
    """John Lennon with DeLuce sidereal mode."""
    return create_sidereal_subject("DeLuce", "DELUCE")


@pytest.fixture(scope="module")
def j2000_subject():
    """John Lennon with J2000 sidereal mode."""
    return create_sidereal_subject("J2000", "J2000")


# =============================================================================
# ALL ACTIVE POINTS FIXTURES
# =============================================================================


@pytest.fixture(scope="module")
def all_active_points_subject():
    """John Lennon with all active points enabled."""
    return AstrologicalSubjectFactory.from_birth_data(
        "John Lennon - All Active Points",
        *JOHN_LENNON_BIRTH_DATA,
        suppress_geonames_warning=True,
        active_points=ALL_ACTIVE_POINTS,
    )


@pytest.fixture(scope="module")
def all_active_points_second_subject():
    """Paul McCartney with all active points enabled."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Paul McCartney - All Active Points",
        *PAUL_MCCARTNEY_BIRTH_DATA,
        suppress_geonames_warning=True,
        active_points=ALL_ACTIVE_POINTS,
    )


# =============================================================================
# LANGUAGE TEST FIXTURES
# =============================================================================


@pytest.fixture(scope="module")
def chinese_subject():
    """Hua Chenyu - Chinese subject."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Hua Chenyu", 1990, 2, 7, 12, 0, "Hunan", "CN", suppress_geonames_warning=True
    )


@pytest.fixture(scope="module")
def french_subject():
    """Jeanne Moreau - French subject."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Jeanne Moreau", 1928, 1, 23, 10, 0, "Paris", "FR", suppress_geonames_warning=True
    )


@pytest.fixture(scope="module")
def spanish_subject():
    """Antonio Banderas - Spanish subject."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Antonio Banderas", 1960, 8, 10, 12, 0, "Malaga", "ES", suppress_geonames_warning=True
    )


@pytest.fixture(scope="module")
def portuguese_subject():
    """Cristiano Ronaldo - Portuguese subject."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Cristiano Ronaldo", 1985, 2, 5, 5, 25, "Funchal", "PT", suppress_geonames_warning=True
    )


@pytest.fixture(scope="module")
def italian_subject():
    """Sophia Loren - Italian subject."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Sophia Loren", 1934, 9, 20, 2, 0, "Rome", "IT", suppress_geonames_warning=True
    )


@pytest.fixture(scope="module")
def russian_subject():
    """Mikhail Bulgakov - Russian subject."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Mikhail Bulgakov", 1891, 5, 15, 12, 0, "Kiev", "UA", suppress_geonames_warning=True
    )


@pytest.fixture(scope="module")
def turkish_subject():
    """Mehmet Oz - Turkish subject."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Mehmet Oz", 1960, 6, 11, 12, 0, "Istanbul", "TR", suppress_geonames_warning=True
    )


@pytest.fixture(scope="module")
def german_subject():
    """Albert Einstein - German subject."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Albert Einstein", 1879, 3, 14, 11, 30, "Ulm", "DE", suppress_geonames_warning=True
    )


@pytest.fixture(scope="module")
def hindi_subject():
    """Amitabh Bachchan - Hindi subject."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Amitabh Bachchan", 1942, 10, 11, 4, 0, "Allahabad", "IN", suppress_geonames_warning=True
    )
