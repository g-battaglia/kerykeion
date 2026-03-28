# -*- coding: utf-8 -*-
"""Tests for the Astro-Cartography (ACG) factory (v6.0)."""

import math
import pytest
import swisseph as swe
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory, AstroCartographyFactory


@pytest.fixture(scope="module")
def subject():
    return AstrologicalSubjectFactory.from_birth_data(
        "ACG Test", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
    )


class TestACGComputation:
    def test_lines_computed(self, subject):
        """Should compute ACG lines."""
        lines = AstroCartographyFactory.compute(subject, step=5)
        assert isinstance(lines, list)
        assert len(lines) > 0

    def test_mc_ic_lines_present(self, subject):
        """MC and IC lines should be present for each planet."""
        lines = AstroCartographyFactory.compute(subject, step=5, planets=["Sun", "Moon"])
        line_types = [(l.planet, l.line_type) for l in lines]
        assert ("Sun", "MC") in line_types
        assert ("Sun", "IC") in line_types
        assert ("Moon", "MC") in line_types
        assert ("Moon", "IC") in line_types

    def test_asc_dsc_lines_present(self, subject):
        """ASC and/or DSC lines should be present for at least some planets."""
        lines = AstroCartographyFactory.compute(subject, step=5)
        has_asc = any(l.line_type == "ASC" for l in lines)
        has_dsc = any(l.line_type == "DSC" for l in lines)
        assert has_asc or has_dsc, "Should have at least some ASC or DSC lines"

    def test_mc_line_is_vertical(self, subject):
        """MC lines should be vertical (same longitude, different latitudes)."""
        lines = AstroCartographyFactory.compute(subject, step=5, planets=["Sun"])
        mc_lines = [l for l in lines if l.line_type == "MC"]
        assert len(mc_lines) > 0
        mc = mc_lines[0]
        lngs = set(p.longitude for p in mc.points)
        # All points should have the same longitude (vertical line)
        assert len(lngs) == 1

    def test_longitude_range(self, subject):
        """Line points should be within valid geographic longitude."""
        lines = AstroCartographyFactory.compute(subject, step=5)
        for line in lines:
            for point in line.points:
                assert -180 <= point.longitude <= 180

    def test_latitude_range(self, subject):
        """Line points should be within the specified latitude range."""
        lines = AstroCartographyFactory.compute(subject, step=5, lat_range=(-60, 60))
        for line in lines:
            for point in line.points:
                assert -60 <= point.latitude <= 60

    def test_planet_filter(self, subject):
        """Should respect planet filter."""
        lines = AstroCartographyFactory.compute(subject, step=5, planets=["Jupiter"])
        for line in lines:
            assert line.planet == "Jupiter"

    def test_step_affects_detail(self, subject):
        """Smaller step should produce more points (for MC/IC vertical lines)."""
        coarse = AstroCartographyFactory.compute(subject, step=10, planets=["Sun"])
        fine = AstroCartographyFactory.compute(subject, step=2, planets=["Sun"])

        # MC lines should have more points with finer step
        coarse_mc = [l for l in coarse if l.line_type == "MC"][0]
        fine_mc = [l for l in fine if l.line_type == "MC"][0]
        assert len(fine_mc.points) >= len(coarse_mc.points)


class TestACGSweRegressions:
    """Known-value regression tests using Swiss Ephemeris as reference source.

    Verifies that the Sun MC line longitude produced by AstroCartographyFactory
    matches the value derived directly from swe.sidtime and swe.calc_ut.
    """

    @pytest.fixture(scope="class")
    def acg_subject(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "ACG Regression", 1990, 6, 15, 14, 30,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
        )

    def test_sun_mc_line_longitude_matches_swe(self, acg_subject):
        """Sun MC line longitude must match the value derived from swe directly.

        The Sun's MC line falls at the geographic longitude where the Sun
        culminates (transits the local meridian).  From swe:
            Sun RA (ecliptic->equatorial, zero ecliptic latitude approx)
            GAST = swe.sidtime(jd) in hours
            mc_geo_lng = (sun_RA - GAST * 15) mod 360, shifted to [-180,180]

        The factory uses the same formula, so the MC line's longitude should
        match within 1 degree.
        """
        ephe_path = str(Path(__file__).resolve().parent.parent.parent / "kerykeion" / "sweph")
        swe.set_ephe_path(ephe_path)

        jd = acg_subject.julian_day
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED

        # Get obliquity
        obliquity = swe.calc_ut(jd, swe.ECL_NUT, iflag)[0][0]

        # Get Sun ecliptic longitude
        sun_ecl = swe.calc_ut(jd, swe.SUN, iflag)[0]
        sun_ecl_lon = sun_ecl[0]

        # Convert to RA (zero ecliptic latitude approximation, same as factory)
        ecl_rad = math.radians(sun_ecl_lon)
        eps_rad = math.radians(obliquity)
        ra_rad = math.atan2(
            math.sin(ecl_rad) * math.cos(eps_rad),
            math.cos(ecl_rad),
        )
        sun_ra = math.degrees(ra_rad) % 360

        # Greenwich apparent sidereal time
        gst_hours = swe.sidtime(jd)
        swe.close()

        # Expected MC geographic longitude
        expected_mc_lng = (sun_ra - gst_hours * 15.0) % 360
        if expected_mc_lng > 180:
            expected_mc_lng -= 360

        # Get factory result
        lines = AstroCartographyFactory.compute(acg_subject, step=1, planets=["Sun"])
        sun_mc = next(l for l in lines if l.planet == "Sun" and l.line_type == "MC")

        # MC line is vertical, so all points share the same longitude
        factory_mc_lng = sun_mc.points[0].longitude

        assert abs(factory_mc_lng - expected_mc_lng) < 1.0, (
            f"Sun MC line longitude mismatch: factory={factory_mc_lng}, "
            f"expected={expected_mc_lng}"
        )
