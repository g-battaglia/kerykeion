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
        "ProgressedToNatalAspect",
        "SecondaryProgressionFactory",
        "SecondaryProgressionsResult",
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
    pairs = {frozenset((midpoint.point_a, midpoint.point_b)) for midpoint in midpoints}

    assert any("True_North_Lunar_Node" in pair for pair in pairs)


def test_midpoint_pair_count():
    """Default points → C(n, 2) unordered pairs."""
    from math import comb

    midpoints = MidpointFactory.compute(_subject(), compute_aspects=False)
    unique_points = {p for m in midpoints for p in (m.point_a, m.point_b)}
    n = len(unique_points)
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


def test_secondary_progression_bce_iso_round_trips_seconds():
    target_jd = SecondaryProgressionFactory._target_to_jd(
        "-0460-01-01T00:00:13Z",
        None,
    )

    assert SecondaryProgressionFactory._jd_to_utc_iso(target_jd) == "-0460-01-01T00:00:13.000000Z"


def test_secondary_progression_rejects_naive_target_iso():
    with pytest.raises(KerykeionException, match="explicit UTC offset"):
        SecondaryProgressionFactory.compute(
            _subject(),
            target_iso_utc_datetime="2026-04-25T00:00:00",
        )


def test_secondary_progression_large_ce_target_year_formats_without_datetime():
    target_jd = SecondaryProgressionFactory._target_to_jd(None, 10000)

    assert SecondaryProgressionFactory._jd_to_utc_iso(target_jd) == "+10000-01-01T00:00:00.000000Z"


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


def test_solar_arc_target_year_reports_requested_target_datetime():
    solar_arc = SolarArcFactory.compute(_subject(), target_year=2030, compute_aspects=False)

    assert solar_arc.target_iso_utc_datetime == "2030-01-01T00:00:00.000000Z"


def test_solar_arc_large_ce_target_year_reports_requested_target_datetime():
    solar_arc = SolarArcFactory.compute(_subject(), target_year=10000, compute_aspects=False)

    assert solar_arc.target_iso_utc_datetime == "+10000-01-01T00:00:00.000000Z"


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
        aspect_orb=5.0,
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
    assert solar_arc.target_iso_utc_datetime == "-0460-01-01T00:00:00.000000Z"


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


def test_solar_arc_bce_iso_target_preserves_seconds():
    solar_arc = SolarArcFactory.compute(
        _bce_subject(),
        target_iso_utc_datetime="-0460-01-01T00:00:13Z",
        compute_aspects=False,
    )

    assert solar_arc.target_iso_utc_datetime == "-0460-01-01T00:00:13.000000Z"


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


# ─── SecondaryProgressionFactory.compute_full() ─────────────────────


def test_compute_full_returns_result_model():
    result = SecondaryProgressionFactory.compute_full(
        _subject(), target_iso_utc_datetime="2026-01-01T00:00:00Z",
    )
    assert isinstance(result, kerykeion.SecondaryProgressionsResult)
    assert result.natal_name == "Predictive Test"
    assert result.target_iso_utc_datetime == "2026-01-01T00:00:00.000000Z"
    assert result.ephemeris_iso_utc_datetime is not None
    assert result.progressed_subject.sun is not None


def test_compute_full_ephemeris_date_is_near_birth():
    """The ephemeris date should be ~36 days after birth for a 36-year progression."""
    result = SecondaryProgressionFactory.compute_full(
        _subject(), target_iso_utc_datetime="2026-01-01T00:00:00Z",
    )
    # Born 1990-06-15, progressed ~35.5 years → ephemeris date ~35.5 days after birth → ~July 1990
    assert result.ephemeris_iso_utc_datetime.startswith("1990-07")


def test_compute_full_default_aspects_are_ptolemaic():
    """Default: only 5 Ptolemaic aspects (no quintile, semi-sextile, etc.)."""
    result = SecondaryProgressionFactory.compute_full(
        _subject(), target_iso_utc_datetime="2026-01-01T00:00:00Z",
    )
    aspect_names = {a.aspect for a in result.progressed_to_natal_aspects}
    ptolemaic = {"conjunction", "opposition", "trine", "sextile", "square"}
    assert aspect_names <= ptolemaic, f"Non-Ptolemaic aspects found: {aspect_names - ptolemaic}"


