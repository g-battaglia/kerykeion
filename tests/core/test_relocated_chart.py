# -*- coding: utf-8 -*-
"""Tests for the Relocated Chart factory."""

import pytest
from kerykeion import AstrologicalSubjectFactory, RelocatedChartFactory


@pytest.fixture(scope="module")
def natal():
    return AstrologicalSubjectFactory.from_birth_data(
        "Test Subject", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
    )


class TestRelocatedChart:
    def test_planets_unchanged(self, natal):
        relocated = RelocatedChartFactory.relocate(natal, new_lat=40.7128, new_lng=-74.006, new_city="New York")
        assert abs(relocated.sun.abs_pos - natal.sun.abs_pos) < 0.001
        assert abs(relocated.moon.abs_pos - natal.moon.abs_pos) < 0.001
        assert abs(relocated.mars.abs_pos - natal.mars.abs_pos) < 0.001

    def test_houses_changed(self, natal):
        relocated = RelocatedChartFactory.relocate(natal, new_lat=40.7128, new_lng=-74.006, new_city="New York")
        # With such a large longitude difference, houses should differ significantly
        assert abs(relocated.ascendant.abs_pos - natal.ascendant.abs_pos) > 1.0

    def test_city_updated(self, natal):
        relocated = RelocatedChartFactory.relocate(natal, new_lat=40.7128, new_lng=-74.006, new_city="New York", new_nation="US")
        assert relocated.city == "New York"
        assert relocated.nation == "US"
        assert relocated.lat == 40.7128
        assert relocated.lng == -74.006

    def test_same_julian_day(self, natal):
        relocated = RelocatedChartFactory.relocate(natal, new_lat=51.5, new_lng=-0.1, new_city="London")
        assert relocated.julian_day == natal.julian_day

    def test_relocate_to_same_location_preserves_houses(self, natal):
        relocated = RelocatedChartFactory.relocate(natal, new_lat=natal.lat, new_lng=natal.lng)
        # Houses should be very similar (small numerical differences possible)
        assert abs(relocated.ascendant.abs_pos - natal.ascendant.abs_pos) < 0.5

    def test_all_houses_present(self, natal):
        relocated = RelocatedChartFactory.relocate(natal, new_lat=35.6895, new_lng=139.6917, new_city="Tokyo")
        for attr in ["first_house", "second_house", "third_house", "fourth_house",
                      "fifth_house", "sixth_house", "seventh_house", "eighth_house",
                      "ninth_house", "tenth_house", "eleventh_house", "twelfth_house"]:
            house = getattr(relocated, attr)
            assert house is not None
            assert 0 <= house.abs_pos < 360


class TestRelocatedSweReference:
    """Compare factory relocated ASC/MC with direct swe.houses_armc() output."""

    def test_relocated_asc_mc_match_swe(self, natal):
        """Factory relocated ASC and MC must match raw swe.houses_armc()."""
        import swisseph as swe
        from pathlib import Path

        swe.set_ephe_path(str(Path(__file__).parents[2] / "kerykeion" / "sweph"))

        new_lat = 40.7128
        new_lng = -74.006
        relocated = RelocatedChartFactory.relocate(natal, new_lat=new_lat, new_lng=new_lng, new_city="New York")

        jd = natal.julian_day
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED
        hsys = natal.houses_system_identifier.encode("ascii")

        # Obliquity of ecliptic
        eps = swe.calc_ut(jd, swe.ECL_NUT, iflag)[0][0]

        # ARMC for new location (same logic as factory)
        armc_hours = swe.sidtime(jd)
        local_st_hours = armc_hours + new_lng / 15.0
        armc_degrees = (local_st_hours * 15.0) % 360.0

        # Direct swe.houses_armc call
        cusps, ascmc = swe.houses_armc(armc_degrees, new_lat, eps, hsys)
        expected_asc = ascmc[0] % 360
        expected_mc = ascmc[1] % 360

        assert relocated.ascendant.abs_pos == pytest.approx(expected_asc, abs=0.01), (
            f"Relocated ASC {relocated.ascendant.abs_pos} != swe ASC {expected_asc}"
        )
        assert relocated.medium_coeli.abs_pos == pytest.approx(expected_mc, abs=0.01), (
            f"Relocated MC {relocated.medium_coeli.abs_pos} != swe MC {expected_mc}"
        )

    def test_relocated_tokyo_asc_mc_match_swe(self, natal):
        """Same check for Tokyo to ensure generalisation across locations."""
        import swisseph as swe
        from pathlib import Path

        swe.set_ephe_path(str(Path(__file__).parents[2] / "kerykeion" / "sweph"))

        new_lat = 35.6895
        new_lng = 139.6917
        relocated = RelocatedChartFactory.relocate(natal, new_lat=new_lat, new_lng=new_lng, new_city="Tokyo")

        jd = natal.julian_day
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED
        hsys = natal.houses_system_identifier.encode("ascii")

        eps = swe.calc_ut(jd, swe.ECL_NUT, iflag)[0][0]
        armc_hours = swe.sidtime(jd)
        local_st_hours = armc_hours + new_lng / 15.0
        armc_degrees = (local_st_hours * 15.0) % 360.0

        cusps, ascmc = swe.houses_armc(armc_degrees, new_lat, eps, hsys)
        expected_asc = ascmc[0] % 360
        expected_mc = ascmc[1] % 360

        assert relocated.ascendant.abs_pos == pytest.approx(expected_asc, abs=0.01)
        assert relocated.medium_coeli.abs_pos == pytest.approx(expected_mc, abs=0.01)
