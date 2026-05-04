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

from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.schemas.kr_models import AstrologicalSubjectModel
from kerykeion.schemas import KerykeionException

DAYS_PER_TROPICAL_YEAR = 365.25


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
    def _natal_birth_utc(natal: AstrologicalSubjectModel) -> datetime:
        """Return the natal birth moment as an aware UTC ``datetime``."""
        if natal.iso_formatted_utc_datetime:
            iso = natal.iso_formatted_utc_datetime.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(iso)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                pass

        try:
            local_tz = ZoneInfo(natal.tz_str or "UTC")
            second = int(getattr(natal, "second", 0) or 0)
            local_dt = datetime(
                natal.year, natal.month, natal.day, natal.hour, natal.minute,
                second, tzinfo=local_tz,
            )
            return local_dt.astimezone(timezone.utc)
        except Exception as exc:  # pragma: no cover - defensive
            raise KerykeionException(
                f"Cannot reconstruct natal UTC datetime: {exc}"
            ) from exc

    @staticmethod
    def _progressed_utc(natal_birth_utc: datetime, target_utc: datetime) -> datetime:
        """Map a real-time target moment onto the progressed scale.

        Symbolic mapping:
            real_years  = (target - birth) / DAYS_PER_TROPICAL_YEAR
            progressed_days = real_years
            progressed_dt   = birth + progressed_days

        i.e. one real-time year of life maps to one real day of motion
        starting from the moment of birth.
        """
        real_seconds = (target_utc - natal_birth_utc).total_seconds()
        real_years = real_seconds / (DAYS_PER_TROPICAL_YEAR * 86400.0)
        progressed_seconds = real_years * 86400.0
        return natal_birth_utc + timedelta(seconds=progressed_seconds)

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
                target_utc = datetime(target_year, 1, 1, tzinfo=timezone.utc)
            except (ValueError, OverflowError, TypeError) as exc:
                raise KerykeionException(
                    f"Invalid `target_year`: {target_year!r}"
                ) from exc
        else:
            try:
                if not isinstance(target_iso_utc_datetime, str):
                    raise TypeError(f"expected str, got {type(target_iso_utc_datetime).__name__}")
                iso = target_iso_utc_datetime.replace("Z", "+00:00")
                target_utc = datetime.fromisoformat(iso)
            except (ValueError, TypeError) as exc:
                raise KerykeionException(
                    f"Invalid `target_iso_utc_datetime`: {target_iso_utc_datetime!r}"
                ) from exc
            if target_utc.tzinfo is None:
                target_utc = target_utc.replace(tzinfo=timezone.utc)
            else:
                target_utc = target_utc.astimezone(timezone.utc)

        natal_birth_utc = SecondaryProgressionFactory._natal_birth_utc(natal_subject)
        progressed_utc = SecondaryProgressionFactory._progressed_utc(
            natal_birth_utc=natal_birth_utc,
            target_utc=target_utc,
        )

        progressed_iso = progressed_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        if progressed_subject_name is None:
            target_label = target_utc.strftime("%Y-%m-%d")
            progressed_subject_name = f"{natal_subject.name} (Progressed {target_label})"

        if natal_subject.lng is None or natal_subject.lat is None:
            raise KerykeionException(
                "Natal subject is missing longitude/latitude — cannot progress."
            )

        return AstrologicalSubjectFactory.from_iso_utc_time(
            name=progressed_subject_name,
            iso_utc_time=progressed_iso,
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
            custom_ayanamsa_t0=getattr(natal_subject, "custom_ayanamsa_t0", None),
            custom_ayanamsa_ayan_t0=getattr(natal_subject, "custom_ayanamsa_ayan_t0", None),
        )
