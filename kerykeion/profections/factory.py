# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from kerykeion.dignities.rulers import get_domicile_ruler
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_models import (
    AstrologicalSubjectModel,
    KerykeionPointModel,
    ProfectionsModel,
    ProfectionYearModel,
)
from kerykeion.utilities import resolve_subject_birth_datetime, resolve_subject_local_now

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


def _anniversary(year: int, birth: datetime) -> date:
    """The birthday anniversary in ``year``, in the civil calendar.

    A February 29 birthday rolls to March 1 in common years — the same
    convention civil calendars (and the previous client implementation) use.
    Any other ValueError (a year outside the ``date`` range) is a real error
    and surfaces as such.
    """
    try:
        return date(year, birth.month, birth.day)
    except ValueError as exc:
        if birth.month == 2 and birth.day == 29 and 1 <= year <= 9999:
            return date(year, 3, 1)
        raise KerykeionException(
            f"Cannot build the profection anniversary for year {year}: {exc}"
        ) from exc


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
            subject: The natal chart. Requires the twelve house cusps.
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

        birth = resolve_subject_birth_datetime(subject)

        if target_date is not None:
            try:
                target = date.fromisoformat(target_date)
            except ValueError as exc:
                raise KerykeionException(
                    f"Invalid target_date {target_date!r} (expected ISO YYYY-MM-DD)."
                ) from exc
        else:
            target = resolve_subject_local_now(subject).date()

        age = target.year - birth.year
        if target < _anniversary(target.year, birth):
            age -= 1
        if age < 0:
            raise KerykeionException(
                f"target_date {target.isoformat()} precedes the birth date "
                f"{birth.date().isoformat()} — no profection year exists yet."
            )

        years_before = max(0, years_before)
        years_after = max(0, years_after)

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
                year_start=_anniversary(birth.year + entry_age, birth).isoformat(),
                year_end=_anniversary(birth.year + entry_age + 1, birth).isoformat(),
            )
            years.append(entry)
            if entry_age == age:
                current = entry

        assert current is not None  # age is always inside the window built above
        return ProfectionsModel(current=current, years=years)
