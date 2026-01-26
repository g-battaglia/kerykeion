# -*- coding: utf-8 -*-
"""
Return Chart (Solar/Lunar) SVG Tests

This module tests return chart generation including:
- Dual return charts (Natal + Return wheel)
- Single return charts (Return only)
- Solar returns
- Lunar returns
- House and cusp comparison options
- Theme variations
- Wheel-only and aspect-grid-only outputs

Usage:
    pytest tests/charts/test_returns.py -v
"""

from kerykeion import AstrologicalSubjectFactory, ChartDrawer
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory

from .conftest import (
    JOHN_LENNON_BIRTH_DATA,
    compare_chart_svg,
    create_return_factory,
)


class TestSolarReturnDual:
    """Dual solar return chart tests (Natal + Solar Return)."""

    def test_dual_return_solar_chart(self, john_lennon):
        """Test dual return chart (Natal + Solar Return)."""
        return_factory = create_return_factory(john_lennon)
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Solar"
        )
        chart_data = ChartDataFactory.create_return_chart_data(john_lennon, solar_return)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Solar Return.svg", chart_svg)

    def test_dual_return_solar_no_house_comparison(self, john_lennon):
        """Test dual solar return chart with no house comparison."""
        return_factory = create_return_factory(john_lennon)
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Solar"
        )
        chart_data = ChartDataFactory.create_return_chart_data(john_lennon, solar_return)
        chart_svg = ChartDrawer(chart_data, show_house_position_comparison=False).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Solar Return - No House Comparison.svg", chart_svg)

    def test_dual_return_solar_house_comparison_only(self, john_lennon):
        """Test dual solar return chart with house comparison only."""
        return_factory = create_return_factory(john_lennon)
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Solar"
        )
        chart_data = ChartDataFactory.create_return_chart_data(john_lennon, solar_return)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=False,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Solar Return - House Comparison Only.svg", chart_svg)

    def test_dual_return_solar_cusp_comparison_only(self, john_lennon):
        """Test dual solar return chart with cusp comparison only."""
        return_factory = create_return_factory(john_lennon)
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Solar"
        )
        chart_data = ChartDataFactory.create_return_chart_data(john_lennon, solar_return)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=False,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Solar Return - Cusp Comparison Only.svg", chart_svg)

    def test_dual_return_solar_house_and_cusp_comparison(self, john_lennon):
        """Test dual solar return chart with both house and cusp comparison."""
        return_factory = create_return_factory(john_lennon)
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Solar"
        )
        chart_data = ChartDataFactory.create_return_chart_data(john_lennon, solar_return)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        compare_chart_svg(
            "John Lennon - DualReturnChart Chart - Solar Return - House and Cusp Comparison.svg", chart_svg
        )

    def test_black_and_white_dual_return_chart(self, john_lennon):
        """Test dual return chart with black-and-white theme."""
        return_factory = create_return_factory(john_lennon)
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Solar"
        )
        chart_data = ChartDataFactory.create_return_chart_data(john_lennon, solar_return)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        compare_chart_svg("John Lennon - Black and White Theme - DualReturnChart Chart - Solar Return.svg", chart_svg)

    def test_strawberry_solar_return_dual(self, john_lennon):
        """Test dual solar return chart with Strawberry theme."""
        return_factory = create_return_factory(john_lennon)
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00",
            return_type="Solar",
        )
        chart_data = ChartDataFactory.create_return_chart_data(john_lennon, solar_return)
        chart_svg = ChartDrawer(chart_data, theme="strawberry").generate_svg_string()
        compare_chart_svg("John Lennon - Strawberry Theme - DualReturnChart Chart - Solar Return.svg", chart_svg)


class TestSolarReturnSingle:
    """Single solar return chart tests (Return only)."""

    def test_single_return_solar_chart(self, john_lennon):
        """Test single wheel return chart (Solar Return only)."""
        return_factory = create_return_factory(john_lennon)
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Solar"
        )
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Solar Return - SingleReturnChart Chart.svg", chart_svg)

    def test_black_and_white_single_return_chart(self, john_lennon):
        """Test single return chart with black-and-white theme."""
        return_factory = create_return_factory(john_lennon)
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Solar"
        )
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        compare_chart_svg("John Lennon Solar Return - Black and White Theme - SingleReturnChart Chart.svg", chart_svg)