def test_compute_full_all_aspects_when_explicit():
    """Passing all aspect names should return more hits than Ptolemaic only."""
    all_names = [
        "conjunction", "opposition", "trine", "sextile", "square",
        "quintile", "semi-sextile", "semi-square", "sesquiquadrate",
        "biquintile", "quincunx",
    ]
    result_ptolemaic = SecondaryProgressionFactory.compute_full(
        _subject(), target_iso_utc_datetime="2026-01-01T00:00:00Z",
    )
    result_all = SecondaryProgressionFactory.compute_full(
        _subject(), target_iso_utc_datetime="2026-01-01T00:00:00Z",
        aspects=all_names,
    )
    assert len(result_all.progressed_to_natal_aspects) > len(result_ptolemaic.progressed_to_natal_aspects)


def test_compute_full_configurable_orb():
    """Tighter orb should yield fewer aspects."""
    result_3 = SecondaryProgressionFactory.compute_full(
        _subject(), target_iso_utc_datetime="2026-01-01T00:00:00Z", aspect_orb=3.0,
    )
    result_1 = SecondaryProgressionFactory.compute_full(
        _subject(), target_iso_utc_datetime="2026-01-01T00:00:00Z", aspect_orb=1.0,
    )
    assert len(result_1.progressed_to_natal_aspects) < len(result_3.progressed_to_natal_aspects)


def test_compute_full_no_aspects_when_disabled():
    result = SecondaryProgressionFactory.compute_full(
        _subject(), target_iso_utc_datetime="2026-01-01T00:00:00Z", compute_aspects=False,
    )
    assert result.progressed_to_natal_aspects == []
    assert result.progressed_subject.sun is not None


def test_compute_full_includes_self_conjunctions():
    """SP self-conjunctions are meaningful (each planet moves at its own rate)."""
    natal = _subject()
    result = SecondaryProgressionFactory.compute_full(
        natal, target_iso_utc_datetime="2026-01-01T00:00:00Z", aspect_orb=3.0,
    )
    self_conjs = [a for a in result.progressed_to_natal_aspects
                  if a.progressed_point == a.natal_point and a.aspect == "conjunction"]
    assert len(self_conjs) > 0, "Should include self-conjunctions (e.g. Saturn conj Saturn)"


def test_compute_full_custom_active_points():
    result = SecondaryProgressionFactory.compute_full(
        _subject(),
        target_iso_utc_datetime="2026-01-01T00:00:00Z",
        active_points=["Sun", "Moon"],
    )
    progressed_names = {a.progressed_point for a in result.progressed_to_natal_aspects}
    assert progressed_names <= {"Sun", "Moon"}


# ─── compute_full baselines ─────────────────────────────────────────


def test_baseline_compute_full_ce_progression():
    """Regression baseline: CE compute_full (Rome, 1990-06-15) → 2026."""
    result = SecondaryProgressionFactory.compute_full(
        _subject(), target_iso_utc_datetime="2026-01-01T00:00:00Z",
    )
    assert result.progressed_subject.sun.abs_pos == pytest.approx(118.06, abs=0.1)
    assert result.progressed_subject.moon.abs_pos == pytest.approx(103.91, abs=0.5)
    assert result.ephemeris_iso_utc_datetime.startswith("1990-07-21")
    assert len(result.progressed_to_natal_aspects) == 31


def test_baseline_compute_full_tight_orb():
    """Regression baseline: 1° orb yields exactly 8 aspects."""
    result = SecondaryProgressionFactory.compute_full(
        _subject(), target_iso_utc_datetime="2026-01-01T00:00:00Z", aspect_orb=1.0,
    )
    assert len(result.progressed_to_natal_aspects) == 8


def test_baseline_solar_arc_ptolemaic_default():
    """Regression baseline: SA with 3° Ptolemaic default."""
    sa = SolarArcFactory.compute(
        _subject(), target_iso_utc_datetime="2026-01-01T00:00:00Z",
    )
    assert sa.solar_arc == pytest.approx(33.91, abs=0.1)
    assert len(sa.directed_to_natal_aspects) == 27
    aspect_names = {a.aspect for a in sa.directed_to_natal_aspects}
    ptolemaic = {"conjunction", "opposition", "trine", "sextile", "square"}
    assert aspect_names <= ptolemaic


# ─── Reference cross-validation baselines (12 SP, 12 SA) ────────────
#
# Ephemeris dates verified against an independent online progressed-chart
# calculator; kerykeion must stay within 3 minutes of the reference.


