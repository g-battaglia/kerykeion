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
from kerykeion.planetary_returns.factory import PlanetaryReturnFactory
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

    @pytest.mark.parametrize("bad_iso", ["", "not-a-date", "2024-13-01T00:00:00Z"])
    def test_malformed_iso_raises_kerykeion(self, factory, bad_iso):
        """Round 19: a malformed ISO timestamp on the *_from_iso_formatted_time
        entry points surfaces as KerykeionException, not a raw ValueError."""
        with pytest.raises(KerykeionException):
            factory.next_return_from_iso_formatted_time(bad_iso, "Solar")
        with pytest.raises(KerykeionException):
            factory.next_lunar_node_crossing_from_iso_formatted_time(bad_iso)

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


# ===========================================================================
# Sidereal returns (v6 regression)
# ===========================================================================


class TestSiderealReturns:
    """v6 regression: the crossing search must run in the natal zodiac.

    Before the fix, solcross_ut/mooncross_ut received the SIDEREAL natal
    abs_pos but searched TROPICAL longitudes, landing solar returns ~25 days
    off (the ayanamsa divided by the Sun's daily motion).
    """

    @pytest.fixture(scope="class")
    def sidereal_subject(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Return Test",
            1990,
            6,
            15,
            14,
            30,
            lat=ROME_LAT,
            lng=ROME_LNG,
            tz_str=ROME_TZ,
            online=False,
            suppress_geonames_warning=True,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
        )

    @pytest.fixture(scope="class")
    def sidereal_factory(self, sidereal_subject):
        return PlanetaryReturnFactory(
            sidereal_subject,
            lat=ROME_LAT,
            lng=ROME_LNG,
            tz_str=ROME_TZ,
            online=False,
        )

    def test_sidereal_solar_return_sun_matches_natal(self, sidereal_factory, sidereal_subject):
        """Return Sun abs_pos (sidereal) must equal the natal Sun within 1e-3°."""
        result = sidereal_factory.next_return_from_date(2024, 1, 1, return_type="Solar")
        diff = _angular_diff(result.sun.abs_pos, sidereal_subject.sun.abs_pos)
        assert diff < 1e-3, (
            f"Sidereal solar return Sun {result.sun.abs_pos}° differs from natal "
            f"{sidereal_subject.sun.abs_pos}° by {diff}° — crossing searched in the wrong zodiac"
        )

    def test_sidereal_solar_return_near_birthday(self, sidereal_factory):
        """The sidereal return is ~1 day per 72 years from the birthday, not ~25 days off."""
        result = sidereal_factory.next_return_from_date(2024, 1, 1, return_type="Solar")
        return_dt = datetime.fromisoformat(result.iso_formatted_utc_datetime)
        birthday = datetime(2024, 6, 15, tzinfo=timezone.utc)
        assert abs((return_dt - birthday).days) <= 3, (
            f"Sidereal solar return on {return_dt.date()} is too far from the birthday"
        )

    def test_sidereal_lunar_return_moon_matches_natal(self, sidereal_factory, sidereal_subject):
        result = sidereal_factory.next_return_from_date(2024, 1, 1, return_type="Lunar")
        diff = _angular_diff(result.moon.abs_pos, sidereal_subject.moon.abs_pos)
        assert diff < 1e-3, (
            f"Sidereal lunar return Moon {result.moon.abs_pos}° differs from natal "
            f"{sidereal_subject.moon.abs_pos}° by {diff}°"
        )

    def test_sidereal_return_chart_is_sidereal(self, sidereal_factory):
        result = sidereal_factory.next_return_from_date(2024, 1, 1, return_type="Solar")
        assert result.zodiac_type == "Sidereal"
        assert result.sidereal_mode == "LAHIRI"


# ===========================================================================
# Perspective-aware returns (v6 regression)
# ===========================================================================


