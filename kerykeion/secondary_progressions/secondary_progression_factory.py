# -*- coding: utf-8 -*-
"""
Secondary progressions factory.

The *secondary progression* is the most widely used predictive technique
in Western astrology. Its symbolism is "a day for a year": the chart
calculated for the natal location ``N`` real days after birth represents
the ``N``-th year of the native's life. The Sun progresses ~1° / year, the
Moon ~12° / year, and the slower planets shift only a few degrees in a
lifetime — most of the predictive value sits in the fast bodies and in
their angular contacts with the natal chart.

This factory wraps :class:`AstrologicalSubjectFactory` to build the
progressed chart for any target moment, reusing all of the natal subject's
calculation settings (zodiac type, sidereal mode, house system,
perspective, active points, altitude, location, timezone).

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.ephemeris_backend import swe
from kerykeion.schemas.kr_models import AstrologicalSubjectModel
from kerykeion.schemas import KerykeionException
from kerykeion.utilities import datetime_to_julian

DAYS_PER_TROPICAL_YEAR = 365.25

_ANCIENT_ISO_RE = re.compile(
    r"^(?P<year>[+-]?\d{4,})-(?P<month>\d{2})-(?P<day>\d{2})"
    r"(?:[T\s](?P<hour>\d{2})(?::(?P<minute>\d{2})"
    r"(?::(?P<second>\d{2}(?:\.\d+)?))?)?)?"
    r"(?P<tz>Z|[+-]\d{2}:?\d{2})?$"
)


class SecondaryProgressionFactory:
    """Compute the secondary-progressed chart for a given target moment.

    Example::

        from kerykeion import AstrologicalSubjectFactory, SecondaryProgressionFactory

        natal = AstrologicalSubjectFactory.from_birth_data(
            "John", 1990, 6, 15, 14, 30,
            lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
        )
        progressed = SecondaryProgressionFactory.compute(
            natal,
            target_iso_utc_datetime="2026-04-25T00:00:00Z",
        )
        print(progressed.sun.sign, progressed.moon.sign)

    The returned object is a regular :class:`AstrologicalSubjectModel` whose
    ``year/month/day/hour/minute`` fields refer to the *progressed* moment
    (i.e. the moment ``birth_date + delta_years_in_days``), so every
    downstream tool (aspects, dignities, chart drawer) keeps working
    transparently.
    """

    @staticmethod
    def _natal_jd(natal: AstrologicalSubjectModel) -> float:
        """Return the natal birth moment as Julian Day UT."""
        if natal.julian_day is None:
            raise KerykeionException("Natal subject is missing Julian Day - cannot progress.")
        return natal.julian_day

    @staticmethod
    def _parse_ancient_iso_to_jd(iso_datetime: str) -> float:
        """Parse an ISO-like timestamp with a year unsupported by ``datetime``."""
        match = _ANCIENT_ISO_RE.fullmatch(iso_datetime)
        if match is None:
            raise ValueError(f"Invalid ancient ISO timestamp: {iso_datetime!r}")

        year = int(match.group("year"))
        month = int(match.group("month"))
        day = int(match.group("day"))
        hour = int(match.group("hour") or 0)
        minute = int(match.group("minute") or 0)
        second = float(match.group("second") or 0.0)
        tz_part = match.group("tz")
        if tz_part is None:
            raise ValueError(
                f"Timezone is required for target_iso_utc_datetime: {iso_datetime!r}"
            )

        if not (1 <= month <= 12 and 1 <= day <= 31):
            raise ValueError(f"Invalid ancient ISO date: {iso_datetime!r}")
        if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second < 60):
            raise ValueError(f"Invalid ancient ISO time: {iso_datetime!r}")

        if tz_part == "Z":
            utc_offset_hours = 0.0
        else:
            sign = 1.0 if tz_part[0] == "+" else -1.0
            offset_body = tz_part[1:].replace(":", "")
            offset_hours = int(offset_body[:2])
            offset_minutes = int(offset_body[2:])
            if not (0 <= offset_hours <= 23 and 0 <= offset_minutes <= 59):
                raise ValueError(f"Invalid ancient ISO offset: {iso_datetime!r}")
            utc_offset_hours = sign * (offset_hours + offset_minutes / 60.0)

        decimal_hour = hour + minute / 60.0 + second / 3600.0
        calendar_flag = swe.JUL_CAL if year < 1 else swe.GREG_CAL
        local_jd = swe.julday(year, month, day, decimal_hour, calendar_flag)
        parsed_year, parsed_month, parsed_day, _ = swe.revjul(local_jd, calendar_flag)
        if (int(parsed_year), int(parsed_month), int(parsed_day)) != (year, month, day):
            raise ValueError(f"Invalid ancient ISO date: {iso_datetime!r}")
        return local_jd - utc_offset_hours / 24.0

    @staticmethod
    def _target_to_jd(
        target_iso_utc_datetime: Optional[str],
        target_year: Optional[int],
    ) -> float:
        """Convert a target timestamp/year to Julian Day UT."""
        if target_iso_utc_datetime is not None and target_year is not None:
            raise KerykeionException(
                "Pass exactly one of `target_iso_utc_datetime` or `target_year`."
            )
        if target_iso_utc_datetime is None and target_year is None:
            raise KerykeionException(
                "Pass one of `target_iso_utc_datetime` or `target_year`."
            )

        if target_year is not None:
            try:
                if target_year < 1:
                    return swe.julday(target_year, 1, 1, 0.0, swe.JUL_CAL)
                target_utc = datetime(target_year, 1, 1, tzinfo=timezone.utc)
                return datetime_to_julian(target_utc)
            except (ValueError, OverflowError, TypeError) as exc:
                raise KerykeionException(
                    f"Invalid `target_year`: {target_year!r}"
                ) from exc

        try:
            if not isinstance(target_iso_utc_datetime, str):
                raise TypeError(f"expected str, got {type(target_iso_utc_datetime).__name__}")
            iso = target_iso_utc_datetime.replace("Z", "+00:00")
            try:
                target_utc = datetime.fromisoformat(iso)
            except ValueError:
                return SecondaryProgressionFactory._parse_ancient_iso_to_jd(
                    target_iso_utc_datetime
                )
        except (ValueError, TypeError) as exc:
            raise KerykeionException(
                f"Invalid `target_iso_utc_datetime`: {target_iso_utc_datetime!r}"
            ) from exc

        if target_utc.tzinfo is None:
            target_utc = target_utc.replace(tzinfo=timezone.utc)
        else:
            target_utc = target_utc.astimezone(timezone.utc)
        return datetime_to_julian(target_utc)

    @staticmethod
    def _progressed_jd(natal_jd: float, target_jd: float) -> float:
        """Map a real-time target moment onto the progressed Julian Day scale.

        Symbolic mapping:
            real_years  = (target - birth) / DAYS_PER_TROPICAL_YEAR
            progressed_jd = birth + real_years

        i.e. one real-time year of life maps to one real day of motion
        starting from the moment of birth.
        """
        real_years = (target_jd - natal_jd) / DAYS_PER_TROPICAL_YEAR
        return natal_jd + real_years

    @staticmethod
    def _jd_to_components(jd: float, calendar_flag: int) -> tuple[int, int, int, int, int, int]:
        """Convert a JD to integer date/time components in the requested calendar."""
        year, month, day, decimal_hour = swe.revjul(jd, calendar_flag)
        total_seconds = int(round(decimal_hour * 3600.0))
        if total_seconds >= 86400:
            next_midnight = swe.julday(int(year), int(month), int(day), 0.0, calendar_flag) + 1.0
            year, month, day, _ = swe.revjul(next_midnight, calendar_flag)
            total_seconds = 0

        hour = total_seconds // 3600
        minute = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return int(year), int(month), int(day), hour, minute, seconds

    @staticmethod
    def _jd_to_utc_datetime(jd: float) -> datetime:
        """Convert a CE Julian Day UT to an aware UTC ``datetime``."""
        year, month, day, hour, minute, seconds = SecondaryProgressionFactory._jd_to_components(
            jd, swe.GREG_CAL
        )
        return datetime(year, month, day, hour, minute, seconds, tzinfo=timezone.utc)

    @staticmethod
    def _jd_to_utc_iso(jd: float) -> str:
        """Format a Julian Day UT as a UTC ISO timestamp."""
        gregorian_year, _, _, _ = swe.revjul(jd, swe.GREG_CAL)
        if int(gregorian_year) >= 1:
            return SecondaryProgressionFactory._jd_to_utc_datetime(jd).isoformat(
                timespec="microseconds"
            ).replace("+00:00", "Z")

        year, month, day, hour, minute, seconds = SecondaryProgressionFactory._jd_to_components(
            jd, swe.JUL_CAL
        )
        year_label = f"{year:04d}" if year > 0 else f"-{abs(year):04d}"
        return f"{year_label}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{seconds:02d}+00:00"

    @staticmethod
    def _jd_to_date_label(jd: float) -> str:
        """Format a target JD as a calendar date label."""
        gregorian_year, _, _, _ = swe.revjul(jd, swe.GREG_CAL)
        calendar_flag = swe.GREG_CAL if int(gregorian_year) >= 1 else swe.JUL_CAL
        year, month, day, _, _, _ = SecondaryProgressionFactory._jd_to_components(
            jd, calendar_flag
        )
        year_label = f"{year:04d}" if year > 0 else f"-{abs(year):04d}"
        return f"{year_label}-{month:02d}-{day:02d}"

    @staticmethod
    def compute(
        natal_subject: AstrologicalSubjectModel,
        *,
        target_iso_utc_datetime: Optional[str] = None,
        target_year: Optional[int] = None,
        progressed_subject_name: Optional[str] = None,
    ) -> AstrologicalSubjectModel:
        """Build the secondary-progressed chart for ``natal_subject`` at the
        requested target moment.

        Args:
            natal_subject: A fully-built natal :class:`AstrologicalSubjectModel`.
                All calculation settings (zodiac type, sidereal mode,
                house system, perspective, altitude, active points) are
                copied from this subject so the progressed chart stays
                consistent with the natal one.
            target_iso_utc_datetime: ISO-8601 UTC timestamp of the target
                moment (e.g. ``"2026-04-25T00:00:00Z"``). Mutually
                exclusive with ``target_year``.
            target_year: Convenience: the calendar year for which to
                progress (the moment used is January 1st of that year at
                00:00 UTC). Mutually exclusive with ``target_iso_utc_datetime``.
            progressed_subject_name: Optional override for the returned
                subject's ``name``. Defaults to
                ``"<natal.name> (Progressed YYYY-MM-DD)"``.

        Returns:
            An :class:`AstrologicalSubjectModel` representing the progressed
            chart at the natal location.

        Raises:
            KerykeionException: If neither ``target_iso_utc_datetime`` nor
                ``target_year`` is supplied, or if both are supplied, or
                if the natal subject is missing critical data.
        """
        natal_jd = SecondaryProgressionFactory._natal_jd(natal_subject)
        target_jd = SecondaryProgressionFactory._target_to_jd(
            target_iso_utc_datetime, target_year
        )
        progressed_jd = SecondaryProgressionFactory._progressed_jd(natal_jd, target_jd)

        if progressed_subject_name is None:
            target_label = SecondaryProgressionFactory._jd_to_date_label(target_jd)
            progressed_subject_name = f"{natal_subject.name} (Progressed {target_label})"

        if natal_subject.lng is None or natal_subject.lat is None:
            raise KerykeionException(
                "Natal subject is missing longitude/latitude — cannot progress."
            )

        progressed_year_gregorian, _, _, _ = swe.revjul(progressed_jd, swe.GREG_CAL)
        common_kwargs = dict(
            name=progressed_subject_name,
            city=natal_subject.city or "Natal Location",
            nation=natal_subject.nation or "",
            tz_str=natal_subject.tz_str or "UTC",
            online=False,
            lng=natal_subject.lng,
            lat=natal_subject.lat,
            zodiac_type=natal_subject.zodiac_type,
            sidereal_mode=natal_subject.sidereal_mode,
            houses_system_identifier=natal_subject.houses_system_identifier,
            perspective_type=natal_subject.perspective_type,
            altitude=getattr(natal_subject, "altitude", None),
            active_points=natal_subject.active_points,
            calculate_lunar_phase=True,
            custom_ayanamsa_t0=natal_subject.custom_ayanamsa_t0,
            custom_ayanamsa_ayan_t0=natal_subject.custom_ayanamsa_ayan_t0,
        )

        if int(progressed_year_gregorian) >= 1:
            progressed_iso = SecondaryProgressionFactory._jd_to_utc_iso(progressed_jd)
            return AstrologicalSubjectFactory.from_iso_utc_time(
                iso_utc_time=progressed_iso,
                **common_kwargs,
            )

        # The BCE path interprets from_birth_data input as Local Mean Time.
        # Convert the progressed UT JD to LMT components before delegating.
        lmt_offset_hours = natal_subject.lng / 15.0
        progressed_lmt_jd = progressed_jd + lmt_offset_hours / 24.0
        year, month, day, hour, minute, seconds = SecondaryProgressionFactory._jd_to_components(
            progressed_lmt_jd, swe.JUL_CAL
        )
        return AstrologicalSubjectFactory.from_birth_data(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            seconds=seconds,
            **common_kwargs,
        )
