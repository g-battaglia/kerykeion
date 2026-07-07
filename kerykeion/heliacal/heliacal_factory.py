# -*- coding: utf-8 -*-
"""
Heliacal Risings and Settings Factory
======================================

Calculates heliacal events (first/last visibility of planets and stars
relative to the Sun) using the Swiss Ephemeris ``ephe.heliacal_ut()``
function.

A heliacal rising is the first morning a celestial body becomes visible
above the eastern horizon just before sunrise after a period of
invisibility.  A heliacal setting is the last evening it is visible
above the western horizon just after sunset.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

import logging
from typing import List, Optional, Sequence, Tuple

from kerykeion.ephemeris_backend import ephe, ephemeris_session
from kerykeion._predictive_utils import jd_to_iso_utc

from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_models import SubscriptableBaseModel

logger = logging.getLogger(__name__)

# Backend-specific "no event in the search window" errors: libephemeris (and
# the jd<=0 guard in _find_event) raise ValueError; pyswisseph raises its own
# swisseph.Error, which does NOT subclass ValueError.
_NO_EVENT_ERRORS: tuple = tuple(
    {ValueError, getattr(ephe, "Error", ValueError)}
)

def _resolve_skyfield_range_error() -> Optional[type]:
    """libephemeris runs ``heliacal_ut`` through Skyfield, which raises its OWN
    ``skyfield.errors.EphemerisRangeError`` (a plain ``ValueError`` subclass,
    unrelated to libephemeris's exception tree) when a search walks off the end
    of the ephemeris. Resolve it defensively so an out-of-range window is treated
    as a hard error rather than a benign "no event". Returns ``None`` on
    installs without Skyfield (e.g. the swisseph backend)."""
    try:
        from skyfield.errors import EphemerisRangeError

        return EphemerisRangeError
    except Exception:  # pragma: no cover - Skyfield absent (swisseph backend)
        return None


# Backend errors that are NOT a benign "no event in window": a mistyped body
# (DataNotFoundError, whose subclasses include UnknownBodyError/StarNotFoundError),
# an out-of-range date/window (EphemerisRangeError), or a bad config
# (ConfigurationError) are real failures and must surface, not be swallowed as
# "no event". Resolved defensively: on the swisseph backend these subclasses do
# not exist, so only the resolvable members are included and other failures
# remain best-effort "no event" — the generic swisseph.Error cannot be told
# apart. The heliacal path in particular surfaces the *Skyfield* range error, so
# it is resolved separately above.
_BACKEND_HARD_ERRORS: tuple = tuple(
    t
    for t in (
        getattr(ephe, "EphemerisRangeError", None),
        getattr(ephe, "DataNotFoundError", None),
        getattr(ephe, "ConfigurationError", None),
        _resolve_skyfield_range_error(),
    )
    if isinstance(t, type)
)

# ---- Event-type constants (mirrors Swiss Ephemeris) ----
HELIACAL_RISING: int = ephe.HELIACAL_RISING    # 1 - morning first
HELIACAL_SETTING: int = ephe.HELIACAL_SETTING  # 2 - evening last
EVENING_FIRST: int = ephe.EVENING_FIRST        # 3
MORNING_LAST: int = ephe.MORNING_LAST          # 4

EVENT_TYPE_LABELS = {
    HELIACAL_RISING: "heliacal_rising",
    HELIACAL_SETTING: "heliacal_setting",
    EVENING_FIRST: "evening_first",
    MORNING_LAST: "morning_last",
}

# ---- Default atmospheric / observer parameters ----
DEFAULT_PRESSURE: float = 1013.25   # mbar (hPa)
DEFAULT_TEMPERATURE: float = 15.0   # Celsius
DEFAULT_HUMIDITY: float = 40.0      # percent
DEFAULT_EXTINCTION: float = 0.2     # extinction coefficient

DEFAULT_ATMO: Tuple[float, float, float, float] = (
    DEFAULT_PRESSURE,
    DEFAULT_TEMPERATURE,
    DEFAULT_HUMIDITY,
    DEFAULT_EXTINCTION,
)

DEFAULT_OBSERVER: Tuple[float, float, float, float, float, float] = (
    36.0,  # age of observer in years
    1.0,   # Snellen ratio (1 = normal vision)
    0.0,   # monocular (0) / binocular (1)
    0.0,   # telescope magnification (0 = naked eye default)
    0.0,   # optical aperture in mm
    0.0,   # optical transmission
)

# Planets supported by ephe.heliacal_ut
PLANETS = ("Mercury", "Venus", "Mars", "Jupiter", "Saturn")

# Inner planets support all four event types; outer planets only rising/setting.
INNER_PLANETS = {"Mercury", "Venus"}


def _resolve_geopos(
    geopos: Optional[Tuple[float, float, float]],
    lat: Optional[float],
    lng: Optional[float],
    altitude: Optional[float],
) -> Tuple[float, float, float]:
    """Resolve the observer position from ``geopos`` or lat/lng/altitude keywords.

    ``geopos`` follows the Swiss Ephemeris convention ``(longitude, latitude,
    altitude_m)`` — longitude FIRST — which is easy to pass inverted; the
    keyword form is unambiguous. The two forms are mutually exclusive.

    Raises:
        KerykeionException: If both forms are given, or if neither fully
            specifies a position (``lat`` and ``lng`` are both required in
            keyword form; ``altitude`` defaults to 0 m).
    """
    if geopos is not None and any(v is not None for v in (lat, lng, altitude)):
        raise KerykeionException(
            "Provide either geopos=(lng, lat, altitude_m) or the lat=/lng=/altitude= "
            "keywords, not both."
        )
    if geopos is not None:
        return geopos
    if lat is None or lng is None:
        raise KerykeionException(
            "Observer position required: pass geopos=(lng, lat, altitude_m) or "
            "both lat= and lng= (with optional altitude=, defaulting to 0 m)."
        )
    return (lng, lat, altitude if altitude is not None else 0.0)


# ---- Data model ----
class HeliacalEventModel(SubscriptableBaseModel):
    """Model representing a single heliacal event."""

    event_type: str
    """Human-readable event type, e.g. 'heliacal_rising'."""

    julian_day: float
    """Julian Day (UT) of the start of visibility."""

    planet_name: str
    """Name of the planet or star."""

    datestamp: str
    """ISO-style date string (YYYY-MM-DD) for quick reference."""


# ---- Factory ----
class HeliacalFactory:
    """Find heliacal rising and setting events for planets.

    Usage::

        factory = HeliacalFactory()
        event = factory.next_heliacal_rising(
            julian_day=2461125.5,
            planet_name_or_star="Venus",
            geopos=(12.4964, 41.9028, 50),
        )
        print(event.datestamp)

    Parameters
    ----------
    ephe_path : str or None
        Path to the ephemeris data directory.  Defaults to the path
        configured via ``KERYKEION_EPHE_PATH`` (or empty string). The path
        is applied per calculation via ``ephemeris_session`` rather than
        mutating global state at construction time.
    """

    def __init__(self, ephe_path: Optional[str] = None) -> None:
        self._ephe_path = ephe_path

    # ------------------------------------------------------------------ #
    #  Public API                                                         #
    # ------------------------------------------------------------------ #

    def next_heliacal_rising(
        self,
        julian_day: float,
        planet_name_or_star: str,
        geopos: Optional[Tuple[float, float, float]] = None,
        atmo: Optional[Tuple[float, float, float, float]] = None,
        observer: Optional[Tuple[float, float, float, float, float, float]] = None,
        *,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        altitude: Optional[float] = None,
    ) -> HeliacalEventModel:
        """Find the next heliacal rising after *julian_day*.

        Parameters
        ----------
        julian_day:
            Starting Julian Day (UT).
        planet_name_or_star:
            Planet name (e.g. ``"Venus"``) or fixed-star name.
        geopos:
            ``(longitude, latitude, altitude_m)`` of the observer — note the
            Swiss Ephemeris order: longitude FIRST, then latitude, then
            altitude in meters. Mutually exclusive with the
            ``lat``/``lng``/``altitude`` keywords.
        atmo:
            ``(pressure, temperature, humidity, extinction)``; uses
            sensible defaults when *None*.
        observer:
            Observer parameters tuple of length 6; uses defaults when
            *None*.
        lat, lng, altitude:
            Keyword-only alternative to ``geopos`` that cannot be passed in
            the wrong order. ``altitude`` (meters) defaults to 0 when only
            ``lat``/``lng`` are given.

        Returns
        -------
        HeliacalEventModel

        Raises
        ------
        KerykeionException
            If no heliacal rising occurs in the search window (the library's
            user-facing "no result" convention; the internal backend/guard
            signals ``_NO_EVENT_ERRORS`` are normalized here so callers see one
            exception type regardless of backend); or if the observer position
            is given both as ``geopos`` and as keywords (or not at all).
        """
        geopos = _resolve_geopos(geopos, lat, lng, altitude)
        with ephemeris_session(ephe_path=self._ephe_path):
            try:
                result = self._find_event(
                    julian_day=julian_day,
                    planet_name_or_star=planet_name_or_star,
                    geopos=geopos,
                    event_type=HELIACAL_RISING,
                    atmo=atmo,
                    observer=observer,
                )
            except _NO_EVENT_ERRORS as exc:
                if isinstance(exc, _BACKEND_HARD_ERRORS):
                    # Not a "no event in window" signal: the date/window is
                    # outside the available ephemeris range or the body/config is
                    # invalid. Surface it as such instead of a misleading "no
                    # rising found" (mirrors lunation_factory normalization).
                    raise KerykeionException(
                        f"Heliacal rising search for {planet_name_or_star!r} could "
                        f"not complete: the date is outside the available ephemeris "
                        f"range or the body/config is invalid; narrow the date range "
                        f"or check inputs: {exc}"
                    ) from exc
                # A mistyped body (planet OR star) raises a plain ValueError /
                # base ephe.Error here — NOT a _BACKEND_HARD_ERRORS subtype — so
                # it is indistinguishable BY TYPE from a genuine "no event", and
                # this method accepts fixed-star names too (cannot hard-validate
                # against PLANETS). Make the MESSAGE own both possibilities and be
                # actionable rather than assert a definite "no rising".
                raise KerykeionException(
                    f"No heliacal rising found for {planet_name_or_star!r} after "
                    f"JD {julian_day:.5f}. If this is unexpected, verify it is a "
                    f"supported planet {PLANETS} or a recognized fixed-star name, "
                    f"and try widening the search window."
                ) from exc
        return result

    def search_events(
        self,
        julian_day: float,
        geopos: Optional[Tuple[float, float, float]] = None,
        count: int = 5,
        planets: Optional[Sequence[str]] = None,
        event_types: Optional[Sequence[int]] = None,
        atmo: Optional[Tuple[float, float, float, float]] = None,
        observer: Optional[Tuple[float, float, float, float, float, float]] = None,
        *,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        altitude: Optional[float] = None,
    ) -> List[HeliacalEventModel]:
        """Find the next *count* heliacal events across multiple planets.

        Events are returned sorted by Julian Day (chronologically).

        Parameters
        ----------
        julian_day:
            Starting Julian Day (UT).
        geopos:
            ``(longitude, latitude, altitude_m)`` of the observer — note the
            Swiss Ephemeris order: longitude FIRST, then latitude, then
            altitude in meters. Mutually exclusive with the
            ``lat``/``lng``/``altitude`` keywords.
        count:
            Maximum number of events to return.
        planets:
            Planet names to scan.  Defaults to all five visible planets.
        event_types:
            Event type constants to look for.  Defaults to
            ``[HELIACAL_RISING, HELIACAL_SETTING]``.
        atmo:
            Atmospheric parameters; uses defaults when *None*.
        observer:
            Observer parameters; uses defaults when *None*.
        lat, lng, altitude:
            Keyword-only alternative to ``geopos`` that cannot be passed in
            the wrong order. ``altitude`` (meters) defaults to 0 when only
            ``lat``/``lng`` are given.

        Returns
        -------
        list[HeliacalEventModel]

        Raises
        ------
        KerykeionException
            If the observer position is given both as ``geopos`` and as
            keywords (or not at all).
        """
        geopos = _resolve_geopos(geopos, lat, lng, altitude)
        if count <= 0:
            return []
        # Each event costs a full heliacal search (seconds per call), so an
        # unbounded count would hang. Cap it like the other event factories'
        # _ensure_scannable guards rather than scan indefinitely.
        _MAX_HELIACAL_EVENTS = 200
        if count > _MAX_HELIACAL_EVENTS:
            raise ValueError(
                f"count too large ({count} > {_MAX_HELIACAL_EVENTS}); each heliacal "
                "event requires a full ephemeris search. Request fewer events."
            )
        if planets is None:
            planets = PLANETS
        else:
            # search_events hard-validates its planet set UP FRONT (this loop):
            # a mistyped name would otherwise be swallowed as a benign "no event"
            # and silently omitted. It takes planets only (never fixed stars), so
            # it CAN hard-validate here. next_heliacal_rising also accepts
            # fixed-star names, so it cannot hard-validate and instead surfaces an
            # unrecognized body via the actionable "No heliacal rising" message
            # (full fixed-star-name validation is tracked as a mandatory
            # evolution). ephe.heliacal_ut is case-insensitive, so accept any
            # casing and canonicalize to the PLANETS spelling for consistent
            # downstream output (HeliacalEventModel.planet_name).
            _canonical_by_lower = {p.lower(): p for p in PLANETS}
            canonicalized: List[str] = []
            for name in planets:
                canonical = _canonical_by_lower.get(str(name).lower())
                if canonical is None:
                    raise KerykeionException(
                        f"Unknown planet {name!r}; heliacal search supports {PLANETS}."
                    )
                canonicalized.append(canonical)
            planets = canonicalized
        if event_types is None:
            event_types = [HELIACAL_RISING, HELIACAL_SETTING]

        # Build the list of (planet, event_type) combinations to interleave.
        combos = [
            (planet, etype)
            for planet in planets
            for etype in event_types
            if not (etype in (EVENING_FIRST, MORNING_LAST) and planet not in INNER_PLANETS)
        ]

        def _next_event(planet, etype, from_jd):
            """Next event of one combo at/after ``from_jd`` (None if none)."""
            try:
                return self._find_event(
                    julian_day=from_jd,
                    planet_name_or_star=planet,
                    geopos=geopos,
                    event_type=etype,
                    atmo=atmo,
                    observer=observer,
                )
            except _NO_EVENT_ERRORS as exc:
                if isinstance(exc, _BACKEND_HARD_ERRORS):
                    # Not a "no event in window" signal: the date/window is
                    # outside the available ephemeris range or the body/config is
                    # invalid. Surface it instead of silently returning [].
                    raise KerykeionException(
                        f"Heliacal search for {planet!r} could not complete: the "
                        f"date/window is outside the available ephemeris range or "
                        f"the body/config is invalid; narrow the date range or "
                        f"check inputs: {exc}"
                    ) from exc
                # Expected "no solution in window" skip (ValueError on
                # libephemeris / swisseph.Error on pyswisseph). Narrower than a
                # blanket except so real bugs still propagate.
                logger.debug("Skipping %s %s: %s", planet, EVENT_TYPE_LABELS.get(etype, etype), exc)
                return None

        events: List[HeliacalEventModel] = []

        with ephemeris_session(ephe_path=self._ephe_path):
            # Interleaved merge: keep the current next-event per combo, always
            # emit the globally earliest, and advance ONLY that combo. This
            # yields the true "next `count` events sorted by JD" without the old
            # hard cap of one-per-combo, while calling the (expensive) heliacal
            # search at most count + len(combos) times — not count-per-combo.
            heads = {}
            for planet, etype in combos:
                ev = _next_event(planet, etype, julian_day)
                if ev is not None:
                    heads[(planet, etype)] = ev

            while heads and len(events) < count:
                key = min(heads, key=lambda k: heads[k].julian_day)
                ev = heads.pop(key)
                events.append(ev)
                planet, etype = key
                # Advance just past this event (+1 day is safely inside any
                # body's synodic gap; a non-advancing cursor would re-find it).
                nxt = _next_event(planet, etype, ev.julian_day + 1.0)
                if nxt is not None and nxt.julian_day > ev.julian_day:
                    heads[key] = nxt

        # Already emitted in chronological order; sort defensively and trim.
        events.sort(key=lambda e: e.julian_day)
        return events[:count]

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _find_event(
        self,
        julian_day: float,
        planet_name_or_star: str,
        geopos: Tuple[float, float, float],
        event_type: int,
        atmo: Optional[Tuple[float, float, float, float]],
        observer: Optional[Tuple[float, float, float, float, float, float]],
    ) -> HeliacalEventModel:
        """Low-level wrapper around ``ephe.heliacal_ut``.

        Must be called inside an :func:`ephemeris_session` (the public entry
        points open one).
        """
        if atmo is None:
            atmo = DEFAULT_ATMO
        if observer is None:
            observer = DEFAULT_OBSERVER

        dret = ephe.heliacal_ut(
            julian_day,
            geopos,
            atmo,
            observer,
            planet_name_or_star,
            event_type,
            0,  # flags
        )

        result_jd = dret[0]  # start of visibility

        if result_jd <= 0.0:
            # libephemeris signals "no event found" by returning jd 0.0 rather
            # than raising: without this guard the scan emits fake events dated
            # -4713-11-24 that sort first in the results.
            raise ValueError(
                f"No heliacal event found for {planet_name_or_star} "
                f"(event type {event_type}) in the search window."
            )

        # Date part of the shared ISO formatter (split on "T", not [:10]:
        # a leading BCE minus sign would be truncated by a fixed slice).
        datestamp = jd_to_iso_utc(result_jd).split("T", 1)[0]

        return HeliacalEventModel(
            event_type=EVENT_TYPE_LABELS.get(event_type, str(event_type)),
            julian_day=result_jd,
            planet_name=planet_name_or_star,
            datestamp=datestamp,
        )
