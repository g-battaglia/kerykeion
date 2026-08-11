# -*- coding: utf-8 -*-
"""
Tests for the v6 point/chart-data enrichments added for downstream products:
per-point motion_state, star-catalog constellation, chart-data angularities
and stelliums, progressed_points with sign_changed, and the precise lunar age.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import pytest

from kerykeion import ChartDataFactory, SecondaryProgressionFactory
from kerykeion.chart_data_factory import (
    ANGULARITY_ORB_DEGREES,
    STELLIUM_MIN_POINTS,
    _angular_distance,
    _compute_angularities,
    _compute_stelliums,
)
from kerykeion.fixed_stars.catalog import FixedStarCatalog, _constellation_from_nomenclature
from kerykeion.motion import MEAN_DAILY_MOTION_DEGREES, classify_motion_state

pytestmark = pytest.mark.core


# ---------------------------------------------------------------------------
# motion_state
# ---------------------------------------------------------------------------

def test_classify_motion_state_bands():
    assert classify_motion_state("Mercury", -0.5) == "retrograde"
    mean = MEAN_DAILY_MOTION_DEGREES["Mercury"]
    assert classify_motion_state("Mercury", mean * 0.01) == "stationary"
    assert classify_motion_state("Mercury", mean * 0.5) == "slow"
    assert classify_motion_state("Mercury", mean) == "average"
    assert classify_motion_state("Mercury", mean * 1.5) == "fast"


def test_classify_motion_state_unknown_bodies():
    assert classify_motion_state("Chiron", 0.05) is None
    assert classify_motion_state("Mean_North_Lunar_Node", -0.05) is None
    assert classify_motion_state("Sun", None) is None


def test_points_carry_motion_state(john_lennon):
    for field in ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"):
        point = getattr(john_lennon, field)
        assert point.motion_state is not None
        assert point.motion_state == classify_motion_state(str(point.name), point.speed)
    # The Sun is never retrograde; on a real chart it is not stationary either.
    assert john_lennon.sun.motion_state in ("slow", "average", "fast")


# ---------------------------------------------------------------------------
# Star catalog constellation
# ---------------------------------------------------------------------------

def test_constellation_from_nomenclature():
    assert _constellation_from_nomenclature("alLeo") == "Leo"
    assert _constellation_from_nomenclature("epVir") == "Virgo"
    assert _constellation_from_nomenclature("alUMi") == "Ursa Minor"
    assert _constellation_from_nomenclature(None) is None


def test_catalog_entries_carry_constellations():
    entries = FixedStarCatalog.list_all()
    assert entries, "catalog must not be empty"
    # Every entry with a REAL Bayer/Flamsteed designation must resolve; the
    # only legitimate misses are entries whose nomenclature just echoes the
    # proper name (no designation to parse).
    unresolved = [e for e in entries if e.nomenclature and not e.constellation]
    assert all(e.nomenclature == e.name for e in unresolved), [
        (e.name, e.nomenclature) for e in unresolved if e.nomenclature != e.name
    ]
    regulus = FixedStarCatalog.find("Regulus")
    assert regulus is not None and regulus.constellation == "Leo"
    # Component-letter designations resolve too.
    trapezium = FixedStarCatalog.find("th01OriA")
    if trapezium is not None:
        assert trapezium.constellation == "Orion"


# ---------------------------------------------------------------------------
# Chart-data angularities and stelliums
# ---------------------------------------------------------------------------

def test_angular_distance_wraps():
    assert _angular_distance(359.0, 1.0) == pytest.approx(2.0)
    assert _angular_distance(10.0, 190.0) == pytest.approx(180.0)


def test_angularities_respect_the_orb(john_lennon):
    angularities = _compute_angularities(john_lennon)
    for entry in angularities:
        assert entry.distance <= ANGULARITY_ORB_DEGREES
        planet = getattr(john_lennon, entry.point.lower())
        assert planet is not None
    # Sorted closest-first.
    distances = [entry.distance for entry in angularities]
    assert distances == sorted(distances)


def test_angularities_report_every_pair_within_orb(john_lennon):
    """ALL (planet, angle) pairs inside the orb are emitted — not just each
    planet's nearest angle — so an ASC/MC-only consumer can filter without
    losing a planet whose nearest angle happens to be DSC or IC."""
    wide = _compute_angularities(john_lennon, orb=180.0)
    # With an unbounded orb every present planet pairs with every present angle.
    from kerykeion.chart_data_factory import _ANGLE_FIELDS, _CLASSICAL_PLANET_FIELDS

    present_planets = [f for f in _CLASSICAL_PLANET_FIELDS if getattr(john_lennon, f, None) is not None]
    present_angles = [f for f in _ANGLE_FIELDS if getattr(john_lennon, f, None) is not None]
    assert len(wide) == len(present_planets) * len(present_angles)


def test_analysis_honours_active_points(john_lennon):
    """A chart restricted to Sun+Moon must not report an excluded planet in
    its angularity or stellium analysis (the serialized active_points and the
    analysis must agree)."""
    restricted = ChartDataFactory.create_natal_chart_data(
        john_lennon, active_points=["Sun", "Moon"]
    )
    for entry in restricted.angularities:
        assert entry.point in ("Sun", "Moon")
    for stellium in restricted.stelliums:
        assert all(point in ("Sun", "Moon") for point in stellium.points)
    # Two points can never form a 3-planet stellium.
    assert restricted.stelliums == []


def test_stelliums_threshold(john_lennon):
    stelliums = _compute_stelliums(john_lennon)
    for stellium in stelliums:
        assert len(stellium.points) >= STELLIUM_MIN_POINTS
        assert 1 <= stellium.house <= 12


def test_chart_data_carries_the_analysis(john_lennon):
    chart_data = ChartDataFactory.create_natal_chart_data(john_lennon)
    # The factory applies the subject's own active_points as the filter.
    own = set(str(p) for p in john_lennon.active_points)
    assert chart_data.angularities == _compute_angularities(john_lennon, active_points=own)
    assert chart_data.stelliums == _compute_stelliums(john_lennon, active_points=own)


def test_synastry_enrichments_honour_the_common_set(john_lennon):
    """A synastry with a Sun-only partner serializes the COMMON active_points
    (the intersection); the per-subject analyses must not surface planets
    that contract excludes — active_points=['Sun'] with a Venus/Mars
    stellium in the payload would be internally inconsistent."""
    sun_only = john_lennon.model_copy(update={"active_points": ["Sun"]})
    data = ChartDataFactory.create_chart_data("Synastry", john_lennon, sun_only)
    allowed = set(str(p) for p in data.active_points)
    for entry in data.first_subject_angularities + data.second_subject_angularities:
        assert entry.point in allowed
    assert data.first_subject_stelliums == []
    assert data.second_subject_stelliums == []


def test_transit_first_subject_analysis_keeps_the_natal_set(john_lennon):
    """Transit-like charts mirror the distribution convention instead: the
    NATAL analysis is not truncated by the moving chart's tracking set."""
    moving = john_lennon.model_copy(update={"active_points": ["Sun"]})
    data = ChartDataFactory.create_chart_data("Transit", john_lennon, moving)
    natal_own = set(str(p) for p in john_lennon.active_points)
    assert data.first_subject_angularities == _compute_angularities(
        john_lennon, active_points=natal_own
    )
    assert data.first_subject_stelliums == _compute_stelliums(
        john_lennon, active_points=natal_own
    )


