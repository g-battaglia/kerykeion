# -*- coding: utf-8 -*-
"""
Backend Comparison Tests
========================

When both ``pyswisseph`` and ``libephemeris`` are installed, these tests
run identical calculations through each backend and verify the results
agree within acceptable tolerances.

Install both backends to enable these tests::

    pip install pyswisseph libephemeris

Run with::

    pytest tests/core/test_backend_comparison.py -v
"""

import importlib
import math

import pytest


def _try_import(name: str):
    try:
        return importlib.import_module(name)
    except ImportError:
        return None


_swisseph = _try_import("swisseph")
_libephemeris = _try_import("libephemeris")

both_installed = pytest.mark.skipif(
    _swisseph is None or _libephemeris is None,
    reason="Both pyswisseph and libephemeris must be installed for comparison tests",
)


# ── Test Data ────────────────────────────────────────────────────────────
# John Lennon: 1940-10-09 18:30 UTC, Liverpool (53.4084° N, 2.9916° W)
JD_LENNON = 2429878.2708333335  # Julian Day
LAT, LON = 53.4084, -2.9916

# Planet IDs shared by both backends
SUN, MOON, MERCURY, VENUS, MARS = 0, 1, 2, 3, 4
JUPITER, SATURN, URANUS, NEPTUNE, PLUTO = 5, 6, 7, 8, 9
TRUE_NODE = 11


# ── Helpers ──────────────────────────────────────────────────────────────

def _calc_planet(backend, planet_id: int, jd: float = JD_LENNON):
    """Calculate a planet position using a specific backend module."""
    backend.set_ephe_path("")
    flags = backend.FLG_SWIEPH | backend.FLG_SPEED
    result, _retflags = backend.calc_ut(jd, planet_id, flags)
    return result  # (lon, lat, dist, lon_speed, lat_speed, dist_speed)


def _calc_houses(backend, jd: float = JD_LENNON):
    """Calculate houses using a specific backend module."""
    backend.set_ephe_path("")
    flags = backend.FLG_SWIEPH
    cusps, ascmc, cusps_speed, ascmc_speed = backend.houses_ex2(jd, LAT, LON, b"P", flags)
    return cusps, ascmc


def _angular_diff(a: float, b: float) -> float:
    """Absolute angular difference, accounting for 360° wrap."""
    d = abs(a - b) % 360
    return min(d, 360 - d)


# ── Planetary Position Comparison ────────────────────────────────────────

@both_installed
class TestPlanetaryPositionComparison:
    """Compare planetary longitudes between backends."""

    @pytest.mark.parametrize("planet_id,name,tolerance", [
        (SUN, "Sun", 0.01),
        (MOON, "Moon", 0.02),
        (MERCURY, "Mercury", 0.01),
        (VENUS, "Venus", 0.01),
        (MARS, "Mars", 0.01),
        (JUPITER, "Jupiter", 0.01),
        (SATURN, "Saturn", 0.01),
        (URANUS, "Uranus", 0.01),
        (NEPTUNE, "Neptune", 0.01),
        (PLUTO, "Pluto", 0.02),
        (TRUE_NODE, "True Node", 0.1),
    ])
    def test_longitude_agreement(self, planet_id, name, tolerance):
        """Longitude should agree within tolerance (degrees)."""
        swe_result = _calc_planet(_swisseph, planet_id)
        lib_result = _calc_planet(_libephemeris, planet_id)

        diff = _angular_diff(swe_result[0], lib_result[0])
        assert diff < tolerance, (
            f"{name} longitude: swisseph={swe_result[0]:.6f}, "
            f"libephemeris={lib_result[0]:.6f}, diff={diff:.6f}° (tolerance={tolerance}°)"
        )

    @pytest.mark.parametrize("planet_id,name", [
        (SUN, "Sun"), (MOON, "Moon"), (MARS, "Mars"),
        (JUPITER, "Jupiter"), (SATURN, "Saturn"),
    ])
    def test_speed_agreement(self, planet_id, name):
        """Daily speed should agree within 0.01 deg/day for major planets."""
        swe_result = _calc_planet(_swisseph, planet_id)
        lib_result = _calc_planet(_libephemeris, planet_id)

        speed_diff = abs(swe_result[3] - lib_result[3])
        assert speed_diff < 0.01, (
            f"{name} speed: swisseph={swe_result[3]:.6f}, "
            f"libephemeris={lib_result[3]:.6f}, diff={speed_diff:.6f}"
        )

    @pytest.mark.parametrize("planet_id,name", [
        (SUN, "Sun"), (MOON, "Moon"), (MARS, "Mars"),
    ])
    def test_latitude_agreement(self, planet_id, name):
        """Ecliptic latitude should agree within 0.01 degrees."""
        swe_result = _calc_planet(_swisseph, planet_id)
        lib_result = _calc_planet(_libephemeris, planet_id)

        lat_diff = abs(swe_result[1] - lib_result[1])
        assert lat_diff < 0.01, (
            f"{name} latitude: swisseph={swe_result[1]:.6f}, "
            f"libephemeris={lib_result[1]:.6f}, diff={lat_diff:.6f}"
        )

    def test_retrograde_agreement(self):
        """Retrograde status should match for all planets."""
        for planet_id in [MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE, PLUTO]:
            swe_result = _calc_planet(_swisseph, planet_id)
            lib_result = _calc_planet(_libephemeris, planet_id)
            swe_retro = swe_result[3] < 0
            lib_retro = lib_result[3] < 0
            assert swe_retro == lib_retro, (
                f"Planet {planet_id}: swisseph retrograde={swe_retro}, "
                f"libephemeris retrograde={lib_retro}"
            )

    def test_zodiac_sign_agreement(self):
        """All planets should be in the same zodiac sign."""
        for planet_id in [SUN, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN]:
            swe_result = _calc_planet(_swisseph, planet_id)
            lib_result = _calc_planet(_libephemeris, planet_id)
            swe_sign = int(swe_result[0] / 30)
            lib_sign = int(lib_result[0] / 30)
            assert swe_sign == lib_sign, (
                f"Planet {planet_id}: swisseph sign={swe_sign}, "
                f"libephemeris sign={lib_sign} "
                f"(lon: {swe_result[0]:.4f} vs {lib_result[0]:.4f})"
            )


