#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive tests for ChartDataFactory.

Integrates and extends all test cases from:
  - tests/factories/test_chart_data_factory.py
  - tests/factories/test_chart_data_factory_complete.py
  - tests/factories/test_all_active_points.py

All subjects are created offline with explicit coordinates to avoid network
dependencies.

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

import json
import time

import pytest

from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    CompositeSubjectFactory,
    SingleChartDataModel,
    DualChartDataModel,
    ElementDistributionModel,
    QualityDistributionModel,
)
from kerykeion.composite_subject_factory import CompositeSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.schemas import KerykeionException, AstrologicalSubjectModel
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS, DEFAULT_ACTIVE_ASPECTS
from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS
from kerykeion.utilities import find_common_active_points


# =============================================================================
# SESSION-SCOPED FIXTURES  (shared across all test classes)
# =============================================================================


@pytest.fixture(scope="session")
def johnny_depp():
    """Johnny Depp – canonical test subject."""
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


@pytest.fixture(scope="session")
def john_lennon():
    """John Lennon – secondary test subject."""
    return AstrologicalSubjectFactory.from_birth_data(
        "John Lennon",
        1940,
        10,
        9,
        18,
        30,
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="session")
def yoko_ono():
    """Yoko Ono – for synastry pairing."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Yoko Ono",
        1933,
        2,
        18,
        20,
        30,
        lat=35.6762,
        lng=139.6503,
        tz_str="Asia/Tokyo",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="session")
def subject_new_york():
    """Test Subject (New York) – from the _complete suite."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Test Subject NY",
        1990,
        6,
        15,
        12,
        30,
        lat=40.7128,
        lng=-74.006,
        tz_str="America/New_York",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="session")
def subject_los_angeles():
    """Test Subject (Los Angeles) – from the _complete suite."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Test Subject LA",
        1992,
        8,
        20,
        14,
        45,
        lat=34.0522,
        lng=-118.2437,
        tz_str="America/Los_Angeles",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="session")
def composite_subject(johnny_depp, john_lennon):
    """Composite subject from two canonical subjects."""
    factory = CompositeSubjectFactory(johnny_depp, john_lennon)
    return factory.get_midpoint_composite_subject_model()


@pytest.fixture(scope="session")
def return_subject(johnny_depp):
    """Solar return subject for Johnny Depp (2024)."""
    return_factory = PlanetaryReturnFactory(
        johnny_depp,
        lat=37.7742,
        lng=-87.1133,
        tz_str="America/Chicago",
        online=False,
    )
    return return_factory.next_return_from_date(2024, 1, 1, return_type="Solar")


# =============================================================================
# 1. TestSingleChartDataModel
# =============================================================================


class TestSingleChartDataModel:
    """Tests for natal (single-subject) chart creation and serialization."""

    def test_natal_chart_creation(self, johnny_depp):
        """create_natal_chart_data returns a SingleChartDataModel."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)

        assert isinstance(chart, SingleChartDataModel)
        assert chart.chart_type == "Natal"

    def test_natal_chart_subject_attributes(self, johnny_depp):
        """Subject attributes are preserved in the chart model."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)

        assert chart.subject.name == "Johnny Depp"
        if isinstance(chart.subject, AstrologicalSubjectModel):
            assert chart.subject.year == 1963
            assert chart.subject.month == 6
            assert chart.subject.day == 9
            assert chart.subject.hour == 0
            assert chart.subject.minute == 0

    def test_natal_chart_has_aspects(self, johnny_depp):
        """Natal chart should contain calculated aspects."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)

        assert hasattr(chart, "aspects")
        assert chart.aspects is not None
        assert len(chart.aspects) > 0

    def test_natal_chart_has_element_distribution(self, johnny_depp):
        """Natal chart should contain element distribution."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)

        assert isinstance(chart.element_distribution, ElementDistributionModel)

    def test_natal_chart_has_quality_distribution(self, johnny_depp):
        """Natal chart should contain quality distribution."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)

        assert isinstance(chart.quality_distribution, QualityDistributionModel)

    def test_natal_chart_has_active_points(self, johnny_depp):
        """Natal chart should list active points."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)

        assert hasattr(chart, "active_points")
        assert len(chart.active_points) > 0

    def test_natal_chart_has_active_aspects(self, johnny_depp):
        """Natal chart should list active aspect types."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)

        assert hasattr(chart, "active_aspects")
        assert len(chart.active_aspects) > 0

    def test_single_chart_json_serialization_roundtrip(self, johnny_depp):
        """SingleChartDataModel serializes to JSON and back without data loss."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)
        data_dict = chart.model_dump()

        json_str = json.dumps(data_dict, default=str)
        assert len(json_str) > 0

        loaded = json.loads(json_str)
        assert loaded["chart_type"] == "Natal"
        assert loaded["subject"]["name"] == "Johnny Depp"
        assert "element_distribution" in loaded
        assert "quality_distribution" in loaded
        assert "aspects" in loaded

    def test_create_chart_data_generic_natal(self, johnny_depp):
        """create_chart_data with 'Natal' returns SingleChartDataModel."""
        chart = ChartDataFactory.create_chart_data("Natal", johnny_depp)

        assert isinstance(chart, SingleChartDataModel)
        assert chart.chart_type == "Natal"
        assert chart.subject.name == "Johnny Depp"

    def test_natal_chart_data_immutability(self, johnny_depp):
        """Chart data preserves the original subject data."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)

        assert chart.subject.name == johnny_depp.name


