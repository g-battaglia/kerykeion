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
from typing import Any, Dict, List, Mapping, Optional, Sequence

from pydantic import BaseModel, Field

from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.aspects.aspects_utils import get_aspect_from_two_points
from kerykeion.aspects.orb_utils import OrbAdjustmentStrategy, resolve_pair_orb_adjustment
from kerykeion.ephemeris_backend import swe
from kerykeion.schemas.kr_models import AstrologicalSubjectModel
from kerykeion.schemas import KerykeionException
from kerykeion._predictive_utils import gather_active_points, build_aspect_settings, PTOLEMAIC_ASPECTS
from kerykeion.utilities import datetime_to_julian

# Mean tropical year (epoch J2000) — the "year" unit of the day-for-a-year
# method. Previously 365.25 (the Julian year), which contradicted this name
# and drifted from reference progressed-chart calculators by up to ~3.5 min
# on long progression spans; 365.24219 is the astronomically correct value.
DAYS_PER_TROPICAL_YEAR = 365.24219

class ProgressedToNatalAspect(BaseModel):
    """A progressed-to-natal aspect contact — the predictive timing signal."""

    progressed_point: str = Field(description="Name of the progressed (moving) point.")
    natal_point: str = Field(description="Name of the natal (receiving) point.")
    progressed_abs_pos: float
    natal_abs_pos: float
    aspect: str
    aspect_degrees: int
    orb: float


