# -*- coding: utf-8 -*-
"""Tests for Local Space azimuth/altitude calculations."""

import pytest
from kerykeion import AstrologicalSubjectFactory


@pytest.fixture(scope="module")
def subject_with_local_space():
    return AstrologicalSubjectFactory.from_birth_data(
        "Local Space Test", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
        calculate_local_space=True,
    )


@pytest.fixture(scope="module")
def subject_without_local_space():
    return AstrologicalSubjectFactory.from_birth_data(
        "No Local Space", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
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
                assert point.altitude_above_horizon is not None, (
                    f"{name} should have altitude_above_horizon"
                )

    def test_not_populated_by_default(self, subject_without_local_space):
        """Azimuth/altitude should be None when not enabled."""
        assert subject_without_local_space.sun.azimuth is None
        assert subject_without_local_space.sun.altitude_above_horizon is None

    def test_azimuth_range(self, subject_with_local_space):
        """Azimuth should be in 0-360 range."""
        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(subject_with_local_space, name)
            if point is not None and point.azimuth is not None:
                assert 0 <= point.azimuth < 360, (
                    f"{name} azimuth {point.azimuth} outside 0-360 range"
                )

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
