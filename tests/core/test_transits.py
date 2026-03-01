"""
Comprehensive tests for TransitsTimeRangeFactory module.

Integrates all test cases from tests/factories/test_transits_time_range_factory_complete.py
and adds additional coverage for initialization, transit moments, custom configuration,
empty data paths, and full integration pipeline.
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion.transits_time_range_factory import TransitsTimeRangeFactory
from kerykeion.ephemeris_data_factory import EphemerisDataFactory
from kerykeion.schemas.kr_models import TransitsTimeRangeModel, TransitMomentModel
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS, DEFAULT_ACTIVE_ASPECTS


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def natal_subject():
    """Create a natal subject offline for reuse across tests."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Johnny Depp",
        1963,
        6,
        9,
        0,
        0,
        lat=37.7742,
        lng=-87.1133,
        tz_str="America/Chicago",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="module")
def ephemeris_subjects(natal_subject):
    """Generate a short ephemeris data series as astrological subjects."""
    start = datetime(2024, 1, 1, 12, 0)
    end = start + timedelta(days=2)
    factory = EphemerisDataFactory(
        start_datetime=start,
        end_datetime=end,
        step_type="days",
        step=1,
        lat=natal_subject.lat,
        lng=natal_subject.lng,
        tz_str=natal_subject.tz_str,
    )
    return factory.get_ephemeris_data_as_astrological_subjects()


# ===========================================================================
# 1. TestBasicInitialization
# ===========================================================================


class TestBasicInitialization:
    """Verify factory construction with various parameter combinations."""

    def test_default_parameters(self, natal_subject, ephemeris_subjects):
        """Factory with no optional args uses library defaults."""
        factory = TransitsTimeRangeFactory(natal_subject, ephemeris_subjects)

        assert factory.natal_chart == natal_subject
        assert factory.ephemeris_data_points == ephemeris_subjects
        assert factory.active_points == DEFAULT_ACTIVE_POINTS
        assert factory.active_aspects == DEFAULT_ACTIVE_ASPECTS
        assert factory.settings_file is None

    def test_custom_active_points(self, natal_subject, ephemeris_subjects):
        """Factory accepts a reduced set of active points."""
        custom_points = ["Sun", "Moon"]
        factory = TransitsTimeRangeFactory(
            natal_subject,
            ephemeris_subjects,
            active_points=custom_points,
        )
        assert factory.active_points == custom_points

    def test_custom_active_aspects(self, natal_subject, ephemeris_subjects):
        """Factory accepts custom aspect definitions."""
        custom_aspects = [{"name": "conjunction", "orb": 8}, {"name": "opposition", "orb": 8}]
        factory = TransitsTimeRangeFactory(
            natal_subject,
            ephemeris_subjects,
            active_aspects=custom_aspects,
        )
        assert factory.active_aspects == custom_aspects

    def test_settings_file_path(self, natal_subject, ephemeris_subjects, tmp_path):
        """Factory stores a Path-based settings reference."""
        settings_path = tmp_path / "test_settings.json"
        factory = TransitsTimeRangeFactory(
            natal_subject,
            ephemeris_subjects,
            settings_file=settings_path,
        )
        assert factory.settings_file == settings_path

    def test_settings_dict(self, natal_subject, ephemeris_subjects):
        """Factory stores a dict-based settings reference."""
        settings_dict = {"default_orb": 8.0}
        factory = TransitsTimeRangeFactory(
            natal_subject,
            ephemeris_subjects,
            settings_file=settings_dict,
        )
        assert factory.settings_file == settings_dict


# ===========================================================================
# 2. TestTransitMoments
# ===========================================================================


class TestTransitMoments:
    """Verify the output structure and ordering of transit moments."""

    def test_basic_transit_detection(self, natal_subject, ephemeris_subjects):
        """get_transit_moments returns a valid TransitsTimeRangeModel."""
        factory = TransitsTimeRangeFactory(natal_subject, ephemeris_subjects)
        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert result.subject == natal_subject

    def test_transit_count_matches_ephemeris(self, natal_subject, ephemeris_subjects):
        """Number of transit moment entries equals number of ephemeris points."""
        factory = TransitsTimeRangeFactory(natal_subject, ephemeris_subjects)
        result = factory.get_transit_moments()

        assert len(result.transits) == len(ephemeris_subjects)

    def test_dates_list_present(self, natal_subject, ephemeris_subjects):
        """Dates list (if present) matches ephemeris length and contains ISO strings."""
        factory = TransitsTimeRangeFactory(natal_subject, ephemeris_subjects)
        result = factory.get_transit_moments()

        if result.dates is not None:
            assert len(result.dates) == len(ephemeris_subjects)
            for date_str in result.dates:
                assert isinstance(date_str, str)
                # Must be parseable as an ISO datetime
                datetime.fromisoformat(date_str.replace("Z", "+00:00"))

    def test_moments_have_expected_fields(self, natal_subject, ephemeris_subjects):
        """Each TransitMomentModel carries a date and an aspects list."""
        factory = TransitsTimeRangeFactory(natal_subject, ephemeris_subjects)
        result = factory.get_transit_moments()

        for moment in result.transits:
            assert isinstance(moment, TransitMomentModel)
            assert hasattr(moment, "date")
            assert hasattr(moment, "aspects")
            assert isinstance(moment.aspects, list)

    def test_moments_chronologically_ordered(self, natal_subject, ephemeris_subjects):
        """Transit moments appear in ascending datetime order."""
        factory = TransitsTimeRangeFactory(natal_subject, ephemeris_subjects)
        result = factory.get_transit_moments()

        dates = [datetime.fromisoformat(m.date.replace("Z", "+00:00")) for m in result.transits]
        for i in range(len(dates) - 1):
            assert dates[i] <= dates[i + 1], (
                f"Moments not chronologically ordered at index {i}: {dates[i]} > {dates[i + 1]}"
            )

    def test_single_ephemeris_point(self, natal_subject, ephemeris_subjects):
        """Factory works correctly with a single ephemeris data point."""
        single_point = [ephemeris_subjects[0]]
        factory = TransitsTimeRangeFactory(natal_subject, single_point)
        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert len(result.transits) == 1
        assert result.subject == natal_subject
        if result.dates is not None:
            assert len(result.dates) == 1