class TestReturnPerspectivePropagation:
    """v6 regression: the crossing search must run in the natal perspective.

    Before the fix, the search session propagated the natal zodiac but NOT
    the natal perspective, so a "True Geocentric" natal Sun was searched
    against apparent-geocentric longitudes (return Sun ~0.0056° off, the
    annual aberration, i.e. ~8 minutes early) and a "Topocentric" natal Moon
    against geocentric longitudes (~0.319° off, the lunar parallax, i.e.
    ~35 minutes off).
    """

    def _make_subject(self, perspective_type):
        return AstrologicalSubjectFactory.from_birth_data(
            f"{perspective_type} Return Test",
            1990,
            6,
            15,
            12,
            30,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
            suppress_geonames_warning=True,
            perspective_type=perspective_type,
        )

    def _make_factory(self, subject):
        return PlanetaryReturnFactory(
            subject,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )

    def test_true_geocentric_solar_return_sun_matches_natal(self):
        """Return Sun (True Geocentric) must equal the natal Sun within 1e-3°.

        Pre-fix error was ~0.0056° (the aberration of light).
        """
        subject = self._make_subject("True Geocentric")
        factory = self._make_factory(subject)
        result = factory.next_return_from_date(2024, 1, 1, return_type="Solar")
        assert result.perspective_type == "True Geocentric"
        diff = _angular_diff(result.sun.abs_pos, subject.sun.abs_pos)
        assert diff < 1e-3, (
            f"True Geocentric solar return Sun {result.sun.abs_pos}° differs from natal "
            f"{subject.sun.abs_pos}° by {diff}° — crossing searched in the wrong perspective"
        )

    def test_true_geocentric_lunar_return_moon_matches_natal(self):
        subject = self._make_subject("True Geocentric")
        factory = self._make_factory(subject)
        result = factory.next_return_from_date(2024, 1, 1, return_type="Lunar")
        diff = _angular_diff(result.moon.abs_pos, subject.moon.abs_pos)
        assert diff < 1e-3, (
            f"True Geocentric lunar return Moon {result.moon.abs_pos}° differs from natal "
            f"{subject.moon.abs_pos}° by {diff}°"
        )

    def test_topocentric_lunar_return_moon_matches_natal(self):
        """Return Moon (Topocentric, return cast at the natal location) must
        equal the natal Moon within 1e-3°.

        Pre-fix error was ~0.319° (the lunar parallax at the natal latitude).
        """
        subject = self._make_subject("Topocentric")
        factory = self._make_factory(subject)
        result = factory.next_return_from_date(2024, 1, 1, return_type="Lunar")
        assert result.perspective_type == "Topocentric"
        diff = _angular_diff(result.moon.abs_pos, subject.moon.abs_pos)
        assert diff < 1e-3, (
            f"Topocentric lunar return Moon {result.moon.abs_pos}° differs from natal "
            f"{subject.moon.abs_pos}° by {diff}° — crossing searched without the natal topo frame"
        )

    def test_topocentric_solar_return_sun_matches_natal(self):
        subject = self._make_subject("Topocentric")
        factory = self._make_factory(subject)
        result = factory.next_return_from_date(2024, 1, 1, return_type="Solar")
        diff = _angular_diff(result.sun.abs_pos, subject.sun.abs_pos)
        assert diff < 1e-3, (
            f"Topocentric solar return Sun {result.sun.abs_pos}° differs from natal "
            f"{subject.sun.abs_pos}° by {diff}°"
        )

    def test_heliocentric_natal_raises_pointing_to_heliocentric_api(self):
        """A heliocentric natal has no geocentric crossing target — loud error."""
        subject = self._make_subject("Heliocentric")
        factory = self._make_factory(subject)
        with pytest.raises(KerykeionException, match="next_heliocentric_return"):
            factory.next_return_from_date(2024, 1, 1, return_type="Solar")
        with pytest.raises(KerykeionException, match="next_heliocentric_return"):
            factory.next_return_from_date(2024, 1, 1, return_type="Lunar")

    def test_heliocentric_natal_still_supports_heliocentric_returns(self):
        """The same factory must keep working through the heliocentric API."""
        subject = self._make_subject("Heliocentric")
        factory = self._make_factory(subject)
        result = factory.next_heliocentric_return_from_year("Mars", 2024)
        assert result.return_type == "Heliocentric"

    def test_unsupported_perspective_raises(self):
        """Perspectives the search cannot reproduce (e.g. Barycentric) raise."""
        subject = self._make_subject("Barycentric")
        factory = self._make_factory(subject)
        with pytest.raises(KerykeionException, match="Barycentric"):
            factory.next_return_from_date(2024, 1, 1, return_type="Solar")

    def test_heliocentric_return_sidereal_honors_frame(self):
        """A sidereal subject's heliocentric return must land where the planet's
        SIDEREAL heliocentric longitude equals the natal one — not the tropical
        one. Regression guard: ``helio_cross_ut`` honors FLG_SIDEREAL (unlike
        ``nod_aps_ut``), so masking the flag out would search a tropical
        crossing and land ~24° (the ayanamsa) off."""
        from kerykeion.ephemeris_backend import ephe, ephemeris_session

        subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Helio Return",
            1990,
            6,
            15,
            12,
            30,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
            suppress_geonames_warning=True,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
        )
        factory = PlanetaryReturnFactory(
            subject,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            city="New York",
            nation="US",
            online=False,
        )
        result = factory.next_heliocentric_return_from_year("Jupiter", 2001)
        assert result.return_type == "Heliocentric"

        # _build_return_chart casts a geocentric chart, so recompute the
        # heliocentric longitude at the natal/return instants ourselves.
        planet_id = ephe.JUPITER
        with ephemeris_session(zodiac_type="Sidereal", sidereal_mode="LAHIRI") as iflag:
            helio = iflag | ephe.FLG_HELCTR
            natal_sid = ephe.calc_ut(subject.julian_day, planet_id, helio)[0][0]
            ret_sid = ephe.calc_ut(result.julian_day, planet_id, helio)[0][0]
            ret_trop = ephe.calc_ut(result.julian_day, planet_id, helio & ~ephe.FLG_SIDEREAL)[0][0]

        # The return moment reproduces the natal SIDEREAL heliocentric longitude.
        assert _angular_diff(ret_sid, natal_sid) < 1e-2, (
            f"sidereal helio return off by {_angular_diff(ret_sid, natal_sid)}°"
        )
        # And it is genuinely sidereal: the tropical longitude there differs by
        # the ayanamsa (~24°), so a flag-masking 'fix' would have been ~24° off.
        assert _angular_diff(ret_trop, natal_sid) > 1.0


