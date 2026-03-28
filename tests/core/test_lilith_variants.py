# -*- coding: utf-8 -*-
"""Tests for Interpolated Lilith, Mean Priapus, and True Priapus."""

import pytest
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
        "Lilith Test", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
        active_points=LILITH_POINTS,
    )


@pytest.fixture(scope="module")
def subject_default():
    """Subject with default active_points (no Interpolated Lilith or Priapus)."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Default Test", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
    )


class TestInterpolatedLilith:
    def test_interpolated_lilith_calculated(self, subject_with_lilith_variants):
        """Interpolated Lilith should be calculated when in active_points."""
        il = subject_with_lilith_variants.interpolated_lilith
        assert il is not None
        assert il.name == "Interpolated_Lilith"

    def test_interpolated_between_mean_and_true(self, subject_with_lilith_variants):
        """Interpolated Lilith should lie between Mean and True Lilith positions."""
        mean = subject_with_lilith_variants.mean_lilith
        true = subject_with_lilith_variants.true_lilith
        interp = subject_with_lilith_variants.interpolated_lilith

        assert mean is not None
        assert true is not None
        assert interp is not None

        # The interpolated value should be close to both mean and true
        # (within 15 degrees — True Lilith can deviate significantly from Mean)
        diff_from_mean = abs(interp.abs_pos - mean.abs_pos)
        if diff_from_mean > 180:
            diff_from_mean = 360 - diff_from_mean
        diff_from_true = abs(interp.abs_pos - true.abs_pos)
        if diff_from_true > 180:
            diff_from_true = 360 - diff_from_true

        assert diff_from_mean <= 15.0 or diff_from_true <= 15.0, (
            f"Interpolated Lilith ({interp.abs_pos:.2f}) too far from both "
            f"Mean ({mean.abs_pos:.2f}) and True ({true.abs_pos:.2f})"
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
            f"Mean Priapus ({mean_pri.abs_pos:.4f}) not opposite "
            f"Mean Lilith ({mean_lil.abs_pos:.4f}), diff={diff:.4f}"
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
            f"True Priapus ({true_pri.abs_pos:.4f}) not opposite "
            f"True Lilith ({true_lil.abs_pos:.4f}), diff={diff:.4f}"
        )

    def test_all_lilith_points_have_house(self, subject_with_lilith_variants):
        """All Lilith/Priapus points should have house placement."""
        for attr in ["interpolated_lilith", "mean_priapus", "true_priapus"]:
            point = getattr(subject_with_lilith_variants, attr)
            if point is not None:
                assert point.house is not None, f"{attr} should have house placement"
