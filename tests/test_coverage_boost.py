# -*- coding: utf-8 -*-
"""
Coverage Boost Tests for Kerykeion

This module contains tests specifically designed to increase code coverage
by targeting previously untested code paths and edge cases.

Test Categories:
1. Sidereal zodiac charts (all chart types)
2. External view mode for Natal charts
3. Aspect grid table type for dual charts
4. ReportGenerator edge cases
5. Charts utilities edge cases
6. Backward compatibility edge cases
7. SVG generation options
8. House comparison edge cases
9. Astrological subject factory edge cases
"""

import warnings
import tempfile
import os
from pathlib import Path
from datetime import timedelta

import pytest

from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDrawer,
    ChartDataFactory,
    ReportGenerator,
    CompositeSubjectFactory,
)
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.schemas import KerykeionException


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture(scope="module")
def rome_location():
    return {
        "city": "Rome",
        "nation": "IT",
        "lat": 41.9028,
        "lng": 12.4964,
        "tz_str": "Europe/Rome",
        "online": False,
        "suppress_geonames_warning": True,
    }


@pytest.fixture(scope="module")
def tropical_subject(rome_location):
    return AstrologicalSubjectFactory.from_birth_data(
        "Test Subject",
        year=1990,
        month=6,
        day=15,
        hour=12,
        minute=30,
        **rome_location,
    )


@pytest.fixture(scope="module")
def second_subject(rome_location):
    return AstrologicalSubjectFactory.from_birth_data(
        "Second Subject",
        year=1992,
        month=3,
        day=20,
        hour=8,
        minute=15,
        **rome_location,
    )


@pytest.fixture(scope="module")
def sidereal_subject(rome_location):
    """Subject with Sidereal zodiac type."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Sidereal Subject",
        year=1990,
        month=6,
        day=15,
        hour=12,
        minute=30,
        zodiac_type="Sidereal",
        sidereal_mode="FAGAN_BRADLEY",
        **rome_location,
    )


@pytest.fixture(scope="module")
def sidereal_second_subject(rome_location):
    """Second subject with Sidereal zodiac type."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Sidereal Second",
        year=1992,
        month=3,
        day=20,
        hour=8,
        minute=15,
        zodiac_type="Sidereal",
        sidereal_mode="FAGAN_BRADLEY",
        **rome_location,
    )


# ==============================================================================
# SECTION 1: SIDEREAL CHARTS TESTS
# ==============================================================================