# ===========================================================================
# Timezone-aware ISO entry points (v6 regression)
# ===========================================================================


class TestAwareIsoEntryPoint:
    """Offset-aware ISO datetimes must be normalised to UTC before the search."""

    def test_offset_aware_iso_equals_utc_equivalent(self, johnny_depp):
        """'...T10:30:00+05:00' must give the same return as '...T05:30:00Z'."""
        factory = PlanetaryReturnFactory(
            johnny_depp,
            lat=NY_LAT,
            lng=NY_LNG,
            tz_str=NY_TZ,
            online=False,
        )
        with_offset = factory.next_return_from_iso_formatted_time("2024-01-01T10:30:00+05:00", "Lunar")
        utc_equiv = factory.next_return_from_iso_formatted_time("2024-01-01T05:30:00+00:00", "Lunar")
        assert with_offset.julian_day == approx(utc_equiv.julian_day, abs=1e-8)


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


class TestPlanetaryReturnV6FlagPropagation:
    """Regression: 6.0.0a44 → a45 — return charts ignored v6 calc flags."""

    def _make_natal(self, **kwargs):
        return AstrologicalSubjectFactory.from_birth_data(
            "Test V6 Return",
            1993,
            6,
            10,
            12,
            15,
            lat=45.41317,
            lng=10.39799,
            tz_str="Europe/Rome",
            city="Montichiari",
            nation="IT",
            online=False,
            suppress_geonames_warning=True,
            **kwargs,
        )

    def _make_factory(self, natal, **kwargs):
        return PlanetaryReturnFactory(
            natal,
            online=False,
            city="Montichiari",
            nation="IT",
            lng=10.39799,
            lat=45.41317,
            tz_str="Europe/Rome",
            **kwargs,
        )

    def test_solar_return_propagates_active_fixed_stars(self):
        natal = self._make_natal(active_fixed_stars=["Betelgeuse", "Vindemiatrix"])
        factory = self._make_factory(natal, active_fixed_stars=["Betelgeuse", "Vindemiatrix"])
        return_subj = factory.next_return_from_date(2026, 1, 1, return_type="Solar")
        names = {s.name for s in return_subj.fixed_stars}
        assert "Betelgeuse" in names
        assert "Vindemiatrix" in names

    def test_solar_return_propagates_calculate_dignities(self):
        natal = self._make_natal(calculate_dignities=True)
        factory = self._make_factory(natal, calculate_dignities=True)
        return_subj = factory.next_return_from_date(2026, 1, 1, return_type="Solar")
        # Every classical planet should carry an essential_dignity value
        # (Peregrine for un-dignified placements, never None when the flag
        # is set).
        assert return_subj.sun.essential_dignity is not None
        assert return_subj.moon.essential_dignity is not None

    def test_solar_return_dual_wheel_renders_without_indexerror(self):
        """Regression for the IndexError in _calculate_secondary_indicator_adjustments
        when the return subject's collected point count differs from
        active_points length."""
        from kerykeion.chart_data.factory import ChartDataFactory
        from kerykeion.charts.drawer import ChartDrawer

        natal = self._make_natal(active_fixed_stars=["Betelgeuse"])
        factory = self._make_factory(natal, active_fixed_stars=["Betelgeuse"])
        return_subj = factory.next_return_from_date(2026, 1, 1, return_type="Solar")
        data = ChartDataFactory.create_return_chart_data(natal, return_subj)
        svg = ChartDrawer(data).generate_wheel_only_svg_string()
        assert len(svg) > 0
        assert "<svg" in svg
        # Betelgeuse should be referenced in the chart (kr:slug on the wheel)
        assert "Betelgeuse" in svg

    def test_factory_defaults_keep_legacy_behaviour(self):
        """Caller that doesn't opt into v6 flags should not see any fixed
        star or dignity computed on the return — preserving pre-a45 behaviour
        for downstream consumers that haven't migrated yet."""
        natal = self._make_natal()
        factory = self._make_factory(natal)
        return_subj = factory.next_return_from_date(2026, 1, 1, return_type="Solar")
        assert return_subj.fixed_stars == []
        assert return_subj.sun.essential_dignity is None


