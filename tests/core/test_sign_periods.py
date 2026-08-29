# -*- coding: utf-8 -*-
"""Tests for SignIngressFactory.sign_periods_*: contiguous sign stays clipped to a range."""

from datetime import datetime, timezone

import pytest

from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.sign_ingresses import SignIngressFactory
from kerykeion.void_of_course_moon import VoidOfCourseMoonFactory
from kerykeion.utilities import datetime_to_julian

ONE_SECOND = 1.0 / 86400.0


def _jd(iso: str) -> float:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return datetime_to_julian(dt)


class TestSunMarch2026:
    """The Sun's March equinox is an exact anchor: Pisces until 2026-03-20, then Aries."""

    def test_two_contiguous_stays_around_the_equinox(self):
        res = SignIngressFactory.sign_periods_from_iso_range("2026-03-01", "2026-03-31", ["Sun"])
        assert [p.sign for p in res.periods] == ["Pis", "Ari"]
        pisces, aries = res.periods
        assert pisces.start_jd == res.start_jd and pisces.start_clipped
        assert aries.end_jd == res.end_jd and aries.end_clipped
        assert not pisces.end_clipped and not aries.start_clipped
        assert pisces.end_jd == aries.start_jd
        assert aries.start.startswith("2026-03-20")
        assert pisces.start == "2026-03-01T00:00:00Z"

    def test_boundaries_are_the_ingress_instants(self):
        periods = SignIngressFactory.sign_periods_from_iso_range("2026-01-01", "2026-12-31", ["Sun"]).periods
        ingresses = SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31", ["Sun"]).ingresses
        assert len(periods) == len(ingresses) + 1
        for period, ingress in zip(periods[1:], ingresses):
            assert period.start_jd == ingress.julian_day
            assert period.sign == ingress.sign
            assert period.sign_num == ingress.sign_num
        for a, b in zip(periods, periods[1:]):
            assert a.end_jd == b.start_jd
            assert a.sign != b.sign


class TestMoon:
    def test_a_month_holds_thirteen_or_fourteen_stays(self):
        res = SignIngressFactory.sign_periods_from_iso_range("2026-09-01", "2026-09-30", ["Moon"])
        assert 13 <= len(res.periods) <= 15
        for a, b in zip(res.periods, res.periods[1:]):
            assert a.end_jd == b.start_jd
            assert b.sign_num == (a.sign_num + 1) % 12

    def test_boundaries_agree_with_the_void_of_course_ends_within_a_second(self):
        periods = SignIngressFactory.sign_periods_from_iso_range("2026-09-01", "2026-09-30", ["Moon"]).periods
        windows = VoidOfCourseMoonFactory.from_iso_range("2026-09-01", "2026-09-30").windows
        void_ends = [_jd(w.void_end if isinstance(w.void_end, str) else w.void_end.isoformat()) for w in windows]
        starts = [p.start_jd for p in periods[1:]]
        assert starts, "expected in-range Moon ingresses"
        for start in starts:
            assert min(abs(start - v) for v in void_ends) <= ONE_SECOND


class TestFrameAndEdges:
    def test_sidereal_lahiri_shifts_the_stays_by_one_sign(self):
        res = SignIngressFactory.sign_periods_from_iso_range(
            "2026-03-01", "2026-03-31", ["Sun"], zodiac_type="Sidereal", sidereal_mode="LAHIRI"
        )
        assert [p.sign for p in res.periods] == ["Aqu", "Pis"]
        assert res.periods[1].start.startswith("2026-03-14")

    def test_sidereal_requires_a_mode(self):
        with pytest.raises(KerykeionException):
            SignIngressFactory.sign_periods_from_iso_range("2026-03-01", "2026-03-31", ["Sun"], zodiac_type="Sidereal")

    def test_empty_and_inverted_ranges_yield_nothing(self):
        jd = datetime_to_julian(datetime(2026, 3, 10))
        assert SignIngressFactory.sign_periods_from_julian_day(jd, jd, ["Sun"]).periods == []
        assert SignIngressFactory.sign_periods_from_julian_day(jd, jd - 5, ["Sun"]).periods == []

    def test_unknown_planet_is_rejected(self):
        with pytest.raises(ValueError):
            SignIngressFactory.sign_periods_from_iso_range("2026-03-01", "2026-03-31", ["Ceres"])

    def test_default_set_excludes_the_moon(self):
        res = SignIngressFactory.sign_periods_from_iso_range("2026-03-01", "2026-03-05")
        planets = {p.planet for p in res.periods}
        assert "Moon" not in planets and "Sun" in planets and "Pluto" in planets
        # Every planet: first stay clipped at the start, last at the end, contiguous between.
        for planet in planets:
            stays = [p for p in res.periods if p.planet == planet]
            assert stays[0].start_clipped and stays[-1].end_clipped
            assert all(a.end_jd == b.start_jd for a, b in zip(stays, stays[1:]))


class TestRangeStartingOnAnIngress:
    """A range that begins on the ingress instant opens the entered sign unclipped."""

    def test_first_stay_is_not_clipped_when_the_range_starts_on_the_ingress(self):
        aries = next(
            x for x in SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31", ["Sun"]).ingresses if x.sign == "Ari"
        )
        res = SignIngressFactory.sign_periods_from_julian_day(aries.julian_day, aries.julian_day + 10, ["Sun"])
        assert [p.sign for p in res.periods] == ["Ari"]
        first = res.periods[0]
        assert first.start_jd == aries.julian_day
        assert not first.start_clipped
        assert first.end_clipped

    def test_first_stay_is_clipped_when_the_range_starts_mid_sign(self):
        res = SignIngressFactory.sign_periods_from_iso_range("2026-03-01", "2026-03-10", ["Sun"])
        assert res.periods[0].start_clipped
