# -*- coding: utf-8 -*-
"""Tests for RetrogradeStationFactory.retrograde_periods_*: retrograde spans clipped to a range."""

from datetime import datetime

import pytest

from kerykeion.retrograde_stations import RetrogradeStationFactory
from kerykeion.utilities import datetime_to_julian

ONE_SECOND = 1.0 / 86400.0


class TestMarch2025:
    """Venus is already retrograde on 5 March 2025; Mercury turns on the 15th; both run past the 31st."""

    def test_venus_open_at_the_start_and_mercury_from_its_station(self):
        res = RetrogradeStationFactory.retrograde_periods_from_iso_range("2025-03-05", "2025-03-31")
        by_planet = {p.planet: p for p in res.periods}
        assert set(by_planet) == {"Venus", "Mercury"}, [p.planet for p in res.periods]
        venus, mercury = by_planet["Venus"], by_planet["Mercury"]
        assert venus.start_clipped and venus.end_clipped
        assert venus.start_jd == res.start_jd and venus.end_jd == res.end_jd
        assert not mercury.start_clipped and mercury.end_clipped
        assert mercury.start.startswith("2025-03-15")
        assert mercury.end_jd == res.end_jd

    def test_span_starts_are_the_retrograde_stations(self):
        periods = RetrogradeStationFactory.retrograde_periods_from_iso_range("2025-01-01", "2025-12-31").periods
        stations = RetrogradeStationFactory.from_iso_range("2025-01-01", "2025-12-31").stations
        # The period scan starts one second before the range (edge rule), so
        # its brackets differ from the station scan's and the bisected instants
        # agree to well under a second — never compare the floats for equality.
        sr = [(s.planet, s.julian_day) for s in stations if s.station_type == "SR"]
        sd = [(s.planet, s.julian_day) for s in stations if s.station_type == "SD"]

        def near(planet: str, jd: float, pool: list) -> bool:
            return any(p == planet and abs(j - jd) <= ONE_SECOND for p, j in pool)

        for p in periods:
            if not p.start_clipped:
                assert near(p.planet, p.start_jd, sr), (p.planet, p.start)
            if not p.end_clipped:
                assert near(p.planet, p.end_jd, sd), (p.planet, p.end)
            assert p.start_jd < p.end_jd

    def test_spans_never_overlap_per_planet(self):
        periods = RetrogradeStationFactory.retrograde_periods_from_iso_range("2024-01-01", "2025-12-31").periods
        for planet in {p.planet for p in periods}:
            spans = sorted((p for p in periods if p.planet == planet), key=lambda p: p.start_jd)
            for a, b in zip(spans, spans[1:]):
                assert a.end_jd <= b.start_jd


class TestEdges:
    def test_a_quiet_month_for_a_direct_planet_yields_nothing(self):
        # Mars is direct throughout April 2025 (its retrograde ended 24 Feb 2025).
        res = RetrogradeStationFactory.retrograde_periods_from_iso_range("2025-04-01", "2025-04-30", ["Mars"])
        assert res.periods == []

    def test_a_station_on_the_range_start_opens_the_span_unclipped(self):
        stations = RetrogradeStationFactory.from_iso_range("2025-03-01", "2025-03-31", ["Mercury"]).stations
        sr = next(s for s in stations if s.station_type == "SR")
        res = RetrogradeStationFactory.retrograde_periods_from_julian_day(sr.julian_day, sr.julian_day + 20, ["Mercury"])
        assert len(res.periods) == 1
        period = res.periods[0]
        assert abs(period.start_jd - sr.julian_day) <= ONE_SECOND
        assert not period.start_clipped
        assert period.end_clipped

    def test_chiron_is_opt_in_and_luminaries_stay_rejected(self):
        res = RetrogradeStationFactory.retrograde_periods_from_iso_range("2025-01-01", "2025-12-31", ["Chiron"])
        assert res.periods and all(p.planet == "Chiron" for p in res.periods)
        default = RetrogradeStationFactory.retrograde_periods_from_iso_range("2025-01-01", "2025-12-31")
        assert "Chiron" not in {p.planet for p in default.periods}
        with pytest.raises(ValueError):
            RetrogradeStationFactory.retrograde_periods_from_iso_range("2025-01-01", "2025-12-31", ["Sun"])

    def test_times_are_identical_under_a_sidereal_zodiac(self):
        tropical = RetrogradeStationFactory.retrograde_periods_from_iso_range("2025-03-05", "2025-03-31")
        sidereal = RetrogradeStationFactory.retrograde_periods_from_iso_range(
            "2025-03-05", "2025-03-31", zodiac_type="Sidereal", sidereal_mode="LAHIRI"
        )
        assert [(p.planet, p.start_jd, p.end_jd) for p in tropical.periods] == [
            (p.planet, p.start_jd, p.end_jd) for p in sidereal.periods
        ]

    def test_empty_range_yields_nothing(self):
        jd = datetime_to_julian(datetime(2025, 3, 10))
        assert RetrogradeStationFactory.retrograde_periods_from_julian_day(jd, jd).periods == []
