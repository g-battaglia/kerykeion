# -*- coding: utf-8 -*-
"""Tests for planetocentric perspective calculations."""

import pytest
from kerykeion import AstrologicalSubjectFactory


@pytest.fixture(scope="module")
def geocentric():
    return AstrologicalSubjectFactory.from_birth_data(
        "Geocentric", 2000, 1, 1, 12, 0,
        lng=0.0, lat=51.5, tz_str="Etc/GMT",
        city="Greenwich", nation="GB", online=False,
    )


class TestPlanetocentricPerspective:
    @pytest.mark.parametrize("perspective", [
        "Marscentric", "Jupitercentric", "Venuscentric",
    ])
    def test_creates_valid_chart(self, perspective):
        s = AstrologicalSubjectFactory.from_birth_data(
            f"{perspective} Test", 2000, 1, 1, 12, 0,
            lng=0.0, lat=51.5, tz_str="Etc/GMT",
            city="Greenwich", nation="GB", online=False,
            perspective_type=perspective,
        )
        assert s is not None
        assert s.perspective_type == perspective
        assert s.sun is not None
        assert 0 <= s.sun.abs_pos < 360

    def test_marscentric_chart_valid(self, geocentric):
        mars_view = AstrologicalSubjectFactory.from_birth_data(
            "From Mars", 2000, 1, 1, 12, 0,
            lng=0.0, lat=51.5, tz_str="Etc/GMT",
            city="Greenwich", nation="GB", online=False,
            perspective_type="Marscentric",
        )
        # Chart should be valid (may fallback to geocentric if sepl file unavailable)
        assert mars_view.sun is not None
        assert 0 <= mars_view.sun.abs_pos < 360
        assert mars_view.perspective_type == "Marscentric"

    def test_jupitercentric_sun_position(self):
        s = AstrologicalSubjectFactory.from_birth_data(
            "From Jupiter", 2000, 1, 1, 12, 0,
            lng=0.0, lat=51.5, tz_str="Etc/GMT",
            city="Greenwich", nation="GB", online=False,
            perspective_type="Jupitercentric",
        )
        assert s.sun is not None
        # Sun should still have a valid position
        assert 0 <= s.sun.abs_pos < 360
        assert s.moon is not None

    def test_selenocentric(self):
        """View from the Moon."""
        s = AstrologicalSubjectFactory.from_birth_data(
            "From Moon", 2000, 1, 1, 12, 0,
            lng=0.0, lat=51.5, tz_str="Etc/GMT",
            city="Greenwich", nation="GB", online=False,
            perspective_type="Selenocentric",
        )
        assert s.sun is not None
        assert s.mars is not None
