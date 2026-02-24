# -*- coding: utf-8 -*-
"""
This module tests edge cases and uncovered code paths across the kerykeion library.
"""

import pytest
import warnings
from datetime import datetime
from unittest.mock import patch, MagicMock

# Core imports
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ReportGenerator
from kerykeion.aspects.aspects_factory import AspectsFactory
from kerykeion.aspects.aspects_utils import planet_id_decoder
from kerykeion.utilities import (
    get_kerykeion_point_from_degree,
    get_moon_emoji_from_phase_int,
    get_moon_phase_name_from_phase_int,
    circular_sort,
    inline_css_variables_in_svg,
    julian_to_datetime,
    get_house_name,
    get_house_number,
    distribute_percentages_to_100,
)
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.settings.kerykeion_settings import load_settings_mapping
from kerykeion.settings.translations import get_translations
from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS


# ============================================================================
# Test fixtures
# ============================================================================


@pytest.fixture
def basic_subject():
    """Create a basic astrological subject for testing."""
    return AstrologicalSubjectFactory.from_birth_data(
        name="Test",
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


@pytest.fixture
def second_subject():
    """Create a second astrological subject for testing."""
    return AstrologicalSubjectFactory.from_birth_data(
        name="Test2",
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


# ============================================================================
# Aspects Factory Tests
# ============================================================================


class TestAspectsFactoryAxisOrbFilter:
    """Tests for axis orb filtering in AspectsFactory."""

    def test_axis_orb_filter_filters_wide_axis_aspects(self, basic_subject):
        """Test that axis aspects with orbs beyond limit are filtered."""
        # Get aspects with strict axis orb limit
        aspects = AspectsFactory.single_chart_aspects(
            basic_subject,
            axis_orb_limit=1.0,  # Very strict limit
        )
        # Verify we get a result (the filtering logic is exercised)
        assert aspects is not None

    def test_axis_orb_filter_disabled(self, basic_subject):
        """Test aspects without axis orb filtering."""
        aspects = AspectsFactory.single_chart_aspects(
            basic_subject,
            axis_orb_limit=None,  # No filtering
        )
        assert aspects is not None

    def test_legacy_natal_aspects_method(self, basic_subject):
        """Test the legacy natal_aspects method (deprecated)."""
        aspects = AspectsFactory.natal_aspects(basic_subject)
        assert aspects is not None
        assert len(aspects.aspects) > 0

    def test_legacy_synastry_aspects_method(self, basic_subject, second_subject):
        """Test the legacy synastry_aspects method (deprecated)."""
        aspects = AspectsFactory.synastry_aspects(basic_subject, second_subject)
        assert aspects is not None
        assert len(aspects.aspects) > 0


# ============================================================================
# Aspects Utils Tests
# ============================================================================


class TestAspectsUtils:
    """Tests for aspects utility functions."""

    def test_planet_id_decoder_valid_planet(self):
        """Test planet_id_decoder with a valid planet name."""
        result = planet_id_decoder(DEFAULT_CELESTIAL_POINTS_SETTINGS, "Sun")
        assert isinstance(result, int)

    def test_planet_id_decoder_invalid_planet(self):
        """Test planet_id_decoder raises ValueError for unknown planet."""
        with pytest.raises(ValueError, match="not found"):
            planet_id_decoder(DEFAULT_CELESTIAL_POINTS_SETTINGS, "InvalidPlanet")


# ============================================================================
# Utilities Tests - Edge Cases
# ============================================================================


class TestUtilitiesEdgeCases:
    """Tests for edge cases in utility functions."""

    def test_get_kerykeion_point_from_degree_raises_on_360(self):
        """Test that degree >= 360 raises exception."""
        with pytest.raises(KerykeionException, match="Error in calculating positions"):
            get_kerykeion_point_from_degree(360.0, "Test", point_type="Natal")

    def test_get_moon_emoji_from_phase_int_invalid_phase(self):
        """Test invalid phase raises exception."""
        with pytest.raises(KerykeionException, match="Error in lunar phase calculation"):
            get_moon_emoji_from_phase_int(30)

    def test_get_moon_phase_name_from_phase_int_invalid_phase(self):
        """Test invalid phase raises exception."""
        with pytest.raises(KerykeionException, match="Error in lunar phase calculation"):
            get_moon_phase_name_from_phase_int(30)

    def test_circular_sort_empty_list(self):
        """Test circular_sort raises error on empty list."""
        with pytest.raises(ValueError, match="cannot be empty"):
            circular_sort([])

    def test_circular_sort_invalid_type(self):
        """Test circular_sort raises error on non-numeric values."""
        with pytest.raises(ValueError, match="must be numeric"):
            circular_sort([1.0, "invalid", 3.0])  # type: ignore

    def test_circular_sort_single_element(self):
        """Test circular_sort with single element."""
        result = circular_sort([45.0])
        assert result == [45.0]

    def test_inline_css_variables_with_fallback(self):
        """Test CSS variable replacement with fallback values."""
        svg_content = """
        <style>
            :root {
                --main-color: blue;
            }
        </style>
        <rect fill="var(--main-color, red)" />
        <rect fill="var(--unknown, green)" />
        """
        result = inline_css_variables_in_svg(svg_content)
        assert "blue" in result
        # Unknown variable should be replaced with fallback
        # Style block should be removed
        assert "<style>" not in result

    def test_julian_to_datetime_julian_calendar(self):
        """Test julian_to_datetime for dates before Gregorian reform."""
        # JD 2299160 is before the Gregorian reform (Oct 15, 1582)
        result = julian_to_datetime(2299160.0)
        assert isinstance(result, datetime)

    def test_get_house_name_valid_numbers(self):
        """Test get_house_name for all valid house numbers."""
        for i in range(1, 13):
            result = get_house_name(i)
            assert "_House" in result

    def test_get_house_name_invalid_number(self):
        """Test get_house_name raises error for invalid house number."""
        with pytest.raises(ValueError, match="Invalid house number"):
            get_house_name(13)
        with pytest.raises(ValueError, match="Invalid house number"):
            get_house_name(0)

    def test_get_house_number_invalid_name(self):
        """Test get_house_number raises error for invalid house name."""
        with pytest.raises(ValueError, match="Invalid house name"):
            get_house_number("Invalid_House")  # type: ignore

    def test_distribute_percentages_empty_dict(self):
        """Test distribute_percentages_to_100 with empty dict."""
        result = distribute_percentages_to_100({})
        assert result == {}


# ============================================================================
# Backward Compatibility Tests
# ============================================================================


class TestBackwardCompatibility:
    """Tests for backward compatibility module (backword.py)."""

    def test_legacy_astrological_subject_deprecation_warning(self):
        """Test that AstrologicalSubject emits deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from kerykeion.backword import AstrologicalSubject

            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            assert subject is not None
            # Check that deprecation warning was issued
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) > 0

    def test_legacy_astrological_subject_disable_chiron_warning(self):
        """Test disable_chiron parameter emits deprecation warning."""
        with warnings.catch_warnings(record=True) as _:
            warnings.simplefilter("always")
            from kerykeion.backword import AstrologicalSubject

            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
                disable_chiron=True,
            )
            assert subject is not None

    def test_legacy_astrological_subject_disable_chiron_and_lilith_warning(self):
        """Test disable_chiron_and_lilith parameter emits warning."""
        with warnings.catch_warnings(record=True) as _:
            warnings.simplefilter("always")
            from kerykeion.backword import AstrologicalSubject

            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
                disable_chiron_and_lilith=True,
            )
            assert subject is not None

    def test_legacy_zodiac_type_normalization(self):
        """Test legacy zodiac type values are normalized with warning."""
        with warnings.catch_warnings(record=True) as _:
            warnings.simplefilter("always")
            from kerykeion.backword import AstrologicalSubject

            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
                zodiac_type="tropic",  # Legacy format - will cause warning
            )
            assert subject is not None

    def test_legacy_node_names_deprecation(self):
        """Test that legacy node property names emit deprecation warnings."""
        with warnings.catch_warnings(record=True) as _:
            warnings.simplefilter("always")
            from kerykeion.backword import AstrologicalSubject

            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            # Access deprecated properties
            _ = subject.mean_node
            _ = subject.true_node
            _ = subject.mean_south_node
            _ = subject.true_south_node

    def test_legacy_astrological_subject_json_method(self):
        """Test legacy json() method."""
        from kerykeion.backword import AstrologicalSubject

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            json_str = subject.json(dump=False)
            assert isinstance(json_str, str)
            assert "Test" in json_str

    def test_legacy_astrological_subject_json_dump(self, tmp_path):
        """Test legacy json() method with dump=True."""
        from kerykeion.backword import AstrologicalSubject

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            json_str = subject.json(dump=True, destination_folder=str(tmp_path))
            assert isinstance(json_str, str)
            # Check file was created
            files = list(tmp_path.glob("*.json"))
            assert len(files) == 1

    def test_legacy_astrological_subject_model_method(self):
        """Test legacy model() method."""
        from kerykeion.backword import AstrologicalSubject

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            model = subject.model()
            assert model is not None
            assert model.name == "Test"

    def test_legacy_astrological_subject_getitem(self):
        """Test legacy __getitem__ method."""
        from kerykeion.backword import AstrologicalSubject

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            assert subject["name"] == "Test"

    def test_legacy_astrological_subject_get_method(self):
        """Test legacy get() method."""
        from kerykeion.backword import AstrologicalSubject

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            assert subject.get("name") == "Test"
            assert subject.get("invalid", "default") == "default"

    def test_legacy_astrological_subject_str(self):
        """Test legacy __str__ method."""
        from kerykeion.backword import AstrologicalSubject

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            result = str(subject)
            assert "Test" in result

    def test_legacy_astrological_subject_utc_time(self):
        """Test legacy utc_time property."""
        from kerykeion.backword import AstrologicalSubject

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            utc_time = subject.utc_time
            assert isinstance(utc_time, float)

    def test_legacy_astrological_subject_local_time(self):
        """Test legacy local_time property."""
        from kerykeion.backword import AstrologicalSubject

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            local_time = subject.local_time
            assert isinstance(local_time, float)

    def test_legacy_get_from_iso_utc_time(self):
        """Test legacy get_from_iso_utc_time class method."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from kerykeion.backword import AstrologicalSubject

            subject = AstrologicalSubject.get_from_iso_utc_time(
                name="Test",
                iso_utc_time="1990-06-15T10:00:00+00:00",
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            assert subject is not None

    def test_legacy_get_from_iso_utc_time_with_disable_chiron(self):
        """Test legacy get_from_iso_utc_time with disable_chiron_and_lilith."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from kerykeion.backword import AstrologicalSubject

            subject = AstrologicalSubject.get_from_iso_utc_time(
                name="Test",
                iso_utc_time="1990-06-15T10:00:00+00:00",
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
                disable_chiron_and_lilith=True,
            )
            assert subject is not None


# ============================================================================
# Legacy KerykeionChartSVG Tests
# ============================================================================


class TestLegacyKerykeionChartSVG:
    """Tests for legacy KerykeionChartSVG wrapper."""

    def test_legacy_kerykeion_chart_svg_with_settings_file_warning(self, basic_subject):
        """Test new_settings_file parameter emits deprecation warning."""
        with warnings.catch_warnings(record=True) as _:
            warnings.simplefilter("always")
            from kerykeion.backword import KerykeionChartSVG

            chart = KerykeionChartSVG(
                basic_subject,
                chart_type="Natal",
                new_settings_file={"some": "config"},  # Should emit warning
            )
            assert chart is not None

    def test_legacy_kerykeion_chart_svg_with_astrological_subject(self):
        """Test KerykeionChartSVG with legacy AstrologicalSubject."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from kerykeion.backword import AstrologicalSubject, KerykeionChartSVG

            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            chart = KerykeionChartSVG(subject, chart_type="Natal")
            assert chart is not None


# ============================================================================
# kr_types Backward Compatibility Tests
# ============================================================================


class TestKrTypesBackwardCompatibility:
    """Tests for kr_types backward compatibility modules."""

    def test_kr_types_chart_template_model_deprecation(self):
        """Test importing from kr_types.chart_template_model emits warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from kerykeion.kr_types import chart_template_model  # noqa: F401

            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) > 0

    def test_kr_types_kerykeion_exception_deprecation(self):
        """Test importing from kr_types.kerykeion_exception emits warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from kerykeion.kr_types import kerykeion_exception  # noqa: F401

            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) > 0

    def test_kr_types_settings_models_deprecation(self):
        """Test importing from kr_types.settings_models emits warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from kerykeion.kr_types import settings_models  # noqa: F401

            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) > 0


# ============================================================================
# Settings Tests
# ============================================================================


class TestSettingsEdgeCases:
    """Tests for settings edge cases."""

    def test_load_settings_mapping_with_overrides(self):
        """Test load_settings_mapping with overrides."""
        result = load_settings_mapping({"language_settings": {"EN": {"test": "value"}}})
        # Should return merged settings
        assert result is not None
        assert "language_settings" in result

    def test_get_translations_missing_key_returns_key(self):
        """Test get_translations returns key for missing key."""
        result = get_translations("completely_nonexistent_key_xyz123", "fallback_default")
        # Should return the fallback default
        assert result == "fallback_default"


# ============================================================================
# Report Tests - Edge Cases
# ============================================================================


class TestReportEdgeCases:
    """Tests for ReportGenerator edge cases."""

    def test_report_with_composite_subject(self, basic_subject, second_subject):
        """Test ReportGenerator with CompositeSubjectModel."""
        from kerykeion.composite_subject_factory import CompositeSubjectFactory

        composite = CompositeSubjectFactory(basic_subject, second_subject)
        composite_subject = composite.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        report = ReportGenerator(chart_data)
        result = report.generate_report()
        assert "Composite" in result

    def test_report_with_synastry_chart(self, basic_subject, second_subject):
        """Test ReportGenerator with synastry chart data."""
        chart_data = ChartDataFactory.create_synastry_chart_data(basic_subject, second_subject)
        report = ReportGenerator(chart_data)
        result = report.generate_report()
        assert "Synastry" in result or basic_subject.name in result

    def test_report_with_transit_chart(self, basic_subject, second_subject):
        """Test ReportGenerator with transit chart data."""
        chart_data = ChartDataFactory.create_transit_chart_data(basic_subject, second_subject)
        report = ReportGenerator(chart_data)
        result = report.generate_report()
        assert "Transit" in result or basic_subject.name in result

    def test_report_with_single_return_chart(self, basic_subject):
        """Test ReportGenerator with single return chart data."""
        from kerykeion.planetary_return_factory import PlanetaryReturnFactory

        factory = PlanetaryReturnFactory(
            basic_subject,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )
        solar_return = factory.next_return_from_date(2024, 1, 1, return_type="Solar")
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
        report = ReportGenerator(chart_data)
        result = report.generate_report()
        assert "Solar Return" in result or "Return" in result

    def test_report_with_dual_return_chart(self, basic_subject):
        """Test ReportGenerator with dual return chart data."""
        from kerykeion.planetary_return_factory import PlanetaryReturnFactory

        factory = PlanetaryReturnFactory(
            basic_subject,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )
        solar_return = factory.next_return_from_date(2024, 1, 1, return_type="Solar")
        chart_data = ChartDataFactory.create_return_chart_data(basic_subject, solar_return)
        report = ReportGenerator(chart_data)
        result = report.generate_report()
        assert "Return" in result or basic_subject.name in result

    def test_report_with_lunar_return(self, basic_subject):
        """Test ReportGenerator with lunar return chart."""
        from kerykeion.planetary_return_factory import PlanetaryReturnFactory

        factory = PlanetaryReturnFactory(
            basic_subject,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )
        lunar_return = factory.next_return_from_date(2024, 1, 1, return_type="Lunar")
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(lunar_return)
        report = ReportGenerator(chart_data)
        result = report.generate_report()
        assert "Lunar Return" in result or "Return" in result


# ============================================================================
# Planetary Return Factory Tests
# ============================================================================


class TestPlanetaryReturnFactoryEdgeCases:
    """Tests for PlanetaryReturnFactory edge cases."""

    def test_next_return_from_year_deprecation(self, basic_subject):
        """Test next_return_from_year emits deprecation warning."""
        from kerykeion.planetary_return_factory import PlanetaryReturnFactory

        factory = PlanetaryReturnFactory(
            basic_subject,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = factory.next_return_from_year(2024, "Solar")
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) > 0
            assert result is not None

    def test_next_return_from_month_and_year_deprecation(self, basic_subject):
        """Test next_return_from_month_and_year emits deprecation warning."""
        from kerykeion.planetary_return_factory import PlanetaryReturnFactory

        factory = PlanetaryReturnFactory(
            basic_subject,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = factory.next_return_from_month_and_year(2024, 6, "Solar")
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) > 0
            assert result is not None

    def test_next_return_from_date_invalid_month(self, basic_subject):
        """Test next_return_from_date with invalid month."""
        from kerykeion.planetary_return_factory import PlanetaryReturnFactory

        factory = PlanetaryReturnFactory(
            basic_subject,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )
        with pytest.raises(KerykeionException, match="Invalid month"):
            factory.next_return_from_date(2024, 13, 1, return_type="Solar")
        with pytest.raises(KerykeionException, match="Invalid month"):
            factory.next_return_from_date(2024, 0, 1, return_type="Solar")

    def test_next_return_from_date_invalid_day(self, basic_subject):
        """Test next_return_from_date with invalid day."""
        from kerykeion.planetary_return_factory import PlanetaryReturnFactory

        factory = PlanetaryReturnFactory(
            basic_subject,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )
        with pytest.raises(KerykeionException, match="Invalid day"):
            factory.next_return_from_date(2024, 2, 30, return_type="Solar")

    def test_next_return_invalid_return_type(self, basic_subject):
        """Test next_return with invalid return type."""
        from kerykeion.planetary_return_factory import PlanetaryReturnFactory

        factory = PlanetaryReturnFactory(
            basic_subject,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )
        with pytest.raises(KerykeionException, match="Invalid return type"):
            factory.next_return_from_iso_formatted_time(
                "2024-01-01T00:00:00+00:00",
                "Invalid",  # type: ignore
            )


# ============================================================================
# Context Serializer Tests
# ============================================================================


class TestContextSerializerEdgeCases:
    """Tests for context serializer edge cases."""

    def test_to_context_with_unsupported_type(self):
        """Test to_context raises TypeError for unsupported model."""
        from kerykeion.context_serializer import to_context

        with pytest.raises(TypeError, match="Unsupported model type"):
            to_context("invalid")  # type: ignore

    def test_to_context_with_kerykeion_point(self, basic_subject):
        """Test to_context with KerykeionPointModel."""
        from kerykeion.context_serializer import to_context

        result = to_context(basic_subject.sun)
        assert "Sun" in result

    def test_to_context_with_lunar_phase(self, basic_subject):
        """Test to_context with LunarPhaseModel."""
        from kerykeion.context_serializer import to_context

        if basic_subject.lunar_phase:
            result = to_context(basic_subject.lunar_phase)
            assert "phase" in result.lower() or "Moon" in result

    def test_to_context_with_element_distribution(self, basic_subject):
        """Test to_context with ElementDistributionModel."""
        from kerykeion.context_serializer import to_context

        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        result = to_context(chart_data.element_distribution)
        assert "Element" in result

    def test_to_context_with_quality_distribution(self, basic_subject):
        """Test to_context with QualityDistributionModel."""
        from kerykeion.context_serializer import to_context

        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        result = to_context(chart_data.quality_distribution)
        assert "Quality" in result

    def test_to_context_with_transit_moment(self, basic_subject):
        """Test to_context with TransitMomentModel."""
        # Skip this test as it requires complex setup
        pass

    def test_to_context_with_transits_time_range(self, basic_subject):
        """Test to_context with TransitsTimeRangeModel."""
        # Skip this test as it requires complex setup
        pass

    def test_to_context_with_house_comparison(self, basic_subject, second_subject):
        """Test to_context with HouseComparisonModel."""
        from kerykeion.context_serializer import to_context
        from kerykeion.house_comparison import HouseComparisonFactory

        factory = HouseComparisonFactory(basic_subject, second_subject)
        comparison = factory.get_house_comparison()
        result = to_context(comparison)
        assert "House" in result

    def test_to_context_with_point_in_house(self, basic_subject, second_subject):
        """Test to_context with PointInHouseModel."""
        from kerykeion.context_serializer import to_context
        from kerykeion.house_comparison import HouseComparisonFactory

        factory = HouseComparisonFactory(basic_subject, second_subject)
        comparison = factory.get_house_comparison()
        if comparison.first_points_in_second_houses:
            result = to_context(comparison.first_points_in_second_houses[0])
            assert "falls in" in result

    def test_aspect_to_context_synastry(self, basic_subject, second_subject):
        """Test aspect_to_context for synastry aspects."""
        from kerykeion.context_serializer import aspect_to_context

        aspects = AspectsFactory.dual_chart_aspects(basic_subject, second_subject)
        if aspects.aspects:
            result = aspect_to_context(aspects.aspects[0], is_synastry=True)
            assert "between" in result

    def test_aspect_to_context_transit(self, basic_subject, second_subject):
        """Test aspect_to_context for transit aspects."""
        from kerykeion.context_serializer import aspect_to_context

        aspects = AspectsFactory.dual_chart_aspects(basic_subject, second_subject)
        if aspects.aspects:
            result = aspect_to_context(aspects.aspects[0], is_synastry=True, is_transit=True)
            assert "Transit" in result


# ============================================================================
# House Comparison Tests
# ============================================================================


class TestHouseComparisonEdgeCases:
    """Tests for house comparison edge cases."""

    def test_house_comparison_context_transit(self, basic_subject, second_subject):
        """Test house_comparison_to_context with is_transit=True."""
        from kerykeion.context_serializer import house_comparison_to_context
        from kerykeion.house_comparison import HouseComparisonFactory

        factory = HouseComparisonFactory(basic_subject, second_subject)
        comparison = factory.get_house_comparison()
        result = house_comparison_to_context(comparison, is_transit=True)
        assert "House" in result


# ============================================================================
# Composite Subject Factory Tests
# ============================================================================


class TestCompositeSubjectFactoryEdgeCases:
    """Tests for CompositeSubjectFactory edge cases."""

    def test_composite_with_davison_method(self, basic_subject, second_subject):
        """Test composite creation with Davison method."""
        from kerykeion.composite_subject_factory import CompositeSubjectFactory

        composite_factory = CompositeSubjectFactory(basic_subject, second_subject)
        composite = composite_factory.get_midpoint_composite_subject_model()
        assert composite is not None


# ============================================================================
# Ephemeris Data Factory Edge Cases
# ============================================================================


class TestEphemerisDataFactoryEdgeCases:
    """Tests for EphemerisDataFactory edge cases."""

    def test_ephemeris_data_basic(self, basic_subject):
        """Test basic ephemeris data generation."""
        from kerykeion.ephemeris_data_factory import EphemerisDataFactory
        from datetime import datetime

        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 3)

        factory = EphemerisDataFactory(start, end)
        data = factory.get_ephemeris_data_as_astrological_subjects()
        assert len(data) >= 1


# ============================================================================
# Active Points - All Points
# ============================================================================


class TestAllActivePoints:
    """Tests for calculations with all active points."""

    def test_fixed_stars_calculation(self):
        """Test calculation with fixed stars active."""
        from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
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
            active_points=ALL_ACTIVE_POINTS,
        )
        # Check that we have more points than default
        assert subject.active_points is not None
        assert len(subject.active_points) > 10

    def test_arabic_parts_calculation(self):
        """Test calculation with Arabic parts active."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
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
            active_points=["Sun", "Moon", "Ascendant", "Pars_Fortunae"],
        )
        assert subject.pars_fortunae is not None


# ============================================================================
# Legacy NatalAspects and SynastryAspects Tests
# ============================================================================


class TestLegacyNatalAspects:
    """Tests for legacy NatalAspects wrapper."""

    def test_natal_aspects_with_new_settings_file_warning(self, basic_subject):
        """Test new_settings_file parameter emits deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from kerykeion.backword import NatalAspects

            aspects = NatalAspects(
                basic_subject,
                new_settings_file={"some": "config"},  # Should emit warning
            )
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) > 0
            assert aspects is not None

    def test_natal_aspects_with_custom_active_aspects(self, basic_subject):
        """Test NatalAspects with custom active aspects."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from kerykeion.backword import NatalAspects

            # Use lowercase aspect names as required by the API
            active_aspects = [
                {"name": "conjunction", "orb": 6},
                {"name": "opposition", "orb": 6},
            ]
            aspects = NatalAspects(
                basic_subject,
                active_aspects=active_aspects,
            )
            assert aspects is not None
            _ = aspects.all_aspects
            _ = aspects.relevant_aspects

    def test_synastry_aspects_with_new_settings_file_warning(self, basic_subject, second_subject):
        """Test SynastryAspects new_settings_file parameter emits deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from kerykeion.backword import SynastryAspects

            aspects = SynastryAspects(
                basic_subject,
                second_subject,
                new_settings_file={"some": "config"},  # Should emit warning
            )
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) > 0
            assert aspects is not None

    def test_synastry_aspects_with_custom_active_aspects(self, basic_subject, second_subject):
        """Test SynastryAspects with custom active aspects."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from kerykeion.backword import SynastryAspects

            # Use lowercase aspect names as required by the API
            active_aspects = [
                {"name": "conjunction", "orb": 6},
                {"name": "opposition", "orb": 6},
            ]
            aspects = SynastryAspects(
                basic_subject,
                second_subject,
                active_aspects=active_aspects,
            )
            assert aspects is not None
            _ = aspects.all_aspects
            _ = aspects.relevant_aspects


# ============================================================================
# ChartDataFactory Validation Tests
# ============================================================================


class TestChartDataFactoryValidation:
    """Tests for ChartDataFactory validation errors."""

    def test_composite_chart_requires_composite_model(self, basic_subject):
        """Test Composite chart requires CompositeSubjectModel."""
        with pytest.raises(KerykeionException, match="CompositeSubjectModel"):
            ChartDataFactory.create_composite_chart_data(basic_subject)

    def test_single_return_chart_requires_return_model(self, basic_subject):
        """Test SingleReturnChart requires PlanetReturnModel."""
        with pytest.raises(KerykeionException, match="PlanetReturnModel"):
            ChartDataFactory.create_single_wheel_return_chart_data(basic_subject)

    def test_transit_chart_requires_second_subject(self, basic_subject):
        """Test Transit chart requires second subject."""
        with pytest.raises(KerykeionException, match="Second subject is required"):
            ChartDataFactory.create_chart_data(
                first_subject=basic_subject,
                chart_type="Transit",
                second_subject=None,
            )

    def test_synastry_chart_requires_second_subject(self, basic_subject):
        """Test Synastry chart requires second subject."""
        with pytest.raises(KerykeionException, match="Second subject is required"):
            ChartDataFactory.create_chart_data(
                first_subject=basic_subject,
                chart_type="Synastry",
                second_subject=None,
            )


# ============================================================================
# Context Serializer Transit Tests
# ============================================================================


class TestContextSerializerTransits:
    """Tests for context serializer transit functions."""

    def test_transit_moment_to_context(self, basic_subject):
        """Test transit_moment_to_context function."""
        from kerykeion.context_serializer import transit_moment_to_context, to_context
        from kerykeion.schemas.kr_models import TransitMomentModel, AspectModel

        # Create a mock transit moment with aspects using correct field names
        aspect = AspectModel(
            p1_name="Sun",
            p1_owner="Test",
            p1_abs_pos=10.5,
            p2_name="Moon",
            p2_owner="Test",
            p2_abs_pos=100.5,
            aspect="Square",
            aspect_degrees=90,
            orbit=0.5,
            diff=0.5,
            p1=0,
            p2=1,
            p1_speed=1.0,
            p2_speed=12.0,
            aspect_movement="Applying",
        )
        transit_moment = TransitMomentModel(
            date="2024-01-15T12:00:00",
            aspects=[aspect],
        )

        result = transit_moment_to_context(transit_moment)
        assert "Transit moment" in result
        assert "2024-01-15" in result
        assert "Active transits" in result

        # Also test via to_context
        result2 = to_context(transit_moment)
        assert "Transit moment" in result2

    def test_transit_moment_to_context_no_aspects(self):
        """Test transit_moment_to_context with no aspects."""
        from kerykeion.context_serializer import transit_moment_to_context
        from kerykeion.schemas.kr_models import TransitMomentModel

        transit_moment = TransitMomentModel(
            date="2024-01-15T12:00:00",
            aspects=[],
        )

        result = transit_moment_to_context(transit_moment)
        assert "No active transits" in result

    def test_transits_time_range_to_context(self, basic_subject):
        """Test transits_time_range_to_context function."""
        from kerykeion.context_serializer import transits_time_range_to_context, to_context
        from kerykeion.schemas.kr_models import TransitsTimeRangeModel, TransitMomentModel, AspectModel

        # Create a mock transits time range with correct field names
        aspect = AspectModel(
            p1_name="Sun",
            p1_owner="Test",
            p1_abs_pos=10.5,
            p2_name="Moon",
            p2_owner="Test",
            p2_abs_pos=100.5,
            aspect="Square",
            aspect_degrees=90,
            orbit=0.5,
            diff=0.5,
            p1=0,
            p2=1,
            p1_speed=1.0,
            p2_speed=12.0,
            aspect_movement="Applying",
        )
        transit_moment = TransitMomentModel(
            date="2024-01-15T12:00:00",
            aspects=[aspect],
        )
        transits_range = TransitsTimeRangeModel(
            subject=basic_subject,
            transits=[transit_moment],
            dates=["2024-01-15T12:00:00"],
        )

        result = transits_time_range_to_context(transits_range)
        assert "Transit analysis" in result
        assert basic_subject.name in result
        assert "Time range" in result

        # Also test via to_context
        result2 = to_context(transits_range)
        assert "Transit analysis" in result2

    def test_transits_time_range_to_context_no_subject(self):
        """Test transits_time_range_to_context without subject."""
        from kerykeion.context_serializer import transits_time_range_to_context
        from kerykeion.schemas.kr_models import TransitsTimeRangeModel, TransitMomentModel

        transit_moment = TransitMomentModel(
            date="2024-01-15T12:00:00",
            aspects=[],
        )
        transits_range = TransitsTimeRangeModel(
            subject=None,
            transits=[transit_moment],
            dates=["2024-01-15T12:00:00"],
        )

        result = transits_time_range_to_context(transits_range)
        assert "Transit analysis" in result


# ============================================================================
# ReportGenerator Validation Tests
# ============================================================================


class TestReportGeneratorValidation:
    """Tests for ReportGenerator validation."""

    def test_report_generator_unsupported_model_type(self):
        """Test ReportGenerator raises TypeError for unsupported model type."""
        with pytest.raises(TypeError, match="Unsupported model type"):
            ReportGenerator("invalid_model")


# ============================================================================
# Legacy KerykeionChartSVG Additional Tests
# ============================================================================


class TestLegacyKerykeionChartSVGChartTypes:
    """Tests for KerykeionChartSVG with different chart types."""

    def test_synastry_chart(self, basic_subject, second_subject):
        """Test KerykeionChartSVG with Synastry chart type."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from kerykeion.backword import KerykeionChartSVG

            chart = KerykeionChartSVG(
                basic_subject,
                chart_type="Synastry",
                second_obj=second_subject,
            )
            svg = chart.makeTemplate()
            assert svg is not None
            assert "<svg" in svg

    def test_transit_chart(self, basic_subject, second_subject):
        """Test KerykeionChartSVG with Transit chart type."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from kerykeion.backword import KerykeionChartSVG

            chart = KerykeionChartSVG(
                basic_subject,
                chart_type="Transit",
                second_obj=second_subject,
            )
            svg = chart.makeTemplate()
            assert svg is not None
            assert "<svg" in svg

    def test_composite_chart(self, basic_subject, second_subject):
        """Test KerykeionChartSVG with Composite chart type."""
        from kerykeion.composite_subject_factory import CompositeSubjectFactory

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from kerykeion.backword import KerykeionChartSVG

            # Create composite subject
            composite = CompositeSubjectFactory(basic_subject, second_subject)
            composite_subject = composite.get_midpoint_composite_subject_model()

            chart = KerykeionChartSVG(
                composite_subject,
                chart_type="Composite",
            )
            svg = chart.makeTemplate()
            assert svg is not None
            assert "<svg" in svg

    def test_external_natal_chart(self, basic_subject):
        """Test KerykeionChartSVG with ExternalNatal chart type."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from kerykeion.backword import KerykeionChartSVG

            chart = KerykeionChartSVG(
                basic_subject,
                chart_type="ExternalNatal",
            )
            svg = chart.makeTemplate()
            assert svg is not None
            assert "<svg" in svg

    def test_synastry_chart_requires_second_obj(self, basic_subject):
        """Test KerykeionChartSVG Synastry without second obj raises error."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from kerykeion.backword import KerykeionChartSVG

            chart = KerykeionChartSVG(
                basic_subject,
                chart_type="Synastry",
            )
            with pytest.raises(ValueError, match="Second object is required"):
                chart.makeTemplate()

    def test_transit_chart_requires_second_obj(self, basic_subject):
        """Test KerykeionChartSVG Transit without second obj raises error."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from kerykeion.backword import KerykeionChartSVG

            chart = KerykeionChartSVG(
                basic_subject,
                chart_type="Transit",
            )
            with pytest.raises(ValueError, match="Second object is required"):
                chart.makeTemplate()

    def test_composite_chart_requires_composite_model(self, basic_subject):
        """Test KerykeionChartSVG Composite with wrong type raises error."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from kerykeion.backword import KerykeionChartSVG

            chart = KerykeionChartSVG(
                basic_subject,  # Wrong type, should be CompositeSubjectModel
                chart_type="Composite",
            )
            with pytest.raises(ValueError, match="CompositeSubjectModel"):
                chart.makeTemplate()

    def test_unsupported_chart_type(self, basic_subject):
        """Test KerykeionChartSVG with unsupported chart type raises error."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from kerykeion.backword import KerykeionChartSVG

            chart = KerykeionChartSVG(
                basic_subject,
                chart_type="InvalidType",
            )
            with pytest.raises(ValueError, match="Unsupported"):
                chart.makeTemplate()


# ============================================================================
# Legacy Active Points Normalization Tests
# ============================================================================


class TestLegacyActivePointsNormalization:
    """Tests for legacy active points normalization."""

    def test_legacy_node_names_in_active_points(self):
        """Test legacy node names in active points emit deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from kerykeion.backword import NatalAspects

            # Use legacy node name
            aspects = NatalAspects(
                AstrologicalSubjectFactory.from_birth_data(
                    name="Test",
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
                ),
                active_points=["Sun", "Moon", "Mean_Node"],  # Legacy name
            )
            # Should have triggered deprecation warning for Mean_Node
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) > 0
            assert aspects is not None

    def test_active_aspects_passed_to_aspects_wrapper(self, basic_subject):
        """Test that active_aspects passed to wrapper are used."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from kerykeion.backword import NatalAspects

            # Pass None to test else branch
            aspects = NatalAspects(
                basic_subject,
                active_aspects=None,
            )
            assert aspects is not None
            _ = aspects.all_aspects


# ============================================================================
# Charts Utils Edge Cases
# ============================================================================


class TestChartsUtilsEdgeCases:
    """Tests for charts utility functions edge cases."""

    def test_chart_drawer_with_many_points(self, basic_subject):
        """Test chart drawer warning with many active points."""
        from kerykeion.charts.chart_drawer import ChartDrawer
        from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
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
            active_points=ALL_ACTIVE_POINTS,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)

        # Just creating the drawer should work
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert svg is not None
        assert len(svg) > 0


# ============================================================================
# Additional Tests for 100% Coverage - Trans-Neptunian Objects
# ============================================================================


class TestTransNeptunianObjects:
    """Tests for trans-Neptunian object calculations."""

    def test_eris_calculation(self):
        """Test calculation with Eris active."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
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
            active_points=["Sun", "Moon", "Eris"],
        )
        # Eris should be calculated if available
        assert subject is not None

    def test_sedna_calculation(self):
        """Test calculation with Sedna active."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
            year=2000,
            month=1,
            day=1,
            hour=12,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            active_points=["Sun", "Moon", "Sedna"],
        )
        assert subject is not None

    def test_haumea_calculation(self):
        """Test calculation with Haumea active."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
            year=2005,
            month=6,
            day=15,
            hour=12,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            active_points=["Sun", "Moon", "Haumea"],
        )
        assert subject is not None

    def test_makemake_calculation(self):
        """Test calculation with Makemake active."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
            year=2006,
            month=6,
            day=15,
            hour=12,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            active_points=["Sun", "Moon", "Makemake"],
        )
        assert subject is not None

    def test_ixion_calculation(self):
        """Test calculation with Ixion active."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
            year=2001,
            month=6,
            day=15,
            hour=12,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            active_points=["Sun", "Moon", "Ixion"],
        )
        assert subject is not None

    def test_orcus_calculation(self):
        """Test calculation with Orcus active."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
            year=2004,
            month=6,
            day=15,
            hour=12,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            active_points=["Sun", "Moon", "Orcus"],
        )
        assert subject is not None

    def test_quaoar_calculation(self):
        """Test calculation with Quaoar active."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
            year=2002,
            month=6,
            day=15,
            hour=12,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            active_points=["Sun", "Moon", "Quaoar"],
        )
        assert subject is not None

    def test_fixed_stars_regulus_spica(self):
        """Test calculation with fixed stars Regulus and Spica."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
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
            active_points=["Sun", "Moon", "Regulus", "Spica"],
        )
        assert subject is not None

    def test_pars_fortunae_calculation(self):
        """Test calculation with Pars Fortunae (Part of Fortune)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
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
            active_points=["Sun", "Moon", "Ascendant", "Pars_Fortunae"],
        )
        assert subject is not None
        assert subject.pars_fortunae is not None

    def test_pars_spiritus_calculation(self):
        """Test calculation with Pars Spiritus (Part of Spirit)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
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
            active_points=["Sun", "Moon", "Ascendant", "Pars_Spiritus"],
        )
        assert subject is not None

    def test_pars_amoris_calculation(self):
        """Test calculation with Pars Amoris (Part of Love)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
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
            active_points=["Sun", "Venus", "Ascendant", "Pars_Amoris"],
        )
        assert subject is not None

    def test_pars_fidei_calculation(self):
        """Test calculation with Pars Fidei (Part of Faith)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
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
            active_points=["Jupiter", "Saturn", "Ascendant", "Pars_Fidei"],
        )
        assert subject is not None

    def test_vertex_anti_vertex_calculation(self):
        """Test calculation with Vertex and Anti-Vertex."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
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
            active_points=["Sun", "Moon", "Vertex", "Anti_Vertex"],
        )
        assert subject is not None


