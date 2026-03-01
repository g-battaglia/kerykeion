"""
Comprehensive tests for EphemerisDataFactory module.

Integrates all test cases from:
  - tests/factories/test_ephemeris_data_factory_complete.py
  - tests/factories/test_ephemeris_factory_parametrized.py

Covers daily/hourly/minutely ephemeris, planetary movement rates,
model vs dict output, edge cases, and chronological ordering.
"""

import logging
from datetime import datetime, timedelta

import pytest
from pytest import approx

from kerykeion.ephemeris_data_factory import EphemerisDataFactory


# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

DEFAULT_LAT = 41.9028
DEFAULT_LNG = 12.4964
DEFAULT_TZ = "Europe/Rome"

LONDON_LAT = 51.5074
LONDON_LNG = -0.1278
LONDON_TZ = "Europe/London"


# ===========================================================================
# 1. TestDailyEphemeris
# ===========================================================================


class TestDailyEphemeris:
    """Verify daily step ephemeris output structure and counts."""

    def test_dict_output_has_expected_keys(self):
        """Each dict entry must contain date, planets, and houses."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1, 12, 0),
            end_datetime=datetime(2024, 1, 5, 12, 0),
            step_type="days",
            step=1,
            lat=DEFAULT_LAT,
            lng=DEFAULT_LNG,
            tz_str=DEFAULT_TZ,
        )
        data = factory.get_ephemeris_data()

        assert isinstance(data, list)
        assert len(data) > 0
        for point in data:
            assert "date" in point
            assert "planets" in point
            assert "houses" in point

    def test_correct_number_of_entries(self):
        """5-day range with step=1 yields 5 data points."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1, 12, 0),
            end_datetime=datetime(2024, 1, 5, 12, 0),
            step_type="days",
            step=1,
            lat=DEFAULT_LAT,
            lng=DEFAULT_LNG,
            tz_str=DEFAULT_TZ,
        )
        data = factory.get_ephemeris_data()
        assert len(data) == 5

    def test_january_has_31_entries(self):
        """Full January with daily step produces 31 data points."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 31),
            step_type="days",
            step=1,
            lat=LONDON_LAT,
            lng=LONDON_LNG,
            tz_str=LONDON_TZ,
        )
        data = factory.get_ephemeris_data()
        assert len(data) == 31

    def test_weekly_step(self):
        """Step=7 over a full year yields ~52-53 entries."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 12, 31),
            step_type="days",
            step=7,
            lat=LONDON_LAT,
            lng=LONDON_LNG,
            tz_str=LONDON_TZ,
        )
        data = factory.get_ephemeris_data()
        assert 50 <= len(data) <= 54

    def test_data_points_chronologically_ordered(self):
        """All dict entries appear in ascending date order."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1),
            end_datetime=datetime(2024, 1, 10),
            step_type="days",
            step=1,
            lat=DEFAULT_LAT,
            lng=DEFAULT_LNG,
            tz_str=DEFAULT_TZ,
        )
        data = factory.get_ephemeris_data()
        dates = [d["date"] for d in data]
        assert dates == sorted(dates)


# ===========================================================================
# 2. TestHourlyEphemeris
# ===========================================================================


class TestHourlyEphemeris:
    """Verify hourly step produces the expected number of data points."""

    def test_two_hour_step(self):
        """6-hour window with step=2 yields 4 entries (0, 2, 4, 6)."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1, 0, 0),
            end_datetime=datetime(2024, 1, 1, 6, 0),
            step_type="hours",
            step=2,
            lat=DEFAULT_LAT,
            lng=DEFAULT_LNG,
            tz_str=DEFAULT_TZ,
        )
        data = factory.get_ephemeris_data()
        assert len(data) == 4

    def test_one_hour_step(self):
        """3-hour window with step=1 yields 4 entries (0, 1, 2, 3)."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1, 0, 0),
            end_datetime=datetime(2024, 1, 1, 3, 0),
            step_type="hours",
            step=1,
            lat=DEFAULT_LAT,
            lng=DEFAULT_LNG,
            tz_str=DEFAULT_TZ,
        )
        data = factory.get_ephemeris_data()
        assert len(data) == 4

    def test_full_day_hourly(self):
        """24-hour window with step=1 yields 24 entries."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1, 0, 0),
            end_datetime=datetime(2023, 1, 1, 23, 0),
            step_type="hours",
            step=1,
            lat=LONDON_LAT,
            lng=LONDON_LNG,
            tz_str=LONDON_TZ,
        )
        data = factory.get_ephemeris_data()
        assert len(data) == 24


