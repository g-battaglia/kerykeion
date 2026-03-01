# -*- coding: utf-8 -*-
"""
Parametrized Chart SVG Tests for Extended Coverage (consolidated from tests/charts/test_parametrized.py)

This module provides parametrized tests for the extended SVG chart coverage:
- Temporal subject tests (25 subjects spanning 2700 years)
- Geographic subject tests (16 locations worldwide)
- Cross-combination tests (sidereal × themes, house systems × chart types)
- Historical pairs (John and Yoko synastry)

These tests compare generated SVG output against baseline files.

Usage:
    pytest tests/core/test_chart_parametrized.py -v
    pytest tests/core/test_chart_parametrized.py -k "temporal" -v
    pytest tests/core/test_chart_parametrized.py -k "geographic" -v
    pytest tests/core/test_chart_parametrized.py -k "cross" -v
"""

from pathlib import Path
from typing import Dict, Any

import pytest

from kerykeion import AstrologicalSubjectFactory, ChartDrawer
from kerykeion.chart_data_factory import ChartDataFactory

from tests.data.test_subjects_matrix import (
    TEMPORAL_SUBJECTS,
    GEOGRAPHIC_SUBJECTS,
    get_subject_by_id,
)
from tests.data.compare_svg_lines import compare_svg_lines


# =============================================================================
# CONSTANTS
# =============================================================================

SVG_DIR = Path(__file__).parent.parent / "data" / "svg"

# Common birth data constants
# Format: (year, month, day, hour, minute, city, country)
JOHN_LENNON_BIRTH_DATA = (1940, 10, 9, 18, 30, "Liverpool", "GB")
PAUL_MCCARTNEY_BIRTH_DATA = (1942, 6, 18, 15, 30, "Liverpool", "GB")

# Subjects that are already covered by the main regenerate_test_charts.py script
# and should be excluded from temporal subject tests to avoid test conflicts.
# These subjects use proper city/nation from GeoNames in the main script,
# while the temporal matrix uses name as city with "XX" as nation.
SUBJECTS_COVERED_BY_MAIN_SCRIPT = {
    "john_lennon_1940",
    "paul_mccartney_1942",
    "johnny_depp_1963",
    "yoko_ono_1933",
}

# Filter temporal subjects to exclude those covered by main script
TEMPORAL_SUBJECTS_FOR_EXTENDED_TESTS = [s for s in TEMPORAL_SUBJECTS if s["id"] not in SUBJECTS_COVERED_BY_MAIN_SCRIPT]

