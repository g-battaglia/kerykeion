# -*- coding: utf-8 -*-
"""
Consolidated tests for kerykeion.utilities.

Integrates all cases from tests/utils/test_utilities.py plus utility-related
edge cases from tests/edge_cases/test_edge_cases.py and
tests/edge_cases/test_coverage_boost.py.
"""

import math
from datetime import datetime

import pytest

from kerykeion.schemas import KerykeionException
from kerykeion.utilities import (
    get_number_from_name,
    get_kerykeion_point_from_degree,
    setup_logging,
    is_point_between,
    get_planet_house,
    circular_mean,
    circular_sort,
    get_moon_emoji_from_phase_int,
    get_moon_phase_name_from_phase_int,
    check_and_adjust_polar_latitude,
    find_common_active_points,
    datetime_to_julian,
    julian_to_datetime,
    calculate_moon_phase,
    inline_css_variables_in_svg,
    distribute_percentages_to_100,
    normalize_zodiac_type,
    get_house_name,
    get_house_number,
    format_ancient_iso,
    format_timedelta_hhmm,
)
from kerykeion.charts.charts_utils import convert_decimal_to_degree_string


# =============================================================================
# TestGetNumberFromName
# =============================================================================


class TestGetNumberFromName:
    """Tests for get_number_from_name."""

    def test_sun_returns_zero(self):
        assert get_number_from_name("Sun") == 0

    def test_moon_returns_one(self):
        assert get_number_from_name("Moon") == 1

    def test_pluto_returns_nine(self):
        assert get_number_from_name("Pluto") == 9

    def test_chiron_returns_fifteen(self):
        assert get_number_from_name("Chiron") == 15

    def test_true_south_lunar_node(self):
        assert get_number_from_name("True_South_Lunar_Node") == 1100

    def test_unknown_name_raises_kerykeion_exception(self):
        with pytest.raises(KerykeionException):
            get_number_from_name("ImaginaryPlanet")  # type: ignore[arg-type]


# =============================================================================
# TestGetKerykeionPointFromDegree
# =============================================================================


class TestGetKerykeionPointFromDegree:
    """Tests for get_kerykeion_point_from_degree."""

    def test_valid_conversion_45_degrees(self):
        point = get_kerykeion_point_from_degree(45, "Sun", "AstrologicalPoint")
        assert point.sign == "Tau"
        assert point.position == 15

    def test_negative_angle_wraps(self):
        point = get_kerykeion_point_from_degree(-30, "Sun", "AstrologicalPoint")
        assert point.abs_pos == 330
        assert point.sign == "Pis"

    def test_degree_360_raises_kerykeion_exception(self):
        with pytest.raises(KerykeionException, match="Error in calculating positions"):
            get_kerykeion_point_from_degree(360.0, "Test", point_type="Natal")

    def test_degree_above_360_raises_kerykeion_exception(self):
        with pytest.raises(KerykeionException):
            get_kerykeion_point_from_degree(400.0, "Test", point_type="Natal")

    def test_zero_degrees_is_aries(self):
        point = get_kerykeion_point_from_degree(0, "Sun", "AstrologicalPoint")
        assert point.sign == "Ari"
        assert point.position == 0

    def test_boundary_30_degrees_is_taurus(self):
        point = get_kerykeion_point_from_degree(30, "Sun", "AstrologicalPoint")
        assert point.sign == "Tau"
        assert point.position == 0


# =============================================================================
# TestSetupLogging
# =============================================================================


class TestSetupLogging:
    """Tests for setup_logging."""

    @pytest.mark.parametrize("level", ["debug", "info", "warning", "error", "critical"])
    def test_valid_levels_accepted(self, level):
        setup_logging(level)

    def test_uppercase_levels_accepted(self):
        setup_logging("DEBUG")
        setup_logging("INFO")

    def test_invalid_level_defaults_to_info(self):
        # Should not raise; invalid level falls back to INFO
        setup_logging("nonexistent_level")


# =============================================================================
# TestIsPointBetween
# =============================================================================


