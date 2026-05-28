# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from datetime import timezone
from typing import Optional

from kerykeion.ephemeris_backend import swe
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_literals import SIGN_CODES, SiderealMode, ZodiacType
from kerykeion.schemas.kr_models import VoidOfCourseAspectModel, VoidOfCourseMoonModel
from kerykeion.sun_times.utils import localize_datetime, resolve_timezone
from kerykeion.void_of_course_moon.utils import AspectEvent, compute_void_of_course


def _resolve_iflag(zodiac_type: ZodiacType, sidereal_mode: Optional[SiderealMode]) -> int:
    """Build the ephemeris calculation flags for the requested zodiac.

    Raises:
        KerykeionException: For an unknown ``zodiac_type``/``sidereal_mode``, or a
            missing ``sidereal_mode`` when a sidereal zodiac is requested.
    """
    if zodiac_type not in ("Tropical", "Sidereal"):
        raise KerykeionException(f"Unknown zodiac_type: {zodiac_type!r} (expected 'Tropical' or 'Sidereal').")

    iflag = swe.FLG_SWIEPH | swe.FLG_SPEED
    if zodiac_type == "Sidereal":
        if sidereal_mode is None:
            raise KerykeionException("sidereal_mode is required when zodiac_type='Sidereal'.")
        try:
            swe.set_sid_mode(getattr(swe, f"SIDM_{sidereal_mode}"))
        except AttributeError as exc:
            raise KerykeionException(f"Unknown sidereal_mode: {sidereal_mode!r}.") from exc
        iflag |= swe.FLG_SIDEREAL
    return iflag


def _to_aspect_model(event: Optional[AspectEvent]) -> Optional[VoidOfCourseAspectModel]:
    """Map an internal :class:`AspectEvent` to its public Pydantic model."""
    if event is None:
        return None
    return VoidOfCourseAspectModel(
        planet=event.planet,
        aspect=event.aspect,  # type: ignore[arg-type]
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
            year: Civil year (astronomical numbering: 0 = 1 BCE).
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
        iflag = _resolve_iflag(zodiac_type, sidereal_mode)

        result = compute_void_of_course(moment_utc, iflag)

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