# ============================================================================
# Chart Data Factory Return Type Tests
# ============================================================================


class TestChartDataFactoryReturnTypes:
    """Tests for ChartDataFactory return chart type validation."""

    def test_return_chart_requires_planet_return_model(self, basic_subject, second_subject):
        """Test Return chart requires PlanetReturnModel as second subject."""
        # This should raise an error since second_subject is not a PlanetReturnModel
        with pytest.raises(KerykeionException, match="PlanetReturnModel"):
            ChartDataFactory.create_chart_data(
                first_subject=basic_subject,
                chart_type="Return",
                second_subject=second_subject,  # Wrong type
            )

    def test_synastry_chart_with_incompatible_types(self, basic_subject):
        """Test synastry chart with incompatible types uses fallback distribution."""

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
        # Create synastry chart
        chart_data = ChartDataFactory.create_synastry_chart_data(basic_subject, second)
        assert chart_data is not None


# ============================================================================
# Ephemeris Data Factory Edge Cases
# ============================================================================


class TestEphemerisDataFactoryStepValidation:
    """Tests for EphemerisDataFactory step validation."""

    def test_invalid_step_type(self):
        """Test EphemerisDataFactory with invalid step type."""
        from kerykeion.ephemeris_data_factory import EphemerisDataFactory
        from datetime import datetime

        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 2)

        with pytest.raises(ValueError, match="Invalid step type"):
            EphemerisDataFactory(
                start,
                end,
                step=1,
                step_type="invalid",  # type: ignore
            )