class TestIsPointBetween:
    """Tests for is_point_between."""

    def test_point_inside(self):
        assert is_point_between(0, 30, 15) is True

    def test_point_outside(self):
        assert is_point_between(0, 30, 35) is False

    def test_wraparound_point_inside(self):
        assert is_point_between(350, 20, 10) is True

    def test_span_over_180_raises(self):
        with pytest.raises(KerykeionException):
            is_point_between(0, 200, 50)

    def test_reflex_span_allowed_with_flag(self):
        """allow_reflex=True accepts arcs > 180° instead of raising."""
        # 0 -> 200 is a 200° clockwise arc; 50 lies on it, 250 does not.
        assert is_point_between(0, 200, 50, allow_reflex=True) is True
        assert is_point_between(0, 200, 250, allow_reflex=True) is False

    def test_floating_point_boundary_regression(self):
        """Regression: planet longitude nearly equal to cusp due to float rounding.

        When a planet degree differs from a cusp by ~5e-14 (floating point noise),
        the old == comparison failed silently, causing get_planet_house to raise.
        See: Jhalawar 2023-03-17 14:30 Sidereal LAHIRI edge case.
        """
        cusp_start = 278.91912462695  # 7th house cusp
        planet = 278.91912462694995  # planet longitude (diff ~5.68e-14)
        cusp_end = 303.5944921144874  # 8th house cusp

        assert is_point_between(cusp_start, cusp_end, planet) is True

        prev_cusp_start = 249.2337785390238  # 6th house cusp
        assert is_point_between(prev_cusp_start, cusp_start, planet) is False

    def test_exact_boundary_start_inclusive(self):
        """Point exactly on start cusp belongs to that house."""
        assert is_point_between(30, 60, 30) is True

    def test_exact_boundary_end_exclusive(self):
        """Point exactly on end cusp does not belong to that house."""
        assert is_point_between(0, 30, 30) is False

    def test_math_isclose_near_boundary(self):
        """Verify near-boundary floats are handled with math.isclose semantics."""
        start = 100.0
        end = 130.0
        near_start = start + 1e-14
        assert is_point_between(start, end, near_start) is True


# =============================================================================
# TestGetPlanetHouse
# =============================================================================


class TestGetPlanetHouse:
    """Tests for get_planet_house."""

    def test_simple_cycle_first_house(self):
        houses = [i * 30 for i in range(12)]
        assert get_planet_house(15, houses) == "First_House"

    def test_simple_cycle_third_house(self):
        houses = [i * 30 for i in range(12)]
        assert get_planet_house(75, houses) == "Third_House"

    def test_not_found_raises_value_error(self):
        houses = [0] * 12
        with pytest.raises(ValueError):
            get_planet_house(15, houses)

    def test_floating_point_cusp_boundary_regression(self):
        """Regression: planet on cusp with floating point noise must not raise.

        Reproduces the exact ValueError from the bug report where
        planet=278.919...95 and house cusp 7=278.919...00, differing by ~5e-14.
        """
        planet = 278.91912462694995
        houses = [
            98.91912462694998,
            123.59449211448738,
            151.93854125279213,
            184.03102407800813,
            217.37620913190696,
            249.2337785390238,
            278.91912462695,
            303.5944921144874,
            331.93854125279216,
            4.031024078008134,
            37.37620913190699,
            69.2337785390238,
        ]
        result = get_planet_house(planet, houses)
        assert result == "Seventh_House"

    def test_non_quadrant_wide_span_house(self):
        """Non-quadrant systems can have cusps spanning > 180°; the planet must
        still resolve via the reflex-aware arc containment instead of raising."""
        # First house spans 200° (0 -> 200), the rest are crammed into 200..360.
        houses = [0, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300]
        assert get_planet_house(100, houses) == "First_House"
        assert get_planet_house(205, houses) == "Second_House"

    def test_planet_exactly_on_cusp_is_start_inclusive(self):
        """A planet exactly on a cusp falls into the house that cusp opens."""
        houses = [i * 30 for i in range(12)]
        assert get_planet_house(30, houses) == "Second_House"
        assert get_planet_house(0, houses) == "First_House"


# =============================================================================
# TestCircularMean
# =============================================================================


