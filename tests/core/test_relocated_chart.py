# -*- coding: utf-8 -*-
"""Tests for the Relocated Chart factory."""

from datetime import datetime

import pytest
from kerykeion import AstrologicalSubjectFactory, RelocatedChartFactory
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS


def _angular_diff(a: float, b: float) -> float:
    diff = abs(a - b) % 360.0
    return min(diff, 360.0 - diff)


@pytest.fixture(scope="module")
def natal():
    return AstrologicalSubjectFactory.from_birth_data(
        "Test Subject", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
    )


@pytest.fixture(scope="module")
def sidereal_natal():
    return AstrologicalSubjectFactory.from_birth_data(
        "Sidereal Subject", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
        zodiac_type="Sidereal", sidereal_mode="LAHIRI",
    )


@pytest.fixture(scope="module")
def natal_with_derived_points():
    """Natal with Vertex / Anti-Vertex / Arabic parts active."""
    extra = ["Vertex", "Anti_Vertex", "Pars_Fortunae", "Pars_Spiritus"]
    points = list(DEFAULT_ACTIVE_POINTS) + [p for p in extra if p not in DEFAULT_ACTIVE_POINTS]
    return AstrologicalSubjectFactory.from_birth_data(
        "Derived Points Subject", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
        active_points=points,
    )


class TestRelocatedChart:
    def test_planets_unchanged(self, natal):
        relocated = RelocatedChartFactory.relocate(natal, new_lat=40.7128, new_lng=-74.006, new_city="New York")
        assert abs(relocated.sun.abs_pos - natal.sun.abs_pos) < 0.001
        assert abs(relocated.moon.abs_pos - natal.moon.abs_pos) < 0.001
        assert abs(relocated.mars.abs_pos - natal.mars.abs_pos) < 0.001

    def test_houses_changed(self, natal):
        relocated = RelocatedChartFactory.relocate(natal, new_lat=40.7128, new_lng=-74.006, new_city="New York")
        # With such a large longitude difference, houses should differ significantly
        assert abs(relocated.ascendant.abs_pos - natal.ascendant.abs_pos) > 1.0

    def test_city_updated(self, natal):
        relocated = RelocatedChartFactory.relocate(natal, new_lat=40.7128, new_lng=-74.006, new_city="New York", new_nation="US")
        assert relocated.city == "New York"
        assert relocated.nation == "US"
        assert relocated.lat == 40.7128
        assert relocated.lng == -74.006

    def test_same_julian_day(self, natal):
        relocated = RelocatedChartFactory.relocate(natal, new_lat=51.5, new_lng=-0.1, new_city="London")
        assert relocated.julian_day == natal.julian_day

    def test_relocate_to_same_location_preserves_houses(self, natal):
        relocated = RelocatedChartFactory.relocate(natal, new_lat=natal.lat, new_lng=natal.lng)
        # Houses should be very similar (small numerical differences possible)
        assert abs(relocated.ascendant.abs_pos - natal.ascendant.abs_pos) < 0.5

    def test_all_houses_present(self, natal):
        relocated = RelocatedChartFactory.relocate(natal, new_lat=35.6895, new_lng=139.6917, new_city="Tokyo")
        for attr in ["first_house", "second_house", "third_house", "fourth_house",
                      "fifth_house", "sixth_house", "seventh_house", "eighth_house",
                      "ninth_house", "tenth_house", "eleventh_house", "twelfth_house"]:
            house = getattr(relocated, attr)
            assert house is not None
            assert 0 <= house.abs_pos < 360


