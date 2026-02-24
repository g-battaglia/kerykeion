import math
from datetime import datetime

import pytest

from kerykeion import KerykeionException
from kerykeion.utilities import (
    calculate_moon_phase,
    check_and_adjust_polar_latitude,
    circular_mean,
    datetime_to_julian,
    circular_sort,
    distribute_percentages_to_100,
    find_common_active_points,
    get_kerykeion_point_from_degree,
    get_moon_emoji_from_phase_int,
    get_moon_phase_name_from_phase_int,
    get_number_from_name,
    get_planet_house,
    inline_css_variables_in_svg,
    is_point_between,
    julian_to_datetime,
    setup_logging,
)


# --- get_number_from_name ----------------------------------------------------


def test_get_number_from_name_known_values():
    assert get_number_from_name("Sun") == 0
    assert get_number_from_name("Moon") == 1
    assert get_number_from_name("True_South_Lunar_Node") == 1100


def test_get_number_from_name_unknown_value():
    with pytest.raises(KerykeionException):
        get_number_from_name("ImaginaryPlanet")  # type: ignore[arg-type]


# --- get_kerykeion_point_from_degree -----------------------------------------


def test_get_kerykeion_point_from_degree_converts_values():
    point = get_kerykeion_point_from_degree(45, "Sun", "AstrologicalPoint")
    assert point.sign == "Tau"
    assert point.position == 15


def test_get_kerykeion_point_from_degree_negative_angle():
    point = get_kerykeion_point_from_degree(-30, "Sun", "AstrologicalPoint")
    assert point.abs_pos == 330
    assert point.sign == "Pis"


# --- setup_logging -----------------------------------------------------------


def test_setup_logging_accepts_valid_levels():
    for level in ["debug", "info", "warning", "error", "critical"]:
        setup_logging(level)


# --- is_point_between --------------------------------------------------------


def test_is_point_between_basic_cases():
    assert is_point_between(0, 30, 15) is True
    assert is_point_between(0, 30, 35) is False
    assert is_point_between(350, 20, 10) is True


def test_is_point_between_span_too_large():
    with pytest.raises(KerykeionException):
        is_point_between(0, 200, 50)


def test_is_point_between_floating_point_boundary():
    """Regression: planet longitude nearly equal to cusp due to float rounding.

    When a planet degree differs from a cusp by ~5e-14 (floating point noise),
    the old == comparison failed silently, causing get_planet_house to raise.
    See: Jhalawar 2023-03-17 14:30 Sidereal LAHIRI edge case.
    """
    # Exact values from the bug report
    cusp_start = 278.91912462695  # 7th house cusp
    planet = 278.91912462694995  # planet longitude (diff ~5.68e-14)
    cusp_end = 303.5944921144874  # 8th house cusp

    # Planet is essentially ON the start cusp -> should be inside this house
    assert is_point_between(cusp_start, cusp_end, planet) is True

    # The previous house ends at cusp_start; planet on the end -> should be outside
    prev_cusp_start = 249.2337785390238  # 6th house cusp
    assert is_point_between(prev_cusp_start, cusp_start, planet) is False


def test_is_point_between_exact_boundary():
    """Point exactly on start cusp belongs to that house; on end cusp does not."""
    assert is_point_between(30, 60, 30) is True  # on start -> inside
    assert is_point_between(0, 30, 30) is False  # on end -> outside (next house)


# --- get_planet_house --------------------------------------------------------


def test_get_planet_house_simple_cycle():
    houses = [i * 30 for i in range(12)]
    assert get_planet_house(15, houses) == "First_House"
    assert get_planet_house(75, houses) == "Third_House"


def test_get_planet_house_raises_when_not_found():
    houses = [0] * 12
    with pytest.raises(ValueError):
        get_planet_house(15, houses)


def test_get_planet_house_floating_point_cusp_boundary():
    """Regression: planet on cusp with floating point noise must not raise.

    Reproduces the exact ValueError from the bug report where planet=278.919...95
    and house cusp 7=278.919...00, differing by ~5e-14.
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
    # Must not raise; planet is on 7th house cusp -> assigned to 7th house
    result = get_planet_house(planet, houses)
    assert result == "Seventh_House"


# --- angular helpers ---------------------------------------------------------


def test_circular_mean_handles_wraparound():
    result = circular_mean(350, 10)
    assert 0 <= result <= 360


def test_circular_sort_keeps_clockwise_order():
    values = [40, 10, 350, 80]
    sorted_values = circular_sort(values)
    assert sorted_values == [40, 80, 350, 10]


# --- moon helpers ------------------------------------------------------------


def test_get_moon_emoji_and_name_from_phase():
    assert get_moon_emoji_from_phase_int(1)
    assert get_moon_phase_name_from_phase_int(14) == "Full Moon"


# --- polar latitude ----------------------------------------------------------


def test_check_and_adjust_polar_latitude_caps_values():
    assert check_and_adjust_polar_latitude(80) == 66
    assert check_and_adjust_polar_latitude(-90) == -66
    assert check_and_adjust_polar_latitude(10) == 10


# --- active points -----------------------------------------------------------


def test_find_common_active_points_simple_match():
    result = find_common_active_points(["Sun", "Moon"], ["Moon", "Mars"])  # type: ignore[arg-type]
    assert result == ["Moon"]


# --- julian conversion -------------------------------------------------------


def test_datetime_to_julian_and_back():
    dt = datetime(2000, 1, 1, 12, 0)
    julian = datetime_to_julian(dt)
    assert math.isclose(julian, 2451545.0, rel_tol=1e-9)
    assert julian_to_datetime(julian) == dt


# --- moon phase calculation --------------------------------------------------


def test_calculate_moon_phase_returns_expected_structure():
    phase = calculate_moon_phase(0, 0)
    assert phase.moon_phase == 1
    assert phase.moon_phase_name


# --- inline css --------------------------------------------------------------


def test_inline_css_variables_in_svg_simple_case():
    svg = """
    <svg>
        <style>:root { --color: #ff0000; }</style>
        <rect fill="var(--color)" />
    </svg>
    """
    result = inline_css_variables_in_svg(svg)
    assert "--color" not in result


# --- distribution helpers ----------------------------------------------------


def test_distribute_percentages_to_100_returns_integers():
    values = {"Fire": 2, "Water": 1, "Air": 1}
    result = distribute_percentages_to_100(values)
    assert sum(result.values()) == 100
    assert set(result.keys()) == {"Fire", "Water", "Air"}


def test_distribute_percentages_to_100_handles_zeros():
    assert distribute_percentages_to_100({"Fire": 0, "Water": 0}) == {"Fire": 0, "Water": 0}
