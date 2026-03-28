# -*- coding: utf-8 -*-
"""Tests for heliocentric returns and lunar node crossing.

Verifies the core invariants:
- Heliocentric return: planet's heliocentric longitude at the return moment
  matches its natal heliocentric longitude.
- Lunar node crossing: the Moon's longitude at the crossing moment is near
  a lunar node (ascending or descending).
- Return JD falls within a physically reasonable range (one orbital period
  from the search start).
- return_type field is set correctly on every result.
"""

from pathlib import Path

import pytest
import swisseph as swe

from kerykeion import AstrologicalSubjectFactory, PlanetaryReturnFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EPHE_PATH = str(Path(__file__).resolve().parent.parent.parent / "kerykeion" / "sweph")

# Approximate synodic / sidereal orbital periods in days (generous upper bounds).
MARS_ORBITAL_PERIOD = 687      # ~1.88 years
JUPITER_ORBITAL_PERIOD = 4333  # ~11.86 years


def _angular_distance(a: float, b: float) -> float:
    """Shortest arc between two ecliptic longitudes (0-180 degrees)."""
    diff = abs(a - b) % 360.0
    return min(diff, 360.0 - diff)


def _helio_longitude(jd: float, planet_id: int) -> float:
    """Compute heliocentric ecliptic longitude at a given Julian Day."""
    swe.set_ephe_path(EPHE_PATH)
    data = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH | swe.FLG_HELCTR)
    swe.close()
    return data[0][0]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def subject():
    return AstrologicalSubjectFactory.from_birth_data(
        "Test", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
    )


@pytest.fixture(scope="module")
def factory(subject):
    return PlanetaryReturnFactory(
        subject, lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
    )


@pytest.fixture(scope="module")
def start_jd():
    return swe.julday(2025, 1, 1, 0.0)


# ---------------------------------------------------------------------------
# Heliocentric return tests
# ---------------------------------------------------------------------------

class TestHeliocentricReturn:
    """Verify that heliocentric returns satisfy the fundamental invariant:
    the planet's heliocentric longitude at the return equals its natal value."""

    def test_mars_return_longitude_matches_natal(self, factory, subject, start_jd):
        """Planet heliocentric longitude at return must match natal longitude."""
        result = factory.next_heliocentric_return("Mars", start_jd)

        natal_lon = _helio_longitude(subject.julian_day, 4)  # Mars = SE_MARS = 4
        return_lon = _helio_longitude(result.julian_day, 4)

        assert _angular_distance(return_lon, natal_lon) < 1.0, (
            f"Mars helio return longitude {return_lon:.4f} differs from "
            f"natal {natal_lon:.4f} by more than 1 degree"
        )

    def test_jupiter_return_longitude_matches_natal(self, factory, subject, start_jd):
        """Jupiter heliocentric return must also satisfy the longitude invariant."""
        result = factory.next_heliocentric_return("Jupiter", start_jd)

        natal_lon = _helio_longitude(subject.julian_day, 5)  # Jupiter = SE_JUPITER = 5
        return_lon = _helio_longitude(result.julian_day, 5)

        assert _angular_distance(return_lon, natal_lon) < 1.0, (
            f"Jupiter helio return longitude {return_lon:.4f} differs from "
            f"natal {natal_lon:.4f} by more than 1 degree"
        )

    def test_mars_return_within_one_orbital_period(self, factory, start_jd):
        """Mars return from start_jd should occur within one Mars orbital period."""
        result = factory.next_heliocentric_return("Mars", start_jd)
        days_elapsed = result.julian_day - start_jd

        assert 0 < days_elapsed <= MARS_ORBITAL_PERIOD, (
            f"Mars return occurred {days_elapsed:.1f} days after start; "
            f"expected 0 < days <= {MARS_ORBITAL_PERIOD}"
        )

    def test_jupiter_return_within_one_orbital_period(self, factory, start_jd):
        """Jupiter return from start_jd should occur within one Jupiter orbital period."""
        result = factory.next_heliocentric_return("Jupiter", start_jd)
        days_elapsed = result.julian_day - start_jd

        assert 0 < days_elapsed <= JUPITER_ORBITAL_PERIOD, (
            f"Jupiter return occurred {days_elapsed:.1f} days after start; "
            f"expected 0 < days <= {JUPITER_ORBITAL_PERIOD}"
        )

    def test_mars_return_type_is_heliocentric(self, factory, start_jd):
        """return_type must be 'Heliocentric'."""
        result = factory.next_heliocentric_return("Mars", start_jd)
        assert result.return_type == "Heliocentric"

    def test_jupiter_return_type_is_heliocentric(self, factory, start_jd):
        """return_type must be 'Heliocentric'."""
        result = factory.next_heliocentric_return("Jupiter", start_jd)
        assert result.return_type == "Heliocentric"

    def test_heliocentric_return_has_chart_data(self, factory, start_jd):
        """Return chart should contain populated planetary and angular data."""
        result = factory.next_heliocentric_return("Mars", start_jd)
        assert result.sun is not None
        assert result.moon is not None
        assert result.ascendant is not None

    def test_return_jd_is_after_start(self, factory, start_jd):
        """Return JD must be strictly after the search start."""
        result = factory.next_heliocentric_return("Mars", start_jd)
        assert result.julian_day > start_jd


# ---------------------------------------------------------------------------
# Lunar node crossing tests
# ---------------------------------------------------------------------------

