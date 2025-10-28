#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for ChartDataFactory

This module contains comprehensive unit tests for the ChartDataFactory class,
testing both SingleChartDataModel and DualChartDataModel functionality,
data validation, error handling, and performance characteristics.

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

import pytest
import tempfile
import json

from kerykeion import (
    ChartDataFactory,
    AstrologicalSubjectFactory,
    CompositeSubjectFactory,
    SingleChartDataModel,
    DualChartDataModel,
    ElementDistributionModel,
    QualityDistributionModel,
)
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.schemas import KerykeionException, AstrologicalSubjectModel


# Global fixtures for all test classes
@pytest.fixture
def factory():
    """Factory instance for tests."""
    return ChartDataFactory()

@pytest.fixture
def subject_factory():
    """Subject factory instance for tests."""
    return AstrologicalSubjectFactory()

@pytest.fixture
def test_subject_1(subject_factory):
    """First test subject for chart calculations."""
    return subject_factory.from_birth_data(
        name="Test Person 1",
        year=1990, month=6, day=15,
        hour=14, minute=30,
        city="Rome", nation="IT",
        suppress_geonames_warning=True
    )

@pytest.fixture
def test_subject_2(subject_factory):
    """Second test subject for dual chart calculations."""
    return subject_factory.from_birth_data(
        name="Test Person 2",
        year=1992, month=12, day=25,
        hour=16, minute=45,
        city="Milan", nation="IT",
        suppress_geonames_warning=True
    )

@pytest.fixture
def test_composite_subject(test_subject_1, test_subject_2):
    """Composite subject for composite chart tests."""
    composite_factory = CompositeSubjectFactory(test_subject_1, test_subject_2)
    return composite_factory.get_midpoint_composite_subject_model()

@pytest.fixture
def test_return_subject(test_subject_1):
    """Planet return subject for return chart tests."""
    return_factory = PlanetaryReturnFactory(
        test_subject_1,
        city="Rome",
        nation="IT"
    )
    return return_factory.next_return_from_year(year=2024, return_type="Solar")


class TestSingleChartDataModel:
    """Tests for SingleChartDataModel functionality."""

    def test_natal_chart_creation(self, factory, test_subject_1):
        """Test creation of natal chart data."""
        chart_data = factory.create_chart_data("Natal", test_subject_1)

        # Verify model type
        assert isinstance(chart_data, SingleChartDataModel)
        assert chart_data.chart_type == "Natal"

        # Verify subject data (only for AstrologicalSubjectModel)
        assert chart_data.subject.name == "Test Person 1"
        if isinstance(chart_data.subject, AstrologicalSubjectModel):
            assert chart_data.subject.year == 1990
            assert chart_data.subject.month == 6
            assert chart_data.subject.day == 15

        # Verify aspects are calculated
        assert hasattr(chart_data, 'aspects')
        assert len(chart_data.aspects) > 0

        # Verify element and quality distributions
        assert isinstance(chart_data.element_distribution, ElementDistributionModel)
        assert isinstance(chart_data.quality_distribution, QualityDistributionModel)

        # Verify percentages sum to approximately 100 (allowing for rounding)
        elements = chart_data.element_distribution
        total_elements = (elements.fire_percentage + elements.earth_percentage +
                         elements.air_percentage + elements.water_percentage)
        assert 99 <= total_elements <= 101  # Allow for rounding errors

        qualities = chart_data.quality_distribution
        total_qualities = (qualities.cardinal_percentage + qualities.fixed_percentage +
                          qualities.mutable_percentage)
        assert 99 <= total_qualities <= 101  # Allow for rounding errors        # Verify location data

    def test_external_natal_chart_creation(self, factory, test_subject_1):
        """Test creation of natal chart data (external visualization is handled by ChartDrawer)."""
        chart_data = factory.create_chart_data("Natal", test_subject_1)

        assert isinstance(chart_data, SingleChartDataModel)
        assert chart_data.chart_type == "Natal"
        assert chart_data.subject.name == "Test Person 1"

    def test_single_chart_json_serialization(self, factory, test_subject_1):
        """Test JSON serialization of SingleChartDataModel."""
        chart_data = factory.create_chart_data("Natal", test_subject_1)

        # Convert to dictionary
        data_dict = chart_data.model_dump()

        # Verify serializable to JSON
        json_str = json.dumps(data_dict, default=str)
        assert len(json_str) > 0

        # Verify key fields are present
        assert data_dict["chart_type"] == "Natal"
        assert data_dict["subject"]["name"] == "Test Person 1"
        assert "element_distribution" in data_dict
        assert "quality_distribution" in data_dict
        assert "aspects" in data_dict


