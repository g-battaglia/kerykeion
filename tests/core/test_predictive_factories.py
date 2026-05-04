# -*- coding: utf-8 -*-
"""Regression tests for predictive factories."""

from functools import lru_cache

import pytest

import kerykeion
from kerykeion import (
    AstrologicalSubjectFactory,
    MidpointFactory,
    SecondaryProgressionFactory,
    SolarArcFactory,
)
from kerykeion.ephemeris_backend import swe
from kerykeion.schemas import KerykeionException
from kerykeion.secondary_progressions.secondary_progression_factory import DAYS_PER_TROPICAL_YEAR


@lru_cache(maxsize=1)
def _subject():
    return AstrologicalSubjectFactory.from_birth_data(
        "Predictive Test",
        1990,
        6,
        15,
        14,
        30,
        lng=12.5,
        lat=41.9,
        tz_str="Europe/Rome",
        city="Rome",
        nation="IT",
        online=False,
    )


# ─── Top-level exports ────────────────────────────────────────────────


def test_predictive_factories_are_in_top_level_all():
    expected_exports = {
        "MidpointFactory",
        "MidpointModel",
        "MidpointAspectModel",
        "SecondaryProgressionFactory",
        "SolarArcFactory",
        "SolarArcDirectedAspect",
        "SolarArcDirectedPoint",
        "SolarArcSubjectModel",
    }

    assert expected_exports <= set(kerykeion.__all__)
    for export in expected_exports:
        assert hasattr(kerykeion, export)


# ─── MidpointFactory ──────────────────────────────────────────────────


def test_midpoint_defaults_include_lunar_nodes():
    midpoints = MidpointFactory.compute(_subject(), compute_aspects=False)
    pairs = {(midpoint.point_a, midpoint.point_b) for midpoint in midpoints}

    assert ("True_North_Lunar_Node", "True_South_Lunar_Node") in pairs
    assert any("True_North_Lunar_Node" in pair for pair in pairs)
    assert any("True_South_Lunar_Node" in pair for pair in pairs)


def test_midpoint_pair_count():
    """Default points → C(n, 2) unordered pairs."""
    from math import comb
    from kerykeion.settings.chart_defaults import DEFAULT_PREDICTIVE_POINTS

    midpoints = MidpointFactory.compute(_subject(), compute_aspects=False)
    n = len(set(DEFAULT_PREDICTIVE_POINTS))
    assert len(midpoints) == comb(n, 2)


def test_midpoint_shorter_arc_same_point():
    """Midpoint of a point with itself is the point."""
    result = MidpointFactory._shorter_arc_midpoint(45.0, 45.0)
    assert abs(result - 45.0) < 1e-9


def test_midpoint_shorter_arc_simple():
    """10° and 80° → midpoint at 45°."""
    result = MidpointFactory._shorter_arc_midpoint(10.0, 80.0)
    assert abs(result - 45.0) < 1e-9


def test_midpoint_shorter_arc_crosses_zero():
    """350° and 10° → midpoint at 0° (shorter arc crosses 0°)."""
    result = MidpointFactory._shorter_arc_midpoint(350.0, 10.0)
    assert abs(result - 0.0) < 1e-9 or abs(result - 360.0) < 1e-9


def test_midpoint_shorter_arc_at_180():
    """0° and 180° → separation is exactly 180°, midpoint at 90°."""
    result = MidpointFactory._shorter_arc_midpoint(0.0, 180.0)
    assert abs(result - 90.0) < 1e-9


def test_midpoint_sign_and_position():
    sign, pos = MidpointFactory._sign_and_position(45.0)
    assert sign == "Tau"
    assert abs(pos - 15.0) < 1e-9


def test_midpoint_sign_and_position_boundary():
    """Exactly 0° should be Aries 0°."""
    sign, pos = MidpointFactory._sign_and_position(0.0)
    assert sign == "Ari"
    assert abs(pos) < 1e-9


