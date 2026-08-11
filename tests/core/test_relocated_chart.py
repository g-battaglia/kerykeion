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
    """Compare factory relocated ASC/MC with direct ephe.houses_armc() output."""

    def test_relocated_asc_mc_match_swe(self, natal):
        """Factory relocated ASC and MC must match raw ephe.houses_armc()."""
        from kerykeion.ephemeris_backend import ephe, EPHE_DATA_PATH
        ephe.set_ephe_path(EPHE_DATA_PATH)

        new_lat = 40.7128
        new_lng = -74.006
        relocated = RelocatedChartFactory.relocate(natal, new_lat=new_lat, new_lng=new_lng, new_city="New York")

        jd = natal.julian_day
        iflag = ephe.FLG_SWIEPH | ephe.FLG_SPEED
        hsys = natal.houses_system_identifier.encode("ascii")

        # Obliquity of ecliptic
        eps = ephe.calc_ut(jd, ephe.ECL_NUT, iflag)[0][0]

        # ARMC for new location (same logic as factory)
        armc_hours = ephe.sidtime(jd)
        local_st_hours = armc_hours + new_lng / 15.0
        armc_degrees = (local_st_hours * 15.0) % 360.0

        # Direct ephe.houses_armc call
        cusps, ascmc = ephe.houses_armc(armc_degrees, new_lat, eps, hsys)
        expected_asc = ascmc[0] % 360
        expected_mc = ascmc[1] % 360

        assert relocated.ascendant.abs_pos == pytest.approx(expected_asc, abs=0.01), (
            f"Relocated ASC {relocated.ascendant.abs_pos} != ephe ASC {expected_asc}"
        )
        assert relocated.medium_coeli.abs_pos == pytest.approx(expected_mc, abs=0.01), (
            f"Relocated MC {relocated.medium_coeli.abs_pos} != ephe MC {expected_mc}"
        )

    def test_relocated_tokyo_asc_mc_match_swe(self, natal):
        """Same check for Tokyo to ensure generalisation across locations."""
        from kerykeion.ephemeris_backend import ephe, EPHE_DATA_PATH
        ephe.set_ephe_path(EPHE_DATA_PATH)

        new_lat = 35.6895
        new_lng = 139.6917
        relocated = RelocatedChartFactory.relocate(natal, new_lat=new_lat, new_lng=new_lng, new_city="Tokyo")

        jd = natal.julian_day
        iflag = ephe.FLG_SWIEPH | ephe.FLG_SPEED
        hsys = natal.houses_system_identifier.encode("ascii")

        eps = ephe.calc_ut(jd, ephe.ECL_NUT, iflag)[0][0]
        armc_hours = ephe.sidtime(jd)
        local_st_hours = armc_hours + new_lng / 15.0
        armc_degrees = (local_st_hours * 15.0) % 360.0

        cusps, ascmc = ephe.houses_armc(armc_degrees, new_lat, eps, hsys)
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

    def test_local_date_fields_recomputed_with_new_tz_boundary(self):
        natal = AstrologicalSubjectFactory.from_iso_utc_time(
            "Timezone Boundary Subject",
            "2024-01-01T23:30:15Z",
            lng=0.0,
            lat=51.5,
            tz_str="Etc/GMT",
            city="Greenwich",
            nation="GB",
            online=False,
        )
        relocated = RelocatedChartFactory.relocate(
            natal,
            new_lat=35.6895,
            new_lng=139.6917,
            new_city="Tokyo",
            new_nation="JP",
            new_tz_str="Asia/Tokyo",
        )
        relocated_local = datetime.fromisoformat(relocated.iso_formatted_local_datetime)

        assert relocated.iso_formatted_local_datetime.startswith("2024-01-02T08:30:15")
        assert (relocated.year, relocated.month, relocated.day, relocated.hour, relocated.minute) == (
            relocated_local.year,
            relocated_local.month,
            relocated_local.day,
            relocated_local.hour,
            relocated_local.minute,
        )
        assert relocated.day_of_week == "Tuesday"

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
        """_compute_is_diurnal calls ephe.* (Sun position + azalt): relocation
        must wrap it in an ephemeris session, so no tracked ephe call may run
        after the last session reset."""
        import kerykeion.ephemeris_backend.backend as eb

        events = []
        real_reset = eb.reset_ephemeris_session
        real_azalt = eb.ephe.azalt

        def tracking_reset():
            events.append("session_reset")
            real_reset()

        def tracking_azalt(*args, **kwargs):
            events.append("azalt")
            return real_azalt(*args, **kwargs)

        monkeypatch.setattr(eb, "reset_ephemeris_session", tracking_reset)
        monkeypatch.setattr(eb.ephe, "azalt", tracking_azalt)

        RelocatedChartFactory.relocate(
            enriched_natal, new_lat=35.6895, new_lng=139.6917, new_city="Tokyo"
        )

        assert "azalt" in events, "sect recomputation (azalt) was never invoked"
        assert events[-1] == "session_reset", (
            f"ephe calls escaped the ephemeris session during relocation: {events}"
        )


