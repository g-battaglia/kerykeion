# -*- coding: utf-8 -*-
"""Tests for Interpolated Lilith, Mean Priapus, and True Priapus."""

import math
import pytest
from kerykeion.ephemeris_backend import swe
from kerykeion import AstrologicalSubjectFactory
from kerykeion.schemas.kr_literals import AstrologicalPoint
from typing import List


LILITH_POINTS: List[AstrologicalPoint] = [
    "Mean_Lilith",
    "True_Lilith",
    "Interpolated_Lilith",
    "Mean_Priapus",
    "True_Priapus",
]


@pytest.fixture(scope="module")
def subject_with_lilith_variants():
    """Subject with all Lilith and Priapus points active."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Lilith Test",
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
        active_points=LILITH_POINTS,
    )


@pytest.fixture(scope="module")
def subject_default():
    """Subject with default active_points (no Interpolated Lilith or Priapus)."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Default Test",
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


class TestInterpolatedLilith:
    def test_interpolated_lilith_calculated(self, subject_with_lilith_variants):
        """Interpolated Lilith should be calculated when in active_points."""
        il = subject_with_lilith_variants.interpolated_lilith
        assert il is not None
        assert il.name == "Interpolated_Lilith"

    def test_interpolated_lilith_near_lunar_apogee(self, subject_with_lilith_variants):
        """Interpolated Lilith (SE_INTP_APOG) should be in the lunar apogee region.

        Since v6.0, Interpolated Lilith uses the Swiss Ephemeris interpolated
        apogee (body ID 21, ELP2000-82B perturbation series) instead of the
        previous naive circular_mean(Mean, True) formula.  It measures the same
        physical point as Mean/True Lilith (lunar apogee) so it should remain
        within ~30 degrees of Mean Lilith, but it is NOT constrained to lie
        between Mean and True.
        """
        mean = subject_with_lilith_variants.mean_lilith
        interp = subject_with_lilith_variants.interpolated_lilith

        assert mean is not None
        assert interp is not None

        diff = abs(interp.abs_pos - mean.abs_pos)
        if diff > 180:
            diff = 360 - diff

        assert diff <= 30.0, (
            f"Interpolated Lilith ({interp.abs_pos:.2f}) too far from Mean Lilith ({mean.abs_pos:.2f}), diff={diff:.2f}"
        )

    def test_interpolated_not_default(self, subject_default):
        """Interpolated Lilith should be None when not in active_points."""
        assert subject_default.interpolated_lilith is None

    def test_interpolated_has_sign(self, subject_with_lilith_variants):
        """Interpolated Lilith should have zodiac sign data."""
        il = subject_with_lilith_variants.interpolated_lilith
        assert il.sign is not None
        assert 0 <= il.position <= 30


class TestMeanPriapus:
    def test_mean_priapus_calculated(self, subject_with_lilith_variants):
        """Mean Priapus should be calculated when in active_points."""
        mp = subject_with_lilith_variants.mean_priapus
        assert mp is not None
        assert mp.name == "Mean_Priapus"

    def test_mean_priapus_opposite_mean_lilith(self, subject_with_lilith_variants):
        """Mean Priapus should be exactly 180 degrees from Mean Lilith."""
        mean_lil = subject_with_lilith_variants.mean_lilith
        mean_pri = subject_with_lilith_variants.mean_priapus

        assert mean_lil is not None
        assert mean_pri is not None

        diff = abs(mean_pri.abs_pos - mean_lil.abs_pos)
        if diff > 180:
            diff = 360 - diff
        assert abs(diff - 180) < 0.01, (
            f"Mean Priapus ({mean_pri.abs_pos:.4f}) not opposite Mean Lilith ({mean_lil.abs_pos:.4f}), diff={diff:.4f}"
        )

    def test_mean_priapus_not_default(self, subject_default):
        """Mean Priapus should be None when not in active_points."""
        assert subject_default.mean_priapus is None


