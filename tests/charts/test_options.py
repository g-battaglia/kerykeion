# -*- coding: utf-8 -*-
"""
ChartDrawer Options and Edge Cases SVG Tests

This module tests ChartDrawer configuration options and edge cases:
- Custom titles
- Padding options
- Aspect icons
- Auto-size
- CSS variables
- Custom colors and settings
- Language pack overrides
- Parameter combinations
- Edge cases (long names, extreme latitudes, historical/future dates)
- Error handling
- Save methods

Usage:
    pytest tests/charts/test_options.py -v
"""

import copy
import os
import tempfile

import pytest

from kerykeion import AstrologicalSubjectFactory, ChartDrawer
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.schemas import KerykeionException

from .conftest import (
    JOHN_LENNON_BIRTH_DATA,
    compare_chart_svg,
)


class TestChartDrawerOptions:
    """ChartDrawer configuration option tests."""

    def test_custom_title_natal_chart(self):
        """Test natal chart with custom title override."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Custom Title", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, custom_title="My Custom Chart Title").generate_svg_string()
        compare_chart_svg("John Lennon - Custom Title - Natal Chart.svg", chart_svg)

    def test_show_aspect_icons_false(self):
        """Test natal chart with aspect icons disabled."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - No Aspect Icons", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, show_aspect_icons=False).generate_svg_string()
        compare_chart_svg("John Lennon - No Aspect Icons - Natal Chart.svg", chart_svg)

    def test_auto_size_false(self):
        """Test natal chart with auto_size disabled."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Auto Size False", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, auto_size=False).generate_svg_string()
        compare_chart_svg("John Lennon - Auto Size False - Natal Chart.svg", chart_svg)

    def test_remove_css_variables(self):
        """Test natal chart with CSS variables removed (inlined)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - No CSS Variables", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string(remove_css_variables=True)
        compare_chart_svg("John Lennon - No CSS Variables - Natal Chart.svg", chart_svg)

    def test_custom_padding_natal_chart(self):
        """Test natal chart with custom padding (50px instead of default 20px)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Custom Padding", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, padding=50).generate_svg_string()
        compare_chart_svg("John Lennon - Custom Padding - Natal Chart.svg", chart_svg)


class TestUntestedParameters:
    """Tests for previously untested parameters."""

    def test_theme_none(self):
        """Test natal chart with theme=None (no CSS theme applied)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - No Theme", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme=None).generate_svg_string()
        compare_chart_svg("John Lennon - No Theme - Natal Chart.svg", chart_svg)

    def test_show_degree_indicators_false(self):
        """Test natal chart with degree indicators hidden."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - No Degree Indicators", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, show_degree_indicators=False).generate_svg_string()
        compare_chart_svg("John Lennon - No Degree Indicators - Natal Chart.svg", chart_svg)

    def test_custom_colors_settings(self):
        """Test natal chart with custom colors settings."""
        from kerykeion.settings.chart_defaults import DEFAULT_CHART_COLORS

        custom_colors = DEFAULT_CHART_COLORS.copy()
        custom_colors["paper_0"] = "#ff0000"  # Red background
        custom_colors["paper_1"] = "#00ff00"  # Green paper
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Custom Colors", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, colors_settings=custom_colors).generate_svg_string()
        compare_chart_svg("John Lennon - Custom Colors - Natal Chart.svg", chart_svg)

    def test_custom_aspects_settings(self):
        """Test natal chart with custom aspect settings (custom colors)."""
        from kerykeion.settings.chart_defaults import DEFAULT_CHART_ASPECTS_SETTINGS

        # Customize colors for aspects instead of removing them
        custom_aspects = copy.deepcopy(DEFAULT_CHART_ASPECTS_SETTINGS)
        for aspect in custom_aspects:
            if aspect["name"] == "conjunction":
                aspect["color"] = "#FF0000"  # Red
            elif aspect["name"] == "opposition":
                aspect["color"] = "#0000FF"  # Blue
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Custom Aspect Colors", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, aspects_settings=custom_aspects).generate_svg_string()
        compare_chart_svg("John Lennon - Custom Aspect Colors - Natal Chart.svg", chart_svg)

    def test_custom_celestial_points_settings(self):
        """Test natal chart with custom celestial point colors."""
        from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS

        custom_points = copy.deepcopy(DEFAULT_CELESTIAL_POINTS_SETTINGS)
        # Change Sun and Moon colors to fixed values
        for point in custom_points:
            if point["name"] == "Sun":
                point["color"] = "#FFD700"  # Gold
            elif point["name"] == "Moon":
                point["color"] = "#C0C0C0"  # Silver
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Custom Planet Colors", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, celestial_points_settings=custom_points).generate_svg_string()
        compare_chart_svg("John Lennon - Custom Planet Colors - Natal Chart.svg", chart_svg)

    def test_language_pack_override(self):
        """Test natal chart with custom language pack overriding default translations."""
        custom_language_pack = {
            "Sun": "Sole Custom",
            "Moon": "Luna Custom",
        }
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Language Pack", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(
            chart_data, chart_language="IT", language_pack=custom_language_pack
        ).generate_svg_string()
        compare_chart_svg("John Lennon - Language Pack - Natal Chart.svg", chart_svg)


class TestParameterCombinations:
    """Tests for parameter combinations."""

    def test_transparent_background_dark_theme(self):
        """Test natal chart with transparent background and dark theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Transparent Dark", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="dark", transparent_background=True).generate_svg_string()
        compare_chart_svg("John Lennon - Transparent Dark - Natal Chart.svg", chart_svg)

    def test_padding_zero(self):
        """Test natal chart with zero padding."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Zero Padding", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, padding=0).generate_svg_string()
        compare_chart_svg("John Lennon - Zero Padding - Natal Chart.svg", chart_svg)

    def test_padding_large(self):
        """Test natal chart with large padding (100px)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Large Padding", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, padding=100).generate_svg_string()
        compare_chart_svg("John Lennon - Large Padding - Natal Chart.svg", chart_svg)

    def test_minify_and_remove_css_combined(self):
        """Test natal chart with both minify and remove_css_variables enabled."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Minify CSS", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string(minify=True, remove_css_variables=True)
        compare_chart_svg("John Lennon - Minify CSS - Natal Chart.svg", chart_svg)


class TestEdgeCases:
    """Edge case tests."""

    def test_very_long_name(self):
        """Test natal chart with a very long subject name (tests truncation)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "A" * 100,  # 100 character name
            *JOHN_LENNON_BIRTH_DATA,
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("Long Name - Natal Chart.svg", chart_svg)

    def test_extreme_latitude_north(self):
        """Test natal chart with extreme northern latitude (near North Pole)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Arctic Subject",
            1990,
            6,
            21,
            12,
            0,
            "Longyearbyen",
            "NO",
            lat=78.22,
            lng=15.65,
            tz_str="Arctic/Longyearbyen",
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("Arctic Subject - Natal Chart.svg", chart_svg)

    def test_extreme_latitude_south(self):
        """Test natal chart with extreme southern latitude (Antarctica)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Antarctic Subject",
            1990,
            12,
            21,
            12,
            0,
            "McMurdo Station",
            "AQ",
            lat=-77.85,
            lng=166.67,
            tz_str="Antarctica/McMurdo",
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("Antarctic Subject - Natal Chart.svg", chart_svg)

    def test_historical_date(self):
        """Test natal chart with historical date (year 1500)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Historical Subject", 1500, 3, 15, 12, 0, "Florence", "IT", suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("Historical Subject - Natal Chart.svg", chart_svg)

    def test_future_date(self):
        """Test natal chart with future date (year 2100)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Future Subject", 2100, 7, 4, 12, 0, "New York", "US", suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("Future Subject - Natal Chart.svg", chart_svg)

    def test_date_line_crossing(self):
        """Test natal chart with location near International Date Line."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Date Line Subject",
            1990,
            1,
            1,
            12,
            0,
            "Suva",
            "FJ",
            lat=-18.14,
            lng=178.44,
            tz_str="Pacific/Fiji",
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("Date Line Subject - Natal Chart.svg", chart_svg)


class TestErrorHandling:
    """Error handling tests."""

    def test_invalid_theme_raises_exception(self, john_lennon):
        """Test that invalid theme raises KerykeionException."""
        chart_data = ChartDataFactory.create_natal_chart_data(john_lennon)
        with pytest.raises(KerykeionException):
            ChartDrawer(chart_data, theme="invalid_theme_name")  # type: ignore


class TestSaveMethods:
    """Save methods tests."""

    def test_save_svg_creates_file(self, john_lennon):
        """Test that save_svg method creates a file on disk."""
        chart_data = ChartDataFactory.create_natal_chart_data(john_lennon)
        drawer = ChartDrawer(chart_data)

        with tempfile.TemporaryDirectory() as tmpdir:
            drawer.save_svg(output_path=tmpdir, filename="test_output")
            expected_file = os.path.join(tmpdir, "test_output.svg")
            assert os.path.exists(expected_file), f"File {expected_file} was not created"

            # Verify content is valid SVG (contains svg tag somewhere)
            with open(expected_file, "r") as f:
                content = f.read()
                assert "<svg" in content, "File does not contain SVG content"

    def test_save_wheel_only_creates_file(self, john_lennon):
        """Test that save_wheel_only_svg_file method creates a file on disk."""
        chart_data = ChartDataFactory.create_natal_chart_data(john_lennon)
        drawer = ChartDrawer(chart_data)

        with tempfile.TemporaryDirectory() as tmpdir:
            drawer.save_wheel_only_svg_file(output_path=tmpdir, filename="test_wheel")
            expected_file = os.path.join(tmpdir, "test_wheel.svg")
            assert os.path.exists(expected_file), f"File {expected_file} was not created"

    def test_save_aspect_grid_only_creates_file(self, john_lennon):
        """Test that save_aspect_grid_only_svg_file method creates a file on disk."""
        chart_data = ChartDataFactory.create_natal_chart_data(john_lennon)
        drawer = ChartDrawer(chart_data)

        with tempfile.TemporaryDirectory() as tmpdir:
            drawer.save_aspect_grid_only_svg_file(output_path=tmpdir, filename="test_grid")
            expected_file = os.path.join(tmpdir, "test_grid.svg")
            assert os.path.exists(expected_file), f"File {expected_file} was not created"