class TestCircularMean:
    """Tests for circular_mean."""

    def test_simple_average(self):
        result = circular_mean(90, 90)
        assert math.isclose(result, 90.0, abs_tol=1e-9)

    def test_wraparound_near_zero(self):
        result = circular_mean(350, 10)
        assert 0 <= result < 360
        # Expect result near 0/360
        assert result < 10 or result > 350

    def test_wraparound_returns_zero_not_360(self):
        """Float rounding of 360 - 4.6e-15 used to return exactly 360.0,
        which get_kerykeion_point_from_degree rejects (degree >= 360)."""
        result = circular_mean(350.0, 10.0)
        assert result == 0.0

    def test_result_always_below_360(self):
        for first, second in [(350.0, 10.0), (359.9, 0.1), (355.5, 4.5), (180.0, 180.0)]:
            result = circular_mean(first, second)
            assert 0.0 <= result < 360.0

    def test_antipodal_tie_break_is_deterministic(self):
        """Exactly antipodal inputs have no unique mean; the tie-break is
        the plain average of the normalized positions."""
        assert circular_mean(10.0, 190.0) == 100.0
        assert circular_mean(190.0, 10.0) == 100.0
        assert circular_mean(0.0, 180.0) == 90.0

    def test_antipodal_matches_midpoint_factory_convention(self):
        from kerykeion.midpoints.midpoint_factory import MidpointFactory

        for first, second in [(10.0, 190.0), (0.0, 180.0), (350.0, 170.0)]:
            assert circular_mean(first, second) == MidpointFactory._shorter_arc_midpoint(first, second)

    def test_near_antipodal_stays_on_regular_path(self):
        """Inputs just shy of antipodal must not snap to the tie-break."""
        result = circular_mean(10.0, 189.999999)
        assert math.isclose(result, 99.9999995, abs_tol=1e-5)

    def test_mean_feeds_get_kerykeion_point_from_degree(self):
        """Mirror-symmetric positions around 0° Aries (the composite-chart
        crash case): the mean must be accepted by the point builder."""
        for first, second in [(350.0, 10.0), (359.9, 0.1), (355.5, 4.5)]:
            point = get_kerykeion_point_from_degree(
                circular_mean(first, second), "Sun", "AstrologicalPoint"
            )
            # Circular distance from 0° Aries (float noise may land the mean
            # on either side of the 0°/360° seam).
            assert min(point.abs_pos, 360.0 - point.abs_pos) < 1e-6


# =============================================================================
# TestCircularSort
# =============================================================================