class TestRelocatedSweReference:
    """Compare factory relocated ASC/MC with direct swe.houses_armc() output."""

    def test_relocated_asc_mc_match_swe(self, natal):
        """Factory relocated ASC and MC must match raw swe.houses_armc()."""
        from kerykeion.ephemeris_backend import swe, EPHE_DATA_PATH
        swe.set_ephe_path(EPHE_DATA_PATH)

        new_lat = 40.7128
        new_lng = -74.006
        relocated = RelocatedChartFactory.relocate(natal, new_lat=new_lat, new_lng=new_lng, new_city="New York")

        jd = natal.julian_day
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED
        hsys = natal.houses_system_identifier.encode("ascii")

        # Obliquity of ecliptic
        eps = swe.calc_ut(jd, swe.ECL_NUT, iflag)[0][0]

        # ARMC for new location (same logic as factory)
        armc_hours = swe.sidtime(jd)
        local_st_hours = armc_hours + new_lng / 15.0
        armc_degrees = (local_st_hours * 15.0) % 360.0

        # Direct swe.houses_armc call
        cusps, ascmc = swe.houses_armc(armc_degrees, new_lat, eps, hsys)
        expected_asc = ascmc[0] % 360
        expected_mc = ascmc[1] % 360

        assert relocated.ascendant.abs_pos == pytest.approx(expected_asc, abs=0.01), (
            f"Relocated ASC {relocated.ascendant.abs_pos} != swe ASC {expected_asc}"
        )
        assert relocated.medium_coeli.abs_pos == pytest.approx(expected_mc, abs=0.01), (
            f"Relocated MC {relocated.medium_coeli.abs_pos} != swe MC {expected_mc}"
        )

    def test_relocated_tokyo_asc_mc_match_swe(self, natal):
        """Same check for Tokyo to ensure generalisation across locations."""
        from kerykeion.ephemeris_backend import swe, EPHE_DATA_PATH
        swe.set_ephe_path(EPHE_DATA_PATH)

        new_lat = 35.6895
        new_lng = 139.6917
        relocated = RelocatedChartFactory.relocate(natal, new_lat=new_lat, new_lng=new_lng, new_city="Tokyo")

        jd = natal.julian_day
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED
        hsys = natal.houses_system_identifier.encode("ascii")

        eps = swe.calc_ut(jd, swe.ECL_NUT, iflag)[0][0]
        armc_hours = swe.sidtime(jd)
        local_st_hours = armc_hours + new_lng / 15.0
        armc_degrees = (local_st_hours * 15.0) % 360.0

        cusps, ascmc = swe.houses_armc(armc_degrees, new_lat, eps, hsys)
        expected_asc = ascmc[0] % 360
        expected_mc = ascmc[1] % 360

        assert relocated.ascendant.abs_pos == pytest.approx(expected_asc, abs=0.01)
        assert relocated.medium_coeli.abs_pos == pytest.approx(expected_mc, abs=0.01)


class TestRelocatedSiderealIdentity:
    """v6 regression: houses_armc returns TROPICAL cusps — sidereal charts
    must be shifted by the ayanamsa, otherwise relocating a sidereal chart to
    its own birthplace moves the ASC by ~24°."""

    def test_tropical_identity(self, natal):
        relocated = RelocatedChartFactory.relocate(natal, new_lat=natal.lat, new_lng=natal.lng)
        assert _angular_diff(relocated.ascendant.abs_pos, natal.ascendant.abs_pos) < 1e-6

    def test_sidereal_identity(self, sidereal_natal):
        relocated = RelocatedChartFactory.relocate(
            sidereal_natal, new_lat=sidereal_natal.lat, new_lng=sidereal_natal.lng
        )
        assert _angular_diff(relocated.ascendant.abs_pos, sidereal_natal.ascendant.abs_pos) < 1e-6, (
            "Relocating a sidereal chart to its birthplace must keep the natal ASC "
            "(ayanamsa not subtracted from houses_armc output)"
        )

    def test_sidereal_identity_all_cusps(self, sidereal_natal):
        relocated = RelocatedChartFactory.relocate(
            sidereal_natal, new_lat=sidereal_natal.lat, new_lng=sidereal_natal.lng
        )
        for attr in ["first_house", "fourth_house", "seventh_house", "tenth_house",
                     "medium_coeli", "descendant", "imum_coeli"]:
            natal_pos = getattr(sidereal_natal, attr).abs_pos
            relocated_pos = getattr(relocated, attr).abs_pos
            assert _angular_diff(relocated_pos, natal_pos) < 1e-5, f"{attr} moved on identity relocation"

    def test_sidereal_offset_matches_ayanamsa(self, natal, sidereal_natal):
        """Sidereal relocated ASC = tropical relocated ASC - ayanamsa."""
        tropical = RelocatedChartFactory.relocate(natal, new_lat=40.7128, new_lng=-74.006)
        sidereal = RelocatedChartFactory.relocate(sidereal_natal, new_lat=40.7128, new_lng=-74.006)
        assert sidereal_natal.ayanamsa_value is not None
        expected = (tropical.ascendant.abs_pos - sidereal_natal.ayanamsa_value) % 360.0
        assert _angular_diff(sidereal.ascendant.abs_pos, expected) < 1e-5


