# -*- coding: utf-8 -*-
"""Tests for planetocentric perspective calculations.

These tests verify that planetocentric charts actually differ from geocentric
charts, catching silent fallbacks to geocentric data.
"""

import pytest
from kerykeion import AstrologicalSubjectFactory


# ---------------------------------------------------------------------------
# Shared birth data for consistent comparisons
# ---------------------------------------------------------------------------
_BIRTH_KWARGS = dict(
    year=2000, month=1, day=1, hour=12, minute=0,
    lng=0.0, lat=51.5, tz_str="Etc/GMT",
    city="Greenwich", nation="GB", online=False,
)


def _angular_diff(a: float, b: float) -> float:
    """Shortest angular difference between two ecliptic longitudes (0-180)."""
    d = abs(a - b) % 360
    return d if d <= 180 else 360 - d


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def geocentric():
    return AstrologicalSubjectFactory.from_birth_data(
        "Geocentric", **_BIRTH_KWARGS,
    )


@pytest.fixture(scope="module")
def marscentric():
    return AstrologicalSubjectFactory.from_birth_data(
        "Marscentric", **_BIRTH_KWARGS, perspective_type="Marscentric",
    )


@pytest.fixture(scope="module")
def jupitercentric():
    return AstrologicalSubjectFactory.from_birth_data(
        "Jupitercentric", **_BIRTH_KWARGS, perspective_type="Jupitercentric",
    )


@pytest.fixture(scope="module")
def venuscentric():
    return AstrologicalSubjectFactory.from_birth_data(
        "Venuscentric", **_BIRTH_KWARGS, perspective_type="Venuscentric",
    )


@pytest.fixture(scope="module")
def selenocentric():
    return AstrologicalSubjectFactory.from_birth_data(
        "Selenocentric", **_BIRTH_KWARGS, perspective_type="Selenocentric",
    )


# List of planet attribute names we can compare across subjects.
# Sun is excluded because calc_pctr for the Sun requires the sepl_*.se1
# planetary ephemeris file which is not bundled; the factory silently falls
# back to geocentric for any body whose calc_pctr call fails.
_COMPARABLE_PLANETS = ["moon", "mercury", "venus", "mars", "jupiter", "saturn"]


# ---------------------------------------------------------------------------
# 1. Basic creation and perspective_type stored correctly
# ---------------------------------------------------------------------------
class TestPerspectiveTypeStored:
    """Verify that the perspective_type attribute is recorded on the model."""

    @pytest.mark.parametrize("perspective", [
        "Marscentric", "Jupitercentric", "Venuscentric", "Selenocentric",
    ])
    def test_perspective_type_attribute(self, perspective):
        s = AstrologicalSubjectFactory.from_birth_data(
            f"{perspective} Test", **_BIRTH_KWARGS,
            perspective_type=perspective,
        )
        assert s.perspective_type == perspective

    def test_default_perspective_is_apparent_geocentric(self, geocentric):
        assert geocentric.perspective_type == "Apparent Geocentric"

    @pytest.mark.parametrize("perspective", [
        "Marscentric", "Jupitercentric", "Venuscentric", "Selenocentric",
    ])
    def test_creates_valid_chart_with_positions(self, perspective):
        s = AstrologicalSubjectFactory.from_birth_data(
            f"{perspective} Test", **_BIRTH_KWARGS,
            perspective_type=perspective,
        )
        assert s is not None
        assert s.sun is not None
        assert 0 <= s.sun.abs_pos < 360
        assert s.moon is not None
        assert 0 <= s.moon.abs_pos < 360


# ---------------------------------------------------------------------------
# 2. KEY ASSERTION: planetocentric positions differ from geocentric
# ---------------------------------------------------------------------------
class TestPositionsDifferFromGeocentric:
    """At least one planet must differ by >0.01 degrees from geocentric.

    This is the critical test that catches a silent fallback to geocentric
    data.  For each planetocentric perspective, we compare every comparable
    planet and require at least one measurable difference.

    Note: The Sun position may silently fall back to geocentric when the
    sepl_*.se1 planetary ephemeris file is unavailable.  We exclude it from
    the comparison set and focus on Moon through Saturn, which use the
    seas_*.se1 or internal Moshier fallback successfully.
    """

    @pytest.mark.parametrize("perspective_fixture,center_attr", [
        ("marscentric", "mars"),
        ("jupitercentric", "jupiter"),
        ("venuscentric", "venus"),
        ("selenocentric", "moon"),
    ])
    def test_at_least_one_planet_differs(
        self, perspective_fixture, center_attr, geocentric, request,
    ):
        pctr = request.getfixturevalue(perspective_fixture)
        max_diff = 0.0
        diffs = {}
        for planet in _COMPARABLE_PLANETS:
            geo_point = getattr(geocentric, planet)
            pctr_point = getattr(pctr, planet)
            if geo_point is None or pctr_point is None:
                continue
            diff = _angular_diff(geo_point.abs_pos, pctr_point.abs_pos)
            diffs[planet] = diff
            if diff > max_diff:
                max_diff = diff

        assert max_diff > 0.01, (
            f"{perspective_fixture} positions are identical to geocentric "
            f"(max diff={max_diff:.6f} deg). Likely silent fallback! "
            f"Diffs: {diffs}"
        )


