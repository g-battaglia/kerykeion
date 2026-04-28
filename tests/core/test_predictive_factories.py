# -*- coding: utf-8 -*-
"""Regression tests for predictive factories."""

import pytest

import kerykeion
from kerykeion import (
    AstrologicalSubjectFactory,
    MidpointFactory,
    SecondaryProgressionFactory,
    SolarArcFactory,
)
from kerykeion.schemas import KerykeionException
from kerykeion.midpoints.midpoint_factory import MidpointModel


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
    """16 default points → C(16, 2) = 120 unordered pairs."""
    midpoints = MidpointFactory.compute(_subject(), compute_aspects=False)
    assert len(midpoints) == 120


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
    years = 2030 - 1990
    natal_sun = natal.sun.abs_pos
    progressed_sun = progressed.sun.abs_pos
    delta = (progressed_sun - natal_sun) % 360.0
    assert 30.0 < delta < 50.0  # ~40 years * ~1°/year


def test_secondary_progression_error_both_targets():
    with pytest.raises(KerykeionException, match="exactly one"):
        SecondaryProgressionFactory.compute(
            _subject(),
            target_iso_utc_datetime="2026-01-01T00:00:00Z",
            target_year=2026,
        )


def test_secondary_progression_error_no_target():
    with pytest.raises(KerykeionException, match="one of"):
        SecondaryProgressionFactory.compute(_subject())


# ─── SolarArcFactory ─────────────────────────────────────────────────


def test_solar_arc_defaults_direct_lunar_nodes():
    solar_arc = SolarArcFactory.compute(_subject(), target_year=2030, compute_aspects=False)
    directed_names = {point.name for point in solar_arc.directed_points}

    assert "True_North_Lunar_Node" in directed_names
    assert "True_South_Lunar_Node" in directed_names


def test_solar_arc_target_year_reports_requested_target_datetime():
    solar_arc = SolarArcFactory.compute(_subject(), target_year=2030, compute_aspects=False)

    assert solar_arc.target_iso_utc_datetime == "2030-01-01T00:00:00.000Z"


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
    assert solar_arc.target_iso_utc_datetime == "2030-06-15T12:00:00.000Z"


def test_solar_arc_error_both_targets():
    with pytest.raises(KerykeionException, match="exactly one"):
        SolarArcFactory.compute(
            _subject(),
            target_iso_utc_datetime="2030-01-01T00:00:00Z",
            target_year=2030,
            compute_aspects=False,
        )


def test_solar_arc_error_no_target():
    with pytest.raises(KerykeionException, match="one of"):
        SolarArcFactory.compute(_subject(), compute_aspects=False)