class TestSiderealCharts:
    """Test Sidereal zodiac chart generation for all chart types."""

    def test_natal_chart_sidereal(self, sidereal_subject):
        """Test Natal chart with Sidereal zodiac."""
        chart_data = ChartDataFactory.create_natal_chart_data(sidereal_subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert "<svg" in svg
        assert chart_data.chart_type == "Natal"

    def test_transit_chart_sidereal(self, sidereal_subject, sidereal_second_subject):
        """Test Transit chart with Sidereal zodiac."""
        chart_data = ChartDataFactory.create_transit_chart_data(sidereal_subject, sidereal_second_subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert "<svg" in svg
        assert chart_data.chart_type == "Transit"

    def test_synastry_chart_sidereal(self, sidereal_subject, sidereal_second_subject):
        """Test Synastry chart with Sidereal zodiac."""
        chart_data = ChartDataFactory.create_synastry_chart_data(sidereal_subject, sidereal_second_subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert "<svg" in svg
        assert chart_data.chart_type == "Synastry"

    def test_composite_chart_sidereal(self, sidereal_subject, sidereal_second_subject):
        """Test Composite chart with Sidereal zodiac."""
        composite_subject = CompositeSubjectFactory(
            sidereal_subject, sidereal_second_subject
        ).get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert "<svg" in svg
        assert chart_data.chart_type == "Composite"

    def test_solar_return_chart_sidereal(self, rome_location):
        """Test Solar Return chart with Sidereal zodiac."""
        natal = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Return Test",
            year=1985,
            month=7,
            day=10,
            hour=14,
            minute=30,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            **rome_location,
        )
        factory = PlanetaryReturnFactory(
            natal,
            city=rome_location["city"],
            nation=rome_location["nation"],
            lat=rome_location["lat"],
            lng=rome_location["lng"],
            tz_str=rome_location["tz_str"],
            online=False,
        )
        solar_return = factory.next_return_from_iso_formatted_time(natal.iso_formatted_local_datetime, "Solar")
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert "<svg" in svg

    def test_dual_return_chart_sidereal(self, rome_location):
        """Test Dual Return chart with Sidereal zodiac."""
        natal = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Dual Return",
            year=1985,
            month=7,
            day=10,
            hour=14,
            minute=30,
            zodiac_type="Sidereal",
            sidereal_mode="FAGAN_BRADLEY",
            **rome_location,
        )
        factory = PlanetaryReturnFactory(
            natal,
            city=rome_location["city"],
            nation=rome_location["nation"],
            lat=rome_location["lat"],
            lng=rome_location["lng"],
            tz_str=rome_location["tz_str"],
            online=False,
        )
        solar_return = factory.next_return_from_iso_formatted_time(natal.iso_formatted_local_datetime, "Solar")
        chart_data = ChartDataFactory.create_return_chart_data(natal, solar_return)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert "<svg" in svg


# ==============================================================================
# SECTION 2: EXTERNAL VIEW TESTS
# ==============================================================================


class TestExternalView:
    """Test external_view mode for Natal charts."""

    def test_natal_chart_external_view(self, tropical_subject):
        """Test Natal chart with external_view=True."""
        chart_data = ChartDataFactory.create_natal_chart_data(tropical_subject)
        drawer = ChartDrawer(chart_data, external_view=True)
        svg = drawer.generate_svg_string()
        assert "<svg" in svg

    def test_natal_chart_external_view_dark_theme(self, tropical_subject):
        """Test Natal chart with external_view and dark theme."""
        chart_data = ChartDataFactory.create_natal_chart_data(tropical_subject)
        drawer = ChartDrawer(chart_data, external_view=True, theme="dark")
        svg = drawer.generate_svg_string()
        assert "<svg" in svg


# ==============================================================================
# SECTION 3: ASPECT GRID TABLE TYPE TESTS
# ==============================================================================


class TestAspectGridTable:
    """Test double_chart_aspect_grid_type='table' for dual charts."""

    def test_transit_aspect_grid_table(self, tropical_subject, second_subject):
        """Test Transit chart with table aspect grid."""
        chart_data = ChartDataFactory.create_transit_chart_data(tropical_subject, second_subject)
        drawer = ChartDrawer(chart_data, double_chart_aspect_grid_type="table")
        svg = drawer.generate_svg_string()
        assert "<svg" in svg

    def test_synastry_aspect_grid_table(self, tropical_subject, second_subject):
        """Test Synastry chart with table aspect grid."""
        chart_data = ChartDataFactory.create_synastry_chart_data(tropical_subject, second_subject)
        drawer = ChartDrawer(chart_data, double_chart_aspect_grid_type="table")
        svg = drawer.generate_svg_string()
        assert "<svg" in svg

    def test_dual_return_aspect_grid_table(self, rome_location):
        """Test Dual Return chart with table aspect grid."""
        natal = AstrologicalSubjectFactory.from_birth_data(
            "Dual Return Table",
            year=1985,
            month=7,
            day=10,
            hour=14,
            minute=30,
            **rome_location,
        )
        factory = PlanetaryReturnFactory(
            natal,
            city=rome_location["city"],
            nation=rome_location["nation"],
            lat=rome_location["lat"],
            lng=rome_location["lng"],
            tz_str=rome_location["tz_str"],
            online=False,
        )
        solar_return = factory.next_return_from_iso_formatted_time(natal.iso_formatted_local_datetime, "Solar")
        chart_data = ChartDataFactory.create_return_chart_data(natal, solar_return)
        drawer = ChartDrawer(chart_data, double_chart_aspect_grid_type="table")
        svg = drawer.generate_svg_string()
        assert "<svg" in svg


# ==============================================================================
# SECTION 4: REPORT GENERATOR EDGE CASES
# ==============================================================================


class TestReportGeneratorEdgeCases:
    """Test ReportGenerator edge cases and all chart types."""

    def test_report_transit_chart(self, tropical_subject, second_subject):
        """Test ReportGenerator for Transit chart."""
        chart_data = ChartDataFactory.create_transit_chart_data(tropical_subject, second_subject)
        report = ReportGenerator(chart_data)
        text = report.generate_report(max_aspects=5)
        assert "Transit" in text
        assert tropical_subject.name in text

    def test_report_dual_return_chart(self, rome_location):
        """Test ReportGenerator for Dual Return chart."""
        natal = AstrologicalSubjectFactory.from_birth_data(
            "Dual Return Report",
            year=1985,
            month=7,
            day=10,
            hour=14,
            minute=30,
            **rome_location,
        )
        factory = PlanetaryReturnFactory(
            natal,
            city=rome_location["city"],
            nation=rome_location["nation"],
            lat=rome_location["lat"],
            lng=rome_location["lng"],
            tz_str=rome_location["tz_str"],
            online=False,
        )
        solar_return = factory.next_return_from_iso_formatted_time(natal.iso_formatted_local_datetime, "Solar")
        chart_data = ChartDataFactory.create_return_chart_data(natal, solar_return)
        report = ReportGenerator(chart_data)
        text = report.generate_report(max_aspects=3)
        assert "Return" in text

    def test_report_lunar_return_chart(self, rome_location):
        """Test ReportGenerator for Lunar Return chart."""
        natal = AstrologicalSubjectFactory.from_birth_data(
            "Lunar Return Report",
            year=1985,
            month=7,
            day=10,
            hour=14,
            minute=30,
            **rome_location,
        )
        factory = PlanetaryReturnFactory(
            natal,
            city=rome_location["city"],
            nation=rome_location["nation"],
            lat=rome_location["lat"],
            lng=rome_location["lng"],
            tz_str=rome_location["tz_str"],
            online=False,
        )
        lunar_return = factory.next_return_from_iso_formatted_time(natal.iso_formatted_local_datetime, "Lunar")
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(lunar_return)
        report = ReportGenerator(chart_data)
        text = report.generate_report()
        assert "Lunar Return" in text

    def test_report_relationship_score(self, tropical_subject, second_subject):
        """Test ReportGenerator with relationship score section."""
        chart_data = ChartDataFactory.create_synastry_chart_data(tropical_subject, second_subject)
        report = ReportGenerator(chart_data)
        text = report.generate_report(max_aspects=10)
        # Check that house comparison section exists
        assert "points in" in text.lower()


# ==============================================================================
# SECTION 5: CHARTS UTILS EDGE CASES
# ==============================================================================


class TestChartsUtilsEdgeCases:
    """Test edge cases in charts_utils module."""

    def test_degree_sum_exact_360(self):
        """Test degreeSum returns 0.0 when sum is exactly 360."""
        from kerykeion.charts.charts_utils import degreeSum

        result = degreeSum(180, 180)
        assert result == 0.0

    def test_normalize_degree_360(self):
        """Test normalizeDegree returns 0.0 for input 360."""
        from kerykeion.charts.charts_utils import normalizeDegree

        result = normalizeDegree(360)
        assert result == 0.0

    def test_normalize_degree_negative(self):
        """Test normalizeDegree handles negative values."""
        from kerykeion.charts.charts_utils import normalizeDegree

        result = normalizeDegree(-90)
        assert result == 270.0

    def test_dec_hour_join(self):
        """Test decHourJoin calculation."""
        from kerykeion.charts.charts_utils import decHourJoin

        # 12 hours, 30 minutes, 0 seconds = 12.5
        result = decHourJoin(12, 30, 0)
        assert result == pytest.approx(12.5, abs=0.001)

    def test_offset_to_tz_none_raises(self):
        """Test offsetToTz raises exception for None input."""
        from kerykeion.charts.charts_utils import offsetToTz

        with pytest.raises(Exception):
            offsetToTz(None)

    def test_offset_to_tz_valid(self):
        """Test offsetToTz with valid timedelta."""
        from kerykeion.charts.charts_utils import offsetToTz

        offset = timedelta(hours=2)
        result = offsetToTz(offset)
        assert result == 2.0

    def test_get_decoded_celestial_point_unknown(self):
        """Test unknown celestial point raises exception."""
        from kerykeion.charts.charts_utils import get_decoded_kerykeion_celestial_point_name
        from kerykeion.schemas.settings_models import KerykeionLanguageCelestialPointModel

        # Create a minimal language model
        lang_model = KerykeionLanguageCelestialPointModel(
            Sun="Sun",
            Moon="Moon",
            Mercury="Mercury",
            Venus="Venus",
            Mars="Mars",
            Jupiter="Jupiter",
            Saturn="Saturn",
            Uranus="Uranus",
            Neptune="Neptune",
            Pluto="Pluto",
            Mean_North_Lunar_Node="Mean Node",
            True_North_Lunar_Node="True Node",
            Chiron="Chiron",
            Mean_Lilith="Lilith",
            Mean_South_Lunar_Node="South Node",
            True_South_Lunar_Node="True South Node",
            True_Lilith="True Lilith",
            Earth="Earth",
            Pholus="Pholus",
            Ceres="Ceres",
            Pallas="Pallas",
            Juno="Juno",
            Vesta="Vesta",
            Eris="Eris",
            Sedna="Sedna",
            Haumea="Haumea",
            Makemake="Makemake",
            Ixion="Ixion",
            Orcus="Orcus",
            Quaoar="Quaoar",
            Regulus="Regulus",
            Spica="Spica",
            Pars_Fortunae="Part of Fortune",
            Pars_Spiritus="Part of Spirit",
            Pars_Amoris="Part of Love",
            Pars_Fidei="Part of Faith",
            Vertex="Vertex",
            Anti_Vertex="Anti-Vertex",
            Ascendant="Ascendant",
            Medium_Coeli="Medium Coeli",
            Descendant="Descendant",
            Imum_Coeli="Imum Coeli",
        )

        with pytest.raises(KerykeionException):
            get_decoded_kerykeion_celestial_point_name("NonExistentPoint", lang_model)


# ==============================================================================
# SECTION 6: BACKWARD COMPATIBILITY EDGE CASES
# ==============================================================================


class TestBackwardCompatibilityEdgeCases:
    """Test edge cases in backward compatibility layer."""

    def test_legacy_node_names_normalization(self):
        """Test legacy node name normalization helper function."""
        from kerykeion.backword import _normalize_active_points

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Test with legacy node name
            result = _normalize_active_points(["Sun", "Moon", "Mean_Node"])

            # Check deprecation warning was raised for Mean_Node
            node_warnings = [x for x in w if "Mean_Node" in str(x.message)]
            assert len(node_warnings) >= 1

    def test_json_dump_false(self):
        """Test json(dump=False) returns string without writing file."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from kerykeion.backword import AstrologicalSubject

            subject = AstrologicalSubject(
                name="JSON Test",
                year=1990,
                month=1,
                day=1,
                hour=12,
                minute=0,
                city="Rome",
                nation="IT",
                lat=41.9028,
                lng=12.4964,
                tz_str="Europe/Rome",
                online=False,
            )

            json_str = subject.json(dump=False)
            assert isinstance(json_str, str)
            assert "JSON Test" in json_str

    def test_json_dump_custom_destination(self, tmp_path):
        """Test json(dump=True, destination_folder=...) creates file in custom location."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from kerykeion.backword import AstrologicalSubject

            subject = AstrologicalSubject(
                name="Custom Dest",
                year=1990,
                month=1,
                day=1,
                hour=12,
                minute=0,
                city="Rome",
                nation="IT",
                lat=41.9028,
                lng=12.4964,
                tz_str="Europe/Rome",
                online=False,
            )

            subject.json(dump=True, destination_folder=str(tmp_path))
            expected_file = tmp_path / "Custom Dest_kerykeion.json"
            assert expected_file.exists()


# ==============================================================================
# SECTION 7: SVG GENERATION OPTIONS
# ==============================================================================


class TestSVGGenerationOptions:
    """Test SVG generation options for wheel-only and aspect-grid-only."""

    def test_wheel_only_minify_true(self, tropical_subject):
        """Test wheel-only SVG with minify=True."""
        chart_data = ChartDataFactory.create_natal_chart_data(tropical_subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_wheel_only_svg_string(minify=True)
        assert "<svg" in svg
        # Minified SVG should have fewer newlines
        assert svg.count("\n") < 100

    def test_wheel_only_minify_false(self, tropical_subject):
        """Test wheel-only SVG with minify=False."""
        chart_data = ChartDataFactory.create_natal_chart_data(tropical_subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_wheel_only_svg_string(minify=False)
        assert "<svg" in svg

    def test_aspect_grid_only_minify_true(self, tropical_subject):
        """Test aspect-grid-only SVG with minify=True."""
        chart_data = ChartDataFactory.create_natal_chart_data(tropical_subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_aspect_grid_only_svg_string(minify=True)
        assert "<svg" in svg

    def test_aspect_grid_only_remove_css_true(self, tropical_subject):
        """Test aspect-grid-only SVG with remove_css_variables=True."""
        chart_data = ChartDataFactory.create_natal_chart_data(tropical_subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_aspect_grid_only_svg_string(minify=True, remove_css_variables=True)
        assert "<svg" in svg
        # Should not contain CSS variables
        assert "var(--" not in svg


# ==============================================================================
# SECTION 8: HOUSE COMPARISON EDGE CASES
# ==============================================================================


class TestHouseComparisonEdgeCases:
    """Test edge cases in house comparison utilities."""

    def test_calculate_cusps_in_reciprocal_houses(self, tropical_subject, second_subject):
        """Test calculate_cusps_in_reciprocal_houses function."""
        from kerykeion.house_comparison.house_comparison_utils import calculate_cusps_in_reciprocal_houses

        result = calculate_cusps_in_reciprocal_houses(tropical_subject, second_subject)
        assert isinstance(result, list)
        assert len(result) == 12  # 12 houses


# ==============================================================================
# SECTION 9: ASTROLOGICAL SUBJECT FACTORY EDGE CASES
# ==============================================================================


class TestAstrologicalSubjectFactoryEdgeCases:
    """Test edge cases in AstrologicalSubjectFactory."""

    def test_sidereal_without_mode_uses_default(self, rome_location):
        """Test that Sidereal zodiac without explicit mode uses default."""
        # Create subject with Sidereal but no explicit sidereal_mode
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Default Mode",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=30,
            zodiac_type="Sidereal",
            # sidereal_mode not specified - should use FAGAN_BRADLEY
            **rome_location,
        )
        assert subject.zodiac_type == "Sidereal"
        assert subject.sidereal_mode == "FAGAN_BRADLEY"

    def test_pars_fortunae_calculation(self, rome_location):
        """Test Pars Fortunae (Part of Fortune) calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Pars Fortunae Test",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=30,
            active_points=["Sun", "Moon", "Ascendant", "Pars_Fortunae"],
            **rome_location,
        )
        assert subject.pars_fortunae is not None
        assert subject.pars_fortunae.name == "Pars_Fortunae"

    def test_pars_spiritus_calculation(self, rome_location):
        """Test Pars Spiritus (Part of Spirit) calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Pars Spiritus Test",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=30,
            active_points=["Sun", "Moon", "Ascendant", "Pars_Spiritus"],
            **rome_location,
        )
        assert subject.pars_spiritus is not None
        assert subject.pars_spiritus.name == "Pars_Spiritus"

    def test_night_chart_pars_fortunae(self, rome_location):
        """Test Pars Fortunae for night chart (Sun below horizon)."""
        # Use a night time (22:00) to get Sun below horizon
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Night Chart Test",
            year=1990,
            month=6,
            day=15,
            hour=22,  # Night time
            minute=30,
            active_points=["Sun", "Moon", "Ascendant", "Pars_Fortunae"],
            **rome_location,
        )
        assert subject.pars_fortunae is not None


# ==============================================================================
# SECTION 10: SAVE METHODS WITH AUTO-GENERATED FILENAMES
# ==============================================================================


class TestSaveMethodsAutoFilename:
    """Test save methods with auto-generated filenames."""

    def test_save_svg_without_filename(self, tropical_subject, tmp_path):
        """Test save_svg with output_path only (auto-generate filename)."""
        chart_data = ChartDataFactory.create_natal_chart_data(tropical_subject)
        drawer = ChartDrawer(chart_data)
        drawer.save_svg(output_path=str(tmp_path))

        # Should create file with auto-generated name
        svg_files = list(tmp_path.glob("*.svg"))
        assert len(svg_files) == 1

    def test_save_dual_return_svg_auto_filename(self, rome_location, tmp_path):
        """Test save_svg for DualReturnChart with auto-generated filename."""
        natal = AstrologicalSubjectFactory.from_birth_data(
            "Dual Return Save",
            year=1985,
            month=7,
            day=10,
            hour=14,
            minute=30,
            **rome_location,
        )
        factory = PlanetaryReturnFactory(
            natal,
            city=rome_location["city"],
            nation=rome_location["nation"],
            lat=rome_location["lat"],
            lng=rome_location["lng"],
            tz_str=rome_location["tz_str"],
            online=False,
        )
        solar_return = factory.next_return_from_iso_formatted_time(natal.iso_formatted_local_datetime, "Solar")
        chart_data = ChartDataFactory.create_return_chart_data(natal, solar_return)
        drawer = ChartDrawer(chart_data)
        drawer.save_svg(output_path=str(tmp_path))

        svg_files = list(tmp_path.glob("*.svg"))
        assert len(svg_files) == 1


# ==============================================================================
# SECTION 11: ADDITIONAL COVERAGE TESTS
# ==============================================================================


class TestAdditionalCoverage:
    """Additional tests to boost coverage further."""

    def test_lunar_return_single_chart(self, rome_location):
        """Test Lunar Return single wheel chart."""
        natal = AstrologicalSubjectFactory.from_birth_data(
            "Lunar Return Single",
            year=1985,
            month=7,
            day=10,
            hour=14,
            minute=30,
            **rome_location,
        )
        factory = PlanetaryReturnFactory(
            natal,
            city=rome_location["city"],
            nation=rome_location["nation"],
            lat=rome_location["lat"],
            lng=rome_location["lng"],
            tz_str=rome_location["tz_str"],
            online=False,
        )
        lunar_return = factory.next_return_from_iso_formatted_time(natal.iso_formatted_local_datetime, "Lunar")
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(lunar_return)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert "<svg" in svg

    def test_chart_without_lunar_phase(self, rome_location):
        """Test chart generation when lunar_phase might be None."""
        # Create subject with minimal active points that might not include Moon
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Minimal Points Test",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=30,
            active_points=["Sun", "Mercury", "Venus"],  # No Moon
            **rome_location,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert "<svg" in svg

    def test_synastry_with_custom_active_aspects(self, tropical_subject, second_subject):
        """Test Synastry chart with custom active aspects."""
        from kerykeion.schemas.kr_models import ActiveAspect

        custom_aspects = [
            ActiveAspect(name="conjunction", orb=5),
            ActiveAspect(name="opposition", orb=5),
        ]
        chart_data = ChartDataFactory.create_synastry_chart_data(
            tropical_subject, second_subject, active_aspects=custom_aspects
        )
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert "<svg" in svg

    def test_transit_with_custom_active_points(self, rome_location):
        """Test Transit chart with custom active points."""
        from kerykeion.schemas.kr_literals import AstrologicalPoint
        from typing import List

        subject = AstrologicalSubjectFactory.from_birth_data(
            "Transit Custom Points",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=30,
            **rome_location,
        )
        transit_subject = AstrologicalSubjectFactory.from_birth_data(
            "Transit Subject",
            year=2024,
            month=1,
            day=15,
            hour=12,
            minute=30,
            **rome_location,
        )
        custom_points: List[AstrologicalPoint] = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
        chart_data = ChartDataFactory.create_transit_chart_data(subject, transit_subject, active_points=custom_points)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert "<svg" in svg

    def test_report_with_include_aspects_false(self, tropical_subject):
        """Test ReportGenerator with include_aspects=False."""
        chart_data = ChartDataFactory.create_natal_chart_data(tropical_subject)
        report = ReportGenerator(chart_data, include_aspects=False)
        text = report.generate_report()
        # Should not have Aspects section when disabled
        assert "Element Distribution" in text

    def test_composite_chart_basic(self, tropical_subject, second_subject):
        """Test Composite chart basic generation."""
        composite_subject = CompositeSubjectFactory(
            tropical_subject, second_subject
        ).get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert "<svg" in svg


class TestReportGeneratorMoreCases:
    """Additional ReportGenerator tests for edge cases."""

    def test_report_print_method(self, tropical_subject, capsys):
        """Test ReportGenerator print_report method."""
        chart_data = ChartDataFactory.create_natal_chart_data(tropical_subject)
        report = ReportGenerator(chart_data)
        report.print_report(max_aspects=2)
        captured = capsys.readouterr()
        assert "Natal Chart Report" in captured.out

    def test_report_subject_only(self, tropical_subject):
        """Test ReportGenerator with subject model only (not chart data)."""
        report = ReportGenerator(tropical_subject)
        text = report.generate_report()
        assert "Subject Report" in text
        assert tropical_subject.name in text


class TestChartDrawerEdgeCases:
    """Additional ChartDrawer edge cases."""

    def test_chart_with_all_themes(self, tropical_subject):
        """Test all available themes generate valid SVG."""
        chart_data = ChartDataFactory.create_natal_chart_data(tropical_subject)

        for theme in ["classic", "dark", "light", "dark-high-contrast"]:
            drawer = ChartDrawer(chart_data, theme=theme)
            svg = drawer.generate_svg_string()
            assert "<svg" in svg, f"Theme {theme} failed to generate valid SVG"

    def test_chart_with_all_languages(self, rome_location):
        """Test multiple chart languages."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Language Test",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=30,
            **rome_location,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)

        for lang in ["EN", "IT", "FR", "DE", "ES"]:
            drawer = ChartDrawer(chart_data, chart_language=lang)
            svg = drawer.generate_svg_string()
            assert "<svg" in svg, f"Language {lang} failed to generate valid SVG"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