# ---------------------------------------------------------------------------
# 3. Center planet behavior: position unchanged (geocentric fallback by
#    design) because when planet_id == center_body_id the factory uses
#    regular calc_ut.
# ---------------------------------------------------------------------------
class TestCenterPlanetBehavior:
    """The center planet's position should equal its geocentric position.

    When calculating from Mars, Mars itself cannot be computed via calc_pctr
    (the body and the center are the same), so the factory correctly falls
    back to calc_ut.  This means the center planet's position matches the
    geocentric position exactly.
    """

    def test_marscentric_mars_matches_geocentric(self, marscentric, geocentric):
        assert marscentric.mars is not None
        assert geocentric.mars is not None
        assert marscentric.mars.abs_pos == pytest.approx(
            geocentric.mars.abs_pos, abs=1e-6,
        )

    def test_jupitercentric_jupiter_matches_geocentric(self, jupitercentric, geocentric):
        assert jupitercentric.jupiter is not None
        assert geocentric.jupiter is not None
        assert jupitercentric.jupiter.abs_pos == pytest.approx(
            geocentric.jupiter.abs_pos, abs=1e-6,
        )

    def test_venuscentric_venus_matches_geocentric(self, venuscentric, geocentric):
        assert venuscentric.venus is not None
        assert geocentric.venus is not None
        assert venuscentric.venus.abs_pos == pytest.approx(
            geocentric.venus.abs_pos, abs=1e-6,
        )

    def test_selenocentric_moon_matches_geocentric(self, selenocentric, geocentric):
        assert selenocentric.moon is not None
        assert geocentric.moon is not None
        assert selenocentric.moon.abs_pos == pytest.approx(
            geocentric.moon.abs_pos, abs=1e-6,
        )


# ---------------------------------------------------------------------------
# 4. Non-center planets should differ dramatically from geocentric
#    (for outer-planet perspectives the angular shift is large).
# ---------------------------------------------------------------------------
class TestNonCenterPlanetsDifferSignificantly:
    """Specific planets that should show large shifts in planetocentric views.

    When viewing from Mars or Jupiter, inner planets like Moon and Mercury
    appear at very different ecliptic longitudes compared to geocentric.
    """

    def test_marscentric_moon_differs_dramatically(self, marscentric, geocentric):
        """Moon seen from Mars should differ by many degrees from geocentric."""
        diff = _angular_diff(marscentric.moon.abs_pos, geocentric.moon.abs_pos)
        assert diff > 1.0, (
            f"Marscentric Moon diff={diff:.4f} deg is too small; "
            f"expected a large shift when viewed from Mars."
        )

    def test_marscentric_mercury_differs_dramatically(self, marscentric, geocentric):
        diff = _angular_diff(marscentric.mercury.abs_pos, geocentric.mercury.abs_pos)
        assert diff > 1.0, (
            f"Marscentric Mercury diff={diff:.4f} deg is too small."
        )

    def test_jupitercentric_mars_differs_dramatically(self, jupitercentric, geocentric):
        """Mars seen from Jupiter should differ by many degrees."""
        diff = _angular_diff(jupitercentric.mars.abs_pos, geocentric.mars.abs_pos)
        assert diff > 1.0, (
            f"Jupitercentric Mars diff={diff:.4f} deg is too small."
        )

    def test_jupitercentric_moon_differs_dramatically(self, jupitercentric, geocentric):
        diff = _angular_diff(jupitercentric.moon.abs_pos, geocentric.moon.abs_pos)
        assert diff > 1.0, (
            f"Jupitercentric Moon diff={diff:.4f} deg is too small."
        )

    def test_venuscentric_moon_differs_dramatically(self, venuscentric, geocentric):
        """Moon seen from Venus should differ enormously."""
        diff = _angular_diff(venuscentric.moon.abs_pos, geocentric.moon.abs_pos)
        assert diff > 1.0, (
            f"Venuscentric Moon diff={diff:.4f} deg is too small."
        )

    def test_selenocentric_mercury_differs(self, selenocentric, geocentric):
        """Mercury seen from the Moon differs slightly (Moon is close to Earth)."""
        diff = _angular_diff(selenocentric.mercury.abs_pos, geocentric.mercury.abs_pos)
        # Moon is close to Earth, so differences are small but still measurable
        assert diff > 0.01, (
            f"Selenocentric Mercury diff={diff:.6f} deg; expected >0.01."
        )


# ---------------------------------------------------------------------------
# 5. All positions remain valid (within 0-360 range)
# ---------------------------------------------------------------------------
class TestAllPositionsValid:
    """Every planet on every planetocentric chart should have abs_pos in [0, 360)."""

    _ALL_PLANETS = [
        "sun", "moon", "mercury", "venus", "mars",
        "jupiter", "saturn", "uranus", "neptune", "pluto",
    ]

    @pytest.mark.parametrize("perspective_fixture", [
        "marscentric", "jupitercentric", "venuscentric", "selenocentric",
    ])
    def test_all_positions_in_range(self, perspective_fixture, request):
        pctr = request.getfixturevalue(perspective_fixture)
        for planet in self._ALL_PLANETS:
            point = getattr(pctr, planet, None)
            if point is not None:
                assert 0 <= point.abs_pos < 360, (
                    f"{perspective_fixture}.{planet}.abs_pos = {point.abs_pos} "
                    f"is out of [0, 360) range"
                )