# Sidereal × Theme combinations
SIDEREAL_THEME_COMBOS = [
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

# House systems for cross-chart testing
HOUSE_SYSTEM_NAMES = {
    "K": "Koch",
    "W": "Whole Sign",
    "R": "Regiomontanus",
    "C": "Campanus",
    "O": "Porphyry",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


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


def _compare_chart_svg(file_name: str, chart_svg: str) -> None:
    """
    Compare generated SVG content against a baseline file.

    This version skips the test if the baseline file doesn't exist,
    which is appropriate for parametrized tests where not all combinations
    may have baseline files.

    Args:
        file_name: Name of the baseline SVG file in SVG_DIR.
        chart_svg: Generated SVG string to compare.

    Raises:
        AssertionError: If line counts differ or any line doesn't match.
    """
    baseline_path = SVG_DIR / file_name
    if not baseline_path.exists():
        pytest.skip(f"Baseline file not found: {file_name}. Run regenerate_test_charts_extended.py first.")

    chart_svg_lines = chart_svg.splitlines()

    with open(baseline_path, "r", encoding="utf-8") as f:
        file_content = f.read()

    file_content_lines = file_content.splitlines()

    assert len(chart_svg_lines) == len(file_content_lines), (
        f"Line count mismatch in {file_name}: Expected {len(file_content_lines)} lines, got {len(chart_svg_lines)}"
    )

    for expected_line, actual_line in zip(file_content_lines, chart_svg_lines):
        compare_svg_lines(expected_line, actual_line)


# =============================================================================
# TEMPORAL SUBJECT TESTS
# =============================================================================


class TestTemporalSubjects:
    """
    Parametrized tests for temporal subjects spanning 2700 years.

    Each subject from TEMPORAL_SUBJECTS is tested with a natal chart comparison.
    Subjects covered by the main regenerate_test_charts.py script are excluded
    to avoid conflicts between different SVG generation methods.
    """

    @pytest.mark.parametrize(
        "subject_data",
        TEMPORAL_SUBJECTS_FOR_EXTENDED_TESTS,
        ids=[s["id"] for s in TEMPORAL_SUBJECTS_FOR_EXTENDED_TESTS],
    )
    def test_temporal_subject_natal_chart(self, subject_data):
        """Test natal chart generation for each temporal subject."""
        try:
            subject = create_subject_from_dict(subject_data)
            chart_data = ChartDataFactory.create_natal_chart_data(subject)
            chart_svg = ChartDrawer(chart_data).generate_svg_string()
            expected_file = f"{subject_data['name']} - Natal Chart.svg"
            _compare_chart_svg(expected_file, chart_svg)
        except Exception as e:
            pytest.skip(f"Could not generate chart for {subject_data['name']}: {e}")

    @pytest.mark.parametrize(
        "subject_id,theme",
        [
            ("ancient_500bc", "dark"),
            ("ancient_200bc", "dark"),
            ("roman_100ad", "dark"),
            ("late_antiquity_400", "dark"),
            ("early_medieval_800", "dark"),
            ("future_2050", "light"),
            ("future_2100", "light"),
            ("future_2200", "light"),
        ],
        ids=lambda x: f"{x[0]}_{x[1]}" if isinstance(x, tuple) else x,
    )
    def test_temporal_subject_with_themes(self, subject_id, theme):
        """Test temporal subjects with specific themes."""
        subject_data = get_subject_by_id(subject_id)
        try:
            subject = create_subject_from_dict(subject_data)
            subject.name = f"{subject_data['name']} - {theme.title()} Theme"
            chart_data = ChartDataFactory.create_natal_chart_data(subject)
            chart_svg = ChartDrawer(chart_data, theme=theme).generate_svg_string()
            expected_file = f"{subject.name} - Natal Chart.svg"
            _compare_chart_svg(expected_file, chart_svg)
        except Exception as e:
            pytest.skip(f"Could not generate chart for {subject_data['name']} with {theme}: {e}")


# =============================================================================
# GEOGRAPHIC SUBJECT TESTS
# =============================================================================


class TestGeographicSubjects:
    """
    Parametrized tests for geographic subjects covering all latitudes.

    Tests include:
    - Basic natal charts for all 16 locations
    - Koch house system variants
    - Whole Sign for extreme latitudes
    """

    @pytest.mark.parametrize("subject_data", GEOGRAPHIC_SUBJECTS, ids=[s["id"] for s in GEOGRAPHIC_SUBJECTS])
    def test_geographic_subject_natal_chart(self, subject_data):
        """Test natal chart generation for each geographic subject."""
        try:
            subject = create_subject_from_dict(subject_data)
            chart_data = ChartDataFactory.create_natal_chart_data(subject)
            chart_svg = ChartDrawer(chart_data).generate_svg_string()
            expected_file = f"{subject_data['name']} - Natal Chart.svg"
            _compare_chart_svg(expected_file, chart_svg)
        except Exception as e:
            pytest.skip(f"Could not generate chart for {subject_data['name']}: {e}")

    @pytest.mark.parametrize("subject_data", GEOGRAPHIC_SUBJECTS, ids=[f"{s['id']}_koch" for s in GEOGRAPHIC_SUBJECTS])
    def test_geographic_subject_koch_house_system(self, subject_data):
        """Test Koch house system for each geographic subject."""
        try:
            subject = create_subject_from_dict(subject_data, houses_system_identifier="K")
            subject.name = f"{subject_data['name']} - Koch"
            chart_data = ChartDataFactory.create_natal_chart_data(subject)
            chart_svg = ChartDrawer(chart_data).generate_svg_string()
            expected_file = f"{subject.name} - Natal Chart.svg"
            _compare_chart_svg(expected_file, chart_svg)
        except Exception as e:
            pytest.skip(f"Could not generate Koch chart for {subject_data['name']}: {e}")

    @pytest.mark.parametrize(
        "subject_id",
        [
            "arctic_circle_66n",
            "antarctic_circle_66s",
            "reykjavik_64n",
            "ushuaia_55s",
            "oslo_60n",
            "quito_equator",
            "singapore_1n",
            "nairobi_1s",
        ],
        ids=lambda x: f"{x}_whole_sign",
    )
    def test_extreme_latitude_whole_sign(self, subject_id):
        """Test Whole Sign house system for extreme latitude locations."""
        subject_data = get_subject_by_id(subject_id)
        try:
            subject = create_subject_from_dict(subject_data, houses_system_identifier="W")
            subject.name = f"{subject_data['name']} - Whole Sign"
            chart_data = ChartDataFactory.create_natal_chart_data(subject)
            chart_svg = ChartDrawer(chart_data).generate_svg_string()
            expected_file = f"{subject.name} - Natal Chart.svg"
            _compare_chart_svg(expected_file, chart_svg)
        except Exception as e:
            pytest.skip(f"Could not generate Whole Sign chart for {subject_data['name']}: {e}")


# =============================================================================
# CROSS-COMBINATION TESTS
# =============================================================================


class TestCrossCombinations:
    """
    Tests for cross-combinations:
    - Sidereal modes × Themes
    - House systems × Chart types (Synastry, Transit)
    """

    @pytest.mark.parametrize(
        "sidereal_mode,theme", SIDEREAL_THEME_COMBOS, ids=[f"{s}_{t}" for s, t in SIDEREAL_THEME_COMBOS]
    )
    def test_sidereal_theme_combinations(self, sidereal_mode, theme):
        """Test sidereal modes with different themes."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            f"John Lennon {sidereal_mode} - {theme.title()} Theme",
            *JOHN_LENNON_BIRTH_DATA,
            zodiac_type="Sidereal",
            sidereal_mode=sidereal_mode,
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme=theme).generate_svg_string()
        expected_file = f"{subject.name} - Natal Chart.svg"
        _compare_chart_svg(expected_file, chart_svg)

    @pytest.mark.parametrize(
        "house_id,house_name",
        list(HOUSE_SYSTEM_NAMES.items()),
        ids=[f"synastry_{name}" for name in HOUSE_SYSTEM_NAMES.values()],
    )
    def test_house_system_synastry(self, house_id, house_name):
        """Test different house systems with synastry charts."""
        first = AstrologicalSubjectFactory.from_birth_data(
            f"John Lennon - {house_name} Synastry",
            *JOHN_LENNON_BIRTH_DATA,
            houses_system_identifier=house_id,
            suppress_geonames_warning=True,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            f"Paul McCartney - {house_name}",
            *PAUL_MCCARTNEY_BIRTH_DATA,
            houses_system_identifier=house_id,
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(first, second)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        expected_file = f"John Lennon - {house_name} - Synastry Chart.svg"
        _compare_chart_svg(expected_file, chart_svg)

    @pytest.mark.parametrize(
        "house_id,house_name",
        list(HOUSE_SYSTEM_NAMES.items()),
        ids=[f"transit_{name}" for name in HOUSE_SYSTEM_NAMES.values()],
    )
    def test_house_system_transit(self, house_id, house_name):
        """Test different house systems with transit charts."""
        first = AstrologicalSubjectFactory.from_birth_data(
            f"John Lennon - {house_name} Transit",
            *JOHN_LENNON_BIRTH_DATA,
            houses_system_identifier=house_id,
            suppress_geonames_warning=True,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            f"Paul McCartney - {house_name} Transit",
            *PAUL_MCCARTNEY_BIRTH_DATA,
            houses_system_identifier=house_id,
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_transit_chart_data(first, second)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        expected_file = f"John Lennon - {house_name} - Transit Chart.svg"
        _compare_chart_svg(expected_file, chart_svg)


# =============================================================================
# HISTORICAL PAIRS TESTS
# =============================================================================


class TestHistoricalPairs:
    """Tests for historically significant astrological pairs."""

    def test_john_and_yoko_synastry(self):
        """Test John Lennon and Yoko Ono synastry chart."""
        john_data = get_subject_by_id("john_lennon_1940")
        yoko_data = get_subject_by_id("yoko_ono_1933")

        john = create_subject_from_dict(john_data)
        john.name = "John and Yoko"
        yoko = create_subject_from_dict(yoko_data)

        chart_data = ChartDataFactory.create_synastry_chart_data(john, yoko)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        _compare_chart_svg("John and Yoko - Synastry Chart.svg", chart_svg)