def test_midpoint_sign_and_position_end_of_zodiac():
    """359° should be Pisces 29°."""
    sign, pos = MidpointFactory._sign_and_position(359.0)
    assert sign == "Pis"
    assert abs(pos - 29.0) < 1e-9


def test_midpoint_modulus_90():
    midpoints = MidpointFactory.compute(_subject(), compute_aspects=False)
    for m in midpoints:
        assert 0.0 <= m.midpoint_modulus_90 < 90.0
        assert abs(m.midpoint_modulus_90 - (m.midpoint_abs_pos % 90.0)) < 1e-9


def test_midpoint_aspect_detection():
    """With a wide enough orb, at least some midpoints should have aspects."""
    midpoints = MidpointFactory.compute(_subject(), compute_aspects=True, aspect_orb=2.0)
    total_aspects = sum(len(m.aspects_to_midpoint) for m in midpoints)
    assert total_aspects > 0


def test_midpoint_no_aspects_when_disabled():
    midpoints = MidpointFactory.compute(_subject(), compute_aspects=False)
    for m in midpoints:
        assert len(m.aspects_to_midpoint) == 0


def test_midpoint_custom_active_points():
    midpoints = MidpointFactory.compute(
        _subject(),
        active_points=["Sun", "Moon", "Mercury"],
        compute_aspects=False,
    )
    assert len(midpoints) == 3  # C(3, 2) = 3
    names = set()
    for m in midpoints:
        names.add(m.point_a)
        names.add(m.point_b)
    assert names == {"Sun", "Moon", "Mercury"}


def test_midpoint_fewer_than_two_points_returns_empty():
    midpoints = MidpointFactory.compute(
        _subject(),
        active_points=["Sun"],
        compute_aspects=False,
    )
    assert midpoints == []


def test_midpoint_empty_active_points_returns_empty():
    midpoints = MidpointFactory.compute(
        _subject(),
        active_points=[],
        compute_aspects=False,
    )
    assert midpoints == []


def test_midpoint_empty_aspects_disables_aspect_detection():
    midpoints = MidpointFactory.compute(
        _subject(),
        compute_aspects=True,
        aspect_orb=2.0,
        aspects=[],
    )
    assert all(len(m.aspects_to_midpoint) == 0 for m in midpoints)


# ─── SecondaryProgressionFactory ──────────────────────────────────────


def test_secondary_progression_basic():
    progressed = SecondaryProgressionFactory.compute(_subject(), target_year=2030)
    assert progressed.sun is not None
    assert progressed.moon is not None
    assert "Progressed" in progressed.name


def test_secondary_progression_name_contains_target_date():
    progressed = SecondaryProgressionFactory.compute(
        _subject(),
        target_iso_utc_datetime="2026-04-25T00:00:00Z",
    )
    assert "2026-04-25" in progressed.name


def test_secondary_progression_custom_name():
    progressed = SecondaryProgressionFactory.compute(
        _subject(),
        target_year=2030,
        progressed_subject_name="Custom Name",
    )
    assert progressed.name == "Custom Name"


def test_secondary_progression_sun_advances_roughly_1_deg_per_year():
    natal = _subject()
    progressed = SecondaryProgressionFactory.compute(natal, target_year=2030)
    natal_sun = natal.sun.abs_pos
    progressed_sun = progressed.sun.abs_pos
    delta = (progressed_sun - natal_sun) % 360.0
    assert 30.0 < delta < 50.0  # ~40 years * ~1°/year


def test_secondary_progression_bce_subject():
    natal = AstrologicalSubjectFactory.from_birth_data(
        "BCE Test",
        -500,
        3,
        21,
        12,
        0,
        lng=23.7,
        lat=37.97,
        tz_str="Etc/GMT",
        online=False,
    )

    progressed = SecondaryProgressionFactory.compute(natal, target_year=-460)

    target_jd = swe.julday(-460, 1, 1, 0.0, swe.JUL_CAL)
    expected_jd = natal.julian_day + (
        (target_jd - natal.julian_day) / DAYS_PER_TROPICAL_YEAR
    )
    assert progressed.sun is not None
    assert progressed.year < 1
    assert progressed.julian_day == pytest.approx(expected_jd, abs=2e-5)