_REFERENCE_EPHEMERIS = {
    # name: (year, month, day, hour, minute) — independently verified (UT)
    "Rome1990": (1990, 7, 21, 1, 38),
    "Milan1985": (1985, 5, 1, 2, 2),
    "London1975": (1976, 2, 13, 4, 15),
    "NYC1960": (1960, 9, 8, 13, 50),
    "Tokyo1988": (1988, 12, 18, 5, 31),
    "Sydney2000": (2000, 1, 26, 13, 4),
    "Berlin1945": (1945, 7, 28, 1, 39),
    "Paris1968": (1968, 6, 27, 21, 35),
    "Mumbai1955": (1955, 10, 24, 12, 41),
    "BA1982": (1982, 8, 12, 6, 12),
    "Cairo1970": (1970, 5, 9, 22, 13),
    "Moscow1991": (1992, 1, 28, 22, 26),
}

_REFERENCE_SUBJECTS = [
    ("Rome1990", 1990, 6, 15, 14, 30, 41.9, 12.5, "Europe/Rome"),
    ("Milan1985", 1985, 3, 21, 8, 15, 45.46, 9.19, "Europe/Rome"),
    ("London1975", 1975, 12, 25, 3, 45, 51.51, -0.13, "Europe/London"),
    ("NYC1960", 1960, 7, 4, 22, 0, 40.71, -74.01, "America/New_York"),
    ("Tokyo1988", 1988, 11, 11, 11, 11, 35.68, 139.77, "Asia/Tokyo"),
    ("Sydney2000", 2000, 1, 1, 0, 0, -33.87, 151.21, "Australia/Sydney"),
    ("Berlin1945", 1945, 5, 8, 12, 0, 52.52, 13.41, "Europe/Berlin"),
    ("Paris1968", 1968, 5, 1, 6, 30, 48.86, 2.35, "Europe/Paris"),
    ("Mumbai1955", 1955, 8, 15, 9, 0, 19.08, 72.88, "Asia/Kolkata"),
    ("BA1982", 1982, 6, 29, 15, 0, -34.60, -58.38, "America/Argentina/Buenos_Aires"),
    ("Cairo1970", 1970, 3, 15, 5, 0, 30.04, 31.24, "Africa/Cairo"),
    ("Moscow1991", 1991, 12, 25, 23, 59, 55.76, 37.62, "Europe/Moscow"),
]


@pytest.mark.parametrize(
    "name,yr,mo,dy,hr,mn,lat,lng,tz",
    _REFERENCE_SUBJECTS,
    ids=[s[0] for s in _REFERENCE_SUBJECTS],
)
def test_reference_ephemeris_date(name, yr, mo, dy, hr, mn, lat, lng, tz):
    """Ephemeris date must match the reference within 3 minutes (180s)."""
    from datetime import datetime, timezone

    natal = AstrologicalSubjectFactory.from_birth_data(
        name, yr, mo, dy, hr, mn, lng=lng, lat=lat, tz_str=tz, online=False,
    )
    result = SecondaryProgressionFactory.compute_full(
        natal, target_iso_utc_datetime="2026-01-01T00:00:00Z",
    )
    our_dt = datetime.fromisoformat(
        result.ephemeris_iso_utc_datetime.replace("Z", "+00:00")
    )
    ref_y, ref_mo, ref_d, ref_h, ref_mn = _REFERENCE_EPHEMERIS[name]
    ref_dt = datetime(ref_y, ref_mo, ref_d, ref_h, ref_mn, tzinfo=timezone.utc)
    diff = abs((our_dt - ref_dt).total_seconds())
    assert diff < 180, f"Ephemeris date off by {diff:.0f}s (>180s): ours={our_dt} vs reference={ref_dt}"


@pytest.mark.parametrize(
    "name,yr,mo,dy,hr,mn,lat,lng,tz",
    _REFERENCE_SUBJECTS,
    ids=[s[0] for s in _REFERENCE_SUBJECTS],
)
def test_reference_solar_arc_positive(name, yr, mo, dy, hr, mn, lat, lng, tz):
    """Solar arc for a future target must be positive."""
    natal = AstrologicalSubjectFactory.from_birth_data(
        name, yr, mo, dy, hr, mn, lng=lng, lat=lat, tz_str=tz, online=False,
    )
    sa = SolarArcFactory.compute(
        natal, target_iso_utc_datetime="2026-01-01T00:00:00Z",
    )
    assert sa.solar_arc > 0
    assert len(sa.directed_to_natal_aspects) >= 0
    aspect_names = {a.aspect for a in sa.directed_to_natal_aspects}
    ptolemaic = {"conjunction", "opposition", "trine", "sextile", "square"}
    assert aspect_names <= ptolemaic


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