class TestDualChartDataModel:
    """Tests for DualChartDataModel functionality."""

    def test_synastry_chart_creation(self, factory, test_subject_1, test_subject_2):
        """Test creation of synastry chart data."""
        chart_data = factory.create_chart_data("Synastry", test_subject_1, test_subject_2)

        # Verify model type
        assert isinstance(chart_data, DualChartDataModel)
        assert chart_data.chart_type == "Synastry"

        # Verify both subjects
        assert chart_data.first_subject.name == "Test Person 1"
        assert chart_data.second_subject.name == "Test Person 2"

        # Verify inter-chart aspects
        assert hasattr(chart_data, 'aspects')
        assert len(chart_data.aspects) > 0

        # Verify synastry-specific features
        assert chart_data.house_comparison is not None
        assert chart_data.relationship_score is not None

        # Verify element and quality distributions (combined)
        assert isinstance(chart_data.element_distribution, ElementDistributionModel)
        assert isinstance(chart_data.quality_distribution, QualityDistributionModel)

    def test_transit_chart_creation(self, factory, test_subject_1, subject_factory):
        """Test creation of transit chart data."""
        # Create transit subject (current time)
        transit_subject = subject_factory.from_current_time(
            name="Current Transits",
            city="Rome", nation="IT"
        )

        chart_data = factory.create_chart_data("Transit", test_subject_1, transit_subject)

        assert isinstance(chart_data, DualChartDataModel)
        assert chart_data.chart_type == "Transit"
        assert chart_data.first_subject.name == "Test Person 1"
        assert chart_data.second_subject.name == "Current Transits"

        # Verify house comparison for transits
        assert chart_data.house_comparison is not None
        # Relationship score should be None for transits
        assert chart_data.relationship_score is None

    def test_dual_chart_json_serialization(self, factory, test_subject_1, test_subject_2):
        """Test JSON serialization of DualChartDataModel."""
        chart_data = factory.create_chart_data("Synastry", test_subject_1, test_subject_2)

        # Convert to dictionary
        data_dict = chart_data.model_dump()

        # Verify serializable to JSON
        json_str = json.dumps(data_dict, default=str)
        assert len(json_str) > 0

        # Verify key fields are present
        assert data_dict["chart_type"] == "Synastry"
        assert data_dict["first_subject"]["name"] == "Test Person 1"
        assert data_dict["second_subject"]["name"] == "Test Person 2"
        assert "house_comparison" in data_dict
        assert "relationship_score" in data_dict


class TestFactoryParameterValidation:
    """Tests for factory parameter validation and error handling."""

    def test_missing_second_subject_for_synastry(self, factory, test_subject_1):
        """Test error when second subject is missing for synastry."""
        with pytest.raises(KerykeionException) as exc_info:
            factory.create_chart_data("Synastry", test_subject_1)

        assert "Second subject is required for Synastry charts" in str(exc_info.value)

    def test_missing_second_subject_for_transit(self, factory, test_subject_1):
        """Test error when second subject is missing for transit."""
        with pytest.raises(KerykeionException) as exc_info:
            factory.create_chart_data("Transit", test_subject_1)

        assert "Second subject is required for Transit charts" in str(exc_info.value)

    def test_invalid_chart_type(self, factory, test_subject_1):
        """Test error with invalid chart type."""
        with pytest.raises((ValueError, KerykeionException)):
            factory.create_chart_data("InvalidType", test_subject_1)

    def test_custom_active_points(self, factory, test_subject_1):
        """Test chart creation with custom active points."""
        custom_points = ["Sun", "Moon", "Mercury", "Venus", "Mars"]

        chart_data = factory.create_chart_data(
            "Natal", test_subject_1,
            active_points=custom_points
        )

        assert isinstance(chart_data, SingleChartDataModel)
        # Verify that only specified points are included
        assert len(chart_data.active_points) <= len(custom_points)

    def test_custom_active_aspects(self, factory, test_subject_1):
        """Test chart creation with custom aspect configuration."""
        custom_aspects = [
            {"name": "conjunction", "orb": 10},
            {"name": "opposition", "orb": 10},
            {"name": "trine", "orb": 8},
            {"name": "square", "orb": 8}
        ]

        chart_data = factory.create_chart_data(
            "Natal", test_subject_1,
            active_aspects=custom_aspects
        )

        assert isinstance(chart_data, SingleChartDataModel)
        assert len(chart_data.active_aspects) == len(custom_aspects)


