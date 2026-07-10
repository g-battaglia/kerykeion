# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from kerykeion.ephemeris_backend import ephemeris_session, ephe
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_literals import SIGN_CODES, SiderealMode, ZodiacType
from kerykeion.schemas.kr_models import (
    VoidOfCourseAspectModel,
    VoidOfCourseMoonModel,
    VoidOfCourseWindowModel,
    VoidOfCourseWindowsCollectionModel,
)
from kerykeion.sun_times.utils import localize_datetime, resolve_timezone
from kerykeion.utilities import datetime_to_julian
from kerykeion.void_of_course_moon.utils import AspectEvent, compute_void_of_course, compute_void_windows


def _validate_zodiac(zodiac_type: ZodiacType, sidereal_mode: Optional[SiderealMode]) -> None:
    """Validate the zodiac configuration before opening an ephemeris session.

    Pure validation — no global ephemeris state is touched here; the session
    itself configures path and sidereal mode from the validated values.

    Raises:
        KerykeionException: For an unknown ``zodiac_type``/``sidereal_mode``, a
            missing ``sidereal_mode`` when a sidereal zodiac is requested, or the
            unsupported ``"USER"`` mode.
    """
    if zodiac_type not in ("Tropical", "Sidereal"):
        raise KerykeionException(f"Unknown zodiac_type: {zodiac_type!r} (expected 'Tropical' or 'Sidereal').")

    if zodiac_type == "Sidereal":
        if sidereal_mode is None:
            raise KerykeionException("sidereal_mode is required when zodiac_type='Sidereal'.")
        if sidereal_mode == "USER":
            raise KerykeionException(
                "sidereal_mode='USER' requires custom ayanamsha parameters, which VoidOfCourseMoonFactory does not accept."
            )
        if not hasattr(ephe, f"SIDM_{sidereal_mode}"):
            raise KerykeionException(f"Unknown sidereal_mode: {sidereal_mode!r}.")


def _to_aspect_model(event: Optional[AspectEvent]) -> Optional[VoidOfCourseAspectModel]:
    """Map an internal :class:`AspectEvent` to its public Pydantic model."""
    if event is None:
        return None
    return VoidOfCourseAspectModel(
        planet=event.planet,
        aspect=event.aspect,
        aspect_degrees=event.degrees,
        exact_time=event.exact_time,
    )


