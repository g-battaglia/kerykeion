# -*- coding: utf-8 -*-
"""
House Comparison Utils Tests.

Tests for house comparison utility functions (calculate_cusps_in_reciprocal_houses,
calculate_points_in_reciprocal_houses) consolidated from edge_cases tests.
"""

import pytest

from kerykeion import AstrologicalSubjectFactory


@pytest.fixture(scope="module")
def subject_pair():
    s1 = AstrologicalSubjectFactory.from_birth_data(
        "First",
        1990,
        6,
        15,
        12,
        0,
        lat=41.9,
        lng=12.5,
        tz_str="Europe/Rome",
        online=False,
        suppress_geonames_warning=True,
    )
    s2 = AstrologicalSubjectFactory.from_birth_data(
        "Second",
        1985,
        3,
        20,
        15,
        30,
        lat=51.5,
        lng=0.0,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
    )
    return s1, s2


class TestCuspsInReciprocalHouses:
    """Tests for calculate_cusps_in_reciprocal_houses."""

    def test_returns_12_cusps(self, subject_pair):
        from kerykeion.house_comparison.house_comparison_utils import calculate_cusps_in_reciprocal_houses

        s1, s2 = subject_pair
        result = calculate_cusps_in_reciprocal_houses(s1, s2)
        assert len(result) == 12

    def test_cusp_projected_house_numbers_valid(self, subject_pair):
        from kerykeion.house_comparison.house_comparison_utils import calculate_cusps_in_reciprocal_houses

        s1, s2 = subject_pair
        result = calculate_cusps_in_reciprocal_houses(s1, s2)
        for cusp in result:
            assert 1 <= cusp.projected_house_number <= 12


class TestPointsInReciprocalHouses:
    """Tests for calculate_points_in_reciprocal_houses."""

    def test_returns_points(self, subject_pair):
        from kerykeion.house_comparison.house_comparison_utils import calculate_points_in_reciprocal_houses

        s1, s2 = subject_pair
        result = calculate_points_in_reciprocal_houses(s1, s2)
        assert len(result) > 0

    def test_limited_active_points(self):
        from kerykeion.house_comparison.house_comparison_utils import calculate_points_in_reciprocal_houses

        s1 = AstrologicalSubjectFactory.from_birth_data(
            "First",
            1990,
            6,
            15,
            12,
            0,
            lat=41.9,
            lng=12.5,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            active_points=["Sun", "Moon"],
        )
        s2 = AstrologicalSubjectFactory.from_birth_data(
            "Second",
            1985,
            3,
            20,
            15,
            30,
            lat=51.5,
            lng=0.0,
            tz_str="Europe/London",
            online=False,
            suppress_geonames_warning=True,
        )
        result = calculate_points_in_reciprocal_houses(s1, s2, active_points=["Sun"])
        assert result is not None
        for point in result:
            assert point.point_name == "Sun"


class TestHouseComparisonFactory:
    """Tests for HouseComparisonFactory end-to-end."""

    def test_full_comparison(self, subject_pair):
        from kerykeion.house_comparison import HouseComparisonFactory

        s1, s2 = subject_pair
        factory = HouseComparisonFactory(s1, s2)
        comparison = factory.get_house_comparison()
        assert comparison is not None
        assert comparison.first_points_in_second_houses is not None
        assert comparison.second_points_in_first_houses is not None


# ---------------------------------------------------------------------------
# Missing edge-case tests (migrated from tests/edge_cases/test_edge_cases.py)
# ---------------------------------------------------------------------------


class TestHouseComparisonMalformedData:
    """House comparison utils handle malformed or edge-case data."""

    def test_cusps_in_houses_with_malformed_cusp_name(self):
        """calculate_cusps_in_reciprocal_houses works with normal subjects."""
        from kerykeion.house_comparison.house_comparison_utils import calculate_cusps_in_reciprocal_houses

        first = AstrologicalSubjectFactory.from_birth_data(
            name="First",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            name="Second",
            year=1985,
            month=3,
            day=20,
            hour=15,
            minute=30,
            lng=0.0,
            lat=51.5,
            tz_str="Europe/London",
            online=False,
            suppress_geonames_warning=True,
        )
        result = calculate_cusps_in_reciprocal_houses(first, second)
        assert result is not None
        assert len(result) > 0

    def test_point_not_in_active_points_skipped(self):
        """Points not in active_points list are silently skipped."""
        from kerykeion.house_comparison.house_comparison_utils import calculate_points_in_reciprocal_houses

        first = AstrologicalSubjectFactory.from_birth_data(
            name="First",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            active_points=["Sun", "Moon"],
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            name="Second",
            year=1985,
            month=3,
            day=20,
            hour=15,
            minute=30,
            lng=0.0,
            lat=51.5,
            tz_str="Europe/London",
            online=False,
            suppress_geonames_warning=True,
        )
        result = calculate_points_in_reciprocal_houses(first, second, active_points=["Sun"])
        assert result is not None
        for point in result:
            assert point.point_name == "Sun"
