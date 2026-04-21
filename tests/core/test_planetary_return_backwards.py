"""
Backward planetary return tests for PlanetaryReturnFactory.

Covers ``backwards=True`` on:
  - ``next_return_from_iso_formatted_time`` (Solar / Lunar)
  - ``next_return_from_date`` (Solar / Lunar)
  - ``next_heliocentric_return*`` (already partial — round-trip added)
  - ``next_lunar_node_crossing*``

The libephemeris backend is required for backward search. When pyswisseph
is active, the factory must raise ``KerykeionException`` with a clear
message pointing at the backend limitation.
"""

from __future__ import annotations

import os
import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from kerykeion import AstrologicalSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.schemas import KerykeionException
from kerykeion.utilities import datetime_to_julian, julian_to_datetime


TROPICAL_YEAR = 365.2422
SIDEREAL_MONTH = 27.3217
NODAL_HALF_MONTH = 13.61


@pytest.fixture(scope="module")
def subject():
    return AstrologicalSubjectFactory.from_birth_data(
        "Test",
        1990,
        6,
        15,
        12,
        0,
        lat=40.7128,
        lng=-74.006,
        tz_str="America/New_York",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="module")
def factory(subject):
    return PlanetaryReturnFactory(
        subject,
        city="New York",
        nation="US",
        lat=40.7128,
        lng=-74.006,
        tz_str="America/New_York",
        online=False,
    )