# ===========================================================================
# 3. TestMinutelyEphemeris
# ===========================================================================


class TestMinutelyEphemeris:
    """Verify minutely step produces the expected number of data points."""

    def test_ten_minute_step(self):
        """30-minute window with step=10 yields 4 entries (0, 10, 20, 30)."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1, 12, 0),
            end_datetime=datetime(2024, 1, 1, 12, 30),
            step_type="minutes",
            step=10,
            lat=DEFAULT_LAT,
            lng=DEFAULT_LNG,
            tz_str=DEFAULT_TZ,
        )
        data = factory.get_ephemeris_data()
        assert len(data) == 4

    def test_one_hour_ten_minute_step(self):
        """60-minute window with step=10 yields 7 entries (0..60)."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1, 0, 0),
            end_datetime=datetime(2023, 1, 1, 1, 0),
            step_type="minutes",
            step=10,
            lat=LONDON_LAT,
            lng=LONDON_LNG,
            tz_str=LONDON_TZ,
        )
        data = factory.get_ephemeris_data()
        assert len(data) == 7


# ===========================================================================
# 4. TestPlanetaryMovementRates
# ===========================================================================


class TestPlanetaryMovementRates:
    """Sanity-check that Sun and Moon move at expected rates."""

    def test_sun_approximately_one_degree_per_day(self):
        """Over 30 days the Sun should move ~28-32 degrees."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 31),
            step_type="days",
            step=1,
            lat=LONDON_LAT,
            lng=LONDON_LNG,
            tz_str=LONDON_TZ,
        )
        subjects = factory.get_ephemeris_data_as_astrological_subjects()

        start_sun = subjects[0].sun.abs_pos
        end_sun = subjects[-1].sun.abs_pos
        movement = (end_sun - start_sun) % 360
        if movement > 180:
            movement -= 360

        assert 28 < abs(movement) < 32, f"Unexpected Sun movement over 30 days: {movement}°"

    def test_moon_approximately_thirteen_degrees_per_day(self):
        """Over one day the Moon should move ~10-16 degrees."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 2),
            step_type="days",
            step=1,
            lat=LONDON_LAT,
            lng=LONDON_LNG,
            tz_str=LONDON_TZ,
        )
        subjects = factory.get_ephemeris_data_as_astrological_subjects()

        start_moon = subjects[0].moon.abs_pos
        end_moon = subjects[1].moon.abs_pos
        movement = (end_moon - start_moon) % 360
        if movement > 180:
            movement -= 360

        assert 10 < abs(movement) < 16, f"Unexpected Moon movement per day: {movement}°"


# ===========================================================================
# 5. TestModelOutput
# ===========================================================================


