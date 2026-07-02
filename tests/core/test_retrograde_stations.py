# -*- coding: utf-8 -*-
"""Tests for the Retrograde Station Factory."""

import pytest

from kerykeion.retrograde_stations import RetrogradeStationFactory
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.utilities import datetime_to_julian
from datetime import datetime


class TestMercuryStations2026:
    """Mercury's three 2026 retrograde periods are well-documented anchors."""

    def test_six_stations_alternating(self):
        res = RetrogradeStationFactory.from_iso_range(
            "2026-01-01", "2026-12-31", ["Mercury"]
        )
        # Three retrograde periods => three SR + three SD, strictly alternating.
        assert len(res.stations) == 6
        types = [s.station_type for s in res.stations]
        assert types == ["SR", "SD", "SR", "SD", "SR", "SD"]

    def test_first_station_is_late_february_in_pisces(self):
        res = RetrogradeStationFactory.from_iso_range(
            "2026-01-01", "2026-12-31", ["Mercury"]
        )
        first = res.stations[0]
        assert first.station_type == "SR"
        assert first.iso_utc.startswith("2026-02-26")
        assert first.sign == "Pis"

    def test_chronological_and_within_sign_pairs(self):
        res = RetrogradeStationFactory.from_iso_range(
            "2026-01-01", "2026-12-31", ["Mercury"]
        )
        jds = [s.julian_day for s in res.stations]
        assert jds == sorted(jds)
        # Each SR/SD pair brackets one retrograde period (~3 weeks long).
        for sr, sd in zip(res.stations[0::2], res.stations[1::2]):
            assert sr.station_type == "SR" and sd.station_type == "SD"
            assert 15.0 < (sd.julian_day - sr.julian_day) < 30.0


class TestStationApi:
    """Factory entry points, defaults, and validation."""

    def test_default_planet_set_excludes_luminaries(self):
        res = RetrogradeStationFactory.from_iso_range("2026-01-01", "2026-12-31")
        planets = {s.planet for s in res.stations}
        assert "Sun" not in planets and "Moon" not in planets
        # Every station is a real motion reversal of a non-luminary planet.
        assert all(s.station_type in ("SR", "SD") for s in res.stations)
        assert res.stations == sorted(res.stations, key=lambda s: s.julian_day)

    def test_luminaries_rejected(self):
        with pytest.raises(ValueError):
            RetrogradeStationFactory.from_iso_range("2026-01-01", "2026-12-31", ["Sun"])
        with pytest.raises(ValueError):
            RetrogradeStationFactory.from_iso_range("2026-01-01", "2026-12-31", ["Moon"])

    def test_zodiac_fields_consistent(self):
        res = RetrogradeStationFactory.from_iso_range(
            "2026-01-01", "2026-12-31", ["Mercury"]
        )
        for s in res.stations:
            assert 0 <= s.sign_num <= 11
            assert 0.0 <= s.degree < 30.0
            assert 0.0 <= s.ecliptic_longitude < 360.0
            assert "T" in s.iso_utc and s.iso_utc.endswith("Z")

    def test_empty_range(self):
        start = datetime_to_julian(datetime(2026, 1, 1))
        res = RetrogradeStationFactory.from_julian_day(start, start)
        assert res.stations == []

    def test_empty_planet_list_returns_nothing(self):
        # An explicit empty list means "scan nothing", not "scan the defaults".
        res = RetrogradeStationFactory.from_iso_range("2026-01-01", "2026-12-31", [])
        assert res.stations == []

    def test_oversized_range_raises(self):
        # A range too long to scan (> _MAX_SAMPLES at the current step) is
        # rejected up front, never silently truncated.
        with pytest.raises(ValueError):
            RetrogradeStationFactory.from_julian_day(0.0, 20_000_000.0)

    def test_bce_range_via_julian_day(self):
        # The BCE range must not crash on JD->ISO conversion (datetime caps at
        # year 1). Mercury stations in 100 BCE; just assert it runs and formats.
        from kerykeion.ephemeris_backend import ephe

        jd0 = ephe.julday(-100, 1, 1, 0.0)
        jd1 = ephe.julday(-100, 12, 31, 23.9)
        res = RetrogradeStationFactory.from_julian_day(jd0, jd1, ["Mercury"])
        assert all(s.iso_utc.startswith("-0100-") for s in res.stations)

    def test_duplicate_planets_deduplicated(self):
        once = RetrogradeStationFactory.from_iso_range("2026-01-01", "2026-12-31", ["Mercury"]).stations
        twice = RetrogradeStationFactory.from_iso_range("2026-01-01", "2026-12-31", ["Mercury", "Mercury"]).stations
        assert len(once) == len(twice)

    def test_from_julian_day(self):
        start = datetime_to_julian(datetime(2026, 1, 1))
        end = datetime_to_julian(datetime(2026, 12, 31))
        res = RetrogradeStationFactory.from_julian_day(start, end, ["Mercury"])
        assert len(res.stations) == 6
        assert res.start_jd == start and res.end_jd == end


class TestStationErrorContract:
    """Backend failures mid-scan must surface as KerykeionException, matching
    the lunation factory's contract — never propagate raw backend errors and
    never return silently truncated results."""

    def test_backend_failure_raises_kerykeion_exception(self, monkeypatch):
        # Simulate the backend rejecting a date (as a raw libephemeris
        # EphemerisRangeError / swisseph.Error would) instead of using extreme
        # years: the local dev kernel range differs from production DE441.
        import kerykeion.retrograde_stations.retrograde_station_factory as rsf

        def failing_calc_ut(jd, body, flags):
            raise RuntimeError(f"jd {jd} outside ephemeris range")

        monkeypatch.setattr(rsf.ephe, "calc_ut", failing_calc_ut)
        with pytest.raises(KerykeionException, match="narrow the date range"):
            RetrogradeStationFactory.from_iso_range(
                "2026-01-01", "2026-01-10", ["Mercury"]
            )

    def test_mid_scan_failure_raises_not_truncates(self, monkeypatch):
        # First samples succeed, then the scan walks past the range edge: the
        # whole search must raise rather than return partial stations claiming
        # full coverage.
        import kerykeion.retrograde_stations.retrograde_station_factory as rsf

        calls = {"n": 0}

        def flaky_calc_ut(jd, body, flags):
            calls["n"] += 1
            if calls["n"] > 1:
                raise RuntimeError(f"jd {jd} outside ephemeris range")
            return ((10.0, 0.0, 1.0, 1.0, 0.0, 0.0), 0)

        monkeypatch.setattr(rsf.ephe, "calc_ut", flaky_calc_ut)
        with pytest.raises(KerykeionException, match=r"failed at JD "):
            RetrogradeStationFactory.from_iso_range(
                "2026-01-01", "2026-01-10", ["Mercury"]
            )
