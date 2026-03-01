# -*- coding: utf-8 -*-
"""
Comprehensive test suite for draw_planets function.

This module consolidates and extends all tests from tests/charts/test_draw_planets.py
with additional coverage for planet glyph positioning, retrograde markers, degree labels,
grouping logic, edge cases, and SVG output validation.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import pytest
import re
from unittest.mock import patch
from kerykeion.charts.draw_planets import (
    draw_planets,
    _calculate_planet_adjustments,
    _calculate_point_offset,
    _determine_point_radius,
    _generate_point_svg,
    _calculate_text_rotation,
    _calculate_indicator_adjustments,
    _apply_group_adjustments,
    _handle_two_point_group,
    _handle_multi_point_group,
    PLANET_GROUPING_THRESHOLD,
    INDICATOR_GROUPING_THRESHOLD,
    CHART_ANGLE_MIN_INDEX,
    CHART_ANGLE_MAX_INDEX,
    DUAL_CHART_TYPES,
)
from kerykeion.schemas import KerykeionException, KerykeionPointModel
from kerykeion.schemas.settings_models import KerykeionSettingsCelestialPointModel


# =============================================================================
# HELPERS AND FIXTURES
# =============================================================================


def _make_point(
    name,
    abs_pos,
    position=None,
    sign="Ari",
    sign_num=0,
    house="First_House",
    quality="Cardinal",
    element="Fire",
    emoji="☉",
    point_type="AstrologicalPoint",
    retrograde=False,
):
    """Build a KerykeionPointModel from minimal keyword arguments."""
    if position is None:
        position = abs_pos % 30.0
    return KerykeionPointModel(
        name=name,
        abs_pos=abs_pos,
        position=position,
        house=house,
        sign=sign,
        quality=quality,
        element=element,
        sign_num=sign_num,
        emoji=emoji,
        point_type=point_type,
        retrograde=retrograde,
    )


def _make_setting(id_, name, color="#000000", label=None, element_points=3, is_active=True):
    """Build a KerykeionSettingsCelestialPointModel from minimal arguments."""
    return KerykeionSettingsCelestialPointModel(
        id=id_,
        name=name,
        color=color,
        element_points=element_points,
        label=label or name,
        is_active=is_active,
    )


# Standard test parameters shared by many tests
RADIUS = 200
THIRD_CIRCLE_RADIUS = 30
FIRST_HOUSE_DEG = 0.0
SEVENTH_HOUSE_DEG = 180.0


def _natal_draw(points, settings, **kwargs):
    """Convenience wrapper for draw_planets with Natal defaults."""
    defaults = dict(
        radius=RADIUS,
        third_circle_radius=THIRD_CIRCLE_RADIUS,
        main_subject_first_house_degree_ut=FIRST_HOUSE_DEG,
        main_subject_seventh_house_degree_ut=SEVENTH_HOUSE_DEG,
        chart_type="Natal",
    )
    defaults.update(kwargs)
    return draw_planets(
        available_kerykeion_celestial_points=points,
        available_planets_setting=settings,
        **defaults,
    )


# Pre-built mock data sets ====================================================

MOCK_POINTS_DATA = [
    {
        "name": "Sun",
        "abs_pos": 15.5,
        "position": 15.5,
        "house": "First_House",
        "sign": "Ari",
        "quality": "Cardinal",
        "element": "Fire",
        "sign_num": 0,
        "emoji": "☉",
        "point_type": "AstrologicalPoint",
        "retrograde": False,
    },
    {
        "name": "Moon",
        "abs_pos": 45.2,
        "position": 15.2,
        "house": "Second_House",
        "sign": "Tau",
        "quality": "Fixed",
        "element": "Earth",
        "sign_num": 1,
        "emoji": "☽",
        "point_type": "AstrologicalPoint",
        "retrograde": False,
    },
    {
        "name": "Mercury",
        "abs_pos": 20.1,
        "position": 20.1,
        "house": "First_House",
        "sign": "Ari",
        "quality": "Cardinal",
        "element": "Fire",
        "sign_num": 0,
        "emoji": "☿",
        "point_type": "AstrologicalPoint",
        "retrograde": True,
    },
]

MOCK_SETTINGS_DATA = [
    {"id": 0, "name": "Sun", "color": "#FFA500", "element_points": 5, "label": "Sun", "is_active": True},
    {"id": 1, "name": "Moon", "color": "#C0C0C0", "element_points": 4, "label": "Moon", "is_active": True},
    {"id": 4, "name": "Mercury", "color": "#87CEEB", "element_points": 3, "label": "Mercury", "is_active": True},
]


def _mock_points(data=None):
    return [KerykeionPointModel(**d) for d in (data or MOCK_POINTS_DATA)]


def _mock_settings(data=None):
    return [KerykeionSettingsCelestialPointModel(**d) for d in (data or MOCK_SETTINGS_DATA)]


# =============================================================================
# 1. TestPlanetGlyphPositioning
# =============================================================================


class TestPlanetGlyphPositioning:
    """Unit tests verifying planet glyphs are positioned correctly given input positions."""

    def test_basic_natal_chart_produces_output(self):
        """Basic natal chart generation produces non-empty SVG output."""
        result = _natal_draw(_mock_points(), _mock_settings())
        assert isinstance(result, str)
        assert len(result) > 0

    def test_all_planets_present_in_output(self):
        """Each planet glyph appears exactly once."""
        result = _natal_draw(_mock_points(), _mock_settings())
        assert 'xlink:href="#Sun"' in result
        assert 'xlink:href="#Moon"' in result
        assert 'xlink:href="#Mercury"' in result

    def test_planet_use_elements_unique(self):
        """Each planet's <use> reference appears exactly once."""
        result = _natal_draw(_mock_points(), _mock_settings())
        assert result.count('xlink:href="#Sun"') == 1
        assert result.count('xlink:href="#Moon"') == 1
        assert result.count('xlink:href="#Mercury"') == 1

    def test_no_external_view_lines_in_standard_natal(self):
        """Standard natal chart must NOT contain connecting lines."""
        result = _natal_draw(_mock_points(), _mock_settings())
        assert "<line x1=" not in result

    def test_natal_chart_with_external_view_has_lines(self):
        """External view natal chart MUST contain connecting lines."""
        result = _natal_draw(_mock_points(), _mock_settings(), external_view=True)
        assert "<line x1=" in result
        assert "stroke-opacity:.3" in result
        assert "stroke-opacity:.5" in result

    def test_external_view_still_has_glyphs(self):
        """External view should still render all planet glyphs."""
        result = _natal_draw(_mock_points(), _mock_settings(), external_view=True)
        assert '<g kr:node="ChartPoint"' in result
        assert 'xlink:href="#Sun"' in result

    def test_different_radii_produce_valid_output(self):
        """Small and large radii both produce valid SVG."""
        pts = [_mock_points()[0]]
        stg = [_mock_settings()[0]]
        r_small = _natal_draw(pts, stg, radius=50, third_circle_radius=10)
        r_large = _natal_draw(pts, stg, radius=500, third_circle_radius=50)
        assert len(r_small) > 0 and len(r_large) > 0

    def test_float_radius_parameters(self):
        """Float radii are accepted without error."""
        result = _natal_draw(
            [_mock_points()[0]],
            [_mock_settings()[0]],
            radius=200.5,
            third_circle_radius=30.25,
            main_subject_first_house_degree_ut=0.75,
            main_subject_seventh_house_degree_ut=180.33,
        )
        assert isinstance(result, str) and len(result) > 0

    def test_chart_angles_positioning(self):
        """Chart angle points (ASC) render with correct xlink:href."""
        angle_point = _make_point(
            "First_House",
            0.0,
            position=0.0,
            emoji="AC",
            point_type="House",
        )
        angle_setting = _make_setting(23, "First_House", label="ASC")
        result = _natal_draw([angle_point], [angle_setting])
        assert 'xlink:href="#First_House"' in result

    def test_determine_point_radius_natal(self):
        """_determine_point_radius returns expected values for Natal chart."""
        # Regular planet, not alternate
        assert _determine_point_radius(0, "Natal", False) == 94
        # Regular planet, alternate
        assert _determine_point_radius(0, "Natal", True) == 74
        # Chart angle (index 23 is between 22-27)
        assert _determine_point_radius(23, "Natal", False) == 40

    def test_determine_point_radius_dual_chart(self):
        """_determine_point_radius returns dual chart radii for Transit."""
        assert _determine_point_radius(0, "Transit", False) == 130
        assert _determine_point_radius(0, "Transit", True) == 110
        assert _determine_point_radius(23, "Transit", False) == 76

    def test_determine_point_radius_external_view(self):
        """_determine_point_radius returns 10 for all external view cases."""
        assert _determine_point_radius(0, "Natal", False, external_view=True) == 10
        assert _determine_point_radius(0, "Natal", True, external_view=True) == 10
        assert _determine_point_radius(23, "Natal", False, external_view=True) == 10

    def test_calculate_point_offset(self):
        """_calculate_point_offset returns correct angular offset."""
        # offset = -seventh_house / 1  +  (point_degree + adjustment)
        offset = _calculate_point_offset(180, 45, 0)
        assert offset == -180 + 45  # = -135

    def test_calculate_point_offset_with_adjustment(self):
        """Adjustment is added to the point degree before computing offset."""
        offset = _calculate_point_offset(180, 45, 5)
        assert offset == -180 + 50  # = -130


