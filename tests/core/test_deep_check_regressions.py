"""
Regression tests for the pre-beta deep-check findings.

Each test pins a fix from the adversarial verification round:
frame-correctness of local-space and Gauquelin cusps for sidereal charts,
double-DST fold handling in from_iso_utc_time, fold-safe from_current_time,
and relocation recomputing every location/timezone-dependent field.
"""

from __future__ import annotations

import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion.dignities import calculate_essential_dignity
from kerykeion.relocated_chart.factory import RelocatedChartFactory

_ROME = dict(lng=12.49, lat=41.89, tz_str="Europe/Rome", online=False)


class TestSiderealPhysicalFrames:
    """Azimuth/altitude and Gauquelin cusps are physical/mundane quantities:
    they must not move with the zodiac convention."""

    @pytest.fixture(scope="class")
    def pair(self):
        kw = dict(calculate_local_space=True, calculate_gauquelin=True, **_ROME)
        tropical = AstrologicalSubjectFactory.from_birth_data("t", 1990, 6, 15, 10, 30, **kw)
        sidereal = AstrologicalSubjectFactory.from_birth_data(
            "s", 1990, 6, 15, 10, 30, zodiac_type="Sidereal", sidereal_mode="LAHIRI", **kw
        )
        return tropical, sidereal

    def test_azimuth_is_zodiac_independent(self, pair):
        tropical, sidereal = pair
        # Pre-fix the sidereal azimuth described a point ~ayanamsa (24 deg)
        # away from the physical body (measured 20.2 vs 316.1 for the Sun).
        for pname in ("sun", "moon", "mars"):
            t, s = getattr(tropical, pname), getattr(sidereal, pname)
            assert abs(t.azimuth - s.azimuth) < 0.01, pname
            assert abs(t.altitude_above_horizon - s.altitude_above_horizon) < 0.01, pname

    def test_gauquelin_cusps_follow_subject_frame(self, pair):
        tropical, sidereal = pair
        ayanamsa = sidereal.ayanamsa_value
        assert ayanamsa is not None and ayanamsa > 20.0
        for t_cusp, s_cusp in zip(tropical.gauquelin_sector_cusps, sidereal.gauquelin_sector_cusps):
            delta = (t_cusp - s_cusp - ayanamsa) % 360.0
            assert min(delta, 360.0 - delta) < 0.01

    def test_gauquelin_sector_is_zodiac_independent(self, pair):
        tropical, sidereal = pair
        assert tropical.sun.gauquelin_sector == pytest.approx(sidereal.sun.gauquelin_sector, abs=1e-3)


class TestUtcEntryPointFolds:
    def test_modern_fold_both_sides(self):
        a = AstrologicalSubjectFactory.from_iso_utc_time("a", "2024-10-27T00:30:00Z", **_ROME)
        b = AstrologicalSubjectFactory.from_iso_utc_time("b", "2024-10-27T01:30:00Z", **_ROME)
        assert (b.julian_day - a.julian_day) * 24.0 == pytest.approx(1.0, abs=1e-6)

    def test_double_dst_fold_resolves_to_exact_instant(self):
        # UK double summer time (1941-1947): both fold occurrences are DST, so a
        # boolean is_dst cannot disambiguate them at all. from_iso_utc_time passes
        # the resolved UTC offset down directly (not a boolean is_dst), so it
        # reconstructs the exact source instant instead of raising or landing an
        # hour off. Same mechanism fixes the standard-offset-change folds
        # (UK 1971 BST->GMT, Portugal 1976).
        from kerykeion.utilities import datetime_to_julian
        from datetime import datetime, timezone

        subject = AstrologicalSubjectFactory.from_iso_utc_time(
            "c", "1947-08-10T01:30:00Z", tz_str="Europe/London", lng=-0.12, lat=51.5, online=False
        )
        expected = datetime_to_julian(datetime(1947, 8, 10, 1, 30, 0, tzinfo=timezone.utc))
        assert abs(subject.julian_day - expected) < 2 / 86400.0

    def test_double_dst_day_unambiguous_time_works(self):
        subject = AstrologicalSubjectFactory.from_iso_utc_time(
            "d", "1947-08-10T12:00:00Z", tz_str="Europe/London", lng=-0.12, lat=51.5, online=False
        )
        assert subject.julian_day == pytest.approx(2432408.0, abs=1e-6)

    def test_from_current_time_with_explicit_tz(self):
        # Renders the current instant in the requested zone (fold-safe);
        # previously the system wall clock was reinterpreted in tz_str.
        subject = AstrologicalSubjectFactory.from_current_time(
            "now", tz_str="Pacific/Auckland", lng=174.76, lat=-36.85, online=False
        )
        assert subject.tz_str == "Pacific/Auckland"


class TestRelocationConsistency:
    @pytest.fixture(scope="class")
    def relocated_pair(self):
        natal = AstrologicalSubjectFactory.from_birth_data(
            "r",
            1990,
            6,
            11,
            23,
            30,
            calculate_dignities=True,
            active_fixed_stars=["Regulus", "Spica"],
            **_ROME,
        )
        relocated = RelocatedChartFactory.relocate(
            natal, new_lat=-36.85, new_lng=174.76, new_city="Auckland", new_tz_str="Pacific/Auckland"
        )
        return natal, relocated

    def test_day_of_week_follows_local_calendar(self, relocated_pair):
        natal, relocated = relocated_pair
        assert natal.day_of_week == "Monday"
        # Rome Mon 23:30 is already Tue 09:30 in Auckland.
        assert relocated.day_of_week == "Tuesday"
        assert relocated.iso_formatted_local_datetime.startswith("1990-06-12")

    def test_dignities_recomputed_for_relocated_sect(self, relocated_pair):
        natal, relocated = relocated_pair
        assert natal.is_diurnal != relocated.is_diurnal
        for pname in ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"):
            point = getattr(relocated, pname)
            expected = calculate_essential_dignity(
                planet_name=point.name,
                sign=point.sign,
                element=point.element,
                position=point.position,
                is_diurnal=relocated.is_diurnal,
            )
            assert point.essential_dignity == expected["essential_dignity"], pname
            assert point.dignity_score == expected["dignity_score"], pname

    def test_fixed_star_houses_reassigned(self, relocated_pair):
        natal, relocated = relocated_pair
        from kerykeion.utilities import get_houses_list, get_planet_house

        cusps = [h.abs_pos for h in get_houses_list(relocated)]
        for star in relocated.fixed_stars:
            assert star.house == get_planet_house(star.abs_pos, cusps), star.name
