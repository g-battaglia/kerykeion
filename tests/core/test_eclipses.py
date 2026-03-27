# -*- coding: utf-8 -*-
"""Tests for the Eclipse Factory module."""

import pytest
from kerykeion.eclipses import EclipseFactory


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
        if result.solar_eclipses:
            ecl = result.solar_eclipses[0]
            assert ecl.type in ("total", "annular", "partial", "annular-total", "unknown")
            assert ecl.maximum_jd > 0
            assert len(ecl.datestamp) > 0

    def test_lunar_eclipse_has_type(self):
        result = EclipseFactory.search_global(start_year=2025, count=1)
        if result.lunar_eclipses:
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
        if result.solar_eclipses:
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