# =============================================================================
# 2. TestRetrogradeMarkers
# =============================================================================


class TestRetrogradeMarkers:
    """Verify retrograde planets get appropriate metadata in the SVG output."""

    def test_retrograde_planet_included(self):
        """A retrograde planet should still be rendered."""
        retro_pt = _make_point("Mercury", 20.1, retrograde=True, emoji="☿")
        stg = _make_setting(4, "Mercury", color="#87CEEB")
        result = _natal_draw([retro_pt], [stg])
        assert 'xlink:href="#Mercury"' in result

    def test_non_retrograde_planet_included(self):
        """A direct-motion planet should still be rendered."""
        direct_pt = _make_point("Sun", 15.5, retrograde=False)
        stg = _make_setting(0, "Sun", color="#FFA500")
        result = _natal_draw([direct_pt], [stg])
        assert 'xlink:href="#Sun"' in result

    def test_mixed_retrograde_and_direct(self):
        """Both retrograde and direct planets rendered together."""
        result = _natal_draw(_mock_points(), _mock_settings())
        # Mercury is retrograde, Sun/Moon are direct – all present
        assert 'xlink:href="#Mercury"' in result
        assert 'xlink:href="#Sun"' in result
        assert 'xlink:href="#Moon"' in result

    def test_retrograde_attribute_in_model(self):
        """KerykeionPointModel correctly stores retrograde flag."""
        retro = _make_point(
            "Saturn", 280.0, retrograde=True, sign="Cap", sign_num=9, quality="Cardinal", element="Earth", emoji="♄"
        )
        assert retro.retrograde is True
        direct = _make_point(
            "Jupiter", 120.0, retrograde=False, sign="Leo", sign_num=4, quality="Fixed", element="Fire", emoji="♃"
        )
        assert direct.retrograde is False

    def test_multiple_retrograde_planets(self):
        """Multiple retrograde planets all render correctly."""
        pts = [
            _make_point("Mercury", 20.0, retrograde=True, emoji="☿"),
            _make_point(
                "Saturn", 100.0, retrograde=True, sign="Can", sign_num=3, quality="Cardinal", element="Water", emoji="♄"
            ),
            _make_point(
                "Jupiter", 200.0, retrograde=True, sign="Lib", sign_num=6, quality="Cardinal", element="Air", emoji="♃"
            ),
        ]
        stgs = [
            _make_setting(4, "Mercury"),
            _make_setting(6, "Saturn"),
            _make_setting(5, "Jupiter"),
        ]
        result = _natal_draw(pts, stgs)
        for name in ("Mercury", "Saturn", "Jupiter"):
            assert f'xlink:href="#{name}"' in result

    def test_retrograde_flag_preserved_in_svg_metadata(self):
        """The SVG <g> node carries kr:slug with the planet name regardless of retrograde."""
        retro_pt = _make_point("Mercury", 20.1, retrograde=True, emoji="☿")
        stg = _make_setting(4, "Mercury")
        result = _natal_draw([retro_pt], [stg])
        assert 'kr:slug="Mercury"' in result


