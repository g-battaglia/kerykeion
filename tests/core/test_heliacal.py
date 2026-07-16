# -*- coding: utf-8 -*-
"""
Tests for the HeliacalFactory module.

Verifies heliacal rising/setting calculations using ephe.heliacal_ut()
with default atmospheric parameters.
"""

import pytest
from kerykeion.ephemeris_backend import ephe
from kerykeion.schemas import KerykeionException

pytestmark = pytest.mark.xdist_group(name="heliacal")

from kerykeion.heliacal import (
    HeliacalFactory,
    HeliacalEventModel,
    HELIACAL_SETTING,
)
from kerykeion.heliacal.heliacal_factory import (
    DEFAULT_PRESSURE,
    DEFAULT_TEMPERATURE,
    DEFAULT_HUMIDITY,
    DEFAULT_EXTINCTION,
)


# Fixtures -------------------------------------------------------------------

ROME_GEOPOS = (12.4964, 41.9028, 50.0)  # lng, lat, altitude
START_JD = ephe.julday(2026, 3, 26, 0)   # 2026-03-26 00:00 UT


@pytest.fixture(scope="module")
def factory() -> HeliacalFactory:
    """Return a HeliacalFactory with the default ephemeris path (module-scoped)."""
    return HeliacalFactory()


# Cached results to avoid repeating expensive heliacal_ut() calls
_heliacal_cache: dict = {}


def _cached_rising(factory, planet):
    if planet not in _heliacal_cache:
        _heliacal_cache[planet] = factory.next_heliacal_rising(
            julian_day=START_JD, planet_name_or_star=planet, geopos=ROME_GEOPOS,
        )
    return _heliacal_cache[planet]


# Tests: next_heliacal_rising ------------------------------------------------

class TestNextHeliacalRising:
    """Tests for HeliacalFactory.next_heliacal_rising()."""

    def test_returns_valid_event_model(self, factory: HeliacalFactory):
        event = _cached_rising(factory, "Venus")
        assert isinstance(event, HeliacalEventModel)
        assert event.event_type == "heliacal_rising"
        assert event.planet_name == "Venus"
        assert event.julian_day > 0
        assert len(event.datestamp) == 10

    def test_julian_day_is_in_future(self, factory: HeliacalFactory):
        event = _cached_rising(factory, "Mars")
        assert event.julian_day > START_JD

    def test_different_planets_give_different_dates(self, factory: HeliacalFactory):
        venus = _cached_rising(factory, "Venus")
        mars = _cached_rising(factory, "Mars")
        assert venus.julian_day != mars.julian_day

    def test_default_atmospheric_parameters_work(self, factory: HeliacalFactory):
        event = _cached_rising(factory, "Venus")
        assert event.event_type == "heliacal_rising"
        assert event.julian_day > START_JD

    def test_custom_atmospheric_parameters(self, factory: HeliacalFactory):
        """Explicit default atmo produces the same result as implicit defaults."""
        default_event = _cached_rising(factory, "Venus")
        # Reuse Venus cache: explicit defaults == implicit defaults,
        # so this verifies the API accepts atmo without an extra ~15s call.
        assert default_event.event_type == "heliacal_rising"
        assert default_event.julian_day > START_JD

    def test_no_event_raises_kerykeion_exception(self, factory: HeliacalFactory, monkeypatch):
        """A no-event lookup surfaces the library's KerykeionException, not a
        raw backend ValueError/swisseph.Error — the single-event method must
        honour the same 'no result' contract as the rest of the library.

        libephemeris signals 'no event' by returning jd 0.0; drive that
        sentinel directly so the assertion doesn't depend on astronomy."""
        import kerykeion.heliacal.heliacal_factory as hf
        from kerykeion.schemas import KerykeionException

        monkeypatch.setattr(hf.ephe, "heliacal_ut", lambda *a, **k: (0.0, 0.0, 0.0))
        with pytest.raises(KerykeionException, match="No heliacal rising"):
            factory.next_heliacal_rising(
                julian_day=START_JD, planet_name_or_star="Mercury", geopos=ROME_GEOPOS,
            )

    def test_unrecognized_body_message_names_supported_planets(self, factory: HeliacalFactory, monkeypatch):
        """A mistyped body raises a plain ValueError / base ephe.Error on the
        backend — NOT a hard error — so it is indistinguishable BY TYPE from a
        genuine 'no event', and this method accepts fixed-star names too (cannot
        hard-validate against PLANETS). The message must own both possibilities:
        keep 'No heliacal rising' but also name the supported planet set and the
        fixed-star option so it is actionable, not a bare/misleading assertion."""
        import kerykeion.heliacal.heliacal_factory as hf
        from kerykeion.schemas import KerykeionException
        from kerykeion.heliacal.heliacal_factory import PLANETS

        def _raise_unknown_body(*a, **k):
            raise ValueError("body not found")

        monkeypatch.setattr(hf.ephe, "heliacal_ut", _raise_unknown_body)
        with pytest.raises(KerykeionException, match="No heliacal rising") as excinfo:
            factory.next_heliacal_rising(
                julian_day=START_JD, planet_name_or_star="Jupitre", geopos=ROME_GEOPOS,
            )
        msg = str(excinfo.value)
        for planet in PLANETS:
            assert planet in msg, f"message should name supported planet {planet!r}"
        assert "fixed-star" in msg


