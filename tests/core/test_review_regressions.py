"""Regression tests for the fresh full-codebase review campaign.

Every test here pins a defect that was reproduced by execution before being
fixed. Each one fails on the pre-fix code.

The two `test_guard_*` tests exist because the guards they cover had no test at
all: deleting the guard left the suite green, which is how the defects survived
earlier review rounds.
"""

import math

import pytest

from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    DominantsFactory,
)
from kerykeion.charts.drawer import ChartDrawer
from kerykeion.charts.draw_planets import draw_planets
from kerykeion.schemas import KerykeionException


@pytest.fixture(scope="module")
def rome_subject():
    return AstrologicalSubjectFactory.from_birth_data(
        name="Review Subject", year=1990, month=6, day=15, hour=14, minute=30,
        lng=12.5, lat=41.9, tz_str="Europe/Rome", city="Rome", nation="IT",
        online=False, suppress_geonames_warning=True,
    )


class TestAlmutenScoreBreakdownContract:
    """`include_score_breakdown=False` must leave score_breakdown empty.

    The essential-dignity loop guarded its appends with the flag, but
    _add_accidental_dignities appended unconditionally, so enabling accidental
    dignities silently populated the audit trail the caller had opted out of.
    """

    @staticmethod
    def _almuten(subject, include_score_breakdown):
        return DominantsFactory.from_subject(
            subject, strategy="almuten_figuris",
            include_accidental_dignities=True,
            include_score_breakdown=include_score_breakdown,
        )

    def test_breakdown_suppressed_when_flag_off(self, rome_subject):
        assert self._almuten(rome_subject, False).score_breakdown == []

    def test_breakdown_present_when_flag_on(self, rome_subject):
        assert self._almuten(rome_subject, True).score_breakdown

    def test_scores_identical_regardless_of_flag(self, rome_subject):
        off = [(p.name, p.score) for p in self._almuten(rome_subject, False).planets]
        on = [(p.name, p.score) for p in self._almuten(rome_subject, True).planets]
        assert off == on, "the audit-trail flag must not change the scores"


class TestAstronomicalYearZeroIsoFormat:
    """Astronomical year 0 (1 BCE) must render as '0000', never '-0000'.

    Both formatters in the secondary-progressions factory tested `year > 0`,
    sending year 0 down the negative branch. The sibling formatter in
    _predictive_utils tests `year < 0` and was always right.
    """

    # JD 1721223.5 -> astronomical year 0 in the Julian calendar.
    JD_YEAR_ZERO = 1721223.5

    def test_jd_to_utc_iso_has_no_spurious_minus(self):
        from kerykeion.secondary_progressions.factory import (
            SecondaryProgressionFactory,
        )

        iso = SecondaryProgressionFactory._jd_to_utc_iso(self.JD_YEAR_ZERO)
        assert not iso.startswith("-"), iso
        assert iso.startswith("0000-"), iso

    def test_jd_to_date_label_has_no_spurious_minus(self):
        from kerykeion.secondary_progressions.factory import (
            SecondaryProgressionFactory,
        )

        label = SecondaryProgressionFactory._jd_to_date_label(self.JD_YEAR_ZERO)
        assert label.startswith("0000-"), label

    def test_negative_years_keep_their_minus(self):
        from kerykeion.secondary_progressions.factory import (
            SecondaryProgressionFactory,
        )

        # ~1 year earlier: astronomical year -1 (2 BCE).
        iso = SecondaryProgressionFactory._jd_to_utc_iso(self.JD_YEAR_ZERO - 366)
        assert iso.startswith("-0001-"), iso

    def test_matches_sibling_formatter_sign_convention(self):
        from kerykeion._predictive_utils import jd_to_iso_utc
        from kerykeion.secondary_progressions.factory import (
            SecondaryProgressionFactory,
        )

        for jd in (self.JD_YEAR_ZERO, self.JD_YEAR_ZERO - 366, 2451545.0):
            sibling_negative = jd_to_iso_utc(jd).startswith("-")
            ours_negative = SecondaryProgressionFactory._jd_to_utc_iso(jd).startswith("-")
            assert sibling_negative == ours_negative, f"sign disagreement at jd={jd}"