class SecondaryProgressionsResult(BaseModel):
    """Full secondary progressions result: progressed subject + cross-aspects."""

    natal_name: str
    target_iso_utc_datetime: str = Field(description="Target moment — the real-world date requested (ISO UTC).")
    ephemeris_iso_utc_datetime: str = Field(
        description=(
            "Ephemeris date — the actual date looked up in the ephemeris. "
            "E.g. for a subject born 1990-01-01 progressed to 2026, this "
            "is ~36 days after birth: 1990-02-06."
        )
    )
    progressed_subject: AstrologicalSubjectModel
    progressed_to_natal_aspects: List[ProgressedToNatalAspect] = Field(default_factory=list)

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

    Progressed angles convention (Asc/MC/houses):
        This factory casts a complete chart for the progressed instant at the
        natal location — the **"Q2 / daily houses"** convention. The
        progressed MC is therefore the actual MC of the sky on the ephemeris
        date, sweeping a full ~360° per year of life, and the Ascendant and
        house cusps move with it. This differs from the mainstream default of
        astro.com and Astro-Seek, which keep the *solar-arc-advanced* MC
        (natal MC + the Sun's progressed arc, ~1°/year) and derive the
        Ascendant/houses from that slow-moving MC. Progressed **planet**
        positions are identical under both conventions; only the angles and
        house cusps (and anything derived from them, such as house
        placements) differ — so the progressed Asc/MC reported here will not
        match astro.com's default output.
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
                return swe.julday(target_year, 1, 1, 0.0, swe.GREG_CAL)
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
            raise KerykeionException(
                "`target_iso_utc_datetime` must include `Z` or an explicit UTC offset."
            )
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
        if not (1 <= year <= 9999):
            raise KerykeionException(
                f"Julian Day {jd!r} is outside Python datetime's supported year range."
            )
        return datetime(year, month, day, hour, minute, seconds, tzinfo=timezone.utc)

    @staticmethod
    def _jd_to_utc_iso(jd: float) -> str:
        """Format a Julian Day UT as a UTC ISO timestamp."""
        gregorian_year, _, _, _ = swe.revjul(jd, swe.GREG_CAL)
        if int(gregorian_year) >= 1:
            year, month, day, hour, minute, seconds = SecondaryProgressionFactory._jd_to_components(
                jd, swe.GREG_CAL
            )
            if year > 9999:
                return f"+{year:05d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{seconds:02d}.000000Z"
            return SecondaryProgressionFactory._jd_to_utc_datetime(jd).isoformat(
                timespec="microseconds"
            ).replace("+00:00", "Z")

        year, month, day, hour, minute, seconds = SecondaryProgressionFactory._jd_to_components(
            jd, swe.JUL_CAL
        )
        year_label = f"{year:04d}" if year > 0 else f"-{abs(year):04d}"
        return f"{year_label}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{seconds:02d}.000000Z"

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

        Note:
            Angles and house cusps follow the "Q2 / daily houses" convention:
            they are the real angles of the sky at the progressed instant
            (progressed MC ≈ 360°/year), NOT the solar-arc-advanced angles
            (~1°/year) that astro.com / Astro-Seek report by default.
            Progressed planet positions are unaffected by this choice. See
            the class docstring for details.
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
        # Heterogeneous keyword bundle forwarded via ** to the factory entry points.
        common_kwargs: Dict[str, Any] = dict(
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

    @staticmethod
    def compute_full(
        natal_subject: AstrologicalSubjectModel,
        *,
        target_iso_utc_datetime: Optional[str] = None,
        target_year: Optional[int] = None,
        progressed_subject_name: Optional[str] = None,
        active_points: Optional[Sequence[str]] = None,
        compute_aspects: bool = True,
        aspect_orb: float = 3.0,
        aspects: Optional[Sequence[str]] = None,
        point_orb_adjustments: Optional[Mapping[str, float]] = None,
        point_orb_adjustment_strategy: OrbAdjustmentStrategy = "max_explicit",
    ) -> SecondaryProgressionsResult:
        """Build the progressed chart with optional progressed-to-natal aspects.

        Wraps :meth:`compute` and adds cross-chart aspect detection, following
        the same pattern as :meth:`SolarArcFactory.compute`. The progressed
        angles follow the same "Q2 / daily houses" convention as
        :meth:`compute` (progressed MC ≈ 360°/year, unlike astro.com's
        solar-arc-advanced default — see the class docstring).

        Args:
            natal_subject: Fully-built natal subject.
            target_iso_utc_datetime: ISO-8601 UTC target timestamp.
            target_year: Convenience target year (Jan 1 00:00 UTC).
            progressed_subject_name: Optional name override for the progressed
                subject.
            active_points: Points to include in aspect detection.
                Defaults to :data:`DEFAULT_PREDICTIVE_POINTS`.
            compute_aspects: If ``True`` (default), compute the progressed-to-
                natal aspect list.
            aspect_orb: Orb in degrees for cross-aspect detection (default 3.0,
                the conventional tight orb for predictive work).
            aspects: Optional whitelist of aspect names to detect.
            point_orb_adjustments: Optional per-point orb adjustment table.
                ``None`` (default) means no adjustment — progressions use a
                flat, tight orb regardless of which point is involved.
            point_orb_adjustment_strategy: How to combine the two points'
                adjustments when a table is supplied (default ``"max_explicit"``).

        Returns:
            A :class:`SecondaryProgressionsResult` with the progressed subject
            and (optionally) the cross-aspect contacts.
        """
        progressed = SecondaryProgressionFactory.compute(
            natal_subject,
            target_iso_utc_datetime=target_iso_utc_datetime,
            target_year=target_year,
            progressed_subject_name=progressed_subject_name,
        )

        natal_jd = SecondaryProgressionFactory._natal_jd(natal_subject)
        target_jd = SecondaryProgressionFactory._target_to_jd(
            target_iso_utc_datetime, target_year
        )
        progressed_jd = SecondaryProgressionFactory._progressed_jd(natal_jd, target_jd)

        result_target_iso = SecondaryProgressionFactory._jd_to_utc_iso(target_jd)
        ephemeris_iso = SecondaryProgressionFactory._jd_to_utc_iso(progressed_jd)

        progressed_to_natal: List[ProgressedToNatalAspect] = []
        if compute_aspects:
            progressed_points = gather_active_points(progressed, active_points)
            natal_targets = gather_active_points(natal_subject, natal_subject.active_points)
            effective_aspects = aspects if aspects is not None else PTOLEMAIC_ASPECTS
            aspect_settings = build_aspect_settings(aspect_orb, effective_aspects)

            for prog_name, prog_pos in progressed_points:
                for natal_name, natal_pos in natal_targets:
                    extra_orb = resolve_pair_orb_adjustment(
                        prog_name,
                        natal_name,
                        point_orb_adjustments,
                        point_orb_adjustment_strategy,
                    )
                    outcome = get_aspect_from_two_points(
                        aspects_settings=aspect_settings,
                        point_one=prog_pos,
                        point_two=natal_pos,
                        extra_orb=extra_orb,
                    )
                    if outcome.get("verdict"):
                        progressed_to_natal.append(
                            ProgressedToNatalAspect(
                                progressed_point=prog_name,
                                natal_point=natal_name,
                                progressed_abs_pos=prog_pos,
                                natal_abs_pos=natal_pos,
                                aspect=outcome["name"],
                                aspect_degrees=outcome["aspect_degrees"],
                                orb=outcome["orbit"],
                            )
                        )

        return SecondaryProgressionsResult(
            natal_name=natal_subject.name,
            target_iso_utc_datetime=result_target_iso,
            ephemeris_iso_utc_datetime=ephemeris_iso,
            progressed_subject=progressed,
            progressed_to_natal_aspects=progressed_to_natal,
        )