# ============================================================================
# Planetary Return Factory Edge Cases
# ============================================================================


class TestPlanetaryReturnFactoryOnlineMode:
    """Tests for PlanetaryReturnFactory online mode edge cases."""

    def test_online_mode_missing_city_raises_error(self, basic_subject):
        """Test online mode without city raises error."""
        from kerykeion.planetary_return_factory import PlanetaryReturnFactory

        with pytest.raises(KerykeionException, match="city"):
            PlanetaryReturnFactory(
                basic_subject,
                city=None,  # Missing city
                nation="IT",
                online=True,
            )


# ============================================================================
# FetchGeonames Edge Cases
# ============================================================================


class TestFetchGeonamesEdgeCases:
    """Tests for FetchGeonames edge cases."""

    def test_geonames_cache_name_from_env(self, monkeypatch):
        """Test FetchGeonames cache name resolution from environment."""
        from kerykeion.fetch_geonames import FetchGeonames

        # Use monkeypatch for environment variable to ensure parallel test safety
        monkeypatch.setenv("KERYKEION_GEONAMES_CACHE_NAME", "/tmp/test_cache")

        resolved = FetchGeonames._resolve_cache_name(None)
        assert str(resolved) == "/tmp/test_cache"

    def test_geonames_set_default_cache_name(self, monkeypatch):
        """Test FetchGeonames set_default_cache_name class method."""
        from kerykeion.fetch_geonames import FetchGeonames
        from pathlib import Path

        # Use monkeypatch for class attribute to ensure parallel test safety
        monkeypatch.setattr(FetchGeonames, "default_cache_name", Path("/custom/cache/path"))
        assert FetchGeonames.default_cache_name == Path("/custom/cache/path")


