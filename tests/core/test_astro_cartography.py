# -*- coding: utf-8 -*-
"""Tests for the Astro-Cartography (ACG) factory (v6.0)."""

import math
import pytest
from kerykeion.ephemeris_backend import ephe, ephemeris_session
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
        line_types = [(line.planet, line.line_type) for line in lines]
        assert ("Sun", "MC") in line_types
        assert ("Sun", "IC") in line_types
        assert ("Moon", "MC") in line_types
        assert ("Moon", "IC") in line_types

    def test_asc_dsc_lines_present(self, subject):
        """ASC and/or DSC lines should be present for at least some planets."""
        lines = AstroCartographyFactory.compute(subject, step=5)
        has_asc = any(line.line_type == "ASC" for line in lines)
        has_dsc = any(line.line_type == "DSC" for line in lines)
        assert has_asc or has_dsc, "Should have at least some ASC or DSC lines"

    def test_mc_line_is_vertical(self, subject):
        """MC lines should be vertical (same longitude, different latitudes)."""
        lines = AstroCartographyFactory.compute(subject, step=5, planets=["Sun"])
        mc_lines = [line for line in lines if line.line_type == "MC"]
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

    @pytest.mark.parametrize("planets", [["Nope"], ["Sun", "Nope"], [1], "Sun"])
    def test_invalid_planet_filter_rejected(self, subject, planets):
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException, match="planets"):
            AstroCartographyFactory.compute(subject, planets=planets)  # type: ignore[arg-type]

    def test_supported_but_absent_planet_is_valid_empty_filter(self, subject):
        without_pluto = subject.model_copy(update={"pluto": None})
        assert AstroCartographyFactory.compute(without_pluto, planets=["Pluto"]) == []

    def test_step_affects_detail(self, subject):
        """Smaller step should produce more points (for MC/IC vertical lines)."""
        coarse = AstroCartographyFactory.compute(subject, step=10, planets=["Sun"])
        fine = AstroCartographyFactory.compute(subject, step=2, planets=["Sun"])

        # MC lines should have more points with finer step
        coarse_mc = next(line for line in coarse if line.line_type == "MC")
        fine_mc = next(line for line in fine if line.line_type == "MC")
        assert len(fine_mc.points) >= len(coarse_mc.points)

    @pytest.mark.parametrize(
        "invalid_step",
        [float("nan"), float("inf"), float("-inf"), 0.0, -1.0, 10**309],
        ids=[
            "nan",
            "positive-infinity",
            "negative-infinity",
            "zero",
            "negative",
            "unrepresentably-large",
        ],
    )
    def test_invalid_step_rejected(self, subject, invalid_step):
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException, match="step"):
            AstroCartographyFactory.compute(subject, step=invalid_step)

    @pytest.mark.parametrize("step", [1e-9, 1e-306])
    def test_projected_point_limit_rejects_pathological_grid(self, subject, step):
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException, match="safety limit"):
            AstroCartographyFactory.compute(subject, step=step, planets=["Sun"])

    @pytest.mark.parametrize(
        "julian_day",
        [float("nan"), float("inf"), float("-inf"), 10**309],
        ids=["nan", "positive-infinity", "negative-infinity", "unrepresentably-large"],
    )
    def test_non_finite_subject_julian_day_rejected(self, subject, julian_day):
        from kerykeion.schemas import KerykeionException

        corrupted = subject.model_copy(update={"julian_day": julian_day})
        with pytest.raises(KerykeionException, match="Julian Day.*finite"):
            AstroCartographyFactory.compute(corrupted, planets=["Sun"])

    @pytest.mark.parametrize(
        "invalid_lat_range",
        [
            (-90.1, 0.0),
            (0.0, 90.1),
            (float("nan"), 0.0),
            (0.0, float("inf")),
            (0.0, 10**309),
            (10.0, -10.0),
        ],
    )
    def test_invalid_lat_range_rejected(self, subject, invalid_lat_range):
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException, match="lat_range"):
            AstroCartographyFactory.compute(subject, lat_range=invalid_lat_range)


def _true_equatorial(jd, planet_id):
    """True equatorial RA/declination (degrees), sidereal flag stripped."""
    with ephemeris_session() as iflag:
        eq_iflag = (iflag & ~ephe.FLG_SIDEREAL) | ephe.FLG_EQUATORIAL
        pos = ephe.calc_ut(jd, planet_id, eq_iflag)[0]
        return pos[0], pos[1]


