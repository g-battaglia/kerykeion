# -*- coding: utf-8 -*-
"""Tests for the Sign Ingress Factory."""

import pytest

from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.sign_ingresses import SignIngressFactory
from kerykeion.utilities import datetime_to_julian
from datetime import datetime


class TestSunIngresses2026:
    """The Sun's ingresses are the equinoxes/solstices — exact known anchors."""

    def test_twelve_ingresses_never_retrograde(self):
        res = SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31", ["Sun"])
        assert len(res.ingresses) == 12
        assert all(not x.retrograde for x in res.ingresses)
        # Each ingress lands on a 30° boundary.
        assert all(x.ecliptic_longitude % 30 == 0 for x in res.ingresses)

    def test_spring_equinox_into_aries(self):
        res = SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31", ["Sun"])
        aries = [x for x in res.ingresses if x.sign == "Ari"][0]
        assert aries.iso_utc.startswith("2026-03-20")
        assert aries.from_sign == "Pis"
        assert aries.ecliptic_longitude == 0.0

    def test_summer_solstice_into_cancer(self):
        res = SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31", ["Sun"])
        cancer = [x for x in res.ingresses if x.sign == "Can"][0]
        assert cancer.iso_utc.startswith("2026-06-21")
        assert cancer.ecliptic_longitude == 90.0

    def test_chronological_and_adjacent_signs(self):
        res = SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31", ["Sun"])
        jds = [x.julian_day for x in res.ingresses]
        assert jds == sorted(jds)
        # Forward motion: each entered sign is the one after the sign left.
        for x in res.ingresses:
            assert x.sign_num == (x.from_sign_num + 1) % 12


class TestRetrogradeIngresses:
    """Pluto's 2023-2024 Capricorn<->Aquarius dance is a documented anchor."""

    def test_pluto_retrograde_reentry_into_capricorn(self):
        res = SignIngressFactory.from_iso_range("2023-01-01", "2024-12-31", ["Pluto"])
        # The retrograde step back into Capricorn on 11 Jun 2023.
        retro = [x for x in res.ingresses if x.retrograde]
        assert retro, "expected at least one retrograde ingress"
        first_retro = retro[0]
        assert first_retro.iso_utc.startswith("2023-06-11")
        assert first_retro.from_sign == "Aqu" and first_retro.sign == "Cap"
        assert first_retro.ecliptic_longitude == 300.0

    def test_pluto_final_ingress_into_aquarius_nov_2024(self):
        res = SignIngressFactory.from_iso_range("2023-01-01", "2024-12-31", ["Pluto"])
        last = res.ingresses[-1]
        assert last.iso_utc.startswith("2024-11-19")
        assert last.sign == "Aqu" and not last.retrograde

    def test_double_crossing_within_one_interval(self):
        # Mercury crossed into Aquarius ~04:20 UTC and retrograded back into
        # Capricorn ~11:59 UTC on 1970-01-04 — both inside a single sampling
        # interval. Endpoint-only detection misses both; the midpoint probe
        # recovers them.
        res = SignIngressFactory.from_iso_range("1970-01-03", "1970-01-06", ["Mercury"])
        assert len(res.ingresses) == 2
        first, second = res.ingresses
        assert first.from_sign == "Cap" and first.sign == "Aqu" and not first.retrograde
        assert second.from_sign == "Aqu" and second.sign == "Cap" and second.retrograde
        assert first.iso_utc.startswith("1970-01-04")
        assert second.iso_utc.startswith("1970-01-04")