class TestRelocatedDerivedPoints:
    """v6: Vertex/Anti-Vertex, Arabic parts, axis houses and the local
    datetime are location-dependent and must be refreshed on relocation."""

    def test_vertex_identity(self, natal_with_derived_points):
        subj = natal_with_derived_points
        relocated = RelocatedChartFactory.relocate(subj, new_lat=subj.lat, new_lng=subj.lng)
        assert _angular_diff(relocated.vertex.abs_pos, subj.vertex.abs_pos) < 1e-4
        assert _angular_diff(relocated.anti_vertex.abs_pos, subj.anti_vertex.abs_pos) < 1e-4

    def test_vertex_changes_on_relocation(self, natal_with_derived_points):
        subj = natal_with_derived_points
        relocated = RelocatedChartFactory.relocate(subj, new_lat=40.7128, new_lng=-74.006, new_city="New York")
        assert _angular_diff(relocated.vertex.abs_pos, subj.vertex.abs_pos) > 1.0, (
            "Vertex is location-dependent: it must move with the relocation"
        )
        # Anti-Vertex stays opposite the Vertex
        assert _angular_diff(relocated.anti_vertex.abs_pos, (relocated.vertex.abs_pos + 180.0) % 360.0) < 1e-9

    def test_arabic_parts_identity(self, natal_with_derived_points):
        subj = natal_with_derived_points
        relocated = RelocatedChartFactory.relocate(subj, new_lat=subj.lat, new_lng=subj.lng)
        assert _angular_diff(relocated.pars_fortunae.abs_pos, subj.pars_fortunae.abs_pos) < 1e-4
        assert _angular_diff(relocated.pars_spiritus.abs_pos, subj.pars_spiritus.abs_pos) < 1e-4

    def test_arabic_parts_follow_new_ascendant(self, natal_with_derived_points):
        """Pars Fortunae uses the ASC: it must be recomputed for the new location."""
        subj = natal_with_derived_points
        relocated = RelocatedChartFactory.relocate(subj, new_lat=40.7128, new_lng=-74.006, new_city="New York")
        assert _angular_diff(relocated.pars_fortunae.abs_pos, subj.pars_fortunae.abs_pos) > 1.0

        # Verify the day/night formula with the recomputed sect:
        asc = relocated.ascendant.abs_pos
        sun = relocated.sun.abs_pos
        moon = relocated.moon.abs_pos
        if relocated.is_diurnal:
            expected = (asc + moon - sun) % 360.0
        else:
            expected = (asc + sun - moon) % 360.0
        assert _angular_diff(relocated.pars_fortunae.abs_pos, expected) < 1e-9

    def test_sect_recomputed_for_new_location(self, natal_with_derived_points):
        """14:30 local in Rome is day; the same instant in Tokyo (21:30 local) is night."""
        subj = natal_with_derived_points
        assert subj.is_diurnal is True
        relocated = RelocatedChartFactory.relocate(
            subj, new_lat=35.6895, new_lng=139.6917, new_city="Tokyo", new_tz_str="Asia/Tokyo"
        )
        assert relocated.is_diurnal is False, (
            "Sun below the horizon in Tokyo at the same UT instant: sect must flip"
        )

    def test_axes_have_house_populated(self, natal_with_derived_points):
        subj = natal_with_derived_points
        relocated = RelocatedChartFactory.relocate(subj, new_lat=40.7128, new_lng=-74.006, new_city="New York")
        for attr in ["ascendant", "medium_coeli", "descendant", "imum_coeli", "vertex", "anti_vertex"]:
            point = getattr(relocated, attr)
            assert point.house is not None, f"{attr} missing house assignment after relocation"

    def test_local_datetime_recomputed_with_new_tz(self, natal):
        relocated = RelocatedChartFactory.relocate(
            natal, new_lat=40.7128, new_lng=-74.006, new_city="New York", new_tz_str="America/New_York"
        )
        natal_local = datetime.fromisoformat(natal.iso_formatted_local_datetime)
        relocated_local = datetime.fromisoformat(relocated.iso_formatted_local_datetime)
        # Same UTC instant, different wall-clock representation
        assert relocated_local.utcoffset() != natal_local.utcoffset()
        assert relocated_local.astimezone(natal_local.tzinfo) == natal_local

    def test_local_datetime_kept_without_new_tz(self, natal):
        relocated = RelocatedChartFactory.relocate(natal, new_lat=40.7128, new_lng=-74.006, new_city="New York")
        assert relocated.iso_formatted_local_datetime == natal.iso_formatted_local_datetime