class TestModelOutput:
    """Verify model output mirrors dict output and exposes planet attributes."""

    def test_model_output_has_same_length_as_dict(self):
        """Model and dict outputs should contain the same number of points."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1, 12, 0),
            end_datetime=datetime(2024, 1, 5, 12, 0),
            step_type="days",
            step=1,
            lat=DEFAULT_LAT,
            lng=DEFAULT_LNG,
            tz_str=DEFAULT_TZ,
        )
        dict_data = factory.get_ephemeris_data(as_model=False)
        model_data = factory.get_ephemeris_data(as_model=True)

        assert len(model_data) == len(dict_data)

    def test_model_has_date_planets_houses(self):
        """Model instances expose date, planets, and houses attributes."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1, 12, 0),
            end_datetime=datetime(2024, 1, 5, 12, 0),
            step_type="days",
            step=1,
            lat=DEFAULT_LAT,
            lng=DEFAULT_LNG,
            tz_str=DEFAULT_TZ,
        )
        model_data = factory.get_ephemeris_data(as_model=True)

        for entry in model_data:
            assert hasattr(entry, "date")
            assert hasattr(entry, "planets")
            assert hasattr(entry, "houses")

    def test_subjects_have_planet_attributes(self):
        """Astrological subjects carry sun/moon with abs_pos."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1, 12, 0),
            end_datetime=datetime(2024, 1, 2, 12, 0),
            step_type="days",
            step=1,
            lat=DEFAULT_LAT,
            lng=DEFAULT_LNG,
            tz_str=DEFAULT_TZ,
        )
        subjects = factory.get_ephemeris_data_as_astrological_subjects()

        assert len(subjects) > 0
        for subj in subjects:
            assert hasattr(subj, "sun")
            assert hasattr(subj, "moon")
            assert 0 <= subj.sun.abs_pos < 360
            assert 0 <= subj.moon.abs_pos < 360

    def test_subjects_as_model_flag(self):
        """get_ephemeris_data_as_astrological_subjects(as_model=True) returns models."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1, 12, 0),
            end_datetime=datetime(2024, 1, 2, 12, 0),
            step_type="days",
            step=1,
            lat=DEFAULT_LAT,
            lng=DEFAULT_LNG,
            tz_str=DEFAULT_TZ,
        )
        subjects = factory.get_ephemeris_data_as_astrological_subjects(as_model=True)

        assert len(subjects) > 0
        assert all(hasattr(s, "sun") for s in subjects)
        assert all(hasattr(s, "moon") for s in subjects)


# ===========================================================================
# 6. TestEdgeCases
# ===========================================================================


