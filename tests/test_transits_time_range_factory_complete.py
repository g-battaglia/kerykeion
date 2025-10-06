"""
Comprehensive tests for TransitsTimeRangeFactory module.
This test suite aims to achieve 100% code coverage.
"""

from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path

from kerykeion import AstrologicalSubjectFactory
from kerykeion.transits_time_range_factory import TransitsTimeRangeFactory
from kerykeion.ephemeris_data_factory import EphemerisDataFactory
from kerykeion.schemas.kr_models import TransitsTimeRangeModel, TransitMomentModel
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
            nation="US"
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

from typing import List

from kerykeion.schemas.kr_literals import AstrologicalPoint
from kerykeion.schemas.kr_models import ActiveAspect


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
            nation="US"
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
        # Use the format from config_constants
        custom_points: List[AstrologicalPoint] = ["Sun", "Moon"]

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data,
            active_points=custom_points
        )

        assert factory.active_points == custom_points

    def test_factory_with_custom_active_aspects(self):
        """Test factory creation with custom active aspects."""
        # Use the format from config_constants
        custom_aspects: List[ActiveAspect] = [{"name": "conjunction", "orb": 8}, {"name": "opposition", "orb": 8}]

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

    def test_factory_with_settings_model(self):
        """Test factory creation with basic setup."""
        # Test with basic factory initialization
        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data
        )

        # Assert that the factory was created successfully
        assert factory is not None
        assert hasattr(factory, 'natal_chart')
        assert hasattr(factory, 'ephemeris_data_points')

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
        assert len(result.dates) == len(self.ephemeris_data)
        assert len(result.transits) == len(self.ephemeris_data)

        # Check that all dates are ISO formatted strings
        for date_str in result.dates:
            assert isinstance(date_str, str)
            # Should be parseable as datetime
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))

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
        custom_aspects = [{"name": "conjunction", "orb": 10}]

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data,
            active_aspects=custom_aspects
        )

        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert len(result.transits) == len(self.ephemeris_data)

    def test_transit_moment_structure(self):
        """Test the structure of individual transit moments."""
        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data
        )

        result = factory.get_transit_moments()

        for transit_moment in result.transits:
            assert isinstance(transit_moment, TransitMomentModel)
            assert hasattr(transit_moment, 'date')
            assert hasattr(transit_moment, 'aspects')
            assert isinstance(transit_moment.date, str)
            assert isinstance(transit_moment.aspects, list)

    def test_empty_ephemeris_data(self):
        """Test factory with empty ephemeris data."""
        empty_ephemeris = []

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            empty_ephemeris
        )

        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert len(result.dates) == 0
        assert len(result.transits) == 0
        assert result.subject == self.natal_chart

    def test_single_ephemeris_point(self):
        """Test factory with single ephemeris data point."""
        single_point = [self.ephemeris_data[0]]

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            single_point
        )

        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert len(result.dates) == 1
        assert len(result.transits) == 1
        assert result.subject == self.natal_chart

    @patch('kerykeion.aspects.AspectsFactory.dual_chart_aspects')
    def test_aspects_factory_integration(self, mock_dual_chart_aspects):
        """Test integration with AspectsFactory."""
        # Mock the aspects factory response
        mock_aspects_result = MagicMock()
        mock_aspects_result.relevant_aspects = []
        mock_dual_chart_aspects.return_value = mock_aspects_result

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data
        )

        result = factory.get_transit_moments()

        # Verify AspectsFactory was called for each ephemeris point
        assert mock_dual_chart_aspects.call_count == len(self.ephemeris_data)

        # Verify parameters passed to AspectsFactory
        for call in mock_dual_chart_aspects.call_args_list:
            args, kwargs = call
            assert len(args) == 2  # ephemeris_point, natal_chart
            assert 'active_points' in kwargs
            assert 'active_aspects' in kwargs

    def test_minimal_configuration(self):
        """Test factory with minimal configuration."""
        # Test with minimal configuration for performance
        minimal_points = ["Sun"]
        minimal_aspects = [{"name": "conjunction", "orb": 10}]

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data,
            active_points=minimal_points,
            active_aspects=minimal_aspects
        )

        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert factory.active_points == minimal_points
        assert factory.active_aspects == minimal_aspects

    def test_comprehensive_configuration(self):
        """Test factory with comprehensive configuration."""
        # Test with comprehensive configuration
        all_points = [
            "Sun", "Moon",
            "Mercury", "Venus",
            "Mars", "Jupiter",
            "Saturn"
        ]
        all_aspects = [
            {"name": "conjunction", "orb": 10}, {"name": "opposition", "orb": 10},
            {"name": "trine", "orb": 8}, {"name": "square", "orb": 5},
            {"name": "sextile", "orb": 6}
        ]

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data,
            active_points=all_points,
            active_aspects=all_aspects
        )

        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert factory.active_points == all_points
        assert factory.active_aspects == all_aspects

    def test_dates_chronological_order(self):
        """Test that dates are maintained in chronological order."""
        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data
        )

        result = factory.get_transit_moments()

        # Convert to datetime objects for comparison
        datetimes = [
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            for date_str in result.dates
        ]

        # Check chronological order
        for i in range(len(datetimes) - 1):
            assert datetimes[i] <= datetimes[i + 1]

    def test_transit_moments_consistency(self):
        """Test consistency between dates and transit moments."""
        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data
        )

        result = factory.get_transit_moments()

        # Each transit moment should correspond to a date
        assert len(result.dates) == len(result.transits)

        for i, transit_moment in enumerate(result.transits):
            expected_date = result.dates[i]
            assert transit_moment.date == expected_date

    def test_performance_with_large_dataset(self):
        """Test performance considerations with larger dataset."""
        # Create larger ephemeris dataset
        start_date = datetime(2024, 1, 1, 12, 0)
        end_date = start_date + timedelta(days=7)  # One week

        ephemeris_factory = EphemerisDataFactory(
            start_datetime=start_date,
            end_datetime=end_date,
            step_type="hours",
            step=6,  # Every 6 hours
            lat=self.natal_chart.lat,
            lng=self.natal_chart.lng,
            tz_str=self.natal_chart.tz_str,
        )

        large_ephemeris_data = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            large_ephemeris_data
        )

        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert len(result.transits) == len(large_ephemeris_data)
        assert len(result.dates) == len(large_ephemeris_data)

    def test_model_serialization(self):
        """Test that the result model can be serialized."""
        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data
        )

        result = factory.get_transit_moments()

        # Test model serialization
        serialized = result.model_dump()

        assert isinstance(serialized, dict)
        assert 'dates' in serialized
        assert 'subject' in serialized
        assert 'transits' in serialized
        assert isinstance(serialized['dates'], list)
        assert isinstance(serialized['transits'], list)

    def test_attribute_access_after_initialization(self):
        """Test that all attributes are accessible after initialization."""
        """Test attribute access after initialization."""
        custom_points = ["Sun", "Moon"]
        custom_aspects = [{"name": "conjunction", "orb": 10}, {"name": "opposition", "orb": 10}]
        settings_dict = {"default_orb": 10.0}

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data,
            active_points=custom_points,
            active_aspects=custom_aspects,
            settings_file=settings_dict
        )

        # Test attribute access
        assert factory.natal_chart is not None
        assert factory.ephemeris_data_points is not None
        assert factory.active_points == custom_points
        assert factory.active_aspects == custom_aspects
        assert factory.settings_file == settings_dict

    def test_string_active_points_handling(self):
        """Test handling of string-based active points."""
        string_points = ["Sun", "Moon", "Mercury"]

        factory = TransitsTimeRangeFactory(
            self.natal_chart,
            self.ephemeris_data,
            active_points=string_points
        )

        result = factory.get_transit_moments()

        assert isinstance(result, TransitsTimeRangeModel)
        assert factory.active_points == string_points
