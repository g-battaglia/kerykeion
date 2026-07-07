# -*- coding: utf-8 -*-
"""Tests for the Eclipse Factory module."""

import pytest
from kerykeion.ephemeris_backend import ephe, ephemeris_session
from kerykeion.eclipses import EclipseFactory
from kerykeion.schemas.kerykeion_exception import KerykeionException


class TestGlobalSearch:
    """Test global eclipse search (no location)."""

    def test_finds_solar_eclipses(self):
        result = EclipseFactory.search_global(start_year=2025, count=3)
        assert len(result.solar_eclipses) > 0
        assert len(result.solar_eclipses) <= 3

    def test_finds_lunar_eclipses(self):
        result = EclipseFactory.search_global(start_year=2025, count=3)
        assert len(result.lunar_eclipses) > 0
        assert len(result.lunar_eclipses) <= 3

    def test_no_location_in_global(self):
        result = EclipseFactory.search_global(start_year=2025, count=1)
        assert result.latitude is None
        assert result.longitude is None

    def test_solar_eclipse_has_type(self):
        result = EclipseFactory.search_global(start_year=2025, count=1)
        assert len(result.solar_eclipses) >= 1, "Global search with count=1 should find at least one solar eclipse"
        ecl = result.solar_eclipses[0]
        assert ecl.type in ("total", "annular", "partial", "annular-total", "unknown")
        assert ecl.maximum_jd > 0
        assert len(ecl.datestamp) > 0

    def test_global_magnitude_and_obscuration_are_none(self):
        # magnitude/obscuration are observer-dependent; in global mode there is
        # no observer, so they must be None (not a fake 0.0).
        result = EclipseFactory.search_global(start_year=2025, count=2)
        assert result.solar_eclipses
        for ecl in result.solar_eclipses:
            assert ecl.magnitude is None
            assert ecl.obscuration is None

    def test_count_too_large_rejected_upfront(self):
        with pytest.raises(ValueError):
            EclipseFactory.search_global(start_year=2025, count=1_000_001)
        with pytest.raises(ValueError):
            EclipseFactory.search_from_location(lat=41.9, lng=12.5, count=1_000_001)

    def test_lunar_eclipse_has_type(self):
        result = EclipseFactory.search_global(start_year=2025, count=1)
        assert len(result.lunar_eclipses) >= 1, "Global search with count=1 should find at least one lunar eclipse"
        ecl = result.lunar_eclipses[0]
        assert ecl.type in ("total", "partial", "penumbral", "unknown")
        assert ecl.maximum_jd > 0

    def test_eclipses_in_chronological_order(self):
        result = EclipseFactory.search_global(start_year=2020, count=5)
        for eclipses in [result.solar_eclipses, result.lunar_eclipses]:
            for i in range(len(eclipses) - 1):
                assert eclipses[i].maximum_jd < eclipses[i + 1].maximum_jd


class TestDefaultStartYear:
    """start_year defaults to the current UTC year at call time (a wired-in
    default year would silently age)."""

    @staticmethod
    def _capture_julday(monkeypatch):
        import kerykeion.eclipses.eclipse_factory as ef

        captured = {}

        def fake_julday(year, month, day, hour):
            captured["args"] = (year, month, day, hour)
            return 2451545.0

        monkeypatch.setattr(ef.ephe, "julday", fake_julday)
        # Stub the internal searches: only the start_jd resolution is under test.
        monkeypatch.setattr(ef.EclipseFactory, "_find_solar_global", staticmethod(lambda jd, count: []))
        monkeypatch.setattr(ef.EclipseFactory, "_find_lunar_global", staticmethod(lambda jd, count: []))
        monkeypatch.setattr(ef.EclipseFactory, "_find_solar_local", staticmethod(lambda jd, geopos, count: []))
        monkeypatch.setattr(ef.EclipseFactory, "_find_lunar_local", staticmethod(lambda jd, geopos, count: []))
        return captured

    def test_global_default_is_current_utc_year(self, monkeypatch):
        from datetime import datetime, timezone

        captured = self._capture_julday(monkeypatch)
        EclipseFactory.search_global()
        assert captured["args"] == (datetime.now(timezone.utc).year, 1, 1, 0.0)

    def test_local_default_is_current_utc_year(self, monkeypatch):
        from datetime import datetime, timezone

        captured = self._capture_julday(monkeypatch)
        EclipseFactory.search_from_location(lat=41.9, lng=12.5)
        assert captured["args"] == (datetime.now(timezone.utc).year, 1, 1, 0.0)

    def test_explicit_start_year_still_honored(self, monkeypatch):
        captured = self._capture_julday(monkeypatch)
        EclipseFactory.search_global(start_year=2030)
        assert captured["args"] == (2030, 1, 1, 0.0)


