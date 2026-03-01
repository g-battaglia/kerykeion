"""
Comprehensive tests for PlanetaryReturnFactory.

Integrates all test cases from:
- tests/factories/test_planetary_return_factory_complete.py
- tests/factories/test_planetary_returns_parametrized.py

Covers initialization, solar/lunar returns, yearly succession,
return model attributes, validation errors, and default behaviour.
"""

import pytest
from datetime import datetime, timedelta, timezone

from kerykeion import AstrologicalSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.schemas import KerykeionException
from pytest import approx


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def johnny_depp():
    """Primary test subject: Johnny Depp (offline, explicit coordinates)."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Johnny Depp",
        1963,
        6,
        9,
        0,
        0,
        lat=37.7742,
        lng=-87.1133,
        tz_str="America/Chicago",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="module")
def secondary_subject():
    """Secondary test subject for cross-validation."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Test Subject",
        1990,
        6,
        15,
        12,
        30,
        lat=40.7128,
        lng=-74.006,
        tz_str="America/New_York",
        online=False,
        suppress_geonames_warning=True,
    )


# New York coordinates used across many tests
NY_LAT = 40.7128
NY_LNG = -74.006
NY_TZ = "America/New_York"

# Rome coordinates
ROME_LAT = 41.9028
ROME_LNG = 12.4964
ROME_TZ = "Europe/Rome"


def _angular_diff(a: float, b: float) -> float:
    """Compute the shortest angular distance between two positions on a 360° circle."""
    diff = abs(a - b) % 360
    return min(diff, 360 - diff)


# ===========================================================================
# 1. TestInitialization
# ===========================================================================


