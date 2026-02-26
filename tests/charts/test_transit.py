# -*- coding: utf-8 -*-
"""
Transit Chart SVG Tests

This module tests transit chart generation including:
- Basic transit charts
- House and cusp comparison options
- Table grid layout
- Theme variations
- Perspective types
- Language tests
- All active points

Usage:
    pytest tests/charts/test_transit.py -v
"""

from kerykeion import AstrologicalSubjectFactory, ChartDrawer
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

from .conftest import (
    JOHN_LENNON_BIRTH_DATA,
    PAUL_MCCARTNEY_BIRTH_DATA,
    compare_chart_svg,
)


class TestTransitChartBasic:
    """Basic transit chart tests."""

    def test_transit_chart(self, john_lennon, paul_mccartney):
        """Test basic transit chart."""
        chart_data = ChartDataFactory.create_transit_chart_data(john_lennon, paul_mccartney)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon - Transit Chart.svg", chart_svg)

    def test_transit_chart_without_house_comparison_grid(self, john_lennon, paul_mccartney):
        """Test transit chart without house comparison grid."""
        chart_data = ChartDataFactory.create_transit_chart_data(john_lennon, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, show_house_position_comparison=False).generate_svg_string()
        compare_chart_svg("John Lennon - Transit Chart - No House Comparison.svg", chart_svg)

    def test_transit_chart_with_house_comparison_only(self, john_lennon, paul_mccartney):
        """Test transit chart with house comparison only (no cusp comparison)."""
        chart_data = ChartDataFactory.create_transit_chart_data(john_lennon, paul_mccartney)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=False,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - Transit Chart - House Comparison Only.svg", chart_svg)

    def test_transit_chart_with_cusp_comparison_only(self, john_lennon, paul_mccartney):
        """Test transit chart with cusp comparison only (no house comparison)."""
        chart_data = ChartDataFactory.create_transit_chart_data(john_lennon, paul_mccartney)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=False,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - Transit Chart - Cusp Comparison Only.svg", chart_svg)

    def test_transit_chart_with_house_and_cusp_comparison(self, john_lennon, paul_mccartney):
        """Test transit chart with both house and cusp comparison."""
        chart_data = ChartDataFactory.create_transit_chart_data(john_lennon, paul_mccartney)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - Transit Chart - House and Cusp Comparison.svg", chart_svg)

    def test_transit_chart_with_table_grid(self, paul_mccartney):
        """Test transit chart with table grid layout."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - TCWTG", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, double_chart_aspect_grid_type="table", theme="dark").generate_svg_string()
        compare_chart_svg("John Lennon - TCWTG - Transit Chart.svg", chart_svg)


class TestTransitChartThemes:
    """Theme-based transit chart tests."""

    def test_black_and_white_transit_chart(self, john_lennon, paul_mccartney):
        """Test transit chart with black-and-white theme."""
        chart_data = ChartDataFactory.create_transit_chart_data(john_lennon, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        compare_chart_svg("John Lennon - Black and White Theme - Transit Chart.svg", chart_svg)

    def test_light_theme_transit_chart(self, john_lennon, paul_mccartney):
        """Test transit chart with light theme."""
        chart_data = ChartDataFactory.create_transit_chart_data(john_lennon, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="light").generate_svg_string()
        compare_chart_svg("John Lennon - Light Theme - Transit Chart.svg", chart_svg)

    def test_dark_theme_transit_chart(self, john_lennon, paul_mccartney):
        """Test transit chart with dark theme."""
        chart_data = ChartDataFactory.create_transit_chart_data(john_lennon, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_svg_string()
        compare_chart_svg("John Lennon - Dark Theme - Transit Chart.svg", chart_svg)

    def test_strawberry_transit_chart(self, paul_mccartney):
        """Test transit chart with Strawberry theme."""
        first = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Strawberry Theme Transit", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(first, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="strawberry").generate_svg_string()
        compare_chart_svg("John Lennon - Strawberry Theme Transit - Transit Chart.svg", chart_svg)


class TestTransitChartPerspectives:
    """Perspective type transit chart tests."""

    def test_topocentric_transit_chart(self):
        """Test transit chart with topocentric perspective."""
        first = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Topocentric Transit",
            *JOHN_LENNON_BIRTH_DATA,
            perspective_type="Topocentric",
            suppress_geonames_warning=True,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            "Paul McCartney - Topocentric",
            *PAUL_MCCARTNEY_BIRTH_DATA,
            perspective_type="Topocentric",
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_transit_chart_data(first, second)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon - Topocentric - Transit Chart.svg", chart_svg)


class TestTransitChartLanguages:
    """Language-specific transit chart tests."""

    def test_chinese_transit_chart(self, paul_mccartney):
        """Test transit chart with Chinese language."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - CN", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, chart_language="CN").generate_svg_string()
        compare_chart_svg("John Lennon - CN - Transit Chart.svg", chart_svg)

    def test_spanish_transit_chart(self, paul_mccartney):
        """Test transit chart with Spanish language."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - ES", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, chart_language="ES").generate_svg_string()
        compare_chart_svg("John Lennon - ES - Transit Chart.svg", chart_svg)

    def test_russian_transit_chart(self, paul_mccartney):
        """Test transit chart with Russian language."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - RU", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, chart_language="RU").generate_svg_string()
        compare_chart_svg("John Lennon - RU - Transit Chart.svg", chart_svg)


class TestTransitChartAllActivePoints:
    """All active points transit chart tests."""

    def test_transit_all_active_points(self):
        """Test transit chart with all active points enabled."""
        first = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - All Active Points Transit",
            *JOHN_LENNON_BIRTH_DATA,
            suppress_geonames_warning=True,
            active_points=ALL_ACTIVE_POINTS,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            "Paul McCartney - All Active Points Transit",
            *PAUL_MCCARTNEY_BIRTH_DATA,
            suppress_geonames_warning=True,
            active_points=ALL_ACTIVE_POINTS,
        )
        chart_data = ChartDataFactory.create_transit_chart_data(first, second, active_points=ALL_ACTIVE_POINTS)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon - All Active Points - Transit Chart.svg", chart_svg)


class TestTransitChartCombinations:
    """Combined option transit chart tests."""

    def test_custom_title_transit(self, paul_mccartney):
        """Test transit chart with custom title."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Custom Title Transit", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, custom_title="Transit Analysis 2024").generate_svg_string()
        compare_chart_svg("John Lennon - Custom Title Transit - Transit Chart.svg", chart_svg)