# =============================================================================
# 2. TestDualChartDataModel
# =============================================================================


class TestDualChartDataModel:
    """Tests for dual-subject charts: synastry and transit."""

    def test_synastry_chart_creation(self, johnny_depp, john_lennon):
        """create_synastry_chart_data returns a DualChartDataModel."""
        chart = ChartDataFactory.create_synastry_chart_data(
            johnny_depp,
            john_lennon,
            include_relationship_score=True,
        )

        assert isinstance(chart, DualChartDataModel)
        assert chart.chart_type == "Synastry"

    def test_synastry_subjects(self, johnny_depp, john_lennon):
        """Both subjects are accessible on the synastry model."""
        chart = ChartDataFactory.create_synastry_chart_data(
            johnny_depp,
            john_lennon,
        )

        assert chart.first_subject.name == "Johnny Depp"
        assert chart.second_subject.name == "John Lennon"

    def test_synastry_has_aspects(self, johnny_depp, john_lennon):
        """Synastry chart should have inter-chart aspects."""
        chart = ChartDataFactory.create_synastry_chart_data(
            johnny_depp,
            john_lennon,
        )

        assert hasattr(chart, "aspects")
        assert len(chart.aspects) > 0

    def test_synastry_has_house_comparison(self, johnny_depp, john_lennon):
        """Synastry chart includes house comparison by default."""
        chart = ChartDataFactory.create_synastry_chart_data(
            johnny_depp,
            john_lennon,
            include_house_comparison=True,
        )

        assert chart.house_comparison is not None

    def test_synastry_has_relationship_score(self, johnny_depp, john_lennon):
        """Relationship score is present when requested."""
        chart = ChartDataFactory.create_synastry_chart_data(
            johnny_depp,
            john_lennon,
            include_relationship_score=True,
        )

        assert chart.relationship_score is not None

    def test_synastry_has_element_and_quality(self, johnny_depp, john_lennon):
        """Synastry chart includes element and quality distributions."""
        chart = ChartDataFactory.create_synastry_chart_data(
            johnny_depp,
            john_lennon,
        )

        assert isinstance(chart.element_distribution, ElementDistributionModel)
        assert isinstance(chart.quality_distribution, QualityDistributionModel)

    def test_transit_chart_creation(self, johnny_depp, john_lennon):
        """create_transit_chart_data returns a DualChartDataModel."""
        chart = ChartDataFactory.create_transit_chart_data(
            johnny_depp,
            john_lennon,
        )

        assert isinstance(chart, DualChartDataModel)
        assert chart.chart_type == "Transit"
        assert chart.first_subject.name == "Johnny Depp"
        assert chart.second_subject.name == "John Lennon"

    def test_transit_has_house_comparison(self, johnny_depp, john_lennon):
        """Transit chart includes house comparison by default."""
        chart = ChartDataFactory.create_transit_chart_data(
            johnny_depp,
            john_lennon,
            include_house_comparison=True,
        )

        assert chart.house_comparison is not None

    def test_transit_no_relationship_score(self, johnny_depp, john_lennon):
        """Transit charts should not have a relationship score."""
        chart = ChartDataFactory.create_transit_chart_data(
            johnny_depp,
            john_lennon,
        )

        assert chart.relationship_score is None

    def test_dual_chart_json_serialization(self, johnny_depp, john_lennon):
        """DualChartDataModel serializes to JSON and back."""
        chart = ChartDataFactory.create_synastry_chart_data(
            johnny_depp,
            john_lennon,
        )
        data_dict = chart.model_dump()

        json_str = json.dumps(data_dict, default=str)
        assert len(json_str) > 0

        loaded = json.loads(json_str)
        assert loaded["chart_type"] == "Synastry"
        assert loaded["first_subject"]["name"] == "Johnny Depp"
        assert loaded["second_subject"]["name"] == "John Lennon"
        assert "house_comparison" in loaded
        assert "relationship_score" in loaded

    def test_generic_synastry(self, johnny_depp, john_lennon):
        """create_chart_data with 'Synastry' returns DualChartDataModel."""
        chart = ChartDataFactory.create_chart_data(
            "Synastry",
            johnny_depp,
            john_lennon,
        )

        assert isinstance(chart, DualChartDataModel)
        assert chart.chart_type == "Synastry"

    def test_generic_transit(self, johnny_depp, john_lennon):
        """create_chart_data with 'Transit' returns DualChartDataModel."""
        chart = ChartDataFactory.create_chart_data(
            "Transit",
            johnny_depp,
            john_lennon,
        )

        assert isinstance(chart, DualChartDataModel)
        assert chart.chart_type == "Transit"


