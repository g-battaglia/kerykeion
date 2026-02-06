"""
Comprehensive Parametrized Tests for EphemerisDataFactory.

This module provides extensive test coverage for the EphemerisDataFactory
for generating time-series ephemeris data across various time ranges.

The tests verify:
- Daily ephemeris generation
- Hourly ephemeris generation
- Consistency of ephemeris data points
- Comparison against pre-generated expected fixtures
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from kerykeion.ephemeris_data_factory import EphemerisDataFactory

from tests.data.test_subjects_matrix import (
    CORE_PLANETS,
)

# Configuration directory for expected data
CONFIGURATIONS_DIR = Path(__file__).parent.parent / "data" / "configurations"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def load_expected_ephemeris() -> Optional[Dict[str, Any]]:
    """Load expected ephemeris data."""
    fixture_path = CONFIGURATIONS_DIR / "ephemeris" / "expected_ephemeris_ranges.py"

    if not fixture_path.exists():
        return None

    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("fixture", fixture_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return getattr(module, "EXPECTED_EPHEMERIS_RANGES", None)
    except (NameError, ImportError):
        # The file may contain unimportable objects
        return None


# =============================================================================
# EPHEMERIS CREATION TESTS
# =============================================================================


class TestEphemerisCreation:
    """
    Test EphemerisDataFactory for creating ephemeris data.
    """

    def test_daily_ephemeris_creation(self):
        """Test creation of daily ephemeris data."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 31),
            step_type="days",
            step=1,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
        )

        data = factory.get_ephemeris_data()

        assert data is not None
        assert isinstance(data, list)
        assert len(data) == 31  # 31 days in January

    def test_weekly_ephemeris_creation(self):
        """Test creation of weekly ephemeris data."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 12, 31),
            step_type="days",
            step=7,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
        )

        data = factory.get_ephemeris_data()

        assert data is not None
        assert isinstance(data, list)
        # Approximately 52 weeks in a year
        assert 50 <= len(data) <= 54

    def test_hourly_ephemeris_creation(self):
        """Test creation of hourly ephemeris data."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1, 0, 0),
            end_datetime=datetime(2023, 1, 1, 23, 0),
            step_type="hours",
            step=1,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
        )

        data = factory.get_ephemeris_data()

        assert data is not None
        assert isinstance(data, list)
        assert len(data) == 24  # 24 hours

    def test_minute_ephemeris_creation(self):
        """Test creation of minute-level ephemeris data."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1, 0, 0),
            end_datetime=datetime(2023, 1, 1, 1, 0),
            step_type="minutes",
            step=10,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
        )

        data = factory.get_ephemeris_data()

        assert data is not None
        assert isinstance(data, list)
        # 60 minutes / 10 = 6 data points + 1 for end
        assert len(data) == 7


# =============================================================================
# EPHEMERIS DATA STRUCTURE TESTS
# =============================================================================


class TestEphemerisDataStructure:
    """
    Test the structure of ephemeris data points.
    """

    def test_ephemeris_data_point_structure(self):
        """Test that each data point has expected structure."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 7),
            step_type="days",
            step=1,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
        )

        data = factory.get_ephemeris_data()

        for point in data:
            # Should be a dictionary with date and planets keys
            assert point is not None
            assert isinstance(point, dict)

            # Check that it has expected keys
            assert "date" in point
            assert "planets" in point

            # Check for planet data in the planets list
            planet_names = [p.name.lower() for p in point["planets"]]
            for planet in CORE_PLANETS:
                assert planet in planet_names, f"Missing {planet} in ephemeris point"

    def test_ephemeris_as_subjects(self):
        """Test getting ephemeris as full astrological subjects."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 3),
            step_type="days",
            step=1,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
        )

        subjects = factory.get_ephemeris_data_as_astrological_subjects()

        assert subjects is not None
        assert isinstance(subjects, list)
        assert len(subjects) == 3

        for subject in subjects:
            # Should be a full subject with all planets
            assert hasattr(subject, "sun")
            assert hasattr(subject, "moon")
            assert 0 <= subject.sun.abs_pos < 360


# =============================================================================
# EPHEMERIS PROGRESSION TESTS
# =============================================================================


class TestEphemerisProgression:
    """
    Test that ephemeris data shows expected planetary movement.
    """

    def test_sun_moves_approximately_one_degree_per_day(self):
        """Test that the Sun moves approximately 1 degree per day."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 31),
            step_type="days",
            step=1,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
        )

        subjects = factory.get_ephemeris_data_as_astrological_subjects()

        # Calculate total Sun movement
        start_sun = subjects[0].sun.abs_pos
        end_sun = subjects[-1].sun.abs_pos

        # Handle wrap-around at 0/360
        movement = (end_sun - start_sun) % 360
        if movement > 180:
            movement = movement - 360

        # Sun moves about 1 degree per day, so 30 days ≈ 30 degrees
        assert 28 < abs(movement) < 32, f"Unexpected Sun movement over 30 days: {movement} degrees"

    def test_moon_moves_approximately_13_degrees_per_day(self):
        """Test that the Moon moves approximately 13 degrees per day."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 2),
            step_type="days",
            step=1,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
        )

        subjects = factory.get_ephemeris_data_as_astrological_subjects()

        start_moon = subjects[0].moon.abs_pos
        end_moon = subjects[1].moon.abs_pos

        # Handle wrap-around
        movement = (end_moon - start_moon) % 360
        if movement > 180:
            movement = movement - 360

        # Moon moves about 12-14 degrees per day
        assert 10 < abs(movement) < 16, f"Unexpected Moon movement per day: {movement} degrees"

    def test_ephemeris_is_chronologically_ordered(self):
        """Test that ephemeris data points are in chronological order."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 10),
            step_type="days",
            step=1,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
        )

        subjects = factory.get_ephemeris_data_as_astrological_subjects()

        for i in range(len(subjects) - 1):
            current_jd = subjects[i].julian_day
            next_jd = subjects[i + 1].julian_day

            assert next_jd > current_jd, f"Ephemeris not chronologically ordered at index {i}"