def test_non_terrestrial_perspective_yields_no_analysis():
    """A Heliocentric (or barycentric/planetocentric) chart measures planet
    longitudes from a non-Earth origin while ASC/MC stay terrestrial horizon
    longitudes: the comparison would emit plausible but false analyses, so
    it must stay silent even with an unbounded orb."""
    from types import SimpleNamespace

    helio = SimpleNamespace(
        perspective_type="Heliocentric",
        sun=SimpleNamespace(name="Sun", abs_pos=100.0, house="First_House"),
        mercury=SimpleNamespace(name="Mercury", abs_pos=101.0, house="First_House"),
        venus=SimpleNamespace(name="Venus", abs_pos=102.0, house="First_House"),
        ascendant=SimpleNamespace(name="Ascendant", abs_pos=100.0),
    )
    assert _compute_angularities(helio, orb=180.0) == []
    assert _compute_stelliums(helio) == []
    # The terrestrial perspectives keep the analysis (Lennon is Apparent
    # Geocentric and does produce angularities — see the tests above).
    for perspective in ("Apparent Geocentric", "True Geocentric", "Topocentric"):
        terrestrial = SimpleNamespace(**{**helio.__dict__, "perspective_type": perspective})
        assert _compute_angularities(terrestrial, orb=180.0) != []


# ---------------------------------------------------------------------------
# Progressed points (sign_changed)
# ---------------------------------------------------------------------------

def test_progressed_points_sign_changed(john_lennon):
    result = SecondaryProgressionFactory.compute_full(
        john_lennon, target_iso_utc_datetime="2024-06-15T00:00:00Z", compute_aspects=False
    )
    assert result.progressed_points, "expected a natal-vs-progressed comparison per point"
    by_name = {entry.name: entry for entry in result.progressed_points}
    # The progressed Moon moves ~13°/day-year: over 83 years it has certainly
    # left its natal sign at least once; more robustly, each entry's flag must
    # simply agree with its own sign pair.
    for entry in result.progressed_points:
        assert entry.sign_changed == (entry.natal_sign != entry.progressed_sign)
    assert "Sun" in by_name and "Moon" in by_name
    # 83 progressed years move the Sun ~83° — it cannot still be in Libra.
    assert by_name["Sun"].sign_changed is True
