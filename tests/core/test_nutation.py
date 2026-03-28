# -*- coding: utf-8 -*-
"""Tests for the Nutation/Obliquity model."""

import pytest
from kerykeion import AstrologicalSubjectFactory


@pytest.fixture(scope="module")
def subject_with_nutation():
    return AstrologicalSubjectFactory.from_birth_data(
        "Nutation Test", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
        calculate_nutation=True,
    )


@pytest.fixture(scope="module")
def subject_without_nutation():
    return AstrologicalSubjectFactory.from_birth_data(
        "No Nutation", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
    )


class TestNutationModel:
    def test_nutation_populated(self, subject_with_nutation):
        """Nutation model should be populated when enabled."""
        assert subject_with_nutation.nutation is not None

    def test_nutation_not_populated_by_default(self, subject_without_nutation):
        """Nutation should be None when not enabled."""
        assert subject_without_nutation.nutation is None

    def test_true_obliquity_range(self, subject_with_nutation):
        """True obliquity should be approximately 23.44 degrees for modern epochs."""
        obl = subject_with_nutation.nutation.true_obliquity
        assert 22.0 < obl < 24.0, f"True obliquity {obl} outside expected range"

    def test_mean_obliquity_range(self, subject_with_nutation):
        """Mean obliquity should be close to true obliquity."""
        mean = subject_with_nutation.nutation.mean_obliquity
        true = subject_with_nutation.nutation.true_obliquity
        assert 22.0 < mean < 24.0
        # Mean and true should differ by less than 0.01 degrees (nutation amplitude)
        assert abs(mean - true) < 0.01

    def test_nutation_longitude_small(self, subject_with_nutation):
        """Nutation in longitude should be a small value (typically < 0.01 degrees)."""
        nut_lon = subject_with_nutation.nutation.nutation_longitude
        assert abs(nut_lon) < 0.01, f"Nutation in longitude {nut_lon} seems too large"

    def test_nutation_obliquity_small(self, subject_with_nutation):
        """Nutation in obliquity should be a small value."""
        nut_obl = subject_with_nutation.nutation.nutation_obliquity
        assert abs(nut_obl) < 0.01, f"Nutation in obliquity {nut_obl} seems too large"

    def test_all_fields_are_float(self, subject_with_nutation):
        """All nutation fields should be floats."""
        nut = subject_with_nutation.nutation
        assert isinstance(nut.true_obliquity, float)
        assert isinstance(nut.mean_obliquity, float)
        assert isinstance(nut.nutation_longitude, float)
        assert isinstance(nut.nutation_obliquity, float)
