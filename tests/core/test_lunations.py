# -*- coding: utf-8 -*-
"""Tests for the Lunation Finder Factory."""

from datetime import datetime

import pytest

from kerykeion.lunations import LunationFinderFactory
from kerykeion.schemas.exceptions import KerykeionException
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

    def test_unknown_phase_raises(self):
        with pytest.raises(ValueError):
            LunationFinderFactory.from_iso_range(
                "2026-01-01", "2026-12-31", phases=["full", "waxing"]
            )

    def test_oversized_range_raises(self):
        # A range too long to scan is rejected upfront, never silently truncated.
        with pytest.raises(ValueError):
            LunationFinderFactory.from_julian_day(2451545.0, 2451545.0 + 3.1e6)

    @pytest.mark.parametrize("bad_jd", [float("nan"), float("inf"), float("-inf")])
    @pytest.mark.parametrize("bad_bound", ["start", "end"])
    def test_non_finite_julian_bounds_rejected(self, bad_jd, bad_bound):
        start, end = (bad_jd, 2451546.0) if bad_bound == "start" else (2451545.0, bad_jd)
        with pytest.raises(ValueError, match="finite"):
            LunationFinderFactory.from_julian_day(start, end, phases=[])

    def test_date_only_end_covers_full_day(self):
        # A date-only end_date must span through the end of that UTC day, not
        # stop at midnight (which would drop a lunation later on the last day).
        res = LunationFinderFactory.from_iso_range("2026-01-01", "2026-01-01")
        span = res.end_jd - res.start_jd
        # ~1 full day (end-of-day), not 0 as a bare midnight end_date would give.
        assert 0.99 < span <= 1.0

    def test_lowercase_t_end_datetime_not_widened(self):
        # Lowercase "t" is a valid ISO 8601 separator: an end_date carrying an
        # explicit time must be honored exactly, never widened to end-of-day.
        res = LunationFinderFactory.from_iso_range("2026-03-01", "2026-03-20t00:00:00")
        assert res.end_jd == datetime_to_julian(datetime(2026, 3, 20))
        upper = LunationFinderFactory.from_iso_range("2026-03-01", "2026-03-20T00:00:00")
        assert res.end_jd == upper.end_jd
        # And every reported lunation respects that exact boundary.
        assert all(lun.julian_day <= res.end_jd for lun in res.lunations)

    def test_nonstandard_datetime_separator_not_widened(self):
        end = "2026-03-20_12:00:00"
        res = LunationFinderFactory.from_iso_range("2026-03-20_12:00:00", end, phases=[])
        assert res.end_jd == datetime_to_julian(datetime.fromisoformat(end))

    def test_no_phantom_lunation_at_range_start(self):
        # A range beginning just after a new moon (12 Aug 2026) must not report a
        # phantom new moon echoed at the range start.
        res = LunationFinderFactory.from_iso_range(
            "2026-08-13", "2026-08-13", phases=["new"]
        )
        assert res.lunations == []

    def test_offset_aware_input_normalized_to_utc(self):
        from datetime import datetime
        from kerykeion.lunations.lunation_factory import _to_utc_naive

        # +02:00 wall-clock midnight is 22:00 UTC on the previous day.
        naive = _to_utc_naive(datetime.fromisoformat("2026-01-01T00:00:00+02:00"))
        assert naive.tzinfo is None
        assert (naive.year, naive.month, naive.day, naive.hour) == (2025, 12, 31, 22)


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