class TestCircularSort:
    """Tests for circular_sort."""

    def test_clockwise_order_from_first(self):
        values = [40, 10, 350, 80]
        sorted_values = circular_sort(values)
        assert sorted_values == [40, 80, 350, 10]

    def test_empty_list_raises_value_error(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            circular_sort([])

    def test_single_element(self):
        result = circular_sort([45.0])
        assert result == [45.0]

    def test_invalid_type_raises_value_error(self):
        with pytest.raises(ValueError, match="must be numeric"):
            circular_sort([1.0, "invalid", 3.0])  # type: ignore


# =============================================================================
# TestMoonPhaseHelpers
# =============================================================================


class TestMoonPhaseHelpers:
    """Tests for get_moon_emoji_from_phase_int and get_moon_phase_name_from_phase_int."""

    def test_emoji_from_phase_1(self):
        emoji = get_moon_emoji_from_phase_int(1)
        assert emoji  # non-empty string

    def test_name_from_phase_14_is_full_moon(self):
        assert get_moon_phase_name_from_phase_int(14) == "Full Moon"

    @pytest.mark.parametrize("phase", [1, 4, 7, 10, 14, 18, 21, 25])
    def test_all_eight_major_phases_return_emoji(self, phase):
        emoji = get_moon_emoji_from_phase_int(phase)
        assert isinstance(emoji, str)
        assert len(emoji) > 0

    @pytest.mark.parametrize("phase", [1, 4, 7, 10, 14, 18, 21, 25])
    def test_all_eight_major_phases_return_name(self, phase):
        name = get_moon_phase_name_from_phase_int(phase)
        assert isinstance(name, str)
        assert len(name) > 0

    def test_out_of_range_emoji_raises(self):
        with pytest.raises(KerykeionException, match="Error in lunar phase calculation"):
            get_moon_emoji_from_phase_int(30)

    def test_out_of_range_name_raises(self):
        with pytest.raises(KerykeionException, match="Error in lunar phase calculation"):
            get_moon_phase_name_from_phase_int(30)


# =============================================================================
# TestCheckAndAdjustPolarLatitude
# =============================================================================


class TestCheckAndAdjustPolarLatitude:
    """Tests for check_and_adjust_polar_latitude."""

    def test_high_latitude_capped_at_66(self):
        assert check_and_adjust_polar_latitude(80) == 66

    def test_very_high_latitude_capped(self):
        assert check_and_adjust_polar_latitude(90) == 66

    def test_low_latitude_capped_at_minus_66(self):
        assert check_and_adjust_polar_latitude(-90) == -66

    def test_moderate_negative_capped(self):
        assert check_and_adjust_polar_latitude(-70) == -66

    def test_value_in_range_unchanged(self):
        assert check_and_adjust_polar_latitude(10) == 10

    def test_zero_unchanged(self):
        assert check_and_adjust_polar_latitude(0) == 0

    def test_boundary_66_unchanged(self):
        assert check_and_adjust_polar_latitude(66) == 66


# =============================================================================
# TestFindCommonActivePoints
# =============================================================================


class TestFindCommonActivePoints:
    """Tests for find_common_active_points."""

    def test_simple_match(self):
        result = find_common_active_points(["Sun", "Moon"], ["Moon", "Mars"])  # type: ignore[arg-type]
        assert result == ["Moon"]

    def test_no_overlap_returns_empty(self):
        result = find_common_active_points(["Sun", "Venus"], ["Moon", "Mars"])  # type: ignore[arg-type]
        assert result == []

    def test_full_overlap(self):
        result = find_common_active_points(["Sun", "Moon"], ["Moon", "Sun"])  # type: ignore[arg-type]
        assert set(result) == {"Sun", "Moon"}


# =============================================================================
# TestDateTimeConversions
# =============================================================================


class TestDateTimeConversions:
    """Tests for datetime_to_julian and julian_to_datetime."""

    def test_round_trip_j2000(self):
        dt = datetime(2000, 1, 1, 12, 0)
        julian = datetime_to_julian(dt)
        assert math.isclose(julian, 2451545.0, rel_tol=1e-9)
        assert julian_to_datetime(julian) == dt

    def test_known_j2000_epoch_value(self):
        dt = datetime(2000, 1, 1, 12, 0)
        julian = datetime_to_julian(dt)
        assert math.isclose(julian, 2451545.0, rel_tol=1e-9)

    def test_julian_to_datetime_pre_gregorian(self):
        """julian_to_datetime for dates before Gregorian reform."""
        result = julian_to_datetime(2299160.0)
        assert isinstance(result, datetime)

    def test_round_trip_arbitrary_date(self):
        dt = datetime(1990, 6, 15, 14, 30)
        julian = datetime_to_julian(dt)
        recovered = julian_to_datetime(julian)
        assert recovered.year == dt.year
        assert recovered.month == dt.month
        assert recovered.day == dt.day


# =============================================================================
# TestCalculateMoonPhase
# =============================================================================


class TestCalculateMoonPhase:
    """Tests for calculate_moon_phase."""

    def test_expected_structure(self):
        phase = calculate_moon_phase(0, 0)
        assert hasattr(phase, "degrees_between_s_m")
        assert hasattr(phase, "moon_phase")
        assert hasattr(phase, "moon_emoji")
        assert hasattr(phase, "moon_phase_name")

    def test_new_moon_near_zero_apart(self):
        phase = calculate_moon_phase(0, 0)
        assert phase.moon_phase == 1
        assert phase.moon_phase_name

    def test_full_moon_near_180_apart(self):
        phase = calculate_moon_phase(180, 0)
        # degrees_between should be ~180
        assert 170 <= phase.degrees_between_s_m <= 190
        assert "Full" in phase.moon_phase_name or phase.moon_phase == 14


# =============================================================================
# TestInlineCssVariables
# =============================================================================


class TestInlineCssVariables:
    """Tests for inline_css_variables_in_svg."""

    def test_simple_css_variable_replacement(self):
        svg = """
        <svg>
            <style>:root { --color: #ff0000; }</style>
            <rect fill="var(--color)" />
        </svg>
        """
        result = inline_css_variables_in_svg(svg)
        assert "--color" not in result

    def test_fallback_values(self):
        svg = """
        <style>
            :root {
                --main-color: blue;
            }
        </style>
        <rect fill="var(--main-color, red)" />
        <rect fill="var(--unknown, green)" />
        """
        result = inline_css_variables_in_svg(svg)
        assert "blue" in result

    def test_multiple_variables(self):
        svg = """
        <style>:root { --a: red; --b: blue; }</style>
        <rect fill="var(--a)" stroke="var(--b)" />
        """
        result = inline_css_variables_in_svg(svg)
        assert "red" in result
        assert "blue" in result
        assert "var(--a)" not in result
        assert "var(--b)" not in result

    def test_style_block_removal(self):
        svg = """
        <style>
            :root {
                --main-color: blue;
            }
        </style>
        <rect fill="var(--main-color, red)" />
        <rect fill="var(--unknown, green)" />
        """
        result = inline_css_variables_in_svg(svg)
        assert "<style>" not in result


# =============================================================================
# TestDistributePercentages
# =============================================================================


class TestDistributePercentages:
    """Tests for distribute_percentages_to_100."""

    def test_integers_sum_to_100(self):
        values = {"Fire": 2, "Water": 1, "Air": 1}
        result = distribute_percentages_to_100(values)
        assert sum(result.values()) == 100
        assert set(result.keys()) == {"Fire", "Water", "Air"}

    def test_all_values_are_integers(self):
        values = {"Fire": 2, "Water": 1, "Air": 1}
        result = distribute_percentages_to_100(values)
        for v in result.values():
            assert isinstance(v, int)

    def test_zero_handling(self):
        assert distribute_percentages_to_100({"Fire": 0, "Water": 0}) == {"Fire": 0, "Water": 0}

    def test_empty_dict(self):
        result = distribute_percentages_to_100({})
        assert result == {}


# =============================================================================
# TestNormalizeZodiacType
# =============================================================================


class TestNormalizeZodiacType:
    """Tests for normalize_zodiac_type."""

    def test_lowercase_tropical(self):
        assert normalize_zodiac_type("tropical") == "Tropical"

    def test_legacy_tropic(self):
        assert normalize_zodiac_type("Tropic") == "Tropical"

    def test_uppercase_sidereal(self):
        assert normalize_zodiac_type("SIDEREAL") == "Sidereal"

    def test_mixed_case_sidereal(self):
        assert normalize_zodiac_type("sidereal") == "Sidereal"

    def test_invalid_raises_value_error(self):
        with pytest.raises(ValueError):
            normalize_zodiac_type("invalid_zodiac")

    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError):
            normalize_zodiac_type("")