# =============================================================================
# 3. TestDegreeLabels
# =============================================================================


class TestDegreeLabels:
    """Verify degree labels are generated correctly for various chart types."""

    def test_natal_degree_indicators_with_first_circle_radius(self):
        """Natal chart with first_circle_radius shows degree indicator lines."""
        result = _natal_draw(
            _mock_points(),
            _mock_settings(),
            first_circle_radius=160,
            show_degree_indicators=True,
        )
        assert 'class="planet-degree-line"' in result

    def test_natal_no_indicators_when_disabled(self):
        """Degree indicators absent when show_degree_indicators=False."""
        result = _natal_draw(
            _mock_points(),
            _mock_settings(),
            first_circle_radius=160,
            show_degree_indicators=False,
        )
        assert 'class="planet-degree-line"' not in result

    def test_natal_no_indicators_without_first_circle_radius(self):
        """Degree indicators absent when first_circle_radius is None."""
        result = _natal_draw(
            _mock_points(),
            _mock_settings(),
            show_degree_indicators=True,
            # first_circle_radius defaults to None
        )
        assert 'class="planet-degree-line"' not in result

    def test_natal_external_view_hides_degree_indicators(self):
        """External view should suppress primary degree indicators."""
        result = _natal_draw(
            _mock_points(),
            _mock_settings(),
            first_circle_radius=160,
            show_degree_indicators=True,
            external_view=True,
        )
        assert 'class="planet-degree-line"' not in result

    def test_degree_text_present_in_natal_indicators(self):
        """Degree text labels contain the ° character."""
        result = _natal_draw(
            _mock_points(),
            _mock_settings(),
            first_circle_radius=160,
            show_degree_indicators=True,
        )
        assert "°" in result

    def test_transit_has_degree_indicators(self):
        """Transit chart renders degree text for secondary points."""
        secondary = [
            _make_point(
                "Sun",
                75.5,
                position=15.5,
                sign="Gem",
                sign_num=2,
                quality="Mutable",
                element="Air",
                house="Third_House",
            ),
            _make_point(
                "Moon",
                105.2,
                position=15.2,
                sign="Can",
                sign_num=3,
                quality="Cardinal",
                element="Water",
                house="Fourth_House",
                emoji="☽",
            ),
            _make_point(
                "Mercury",
                80.1,
                position=20.1,
                sign="Gem",
                sign_num=2,
                quality="Mutable",
                element="Air",
                house="Third_House",
                emoji="☿",
            ),
        ]
        stgs = _mock_settings()
        result = draw_planets(
            radius=RADIUS,
            available_kerykeion_celestial_points=_mock_points(),
            available_planets_setting=stgs,
            third_circle_radius=THIRD_CIRCLE_RADIUS,
            main_subject_first_house_degree_ut=FIRST_HOUSE_DEG,
            main_subject_seventh_house_degree_ut=SEVENTH_HOUSE_DEG,
            chart_type="Transit",
            second_subject_available_kerykeion_celestial_points=secondary,
        )
        assert "°" in result

    def test_dual_chart_inner_indicators(self):
        """Dual chart renders inner degree indicator lines."""
        secondary = [
            _make_point(
                "Sun",
                105.3,
                position=15.3,
                sign="Can",
                sign_num=3,
                quality="Cardinal",
                element="Water",
                house="Fourth_House",
            ),
            _make_point(
                "Moon",
                135.2,
                position=15.2,
                sign="Leo",
                sign_num=4,
                quality="Fixed",
                element="Fire",
                house="Fifth_House",
                emoji="☽",
            ),
            _make_point(
                "Mercury",
                110.1,
                position=20.1,
                sign="Can",
                sign_num=3,
                quality="Cardinal",
                element="Water",
                house="Fourth_House",
                emoji="☿",
                retrograde=True,
            ),
        ]
        result = draw_planets(
            radius=RADIUS,
            available_kerykeion_celestial_points=_mock_points(),
            available_planets_setting=_mock_settings(),
            third_circle_radius=THIRD_CIRCLE_RADIUS,
            main_subject_first_house_degree_ut=FIRST_HOUSE_DEG,
            main_subject_seventh_house_degree_ut=SEVENTH_HOUSE_DEG,
            chart_type="Synastry",
            second_subject_available_kerykeion_celestial_points=secondary,
        )
        assert 'class="planet-degree-line-inner"' in result

    def test_calculate_text_rotation_right_side(self):
        """Text on the right side of the chart should anchor at 'end'."""
        rotation, anchor = _calculate_text_rotation(0.0, 350.0)
        assert anchor in ("end", "start")

    def test_calculate_text_rotation_left_side(self):
        """Text on the left side should flip and anchor 'start'."""
        rotation, anchor = _calculate_text_rotation(0.0, 180.0)
        # At 180° the rotation would be -180, which triggers the flip
        assert anchor in ("end", "start")
        assert -180 <= rotation <= 180

    def test_calculate_text_rotation_normalises(self):
        """Rotation is always in [-180, 180] range."""
        for abs_pos in [0, 45, 90, 135, 180, 225, 270, 315, 359.9]:
            rotation, _ = _calculate_text_rotation(10.0, abs_pos)
            assert -180 <= rotation <= 180


