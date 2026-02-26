"""
Fixtures specific to core tests.

These fixtures provide helper utilities for planetary position
and house cusp testing.
"""

import pytest
from pytest import approx
from typing import Any, Dict, Optional

# Tolerance levels for position comparisons
POSITION_TOLERANCE = 1e-2  # 0.01 degrees (about 36 arcseconds)
SPEED_TOLERANCE = 1e-4  # For planetary speeds
DECLINATION_TOLERANCE = 1e-2  # For declinations


def assert_position_equal(actual: float, expected: float, abs_tol: float = POSITION_TOLERANCE) -> None:
    """Assert that two positions are equal within tolerance."""
    assert actual == approx(expected, abs=abs_tol), f"Position mismatch: got {actual}, expected {expected}"


def assert_positions_match(actual_point: Any, expected_data: Dict[str, Any]) -> None:
    """
    Assert that an actual point matches expected data dictionary.

    Args:
        actual_point: KerykeionPointModel from calculation
        expected_data: Dictionary with expected values
    """
    # Required attributes
    assert actual_point.name == expected_data["name"]
    assert actual_point.abs_pos == approx(expected_data["abs_pos"], abs=POSITION_TOLERANCE)
    assert actual_point.position == approx(expected_data["position"], abs=POSITION_TOLERANCE)
    assert actual_point.sign == expected_data["sign"]
    assert actual_point.sign_num == expected_data["sign_num"]

    # Optional attributes
    if "element" in expected_data:
        assert actual_point.element == expected_data["element"]
    if "quality" in expected_data:
        assert actual_point.quality == expected_data["quality"]
    if "retrograde" in expected_data and expected_data["retrograde"] is not None:
        assert actual_point.retrograde == expected_data["retrograde"]
    if "speed" in expected_data:
        assert actual_point.speed == approx(expected_data["speed"], abs=SPEED_TOLERANCE)
    if "declination" in expected_data:
        assert actual_point.declination == approx(expected_data["declination"], abs=DECLINATION_TOLERANCE)
    if "house" in expected_data and expected_data["house"] is not None:
        assert actual_point.house == expected_data["house"]