# =============================================================================
# TestHouseNameConversions
# =============================================================================


class TestHouseNameConversions:
    """Tests for get_house_name and get_house_number."""

    def test_get_house_name_first(self):
        assert get_house_name(1) == "First_House"

    def test_get_house_name_twelfth(self):
        assert get_house_name(12) == "Twelfth_House"

    def test_get_house_number_first_house(self):
        assert get_house_number("First_House") == 1

    def test_get_house_number_twelfth_house(self):
        assert get_house_number("Twelfth_House") == 12

    @pytest.mark.parametrize("number", range(1, 13))
    def test_all_valid_house_numbers_return_name(self, number):
        result = get_house_name(number)
        assert "_House" in result

    def test_invalid_house_number_zero_raises(self):
        with pytest.raises(ValueError, match="Invalid house number"):
            get_house_name(0)

    def test_invalid_house_number_13_raises(self):
        with pytest.raises(ValueError, match="Invalid house number"):
            get_house_name(13)

    def test_invalid_house_name_raises(self):
        with pytest.raises(ValueError, match="Invalid house name"):
            get_house_number("Invalid_House")  # type: ignore

    @pytest.mark.parametrize("number", range(1, 13))
    def test_round_trip_name_number(self, number):
        name = get_house_name(number)
        assert get_house_number(name) == number


# =============================================================================
# CHARTS UTILS INTERNAL FUNCTIONS (from edge_cases/test_coverage_boost.py)
# =============================================================================


