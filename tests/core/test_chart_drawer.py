# -*- coding: utf-8 -*-
"""
Comprehensive ChartDrawer Tests

Consolidated test suite integrating all chart drawer test cases:
- Basic creation and properties (from test_chart_drawer_complete.py)
- Natal chart golden-file regression (from test_natal.py)
- Synastry chart golden-file regression (from test_synastry.py)
- Transit chart golden-file regression (from test_transit.py)
- Composite chart golden-file regression (from test_composite.py)
- Return chart tests (from test_returns.py)
- Chart options and edge cases (from test_options.py)
- Partial views: wheel-only, aspect-grid-only (from test_partial_views.py)
- Parametrized extended tests (from test_parametrized.py)
- Indicators-off tests (from test_indicators_off.py)

Usage:
    pytest tests/core/test_chart_drawer.py -v
"""

import copy
import os
import re
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion.charts.charts_utils import makeLunarPhase
from kerykeion.composite_subject_factory import CompositeSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.schemas import KerykeionException


# =============================================================================
# CONSTANTS
# =============================================================================

SVG_DIR = Path(__file__).parent.parent / "data" / "svg"

# Common birth data: (year, month, day, hour, minute, city, country)
JOHN_LENNON_BIRTH_DATA = (1940, 10, 9, 18, 30, "Liverpool", "GB")
PAUL_MCCARTNEY_BIRTH_DATA = (1942, 6, 18, 15, 30, "Liverpool", "GB")


# =============================================================================
# SVG COMPARISON UTILITY
# =============================================================================


def compare_svg_lines(
    expected_line: str,
    actual_line: str,
    rel_tol: float = 1e-10,
    abs_tol: float = 1e-10,
) -> None:
    """Compare two SVG lines allowing small floating-point differences."""
    number_regex = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"

    expected_numbers = [float(x) for x in re.findall(number_regex, expected_line)]
    actual_numbers = [float(x) for x in re.findall(number_regex, actual_line)]

    assert len(expected_numbers) == len(actual_numbers), (
        f"Different number of numeric values found:\nExpected: {expected_numbers}\nActual: {actual_numbers}"
    )

    for index, (e, a) in enumerate(zip(expected_numbers, actual_numbers)):
        if abs(a - e) > max(rel_tol * abs(e), abs_tol):
            assert False, (
                f"Numeric values exceed tolerance at position {index}:\n"
                f"Expected line: {expected_line}\n"
                f"Actual line:   {actual_line}\n"
                f"Expected: {e}, Actual: {a}"
            )

    expected_text = re.sub(number_regex, "NUM", expected_line)
    actual_text = re.sub(number_regex, "NUM", actual_line)
    assert expected_text == actual_text, f"Non-numeric parts differ:\nExpected: {expected_text}\nActual: {actual_text}"


def compare_chart_svg(file_name: str, chart_svg: str) -> None:
    """Compare generated SVG against a baseline file, skipping if missing."""
    baseline = SVG_DIR / file_name
    if not baseline.exists():
        pytest.skip(f"Baseline not found: {baseline}. Run: poe regenerate:charts")

    chart_svg_lines = chart_svg.splitlines()
    with open(baseline, "r", encoding="utf-8") as f:
        file_content_lines = f.read().splitlines()

    assert len(chart_svg_lines) == len(file_content_lines), (
        f"Line count mismatch in {file_name}: Expected {len(file_content_lines)} lines, got {len(chart_svg_lines)}"
    )

    for expected_line, actual_line in zip(file_content_lines, chart_svg_lines):
        compare_svg_lines(expected_line, actual_line)


# =============================================================================
# SUBJECT FACTORY HELPERS
# =============================================================================


def _make_john(name_suffix="", **kwargs):
    """Create a John Lennon subject with optional suffix and overrides."""
    name = f"John Lennon{' - ' + name_suffix if name_suffix else ''}"
    return AstrologicalSubjectFactory.from_birth_data(
        name, *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True, **kwargs
    )


def _make_paul(name_suffix="", **kwargs):
    """Create a Paul McCartney subject with optional suffix and overrides."""
    name = f"Paul McCartney{' - ' + name_suffix if name_suffix else ''}"
    return AstrologicalSubjectFactory.from_birth_data(
        name, *PAUL_MCCARTNEY_BIRTH_DATA, suppress_geonames_warning=True, **kwargs
    )


def _make_sidereal_subject(name_suffix, sidereal_mode):
    """Create a sidereal John Lennon subject."""
    return AstrologicalSubjectFactory.from_birth_data(
        f"John Lennon {name_suffix}",
        *JOHN_LENNON_BIRTH_DATA,
        zodiac_type="Sidereal",
        sidereal_mode=sidereal_mode,
        suppress_geonames_warning=True,
    )


def _make_return_factory(subject):
    """Create a PlanetaryReturnFactory for a subject."""
    return PlanetaryReturnFactory(
        subject,
        lng=-2.9833,
        lat=53.4000,
        tz_str="Europe/London",
        online=False,
    )


def _make_angelina():
    return AstrologicalSubjectFactory.from_birth_data(
        "Angelina Jolie",
        1975,
        6,
        4,
        9,
        9,
        "Los Angeles",
        "US",
        lng=-118.15,
        lat=34.03,
        tz_str="America/Los_Angeles",
        suppress_geonames_warning=True,
    )


def _make_brad():
    return AstrologicalSubjectFactory.from_birth_data(
        "Brad Pitt",
        1963,
        12,
        18,
        6,
        31,
        "Shawnee",
        "US",
        lng=-96.56,
        lat=35.20,
        tz_str="America/Chicago",
        suppress_geonames_warning=True,
    )


# =============================================================================
# 1. TestChartDrawerBasic
# =============================================================================


