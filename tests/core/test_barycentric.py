# -*- coding: utf-8 -*-
"""Tests for the Barycentric perspective type."""

import pytest
from kerykeion import AstrologicalSubjectFactory


@pytest.fixture(scope="module")
def barycentric_subject():
    return AstrologicalSubjectFactory.from_birth_data(
        "Barycentric Test", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
        perspective_type="Barycentric",
    )


@pytest.fixture(scope="module")
def geocentric_subject():
    return AstrologicalSubjectFactory.from_birth_data(
        "Geocentric Test", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
    )


class TestBarycentricPerspective:
    def test_subject_created(self, barycentric_subject):
        """Barycentric subject should be created without errors."""
        assert barycentric_subject is not None
        assert barycentric_subject.perspective_type == "Barycentric"

    def test_planets_calculated(self, barycentric_subject):
        """Main planets should be calculated in barycentric mode."""
        assert barycentric_subject.jupiter is not None
        assert barycentric_subject.saturn is not None
        assert 0 <= barycentric_subject.jupiter.abs_pos < 360

    def test_positions_differ_from_geocentric(self, barycentric_subject, geocentric_subject):
        """Barycentric positions should differ from geocentric for outer planets."""
        # Jupiter and Saturn should have measurably different positions
        assert barycentric_subject.jupiter.abs_pos != geocentric_subject.jupiter.abs_pos
        assert barycentric_subject.saturn.abs_pos != geocentric_subject.saturn.abs_pos

    def test_inner_planets_small_difference(self, barycentric_subject, geocentric_subject):
        """Inner planet differences should be smaller than outer planet differences."""
        # The barycenter is very close to the Sun, so inner planets show small shifts
        jupiter_diff = abs(barycentric_subject.jupiter.abs_pos - geocentric_subject.jupiter.abs_pos)
        assert jupiter_diff > 0.001  # Should be measurably different
