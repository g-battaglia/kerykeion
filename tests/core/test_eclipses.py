# -*- coding: utf-8 -*-
"""Tests for the Eclipse Factory module."""

import pytest
import swisseph as swe
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