# =============================================================================
# 3. TestAllChartTypes
# =============================================================================


class TestAllChartTypes:
    """Verify all 6 chart types can be created and return the correct model."""

    def test_natal(self, johnny_depp):
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)
        assert isinstance(chart, SingleChartDataModel)
        assert chart.chart_type == "Natal"
        assert len(chart.aspects) > 0

    def test_synastry(self, johnny_depp, john_lennon):
        chart = ChartDataFactory.create_synastry_chart_data(
            johnny_depp,
            john_lennon,
        )
        assert isinstance(chart, DualChartDataModel)
        assert chart.chart_type == "Synastry"
        assert len(chart.aspects) > 0

    def test_transit(self, johnny_depp, john_lennon):
        chart = ChartDataFactory.create_transit_chart_data(
            johnny_depp,
            john_lennon,
        )
        assert isinstance(chart, DualChartDataModel)
        assert chart.chart_type == "Transit"
        assert len(chart.aspects) > 0

    def test_composite(self, composite_subject):
        chart = ChartDataFactory.create_composite_chart_data(composite_subject)
        assert isinstance(chart, SingleChartDataModel)
        assert chart.chart_type == "Composite"
        assert len(chart.aspects) > 0

    def test_single_return(self, return_subject):
        """Single-wheel return chart (return subject only)."""
        chart = ChartDataFactory.create_single_wheel_return_chart_data(
            return_subject,
        )
        assert isinstance(chart, SingleChartDataModel)
        assert chart.chart_type == "SingleReturnChart"
        assert len(chart.aspects) > 0

    def test_dual_return(self, johnny_depp, return_subject):
        """Dual-wheel return chart (natal + return)."""
        chart = ChartDataFactory.create_return_chart_data(
            johnny_depp,
            return_subject,
        )
        assert isinstance(chart, DualChartDataModel)
        assert chart.chart_type == "DualReturnChart"
        assert len(chart.aspects) > 0

    def test_single_types_return_single_model(self, johnny_depp):
        """Natal via the generic method gives SingleChartDataModel."""
        chart = ChartDataFactory.create_chart_data("Natal", johnny_depp)
        assert isinstance(chart, SingleChartDataModel)

    def test_dual_types_return_dual_model(self, johnny_depp, john_lennon):
        """Synastry and Transit via the generic method give DualChartDataModel."""
        for chart_type in ("Synastry", "Transit"):
            chart = ChartDataFactory.create_chart_data(
                chart_type,
                johnny_depp,
                john_lennon,
            )
            assert isinstance(chart, DualChartDataModel)
            assert chart.chart_type == chart_type

    def test_composite_via_generic(self, composite_subject):
        chart = ChartDataFactory.create_chart_data("Composite", composite_subject)
        assert isinstance(chart, SingleChartDataModel)
        assert chart.chart_type == "Composite"

    def test_single_return_via_generic(self, return_subject):
        chart = ChartDataFactory.create_chart_data("SingleReturnChart", return_subject)
        assert isinstance(chart, SingleChartDataModel)
        assert chart.chart_type == "SingleReturnChart"