def _iso_to_jd(iso: str) -> float:
    dt = datetime.fromisoformat(iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return datetime_to_julian(dt)


def _jd_to_iso(jd: float) -> str:
    """Round-trip safely: precise JD → ISO string with microseconds."""
    dt = julian_to_datetime(jd).replace(tzinfo=timezone.utc)
    return dt.isoformat()


# ---------------------------------------------------------------------------
# Solar backward
# ---------------------------------------------------------------------------


class TestSolarBackwards:
    def test_backwards_returns_past(self, factory):
        past = factory.next_return_from_iso_formatted_time(
            "2025-12-31T00:00:00+00:00", "Solar", backwards=True
        )
        ret_jd = _iso_to_jd(past.iso_formatted_utc_datetime)
        start_jd = _iso_to_jd("2025-12-31T00:00:00+00:00")
        assert ret_jd < start_jd
        assert start_jd - ret_jd < TROPICAL_YEAR + 5

    def test_back_is_one_cycle_earlier(self, factory):
        """back(fwd) must be exactly one tropical year before fwd."""
        fwd = factory.next_return_from_iso_formatted_time(
            "2024-01-01T00:00:00+00:00", "Solar"
        )
        back = factory.next_return_from_iso_formatted_time(
            _jd_to_iso(fwd.julian_day), "Solar", backwards=True
        )
        delta_days = fwd.julian_day - back.julian_day
        assert abs(delta_days - TROPICAL_YEAR) < 2.0, (
            f"Delta {delta_days} days ≠ ~1 tropical year"
        )

    def test_date_wrapper_backwards(self, factory):
        back = factory.next_return_from_date(2025, 12, 31, return_type="Solar", backwards=True)
        assert "2025" in back.iso_formatted_utc_datetime or "2024" in back.iso_formatted_utc_datetime


# ---------------------------------------------------------------------------
# Lunar backward
# ---------------------------------------------------------------------------


class TestLunarBackwards:
    def test_backwards_returns_past(self, factory):
        past = factory.next_return_from_iso_formatted_time(
            "2024-06-01T00:00:00+00:00", "Lunar", backwards=True
        )
        ret_jd = _iso_to_jd(past.iso_formatted_utc_datetime)
        start_jd = _iso_to_jd("2024-06-01T00:00:00+00:00")
        assert ret_jd < start_jd
        assert start_jd - ret_jd < 30  # within a sidereal month

    def test_back_is_one_cycle_earlier(self, factory):
        """back(fwd) must be exactly one sidereal month before fwd."""
        fwd = factory.next_return_from_iso_formatted_time(
            "2024-01-01T00:00:00+00:00", "Lunar"
        )
        back = factory.next_return_from_iso_formatted_time(
            _jd_to_iso(fwd.julian_day), "Lunar", backwards=True
        )
        delta_days = fwd.julian_day - back.julian_day
        assert abs(delta_days - SIDEREAL_MONTH) < 0.5, (
            f"Delta {delta_days} days ≠ ~1 sidereal month"
        )


# ---------------------------------------------------------------------------
# Lunar node crossing backward
# ---------------------------------------------------------------------------


class TestLunarNodeCrossingBackwards:
    def test_backwards_returns_past(self, factory):
        past = factory.next_lunar_node_crossing_from_iso_formatted_time(
            "2024-06-15T00:00:00+00:00", backwards=True
        )
        ret_jd = _iso_to_jd(past.iso_formatted_utc_datetime)
        start_jd = _iso_to_jd("2024-06-15T00:00:00+00:00")
        assert ret_jd < start_jd
        assert start_jd - ret_jd < NODAL_HALF_MONTH + 3

    def test_date_wrapper_backwards(self, factory):
        back = factory.next_lunar_node_crossing_from_date(2024, 6, 15, backwards=True)
        assert back.iso_formatted_utc_datetime  # sanity — produced a chart

    def test_back_is_one_cycle_earlier(self, factory):
        """back(fwd) must be ~half a nodal month earlier."""
        fwd = factory.next_lunar_node_crossing_from_iso_formatted_time(
            "2024-01-01T00:00:00+00:00"
        )
        back = factory.next_lunar_node_crossing_from_iso_formatted_time(
            _jd_to_iso(fwd.julian_day), backwards=True
        )
        delta_days = fwd.julian_day - back.julian_day
        assert abs(delta_days - NODAL_HALF_MONTH) < 1.5, (
            f"Delta {delta_days} days ≠ ~13.61 (half nodal month)"
        )


# ---------------------------------------------------------------------------
# Heliocentric backward (already exists — add round-trip)
# ---------------------------------------------------------------------------


class TestHeliocentricBackwards:
    def test_back_is_earlier(self, factory):
        """Heliocentric Jupiter back step must land earlier than fwd."""
        jd = datetime_to_julian(datetime(2024, 1, 1, tzinfo=timezone.utc))
        fwd = factory.next_heliocentric_return("Jupiter", jd)
        back = factory.next_heliocentric_return("Jupiter", fwd.julian_day, backwards=True)
        assert back.julian_day < fwd.julian_day
        # Jupiter heliocentric period ~11.86 years ~= 4333 days
        delta_days = fwd.julian_day - back.julian_day
        assert 4200 < delta_days < 4500, f"Jupiter cycle delta {delta_days} out of bounds"


# ---------------------------------------------------------------------------
# Swisseph fallback — raise KerykeionException with clear message
# ---------------------------------------------------------------------------


class TestSwissephFallback:
    """When pyswisseph is the backend, backward methods must raise cleanly.

    We simulate the fallback by patching ``swe.solcross_ut`` /
    ``swe.mooncross_ut`` / ``swe.mooncross_node_ut`` so calling them with
    ``backwards=True`` raises ``TypeError`` (what pyswisseph does).
    """

    def test_solar_backwards_raises_on_swisseph(self, factory):
        import kerykeion.planetary_return_factory as prf

        original = prf.swe.solcross_ut

        def fake_solcross(*args, **kwargs):
            if "backwards" in kwargs:
                raise TypeError("pyswisseph solcross_ut() got an unexpected keyword argument 'backwards'")
            return original(*args, **kwargs)

        with patch.object(prf.swe, "solcross_ut", side_effect=fake_solcross):
            with pytest.raises(KerykeionException, match="libephemeris"):
                factory.next_return_from_iso_formatted_time(
                    "2025-12-31T00:00:00+00:00", "Solar", backwards=True
                )

    def test_lunar_backwards_raises_on_swisseph(self, factory):
        import kerykeion.planetary_return_factory as prf

        original = prf.swe.mooncross_ut

        def fake_mooncross(*args, **kwargs):
            if "backwards" in kwargs:
                raise TypeError("pyswisseph mooncross_ut() got an unexpected keyword argument 'backwards'")
            return original(*args, **kwargs)

        with patch.object(prf.swe, "mooncross_ut", side_effect=fake_mooncross):
            with pytest.raises(KerykeionException, match="libephemeris"):
                factory.next_return_from_iso_formatted_time(
                    "2024-06-01T00:00:00+00:00", "Lunar", backwards=True
                )

    def test_node_crossing_backwards_raises_on_swisseph(self, factory):
        import kerykeion.planetary_return_factory as prf

        original = prf.swe.mooncross_node_ut

        def fake_node(*args, **kwargs):
            if "backwards" in kwargs:
                raise TypeError("pyswisseph mooncross_node_ut() got an unexpected keyword argument 'backwards'")
            return original(*args, **kwargs)

        with patch.object(prf.swe, "mooncross_node_ut", side_effect=fake_node):
            with pytest.raises(KerykeionException, match="libephemeris"):
                factory.next_lunar_node_crossing_from_iso_formatted_time(
                    "2024-06-15T00:00:00+00:00", backwards=True
                )