# ─── Wide internal-consistency sweep across diverse subjects ─────────
#
# A large parametrized set exercising the predictive factories across many
# cities, epochs, hemispheres and target dates. Each case verifies the
# mathematical invariants of the technique rather than a fixed baseline.

_SWEEP_SUBJECTS = [
    # (name, year, month, day, hour, minute, lat, lng, tz, target_year)
    ("Rome", 1990, 6, 15, 14, 30, 41.9, 12.5, "Europe/Rome", 2026),
    ("Milan", 1985, 3, 21, 8, 15, 45.46, 9.19, "Europe/Rome", 2030),
    ("London", 1975, 12, 25, 3, 45, 51.51, -0.13, "Europe/London", 2026),
    ("NYC", 1960, 7, 4, 22, 0, 40.71, -74.01, "America/New_York", 2040),
    ("Tokyo", 1988, 11, 11, 11, 11, 35.68, 139.77, "Asia/Tokyo", 2026),
    ("Sydney", 2000, 1, 1, 0, 0, -33.87, 151.21, "Australia/Sydney", 2050),
    ("Berlin", 1955, 5, 8, 12, 0, 52.52, 13.41, "Europe/Berlin", 2026),
    ("Paris", 1968, 5, 1, 6, 30, 48.86, 2.35, "Europe/Paris", 2035),
    ("Mumbai", 1955, 8, 15, 9, 0, 19.08, 72.88, "Asia/Kolkata", 2026),
    ("BuenosAires", 1982, 6, 29, 15, 0, -34.60, -58.38, "America/Argentina/Buenos_Aires", 2026),
    ("Cairo", 1970, 3, 15, 5, 0, 30.04, 31.24, "Africa/Cairo", 2026),
    ("Moscow", 1991, 12, 25, 23, 59, 55.76, 37.62, "Europe/Moscow", 2026),
    ("LosAngeles", 1999, 9, 9, 9, 9, 34.05, -118.24, "America/Los_Angeles", 2026),
    ("Reykjavik", 1980, 6, 21, 0, 0, 64.15, -21.94, "Atlantic/Reykjavik", 2026),
    ("CapeTown", 1995, 2, 14, 14, 14, -33.93, 18.42, "Africa/Johannesburg", 2026),
    ("Beijing", 1978, 10, 1, 10, 0, 39.90, 116.40, "Asia/Shanghai", 2026),
    ("SaoPaulo", 1990, 12, 21, 18, 30, -23.55, -46.63, "America/Sao_Paulo", 2026),
    ("Athens", 1965, 4, 15, 7, 0, 37.98, 23.73, "Europe/Athens", 2026),
    ("Bangkok", 2005, 8, 8, 8, 8, 13.76, 100.50, "Asia/Bangkok", 2026),
    ("Toronto", 1992, 2, 29, 12, 0, 43.65, -79.38, "America/Toronto", 2026),
    ("Madrid", 1973, 7, 18, 16, 20, 40.42, -3.70, "Europe/Madrid", 2026),
    ("Oslo", 1986, 1, 20, 21, 40, 59.91, 10.75, "Europe/Oslo", 2026),
    ("Delhi", 2001, 8, 15, 2, 30, 28.61, 77.21, "Asia/Kolkata", 2026),
    ("Nairobi", 1994, 6, 1, 6, 0, -1.29, 36.82, "Africa/Nairobi", 2026),
    ("Seoul", 1989, 8, 15, 20, 20, 37.57, 126.98, "Asia/Seoul", 2026),
]