class TestLocalSearch:
    """Test location-specific eclipse search."""

    def test_finds_local_solar_eclipses(self):
        result = EclipseFactory.search_from_location(
            lat=41.9, lng=12.5, start_year=2020, count=3
        )
        assert len(result.solar_eclipses) > 0

    def test_local_solar_omits_global_gamma_duration(self):
        # gamma and central duration are global central-line properties; local
        # results (max_jd = observer maximum) must not carry them.
        result = EclipseFactory.search_from_location(
            lat=41.9, lng=12.5, start_year=2020, count=3
        )
        assert result.solar_eclipses
        for e in result.solar_eclipses:
            assert e.gamma is None
            assert e.duration_minutes is None

    def test_finds_local_lunar_eclipses(self):
        result = EclipseFactory.search_from_location(
            lat=41.9, lng=12.5, start_year=2020, count=3
        )
        assert len(result.lunar_eclipses) > 0

    def test_location_stored(self):
        result = EclipseFactory.search_from_location(
            lat=41.9, lng=12.5, start_year=2025, count=1
        )
        assert result.latitude == 41.9
        assert result.longitude == 12.5

    def test_solar_has_magnitude(self):
        result = EclipseFactory.search_from_location(
            lat=41.9, lng=12.5, start_year=2020, count=1
        )
        assert len(result.solar_eclipses) >= 1, "Local search from Rome with count=1 should find at least one solar eclipse"
        ecl = result.solar_eclipses[0]
        # Local searches populate the observer-dependent fields.
        assert ecl.magnitude is not None and ecl.magnitude >= 0
        assert ecl.obscuration is not None and ecl.obscuration >= 0

    def test_datestamp_format(self):
        result = EclipseFactory.search_from_location(
            lat=0, lng=0, start_year=2020, count=1
        )
        for eclipses in [result.solar_eclipses, result.lunar_eclipses]:
            for ecl in eclipses:
                assert "T" in ecl.datestamp
                assert ecl.datestamp.endswith("Z")


class TestClassifyHelpers:
    """Test the classification helper functions and _jd_to_iso edge cases."""

    def test_classify_solar_annular_total(self):
        """ECL_ANNULAR_TOTAL flag should classify as 'annular-total'."""
        from kerykeion.eclipses.eclipse_factory import (
            _classify_solar_eclipse, ECL_ANNULAR_TOTAL,
        )
        assert _classify_solar_eclipse(ECL_ANNULAR_TOTAL) == "annular-total"

    def test_classify_solar_unknown(self):
        """Flag 0 (no type bits) should classify as 'unknown'."""
        from kerykeion.eclipses.eclipse_factory import _classify_solar_eclipse
        assert _classify_solar_eclipse(0) == "unknown"

    def test_classify_lunar_unknown(self):
        """Flag 0 (no type bits) should classify as 'unknown'."""
        from kerykeion.eclipses.eclipse_factory import _classify_lunar_eclipse
        assert _classify_lunar_eclipse(0) == "unknown"

    def test_jd_to_iso_bce_year(self):
        """BCE Julian Days must format with a signed 4-digit extended year and
        real seconds, e.g. -0044-03-15T12:00:00Z (not the old '-044-...')."""
        from kerykeion.eclipses.eclipse_factory import _jd_to_iso

        jd = ephe.julday(-44, 3, 15, 12.0)
        assert _jd_to_iso(jd) == "-0044-03-15T12:00:00Z"

    def test_jd_to_iso_ce_year_with_seconds(self):
        """CE formatting keeps the unsigned year and includes real seconds."""
        from kerykeion.eclipses.eclipse_factory import _jd_to_iso

        jd = ephe.julday(2026, 8, 12, 17.0 + 30.0 / 60.0 + 42.0 / 3600.0)
        assert _jd_to_iso(jd) == "2026-08-12T17:30:42Z"