class TestRelocatedLocalDatetimeRecompute:
    """Unit tests for ``_recompute_local_datetime_fields``, the pure helper that
    rebuilds the local calendar fields for a new timezone. The BCE path cannot
    be exercised through the full ``relocate()`` flow with the short-range dev
    ephemeris kernel, so the helper is tested directly (its only ephemeris call,
    ``ephe.revjul``, is pure calendar arithmetic and needs no kernel data)."""

    def test_negative_year_subject_uses_lmt_path_without_crashing(self):
        # NOTE: deliberately avoids the substring the conftest tier filter uses
        # to gate extended-kernel tests — this helper only does pure calendar
        # arithmetic (ephe.revjul/julday) and needs no ephemeris data, so it must
        # run on every tier.
        from kerykeion.ephemeris_backend import ephe
        from kerykeion.utilities import format_ancient_iso

        # Astronomical year -500. Treat this as the stored UT instant.
        jd_ut = ephe.julday(-500, 3, 21, 12.0, ephe.JUL_CAL)
        iso_utc = format_ancient_iso(-500, 3, 21, 12.0, 0.0)

        # The very string a BCE subject stores is unparseable by fromisoformat —
        # this is exactly the crash the BCE branch avoids.
        with pytest.raises(ValueError):
            datetime.fromisoformat(iso_utc)

        new_lng = 139.6917  # Tokyo
        data: dict = {}
        RelocatedChartFactory._recompute_local_datetime_fields(
            data,
            year=-500,
            julian_day=jd_ut,
            new_lng=new_lng,
            new_tz_str="Asia/Tokyo",
            iso_utc=iso_utc,
        )

        lmt_offset = new_lng / 15.0
        ey, em, ed, edh = ephe.revjul(jd_ut + lmt_offset / 24.0, ephe.JUL_CAL)
        assert data["iso_formatted_local_datetime"] == format_ancient_iso(
            int(ey), int(em), int(ed), edh, lmt_offset
        )
        assert data["iso_formatted_local_datetime"].startswith("-0500-")
        assert (data["year"], data["month"], data["day"]) == (int(ey), int(em), int(ed))

        # Integer h/m/s fields stay consistent with the ISO local string. The
        # time component is derived the same way format_ancient_iso renders it
        # (round to nearest second, carry overflow), so parse it back out of the
        # produced string and compare — this is the invariant the docstring
        # promises ("the integer fields and the ISO string agree").
        iso_local = data["iso_formatted_local_datetime"]
        date_part, time_part = iso_local[: iso_local.index("T")], iso_local[iso_local.index("T") + 1 :]
        hh, mm, ss = (int(x) for x in time_part[:8].split(":"))
        assert (data["hour"], data["minute"], data["seconds"]) == (hh, mm, ss)
        assert date_part == f"-{abs(data['year']):04d}-{data['month']:02d}-{data['day']:02d}"

    def test_negative_year_local_fields_round_and_carry_at_midnight_boundary(self):
        # A loc_dec_hour within ~0.5s of midnight must round up to 86400 and carry
        # into the next day for BOTH the integer fields and the ISO string, so the
        # two never disagree (the int()-truncation bug rendered 23:59:59 of the
        # wrong day while format_ancient_iso emitted 00:00:00 of the next day).
        from unittest.mock import patch

        new_lng = 0.0  # LMT offset 0 -> local == the revjul value we mock
        data: dict = {}
        # Mock revjul to return a value 0.4s before midnight of -0500-03-21.
        with patch(
            "kerykeion.relocated_chart.factory.ephe.revjul",
            return_value=(-500.0, 3.0, 21.0, 23.999888888),
        ):
            RelocatedChartFactory._recompute_local_datetime_fields(
                data,
                year=-500,
                julian_day=0.0,
                new_lng=new_lng,
                new_tz_str="UTC",
                iso_utc="-0500-03-21T00:00:00+00:00",
            )

        # Carries to 00:00:00 of -0500-03-22; integer fields match the ISO string.
        assert (data["hour"], data["minute"], data["seconds"]) == (0, 0, 0)
        assert (data["year"], data["month"], data["day"]) == (-500, 3, 22)
        assert data["iso_formatted_local_datetime"].startswith("-0500-03-22T00:00:00")

    def test_ce_subject_matches_stdlib_zoneinfo(self):
        # The normative reference for a CE conversion is the stdlib tz database
        # reader: the factory must not reimplement the offset lookup, only route to it.
        from zoneinfo import ZoneInfo

        iso_utc = "2024-01-01T23:30:15+00:00"
        data: dict = {}
        RelocatedChartFactory._recompute_local_datetime_fields(
            data,
            year=2024,
            julian_day=0.0,  # unused on the CE path
            new_lng=139.6917,
            new_tz_str="Asia/Tokyo",
            iso_utc=iso_utc,
        )

        expected = datetime.fromisoformat(iso_utc).astimezone(ZoneInfo("Asia/Tokyo"))
        assert data["iso_formatted_local_datetime"] == expected.isoformat()
        assert (
            data["year"],
            data["month"],
            data["day"],
            data["hour"],
            data["minute"],
            data["seconds"],
        ) == (
            expected.year,
            expected.month,
            expected.day,
            expected.hour,
            expected.minute,
            expected.second,
        )