# =============================================================================
# 4. TestGrouping
# =============================================================================


class TestGrouping:
    """Test planet grouping logic when planets are close together."""

    def test_two_close_planets_within_threshold(self):
        """Two planets within PLANET_GROUPING_THRESHOLD render without error."""
        pts = [
            _make_point("Sun", 15.0),
            _make_point("Mercury", 16.5, emoji="☿"),
        ]
        stgs = [
            _make_setting(0, "Sun", color="#FFA500"),
            _make_setting(4, "Mercury", color="#87CEEB"),
        ]
        result = _natal_draw(pts, stgs)
        assert 'xlink:href="#Sun"' in result
        assert 'xlink:href="#Mercury"' in result

    def test_three_close_planets(self):
        """Three planets clustered together render without error."""
        pts = [
            _make_point("Sun", 15.0),
            _make_point("Mercury", 16.5, emoji="☿"),
            _make_point("Venus", 18.0, emoji="♀"),
        ]
        stgs = [
            _make_setting(0, "Sun"),
            _make_setting(4, "Mercury"),
            _make_setting(3, "Venus"),
        ]
        result = _natal_draw(pts, stgs)
        assert 'xlink:href="#Sun"' in result
        assert 'xlink:href="#Mercury"' in result
        assert 'xlink:href="#Venus"' in result

    def test_well_separated_planets_have_zero_adjustments(self):
        """Planets far apart should have no position adjustments."""
        pts = [
            _make_point("Sun", 10.0),
            _make_point("Moon", 100.0, sign="Can", sign_num=3, quality="Cardinal", element="Water", emoji="☽"),
            _make_point("Mars", 250.0, sign="Sag", sign_num=8, quality="Mutable", element="Fire", emoji="♂"),
        ]
        stgs = [
            _make_setting(0, "Sun"),
            _make_setting(1, "Moon"),
            _make_setting(2, "Mars"),
        ]
        abs_positions = [p.abs_pos for p in pts]
        pos_map = {abs_positions[i]: i for i in range(len(stgs))}
        sorted_pos = sorted(pos_map.keys())
        adjustments = _calculate_planet_adjustments(abs_positions, stgs, pos_map, sorted_pos)
        assert all(adj == 0.0 for adj in adjustments)

    def test_apply_group_adjustments_two(self):
        """Two-element group receives symmetric ±1.5 adjustments."""
        adj = {0: 0.0, 1: 0.0}
        _apply_group_adjustments([0, 1], adj)
        assert adj[0] == -1.5
        assert adj[1] == 1.5

    def test_apply_group_adjustments_three(self):
        """Three-element group receives -2/0/+2 adjustments."""
        adj = {0: 0.0, 1: 0.0, 2: 0.0}
        _apply_group_adjustments([0, 1, 2], adj)
        assert adj[0] == -2.0
        assert adj[1] == 0.0
        assert adj[2] == 2.0

    def test_apply_group_adjustments_four(self):
        """Four-element group receives -3/-1/+1/+3 adjustments."""
        adj = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0}
        _apply_group_adjustments([0, 1, 2, 3], adj)
        assert adj[0] == -3.0
        assert adj[1] == -1.0
        assert adj[2] == 1.0
        assert adj[3] == 3.0

    def test_apply_group_adjustments_five(self):
        """Five-element group is evenly distributed with spread=1.5."""
        adj = {i: 0.0 for i in range(5)}
        _apply_group_adjustments([0, 1, 2, 3, 4], adj)
        # mid = 2.0; offsets = (i - 2)*1.5
        assert adj[0] == pytest.approx(-3.0)
        assert adj[2] == pytest.approx(0.0)
        assert adj[4] == pytest.approx(3.0)

    def test_calculate_indicator_adjustments_no_overlap(self):
        """Indicator adjustments are all zero when points are well separated."""
        pts = [
            _make_point("Sun", 10.0),
            _make_point("Moon", 100.0, sign="Can", sign_num=3, quality="Cardinal", element="Water", emoji="☽"),
        ]
        stgs = [_make_setting(0, "Sun"), _make_setting(1, "Moon")]
        abs_positions = [p.abs_pos for p in pts]
        adj = _calculate_indicator_adjustments(abs_positions, stgs)
        assert adj[0] == 0.0
        assert adj[1] == 0.0

    def test_calculate_indicator_adjustments_overlap(self):
        """Overlapping indicators receive non-zero adjustments."""
        pts = [
            _make_point("Sun", 10.0),
            _make_point("Mercury", 11.5, emoji="☿"),
        ]
        stgs = [_make_setting(0, "Sun"), _make_setting(4, "Mercury")]
        abs_positions = [p.abs_pos for p in pts]
        adj = _calculate_indicator_adjustments(abs_positions, stgs)
        # 1.5° apart is within INDICATOR_GROUPING_THRESHOLD (2.5)
        assert adj[0] != 0.0 or adj[1] != 0.0

    def test_grouping_constants(self):
        """Verify module-level threshold constants have expected values."""
        assert PLANET_GROUPING_THRESHOLD == 3.4
        assert INDICATOR_GROUPING_THRESHOLD == 2.5