class TestRelocatedStaleLocationFields:
    """v6: per-point local-space/Gauquelin enrichments and the Gauquelin
    sector cusps were computed for the NATAL horizon; relocation must null
    them (honest "not computed") instead of carrying stale natal values."""

    @pytest.fixture(scope="class")
    def enriched_natal(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "Enriched Subject", 1990, 6, 15, 14, 30,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
            calculate_gauquelin=True, calculate_local_space=True,
        )

    def test_natal_has_location_dependent_enrichments(self, enriched_natal):
        """Sanity check: the natal subject actually carries the enrichments."""
        assert enriched_natal.sun.gauquelin_sector is not None
        assert enriched_natal.sun.azimuth is not None
        assert enriched_natal.sun.altitude_above_horizon is not None
        assert enriched_natal.gauquelin_sector_cusps is not None

    def test_location_dependent_fields_nulled_on_relocation(self, enriched_natal):
        relocated = RelocatedChartFactory.relocate(
            enriched_natal, new_lat=40.7128, new_lng=-74.006, new_city="New York"
        )
        for attr in ["sun", "moon", "mercury", "venus", "mars", "ascendant", "first_house"]:
            point = getattr(relocated, attr)
            assert point.gauquelin_sector is None, f"{attr} carries a stale natal gauquelin_sector"
            assert point.azimuth is None, f"{attr} carries a stale natal azimuth"
            assert point.altitude_above_horizon is None, (
                f"{attr} carries a stale natal altitude_above_horizon"
            )
        assert relocated.gauquelin_sector_cusps is None

    def test_relocated_sect_swe_calls_run_inside_session(self, enriched_natal, monkeypatch):
        """_compute_is_diurnal calls swe.* (Sun position + azalt): relocation
        must wrap it in an ephemeris session, so no tracked swe call may run
        after the last session reset."""
        import kerykeion.ephemeris_backend as eb

        events = []
        real_reset = eb.reset_ephemeris_session
        real_azalt = eb.swe.azalt

        def tracking_reset():
            events.append("session_reset")
            real_reset()

        def tracking_azalt(*args, **kwargs):
            events.append("azalt")
            return real_azalt(*args, **kwargs)

        monkeypatch.setattr(eb, "reset_ephemeris_session", tracking_reset)
        monkeypatch.setattr(eb.swe, "azalt", tracking_azalt)

        RelocatedChartFactory.relocate(
            enriched_natal, new_lat=35.6895, new_lng=139.6917, new_city="Tokyo"
        )

        assert "azalt" in events, "sect recomputation (azalt) was never invoked"
        assert events[-1] == "session_reset", (
            f"swe calls escaped the ephemeris session during relocation: {events}"
        )
