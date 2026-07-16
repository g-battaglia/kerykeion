# -*- coding: utf-8 -*-
"""Tests for the Mundane Aspect Factory (transiting-to-transiting aspectarian)."""

import pytest

from kerykeion.aspects.aspects_utils import difdeg2n
from kerykeion.ephemeris_backend import ephe, ephemeris_session
from kerykeion.mundane_aspects import MundaneAspectFactory
from kerykeion.schemas.kerykeion_exception import KerykeionException


class TestGreatConjunction2020:
    """The Jupiter-Saturn Great Conjunction is a documented anchor: 2020-12-21 ~18:20 UTC."""

    def test_found_once_at_the_published_instant(self):
        res = MundaneAspectFactory.from_iso_range("2020-12-01", "2020-12-31")
        jupsat = [
            a for a in res.aspects
            if {a.point_a, a.point_b} == {"Jupiter", "Saturn"} and a.aspect == "conjunction"
        ]
        assert len(jupsat) == 1
        event = jupsat[0]
        assert event.iso_utc.startswith("2020-12-21T18:2")
        # Canonical fast-to-slow ordering: Jupiter before Saturn.
        assert (event.point_a, event.point_b) == ("Jupiter", "Saturn")
        # Both direct, both at 0° Aquarius (tropical).
        assert not event.point_a_retrograde and not event.point_b_retrograde
        assert event.point_a_sign == "Aqu" and event.point_b_sign == "Aqu"
        assert event.aspect_degrees == 0.0


class TestRetrogradeTriplePerfection:
    """Jupiter square Neptune perfected exactly three times in 2019 — the
    retrograde re-crossing path (Jan 13, Jun 16, Sep 21)."""

    def test_three_events_with_correct_retrograde_flags(self):
        res = MundaneAspectFactory.from_iso_range(
            "2019-01-01", "2019-12-31", points=["Jupiter", "Neptune"], aspects=["square"]
        )
        assert len(res.aspects) == 3
        dates = [a.iso_utc[:10] for a in res.aspects]
        assert dates == ["2019-01-13", "2019-06-16", "2019-09-21"]
        # June: Jupiter retrograde; September: Neptune retrograde.
        assert res.aspects[1].point_a_retrograde and not res.aspects[1].point_b_retrograde
        assert not res.aspects[2].point_a_retrograde and res.aspects[2].point_b_retrograde


class TestSelfConsistency:
    """The strongest property: recomputing both longitudes at every reported
    instant must reproduce the aspect angle to sub-arcsecond accuracy."""

    def test_reported_instants_are_exact(self):
        res = MundaneAspectFactory.from_iso_range("2025-03-01", "2025-03-31")
        assert res.aspects, "expected events in March 2025"
        from kerykeion.settings.config_constants import POINT_NUMBER_MAP

        with ephemeris_session() as iflag:
            for event in res.aspects:
                lon_a = ephe.calc_ut(event.julian_day, POINT_NUMBER_MAP[event.point_a], iflag)[0][0]
                lon_b = ephe.calc_ut(event.julian_day, POINT_NUMBER_MAP[event.point_b], iflag)[0][0]
                separation = difdeg2n(lon_a, lon_b)
                # |separation| equals the aspect angle regardless of which side
                # of the target the signed separation sits on.
                assert abs(abs(separation) - event.aspect_degrees) < 5e-4, (
                    f"{event.point_a} {event.aspect} {event.point_b} at {event.iso_utc}: "
                    f"separation {separation}"
                )

    def test_reported_longitudes_match_the_event(self):
        res = MundaneAspectFactory.from_iso_range("2025-03-01", "2025-03-07")
        for event in res.aspects:
            assert abs(difdeg2n(event.point_a_longitude, event.point_b_longitude)) == pytest.approx(
                event.aspect_degrees, abs=5e-4
            )


class TestMoonOptIn:
    """The Moon is excluded by default and opt-in by listing it in points."""

    def test_default_excludes_moon(self):
        res = MundaneAspectFactory.from_iso_range("2025-01-01", "2025-01-31")
        assert all("Moon" not in (a.point_a, a.point_b) for a in res.aspects)

    def test_moon_events_appear_when_requested(self):
        res = MundaneAspectFactory.from_iso_range(
            "2025-01-01", "2025-01-31", points=["Moon", "Sun"]
        )
        # Moon-Sun perfects each of the 5 Ptolemaic families roughly once per
        # synodic month → 8±2 events expected in a 31-day window.
        assert 6 <= len(res.aspects) <= 10
        assert all({a.point_a, a.point_b} == {"Moon", "Sun"} for a in res.aspects)
        # Moon is the faster body: always point_a.
        assert all(a.point_a == "Moon" for a in res.aspects)