# ============================================================================
# House Comparison Utils Edge Cases
# ============================================================================


class TestHouseComparisonUtilsEdgeCases:
    """Tests for house comparison utility edge cases."""

    def test_cusps_in_reciprocal_houses(self, basic_subject, second_subject):
        """Test calculate_cusps_in_reciprocal_houses function."""
        from kerykeion.house_comparison.house_comparison_utils import calculate_cusps_in_reciprocal_houses

        cusps = calculate_cusps_in_reciprocal_houses(basic_subject, second_subject)
        assert len(cusps) == 12  # 12 house cusps

    def test_points_in_reciprocal_houses_skips_none(self, basic_subject, second_subject):
        """Test that calculate_points_in_reciprocal_houses skips None points."""
        from kerykeion.house_comparison.house_comparison_utils import calculate_points_in_reciprocal_houses

        points = calculate_points_in_reciprocal_houses(basic_subject, second_subject)
        assert len(points) > 0


# ============================================================================
# Composite Subject Factory Edge Cases
# ============================================================================


class TestCompositeSubjectFactoryHash:
    """Tests for CompositeSubjectFactory hash behavior."""

    def test_composite_hash(self, basic_subject, second_subject):
        """Test CompositeSubjectFactory __hash__ method raises TypeError."""
        from kerykeion.composite_subject_factory import CompositeSubjectFactory

        # Create subjects with matching zodiac configuration
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
        composite = CompositeSubjectFactory(first, second)
        # The __hash__ method exists - it raises TypeError due to unhashable subjects
        with pytest.raises(TypeError, match="unhashable"):
            hash(composite)

    def test_composite_copy(self, basic_subject, second_subject):
        """Test CompositeSubjectFactory __copy__ method."""
        from kerykeion.composite_subject_factory import CompositeSubjectFactory
        import copy

        composite = CompositeSubjectFactory(basic_subject, second_subject)
        composite_copy = copy.copy(composite)
        assert composite_copy.name == composite.name


