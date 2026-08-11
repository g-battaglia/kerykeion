# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple, cast

from kerykeion.schemas.kr_literals import ClassicalPlanet
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_models import (
    AstrologicalSubjectModel,
    FirdariaModel,
    FirdariaPeriodModel,
    FirdariaSubPeriodModel,
)
from kerykeion.utilities import (
    civil_jd,
    jd_to_iso_date,
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
                against. When omitted, now in the subject's timezone.
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
            try:
                target = datetime.fromisoformat(target_date)
            except ValueError as exc:
                raise KerykeionException(
                    f"Invalid target_date {target_date!r} (expected ISO YYYY-MM-DD)."
                ) from exc
            if target.tzinfo is not None:
                raise KerykeionException(
                    f"target_date {target_date!r} must be timezone-naive "
                    "(pass a bare ISO date, e.g. '2026-06-04')."
                )
        else:
            target = resolve_subject_local_now(subject)
        target_jd = civil_jd(
            target.year, target.month, target.day, target.hour + target.minute / 60.0
        )

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
                            start=jd_to_iso_date(sub_cursor_jd),
                            end=jd_to_iso_date(sub_end_jd),
                        )
                        sub_periods.append(sub_period)
                        sub_bounds.append((sub_period, sub_cursor_jd, sub_end_jd))
                        sub_cursor_jd = sub_end_jd

                period = FirdariaPeriodModel(
                    lord=lord,
                    years=years,
                    age_start=age_cursor,
                    age_end=age_cursor + years,
                    start=jd_to_iso_date(period_start_jd),
                    end=jd_to_iso_date(period_end_jd),
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
        for period, start_jd, end_jd, sub_bounds in bounds:
            if start_jd <= target_jd < end_jd:
                current = period
                for sub_period, sub_start_jd, sub_end_jd in sub_bounds:
                    if sub_start_jd <= target_jd < sub_end_jd:
                        current_sub = sub_period
                        break
                break

        return FirdariaModel(
            is_diurnal=is_diurnal,
            periods=periods,
            current=current,
            current_sub=current_sub,
        )