class TestSiderealInvariance:
    """Aspect instants are zodiac-independent; signs shift with the ayanamsha."""

    def test_identical_timestamps_shifted_signs(self):
        tropical = MundaneAspectFactory.from_iso_range("2020-12-01", "2020-12-31")
        sidereal = MundaneAspectFactory.from_iso_range(
            "2020-12-01", "2020-12-31", zodiac_type="Sidereal", sidereal_mode="LAHIRI"
        )
        tro = {(a.point_a, a.point_b, a.aspect): a for a in tropical.aspects}
        sid = {(a.point_a, a.point_b, a.aspect): a for a in sidereal.aspects}
        assert set(tro) == set(sid)
        for key, event in tro.items():
            assert abs(event.julian_day - sid[key].julian_day) * 86400.0 < 1.0
        # Lahiri ayanamsha (~24°) pushes the 0° Aquarius conjunction into Capricorn.
        jupsat = sid[("Jupiter", "Saturn", "conjunction")]
        assert jupsat.point_a_sign == "Cap"

    def test_sidereal_requires_mode(self):
        with pytest.raises(KerykeionException, match="sidereal_mode is required"):
            MundaneAspectFactory.from_iso_range("2025-01-01", "2025-01-31", zodiac_type="Sidereal")


class TestContract:
    """Input guards and output invariants."""

    def test_chronological_order(self):
        res = MundaneAspectFactory.from_iso_range("2025-01-01", "2025-03-31")
        jds = [a.julian_day for a in res.aspects]
        assert jds == sorted(jds)

    def test_date_only_end_includes_the_whole_day(self):
        # The Great Conjunction perfects at 18:20 UTC on the range's last day.
        res = MundaneAspectFactory.from_iso_range(
            "2020-12-15", "2020-12-21", points=["Jupiter", "Saturn"], aspects=["conjunction"]
        )
        assert len(res.aspects) == 1

    def test_nonstandard_datetime_separator_not_widened(self):
        from datetime import datetime

        from kerykeion.utilities import datetime_to_julian

        end = "2026-01-01_12:00:00"
        res = MundaneAspectFactory.from_iso_range(end, end, points=[])
        assert res.end_jd == datetime_to_julian(datetime.fromisoformat(end))

    def test_unknown_point_rejected(self):
        with pytest.raises(ValueError, match="Unknown points"):
            MundaneAspectFactory.from_iso_range("2025-01-01", "2025-01-31", points=["Vulcan"])

    def test_declination_aspects_rejected(self):
        with pytest.raises(ValueError, match="Unknown aspects"):
            MundaneAspectFactory.from_iso_range("2025-01-01", "2025-01-31", aspects=["parallel"])

    def test_malformed_iso_raises_kerykeion_exception(self):
        with pytest.raises(KerykeionException, match="Invalid ISO"):
            MundaneAspectFactory.from_iso_range("not-a-date", "2025-01-31")

    def test_range_too_large_rejected(self):
        with pytest.raises(ValueError, match="too large"):
            MundaneAspectFactory.from_julian_day(0.0, 600_000_000.0)

    @pytest.mark.parametrize("bad_jd", [float("nan"), float("inf"), float("-inf")])
    @pytest.mark.parametrize("bad_bound", ["start", "end"])
    def test_non_finite_julian_bounds_rejected(self, bad_jd, bad_bound):
        start, end = (bad_jd, 2451546.0) if bad_bound == "start" else (2451545.0, bad_jd)
        with pytest.raises(ValueError, match="finite"):
            MundaneAspectFactory.from_julian_day(start, end, points=[])

    def test_empty_points_yields_empty_result(self):
        res = MundaneAspectFactory.from_iso_range("2025-01-01", "2025-01-31", points=[])
        assert res.aspects == []

    def test_single_point_yields_empty_result(self):
        res = MundaneAspectFactory.from_iso_range("2025-01-01", "2025-01-31", points=["Sun"])
        assert res.aspects == []

    def test_minor_aspects_are_searchable(self):
        res = MundaneAspectFactory.from_iso_range(
            "2025-01-01", "2025-02-28", aspects=["quincunx", "semi-sextile"]
        )
        assert all(a.aspect in ("quincunx", "semi-sextile") for a in res.aspects)
        assert all(a.aspect_degrees in (150.0, 30.0) for a in res.aspects)

    def test_duplicate_inputs_do_not_duplicate_events(self):
        res = MundaneAspectFactory.from_iso_range(
            "2020-12-01", "2020-12-31",
            points=["Jupiter", "Saturn", "Jupiter"],
            aspects=["conjunction", "conjunction"],
        )
        assert len(res.aspects) == 1