# =============================================================================
# EXPECTED DATA COMPARISON TESTS
# =============================================================================


class TestEphemerisExpectedData:
    """
    Test ephemeris data against pre-generated expected fixtures.
    """

    def test_daily_ephemeris_matches_expected(self):
        """Test that daily ephemeris matches expected values."""
        expected_data = load_expected_ephemeris()

        if expected_data is None:
            pytest.skip("No expected ephemeris data available")

        if "daily_2023_jan" not in expected_data:
            pytest.skip("No expected data for daily_2023_jan")

        expected = expected_data["daily_2023_jan"]

        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 31),
            step_type="days",
            step=1,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
        )

        data = factory.get_ephemeris_data()

        # Compare total points
        assert len(data) == expected["metadata"]["total_points"], (
            f"Data point count mismatch: expected {expected['metadata']['total_points']}, got {len(data)}"
        )

    def test_weekly_ephemeris_matches_expected(self):
        """Test that weekly ephemeris matches expected values."""
        expected_data = load_expected_ephemeris()

        if expected_data is None:
            pytest.skip("No expected ephemeris data available")

        if "weekly_2023" not in expected_data:
            pytest.skip("No expected data for weekly_2023")

        expected = expected_data["weekly_2023"]

        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 12, 31),
            step_type="days",
            step=7,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
        )

        data = factory.get_ephemeris_data()

        # Compare total points
        assert len(data) == expected["metadata"]["total_points"]


# =============================================================================
# CONFIGURATION TESTS
# =============================================================================


class TestEphemerisConfigurations:
    """
    Test ephemeris with different configurations.
    """

    def test_ephemeris_with_different_locations(self):
        """Test that location affects house positions but not planets."""
        factory_london = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 2),
            step_type="days",
            step=1,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
        )

        factory_ny = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 2),
            step_type="days",
            step=1,
            lat=40.7128,
            lng=-74.0060,
            tz_str="America/New_York",
        )

        subjects_london = factory_london.get_ephemeris_data_as_astrological_subjects()
        subjects_ny = factory_ny.get_ephemeris_data_as_astrological_subjects()

        # Sun position should be similar (minor differences due to topocentric and timezone)
        sun_diff = abs(subjects_london[0].sun.abs_pos - subjects_ny[0].sun.abs_pos)
        assert sun_diff < 0.5, f"Unexpected Sun position difference: {sun_diff}"

        # Ascendant should be different
        asc_diff = abs(subjects_london[0].ascendant.abs_pos - subjects_ny[0].ascendant.abs_pos)
        assert asc_diff > 1, "Ascendant should differ for different locations"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


class TestEphemerisEdgeCases:
    """
    Test ephemeris edge cases.
    """

    def test_ephemeris_across_year_boundary(self):
        """Test ephemeris that spans year boundary."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2022, 12, 25),
            end_datetime=datetime(2023, 1, 5),
            step_type="days",
            step=1,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
        )

        subjects = factory.get_ephemeris_data_as_astrological_subjects()

        assert len(subjects) == 12  # Dec 25-31 (7) + Jan 1-5 (5) = 12

        # Verify year change
        years = [s.year for s in subjects]
        assert 2022 in years
        assert 2023 in years

    def test_ephemeris_single_point(self):
        """Test ephemeris for a single point in time."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 1),
            step_type="days",
            step=1,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
        )

        subjects = factory.get_ephemeris_data_as_astrological_subjects()

        assert len(subjects) == 1

    def test_ephemeris_deterministic(self):
        """Test that ephemeris calculations are deterministic."""
        factory1 = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 7),
            step_type="days",
            step=1,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
        )

        factory2 = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 7),
            step_type="days",
            step=1,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
        )

        subjects1 = factory1.get_ephemeris_data_as_astrological_subjects()
        subjects2 = factory2.get_ephemeris_data_as_astrological_subjects()

        for s1, s2 in zip(subjects1, subjects2):
            assert s1.sun.abs_pos == s2.sun.abs_pos
            assert s1.moon.abs_pos == s2.moon.abs_pos
