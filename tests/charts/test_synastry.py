# -*- coding: utf-8 -*-
"""
Synastry Chart SVG Tests

This module tests synastry chart generation including:
- Basic synastry charts
- House and cusp comparison options
- Theme variations
- Perspective types
- Language tests
- Relationship score integration
- All active points

Usage:
    pytest tests/charts/test_synastry.py -v
"""

from kerykeion import AstrologicalSubjectFactory, ChartDrawer
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

from .conftest import (
    JOHN_LENNON_BIRTH_DATA,
    PAUL_MCCARTNEY_BIRTH_DATA,
    compare_chart_svg,
)


class TestSynastryChartBasic:
    """Basic synastry chart tests."""

    def test_synastry_chart(self, john_lennon, paul_mccartney):
        """Test basic synastry chart."""
        chart_data = ChartDataFactory.create_synastry_chart_data(john_lennon, paul_mccartney)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon - Synastry Chart.svg", chart_svg)

    def test_synastry_chart_without_house_comparison_grid(self, john_lennon, paul_mccartney):
        """Test synastry chart without house comparison grid."""
        chart_data = ChartDataFactory.create_synastry_chart_data(john_lennon, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, show_house_position_comparison=False).generate_svg_string()
        compare_chart_svg("John Lennon - Synastry Chart - No House Comparison.svg", chart_svg)

    def test_synastry_chart_with_house_comparison_only(self, john_lennon, paul_mccartney):
        """Test synastry chart with house comparison only (no cusp comparison)."""
        chart_data = ChartDataFactory.create_synastry_chart_data(john_lennon, paul_mccartney)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=False,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - Synastry Chart - House Comparison Only.svg", chart_svg)

    def test_synastry_chart_with_cusp_comparison_only(self, john_lennon, paul_mccartney):
        """Test synastry chart with cusp comparison only (no house comparison)."""
        chart_data = ChartDataFactory.create_synastry_chart_data(john_lennon, paul_mccartney)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=False,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - Synastry Chart - Cusp Comparison Only.svg", chart_svg)

    def test_synastry_chart_with_house_and_cusp_comparison(self, john_lennon, paul_mccartney):
        """Test synastry chart with both house and cusp comparison."""
        chart_data = ChartDataFactory.create_synastry_chart_data(john_lennon, paul_mccartney)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - Synastry Chart - House and Cusp Comparison.svg", chart_svg)

    def test_synastry_chart_with_list_layout(self, paul_mccartney):
        """Test synastry chart with list layout for aspects."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - SCTWL", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, double_chart_aspect_grid_type="list", theme="dark").generate_svg_string()
        compare_chart_svg("John Lennon - SCTWL - Synastry Chart.svg", chart_svg)


class TestSynastryChartThemes:
    """Theme-based synastry chart tests."""

    def test_black_and_white_synastry_chart(self, john_lennon, paul_mccartney):
        """Test synastry chart with black-and-white theme."""
        chart_data = ChartDataFactory.create_synastry_chart_data(john_lennon, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        compare_chart_svg("John Lennon - Black and White Theme - Synastry Chart.svg", chart_svg)

    def test_dark_theme_synastry_chart(self, paul_mccartney):
        """Test synastry chart with dark theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - DTS", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_svg_string()
        compare_chart_svg("John Lennon - DTS - Synastry Chart.svg", chart_svg)

    def test_light_theme_synastry_chart(self, john_lennon, paul_mccartney):
        """Test synastry chart with light theme."""
        chart_data = ChartDataFactory.create_synastry_chart_data(john_lennon, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="light").generate_svg_string()
        compare_chart_svg("John Lennon - Light Theme - Synastry Chart.svg", chart_svg)

    def test_strawberry_synastry_chart(self, paul_mccartney):
        """Test synastry chart with Strawberry theme."""
        first = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Strawberry Theme Synastry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(first, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="strawberry").generate_svg_string()
        compare_chart_svg("John Lennon - Strawberry Theme Synastry - Synastry Chart.svg", chart_svg)