class TestIngressApi:
    """Factory entry points, defaults, and validation."""

    def test_default_excludes_moon(self):
        res = SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31")
        assert all(x.planet != "Moon" for x in res.ingresses)

    def test_moon_is_opt_in_and_frequent(self):
        res = SignIngressFactory.from_iso_range(
            "2026-01-01", "2026-12-31", ["Moon"]
        )
        # The Moon changes sign every ~2.3 days => ~150+ ingresses a year.
        assert len(res.ingresses) > 140
        assert all(x.planet == "Moon" for x in res.ingresses)

    def test_unknown_planet_raises(self):
        with pytest.raises(ValueError):
            SignIngressFactory.from_iso_range(
                "2026-01-01", "2026-12-31", ["Sun", "Nibiru"]
            )

    def test_empty_range(self):
        start = datetime_to_julian(datetime(2026, 1, 1))
        res = SignIngressFactory.from_julian_day(start, start)
        assert res.ingresses == []

    def test_empty_planet_list_returns_nothing(self):
        # An explicit empty list means "scan nothing", not "scan the defaults".
        res = SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31", [])
        assert res.ingresses == []

    def test_oversized_range_raises(self):
        # A range too long to scan is rejected, never silently truncated.
        with pytest.raises(ValueError):
            SignIngressFactory.from_iso_range("0001-01-01", "3000-01-01")

    @pytest.mark.extended
    def test_bce_range_via_julian_day(self):
        # The BCE range Kerykeion supports must not crash on JD->ISO conversion
        # (Python datetime caps at year 1). Year -100 has 12 solar ingresses.
        from kerykeion.ephemeris_backend import ephe

        jd0 = ephe.julday(-100, 1, 1, 0.0)
        jd1 = ephe.julday(-100, 12, 31, 23.9)
        res = SignIngressFactory.from_julian_day(jd0, jd1, ["Sun"])
        assert len(res.ingresses) == 12
        assert res.ingresses[0].iso_utc.startswith("-0100-")

    def test_lowercase_t_end_not_extended(self):
        # fromisoformat accepts a lowercase 't'; it must be read as a datetime,
        # not widened to end-of-day. The Sun enters Aries 2026-03-20T14:45Z, so a
        # 't00:00:00' end on that day must exclude it.
        res = SignIngressFactory.from_iso_range("2026-03-19", "2026-03-20t00:00:00", ["Sun"])
        assert all(x.sign != "Ari" for x in res.ingresses)

    def test_duplicate_planets_deduplicated(self):
        once = SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31", ["Sun"]).ingresses
        twice = SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31", ["Sun", "Sun"]).ingresses
        assert len(once) == len(twice)

    def test_from_julian_day(self):
        start = datetime_to_julian(datetime(2026, 1, 1))
        end = datetime_to_julian(datetime(2026, 12, 31))
        res = SignIngressFactory.from_julian_day(start, end, ["Sun"])
        assert len(res.ingresses) == 12
        assert res.start_jd == start and res.end_jd == end


class TestIngressErrorContract:
    """Backend failures mid-scan must surface as KerykeionException, matching
    the lunation factory's contract — never propagate raw backend errors and
    never return silently truncated results."""

    def test_malformed_iso_raises_kerykeion_exception(self):
        # A malformed ISO date must surface as KerykeionException (same wrap
        # as LunationFinderFactory.from_iso_range), never as a raw ValueError
        # leaking from datetime.fromisoformat.
        with pytest.raises(KerykeionException, match="Invalid ISO"):
            SignIngressFactory.from_iso_range("not-a-date", "2026-12-31", ["Sun"])
        with pytest.raises(KerykeionException, match="Invalid ISO"):
            SignIngressFactory.from_iso_range("2026-01-01", "2026-13-45", ["Sun"])

    def test_backend_failure_raises_kerykeion_exception(self, monkeypatch):
        # Simulate the backend rejecting a date (as a raw libephemeris
        # EphemerisRangeError / swisseph.Error would) instead of using extreme
        # years: the local dev kernel range differs from production DE441.
        import kerykeion.sign_ingresses.sign_ingress_factory as sif

        def failing_calc_ut(jd, body, flags):
            raise RuntimeError(f"jd {jd} outside ephemeris range")

        monkeypatch.setattr(sif.ephe, "calc_ut", failing_calc_ut)
        with pytest.raises(KerykeionException, match="narrow the date range"):
            SignIngressFactory.from_iso_range("2026-01-01", "2026-01-10", ["Sun"])

    def test_mid_scan_failure_raises_not_truncates(self, monkeypatch):
        # First samples succeed, then the scan walks past the range edge: the
        # whole search must raise rather than return partial ingresses claiming
        # full coverage.
        import kerykeion.sign_ingresses.sign_ingress_factory as sif

        calls = {"n": 0}

        def flaky_calc_ut(jd, body, flags):
            calls["n"] += 1
            if calls["n"] > 3:
                raise RuntimeError(f"jd {jd} outside ephemeris range")
            return ((15.0, 0.0, 1.0, 1.0, 0.0, 0.0), 0)

        monkeypatch.setattr(sif.ephe, "calc_ut", flaky_calc_ut)
        with pytest.raises(KerykeionException, match=r"failed at JD "):
            SignIngressFactory.from_iso_range("2026-01-01", "2026-01-10", ["Sun"])
