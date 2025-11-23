from kerykeion.aspects.aspects_utils import calculate_aspect_movement


def test_applying_when_faster_approaches():
    result = calculate_aspect_movement(
        point_one_abs_pos=45.0,
        point_two_abs_pos=50.0,
        aspect_degrees=0.0,
        point_one_speed=12.5,  # faster point behind the slower one
        point_two_speed=1.0,
    )
    assert result == "Applying"


def test_separating_when_faster_moves_away():
    result = calculate_aspect_movement(
        point_one_abs_pos=55.0,
        point_two_abs_pos=50.0,
        aspect_degrees=0.0,
        point_one_speed=12.5,  # faster point ahead and still moving forward
        point_two_speed=1.0,
    )
    assert result == "Separating"


def test_retrograde_faster_still_applying():
    result = calculate_aspect_movement(
        point_one_abs_pos=110.0,
        point_two_abs_pos=100.0,
        aspect_degrees=0.0,
        point_one_speed=-0.8,  # faster in absolute value but retrograde
        point_two_speed=0.1,
    )
    assert result == "Applying"


def test_fixed_when_both_stationary():
    result = calculate_aspect_movement(
        point_one_abs_pos=10.0,
        point_two_abs_pos=20.0,
        aspect_degrees=0.0,
        point_one_speed=0.0,
        point_two_speed=0.0,
    )
    assert result == "Static"


def test_fixed_when_relative_speed_is_zero():
    result = calculate_aspect_movement(
        point_one_abs_pos=10.0,
        point_two_abs_pos=40.0,
        aspect_degrees=30.0,
        point_one_speed=1.0,
        point_two_speed=1.0,  # same speed keeps orb constant
    )
    assert result == "Static"
