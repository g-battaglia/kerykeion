# -*- coding: utf-8 -*-
"""
Partial View (Wheel-Only, Aspect-Grid-Only) SVG Tests

This module tests partial chart outputs:
- Wheel-only natal charts
- Wheel-only synastry charts
- Wheel-only transit charts
- Aspect-grid-only natal charts
- Aspect-grid-only synastry charts
- Aspect-grid-only transit charts
- Theme variations for partial views
- All active points for partial views

Usage:
    pytest tests/charts/test_partial_views.py -v
"""

from kerykeion import AstrologicalSubjectFactory, ChartDrawer
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS, TRADITIONAL_ASTROLOGY_ACTIVE_POINTS

from .conftest import (
    JOHN_LENNON_BIRTH_DATA,
    PAUL_MCCARTNEY_BIRTH_DATA,
    compare_chart_svg,
)


class TestWheelOnlyNatal:
    """Wheel-only natal chart tests."""

    def test_wheel_only_chart(self):
        """Test natal chart wheel-only output."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Only", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Only - Natal Chart - Wheel Only.svg", chart_svg)

    def test_wheel_external_chart(self):
        """Test external natal chart wheel-only output."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel External Only", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, external_view=True).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel External Only - ExternalNatal Chart - Wheel Only.svg", chart_svg)

    def test_wheel_only_dark_natal(self):
        """Test natal chart wheel-only with dark theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Only Dark", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Only Dark - Natal Chart - Wheel Only.svg", chart_svg)

    def test_wheel_only_dark_transparent_natal(self):
        """Test natal chart wheel-only with dark theme and transparent background (hero image).

        Uses TRADITIONAL_ASTROLOGY_ACTIVE_POINTS (Sun to Saturn + lunar nodes).
        """
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Only Dark Transparent",
            *JOHN_LENNON_BIRTH_DATA,
            suppress_geonames_warning=True,
            active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(
            subject, active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS
        )
        chart_svg = ChartDrawer(chart_data, theme="dark", transparent_background=True).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Only Dark Transparent - Natal Chart - Wheel Only.svg", chart_svg)

    def test_wheel_only_classic_transparent_natal(self):
        """Test natal chart wheel-only with classic theme and transparent background (hero image).

        Uses TRADITIONAL_ASTROLOGY_ACTIVE_POINTS (Sun to Saturn + lunar nodes).
        """
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Only Classic Transparent",
            *JOHN_LENNON_BIRTH_DATA,
            suppress_geonames_warning=True,
            active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(
            subject, active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS
        )
        chart_svg = ChartDrawer(
            chart_data, theme="classic", transparent_background=True
        ).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Only Classic Transparent - Natal Chart - Wheel Only.svg", chart_svg)

    def test_wheel_only_light_natal(self):
        """Test natal chart wheel-only with light theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Only Light", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="light").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Only Light - Natal Chart - Wheel Only.svg", chart_svg)

    def test_strawberry_wheel_only(self):
        """Test wheel-only chart with Strawberry theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Only Strawberry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="strawberry").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Only Strawberry - Natal Chart - Wheel Only.svg", chart_svg)


class TestWheelOnlySynastryTransit:
    """Wheel-only synastry and transit chart tests."""

    def test_wheel_synastry_chart(self, paul_mccartney):
        """Test synastry chart wheel-only output."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Synastry Only", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Synastry Only - Synastry Chart - Wheel Only.svg", chart_svg)

    def test_wheel_transit_chart(self, paul_mccartney):
        """Test transit chart wheel-only output."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Transit Only", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Transit Only - Transit Chart - Wheel Only.svg", chart_svg)

    def test_wheel_synastry_dark(self, paul_mccartney):
        """Test synastry chart wheel-only with dark theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Synastry Dark", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Synastry Dark - Synastry Chart - Wheel Only.svg", chart_svg)

    def test_wheel_transit_dark(self, paul_mccartney):
        """Test transit chart wheel-only with dark theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Transit Dark", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Transit Dark - Transit Chart - Wheel Only.svg", chart_svg)


class TestWheelOnlyAllActivePoints:
    """Wheel-only all active points tests."""

    def test_wheel_only_all_active_points_chart(self, all_active_points_subject):
        """Test natal chart wheel-only with all active points."""
        chart_data = ChartDataFactory.create_natal_chart_data(
            all_active_points_subject, active_points=ALL_ACTIVE_POINTS
        )
        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)
        chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - All Active Points - Natal Chart - Wheel Only.svg", chart_svg)

    def test_wheel_only_all_active_points_synastry_chart(
        self, all_active_points_subject, all_active_points_second_subject
    ):
        """Test synastry chart wheel-only with all active points."""
        chart_data = ChartDataFactory.create_synastry_chart_data(
            all_active_points_subject,
            all_active_points_second_subject,
            active_points=ALL_ACTIVE_POINTS,
        )
        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)
        chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - All Active Points - Synastry Chart - Wheel Only.svg", chart_svg)


class TestAspectGridOnlyNatal:
    """Aspect-grid-only natal chart tests."""

    def test_aspect_grid_only_chart(self):
        """Test natal chart aspect-grid-only output."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Only", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Only - Natal Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_dark_chart(self):
        """Test natal chart aspect-grid-only with dark theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Dark Theme", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Dark Theme - Natal Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_light_chart(self):
        """Test natal chart aspect-grid-only with light theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Light Theme", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="light").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Light Theme - Natal Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_black_and_white_natal(self):
        """Test natal chart aspect-grid-only with black-and-white theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid BW", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid BW - Natal Chart - Aspect Grid Only.svg", chart_svg)

    def test_strawberry_aspect_grid_only(self):
        """Test aspect grid only chart with Strawberry theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Strawberry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="strawberry").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Strawberry - Natal Chart - Aspect Grid Only.svg", chart_svg)