def test_secondary_progression_bce_iso_target_matches_year_target():
    natal = AstrologicalSubjectFactory.from_birth_data(
        "BCE Test",
        -500,
        3,
        21,
        12,
        0,
        lng=23.7,
        lat=37.97,
        tz_str="Etc/GMT",
        online=False,
    )

    from_year = SecondaryProgressionFactory.compute(natal, target_year=-460)
    from_iso = SecondaryProgressionFactory.compute(
        natal,
        target_iso_utc_datetime="-0460-01-01T00:00:00+00:00",
    )

    assert from_iso.julian_day == pytest.approx(from_year.julian_day, abs=2e-5)


def test_secondary_progression_ce_subject_bce_target_year_is_computable():
    progressed = SecondaryProgressionFactory.compute(_subject(), target_year=-500)

    assert progressed.sun is not None
    assert progressed.julian_day < _subject().julian_day


def test_secondary_progression_error_both_targets():
    with pytest.raises(KerykeionException, match=r"at most one|exactly one"):
        SecondaryProgressionFactory.compute(
            _subject(),
            target_iso_utc_datetime="2026-01-01T00:00:00Z",
            target_year=2026,
        )


def test_secondary_progression_error_no_target():
    with pytest.raises(KerykeionException, match=r"one of"):
        SecondaryProgressionFactory.compute(_subject())


# ─── SolarArcFactory ─────────────────────────────────────────────────


def test_solar_arc_defaults_direct_lunar_nodes():
    solar_arc = SolarArcFactory.compute(_subject(), target_year=2030, compute_aspects=False)
    directed_names = {point.name for point in solar_arc.directed_points}

    assert "True_North_Lunar_Node" in directed_names
    assert "True_South_Lunar_Node" in directed_names


def test_solar_arc_target_year_reports_requested_target_datetime():
    solar_arc = SolarArcFactory.compute(_subject(), target_year=2030, compute_aspects=False)

    assert solar_arc.target_iso_utc_datetime == "2030-01-01T00:00:00.000000Z"


def test_solar_arc_preserves_inter_point_geometry():
    """All directed points should advance by the same arc."""
    solar_arc = SolarArcFactory.compute(_subject(), target_year=2030, compute_aspects=False)
    arc = solar_arc.solar_arc
    for point in solar_arc.directed_points:
        expected = (point.natal_abs_pos + arc) % 360.0
        assert abs(point.directed_abs_pos - expected) < 1e-9


def test_solar_arc_sign_changed_flag():
    solar_arc = SolarArcFactory.compute(_subject(), target_year=2030, compute_aspects=False)
    for point in solar_arc.directed_points:
        assert point.sign_changed == (point.natal_sign != point.directed_sign)


def test_solar_arc_aspect_detection():
    """With aspects enabled, there should be at least one directed-to-natal hit."""
    solar_arc = SolarArcFactory.compute(
        _subject(), target_year=2030, compute_aspects=True, aspect_orb=1.5,
    )
    assert len(solar_arc.directed_to_natal_aspects) > 0


def test_solar_arc_no_aspects_when_disabled():
    solar_arc = SolarArcFactory.compute(_subject(), target_year=2030, compute_aspects=False)
    assert len(solar_arc.directed_to_natal_aspects) == 0


def test_solar_arc_filtered_sources_full_natal_targets():
    """active_points filters directed sources but aspects check the full natal chart."""
    solar_arc = SolarArcFactory.compute(
        _subject(),
        target_year=2030,
        active_points=["Sun"],
        compute_aspects=True,
        aspect_orb=2.0,
    )
    assert len(solar_arc.directed_points) == 1
    assert solar_arc.directed_points[0].name == "Sun"
    natal_targets_hit = {asp.natal_point for asp in solar_arc.directed_to_natal_aspects}
    assert all(asp.directed_point == "Sun" for asp in solar_arc.directed_to_natal_aspects)
    assert len(natal_targets_hit - {"Sun"}) > 0, "Should find aspects to natal points beyond Sun"