# ===========================================================================
# 3. TestCustomConfiguration
# ===========================================================================


class TestCustomConfiguration:
    """Ensure custom points / aspects filter the output correctly."""

    def test_custom_active_points_filter(self, natal_subject, ephemeris_subjects):
        """Restricting active points still produces a valid model."""
        custom_points = ["Sun", "Moon"]
        factory = TransitsTimeRangeFactory(
            natal_subject,
            ephemeris_subjects,
            active_points=custom_points,
        )
        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert len(result.transits) == len(ephemeris_subjects)

    def test_custom_active_aspects_filter(self, natal_subject, ephemeris_subjects):
        """Restricting active aspects still produces a valid model."""
        custom_aspects = [{"name": "conjunction", "orb": 8}]
        factory = TransitsTimeRangeFactory(
            natal_subject,
            ephemeris_subjects,
            active_aspects=custom_aspects,
        )
        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert len(result.transits) == len(ephemeris_subjects)


# ===========================================================================
# 4. TestEmptyDataPath
# ===========================================================================


class TestEmptyDataPath:
    """Edge case: empty ephemeris data should yield empty results."""

    def test_empty_ephemeris_returns_empty_transits(self, natal_subject):
        """An empty ephemeris list produces zero transit moments."""
        factory = TransitsTimeRangeFactory(natal_subject, [])
        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert len(result.transits) == 0
        assert result.subject == natal_subject

    def test_empty_ephemeris_dates_field(self, natal_subject):
        """Dates list (if present) is also empty when ephemeris is empty."""
        factory = TransitsTimeRangeFactory(natal_subject, [])
        result = factory.get_transit_moments()

        if result.dates is not None:
            assert len(result.dates) == 0


# ===========================================================================
# 5. TestTransitIntegration
# ===========================================================================


class TestTransitIntegration:
    """Full pipeline: subject creation → ephemeris generation → transit detection."""

    def test_full_pipeline(self):
        """End-to-end transit calculation from scratch."""
        # 1. Create natal subject offline
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Johnny Depp",
            1963,
            6,
            9,
            0,
            0,
            lat=37.7742,
            lng=-87.1133,
            tz_str="America/Chicago",
            online=False,
            suppress_geonames_warning=True,
        )

        # 2. Generate ephemeris data
        start = datetime(2024, 1, 1, 12, 0)
        end = start + timedelta(days=3)
        ephemeris_factory = EphemerisDataFactory(
            start_datetime=start,
            end_datetime=end,
            step_type="days",
            step=1,
            lat=40.7128,
            lng=-74.006,
            tz_str="America/New_York",
        )
        ephemeris_data = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()
        assert len(ephemeris_data) == 4  # days 0, 1, 2, 3

        # 3. Calculate transits
        factory = TransitsTimeRangeFactory(
            natal_chart=subject,
            ephemeris_data_points=ephemeris_data,
        )
        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert len(result.transits) == len(ephemeris_data)
        assert result.subject == subject

        # 4. Verify every transit moment has at least a date string
        for moment in result.transits:
            assert moment.date
            assert isinstance(moment.aspects, list)

    def test_pipeline_with_hourly_ephemeris(self):
        """Pipeline works with hourly resolution."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Test",
            1990,
            3,
            21,
            14,
            30,
            lat=48.8566,
            lng=2.3522,
            tz_str="Europe/Paris",
            online=False,
            suppress_geonames_warning=True,
        )

        start = datetime(2024, 6, 1, 0, 0)
        end = datetime(2024, 6, 1, 6, 0)
        ephemeris_factory = EphemerisDataFactory(
            start_datetime=start,
            end_datetime=end,
            step_type="hours",
            step=2,
            lat=subject.lat,
            lng=subject.lng,
            tz_str=subject.tz_str,
        )
        ephemeris_data = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()
        assert len(ephemeris_data) == 4  # hours 0, 2, 4, 6

        result = TransitsTimeRangeFactory(subject, ephemeris_data).get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert len(result.transits) == 4