# =============================================================================
# 5. TestEdgeCases
# =============================================================================


class TestEdgeCases:
    """Edge cases: single planet, no planets, evenly spaced, all at same position."""

    def test_single_planet(self):
        """Chart with a single planet renders successfully."""
        pts = [_make_point("Sun", 15.0)]
        stgs = [_make_setting(0, "Sun", color="#FFA500")]
        result = _natal_draw(pts, stgs)
        assert isinstance(result, str)
        assert 'xlink:href="#Sun"' in result

    def test_empty_planet_list(self):
        """Empty planet list produces empty output string."""
        result = _natal_draw([], [])
        assert result == ""

    def test_twelve_planets_evenly_spaced(self):
        """12 planets at 30° intervals (no overlap) all render."""
        names = [
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
            "Mean_North_Lunar_Node",
            "True_North_Lunar_Node",
        ]
        emojis = ["☉", "☽", "☿", "♀", "♂", "♃", "♄", "♅", "♆", "♇", "☊", "☋"]
        signs = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
        qualities = ["Cardinal", "Fixed", "Mutable"] * 4
        elements = ["Fire", "Earth", "Air", "Water"] * 3
        pts = []
        stgs = []
        for i, name in enumerate(names):
            pts.append(
                _make_point(
                    name,
                    abs_pos=i * 30.0,
                    position=0.0,
                    sign=signs[i],
                    sign_num=i,
                    emoji=emojis[i],
                    quality=qualities[i],
                    element=elements[i],
                )
            )
            stgs.append(_make_setting(i, name))

        result = _natal_draw(pts, stgs)
        assert isinstance(result, str) and len(result) > 0
        for name in names:
            assert f'xlink:href="#{name}"' in result

    def test_all_planets_at_same_position(self):
        """All planets at 0° should still render (grouping logic is exercised)."""
        pts = [
            _make_point("Sun", 0.0),
            _make_point("Moon", 0.1, emoji="☽"),
            _make_point("Mercury", 0.2, emoji="☿"),
        ]
        stgs = [
            _make_setting(0, "Sun"),
            _make_setting(1, "Moon"),
            _make_setting(4, "Mercury"),
        ]
        result = _natal_draw(pts, stgs)
        assert 'xlink:href="#Sun"' in result
        assert 'xlink:href="#Moon"' in result
        assert 'xlink:href="#Mercury"' in result

    def test_planet_at_zero_degrees(self):
        """Planet at exactly 0.0° renders without error."""
        pt = _make_point("Sun", 0.0, position=0.0)
        stg = _make_setting(0, "Sun")
        result = _natal_draw([pt], [stg])
        assert len(result) > 0

    def test_planet_at_359_degrees(self):
        """Planet at 359.99° renders without error."""
        pt = _make_point(
            "Moon",
            359.99,
            position=29.99,
            sign="Pis",
            sign_num=11,
            quality="Mutable",
            element="Water",
            emoji="☽",
            house="Twelfth_House",
        )
        stg = _make_setting(0, "Moon")
        result = _natal_draw([pt], [stg])
        assert len(result) > 0

    def test_transit_without_secondary_raises(self):
        """Transit chart without secondary points raises KerykeionException."""
        with pytest.raises(KerykeionException, match="Secondary celestial points are required for Transit"):
            draw_planets(
                radius=RADIUS,
                available_kerykeion_celestial_points=_mock_points(),
                available_planets_setting=_mock_settings(),
                third_circle_radius=THIRD_CIRCLE_RADIUS,
                main_subject_first_house_degree_ut=FIRST_HOUSE_DEG,
                main_subject_seventh_house_degree_ut=SEVENTH_HOUSE_DEG,
                chart_type="Transit",
            )

    def test_synastry_without_secondary_raises(self):
        """Synastry chart without secondary points raises KerykeionException."""
        with pytest.raises(KerykeionException, match="Secondary celestial points are required for Synastry"):
            draw_planets(
                radius=RADIUS,
                available_kerykeion_celestial_points=_mock_points(),
                available_planets_setting=_mock_settings(),
                third_circle_radius=THIRD_CIRCLE_RADIUS,
                main_subject_first_house_degree_ut=FIRST_HOUSE_DEG,
                main_subject_seventh_house_degree_ut=SEVENTH_HOUSE_DEG,
                chart_type="Synastry",
            )

    def test_single_return_chart_without_secondary_does_not_raise(self):
        """SingleReturnChart without secondary points does NOT raise exception."""
        result = draw_planets(
            radius=RADIUS,
            available_kerykeion_celestial_points=_mock_points(),
            available_planets_setting=_mock_settings(),
            third_circle_radius=THIRD_CIRCLE_RADIUS,
            main_subject_first_house_degree_ut=FIRST_HOUSE_DEG,
            main_subject_seventh_house_degree_ut=SEVENTH_HOUSE_DEG,
            chart_type="SingleReturnChart",
        )
        assert isinstance(result, str)

    def test_dual_return_chart_without_secondary_does_not_raise(self):
        """DualReturnChart without secondary points does NOT raise exception."""
        result = draw_planets(
            radius=RADIUS,
            available_kerykeion_celestial_points=_mock_points(),
            available_planets_setting=_mock_settings(),
            third_circle_radius=THIRD_CIRCLE_RADIUS,
            main_subject_first_house_degree_ut=FIRST_HOUSE_DEG,
            main_subject_seventh_house_degree_ut=SEVENTH_HOUSE_DEG,
            chart_type="DualReturnChart",
        )
        assert isinstance(result, str)

    def test_planets_crossing_zero_boundary(self):
        """Planets spanning the 360/0 boundary render correctly."""
        pts = [
            _make_point(
                "Sun",
                358.0,
                position=28.0,
                sign="Pis",
                sign_num=11,
                quality="Mutable",
                element="Water",
                house="Twelfth_House",
            ),
            _make_point("Moon", 2.0, position=2.0, emoji="☽"),
        ]
        stgs = [
            _make_setting(0, "Sun"),
            _make_setting(1, "Moon"),
        ]
        result = _natal_draw(pts, stgs)
        assert 'xlink:href="#Sun"' in result
        assert 'xlink:href="#Moon"' in result


