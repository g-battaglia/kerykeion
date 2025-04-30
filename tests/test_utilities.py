from kerykeion import KerykeionException
from kerykeion.utilities import is_point_between, julian_to_datetime, datetime_to_julian
import pytest
import math
from datetime import datetime, timezone


class TestUtilities:

    def setup_class(self):
        pass

    def test_is_point_between(self):
        assert is_point_between(10, 30, 25) is True
        assert is_point_between(10, 30, 35) is False
        assert is_point_between(10, 30, 4) is False

        assert is_point_between(340, 10, 350) is True
        assert is_point_between(340, 10, 4) is True
        assert is_point_between(340, 10, 320) is False
        assert is_point_between(340, 10, 20) is False

        # Edge cases
        assert is_point_between(10, 30, 10) is True
        assert is_point_between(10, 30, 30) is False

        assert is_point_between(340, 10, 340) is True
        assert is_point_between(340, 10, 10) is False

        assert is_point_between(0, 20, 0) is True
        assert is_point_between(0, 20, 20) is False

        assert is_point_between(340, 360, 340) is True
        assert is_point_between(340, 360, 360) is False

        assert is_point_between(360, 20, 0) is True
        assert is_point_between(360, 20, 20) is False
        assert is_point_between(360, 20, 360) is True

        assert is_point_between(340, 0, 340) is True
        assert is_point_between(340, 0, 0) is False
        assert is_point_between(360, 20, 360) is True

        assert is_point_between(10, 30, 10.00000000001) is True
        assert is_point_between(10, 30, 9.999999999999) is False
        assert is_point_between(10, 30, 29.999999999999) is True
        assert is_point_between(10, 30, 30.00000000001) is False

        assert is_point_between(97.89789490940346, 116.14575774583493, 97.89789490940348) is True
        assert is_point_between(97.89789490940346, 116.14575774583493, 97.89789490940340) is False
        assert is_point_between(97.89789490940346, 116.14575774583493, 116.14575774583490) is True
        assert is_point_between(97.89789490940346, 116.14575774583493, 116.14575774583496) is False


    def test_is_point_between_with_exception(self):
        with pytest.raises(KerykeionException) as ex:
            is_point_between(5, 200, 15)
            assert str(ex.value).startswith("The angle between start and end point is not allowed to exceed 180°")

        with pytest.raises(KerykeionException) as ex:
            is_point_between(250, 200, 15)
            assert str(ex.value).startswith("The angle between start and end point is not allowed to exceed 180°")

        with pytest.raises(KerykeionException) as ex:
            is_point_between(0, 180.1, 15)
            assert str(ex.value).startswith("The angle between start and end point is not allowed to exceed 180°")

        with pytest.raises(KerykeionException) as ex:
            is_point_between(359.9, 180, 15)
            assert str(ex.value).startswith("The angle between start and end point is not allowed to exceed 180°")


    def test_julian_to_datetime(self):
        # Test with a known Julian date
        julian_date = 2451545.0
        expected_datetime = datetime(2000, 1, 1, 12, 0)
        result = julian_to_datetime(julian_date)
        delta = abs((result - expected_datetime).total_seconds())
        assert delta < 1, f"Expected {expected_datetime}, but got {result} (Δ={delta:.6f}s)"

        # Test with a Julian date that is not an integer
        julian_date = 2460795.413194
        expected_datetime = datetime(2025, 4, 29, 21, 54, 59)
        result = julian_to_datetime(julian_date)
        delta = abs((result - expected_datetime).total_seconds())
        assert delta < 1, f"Expected {expected_datetime}, but got {result} (Δ={delta:.6f}s)"


    def test_datetime_to_julian(self):
        # Test with a known datetime
        dt = datetime(2000, 1, 1, 12, 0)
        expected_julian = 2451545.0
        result = datetime_to_julian(dt)
        assert math.isclose(result, expected_julian, rel_tol=1e-9), f"Expected {expected_julian}, but got {result}"

        # Test with a datetime that is not at noon
        dt = datetime(2025, 4, 29, 21, 54, 59)
        expected_julian = 2460795.413194
        result = datetime_to_julian(dt)
        assert math.isclose(result, expected_julian, rel_tol=1e-9), f"Expected {expected_julian}, but got {result}"


    def test_julian_to_datetime_and_back(self):
        julian_date = 2451545.0
        dt = julian_to_datetime(julian_date)
        result = datetime_to_julian(dt)
        assert result == julian_date, f"Expected {julian_date}, but got {result}"

        # Test with a Julian date that is not an integer
        julian_date = 2460795.413194
        dt = julian_to_datetime(julian_date)
        result = datetime_to_julian(dt)
        assert result == julian_date, f"Expected {julian_date}, but got {result}"

if __name__ == "__main__":
    pytest.main([__file__])
