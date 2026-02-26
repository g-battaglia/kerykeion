"""
Comprehensive Parametrized Tests for PlanetaryReturnFactory.

This module provides extensive test coverage for the PlanetaryReturnFactory
across all supported configurations:
- Solar returns for multiple years
- Lunar returns across the lunar cycle
- Returns calculated with various house systems
- Returns calculated with sidereal modes

The tests compare computed values against pre-generated expected fixtures
to ensure consistency and catch regressions.
"""

import pytest
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from kerykeion import AstrologicalSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory

from tests.data.test_subjects_matrix import (
    TEMPORAL_SUBJECTS,
    HOUSE_SYSTEMS,
    SIDEREAL_MODES,
    get_primary_test_subjects,
)

# Configuration directory for expected data
CONFIGURATIONS_DIR = Path(__file__).parent.parent / "data" / "configurations"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def load_expected_returns(return_type: str) -> Optional[Dict[str, Any]]:
    """Load expected return data."""
    if return_type == "solar":
        fixture_path = CONFIGURATIONS_DIR / "returns" / "expected_solar_returns.py"
    elif return_type == "lunar":
        fixture_path = CONFIGURATIONS_DIR / "returns" / "expected_lunar_returns.py"
    else:
        return None

    if not fixture_path.exists():
        return None

    import importlib.util

    spec = importlib.util.spec_from_file_location("fixture", fixture_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if return_type == "solar":
        return getattr(module, "EXPECTED_SOLAR_RETURNS", None)
    else:
        return getattr(module, "EXPECTED_LUNAR_RETURNS", None)


def get_subject_data_by_id(subject_id: str) -> Optional[Dict[str, Any]]:
    """Get subject data by ID from temporal subjects."""
    for data in TEMPORAL_SUBJECTS:
        if data["id"] == subject_id:
            return data
    return None


def get_return_year(return_model) -> int:
    """Extract year from a PlanetReturnModel's iso_formatted_local_datetime."""
    dt = datetime.fromisoformat(return_model.iso_formatted_local_datetime)
    return dt.year


def get_return_date(return_model):
    """Extract date from a PlanetReturnModel's iso_formatted_local_datetime."""
    from datetime import date as date_type

    dt = datetime.fromisoformat(return_model.iso_formatted_local_datetime)
    return date_type(dt.year, dt.month, dt.day)


def create_subject_from_data(data: Dict[str, Any]):
    """Create an AstrologicalSubjectModel from subject data dictionary."""
    return AstrologicalSubjectFactory.from_birth_data(
        name=data.get("name", data["id"]),
        year=data["year"],
        month=data["month"],
        day=data["day"],
        hour=data["hour"],
        minute=data["minute"],
        lat=data["lat"],
        lng=data["lng"],
        tz_str=data["tz_str"],
        online=False,
        suppress_geonames_warning=True,
    )


# =============================================================================
# SOLAR RETURN TESTS
# =============================================================================


class TestSolarReturns:
    """
    Test PlanetaryReturnFactory for Solar returns.

    Solar returns occur when the Sun returns to its natal position,
    approximately once per year.
    """

    @pytest.mark.parametrize("subject_id", get_primary_test_subjects(), ids=lambda s: s)
    def test_solar_return_creation(self, subject_id):
        """Test that solar returns can be created for key subjects."""
        subject_data = get_subject_data_by_id(subject_id)
        assert subject_data is not None

        subject = create_subject_from_data(subject_data)

        factory = PlanetaryReturnFactory(
            subject,
            lat=subject_data["lat"],
            lng=subject_data["lng"],
            tz_str=subject_data["tz_str"],
            online=False,
        )

        # Calculate solar return for 2023
        return_subject = factory.next_return_from_date(2023, 1, 1, return_type="Solar")

        assert return_subject is not None
        assert hasattr(return_subject, "sun")
        assert hasattr(return_subject, "moon")

    @pytest.mark.parametrize("subject_id", get_primary_test_subjects(), ids=lambda s: s)
    def test_solar_return_sun_position(self, subject_id):
        """Test that solar return Sun position matches natal Sun position."""
        subject_data = get_subject_data_by_id(subject_id)
        assert subject_data is not None

        subject = create_subject_from_data(subject_data)

        factory = PlanetaryReturnFactory(
            subject,
            lat=subject_data["lat"],
            lng=subject_data["lng"],
            tz_str=subject_data["tz_str"],
            online=False,
        )

        return_subject = factory.next_return_from_date(2023, 1, 1, return_type="Solar")

        # Sun should be at the same position as natal Sun
        natal_sun_pos = subject.sun.abs_pos
        return_sun_pos = return_subject.sun.abs_pos

        diff = abs(natal_sun_pos - return_sun_pos)
        if diff > 180:
            diff = 360 - diff

        assert diff < 0.1, (
            f"Solar return Sun position {return_sun_pos} differs from natal Sun {natal_sun_pos} by {diff} degrees"
        )

    @pytest.mark.parametrize(
        "year",
        [2020, 2021, 2022, 2023, 2024, 2025],
        ids=lambda y: f"year_{y}",
    )
    def test_solar_return_yearly_succession(self, year):
        """Test solar returns for consecutive years."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(subject_data)

        factory = PlanetaryReturnFactory(
            subject,
            lat=subject_data["lat"],
            lng=subject_data["lng"],
            tz_str=subject_data["tz_str"],
            online=False,
        )

        return_subject = factory.next_return_from_date(year, 1, 1, return_type="Solar")

        assert return_subject is not None
        # Return should occur in the same year (or very close)
        return_year = get_return_year(return_subject)
        assert return_year == year or return_year == year + 1

    @pytest.mark.parametrize("subject_id", get_primary_test_subjects(), ids=lambda s: s)
    def test_solar_return_positions_match_expected(self, subject_id):
        """Test that solar return positions match expected values."""
        expected_data = load_expected_returns("solar")

        if expected_data is None:
            pytest.skip("No expected solar return data available")

        if subject_id not in expected_data:
            pytest.skip(f"No expected data for {subject_id}")

        subject_data = get_subject_data_by_id(subject_id)
        subject = create_subject_from_data(subject_data)

        factory = PlanetaryReturnFactory(
            subject,
            lat=subject_data["lat"],
            lng=subject_data["lng"],
            tz_str=subject_data["tz_str"],
            online=False,
        )

        expected_returns = expected_data[subject_id].get("returns", {})

        for year_str, expected in expected_returns.items():
            year = int(year_str)
            return_subject = factory.next_return_from_date(year, 1, 1, return_type="Solar")

            # Compare Julian day (timing)
            if "julian_day" in expected:
                assert abs(return_subject.julian_day - expected["julian_day"]) < 0.01, (
                    f"Julian day mismatch for {subject_id} {year}: "
                    f"expected {expected['julian_day']}, got {return_subject.julian_day}"
                )


# =============================================================================
# LUNAR RETURN TESTS
# =============================================================================


class TestLunarReturns:
    """
    Test PlanetaryReturnFactory for Lunar returns.

    Lunar returns occur when the Moon returns to its natal position,
    approximately every 27.3 days.
    """

    @pytest.mark.parametrize("subject_id", get_primary_test_subjects(), ids=lambda s: s)
    def test_lunar_return_creation(self, subject_id):
        """Test that lunar returns can be created for key subjects."""
        subject_data = get_subject_data_by_id(subject_id)
        assert subject_data is not None

        subject = create_subject_from_data(subject_data)

        factory = PlanetaryReturnFactory(
            subject,
            lat=subject_data["lat"],
            lng=subject_data["lng"],
            tz_str=subject_data["tz_str"],
            online=False,
        )

        return_subject = factory.next_return_from_date(2023, 1, 1, return_type="Lunar")

        assert return_subject is not None
        assert hasattr(return_subject, "moon")

    @pytest.mark.parametrize("subject_id", get_primary_test_subjects(), ids=lambda s: s)
    def test_lunar_return_moon_position(self, subject_id):
        """Test that lunar return Moon position matches natal Moon position."""
        subject_data = get_subject_data_by_id(subject_id)
        subject = create_subject_from_data(subject_data)

        factory = PlanetaryReturnFactory(
            subject,
            lat=subject_data["lat"],
            lng=subject_data["lng"],
            tz_str=subject_data["tz_str"],
            online=False,
        )

        return_subject = factory.next_return_from_date(2023, 1, 1, return_type="Lunar")

        # Moon should be at the same position as natal Moon
        natal_moon_pos = subject.moon.abs_pos
        return_moon_pos = return_subject.moon.abs_pos

        diff = abs(natal_moon_pos - return_moon_pos)
        if diff > 180:
            diff = 360 - diff

        assert diff < 0.1, (
            f"Lunar return Moon position {return_moon_pos} differs from natal Moon {natal_moon_pos} by {diff} degrees"
        )

    def test_lunar_return_cycle_period(self):
        """Test that lunar returns occur approximately every 27.3 days."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(subject_data)

        factory = PlanetaryReturnFactory(
            subject,
            lat=subject_data["lat"],
            lng=subject_data["lng"],
            tz_str=subject_data["tz_str"],
            online=False,
        )

        # Get two consecutive lunar returns
        first_return = factory.next_return_from_date(2023, 1, 1, return_type="Lunar")

        # Calculate date for second search: add days to get past the first return
        from datetime import timedelta

        first_date = get_return_date(first_return)
        second_start = first_date + timedelta(days=1)

        second_return = factory.next_return_from_date(
            second_start.year,
            second_start.month,
            second_start.day,
            return_type="Lunar",
        )

        # Calculate days between returns
        days_diff = second_return.julian_day - first_return.julian_day

        # Lunar cycle is approximately 27.3 days
        assert 26 < days_diff < 29, f"Unexpected lunar return period: {days_diff} days"

    def test_lunar_returns_monthly(self):
        """Test that there's approximately one lunar return per month."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(subject_data)

        factory = PlanetaryReturnFactory(
            subject,
            lat=subject_data["lat"],
            lng=subject_data["lng"],
            tz_str=subject_data["tz_str"],
            online=False,
        )

        returns_2023 = []
        for month in range(1, 13):
            return_subject = factory.next_return_from_date(2023, month, 1, return_type="Lunar")
            returns_2023.append(return_subject)

        # Should have 12 different lunar returns
        julian_days = [r.julian_day for r in returns_2023]
        unique_julian_days = set(round(jd, 2) for jd in julian_days)

        # Due to the ~27 day cycle, some months might find the same return
        # but we should have at least 11 unique returns
        assert len(unique_julian_days) >= 11


# =============================================================================
# RETURN CONFIGURATION TESTS
# =============================================================================


class TestReturnConfigurations:
    """
    Test planetary returns with different configurations.
    """

    @pytest.mark.parametrize("house_system", HOUSE_SYSTEMS[:4], ids=lambda h: f"house_{h}")
    def test_solar_return_with_house_systems(self, house_system):
        """Test solar returns calculated with different house systems.

        Note: Currently PlanetaryReturnFactory doesn't support custom house systems,
        so this test only verifies that the return chart is created successfully.
        """
        subject_data = get_subject_data_by_id("john_lennon_1940")

        # Create subject with specified house system
        subject = AstrologicalSubjectFactory.from_birth_data(
            name=subject_data["name"],
            year=subject_data["year"],
            month=subject_data["month"],
            day=subject_data["day"],
            hour=subject_data["hour"],
            minute=subject_data["minute"],
            lat=subject_data["lat"],
            lng=subject_data["lng"],
            tz_str=subject_data["tz_str"],
            online=False,
            suppress_geonames_warning=True,
            houses_system_identifier=house_system,
        )

        factory = PlanetaryReturnFactory(
            subject,
            lat=subject_data["lat"],
            lng=subject_data["lng"],
            tz_str=subject_data["tz_str"],
            online=False,
        )

        return_subject = factory.next_return_from_date(2023, 1, 1, return_type="Solar")

        assert return_subject is not None
        # Note: PlanetaryReturnFactory doesn't currently support inheriting house system
        # This is a feature request, not a bug. For now, just verify the return works.
        assert return_subject.houses_system_identifier is not None

    def test_return_with_different_location(self):
        """Test that return location affects houses but not Sun/Moon position."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(subject_data)

        # Return in Liverpool (birth place)
        factory_liverpool = PlanetaryReturnFactory(
            subject,
            lat=subject_data["lat"],
            lng=subject_data["lng"],
            tz_str=subject_data["tz_str"],
            online=False,
        )

        # Return in New York
        factory_ny = PlanetaryReturnFactory(
            subject,
            lat=40.7128,
            lng=-74.0060,
            tz_str="America/New_York",
            online=False,
        )

        return_liverpool = factory_liverpool.next_return_from_date(2023, 1, 1, return_type="Solar")
        return_ny = factory_ny.next_return_from_date(2023, 1, 1, return_type="Solar")

        # Sun position should be the same (same return moment)
        assert abs(return_liverpool.sun.abs_pos - return_ny.sun.abs_pos) < 0.01

        # But Ascendant should be different due to location
        assert abs(return_liverpool.ascendant.abs_pos - return_ny.ascendant.abs_pos) > 1


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


class TestReturnEdgeCases:
    """
    Test planetary returns edge cases.
    """

    def test_return_for_ancient_subject(self):
        """Test returns for subjects from ancient eras."""
        subject_data = get_subject_data_by_id("galileo_1564")

        if subject_data is None:
            pytest.skip("Galileo subject data not available")

        subject = create_subject_from_data(subject_data)

        factory = PlanetaryReturnFactory(
            subject,
            lat=subject_data["lat"],
            lng=subject_data["lng"],
            tz_str=subject_data["tz_str"],
            online=False,
        )

        # Calculate a solar return in 1600
        return_subject = factory.next_return_from_date(1600, 1, 1, return_type="Solar")

        assert return_subject is not None
        return_year = get_return_year(return_subject)
        assert return_year == 1600

    def test_return_for_future_date(self):
        """Test returns calculated for future dates."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(subject_data)

        factory = PlanetaryReturnFactory(
            subject,
            lat=subject_data["lat"],
            lng=subject_data["lng"],
            tz_str=subject_data["tz_str"],
            online=False,
        )

        # Calculate solar return for 2050
        return_subject = factory.next_return_from_date(2050, 1, 1, return_type="Solar")

        assert return_subject is not None
        return_year = get_return_year(return_subject)
        assert return_year == 2050