def test_solar_arc_empty_active_points_return_no_points_or_aspects():
    solar_arc = SolarArcFactory.compute(
        _subject(),
        target_year=2030,
        active_points=[],
        compute_aspects=True,
    )
    assert solar_arc.directed_points == []
    assert solar_arc.directed_to_natal_aspects == []


def test_solar_arc_empty_aspects_disables_aspect_detection():
    solar_arc = SolarArcFactory.compute(
        _subject(),
        target_year=2030,
        compute_aspects=True,
        aspect_orb=2.0,
        aspects=[],
    )
    assert solar_arc.directed_to_natal_aspects == []


def test_solar_arc_roughly_1_deg_per_year():
    natal = _subject()
    solar_arc = SolarArcFactory.compute(natal, target_year=2030, compute_aspects=False)
    years = 2030 - 1990
    assert abs(solar_arc.solar_arc - years) < 5.0  # ~1°/year ± ephemeris deviation


def test_solar_arc_bce_subject():
    natal = AstrologicalSubjectFactory.from_birth_data(
        "BCE Test",
        -500,
        3,
        21,
        12,
        0,
        lng=23.7,
        lat=37.97,
        tz_str="Etc/GMT",
        online=False,
    )

    solar_arc = SolarArcFactory.compute(natal, target_year=-460, compute_aspects=False)

    assert solar_arc.solar_arc > 0
    assert solar_arc.target_iso_utc_datetime == "-0460-01-01T00:00:00+00:00"


def test_solar_arc_uses_forward_progressed_sun_delta_beyond_180_degrees():
    natal = _subject()
    progressed = SecondaryProgressionFactory.compute(natal, target_year=2200)
    solar_arc = SolarArcFactory.compute(natal, target_year=2200, compute_aspects=False)
    expected_arc = (progressed.sun.abs_pos - natal.sun.abs_pos) % 360.0

    assert 180.0 < expected_arc < 360.0
    assert abs(solar_arc.solar_arc - expected_arc) < 1e-9


def test_solar_arc_iso_target():
    solar_arc = SolarArcFactory.compute(
        _subject(),
        target_iso_utc_datetime="2030-06-15T12:00:00Z",
        compute_aspects=False,
    )
    assert solar_arc.target_iso_utc_datetime == "2030-06-15T12:00:00.000000Z"


def test_solar_arc_error_both_targets():
    with pytest.raises(KerykeionException, match=r"at most one|exactly one"):
        SolarArcFactory.compute(
            _subject(),
            target_iso_utc_datetime="2030-01-01T00:00:00Z",
            target_year=2030,
            compute_aspects=False,
        )


def test_solar_arc_error_no_target():
    with pytest.raises(KerykeionException, match=r"one of"):
        SolarArcFactory.compute(_subject(), compute_aspects=False)


# ─── Numerical baselines ─────────────────────────────────────────────


def test_baseline_ce_progression_positions():
    """Regression baseline: CE natal (Rome, 1990-06-15) progressed to 2026."""
    natal = _subject()
    progressed = SecondaryProgressionFactory.compute(natal, target_year=2026)
    assert natal.julian_day == pytest.approx(2448058.020833, abs=1e-3)
    assert progressed.julian_day == pytest.approx(2448093.567662, abs=1e-3)
    assert progressed.sun.abs_pos == pytest.approx(118.06, abs=0.1)
    assert progressed.moon.abs_pos == pytest.approx(103.91, abs=0.5)


def test_baseline_ce_solar_arc():
    """Regression baseline: CE solar arc for 1990 → 2026."""
    arc = SolarArcFactory.compute(_subject(), target_year=2026, compute_aspects=False)
    assert arc.solar_arc == pytest.approx(33.91, abs=0.1)