# =============================================================================
# 4. TestElementAndQualityDistributions
# =============================================================================


class TestElementAndQualityDistributions:
    """Verify element and quality distribution calculations."""

    def test_element_distribution_values_nonnegative(self, johnny_depp):
        """All element raw values and percentages are non-negative."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)
        elem = chart.element_distribution

        assert elem.fire >= 0
        assert elem.earth >= 0
        assert elem.air >= 0
        assert elem.water >= 0
        assert elem.fire_percentage >= 0
        assert elem.earth_percentage >= 0
        assert elem.air_percentage >= 0
        assert elem.water_percentage >= 0

    def test_element_percentages_sum_to_100(self, johnny_depp):
        """Fire + Earth + Air + Water percentages must sum to exactly 100."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)
        elem = chart.element_distribution

        total = elem.fire_percentage + elem.earth_percentage + elem.air_percentage + elem.water_percentage
        assert total == 100

    def test_quality_distribution_values_nonnegative(self, johnny_depp):
        """All quality raw values and percentages are non-negative."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)
        qual = chart.quality_distribution

        assert qual.cardinal >= 0
        assert qual.fixed >= 0
        assert qual.mutable >= 0
        assert qual.cardinal_percentage >= 0
        assert qual.fixed_percentage >= 0
        assert qual.mutable_percentage >= 0

    def test_quality_percentages_sum_to_100(self, johnny_depp):
        """Cardinal + Fixed + Mutable percentages must sum to ~100."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)
        qual = chart.quality_distribution

        total = qual.cardinal_percentage + qual.fixed_percentage + qual.mutable_percentage
        assert 99 <= total <= 101

    def test_element_has_all_attributes(self, subject_new_york):
        """Element distribution model exposes fire/earth/air/water."""
        chart = ChartDataFactory.create_natal_chart_data(subject_new_york)

        assert hasattr(chart.element_distribution, "fire")
        assert hasattr(chart.element_distribution, "earth")
        assert hasattr(chart.element_distribution, "air")
        assert hasattr(chart.element_distribution, "water")

    def test_quality_has_all_attributes(self, subject_new_york):
        """Quality distribution model exposes cardinal/fixed/mutable."""
        chart = ChartDataFactory.create_natal_chart_data(subject_new_york)

        assert hasattr(chart.quality_distribution, "cardinal")
        assert hasattr(chart.quality_distribution, "fixed")
        assert hasattr(chart.quality_distribution, "mutable")

    def test_pure_count_method(self, johnny_depp):
        """pure_count treats every active point equally (count = len(active_points))."""
        chart = ChartDataFactory.create_natal_chart_data(
            johnny_depp,
            distribution_method="pure_count",
        )

        elem = chart.element_distribution
        qual = chart.quality_distribution

        total_elem = elem.fire + elem.earth + elem.air + elem.water
        total_qual = qual.cardinal + qual.fixed + qual.mutable

        assert total_elem == len(chart.active_points)
        assert total_qual == len(chart.active_points)

        elem_pct = elem.fire_percentage + elem.earth_percentage + elem.air_percentage + elem.water_percentage
        qual_pct = qual.cardinal_percentage + qual.fixed_percentage + qual.mutable_percentage

        assert elem_pct == 100
        assert 99 <= qual_pct <= 101

    def test_custom_weight_override_adjusts_totals(self, johnny_depp):
        """Custom distribution weights override defaults and shift totals."""
        base = ChartDataFactory.create_natal_chart_data(johnny_depp)
        custom = ChartDataFactory.create_natal_chart_data(
            johnny_depp,
            distribution_method="weighted",
            custom_distribution_weights={"sun": 10.0},
        )

        base_sum = (
            base.element_distribution.fire
            + base.element_distribution.earth
            + base.element_distribution.air
            + base.element_distribution.water
        )
        custom_sum = (
            custom.element_distribution.fire
            + custom.element_distribution.earth
            + custom.element_distribution.air
            + custom.element_distribution.water
        )

        assert custom_sum == pytest.approx(base_sum + 8.0, abs=1e-6)

        sun_element = johnny_depp.sun.element.lower()
        assert getattr(custom.element_distribution, sun_element) > getattr(base.element_distribution, sun_element)

    def test_synastry_element_distribution(self, johnny_depp, john_lennon):
        """Synastry element percentages still sum to 100."""
        chart = ChartDataFactory.create_synastry_chart_data(
            johnny_depp,
            john_lennon,
        )
        elem = chart.element_distribution

        total = elem.fire_percentage + elem.earth_percentage + elem.air_percentage + elem.water_percentage
        assert total == 100