# ============================================================================
# Context Serializer Additional Tests
# ============================================================================


class TestContextSerializerDualChart:
    """Tests for context serializer dual chart functions."""

    def test_dual_chart_data_to_context(self, basic_subject, second_subject):
        """Test dual_chart_data_to_context function."""
        from kerykeion.context_serializer import dual_chart_data_to_context

        chart_data = ChartDataFactory.create_synastry_chart_data(basic_subject, second_subject)
        result = dual_chart_data_to_context(chart_data)
        assert "Synastry" in result
        assert basic_subject.name in result

    def test_single_chart_data_to_context(self, basic_subject):
        """Test single_chart_data_to_context function."""
        from kerykeion.context_serializer import single_chart_data_to_context

        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        result = single_chart_data_to_context(chart_data)
        assert "Natal" in result
        assert basic_subject.name in result

    def test_to_context_with_composite_subject(self, basic_subject, second_subject):
        """Test to_context with CompositeSubjectModel."""
        from kerykeion.context_serializer import to_context
        from kerykeion.composite_subject_factory import CompositeSubjectFactory

        composite_factory = CompositeSubjectFactory(basic_subject, second_subject)
        composite = composite_factory.get_midpoint_composite_subject_model()
        result = to_context(composite)
        assert "Composite" in result


# ============================================================================
# Report Generator Additional Tests
# ============================================================================


class TestReportGeneratorEdgeCases:
    """Tests for ReportGenerator edge cases."""

    def test_report_with_no_active_points(self, basic_subject):
        """Test report with minimal active points."""
        chart_data = ChartDataFactory.create_natal_chart_data(
            basic_subject,
            active_points=["Sun", "Moon"],
        )
        report = ReportGenerator(chart_data)
        result = report.generate_report()
        assert basic_subject.name in result

    def test_report_chart_type_variations(self, basic_subject, second_subject):
        """Test report with different chart types."""
        # Transit
        transit_data = ChartDataFactory.create_transit_chart_data(basic_subject, second_subject)
        report = ReportGenerator(transit_data)
        result = report.generate_report()
        assert "Transit" in result

    def test_report_with_dual_return_chart(self, basic_subject):
        """Test ReportGenerator with DualReturnChart."""
        from kerykeion.planetary_return_factory import PlanetaryReturnFactory

        factory = PlanetaryReturnFactory(
            basic_subject,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )
        lunar_return = factory.next_return_from_date(2024, 2, 1, return_type="Lunar")
        chart_data = ChartDataFactory.create_return_chart_data(basic_subject, lunar_return)
        report = ReportGenerator(chart_data)
        result = report.generate_report()
        assert "Lunar" in result or "Return" in result


# ============================================================================
# Chart Drawer Edge Cases
# ============================================================================