@lru_cache(maxsize=1)
def _bce_subject():
    return AstrologicalSubjectFactory.from_birth_data(
        "BCE Baseline", -500, 3, 21, 12, 0,
        lng=23.7, lat=37.97, tz_str="Etc/GMT", online=False,
    )


def test_baseline_bce_natal_positions():
    """Regression baseline: BCE natal (-500, Athens)."""
    natal = _bce_subject()
    assert natal.julian_day == pytest.approx(1538512.934, abs=1e-2)
    assert natal.sun.abs_pos == pytest.approx(355.04, abs=0.1)
    assert natal.moon.abs_pos == pytest.approx(227.27, abs=0.5)


def test_baseline_bce_progression_positions():
    """Regression baseline: BCE natal progressed to -460."""
    progressed = SecondaryProgressionFactory.compute(_bce_subject(), target_year=-460)
    assert progressed.julian_day == pytest.approx(1538552.714, abs=1e-2)
    assert progressed.sun.abs_pos == pytest.approx(33.33, abs=0.1)
    assert progressed.year < 1


def test_baseline_bce_solar_arc():
    """Regression baseline: BCE solar arc for -500 → -460."""
    arc = SolarArcFactory.compute(_bce_subject(), target_year=-460, compute_aspects=False)
    assert arc.solar_arc == pytest.approx(38.29, abs=0.1)


# ─── Custom ayanamsa (USER sidereal mode) ────────────────────────────


@lru_cache(maxsize=1)
def _user_sidereal_subject():
    return AstrologicalSubjectFactory.from_birth_data(
        "Sidereal USER Test",
        1990, 6, 15, 14, 30,
        lng=12.5, lat=41.9, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
        zodiac_type="Sidereal",
        sidereal_mode="USER",
        custom_ayanamsa_t0=2451545.0,
        custom_ayanamsa_ayan_t0=23.5,
    )


def test_custom_ayanamsa_persisted_on_subject():
    subject = _user_sidereal_subject()
    assert subject.custom_ayanamsa_t0 == 2451545.0
    assert subject.custom_ayanamsa_ayan_t0 == 23.5


def test_secondary_progression_with_user_sidereal():
    subject = _user_sidereal_subject()
    progressed = SecondaryProgressionFactory.compute(subject, target_year=2026)
    assert progressed.sun is not None
    assert progressed.sidereal_mode == "USER"
    assert progressed.custom_ayanamsa_t0 == 2451545.0
    assert progressed.custom_ayanamsa_ayan_t0 == 23.5


def test_solar_arc_with_user_sidereal():
    subject = _user_sidereal_subject()
    solar_arc = SolarArcFactory.compute(subject, target_year=2026, compute_aspects=False)
    assert solar_arc.solar_arc > 0
    assert len(solar_arc.directed_points) > 0


# ─── Solar arc natal targets use subject's active_points ─────────────


def test_solar_arc_natal_targets_include_extra_active_points():
    """Natal targets should use the subject's active_points, not DEFAULT_PREDICTIVE_POINTS."""
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Extra Points Test",
        1990, 6, 15, 14, 30,
        lng=12.5, lat=41.9, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
        active_points=[
            "Sun", "Moon", "Mercury", "Venus", "Mars",
            "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
            "True_North_Lunar_Node", "True_South_Lunar_Node",
            "Chiron", "Mean_Lilith", "Ascendant", "Medium_Coeli",
            "Vertex",
        ],
    )
    assert subject.vertex is not None

    solar_arc = SolarArcFactory.compute(
        subject,
        active_points=["Sun"],
        target_year=2030,
        compute_aspects=True,
        aspect_orb=180.0,
    )
    natal_targets_hit = {asp.natal_point for asp in solar_arc.directed_to_natal_aspects}
    assert "Vertex" in natal_targets_hit, (
        "Vertex should appear as a natal target since it's in the subject's active_points"
    )