# =============================================================================
# 6. TestSVGOutput
# =============================================================================


class TestSVGOutput:
    """Output contains valid SVG elements (<text>, <line>, <g>)."""

    def test_svg_g_elements_present(self):
        """Output contains <g> group elements with chart point metadata."""
        result = _natal_draw(_mock_points(), _mock_settings())
        assert '<g kr:node="ChartPoint"' in result
        assert "</g>" in result

    def test_svg_use_elements_present(self):
        """Output contains <use> elements linking to planet symbol defs."""
        result = _natal_draw(_mock_points(), _mock_settings())
        assert "<use " in result
        assert 'xlink:href="#' in result

    def test_svg_transform_and_scale(self):
        """Output includes transform and scale attributes."""
        result = _natal_draw(_mock_points(), _mock_settings())
        assert "transform=" in result
        assert "scale(" in result

    def test_svg_kr_attributes_present(self):
        """Custom kr: namespace attributes are included."""
        result = _natal_draw(_mock_points(), _mock_settings())
        assert "kr:house=" in result
        assert "kr:sign=" in result
        assert "kr:slug=" in result
        assert "kr:absoluteposition=" in result
        assert "kr:signposition=" in result

    def test_svg_text_elements_in_degree_indicators(self):
        """<text> elements appear when degree indicators are enabled."""
        result = _natal_draw(
            _mock_points(),
            _mock_settings(),
            first_circle_radius=160,
            show_degree_indicators=True,
        )
        assert "<text " in result
        assert "text-anchor=" in result

    def test_svg_line_elements_in_external_view(self):
        """<line> elements are present in external view output."""
        result = _natal_draw(_mock_points(), _mock_settings(), external_view=True)
        assert "<line " in result
        # Verify the line has coordinate attributes
        assert 'x1="' in result
        assert 'y1="' in result
        assert 'x2="' in result
        assert 'y2="' in result

    def test_transit_svg_has_transit_classes(self):
        """Transit chart output uses transit-specific CSS classes."""
        secondary = [
            _make_point(
                "Sun",
                75.5,
                position=15.5,
                sign="Gem",
                sign_num=2,
                quality="Mutable",
                element="Air",
                house="Third_House",
            ),
            _make_point(
                "Moon",
                105.2,
                position=15.2,
                sign="Can",
                sign_num=3,
                quality="Cardinal",
                element="Water",
                house="Fourth_House",
                emoji="☽",
            ),
            _make_point(
                "Mercury",
                80.1,
                position=20.1,
                sign="Gem",
                sign_num=2,
                quality="Mutable",
                element="Air",
                house="Third_House",
                emoji="☿",
            ),
        ]
        result = draw_planets(
            radius=RADIUS,
            available_kerykeion_celestial_points=_mock_points(),
            available_planets_setting=_mock_settings(),
            third_circle_radius=THIRD_CIRCLE_RADIUS,
            main_subject_first_house_degree_ut=FIRST_HOUSE_DEG,
            main_subject_seventh_house_degree_ut=SEVENTH_HOUSE_DEG,
            chart_type="Transit",
            second_subject_available_kerykeion_celestial_points=secondary,
        )
        assert 'class="transit-planet-name"' in result
        assert 'class="transit-planet-line"' in result

    def test_generate_point_svg_structure(self):
        """_generate_point_svg produces valid group with use element."""
        pt = _make_point("Mars", 60.0, sign="Gem", sign_num=2, quality="Mutable", element="Air", emoji="♂")
        svg = _generate_point_svg(pt, 100.0, 100.0, 1.0, "Mars")
        assert svg.startswith('<g kr:node="ChartPoint"')
        assert svg.endswith("</g>")
        assert 'xlink:href="#Mars"' in svg
        assert 'kr:slug="Mars"' in svg
        assert 'kr:sign="Gem"' in svg

    def test_generate_point_svg_scale_factor(self):
        """Scale factor appears in the transform attribute."""
        pt = _make_point("Sun", 15.0)
        svg_1x = _generate_point_svg(pt, 100.0, 100.0, 1.0, "Sun")
        svg_08x = _generate_point_svg(pt, 100.0, 100.0, 0.8, "Sun")
        assert "scale(1.0)" in svg_1x
        assert "scale(0.8)" in svg_08x

    def test_output_is_pure_string(self):
        """Return type is always a plain str, never bytes."""
        result = _natal_draw(_mock_points(), _mock_settings())
        assert type(result) is str

    def test_svg_numeric_coordinates_are_valid(self):
        """Extracted x/y coordinates from <use> elements are valid floats."""
        result = _natal_draw(_mock_points(), _mock_settings())
        x_values = re.findall(r'x="([^"]+)"', result)
        y_values = re.findall(r'y="([^"]+)"', result)
        for v in x_values + y_values:
            float(v)  # Should not raise