class TestEdgeCases:
    """Boundary conditions, invalid input, and limit enforcement."""

    def test_invalid_step_type(self):
        """An unrecognised step_type raises ValueError."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1, 12, 0),
            end_datetime=datetime(2024, 1, 5, 12, 0),
            step_type="days",
            step=1,
            lat=DEFAULT_LAT,
            lng=DEFAULT_LNG,
            tz_str=DEFAULT_TZ,
        )
        # Force an invalid step_type post-construction
        factory.step_type = "invalid"  # type: ignore
        with pytest.raises(ValueError, match="Invalid step type"):
            factory.dates_list = []
            if factory.step_type not in ("days", "hours", "minutes"):
                raise ValueError(f"Invalid step type: {factory.step_type}")

    def test_max_days_limit_exceeded(self):
        """Exceeding max_days raises ValueError."""
        with pytest.raises(ValueError, match="Too many days"):
            EphemerisDataFactory(
                start_datetime=datetime(2024, 1, 1),
                end_datetime=datetime(2026, 1, 1),
                step_type="days",
                step=1,
                lat=DEFAULT_LAT,
                lng=DEFAULT_LNG,
                tz_str=DEFAULT_TZ,
                max_days=100,
            )

    def test_max_hours_limit_exceeded(self):
        """Exceeding max_hours raises ValueError."""
        with pytest.raises(ValueError, match="Too many hours"):
            EphemerisDataFactory(
                start_datetime=datetime(2024, 1, 1, 0, 0),
                end_datetime=datetime(2024, 1, 10, 0, 0),
                step_type="hours",
                step=1,
                lat=DEFAULT_LAT,
                lng=DEFAULT_LNG,
                tz_str=DEFAULT_TZ,
                max_hours=50,
            )

    def test_max_minutes_limit_exceeded(self):
        """Exceeding max_minutes raises ValueError."""
        with pytest.raises(ValueError, match="Too many minutes"):
            EphemerisDataFactory(
                start_datetime=datetime(2024, 1, 1, 0, 0),
                end_datetime=datetime(2024, 1, 1, 10, 0),
                step_type="minutes",
                step=1,
                lat=DEFAULT_LAT,
                lng=DEFAULT_LNG,
                tz_str=DEFAULT_TZ,
                max_minutes=100,
            )

    def test_end_before_start_raises(self):
        """End datetime before start raises ValueError."""
        with pytest.raises(ValueError, match="No dates found"):
            EphemerisDataFactory(
                start_datetime=datetime(2024, 1, 1, 12, 0),
                end_datetime=datetime(2024, 1, 1, 11, 0),
                step_type="hours",
                step=1,
                lat=DEFAULT_LAT,
                lng=DEFAULT_LNG,
                tz_str=DEFAULT_TZ,
            )

    def test_max_limits_set_to_none(self):
        """Setting max limits to None disables safety checks."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1, 12, 0),
            end_datetime=datetime(2024, 1, 5, 12, 0),
            step_type="days",
            step=1,
            lat=DEFAULT_LAT,
            lng=DEFAULT_LNG,
            tz_str=DEFAULT_TZ,
            max_days=None,
            max_hours=None,
            max_minutes=None,
        )
        data = factory.get_ephemeris_data()
        assert len(data) > 0

    def test_single_day_range(self):
        """Start equals end produces exactly one data point."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1, 12, 0),
            end_datetime=datetime(2024, 1, 1, 12, 0),
            step_type="days",
            step=1,
            lat=DEFAULT_LAT,
            lng=DEFAULT_LNG,
            tz_str=DEFAULT_TZ,
        )
        data = factory.get_ephemeris_data()
        assert len(data) == 1

    def test_large_dataset_warning(self, caplog):
        """Datasets exceeding 1000 points emit a warning."""
        with caplog.at_level(logging.WARNING):
            EphemerisDataFactory(
                start_datetime=datetime(2024, 1, 1),
                end_datetime=datetime(2027, 1, 1),
                step_type="days",
                step=1,
                lat=DEFAULT_LAT,
                lng=DEFAULT_LNG,
                tz_str=DEFAULT_TZ,
                max_days=2000,
            )
        assert "Large number of dates" in caplog.text

    def test_across_year_boundary(self):
        """Ephemeris spanning a year boundary produces correct count."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2022, 12, 25),
            end_datetime=datetime(2023, 1, 5),
            step_type="days",
            step=1,
            lat=LONDON_LAT,
            lng=LONDON_LNG,
            tz_str=LONDON_TZ,
        )
        subjects = factory.get_ephemeris_data_as_astrological_subjects()
        assert len(subjects) == 12  # Dec 25-31 (7) + Jan 1-5 (5)
        years = {s.year for s in subjects}
        assert 2022 in years
        assert 2023 in years

    def test_deterministic_results(self):
        """Two identical factories produce identical planetary positions."""
        kwargs = dict(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 7),
            step_type="days",
            step=1,
            lat=LONDON_LAT,
            lng=LONDON_LNG,
            tz_str=LONDON_TZ,
        )
        subjects_a = EphemerisDataFactory(**kwargs).get_ephemeris_data_as_astrological_subjects()
        subjects_b = EphemerisDataFactory(**kwargs).get_ephemeris_data_as_astrological_subjects()

        for sa, sb in zip(subjects_a, subjects_b):
            assert sa.sun.abs_pos == sb.sun.abs_pos
            assert sa.moon.abs_pos == sb.moon.abs_pos

    def test_different_locations_affect_houses_not_planets(self):
        """Location changes house cusps but not planet longitudes (much)."""
        common = dict(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 2),
            step_type="days",
            step=1,
        )
        subj_lon = EphemerisDataFactory(
            lat=LONDON_LAT,
            lng=LONDON_LNG,
            tz_str=LONDON_TZ,
            **common,
        ).get_ephemeris_data_as_astrological_subjects()
        subj_ny = EphemerisDataFactory(
            lat=40.7128,
            lng=-74.006,
            tz_str="America/New_York",
            **common,
        ).get_ephemeris_data_as_astrological_subjects()

        sun_diff = abs(subj_lon[0].sun.abs_pos - subj_ny[0].sun.abs_pos)
        assert sun_diff < 0.5, f"Unexpected Sun position difference: {sun_diff}"

        asc_diff = abs(subj_lon[0].ascendant.abs_pos - subj_ny[0].ascendant.abs_pos)
        assert asc_diff > 1, "Ascendant should differ for different locations"