def _expected_mc_lng(jd, planet_id):
    """In-mundo MC line geographic longitude: wrap(true RA - GST)."""
    ra_deg, _ = _true_equatorial(jd, planet_id)
    with ephemeris_session():
        gst_deg = ephe.sidtime(jd) * 15.0
    mc_lng = (ra_deg - gst_deg) % 360
    if mc_lng > 180:
        mc_lng -= 360
    return mc_lng


def _zodiacal_mc_lng(jd, planet_id):
    """MC longitude from the OLD beta=0 zodiacal projection (pre-v6-fix)."""
    with ephemeris_session() as iflag:
        obliquity = ephe.calc_ut(jd, ephe.ECL_NUT, iflag)[0][0]
        ecl_lon = ephe.calc_ut(jd, planet_id, iflag)[0][0]
        gst_deg = ephe.sidtime(jd) * 15.0
    ecl_rad = math.radians(ecl_lon)
    eps_rad = math.radians(obliquity)
    ra_rad = math.atan2(math.sin(ecl_rad) * math.cos(eps_rad), math.cos(ecl_rad))
    mc_lng = (math.degrees(ra_rad) % 360 - gst_deg) % 360
    if mc_lng > 180:
        mc_lng -= 360
    return mc_lng


class TestACGSweRegressions:
    """Known-value regression tests using Swiss Ephemeris as reference source.

    Verifies that MC line longitudes produced by AstroCartographyFactory
    match values derived directly from ephe.sidtime and ephe.calc_ut
    (FLG_EQUATORIAL), i.e. the in-mundo culmination meridian.
    """

    @pytest.fixture(scope="class")
    def acg_subject(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "ACG Regression", 1990, 6, 15, 14, 30,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
        )

    def test_sun_mc_line_longitude_matches_swe(self, acg_subject):
        """Sun MC line longitude must match the value derived from ephe directly.

        The Sun's MC line falls at the geographic longitude where the Sun
        culminates (transits the local meridian).  From ephe:
            Sun true RA (ephe.calc_ut with FLG_EQUATORIAL)
            GAST = ephe.sidtime(jd) in hours
            mc_geo_lng = (sun_RA - GAST * 15) mod 360, shifted to [-180,180]

        v6 in-mundo fix: the factory now uses the body's true equatorial RA
        (not the beta=0 zodiacal projection), so the match is exact. For the
        Sun (ecliptic latitude ~0) both methods agree within ~0.001 degrees,
        so this also pins backward compatibility for the Sun line.
        """
        jd = acg_subject.julian_day
        expected_mc_lng = _expected_mc_lng(jd, ephe.SUN)

        # Get factory result
        lines = AstroCartographyFactory.compute(acg_subject, step=1, planets=["Sun"])
        sun_mc = next(line for line in lines if line.planet == "Sun" and line.line_type == "MC")

        # MC line is vertical, so all points share the same longitude
        factory_mc_lng = sun_mc.points[0].longitude

        assert abs(factory_mc_lng - expected_mc_lng) < 0.01, (
            f"Sun MC line longitude mismatch: factory={factory_mc_lng}, "
            f"expected={expected_mc_lng}"
        )