# ── House Cusp Comparison ────────────────────────────────────────────────

@both_installed
class TestHouseCuspComparison:
    """Compare house cusps between backends."""

    def test_ascendant_agreement(self):
        """Ascendant should agree within 0.02 degrees."""
        _swe_cusps, swe_ascmc = _calc_houses(_swisseph)
        _lib_cusps, lib_ascmc = _calc_houses(_libephemeris)

        diff = _angular_diff(swe_ascmc[0], lib_ascmc[0])
        assert diff < 0.02, (
            f"ASC: swisseph={swe_ascmc[0]:.6f}, libephemeris={lib_ascmc[0]:.6f}, diff={diff:.6f}"
        )

    def test_mc_agreement(self):
        """Midheaven should agree within 0.02 degrees."""
        _swe_cusps, swe_ascmc = _calc_houses(_swisseph)
        _lib_cusps, lib_ascmc = _calc_houses(_libephemeris)

        diff = _angular_diff(swe_ascmc[1], lib_ascmc[1])
        assert diff < 0.02, (
            f"MC: swisseph={swe_ascmc[1]:.6f}, libephemeris={lib_ascmc[1]:.6f}, diff={diff:.6f}"
        )

    def test_all_cusps_agreement(self):
        """All 12 house cusps should agree within 0.05 degrees."""
        swe_cusps, _ = _calc_houses(_swisseph)
        lib_cusps, _ = _calc_houses(_libephemeris)

        for i in range(12):
            diff = _angular_diff(swe_cusps[i], lib_cusps[i])
            assert diff < 0.05, (
                f"House {i + 1}: swisseph={swe_cusps[i]:.6f}, "
                f"libephemeris={lib_cusps[i]:.6f}, diff={diff:.6f}"
            )


# ── High-Level Integration Comparison ────────────────────────────────────

@both_installed
class TestKerykeionIntegrationComparison:
    """Compare full kerykeion subject creation across backends."""

    @pytest.fixture(scope="class")
    def subjects(self):
        """Create the same subject with both backends."""
        import os
        from kerykeion import AstrologicalSubjectFactory

        results = {}

        for backend_name in ("swisseph", "libephemeris"):
            os.environ["KERYKEION_BACKEND"] = backend_name
            # Force reimport of the backend module
            import kerykeion.ephemeris_backend as eb
            importlib.reload(eb)

            subject = AstrologicalSubjectFactory.from_birth_data(
                "Test", 1940, 10, 9, 18, 30,
                lng=LON, lat=LAT, tz_str="Europe/London",
                city="Liverpool", nation="GB", online=False,
            )
            results[backend_name] = subject

        # Restore default
        os.environ.pop("KERYKEION_BACKEND", None)
        importlib.reload(eb)

        return results

    def test_sun_sign_matches(self, subjects):
        assert subjects["swisseph"].sun.sign == subjects["libephemeris"].sun.sign

    def test_moon_sign_matches(self, subjects):
        assert subjects["swisseph"].moon.sign == subjects["libephemeris"].moon.sign

    def test_ascendant_sign_matches(self, subjects):
        assert subjects["swisseph"].ascendant.sign == subjects["libephemeris"].ascendant.sign

    def test_sun_position_close(self, subjects):
        diff = _angular_diff(
            subjects["swisseph"].sun.abs_pos,
            subjects["libephemeris"].sun.abs_pos,
        )
        assert diff < 0.02, f"Sun abs_pos diff: {diff:.6f}°"

    def test_moon_position_close(self, subjects):
        diff = _angular_diff(
            subjects["swisseph"].moon.abs_pos,
            subjects["libephemeris"].moon.abs_pos,
        )
        assert diff < 0.05, f"Moon abs_pos diff: {diff:.6f}°"

    def test_house_system_name_matches(self, subjects):
        assert subjects["swisseph"].houses_system_name == subjects["libephemeris"].houses_system_name