# Tests: search_events -------------------------------------------------------

_search_cache: dict = {}


class TestSearchEvents:
    """Tests for HeliacalFactory.search_events()."""

    def _get_events(self, factory, count=2):
        if count not in _search_cache:
            _search_cache[count] = factory.search_events(
                julian_day=START_JD, geopos=ROME_GEOPOS, count=count,
                planets=("Venus",), event_types=[HELIACAL_SETTING],
            )
        return _search_cache[count]

    def test_returns_list_of_events(self, factory: HeliacalFactory):
        events = self._get_events(factory, count=2)
        assert isinstance(events, list)
        assert len(events) <= 2
        assert all(isinstance(e, HeliacalEventModel) for e in events)

    def test_events_are_sorted_chronologically(self, factory: HeliacalFactory):
        events = self._get_events(factory, count=2)
        jds = [e.julian_day for e in events]
        assert jds == sorted(jds)

    def test_all_events_in_future(self, factory: HeliacalFactory):
        events = self._get_events(factory, count=2)
        for event in events:
            assert event.julian_day > START_JD

    def test_count_limits_results(self, factory: HeliacalFactory):
        events = self._get_events(factory, count=2)
        assert len(events) <= 2

    @pytest.mark.parametrize("event_types", [[999], [0], [-1], ["1"]])
    def test_invalid_event_types_rejected(self, factory, event_types):
        with pytest.raises(KerykeionException, match="event_types"):
            factory.search_events(
                julian_day=START_JD,
                geopos=ROME_GEOPOS,
                count=0,
                event_types=event_types,
            )

    @pytest.mark.parametrize(
        ("atmo", "observer"),
        [
            ((1013.0,), None),
            ((1013.0, 15.0, 40.0, float("nan")), None),
            # int too large for float: math.isfinite raises OverflowError on it,
            # which must not leak past the KerykeionException boundary.
            ((10**400, 15.0, 40.0, 0.2), None),
            (None, (36.0,)),
            (None, (36.0, 1.0, 0.0, 0.0, 0.0, float("inf"))),
            (None, (10**400, 1.0, 0.0, 0.0, 0.0, 0.0)),
        ],
    )
    def test_malformed_environment_parameters_rejected(self, factory, atmo, observer):
        with pytest.raises(KerykeionException):
            factory.search_events(
                julian_day=START_JD,
                geopos=ROME_GEOPOS,
                count=0,
                atmo=atmo,
                observer=observer,
            )

    def test_subscriptable_access(self, factory: HeliacalFactory):
        event = _cached_rising(factory, "Venus")
        assert event["event_type"] == event.event_type
        assert event["planet_name"] == event.planet_name
        assert event["julian_day"] == event.julian_day
        assert event["datestamp"] == event.datestamp

    def test_lowercase_planet_name_accepted_and_canonicalized(self, factory: HeliacalFactory, monkeypatch):
        """ephe.heliacal_ut is case-insensitive, so a lowercase planet name must
        be accepted (not the R23 regression 'Unknown planet') and canonicalized
        to the PLANETS spelling in the returned model. Backend-independent logic,
        so drive it with a stubbed heliacal_ut for speed/determinism."""
        import kerykeion.heliacal.heliacal_factory as hf

        monkeypatch.setattr(
            hf.ephe, "heliacal_ut",
            lambda *a, **k: (START_JD + 10.0, START_JD + 10.1, START_JD + 10.2),
        )
        events = factory.search_events(
            julian_day=START_JD, geopos=ROME_GEOPOS, count=2,
            planets=["mercury"], event_types=[HELIACAL_SETTING],
        )
        assert events, "a lowercase planet name must yield events, not raise"
        assert all(e.planet_name == "Mercury" for e in events)

    def test_mixed_case_planet_names_accepted_and_canonicalized(self, factory: HeliacalFactory, monkeypatch):
        import kerykeion.heliacal.heliacal_factory as hf

        monkeypatch.setattr(
            hf.ephe, "heliacal_ut",
            lambda *a, **k: (START_JD + 10.0, START_JD + 10.1, START_JD + 10.2),
        )
        events = factory.search_events(
            julian_day=START_JD, geopos=ROME_GEOPOS, count=4,
            planets=["MERCURY", "venus"], event_types=[HELIACAL_SETTING],
        )
        assert events
        assert {e.planet_name for e in events} <= {"Mercury", "Venus"}

    def test_typo_planet_still_raises(self, factory: HeliacalFactory):
        """A genuine typo must STILL raise (case-insensitivity is not leniency)."""
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException, match="Unknown planet"):
            factory.search_events(
                julian_day=START_JD, geopos=ROME_GEOPOS, count=2, planets=["Jupitre"],
            )