# =============================================================================
# 5. TestAspectCalculations
# =============================================================================


class TestAspectCalculations:
    """Verify aspect calculation for single and dual charts."""

    def test_natal_chart_has_internal_aspects(self, johnny_depp):
        """Natal chart aspects are internal (within the same subject)."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)

        assert len(chart.aspects) > 0

    def test_synastry_has_inter_chart_aspects(self, johnny_depp, john_lennon):
        """Synastry chart aspects are between the two subjects."""
        chart = ChartDataFactory.create_synastry_chart_data(
            johnny_depp,
            john_lennon,
        )

        assert len(chart.aspects) > 0

    def test_dual_chart_aspects_not_none(self, subject_new_york, subject_los_angeles):
        """Dual chart aspects model is populated."""
        chart = ChartDataFactory.create_synastry_chart_data(
            subject_new_york,
            subject_los_angeles,
        )

        assert chart.aspects is not None
        assert len(chart.aspects) > 0

    def test_custom_active_aspects_restricts_types(self, johnny_depp):
        """Passing fewer active_aspects reduces aspect count."""
        full_chart = ChartDataFactory.create_natal_chart_data(johnny_depp)

        custom_aspects = [
            {"name": "conjunction", "orb": 10},
            {"name": "opposition", "orb": 10},
        ]
        limited_chart = ChartDataFactory.create_natal_chart_data(
            johnny_depp,
            active_aspects=custom_aspects,
        )

        assert len(limited_chart.active_aspects) == 2
        assert len(limited_chart.aspects) <= len(full_chart.aspects)

    def test_aspect_points_are_within_active_set(self, johnny_depp):
        """All aspect participant names should belong to the active points."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)
        aspect_points = {a.p1_name for a in chart.aspects}.union({a.p2_name for a in chart.aspects})
        assert aspect_points.issubset(set(chart.active_points))


# =============================================================================
# 6. TestFactoryParameterValidation
# =============================================================================


