# -*- coding: utf-8 -*-
"""Tests for the Vedic Nakshatra module.

Validates the 27 Nakshatra divisions, pada calculations, and
Vimsottari Dasha lord assignments.
"""

import pytest
swe = pytest.importorskip("swisseph")
from kerykeion import AstrologicalSubjectFactory
from kerykeion.vedic.nakshatra_utils import calculate_nakshatra
from kerykeion.vedic.nakshatra_data import NAKSHATRAS, NAKSHATRA_SPAN, PADA_SPAN


class TestNakshatraData:
    """Test completeness of nakshatra reference data."""

    def test_27_nakshatras(self):
        assert len(NAKSHATRAS) == 27

    def test_nakshatra_span(self):
        assert abs(NAKSHATRA_SPAN - 13.333333333) < 0.001

    def test_pada_span(self):
        assert abs(PADA_SPAN - 3.333333333) < 0.001

    def test_full_circle_coverage(self):
        assert abs(27 * NAKSHATRA_SPAN - 360.0) < 1e-10


class TestNakshatraCalculation:
    """Test nakshatra position calculations."""

    def test_first_nakshatra_ashwini(self):
        """0° sidereal Aries = Ashwini, pada 1."""
        result = calculate_nakshatra(0.0)
        assert result["nakshatra"] == "Ashwini"
        assert result["nakshatra_number"] == 1
        assert result["nakshatra_pada"] == 1
        assert result["nakshatra_lord"] == "Ketu"

    def test_ashwini_pada_2(self):
        """3.34° = Ashwini, pada 2."""
        result = calculate_nakshatra(3.34)
        assert result["nakshatra"] == "Ashwini"
        assert result["nakshatra_pada"] == 2

    def test_bharani(self):
        """14° = Bharani (2nd nakshatra)."""
        result = calculate_nakshatra(14.0)
        assert result["nakshatra"] == "Bharani"
        assert result["nakshatra_number"] == 2
        assert result["nakshatra_lord"] == "Venus"

    def test_rohini(self):
        """~46° = Rohini (4th nakshatra)."""
        result = calculate_nakshatra(46.0)
        assert result["nakshatra"] == "Rohini"
        assert result["nakshatra_number"] == 4
        assert result["nakshatra_lord"] == "Moon"

    def test_last_nakshatra_revati(self):
        """~355° = Revati (27th nakshatra)."""
        result = calculate_nakshatra(355.0)
        assert result["nakshatra"] == "Revati"
        assert result["nakshatra_number"] == 27
        assert result["nakshatra_lord"] == "Mercury"

    def test_boundary_13_degrees(self):
        """At 13.33°, should be at start of Bharani."""
        result = calculate_nakshatra(13.34)
        assert result["nakshatra"] == "Bharani"
        assert result["nakshatra_number"] == 2

    def test_pada_boundaries(self):
        """Test all 4 padas within a nakshatra."""
        # Ashwini: 0-13.333
        assert calculate_nakshatra(1.0)["nakshatra_pada"] == 1
        assert calculate_nakshatra(4.0)["nakshatra_pada"] == 2
        assert calculate_nakshatra(7.5)["nakshatra_pada"] == 3
        assert calculate_nakshatra(11.0)["nakshatra_pada"] == 4

    def test_dasha_lord_sequence(self):
        """Verify the Vimsottari Dasha lord sequence repeats correctly."""
        expected_lords = [
            "Ketu", "Venus", "Sun", "Moon", "Mars",
            "Rahu", "Jupiter", "Saturn", "Mercury",
        ]
        for i in range(27):
            pos = i * NAKSHATRA_SPAN + 1.0
            result = calculate_nakshatra(pos)
            expected = expected_lords[i % 9]
            assert result["nakshatra_lord"] == expected, (
                f"Nakshatra {i+1} ({result['nakshatra']}): "
                f"expected lord {expected}, got {result['nakshatra_lord']}"
            )

    def test_wraparound_at_360(self):
        """360° should wrap to Ashwini."""
        result = calculate_nakshatra(360.0)
        assert result["nakshatra"] == "Ashwini"
        assert result["nakshatra_number"] == 1

    def test_just_below_360(self):
        """359.999° should be Revati with clamped pada <= 4."""
        result = calculate_nakshatra(359.999)
        assert result["nakshatra"] == "Revati"
        assert result["nakshatra_number"] == 27
        assert 1 <= result["nakshatra_pada"] <= 4

    def test_nakshatra_index_ge_27_guard(self):
        """Exercise the nakshatra_index >= 27 guard (line 39).

        This guard protects against floating-point edge cases where
        int(pos / NAKSHATRA_SPAN) could be 27. We mock NAKSHATRA_SPAN
        to trigger it.
        """
        from unittest.mock import patch
        # With a slightly smaller NAKSHATRA_SPAN, int(359.0 / 13.0) = 27
        with patch("kerykeion.vedic.nakshatra_utils.NAKSHATRA_SPAN", 13.0):
            # 27 * 13 = 351, so pos_in_nakshatra = 359 - 351 = 8
            # Pada span is still 3.333..., pada = int(8/3.333)+1 = 3
            result = calculate_nakshatra(359.0)
            assert result["nakshatra_number"] == 27  # clamped to 26+1
            assert result["nakshatra"] == "Revati"

    def test_pada_gt_4_guard(self):
        """Exercise the pada > 4 guard (line 47).

        This guard protects against floating-point edge cases where
        int(pos_in_nakshatra / PADA_SPAN) + 1 could exceed 4.
        """
        from unittest.mock import patch
        # With a smaller PADA_SPAN, int(12.5 / 2.5) + 1 = 6 > 4
        with patch("kerykeion.vedic.nakshatra_utils.PADA_SPAN", 2.5):
            result = calculate_nakshatra(12.5)
            assert result["nakshatra_pada"] == 4  # clamped