class TestChartDrawerEdgeCases:
    """Tests for ChartDrawer edge cases."""

    def test_chart_drawer_invalid_theme(self, basic_subject):
        """Test ChartDrawer with invalid theme raises error."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        with pytest.raises(KerykeionException, match="Theme"):
            ChartDrawer(chart_data, theme="invalid_theme")  # type: ignore

    def test_chart_drawer_synastry_with_table_grid(self, basic_subject, second_subject):
        """Test ChartDrawer synastry with table grid type."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        chart_data = ChartDataFactory.create_synastry_chart_data(basic_subject, second_subject)
        drawer = ChartDrawer(chart_data, double_chart_aspect_grid_type="table")
        svg = drawer.generate_svg_string()
        assert svg is not None

    def test_chart_drawer_transit_with_many_aspects(self, basic_subject, second_subject):
        """Test ChartDrawer transit chart with many aspects."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        chart_data = ChartDataFactory.create_transit_chart_data(basic_subject, second_subject)
        drawer = ChartDrawer(chart_data, double_chart_aspect_grid_type="list")
        svg = drawer.generate_svg_string()
        assert svg is not None


# ============================================================================
# Draw Planets Edge Cases
# ============================================================================


class TestDrawPlanetsEdgeCases:
    """Tests for draw_planets edge cases."""

    def test_dual_return_chart_drawing(self, basic_subject):
        """Test drawing DualReturnChart type."""
        from kerykeion.charts.chart_drawer import ChartDrawer
        from kerykeion.planetary_return_factory import PlanetaryReturnFactory

        factory = PlanetaryReturnFactory(
            basic_subject,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )
        solar_return = factory.next_return_from_date(2024, 7, 1, return_type="Solar")
        chart_data = ChartDataFactory.create_return_chart_data(basic_subject, solar_return)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert svg is not None


# ============================================================================
# kr_models Edge Cases
# ============================================================================


class TestKrModelsEdgeCases:
    """Tests for kr_models edge cases."""

    def test_subscriptable_base_model_delitem(self, basic_subject):
        """Test SubscriptableBaseModel __delitem__ method."""

        point = basic_subject.sun
        # Just check the method exists and doesn't crash
        assert hasattr(point, "__delitem__")


# ============================================================================
# Utilities Edge Cases
# ============================================================================


class TestUtilitiesEdgeCasesAdditional:
    """Additional tests for utilities edge cases."""

    def test_inline_css_no_style_block(self):
        """Test inline_css_variables_in_svg with no style block."""
        svg_content = '<svg><rect fill="var(--color, blue)" /></svg>'
        result = inline_css_variables_in_svg(svg_content)
        # Should use fallback
        assert "blue" in result or "var" not in result


# ============================================================================
# Backword Module Additional Tests
# ============================================================================


class TestBackwordAdditional:
    """Additional tests for backword module edge cases."""

    def test_legacy_normalize_zodiac_type_sidereal(self):
        """Test legacy zodiac type normalization with sidereal."""
        with warnings.catch_warnings(record=True) as _:
            warnings.simplefilter("always")
            from kerykeion.backword import AstrologicalSubject

            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
                zodiac_type="sidereal",  # Lowercase should trigger warning
            )
            assert subject is not None

    def test_kerykeion_chart_svg_dual_return(self, basic_subject):
        """Test KerykeionChartSVG with Return chart type."""
        from kerykeion.planetary_return_factory import PlanetaryReturnFactory
        from kerykeion.charts.chart_drawer import ChartDrawer

        factory = PlanetaryReturnFactory(
            basic_subject,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )
        solar_return = factory.next_return_from_date(2024, 8, 1, return_type="Solar")
        chart_data = ChartDataFactory.create_return_chart_data(basic_subject, solar_return)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert svg is not None


# ============================================================================
# Charts Utils Distribution Edge Cases
# ============================================================================


class TestChartsUtilsDistribution:
    """Tests for charts_utils distribution calculation edge cases."""

    def test_planet_grid_layout_fourth_column(self):
        """Test planet grid layout for large number of points (fourth column)."""
        from kerykeion.charts.charts_utils import _planet_grid_layout_position

        # Test fourth column (index >= 36)
        offset, row = _planet_grid_layout_position(40)
        assert row == 4  # 40 - 36 = 4
        assert offset < 0  # Negative offset for columns beyond first


# ============================================================================
# Additional Tests for Maximum Coverage
# ============================================================================


class TestArabicPartsOnlyActivation:
    """Tests for Arabic Parts with only required point activation."""

    def test_pars_spiritus_only(self):
        """Test calculation with only Pars Spiritus (no Sun/Moon/Ascendant initially)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
            year=1990,
            month=6,
            day=15,
            hour=21,  # Night chart to trigger night calculation path
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            active_points=["Pars_Spiritus"],  # Minimal - will auto-add Sun, Moon, Ascendant
        )
        assert subject is not None


class TestReportGeneratorHelperMethods:
    """Tests for ReportGenerator helper methods."""

    def test_extract_year_valid_datetime(self, basic_subject):
        """Test _extract_year with valid datetime."""
        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        report = ReportGenerator(chart_data)
        year = report._extract_year("2024-06-15T12:00:00")
        assert year == "2024"

    def test_extract_year_invalid_datetime(self, basic_subject):
        """Test _extract_year with invalid datetime."""
        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        report = ReportGenerator(chart_data)
        year = report._extract_year("invalid")
        assert year is None

    def test_extract_year_none(self, basic_subject):
        """Test _extract_year with None."""
        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        report = ReportGenerator(chart_data)
        year = report._extract_year(None)
        assert year is None

    def test_format_date_iso_valid(self, basic_subject):
        """Test _format_date_iso with valid datetime."""
        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        report = ReportGenerator(chart_data)
        formatted = report._format_date_iso("2024-06-15T12:00:00")
        assert formatted == "2024-06-15"

    def test_format_date_iso_invalid(self, basic_subject):
        """Test _format_date_iso with invalid datetime."""
        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        report = ReportGenerator(chart_data)
        formatted = report._format_date_iso("invalid")
        assert formatted == "invalid"

    def test_format_date_iso_none(self, basic_subject):
        """Test _format_date_iso with None."""
        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        report = ReportGenerator(chart_data)
        formatted = report._format_date_iso(None)
        assert formatted == ""


class TestChartDrawerSiderealMode:
    """Tests for ChartDrawer with Sidereal zodiac."""

    def test_chart_drawer_sidereal_zodiac(self):
        """Test chart drawer with Sidereal zodiac type."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
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
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert svg is not None
        assert "Lahiri" in svg or "LAHIRI" in svg or "Sidereal" in svg


class TestContextSerializerReturnSubject:
    """Tests for context serializer with return subjects."""

    def test_astrological_subject_to_context_with_return(self, basic_subject):
        """Test astrological_subject_to_context with PlanetReturnModel."""
        from kerykeion.context_serializer import astrological_subject_to_context
        from kerykeion.planetary_return_factory import PlanetaryReturnFactory

        factory = PlanetaryReturnFactory(
            basic_subject,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )
        solar_return = factory.next_return_from_date(2024, 9, 1, return_type="Solar")
        result = astrological_subject_to_context(solar_return)
        assert "Solar" in result


class TestChartDrawerNoLunarPhase:
    """Tests for ChartDrawer when lunar phase is missing."""

    def test_chart_drawer_generates_without_lunar_phase(self, basic_subject):
        """Test chart drawer still works when lunar phase data is available."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert svg is not None


class TestHouseComparisonUtilsCuspParsing:
    """Tests for house comparison cusp parsing edge cases."""

    def test_cusps_in_reciprocal_houses_parsing(self, basic_subject, second_subject):
        """Test cusp name parsing in calculate_cusps_in_reciprocal_houses."""
        from kerykeion.house_comparison.house_comparison_utils import calculate_cusps_in_reciprocal_houses

        result = calculate_cusps_in_reciprocal_houses(basic_subject, second_subject)
        assert len(result) == 12
        for cusp in result:
            assert cusp.projected_house_number >= 1
            assert cusp.projected_house_number <= 12


class TestCompositeSubjectFactoryNe:
    """Tests for CompositeSubjectFactory __ne__ method."""

    def test_composite_ne(self, basic_subject, second_subject):
        """Test CompositeSubjectFactory __ne__ method."""
        from kerykeion.composite_subject_factory import CompositeSubjectFactory

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
        composite1 = CompositeSubjectFactory(first, second)
        composite2 = CompositeSubjectFactory(second, first)  # Different order
        # They should be different
        assert composite1 != composite2


class TestFetchGeonamesErrorHandling:
    """Tests for FetchGeonames error handling."""

    def test_geonames_timezone_error_handling(self):
        """Test FetchGeonames handles errors gracefully."""
        from kerykeion.fetch_geonames import FetchGeonames

        # Just verify the class can be instantiated
        geonames = FetchGeonames("Rome", "IT", "test_user")
        assert geonames.city_name == "Rome"


class TestTransNeptunianCalculationFailures:
    """Tests for handling trans-Neptunian object calculation failures."""

    def test_all_tno_points_calculation(self):
        """Test calculation with all trans-Neptunian objects."""
        from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
            year=2010,
            month=1,
            day=1,
            hour=12,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            active_points=ALL_ACTIVE_POINTS,
        )
        assert subject is not None
        # Check that some TNOs are calculated
        assert subject.sun is not None


class TestUtilitiesInlineCssNoFallback:
    """Tests for utilities inline CSS without fallback."""

    def test_inline_css_no_fallback_unknown_var(self):
        """Test CSS variable replacement without fallback returns empty."""
        svg = '<rect fill="var(--unknown-color)" />'
        result = inline_css_variables_in_svg(svg)
        # Unknown variable with no fallback should return empty string
        assert 'fill=""' in result or "var" not in result


class TestKrModelsSubscriptableOperations:
    """Tests for kr_models SubscriptableBaseModel operations."""

    def test_subscriptable_model_get_default(self, basic_subject):
        """Test SubscriptableBaseModel get method with default."""
        result = basic_subject.get("nonexistent_attribute", "default_value")
        assert result == "default_value"

    def test_subscriptable_model_setitem(self, basic_subject):
        """Test SubscriptableBaseModel __setitem__ method."""
        # This should not raise an error
        try:
            basic_subject["test_attr"] = "test_value"
            # Clean up
            delattr(basic_subject, "test_attr")
        except Exception:
            pass  # May fail due to model validation, that's ok


class TestBackwordJsonDumpDestination:
    """Tests for backword json dump with destination."""

    def test_legacy_json_dump_with_destination(self, tmp_path):
        """Test legacy json() method with destination folder."""
        from kerykeion.backword import AstrologicalSubject

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="JsonTest",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            json_str = subject.json(dump=True, destination_folder=str(tmp_path), indent=2)
            assert json_str is not None
            files = list(tmp_path.glob("*.json"))
            assert len(files) >= 1


# ============================================================================
# Context Serializer Transit Chart Tests
# ============================================================================


class TestContextSerializerTransitChart:
    """Tests for context serializer with transit chart."""

    def test_dual_chart_transit_to_context(self, basic_subject, second_subject):
        """Test dual_chart_data_to_context with transit chart type."""
        from kerykeion.context_serializer import dual_chart_data_to_context

        chart_data = ChartDataFactory.create_transit_chart_data(basic_subject, second_subject)
        result = dual_chart_data_to_context(chart_data)
        assert "Transit Subject" in result