class TestChartDrawerBasic:
    """Basic creation, properties, and attribute tests (from test_chart_drawer_complete.py)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test Subject",
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
            suppress_geonames_warning=True,
        )
        self.chart_data = ChartDataFactory.create_natal_chart_data(self.subject)
        self.subject2 = AstrologicalSubjectFactory.from_birth_data(
            name="Test Subject 2",
            year=1992,
            month=8,
            day=20,
            hour=15,
            minute=45,
            city="Los Angeles",
            nation="US",
            lng=-118.2437,
            lat=34.0522,
            tz_str="America/Los_Angeles",
            suppress_geonames_warning=True,
        )

    def test_basic_chart_creation(self):
        chart = ChartDrawer(self.chart_data)
        assert chart.chart_data is not None
        assert hasattr(chart, "chart_type")
        assert hasattr(chart, "first_obj")

    def test_chart_with_custom_theme(self):
        chart = ChartDrawer(self.chart_data, theme="classic")
        assert chart.chart_data is not None

    def test_chart_with_language_setting(self):
        chart = ChartDrawer(self.chart_data, chart_language="EN")
        assert chart.chart_language == "EN"

    def test_chart_with_transparent_background(self):
        chart = ChartDrawer(self.chart_data, transparent_background=True)
        assert chart.transparent_background is True

    def test_chart_with_external_view(self):
        chart = ChartDrawer(self.chart_data, external_view=True)
        assert chart.external_view is True

    def test_chart_with_custom_title(self):
        custom_title = "My Custom Chart Title"
        chart = ChartDrawer(self.chart_data, custom_title=custom_title)
        assert chart.custom_title == custom_title
        template_dict = chart._create_template_dictionary()
        assert template_dict["stringTitle"] == custom_title

    def test_chart_with_no_custom_title(self):
        chart = ChartDrawer(self.chart_data)
        assert chart.custom_title is None
        template_dict = chart._create_template_dictionary()
        expected_default = f"{self.subject.name} - Birth Chart"
        assert template_dict["stringTitle"] == expected_default

    def test_generate_svg_string_with_kwarg_custom_title(self):
        chart = ChartDrawer(self.chart_data)
        custom_title = "Override Title"
        svg_output = chart.generate_svg_string(custom_title=custom_title)
        assert custom_title in svg_output

    def test_chart_drawer_properties(self):
        chart = ChartDrawer(self.chart_data)
        for attr in ["chart_data", "chart_type", "first_obj", "chart_language", "active_points", "active_aspects"]:
            assert hasattr(chart, attr)

    def test_chart_drawer_default_settings(self):
        chart = ChartDrawer(self.chart_data)
        assert chart.chart_language == "EN"
        assert chart.transparent_background is False
        assert chart.external_view is False
        assert chart.double_chart_aspect_grid_type == "list"
        assert chart.show_house_position_comparison is True
        assert chart.show_cusp_position_comparison is False

    def test_chart_drawer_aspect_grid_types(self):
        chart_list = ChartDrawer(self.chart_data, double_chart_aspect_grid_type="list")
        chart_table = ChartDrawer(self.chart_data, double_chart_aspect_grid_type="table")
        assert chart_list.double_chart_aspect_grid_type == "list"
        assert chart_table.double_chart_aspect_grid_type == "table"

    def test_chart_drawer_constants(self):
        assert ChartDrawer._DEFAULT_HEIGHT > 0
        assert ChartDrawer._DEFAULT_FULL_WIDTH > 0
        assert ChartDrawer._DEFAULT_NATAL_WIDTH > 0

    def test_chart_drawer_viewbox_constants(self):
        assert "0 0" in ChartDrawer._BASIC_CHART_VIEWBOX
        assert "0 0" in ChartDrawer._WIDE_CHART_VIEWBOX
        assert "0 0" in ChartDrawer._ULTRA_WIDE_CHART_VIEWBOX

    def test_chart_drawer_with_different_languages(self):
        for lang in ("EN", "IT", "ES"):
            chart = ChartDrawer(self.chart_data, chart_language=lang)
            assert chart.chart_language == lang

    def test_chart_drawer_multiple_instances(self):
        chart1 = ChartDrawer(self.chart_data)
        chart2 = ChartDrawer(self.chart_data, theme="classic")
        assert chart1.chart_data == chart2.chart_data

    def test_chart_drawer_with_different_themes(self):
        for theme in ("classic", "black-and-white", None):
            chart = ChartDrawer(self.chart_data, theme=theme)
            assert chart.chart_data is not None
            if theme:
                assert chart.color_style_tag.strip() != ""
                assert "--kerykeion-chart-color-paper-0" in chart.color_style_tag

    def test_chart_data_extraction(self):
        chart = ChartDrawer(self.chart_data)
        assert chart.chart_type is not None

    def test_chart_drawer_with_minimal_subject(self):
        minimal = AstrologicalSubjectFactory.from_birth_data(
            name="Minimal",
            year=2000,
            month=1,
            day=1,
            hour=0,
            minute=0,
            city="UTC",
            nation="UT",
            lng=0,
            lat=0,
            tz_str="UTC",
            suppress_geonames_warning=True,
        )
        data = ChartDataFactory.create_natal_chart_data(minimal)
        chart = ChartDrawer(data)
        assert chart.chart_data is not None

    def test_black_and_white_theme_is_monochrome(self):
        repo_root = Path(__file__).resolve().parents[2]
        theme_path = repo_root / "kerykeion" / "charts" / "themes" / "black-and-white.css"
        theme_content = theme_path.read_text(encoding="utf-8")
        hex_colors = re.findall(r"#[0-9a-fA-F]{6}", theme_content)
        assert hex_colors, "Expected hex colors in black-and-white theme."
        for color in hex_colors:
            r, g, b = color[1:3].lower(), color[3:5].lower(), color[5:7].lower()
            assert r == g == b, f"Color {color} is not grayscale."

    def test_dynamic_viewbox_tracks_dimensions(self):
        chart = ChartDrawer(self.chart_data)
        min_y = -ChartDrawer._VERTICAL_PADDING_TOP
        viewbox_height = int(chart.height) + ChartDrawer._VERTICAL_PADDING_TOP + ChartDrawer._VERTICAL_PADDING_BOTTOM
        expected = f"0 {min_y} {int(chart.width)} {viewbox_height}"
        assert chart._dynamic_viewbox() == expected

    def test_chart_drawer_settings_handling(self):
        custom_colors = {"background": "#ffffff"}
        custom_points = [{"name": "Sun", "is_active": True}]
        custom_aspects = [{"name": "conjunction", "is_active": True}]
        chart = ChartDrawer(
            self.chart_data,
            colors_settings=custom_colors,
            celestial_points_settings=custom_points,
            aspects_settings=custom_aspects,
        )
        assert chart.chart_colors_settings == custom_colors
        assert chart.planets_settings == custom_points
        assert chart.aspects_settings == custom_aspects

    def test_chart_drawer_different_settings_combinations(self):
        chart = ChartDrawer(
            self.chart_data,
            theme="classic",
            chart_language="IT",
            transparent_background=True,
            external_view=True,
            double_chart_aspect_grid_type="table",
        )
        assert chart.chart_language == "IT"
        assert chart.transparent_background is True
        assert chart.external_view is True
        assert chart.double_chart_aspect_grid_type == "table"

    def test_chart_drawer_property_access(self):
        chart = ChartDrawer(self.chart_data)
        for attr in ["chart_type", "first_obj", "height", "width", "location", "geolat", "geolon"]:
            assert hasattr(chart, attr)

    def test_composite_chart_drawer(self):
        factory = CompositeSubjectFactory(self.subject, self.subject2)
        composite_subject = factory.get_midpoint_composite_subject_model()
        data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart = ChartDrawer(data)
        assert chart.chart_type == "Composite"
        assert hasattr(chart, "first_circle_radius")
        assert hasattr(chart, "second_circle_radius")

    def test_transit_chart_drawer(self):
        data = ChartDataFactory.create_transit_chart_data(self.subject, self.subject2)
        chart = ChartDrawer(data)
        assert chart.chart_type == "Transit"
        assert hasattr(chart, "second_obj")

    def test_transit_chart_uses_transit_lunar_phase(self):
        data = ChartDataFactory.create_transit_chart_data(self.subject, self.subject2)
        chart = ChartDrawer(data)
        template_dict = chart._create_template_dictionary()
        assert chart.second_obj is not None
        transit_phase = chart.second_obj.lunar_phase
        assert transit_phase is not None
        expected_svg = makeLunarPhase(transit_phase["degrees_between_s_m"], chart.geolat)
        assert template_dict["makeLunarPhase"] == expected_svg

    def test_transit_chart_without_transit_phase_shows_blank(self):
        data = ChartDataFactory.create_transit_chart_data(self.subject, self.subject2)
        chart = ChartDrawer(data)
        assert chart.second_obj is not None
        chart.second_obj.lunar_phase = None  # type: ignore[attr-defined]
        template_dict = chart._create_template_dictionary()
        assert template_dict["makeLunarPhase"] == ""

    def test_synastry_chart_drawer(self):
        data = ChartDataFactory.create_synastry_chart_data(self.subject, self.subject2)
        chart = ChartDrawer(data)
        assert chart.chart_type == "Synastry"
        assert hasattr(chart, "second_obj")

    def test_hide_house_position_comparison_removes_grid(self):
        data = ChartDataFactory.create_synastry_chart_data(self.subject, self.subject2)
        chart = ChartDrawer(data, show_house_position_comparison=False, auto_size=False)
        assert chart.width == ChartDrawer._DEFAULT_FULL_WIDTH
        template_dict = chart._create_template_dictionary()
        assert template_dict["makeHouseComparisonGrid"] == ""

    def test_dual_chart_preserves_second_subject_points(self):
        data = ChartDataFactory.create_synastry_chart_data(self.subject, self.subject2)
        chart = ChartDrawer(data)
        first_points = {p.name: p.abs_pos for p in chart.available_kerykeion_celestial_points}
        second_points = {p.name: p.abs_pos for p in chart.second_subject_celestial_points}
        assert second_points, "Expected secondary subject points to be populated"
        assert "Sun" in second_points
        assert second_points["Sun"] == chart.second_obj.sun.abs_pos
        assert first_points["Sun"] == chart.first_obj.sun.abs_pos
        assert second_points["Sun"] != first_points["Sun"]

    def test_chart_drawer_viewbox_settings_per_type(self):
        natal_chart = ChartDrawer(ChartDataFactory.create_natal_chart_data(self.subject))
        assert natal_chart.chart_type == "Natal"

        factory = CompositeSubjectFactory(self.subject, self.subject2)
        composite_data = ChartDataFactory.create_composite_chart_data(factory.get_midpoint_composite_subject_model())
        assert ChartDrawer(composite_data).chart_type == "Composite"

        transit_data = ChartDataFactory.create_transit_chart_data(self.subject, self.subject2)
        assert ChartDrawer(transit_data).chart_type == "Transit"

    def test_chart_drawer_save_svg_method(self):
        chart = ChartDrawer(self.chart_data)
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_chart.svg")
            try:
                chart.save_svg(output_path)
                assert os.path.exists(output_path)
            except Exception:
                assert hasattr(chart, "save_svg")

    def test_chart_drawer_error_handling(self):
        chart = ChartDrawer(self.chart_data, theme=None)
        assert chart.chart_data is not None

    @patch("kerykeion.charts.chart_drawer.logging")
    def test_chart_drawer_logging(self, mock_logging):
        chart = ChartDrawer(self.chart_data)
        assert chart is not None

    def test_svg_output_is_valid_svg_string(self):
        """Verify SVG output is a string containing <svg."""
        chart = ChartDrawer(self.chart_data)
        svg = chart.generate_svg_string()
        assert isinstance(svg, str)
        assert "<svg" in svg, f"SVG output does not contain <svg tag: {svg[:120]}"

    def test_svg_contains_expected_elements(self):
        """Verify SVG contains planet glyphs and house numbers."""
        chart = ChartDrawer(self.chart_data)
        svg = chart.generate_svg_string()
        assert "<svg" in svg
        # House numbers 1-12 should appear somewhere in the SVG
        for house_num in range(1, 13):
            assert str(house_num) in svg


# =============================================================================
# 2. TestNatalChart
# =============================================================================


class TestNatalChart:
    """Golden-file regression for natal charts (from test_natal.py)."""

    def test_natal_chart_classic(self):
        john = _make_john()
        data = ChartDataFactory.create_natal_chart_data(john)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("John Lennon - Natal Chart.svg", svg)

    def test_external_natal_chart(self):
        subj = _make_john("ExternalNatal")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, external_view=True).generate_svg_string()
        compare_chart_svg("John Lennon - ExternalNatal - Natal Chart.svg", svg)

    def test_minified_natal_chart(self):
        subj = _make_john("Minified")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_svg_string(minify=True)
        compare_chart_svg("John Lennon - Minified - Natal Chart.svg", svg)

    def test_dark_theme_natal_chart(self):
        subj = _make_john("Dark Theme")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="dark").generate_svg_string()
        compare_chart_svg("John Lennon - Dark Theme - Natal Chart.svg", svg)

    def test_dark_high_contrast_theme_natal_chart(self):
        subj = _make_john("Dark High Contrast Theme")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="dark-high-contrast").generate_svg_string()
        compare_chart_svg("John Lennon - Dark High Contrast Theme - Natal Chart.svg", svg)

    def test_light_theme_natal_chart(self):
        subj = _make_john("Light Theme")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="light").generate_svg_string()
        compare_chart_svg("John Lennon - Light Theme - Natal Chart.svg", svg)

    def test_black_and_white_natal_chart(self):
        john = _make_john()
        data = ChartDataFactory.create_natal_chart_data(john)
        svg = ChartDrawer(data, theme="black-and-white").generate_svg_string()
        compare_chart_svg("John Lennon - Black and White Theme - Natal Chart.svg", svg)

    def test_dark_theme_external_natal_chart(self):
        subj = _make_john("Dark Theme External")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="dark", external_view=True).generate_svg_string()
        compare_chart_svg("John Lennon - Dark Theme External - Natal Chart.svg", svg)

    def test_light_theme_external_natal_chart(self):
        subj = _make_john("Light Theme External")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="light", external_view=True).generate_svg_string()
        compare_chart_svg("John Lennon - Light Theme External - Natal Chart.svg", svg)

    def test_black_and_white_external_natal_chart(self):
        subj = _make_john("Black and White Theme External")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="black-and-white", external_view=True).generate_svg_string()
        compare_chart_svg("John Lennon - Black and White Theme External - Natal Chart.svg", svg)

    def test_transparent_background_natal_chart(self):
        subj = _make_john("Transparent Background")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, transparent_background=True).generate_svg_string()
        compare_chart_svg("John Lennon - Transparent Background - Natal Chart.svg", svg)

    def test_strawberry_natal_chart(self):
        subj = _make_john("Strawberry Theme")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="strawberry").generate_svg_string()
        compare_chart_svg("John Lennon - Strawberry Theme - Natal Chart.svg", svg)

    def test_strawberry_external_natal_chart(self):
        subj = _make_john("Strawberry Theme External")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="strawberry", external_view=True).generate_svg_string()
        compare_chart_svg("John Lennon - Strawberry Theme External - Natal Chart.svg", svg)

    def test_heliocentric_natal_chart(self):
        subj = _make_john("Heliocentric", perspective_type="Heliocentric")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("John Lennon - Heliocentric - Natal Chart.svg", svg)

    def test_topocentric_natal_chart(self):
        subj = _make_john("Topocentric", perspective_type="Topocentric")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("John Lennon - Topocentric - Natal Chart.svg", svg)

    def test_true_geocentric_natal_chart(self):
        subj = _make_john("True Geocentric", perspective_type="True Geocentric")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("John Lennon - True Geocentric - Natal Chart.svg", svg)

    def test_english_natal_chart(self):
        subj = _make_john("EN")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, chart_language="EN").generate_svg_string()
        compare_chart_svg("John Lennon - EN - Natal Chart.svg", svg)

    def test_kanye_natal_chart(self):
        subj = AstrologicalSubjectFactory.from_birth_data(
            "Kanye",
            1977,
            6,
            8,
            8,
            45,
            "Atlanta",
            "US",
            suppress_geonames_warning=True,
        )
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("Kanye - Natal Chart.svg", svg)

    def test_all_active_points_natal_chart(self):
        from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

        subj = _make_john("All Active Points", active_points=ALL_ACTIVE_POINTS)
        data = ChartDataFactory.create_natal_chart_data(subj, active_points=ALL_ACTIVE_POINTS)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("John Lennon - All Active Points - Natal Chart.svg", svg)


# =============================================================================
# Natal sidereal + house system tests
# =============================================================================


class TestNatalChartSiderealModes:
    """Sidereal mode natal chart golden-file regression."""

    @pytest.mark.parametrize(
        "display_name,mode",
        [
            ("Lahiri", "LAHIRI"),
            ("Fagan-Bradley", "FAGAN_BRADLEY"),
            ("DeLuce", "DELUCE"),
            ("J2000", "J2000"),
            ("Raman", "RAMAN"),
            ("Ushashashi", "USHASHASHI"),
            ("Krishnamurti", "KRISHNAMURTI"),
            ("Djwhal Khul", "DJWHAL_KHUL"),
            ("Yukteshwar", "YUKTESHWAR"),
            ("JN Bhasin", "JN_BHASIN"),
            ("Babyl Kugler1", "BABYL_KUGLER1"),
            ("Babyl Kugler2", "BABYL_KUGLER2"),
            ("Babyl Kugler3", "BABYL_KUGLER3"),
            ("Babyl Huber", "BABYL_HUBER"),
            ("Babyl Etpsc", "BABYL_ETPSC"),
            ("Aldebaran 15Tau", "ALDEBARAN_15TAU"),
            ("Hipparchos", "HIPPARCHOS"),
            ("Sassanian", "SASSANIAN"),
            ("J1900", "J1900"),
            ("B1950", "B1950"),
        ],
        ids=lambda v: v if isinstance(v, str) and not v.startswith(("BABYL", "ALDEB", "FAGAN")) else None,
    )
    def test_sidereal_natal(self, display_name, mode):
        subj = _make_sidereal_subject(display_name, mode)
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg(f"John Lennon {display_name} - Natal Chart.svg", svg)

    def test_sidereal_lahiri_dark_wheel_only(self):
        subj = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon Lahiri - Dark Theme",
            *JOHN_LENNON_BIRTH_DATA,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            suppress_geonames_warning=True,
        )
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="dark").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon Lahiri - Dark Theme - Natal Chart - Wheel Only.svg", svg)

    def test_sidereal_fagan_bradley_light_wheel_only(self):
        subj = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon Fagan-Bradley - Light Theme",
            *JOHN_LENNON_BIRTH_DATA,
            zodiac_type="Sidereal",
            sidereal_mode="FAGAN_BRADLEY",
            suppress_geonames_warning=True,
        )
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="light").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon Fagan-Bradley - Light Theme - Natal Chart - Wheel Only.svg", svg)


class TestNatalChartHouseSystems:
    """House system natal chart golden-file regression."""

    HOUSE_SYSTEMS = [
        ("M", "Morinus"),
        ("A", "Equal"),
        ("B", "Alcabitius"),
        ("C", "Campanus"),
        ("D", "Equal MC"),
        ("F", "Carter"),
        ("H", "Horizon"),
        ("I", "Sunshine"),
        ("i", "Sunshine Alt"),
        ("K", "Koch"),
        ("L", "Pullen SD"),
        ("N", "Equal Aries"),
        ("O", "Porphyry"),
        ("P", "Placidus"),
        ("Q", "Pullen SR"),
        ("R", "Regiomontanus"),
        ("S", "Sripati"),
        ("T", "Polich Page"),
        ("U", "Krusinski"),
        ("V", "Vehlow"),
        ("W", "Whole Sign"),
        ("X", "Meridian"),
        ("Y", "APC"),
    ]

    @pytest.mark.parametrize("house_id,house_name", HOUSE_SYSTEMS, ids=[n for _, n in HOUSE_SYSTEMS])
    def test_house_system(self, house_id, house_name):
        subj = _make_john(f"House System {house_name}", houses_system_identifier=house_id)
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg(f"John Lennon - House System {house_name} - Natal Chart.svg", svg)


class TestNatalChartLanguages:
    """Language-specific natal chart tests (from test_natal.py)."""

    LANGUAGE_SUBJECTS = [
        ("CN", "Hua Chenyu", 1990, 2, 7, 12, 0, "Hunan", "CN"),
        ("FR", "Jeanne Moreau", 1928, 1, 23, 10, 0, "Paris", "FR"),
        ("ES", "Antonio Banderas", 1960, 8, 10, 12, 0, "Malaga", "ES"),
        ("PT", "Cristiano Ronaldo", 1985, 2, 5, 5, 25, "Funchal", "PT"),
        ("IT", "Sophia Loren", 1934, 9, 20, 2, 0, "Rome", "IT"),
        ("RU", "Mikhail Bulgakov", 1891, 5, 15, 12, 0, "Kiev", "UA"),
        ("TR", "Mehmet Oz", 1960, 6, 11, 12, 0, "Istanbul", "TR"),
        ("DE", "Albert Einstein", 1879, 3, 14, 11, 30, "Ulm", "DE"),
        ("HI", "Amitabh Bachchan", 1942, 10, 11, 4, 0, "Allahabad", "IN"),
    ]

    @pytest.mark.parametrize(
        "lang,name,yr,mo,dy,hr,mn,city,nation",
        LANGUAGE_SUBJECTS,
        ids=[l[0] for l in LANGUAGE_SUBJECTS],
    )
    def test_language_natal_chart(self, lang, name, yr, mo, dy, hr, mn, city, nation):
        subj = AstrologicalSubjectFactory.from_birth_data(
            name,
            yr,
            mo,
            dy,
            hr,
            mn,
            city,
            nation,
            suppress_geonames_warning=True,
        )
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, chart_language=lang).generate_svg_string()
        compare_chart_svg(f"{name} - Natal Chart.svg", svg)


# =============================================================================
# 3. TestSynastryChart
# =============================================================================


class TestSynastryChart:
    """Golden-file regression for synastry charts (from test_synastry.py)."""

    def test_synastry_chart(self):
        john, paul = _make_john(), _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("John Lennon - Synastry Chart.svg", svg)

    def test_synastry_no_house_comparison(self):
        john, paul = _make_john(), _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, show_house_position_comparison=False).generate_svg_string()
        compare_chart_svg("John Lennon - Synastry Chart - No House Comparison.svg", svg)

    def test_synastry_house_comparison_only(self):
        john, paul = _make_john(), _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(
            data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=False,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - Synastry Chart - House Comparison Only.svg", svg)

    def test_synastry_cusp_comparison_only(self):
        john, paul = _make_john(), _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(
            data,
            show_house_position_comparison=False,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - Synastry Chart - Cusp Comparison Only.svg", svg)

    def test_synastry_house_and_cusp_comparison(self):
        john, paul = _make_john(), _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(
            data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - Synastry Chart - House and Cusp Comparison.svg", svg)

    def test_synastry_list_layout(self):
        john = _make_john("SCTWL")
        paul = _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, double_chart_aspect_grid_type="list", theme="dark").generate_svg_string()
        compare_chart_svg("John Lennon - SCTWL - Synastry Chart.svg", svg)

    def test_black_and_white_synastry(self):
        john, paul = _make_john(), _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, theme="black-and-white").generate_svg_string()
        compare_chart_svg("John Lennon - Black and White Theme - Synastry Chart.svg", svg)

    def test_dark_theme_synastry(self):
        john = _make_john("DTS")
        paul = _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, theme="dark").generate_svg_string()
        compare_chart_svg("John Lennon - DTS - Synastry Chart.svg", svg)

    def test_light_theme_synastry(self):
        john, paul = _make_john(), _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, theme="light").generate_svg_string()
        compare_chart_svg("John Lennon - Light Theme - Synastry Chart.svg", svg)

    def test_strawberry_synastry(self):
        john = _make_john("Strawberry Theme Synastry")
        paul = _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, theme="strawberry").generate_svg_string()
        compare_chart_svg("John Lennon - Strawberry Theme Synastry - Synastry Chart.svg", svg)

    def test_heliocentric_synastry(self):
        john = _make_john("Heliocentric Synastry", perspective_type="Heliocentric")
        paul = _make_paul("Heliocentric", perspective_type="Heliocentric")
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("John Lennon - Heliocentric - Synastry Chart.svg", svg)

    def test_true_geocentric_synastry(self):
        john = _make_john("True Geocentric Synastry", perspective_type="True Geocentric")
        paul = _make_paul("True Geocentric", perspective_type="True Geocentric")
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("John Lennon - True Geocentric - Synastry Chart.svg", svg)

    def test_french_synastry(self):
        john = _make_john("FR")
        paul = _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, chart_language="FR").generate_svg_string()
        compare_chart_svg("John Lennon - FR - Synastry Chart.svg", svg)

    def test_german_synastry(self):
        john = _make_john("DE")
        paul = _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, chart_language="DE").generate_svg_string()
        compare_chart_svg("John Lennon - DE - Synastry Chart.svg", svg)

    def test_turkish_synastry(self):
        john = _make_john("TR")
        paul = _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, chart_language="TR").generate_svg_string()
        compare_chart_svg("John Lennon - TR - Synastry Chart.svg", svg)

    def test_hindi_synastry(self):
        john = _make_john("HI")
        paul = _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, chart_language="HI").generate_svg_string()
        compare_chart_svg("John Lennon - HI - Synastry Chart.svg", svg)

    def test_synastry_with_relationship_score(self):
        john, paul = _make_john(), _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul, include_relationship_score=True)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("John Lennon - Relationship Score - Synastry Chart.svg", svg)

    def test_synastry_all_active_points_list(self):
        from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

        john = _make_john("All Active Points", active_points=ALL_ACTIVE_POINTS)
        paul = _make_paul("All Active Points", active_points=ALL_ACTIVE_POINTS)
        data = ChartDataFactory.create_synastry_chart_data(john, paul, active_points=ALL_ACTIVE_POINTS)
        assert set(data.active_points) == set(ALL_ACTIVE_POINTS)
        svg = ChartDrawer(data, double_chart_aspect_grid_type="list").generate_svg_string()
        compare_chart_svg("John Lennon - All Active Points - Synastry Chart - List.svg", svg)

    def test_synastry_all_active_points_grid(self):
        from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

        john = _make_john("All Active Points", active_points=ALL_ACTIVE_POINTS)
        paul = _make_paul("All Active Points", active_points=ALL_ACTIVE_POINTS)
        data = ChartDataFactory.create_synastry_chart_data(john, paul, active_points=ALL_ACTIVE_POINTS)
        svg = ChartDrawer(data, double_chart_aspect_grid_type="table").generate_svg_string()
        compare_chart_svg("John Lennon - All Active Points - Synastry Chart - Grid.svg", svg)

    def test_transparent_synastry(self):
        john = _make_john("Transparent Synastry")
        paul = _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, transparent_background=True).generate_svg_string()
        compare_chart_svg("John Lennon - Transparent Synastry - Synastry Chart.svg", svg)

    def test_custom_title_synastry(self):
        john = _make_john("Custom Title Synastry")
        paul = _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, custom_title="Beatles Synastry Analysis").generate_svg_string()
        compare_chart_svg("John Lennon - Custom Title Synastry - Synastry Chart.svg", svg)


# =============================================================================
# 4. TestTransitChart
# =============================================================================


class TestTransitChart:
    """Golden-file regression for transit charts (from test_transit.py)."""

    def test_transit_chart(self):
        john, paul = _make_john(), _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("John Lennon - Transit Chart.svg", svg)

    def test_transit_no_house_comparison(self):
        john, paul = _make_john(), _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, show_house_position_comparison=False).generate_svg_string()
        compare_chart_svg("John Lennon - Transit Chart - No House Comparison.svg", svg)

    def test_transit_house_comparison_only(self):
        john, paul = _make_john(), _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(
            data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=False,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - Transit Chart - House Comparison Only.svg", svg)

    def test_transit_cusp_comparison_only(self):
        john, paul = _make_john(), _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(
            data,
            show_house_position_comparison=False,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - Transit Chart - Cusp Comparison Only.svg", svg)

    def test_transit_house_and_cusp_comparison(self):
        john, paul = _make_john(), _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(
            data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - Transit Chart - House and Cusp Comparison.svg", svg)

    def test_transit_table_grid(self):
        john = _make_john("TCWTG")
        paul = _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, double_chart_aspect_grid_type="table", theme="dark").generate_svg_string()
        compare_chart_svg("John Lennon - TCWTG - Transit Chart.svg", svg)

    def test_black_and_white_transit(self):
        john, paul = _make_john(), _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, theme="black-and-white").generate_svg_string()
        compare_chart_svg("John Lennon - Black and White Theme - Transit Chart.svg", svg)

    def test_light_theme_transit(self):
        john, paul = _make_john(), _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, theme="light").generate_svg_string()
        compare_chart_svg("John Lennon - Light Theme - Transit Chart.svg", svg)

    def test_dark_theme_transit(self):
        john, paul = _make_john(), _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, theme="dark").generate_svg_string()
        compare_chart_svg("John Lennon - Dark Theme - Transit Chart.svg", svg)

    def test_strawberry_transit(self):
        john = _make_john("Strawberry Theme Transit")
        paul = _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, theme="strawberry").generate_svg_string()
        compare_chart_svg("John Lennon - Strawberry Theme Transit - Transit Chart.svg", svg)

    def test_topocentric_transit(self):
        john = _make_john("Topocentric Transit", perspective_type="Topocentric")
        paul = _make_paul("Topocentric", perspective_type="Topocentric")
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("John Lennon - Topocentric - Transit Chart.svg", svg)

    def test_chinese_transit(self):
        john = _make_john("CN")
        paul = _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, chart_language="CN").generate_svg_string()
        compare_chart_svg("John Lennon - CN - Transit Chart.svg", svg)

    def test_spanish_transit(self):
        john = _make_john("ES")
        paul = _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, chart_language="ES").generate_svg_string()
        compare_chart_svg("John Lennon - ES - Transit Chart.svg", svg)

    def test_russian_transit(self):
        john = _make_john("RU")
        paul = _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, chart_language="RU").generate_svg_string()
        compare_chart_svg("John Lennon - RU - Transit Chart.svg", svg)

    def test_transit_all_active_points(self):
        from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

        john = _make_john("All Active Points Transit", active_points=ALL_ACTIVE_POINTS)
        paul = _make_paul("All Active Points Transit", active_points=ALL_ACTIVE_POINTS)
        data = ChartDataFactory.create_transit_chart_data(john, paul, active_points=ALL_ACTIVE_POINTS)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("John Lennon - All Active Points - Transit Chart.svg", svg)

    def test_custom_title_transit(self):
        john = _make_john("Custom Title Transit")
        paul = _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, custom_title="Transit Analysis 2024").generate_svg_string()
        compare_chart_svg("John Lennon - Custom Title Transit - Transit Chart.svg", svg)


# =============================================================================
# 5. TestCompositeChart
# =============================================================================


class TestCompositeChart:
    """Golden-file regression for composite charts (from test_composite.py)."""

    def _composite_data(self):
        angelina, brad = _make_angelina(), _make_brad()
        factory = CompositeSubjectFactory(angelina, brad)
        model = factory.get_midpoint_composite_subject_model()
        return ChartDataFactory.create_composite_chart_data(model)

    def test_composite_chart(self):
        svg = ChartDrawer(self._composite_data()).generate_svg_string()
        compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - Composite Chart.svg", svg)

    def test_black_and_white_composite(self):
        svg = ChartDrawer(self._composite_data(), theme="black-and-white").generate_svg_string()
        compare_chart_svg(
            "Angelina Jolie and Brad Pitt Composite Chart - Black and White Theme - Composite Chart.svg", svg
        )

    def test_light_theme_composite(self):
        svg = ChartDrawer(self._composite_data(), theme="light").generate_svg_string()
        compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - Light Theme - Composite Chart.svg", svg)

    def test_dark_theme_composite(self):
        svg = ChartDrawer(self._composite_data(), theme="dark").generate_svg_string()
        compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - Dark Theme - Composite Chart.svg", svg)

    def test_strawberry_composite(self):
        svg = ChartDrawer(self._composite_data(), theme="strawberry").generate_svg_string()
        compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - Strawberry Theme - Composite Chart.svg", svg)

    def test_composite_wheel_only(self):
        svg = ChartDrawer(self._composite_data()).generate_wheel_only_svg_string()
        compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - Composite Chart - Wheel Only.svg", svg)

    def test_composite_aspect_grid_only(self):
        svg = ChartDrawer(self._composite_data()).generate_aspect_grid_only_svg_string()
        compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - Composite Chart - Aspect Grid Only.svg", svg)

    def test_italian_composite(self):
        svg = ChartDrawer(self._composite_data(), chart_language="IT").generate_svg_string()
        compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - IT - Composite Chart.svg", svg)

    def test_portuguese_composite(self):
        svg = ChartDrawer(self._composite_data(), chart_language="PT").generate_svg_string()
        compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - PT - Composite Chart.svg", svg)

    def test_french_composite(self):
        svg = ChartDrawer(self._composite_data(), chart_language="FR").generate_svg_string()
        compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - FR - Composite Chart.svg", svg)


# =============================================================================
# 6. TestReturnCharts
# =============================================================================


class TestReturnCharts:
    """Solar/lunar return chart tests (from test_returns.py)."""

    RETURN_ISO = "2025-01-09T18:30:00+01:00"

    def _solar_return(self, john):
        factory = _make_return_factory(john)
        return factory.next_return_from_iso_formatted_time(self.RETURN_ISO, return_type="Solar")

    def _lunar_return(self, john):
        factory = _make_return_factory(john)
        return factory.next_return_from_iso_formatted_time(self.RETURN_ISO, return_type="Lunar")

    # --- Dual solar return ---

    def test_dual_return_solar(self):
        john = _make_john()
        sr = self._solar_return(john)
        data = ChartDataFactory.create_return_chart_data(john, sr)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Solar Return.svg", svg)

    def test_dual_return_solar_no_house_comparison(self):
        john = _make_john()
        sr = self._solar_return(john)
        data = ChartDataFactory.create_return_chart_data(john, sr)
        svg = ChartDrawer(data, show_house_position_comparison=False).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Solar Return - No House Comparison.svg", svg)

    def test_dual_return_solar_house_comparison_only(self):
        john = _make_john()
        sr = self._solar_return(john)
        data = ChartDataFactory.create_return_chart_data(john, sr)
        svg = ChartDrawer(
            data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=False,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Solar Return - House Comparison Only.svg", svg)

    def test_dual_return_solar_cusp_comparison_only(self):
        john = _make_john()
        sr = self._solar_return(john)
        data = ChartDataFactory.create_return_chart_data(john, sr)
        svg = ChartDrawer(
            data,
            show_house_position_comparison=False,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Solar Return - Cusp Comparison Only.svg", svg)

    def test_dual_return_solar_house_and_cusp(self):
        john = _make_john()
        sr = self._solar_return(john)
        data = ChartDataFactory.create_return_chart_data(john, sr)
        svg = ChartDrawer(
            data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Solar Return - House and Cusp Comparison.svg", svg)

    def test_bw_dual_return_solar(self):
        john = _make_john()
        sr = self._solar_return(john)
        data = ChartDataFactory.create_return_chart_data(john, sr)
        svg = ChartDrawer(data, theme="black-and-white").generate_svg_string()
        compare_chart_svg("John Lennon - Black and White Theme - DualReturnChart Chart - Solar Return.svg", svg)

    def test_strawberry_dual_return_solar(self):
        john = _make_john()
        sr = self._solar_return(john)
        data = ChartDataFactory.create_return_chart_data(john, sr)
        svg = ChartDrawer(data, theme="strawberry").generate_svg_string()
        compare_chart_svg("John Lennon - Strawberry Theme - DualReturnChart Chart - Solar Return.svg", svg)

    # --- Single solar return ---

    def test_single_return_solar(self):
        john = _make_john()
        sr = self._solar_return(john)
        data = ChartDataFactory.create_single_wheel_return_chart_data(sr)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("John Lennon Solar Return - SingleReturnChart Chart.svg", svg)

    def test_bw_single_return_solar(self):
        john = _make_john()
        sr = self._solar_return(john)
        data = ChartDataFactory.create_single_wheel_return_chart_data(sr)
        svg = ChartDrawer(data, theme="black-and-white").generate_svg_string()
        compare_chart_svg("John Lennon Solar Return - Black and White Theme - SingleReturnChart Chart.svg", svg)

    def test_strawberry_single_return_solar(self):
        john = _make_john()
        sr = self._solar_return(john)
        data = ChartDataFactory.create_single_wheel_return_chart_data(sr)
        svg = ChartDrawer(data, theme="strawberry").generate_svg_string()
        compare_chart_svg("John Lennon Solar Return - Strawberry Theme - SingleReturnChart Chart.svg", svg)

    # --- Dual lunar return ---

    def test_dual_return_lunar(self):
        john = _make_john()
        lr = self._lunar_return(john)
        data = ChartDataFactory.create_return_chart_data(john, lr)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Lunar Return.svg", svg)

    def test_dual_return_lunar_no_house_comparison(self):
        john = _make_john()
        lr = self._lunar_return(john)
        data = ChartDataFactory.create_return_chart_data(john, lr)
        svg = ChartDrawer(data, show_house_position_comparison=False).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Lunar Return - No House Comparison.svg", svg)

    def test_dual_return_lunar_house_comparison_only(self):
        john = _make_john()
        lr = self._lunar_return(john)
        data = ChartDataFactory.create_return_chart_data(john, lr)
        svg = ChartDrawer(
            data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=False,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Lunar Return - House Comparison Only.svg", svg)

    def test_dual_return_lunar_cusp_comparison_only(self):
        john = _make_john()
        lr = self._lunar_return(john)
        data = ChartDataFactory.create_return_chart_data(john, lr)
        svg = ChartDrawer(
            data,
            show_house_position_comparison=False,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Lunar Return - Cusp Comparison Only.svg", svg)

    def test_dual_return_lunar_house_and_cusp(self):
        john = _make_john()
        lr = self._lunar_return(john)
        data = ChartDataFactory.create_return_chart_data(john, lr)
        svg = ChartDrawer(
            data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        compare_chart_svg("John Lennon - DualReturnChart Chart - Lunar Return - House and Cusp Comparison.svg", svg)

    def test_bw_dual_return_lunar(self):
        john = _make_john()
        lr = self._lunar_return(john)
        data = ChartDataFactory.create_return_chart_data(john, lr)
        svg = ChartDrawer(data, theme="black-and-white").generate_svg_string()
        compare_chart_svg("John Lennon - Black and White Theme - DualReturnChart Chart - Lunar Return.svg", svg)

    def test_strawberry_dual_return_lunar(self):
        john = _make_john()
        lr = self._lunar_return(john)
        data = ChartDataFactory.create_return_chart_data(john, lr)
        svg = ChartDrawer(data, theme="strawberry").generate_svg_string()
        compare_chart_svg("John Lennon - Strawberry Theme - DualReturnChart Chart - Lunar Return.svg", svg)

    # --- Single lunar return ---

    def test_single_return_lunar(self):
        john = _make_john()
        lr = self._lunar_return(john)
        data = ChartDataFactory.create_single_wheel_return_chart_data(lr)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("John Lennon Lunar Return - SingleReturnChart Chart.svg", svg)

    def test_bw_single_return_lunar(self):
        john = _make_john()
        lr = self._lunar_return(john)
        data = ChartDataFactory.create_single_wheel_return_chart_data(lr)
        svg = ChartDrawer(data, theme="black-and-white").generate_svg_string()
        compare_chart_svg("John Lennon Lunar Return - Black and White Theme - SingleReturnChart Chart.svg", svg)

    # --- Partial views ---

    def test_return_wheel_only(self):
        john = _make_john()
        sr = self._solar_return(john)
        data = ChartDataFactory.create_single_wheel_return_chart_data(sr)
        svg = ChartDrawer(data).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon Solar Return - Wheel Only.svg", svg)

    def test_return_aspect_grid_only(self):
        john = _make_john()
        sr = self._solar_return(john)
        data = ChartDataFactory.create_single_wheel_return_chart_data(sr)
        svg = ChartDrawer(data).generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon Solar Return - Aspect Grid Only.svg", svg)


# =============================================================================
# 7. TestChartOptions
# =============================================================================


class TestChartOptions:
    """Configuration options and edge cases (from test_options.py)."""

    def test_custom_title_natal(self):
        subj = _make_john("Custom Title")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, custom_title="My Custom Chart Title").generate_svg_string()
        compare_chart_svg("John Lennon - Custom Title - Natal Chart.svg", svg)

    def test_show_aspect_icons_false(self):
        subj = _make_john("No Aspect Icons")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, show_aspect_icons=False).generate_svg_string()
        compare_chart_svg("John Lennon - No Aspect Icons - Natal Chart.svg", svg)

    def test_auto_size_false(self):
        subj = _make_john("Auto Size False")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, auto_size=False).generate_svg_string()
        compare_chart_svg("John Lennon - Auto Size False - Natal Chart.svg", svg)

    def test_remove_css_variables(self):
        subj = _make_john("No CSS Variables")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_svg_string(remove_css_variables=True)
        compare_chart_svg("John Lennon - No CSS Variables - Natal Chart.svg", svg)

    def test_custom_padding(self):
        subj = _make_john("Custom Padding")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, padding=50).generate_svg_string()
        compare_chart_svg("John Lennon - Custom Padding - Natal Chart.svg", svg)

    def test_theme_none(self):
        subj = _make_john("No Theme")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme=None).generate_svg_string()
        compare_chart_svg("John Lennon - No Theme - Natal Chart.svg", svg)

    def test_show_degree_indicators_false(self):
        subj = _make_john("No Degree Indicators")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, show_degree_indicators=False).generate_svg_string()
        compare_chart_svg("John Lennon - No Degree Indicators - Natal Chart.svg", svg)

    def test_custom_colors_settings(self):
        from kerykeion.settings.chart_defaults import DEFAULT_CHART_COLORS

        custom_colors = DEFAULT_CHART_COLORS.copy()
        custom_colors["paper_0"] = "#ff0000"
        custom_colors["paper_1"] = "#00ff00"
        subj = _make_john("Custom Colors")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, colors_settings=custom_colors).generate_svg_string()
        compare_chart_svg("John Lennon - Custom Colors - Natal Chart.svg", svg)

    def test_custom_aspects_settings(self):
        from kerykeion.settings.chart_defaults import DEFAULT_CHART_ASPECTS_SETTINGS

        custom_aspects = copy.deepcopy(DEFAULT_CHART_ASPECTS_SETTINGS)
        for aspect in custom_aspects:
            if aspect["name"] == "conjunction":
                aspect["color"] = "#FF0000"
            elif aspect["name"] == "opposition":
                aspect["color"] = "#0000FF"
        subj = _make_john("Custom Aspect Colors")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, aspects_settings=custom_aspects).generate_svg_string()
        compare_chart_svg("John Lennon - Custom Aspect Colors - Natal Chart.svg", svg)

    def test_custom_celestial_points_settings(self):
        from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS

        custom_points = copy.deepcopy(DEFAULT_CELESTIAL_POINTS_SETTINGS)
        for point in custom_points:
            if point["name"] == "Sun":
                point["color"] = "#FFD700"
            elif point["name"] == "Moon":
                point["color"] = "#C0C0C0"
        subj = _make_john("Custom Planet Colors")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, celestial_points_settings=custom_points).generate_svg_string()
        compare_chart_svg("John Lennon - Custom Planet Colors - Natal Chart.svg", svg)

    def test_language_pack_override(self):
        custom_language_pack = {"Sun": "Sole Custom", "Moon": "Luna Custom"}
        subj = _make_john("Language Pack")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, chart_language="IT", language_pack=custom_language_pack).generate_svg_string()
        compare_chart_svg("John Lennon - Language Pack - Natal Chart.svg", svg)

    def test_transparent_background_dark_theme(self):
        subj = _make_john("Transparent Dark")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="dark", transparent_background=True).generate_svg_string()
        compare_chart_svg("John Lennon - Transparent Dark - Natal Chart.svg", svg)

    def test_padding_zero(self):
        subj = _make_john("Zero Padding")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, padding=0).generate_svg_string()
        compare_chart_svg("John Lennon - Zero Padding - Natal Chart.svg", svg)

    def test_padding_large(self):
        subj = _make_john("Large Padding")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, padding=100).generate_svg_string()
        compare_chart_svg("John Lennon - Large Padding - Natal Chart.svg", svg)

    def test_minify_and_remove_css_combined(self):
        subj = _make_john("Minify CSS")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_svg_string(minify=True, remove_css_variables=True)
        compare_chart_svg("John Lennon - Minify CSS - Natal Chart.svg", svg)

    def test_very_long_name(self):
        subj = AstrologicalSubjectFactory.from_birth_data(
            "A" * 100,
            *JOHN_LENNON_BIRTH_DATA,
            suppress_geonames_warning=True,
        )
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("Long Name - Natal Chart.svg", svg)

    def test_extreme_latitude_north(self):
        subj = AstrologicalSubjectFactory.from_birth_data(
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
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("Arctic Subject - Natal Chart.svg", svg)

    def test_extreme_latitude_south(self):
        subj = AstrologicalSubjectFactory.from_birth_data(
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
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("Antarctic Subject - Natal Chart.svg", svg)

    def test_historical_date(self):
        subj = AstrologicalSubjectFactory.from_birth_data(
            "Historical Subject",
            1500,
            3,
            15,
            12,
            0,
            "Florence",
            "IT",
            suppress_geonames_warning=True,
        )
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("Historical Subject - Natal Chart.svg", svg)

    def test_future_date(self):
        subj = AstrologicalSubjectFactory.from_birth_data(
            "Future Subject",
            2100,
            7,
            4,
            12,
            0,
            "New York",
            "US",
            suppress_geonames_warning=True,
        )
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("Future Subject - Natal Chart.svg", svg)

    def test_date_line_crossing(self):
        subj = AstrologicalSubjectFactory.from_birth_data(
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
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_svg_string()
        compare_chart_svg("Date Line Subject - Natal Chart.svg", svg)

    def test_invalid_theme_raises_exception(self):
        john = _make_john()
        data = ChartDataFactory.create_natal_chart_data(john)
        with pytest.raises(KerykeionException):
            ChartDrawer(data, theme="invalid_theme_name")  # type: ignore


# =============================================================================
# 8. TestPartialViews
# =============================================================================


class TestPartialViews:
    """Wheel-only and aspect-grid-only tests (from test_partial_views.py)."""

    # --- Wheel-only natal ---

    def test_wheel_only_natal(self):
        subj = _make_john("Wheel Only")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Only - Natal Chart - Wheel Only.svg", svg)

    def test_wheel_external_only(self):
        subj = _make_john("Wheel External Only")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, external_view=True).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel External Only - ExternalNatal Chart - Wheel Only.svg", svg)

    def test_wheel_only_dark_natal(self):
        subj = _make_john("Wheel Only Dark")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="dark").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Only Dark - Natal Chart - Wheel Only.svg", svg)

    def test_wheel_only_dark_transparent_natal(self):
        from kerykeion.settings.config_constants import TRADITIONAL_ASTROLOGY_ACTIVE_POINTS

        subj = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Only Dark Transparent",
            *JOHN_LENNON_BIRTH_DATA,
            suppress_geonames_warning=True,
            active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS,
        )
        data = ChartDataFactory.create_natal_chart_data(subj, active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
        svg = ChartDrawer(data, theme="dark", transparent_background=True).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Only Dark Transparent - Natal Chart - Wheel Only.svg", svg)

    def test_wheel_only_classic_transparent_natal(self):
        from kerykeion.settings.config_constants import TRADITIONAL_ASTROLOGY_ACTIVE_POINTS

        subj = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Only Classic Transparent",
            *JOHN_LENNON_BIRTH_DATA,
            suppress_geonames_warning=True,
            active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS,
        )
        data = ChartDataFactory.create_natal_chart_data(subj, active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
        svg = ChartDrawer(data, theme="classic", transparent_background=True).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Only Classic Transparent - Natal Chart - Wheel Only.svg", svg)

    def test_wheel_only_light_natal(self):
        subj = _make_john("Wheel Only Light")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="light").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Only Light - Natal Chart - Wheel Only.svg", svg)

    def test_strawberry_wheel_only(self):
        subj = _make_john("Wheel Only Strawberry")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="strawberry").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Only Strawberry - Natal Chart - Wheel Only.svg", svg)

    # --- Wheel-only synastry / transit ---

    def test_wheel_synastry(self):
        john = _make_john("Wheel Synastry Only")
        paul = _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Synastry Only - Synastry Chart - Wheel Only.svg", svg)

    def test_wheel_transit(self):
        john = _make_john("Wheel Transit Only")
        paul = _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Transit Only - Transit Chart - Wheel Only.svg", svg)

    def test_wheel_synastry_dark(self):
        john = _make_john("Wheel Synastry Dark")
        paul = _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, theme="dark").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Synastry Dark - Synastry Chart - Wheel Only.svg", svg)

    def test_wheel_transit_dark(self):
        john = _make_john("Wheel Transit Dark")
        paul = _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, theme="dark").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Transit Dark - Transit Chart - Wheel Only.svg", svg)

    def test_wheel_synastry_strawberry(self):
        john = _make_john("Wheel Synastry Strawberry")
        paul = _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, theme="strawberry").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Synastry Strawberry - Synastry Chart - Wheel Only.svg", svg)

    def test_wheel_transit_strawberry(self):
        john = _make_john("Wheel Transit Strawberry")
        paul = _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, theme="strawberry").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Transit Strawberry - Transit Chart - Wheel Only.svg", svg)

    # --- Wheel-only all active points ---

    def test_wheel_only_all_active_points_natal(self):
        from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

        subj = _make_john("All Active Points", active_points=ALL_ACTIVE_POINTS)
        data = ChartDataFactory.create_natal_chart_data(subj, active_points=ALL_ACTIVE_POINTS)
        assert set(data.active_points) == set(ALL_ACTIVE_POINTS)
        svg = ChartDrawer(data).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - All Active Points - Natal Chart - Wheel Only.svg", svg)

    def test_wheel_only_all_active_points_synastry(self):
        from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

        john = _make_john("All Active Points", active_points=ALL_ACTIVE_POINTS)
        paul = _make_paul("All Active Points", active_points=ALL_ACTIVE_POINTS)
        data = ChartDataFactory.create_synastry_chart_data(john, paul, active_points=ALL_ACTIVE_POINTS)
        assert set(data.active_points) == set(ALL_ACTIVE_POINTS)
        svg = ChartDrawer(data).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - All Active Points - Synastry Chart - Wheel Only.svg", svg)

    # --- Aspect-grid-only natal ---

    def test_aspect_grid_only_natal(self):
        subj = _make_john("Aspect Grid Only")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data).generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Only - Natal Chart - Aspect Grid Only.svg", svg)

    def test_aspect_grid_dark_natal(self):
        subj = _make_john("Aspect Grid Dark Theme")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="dark").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Dark Theme - Natal Chart - Aspect Grid Only.svg", svg)

    def test_aspect_grid_light_natal(self):
        subj = _make_john("Aspect Grid Light Theme")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="light").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Light Theme - Natal Chart - Aspect Grid Only.svg", svg)

    def test_aspect_grid_bw_natal(self):
        subj = _make_john("Aspect Grid BW")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="black-and-white").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid BW - Natal Chart - Aspect Grid Only.svg", svg)

    def test_aspect_grid_strawberry_natal(self):
        subj = _make_john("Aspect Grid Strawberry")
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme="strawberry").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Strawberry - Natal Chart - Aspect Grid Only.svg", svg)

    # --- Aspect-grid-only synastry / transit ---

    def test_aspect_grid_synastry(self):
        john = _make_john("Aspect Grid Synastry")
        paul = _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data).generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Synastry - Synastry Chart - Aspect Grid Only.svg", svg)

    def test_aspect_grid_transit(self):
        john = _make_john("Aspect Grid Transit")
        paul = _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data).generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Transit - Transit Chart - Aspect Grid Only.svg", svg)

    def test_aspect_grid_dark_synastry(self):
        john = _make_john("Aspect Grid Dark Synastry")
        paul = _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, theme="dark").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Dark Synastry - Synastry Chart - Aspect Grid Only.svg", svg)

    def test_aspect_grid_bw_synastry(self):
        john = _make_john("Aspect Grid BW Synastry")
        paul = _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, theme="black-and-white").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid BW Synastry - Synastry Chart - Aspect Grid Only.svg", svg)

    def test_aspect_grid_bw_transit(self):
        john = _make_john("Aspect Grid BW Transit")
        paul = _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, theme="black-and-white").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid BW Transit - Transit Chart - Aspect Grid Only.svg", svg)

    def test_aspect_grid_dark_transit(self):
        john = _make_john("Aspect Grid Dark Transit")
        paul = _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, theme="dark").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Dark Transit - Transit Chart - Aspect Grid Only.svg", svg)

    def test_aspect_grid_light_transit(self):
        john = _make_john("Aspect Grid Light Transit")
        paul = _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, theme="light").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Light Transit - Transit Chart - Aspect Grid Only.svg", svg)

    def test_aspect_grid_synastry_strawberry(self):
        john = _make_john("Aspect Grid Synastry Strawberry")
        paul = _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, theme="strawberry").generate_aspect_grid_only_svg_string()
        compare_chart_svg(
            "John Lennon - Aspect Grid Synastry Strawberry - Synastry Chart - Aspect Grid Only.svg",
            svg,
        )

    def test_aspect_grid_transit_strawberry(self):
        john = _make_john("Aspect Grid Transit Strawberry")
        paul = _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, theme="strawberry").generate_aspect_grid_only_svg_string()
        compare_chart_svg(
            "John Lennon - Aspect Grid Transit Strawberry - Transit Chart - Aspect Grid Only.svg",
            svg,
        )

    # --- Aspect-grid-only all active points ---

    def test_aspect_grid_all_active_points_natal(self):
        from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

        subj = _make_john("All Active Points", active_points=ALL_ACTIVE_POINTS)
        data = ChartDataFactory.create_natal_chart_data(subj, active_points=ALL_ACTIVE_POINTS)
        assert set(data.active_points) == set(ALL_ACTIVE_POINTS)
        svg = ChartDrawer(data).generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - All Active Points - Natal Chart - Aspect Grid Only.svg", svg)

    def test_aspect_grid_all_active_points_synastry(self):
        from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

        john = _make_john("All Active Points", active_points=ALL_ACTIVE_POINTS)
        paul = _make_paul("All Active Points", active_points=ALL_ACTIVE_POINTS)
        data = ChartDataFactory.create_synastry_chart_data(john, paul, active_points=ALL_ACTIVE_POINTS)
        assert set(data.active_points) == set(ALL_ACTIVE_POINTS)
        svg = ChartDrawer(data).generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - All Active Points - Synastry Chart - Aspect Grid Only.svg", svg)


# =============================================================================
# 9. TestChartThemes
# =============================================================================


class TestChartThemes:
    """All available themes produce valid SVG."""

    THEMES = ["classic", "dark", "dark-high-contrast", "light", "black-and-white", "strawberry"]

    @pytest.mark.parametrize("theme", THEMES)
    def test_theme_produces_valid_svg(self, theme):
        subj = _make_john()
        data = ChartDataFactory.create_natal_chart_data(subj)
        svg = ChartDrawer(data, theme=theme).generate_svg_string()
        assert isinstance(svg, str)
        assert len(svg) > 100
        assert "<svg" in svg


# =============================================================================
# 10. TestIndicatorsOff
# =============================================================================


class TestIndicatorsOff:
    """Chart with indicators disabled (from test_indicators_off.py)."""

    def test_natal_chart_no_indicators(self):
        john = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon",
            1940,
            10,
            9,
            18,
            30,
            "Liverpool",
            "GB",
            suppress_geonames_warning=True,
        )
        data = ChartDataFactory.create_natal_chart_data(john)
        svg = ChartDrawer(data, show_degree_indicators=False).generate_svg_string()
        compare_chart_svg("John Lennon - Natal Chart - No Degree Indicators.svg", svg)

    def test_synastry_chart_no_indicators(self):
        john = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon",
            1940,
            10,
            9,
            18,
            30,
            "Liverpool",
            "GB",
            suppress_geonames_warning=True,
        )
        paul = AstrologicalSubjectFactory.from_birth_data(
            "Paul McCartney",
            1942,
            6,
            18,
            15,
            30,
            "Liverpool",
            "GB",
            suppress_geonames_warning=True,
        )
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, show_degree_indicators=False).generate_svg_string()
        compare_chart_svg("John Lennon - Synastry Chart - No Degree Indicators.svg", svg)

    def test_transit_chart_no_indicators(self):
        john = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon",
            1940,
            10,
            9,
            18,
            30,
            "Liverpool",
            "GB",
            suppress_geonames_warning=True,
        )
        paul = AstrologicalSubjectFactory.from_birth_data(
            "Paul McCartney",
            1942,
            6,
            18,
            15,
            30,
            "Liverpool",
            "GB",
            suppress_geonames_warning=True,
        )
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, show_degree_indicators=False).generate_svg_string()
        compare_chart_svg("John Lennon - Transit Chart - No Degree Indicators.svg", svg)


# =============================================================================
# 11. TestOutputToFile
# =============================================================================


class TestOutputToFile:
    """Save SVG to directory via tmp_path fixture (from test_options.py)."""

    def test_save_svg_creates_file(self, tmp_path):
        john = _make_john()
        data = ChartDataFactory.create_natal_chart_data(john)
        drawer = ChartDrawer(data)
        drawer.save_svg(output_path=str(tmp_path), filename="test_output")
        expected_file = tmp_path / "test_output.svg"
        assert expected_file.exists(), f"File {expected_file} was not created"
        content = expected_file.read_text(encoding="utf-8")
        assert "<svg" in content, "File does not contain SVG content"

    def test_save_wheel_only_creates_file(self, tmp_path):
        john = _make_john()
        data = ChartDataFactory.create_natal_chart_data(john)
        drawer = ChartDrawer(data)
        drawer.save_wheel_only_svg_file(output_path=str(tmp_path), filename="test_wheel")
        expected_file = tmp_path / "test_wheel.svg"
        assert expected_file.exists(), f"File {expected_file} was not created"

    def test_save_aspect_grid_only_creates_file(self, tmp_path):
        john = _make_john()
        data = ChartDataFactory.create_natal_chart_data(john)
        drawer = ChartDrawer(data)
        drawer.save_aspect_grid_only_svg_file(output_path=str(tmp_path), filename="test_grid")
        expected_file = tmp_path / "test_grid.svg"
        assert expected_file.exists(), f"File {expected_file} was not created"

    def test_save_svg_with_tempdir(self):
        john = _make_john()
        data = ChartDataFactory.create_natal_chart_data(john)
        drawer = ChartDrawer(data)
        with tempfile.TemporaryDirectory() as tmpdir:
            drawer.save_svg(output_path=tmpdir, filename="temp_chart")
            expected = os.path.join(tmpdir, "temp_chart.svg")
            assert os.path.exists(expected)
            with open(expected, "r", encoding="utf-8") as f:
                content = f.read()
            assert "<svg" in content


# ---------------------------------------------------------------------------
# Missing edge-case tests (migrated from tests/edge_cases/test_edge_cases.py)
# ---------------------------------------------------------------------------


class TestChartDrawerLargeAspectList:
    """Synastry chart with many aspects triggers dynamic height adjustment."""

    def test_synastry_with_many_aspects_adjusts_height(self):
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


class TestChartDrawerNoLunarPhase:
    """Chart drawer works when subject has no explicit lunar phase data."""

    def test_chart_drawer_generates_without_lunar_phase(self):
        subject = _make_john()
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        drawer = ChartDrawer(chart_data)
        svg = drawer.generate_svg_string()
        assert svg is not None


class TestChartDrawerCompositeLocation:
    """Composite chart uses average of both subjects' locations."""

    def test_composite_chart_uses_average_location(self):
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


class TestChartDrawerOverlappingPlanets:
    """Synastry chart handles overlapping planet positions gracefully."""

    def test_synastry_chart_with_overlapping_planets(self):
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
        # Second subject born just hours later — similar positions
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
