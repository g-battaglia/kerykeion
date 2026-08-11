# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from typing import List, Optional, Tuple, cast

from kerykeion.schemas.literals import ClassicalPlanet
from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.schemas.models import (
    AstrologicalSubjectModel,
    FirdariaModel,
    FirdariaPeriodModel,
    FirdariaSubPeriodModel,
)
from kerykeion.utilities.core import (
    civil_jd,
    jd_to_iso_datetime,
    parse_astronomical_iso_moment,
    resolve_subject_local_moment,
    resolve_subject_local_now,
)

# A firdaria "year" is the Julian year of 365.25 days — the convention shared
# by the common two-level implementations this factory is validated against.
# (Zodiacal releasing uses the tropical year; the two techniques carry their
# own historical conventions and are deliberately not unified.)
JULIAN_YEAR_DAYS = 365.25

# Major-period sequences (lord, years). Day charts open with the Sun, night
# charts with the Moon; the two lunar nodes close the 75-year cycle.
DIURNAL_SEQUENCE: Tuple[Tuple[str, int], ...] = (
    ("Sun", 10),
    ("Venus", 8),
    ("Mercury", 13),
    ("Moon", 9),
    ("Saturn", 11),
    ("Jupiter", 12),
    ("Mars", 7),
    ("North_Node", 3),
    ("South_Node", 2),
)
NOCTURNAL_SEQUENCE: Tuple[Tuple[str, int], ...] = (
    ("Moon", 9),
    ("Saturn", 11),
    ("Jupiter", 12),
    ("Mars", 7),
    ("Sun", 10),
    ("Venus", 8),
    ("Mercury", 13),
    ("North_Node", 3),
    ("South_Node", 2),
)

# The nodes rule no sub-periods and are excluded from the sub-lord ring.
NODES = frozenset({"North_Node", "South_Node"})


def _jd_second_grid(jd: float) -> int:
    """Whole-second grid shared by serialization and current-selection.

    Boundaries are fractional Julian Days; the public ``start``/``end``
    timestamps round them to the second, so the "which period contains the
    target" comparison must happen on the same grid — otherwise feeding a
    serialized boundary back as ``target_date`` could disagree with it by a
    sub-second residue.
    """
    return round(jd * 86400.0)

# How far the timeline is unrolled, in years of life. The 75-year cycle
# repeats, so the cap only bounds the output length.
DEFAULT_LIFE_CAP_YEARS = 120