class TestNakshatraIntegration:
    """Test nakshatra integrated in AstrologicalSubjectFactory."""

    @pytest.fixture(scope="class")
    def subject_with_nakshatra(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "Nakshatra Test", 1990, 1, 1, 12, 0,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
            calculate_nakshatra=True,
        )

    @pytest.fixture(scope="class")
    def subject_without_nakshatra(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "No Nakshatra", 1990, 1, 1, 12, 0,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
        )

    def test_nakshatra_populated(self, subject_with_nakshatra):
        sun = subject_with_nakshatra.sun
        assert sun.nakshatra is not None
        assert sun.nakshatra_number is not None
        assert 1 <= sun.nakshatra_number <= 27
        assert sun.nakshatra_pada is not None
        assert 1 <= sun.nakshatra_pada <= 4
        assert sun.nakshatra_lord is not None

    def test_nakshatra_not_populated_by_default(self, subject_without_nakshatra):
        sun = subject_without_nakshatra.sun
        assert sun.nakshatra is None
        assert sun.nakshatra_number is None

    def test_all_planets_have_nakshatra(self, subject_with_nakshatra):
        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(subject_with_nakshatra, name)
            if point is not None:
                assert point.nakshatra is not None, f"{name} should have nakshatra"
                assert point.nakshatra_lord is not None, f"{name} should have nakshatra_lord"

    def test_moon_nakshatra_valid(self, subject_with_nakshatra):
        """Moon's nakshatra is the most important in Vedic astrology."""
        moon = subject_with_nakshatra.moon
        nakshatra_names = [n[0] for n in NAKSHATRAS]
        assert moon.nakshatra in nakshatra_names


class TestNakshatraSwissEphRegression:
    """Known-value regression tests using Swiss Ephemeris sidereal positions.

    For each test date, the Moon's sidereal longitude is computed via
    swe.calc_ut with FLG_SIDEREAL + LAHIRI ayanamsa.  The expected nakshatra
    number is derived manually as int(sidereal_pos / (360/27)) + 1.
    Then calculate_nakshatra is called and the results must match.
    """

    @classmethod
    def setup_class(cls):
        swe.set_ephe_path("")

    # (year, month, day, hour, label, expected_nakshatra_name, expected_number)
    # Values pre-computed with swe.calc_ut + LAHIRI
    TEST_DATES = [
        (2000, 1, 1, 12.0, "J2000.0",
         199.470553, "Swati", 15, 4, "Rahu"),
        (2000, 6, 15, 12.0, "mid-2000",
         225.045266, "Anuradha", 17, 4, "Saturn"),
        (2010, 3, 21, 12.0, "2010-equinox",
         42.318238, "Rohini", 4, 1, "Moon"),
    ]

    @pytest.mark.parametrize(
        "year,month,day,hour,label,expected_sid_pos,exp_name,exp_num,exp_pada,exp_lord",
        TEST_DATES,
        ids=[t[4] for t in TEST_DATES],
    )
    def test_moon_nakshatra_matches_swe_sidereal(
        self, year, month, day, hour, label,
        expected_sid_pos, exp_name, exp_num, exp_pada, exp_lord,
    ):
        """Verify nakshatra from swe sidereal Moon position matches calculate_nakshatra."""
        jd = swe.julday(year, month, day, hour)

        # Compute sidereal Moon longitude using LAHIRI ayanamsa
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        moon_sid = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        sid_pos = moon_sid[0][0]

        # Verify swe gives the expected sidereal position (within 0.01 deg)
        assert abs(sid_pos - expected_sid_pos) < 0.01, (
            f"[{label}] swe sidereal Moon = {sid_pos:.6f}, expected ~{expected_sid_pos:.6f}"
        )

        # Manually compute expected nakshatra index
        manual_index = int(sid_pos / (360.0 / 27.0))
        manual_number = manual_index + 1
        assert manual_number == exp_num, (
            f"[{label}] manual nakshatra number = {manual_number}, expected {exp_num}"
        )

        # Use kerykeion's calculate_nakshatra and verify all fields
        result = calculate_nakshatra(sid_pos)
        assert result["nakshatra"] == exp_name, (
            f"[{label}] nakshatra name = {result['nakshatra']}, expected {exp_name}"
        )
        assert result["nakshatra_number"] == exp_num, (
            f"[{label}] nakshatra number = {result['nakshatra_number']}, expected {exp_num}"
        )
        assert result["nakshatra_pada"] == exp_pada, (
            f"[{label}] pada = {result['nakshatra_pada']}, expected {exp_pada}"
        )
        assert result["nakshatra_lord"] == exp_lord, (
            f"[{label}] lord = {result['nakshatra_lord']}, expected {exp_lord}"
        )