class TestAspectGridOnlySynastryTransit:
    """Aspect-grid-only synastry and transit chart tests."""

    def test_aspect_grid_synastry_chart(self, paul_mccartney):
        """Test synastry chart aspect-grid-only output."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Synastry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Synastry - Synastry Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_transit(self, paul_mccartney):
        """Test transit chart aspect-grid-only output."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Transit", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Transit - Transit Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_dark_synastry(self, paul_mccartney):
        """Test synastry chart aspect-grid-only with dark theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Dark Synastry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Dark Synastry - Synastry Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_black_and_white_synastry(self, paul_mccartney):
        """Test synastry chart aspect-grid-only with black-and-white theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid BW Synastry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid BW Synastry - Synastry Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_black_and_white_transit(self, paul_mccartney):
        """Test transit chart aspect-grid-only with black-and-white theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid BW Transit", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid BW Transit - Transit Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_transit_dark(self, paul_mccartney):
        """Test transit chart aspect-grid-only with dark theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Dark Transit", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Dark Transit - Transit Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_transit_light(self, paul_mccartney):
        """Test transit chart aspect-grid-only with light theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Light Transit", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="light").generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - Aspect Grid Light Transit - Transit Chart - Aspect Grid Only.svg", chart_svg)


class TestAspectGridOnlyAllActivePoints:
    """Aspect-grid-only all active points tests."""

    def test_aspect_grid_all_active_points_chart(self, all_active_points_subject):
        """Test natal chart aspect-grid-only with all active points."""
        chart_data = ChartDataFactory.create_natal_chart_data(
            all_active_points_subject, active_points=ALL_ACTIVE_POINTS
        )
        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)
        chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - All Active Points - Natal Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_all_active_points_synastry_chart(
        self, all_active_points_subject, all_active_points_second_subject
    ):
        """Test synastry chart aspect-grid-only with all active points."""
        chart_data = ChartDataFactory.create_synastry_chart_data(
            all_active_points_subject,
            all_active_points_second_subject,
            active_points=ALL_ACTIVE_POINTS,
        )
        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)
        chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()
        compare_chart_svg("John Lennon - All Active Points - Synastry Chart - Aspect Grid Only.svg", chart_svg)


class TestStrawberrySynastryTransitPartialViews:
    """Strawberry theme partial views for synastry and transit charts."""

    def test_wheel_synastry_strawberry(self, paul_mccartney):
        """Test synastry chart wheel-only with Strawberry theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Synastry Strawberry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="strawberry").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Synastry Strawberry - Synastry Chart - Wheel Only.svg", chart_svg)

    def test_wheel_transit_strawberry(self, paul_mccartney):
        """Test transit chart wheel-only with Strawberry theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Transit Strawberry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="strawberry").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon - Wheel Transit Strawberry - Transit Chart - Wheel Only.svg", chart_svg)

    def test_aspect_grid_synastry_strawberry(self, paul_mccartney):
        """Test synastry chart aspect-grid-only with Strawberry theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Synastry Strawberry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="strawberry").generate_aspect_grid_only_svg_string()
        compare_chart_svg(
            "John Lennon - Aspect Grid Synastry Strawberry - Synastry Chart - Aspect Grid Only.svg", chart_svg
        )

    def test_aspect_grid_transit_strawberry(self, paul_mccartney):
        """Test transit chart aspect-grid-only with Strawberry theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Transit Strawberry", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, paul_mccartney)
        chart_svg = ChartDrawer(chart_data, theme="strawberry").generate_aspect_grid_only_svg_string()
        compare_chart_svg(
            "John Lennon - Aspect Grid Transit Strawberry - Transit Chart - Aspect Grid Only.svg", chart_svg
        )
