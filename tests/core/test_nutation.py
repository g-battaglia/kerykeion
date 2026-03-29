# -*- coding: utf-8 -*-
"""Tests for the Nutation/Obliquity model."""

import pytest
swe = pytest.importorskip("swisseph")
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


class TestNutationSwissEphRegression:
    """Known-value regression tests using Swiss Ephemeris (swe) as the reference.

    At J2000.0 (JD 2451545.0 = 2000-01-01 12:00 UTC), swe.calc_ut with
    ECL_NUT returns well-known nutation/obliquity values that serve as a
    stable reference for regression testing.
    """

    # Reference values from swe.calc_ut(2451545.0, swe.ECL_NUT, swe.FLG_SWIEPH)
    J2000_JD = 2451545.0
    SWE_TRUE_OBLIQUITY = 23.4376767161
    SWE_MEAN_OBLIQUITY = 23.4392794439
    SWE_NUT_LONGITUDE = -0.0038698677
    SWE_NUT_OBLIQUITY = -0.0016027278

    @classmethod
    def setup_class(cls):
        swe.set_ephe_path("")

    def test_swe_ecl_nut_j2000_true_obliquity(self):
        """True obliquity at J2000.0 should be ~23.4377 deg per swe."""
        nut = swe.calc_ut(self.J2000_JD, swe.ECL_NUT, swe.FLG_SWIEPH)[0]
        assert abs(nut[0] - self.SWE_TRUE_OBLIQUITY) < 1e-6

    def test_swe_ecl_nut_j2000_mean_obliquity(self):
        """Mean obliquity at J2000.0 should be ~23.4393 deg per swe."""
        nut = swe.calc_ut(self.J2000_JD, swe.ECL_NUT, swe.FLG_SWIEPH)[0]
        assert abs(nut[1] - self.SWE_MEAN_OBLIQUITY) < 1e-6

    def test_swe_ecl_nut_j2000_nutation_longitude(self):
        """Nutation in longitude at J2000.0 should be ~-0.00387 deg per swe."""
        nut = swe.calc_ut(self.J2000_JD, swe.ECL_NUT, swe.FLG_SWIEPH)[0]
        assert abs(nut[2] - self.SWE_NUT_LONGITUDE) < 1e-6

    def test_swe_ecl_nut_j2000_nutation_obliquity(self):
        """Nutation in obliquity at J2000.0 should be ~-0.00160 deg per swe."""
        nut = swe.calc_ut(self.J2000_JD, swe.ECL_NUT, swe.FLG_SWIEPH)[0]
        assert abs(nut[3] - self.SWE_NUT_OBLIQUITY) < 1e-6

    def test_subject_nutation_matches_swe_at_j2000(self):
        """AstrologicalSubjectFactory nutation at J2000.0 must match swe reference.

        Creates a subject for 2000-01-01 12:00 UTC (JD 2451545.0) and verifies
        its nutation model fields against the swe.calc_ut ECL_NUT output.
        """
        subject = AstrologicalSubjectFactory.from_birth_data(
            "J2000 Nutation Regression", 2000, 1, 1, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            city="Greenwich", nation="GB", online=False,
            calculate_nutation=True,
        )

        assert subject.nutation is not None, "Nutation should be populated"
        assert abs(subject.julian_day - self.J2000_JD) < 1e-4, (
            f"JD mismatch: {subject.julian_day} vs {self.J2000_JD}"
        )

        # Compare each field against the swe reference with tight tolerance
        assert abs(subject.nutation.true_obliquity - self.SWE_TRUE_OBLIQUITY) < 1e-4, (
            f"true_obliquity: {subject.nutation.true_obliquity} vs {self.SWE_TRUE_OBLIQUITY}"
        )
        assert abs(subject.nutation.mean_obliquity - self.SWE_MEAN_OBLIQUITY) < 1e-4, (
            f"mean_obliquity: {subject.nutation.mean_obliquity} vs {self.SWE_MEAN_OBLIQUITY}"
        )
        assert abs(subject.nutation.nutation_longitude - self.SWE_NUT_LONGITUDE) < 1e-6, (
            f"nutation_longitude: {subject.nutation.nutation_longitude} vs {self.SWE_NUT_LONGITUDE}"
        )
        assert abs(subject.nutation.nutation_obliquity - self.SWE_NUT_OBLIQUITY) < 1e-6, (
            f"nutation_obliquity: {subject.nutation.nutation_obliquity} vs {self.SWE_NUT_OBLIQUITY}"
        )
