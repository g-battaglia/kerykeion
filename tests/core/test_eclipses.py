# -*- coding: utf-8 -*-
"""Tests for the Eclipse Factory module."""

import pytest
from kerykeion.ephemeris_backend import swe, EPHE_DATA_PATH
from kerykeion.eclipses import EclipseFactory

_EPHE_PATH = EPHE_DATA_PATH


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


class TestLocalSearch:
    """Test location-specific eclipse search."""

    def test_finds_local_solar_eclipses(self):
        result = EclipseFactory.search_from_location(
            lat=41.9, lng=12.5, start_year=2020, count=3
        )
        assert len(result.solar_eclipses) > 0

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
        assert ecl.magnitude >= 0

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

    def test_jd_to_iso_exception_returns_empty(self):
        """_jd_to_iso should return '' when swe.revjul raises."""
        from kerykeion.eclipses.eclipse_factory import _jd_to_iso
        from unittest.mock import patch
        with patch("kerykeion.eclipses.eclipse_factory.swe.revjul", side_effect=RuntimeError("bad")):
            assert _jd_to_iso(0.0) == ""


class TestEclipseSearchBreakAndErrorPaths:
    """Test break-on-zero and exception paths in the internal search methods."""

    def test_solar_local_break_on_zero_tret(self):
        """_find_solar_local should return empty list if tret[0] == 0."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory
        from unittest.mock import patch
        zero_tret = [0.0] * 10
        with patch(
            "kerykeion.eclipses.eclipse_factory.swe.sol_eclipse_when_loc",
            return_value=(0, zero_tret, [0.0] * 10),
        ):
            result = EclipseFactory._find_solar_local(2451545.0, (12.0, 41.0, 0.0), 3)
            assert result == []

    def test_solar_local_exception_path(self):
        """_find_solar_local should handle exceptions gracefully."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory
        from unittest.mock import patch
        with patch(
            "kerykeion.eclipses.eclipse_factory.swe.sol_eclipse_when_loc",
            side_effect=RuntimeError("swe failure"),
        ):
            result = EclipseFactory._find_solar_local(2451545.0, (12.0, 41.0, 0.0), 3)
            assert result == []

    def test_solar_global_break_on_zero_tret(self):
        """_find_solar_global should return empty list if tret[0] == 0."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory
        from unittest.mock import patch
        zero_tret = [0.0] * 10
        with patch(
            "kerykeion.eclipses.eclipse_factory.swe.sol_eclipse_when_glob",
            return_value=(0, zero_tret),
        ):
            result = EclipseFactory._find_solar_global(2451545.0, 3)
            assert result == []

    def test_solar_global_exception_path(self):
        """_find_solar_global should handle exceptions gracefully."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory
        from unittest.mock import patch
        with patch(
            "kerykeion.eclipses.eclipse_factory.swe.sol_eclipse_when_glob",
            side_effect=RuntimeError("swe failure"),
        ):
            result = EclipseFactory._find_solar_global(2451545.0, 3)
            assert result == []

    def test_lunar_local_break_on_zero_tret(self):
        """_find_lunar_local should return empty list if tret[0] == 0."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory
        from unittest.mock import patch
        zero_tret = [0.0] * 10
        with patch(
            "kerykeion.eclipses.eclipse_factory.swe.lun_eclipse_when_loc",
            return_value=(0, zero_tret, [0.0] * 10),
        ):
            result = EclipseFactory._find_lunar_local(2451545.0, (12.0, 41.0, 0.0), 3)
            assert result == []

    def test_lunar_local_exception_path(self):
        """_find_lunar_local should handle exceptions gracefully."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory
        from unittest.mock import patch
        with patch(
            "kerykeion.eclipses.eclipse_factory.swe.lun_eclipse_when_loc",
            side_effect=RuntimeError("swe failure"),
        ):
            result = EclipseFactory._find_lunar_local(2451545.0, (12.0, 41.0, 0.0), 3)
            assert result == []

    def test_lunar_global_break_on_zero_tret(self):
        """_find_lunar_global should return empty list if tret[0] == 0."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory
        from unittest.mock import patch
        zero_tret = [0.0] * 10
        with patch(
            "kerykeion.eclipses.eclipse_factory.swe.lun_eclipse_when",
            return_value=(0, zero_tret),
        ):
            result = EclipseFactory._find_lunar_global(2451545.0, 3)
            assert result == []

    def test_lunar_global_exception_path(self):
        """_find_lunar_global should handle exceptions gracefully."""
        from kerykeion.eclipses.eclipse_factory import EclipseFactory
        from unittest.mock import patch
        with patch(
            "kerykeion.eclipses.eclipse_factory.swe.lun_eclipse_when",
            side_effect=RuntimeError("swe failure"),
        ):
            result = EclipseFactory._find_lunar_global(2451545.0, 3)
            assert result == []


class TestSweRegressionEclipses:
    """Regression tests: verify factory results match raw Swiss Ephemeris calls."""

    def test_solar_eclipse_jd_matches_swe(self):
        """Factory solar eclipse maximum_jd should match swe.sol_eclipse_when_glob."""
        swe.set_ephe_path(_EPHE_PATH)
        jd_2024 = swe.julday(2024, 1, 1, 0.0)
        _retflags, tret = swe.sol_eclipse_when_glob(jd_2024, swe.FLG_SWIEPH)
        swe_solar_max_jd = tret[0]
        swe.close()

        result = EclipseFactory.search_global(start_year=2024, count=1)
        assert len(result.solar_eclipses) >= 1
        factory_solar_max_jd = result.solar_eclipses[0].maximum_jd

        assert abs(factory_solar_max_jd - swe_solar_max_jd) < 0.01, (
            f"Factory solar JD {factory_solar_max_jd} != swe JD {swe_solar_max_jd}"
        )

    def test_lunar_eclipse_jd_matches_swe(self):
        """Factory lunar eclipse maximum_jd should match swe.lun_eclipse_when."""
        swe.set_ephe_path(_EPHE_PATH)
        jd_2024 = swe.julday(2024, 1, 1, 0.0)
        _retflags, tret = swe.lun_eclipse_when(jd_2024, swe.FLG_SWIEPH, 0)
        swe_lunar_max_jd = tret[0]
        swe.close()

        result = EclipseFactory.search_global(start_year=2024, count=1)
        assert len(result.lunar_eclipses) >= 1
        factory_lunar_max_jd = result.lunar_eclipses[0].maximum_jd

        assert abs(factory_lunar_max_jd - swe_lunar_max_jd) < 0.01, (
            f"Factory lunar JD {factory_lunar_max_jd} != swe JD {swe_lunar_max_jd}"
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
        if hasattr(swe, "get_saros_number"):
            assert ecl.saros == 126

    def test_solar_gamma_and_duration_when_available(self):
        result = EclipseFactory.search_global(start_year=2026, count=2)
        central = [e for e in result.solar_eclipses if e.type in ("total", "annular")]
        assert central
        ecl = central[0]
        if hasattr(swe, "sol_eclipse_max_time"):
            assert ecl.gamma is not None
            assert -1.6 < ecl.gamma < 1.6
        if hasattr(swe, "calc_solar_eclipse_duration"):
            # Central eclipses have a positive duration; partial -> None.
            assert ecl.duration_minutes is None or ecl.duration_minutes > 0

    def test_swisseph_guard_returns_none(self):
        """When libephemeris extensions are absent, series fields stay empty."""
        from unittest.mock import patch
        from kerykeion.eclipses import eclipse_factory as ef

        with patch.object(ef.swe, "get_saros_number", None), \
             patch.object(ef.swe, "get_inex_number", None):
            assert ef._saros_inex(2451545.0, "solar") == {}