class TestReturnFactoryOnlineGating:
    """Regression: online mode must fetch when ANY of tz_str/lat/lng is
    missing (an AND gate skipped the fetch for partial input, leaving None
    coordinates that crashed every return calculation) and must not overwrite
    the fields the caller provided."""

    def test_partial_input_fetches_and_preserves_tz(self, monkeypatch, johnny_depp):
        from kerykeion.geonames import fetcher

        rome = {"countryCode": "IT", "timezonestr": "Europe/Rome", "lat": "41.89193", "lng": "12.51133"}
        monkeypatch.setattr(
            fetcher.FetchGeonames, "get_serialized_data", lambda self: dict(rome)
        )
        factory = PlanetaryReturnFactory(
            johnny_depp,
            city="Rome", nation="IT", tz_str="Europe/Vienna",  # tz given, coords missing
            online=True,
        )
        assert factory.lat == pytest.approx(41.89193)
        assert factory.lng == pytest.approx(12.51133)
        assert factory.tz_str == "Europe/Vienna"  # explicit value preserved


class TestReturnEnrichmentParityRound4:
    """Round-4 regression: the return chart must inherit the natal subject's
    enrichments (parity with SecondaryProgressionFactory), and a USER-sidereal
    subject must not require re-passing its ayanamsa."""

    def test_return_inherits_natal_enrichments(self):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.planetary_returns.factory import PlanetaryReturnFactory

        natal = AstrologicalSubjectFactory.from_birth_data(
            name="T", year=1990, month=6, day=15, hour=12, minute=0,
            city="Rome", nation="IT", lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True,
            calculate_dignities=True, active_fixed_stars=["Regulus", "Spica"],
        )
        rf = PlanetaryReturnFactory(
            natal, lng=12.5, lat=41.9, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
        )
        ret = rf.next_return_from_iso_formatted_time("2026-06-01T00:00:00Z", "Solar")
        assert ret.sun.essential_dignity is not None
        assert [s.name for s in ret.fixed_stars] == ["Regulus", "Spica"]

    def test_user_sidereal_return_reads_ayanamsa_from_subject(self):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.planetary_returns.factory import PlanetaryReturnFactory

        sid = AstrologicalSubjectFactory.from_birth_data(
            name="S", year=1990, month=6, day=15, hour=12, minute=0,
            city="Rome", nation="IT", lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True,
            zodiac_type="Sidereal", sidereal_mode="USER",
            custom_ayanamsa_t0=2451545.0, custom_ayanamsa_ayan_t0=23.5,
        )
        # Must NOT raise despite not re-passing custom_ayanamsa_* to the factory.
        rf = PlanetaryReturnFactory(
            sid, lng=12.5, lat=41.9, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
        )
        ret = rf.next_return_from_date(2027, 1, 1, return_type="Solar")
        assert ret is not None


