# -*- coding: utf-8 -*-
"""Tests for Uranian / Hamburg School hypothetical planets (Cupido-Poseidon).

These 8 hypothetical trans-Neptunian points (SwissEph IDs 40-47) are used
in the Hamburg School of Astrology (Alfred Witte / Friedrich Sieggruen).
"""

import pytest
from kerykeion import AstrologicalSubjectFactory, AspectsFactory, ChartDataFactory, ChartDrawer
from kerykeion.settings.config_constants import URANIAN_ACTIVE_POINTS, ALL_ACTIVE_POINTS

URANIAN_NAMES = [
    "Cupido", "Hades", "Zeus", "Kronos",
    "Apollon", "Admetos", "Vulkanus", "Poseidon",
]


@pytest.fixture(scope="module")
def subject_with_uranian():
    """Create a subject with Uranian planets activated."""
    active = [
        "Sun", "Moon", "Mercury", "Venus", "Mars",
        "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
        "True_North_Lunar_Node", "True_South_Lunar_Node",
        "Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli",
    ] + URANIAN_NAMES
    return AstrologicalSubjectFactory.from_birth_data(
        "Uranian Test",
        year=1990, month=6, day=15, hour=14, minute=30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
        active_points=active,
    )


@pytest.fixture(scope="module")
def subject_without_uranian():
    """Create a subject without Uranian planets (default)."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Default Test",
        year=1990, month=6, day=15, hour=14, minute=30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
    )


class TestUranianPlanetsCalculation:
    """Test that Uranian planet positions are correctly calculated."""

    @pytest.mark.parametrize("planet_name", URANIAN_NAMES)
    def test_uranian_planet_is_calculated(self, subject_with_uranian, planet_name):
        """Each Uranian planet should be present and have valid data."""
        point = getattr(subject_with_uranian, planet_name.lower())
        assert point is not None, f"{planet_name} should be calculated"
        assert 0 <= point.abs_pos < 360, f"{planet_name} abs_pos should be in [0, 360)"
        assert point.sign in ("Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis")
        assert 0 <= point.position < 30, f"{planet_name} position should be in [0, 30)"
        assert point.point_type == "AstrologicalPoint"

    @pytest.mark.parametrize("planet_name", URANIAN_NAMES)
    def test_uranian_planet_has_speed(self, subject_with_uranian, planet_name):
        """Each Uranian planet should have speed (degrees/day)."""
        point = getattr(subject_with_uranian, planet_name.lower())
        assert point.speed is not None, f"{planet_name} should have speed"

    @pytest.mark.parametrize("planet_name", URANIAN_NAMES)
    def test_uranian_planet_has_house(self, subject_with_uranian, planet_name):
        """Each Uranian planet should be assigned to a house."""
        point = getattr(subject_with_uranian, planet_name.lower())
        assert point.house is not None, f"{planet_name} should have a house"

    @pytest.mark.parametrize("planet_name", URANIAN_NAMES)
    def test_uranian_not_calculated_by_default(self, subject_without_uranian, planet_name):
        """Uranian planets should NOT be calculated when not in active_points."""
        point = getattr(subject_without_uranian, planet_name.lower())
        assert point is None, f"{planet_name} should not be in default chart"


class TestUranianPlanetsConfig:
    """Test configuration presets for Uranian planets."""

    def test_uranian_active_points_preset(self):
        """URANIAN_ACTIVE_POINTS should contain exactly 8 planets."""
        assert len(URANIAN_ACTIVE_POINTS) == 8
        for name in URANIAN_NAMES:
            assert name in URANIAN_ACTIVE_POINTS

    def test_uranian_in_all_active_points(self):
        """ALL_ACTIVE_POINTS should include Uranian planets."""
        for name in URANIAN_NAMES:
            assert name in ALL_ACTIVE_POINTS


class TestUranianPlanetsAspects:
    """Test that aspects involving Uranian planets are correctly calculated."""

    def test_aspects_with_uranian_planets(self, subject_with_uranian):
        """Should calculate aspects involving Uranian planets."""
        aspects = AspectsFactory.single_chart_aspects(subject_with_uranian)
        uranian_aspects = [
            a for a in aspects.aspects
            if a.p1_name in URANIAN_NAMES or a.p2_name in URANIAN_NAMES
        ]
        # At least some aspects should involve Uranian planets
        assert len(uranian_aspects) > 0, "Should have at least one aspect involving Uranian planets"


class TestUranianPlanetsSVG:
    """Test SVG chart generation with Uranian planets."""

    def test_natal_chart_svg_with_uranian(self, subject_with_uranian, tmp_path):
        """Should generate SVG containing Uranian planet glyphs."""
        chart_data = ChartDataFactory.create_natal_chart_data(subject_with_uranian)
        drawer = ChartDrawer(chart_data=chart_data, theme="dark")
        drawer.save_svg(output_path=str(tmp_path), filename="uranian_natal")

        svg_file = tmp_path / "uranian_natal.svg"
        assert svg_file.exists(), "SVG file should be created"

        svg_content = svg_file.read_text()
        assert len(svg_content) > 1000, "SVG should have substantial content"

    def test_natal_chart_modern_svg_with_uranian(self, subject_with_uranian, tmp_path):
        """Should generate modern-style SVG with Uranian planets."""
        chart_data = ChartDataFactory.create_natal_chart_data(subject_with_uranian)
        drawer = ChartDrawer(chart_data=chart_data, theme="dark")
        drawer.save_svg(output_path=str(tmp_path), filename="uranian_modern", style="modern")

        svg_file = tmp_path / "uranian_modern.svg"
        assert svg_file.exists(), "Modern SVG file should be created"


class TestUranianSweReference:
    """Compare factory Uranian planet positions with direct swe.calc_ut() calls."""

    URANIAN_SWE_IDS = {
        "cupido": 40,
        "hades": 41,
        "poseidon": 47,
    }

    @pytest.mark.parametrize("attr,swe_id", [
        ("cupido", 40),
        ("hades", 41),
        ("poseidon", 47),
    ])
    def test_uranian_longitude_matches_swe(self, subject_with_uranian, attr, swe_id):
        """Factory Uranian abs_pos must match swe.calc_ut() longitude."""
        import swisseph as swe
        from pathlib import Path

        swe.set_ephe_path(str(Path(__file__).parents[2] / "kerykeion" / "sweph"))

        jd = subject_with_uranian.julian_day
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED

        expected_lng = swe.calc_ut(jd, swe_id, iflag)[0][0]

        point = getattr(subject_with_uranian, attr)
        assert point is not None, f"{attr} should be calculated"
        assert point.abs_pos == pytest.approx(expected_lng, abs=0.01), (
            f"{attr} abs_pos {point.abs_pos} != swe longitude {expected_lng}"
        )