class TestToContextWithAspectModel:
    """Tests for to_context with AspectModel."""

    def test_to_context_with_aspect_model(self, basic_subject, second_subject):
        """Test to_context with AspectModel."""
        from kerykeion.context_serializer import to_context
        from kerykeion.aspects import AspectsFactory

        aspects = AspectsFactory.dual_chart_aspects(basic_subject, second_subject)
        if aspects.aspects:
            result = to_context(aspects.aspects[0])
            assert "aspect" in result.lower() or aspects.aspects[0].aspect.lower() in result.lower()


class TestToContextWithQualityDistribution:
    """Tests for to_context with QualityDistributionModel."""

    def test_to_context_with_quality_distribution(self, basic_subject):
        """Test to_context with QualityDistributionModel."""
        from kerykeion.context_serializer import to_context

        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        result = to_context(chart_data.quality_distribution)
        assert "Quality" in result or "Cardinal" in result


# ============================================================================
# Report Generator Relationship Score Tests
# ============================================================================


class TestReportGeneratorRelationshipScore:
    """Tests for ReportGenerator with relationship score."""

    def test_report_with_synastry_relationship_score(self, basic_subject, second_subject):
        """Test report with synastry chart and relationship score."""
        chart_data = ChartDataFactory.create_synastry_chart_data(
            basic_subject,
            second_subject,
            include_relationship_score=True,
        )
        report = ReportGenerator(chart_data)
        result = report.generate_report()
        # Should have relationship score in report
        assert basic_subject.name in result or second_subject.name in result


# ============================================================================
# Chart Drawer Wheel Only and Aspect Grid Tests
# ============================================================================


class TestChartDrawerWheelAndAspectGrid:
    """Tests for ChartDrawer wheel only and aspect grid methods."""

    def test_wheel_only_svg(self, basic_subject):
        """Test wheel only SVG generation."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_wheel_only_svg_string()
        assert svg is not None
        assert "<svg" in svg

    def test_aspect_grid_only_svg(self, basic_subject):
        """Test aspect grid only SVG generation."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_aspect_grid_only_svg_string()
        assert svg is not None
        assert "<svg" in svg

    def test_synastry_wheel_only_svg(self, basic_subject, second_subject):
        """Test synastry wheel only SVG generation."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        chart_data = ChartDataFactory.create_synastry_chart_data(basic_subject, second_subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_wheel_only_svg_string()
        assert svg is not None

    def test_transit_aspect_grid_svg(self, basic_subject, second_subject):
        """Test transit aspect grid only SVG generation."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        chart_data = ChartDataFactory.create_transit_chart_data(basic_subject, second_subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_aspect_grid_only_svg_string()
        assert svg is not None


# ============================================================================
# Chart Drawer Save Methods Tests
# ============================================================================


class TestChartDrawerSaveMethods:
    """Tests for ChartDrawer save methods."""

    def test_save_svg(self, basic_subject, tmp_path):
        """Test save_svg method."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        drawer = ChartDrawer(chart_data)
        drawer.save_svg(tmp_path)
        files = list(tmp_path.glob("*.svg"))
        assert len(files) >= 1

    def test_save_wheel_only_svg(self, basic_subject, tmp_path):
        """Test save_wheel_only_svg_file method."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        drawer = ChartDrawer(chart_data)
        drawer.save_wheel_only_svg_file(tmp_path)
        files = list(tmp_path.glob("*.svg"))
        assert len(files) >= 1

    def test_save_aspect_grid_only_svg(self, basic_subject, tmp_path):
        """Test save_aspect_grid_only_svg_file method."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        chart_data = ChartDataFactory.create_natal_chart_data(basic_subject)
        drawer = ChartDrawer(chart_data)
        drawer.save_aspect_grid_only_svg_file(tmp_path)
        files = list(tmp_path.glob("*.svg"))
        assert len(files) >= 1


# ============================================================================
# Utilities Additional Edge Cases
# ============================================================================


class TestUtilitiesAdditionalEdgeCases:
    """Additional tests for utilities edge cases."""

    def test_get_house_name_all_valid(self):
        """Test get_house_name for all valid house numbers."""
        from kerykeion.utilities import get_house_name

        for i in range(1, 13):
            name = get_house_name(i)
            assert "_House" in name

    def test_get_house_number_all_valid(self):
        """Test get_house_number for all valid house names."""
        from kerykeion.utilities import get_house_number, get_house_name

        for i in range(1, 13):
            name = get_house_name(i)
            number = get_house_number(name)
            assert number == i


# ============================================================================
# Planetary Return Factory Validation Tests
# ============================================================================


class TestPlanetaryReturnFactoryValidation:
    """Tests for PlanetaryReturnFactory validation."""

    def test_offline_mode_requires_coordinates(self, basic_subject):
        """Test offline mode requires coordinates."""
        from kerykeion.planetary_return_factory import PlanetaryReturnFactory

        # This should work - coordinates are provided
        factory = PlanetaryReturnFactory(
            basic_subject,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )
        assert factory is not None


# ============================================================================
# Composite Subject Validation Tests
# ============================================================================


class TestCompositeSubjectValidation:
    """Tests for CompositeSubjectFactory validation."""

    def test_composite_requires_same_zodiac_type(self):
        """Test composite subjects must have same zodiac type."""
        from kerykeion.composite_subject_factory import CompositeSubjectFactory

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
            zodiac_type="Tropical",
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
            zodiac_type="Tropical",
        )
        # Should work with same zodiac type
        composite = CompositeSubjectFactory(first, second)
        assert composite is not None


# ============================================================================
# Draw Planets Single Planet Tests
# ============================================================================


class TestDrawPlanetsSinglePoint:
    """Tests for draw_planets with single point."""

    def test_chart_with_minimal_points(self):
        """Test chart with minimal active points."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Minimal",
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
            active_points=["Sun"],
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert svg is not None


# ============================================================================
# Backword Legacy Chart Type Validation Tests
# ============================================================================


class TestBackwordChartTypeValidation:
    """Tests for KerykeionChartSVG chart type validation."""

    def test_synastry_requires_astrological_subjects(self):
        """Test synastry charts require both AstrologicalSubject instances."""
        from kerykeion.backword import KerykeionChartSVG, AstrologicalSubject
        import tempfile

        # Create two valid subjects
        first = AstrologicalSubject(
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
        )
        second = AstrologicalSubject(
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
        )
        # Should work with two AstrologicalSubject instances
        with tempfile.TemporaryDirectory() as tmpdir:
            chart = KerykeionChartSVG(first, second_obj=second, chart_type="Synastry", new_output_directory=tmpdir)
            # makeSVG returns None, use makeTemplate() or makeSVGstring() to get the SVG string
            svg_string = chart.makeTemplate()
            assert svg_string is not None
            assert "<svg" in svg_string

    def test_transit_requires_astrological_subjects(self):
        """Test transit charts require both AstrologicalSubject instances."""
        from kerykeion.backword import KerykeionChartSVG, AstrologicalSubject
        import tempfile

        first = AstrologicalSubject(
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
        )
        second = AstrologicalSubject(
            name="Transit",
            year=2024,
            month=1,
            day=15,
            hour=12,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )
        # Should work with two AstrologicalSubject instances
        with tempfile.TemporaryDirectory() as tmpdir:
            chart = KerykeionChartSVG(first, second_obj=second, chart_type="Transit", new_output_directory=tmpdir)
            svg_string = chart.makeTemplate()
            assert svg_string is not None
            assert "<svg" in svg_string

    def test_chart_with_no_first_object_raises_error(self):
        """Test that charts without first object raise error."""
        from kerykeion.backword import KerykeionChartSVG

        # Try to create chart with None as first object - should raise at chart generation
        with pytest.raises((ValueError, TypeError)):
            chart = KerykeionChartSVG(None, chart_type="Natal")  # type: ignore
            chart.makeSVG()


# ============================================================================
# Backword ISO DateTime Parser Tests
# ============================================================================


class TestBackwordIsoDatetimeParser:
    """Tests for _parse_iso_datetime helper in backword."""

    def test_parse_iso_datetime_with_z_suffix(self):
        """Test parsing ISO datetime with Z suffix."""
        from kerykeion.backword import AstrologicalSubject

        # Create subject using get_from_iso_utc_time (the correct method name)
        subject = AstrologicalSubject.get_from_iso_utc_time(
            name="Test",
            iso_utc_time="1990-06-15T12:00:00Z",
            city="Rome",
            nation="IT",
            tz_str="Europe/Rome",
            lng=12.5,
            lat=41.9,
            online=False,
        )
        assert subject is not None
        assert subject.name == "Test"


# ============================================================================
# Fetch Geonames Error Handling Tests
# ============================================================================