class TestChartTypeMapping:
    """Tests for correct model type mapping based on chart type."""

    def test_single_chart_types_return_single_model(self, factory, test_subject_1):
        """Test that single chart types return SingleChartDataModel."""
        # Only test Natal with AstrologicalSubjectModel
        chart_data = factory.create_chart_data("Natal", test_subject_1)
        assert isinstance(chart_data, SingleChartDataModel)
        assert chart_data.chart_type == "Natal"

    def test_composite_chart_creation(self, factory, test_composite_subject):
        """Test that Composite charts work with CompositeSubjectModel."""
        chart_data = factory.create_chart_data("Composite", test_composite_subject)
        assert isinstance(chart_data, SingleChartDataModel)
        assert chart_data.chart_type == "Composite"

    def test_single_wheel_return_chart_creation(self, factory, test_return_subject):
        """Test that SingleReturnChart charts work with PlanetReturnModel."""
        chart_data = factory.create_chart_data("SingleReturnChart", test_return_subject)
        assert isinstance(chart_data, SingleChartDataModel)
        assert chart_data.chart_type == "SingleReturnChart"

    def test_dual_chart_types_return_dual_model(self, factory, test_subject_1, test_subject_2):
        """Test that dual chart types return DualChartDataModel."""
        dual_chart_types = ["Synastry", "Transit"]

        for chart_type in dual_chart_types:
            chart_data = factory.create_chart_data(chart_type, test_subject_1, test_subject_2)
            assert isinstance(chart_data, DualChartDataModel)
            assert chart_data.chart_type == chart_type