class TestACGInMundoLines:
    """v6 pre-beta fix: ACG lines are computed in mundo from TRUE equatorial
    coordinates. Previously RA was derived from the ecliptic longitude at
    latitude beta=0, which shifted the lines of bodies with nonzero ecliptic
    latitude (measured: ~4.6 deg for Pluto, ~1.2 deg for the Moon on the
    1990-06-15 fixture date) away from reference maps (Jim Lewis / astro.com).
    """

    @pytest.fixture(scope="class")
    def acg_subject(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "ACG In Mundo", 1990, 6, 15, 14, 30,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
        )

    @pytest.mark.parametrize(
        "planet,planet_id,min_shift",
        [
            # Pluto ecliptic latitude ~ +15.85 deg on this date -> ~4.56 deg shift
            ("Pluto", ephe.PLUTO, 4.0),
            # Moon ecliptic latitude ~ +3.15 deg on this date -> ~1.22 deg shift
            ("Moon", ephe.MOON, 1.0),
        ],
    )
    def test_mc_line_uses_true_ra(self, acg_subject, planet, planet_id, min_shift):
        """MC line must sit on the true-RA culmination meridian, not on the
        zodiacal (beta=0) projection the pre-fix code used."""
        jd = acg_subject.julian_day
        expected = _expected_mc_lng(jd, planet_id)
        zodiacal = _zodiacal_mc_lng(jd, planet_id)

        # The two methods must actually diverge here, otherwise the test
        # would not discriminate (guards the fixture date).
        diff = abs(expected - zodiacal)
        if diff > 180:
            diff = 360 - diff
        assert diff > min_shift, (
            f"{planet}: fixture no longer discriminative ({diff=:.4f})"
        )

        lines = AstroCartographyFactory.compute(acg_subject, step=1, planets=[planet])
        mc = next(line for line in lines if line.planet == planet and line.line_type == "MC")
        assert mc.points[0].longitude == pytest.approx(expected, abs=0.01), (
            f"{planet} MC line is not on the true-RA meridian"
        )

    def test_sun_rising_line_point_is_on_horizon(self, acg_subject):
        """Independent cross-check: at a point of the Sun ASC line the Sun's
        geometric altitude (ephe.azalt) must be ~0."""
        jd = acg_subject.julian_day
        lines = AstroCartographyFactory.compute(acg_subject, step=1, planets=["Sun"])
        sun_asc = next(line for line in lines if line.planet == "Sun" and line.line_type == "ASC")
        point = next(p for p in sun_asc.points if p.latitude == 40.0)

        with ephemeris_session() as iflag:
            eq_iflag = (iflag & ~ephe.FLG_SIDEREAL) | ephe.FLG_EQUATORIAL
            ra, dec, dist = ephe.calc_ut(jd, ephe.SUN, eq_iflag)[0][:3]
            azimuth, true_alt = ephe.azalt(
                jd, ephe.EQU2HOR, (point.longitude, point.latitude, 0.0),
                0.0, 0.0, (ra, dec, dist),
            )[:2]

        assert abs(true_alt) <= 0.2, (
            f"Sun not on geometric horizon at ASC line point: alt={true_alt}"
        )
        # Rising side: azimuth east of the meridian (ephe convention: from
        # south, clockwise -> east is 180..360).
        assert 180.0 < azimuth < 360.0, f"ASC point is not on the rising side: az={azimuth}"

    def test_asc_dsc_one_point_per_latitude(self, acg_subject):
        """The horizon equation is solved exactly: each scanned latitude
        contributes at most one ASC and one DSC point (the pre-fix scan could
        also sample the -180/+180 meridian twice)."""
        lines = AstroCartographyFactory.compute(acg_subject, step=5, planets=["Sun"])
        for line_type in ("ASC", "DSC"):
            line = next(line for line in lines if line.line_type == line_type)
            latitudes = [p.latitude for p in line.points]
            assert len(latitudes) == len(set(latitudes)), f"duplicate latitude on {line_type}"


class TestACGSiderealFrameConsistency:
    """v6 pre-beta fix: ACG lines are physical (horizon/meridian crossings) and
    must not depend on the zodiac convention. Previously sidereal abs_pos was
    fed straight into tropical RA / houses_armc math, shifting every line by
    the ayanamsa."""

    def test_sidereal_acg_lines_identical_to_tropical(self):
        """LAHIRI vs tropical subject at the same instant: identical geography."""
        birth = dict(
            year=1990, month=6, day=15, hour=14, minute=30,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
        )
        tropical = AstrologicalSubjectFactory.from_birth_data("ACG Tropical", **birth)
        sidereal = AstrologicalSubjectFactory.from_birth_data(
            "ACG Lahiri", **birth, zodiac_type="Sidereal", sidereal_mode="LAHIRI"
        )
        assert sidereal.ayanamsa_value is not None and sidereal.ayanamsa_value > 20.0

        trop_lines = AstroCartographyFactory.compute(tropical, step=5, planets=["Sun", "Moon"])
        sid_lines = AstroCartographyFactory.compute(sidereal, step=5, planets=["Sun", "Moon"])

        def by_key(lines):
            return {(line.planet, line.line_type): line for line in lines}

        trop_map, sid_map = by_key(trop_lines), by_key(sid_lines)
        assert set(trop_map) == set(sid_map)

        for key, trop_line in trop_map.items():
            sid_line = sid_map[key]
            if key[1] in ("MC", "IC"):
                # Vertical lines: the single geographic longitude must match.
                assert sid_line.points[0].longitude == pytest.approx(
                    trop_line.points[0].longitude, abs=0.01
                ), f"{key}: sidereal MC/IC longitude diverges from tropical"
            else:
                # ASC/DSC scans share the same grid: identical point sets.
                trop_pts = {(p.longitude, p.latitude) for p in trop_line.points}
                sid_pts = {(p.longitude, p.latitude) for p in sid_line.points}
                assert sid_pts == trop_pts, f"{key}: sidereal line geography diverges"