class TestSiderealLunations:
    """Phase instants are the Sun-Moon elongation (frame-independent), so the
    lunation TIMES are identical tropical vs sidereal; only the signs shift."""

    def test_phase_times_identical_signs_shift(self):
        trop = LunationFinderFactory.from_iso_range("2026-08-01", "2026-09-30")
        sid = LunationFinderFactory.from_iso_range(
            "2026-08-01", "2026-09-30", zodiac_type="Sidereal", sidereal_mode="LAHIRI"
        )
        # Same events in the same order (times are frame-independent).
        assert len(trop.lunations) == len(sid.lunations)
        sign_changed = False
        for t, s in zip(trop.lunations, sid.lunations):
            assert t.phase == s.phase
            # Phase TIME identical to within 1 second.
            assert abs(t.julian_day - s.julian_day) * 86400.0 <= 1.0
            # The elongation is preserved: the Sun-Moon separation matches the
            # phase in BOTH frames (the ayanamsha cancels in the separation).
            expected_sep = {"new": 0.0, "first_quarter": 90.0, "full": 180.0, "last_quarter": 90.0}[t.phase]
            for lun in (t, s):
                sep = abs(lun.sun.abs_pos - lun.moon.abs_pos) % 360.0
                sep = min(sep, 360.0 - sep)  # fold to [0, 180]; last_quarter (270) -> 90
                assert abs(sep - expected_sep) < 0.5
            if t.sun.sign != s.sun.sign or t.moon.sign != s.moon.sign:
                sign_changed = True
        # The ~24° Lahiri shift relabels at least some signs over two months.
        assert sign_changed

    def test_known_aug_2026_new_moon_leo_to_cancer(self):
        # The 12 Aug 2026 New Moon is ~20° Leo tropical; under Lahiri (~24°) it
        # lands in the previous sign, Cancer, at the identical instant.
        trop = LunationFinderFactory.from_iso_range("2026-08-01", "2026-08-31", phases=["new"])
        sid = LunationFinderFactory.from_iso_range(
            "2026-08-01", "2026-08-31", phases=["new"], zodiac_type="Sidereal", sidereal_mode="LAHIRI"
        )
        assert trop.lunations[0].julian_day == sid.lunations[0].julian_day
        assert trop.lunations[0].sun.sign == "Leo"
        assert sid.lunations[0].sun.sign == "Can"

    def test_sidereal_requires_mode(self):
        with pytest.raises(KerykeionException):
            LunationFinderFactory.from_iso_range("2026-01-01", "2026-02-01", zodiac_type="Sidereal")


class TestLunationFormatter:
    """The revjul-based ISO formatter must handle the BCE range."""

    def test_jd_to_iso_bce_year(self):
        # BCE years format with a signed 4-digit extended year and real seconds
        # (datetime caps at year 1, so revjul is used instead).
        from kerykeion.ephemeris_backend import ephe
        from kerykeion.lunations.lunation_factory import _jd_to_iso

        jd = ephe.julday(-44, 3, 15, 12.0)
        assert _jd_to_iso(jd) == "-0044-03-15T12:00:00Z"

    def test_jd_to_iso_ce_year(self):
        from kerykeion.ephemeris_backend import ephe
        from kerykeion.lunations.lunation_factory import _jd_to_iso

        jd = ephe.julday(2026, 8, 12, 17.0 + 30.0 / 60.0 + 42.0 / 3600.0)
        assert _jd_to_iso(jd) == "2026-08-12T17:30:42Z"


class TestLunationTruncationContract:
    """A backend failure mid-scan must raise, never silently truncate."""

    def test_backend_failure_raises(self, monkeypatch):
        # compute_lunar_phase_jd swallows backend RuntimeErrors and returns
        # None; the factory must surface that as KerykeionException instead of
        # returning an empty/partial result claiming the full range.
        import kerykeion.lunations.lunation_factory as lf

        monkeypatch.setattr(lf, "compute_lunar_phase_jd", lambda *a, **k: None)
        with pytest.raises(KerykeionException, match="ephemeris"):
            LunationFinderFactory.from_julian_day(2461041.5, 2461141.5, phases=["full"])

    def test_mid_scan_failure_raises_not_truncates(self, monkeypatch):
        # First solver call succeeds, second fails (e.g. the scan walked past
        # the ephemeris range edge): the events already found must NOT be
        # returned as if they covered the whole requested range.
        import kerykeion.lunations.lunation_factory as lf

        hits = iter([2461042.0, None])
        monkeypatch.setattr(lf, "compute_lunar_phase_jd", lambda *a, **k: next(hits))
        with pytest.raises(KerykeionException, match="full"):
            LunationFinderFactory.from_julian_day(2461041.5, 2461141.5, phases=["full"])
