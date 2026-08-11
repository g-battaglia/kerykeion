# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from datetime import date
from typing import List, Optional, Tuple

from kerykeion.dignities.rulers import get_domicile_ruler
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_models import (
    AstrologicalSubjectModel,
    KerykeionPointModel,
    ProfectionsModel,
    ProfectionYearModel,
)
from kerykeion.utilities import (
    format_astronomical_iso_date,
    resolve_subject_local_moment,
    resolve_subject_local_now,
)

# House cusp fields on the subject, in house order (1st..12th).
HOUSE_CUSP_FIELDS: tuple[str, ...] = (
    "first_house",
    "second_house",
    "third_house",
    "fourth_house",
    "fifth_house",
    "sixth_house",
    "seventh_house",
    "eighth_house",
    "ninth_house",
    "tenth_house",
    "eleventh_house",
    "twelfth_house",
)


def _is_gregorian_leap(year: int) -> bool:
    """Proleptic-Gregorian leap rule, valid for any astronomical year."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _anniversary(year: int, birth_month: int, birth_day: int) -> Tuple[int, int]:
    """The birthday anniversary ``(month, day)`` in ``year``.

    A February 29 birthday rolls to March 1 in common years — the civil
    convention. Pure integer arithmetic, so BCE years work (Python's ``date``
    stops at year 1; astronomical numbering does not).
    """
    if birth_month == 2 and birth_day == 29 and not _is_gregorian_leap(year):
        return (3, 1)
    return (birth_month, birth_day)


class ProfectionsFactory:
    """Compute annual profections from a subject's houses.

    The profected house for a completed age is ``(age % 12) + 1``; the sign is
    the one on that house's cusp in the subject's own house system (whole-sign
    charts profect through whole signs by construction), and the Lord of the
    Year is the sign's traditional ruler.

    Example:
        >>> from kerykeion import AstrologicalSubjectFactory, ProfectionsFactory
        >>> subject = AstrologicalSubjectFactory.from_birth_data(
        ...     "Jane", 1990, 6, 15, 12, 0, lat=41.9, lng=12.5, tz_str="Europe/Rome")
        >>> profections = ProfectionsFactory.from_subject(subject, target_date="2026-06-04")
        >>> profections.current.age
        35
    """

    @classmethod
    def from_subject(
        cls,
        subject: AstrologicalSubjectModel,
        *,
        target_date: Optional[str] = None,
        years_before: int = 3,
        years_after: int = 4,
    ) -> ProfectionsModel:
        """Build the profection years around a target date.

        Args:
            subject: The natal chart. Requires the twelve house cusps. BCE
                birth years (astronomical numbering) are supported.
            target_date: ISO date (``YYYY-MM-DD``) the "current" year is
                resolved against. When omitted, today in the subject's own
                timezone is used.
            years_before: Past years to include in the table.
            years_after: Future years to include in the table.

        Returns:
            A :class:`ProfectionsModel` with the current year and the window.

        Raises:
            KerykeionException: When the cusps are missing, the target date is
                unparseable, or it precedes the birth date.
        """
        cusps: List[KerykeionPointModel] = []
        for field in HOUSE_CUSP_FIELDS:
            cusp = getattr(subject, field, None)
            if cusp is None:
                raise KerykeionException(
                    "Annual profections require the twelve house cusps; "
                    f"{field!r} is missing on the subject."
                )
            cusps.append(cusp)

        # Birth components without datetime: BCE-safe, ISO-only-subject-safe.
        birth_year, birth_month, birth_day, _birth_hour = resolve_subject_local_moment(subject)

        if target_date is not None:
            try:
                target = date.fromisoformat(target_date)
            except ValueError as exc:
                raise KerykeionException(
                    f"Invalid target_date {target_date!r} (expected ISO YYYY-MM-DD)."
                ) from exc
        else:
            target = resolve_subject_local_now(subject).date()

        # Age by civil anniversary — pure integer arithmetic on astronomical
        # years, so a BCE birth with a CE target just yields a large age.
        age = target.year - birth_year
        if (target.month, target.day) < _anniversary(target.year, birth_month, birth_day):
            age -= 1
        if age < 0:
            raise KerykeionException(
                f"target_date {target.isoformat()} precedes the birth date "
                f"{format_astronomical_iso_date(birth_year, birth_month, birth_day)} "
                "— no profection year exists yet."
            )

        years_before = max(0, years_before)
        years_after = max(0, years_after)

        def _year_boundary(year: int) -> str:
            month, day = _anniversary(year, birth_month, birth_day)
            return format_astronomical_iso_date(year, month, day)

        current: Optional[ProfectionYearModel] = None
        years: List[ProfectionYearModel] = []
        for entry_age in range(max(0, age - years_before), age + years_after + 1):
            house = (entry_age % 12) + 1
            sign = cusps[house - 1].sign
            entry = ProfectionYearModel(
                age=entry_age,
                house=house,
                sign=sign,
                lord=get_domicile_ruler(sign),
                year_start=_year_boundary(birth_year + entry_age),
                year_end=_year_boundary(birth_year + entry_age + 1),
            )
            years.append(entry)
            if entry_age == age:
                current = entry

        assert current is not None  # age is always inside the window built above
        return ProfectionsModel(current=current, years=years)
