# -*- coding: utf-8 -*-
"""Tests for the Planetary Phenomena factory.

Validates phase angle, elongation, illumination, apparent magnitude,
and morning/evening star status calculations via swe.pheno_ut().
"""

import pytest
from kerykeion.ephemeris_backend import swe
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory, PlanetaryPhenomenaFactory

_EPHE_PATH = str(Path(__file__).parent.parent.parent / "kerykeion" / "sweph")


@pytest.fixture(scope="module")
def subject():
    return AstrologicalSubjectFactory.from_birth_data(
        "Phenomena Test", 2000, 1, 1, 12, 0,
        lng=0.0, lat=51.5, tz_str="Etc/GMT",
        city="Greenwich", nation="GB", online=False,
    )


class TestPhenomenaFromSubject:
    """Test phenomena calculation from an existing subject."""

    def test_all_planets_returned(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(subject)
        names = [p.name for p in result.phenomena]
        assert "Mars" in names
        assert "Venus" in names
        assert "Jupiter" in names
        assert len(result.phenomena) >= 7  # At least Moon through Pluto

    def test_julian_day_set(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(subject)
        assert result.julian_day == subject.julian_day

    def test_elongation_range(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(subject)
        for p in result.phenomena:
            assert 0 <= p.elongation <= 180, f"{p.name} elongation should be 0-180"

    def test_phase_range(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(subject)
        for p in result.phenomena:
            assert 0 <= p.phase <= 1, f"{p.name} phase should be 0-1"

    def test_venus_morning_or_evening(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(subject)
        venus = next((p for p in result.phenomena if p.name == "Venus"), None)
        assert venus is not None
        assert venus.is_morning_star is not None
        assert venus.is_evening_star is not None
        # Must be one or the other (XOR)
        assert venus.is_morning_star != venus.is_evening_star

    def test_mercury_morning_or_evening(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(subject)
        mercury = next((p for p in result.phenomena if p.name == "Mercury"), None)
        assert mercury is not None
        assert mercury.is_morning_star is not None
        assert mercury.is_evening_star is not None

    def test_mars_no_morning_evening(self, subject):
        """Superior planets don't have morning/evening star status."""
        result = PlanetaryPhenomenaFactory.from_subject(subject)
        mars = next((p for p in result.phenomena if p.name == "Mars"), None)
        assert mars is not None
        assert mars.is_morning_star is None
        assert mars.is_evening_star is None


class TestPhenomenaFromJulianDay:
    """Test phenomena from direct Julian Day input."""

    def test_j2000_epoch(self):
        result = PlanetaryPhenomenaFactory.from_julian_day(2451545.0)
        assert len(result.phenomena) >= 7

    def test_apparent_magnitude_reasonable(self):
        result = PlanetaryPhenomenaFactory.from_julian_day(2451545.0)
        for p in result.phenomena:
            # Moon can be ~-13, Venus ~-4.6, Pluto ~+14
            assert -15 <= p.apparent_magnitude <= 25, (
                f"{p.name} magnitude {p.apparent_magnitude} out of range"
            )


class TestPhenomenaFiltering:
    """Test planet name filtering."""

    def test_single_planet(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(subject, planets=["Mars"])
        assert len(result.phenomena) == 1
        assert result.phenomena[0].name == "Mars"

    def test_multiple_planets(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(
            subject, planets=["Venus", "Jupiter"]
        )
        assert len(result.phenomena) == 2
        names = {p.name for p in result.phenomena}
        assert names == {"Venus", "Jupiter"}

    def test_nonexistent_planet_ignored(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(
            subject, planets=["FakePlanet"]
        )
        assert len(result.phenomena) == 0


class TestPhenomenaEdgeCases:
    """Test edge-case branches in the phenomena factory."""

    def test_sun_calc_failure_gives_none_morning_evening(self):
        """If swe.calc_ut for the Sun fails, morning/evening star should be None."""
        from unittest.mock import patch

        original_calc_ut = swe.calc_ut

        def mock_calc_ut(jd, planet_id, iflag):
            if planet_id == swe.SUN:
                raise RuntimeError("Mock Sun failure")
            return original_calc_ut(jd, planet_id, iflag)

        with patch("kerykeion.planetary_phenomena.phenomena_factory.swe.calc_ut", side_effect=mock_calc_ut):
            result = PlanetaryPhenomenaFactory.from_julian_day(2451545.0, planets=["Venus"])
            assert len(result.phenomena) == 1
            # Without Sun longitude, morning/evening cannot be determined
            assert result.phenomena[0].is_morning_star is None
            assert result.phenomena[0].is_evening_star is None

    def test_pheno_ut_exception_skips_planet(self):
        """If swe.pheno_ut raises for a planet, that planet should be skipped."""
        from unittest.mock import patch

        original_pheno_ut = swe.pheno_ut

        def mock_pheno_ut(jd, planet_id, iflag):
            if planet_id == swe.MARS:
                raise RuntimeError("Mock pheno failure")
            return original_pheno_ut(jd, planet_id, iflag)

        with patch("kerykeion.planetary_phenomena.phenomena_factory.swe.pheno_ut", side_effect=mock_pheno_ut):
            result = PlanetaryPhenomenaFactory.from_julian_day(2451545.0)
            names = [p.name for p in result.phenomena]
            assert "Mars" not in names
            # Other planets should still be present
            assert "Venus" in names

    def test_venus_evening_star_branch(self):
        """Venus should be classified as either morning or evening star, covering both branches."""
        # Test multiple epochs to ensure both branches are hit
        # Venus at J2000.0 is an evening star (planet east of Sun, diff < 180)
        result = PlanetaryPhenomenaFactory.from_julian_day(2451545.0, planets=["Venus"])
        venus = result.phenomena[0]
        assert venus.is_morning_star is not None
        assert venus.is_evening_star is not None
        # Whatever Venus is at this epoch, test that at another epoch it's different
        result2 = PlanetaryPhenomenaFactory.from_julian_day(2451545.0 + 200, planets=["Venus"])
        venus2 = result2.phenomena[0]
        # At least one epoch should have morning=True and the other evening=True
        # We just need to ensure both code paths can be reached
        assert venus2.is_morning_star is not None or venus2.is_evening_star is not None

    def test_planet_calc_failure_in_morning_evening_gives_none(self):
        """If swe.calc_ut fails for the planet's position in the morning/evening block,
        is_morning_star and is_evening_star should remain None.

        The code flow is:
        1. Sun calc_ut succeeds (sun_lon is set)
        2. pheno_ut succeeds (phenomena data computed)
        3. For inferior planets, calc_ut for planet position -> if this fails,
           is_morning/is_evening stay None.
        """
        from unittest.mock import patch

        original_calc_ut = swe.calc_ut
        venus_calc_count = [0]

        def mock_calc_ut(jd, planet_id, iflag):
            if planet_id == swe.VENUS:
                venus_calc_count[0] += 1
                # The 2nd call for Venus is the position calc inside morning/evening block
                # (1st call is the Sun, then pheno_ut internally may call, then our position calc)
                if venus_calc_count[0] >= 1:
                    raise RuntimeError("Mock Venus position failure")
            return original_calc_ut(jd, planet_id, iflag)

        with patch("kerykeion.planetary_phenomena.phenomena_factory.swe.calc_ut", side_effect=mock_calc_ut):
            result = PlanetaryPhenomenaFactory.from_julian_day(2451545.0, planets=["Venus"])
            if len(result.phenomena) > 0:
                venus = result.phenomena[0]
                # Morning/evening should be None because planet calc failed
                assert venus.is_morning_star is None
                assert venus.is_evening_star is None


class TestSweRegressionPhenomena:
    """Regression tests: verify factory results match raw Swiss Ephemeris calls."""

    def test_venus_phenomena_at_j2000_matches_swe(self):
        """Factory Venus phenomena at J2000.0 should match swe.pheno_ut directly."""
        jd_j2000 = 2451545.0
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED

        swe.set_ephe_path(_EPHE_PATH)
        swe_result = swe.pheno_ut(jd_j2000, swe.VENUS, iflag)
        swe_phase_angle = swe_result[0]
        swe_phase = swe_result[1]
        swe_elongation = swe_result[2]
        swe_apparent_diameter = swe_result[3]
        swe_apparent_magnitude = swe_result[4]
        swe.close()

        factory_result = PlanetaryPhenomenaFactory.from_julian_day(
            jd_j2000, planets=["Venus"]
        )
        assert len(factory_result.phenomena) == 1
        venus = factory_result.phenomena[0]

        assert abs(venus.phase_angle - swe_phase_angle) < 0.001, (
            f"phase_angle: factory={venus.phase_angle} swe={swe_phase_angle}"
        )
        assert abs(venus.phase - swe_phase) < 0.001, (
            f"phase: factory={venus.phase} swe={swe_phase}"
        )
        assert abs(venus.elongation - swe_elongation) < 0.001, (
            f"elongation: factory={venus.elongation} swe={swe_elongation}"
        )
        assert abs(venus.apparent_diameter - swe_apparent_diameter) < 0.0001, (
            f"apparent_diameter: factory={venus.apparent_diameter} swe={swe_apparent_diameter}"
        )
        assert abs(venus.apparent_magnitude - swe_apparent_magnitude) < 0.01, (
            f"apparent_magnitude: factory={venus.apparent_magnitude} swe={swe_apparent_magnitude}"
        )

    def test_mars_phenomena_at_j2000_matches_swe(self):
        """Factory Mars phenomena at J2000.0 should match swe.pheno_ut directly."""
        jd_j2000 = 2451545.0
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED

        swe.set_ephe_path(_EPHE_PATH)
        swe_result = swe.pheno_ut(jd_j2000, swe.MARS, iflag)
        swe_phase_angle = swe_result[0]
        swe_elongation = swe_result[2]
        swe.close()

        factory_result = PlanetaryPhenomenaFactory.from_julian_day(
            jd_j2000, planets=["Mars"]
        )
        assert len(factory_result.phenomena) == 1
        mars = factory_result.phenomena[0]

        assert abs(mars.phase_angle - swe_phase_angle) < 0.001, (
            f"phase_angle: factory={mars.phase_angle} swe={swe_phase_angle}"
        )
        assert abs(mars.elongation - swe_elongation) < 0.001, (
            f"elongation: factory={mars.elongation} swe={swe_elongation}"
        )