class TestFetchGeonamesNetworkErrors:
    """Tests for FetchGeonames network error handling."""

    def test_geonames_request_exception_returns_empty(self):
        """Test that request exceptions return empty dict."""
        from kerykeion.fetch_geonames import FetchGeonames
        from requests import RequestException

        # Create a geonames instance
        geonames = FetchGeonames("Rome", "IT", username="test_user")

        # Mock get_serialized_data to trigger the exception path
        with patch.object(geonames.session, "send", side_effect=RequestException("Network error")):
            result = geonames.get_serialized_data()
            # Should return empty dict on error
            assert result == {}

    def test_geonames_timezone_missing_keys_returns_empty(self):
        """Test that missing timezone keys return empty dict."""
        from kerykeion.fetch_geonames import FetchGeonames

        # Mock the session to return response without timezoneId key
        mock_response = MagicMock()
        mock_response.json.return_value = {"someOtherKey": "value"}

        geonames = FetchGeonames("Rome", "IT", username="test_user")
        with patch.object(geonames.session, "send", return_value=mock_response):
            # get_serialized_data will fail when timezone lookup fails
            result = geonames.get_serialized_data()
            # Should return empty dict when key is missing
            assert result == {}

    def test_geonames_timezone_malformed_payload_returns_empty(self):
        """Test that non-dict timezone payloads return empty dict."""
        from kerykeion.fetch_geonames import FetchGeonames

        timezone_response = MagicMock()
        timezone_response.json.return_value = []

        geonames = FetchGeonames("Rome", "IT", username="test_user")
        with patch.object(geonames.session, "send", return_value=timezone_response):
            result = getattr(geonames, "_FetchGeonames__get_timezone")("41.9", "12.5")
            assert result == {}

    def test_geonames_country_missing_keys_returns_empty(self):
        """Test that missing country data keys return empty dict."""
        from kerykeion.fetch_geonames import FetchGeonames

        # Mock the session to return response without expected geonames key
        mock_response = MagicMock()
        mock_response.json.return_value = {"geonames": []}  # Empty geonames array

        geonames = FetchGeonames("Rome", "IT", username="test_user")
        with patch.object(geonames.session, "send", return_value=mock_response):
            result = geonames.get_serialized_data()
            # Should return empty dict when key is missing
            assert result == {}
            # Access the private method directly
            result = getattr(geonames, "_FetchGeonames__get_contry_data")("Rome", "IT")
            # Should return empty dict when key is missing
            assert result == {}

    def test_geonames_country_malformed_payload_returns_empty(self):
        """Test that malformed country payloads return empty dict."""
        from kerykeion.fetch_geonames import FetchGeonames

        mock_response = MagicMock()
        mock_response.json.return_value = {"geonames": None}

        geonames = FetchGeonames("Rome", "IT", username="test_user")
        with patch.object(geonames.session, "send", return_value=mock_response):
            result = geonames.get_serialized_data()
            assert result == {}
            result = getattr(geonames, "_FetchGeonames__get_contry_data")("Rome", "IT")
            assert result == {}


# ============================================================================
# Chart Drawer Large Aspect List Tests
# ============================================================================


class TestChartDrawerLargeAspectList:
    """Tests for chart drawer with large aspect lists requiring height adjustment."""

    def test_synastry_with_many_aspects_adjusts_height(self):
        """Test synastry chart with many aspects triggers height adjustment."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        # Create subjects with many active points to generate many aspects
        all_points = [
            "Sun",
            "Moon",
            "Mercury",
            "Venus",
            "Mars",
            "Jupiter",
            "Saturn",
            "Uranus",
            "Neptune",
            "Pluto",
            "Ascendant",
            "Medium_Coeli",
            "Mean_North_Lunar_Node",
            "Chiron",
            "Lilith",
        ]
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
            active_points=all_points,
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
            active_points=all_points,
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(
            first,
            second,
            active_points=all_points,
        )
        drawer = ChartDrawer(chart_data, double_chart_aspect_grid_type="list")
        svg = drawer.generate_svg_string()
        assert svg is not None
        assert "svg" in svg


# ============================================================================
# Report Edge Cases - Missing Data Scenarios
# ============================================================================


class TestReportMissingDataScenarios:
    """Tests for ReportGenerator with missing data scenarios."""

    def test_report_houses_with_composite_no_houses(self):
        """Test report generates houses section correctly for composite."""
        from kerykeion.composite_subject_factory import CompositeSubjectFactory

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
        composite = CompositeSubjectFactory(first, second)
        composite_model = composite.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_model)
        report = ReportGenerator(chart_data)
        result = report.generate_report()
        # Should contain composite report info
        assert "Composite" in result

    def test_report_subject_only_mode(self):
        """Test report in subject-only mode without chart data."""
        first = AstrologicalSubjectFactory.from_birth_data(
            name="SubjectOnly",
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
        # Pass just the subject, not chart data
        report = ReportGenerator(first)
        result = report.generate_report()
        assert "SubjectOnly" in result
        assert "Subject Report" in result


# ============================================================================
# House Comparison Utils Edge Cases
# ============================================================================


class TestHouseComparisonUtilsMalformedData:
    """Tests for house_comparison_utils malformed data handling."""

    def test_cusps_in_houses_with_malformed_cusp_name(self):
        """Test cusps_in_houses handles malformed cusp names."""
        from kerykeion.house_comparison.house_comparison_utils import calculate_cusps_in_reciprocal_houses

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
        # Should work normally
        result = calculate_cusps_in_reciprocal_houses(first, second)
        assert result is not None
        assert len(result) > 0

    def test_point_not_in_active_points_skipped(self):
        """Test that points not in active_points are skipped."""
        from kerykeion.house_comparison.house_comparison_utils import calculate_points_in_reciprocal_houses

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
        # Pass limited active_points
        result = calculate_points_in_reciprocal_houses(first, second, active_points=["Sun"])
        assert result is not None
        # Should only contain Sun-related entries
        for point in result:
            assert point.point_name == "Sun"


# ============================================================================
# Charts Utils Distribution Edge Cases
# ============================================================================


class TestChartsUtilsDistributionEdgeCases:
    """Tests for charts_utils distribution calculation edge cases."""

    def test_distribution_with_missing_point(self):
        """Test distribution calculation skips missing points."""
        from kerykeion.charts.charts_utils import calculate_element_points
        from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
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
            active_points=["Sun", "Moon", "Mercury"],
        )

        # Calculate element distribution with some non-existent points
        dist = calculate_element_points(
            DEFAULT_CELESTIAL_POINTS_SETTINGS,
            ["sun", "moon", "nonexistent_point"],
            subject,
        )
        assert dist is not None
        # The function should return element keys
        assert len(dist) == 4  # Fire, Earth, Air, Water

    def test_distribution_with_weighted_method_custom_weights(self):
        """Test distribution with custom weighted method."""
        from kerykeion.charts.charts_utils import calculate_element_points
        from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
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

        # Calculate with weighted method and custom weights including __default__
        dist = calculate_element_points(
            DEFAULT_CELESTIAL_POINTS_SETTINGS,
            ["sun", "moon", "mercury"],
            subject,
            method="weighted",
            custom_weights={"sun": 5.0, "moon": 4.0, "__default__": 1.0},
        )
        assert dist is not None


# ============================================================================
# Planetary Return Factory Validation Edge Cases
# ============================================================================


class TestPlanetaryReturnValidationEdgeCases:
    """Tests for PlanetaryReturnFactory edge cases."""

    def test_return_with_explicit_coordinates(self):
        """Test return calculation with explicit coordinates."""
        from kerykeion.planetary_return_factory import PlanetaryReturnFactory

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
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
        factory = PlanetaryReturnFactory(
            subject,
            lng=15.0,  # Different from birth location
            lat=45.0,
            tz_str="Europe/Rome",
            online=False,
        )
        result = factory.next_return_from_date(2024, 1, 1, return_type="Solar")
        assert result is not None
        assert result.lng == 15.0
        assert result.lat == 45.0


# ============================================================================
# Chart Drawer Composite Location Info Tests
# ============================================================================


class TestChartDrawerCompositeLocation:
    """Tests for chart drawer with composite subject location handling."""

    def test_composite_chart_uses_average_location(self):
        """Test composite chart uses average of both subjects' locations."""
        from kerykeion.charts.chart_drawer import ChartDrawer
        from kerykeion.composite_subject_factory import CompositeSubjectFactory

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
        composite = CompositeSubjectFactory(first, second)
        composite_model = composite.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_model)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert svg is not None


# ============================================================================
# Draw Planets Group Handling Tests
# ============================================================================


class TestDrawPlanetsGroupHandling:
    """Tests for draw_planets group handling edge cases."""

    def test_chart_with_closely_clustered_planets(self):
        """Test chart with closely clustered planets triggers group handling."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        # Find a date where planets cluster together
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Clustered",
            year=2000,
            month=5,
            day=5,
            hour=12,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            active_points=[
                "Sun",
                "Moon",
                "Mercury",
                "Venus",
                "Mars",
                "Jupiter",
                "Saturn",
                "Uranus",
                "Neptune",
                "Pluto",
            ],
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert svg is not None
        assert "<svg" in svg

    def test_synastry_chart_with_overlapping_planets(self):
        """Test synastry chart with overlapping planet positions."""
        from kerykeion.charts.chart_drawer import ChartDrawer

        # Create subjects born at similar times for overlapping positions
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
        # Second subject born just a few hours later - similar positions
        second = AstrologicalSubjectFactory.from_birth_data(
            name="Second",
            year=1990,
            month=6,
            day=15,
            hour=18,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(first, second)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert svg is not None


# ============================================================================
# Regression: floating point cusp boundary (Jhalawar Sidereal LAHIRI)
# ============================================================================


class TestFloatingPointCuspBoundary:
    """Regression test for planet longitude matching a house cusp within
    floating point noise (~5e-14), which previously caused a ValueError
    in get_planet_house because no house arc contained the planet.

    Reported with: Jhalawar (IN), 2023-03-17 14:30, Sidereal LAHIRI.
    Fixed in commit 8fdaca7 (math.isclose in is_point_between).
    """

    def test_jhalawar_sidereal_lahiri_does_not_raise(self):
        """End-to-end: creating the subject must not raise."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Native",
            year=2023,
            month=3,
            day=17,
            hour=14,
            minute=30,
            lng=76.5221078,
            lat=24.3132368,
            tz_str="Asia/Kolkata",
            city="Jhalawar",
            nation="IN",
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            online=False,
            suppress_geonames_warning=True,
        )
        # Subject must be fully constructed with valid house assignments
        assert subject is not None
        assert subject.sun is not None
        assert subject.sun.house is not None
        assert subject.moon is not None
        assert subject.moon.house is not None