class TestEclipseSearchBreakAndErrorPaths:
    """Test break-on-zero and exception paths in the internal search methods."""

    def test_solar_local_break_on_zero_tret(self):
        """_find_solar_local should return empty list if tret[0] == 0."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory
        from unittest.mock import patch
        zero_tret = [0.0] * 10
        with patch(
            "kerykeion.eclipses.eclipse_factory.ephe.sol_eclipse_when_loc",
            return_value=(0, zero_tret, [0.0] * 10),
        ):
            result = EclipseFactory._find_solar_local(2451545.0, (12.0, 41.0, 0.0), 3)
            assert result == []

    def test_solar_local_backend_failure_raises(self):
        """A backend failure must abort the search as KerykeionException
        (with the failing JD), never silently return partial results."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory
        from unittest.mock import patch
        with patch(
            "kerykeion.eclipses.eclipse_factory.ephe.sol_eclipse_when_loc",
            side_effect=RuntimeError("ephe failure"),
        ):
            with pytest.raises(KerykeionException, match=r"JD 2451545\."):
                EclipseFactory._find_solar_local(2451545.0, (12.0, 41.0, 0.0), 3)

    def test_solar_global_break_on_zero_tret(self):
        """_find_solar_global should return empty list if tret[0] == 0."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory
        from unittest.mock import patch
        zero_tret = [0.0] * 10
        with patch(
            "kerykeion.eclipses.eclipse_factory.ephe.sol_eclipse_when_glob",
            return_value=(0, zero_tret),
        ):
            result = EclipseFactory._find_solar_global(2451545.0, 3)
            assert result == []

    def test_solar_global_backend_failure_raises(self):
        """A backend failure must abort the search as KerykeionException."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory
        from unittest.mock import patch
        with patch(
            "kerykeion.eclipses.eclipse_factory.ephe.sol_eclipse_when_glob",
            side_effect=RuntimeError("ephe failure"),
        ):
            with pytest.raises(KerykeionException, match="ephemeris range"):
                EclipseFactory._find_solar_global(2451545.0, 3)

    def test_solar_global_mid_scan_failure_raises_not_truncates(self):
        """If the backend fails after some events were already found (e.g. the
        scan walked past the ephemeris range edge), the whole search must raise
        rather than return a truncated list claiming full coverage."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory, ECL_TOTAL
        from unittest.mock import patch
        good = (ECL_TOTAL, [2451550.0] + [0.0] * 9)
        with patch(
            "kerykeion.eclipses.eclipse_factory.ephe.sol_eclipse_when_glob",
            side_effect=[good, RuntimeError("jd 2451560 outside ephemeris range")],
        ):
            with pytest.raises(KerykeionException, match=r"JD 2451560\."):
                EclipseFactory.search_global(start_year=2000, count=3)

    def test_lunar_local_break_on_zero_tret(self):
        """_find_lunar_local should return empty list if tret[0] == 0."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory
        from unittest.mock import patch
        zero_tret = [0.0] * 10
        with patch(
            "kerykeion.eclipses.eclipse_factory.ephe.lun_eclipse_when_loc",
            return_value=(0, zero_tret, [0.0] * 10),
        ):
            result = EclipseFactory._find_lunar_local(2451545.0, (12.0, 41.0, 0.0), 3)
            assert result == []

    def test_lunar_local_backend_failure_raises(self):
        """A backend failure must abort the search as KerykeionException."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory
        from unittest.mock import patch
        with patch(
            "kerykeion.eclipses.eclipse_factory.ephe.lun_eclipse_when_loc",
            side_effect=RuntimeError("ephe failure"),
        ):
            with pytest.raises(KerykeionException, match=r"JD 2451545\."):
                EclipseFactory._find_lunar_local(2451545.0, (12.0, 41.0, 0.0), 3)

    def test_lunar_global_break_on_zero_tret(self):
        """_find_lunar_global should return empty list if tret[0] == 0."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory
        from unittest.mock import patch
        zero_tret = [0.0] * 10
        with patch(
            "kerykeion.eclipses.eclipse_factory.ephe.lun_eclipse_when",
            return_value=(0, zero_tret),
        ):
            result = EclipseFactory._find_lunar_global(2451545.0, 3)
            assert result == []

    def test_lunar_global_backend_failure_raises(self):
        """A backend failure must abort the search as KerykeionException."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory
        from unittest.mock import patch
        with patch(
            "kerykeion.eclipses.eclipse_factory.ephe.lun_eclipse_when",
            side_effect=RuntimeError("ephe failure"),
        ):
            with pytest.raises(KerykeionException, match="ephemeris range"):
                EclipseFactory._find_lunar_global(2451545.0, 3)


class TestSweRegressionEclipses:
    """Regression tests: verify factory results match raw Swiss Ephemeris calls."""

    def test_solar_eclipse_jd_matches_swe(self):
        """Factory solar eclipse maximum_jd should match ephe.sol_eclipse_when_glob."""
        with ephemeris_session():
            jd_2024 = ephe.julday(2024, 1, 1, 0.0)
            _retflags, tret = ephe.sol_eclipse_when_glob(jd_2024, ephe.FLG_SWIEPH)
            swe_solar_max_jd = tret[0]

        result = EclipseFactory.search_global(start_year=2024, count=1)
        assert len(result.solar_eclipses) >= 1
        factory_solar_max_jd = result.solar_eclipses[0].maximum_jd

        assert abs(factory_solar_max_jd - swe_solar_max_jd) < 0.01, (
            f"Factory solar JD {factory_solar_max_jd} != ephe JD {swe_solar_max_jd}"
        )

    def test_lunar_eclipse_jd_matches_swe(self):
        """Factory lunar eclipse maximum_jd should match ephe.lun_eclipse_when."""
        with ephemeris_session():
            jd_2024 = ephe.julday(2024, 1, 1, 0.0)
            _retflags, tret = ephe.lun_eclipse_when(jd_2024, ephe.FLG_SWIEPH, 0)
            swe_lunar_max_jd = tret[0]

        result = EclipseFactory.search_global(start_year=2024, count=1)
        assert len(result.lunar_eclipses) >= 1
        factory_lunar_max_jd = result.lunar_eclipses[0].maximum_jd

        assert abs(factory_lunar_max_jd - swe_lunar_max_jd) < 0.01, (
            f"Factory lunar JD {factory_lunar_max_jd} != ephe JD {swe_lunar_max_jd}"
        )


class TestEclipseEnrichment:
    """Zodiac position + catalogued series/geometry enrichment fields."""

    def test_solar_has_zodiac_position(self):
        result = EclipseFactory.search_global(start_year=2026, count=2)
        ecl = result.solar_eclipses[0]
        assert ecl.sign is not None
        assert 0 <= ecl.sign_num <= 11
        assert 0.0 <= ecl.degree < 30.0
        assert 0.0 <= ecl.ecliptic_longitude < 360.0

    def test_lunar_has_zodiac_position(self):
        result = EclipseFactory.search_global(start_year=2026, count=2)
        ecl = result.lunar_eclipses[0]
        assert ecl.sign is not None
        assert 0 <= ecl.sign_num <= 11

    def test_aug_2026_total_solar_in_leo(self):
        """The 12 Aug 2026 total solar eclipse falls at ~20 deg Leo, Saros 126."""
        result = EclipseFactory.search_global(start_year=2026, count=2)
        totals = [e for e in result.solar_eclipses if e.type == "total"]
        assert totals, "expected a total solar eclipse in 2026"
        ecl = totals[0]
        assert ecl.sign == "Leo"
        assert 19.0 <= ecl.degree <= 21.0
        if hasattr(ephe, "get_saros_number"):
            assert ecl.saros == 126

    def test_solar_gamma_and_duration_when_available(self):
        result = EclipseFactory.search_global(start_year=2026, count=2)
        central = [e for e in result.solar_eclipses if e.type in ("total", "annular")]
        assert central
        ecl = central[0]
        if hasattr(ephe, "sol_eclipse_max_time"):
            assert ecl.gamma is not None
            assert -1.6 < ecl.gamma < 1.6
        if hasattr(ephe, "calc_solar_eclipse_duration"):
            # Central eclipses have a positive duration; partial -> None.
            assert ecl.duration_minutes is None or ecl.duration_minutes > 0

    def test_swisseph_guard_returns_none(self):
        """When libephemeris extensions are absent, series fields stay empty."""
        from unittest.mock import patch
        from kerykeion.eclipses import eclipse_factory as ef

        with patch.object(ef.ephe, "get_saros_number", None, create=True), \
             patch.object(ef.ephe, "get_inex_number", None, create=True):
            assert ef._saros_inex(2451545.0, "solar") == {}

    def test_non_positive_saros_inex_treated_as_missing(self):
        """libephemeris returns 0 when an eclipse is absent from its catalog
        tables (e.g. the 2027-02-06 annular, canonically Saros 131); a
        non-positive number must become None, never a plausible-looking
        series value."""
        from unittest.mock import patch
        from kerykeion.eclipses import eclipse_factory as ef

        with patch.object(ef.ephe, "get_saros_number", lambda jd, kind: 0, create=True), \
             patch.object(ef.ephe, "get_inex_number", lambda jd, kind: -3, create=True):
            assert ef._saros_inex(2451545.0, "solar") == {}

    def test_positive_saros_pass_through_inex_never_trusted(self):
        """Real (positive) saros numbers are forwarded unchanged; inex is NOT
        populated even when get_inex_number returns a positive value, because
        libephemeris <= 2.0.2 nearest-matches a handful of reference eclipses
        with no residual threshold (every 2026-2027 eclipse reports inex 50,
        mathematically impossible for consecutive eclipses)."""
        from unittest.mock import patch
        from kerykeion.eclipses import eclipse_factory as ef

        with patch.object(ef.ephe, "get_saros_number", lambda jd, kind: 126, create=True), \
             patch.object(ef.ephe, "get_inex_number", lambda jd, kind: 50, create=True):
            assert ef._saros_inex(2451545.0, "solar") == {"saros": 126}

    def test_saros_inex_never_zero_in_results(self):
        """A search window covering the 2027-02-06 annular (missing from the
        libephemeris saros tables) must report saros=None for it, not 0; inex
        is reserved (always None) until upstream provides trustworthy data."""
        result = EclipseFactory.search_global(start_year=2026, count=4)
        for ecl in result.solar_eclipses + result.lunar_eclipses:
            assert ecl.saros is None or ecl.saros > 0
            assert ecl.inex is None

    def test_global_lunar_magnitudes_populated(self):
        """Lunar magnitudes are observer-independent, so global searches must
        report them (the 2025-03-14 total lunar eclipse has umbral magnitude
        ~1.178 and penumbral ~2.26)."""
        result = EclipseFactory.search_global(start_year=2025, count=1)
        assert result.lunar_eclipses
        ecl = result.lunar_eclipses[0]
        assert ecl.type == "total"
        assert ecl.magnitude_umbral == pytest.approx(1.178, abs=0.01)
        assert ecl.magnitude_penumbral == pytest.approx(2.262, abs=0.01)

    def test_global_lunar_magnitudes_all_events(self):
        """Every global lunar result carries both magnitudes; penumbral
        eclipses have a non-positive umbral magnitude (the Moon misses the
        umbra; observed 0.0 on both backends, negative also acceptable)."""
        # 2026 count=4 includes the 2027-02-20 and 2027-07-18 penumbrals.
        result = EclipseFactory.search_global(start_year=2026, count=4)
        assert result.lunar_eclipses
        assert any(e.type == "penumbral" for e in result.lunar_eclipses)
        for ecl in result.lunar_eclipses:
            assert ecl.magnitude_umbral is not None
            assert ecl.magnitude_penumbral is not None
            assert ecl.magnitude_penumbral > 0
            if ecl.type == "penumbral":
                assert ecl.magnitude_umbral <= 0
            else:
                assert ecl.magnitude_umbral > 0


@pytest.mark.parametrize(
    "module_path",
    [
        "kerykeion.eclipses.eclipse_factory",
        "kerykeion.lunations.lunation_factory",
        "kerykeion.occultations.occultation_factory",
    ],
)
def test_jd_to_iso_rolls_over_midnight(module_path):
    """A time rounding up to 24:00:00 must roll over to 00:00:00 of the next
    calendar day (carrying the month/year boundary) instead of clamping to
    23:59:59 of the same day. The three private ``_jd_to_iso`` helpers share
    this logic, so all three are checked."""
    import importlib

    _jd_to_iso = importlib.import_module(module_path)._jd_to_iso

    # 2020-01-31 23:59:59.8 UT → rounds to next-day midnight, across the month
    # (and is a leap year, exercising the day/month carry).
    jd = ephe.julday(2020, 2, 1, 0.0) - (0.2 / 86400.0)
    assert _jd_to_iso(jd) == "2020-02-01T00:00:00Z"

    # A year boundary too: 2019-12-31 23:59:59.9 UT → 2020-01-01T00:00:00Z.
    jd_year = ephe.julday(2020, 1, 1, 0.0) - (0.1 / 86400.0)
    assert _jd_to_iso(jd_year) == "2020-01-01T00:00:00Z"

    # A normal mid-day time is unaffected.
    assert _jd_to_iso(ephe.julday(2020, 6, 15, 12.5)) == "2020-06-15T12:30:00Z"
