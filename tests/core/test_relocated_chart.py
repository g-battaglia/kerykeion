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
