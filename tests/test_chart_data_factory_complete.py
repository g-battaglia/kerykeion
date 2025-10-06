"""
Comprehensive tests for ChartDataFactory module.

This test suite provides complete coverage for the ChartDataFactory functionality,
including chart data creation for all chart types, error handling, and data validation.
"""

import pytest
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.schemas import KerykeionException


class TestChartDataFactory:
    """Test cases for ChartDataFactory covering all code paths."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test fixtures."""
        self.subject1 = AstrologicalSubjectFactory.from_birth_data(
            name="Test Subject 1",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=30,
            city="New York",
            nation="US",
            lng=-74.006,
            lat=40.7128,
            tz_str="America/New_York",
            suppress_geonames_warning=True
        )

        self.subject2 = AstrologicalSubjectFactory.from_birth_data(
            name="Test Subject 2",
            year=1992,
            month=8,
            day=20,
            hour=14,
            minute=45,
            city="Los Angeles",
            nation="US",
            lng=-118.2437,
            lat=34.0522,
            tz_str="America/Los_Angeles",
            suppress_geonames_warning=True
        )

    def test_create_natal_chart_data(self):
        """Test creation of natal chart data."""
        chart_data = ChartDataFactory.create_chart_data("Natal", self.subject1)

        assert chart_data is not None
        assert hasattr(chart_data, 'subject')
        assert hasattr(chart_data, 'element_distribution')
        assert hasattr(chart_data, 'quality_distribution')
        assert chart_data.subject.name == "Test Subject 1"

    def test_create_synastry_chart_data(self):
        """Test creation of synastry chart data."""
        chart_data = ChartDataFactory.create_chart_data("Synastry", self.subject1, self.subject2)

        assert chart_data is not None
        assert hasattr(chart_data, 'first_subject')
        assert hasattr(chart_data, 'second_subject')
        assert chart_data.first_subject.name == "Test Subject 1"
        assert chart_data.second_subject.name == "Test Subject 2"

    def test_create_transit_chart_data(self):
        """Test creation of transit chart data."""
        chart_data = ChartDataFactory.create_chart_data("Transit", self.subject1, self.subject2)

        assert chart_data is not None
        assert hasattr(chart_data, 'first_subject')
        assert hasattr(chart_data, 'second_subject')
        assert chart_data.first_subject.name == "Test Subject 1"

    def test_synastry_missing_second_subject(self):
        """Test error when creating synastry without second subject."""
        with pytest.raises(KerykeionException):
            ChartDataFactory.create_chart_data("Synastry", self.subject1)

    def test_transit_missing_second_subject(self):
        """Test error when creating transit without second subject."""
        with pytest.raises(KerykeionException):
            ChartDataFactory.create_chart_data("Transit", self.subject1)

    def test_element_distribution_calculation(self):
        """Test element distribution calculation."""
        chart_data = ChartDataFactory.create_chart_data("Natal", self.subject1)

        assert hasattr(chart_data, 'element_distribution')
        assert hasattr(chart_data.element_distribution, 'fire')
        assert hasattr(chart_data.element_distribution, 'earth')
        assert hasattr(chart_data.element_distribution, 'air')
        assert hasattr(chart_data.element_distribution, 'water')

    def test_quality_distribution_calculation(self):
        """Test quality distribution calculation."""
        chart_data = ChartDataFactory.create_chart_data("Natal", self.subject1)

        assert hasattr(chart_data, 'quality_distribution')
        assert hasattr(chart_data.quality_distribution, 'cardinal')
        assert hasattr(chart_data.quality_distribution, 'fixed')
        assert hasattr(chart_data.quality_distribution, 'mutable')

    def test_factory_static_method(self):
        """Test that create_chart_data is a static method."""
        # Should be able to call without instantiating
        chart_data = ChartDataFactory.create_chart_data("Natal", self.subject1)
        assert chart_data is not None

    def test_chart_data_immutability(self):
        """Test that chart data preserves subject data."""
        chart_data = ChartDataFactory.create_chart_data("Natal", self.subject1)

        # Original subject should be preserved
        assert hasattr(chart_data, 'subject')
        assert chart_data.subject.name == self.subject1.name

    def test_aspects_calculation(self):
        """Test that aspects are calculated properly."""
        chart_data = ChartDataFactory.create_chart_data("Natal", self.subject1)

        assert hasattr(chart_data, 'aspects')
        # Aspects should be a model or list
        assert chart_data.aspects is not None

    def test_dual_chart_aspects_calculation(self):
        """Test aspects calculation for dual charts."""
        chart_data = ChartDataFactory.create_chart_data("Synastry", self.subject1, self.subject2)

        assert hasattr(chart_data, 'aspects')
        assert chart_data.aspects is not None

    def test_factory_performance(self):
        """Test that factory completes within reasonable time."""
        import time

        start_time = time.time()
        chart_data = ChartDataFactory.create_chart_data("Natal", self.subject1)
        end_time = time.time()

        # Should complete within 10 seconds (generous limit)
        assert end_time - start_time < 10
        assert chart_data is not None