class TestInitialization:
    """Verify factory construction under various parameter combinations."""

    def test_init_with_explicit_coordinates(self, johnny_depp):
        """Initialization with lat/lng/tz_str and online=False succeeds."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        assert factory.lat == NY_LAT
        assert factory.lng == NY_LNG
        assert factory.tz_str == NY_TZ
        assert factory.online is False

    def test_init_stores_subject(self, johnny_depp):
        """The natal subject is preserved on the factory."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        assert factory.subject is johnny_depp
        assert factory.subject.name == "Johnny Depp"

    def test_missing_location_info_raises(self, johnny_depp):
        """Omitting all location info raises KerykeionException."""
        with pytest.raises(KerykeionException):
            PlanetaryReturnFactory(johnny_depp)

    def test_online_false_without_coordinates_raises(self, johnny_depp):
        """online=False without lat/lng/tz_str raises KerykeionException."""
        with pytest.raises(KerykeionException):
            PlanetaryReturnFactory(johnny_depp, online=False)

    def test_online_false_missing_lat_raises(self, johnny_depp):
        """Missing latitude in offline mode raises KerykeionException."""
        with pytest.raises(KerykeionException):
            PlanetaryReturnFactory(
                johnny_depp,
                lng=NY_LNG,
                tz_str=NY_TZ,
                online=False,
            )

    def test_online_false_missing_lng_raises(self, johnny_depp):
        """Missing longitude in offline mode raises KerykeionException."""
        with pytest.raises(KerykeionException):
            PlanetaryReturnFactory(
                johnny_depp,
                lat=NY_LAT,
                tz_str=NY_TZ,
                online=False,
            )

    def test_online_false_missing_tz_str_raises(self, johnny_depp):
        """Missing timezone in offline mode raises KerykeionException."""
        with pytest.raises(KerykeionException):
            PlanetaryReturnFactory(
                johnny_depp,
                lat=NY_LAT,
                lng=NY_LNG,
                online=False,
            )

    def test_online_true_missing_city_raises(self, johnny_depp):
        """online=True without city raises KerykeionException."""
        with pytest.raises(KerykeionException):
            PlanetaryReturnFactory(
                johnny_depp,
                city=None,
                nation="US",
                online=True,
            )

    def test_online_true_missing_nation_raises(self, johnny_depp):
        """online=True without nation raises KerykeionException."""
        with pytest.raises(KerykeionException):
            PlanetaryReturnFactory(
                johnny_depp,
                city="New York",
                nation=None,
                online=True,
            )

    def test_factory_has_expected_methods(self, johnny_depp):
        """Factory exposes all public calculation methods."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        assert callable(getattr(factory, "next_return_from_date", None))
        assert callable(getattr(factory, "next_return_from_iso_formatted_time", None))
        assert callable(getattr(factory, "next_return_from_year", None))

    def test_altitude_stored(self, johnny_depp):
        """Altitude parameter is stored on factory."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
            altitude=250.0,
        )
        assert factory.altitude == 250.0

    def test_init_with_rome_coordinates(self, johnny_depp):
        """Initialization with a different set of coordinates succeeds."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=ROME_LAT,
            lng=ROME_LNG,
            tz_str=ROME_TZ,
            online=False,
        )
        assert factory.lat == ROME_LAT
        assert factory.lng == ROME_LNG
        assert factory.tz_str == ROME_TZ


# ===========================================================================
# 2. TestSolarReturn
# ===========================================================================


class TestSolarReturn:
    """Solar return accuracy and date ordering."""

    @pytest.fixture()
    def solar_factory(self, johnny_depp):
        return PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )

    def test_solar_return_is_not_none(self, solar_factory):
        """next_return_from_date for Sun returns a non-None result."""
        result = solar_factory.next_return_from_date(2024, 1, 1, return_type="Solar")
        assert result is not None

    def test_solar_return_sun_matches_natal(self, solar_factory, johnny_depp):
        """Return sun position is within 0.1° of the natal sun position."""
        result = solar_factory.next_return_from_date(2024, 1, 1, return_type="Solar")
        diff = _angular_diff(result.sun.abs_pos, johnny_depp.sun.abs_pos)
        assert diff < 0.1, (
            f"Solar return Sun {result.sun.abs_pos}° differs from natal {johnny_depp.sun.abs_pos}° by {diff}°"
        )

    def test_solar_return_after_search_date(self, solar_factory):
        """The return datetime falls after the search start date."""
        result = solar_factory.next_return_from_date(2024, 1, 1, return_type="Solar")
        return_dt = datetime.fromisoformat(result.iso_formatted_utc_datetime)
        assert return_dt >= datetime(2024, 1, 1, tzinfo=timezone.utc)

    def test_solar_return_year_matches(self, solar_factory):
        """Solar return should occur within the same year or the next."""
        result = solar_factory.next_return_from_date(2024, 1, 1, return_type="Solar")
        return_dt = datetime.fromisoformat(result.iso_formatted_utc_datetime)
        assert return_dt.year in (2024, 2025)

    @pytest.mark.parametrize("year", [2020, 2021, 2022, 2023, 2024, 2025])
    def test_solar_return_for_multiple_years(self, solar_factory, johnny_depp, year):
        """Sun position matches natal across several years."""
        result = solar_factory.next_return_from_date(year, 1, 1, return_type="Solar")
        diff = _angular_diff(result.sun.abs_pos, johnny_depp.sun.abs_pos)
        assert diff < 0.1

    def test_solar_return_with_secondary_subject(self, secondary_subject):
        """Solar return works with a different natal subject."""
        factory = PlanetaryReturnFactory(
            secondary_subject,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        result = factory.next_return_from_date(2023, 1, 1, return_type="Solar")
        diff = _angular_diff(result.sun.abs_pos, secondary_subject.sun.abs_pos)
        assert diff < 0.1

    def test_solar_return_different_locations_same_sun(self, johnny_depp):
        """Sun position is the same regardless of return location; houses differ."""
        factory_ny = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        factory_rome = PlanetaryReturnFactory(
            johnny_depp,
            lat=ROME_LAT,
            lng=ROME_LNG,
            tz_str=ROME_TZ,
            online=False,
        )
        ret_ny = factory_ny.next_return_from_date(2024, 1, 1, return_type="Solar")
        ret_rome = factory_rome.next_return_from_date(2024, 1, 1, return_type="Solar")

        # Sun position identical (same moment)
        assert abs(ret_ny.sun.abs_pos - ret_rome.sun.abs_pos) < 0.01
        # Ascendant differs due to location
        assert abs(ret_ny.ascendant.abs_pos - ret_rome.ascendant.abs_pos) > 1


# ===========================================================================
# 3. TestLunarReturn
# ===========================================================================


class TestLunarReturn:
    """Lunar return accuracy and cycle period."""

    @pytest.fixture()
    def lunar_factory(self, johnny_depp):
        return PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )

    def test_lunar_return_is_not_none(self, lunar_factory):
        result = lunar_factory.next_return_from_date(2024, 1, 1, return_type="Lunar")
        assert result is not None

    def test_lunar_return_moon_matches_natal(self, lunar_factory, johnny_depp):
        """Return moon position is within 0.1° of the natal moon."""
        result = lunar_factory.next_return_from_date(2024, 1, 1, return_type="Lunar")
        diff = _angular_diff(result.moon.abs_pos, johnny_depp.moon.abs_pos)
        assert diff < 0.1, (
            f"Lunar return Moon {result.moon.abs_pos}° differs from natal {johnny_depp.moon.abs_pos}° by {diff}°"
        )

    def test_lunar_return_after_search_date(self, lunar_factory):
        result = lunar_factory.next_return_from_date(2024, 3, 15, return_type="Lunar")
        return_dt = datetime.fromisoformat(result.iso_formatted_utc_datetime)
        assert return_dt >= datetime(2024, 3, 15, tzinfo=timezone.utc)

    def test_lunar_cycle_period_approx_27_days(self, lunar_factory):
        """Two successive lunar returns are ~27.3 days apart."""
        first = lunar_factory.next_return_from_date(2024, 1, 1, return_type="Lunar")
        first_dt = datetime.fromisoformat(first.iso_formatted_utc_datetime)
        next_start = first_dt + timedelta(days=1)

        second = lunar_factory.next_return_from_date(
            next_start.year,
            next_start.month,
            next_start.day,
            return_type="Lunar",
        )

        days_diff = second.julian_day - first.julian_day
        assert 26 < days_diff < 29, f"Unexpected lunar return period: {days_diff} days"

    def test_two_lunar_returns_differ(self, lunar_factory):
        """Lunar returns from different start dates produce different datetimes."""
        first = lunar_factory.next_return_from_date(2024, 1, 1, return_type="Lunar")
        second = lunar_factory.next_return_from_date(2024, 1, 20, return_type="Lunar")
        assert first.iso_formatted_utc_datetime != second.iso_formatted_utc_datetime

    def test_lunar_returns_monthly_coverage(self, lunar_factory):
        """Searching from month-start for each month yields mostly unique returns."""
        julian_days = []
        for month in range(1, 13):
            ret = lunar_factory.next_return_from_date(2024, month, 1, return_type="Lunar")
            julian_days.append(round(ret.julian_day, 2))
        unique = set(julian_days)
        # ~27 day cycle → at least 11 unique returns from 12 monthly searches
        assert len(unique) >= 11

    def test_lunar_return_with_secondary_subject(self, secondary_subject):
        factory = PlanetaryReturnFactory(
            secondary_subject,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        result = factory.next_return_from_date(2023, 1, 1, return_type="Lunar")
        diff = _angular_diff(result.moon.abs_pos, secondary_subject.moon.abs_pos)
        assert diff < 0.1


# ===========================================================================
# 4. TestYearlySuccession
# ===========================================================================


class TestYearlySuccession:
    """Successive solar returns are ~365.25 days apart."""

    def test_successive_solar_returns_spacing(self, johnny_depp):
        """Adjacent solar returns are approximately 365.25 days apart."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )

        returns = []
        for year in range(2020, 2026):
            ret = factory.next_return_from_date(year, 1, 1, return_type="Solar")
            returns.append(ret)

        for i in range(1, len(returns)):
            days_diff = returns[i].julian_day - returns[i - 1].julian_day
            assert days_diff == approx(365.25, abs=1.5), (
                f"Gap between {2020 + i - 1} and {2020 + i} solar returns is {days_diff} days (expected ~365.25)"
            )

    def test_return_occurs_near_birthday(self, johnny_depp):
        """Solar return occurs within a couple of days of the birthday (June 9)."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        for year in [2022, 2023, 2024]:
            ret = factory.next_return_from_date(year, 1, 1, return_type="Solar")
            return_dt = datetime.fromisoformat(ret.iso_formatted_utc_datetime)
            birthday = datetime(year, 6, 9, tzinfo=timezone.utc)
            delta = abs((return_dt - birthday).days)
            assert delta <= 2, f"Solar return in {year} on {return_dt.date()} is {delta} days from birthday Jun 9"


# ===========================================================================
# 5. TestReturnModelAttributes
# ===========================================================================


class TestReturnModelAttributes:
    """Return model exposes all expected astrological attributes."""

    @pytest.fixture()
    def solar_return(self, johnny_depp):
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        return factory.next_return_from_date(2024, 1, 1, return_type="Solar")

    @pytest.fixture()
    def lunar_return(self, johnny_depp):
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        return factory.next_return_from_date(2024, 1, 1, return_type="Lunar")

    # -- Planets --

    @pytest.mark.parametrize(
        "planet",
        [
            "sun",
            "moon",
            "mercury",
            "venus",
            "mars",
            "jupiter",
            "saturn",
            "uranus",
            "neptune",
            "pluto",
        ],
    )
    def test_solar_return_has_planet(self, solar_return, planet):
        assert getattr(solar_return, planet) is not None

    @pytest.mark.parametrize(
        "planet",
        [
            "sun",
            "moon",
            "mercury",
            "venus",
            "mars",
            "jupiter",
            "saturn",
            "uranus",
            "neptune",
            "pluto",
        ],
    )
    def test_lunar_return_has_planet(self, lunar_return, planet):
        assert getattr(lunar_return, planet) is not None

    # -- Houses --

    @pytest.mark.parametrize(
        "house",
        [
            "first_house",
            "second_house",
            "third_house",
            "fourth_house",
            "fifth_house",
            "sixth_house",
            "seventh_house",
            "eighth_house",
            "ninth_house",
            "tenth_house",
            "eleventh_house",
            "twelfth_house",
        ],
    )
    def test_solar_return_has_house(self, solar_return, house):
        val = getattr(solar_return, house)
        assert val is not None
        assert hasattr(val, "abs_pos")

    # -- Axes --

    def test_has_ascendant(self, solar_return):
        assert solar_return.ascendant is not None

    def test_has_medium_coeli(self, solar_return):
        assert solar_return.medium_coeli is not None

    # -- Metadata --

    def test_name_contains_return_label(self, solar_return):
        assert "Solar Return" in solar_return.name

    def test_lunar_return_name(self, lunar_return):
        assert "Lunar Return" in lunar_return.name

    def test_return_type_field(self, solar_return, lunar_return):
        assert solar_return.return_type == "Solar"
        assert lunar_return.return_type == "Lunar"

    def test_has_julian_day(self, solar_return):
        assert solar_return.julian_day is not None
        assert isinstance(solar_return.julian_day, float)

    def test_has_iso_utc_datetime(self, solar_return):
        assert solar_return.iso_formatted_utc_datetime is not None
        # Should be parseable
        datetime.fromisoformat(solar_return.iso_formatted_utc_datetime)

    def test_has_iso_local_datetime(self, solar_return):
        assert solar_return.iso_formatted_local_datetime is not None
        datetime.fromisoformat(solar_return.iso_formatted_local_datetime)

    def test_has_zodiac_type(self, solar_return):
        assert solar_return.zodiac_type is not None

    def test_has_houses_system_identifier(self, solar_return):
        assert solar_return.houses_system_identifier is not None

    def test_has_perspective_type(self, solar_return):
        assert solar_return.perspective_type is not None

    def test_model_dump_roundtrip(self, solar_return):
        """model_dump produces a dict that contains all key fields."""
        data = solar_return.model_dump()
        assert "sun" in data
        assert "moon" in data
        assert "return_type" in data
        assert "first_house" in data

    def test_planet_abs_pos_range(self, solar_return):
        """All planet abs_pos values lie in [0, 360)."""
        for planet_name in (
            "sun",
            "moon",
            "mercury",
            "venus",
            "mars",
            "jupiter",
            "saturn",
            "uranus",
            "neptune",
            "pluto",
        ):
            planet = getattr(solar_return, planet_name)
            if planet is not None:
                assert 0 <= planet.abs_pos < 360, f"{planet_name} abs_pos={planet.abs_pos} out of range"


# ===========================================================================
# 6. TestValidationErrors
# ===========================================================================


class TestValidationErrors:
    """Invalid parameters raise the appropriate exceptions."""

    @pytest.fixture()
    def factory(self, johnny_depp):
        return PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )

    def test_invalid_return_type_raises(self, factory):
        """An unrecognised return_type raises KerykeionException."""
        with pytest.raises(KerykeionException, match="Invalid return type"):
            factory.next_return_from_iso_formatted_time(
                "2024-01-01T00:00:00+00:00",
                "Mercury",  # type: ignore
            )

    def test_invalid_month_raises(self, factory):
        with pytest.raises(KerykeionException, match="Invalid month"):
            factory.next_return_from_date(2024, 13, 1, return_type="Solar")

    def test_month_zero_raises(self, factory):
        with pytest.raises(KerykeionException, match="Invalid month"):
            factory.next_return_from_date(2024, 0, 1, return_type="Solar")

    def test_invalid_day_raises(self, factory):
        """Feb 30 is never valid."""
        with pytest.raises(KerykeionException, match="Invalid day 30"):
            factory.next_return_from_date(2024, 2, 30, return_type="Lunar")

    def test_day_zero_raises(self, factory):
        with pytest.raises(KerykeionException, match="Invalid day 0"):
            factory.next_return_from_date(2024, 6, 0, return_type="Solar")

    def test_feb_29_non_leap_year_raises(self, factory):
        """Feb 29 in a non-leap year is invalid."""
        with pytest.raises(KerykeionException, match="Invalid day 29"):
            factory.next_return_from_date(2023, 2, 29, return_type="Solar")

    def test_feb_29_leap_year_ok(self, factory):
        """Feb 29 in a leap year is valid and should not raise."""
        result = factory.next_return_from_date(2024, 2, 29, return_type="Lunar")
        assert result is not None


# ===========================================================================
# 7. TestNextReturnFromDateDefault
# ===========================================================================


class TestNextReturnFromDateDefault:
    """Behaviour when optional parameters are at their defaults."""

    def test_day_defaults_to_one(self, johnny_depp):
        """Omitting day uses 1 as default; result equals explicit day=1."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        result_default = factory.next_return_from_date(2024, 6, return_type="Solar")
        result_explicit = factory.next_return_from_date(2024, 6, 1, return_type="Solar")
        assert result_default.julian_day == approx(result_explicit.julian_day, abs=1e-6)

    def test_iso_formatted_time_current_date(self, johnny_depp):
        """next_return_from_iso_formatted_time accepts the current datetime."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        now_iso = datetime.now(timezone.utc).isoformat()
        result = factory.next_return_from_iso_formatted_time(now_iso, "Solar")
        assert result is not None
        return_dt = datetime.fromisoformat(result.iso_formatted_utc_datetime)
        assert return_dt > datetime.now(timezone.utc) - timedelta(days=1)

    def test_from_iso_solar_and_from_date_agree(self, johnny_depp):
        """next_return_from_date and next_return_from_iso_formatted_time match."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        via_date = factory.next_return_from_date(2024, 1, 1, return_type="Solar")
        via_iso = factory.next_return_from_iso_formatted_time("2024-01-01T00:00:00+00:00", "Solar")
        assert via_date.julian_day == approx(via_iso.julian_day, abs=1e-6)

    def test_deprecated_next_return_from_year(self, johnny_depp):
        """next_return_from_year still works but emits DeprecationWarning."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        with pytest.warns(DeprecationWarning, match="deprecated"):
            result = factory.next_return_from_year(2024, "Solar")
        assert result is not None


# ===========================================================================
# Additional integration / edge-case tests
# ===========================================================================


class TestAdditionalIntegration:
    """Extra integration tests ported from the parametrized suite."""

    def test_future_date_return(self, johnny_depp):
        """Solar return can be calculated for a far-future date (2050)."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        result = factory.next_return_from_date(2050, 1, 1, return_type="Solar")
        assert result is not None
        return_dt = datetime.fromisoformat(result.iso_formatted_utc_datetime)
        assert return_dt.year == 2050

    def test_multiple_return_types_on_same_factory(self, johnny_depp):
        """A single factory can compute both solar and lunar returns."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        solar = factory.next_return_from_date(2024, 1, 1, return_type="Solar")
        lunar = factory.next_return_from_date(2024, 1, 1, return_type="Lunar")
        assert solar.return_type == "Solar"
        assert lunar.return_type == "Lunar"
        # They should produce different datetimes
        assert solar.julian_day != lunar.julian_day

    def test_consistency_across_repeated_calls(self, johnny_depp):
        """Calling the same computation twice yields identical results."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        a = factory.next_return_from_date(2024, 3, 10, return_type="Lunar")
        b = factory.next_return_from_date(2024, 3, 10, return_type="Lunar")
        assert a.julian_day == b.julian_day
        assert a.moon.abs_pos == b.moon.abs_pos

    def test_return_from_iso_formatted_time_solar(self, johnny_depp):
        """next_return_from_iso_formatted_time produces a valid solar return."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        result = factory.next_return_from_iso_formatted_time("2023-06-15T12:00:00", "Solar")
        assert result is not None
        assert result.sun is not None
        diff = _angular_diff(result.sun.abs_pos, johnny_depp.sun.abs_pos)
        assert diff < 0.1

    def test_return_from_iso_formatted_time_lunar(self, johnny_depp):
        """next_return_from_iso_formatted_time produces a valid lunar return."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=ROME_LAT,
            lng=ROME_LNG,
            tz_str=ROME_TZ,
            online=False,
        )
        result = factory.next_return_from_iso_formatted_time("2023-03-01T00:00:00", "Lunar")
        assert result is not None
        diff = _angular_diff(result.moon.abs_pos, johnny_depp.moon.abs_pos)
        assert diff < 0.1


# =============================================================================
# DEPRECATED API + ONLINE MODE (from edge_cases + factories)
# =============================================================================


class TestDeprecatedReturnAPIs:
    """Test deprecated PlanetaryReturnFactory methods."""

    @pytest.fixture()
    def _factory(self):
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Test",
            1990,
            6,
            15,
            12,
            0,
            lat=41.9,
            lng=12.5,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
        )
        return PlanetaryReturnFactory(
            subject,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )

    def test_next_return_from_month_and_year_deprecation(self, _factory):
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _factory.next_return_from_month_and_year(2024, 6, "Solar")
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) > 0
            assert result is not None


class TestPlanetaryReturnOnlineMode:
    """Test online-mode initialization parameters."""

    def test_factory_default_online_true(self):
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Test",
            1990,
            6,
            15,
            12,
            0,
            lat=41.9,
            lng=12.5,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
        )
        # Default online should be True
        factory = PlanetaryReturnFactory(subject, city="Rome", nation="IT")
        assert factory.online is True
