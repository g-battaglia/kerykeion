# -*- coding: utf-8 -*-
"""Tests for the Lunation Finder Factory."""

from datetime import datetime

from kerykeion.lunations import LunationFinderFactory
from kerykeion.utilities import datetime_to_julian


class TestLunationsRange:
    """Find lunations across a calendar year."""

    def test_year_count(self):
        res = LunationFinderFactory.from_iso_range("2026-01-01", "2026-12-31")
        # A calendar year holds ~49-50 lunations (12-13 of each phase).
        assert 48 <= len(res.lunations) <= 51

    def test_phase_distribution(self):
        res = LunationFinderFactory.from_iso_range("2026-01-01", "2026-12-31")
        counts: dict = {}
        for lun in res.lunations:
            counts[lun.phase] = counts.get(lun.phase, 0) + 1
        for phase in ("new", "first_quarter", "full", "last_quarter"):
            assert 11 <= counts.get(phase, 0) <= 14

    def test_chronological_no_duplicates(self):
        res = LunationFinderFactory.from_iso_range("2026-01-01", "2026-12-31")
        jds = [lun.julian_day for lun in res.lunations]
        assert jds == sorted(jds)
        # Consecutive lunations are ~7.4 days apart; never closer than 2 days.
        for earlier, later in zip(jds, jds[1:]):
            assert (later - earlier) > 2.0

    def test_phase_filter(self):
        res = LunationFinderFactory.from_iso_range(
            "2026-01-01", "2026-12-31", phases=["new"]
        )
        assert res.lunations
        assert all(lun.phase == "new" for lun in res.lunations)
        assert 11 <= len(res.lunations) <= 13


class TestLunationGeometry:
    """Sun/Moon geometry at each phase."""

    def test_new_moon_conjunction(self):
        res = LunationFinderFactory.from_iso_range(
            "2026-01-01", "2026-03-31", phases=["new"]
        )
        lun = res.lunations[0]
        sep = abs(lun.sun.abs_pos - lun.moon.abs_pos) % 360.0
        sep = min(sep, 360.0 - sep)
        assert sep < 0.5

    def test_full_moon_opposition(self):
        res = LunationFinderFactory.from_iso_range(
            "2026-01-01", "2026-03-31", phases=["full"]
        )
        lun = res.lunations[0]
        sep = abs(lun.sun.abs_pos - lun.moon.abs_pos) % 360.0
        sep = min(sep, 360.0 - sep)
        assert abs(sep - 180.0) < 0.5

    def test_known_new_moon_aug_2026_in_leo(self):
        """The New Moon of 12 Aug 2026 (the total solar eclipse) is ~20 deg Leo."""
        res = LunationFinderFactory.from_iso_range(
            "2026-08-01", "2026-08-31", phases=["new"]
        )
        assert len(res.lunations) == 1
        lun = res.lunations[0]
        assert lun.iso_utc.startswith("2026-08-12")
        assert lun.sun.sign == "Leo"
        assert 19.0 <= lun.sun.position <= 21.0


class TestLunationApi:
    """Factory entry points and edge cases."""

    def test_iso_utc_format(self):
        res = LunationFinderFactory.from_iso_range("2026-01-01", "2026-02-01")
        for lun in res.lunations:
            assert "T" in lun.iso_utc and lun.iso_utc.endswith("Z")

    def test_empty_range(self):
        res = LunationFinderFactory.from_iso_range("2026-01-01", "2026-01-01")
        assert res.lunations == []

    def test_from_julian_day(self):
        start = datetime_to_julian(datetime(2026, 1, 1))
        end = datetime_to_julian(datetime(2026, 4, 1))
        res = LunationFinderFactory.from_julian_day(start, end)
        assert res.lunations
        assert res.start_jd == start
        assert res.end_jd == end