@pytest.mark.parametrize(
    "name,yr,mo,dy,hr,mn,lat,lng,tz,target_year",
    _SWEEP_SUBJECTS,
    ids=[s[0] for s in _SWEEP_SUBJECTS],
)
def test_sweep_ephemeris_matches_day_for_year_formula(name, yr, mo, dy, hr, mn, lat, lng, tz, target_year):
    """compute_full's ephemeris JD must equal natal_jd + (target - natal) / 365.25."""
    natal = AstrologicalSubjectFactory.from_birth_data(
        name, yr, mo, dy, hr, mn, lng=lng, lat=lat, tz_str=tz, online=False,
    )
    result = SecondaryProgressionFactory.compute_full(natal, target_year=target_year)

    natal_jd = natal.julian_day
    target_jd = SecondaryProgressionFactory._target_to_jd(None, target_year)
    expected_jd = natal_jd + (target_jd - natal_jd) / DAYS_PER_TROPICAL_YEAR

    progressed_jd = result.progressed_subject.julian_day
    assert progressed_jd == pytest.approx(expected_jd, abs=2e-3)


@pytest.mark.parametrize(
    "name,yr,mo,dy,hr,mn,lat,lng,tz,target_year",
    _SWEEP_SUBJECTS,
    ids=[s[0] for s in _SWEEP_SUBJECTS],
)
def test_sweep_solar_arc_equals_progressed_sun_delta(name, yr, mo, dy, hr, mn, lat, lng, tz, target_year):
    """Solar arc must equal the forward delta of the progressed Sun from natal."""
    natal = AstrologicalSubjectFactory.from_birth_data(
        name, yr, mo, dy, hr, mn, lng=lng, lat=lat, tz_str=tz, online=False,
    )
    progressed = SecondaryProgressionFactory.compute(natal, target_year=target_year)
    sa = SolarArcFactory.compute(natal, target_year=target_year, compute_aspects=False)

    expected_arc = (progressed.sun.abs_pos - natal.sun.abs_pos) % 360.0
    assert sa.solar_arc == pytest.approx(expected_arc, abs=1e-6)


@pytest.mark.parametrize(
    "name,yr,mo,dy,hr,mn,lat,lng,tz,target_year",
    _SWEEP_SUBJECTS,
    ids=[s[0] for s in _SWEEP_SUBJECTS],
)
def test_sweep_compute_full_matches_compute(name, yr, mo, dy, hr, mn, lat, lng, tz, target_year):
    """compute_full().progressed_subject must equal a bare compute() call."""
    natal = AstrologicalSubjectFactory.from_birth_data(
        name, yr, mo, dy, hr, mn, lng=lng, lat=lat, tz_str=tz, online=False,
    )
    bare = SecondaryProgressionFactory.compute(natal, target_year=target_year)
    full = SecondaryProgressionFactory.compute_full(natal, target_year=target_year)

    assert full.progressed_subject.julian_day == pytest.approx(bare.julian_day, abs=1e-9)
    assert full.progressed_subject.sun.abs_pos == pytest.approx(bare.sun.abs_pos, abs=1e-9)
    assert full.progressed_subject.moon.abs_pos == pytest.approx(bare.moon.abs_pos, abs=1e-9)


@pytest.mark.parametrize(
    "name,yr,mo,dy,hr,mn,lat,lng,tz,target_year",
    _SWEEP_SUBJECTS,
    ids=[s[0] for s in _SWEEP_SUBJECTS],
)
def test_sweep_predictive_invariants(name, yr, mo, dy, hr, mn, lat, lng, tz, target_year):
    """Cross-aspects stay Ptolemaic, within orb, and the progressed Sun
    advances at roughly one degree per year of life."""
    natal = AstrologicalSubjectFactory.from_birth_data(
        name, yr, mo, dy, hr, mn, lng=lng, lat=lat, tz_str=tz, online=False,
    )
    sp = SecondaryProgressionFactory.compute_full(natal, target_year=target_year, aspect_orb=3.0)
    sa = SolarArcFactory.compute(natal, target_year=target_year, aspect_orb=3.0)
    ptolemaic = {"conjunction", "opposition", "trine", "sextile", "square"}

    for a in sp.progressed_to_natal_aspects:
        assert a.aspect in ptolemaic
        assert a.orb <= 3.0 + 1e-6
    for a in sa.directed_to_natal_aspects:
        assert a.aspect in ptolemaic
        assert a.orb <= 3.0 + 1e-6

    years = target_year - yr
    sun_delta = (sp.progressed_subject.sun.abs_pos - natal.sun.abs_pos) % 360.0
    # ~1°/year ± ephemeris seasonal variation
    assert abs(sun_delta - years) < 8.0