class TestFixedStarEnrichment:
    """Fixed stars must receive the frame-independent enrichments.

    They live in a list under calc_data["fixed_stars"], not as KerykeionPointModel
    values of calc_data, so the enrichment loops (which iterate point_keys) skipped
    them entirely and every field stayed None.
    """

    @staticmethod
    def _with_algol(**kwargs):
        return AstrologicalSubjectFactory.from_birth_data(
            name="fs", year=1990, month=6, day=15, hour=14, minute=30,
            lng=12.5, lat=41.9, tz_str="Europe/Rome", city="Rome", nation="IT",
            online=False, suppress_geonames_warning=True,
            active_fixed_stars=["Algol"], **kwargs,
        )

    def test_local_space_and_gauquelin_and_oob_are_populated(self):
        subject = self._with_algol(calculate_local_space=True, calculate_gauquelin=True)
        algol = subject.fixed_stars[0]
        assert algol.name == "Algol"
        assert algol.azimuth is not None
        assert algol.altitude_above_horizon is not None
        assert algol.gauquelin_sector is not None
        assert 1.0 <= algol.gauquelin_sector <= 37.0

    def test_algol_is_out_of_bounds(self):
        """Algol's declination (~+40.9°) far exceeds the obliquity (~23.44°)."""
        subject = self._with_algol(calculate_local_space=True)
        algol = subject.fixed_stars[0]
        assert abs(algol.declination) > 24.0, algol.declination
        assert algol.is_out_of_bounds is True

    def test_nakshatra_is_populated_on_sidereal_charts(self):
        subject = self._with_algol(
            zodiac_type="Sidereal", sidereal_mode="LAHIRI", calculate_nakshatra=True
        )
        assert subject.fixed_stars[0].nakshatra is not None

    def test_ordinary_points_still_enriched(self):
        subject = self._with_algol(calculate_local_space=True, calculate_gauquelin=True)
        assert subject.moon.azimuth is not None
        assert subject.moon.gauquelin_sector is not None
        assert subject.moon.is_out_of_bounds is False

    def test_stars_absent_when_not_requested(self):
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="fs", year=1990, month=6, day=15, hour=14, minute=30,
            lng=12.5, lat=41.9, tz_str="Europe/Rome", city="Rome", nation="IT",
            online=False, suppress_geonames_warning=True, calculate_local_space=True,
        )
        assert subject.fixed_stars == []


class TestDrawPlanetsIndicatorBounds:
    """The two indicator helpers must bound their loop by the shortest list.

    Every sibling helper computes `n = min(len(...), len(...))`; these two
    iterated `range(len(points_settings))` and indexed points_abs_positions.
    """

    def test_settings_longer_than_points_does_not_raise(self, rome_subject):
        drawer = ChartDrawer(ChartDataFactory.create_natal_chart_data(rome_subject))
        points = drawer.available_kerykeion_celestial_points
        settings = list(drawer.available_planets_setting)
        oversized = settings + settings[:2]
        assert len(oversized) > len(points)

        svg = draw_planets(
            radius=240,
            available_kerykeion_celestial_points=points,
            available_planets_setting=oversized,
            third_circle_radius=200,
            main_subject_first_house_degree_ut=rome_subject.first_house.abs_pos,
            main_subject_seventh_house_degree_ut=rome_subject.seventh_house.abs_pos,
            chart_type="Natal",
            show_degree_indicators=True,
            first_circle_radius=200,
        )
        assert "<g" in svg


class TestReportHumanizesProjectedHouse:
    """The cusp-in-house table rendered the raw enum name ('First_House')."""

    def test_projected_house_name_has_no_underscore(self, rome_subject):
        from kerykeion.house_comparison import HouseComparisonFactory
        from kerykeion.report import ReportGenerator

        second = AstrologicalSubjectFactory.from_birth_data(
            name="Other", year=1985, month=3, day=2, hour=8, minute=15,
            lng=9.19, lat=45.46, tz_str="Europe/Rome", city="Milan", nation="IT",
            online=False, suppress_geonames_warning=True,
        )
        comparison = HouseComparisonFactory(rome_subject, second).get_house_comparison()
        table = ReportGenerator(rome_subject)._render_cusp_in_house_table(
            comparison.first_cusps_in_second_houses, "Cusps"
        )
        assert "_House" not in table, table[:400]
        assert "House)" in table


class TestGuardLunarPhaseIndexLowerBound:
    """`_get_lunar_phase_index` guards `phase < 1`; nothing tested it.

    Deleting the guard let sub-1 phases fall into the `phase < 7` branch and
    silently return 'Waxing Crescent' instead of raising.
    """

    @pytest.mark.parametrize("phase", [0, -1, -28])
    def test_below_range_raises(self, phase):
        from kerykeion.utilities import get_moon_phase_name_from_phase_int

        with pytest.raises(KerykeionException):
            get_moon_phase_name_from_phase_int(phase)

    @pytest.mark.parametrize("phase", [0, -1])
    def test_below_range_raises_for_emoji_helper(self, phase):
        from kerykeion.utilities import get_moon_emoji_from_phase_int

        with pytest.raises(KerykeionException):
            get_moon_emoji_from_phase_int(phase)

    def test_valid_bounds_still_resolve(self):
        from kerykeion.utilities import get_moon_phase_name_from_phase_int

        assert get_moon_phase_name_from_phase_int(1)
        assert get_moon_phase_name_from_phase_int(28)