class VoidOfCourseMoonFactory:
    """
    Factory for the void-of-course Moon at a given moment.

    The Moon is *void of course* once it has perfected its last exact Ptolemaic
    aspect (conjunction, sextile, square, trine, opposition) to a traditional
    planet (Sun, Mercury, Venus, Mars, Jupiter, Saturn) while in its current sign,
    and remains void until it ingresses into the next sign — a window during which
    the Moon "makes no further connection", traditionally read as a time when
    matters initiated tend not to come to a decisive outcome.

    The result depends only on geocentric ecliptic longitudes, so it is
    independent of the observer's location (no latitude/longitude needed). Both
    the tropical and sidereal zodiacs are supported; under a sidereal zodiac the
    sign boundaries (and hence the ingress) shift by the chosen ayanamsha.

    Example:
        >>> from kerykeion import VoidOfCourseMoonFactory
        >>> voc = VoidOfCourseMoonFactory.from_datetime(
        ...     2026, 6, 1, 9, 0, tz_str="Europe/Rome")
        >>> voc.is_void_of_course, voc.moon_sign, voc.next_sign
        (True, 'Sag', 'Cap')

    Note:
        The aspecting set and the five Ptolemaic aspects follow the classical
        definition of void of course; the modern outer planets are intentionally
        excluded.
    """

    @classmethod
    def from_datetime(
        cls,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int = 0,
        *,
        tz_str: str,
        zodiac_type: ZodiacType = "Tropical",
        sidereal_mode: Optional[SiderealMode] = None,
    ) -> VoidOfCourseMoonModel:
        """
        Compute the void-of-course Moon state for a moment.

        Args:
            year: Gregorian civil year (1-9999 CE).
            month: Civil month (1-12).
            day: Civil day (1-31).
            hour: Hour of day (0-23) in ``tz_str``.
            minute: Minute (0-59) in ``tz_str``. Defaults to 0.
            tz_str: IANA timezone identifier the clock time is expressed in.
            zodiac_type: ``"Tropical"`` (default) or ``"Sidereal"``.
            sidereal_mode: Ayanamsha to use when ``zodiac_type='Sidereal'``
                (required in that case; ignored otherwise).

        Returns:
            VoidOfCourseMoonModel: void state, current/next sign, ingress, the void
            window, and the framing last/next aspects.

        Raises:
            KerykeionException: For an invalid timezone or zodiac configuration.
        """
        tz = resolve_timezone(tz_str)
        moment_utc = localize_datetime(year, month, day, hour, minute, tz=tz).astimezone(timezone.utc)
        _validate_zodiac(zodiac_type, sidereal_mode)
        # The session serializes access to the process-global backend state
        # (path + sidereal mode) and resets it on exit without degrading the
        # pinned calculation mode; its iflag already includes FLG_SPEED (plus
        # FLG_SIDEREAL for sidereal zodiacs).
        with ephemeris_session(zodiac_type=zodiac_type, sidereal_mode=sidereal_mode) as iflag:
            try:
                result = compute_void_of_course(moment_utc, iflag)
            except getattr(ephe, "Error", ()) as exc:
                # The forward/backward Moon scans walk off the ephemeris near
                # either edge; the raw backend range error is not this factory's
                # documented contract. Normalize it to KerykeionException
                # (mirrors lunation_factory). KerykeionException/ValueError
                # contract errors are not caught and pass through unchanged.
                raise KerykeionException(
                    f"Void-of-course computation failed at {moment_utc.isoformat()}: "
                    f"{exc}. This usually means the date falls outside the available "
                    f"ephemeris range; narrow the date range."
                ) from exc

        return VoidOfCourseMoonModel(
            is_void_of_course=result.is_void_of_course,
            moon_sign=SIGN_CODES[result.moon_sign_index],
            next_sign=SIGN_CODES[result.next_sign_index],
            ingress=result.ingress,
            void_start=result.void_start,
            void_end=result.void_end,
            last_aspect=_to_aspect_model(result.last_aspect),
            next_aspect=_to_aspect_model(result.next_aspect),
        )

    @classmethod
    def from_iso_range(
        cls,
        start_date: str,
        end_date: str,
        *,
        zodiac_type: ZodiacType = "Tropical",
        sidereal_mode: Optional[SiderealMode] = None,
    ) -> VoidOfCourseWindowsCollectionModel:
        """
        Every void-of-course window intersecting an ISO date(time) range (UTC).

        The Moon is walked sign by sign across the range (~13.7 spans per
        month); each span yields one window, from the Moon's last exact in-sign
        Ptolemaic aspect to its ingress into the next sign. Windows are
        returned **unclipped**: the first may start before ``start_date`` and
        the last may end after ``end_date``.

        Args:
            start_date: ISO date or datetime, e.g. ``"2026-01-01"``.
            end_date: ISO date or datetime; a date-only value means "through
                the end of that UTC day".
            zodiac_type: ``"Tropical"`` (default) or ``"Sidereal"``. Aspect
                perfection times are zodiac-independent; sign boundaries (and
                hence the ingresses framing each window) shift with the
                ayanamsha.
            sidereal_mode: Ayanamsha when ``zodiac_type='Sidereal'``.

        Returns:
            VoidOfCourseWindowsCollectionModel: chronologically ordered,
            non-overlapping windows.

        Raises:
            KerykeionException: For an invalid ISO input, an invalid zodiac
                configuration, or an ephemeris-range failure mid-scan.
        """
        try:
            start_dt = cls._to_utc_naive(datetime.fromisoformat(start_date))
            end_dt = cls._to_utc_naive(datetime.fromisoformat(end_date))
        except (ValueError, TypeError) as exc:
            # Same contract as SignIngressFactory.from_iso_range.
            raise KerykeionException(
                f"Invalid ISO date/datetime for void-of-course range "
                f"(start_date={start_date!r}, end_date={end_date!r}): {exc}"
            ) from exc
        if "T" not in end_date and "t" not in end_date and " " not in end_date:
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        start_jd = datetime_to_julian(start_dt)
        end_jd = datetime_to_julian(end_dt)

        _validate_zodiac(zodiac_type, sidereal_mode)
        if end_jd > start_jd:
            with ephemeris_session(zodiac_type=zodiac_type, sidereal_mode=sidereal_mode) as iflag:
                try:
                    raw_windows = compute_void_windows(start_jd, end_jd, iflag)
                except getattr(ephe, "Error", ()) as exc:
                    # Same normalization as from_datetime: backend range errors
                    # become the documented exception type.
                    raise KerykeionException(
                        f"Void-of-course window scan failed for "
                        f"[{start_date!r}, {end_date!r}]: {exc}. This usually means "
                        f"the date falls outside the available ephemeris range; "
                        f"narrow the date range."
                    ) from exc
        else:
            raw_windows = []

        return VoidOfCourseWindowsCollectionModel(
            start_jd=start_jd,
            end_jd=end_jd,
            windows=[
                VoidOfCourseWindowModel(
                    moon_sign=SIGN_CODES[w.moon_sign_index],
                    next_sign=SIGN_CODES[w.next_sign_index],
                    void_start=w.void_start,
                    void_end=w.void_end,
                    duration_minutes=round((w.void_end - w.void_start).total_seconds() / 60.0, 2),
                    last_aspect=_to_aspect_model(w.last_aspect),
                )
                for w in raw_windows
            ],
        )

    @staticmethod
    def _to_utc_naive(dt: datetime) -> datetime:
        """Normalize an offset-aware datetime to naive UTC (see lunation factory)."""
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