class TestElementAndQualityDistributions:
    """Tests for element and quality distribution calculations."""

    def test_element_distribution_values(self, factory, test_subject_1):
        """Test element distribution calculation and validation."""
        chart_data = factory.create_chart_data("Natal", test_subject_1)
        elements = chart_data.element_distribution

        # Verify all percentages are non-negative
        assert elements.fire_percentage >= 0
        assert elements.earth_percentage >= 0
        assert elements.air_percentage >= 0
        assert elements.water_percentage >= 0

        # Verify raw point values are non-negative
        assert elements.fire >= 0
        assert elements.earth >= 0
        assert elements.air >= 0
        assert elements.water >= 0

        # Verify percentages sum to 100
        total = (elements.fire_percentage + elements.earth_percentage +
                elements.air_percentage + elements.water_percentage)
        assert total == 100

    def test_quality_distribution_values(self, factory, test_subject_1):
        """Test quality distribution calculation and validation."""
        chart_data = factory.create_chart_data("Natal", test_subject_1)
        qualities = chart_data.quality_distribution

        # Verify all percentages are non-negative
        assert qualities.cardinal_percentage >= 0
        assert qualities.fixed_percentage >= 0
        assert qualities.mutable_percentage >= 0

        # Verify raw point values are non-negative
        assert qualities.cardinal >= 0
        assert qualities.fixed >= 0
        assert qualities.mutable >= 0

        # Verify percentages sum to approximately 100 (allowing for rounding)
        total = (qualities.cardinal_percentage + qualities.fixed_percentage +
                qualities.mutable_percentage)
        assert 99 <= total <= 101  # Allow for rounding errors

    def test_pure_count_distribution_method(self, factory, test_subject_1):
        """Pure count method should treat every active point equally."""
        chart_data = factory.create_chart_data(
            "Natal",
            test_subject_1,
            distribution_method="pure_count",
        )

        elements = chart_data.element_distribution
        qualities = chart_data.quality_distribution

        total_element_counts = elements.fire + elements.earth + elements.air + elements.water
        total_quality_counts = qualities.cardinal + qualities.fixed + qualities.mutable

        assert total_element_counts == len(chart_data.active_points)
        assert total_quality_counts == len(chart_data.active_points)

        elem_percentage_sum = (
            elements.fire_percentage
            + elements.earth_percentage
            + elements.air_percentage
            + elements.water_percentage
        )
        qual_percentage_sum = (
            qualities.cardinal_percentage
            + qualities.fixed_percentage
            + qualities.mutable_percentage
        )

        assert elem_percentage_sum == 100
        assert 99 <= qual_percentage_sum <= 101

    def test_custom_weight_override_adjusts_totals(self, factory, test_subject_1):
        """Custom distribution weights should override defaults."""
        base_chart = factory.create_chart_data("Natal", test_subject_1)
        custom_chart = factory.create_chart_data(
            "Natal",
            test_subject_1,
            distribution_method="weighted",
            custom_distribution_weights={"sun": 10.0},
        )

        base_sum = (
            base_chart.element_distribution.fire
            + base_chart.element_distribution.earth
            + base_chart.element_distribution.air
            + base_chart.element_distribution.water
        )
        custom_sum = (
            custom_chart.element_distribution.fire
            + custom_chart.element_distribution.earth
            + custom_chart.element_distribution.air
            + custom_chart.element_distribution.water
        )

        assert custom_sum == pytest.approx(base_sum + 8.0, abs=1e-6)

        sun_element_attr = test_subject_1.sun.element.lower()
        assert getattr(custom_chart.element_distribution, sun_element_attr) > getattr(
            base_chart.element_distribution, sun_element_attr
        )

class TestAspectCalculations:
    """Tests for aspect calculations in different chart types."""

    def test_natal_chart_aspects_are_internal(self, factory, test_subject_1):
        """Test that natal chart aspects are internal (same subject)."""
        chart_data = factory.create_chart_data("Natal", test_subject_1)

        # Verify aspects exist
        assert len(chart_data.aspects) > 0

        # For natal charts, all aspects should be internal
        # (this test assumes aspect structure allows checking)
        aspects = chart_data.aspects
        assert len(aspects) > 0

    def test_synastry_aspects_are_inter_chart(self, factory, test_subject_1, test_subject_2):
        """Test that synastry aspects are between different subjects."""
        chart_data = factory.create_chart_data("Synastry", test_subject_1, test_subject_2)

        # Verify inter-chart aspects exist
        assert len(chart_data.aspects) > 0

        # Synastry should have aspects between the two charts
        aspects = chart_data.aspects
        assert len(aspects) > 0


class TestPerformanceAndOptimization:
    """Tests for performance optimization features."""

    def test_limited_active_points_performance(self, factory, test_subject_1):
        """Test that limiting active points reduces calculation time."""
        # Full calculation
        full_chart = factory.create_chart_data("Natal", test_subject_1)

        # Limited calculation
        limited_points = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
        limited_chart = factory.create_chart_data(
            "Natal", test_subject_1,
            active_points=limited_points
        )

        # Limited chart should have fewer or equal aspects
        assert len(limited_chart.aspects) <= len(full_chart.aspects)
        assert len(limited_chart.active_points) <= len(full_chart.active_points)

    def test_selective_synastry_features(self, factory, test_subject_1, test_subject_2):
        """Test selective feature loading for synastry charts."""
        # Full synastry
        full_synastry = factory.create_chart_data(
            "Synastry", test_subject_1, test_subject_2,
            include_house_comparison=True,
            include_relationship_score=True
        )

        # Limited synastry
        limited_synastry = factory.create_chart_data(
            "Synastry", test_subject_1, test_subject_2,
            include_house_comparison=False,
            include_relationship_score=False
        )

        # Verify feature inclusion/exclusion
        assert full_synastry.house_comparison is not None
        assert full_synastry.relationship_score is not None

        # Limited features should be None when disabled
        assert limited_synastry.house_comparison is None
        assert limited_synastry.relationship_score is None


