# -*- coding: utf-8 -*-
"""Tests for the Eclipse Factory module."""

import pytest
from kerykeion.ephemeris_backend import swe
from pathlib import Path
from kerykeion.eclipses import EclipseFactory

_EPHE_PATH = str(Path(__file__).parent.parent.parent / "kerykeion" / "sweph")


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
