# -*- coding: utf-8 -*-
"""Tests for the Barycentric perspective type.

Barycentric mode shifts the observer from Earth's center to the solar system
barycenter (near the Sun's center).  This produces large positional shifts for
nearby bodies (Moon, inner planets) and progressively smaller shifts for more
distant planets.

NOTE: The Sun's barycentric calculation requires the ``sepl_18.se1`` ephemeris
file.  When that file is absent the Sun is returned as ``None``.  Tests that
depend on the Sun gracefully skip in that scenario.
"""

import pytest
from kerykeion import AstrologicalSubjectFactory


def _angular_diff(a: float, b: float) -> float:
    """Return the shortest angular difference in degrees (0..180)."""
    d = abs(a - b) % 360
    return d if d <= 180 else 360 - d


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
    # ------------------------------------------------------------------
    # Basic creation and metadata
    # ------------------------------------------------------------------
    def test_subject_created(self, barycentric_subject):
        """Barycentric subject should be created without errors."""
        assert barycentric_subject is not None

    def test_perspective_type_stored(self, barycentric_subject):
        """The perspective_type attribute must be 'Barycentric'."""
        assert barycentric_subject.perspective_type == "Barycentric"

    def test_planets_calculated(self, barycentric_subject):
        """Main planets should be calculated in barycentric mode."""
        assert barycentric_subject.jupiter is not None
        assert barycentric_subject.saturn is not None
        assert 0 <= barycentric_subject.jupiter.abs_pos < 360

    # ------------------------------------------------------------------
    # Sun: barycentric vs geocentric
    # ------------------------------------------------------------------
    def test_sun_nearly_unchanged(self, barycentric_subject, geocentric_subject):
        """Sun's barycentric position should be very close to geocentric.

        The solar system barycenter is mostly inside the Sun, so the Sun's
        apparent direction barely changes when the observer moves from Earth
        to the barycenter.  The difference should be on the order of
        arcseconds -- we use a generous 0.05 degree (~3 arcminute) tolerance.

        If the required ephemeris file (sepl_18.se1) is not installed the Sun
        is returned as None and the test is skipped.
        """
        if barycentric_subject.sun is None or geocentric_subject.sun is None:
            pytest.skip("Sun unavailable (sepl_18.se1 ephemeris file missing)")

        sun_diff = _angular_diff(
            barycentric_subject.sun.abs_pos,
            geocentric_subject.sun.abs_pos,
        )
        assert sun_diff < 0.05, (
            f"Sun barycentric-geocentric diff is {sun_diff:.6f} deg; "
            f"expected < 0.05 deg"
        )

    # ------------------------------------------------------------------
    # Moon: should show the largest shift
    # ------------------------------------------------------------------
    def test_moon_large_difference(self, barycentric_subject, geocentric_subject):
        """The Moon should show a very large barycentric shift.

        Moving the observer from Earth to the barycenter (~1 AU away) causes a
        massive parallax for the nearby Moon.  The positional difference should
        be many degrees -- we assert at least 10 degrees as a conservative
        lower bound.
        """
        assert barycentric_subject.moon is not None, "Moon should be calculated"
        assert geocentric_subject.moon is not None

        moon_diff = _angular_diff(
            barycentric_subject.moon.abs_pos,
            geocentric_subject.moon.abs_pos,
        )
        assert moon_diff > 10.0, (
            f"Moon barycentric-geocentric diff is only {moon_diff:.6f} deg; "
            f"expected > 10 deg for a ~1 AU observer shift"
        )

    # ------------------------------------------------------------------
    # Outer planets: small(er) differences
    # ------------------------------------------------------------------
    def test_outer_planets_small_difference(self, barycentric_subject, geocentric_subject):
        """Outer planets should have small barycentric-geocentric differences.

        Because Jupiter, Saturn, Uranus, and Neptune are far from Earth, the
        ~1 AU shift to the barycenter produces only a modest parallax.  We
        verify each is under 10 degrees and that more distant planets show
        progressively smaller differences.
        """
        diffs = {}
        for name in ("jupiter", "saturn", "uranus", "neptune"):
            bary_planet = getattr(barycentric_subject, name)
            geo_planet = getattr(geocentric_subject, name)
            assert bary_planet is not None, f"{name} should be calculated (bary)"
            assert geo_planet is not None, f"{name} should be calculated (geo)"
            diffs[name] = _angular_diff(bary_planet.abs_pos, geo_planet.abs_pos)

        # Each outer planet's shift should be under 10 degrees
        for name, diff in diffs.items():
            assert diff < 10.0, (
                f"{name} barycentric shift is {diff:.4f} deg; expected < 10 deg"
            )

        # More distant planets should show smaller shifts than closer ones:
        # Uranus/Neptune should shift less than Jupiter
        assert diffs["uranus"] < diffs["jupiter"], (
            f"Uranus diff ({diffs['uranus']:.4f}) should be < "
            f"Jupiter diff ({diffs['jupiter']:.4f})"
        )
        assert diffs["neptune"] < diffs["jupiter"], (
            f"Neptune diff ({diffs['neptune']:.4f}) should be < "
            f"Jupiter diff ({diffs['jupiter']:.4f})"
        )

    def test_positions_differ_from_geocentric(self, barycentric_subject, geocentric_subject):
        """Barycentric positions should differ from geocentric for outer planets."""
        jupiter_diff = _angular_diff(
            barycentric_subject.jupiter.abs_pos,
            geocentric_subject.jupiter.abs_pos,
        )
        saturn_diff = _angular_diff(
            barycentric_subject.saturn.abs_pos,
            geocentric_subject.saturn.abs_pos,
        )
        assert jupiter_diff > 0.001, "Jupiter should differ measurably"
        assert saturn_diff > 0.001, "Saturn should differ measurably"

    # ------------------------------------------------------------------
    # Moon vs outer planets: Moon shift should dominate
    # ------------------------------------------------------------------
    def test_moon_shift_larger_than_outer_planets(
        self, barycentric_subject, geocentric_subject
    ):
        """The Moon's barycentric shift should be much larger than any outer planet's."""
        moon_diff = _angular_diff(
            barycentric_subject.moon.abs_pos,
            geocentric_subject.moon.abs_pos,
        )
        for name in ("jupiter", "saturn", "uranus", "neptune"):
            planet_diff = _angular_diff(
                getattr(barycentric_subject, name).abs_pos,
                getattr(geocentric_subject, name).abs_pos,
            )
            assert moon_diff > planet_diff, (
                f"Moon diff ({moon_diff:.4f}) should exceed "
                f"{name} diff ({planet_diff:.4f})"
            )