class TestPolarRelocation:
    def test_relocation_to_polar_latitude_substitutes_like_natal(self):
        # Placidus raises PolarCircleError past ~66 deg; the natal path falls back
        # to Porphyry at the real latitude, and relocation must do the same
        # instead of crashing.
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.relocated_chart.factory import RelocatedChartFactory

        natal = AstrologicalSubjectFactory.from_birth_data(
            "Polar Move", 1990, 6, 15, 12, 0,
            lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True,
        )
        relocated = RelocatedChartFactory.relocate(natal, new_lat=78.2, new_lng=15.6)
        assert relocated.first_house is not None
        assert relocated.lat == 78.2
        assert relocated.houses_system_identifier == "P"
        assert relocated.effective_houses_system_identifier == "O"
        assert [fallback.strategy for fallback in relocated.polar_house_fallbacks] == [
            "substitute_system"
        ]

    def test_relocation_to_polar_latitude_agnostic_houses_use_real_lat(self):
        # Whole Sign is defined at every latitude: relocating a Whole Sign chart
        # to a polar latitude must use the REAL latitude for the cusps, matching
        # an independent backend call there (not the 66°-clamped one).
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.relocated_chart.factory import RelocatedChartFactory
        from kerykeion.ephemeris_backend import ephe, ephemeris_session

        natal = AstrologicalSubjectFactory.from_birth_data(
            "Polar WS", 1990, 6, 15, 12, 0,
            lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True, houses_system_identifier="W",
        )
        relocated = RelocatedChartFactory.relocate(natal, new_lat=78.2, new_lng=15.6)
        assert relocated.lat == 78.2
        with ephemeris_session() as iflag:
            _, ascmc_real, _, _ = ephe.houses_ex2(natal.julian_day, 78.2, 15.6, b"W", iflag)
            _, ascmc_66, _, _ = ephe.houses_ex2(natal.julian_day, 66.0, 15.6, b"W", iflag)
        assert abs(relocated.ascendant.abs_pos - ascmc_real[0]) < 1e-6
        assert abs(ascmc_real[0] - ascmc_66[0]) > 1.0


