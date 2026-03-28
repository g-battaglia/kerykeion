# -*- coding: utf-8 -*-
"""Tests for the Primary Directions factory (v6.0)."""

import math
import pytest
import swisseph as swe
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory, PrimaryDirectionsFactory


@pytest.fixture(scope="module")
def subject():
    return AstrologicalSubjectFactory.from_birth_data(
        "Primary Dir Test", 1940, 10, 9, 18, 30,
        lng=-2.9916, lat=53.4084, tz_str="Europe/London",
        city="Liverpool", nation="GB", online=False,
    )


class TestSpeculum:
    def test_speculum_returns_entries(self, subject):
        """Speculum should return entries for direction points."""
        speculum = PrimaryDirectionsFactory.compute_speculum(subject)
        assert isinstance(speculum, list)
        assert len(speculum) > 0

    def test_speculum_has_planets(self, subject):
        """Speculum should include Sun, Moon, and angular points."""
        speculum = PrimaryDirectionsFactory.compute_speculum(subject)
        names = [s.name for s in speculum]
        assert "Sun" in names
        assert "Moon" in names
        assert "Ascendant" in names
        assert "Medium_Coeli" in names

    def test_speculum_ra_range(self, subject):
        """Right Ascension should be 0-360."""
        speculum = PrimaryDirectionsFactory.compute_speculum(subject)
        for entry in speculum:
            assert 0 <= entry.right_ascension < 360, (
                f"{entry.name} RA {entry.right_ascension} out of range"
            )

    def test_speculum_declination_range(self, subject):
        """Declination should be -90 to +90."""
        speculum = PrimaryDirectionsFactory.compute_speculum(subject)
        for entry in speculum:
            assert -90 <= entry.declination <= 90, (
                f"{entry.name} dec {entry.declination} out of range"
            )

    def test_speculum_semi_arc_positive(self, subject):
        """Semi-arcs should be positive."""
        speculum = PrimaryDirectionsFactory.compute_speculum(subject)
        for entry in speculum:
            assert entry.semi_arc > 0, (
                f"{entry.name} semi_arc {entry.semi_arc} should be positive"
            )


class TestPrimaryDirections:
    def test_directions_computed(self, subject):
        """Should compute primary directions."""
        directions = PrimaryDirectionsFactory.compute(subject, max_years=80)
        assert isinstance(directions, list)
        assert len(directions) > 0

    def test_directions_sorted_by_year(self, subject):
        """Directions should be sorted by direction_years."""
        directions = PrimaryDirectionsFactory.compute(subject, max_years=80)
        years = [d.direction_years for d in directions]
        assert years == sorted(years)

    def test_directions_within_max_years(self, subject):
        """All directions should be within max_years."""
        max_yrs = 50
        directions = PrimaryDirectionsFactory.compute(subject, max_years=max_yrs)
        for d in directions:
            assert 0 < d.direction_years <= max_yrs

    def test_directions_have_valid_aspects(self, subject):
        """All directions should have valid aspect names."""
        valid_aspects = {"conjunction", "sextile", "square", "trine", "opposition"}
        directions = PrimaryDirectionsFactory.compute(subject, max_years=80)
        for d in directions:
            assert d.aspect in valid_aspects, f"Invalid aspect: {d.aspect}"

    def test_directions_arc_positive(self, subject):
        """Direction arcs should be positive."""
        directions = PrimaryDirectionsFactory.compute(subject, max_years=80)
        for d in directions:
            assert d.arc > 0

    def test_ptolemy_rate_key(self, subject):
        """Ptolemy rate key: 1 degree = 1 year."""
        directions = PrimaryDirectionsFactory.compute(subject, max_years=80, rate_key="ptolemy")
        for d in directions:
            assert d.rate_key == "ptolemy"
            assert abs(d.direction_years - d.arc) < 0.01  # 1:1 ratio

    def test_naibod_rate_key(self, subject):
        """Naibod rate key: 0.98564 degrees = 1 year."""
        directions = PrimaryDirectionsFactory.compute(subject, max_years=80, rate_key="naibod")
        for d in directions:
            assert d.rate_key == "naibod"
            # Naibod years should be slightly more than Ptolemy for same arc
            expected_years = d.arc / 0.98564
            assert abs(d.direction_years - expected_years) < 0.1

    def test_filter_aspects(self, subject):
        """Should respect aspects filter."""
        conj_only = PrimaryDirectionsFactory.compute(
            subject, max_years=80, aspects=["conjunction"]
        )
        all_aspects = PrimaryDirectionsFactory.compute(subject, max_years=80)
        assert len(conj_only) <= len(all_aspects)
        for d in conj_only:
            assert d.aspect == "conjunction"


class TestSpeculumSweRegressions:
    """Known-value regression tests using Swiss Ephemeris as reference source.

    These tests call swe functions directly to obtain reference values, then
    verify that PrimaryDirectionsFactory.compute_speculum produces matching
    results.  The subject is John Lennon (1940-10-09 18:30, Liverpool).
    """

    @pytest.fixture(scope="class")
    def lennon(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "John Lennon", 1940, 10, 9, 18, 30,
            lng=-2.9916, lat=53.4084, tz_str="Europe/London",
            city="Liverpool", nation="GB", online=False,
        )

    def test_sun_ra_dec_matches_swe(self, lennon):
        """Sun RA and declination from speculum must match swe.calc_ut equatorial coords."""
        ephe_path = str(Path(__file__).resolve().parent.parent.parent / "kerykeion" / "sweph")
        swe.set_ephe_path(ephe_path)

        jd = lennon.julian_day
        eq = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
        swe_ra = eq[0][0]
        swe_dec = eq[0][1]
        swe.close()

        speculum = PrimaryDirectionsFactory.compute_speculum(lennon)
        sun_entry = next(e for e in speculum if e.name == "Sun")

        assert abs(sun_entry.right_ascension - swe_ra) < 0.01, (
            f"Sun RA mismatch: speculum={sun_entry.right_ascension}, swe={swe_ra}"
        )
        assert abs(sun_entry.declination - swe_dec) < 0.01, (
            f"Sun Dec mismatch: speculum={sun_entry.declination}, swe={swe_dec}"
        )

    def test_ramc_matches_swe_sidtime(self, lennon):
        """RAMC must equal (swe.sidtime(jd) * 15 + lng) mod 360."""
        ephe_path = str(Path(__file__).resolve().parent.parent.parent / "kerykeion" / "sweph")
        swe.set_ephe_path(ephe_path)

        jd = lennon.julian_day
        expected_ramc = (swe.sidtime(jd) * 15.0 + lennon.lng) % 360
        swe.close()

        # The speculum does not directly expose RAMC, but we can verify it
        # through the MC entry: MC's meridian distance should be ~0 because
        # it sits on the meridian.  Also verify via re-derivation:
        # For any planet, MD = RA - RAMC (normalized).
        # So RAMC = RA - MD for any planet entry.
        speculum = PrimaryDirectionsFactory.compute_speculum(lennon)
        sun_entry = next(e for e in speculum if e.name == "Sun")
        derived_ramc = (sun_entry.right_ascension - sun_entry.meridian_distance) % 360

        assert abs(derived_ramc - expected_ramc) < 0.01, (
            f"RAMC mismatch: derived={derived_ramc}, expected={expected_ramc}"
        )