class TestLunarReturnDual:
    """Dual lunar return chart tests (Natal + Lunar Return)."""

    def test_dual_return_lunar_chart(self, john_lennon):
        """Test dual return chart (Natal + Lunar Return)."""
        return_factory = create_return_factory(john_lennon)
        lunar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Lunar"
        )
        chart_data = ChartDataFactory.create_return_chart_data(john_lennon, lunar_return)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Lunar Return.svg", chart_svg)

    def test_dual_return_lunar_no_house_comparison(self, john_lennon):
        """Test dual lunar return chart with no house comparison."""
        return_factory = create_return_factory(john_lennon)
        lunar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Lunar"
        )
        chart_data = ChartDataFactory.create_return_chart_data(john_lennon, lunar_return)
        chart_svg = ChartDrawer(chart_data, show_house_position_comparison=False).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Lunar Return - No House Comparison.svg", chart_svg)

    def test_dual_return_lunar_house_comparison_only(self, john_lennon):
        """Test dual lunar return chart with house comparison only."""
        return_factory = create_return_factory(john_lennon)
        lunar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Lunar"
        )
        chart_data = ChartDataFactory.create_return_chart_data(john_lennon, lunar_return)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=False,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Lunar Return - House Comparison Only.svg", chart_svg)

    def test_dual_return_lunar_cusp_comparison_only(self, john_lennon):
        """Test dual lunar return chart with cusp comparison only."""
        return_factory = create_return_factory(john_lennon)
        lunar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Lunar"
        )
        chart_data = ChartDataFactory.create_return_chart_data(john_lennon, lunar_return)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=False,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Lunar Return - Cusp Comparison Only.svg", chart_svg)

    def test_dual_return_lunar_house_and_cusp_comparison(self, john_lennon):
        """Test dual lunar return chart with both house and cusp comparison."""
        return_factory = create_return_factory(john_lennon)
        lunar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Lunar"
        )
        chart_data = ChartDataFactory.create_return_chart_data(john_lennon, lunar_return)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        compare_chart_svg(
            "John Lennon - DualReturnChart Chart - Lunar Return - House and Cusp Comparison.svg", chart_svg
        )

    def test_black_and_white_dual_lunar_return(self, john_lennon):
        """Test dual lunar return chart with black-and-white theme."""
        return_factory = create_return_factory(john_lennon)
        lunar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Lunar"
        )
        chart_data = ChartDataFactory.create_return_chart_data(john_lennon, lunar_return)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        compare_chart_svg("John Lennon - Black and White Theme - DualReturnChart Chart - Lunar Return.svg", chart_svg)


class TestLunarReturnSingle:
    """Single lunar return chart tests (Return only)."""

    def test_single_return_lunar_chart(self, john_lennon):
        """Test single wheel return chart (Lunar Return only)."""
        return_factory = create_return_factory(john_lennon)
        lunar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Lunar"
        )
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(lunar_return)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Lunar Return - SingleReturnChart Chart.svg", chart_svg)

    def test_black_and_white_single_lunar_return(self, john_lennon):
        """Test single lunar return chart with black-and-white theme."""
        return_factory = create_return_factory(john_lennon)
        lunar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Lunar"
        )
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(lunar_return)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        compare_chart_svg("John Lennon Lunar Return - Black and White Theme - SingleReturnChart Chart.svg", chart_svg)


class TestReturnChartPartialViews:
    """Wheel-only and aspect-grid-only return chart tests."""

    def test_return_chart_wheel_only(self, john_lennon):
        """Test solar return chart wheel-only output."""
        return_factory = create_return_factory(john_lennon)
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Solar"
        )
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
        chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon Solar Return - Wheel Only.svg", chart_svg)

    def test_return_chart_aspect_grid_only(self, john_lennon):
        """Test solar return chart aspect-grid-only output."""
        return_factory = create_return_factory(john_lennon)
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Solar"
        )
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
        chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon Solar Return - Aspect Grid Only.svg", chart_svg)


class TestStrawberryReturnCharts:
    """Strawberry theme return chart tests."""

    def test_strawberry_lunar_return_dual(self, john_lennon):
        """Test dual lunar return chart with Strawberry theme."""
        return_factory = create_return_factory(john_lennon)
        lunar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00",
            return_type="Lunar",
        )
        chart_data = ChartDataFactory.create_return_chart_data(john_lennon, lunar_return)
        chart_svg = ChartDrawer(chart_data, theme="strawberry").generate_svg_string()
        compare_chart_svg("John Lennon - Strawberry Theme - DualReturnChart Chart - Lunar Return.svg", chart_svg)

    def test_strawberry_solar_return_single(self, john_lennon):
        """Test single solar return chart with Strawberry theme."""
        return_factory = create_return_factory(john_lennon)
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00",
            return_type="Solar",
        )
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
        chart_svg = ChartDrawer(chart_data, theme="strawberry").generate_svg_string()
        compare_chart_svg("John Lennon Solar Return - Strawberry Theme - SingleReturnChart Chart.svg", chart_svg)