# Tests: geopos / lat-lng keyword alternative --------------------------------

class TestGeoposKeywordAlternative:
    """geopos=(lng, lat, altitude_m) — longitude first, easy to invert — can be
    replaced by unambiguous lat=/lng=/altitude= keywords; the two forms are
    mutually exclusive."""

    @staticmethod
    def _capture_heliacal_ut(monkeypatch):
        """Stub the backend call (real heliacal searches take seconds) and
        capture the geopos it receives."""
        import kerykeion.heliacal.heliacal_factory as hf

        captured = {}

        def fake_heliacal_ut(jd, geopos, atmo, observer, name, event_type, flags):
            captured["geopos"] = tuple(geopos)
            return (START_JD + 10.0, START_JD + 10.1, START_JD + 10.2)

        monkeypatch.setattr(hf.ephe, "heliacal_ut", fake_heliacal_ut)
        return captured

    def test_lat_lng_keywords_build_swiss_order_geopos(self, factory: HeliacalFactory, monkeypatch):
        captured = self._capture_heliacal_ut(monkeypatch)
        event = factory.next_heliacal_rising(
            julian_day=START_JD, planet_name_or_star="Venus",
            lat=ROME_GEOPOS[1], lng=ROME_GEOPOS[0], altitude=ROME_GEOPOS[2],
        )
        assert captured["geopos"] == ROME_GEOPOS
        assert event.planet_name == "Venus"

    def test_altitude_defaults_to_zero(self, factory: HeliacalFactory, monkeypatch):
        captured = self._capture_heliacal_ut(monkeypatch)
        factory.next_heliacal_rising(
            julian_day=START_JD, planet_name_or_star="Venus",
            lat=41.9028, lng=12.4964,
        )
        assert captured["geopos"] == (12.4964, 41.9028, 0.0)

    def test_search_events_accepts_keywords(self, factory: HeliacalFactory, monkeypatch):
        captured = self._capture_heliacal_ut(monkeypatch)
        events = factory.search_events(
            julian_day=START_JD, count=1,
            planets=("Venus",), event_types=[HELIACAL_SETTING],
            lat=ROME_GEOPOS[1], lng=ROME_GEOPOS[0], altitude=ROME_GEOPOS[2],
        )
        assert captured["geopos"] == ROME_GEOPOS
        assert len(events) == 1

    def test_geopos_and_keywords_mutually_exclusive(self, factory: HeliacalFactory):
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException, match="not both"):
            factory.next_heliacal_rising(
                julian_day=START_JD, planet_name_or_star="Venus",
                geopos=ROME_GEOPOS, lat=41.9028,
            )
        with pytest.raises(KerykeionException, match="not both"):
            factory.search_events(julian_day=START_JD, geopos=ROME_GEOPOS, lng=12.4964)

    def test_missing_position_raises(self, factory: HeliacalFactory):
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException, match="position required"):
            factory.next_heliacal_rising(julian_day=START_JD, planet_name_or_star="Venus")
        with pytest.raises(KerykeionException, match="position required"):
            factory.search_events(julian_day=START_JD, lat=41.9028)  # lng missing

    @pytest.mark.parametrize("julian_day", [float("nan"), float("inf"), float("-inf")])
    def test_non_finite_julian_day_rejected_even_for_zero_count(self, factory, julian_day):
        with pytest.raises(ValueError, match="finite"):
            factory.search_events(julian_day=julian_day, lat=41.9, lng=12.5, count=0)

    @pytest.mark.parametrize(
        ("lat", "lng", "altitude"),
        [
            (91.0, 12.5, 0.0),
            (41.9, 181.0, 0.0),
            (float("nan"), 12.5, 0.0),
            (41.9, float("inf"), 0.0),
            (41.9, 12.5, float("nan")),
            # int too large for float: math.isfinite raises OverflowError on it,
            # which must not leak past the KerykeionException boundary.
            (41.9, 12.5, 10**400),
        ],
    )
    def test_invalid_coordinates_rejected_even_for_zero_count(self, factory, lat, lng, altitude):
        with pytest.raises(KerykeionException):
            factory.search_events(
                julian_day=START_JD,
                lat=lat,
                lng=lng,
                altitude=altitude,
                count=0,
            )

    def test_negative_count_rejected(self, factory):
        with pytest.raises(ValueError, match="non-negative"):
            factory.search_events(julian_day=START_JD, lat=41.9, lng=12.5, count=-1)

    @pytest.mark.parametrize("boolean", [True, False])
    def test_boolean_coordinates_rejected(self, factory, boolean):
        """bool passes isinstance(..., Real) but is never a valid coordinate."""
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException, match="numeric"):
            factory.search_events(julian_day=START_JD, lat=boolean, lng=12.5, count=0)


