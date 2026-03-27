# -*- coding: utf-8 -*-
"""Tests for the Planetary Phenomena factory.

Validates phase angle, elongation, illumination, apparent magnitude,
and morning/evening star status calculations via swe.pheno_ut().
"""

import pytest
from kerykeion import AstrologicalSubjectFactory, PlanetaryPhenomenaFactory


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
