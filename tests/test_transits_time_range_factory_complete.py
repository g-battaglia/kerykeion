"""
Comprehensive tests for TransitsTimeRangeFactory module.
This test suite aims to achieve 100% code coverage.
"""

from datetime import datetime, timedelta
from pathlib import Path

from kerykeion import AstrologicalSubjectFactory
from kerykeion.transits_time_range_factory import TransitsTimeRangeFactory
from kerykeion.ephemeris_data_factory import EphemerisDataFactory
from kerykeion.schemas.kr_models import TransitsTimeRangeModel
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS, DEFAULT_ACTIVE_ASPECTS


class TestTransitsTimeRangeFactory:
    """Test cases for TransitsTimeRangeFactory covering all code paths."""

    def setup_method(self):
        """Setup for each test method."""
        # Create a basic natal chart for testing
        self.natal_chart = AstrologicalSubjectFactory.from_birth_data(
            name="Test Subject",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=30,
            lat=40.7128,
            lng=-74.0060,
            tz_str="America/New_York",
            city="New York",
            nation="US",
            suppress_geonames_warning=True
        )

        # Create test ephemeris data
        start_date = datetime(2024, 1, 1, 12, 0)
        end_date = start_date + timedelta(days=2)

        ephemeris_factory = EphemerisDataFactory(
            start_datetime=start_date,
            end_datetime=end_date,
            step_type="days",
            step=1,
            lat=self.natal_chart.lat,
            lng=self.natal_chart.lng,
            tz_str=self.natal_chart.tz_str,
        )

        self.ephemeris_data = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()

    def test_basic_factory_initialization(self):
        """Test basic factory creation with default parameters."""
        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data
        )

        assert factory.natal_chart == self.natal_chart
        assert factory.ephemeris_data_points == self.ephemeris_data
        assert factory.active_points == DEFAULT_ACTIVE_POINTS
        assert factory.active_aspects == DEFAULT_ACTIVE_ASPECTS
        assert factory.settings_file is None

    def test_factory_with_custom_active_points(self):
        """Test factory creation with custom active points."""
        custom_points = ["Sun", "Moon"]

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data,
            active_points=custom_points
        )

        assert factory.active_points == custom_points

    def test_factory_with_custom_active_aspects(self):
        """Test factory creation with custom active aspects."""
        custom_aspects = [{"name": "conjunction", "orb": 8}, {"name": "opposition", "orb": 8}]

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data,
            active_aspects=custom_aspects
        )

        assert factory.active_aspects == custom_aspects

    def test_factory_with_settings_file_path(self):
        """Test factory creation with settings file path."""
        settings_path = Path("/tmp/test_settings.json")

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data,
            settings_file=settings_path
        )

        assert factory.settings_file == settings_path

    def test_factory_with_settings_dict(self):
        """Test factory creation with settings dictionary."""
        settings_dict = {"default_orb": 8.0}

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data,
            settings_file=settings_dict
        )

        assert factory.settings_file == settings_dict

    def test_get_transit_moments_basic(self):
        """Test basic transit moments calculation."""
        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data
        )

        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert result.subject == self.natal_chart

        # Check dates (Optional field)
        if result.dates is not None:
            assert len(result.dates) == len(self.ephemeris_data)
            # Check that all dates are ISO formatted strings
            for date_str in result.dates:
                assert isinstance(date_str, str)
                # Should be parseable as datetime
                datetime.fromisoformat(date_str.replace('Z', '+00:00'))

        assert len(result.transits) == len(self.ephemeris_data)

    def test_get_transit_moments_with_custom_points(self):
        """Test transit moments with custom active points."""
        custom_points = ["Sun", "Moon"]

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data,
            active_points=custom_points
        )

        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert len(result.transits) == len(self.ephemeris_data)

    def test_get_transit_moments_with_custom_aspects(self):
        """Test transit moments with custom active aspects."""
        custom_aspects = [{"name": "conjunction", "orb": 8}]

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data,
            active_aspects=custom_aspects
        )

        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert len(result.transits) == len(self.ephemeris_data)

    def test_empty_ephemeris_data(self):
        """Test factory with empty ephemeris data."""
        empty_ephemeris = []

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            empty_ephemeris
        )

        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert len(result.transits) == 0
        assert result.subject == self.natal_chart

        # Check dates (Optional field)
        if result.dates is not None:
            assert len(result.dates) == 0

    def test_single_ephemeris_point(self):
        """Test factory with single ephemeris data point."""
        single_point = [self.ephemeris_data[0]]

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            single_point
        )

        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert len(result.transits) == 1
        assert result.subject == self.natal_chart

        # Check dates (Optional field)
        if result.dates is not None:
            assert len(result.dates) == 1
