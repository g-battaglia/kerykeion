# -*- coding: utf-8 -*-
"""Tests for Local Space azimuth/altitude calculations."""

import pytest
from kerykeion.ephemeris_backend import ephe
from kerykeion import AstrologicalSubjectFactory


@pytest.fixture(scope="module")
def subject_with_local_space():
    return AstrologicalSubjectFactory.from_birth_data(
        "Local Space Test",
        1990,
        6,
        15,
        14,
        30,
        lng=12.4964,
        lat=41.9028,
        tz_str="Europe/Rome",
        city="Rome",
        nation="IT",
        online=False,
        calculate_local_space=True,
    )


@pytest.fixture(scope="module")
def subject_without_local_space():
    return AstrologicalSubjectFactory.from_birth_data(
        "No Local Space",
        1990,
        6,
        15,
        14,
        30,
        lng=12.4964,
        lat=41.9028,
        tz_str="Europe/Rome",
        city="Rome",
        nation="IT",
        online=False,
    )


class TestLocalSpaceCalculation:
    def test_azimuth_populated(self, subject_with_local_space):
        """Planets should have azimuth when local space is enabled."""
        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(subject_with_local_space, name)
            if point is not None:
                assert point.azimuth is not None, f"{name} should have azimuth"

    def test_altitude_populated(self, subject_with_local_space):
        """Planets should have altitude_above_horizon when local space is enabled."""
        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(subject_with_local_space, name)
            if point is not None:
                assert point.altitude_above_horizon is not None, f"{name} should have altitude_above_horizon"

    def test_not_populated_by_default(self, subject_without_local_space):
        """Azimuth/altitude should be None when not enabled."""
        assert subject_without_local_space.sun.azimuth is None
        assert subject_without_local_space.sun.altitude_above_horizon is None

    def test_azimuth_range(self, subject_with_local_space):
        """Azimuth should be in 0-360 range."""
        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(subject_with_local_space, name)
            if point is not None and point.azimuth is not None:
                assert 0 <= point.azimuth < 360, f"{name} azimuth {point.azimuth} outside 0-360 range"

    def test_altitude_range(self, subject_with_local_space):
        """Altitude should be between -90 and +90 degrees."""
        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(subject_with_local_space, name)
            if point is not None and point.altitude_above_horizon is not None:
                assert -90 <= point.altitude_above_horizon <= 90, (
                    f"{name} altitude {point.altitude_above_horizon} outside -90 to +90 range"
                )

    def test_sun_altitude_positive_for_daytime(self, subject_with_local_space):
        """For a 14:30 birth, the Sun should be above the horizon in Rome in June."""
        sun_alt = subject_with_local_space.sun.altitude_above_horizon
        assert sun_alt > 0, f"Sun altitude {sun_alt} should be positive for daytime chart"

    def test_different_planets_different_azimuths(self, subject_with_local_space):
        """Not all planets should have the same azimuth."""
        azimuths = []
        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(subject_with_local_space, name)
            if point is not None and point.azimuth is not None:
                azimuths.append(round(point.azimuth))
        assert len(set(azimuths)) > 1, "All planets have the same azimuth"

    def test_ecliptic_latitude_populated(self, subject_with_local_space):
        """Planets should expose their true ecliptic latitude (v6.0)."""
        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(subject_with_local_space, name)
            if point is not None:
                assert point.ecliptic_latitude is not None, f"{name} should have ecliptic_latitude"

    def test_true_ecliptic_latitude_used_not_flat_zero(self, subject_with_local_space):
        """Off-ecliptic bodies must project with their true latitude, not a flat 0.

        Locks in the v6 fix: the local-space azimuth/altitude must match an
        ephe.azalt call using the body's real ecliptic latitude, and that result
        must differ from the old (lat=0) projection for bodies off the ecliptic.
        """
        jd = subject_with_local_space.julian_day
        geopos = (subject_with_local_space.lng, subject_with_local_space.lat, 0.0)
        ephe.set_ephe_path("")

        checked = 0
        for name in ["moon", "mars", "jupiter", "saturn", "pluto"]:
            point = getattr(subject_with_local_space, name, None)
            if point is None or point.ecliptic_latitude is None or abs(point.ecliptic_latitude) <= 1.0:
                continue
            checked += 1
            true_proj = ephe.azalt(jd, ephe.ECL2HOR, geopos, 0, 0, (point.abs_pos, point.ecliptic_latitude, 1.0))
            flat_proj = ephe.azalt(jd, ephe.ECL2HOR, geopos, 0, 0, (point.abs_pos, 0.0, 1.0))
            # Production matches the TRUE-latitude reference...
            assert abs(point.altitude_above_horizon - true_proj[1]) < 0.01, f"{name} altitude off true reference"
            # ...and that differs from the old flat lat=0 projection.
            assert abs(true_proj[1] - flat_proj[1]) > 0.01, f"{name} should differ from flat lat=0"
        assert checked > 0, "expected at least one off-ecliptic body to verify"

    def test_sun_azalt_matches_swe_reference(self, subject_with_local_space):
        """Sun azimuth/altitude must match a direct ephe.azalt call."""
        jd = subject_with_local_space.julian_day
        geopos = (
            subject_with_local_space.lng,
            subject_with_local_space.lat,
            0.0,
        )
        ephe.set_ephe_path("")

        # Get the Sun ecliptic longitude/latitude that the factory used.
        sun_ecl_lon = subject_with_local_space.sun.abs_pos
        sun_ecl_lat = subject_with_local_space.sun.ecliptic_latitude or 0.0
        # The factory passes (abs_pos, ecliptic_latitude, 1.0) for ecl_coords.
        ecl_coords = (sun_ecl_lon, sun_ecl_lat, 1.0)
        azalt_result = ephe.azalt(jd, ephe.ECL2HOR, geopos, 0, 0, ecl_coords)

        expected_azimuth = azalt_result[0]
        expected_altitude = azalt_result[1]

        assert abs(subject_with_local_space.sun.azimuth - expected_azimuth) < 0.01, (
            f"Sun azimuth {subject_with_local_space.sun.azimuth} != ephe reference {expected_azimuth}"
        )
        assert abs(subject_with_local_space.sun.altitude_above_horizon - expected_altitude) < 0.01, (
            f"Sun altitude {subject_with_local_space.sun.altitude_above_horizon} != ephe reference {expected_altitude}"
        )

    def test_mars_azalt_matches_swe_reference(self, subject_with_local_space):
        """Mars azimuth/altitude must match a direct ephe.azalt call."""
        jd = subject_with_local_space.julian_day
        geopos = (
            subject_with_local_space.lng,
            subject_with_local_space.lat,
            0.0,
        )
        ephe.set_ephe_path("")

        mars_ecl_lon = subject_with_local_space.mars.abs_pos
        mars_ecl_lat = subject_with_local_space.mars.ecliptic_latitude or 0.0
        ecl_coords = (mars_ecl_lon, mars_ecl_lat, 1.0)
        azalt_result = ephe.azalt(jd, ephe.ECL2HOR, geopos, 0, 0, ecl_coords)

        assert abs(subject_with_local_space.mars.azimuth - azalt_result[0]) < 0.01, (
            f"Mars azimuth {subject_with_local_space.mars.azimuth} != ephe reference {azalt_result[0]}"
        )
        assert abs(subject_with_local_space.mars.altitude_above_horizon - azalt_result[1]) < 0.01, (
            f"Mars altitude {subject_with_local_space.mars.altitude_above_horizon} != ephe reference {azalt_result[1]}"
        )