class TestChartsUtilsInternalFunctions:
    """Tests for internal functions in charts_utils module."""

    def test_degree_sum_exact_360(self):
        from kerykeion.charts.charts_utils import degree_sum

        assert degree_sum(180, 180) == 0.0

    def test_normalize_degree_360(self):
        from kerykeion.charts.charts_utils import normalize_degree

        assert normalize_degree(360) == 0.0

    def test_normalize_degree_negative(self):
        from kerykeion.charts.charts_utils import normalize_degree

        assert normalize_degree(-90) == 270.0

    def test_dec_hour_join(self):
        from kerykeion.charts.charts_utils import hms_to_decimal_hours

        assert hms_to_decimal_hours(12, 30, 0) == pytest.approx(12.5, abs=0.001)

    def test_offset_to_tz_none_raises(self):
        from kerykeion.charts.charts_utils import timedelta_to_decimal_hours

        with pytest.raises(KerykeionException):
            timedelta_to_decimal_hours(None)

    def test_offset_to_tz_valid(self):
        from datetime import timedelta
        from kerykeion.charts.charts_utils import timedelta_to_decimal_hours

        assert timedelta_to_decimal_hours(timedelta(hours=2)) == 2.0

    def test_get_decoded_celestial_point_unknown_raises(self):
        from kerykeion.charts.charts_utils import get_decoded_kerykeion_celestial_point_name
        from kerykeion.schemas.settings_models import KerykeionLanguageCelestialPointModel

        lang_model = KerykeionLanguageCelestialPointModel(
            Sun="Sun",
            Moon="Moon",
            Mercury="Mercury",
            Venus="Venus",
            Mars="Mars",
            Jupiter="Jupiter",
            Saturn="Saturn",
            Uranus="Uranus",
            Neptune="Neptune",
            Pluto="Pluto",
            Mean_North_Lunar_Node="Mean Node",
            True_North_Lunar_Node="True Node",
            Chiron="Chiron",
            Mean_Lilith="Lilith",
            Mean_South_Lunar_Node="South Node",
            True_South_Lunar_Node="True South Node",
            True_Lilith="True Lilith",
            Earth="Earth",
            Pholus="Pholus",
            Ceres="Ceres",
            Pallas="Pallas",
            Juno="Juno",
            Vesta="Vesta",
            Eris="Eris",
            Sedna="Sedna",
            Haumea="Haumea",
            Makemake="Makemake",
            Ixion="Ixion",
            Orcus="Orcus",
            Quaoar="Quaoar",
            Regulus="Regulus",
            Spica="Spica",
            Achernar="Achernar",
            Aldebaran="Aldebaran",
            Antares="Antares",
            Arcturus="Arcturus",
            Betelgeuse="Betelgeuse",
            Canopus="Canopus",
            Capella="Capella",
            Fomalhaut="Fomalhaut",
            Pollux="Pollux",
            Procyon="Procyon",
            Rigel="Rigel",
            Sirius="Sirius",
            Algol="Algol",
            Deneb="Deneb",
            Altair="Altair",
            Vega="Vega",
            Alcyone="Alcyone",
            Alphecca="Alphecca",
            Algorab="Algorab",
            Deneb_Algedi="Deneb Algedi",
            Pars_Fortunae="Part of Fortune",
            Pars_Spiritus="Part of Spirit",
            Pars_Amoris="Part of Love",
            Pars_Fidei="Part of Faith",
            Vertex="Vertex",
            Anti_Vertex="Anti-Vertex",
            Ascendant="Ascendant",
            Medium_Coeli="Medium Coeli",
            Descendant="Descendant",
            Imum_Coeli="Imum Coeli",
        )
        # v6: unknown points no longer raise — they fall back to a slugified
        # version of the input so catalog fixed stars (Vindemiatrix, Polaris,
        # etc.) can render without a language entry.
        result = get_decoded_kerykeion_celestial_point_name("Vindemiatrix", lang_model)
        assert result == "Vindemiatrix"
        result = get_decoded_kerykeion_celestial_point_name("Asellus_Australis", lang_model)
        assert result == "Asellus Australis"


class TestPlanetGridLayout:
    """Tests for _planet_grid_layout_position."""

    def test_fourth_column_layout(self):
        from kerykeion.charts.charts_utils import _planet_grid_layout_position

        offset, row = _planet_grid_layout_position(40)
        assert row == 4  # 40 - 36 = 4
        assert offset < 0  # Negative offset for columns beyond first