class TestSynastryChartPerspectives:
    """Perspective type synastry chart tests."""

    def test_heliocentric_synastry_chart(self):
        """Test synastry chart with heliocentric perspective."""
        first = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Heliocentric Synastry",
            *JOHN_LENNON_BIRTH_DATA,
            perspective_type="Heliocentric",
            suppress_geonames_warning=True,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            "Paul McCartney - Heliocentric",
            *PAUL_MCCARTNEY_BIRTH_DATA,
            perspective_type="Heliocentric",
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(first, second)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon - Heliocentric - Synastry Chart.svg", chart_svg)

    def test_true_geocentric_synastry_chart(self):
        """Test synastry chart with true geocentric perspective."""
        first = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - True Geocentric Synastry",
            *JOHN_LENNON_BIRTH_DATA,
            perspective_type="True Geocentric",
            suppress_geonames_warning=True,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            "Paul McCartney - True Geocentric",
            *PAUL_MCCARTNEY_BIRTH_DATA,
            perspective_type="True Geocentric",
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(first, second)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon - True Geocentric - Synastry Chart.svg", chart_svg)


class TestSynastryChartLanguages:
    """Language-specific synastry chart tests."""

    def test_french_synastry_chart(self, paul_mccartney):
        """Test synastry chart with French language."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - FR", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, chart_language="FR").generate_svg_string()
        compare_chart_svg("John Lennon - FR - Synastry Chart.svg", chart_svg)

    def test_german_synastry_chart(self, paul_mccartney):
        """Test synastry chart with German language."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - DE", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, chart_language="DE").generate_svg_string()
        compare_chart_svg("John Lennon - DE - Synastry Chart.svg", chart_svg)

    def test_turkish_synastry_chart(self, paul_mccartney):
        """Test synastry chart with Turkish language."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - TR", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, chart_language="TR").generate_svg_string()
        compare_chart_svg("John Lennon - TR - Synastry Chart.svg", chart_svg)

    def test_hindi_synastry_chart(self, paul_mccartney):
        """Test Hindi language synastry chart."""
        first = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - HI", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(first, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, chart_language="HI").generate_svg_string()
        compare_chart_svg("John Lennon - HI - Synastry Chart.svg", chart_svg)


class TestSynastryChartRelationshipScore:
    """Relationship score synastry chart tests."""

    def test_synastry_with_relationship_score(self, john_lennon, paul_mccartney):
        """Test synastry chart with relationship score calculation enabled."""
        chart_data = ChartDataFactory.create_synastry_chart_data(
            john_lennon,
            paul_mccartney,
            include_relationship_score=True,
        )
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon - Relationship Score - Synastry Chart.svg", chart_svg)


class TestSynastryChartAllActivePoints:
    """All active points synastry chart tests."""

    def test_synastry_chart_all_active_points_list(self, all_active_points_subject, all_active_points_second_subject):
        """Test synastry chart with all active points and list layout."""
        chart_data = ChartDataFactory.create_synastry_chart_data(
            all_active_points_subject,
            all_active_points_second_subject,
            active_points=ALL_ACTIVE_POINTS,
        )
        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)
        chart_svg = ChartDrawer(chart_data, double_chart_aspect_grid_type="list").generate_svg_string()
        compare_chart_svg("John Lennon - All Active Points - Synastry Chart - List.svg", chart_svg)

    def test_synastry_chart_all_active_points_grid(self, all_active_points_subject, all_active_points_second_subject):
        """Test synastry chart with all active points and table layout."""
        chart_data = ChartDataFactory.create_synastry_chart_data(
            all_active_points_subject,
            all_active_points_second_subject,
            active_points=ALL_ACTIVE_POINTS,
        )
        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)
        chart_svg = ChartDrawer(chart_data, double_chart_aspect_grid_type="table").generate_svg_string()
        compare_chart_svg("John Lennon - All Active Points - Synastry Chart - Grid.svg", chart_svg)


class TestSynastryChartCombinations:
    """Combined option synastry chart tests."""

    def test_transparent_background_synastry(self, paul_mccartney):
        """Test synastry chart with transparent background."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Transparent Synastry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, transparent_background=True).generate_svg_string()
        compare_chart_svg("John Lennon - Transparent Synastry - Synastry Chart.svg", chart_svg)

    def test_custom_title_synastry(self, paul_mccartney):
        """Test synastry chart with custom title."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Custom Title Synastry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, custom_title="Beatles Synastry Analysis").generate_svg_string()
        compare_chart_svg("John Lennon - Custom Title Synastry - Synastry Chart.svg", chart_svg)