class TestRelocatedMidpointsRehoused:
    """Round-1 regression: active_midpoints must be re-housed on relocation."""

    def test_active_midpoints_get_new_houses(self):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.relocated_chart.factory import RelocatedChartFactory
        from kerykeion.midpoints import MidpointFactory
        from kerykeion.utilities import get_planet_house

        subj = AstrologicalSubjectFactory.from_birth_data(
            "Reloc MP", 1990, 6, 15, 12, 0, lng=-74.0, lat=40.71,
            tz_str="America/New_York", online=False, suppress_geonames_warning=True,
        )
        subj.active_midpoints = MidpointFactory.compute_active_midpoint_points(subj, ["Sun_Moon"])
        reloc = RelocatedChartFactory.relocate(
            subj, new_lat=35.68, new_lng=139.69, new_tz_str="Asia/Tokyo",
        )
        assert reloc.active_midpoints, "midpoints missing after relocation"
        house_order = [
            "first", "second", "third", "fourth", "fifth", "sixth",
            "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth",
        ]
        cusps = [getattr(reloc, f"{h}_house").abs_pos for h in house_order]
        for mp in reloc.active_midpoints:
            assert mp.house == get_planet_house(mp.abs_pos, cusps), (
                f"{mp.name} kept a stale natal house after relocation"
            )


class TestRelocatedDerivedOppositesRehoused:
    """Round-2 regression: derived opposite points absent from active_points
    (South lunar nodes, Priapus) must be re-housed on relocation, not left
    with a stale natal house."""

    def test_south_node_rehoused(self):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.relocated_chart.factory import RelocatedChartFactory
        from kerykeion.utilities import get_planet_house

        s = AstrologicalSubjectFactory.from_birth_data(
            "John", 1990, 6, 15, 14, 30, lng=-74.0, lat=40.7,
            tz_str="America/New_York", online=False, suppress_geonames_warning=True,
        )
        r = RelocatedChartFactory.relocate(
            s, new_lat=-33.9, new_lng=151.2, new_tz_str="Australia/Sydney",
        )
        order = ["first", "second", "third", "fourth", "fifth", "sixth",
                 "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth"]
        cusps = [getattr(r, f"{h}_house").abs_pos for h in order]
        south = r.true_south_lunar_node
        assert south.house == get_planet_house(south.abs_pos, cusps)
        # north and south nodes must remain in opposite houses
        assert r.true_north_lunar_node.house != south.house


class TestRelocateBirthplaceExactNoOpRound11:
    """Round-11 regression: relocating to one's own birthplace must be an EXACT
    house no-op. The old ARMC reconstruction from ephe.sidtime drifted ~arcsec
    (amplified at high latitude / far from J2000); houses_ex2 computes the ARMC
    internally and reproduces the natal cusps exactly."""

    _HO = ["first", "second", "third", "fourth", "fifth", "sixth",
           "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth"]

    def _drift(self, natal, reloc):
        m = 0.0
        for h in self._HO:
            d = abs((getattr(reloc, f"{h}_house").abs_pos - getattr(natal, f"{h}_house").abs_pos + 180) % 360 - 180)
            m = max(m, d)
        return m

    def test_tropical_high_latitude_exact(self):
        natal = AstrologicalSubjectFactory.from_birth_data(
            "N", 2131, 8, 13, 20, 55, lng=-10.6457, lat=65.4251, tz_str="Etc/GMT",
            online=False, houses_system_identifier="R")
        reloc = RelocatedChartFactory.relocate(natal, 65.4251, -10.6457, "same")
        assert self._drift(natal, reloc) < 1e-8

    def test_sidereal_exact(self):
        natal = AstrologicalSubjectFactory.from_birth_data(
            "S", 1990, 6, 15, 14, 30, lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, zodiac_type="Sidereal", sidereal_mode="LAHIRI")
        reloc = RelocatedChartFactory.relocate(natal, 41.9, 12.5, "same")
        assert self._drift(natal, reloc) < 1e-8