class TestChartsUtilsDistributionEdgeCases:
    """Tests for element distribution calculation edge cases."""

    def test_distribution_skips_missing_point(self):
        from kerykeion.charts.charts_utils import calculate_element_points
        from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS
        from kerykeion import AstrologicalSubjectFactory

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            active_points=["Sun", "Moon", "Mercury"],
        )
        dist = calculate_element_points(
            DEFAULT_CELESTIAL_POINTS_SETTINGS,
            ["sun", "moon", "nonexistent_point"],
            subject,
        )
        assert dist is not None
        assert len(dist) == 4  # Fire, Earth, Air, Water

    def test_distribution_with_custom_weights(self):
        from kerykeion.charts.charts_utils import calculate_element_points
        from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS
        from kerykeion import AstrologicalSubjectFactory

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
        )
        dist = calculate_element_points(
            DEFAULT_CELESTIAL_POINTS_SETTINGS,
            ["sun", "moon", "mercury"],
            subject,
            method="weighted",
            custom_weights={"sun": 5.0, "moon": 4.0, "__default__": 1.0},
        )
        assert dist is not None

    def test_distribution_counts_fixed_stars_when_opted_in(self):
        """v6 regression: stars live in subject.fixed_stars (not as
        attributes), so the star weight-table entries were unreachable and
        active stars silently dropped out of element distributions. Star
        inclusion is opt-in (include_fixed_stars=True, as the chart data
        factory does) so callers naming an explicit point subset are not
        polluted, and every star weighs 0.2 unless the table says otherwise."""
        from kerykeion.charts.charts_utils import calculate_element_points
        from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS
        from kerykeion import AstrologicalSubjectFactory

        kwargs = dict(
            year=1990, month=6, day=15, hour=12, minute=0,
            lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True,
            active_points=["Sun"],
        )
        without_star = AstrologicalSubjectFactory.from_birth_data(name="NoStar", **kwargs)
        with_star = AstrologicalSubjectFactory.from_birth_data(
            name="Star", **kwargs, active_fixed_stars=["Regulus"],
        )
        base = calculate_element_points(
            DEFAULT_CELESTIAL_POINTS_SETTINGS, ["sun"], without_star, method="weighted",
        )
        with_regulus = calculate_element_points(
            DEFAULT_CELESTIAL_POINTS_SETTINGS, ["sun"], with_star, method="weighted",
            include_fixed_stars=True,
        )
        regulus_sign_group = ["fire", "earth", "air", "water"][
            with_star.fixed_stars[0].sign_num % 4
        ]
        # Regulus (weight 0.2 in the star table) must add to its element.
        assert with_regulus[regulus_sign_group] == pytest.approx(
            base[regulus_sign_group] + 0.2
        )

        # Default (no opt-in): the caller's named subset is exactly what
        # counts — three active stars must not inflate a ["sun"] total.
        default_totals = calculate_element_points(
            DEFAULT_CELESTIAL_POINTS_SETTINGS, ["sun"], with_star, method="pure_count",
        )
        assert sum(default_totals.values()) == pytest.approx(1.0)

    def test_distribution_star_weight_never_planet_grade(self):
        """A catalog star missing from the weight table weighs 0.2 (the star
        fallback), never the generic 1.0 point fallback; slugs go through the
        shared catalog slugger (strip + spaces/hyphens -> underscores)."""
        from kerykeion.charts.charts_utils import (
            _FIXED_STAR_FALLBACK_WEIGHT,
            calculate_element_points,
        )
        from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS
        from kerykeion import AstrologicalSubjectFactory

        assert _FIXED_STAR_FALLBACK_WEIGHT == 0.2

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Star Slug", year=1990, month=6, day=15, hour=12, minute=0,
            lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True,
            active_points=["Sun"], active_fixed_stars=[" Spica "],
        )
        assert len(subject.fixed_stars) == 1
        base = calculate_element_points(
            DEFAULT_CELESTIAL_POINTS_SETTINGS, ["sun"], subject, method="weighted",
        )
        with_star = calculate_element_points(
            DEFAULT_CELESTIAL_POINTS_SETTINGS, ["sun"], subject, method="weighted",
            include_fixed_stars=True,
        )
        # ' Spica ' must slug to 'spica' (table weight 0.2), not '_spica_'
        # (which would silently take a planet-grade fallback weight).
        assert sum(with_star.values()) == pytest.approx(sum(base.values()) + 0.2)


# ---------------------------------------------------------------------------
# Missing edge-case tests (migrated from tests/edge_cases/test_edge_cases.py)
# ---------------------------------------------------------------------------