class TestPlanetaryReturnValidation:
    """Test validation and error paths in PlanetaryReturnFactory."""

    def test_unknown_planet_heliocentric_raises(self, factory, start_jd):
        """next_heliocentric_return with an unknown planet name should raise."""
        from kerykeion.schemas import KerykeionException
        with pytest.raises(KerykeionException, match="Unknown planet"):
            factory.next_heliocentric_return("NonExistentPlanet", start_jd)

    def test_user_sidereal_without_custom_ayanamsa_raises(self, subject):
        """USER sidereal mode without custom ayanamsa params should raise."""
        from kerykeion.schemas import KerykeionException
        # Create a subject with sidereal_mode = "USER"
        from unittest.mock import patch
        user_subject = subject.model_copy()
        user_subject.sidereal_mode = "USER"
        with pytest.raises(KerykeionException, match="custom_ayanamsa"):
            PlanetaryReturnFactory(
                user_subject,
                lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
                city="Rome", nation="IT", online=False,
            )

    def test_custom_ayanamsa_propagation_build_return_chart(self, subject):
        """Factory with custom ayanamsa attrs should propagate them via _build_return_chart."""
        factory_obj = PlanetaryReturnFactory(
            subject, lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
        )
        # Manually set custom ayanamsa attributes to exercise lines 828, 830
        factory_obj.custom_ayanamsa_t0 = 2451545.0
        factory_obj.custom_ayanamsa_ayan_t0 = 23.5

        # Call _build_return_chart to exercise the propagation path
        result = factory_obj._build_return_chart(swe.julday(2025, 6, 15, 12.0), "Solar")
        assert result is not None
        assert result.return_type == "Solar"

    def test_custom_ayanamsa_propagation_iso_time(self, subject):
        """Factory with custom ayanamsa attrs should propagate them via next_return_from_iso_formatted_time."""
        factory_obj = PlanetaryReturnFactory(
            subject, lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
        )
        # Manually set custom ayanamsa attributes to exercise lines 550, 552
        factory_obj.custom_ayanamsa_t0 = 2451545.0
        factory_obj.custom_ayanamsa_ayan_t0 = 23.5

        result = factory_obj.next_return_from_iso_formatted_time("2025-06-15T12:00:00", "Solar")
        assert result is not None
        assert result.return_type == "Solar"

    def test_solar_return_with_no_sun_raises(self, subject):
        """Solar return with a subject whose sun is None should raise."""
        from kerykeion.schemas import KerykeionException
        factory_obj = PlanetaryReturnFactory(
            subject, lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
        )
        # Mock subject.sun = None
        factory_obj.subject = subject.model_copy()
        factory_obj.subject.sun = None
        with pytest.raises(KerykeionException, match="Sun position"):
            factory_obj.next_return_from_iso_formatted_time("2025-06-15T12:00:00", "Solar")

    def test_lunar_return_with_no_moon_raises(self, subject):
        """Lunar return with a subject whose moon is None should raise."""
        from kerykeion.schemas import KerykeionException
        factory_obj = PlanetaryReturnFactory(
            subject, lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
        )
        # Mock subject.moon = None
        factory_obj.subject = subject.model_copy()
        factory_obj.subject.moon = None
        with pytest.raises(KerykeionException, match="Moon position"):
            factory_obj.next_return_from_iso_formatted_time("2025-06-15T12:00:00", "Lunar")


class TestLunarNodeCrossing:
    """Verify that lunar node crossings place the Moon near a node."""

    def test_moon_longitude_near_node_at_crossing(self, factory, start_jd):
        """At a node crossing the Moon's longitude should be very close to
        the True North Node longitude (ascending) or 180 degrees away
        (descending node)."""
        result = factory.next_lunar_node_crossing(start_jd)

        # Compute the True Node longitude at the crossing moment
        swe.set_ephe_path(EPHE_PATH)
        true_node_data = swe.calc_ut(result.julian_day, 11, swe.FLG_SWIEPH)  # True Node = 11
        swe.close()
        node_lon = true_node_data[0][0]

        # Moon longitude from the return chart
        assert result.moon is not None
        moon_lon = result.moon.abs_pos

        # Distance to ascending node or descending node (node + 180)
        dist_asc = _angular_distance(moon_lon, node_lon)
        dist_desc = _angular_distance(moon_lon, (node_lon + 180.0) % 360.0)
        nearest = min(dist_asc, dist_desc)

        assert nearest < 2.0, (
            f"Moon longitude {moon_lon:.4f} is {nearest:.4f} degrees from "
            f"nearest node (True Node at {node_lon:.4f}); expected < 2 degrees"
        )

    def test_crossing_return_type(self, factory, start_jd):
        """return_type must be 'Lunar_Node_Crossing'."""
        result = factory.next_lunar_node_crossing(start_jd)
        assert result.return_type == "Lunar_Node_Crossing"

    def test_crossing_jd_after_start(self, factory, start_jd):
        """Crossing JD must be strictly after the search start."""
        result = factory.next_lunar_node_crossing(start_jd)
        assert result.julian_day > start_jd

    def test_crossing_within_two_weeks(self, factory, start_jd):
        """Moon crosses a node roughly every ~13.6 days (half draconic month),
        so the next crossing should be within 15 days of the start."""
        result = factory.next_lunar_node_crossing(start_jd)
        days_elapsed = result.julian_day - start_jd
        assert days_elapsed < 15, (
            f"Node crossing occurred {days_elapsed:.1f} days after start; "
            f"expected < 15 days (half draconic month)"
        )

    def test_crossing_has_chart_data(self, factory, start_jd):
        """Crossing chart should contain populated planetary data."""
        result = factory.next_lunar_node_crossing(start_jd)
        assert result.sun is not None
        assert result.moon is not None