class TestTruePriapus:
    def test_true_priapus_calculated(self, subject_with_lilith_variants):
        """True Priapus should be calculated when in active_points."""
        tp = subject_with_lilith_variants.true_priapus
        assert tp is not None
        assert tp.name == "True_Priapus"

    def test_true_priapus_opposite_true_lilith(self, subject_with_lilith_variants):
        """True Priapus should be exactly 180 degrees from True Lilith."""
        true_lil = subject_with_lilith_variants.true_lilith
        true_pri = subject_with_lilith_variants.true_priapus

        assert true_lil is not None
        assert true_pri is not None

        diff = abs(true_pri.abs_pos - true_lil.abs_pos)
        if diff > 180:
            diff = 360 - diff
        assert abs(diff - 180) < 0.01, (
            f"True Priapus ({true_pri.abs_pos:.4f}) not opposite True Lilith ({true_lil.abs_pos:.4f}), diff={diff:.4f}"
        )

    def test_all_lilith_points_have_house(self, subject_with_lilith_variants):
        """All Lilith/Priapus points should have house placement."""
        for attr in ["interpolated_lilith", "mean_priapus", "true_priapus"]:
            point = getattr(subject_with_lilith_variants, attr)
            if point is not None:
                assert point.house is not None, f"{attr} should have house placement"


class TestLilithSweReference:
    """Regression tests comparing Lilith/Priapus positions against direct swe calls."""

    def test_mean_lilith_matches_swe_reference(self, subject_with_lilith_variants):
        """Mean Lilith abs_pos must match swe.calc_ut for SE_MEAN_APOG (ID 12) within 0.001 deg."""
        jd = subject_with_lilith_variants.julian_day
        swe.set_ephe_path("")
        mean_lil_calc = swe.calc_ut(jd, 12, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
        expected_lon = mean_lil_calc[0]
        actual_lon = subject_with_lilith_variants.mean_lilith.abs_pos
        assert abs(actual_lon - expected_lon) < 0.001, (
            f"Mean Lilith abs_pos {actual_lon} != swe reference {expected_lon}"
        )

    def test_true_lilith_matches_swe_reference(self, subject_with_lilith_variants):
        """True Lilith abs_pos must match swe.calc_ut for SE_OSCU_APOG (ID 13) within 0.001 deg."""
        jd = subject_with_lilith_variants.julian_day
        swe.set_ephe_path("")
        true_lil_calc = swe.calc_ut(jd, 13, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
        expected_lon = true_lil_calc[0]
        actual_lon = subject_with_lilith_variants.true_lilith.abs_pos
        assert abs(actual_lon - expected_lon) < 0.001, (
            f"True Lilith abs_pos {actual_lon} != swe reference {expected_lon}"
        )

    def test_mean_priapus_opposite_swe_mean_lilith(self, subject_with_lilith_variants):
        """Mean Priapus must be Mean Lilith + 180 deg (mod 360), verified against swe."""
        jd = subject_with_lilith_variants.julian_day
        swe.set_ephe_path("")
        mean_lil_lon = swe.calc_ut(jd, 12, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
        expected_priapus = math.fmod(mean_lil_lon + 180, 360)
        actual_priapus = subject_with_lilith_variants.mean_priapus.abs_pos
        diff = abs(actual_priapus - expected_priapus)
        if diff > 180:
            diff = 360 - diff
        assert diff < 0.001, f"Mean Priapus {actual_priapus} != swe Mean Lilith+180 ({expected_priapus})"

    def test_true_priapus_opposite_swe_true_lilith(self, subject_with_lilith_variants):
        """True Priapus must be True Lilith + 180 deg (mod 360), verified against swe."""
        jd = subject_with_lilith_variants.julian_day
        swe.set_ephe_path("")
        true_lil_lon = swe.calc_ut(jd, 13, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
        expected_priapus = math.fmod(true_lil_lon + 180, 360)
        actual_priapus = subject_with_lilith_variants.true_priapus.abs_pos
        diff = abs(actual_priapus - expected_priapus)
        if diff > 180:
            diff = 360 - diff
        assert diff < 0.001, f"True Priapus {actual_priapus} != swe True Lilith+180 ({expected_priapus})"