class TestInlineCssEdgeCases:
    """Edge cases for inline_css_variables_in_svg."""

    def test_inline_css_no_style_block(self):
        """SVG with no <style> block — fallback values should be used."""
        svg_content = '<svg><rect fill="var(--color, blue)" /></svg>'
        result = inline_css_variables_in_svg(svg_content)
        assert "blue" in result or "var" not in result

    def test_inline_css_no_fallback_unknown_var(self):
        """CSS variable with no fallback and unknown variable returns empty."""
        svg = '<rect fill="var(--unknown-color)" />'
        result = inline_css_variables_in_svg(svg)
        assert 'fill=""' in result or "var" not in result


# =============================================================================
# TestConvertDecimalToDegreeString
# =============================================================================


class TestConvertDecimalToDegreeString:
    """Tests for convert_decimal_to_degree_string (charts_utils)."""

    def test_basic_dms(self):
        assert convert_decimal_to_degree_string(10.5, "3") == "10°30'00\""

    def test_degree_and_minute_formats_floor(self):
        assert convert_decimal_to_degree_string(10.99, "1") == "10°"
        assert convert_decimal_to_degree_string(10.99, "2") == "10°59'"

    def test_format_three_floors_without_overshooting(self):
        """Format "3" floors to the second: it never emits an invalid 60\" and
        never overshoots the sign boundary (consistent with format "1"/"2")."""
        # Just under a whole degree: floors down, no carry into the next degree.
        result = convert_decimal_to_degree_string(10.99997, "3")
        assert result == "10°59'59\""
        assert "60\"" not in result

    def test_format_three_stays_within_sign_at_boundary(self):
        """A within-sign position just below 30° must read "29°59'59\"", not the
        out-of-sign "30°00'00\"" the old rounding produced — and must agree with
        format "1" which floors to "29°"."""
        assert convert_decimal_to_degree_string(29.9999, "3") == "29°59'59\""
        assert convert_decimal_to_degree_string(29.9999, "1") == "29°"

    def test_no_invalid_sixty_across_sampled_boundaries(self):
        for deg in (9, 14, 29, 59):
            for frac in (0.99997, 0.999999):
                out = convert_decimal_to_degree_string(deg + frac, "3")
                assert "'60\"" not in out
                assert "60'" not in out

    def test_negative_inputs_consistent_and_not_malformed(self):
        """Regression: a negative value (e.g. a southern declination) must not
        produce a malformed negative-minute field like "-5°-30'", and all three
        formats must agree on the floored representation."""
        assert convert_decimal_to_degree_string(-5.5, "1") == "-6°"
        assert convert_decimal_to_degree_string(-5.5, "2") == "-6°30'"
        assert convert_decimal_to_degree_string(-5.5, "3") == "-6°30'00\""
        for fmt in ("1", "2", "3"):
            out = convert_decimal_to_degree_string(-5.5, fmt)
            assert "-30" not in out, f"format {fmt} emitted a malformed negative field: {out}"


# =============================================================================
# TestFormatTimedeltaHhmm
# =============================================================================


class TestFormatTimedeltaHhmm:
    """Tests for format_timedelta_hhmm."""

    def test_rounds_to_whole_minutes(self):
        from datetime import timedelta

        assert format_timedelta_hhmm(timedelta(hours=11, minutes=30, seconds=40)) == "11:31"
        assert format_timedelta_hhmm(timedelta(hours=8, minutes=5)) == "8:05"
        assert format_timedelta_hhmm(timedelta(hours=0, minutes=0)) == "0:00"


# =============================================================================
# TestFormatAncientIso
# =============================================================================


class TestFormatAncientIso:
    """Tests for format_ancient_iso, focused on the midnight-rollover carry."""

    def test_midnight_rollover_carries_to_next_day(self):
        """A decimal hour within float-noise of 24:00:00 must roll to 00:00:00
        of the following day, not clamp to 23:59:59 of the same day."""
        result = format_ancient_iso(-500, 3, 21, 23.9999999, 0.0)
        assert result == "-0500-03-22T00:00:00+00:00"

    def test_month_boundary_rollover(self):
        """Rollover across a month boundary increments the month."""
        result = format_ancient_iso(-44, 1, 31, 23.9999999, 0.0)
        assert result.startswith("-0044-02-01T00:00:00")

    def test_no_rollover_for_normal_hour(self):
        result = format_ancient_iso(-500, 3, 21, 11.5, 0.0)
        assert result == "-0500-03-21T11:30:00+00:00"