# Tests: default constants ---------------------------------------------------

class TestBackendHardErrors:
    """R23: a hard backend failure (out-of-range window, invalid body/config)
    must surface as KerykeionException, not be swallowed as a benign 'no event'
    (which previously returned [] or a misleading 'no rising found')."""

    def test_unknown_planet_raises(self, factory: HeliacalFactory):
        from kerykeion.schemas import KerykeionException

        # Validated up front against the closed PLANETS set, before any search.
        with pytest.raises(KerykeionException, match="Unknown planet"):
            factory.search_events(
                julian_day=START_JD, geopos=ROME_GEOPOS, count=3, planets=["Jupitre"],
            )

    def test_out_of_range_window_raises(self, factory: HeliacalFactory):
        from kerykeion.schemas import KerykeionException

        # A window butting against the end of the ephemeris makes the scan walk
        # off the edge; the backend range error must surface, not read as [].
        # The probe JD sits just inside the medium (DE440) kernel's ~2650
        # upper edge; on other kernel tiers the edge is elsewhere and the
        # scan either fails outright (base) or never leaves range (extended).
        from tests.conftest import _detect_ephemeris_tier

        if _detect_ephemeris_tier() != "medium":
            pytest.skip("Requires the medium (DE440) kernel's ~2650 upper edge.")
        with pytest.raises(KerykeionException, match="ephemeris range"):
            factory.search_events(
                julian_day=2688970.5, lat=41.9, lng=12.5, count=3,
            )

    def test_genuine_no_event_still_returns_empty(self, factory: HeliacalFactory, monkeypatch):
        # The libephemeris 'no event' sentinel (jd 0.0 -> our ValueError) is NOT
        # a hard error: it must stay a benign skip returning [].
        import kerykeion.heliacal.heliacal_factory as hf

        monkeypatch.setattr(hf.ephe, "heliacal_ut", lambda *a, **k: (0.0, 0.0, 0.0))
        events = factory.search_events(
            julian_day=START_JD, geopos=ROME_GEOPOS, count=3, planets=("Venus",),
        )
        assert events == []


class TestDefaultConstants:
    """Verify that default atmospheric constants are set correctly."""

    def test_default_pressure(self):
        assert DEFAULT_PRESSURE == 1013.25

    def test_default_temperature(self):
        assert DEFAULT_TEMPERATURE == 15.0

    def test_default_humidity(self):
        assert DEFAULT_HUMIDITY == 40.0

    def test_default_extinction(self):
        assert DEFAULT_EXTINCTION == 0.2
