
import pytest
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

# Edge Cases from Reproduction Scripts

def test_boundary_crossing_separating():
    # Sun at 359, Speed 1. Moon at 5, Speed 13. Aspect 0 (Conjunction).
    # Moon is ahead of Sun by 6 degrees.
    # Moon moves 13, Sun 1. Relative 12.
    # Distance 6 -> 18. Separating.
    result = calculate_aspect_movement(359, 5, 0, 1, 13)
    assert result == "Separating"

def test_boundary_crossing_applying():
    # Sun at 359, Speed 1. Moon at 355, Speed 13. Aspect 0.
    # Moon behind Sun by 4 degrees.
    # Moon moves 13, Sun 1. Relative 12.
    # Distance 4 -> 8 (Moon passes Sun).
    # Wait. Moon 355 -> 355+13 = 8. Sun 359 -> 0.
    # Distance 355 to 359 is 4.
    # Next: 8 to 0 is 8.
    # Distance increased?
    # 355 -> 359 (4 deg).
    # 8 -> 0 (8 deg).
    # Yes, it passed exact conjunction. So it should be Separating?
    # Or Applying if we consider it hasn't reached exactness yet?
    # No, 355 -> 8 crosses 359. It WAS applying, then became separating.
    # But at the INSTANT 355, it is Applying.
    result = calculate_aspect_movement(359, 355, 0, 1, 13)
    assert result == "Applying"

def test_aspect_greater_than_180_applying():
    # Sun 10. Moon 245. Aspect 240 (Trine).
    # 245 is 5 degrees past 240 (relative to 0).
    # Wait. 10 + 240 = 250.
    # Moon is at 245. It is approaching 250.
    # So it is Applying.
    result = calculate_aspect_movement(10, 245, 240, 1, 13)
    assert result == "Applying"

def test_retrograde_applying():
    # Sun 10 (Speed 1). Mercury 15 (Speed -1). Aspect 0.
    # Merc 15 -> 14. Sun 10 -> 11.
    # Distance 5 -> 3. Applying.
    result = calculate_aspect_movement(10, 15, 0, 1, -1)
    assert result == "Applying"

def test_retrograde_separating():
    # Sun 10 (Speed 1). Mercury 5 (Speed -1). Aspect 0.
    # Merc 5 -> 4. Sun 10 -> 11.
    # Distance 5 -> 7. Separating.
    result = calculate_aspect_movement(10, 5, 0, 1, -1)
    assert result == "Separating"

def test_retrograde_both_applying():
    # P1 10 (Speed -1). P2 15 (Speed -2). Aspect 0.
    # P2 is faster (abs speed 2 > 1).
    # P2 15 -> 13. P1 10 -> 9.
    # Distance 5 -> 4. Applying.
    result = calculate_aspect_movement(10, 15, 0, -1, -2)
    assert result == "Applying"

def test_exact_aspect_separating():
    # Sun 10. Moon 130. Aspect 120.
    # Exact.
    # Moon moves 13, Sun 1.
    # Moon moves away from 130. Separating.
    result = calculate_aspect_movement(10, 130, 120, 1, 13)
    assert result == "Separating"

def test_exact_aspect_retrograde_separating():
    # Sun 10. Merc 10. Aspect 0.
    # Merc -1. Sun 1.
    # Merc moves to 9. Sun to 11.
    # Separating.
    result = calculate_aspect_movement(10, 10, 0, 1, -1)
    assert result == "Separating"

def test_180_separation_bug():
    # P1 0. P2 180. Aspect 120.
    # P2 moves +1 (to 181/-179).
    # Distance 180 -> 179.
    # Orb 60 -> 59.
    # Should be Applying.
    result = calculate_aspect_movement(0, 180, 120, 0, 1)
    assert result == "Applying"