class TestFactoryParameterValidation:
    """Tests for parameter validation and error handling."""

    def test_missing_second_subject_for_synastry(self, johnny_depp):
        """Synastry without a second subject raises KerykeionException."""
        with pytest.raises(KerykeionException) as exc_info:
            ChartDataFactory.create_chart_data("Synastry", johnny_depp)

        assert "Second subject is required for Synastry charts" in str(exc_info.value)

    def test_missing_second_subject_for_transit(self, johnny_depp):
        """Transit without a second subject raises KerykeionException."""
        with pytest.raises(KerykeionException) as exc_info:
            ChartDataFactory.create_chart_data("Transit", johnny_depp)

        assert "Second subject is required for Transit charts" in str(exc_info.value)

    def test_invalid_chart_type(self, johnny_depp):
        """Invalid chart type raises ValueError or KerykeionException."""
        with pytest.raises((ValueError, KerykeionException)):
            ChartDataFactory.create_chart_data("InvalidType", johnny_depp)

    def test_custom_active_points(self, johnny_depp):
        """Chart with fewer active points has correspondingly fewer aspects."""
        custom_points = ["Sun", "Moon", "Mercury", "Venus", "Mars"]

        chart = ChartDataFactory.create_natal_chart_data(
            johnny_depp,
            active_points=custom_points,
        )

        assert isinstance(chart, SingleChartDataModel)
        assert len(chart.active_points) <= len(custom_points)

    def test_custom_active_aspects(self, johnny_depp):
        """Chart respects the list of active aspect types provided."""
        custom_aspects = [
            {"name": "conjunction", "orb": 10},
            {"name": "opposition", "orb": 10},
            {"name": "trine", "orb": 8},
            {"name": "square", "orb": 8},
        ]

        chart = ChartDataFactory.create_natal_chart_data(
            johnny_depp,
            active_aspects=custom_aspects,
        )

        assert isinstance(chart, SingleChartDataModel)
        assert len(chart.active_aspects) == len(custom_aspects)

    def test_limited_active_points_reduce_aspects(self, johnny_depp):
        """Fewer active points should produce fewer or equal aspects."""
        full = ChartDataFactory.create_natal_chart_data(johnny_depp)
        limited = ChartDataFactory.create_natal_chart_data(
            johnny_depp,
            active_points=["Sun", "Moon", "Mercury", "Venus", "Mars"],
        )

        assert len(limited.aspects) <= len(full.aspects)
        assert len(limited.active_points) <= len(full.active_points)

    def test_selective_synastry_features(self, johnny_depp, john_lennon):
        """Toggling house_comparison and relationship_score flags works."""
        full = ChartDataFactory.create_synastry_chart_data(
            johnny_depp,
            john_lennon,
            include_house_comparison=True,
            include_relationship_score=True,
        )
        limited = ChartDataFactory.create_synastry_chart_data(
            johnny_depp,
            john_lennon,
            include_house_comparison=False,
            include_relationship_score=False,
        )

        assert full.house_comparison is not None
        assert full.relationship_score is not None
        assert limited.house_comparison is None
        assert limited.relationship_score is None

    def test_factory_is_callable_as_static(self, johnny_depp):
        """create_chart_data is a static method – no instance needed."""
        chart = ChartDataFactory.create_chart_data("Natal", johnny_depp)
        assert chart is not None


# =============================================================================
# 7. TestDataExportAndSerialization
# =============================================================================


class TestDataExportAndSerialization:
    """Tests for dict/JSON export and batch processing."""

    def test_chart_data_to_dict(self, johnny_depp):
        """model_dump() contains all essential keys."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)
        data_dict = chart.model_dump()

        required_keys = [
            "chart_type",
            "subject",
            "aspects",
            "element_distribution",
            "quality_distribution",
        ]
        for key in required_keys:
            assert key in data_dict

    def test_chart_data_json_file_export(self, johnny_depp, tmp_path):
        """Chart data can be written to and loaded from a JSON file."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)

        json_file = tmp_path / "chart_export.json"
        with open(json_file, "w") as f:
            json.dump(chart.model_dump(), f, default=str, indent=2)

        with open(json_file, "r") as f:
            loaded = json.load(f)

        assert loaded["chart_type"] == "Natal"
        assert loaded["subject"]["name"] == "Johnny Depp"

    def test_batch_processing_multiple_subjects(self):
        """Multiple subjects can be batch-processed successfully."""
        configs = [
            ("Batch 1", 1963, 6, 9, 0, 0, 37.7742, -87.1133, "America/Chicago"),
            ("Batch 2", 1940, 10, 9, 18, 30, 53.4084, -2.9916, "Europe/London"),
            ("Batch 3", 1992, 8, 20, 14, 45, 34.0522, -118.2437, "America/Los_Angeles"),
        ]

        results = []
        for name, yr, mo, dy, hr, mi, lat, lng, tz in configs:
            subj = AstrologicalSubjectFactory.from_birth_data(
                name,
                yr,
                mo,
                dy,
                hr,
                mi,
                lat=lat,
                lng=lng,
                tz_str=tz,
                online=False,
                suppress_geonames_warning=True,
            )
            chart = ChartDataFactory.create_natal_chart_data(subj)
            results.append(
                {
                    "name": chart.subject.name,
                    "fire_pct": chart.element_distribution.fire_percentage,
                    "earth_pct": chart.element_distribution.earth_percentage,
                    "aspect_count": len(chart.aspects),
                }
            )

        assert len(results) == 3
        for r in results:
            assert "name" in r
            assert "fire_pct" in r
            assert r["aspect_count"] > 0

    def test_dual_chart_dict_export(self, johnny_depp, john_lennon):
        """DualChartDataModel model_dump contains both subjects."""
        chart = ChartDataFactory.create_synastry_chart_data(
            johnny_depp,
            john_lennon,
        )
        data = chart.model_dump()

        assert "first_subject" in data
        assert "second_subject" in data
        assert data["first_subject"]["name"] == "Johnny Depp"
        assert data["second_subject"]["name"] == "John Lennon"

    def test_json_roundtrip_preserves_aspects(self, johnny_depp):
        """JSON roundtrip preserves the number of aspects."""
        chart = ChartDataFactory.create_natal_chart_data(johnny_depp)
        data = chart.model_dump()

        json_str = json.dumps(data, default=str)
        loaded = json.loads(json_str)

        assert len(loaded["aspects"]) == len(chart.aspects)