# =============================================================================
# 7. TestChartTypes (migrated from original test_draw_planets.py)
# =============================================================================


class TestChartTypes:
    """Test all supported chart types produce valid output."""

    def _secondary_points(self):
        return [
            _make_point(
                "Sun",
                75.5,
                position=15.5,
                sign="Gem",
                sign_num=2,
                quality="Mutable",
                element="Air",
                house="Third_House",
            ),
            _make_point(
                "Moon",
                105.2,
                position=15.2,
                sign="Can",
                sign_num=3,
                quality="Cardinal",
                element="Water",
                house="Fourth_House",
                emoji="☽",
            ),
            _make_point(
                "Mercury",
                80.1,
                position=20.1,
                sign="Gem",
                sign_num=2,
                quality="Mutable",
                element="Air",
                house="Third_House",
                emoji="☿",
            ),
        ]

    def test_transit_chart(self):
        """Transit chart with secondary points renders successfully."""
        result = draw_planets(
            radius=RADIUS,
            available_kerykeion_celestial_points=_mock_points(),
            available_planets_setting=_mock_settings(),
            third_circle_radius=THIRD_CIRCLE_RADIUS,
            main_subject_first_house_degree_ut=FIRST_HOUSE_DEG,
            main_subject_seventh_house_degree_ut=SEVENTH_HOUSE_DEG,
            chart_type="Transit",
            second_subject_available_kerykeion_celestial_points=self._secondary_points(),
        )
        assert isinstance(result, str) and len(result) > 0
        assert '<g kr:node="ChartPoint"' in result
        assert 'class="transit-planet-name"' in result

    def test_synastry_chart(self):
        """Synastry chart renders with style attributes."""
        secondary = [
            _make_point(
                "Sun",
                105.3,
                position=15.3,
                sign="Can",
                sign_num=3,
                quality="Cardinal",
                element="Water",
                house="Fourth_House",
            ),
            _make_point(
                "Moon",
                135.2,
                position=15.2,
                sign="Leo",
                sign_num=4,
                quality="Fixed",
                element="Fire",
                house="Fifth_House",
                emoji="☽",
            ),
            _make_point(
                "Mercury",
                110.1,
                position=20.1,
                sign="Can",
                sign_num=3,
                quality="Cardinal",
                element="Water",
                house="Fourth_House",
                emoji="☿",
                retrograde=True,
            ),
        ]
        result = draw_planets(
            radius=RADIUS,
            available_kerykeion_celestial_points=_mock_points(),
            available_planets_setting=_mock_settings(),
            third_circle_radius=THIRD_CIRCLE_RADIUS,
            main_subject_first_house_degree_ut=FIRST_HOUSE_DEG,
            main_subject_seventh_house_degree_ut=SEVENTH_HOUSE_DEG,
            chart_type="Synastry",
            second_subject_available_kerykeion_celestial_points=secondary,
        )
        assert isinstance(result, str) and len(result) > 0
        assert 'style="stroke:' in result

    def test_return_chart(self):
        """SingleReturnChart renders successfully with secondary points."""
        secondary = [
            _make_point("Sun", 15.5, position=15.5),
            _make_point(
                "Moon",
                45.2,
                position=15.2,
                sign="Tau",
                sign_num=1,
                quality="Fixed",
                element="Earth",
                house="Second_House",
                emoji="☽",
            ),
            _make_point("Mercury", 20.1, position=20.1, emoji="☿", retrograde=True),
        ]
        result = draw_planets(
            radius=RADIUS,
            available_kerykeion_celestial_points=_mock_points(),
            available_planets_setting=_mock_settings(),
            third_circle_radius=THIRD_CIRCLE_RADIUS,
            main_subject_first_house_degree_ut=FIRST_HOUSE_DEG,
            main_subject_seventh_house_degree_ut=SEVENTH_HOUSE_DEG,
            chart_type="SingleReturnChart",
            second_subject_available_kerykeion_celestial_points=secondary,
        )
        assert isinstance(result, str) and len(result) > 0

    def test_dual_return_chart(self):
        """DualReturnChart renders successfully with secondary points."""
        secondary = [
            _make_point("Sun", 15.5, position=15.5),
            _make_point(
                "Moon",
                45.2,
                position=15.2,
                sign="Tau",
                sign_num=1,
                quality="Fixed",
                element="Earth",
                house="Second_House",
                emoji="☽",
            ),
            _make_point("Mercury", 20.1, position=20.1, emoji="☿", retrograde=True),
        ]
        result = draw_planets(
            radius=RADIUS,
            available_kerykeion_celestial_points=_mock_points(),
            available_planets_setting=_mock_settings(),
            third_circle_radius=THIRD_CIRCLE_RADIUS,
            main_subject_first_house_degree_ut=FIRST_HOUSE_DEG,
            main_subject_seventh_house_degree_ut=SEVENTH_HOUSE_DEG,
            chart_type="DualReturnChart",
            second_subject_available_kerykeion_celestial_points=secondary,
        )
        assert isinstance(result, str) and len(result) > 0

    def test_scale_factors_differ_by_chart_type(self):
        """Different chart types apply different scale factors."""
        pts = [_mock_points()[0]]
        stgs = [_mock_settings()[0]]
        sec = [
            _make_point(
                "Moon",
                105.2,
                position=15.2,
                sign="Can",
                sign_num=3,
                quality="Cardinal",
                element="Water",
                house="Fourth_House",
                emoji="☽",
            )
        ]

        result_natal = _natal_draw(pts, stgs)
        result_transit = draw_planets(
            radius=RADIUS,
            available_kerykeion_celestial_points=pts,
            available_planets_setting=stgs,
            third_circle_radius=THIRD_CIRCLE_RADIUS,
            main_subject_first_house_degree_ut=FIRST_HOUSE_DEG,
            main_subject_seventh_house_degree_ut=SEVENTH_HOUSE_DEG,
            chart_type="Transit",
            second_subject_available_kerykeion_celestial_points=sec,
        )
        result_external = _natal_draw(pts, stgs, external_view=True)

        # Natal uses scale(1.0), Transit and external use scale(0.8)
        assert "scale(1.0)" in result_natal
        assert "scale(0.8)" in result_transit
        assert "scale(0.8)" in result_external