class TestRelocateNormalizesLongitudeCodeRabbit:
    """CodeRabbit P2: relocate() must accept an un-normalized longitude (370,
    -190) like the natal path, not leak a raw backend CoordinateError."""

    def test_wrapped_longitude_matches_normalized(self):
        natal = AstrologicalSubjectFactory.from_birth_data(
            "N", 1990, 6, 15, 14, 30, lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True)
        r_wrapped = RelocatedChartFactory.relocate(natal, 41.9, 370.0, "X")
        r_norm = RelocatedChartFactory.relocate(natal, 41.9, 10.0, "X")
        assert r_wrapped.lng == 10.0
        assert abs(r_wrapped.ascendant.abs_pos - r_norm.ascendant.abs_pos) < 1e-9

    def test_negative_wrapped_longitude(self):
        natal = AstrologicalSubjectFactory.from_birth_data(
            "N", 1990, 6, 15, 14, 30, lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True)
        r = RelocatedChartFactory.relocate(natal, 41.9, -190.0, "X")
        assert r.lng == 170.0


class TestRelocateTopocentricRejected:
    """Topocentric subjects cannot be relocated coherently: the planetary
    positions embed the natal observer's parallax, so relocate() must refuse
    instead of returning a chart whose planets still describe the birthplace."""

    def test_topocentric_subject_raises(self):
        from kerykeion.schemas import KerykeionException

        topo = AstrologicalSubjectFactory.from_birth_data(
            "Topo Subject", 1990, 6, 15, 14, 30,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
            perspective_type="Topocentric",
        )
        with pytest.raises(KerykeionException, match="[Tt]opocentric"):
            RelocatedChartFactory.relocate(
                topo, new_lat=40.7128, new_lng=-74.006, new_city="New York"
            )


class TestRelocateExtremeYearBoundary:
    """Round 27: relocating a near-datetime.max/min subject to a timezone whose
    offset pushes the local wall time past datetime's representable range must
    surface as KerykeionException (raw OverflowError before), matching the ISO
    entry points' contract. Uses model_copy to stand in for an extended-kernel
    year-9999 / year-1 subject the default test kernel cannot construct; the
    astimezone conversion at the fix site is kernel-independent."""

    @pytest.mark.parametrize(
        "year, iso_utc, jd_dt, new_tz_str",
        [
            (9999, "9999-12-31T23:59:59+00:00", (9999, 12, 31, 23, 59, 59), "Etc/GMT-14"),
            (1, "0001-01-01T00:00:00+00:00", (1, 1, 1, 0, 0, 0), "Etc/GMT+12"),
        ],
    )
    def test_extreme_year_relocation_raises_kerykeion(self, year, iso_utc, jd_dt, new_tz_str):
        from datetime import datetime, timezone
        from kerykeion.schemas import KerykeionException
        from kerykeion.utilities import datetime_to_julian

        base = AstrologicalSubjectFactory.from_birth_data(
            "B", 2000, 6, 15, 12, 0, lng=0.0, lat=41.9, tz_str="UTC",
            city="X", nation="XX", online=False, suppress_geonames_warning=True,
        )
        edge = base.model_copy(update=dict(
            year=year,
            julian_day=datetime_to_julian(datetime(*jd_dt, tzinfo=timezone.utc)),
            iso_formatted_utc_datetime=iso_utc,
            iso_formatted_local_datetime=iso_utc,
            tz_str="UTC",
        ))
        with pytest.raises(KerykeionException):
            RelocatedChartFactory.relocate(
                edge, new_lat=0.0, new_lng=0.0, new_city="K", new_nation="KI",
                new_tz_str=new_tz_str,
            )