class FirdariaFactory:
    """Compute the firdaria periods of a chart.

    All date arithmetic runs on Julian Days over the subject's LOCAL
    wall-clock anchor (never ``datetime``), so deep-BCE births — which the
    engine supports elsewhere — build a timeline too.

    Example:
        >>> from kerykeion import AstrologicalSubjectFactory, FirdariaFactory
        >>> subject = AstrologicalSubjectFactory.from_birth_data(
        ...     "Jane", 1990, 6, 15, 12, 0, lat=41.9, lng=12.5, tz_str="Europe/Rome")
        >>> firdaria = FirdariaFactory.from_subject(subject, target_date="2026-06-04")
        >>> firdaria.periods[0].lord in ("Sun", "Moon")
        True
    """

    @classmethod
    def from_subject(
        cls,
        subject: AstrologicalSubjectModel,
        *,
        target_date: Optional[str] = None,
        life_cap_years: int = DEFAULT_LIFE_CAP_YEARS,
    ) -> FirdariaModel:
        """Build the firdaria timeline for a subject.

        Args:
            subject: The natal chart. Requires a real sect: ``is_diurnal``
                must be a boolean. A midpoint composite (``None``) has no
                horizon and is rejected — never guessed.
            target_date: ISO date or datetime the current period is resolved
                against; astronomical year numbering is accepted (e.g.
                ``'-0550-10-07'``). When omitted, now in the subject's
                timezone.
            life_cap_years: How far the timeline is unrolled.

        Returns:
            A :class:`FirdariaModel`.

        Raises:
            KerykeionException: When the sect is unresolvable, the birth
                moment is missing, or ``target_date`` is unparseable.
        """
        is_diurnal = getattr(subject, "is_diurnal", None)
        if not isinstance(is_diurnal, bool):
            raise KerykeionException(
                "Firdaria requires the chart's sect, and this subject carries "
                "no boolean is_diurnal (a midpoint composite has no horizon; "
                "an averaged one must never be derived). Refusing to guess."
            )

        # Local wall-clock anchor as a Julian Day: the timeline lives in the
        # subject's civil frame, and JD arithmetic is BCE-safe.
        birth_year, birth_month, birth_day, birth_hour = resolve_subject_local_moment(subject)
        birth_jd = civil_jd(birth_year, birth_month, birth_day, birth_hour)

        if target_date is not None:
            # BCE-safe: datetime.fromisoformat rejects the astronomical year
            # numbering this factory itself emits for BCE boundaries.
            target_year, target_month, target_day, target_hour = parse_astronomical_iso_moment(
                target_date
            )
        else:
            now = resolve_subject_local_now(subject)
            target_year, target_month, target_day = now.year, now.month, now.day
            target_hour = (
                now.hour + now.minute / 60.0 + now.second / 3600.0 + now.microsecond / 3_600_000_000.0
            )
        target_jd = civil_jd(target_year, target_month, target_day, target_hour)

        sequence = DIURNAL_SEQUENCE if is_diurnal else NOCTURNAL_SEQUENCE
        # The ring excludes the nodes by construction, so its members are the
        # seven classical planets — assert that to the type system.
        sub_ring_planets = [cast(ClassicalPlanet, lord) for lord, _years in sequence if lord not in NODES]

        life_cap_years = max(1, life_cap_years)

        periods: List[FirdariaPeriodModel] = []
        bounds: List[Tuple[FirdariaPeriodModel, float, float, List[Tuple[FirdariaSubPeriodModel, float, float]]]] = []
        cursor_jd = birth_jd
        age_cursor = 0

        while age_cursor < life_cap_years:
            for lord, years in sequence:
                period_start_jd = cursor_jd
                period_end_jd = period_start_jd + years * JULIAN_YEAR_DAYS

                sub_periods: List[FirdariaSubPeriodModel] = []
                sub_bounds: List[Tuple[FirdariaSubPeriodModel, float, float]] = []
                if lord not in NODES:
                    start_idx = sub_ring_planets.index(cast(ClassicalPlanet, lord))
                    ring = sub_ring_planets[start_idx:] + sub_ring_planets[:start_idx]
                    sub_days = years * JULIAN_YEAR_DAYS / len(ring)
                    sub_cursor_jd = period_start_jd
                    for sub_lord in ring:
                        sub_end_jd = sub_cursor_jd + sub_days
                        sub_period = FirdariaSubPeriodModel(
                            lord=sub_lord,
                            start=jd_to_iso_datetime(sub_cursor_jd),
                            end=jd_to_iso_datetime(sub_end_jd),
                        )
                        sub_periods.append(sub_period)
                        sub_bounds.append((sub_period, sub_cursor_jd, sub_end_jd))
                        sub_cursor_jd = sub_end_jd

                period = FirdariaPeriodModel(
                    lord=lord,
                    years=years,
                    age_start=age_cursor,
                    age_end=age_cursor + years,
                    start=jd_to_iso_datetime(period_start_jd),
                    end=jd_to_iso_datetime(period_end_jd),
                    sub_periods=sub_periods,
                )
                periods.append(period)
                bounds.append((period, period_start_jd, period_end_jd, sub_bounds))

                cursor_jd = period_end_jd
                age_cursor += years
                if age_cursor >= life_cap_years:
                    break

        current: Optional[FirdariaPeriodModel] = None
        current_sub: Optional[FirdariaSubPeriodModel] = None
        target_s = _jd_second_grid(target_jd)
        for period, start_jd, end_jd, sub_bounds in bounds:
            if _jd_second_grid(start_jd) <= target_s < _jd_second_grid(end_jd):
                current = period
                for sub_period, sub_start_jd, sub_end_jd in sub_bounds:
                    if _jd_second_grid(sub_start_jd) <= target_s < _jd_second_grid(sub_end_jd):
                        current_sub = sub_period
                        break
                break

        return FirdariaModel(
            is_diurnal=is_diurnal,
            periods=periods,
            current=current,
            current_sub=current_sub,
        )