# =============================================================================
# 8. TestEdgeCasesAndRobustness
# =============================================================================


class TestEdgeCasesAndRobustness:
    """Edge-case inputs and robustness checks."""

    def test_midnight_birth(self):
        """Midnight birth (hour=0, minute=0) is handled correctly."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Midnight Birth",
            1990,
            1,
            1,
            0,
            0,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
            online=False,
            suppress_geonames_warning=True,
        )
        chart = ChartDataFactory.create_natal_chart_data(subject)

        assert isinstance(chart, SingleChartDataModel)
        if isinstance(chart.subject, AstrologicalSubjectModel):
            assert chart.subject.hour == 0
            assert chart.subject.minute == 0

    def test_leap_year_birth(self):
        """Feb 29 on a leap year (2000) is handled correctly."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Leap Year Birth",
            2000,
            2,
            29,
            12,
            0,
            lat=48.8566,
            lng=2.3522,
            tz_str="Europe/Paris",
            online=False,
            suppress_geonames_warning=True,
        )
        chart = ChartDataFactory.create_natal_chart_data(subject)

        assert isinstance(chart, SingleChartDataModel)
        if isinstance(chart.subject, AstrologicalSubjectModel):
            assert chart.subject.day == 29
            assert chart.subject.month == 2

    def test_same_subjects_synastry(self, johnny_depp):
        """Synastry with the same subject for both sides is allowed."""
        chart = ChartDataFactory.create_synastry_chart_data(
            johnny_depp,
            johnny_depp,
        )

        assert isinstance(chart, DualChartDataModel)
        assert chart.first_subject.name == chart.second_subject.name
        # Many conjunctions expected
        assert len(chart.aspects) > 0

    def test_factory_performance(self, subject_new_york):
        """Chart creation completes within a generous time limit."""
        start = time.time()
        chart = ChartDataFactory.create_natal_chart_data(subject_new_york)
        elapsed = time.time() - start

        assert chart is not None
        assert elapsed < 10

    def test_composite_from_same_person(self, johnny_depp):
        """Composite from the same subject should still succeed."""
        factory = CompositeSubjectFactory(johnny_depp, johnny_depp)
        comp = factory.get_midpoint_composite_subject_model()
        chart = ChartDataFactory.create_composite_chart_data(comp)

        assert isinstance(chart, SingleChartDataModel)
        assert chart.chart_type == "Composite"


# =============================================================================
# 9. TestAllActivePoints  (from test_all_active_points.py)
# =============================================================================