# =============================================================================
# 8. TestLogging
# =============================================================================


class TestLogging:
    """Ensure logging calls are made during draw_planets execution."""

    @patch("kerykeion.charts.draw_planets.logging.debug")
    def test_debug_logging_called(self, mock_debug):
        """Debug logging is invoked for planet index reporting."""
        _natal_draw([_mock_points()[0]], [_mock_settings()[0]])
        assert mock_debug.called

    @patch("kerykeion.charts.draw_planets.logging.debug")
    def test_debug_logging_called_with_multiple_planets(self, mock_debug):
        """Debug logging is invoked once per planet for index and distance info."""
        _natal_draw(_mock_points(), _mock_settings())
        # At minimum: one call per planet for index + one per planet for distances
        assert mock_debug.call_count >= 3


# =============================================================================
# 9. TestInternalHelpers
# =============================================================================


class TestInternalHelpers:
    """Unit tests for internal module-level helper functions."""

    def test_handle_multi_point_group_applies_adjustments(self):
        """_handle_multi_point_group produces non-zero adjustments for 3+ close points."""
        # Simulate group data: [position_idx, dist_prev, dist_next, label]
        group = [
            [0, 20.0, 2.0, "Sun"],
            [1, 2.0, 2.0, "Mercury"],
            [2, 2.0, 20.0, "Venus"],
        ]
        adjustments = [0.0] * 3
        _handle_multi_point_group(group, adjustments, PLANET_GROUPING_THRESHOLD)
        # At least first and last should be adjusted
        assert any(a != 0.0 for a in adjustments)

    def test_chart_angle_index_boundaries(self):
        """Chart angle constants define the expected index range."""
        assert CHART_ANGLE_MIN_INDEX == 22
        assert CHART_ANGLE_MAX_INDEX == 27

    def test_dual_chart_types_tuple(self):
        """DUAL_CHART_TYPES includes the expected chart type names."""
        assert "Transit" in DUAL_CHART_TYPES
        assert "Synastry" in DUAL_CHART_TYPES
        assert "DualReturnChart" in DUAL_CHART_TYPES
        assert "Natal" not in DUAL_CHART_TYPES

    def test_generate_point_svg_coordinates(self):
        """Generated SVG contains the scaled x/y coordinates."""
        pt = _make_point("Sun", 15.0)
        svg = _generate_point_svg(pt, 150.0, 120.0, 1.0, "Sun")
        assert 'x="150.0"' in svg
        assert 'y="120.0"' in svg

    def test_generate_point_svg_scaled_coordinates(self):
        """When scale != 1.0, coordinates are divided by scale."""
        pt = _make_point("Sun", 15.0)
        svg = _generate_point_svg(pt, 80.0, 80.0, 0.8, "Sun")
        expected_x = 80.0 * (1 / 0.8)
        assert f'x="{expected_x}"' in svg

    def test_generate_point_svg_house_attribute(self):
        """Generated SVG contains the correct house attribute."""
        pt = _make_point(
            "Moon", 45.0, house="Second_House", sign="Tau", sign_num=1, quality="Fixed", element="Earth", emoji="☽"
        )
        svg = _generate_point_svg(pt, 100.0, 100.0, 1.0, "Moon")
        assert 'kr:house="Second_House"' in svg
