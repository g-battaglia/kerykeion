# -*- coding: utf-8 -*-
"""
Composite Chart SVG Tests

This module tests composite chart generation including:
- Basic composite charts
- Theme variations
- Wheel-only and aspect-grid-only outputs
- Language tests

Usage:
    pytest tests/charts/test_composite.py -v
"""

from kerykeion import AstrologicalSubjectFactory, ChartDrawer, CompositeSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory

from .conftest import compare_chart_svg


class TestCompositeChartBasic:
    """Basic composite chart tests."""

    def test_composite_chart(self, angelina_jolie, brad_pitt):
        """Test basic composite chart."""
        factory = CompositeSubjectFactory(angelina_jolie, brad_pitt)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - Composite Chart.svg", chart_svg)


class TestCompositeChartThemes:
    """Theme-based composite chart tests."""

    def test_black_and_white_composite_chart(self, angelina_jolie, brad_pitt):
        """Test composite chart with black-and-white theme."""
        factory = CompositeSubjectFactory(angelina_jolie, brad_pitt)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        compare_chart_svg(
            "Angelina Jolie and Brad Pitt Composite Chart - Black and White Theme - Composite Chart.svg", chart_svg
        )

    def test_light_theme_composite_chart(self, angelina_jolie, brad_pitt):
        """Test composite chart with light theme."""
        factory = CompositeSubjectFactory(angelina_jolie, brad_pitt)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart_svg = ChartDrawer(chart_data, theme="light").generate_svg_string()
        compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - Light Theme - Composite Chart.svg", chart_svg)

    def test_dark_theme_composite_chart(self, angelina_jolie, brad_pitt):
        """Test composite chart with dark theme."""
        factory = CompositeSubjectFactory(angelina_jolie, brad_pitt)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_svg_string()
        compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - Dark Theme - Composite Chart.svg", chart_svg)

    def test_strawberry_composite_chart(self, angelina_jolie, brad_pitt):
        """Test composite chart with Strawberry theme."""
        composite_factory = CompositeSubjectFactory(angelina_jolie, brad_pitt)
        composite_model = composite_factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_model)
        chart_svg = ChartDrawer(chart_data, theme="strawberry").generate_svg_string()
        compare_chart_svg(
            "Angelina Jolie and Brad Pitt Composite Chart - Strawberry Theme - Composite Chart.svg", chart_svg
        )


class TestCompositeChartPartialViews:
    """Wheel-only and aspect-grid-only composite chart tests."""

    def test_composite_chart_wheel_only(self, angelina_jolie, brad_pitt):
        """Test composite chart wheel-only output."""
        factory = CompositeSubjectFactory(angelina_jolie, brad_pitt)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()
        compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - Composite Chart - Wheel Only.svg", chart_svg)

    def test_composite_chart_aspect_grid_only(self, angelina_jolie, brad_pitt):
        """Test composite chart aspect-grid-only output."""
        factory = CompositeSubjectFactory(angelina_jolie, brad_pitt)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()
        compare_chart_svg(
            "Angelina Jolie and Brad Pitt Composite Chart - Composite Chart - Aspect Grid Only.svg", chart_svg
        )


class TestCompositeChartLanguages:
    """Language-specific composite chart tests."""

    def test_italian_composite_chart(self, angelina_jolie, brad_pitt):
        """Test composite chart with Italian language."""
        factory = CompositeSubjectFactory(angelina_jolie, brad_pitt)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="IT").generate_svg_string()
        compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - IT - Composite Chart.svg", chart_svg)

    def test_portuguese_composite_chart(self, angelina_jolie, brad_pitt):
        """Test composite chart with Portuguese language."""
        factory = CompositeSubjectFactory(angelina_jolie, brad_pitt)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="PT").generate_svg_string()
        compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - PT - Composite Chart.svg", chart_svg)

    def test_french_composite_chart(self, angelina_jolie, brad_pitt):
        """Test French language composite chart."""
        composite_factory = CompositeSubjectFactory(angelina_jolie, brad_pitt)
        composite_model = composite_factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_model)
        chart_svg = ChartDrawer(chart_data, chart_language="FR").generate_svg_string()
        compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - FR - Composite Chart.svg", chart_svg)
