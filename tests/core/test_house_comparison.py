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
        from kerykeion.house_comparison.utils import calculate_cusps_in_reciprocal_houses

        s1, s2 = subject_pair
        result = calculate_cusps_in_reciprocal_houses(s1, s2)
        assert len(result) == 12

    def test_cusp_projected_house_numbers_valid(self, subject_pair):
        from kerykeion.house_comparison.utils import calculate_cusps_in_reciprocal_houses

        s1, s2 = subject_pair
        result = calculate_cusps_in_reciprocal_houses(s1, s2)
        for cusp in result:
            assert 1 <= cusp.projected_house_number <= 12

    def test_cusp_owner_house_numbers_are_sequential(self, subject_pair):
        """Regression: every cusp used to report owner house number 1.

        The old implementation parsed the number out of the cusp name
        expecting "House 1"-style names, but the canonical names are
        "First_House".."Twelfth_House" (no digits), so the parsing always
        fell back to 1. The Nth cusp must report owner house N.
        """
        from kerykeion.house_comparison.utils import calculate_cusps_in_reciprocal_houses

        s1, s2 = subject_pair
        for cusp_subject, house_subject in ((s1, s2), (s2, s1)):
            result = calculate_cusps_in_reciprocal_houses(cusp_subject, house_subject)
            owner_numbers = [cusp.point_owner_house_number for cusp in result]
            assert owner_numbers == list(range(1, 13)), (
                f"Cusp owner house numbers {owner_numbers} are not the sequential 1..12"
            )

    def test_cusp_projected_houses_spot_checks(self, subject_pair):
        """Projected houses match placements verified against the cusp degrees.

        Reference cusp longitudes (Placidus) for the fixture pair:
            First  (1990-06-15 12:00 Rome):   H1=161.15° H4=247.71° H6=313.85°
                                              H7=341.15° H12=133.85°
            Second (1985-03-20 15:30 London): H1=152.31° H4=233.00° H5=271.48°
        """
        from kerykeion.house_comparison.utils import calculate_cusps_in_reciprocal_houses

        s1, s2 = subject_pair

        second_in_first = calculate_cusps_in_reciprocal_houses(s2, s1)
        projected = {cusp.point_name: cusp.projected_house_number for cusp in second_in_first}

        # Not the degenerate single-house output of the old all-1 bug
        assert len(set(projected.values())) > 1

        # Second's ascendant (152.31°) sits between First's H12 cusp (133.85°)
        # and First's ascendant (161.15°) -> First's house 12.
        assert projected["First_House"] == 12
        # Second's descendant (332.31°) sits between First's H6 cusp (313.85°)
        # and H7 cusp (341.15°) -> First's house 6.
        assert projected["Seventh_House"] == 6

        first_in_second = calculate_cusps_in_reciprocal_houses(s1, s2)
        projected_fw = {cusp.point_name: cusp.projected_house_number for cusp in first_in_second}

        # First's IC (247.71°) sits between Second's H4 cusp (233.00°)
        # and H5 cusp (271.48°) -> Second's house 4.
        assert projected_fw["Fourth_House"] == 4


class TestPointsInReciprocalHouses:
    """Tests for calculate_points_in_reciprocal_houses."""

    def test_returns_points(self, subject_pair):
        from kerykeion.house_comparison.utils import calculate_points_in_reciprocal_houses

        s1, s2 = subject_pair
        result = calculate_points_in_reciprocal_houses(s1, s2)
        assert len(result) > 0

    def test_limited_active_points(self):
        from kerykeion.house_comparison.utils import calculate_points_in_reciprocal_houses

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

    def test_cusp_lists_have_true_owner_house_numbers(self, subject_pair):
        """End-to-end regression: factory cusp lists are not the all-1 output."""
        from kerykeion.house_comparison import HouseComparisonFactory

        s1, s2 = subject_pair
        comparison = HouseComparisonFactory(s1, s2).get_house_comparison()
        for cusp_list in (
            comparison.first_cusps_in_second_houses,
            comparison.second_cusps_in_first_houses,
        ):
            assert [cusp.point_owner_house_number for cusp in cusp_list] == list(range(1, 13))


# ---------------------------------------------------------------------------
# Missing edge-case tests (migrated from tests/edge_cases/test_edge_cases.py)
# ---------------------------------------------------------------------------


class TestHouseComparisonMalformedData:
    """House comparison utils handle malformed or edge-case data."""

    def test_cusps_in_houses_with_malformed_cusp_name(self):
        """calculate_cusps_in_reciprocal_houses works with normal subjects."""
        from kerykeion.house_comparison.utils import calculate_cusps_in_reciprocal_houses

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
        from kerykeion.house_comparison.utils import calculate_points_in_reciprocal_houses

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