class TestReturnSearchAtEphemerisEdge:
    """Round 31: when the return-crossing search (solcross_ut / mooncross_ut)
    walks off the loaded ephemeris date range, the raw libephemeris Error must be
    normalized to KerykeionException — matching every sibling event factory,
    instead of leaking a raw backend exception through the public API."""

    @pytest.fixture(autouse=True)
    def _require_medium_kernel_edges(self):
        # These tests hardcode the medium (DE440) range boundaries (~1550/2650
        # and their JD equivalents). On a base kernel the natal dates are
        # themselves out of range; on an extended kernel the searches never
        # walk off the edge, so nothing raises. Only the medium kernel puts
        # the edges where the scenarios need them.
        from tests.conftest import _detect_ephemeris_tier

        if _detect_ephemeris_tier() != "medium":
            pytest.skip("Requires the medium (DE440) kernel's range edges (~1550/2650).")

    @pytest.mark.parametrize("return_type", ["Solar", "Lunar"])
    def test_forward_search_past_upper_edge_raises_kerykeion(self, return_type):
        # Natal just below the kernel's upper edge; the forward return search
        # then steps past 2650 and the backend can no longer calculate.
        natal = AstrologicalSubjectFactory.from_iso_utc_time(
            name="Edge", iso_utc_time="2649-06-01T00:00:00Z",
            lng=0.0, lat=51.5, tz_str="UTC", online=False,
        )
        rf = PlanetaryReturnFactory(natal, lng=0.0, lat=51.5, tz_str="UTC", online=False)
        with pytest.raises(KerykeionException):
            rf.next_return_from_iso_formatted_time("2650-01-24T00:00:00Z", return_type)

    @pytest.mark.parametrize("return_type", ["Solar", "Lunar"])
    def test_backward_search_past_lower_edge_raises_kerykeion(self, return_type):
        # Natal just above the kernel's lower edge; the backward search then
        # steps before 1550.
        natal = AstrologicalSubjectFactory.from_iso_utc_time(
            name="Edge", iso_utc_time="1550-06-01T00:00:00Z",
            lng=0.0, lat=51.5, tz_str="UTC", online=False,
        )
        rf = PlanetaryReturnFactory(natal, lng=0.0, lat=51.5, tz_str="UTC", online=False)
        with pytest.raises(KerykeionException):
            rf.next_return_from_iso_formatted_time(
                "1550-01-05T00:00:00Z", return_type, backwards=True
            )

    def _edge_factory(self):
        natal = AstrologicalSubjectFactory.from_iso_utc_time(
            name="Edge", iso_utc_time="2600-06-01T00:00:00Z",
            lng=0.0, lat=51.5, tz_str="UTC", online=False,
        )
        return PlanetaryReturnFactory(natal, lng=0.0, lat=51.5, tz_str="UTC", online=False)

    @pytest.mark.parametrize("backwards", [False, True])
    def test_heliocentric_search_past_edge_raises_kerykeion(self, backwards):
        # Round 32: the heliocentric crossing search (helio_cross_ut) must also
        # normalize an off-range backend error to KerykeionException, like the
        # Solar/Lunar paths (R31 wrapped those but missed this sibling method).
        rf = self._edge_factory()
        start = (2287184.5 + 5) if backwards else (2688976.5 - 5)
        with pytest.raises(KerykeionException):
            rf.next_heliocentric_return("Jupiter", start, backwards=backwards)

    @pytest.mark.parametrize("backwards", [False, True])
    def test_lunar_node_crossing_past_edge_raises_kerykeion(self, backwards):
        # Round 32: same for the lunar-node crossing search (mooncross_node_ut).
        rf = self._edge_factory()
        start = (2287184.5 + 1) if backwards else (2688976.5 - 1)
        with pytest.raises(KerykeionException):
            rf.next_lunar_node_crossing(start, backwards=backwards)


class TestReturnModelSect:
    """is_diurnal must survive the PlanetReturnModel boundary: pydantic used to
    silently drop it (field undeclared), so sect-aware consumers (dominants,
    zodiacal releasing) treated every night return as a day chart."""

    def test_return_model_carries_sect(self):
        natal = AstrologicalSubjectFactory.from_birth_data(
            "Sect Natal", 1990, 6, 15, 12, 0,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True,
        )
        rf = PlanetaryReturnFactory(
            natal, lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
        )
        ret = rf.next_return_from_iso_formatted_time("2026-01-01T00:00:00Z", "Solar")
        assert isinstance(ret.is_diurnal, bool)
        # The 2026 solar return for this natal lands at night local time.
        assert ret.is_diurnal is False