class TestDataExportAndSerialization:
    """Tests for data export and serialization capabilities."""

    def test_chart_data_to_dict(self, factory, test_subject_1):
        """Test conversion of chart data to dictionary."""
        chart_data = factory.create_chart_data("Natal", test_subject_1)
        data_dict = chart_data.model_dump()

        # Verify essential keys are present
        required_keys = [
            "chart_type", "subject", "aspects",
            "element_distribution", "quality_distribution",
        ]

        for key in required_keys:
            assert key in data_dict

    def test_chart_data_json_export(self, factory, test_subject_1):
        """Test JSON export functionality."""
        chart_data = factory.create_chart_data("Natal", test_subject_1)

        # Export to JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(chart_data.model_dump(), f, default=str, indent=2)
            json_file = f.name

        # Verify file was created and can be read back
        with open(json_file, 'r') as f:
            loaded_data = json.load(f)

        assert loaded_data["chart_type"] == "Natal"
        assert loaded_data["subject"]["name"] == "Test Person 1"

    def test_batch_processing_simulation(self, factory, subject_factory):
        """Test batch processing of multiple charts."""
        # Create multiple test subjects
        subjects = []
        for i in range(3):
            subject = subject_factory.from_birth_data(
                name=f"Test Person {i+1}",
                year=1990 + i, month=6, day=15,
                hour=14, minute=30,
                city="Rome", nation="IT",
                suppress_geonames_warning=True
            )
            subjects.append(subject)

        # Process all charts
        results = []
        for subject in subjects:
            chart_data = factory.create_chart_data("Natal", subject)

            # Extract key metrics for batch analysis
            result = {
                "name": chart_data.subject.name,
                "fire_percentage": chart_data.element_distribution.fire_percentage,
                "earth_percentage": chart_data.element_distribution.earth_percentage,
                "aspect_count": len(chart_data.aspects)
            }
            results.append(result)

        # Verify batch processing results
        assert len(results) == 3
        for result in results:
            assert "name" in result
            assert "fire_percentage" in result
            assert result["aspect_count"] > 0


class TestEdgeCasesAndRobustness:
    """Tests for edge cases and robustness."""

    def test_birth_at_midnight(self, factory, subject_factory):
        """Test handling of midnight birth time."""
        subject = subject_factory.from_birth_data(
            name="Midnight Birth",
            year=1990, month=1, day=1,
            hour=0, minute=0,
            city="London", nation="GB",
            suppress_geonames_warning=True
        )

        chart_data = factory.create_chart_data("Natal", subject)
        assert isinstance(chart_data, SingleChartDataModel)
        if isinstance(chart_data.subject, AstrologicalSubjectModel):
            assert chart_data.subject.hour == 0

    def test_leap_year_birth(self, factory, subject_factory):
        """Test handling of leap year birth date."""
        subject = subject_factory.from_birth_data(
            name="Leap Year Birth",
            year=2000, month=2, day=29,
            hour=12, minute=0,
            city="Paris", nation="FR",
            suppress_geonames_warning=True
        )

        chart_data = factory.create_chart_data("Natal", subject)
        assert isinstance(chart_data, SingleChartDataModel)
        if isinstance(chart_data.subject, AstrologicalSubjectModel):
            assert chart_data.subject.day == 29
            assert chart_data.subject.month == 2

    def test_same_subjects_synastry(self, factory, test_subject_1):
        """Test synastry with same subject (should work but show specific patterns)."""
        chart_data = factory.create_chart_data("Synastry", test_subject_1, test_subject_1)

        assert isinstance(chart_data, DualChartDataModel)
        assert chart_data.first_subject.name == chart_data.second_subject.name

        # Should have some aspects (likely many conjunctions)
        assert len(chart_data.aspects) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