class TestAllActivePoints:
    """Verify ALL_ACTIVE_POINTS integration through ChartDataFactory."""

    def test_all_active_points_in_chart(self):
        """ALL_ACTIVE_POINTS results in maximal active points on chart data."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "All Points Test",
            1990,
            1,
            1,
            12,
            0,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
            online=False,
            active_points=ALL_ACTIVE_POINTS,
            suppress_geonames_warning=True,
        )

        chart = ChartDataFactory.create_natal_chart_data(
            subject,
            active_points=ALL_ACTIVE_POINTS,
        )

        # Active points must be a subset of ALL_ACTIVE_POINTS
        assert set(chart.active_points).issubset(set(ALL_ACTIVE_POINTS))
        assert len(chart.active_points) > 0

        # Aspects must exist
        assert chart.aspects is not None
        assert len(chart.aspects) > 0

        # Aspect participant names are within the active set
        aspect_points = {a.p1_name for a in chart.aspects}.union({a.p2_name for a in chart.aspects})
        assert aspect_points.issubset(set(chart.active_points))

    def test_all_active_points_with_chart_drawer(self):
        """ChartDrawer reflects the same active points as the chart data."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        subject = AstrologicalSubjectFactory.from_birth_data(
            "Drawer Test",
            1990,
            1,
            1,
            12,
            0,
            lat=51.5074,
            lng=-0.1278,
            tz_str="Europe/London",
            online=False,
            active_points=ALL_ACTIVE_POINTS,
            suppress_geonames_warning=True,
        )

        chart = ChartDataFactory.create_natal_chart_data(
            subject,
            active_points=ALL_ACTIVE_POINTS,
        )

        drawer = ChartDrawer(chart)

        assert set(drawer.active_points) == set(chart.active_points)
        assert len(drawer.active_points) == len(chart.active_points)

        available_names = [p["name"] for p in drawer.available_planets_setting]
        settings_names = [b["name"] for b in DEFAULT_CELESTIAL_POINTS_SETTINGS]
        expected_names = set(find_common_active_points(settings_names, chart.active_points))

        assert len(available_names) == len(expected_names)
        assert set(available_names) == expected_names
        assert drawer._count_active_planets() == len(expected_names)


# =============================================================================
# 10. TestCompleteFactoryBehavior (from test_chart_data_factory_complete.py)
# =============================================================================


class TestCompleteFactoryBehavior:
    """Additional completeness tests ported from the _complete suite."""

    def test_natal_subject_name_preserved(self, subject_new_york):
        chart = ChartDataFactory.create_natal_chart_data(subject_new_york)

        assert chart is not None
        assert chart.subject.name == "Test Subject NY"

    def test_synastry_both_subjects(self, subject_new_york, subject_los_angeles):
        chart = ChartDataFactory.create_synastry_chart_data(
            subject_new_york,
            subject_los_angeles,
        )

        assert chart is not None
        assert chart.first_subject.name == "Test Subject NY"
        assert chart.second_subject.name == "Test Subject LA"

    def test_transit_both_subjects(self, subject_new_york, subject_los_angeles):
        chart = ChartDataFactory.create_transit_chart_data(
            subject_new_york,
            subject_los_angeles,
        )

        assert chart is not None
        assert chart.first_subject.name == "Test Subject NY"

    def test_synastry_missing_second_raises(self, subject_new_york):
        with pytest.raises(KerykeionException):
            ChartDataFactory.create_chart_data("Synastry", subject_new_york)

    def test_transit_missing_second_raises(self, subject_new_york):
        with pytest.raises(KerykeionException):
            ChartDataFactory.create_chart_data("Transit", subject_new_york)

    def test_element_distribution_present(self, subject_new_york):
        chart = ChartDataFactory.create_natal_chart_data(subject_new_york)
        assert chart.element_distribution is not None

    def test_quality_distribution_present(self, subject_new_york):
        chart = ChartDataFactory.create_natal_chart_data(subject_new_york)
        assert chart.quality_distribution is not None

    def test_aspects_not_none(self, subject_new_york):
        chart = ChartDataFactory.create_natal_chart_data(subject_new_york)
        assert chart.aspects is not None

    def test_dual_aspects_not_none(self, subject_new_york, subject_los_angeles):
        chart = ChartDataFactory.create_synastry_chart_data(
            subject_new_york,
            subject_los_angeles,
        )
        assert chart.aspects is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