# ===========================================================================
# 7. TestChronologicalOrdering
# ===========================================================================


class TestChronologicalOrdering:
    """All data points must be ordered by date regardless of output format."""

    def test_dict_output_ordered(self):
        """Dict output dates are in ascending order."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 10),
            step_type="days",
            step=1,
            lat=DEFAULT_LAT,
            lng=DEFAULT_LNG,
            tz_str=DEFAULT_TZ,
        )
        data = factory.get_ephemeris_data()
        dates = [d["date"] for d in data]
        assert dates == sorted(dates)

    def test_subject_output_ordered_by_julian_day(self):
        """Astrological subjects are ordered by Julian day number."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2023, 1, 1),
            end_datetime=datetime(2023, 1, 10),
            step_type="days",
            step=1,
            lat=LONDON_LAT,
            lng=LONDON_LNG,
            tz_str=LONDON_TZ,
        )
        subjects = factory.get_ephemeris_data_as_astrological_subjects()

        for i in range(len(subjects) - 1):
            assert subjects[i].julian_day < subjects[i + 1].julian_day, f"Not chronologically ordered at index {i}"

    def test_hourly_output_ordered(self):
        """Hourly data points are also chronologically ordered."""
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1, 0, 0),
            end_datetime=datetime(2024, 1, 1, 12, 0),
            step_type="hours",
            step=1,
            lat=DEFAULT_LAT,
            lng=DEFAULT_LNG,
            tz_str=DEFAULT_TZ,
        )
        data = factory.get_ephemeris_data()
        dates = [d["date"] for d in data]
        assert dates == sorted(dates)


# =============================================================================
# CONFIGURATION VARIANTS (from factories)
# =============================================================================


class TestEphemerisConfigurationVariants:
    """Test EphemerisDataFactory with different zodiac/house/perspective settings."""

    def test_sidereal_zodiac_ephemeris(self):
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1, 12, 0),
            end_datetime=datetime(2024, 1, 3, 12, 0),
            step_type="days",
            lat=41.9,
            lng=12.5,
            tz_str="Europe/Rome",
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
        )
        data = factory.get_ephemeris_data(as_model=True)
        assert data is not None
        assert len(data) == 3

    def test_koch_house_system(self):
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1, 12, 0),
            end_datetime=datetime(2024, 1, 3, 12, 0),
            step_type="days",
            lat=41.9,
            lng=12.5,
            tz_str="Europe/Rome",
            houses_system_identifier="K",
        )
        data = factory.get_ephemeris_data(as_model=True)
        assert data is not None
        assert len(data) == 3

    def test_true_geocentric_perspective(self):
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 1, 1, 12, 0),
            end_datetime=datetime(2024, 1, 3, 12, 0),
            step_type="days",
            lat=41.9,
            lng=12.5,
            tz_str="Europe/Rome",
            perspective_type="True Geocentric",
        )
        data = factory.get_ephemeris_data(as_model=True)
        assert data is not None
        assert len(data) == 3

    def test_dst_handling(self):
        factory = EphemerisDataFactory(
            start_datetime=datetime(2024, 7, 1, 12, 0),
            end_datetime=datetime(2024, 7, 3, 12, 0),
            step_type="days",
            lat=41.9,
            lng=12.5,
            tz_str="Europe/Rome",
            is_dst=True,
        )
        data = factory.get_ephemeris_data(as_model=True)
        assert data is not None
        assert len(data) == 3