class TestGuardAspectOrbValidation:
    """`build_aspect_settings` rejects non-finite and negative orbs; nothing tested it."""

    @pytest.mark.parametrize("orb", [float("nan"), float("inf"), -1.0])
    def test_invalid_orb_rejected(self, orb):
        from kerykeion._predictive_utils import build_aspect_settings

        with pytest.raises(KerykeionException):
            build_aspect_settings(orb, None)

    def test_valid_orb_accepted(self):
        from kerykeion._predictive_utils import build_aspect_settings

        settings = build_aspect_settings(3.0, None)
        assert settings
        assert all(math.isfinite(s["orb"]) and s["orb"] >= 0 for s in settings)


# ---------------------------------------------------------------------------
# Round 2
# ---------------------------------------------------------------------------


class TestRelocationNullsFixedStarHorizonFields:
    """Relocation must null a fixed star's natal-location horizon fields.

    Round-1 enrichment made fixed stars carry azimuth/altitude/gauquelin_sector.
    relocate() nulled those only for scalar KerykeionPointModel fields, so a
    relocated chart's fixed stars silently kept the NATAL location's horizon.
    """

    def test_fixed_star_location_fields_reset_on_relocation(self):
        from kerykeion.relocated_chart_factory import RelocatedChartFactory

        natal = AstrologicalSubjectFactory.from_birth_data(
            name="reloc", year=1990, month=6, day=15, hour=14, minute=30,
            lng=12.5, lat=41.9, tz_str="Europe/Rome", city="Rome", nation="IT",
            online=False, suppress_geonames_warning=True,
            active_fixed_stars=["Regulus"], calculate_local_space=True, calculate_gauquelin=True,
        )
        # sanity: the natal star IS enriched, so the test would catch a no-op
        assert natal.fixed_stars[0].azimuth is not None

        relocated = RelocatedChartFactory.relocate(
            natal, new_city="Sydney", new_nation="AU",
            new_lat=-33.87, new_lng=151.21, new_tz_str="Australia/Sydney",
        )
        star = relocated.fixed_stars[0]
        assert star.azimuth is None
        assert star.altitude_above_horizon is None
        assert star.gauquelin_sector is None
        # the frame-independent longitude must survive the relocation
        assert star.abs_pos == natal.fixed_stars[0].abs_pos


class TestAstroCartographyRejectsCompositeSubject:
    """ACG needs a single birth instant; a midpoint composite has julian_day=None.

    Without the guard the None flowed into JD arithmetic and surfaced as a cryptic
    '< not supported between float and NoneType' from inside skyfield.
    """

    def test_composite_raises_clean_exception(self):
        from kerykeion import CompositeSubjectFactory
        from kerykeion.astro_cartography.factory import AstroCartographyFactory

        a = AstrologicalSubjectFactory.from_birth_data(
            name="a", year=1990, month=6, day=15, hour=14, minute=30,
            lng=12.5, lat=41.9, tz_str="Europe/Rome", city="Rome", nation="IT",
            online=False, suppress_geonames_warning=True,
        )
        b = AstrologicalSubjectFactory.from_birth_data(
            name="b", year=1985, month=3, day=2, hour=8, minute=15,
            lng=9.19, lat=45.46, tz_str="Europe/Rome", city="Milan", nation="IT",
            online=False, suppress_geonames_warning=True,
        )
        composite = CompositeSubjectFactory(a, b).get_midpoint_composite_subject_model()
        assert composite.julian_day is None
        with pytest.raises(KerykeionException, match="Julian Day"):
            AstroCartographyFactory.compute(composite)

    def test_ordinary_subject_still_computes(self):
        from kerykeion.astro_cartography.factory import AstroCartographyFactory

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="a", year=1990, month=6, day=15, hour=14, minute=30,
            lng=12.5, lat=41.9, tz_str="Europe/Rome", city="Rome", nation="IT",
            online=False, suppress_geonames_warning=True,
        )
        lines = AstroCartographyFactory.compute(subject, step=30)
        assert lines


class TestReportSanitizesHouseComparisonNames:
    """The house-comparison section rendered subject names without _san."""

    def test_control_chars_in_names_are_stripped(self):
        from kerykeion.report import ReportGenerator

        first = AstrologicalSubjectFactory.from_birth_data(
            name="A\x1b]0;pwn\x07B", year=1990, month=6, day=15, hour=14, minute=30,
            lng=12.5, lat=41.9, tz_str="Europe/Rome", city="Rome", nation="IT",
            online=False, suppress_geonames_warning=True,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            name="C\x1b[2JD", year=1985, month=3, day=2, hour=8, minute=15,
            lng=9.19, lat=45.46, tz_str="Europe/Rome", city="Milan", nation="IT",
            online=False, suppress_geonames_warning=True,
        )
        data = ChartDataFactory.create_synastry_chart_data(first, second)
        report = ReportGenerator(data).generate_report()
        assert "\x1b" not in report
        assert "\x07" not in report
