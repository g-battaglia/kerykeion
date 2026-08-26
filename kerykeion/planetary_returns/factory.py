# -*- coding: utf-8 -*-
"""
Planetary Return Factory Module

This module provides the PlanetaryReturnFactory class for calculating and generating
comprehensive planetary return charts, specifically Solar and Lunar returns. It leverages
the configured ephemeris backend (libephemeris by default, swisseph optionally) for precise
astronomical calculations to determine exact return moments and create complete astrological
chart data.

Key Features:
    - Solar Return calculations (Sun's annual return to natal position)
    - Lunar Return calculations (Moon's monthly return to natal position)
    - Multiple date input formats (ISO datetime, year-based, month/year-based)
    - Flexible location handling (online geocoding or manual coordinates)
    - Complete astrological chart generation for return moments
    - Integration with Geonames service for location data
    - Timezone-aware calculations with UTC precision

A planetary return occurs when a planet returns to the exact degree and minute
it occupied at the time of birth. Solar returns happen approximately once per year
and are widely used for annual forecasting, while Lunar returns occur roughly
every 27.3 days (sidereal month) and are used for monthly analysis and timing.

The factory creates complete AstrologicalSubject instances for the calculated
return moments, enabling full chart analysis including planetary positions,
aspects, house cusps, and all other astrological features.

Classes:
    PlanetaryReturnFactory: Main factory class for calculating planetary returns

Dependencies:
    - kerykeion.ephemeris_backend.backend: Ephemeris calculations (libephemeris or swisseph)
    - kerykeion.AstrologicalSubjectFactory: For creating complete chart data
    - kerykeion.geonames.fetcher: For online location data retrieval
    - kerykeion.utilities.core: For date/time conversions and astronomical functions
    - kerykeion.schemas: For type definitions and model structures

Example:
    Basic Solar Return calculation for a specific year:

    >>> from kerykeion import AstrologicalSubjectFactory
    >>> from kerykeion.planetary_returns.factory import PlanetaryReturnFactory
    >>>
    >>> # Create natal chart
    >>> subject = AstrologicalSubjectFactory.from_birth_data(
    ...     name="John Doe",
    ...     year=1990, month=6, day=15,
    ...     hour=12, minute=30,
    ...     lat=40.7128, lng=-74.0060,
    ...     tz_str="America/New_York"
    ... )
    >>>
    >>> # Create return calculator for New York location
    >>> calculator = PlanetaryReturnFactory(
    ...     subject,
    ...     city="New York",
    ...     nation="US",
    ...     online=True
    ... )
    >>>
    >>> # Calculate Solar Return for 2024
    >>> solar_return = calculator.next_return_from_year(2024, "Solar")
    >>> print(f"Solar Return: {solar_return.iso_formatted_local_datetime}")
    >>> print(f"Sun position: {solar_return.sun.abs_pos}°")

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

import calendar
import logging

from kerykeion.ephemeris_backend.backend import ephe, ephemeris_session

from datetime import datetime, timedelta, timezone
from typing import Callable, List, Literal, Optional, Union, cast

from kerykeion.schemas import KerykeionException
from kerykeion.geonames.fetcher import FetchGeonames
from kerykeion.utilities.core import julian_to_datetime, datetime_to_julian
from kerykeion.astrological_subject.factory import (
    GEONAMES_DEFAULT_USERNAME_WARNING,
    DEFAULT_GEONAMES_CACHE_EXPIRE_AFTER_DAYS,
    DEFAULT_GEONAMES_USERNAME,
)
from kerykeion.astrological_subject.factory import AstrologicalSubjectFactory
from kerykeion.schemas.literals import AstrologicalPoint
from kerykeion.schemas.models import PlanetReturnModel, AstrologicalSubjectModel


# Backend errors the return-crossing search can raise when it walks off the
# ephemeris date range. libephemeris raises its own `Error`; no backend raises
# RuntimeError, but include it defensively. Defined module-level (not inline in
# the except clause) so mypy accepts the dynamic getattr tuple.
_BACKEND_ERRORS: tuple = tuple({RuntimeError, getattr(ephe, "Error", RuntimeError)})

# The Solar/Lunar return entry points accept only these two of ReturnType's four
# members; Heliocentric and Lunar_Node_Crossing have their own dedicated methods
# (next_heliocentric_return / next_lunar_node_crossing) and are rejected here. Use
# the narrow alias so a type checker matches the runtime-accepted set.
SolarLunarReturnType = Literal["Solar", "Lunar"]


class PlanetaryReturnFactory:
    """
    A factory class for calculating and generating planetary return charts.

    This class specializes in computing precise planetary return moments using the Swiss
    Ephemeris library and creating complete astrological charts for those calculated times.
    It supports both Solar Returns (annual) and Lunar Returns (monthly), providing
    comprehensive astrological analysis capabilities for timing and forecasting applications.

    Planetary returns are fundamental concepts in predictive astrology:
    - Solar Returns: Occur when the Sun returns to its exact natal position (~365.25 days)
    - Lunar Returns: Occur when the Moon returns to its exact natal position (~27-29 days)

    The factory handles complex astronomical calculations automatically, including:
    - Precise celestial mechanics computations
    - Timezone conversions and UTC coordination
    - Location-based calculations for return chart casting
    - Integration with online geocoding services
    - Complete chart generation with all astrological points

    Args:
        subject (AstrologicalSubjectModel): The natal astrological subject for whom
            returns are calculated. Must contain complete birth data including
            planetary positions at birth.
        city (Optional[str]): City name for return chart location. Required when
            using online mode for location data retrieval.
        nation (Optional[str]): Nation/country code for return chart location.
            Required when using online mode (e.g., "US", "GB", "FR").
        lng (Optional[Union[int, float]]): Geographic longitude in decimal degrees
            for return chart location. Positive values for East, negative for West.
            Required when using offline mode.
        lat (Optional[Union[int, float]]): Geographic latitude in decimal degrees
            for return chart location. Positive values for North, negative for South.
            Required when using offline mode.
        tz_str (Optional[str]): Timezone identifier for return chart location
            (e.g., "America/New_York", "Europe/London", "Asia/Tokyo").
            Required when using offline mode.
        online (bool, optional): Whether to fetch location data online via Geonames
            service. When True, requires city, nation, and geonames_username.
            When False, requires lng, lat, and tz_str. Defaults to True.
        geonames_username (Optional[str]): Username for Geonames API access.
            Required when online=True and coordinates are not provided.
            Register at http://www.geonames.org/login for free account.
        cache_expire_after_days (int, optional): Number of days to cache Geonames
            location data before refreshing. Defaults to system setting.
        altitude (Optional[Union[float, int]]): Elevation above sea level in meters
            for the return chart location. Forwarded to the return chart's subject, where
            a Topocentric perspective feeds it to the observer position (sub-arcsecond
            effect on positions). Ignored by geocentric perspectives. Defaults to None.

    Raises:
        KerykeionException: If required location parameters are missing for the
            chosen mode (online/offline).
        KerykeionException: If Geonames API fails to retrieve location data.
        KerykeionException: If online mode is used without proper API credentials.

    Attributes:
        subject (AstrologicalSubjectModel): The natal subject for calculations.
        city (Optional[str]): Return chart city name.
        nation (Optional[str]): Return chart nation code.
        lng (float): Return chart longitude coordinate.
        lat (float): Return chart latitude coordinate.
        tz_str (str): Return chart timezone identifier.
        online (bool): Location data retrieval mode.
        city_data (Optional[dict]): Cached location data from Geonames.

    Examples:
        Online mode with automatic location lookup:

        >>> subject = AstrologicalSubjectFactory.from_birth_data(
        ...     name="Alice", year=1985, month=3, day=21,
        ...     hour=14, minute=30, lat=51.5074, lng=-0.1278,
        ...     tz_str="Europe/London"
        ... )
        >>> factory = PlanetaryReturnFactory(
        ...     subject,
        ...     city="London",
        ...     nation="GB",
        ...     online=True,
        ...     geonames_username="your_username"
        ... )

        Offline mode with manual coordinates:

        >>> factory = PlanetaryReturnFactory(
        ...     subject,
        ...     lng=-74.0060,
        ...     lat=40.7128,
        ...     tz_str="America/New_York",
        ...     online=False
        ... )

        Different location for return chart:

        >>> # Calculate return as if living in a different city
        >>> factory = PlanetaryReturnFactory(
        ...     natal_subject,  # Born in London
        ...     city="Paris",   # But living in Paris
        ...     nation="FR",
        ...     online=True
        ... )

    Use Cases:
        - Annual Solar Return charts for yearly forecasting
        - Monthly Lunar Return charts for timing analysis
        - Relocation returns for different geographic locations
        - Research into planetary cycle effects
        - Astrological consultation and chart analysis
        - Educational demonstrations of celestial mechanics

    Note:
        Return calculations use the exact degree and minute of natal planetary
        positions. The resulting charts are cast for the precise moment when
        the transiting planet reaches this position, which may not align with
        calendar dates (especially for Solar Returns, which can occur on
        different dates depending on leap years and location).
    """

    @staticmethod
    def _require_valid_year(year: int) -> None:
        """Reject a year outside datetime's 1..9999 range as KerykeionException.

        Every public entry point that forwards ``year`` to ``datetime(year, ...)``
        must call this first, so an out-of-range year fails with the library's
        own exception instead of a raw ValueError from datetime.
        """
        if year < 1 or year > 9999:
            raise KerykeionException(f"Invalid year {year}. Year must be between 1 and 9999.")

    @staticmethod
    def _parse_iso(iso_formatted_time: str) -> datetime:
        """Parse a user ISO timestamp, surfacing errors as KerykeionException.

        Every public ``*_from_iso_formatted_time`` entry point uses this so a
        malformed timestamp fails with the library's own exception instead of a
        raw ValueError from ``datetime.fromisoformat``.
        """
        try:
            return datetime.fromisoformat(iso_formatted_time)
        except (ValueError, TypeError) as exc:
            raise KerykeionException(
                f"Invalid ISO timestamp {iso_formatted_time!r}: {exc}. "
                "Expected an ISO 8601 datetime such as '2023-06-15T14:30:00Z'."
            ) from exc

    @classmethod
    def _search_start_jd(cls, iso_formatted_time: str, backwards: bool) -> float:
        """Julian Day a return search starts from: the seed's own second excluded.

        Return instants are reported truncated to the whole second (the chart
        is rebuilt from an integer ``seconds`` field), so the exact crossing of
        a return reported at ``T`` lies in ``[T, T + 1s)`` — at or a fraction
        of a second AFTER the value the caller holds. Seeding a forward search
        with that value found the same crossing again, sitting just ahead of
        the seed, so a caller stepping through the sequence of returns with the
        instants this factory reports never advanced; backward searches only
        worked because the truncation happens to land the seed on the right
        side.

        Ordering between a seed and a return is therefore defined at the
        library's reporting resolution. A forward search starts from the whole
        second AFTER the seed's: every crossing inside the seed's own second
        is reported at that second, hence not "after" it. A backward search
        starts from the seed's own whole second: the ephemeris backend's
        backward searches are strictly past (a crossing at the start epoch is
        never the answer), so a crossing inside the seed's second — reported
        at that second, hence not "before" it — is excluded, while one in the
        second before is found. Reported instants become re-usable as seeds —
        ``next`` from the instant of return N is N+1, ``previous`` is N-1,
        exactly — and nothing can be skipped: consecutive crossings of any
        one kind are at least ~12.4 days apart (the shortest interval between
        the Moon's node crossings; half a draconic month is 13.6 days on
        average). The backend's solvers do not reach this resolution on their
        own — their at-crossing dead band spans ~90 ms for the Sun, their
        0.001″ tolerance is seconds of a slow heliocentric body's motion — so
        ``_settled`` holds every supported ISO search to the contract: heliocentric
        crossings are settled to a tenth of a millisecond by bisection, a crossing inside
        the second before a backward seed is looked for explicitly, and a
        result that has not moved past the seed's second restarts from outside
        the solver's basin. Outside it, as before: the heliocentric search for
        the lunar nodes and the Liliths, which are not heliocentric bodies
        (the Moon's own node crossings are inside it).

        Naive timestamps are read as UTC, like every ``*_from_iso`` entry.
        """
        whole_second = cls._seed_whole_second(iso_formatted_time)
        step = timedelta(seconds=0 if backwards else 1)
        try:
            return datetime_to_julian(whole_second + step)
        except OverflowError as exc:
            # 9999-12-31T23:59:59 UTC forward: the next second is outside the
            # civil range. Refuse with the library's own exception, naming the
            # range, not the ephemeris.
            raise KerykeionException(
                f"Cannot search {'backward' if backwards else 'forward'} from "
                f"{iso_formatted_time!r}: the search would start outside the "
                "supported civil range (years 1 to 9999)."
            ) from exc

    @classmethod
    def _seed_whole_second(cls, iso_formatted_time: str) -> datetime:
        """The seed's whole second, in UTC — the instant ordering is decided against."""
        dt = cls._parse_iso(iso_formatted_time)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        try:
            # Normalize to UTC BEFORE truncating: the civil range is a range of
            # instants, and a local wall time at its edge
            # (9999-12-31T23:59:59+14:00 is a mid-morning UTC instant) must not
            # trip on the local representation. What overflows here is an
            # aware timestamp whose UTC instant is already past an edge.
            return dt.astimezone(timezone.utc).replace(microsecond=0)
        except OverflowError as exc:
            raise KerykeionException(
                f"Cannot search from {iso_formatted_time!r}: its UTC instant is outside "
                "the supported civil range (years 1 to 9999)."
            ) from exc

    # One second, in days.
    _SECOND = 1.0 / 86400.0
    # Where a search restarts when the solver handed back the crossing its seed
    # came from: well outside every solver's convergence basin (a minute, for
    # the slowest heliocentric body) and well inside every cycle (twelve days,
    # for a node crossing).
    _ESCAPE_DAYS = 1.0 / 24.0

    @staticmethod
    def _signed_arc(longitude: float, target: float) -> float:
        """Signed arc from ``target`` to ``longitude``, in [-180, 180)."""
        return ((longitude - target + 180.0) % 360.0) - 180.0

    # A sign change of a signed arc is a crossing only when the arc is small
    # on both sides: the arc also flips sign at the antipode of the target,
    # where it jumps from +180 to -180, and that is an opposition, not a
    # return. Over any window used here (a second; a minute around a solver's
    # answer) a body moves a few tens of arcseconds at most, so a genuine
    # crossing keeps the arc within a fraction of a degree of zero.
    _CROSSING_ARC_LIMIT = 90.0
    # Resolution of the bisection, in days: a tenth of a millisecond, just
    # above the granularity of a Julian Day in double precision (~46 µs).
    _CROSSING_RESOLUTION = 1e-4 / 86400.0

    @classmethod
    def _crossing_between(cls, offset: Callable[[float], float], lo: float, hi: float) -> Optional[float]:
        """The root of a monotone signed ``offset`` strictly inside ``[lo, hi)``, to a tenth of a millisecond — or None.

        ``offset`` is negative on one side of the crossing and positive on the
        other; a sign change across the window is the crossing, found by
        bisection. This reaches the resolution the backend's solvers do not:
        inside one second (their at-crossing dead band is ~90 ms either side
        of the target for the Sun) and inside the convergence basin of a slow
        heliocentric body (their 0.001″ tolerance is six seconds of Pluto's
        motion).

        A root at ``hi`` itself — a seed that IS a crossing, the natal instant
        being one by construction — is not inside the window and yields None:
        a crossing at the seed is inside the seed's own second, which the
        ordering contract excludes. Roots within a tenth of a millisecond of
        ``hi`` are treated the same, below the resolution of the bisection.
        """
        f_lo, f_hi = offset(lo), offset(hi)
        if max(abs(f_lo), abs(f_hi)) > cls._CROSSING_ARC_LIMIT:
            return None  # the window straddles the antipode, not the target
        if f_lo == 0.0:
            return lo
        if f_hi == 0.0 or (f_lo < 0.0) == (f_hi < 0.0):
            return None
        top = hi
        for _ in range(64):
            if hi - lo < cls._CROSSING_RESOLUTION:
                break
            mid = 0.5 * (lo + hi)
            f_mid = offset(mid)
            if f_mid == 0.0:
                lo = hi = mid
                break
            if (f_mid < 0.0) == (f_lo < 0.0):
                lo, f_lo = mid, f_mid
            else:
                hi, f_hi = mid, f_mid
        root = 0.5 * (lo + hi)
        if top - root < cls._CROSSING_RESOLUTION:
            return None  # at the seed, within the resolution
        return root

    def _settled(
        self,
        iso_formatted_time: str,
        backwards: bool,
        search: Callable[[float], PlanetReturnModel],
    ) -> PlanetReturnModel:
        """Run ``search`` from the ISO seed and hold it to the ordering contract.

        A result is accepted only when its reported second lies strictly after
        (forward) or before (backward) the seed's whole second. When it does
        not, the solver has handed back the crossing the seed came from — its
        convergence basin, up to a minute for the slowest heliocentric bodies,
        is wider than the second the seed stepped — and the search restarts
        from well outside that basin.
        """
        seed_second = round(datetime_to_julian(self._seed_whole_second(iso_formatted_time)) * 86400.0)
        start_jd = self._search_start_jd(iso_formatted_time, backwards)
        for _ in range(2):
            model = search(start_jd)
            if model.julian_day is None:
                raise KerykeionException("The return chart carries no Julian Day; cannot order it against the seed.")
            reported_second = round(model.julian_day * 86400.0)
            if (reported_second < seed_second) if backwards else (reported_second > seed_second):
                return model
            start_jd = model.julian_day + (-self._ESCAPE_DAYS if backwards else self._ESCAPE_DAYS)
        raise KerykeionException(
            f"The return search could not move past its seed {iso_formatted_time!r}: "
            "the backend keeps answering with the crossing the seed came from."
        )

    def __init__(
        self,
        subject: AstrologicalSubjectModel,
        city: Union[str, None] = None,
        nation: Union[str, None] = None,
        lng: Union[int, float, None] = None,
        lat: Union[int, float, None] = None,
        tz_str: Union[str, None] = None,
        online: bool = True,
        geonames_username: Union[str, None] = None,
        *,
        cache_expire_after_days: int = DEFAULT_GEONAMES_CACHE_EXPIRE_AFTER_DAYS,
        altitude: Union[float, int, None] = None,
        custom_ayanamsa_t0: Union[float, None] = None,
        custom_ayanamsa_ayan_t0: Union[float, None] = None,
        # v6: v6 calc flags propagated to the return subject so that the
        # return chart computes the same enrichments as the natal (fixed
        # stars, dignities, nakshatra, gauquelin sectors, nutation, local
        # space). Without these, the return falls back to the bare
        # planetary positions even when the user requested otherwise on
        # the natal request.
        active_fixed_stars: Union[List[str], None] = None,
        calculate_dignities: bool = False,
        calculate_nakshatra: bool = False,
        calculate_gauquelin: bool = False,
        calculate_nutation: bool = False,
        calculate_local_space: bool = False,
    ):
        """
        Initialize a PlanetaryReturnFactory instance with location and configuration settings.

        This constructor sets up the factory with all necessary parameters for calculating
        planetary returns at a specified location. It supports both online mode (with
        automatic geocoding via Geonames) and offline mode (with manual coordinates).

        The factory validates input parameters based on the chosen mode and automatically
        retrieves missing location data when operating online. All location parameters
        are stored and used for casting return charts at the exact calculated moments.

        Args:
            subject (AstrologicalSubjectModel): The natal astrological subject containing
                birth data and planetary positions. This subject's natal planetary
                positions serve as reference points for calculating returns.
            city (Optional[str]): City name for the return chart location. Must be a
                recognizable city name for Geonames geocoding when using online mode.
                Examples: "New York", "London", "Tokyo", "Paris".
            nation (Optional[str]): Country or nation code for the return chart location.
                Use ISO country codes for best results (e.g., "US", "GB", "JP", "FR").
                Required when online=True.
            lng (Optional[Union[int, float]]): Geographic longitude coordinate in decimal
                degrees for return chart location. Range: -180.0 to +180.0.
                Positive values represent East longitude, negative values West longitude.
                Required when online=False.
            lat (Optional[Union[int, float]]): Geographic latitude coordinate in decimal
                degrees for return chart location. Range: -90.0 to +90.0.
                Positive values represent North latitude, negative values South latitude.
                Required when online=False.
            tz_str (Optional[str]): Timezone identifier string for return chart location.
                Must be a valid timezone from the IANA Time Zone Database
                (e.g., "America/New_York", "Europe/London", "Asia/Tokyo").
                Required when online=False.
            online (bool, optional): Location data retrieval mode. When True, uses
                Geonames web service to automatically fetch coordinates and timezone
                from city/nation parameters. When False, uses manually provided
                coordinates and timezone. Defaults to True.
            geonames_username (Optional[str]): Username for Geonames API access.
                Required when online=True and coordinates are not manually provided.
                Free accounts available at http://www.geonames.org/login.
                If None and required, uses default username with warning.
            cache_expire_after_days (int, optional): Number of days to cache Geonames
                location data locally before requiring refresh. Helps reduce API
                calls and improve performance for repeated calculations.
                Defaults to system configuration value.
            altitude (Optional[Union[float, int]]): Elevation above sea level in meters
                for the return chart location. Forwarded to the return chart's subject, where
                a Topocentric perspective feeds it to the observer position (sub-arcsecond
                effect on positions). Ignored by geocentric perspectives. Defaults to None.

        Raises:
            KerykeionException: If city is not provided when online=True.
            KerykeionException: If nation is not provided when online=True.
            KerykeionException: If coordinates (lat/lng) are not provided when online=False.
            KerykeionException: If timezone (tz_str) is not provided when online=False.
            KerykeionException: If Geonames API fails to retrieve valid location data.
            KerykeionException: If required parameters are missing for the chosen mode.

        Examples:
            Initialize with online geocoding:

            >>> factory = PlanetaryReturnFactory(
            ...     subject,
            ...     city="San Francisco",
            ...     nation="US",
            ...     online=True,
            ...     geonames_username="your_username"
            ... )

            Initialize with manual coordinates:

            >>> factory = PlanetaryReturnFactory(
            ...     subject,
            ...     lng=-122.4194,
            ...     lat=37.7749,
            ...     tz_str="America/Los_Angeles",
            ...     online=False
            ... )

            Initialize with mixed parameters (coordinates override online lookup):

            >>> factory = PlanetaryReturnFactory(
            ...     subject,
            ...     city="Custom Location",
            ...     lng=-74.0060,
            ...     lat=40.7128,
            ...     tz_str="America/New_York",
            ...     online=False
            ... )

        Note:
            - When both online and manual coordinates are provided, offline mode takes precedence
            - Geonames cache helps reduce API calls for frequently used locations
            - Timezone accuracy is crucial for precise return calculations
            - Location parameters affect house cusps and angular positions in return charts
        """
        # Store basic configuration
        self.subject = subject
        self.online = online
        self.cache_expire_after_days = cache_expire_after_days
        self.altitude = altitude
        # Custom ayanamsa: fall back to the values already on the subject (a
        # USER-sidereal subject always carries them — its own validator requires
        # both) so a caller that built a USER-sidereal natal need not re-pass
        # them. Parity with SecondaryProgressionFactory, which reads them off
        # the subject.
        self.custom_ayanamsa_t0 = (
            custom_ayanamsa_t0 if custom_ayanamsa_t0 is not None else subject.custom_ayanamsa_t0
        )
        self.custom_ayanamsa_ayan_t0 = (
            custom_ayanamsa_ayan_t0 if custom_ayanamsa_ayan_t0 is not None else subject.custom_ayanamsa_ayan_t0
        )

        # v6 calc flags forwarded to the return subject. When the caller does not
        # pass them explicitly, INFER them from the natal subject's populated
        # fields so the return computes the same enrichments as the natal
        # (dignities/nakshatra/gauquelin/nutation/local-space/fixed-stars) —
        # otherwise they were silently dropped despite the documented promise.
        # Parity with SecondaryProgressionFactory. Infer the per-point flags
        # from ANY populated point, not subject.sun specifically: in a
        # heliocentric chart the Sun is the excluded center body (sun is None),
        # so keying off it would silently drop the enrichments the user did
        # request. Scan the standard bodies for the first one present.
        def _any_point_has(attr: str) -> bool:
            for _name in ("sun", "moon", "mercury", "venus", "mars", "jupiter",
                          "saturn", "uranus", "neptune", "pluto"):
                _p = getattr(subject, _name, None)
                if _p is not None:
                    return getattr(_p, attr, None) is not None
            return False

        self.active_fixed_stars = (
            active_fixed_stars
            if active_fixed_stars is not None
            else ([s.name for s in (subject.fixed_stars or [])] or None)
        )
        self.calculate_dignities = calculate_dignities or _any_point_has("essential_dignity")
        self.calculate_nakshatra = calculate_nakshatra or _any_point_has("nakshatra")
        self.calculate_gauquelin = calculate_gauquelin or (subject.gauquelin_sector_cusps is not None)
        self.calculate_nutation = calculate_nutation or (subject.nutation is not None)
        self.calculate_local_space = calculate_local_space or _any_point_has("azimuth")

        # Validate USER sidereal mode requires both custom ayanamsa values
        # (after the subject fallback above, so a USER-sidereal subject that
        # carries them is accepted without re-passing).
        if subject.sidereal_mode == "USER" and (
            self.custom_ayanamsa_t0 is None or self.custom_ayanamsa_ayan_t0 is None
        ):
            raise KerykeionException(
                "PlanetaryReturnFactory requires both custom_ayanamsa_t0 and "
                "custom_ayanamsa_ayan_t0 when sidereal_mode='USER'."
            )

        # Geonames username
        if geonames_username is None and online and (lat is None or lng is None or not tz_str):
            logging.warning(GEONAMES_DEFAULT_USERNAME_WARNING)
            self.geonames_username = DEFAULT_GEONAMES_USERNAME
        else:
            self.geonames_username = geonames_username  # type: ignore

        # City
        if not city and online:
            raise KerykeionException("You need to set the city if you want to use the online mode!")
        else:
            self.city = city

        # Nation
        if not nation and online:
            raise KerykeionException("You need to set the nation if you want to use the online mode!")
        else:
            self.nation = nation

        # Latitude
        if lat is None and not online:
            raise KerykeionException(
                "You need to set the coordinates and timezone if you want to use the offline mode!"
            )
        else:
            self.lat = lat  # type: ignore

        # Longitude
        if lng is None and not online:
            raise KerykeionException(
                "You need to set the coordinates and timezone if you want to use the offline mode!"
            )
        else:
            self.lng = lng  # type: ignore

        # Timezone
        if (not online) and (not tz_str):
            raise KerykeionException(
                "You need to set the coordinates and timezone if you want to use the offline mode!"
            )
        else:
            self.tz_str = tz_str  # type: ignore

        # Online mode: fetch whenever ANY of tz_str/lat/lng is missing (the
        # username warning above uses the same OR condition; an AND here left
        # lat/lng as None for callers providing only tz_str, crashing every
        # return calculation later). Only the missing fields are filled —
        # explicitly provided coordinates/timezone are never overwritten.
        if (self.online) and (not self.tz_str or self.lat is None or self.lng is None):
            logging.info("Fetching timezone/coordinates from geonames")

            if not self.city or not self.nation or not self.geonames_username:
                raise KerykeionException("You need to set the city and nation if you want to use the online mode!")

            with FetchGeonames(
                self.city,
                self.nation,
                username=self.geonames_username,
                cache_expire_after_days=self.cache_expire_after_days,
            ) as geonames:
                self.city_data: dict[str, str] = geonames.get_serialized_data()

            if (
                "countryCode" not in self.city_data
                or "timezonestr" not in self.city_data
                or "lat" not in self.city_data
                or "lng" not in self.city_data
            ):
                raise KerykeionException("No data found for this city, try again! Maybe check your connection?")

            if self.lng is None:
                self.lng = float(self.city_data["lng"])
            if self.lat is None:
                self.lat = float(self.city_data["lat"])
            if not self.tz_str:
                self.tz_str = self.city_data["timezonestr"]

    def next_return_from_iso_formatted_time(
        self, iso_formatted_time: str, return_type: SolarLunarReturnType, backwards: bool = False
    ) -> PlanetReturnModel:
        """
        Calculate the next planetary return occurring after a specified ISO-formatted datetime.

        This method computes the exact moment when the specified planet (Sun or Moon) returns
        to its natal position, starting the search from the provided datetime. It uses precise
        ephemeris-backend calculations to determine the exact return moment and generates a
        complete astrological chart for that calculated time.

        The calculation process:
        1. Converts the ISO datetime to Julian Day format for astronomical calculations
        2. Uses the backend's solcross_ut/mooncross_ut to find the exact
           return moment when the planet reaches its natal degree and minute
        3. Creates a complete AstrologicalSubject instance for the calculated return time
        4. Returns a comprehensive PlanetReturnModel with all chart data

        Args:
            iso_formatted_time (str): Starting datetime in ISO format for the search.
                Must be a valid ISO 8601 datetime string (e.g., "2024-01-15T10:30:00"
                or "2024-01-15T10:30:00+00:00"). The method will find the next return
                occurring after this moment, "after" being decided at the whole
                second — the resolution return instants are reported at — so the
                instant of a return this factory reported is a valid seed for the
                following (or, with ``backwards``, the preceding) return.
            return_type (SolarLunarReturnType): Type of planetary return to calculate.
                Must be either "Solar" for Sun returns or "Lunar" for Moon returns.
                This determines which planet's return cycle to compute.
            backwards (bool): If True, search backward in time for the previous
                return instead of forward. Defaults to False.

        Returns:
            PlanetReturnModel: A comprehensive Pydantic model containing complete
                astrological chart data for the calculated return moment, including:
                - Exact return datetime (UTC and local timezone)
                - All planetary positions at the return moment
                - House cusps and angles for the return location
                - Complete astrological subject data with all calculated points
                - Return type identifier and subject name
                - Julian Day Number for the return moment

        Raises:
            KerykeionException: If ``return_type`` is not "Solar" or "Lunar", if
                ``iso_formatted_time`` is not a valid ISO datetime, if the seed's
                UTC instant sits at the edge of the civil range (years 1 to 9999)
                so the search cannot start inside it, or if the return search
                steps outside the available ephemeris date range.

        Examples:
            Calculate next Solar Return after a specific date:

            >>> factory = PlanetaryReturnFactory(subject, ...)
            >>> solar_return = factory.next_return_from_iso_formatted_time(
            ...     "2024-06-15T12:00:00",
            ...     "Solar"
            ... )
            >>> print(f"Solar Return: {solar_return.iso_formatted_local_datetime}")
            >>> print(f"Sun position: {solar_return.sun.abs_pos}°")

            Calculate next Lunar Return with timezone:

            >>> lunar_return = factory.next_return_from_iso_formatted_time(
            ...     "2024-01-01T00:00:00+00:00",
            ...     "Lunar"
            ... )
            >>> print(f"Moon return in {lunar_return.tz_str}")
            >>> print(f"Return occurs: {lunar_return.iso_formatted_local_datetime}")

            Access complete chart data from return:

            >>> return_chart = factory.next_return_from_iso_formatted_time(
            ...     datetime.now().isoformat(),
            ...     "Solar"
            ... )
            >>> # Access planetary positions
            >>> print(f"Sun: {return_chart.sun.abs_pos}° in {return_chart.sun.sign}")
            >>> print(f"Moon: {return_chart.moon.abs_pos}° in {return_chart.moon.sign}")
            >>> # Access house cusps
            >>> print(f"ASC: {return_chart.first_house.abs_pos}°")
            >>> print(f"MC: {return_chart.tenth_house.abs_pos}°")

        Technical Notes:
            - Solar returns typically occur within 1-2 days of the natal birthday
            - Lunar returns occur approximately every 27.3 days (sidereal month)
            - Return moments are calculated to the second for maximum precision
            - The method accounts for leap years and varying orbital speeds
            - Return charts use the factory's configured location, not the natal location

        Use Cases:
            - Annual birthday return chart calculations
            - Monthly lunar return timing for astrological consultation
            - Research into planetary cycle patterns and timing
            - Forecasting and predictive astrology applications
            - Educational demonstrations of astronomical cycles

        See Also:
            next_return_from_year(): Simplified interface for yearly calculations
            next_return_from_date(): Date-based calculation interface
        """

        return self._settled(
            iso_formatted_time,
            backwards,
            lambda start_jd: self._next_return_from_jd(start_jd, return_type, backwards=backwards),
        )

    def _next_return_from_jd(
        self, julian_day: float, return_type: SolarLunarReturnType, backwards: bool = False
    ) -> PlanetReturnModel:
        """Solar/Lunar return search from a Julian Day seed, taken as given.

        The ISO entry point snaps its seed to the reporting resolution before
        arriving here (``_search_start_jd``), so a reported instant steps to
        the next return. The date wrapper passes its midnight seed straight
        through, inclusive: a return in the first second of a date is that
        date's return, as ``next_return_from_date`` has always promised.
        """

        # The natal abs_pos values are expressed in the subject's zodiac
        # (tropical OR sidereal) AND perspective (apparent/true geocentric,
        # topocentric...). The crossing search must run with the same
        # configuration, otherwise a sidereal natal position would be
        # searched against tropical longitudes (~ayanamsa/degree-per-day off,
        # i.e. ~25 days for a solar return with LAHIRI), and e.g. a
        # "True Geocentric" natal Sun would be searched against apparent
        # longitudes (~aberration off, ~8 minutes for a solar return).
        # ephemeris_session configures sidereal mode and perspective and
        # yields the matching iflag.
        perspective_type = self.subject.perspective_type
        if perspective_type == "Heliocentric":
            raise KerykeionException(
                "Solar and Lunar returns search geocentric crossings, which never match a natal "
                "subject computed with perspective_type='Heliocentric'. Use next_heliocentric_return() "
                "(or its from_date/from_iso wrappers) for heliocentric returns."
            )
        if perspective_type not in ("Apparent Geocentric", "True Geocentric", "Topocentric"):
            raise KerykeionException(
                f"Planetary returns are not supported for natal subjects with "
                f"perspective_type='{perspective_type}'. Supported perspectives are "
                "'Apparent Geocentric', 'True Geocentric' and 'Topocentric'."
            )

        # A topocentric natal frame is topocentric at the NATAL location, so
        # the crossing search needs the natal coordinates. The subject model
        # does not store altitude; 0.0 matches the factory default used when
        # the natal chart was computed without an explicit altitude.
        topo = None
        if perspective_type == "Topocentric":
            topo = (self.subject.lng, self.subject.lat, 0.0)

        return_julian_date = None
        with ephemeris_session(
            zodiac_type=self.subject.zodiac_type,
            sidereal_mode=self.subject.sidereal_mode,
            custom_ayanamsa_t0=self.custom_ayanamsa_t0,
            custom_ayanamsa_ayan_t0=self.custom_ayanamsa_ayan_t0,
            perspective_type=perspective_type,
            topo=topo,
        ) as iflag:
            if return_type == "Solar":
                if self.subject.sun is None:
                    raise KerykeionException(
                        "Sun position is required for Solar return but is not available in the subject."
                    )
                if backwards:
                    try:
                        return_julian_date = ephe.solcross_ut(
                            self.subject.sun.abs_pos,
                            julian_day,
                            iflag,
                            backwards=True,
                        )
                    except TypeError:
                        raise KerykeionException(
                            "Backward Solar return search requires the libephemeris backend."
                        )
                    except _BACKEND_ERRORS as exc:
                        raise KerykeionException(
                            "The Solar return search stepped outside the available ephemeris "
                            f"date range; narrow the search window. ({exc})"
                        ) from exc
                else:
                    try:
                        return_julian_date = ephe.solcross_ut(
                            self.subject.sun.abs_pos,
                            julian_day,
                            iflag,
                        )
                    except _BACKEND_ERRORS as exc:
                        raise KerykeionException(
                            "The Solar return search stepped outside the available ephemeris "
                            f"date range; narrow the search window. ({exc})"
                        ) from exc
            elif return_type == "Lunar":
                if self.subject.moon is None:
                    raise KerykeionException(
                        "Moon position is required for Lunar return but is not available in the subject."
                    )
                if backwards:
                    try:
                        return_julian_date = ephe.mooncross_ut(
                            self.subject.moon.abs_pos,
                            julian_day,
                            iflag,
                            backwards=True,
                        )
                    except TypeError:
                        raise KerykeionException(
                            "Backward Lunar return search requires the libephemeris backend."
                        )
                    except _BACKEND_ERRORS as exc:
                        raise KerykeionException(
                            "The Lunar return search stepped outside the available ephemeris "
                            f"date range; narrow the search window. ({exc})"
                        ) from exc
                else:
                    try:
                        return_julian_date = ephe.mooncross_ut(
                            self.subject.moon.abs_pos,
                            julian_day,
                            iflag,
                        )
                    except _BACKEND_ERRORS as exc:
                        raise KerykeionException(
                            "The Lunar return search stepped outside the available ephemeris "
                            f"date range; narrow the search window. ({exc})"
                        ) from exc
            else:
                raise KerykeionException(f"Invalid return type {return_type}. Use 'Solar' or 'Lunar'.")

            if backwards and return_julian_date is not None:
                # The backend treats a body within ~1e-6° of its target as "at
                # the crossing" and jumps a full cycle back: a dead band of
                # ~90 ms for the Sun, ~7 ms for the Moon. A crossing inside the
                # second before the seed is still before it at reporting
                # resolution — look for it explicitly.
                body = self.subject.sun if return_type == "Solar" else self.subject.moon
                assert body is not None
                body_id = ephe.SUN if return_type == "Solar" else ephe.MOON
                target = body.abs_pos

                def geocentric_offset(jd: float) -> float:
                    return self._signed_arc(ephe.calc_ut(jd, body_id, iflag)[0][0], target)

                inside = self._crossing_between(geocentric_offset, julian_day - self._SECOND, julian_day)
                if inside is not None:
                    return_julian_date = inside

        try:
            return_date_utc = julian_to_datetime(return_julian_date)
        except ValueError as exc:
            # julian_to_datetime (and the from_iso_utc_time path below) use
            # Python datetime, which cannot represent years < 1. A return
            # instant landing before 1 CE (e.g. a backwards search from early
            # CE) surfaces as a clear KerykeionException rather than a raw
            # ValueError. BCE returns are not yet supported.
            raise KerykeionException(
                "The return instant falls before 1 CE, which is not supported "
                "(datetime cannot represent BCE years). Narrow the search range."
            ) from exc
        return_date_utc = return_date_utc.replace(tzinfo=timezone.utc)

        # Build kwargs, propagating the source subject's zodiac/sidereal settings
        # so that return charts use the same astrological configuration.
        # v6: also propagate the v6 calc flags configured on this factory so
        # that the return subject computes the same enrichments as the natal
        # (fixed stars, dignities, nakshatra, gauquelin, nutation, local space).
        return_kwargs: dict = dict(
            name=self.subject.name,
            iso_utc_time=return_date_utc.isoformat(),
            lng=self.lng,
            lat=self.lat,
            tz_str=self.tz_str,
            city=self.city,
            nation=self.nation,
            online=False,
            altitude=self.altitude,
            active_points=self.subject.active_points,
            zodiac_type=self.subject.zodiac_type,
            sidereal_mode=self.subject.sidereal_mode,
            houses_system_identifier=self.subject.houses_system_identifier,
            perspective_type=self.subject.perspective_type,
            active_fixed_stars=self.active_fixed_stars,
            calculate_dignities=self.calculate_dignities,
            calculate_nakshatra=self.calculate_nakshatra,
            calculate_gauquelin=self.calculate_gauquelin,
            calculate_nutation=self.calculate_nutation,
            calculate_local_space=self.calculate_local_space,
        )
        # Propagate USER-mode custom ayanamsa parameters if present on the factory
        if self.custom_ayanamsa_t0 is not None:
            return_kwargs["custom_ayanamsa_t0"] = self.custom_ayanamsa_t0
        if self.custom_ayanamsa_ayan_t0 is not None:
            return_kwargs["custom_ayanamsa_ayan_t0"] = self.custom_ayanamsa_ayan_t0

        return_astrological_subject = AstrologicalSubjectFactory.from_iso_utc_time(
            **return_kwargs,  # type: ignore[arg-type]
        )

        model_data = return_astrological_subject.model_dump()
        model_data["name"] = f"{self.subject.name} {return_type} Return"
        model_data["return_type"] = return_type

        return PlanetReturnModel(
            **model_data,
        )

    def next_return_from_year(self, year: int, return_type: SolarLunarReturnType) -> PlanetReturnModel:
        """
        Calculate the planetary return occurring within a specified year.

        .. deprecated::
            Use ``next_return_from_date()`` instead. This method emits a
            DeprecationWarning and delegates to ``next_return_from_date(year, 1, 1, ...)``.

        This is a convenience method that finds the first planetary return (Solar or Lunar)
        that occurs in the given calendar year. It automatically searches from January 1st
        of the specified year and returns the first return found, making it ideal for
        annual forecasting and birthday return calculations.

        For Solar Returns, this typically finds the return closest to the natal birthday
        within that year. For Lunar Returns, it finds the first lunar return occurring
        in January of the specified year.

        The method delegates to next_return_from_date() with January 1st of the
        specified year: an inclusive midnight seed, so a return in the year's
        first second is that year's return (unlike the ISO entry point, whose
        seed's own second is excluded so a reported instant steps).

        Args:
            year (int): The calendar year to search for the return. Must be a valid
                year (typically between 1800-2200 for reliable ephemeris data).
                Examples: 2024, 2025, 1990, 2050.
            return_type (SolarLunarReturnType): The type of planetary return to calculate.
                Must be either "Solar" for Sun returns or "Lunar" for Moon returns.

        Returns:
            PlanetReturnModel: A comprehensive model containing the return chart data
                for the first return found in the specified year. Includes:
                - Exact return datetime in both UTC and local timezone
                - Complete planetary positions at the return moment
                - House cusps calculated for the factory's configured location
                - All astrological chart features and calculated points
                - Return type and subject identification

        Raises:
            KerykeionException: If ``return_type`` is not "Solar" or "Lunar", if
                ``year`` is outside the representable range (1..9999), or if the
                return search steps outside the available ephemeris date range.

        Examples:
            Calculate Solar Return for 2024:

            >>> factory = PlanetaryReturnFactory(subject, ...)
            >>> solar_return_2024 = factory.next_return_from_year(2024, "Solar")
            >>> print(f"2024 Solar Return: {solar_return_2024.iso_formatted_local_datetime}")
            >>> print(f"Birthday location: {solar_return_2024.city}, {solar_return_2024.nation}")

            Calculate first Lunar Return of 2025:

            >>> lunar_return = factory.next_return_from_year(2025, "Lunar")
            >>> print(f"First 2025 Lunar Return: {lunar_return.iso_formatted_local_datetime}")

            Compare multiple years:

            >>> for year in [2023, 2024, 2025]:
            ...     solar_return = factory.next_return_from_year(year, "Solar")
            ...     print(f"{year}: {solar_return.iso_formatted_local_datetime}")

        Practical Applications:
            - Annual Solar Return chart casting for birthday forecasting
            - Comparative analysis of return charts across multiple years
            - Research into planetary return timing patterns
            - Automated birthday return calculations for consultation
            - Educational demonstrations of annual astrological cycles

        Technical Notes:
            - Solar returns in a given year occur near but not exactly on the birthday
            - The exact date can vary by 1-2 days due to leap years and orbital mechanics
            - Lunar returns occur approximately every 27.3 days throughout the year
            - This method finds the chronologically first return in the year
            - Return moment precision is calculated to the second

        Use Cases:
            - Birthday return chart interpretation
            - Annual astrological forecasting
            - Timing analysis for major life events
            - Comparative return chart studies
            - Astrological consultation preparation

        See Also:
            next_return_from_date(): For more specific date-based searches
            next_return_from_iso_formatted_time(): For custom starting dates
        """
        import warnings

        warnings.warn(
            "next_return_from_year is deprecated and will be removed in kerykeion 7.0.0; "
            "use next_return_from_date instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.next_return_from_date(year, 1, 1, return_type=return_type)

    def next_return_from_date(
        self, year: int, month: int, day: int = 1, *, return_type: SolarLunarReturnType, backwards: bool = False
    ) -> PlanetReturnModel:
        """
        Calculate the first planetary return occurring on or after a specified date.

        This method provides precise timing control for planetary return calculations by
        searching from a specific day, month, and year. It's particularly useful for
        finding Lunar Returns when multiple returns occur within a single month
        (approximately every 27.3 days).

        The method searches from midnight (00:00:00 UTC) of the specified date,
        finding the next return that occurs from that point forward.

        Args:
            year (int): The calendar year to search within. Must be a valid year
                within the ephemeris data range (typically 1800-2200).
            month (int): The month to start the search from. Must be between 1 and 12.
            day (int): The day to start the search from. Must be a valid day for the
                specified month (1-28/29/30/31 depending on month). Defaults to 1.
            return_type (SolarLunarReturnType): The type of planetary return to calculate.
                Must be either "Solar" for Sun returns or "Lunar" for Moon returns.
            backwards (bool): If True, search backward in time for the previous
                return instead of forward. Defaults to False.

        Returns:
            PlanetReturnModel: Comprehensive return chart data for the first return
                found on or after the specified date.

        Raises:
            KerykeionException: If month is not between 1 and 12.
            KerykeionException: If day is not valid for the given month/year.
            KerykeionException: If return_type is not "Solar" or "Lunar".

        Examples:
            Find first Lunar Return after January 15, 2024:

            >>> lunar_return = factory.next_return_from_date(
            ...     2024, 1, 15, return_type="Lunar"
            ... )

            Find second Lunar Return in a month (after the first one):

            >>> # First return from start of month
            >>> first_lr = factory.next_return_from_date(2024, 1, 1, return_type="Lunar")
            >>> # Second return from middle of month
            >>> second_lr = factory.next_return_from_date(2024, 1, 15, return_type="Lunar")

        See Also:
            next_return_from_year(): For annual return calculations
            next_return_from_iso_formatted_time(): For custom datetime searches
        """
        # Validate month input
        if month < 1 or month > 12:
            raise KerykeionException(f"Invalid month {month}. Month must be between 1 and 12.")

        # Validate year input — datetime() only accepts 1..9999, and forwarding
        # an out-of-range year would leak a raw ValueError instead of the
        # library's own exception a caller expects from this entry point.
        self._require_valid_year(year)

        # Validate day input
        max_day = calendar.monthrange(year, month)[1]
        if day < 1 or day > max_day:
            raise KerykeionException(f"Invalid day {day} for {year}-{month:02d}. Day must be between 1 and {max_day}.")

        # Create datetime for the specified date (UTC)
        start_date = datetime(year, month, day, 0, 0, tzinfo=timezone.utc)

        # Midnight is the seed, inclusive — NOT the ISO entry point, whose seed
        # is snapped past its own second so that a reported return instant
        # steps to the next return. "The first return of this date" must keep
        # a return that falls in the date's first second.
        return self._next_return_from_jd(datetime_to_julian(start_date), return_type, backwards=backwards)

    def next_return_from_month_and_year(self, year: int, month: int, return_type: SolarLunarReturnType) -> PlanetReturnModel:
        """
        DEPRECATED: Use next_return_from_date() instead.

        Calculate the first planetary return occurring in or after a specified month and year.
        This method is kept for backward compatibility and will be removed in a future version.

        Args:
            year (int): The calendar year to search within.
            month (int): The month to start the search from (1-12).
            return_type (SolarLunarReturnType): "Solar" or "Lunar".

        Returns:
            PlanetReturnModel: Return chart data for the first return found.
        """
        import warnings

        warnings.warn(
            "next_return_from_month_and_year is deprecated and will be removed in "
            "kerykeion 7.0.0; use next_return_from_date instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.next_return_from_date(year, month, 1, return_type=return_type)

    def next_heliocentric_return(
        self,
        planet_name: str,
        start_jd: float,
        backwards: bool = False,
    ) -> PlanetReturnModel:
        """Find when a planet returns to its natal heliocentric longitude.

        Uses ``ephe.helio_cross_ut()`` to find the exact moment a planet
        returns to its natal heliocentric position.

        Args:
            planet_name: Planet name (e.g. "Mars", "Jupiter", "Saturn").
            start_jd: Julian Day to start searching from.
            backwards: If True, search backward in time. Requires the
                libephemeris backend; pyswisseph does not support this.

        Returns:
            PlanetReturnModel for the heliocentric return chart.
        """
        from kerykeion.astrological_subject.factory import STANDARD_PLANETS

        # julian_day is Optional on the model (composite subjects have no
        # single moment in time); without this guard it reaches calc_ut as
        # None and raises a raw, undiagnosable TypeError. Mirrors
        # PrimaryDirectionsFactory's _require_geometry guard.
        if self.subject.julian_day is None:
            raise KerykeionException(
                "Subject is missing Julian Day — cannot compute heliocentric returns "
                "(composite subjects are not supported here)."
            )

        # The public parameter stays `str`; unknown names fall through to the explicit raise below.
        planet_id = STANDARD_PLANETS.get(cast(AstrologicalPoint, planet_name))
        if planet_id is None:
            raise KerykeionException(f"Unknown planet for heliocentric return: {planet_name}")

        # The Sun has no heliocentric longitude (it IS the origin) and the
        # Moon's heliocentric longitude is just Earth's orbit — neither is a
        # meaningful heliocentric return target.
        if planet_name in ("Sun", "Moon"):
            raise KerykeionException(
                f"Heliocentric returns are undefined for {planet_name}: the Sun is the "
                "heliocentric origin and the Moon's heliocentric longitude tracks Earth's orbit. "
                "Use 'Solar' or 'Lunar' geocentric returns instead."
            )

        # Run both the natal lookup and the crossing search with the
        # subject's zodiac configuration so sidereal subjects are searched in
        # sidereal heliocentric longitude (matching the natal value).
        #
        # NOTE: unlike ``nod_aps_ut`` (see nodes_factory, which masks
        # FLG_SIDEREAL out and subtracts the ayanamsa manually because the
        # backend does not apply it there), both ``calc_ut`` and
        # ``helio_cross_ut`` honor FLG_SIDEREAL directly — the crossing search
        # tracks the drifting ayanamsa, so the returned moment is the true
        # sidereal return (verified by
        # test_planetary_return::test_heliocentric_return_sidereal_honors_frame).
        # Do NOT "fix" this by masking the flag; that would yield the tropical
        # return instead.
        with ephemeris_session(
            zodiac_type=self.subject.zodiac_type,
            sidereal_mode=self.subject.sidereal_mode,
            custom_ayanamsa_t0=self.custom_ayanamsa_t0,
            custom_ayanamsa_ayan_t0=self.custom_ayanamsa_ayan_t0,
        ) as iflag:
            helio_iflag = iflag | ephe.FLG_HELCTR

            # Get natal heliocentric longitude
            natal_data = ephe.calc_ut(self.subject.julian_day, planet_id, helio_iflag)
            natal_lon = natal_data[0][0]

            # Find when it returns to that longitude
            if backwards:
                try:
                    return_jd = ephe.helio_cross_ut(planet_id, natal_lon, start_jd, helio_iflag, backwards=True)
                except TypeError:
                    raise KerykeionException(
                        "Backward heliocentric search requires the libephemeris backend."
                    )
                except _BACKEND_ERRORS as exc:
                    raise KerykeionException(
                        "The heliocentric return search stepped outside the available "
                        f"ephemeris date range; narrow the search window. ({exc})"
                    ) from exc
            else:
                try:
                    return_jd = ephe.helio_cross_ut(planet_id, natal_lon, start_jd, helio_iflag)
                except _BACKEND_ERRORS as exc:
                    raise KerykeionException(
                        "The heliocentric return search stepped outside the available "
                        f"ephemeris date range; narrow the search window. ({exc})"
                    ) from exc

            def heliocentric_offset(jd: float) -> float:
                return self._signed_arc(ephe.calc_ut(jd, planet_id, helio_iflag)[0][0], natal_lon)

            # The solver converges to 0.001″ — six seconds of Pluto's motion,
            # two of Uranus', one of Chiron's — so its answer can sit seconds
            # from the crossing, and a seed one second on may be handed back as
            # its own answer. Settle the crossing to a tenth of a millisecond by bisection
            # around the solver's result (no other crossing lies within a
            # minute: the shortest heliocentric period is Mercury's 88 days),
            # so the instant reported is the crossing's own, whatever the seed.
            refined = self._crossing_between(
                heliocentric_offset, return_jd - 60.0 * self._SECOND, return_jd + 60.0 * self._SECOND
            )
            if refined is not None:
                return_jd = refined
            if backwards:
                # A crossing inside the second before the seed is before it at
                # reporting resolution; the solver's past-exclusion may skip it.
                inside = self._crossing_between(heliocentric_offset, start_jd - self._SECOND, start_jd)
                if inside is not None:
                    return_jd = inside

        # Build return chart at that moment (outside the session: subject
        # construction manages its own ephemeris state).
        return_model = self._build_return_chart(return_jd, "Heliocentric")
        return return_model

    def next_lunar_node_crossing(
        self,
        start_jd: float,
        backwards: bool = False,
    ) -> PlanetReturnModel:
        """Find the next moment when the Moon crosses its own node.

        Uses ``ephe.mooncross_node_ut()`` to find when the Moon's
        ecliptic latitude reaches zero (crossing the node).

        Args:
            start_jd: Julian Day to start searching from.
            backwards: If True, search backward in time. Requires the
                libephemeris backend; pyswisseph does not support this.

        Returns:
            PlanetReturnModel for the node crossing chart.
        """
        # Node crossings (Moon latitude = 0) are zodiac-independent, but the
        # session still serializes ephemeris state and provides the base iflag.
        with ephemeris_session() as iflag:
            if backwards:
                try:
                    result = ephe.mooncross_node_ut(start_jd, iflag, backwards=True)
                except TypeError:
                    raise KerykeionException(
                        "Backward lunar node crossing search requires the libephemeris backend."
                    )
                except _BACKEND_ERRORS as exc:
                    raise KerykeionException(
                        "The lunar node crossing search stepped outside the available "
                        f"ephemeris date range; narrow the search window. ({exc})"
                    ) from exc
            else:
                try:
                    result = ephe.mooncross_node_ut(start_jd, iflag)
                except _BACKEND_ERRORS as exc:
                    raise KerykeionException(
                        "The lunar node crossing search stepped outside the available "
                        f"ephemeris date range; narrow the search window. ({exc})"
                    ) from exc
            crossing_jd = result[0]

            if backwards:
                # The Moon crosses its node where its latitude changes sign. A
                # crossing inside the second before the seed is before it at
                # reporting resolution; the solver's dead band (~22 ms) may
                # skip it — look for it explicitly.
                def moon_latitude(jd: float) -> float:
                    return ephe.calc_ut(jd, ephe.MOON, iflag)[0][1]

                inside = self._crossing_between(moon_latitude, start_jd - self._SECOND, start_jd)
                if inside is not None:
                    crossing_jd = inside

        return_model = self._build_return_chart(crossing_jd, "Lunar_Node_Crossing")
        return return_model

    # ── ISO / year convenience wrappers (heliocentric + node crossing) ───────

    def next_heliocentric_return_from_iso_formatted_time(
        self,
        planet_name: str,
        iso_formatted_time: str,
        backwards: bool = False,
    ) -> PlanetReturnModel:
        """Heliocentric return searching forward (or backward) from an ISO datetime.

        Mirrors :meth:`next_return_from_iso_formatted_time` (Solar/Lunar).

        Args:
            planet_name: Planet name (e.g. "Mars", "Jupiter", "Saturn").
            iso_formatted_time: ISO 8601 datetime string to start from. Ordered
                at the whole second, so the instant of a crossing this factory
                reported is a valid seed for the following (or, with
                ``backwards``, the preceding) one.
            backwards: Search backward instead of forward.

        Returns:
            PlanetReturnModel for the heliocentric return chart.
        """
        return self._settled(
            iso_formatted_time,
            backwards,
            lambda start_jd: self.next_heliocentric_return(
                planet_name=planet_name, start_jd=start_jd, backwards=backwards
            ),
        )

    def next_heliocentric_return_from_year(
        self,
        planet_name: str,
        year: int,
    ) -> PlanetReturnModel:
        """First heliocentric return on or after Jan 1 of *year* (UTC).

        Mirrors :meth:`next_return_from_year` (Solar/Lunar).

        Args:
            planet_name: Planet name (e.g. "Mars", "Jupiter", "Saturn").
            year: Calendar year to start searching from.

        Returns:
            PlanetReturnModel for the heliocentric return chart.
        """
        self._require_valid_year(year)
        start = datetime(year, 1, 1, 0, 0, tzinfo=timezone.utc)
        return self.next_heliocentric_return(
            planet_name=planet_name,
            start_jd=datetime_to_julian(start),
        )

    def next_heliocentric_return_from_date(
        self,
        planet_name: str,
        year: int,
        month: int,
        day: int = 1,
        backwards: bool = False,
    ) -> PlanetReturnModel:
        """First heliocentric return on or after a specific date (UTC).

        Mirrors :meth:`next_return_from_date` (Solar/Lunar).

        Args:
            planet_name: Planet name (e.g. "Mars", "Jupiter", "Saturn").
            year: Calendar year.
            month: Month (1-12).
            day: Day of month (default 1).
            backwards: Search backward instead of forward.

        Returns:
            PlanetReturnModel for the heliocentric return chart.
        """
        if month < 1 or month > 12:
            raise KerykeionException(f"Invalid month {month}. Month must be between 1 and 12.")
        max_day = calendar.monthrange(year, month)[1]
        if day < 1 or day > max_day:
            raise KerykeionException(f"Invalid day {day} for {year}-{month:02d}. Day must be between 1 and {max_day}.")
        self._require_valid_year(year)
        start = datetime(year, month, day, 0, 0, tzinfo=timezone.utc)
        return self.next_heliocentric_return(
            planet_name=planet_name,
            start_jd=datetime_to_julian(start),
            backwards=backwards,
        )

    def next_lunar_node_crossing_from_iso_formatted_time(
        self,
        iso_formatted_time: str,
        backwards: bool = False,
    ) -> PlanetReturnModel:
        """Lunar node crossing searching forward (or backward) from an ISO datetime.

        Mirrors :meth:`next_return_from_iso_formatted_time` (Solar/Lunar).

        Args:
            iso_formatted_time: ISO 8601 datetime string to start from. Ordered
                at the whole second, so the instant of a crossing this factory
                reported is a valid seed for the following (or, with
                ``backwards``, the preceding) one.
            backwards: Search backward instead of forward.

        Returns:
            PlanetReturnModel for the node crossing chart.
        """
        return self._settled(
            iso_formatted_time,
            backwards,
            lambda start_jd: self.next_lunar_node_crossing(start_jd=start_jd, backwards=backwards),
        )

    def next_lunar_node_crossing_from_year(
        self,
        year: int,
    ) -> PlanetReturnModel:
        """First lunar node crossing on or after Jan 1 of *year* (UTC).

        Mirrors :meth:`next_return_from_year` (Solar/Lunar).

        Args:
            year: Calendar year to start searching from.

        Returns:
            PlanetReturnModel for the node crossing chart.
        """
        self._require_valid_year(year)
        start = datetime(year, 1, 1, 0, 0, tzinfo=timezone.utc)
        return self.next_lunar_node_crossing(start_jd=datetime_to_julian(start))

    def next_lunar_node_crossing_from_date(
        self,
        year: int,
        month: int,
        day: int = 1,
        backwards: bool = False,
    ) -> PlanetReturnModel:
        """First lunar node crossing on or after a specific date (UTC).

        Mirrors :meth:`next_return_from_date` (Solar/Lunar).

        Args:
            year: Calendar year.
            month: Month (1-12).
            day: Day of month (default 1).
            backwards: Search backward instead of forward.

        Returns:
            PlanetReturnModel for the node crossing chart.
        """
        if month < 1 or month > 12:
            raise KerykeionException(f"Invalid month {month}. Month must be between 1 and 12.")
        max_day = calendar.monthrange(year, month)[1]
        if day < 1 or day > max_day:
            raise KerykeionException(f"Invalid day {day} for {year}-{month:02d}. Day must be between 1 and {max_day}.")
        self._require_valid_year(year)
        start = datetime(year, month, day, 0, 0, tzinfo=timezone.utc)
        return self.next_lunar_node_crossing(
            start_jd=datetime_to_julian(start),
            backwards=backwards,
        )

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _build_return_chart(self, return_jd: float, return_type: str) -> PlanetReturnModel:
        """Build a return chart at the given Julian Day."""
        # isoformat() carries the solver's sub-second part into the ISO string,
        # but from_iso_utc_time rebuilds the chart from an integer `seconds`
        # field, so the sub-second part is truncated downstream (return moments
        # are second-precision, as the class docstring states). For the Moon
        # (~1.5e-4 deg/s) this can shift the rebuilt return Moon by up to ~0.5
        # arcsecond from the exact crossing — well within the 0.1° return
        # tolerance and below display resolution. Kept as isoformat() (not
        # strftime) so no ADDITIONAL rounding is introduced here.
        try:
            return_dt = julian_to_datetime(return_jd).replace(tzinfo=timezone.utc)
        except ValueError as exc:
            raise KerykeionException(
                "The return instant falls before 1 CE, which is not supported "
                "(datetime cannot represent BCE years). Narrow the search range."
            ) from exc
        utc_iso = return_dt.isoformat()

        return_kwargs: dict = dict(
            name=f"{self.subject.name} {return_type} Return",
            iso_utc_time=utc_iso,
            lng=self.lng,
            lat=self.lat,
            tz_str=self.tz_str,
            city=self.city,
            nation=self.nation,
            online=False,
            altitude=self.altitude,
            zodiac_type=self.subject.zodiac_type,
            sidereal_mode=self.subject.sidereal_mode,
            houses_system_identifier=self.subject.houses_system_identifier,
            perspective_type=self.subject.perspective_type,
            active_points=list(self.subject.active_points),
            # v6: forward the calc flags configured on this factory (set
            # explicitly by the caller in v6 mode; default-False otherwise).
            active_fixed_stars=self.active_fixed_stars,
            calculate_dignities=self.calculate_dignities,
            calculate_nakshatra=self.calculate_nakshatra,
            calculate_gauquelin=self.calculate_gauquelin,
            calculate_nutation=self.calculate_nutation,
            calculate_local_space=self.calculate_local_space,
        )

        # Propagate USER-mode custom ayanamsa parameters if present
        if self.custom_ayanamsa_t0 is not None:
            return_kwargs["custom_ayanamsa_t0"] = self.custom_ayanamsa_t0
        if self.custom_ayanamsa_ayan_t0 is not None:
            return_kwargs["custom_ayanamsa_ayan_t0"] = self.custom_ayanamsa_ayan_t0

        return_subject = AstrologicalSubjectFactory.from_iso_utc_time(**return_kwargs)

        model_data = return_subject.model_dump()
        model_data["return_type"] = return_type
        return PlanetReturnModel(**model_data)


if __name__ == "__main__":
    import json

    # Example usage
    subject = AstrologicalSubjectFactory.from_birth_data(
        name="Test Subject",
        lng=-122.4194,
        lat=37.7749,
        tz_str="America/Los_Angeles",
    )

    print("=== Planet Return Calculator ===")
    calculator = PlanetaryReturnFactory(
        subject,
        city="San Francisco",
        nation="USA",
        online=True,
        geonames_username="century.boy",
    )
    date = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    print(f"INITIAL DATE:                   {date.isoformat()}")
    print(f"INITIAL DATE JULIAN:            {datetime_to_julian(date)}")
    print(f"INITIAL DATE REVERSED:          {julian_to_datetime(datetime_to_julian(date)).isoformat()}")
    solar_return = calculator.next_return_from_iso_formatted_time(
        date.isoformat(),
        return_type="Lunar",
    )
    print("--- After ---")
    print(f"Solar Return Date UTC:          {solar_return.iso_formatted_utc_datetime}")
    print(f"Solar Return Date Local:        {solar_return.iso_formatted_local_datetime}")
    print(f"Solar Return JSON:              {json.dumps(solar_return.model_dump(), indent=4)}")
    print(f"Solar Return Julian Data:       {solar_return.julian_day}")
    print(f"ISO UTC:                        {solar_return.iso_formatted_utc_datetime}")

    ## From Date (year, month, day)
    print("=== Planet Return Calculator ===")
    solar_return = calculator.next_return_from_date(
        2026,
        1,
        1,
        return_type="Lunar",
    )
    print("--- From Date (Jan 1) ---")
    print(f"Solar Return Julian Data:       {solar_return.julian_day}")
    print(f"Solar Return Date UTC:          {solar_return.iso_formatted_utc_datetime}")
    ## From Month and Year
    print("=== Planet Return Calculator ===")
    solar_return = calculator.next_return_from_date(
        2026,
        1,
        15,  # Start from January 15
        return_type="Lunar",
    )
    print("--- From Date ---")
    print(f"Solar Return Julian Data:       {solar_return.julian_day}")
    print(f"Solar Return Date UTC:          {solar_return.iso_formatted_utc_datetime}")
