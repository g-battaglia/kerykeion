# -*- coding: utf-8 -*-
"""Tests for the Astro-Cartography (ACG) factory (v6.0)."""

import pytest
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
