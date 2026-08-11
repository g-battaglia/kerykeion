# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterator, List, Literal, Optional

from kerykeion.dignities.rulers import get_domicile_ruler
from kerykeion.dominants.utils import part_of_fortune_degree
from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.utilities.core import resolve_sect_is_diurnal, resolve_subject_birth_datetime
from kerykeion.schemas.literals import SIGN_CODES, Sign
from kerykeion.schemas.models import (
    AstrologicalSubjectModel,
    ZodiacalReleasingModel,
    ZRPeriodModel,
)

# General years per sign (Vettius Valens). These drive every level: L1 counts
# them as years, L2 as months (years / 12), L3 a further twelfth, and so on.
GENERAL_YEARS: dict[Sign, int] = {
    "Ari": 15,
    "Tau": 8,
    "Gem": 20,
    "Can": 25,
    "Leo": 19,
    "Vir": 20,
    "Lib": 8,
    "Sco": 15,
    "Sag": 12,
    "Cap": 27,
    "Aqu": 30,
    "Pis": 12,
}

# Traditional (domicile) ruler of each sign, for display alongside each period.
# Resolved from the shared dignity tables (single source of truth); kept as a
# mapping for backward compatibility with existing imports of this name.
TRADITIONAL_RULERS: dict[Sign, str] = {sign: get_domicile_ruler(sign) for sign in SIGN_CODES}

# Length of a year in days. The tropical year matches the Hellenistic convention
# used by modern zodiacal-releasing implementations.
TROPICAL_YEAR_DAYS = 365.2422

# Default cap on how far the L1 timeline is built, in years of life.
DEFAULT_LIFE_CAP_YEARS = 100

LotName = Literal["fortune", "spirit"]


def _lot_degree(subject: AstrologicalSubjectModel, lot: LotName) -> Optional[float]:
    """Return the absolute longitude of the chosen lot.

    The Part of Fortune reuses kerykeion's sect-sensitive helper. The Part of
    Spirit is its mirror: ``Asc + Sun - Moon`` by day, ``Asc + Moon - Sun`` by
    night.
    """
    if lot == "fortune":
        return part_of_fortune_degree(subject)

    ascendant, sun, moon = subject.ascendant, subject.sun, subject.moon
    if ascendant is None or sun is None or moon is None:
        return None
    if resolve_sect_is_diurnal(subject):
        degree = ascendant.abs_pos + sun.abs_pos - moon.abs_pos
    else:
        degree = ascendant.abs_pos + moon.abs_pos - sun.abs_pos
    return degree % 360.0


def _lob_sequence(start: int) -> Iterator[tuple[int, bool]]:
    """Yield ``(sign_num, is_loosing_the_bond)`` indefinitely from ``start``.

    Sub-periods proceed in zodiacal order. When the sequence would return to the
    sign that began the current revolution, it instead "looses the bond" and
    jumps to the opposite sign, flagged ``True``.
    """
    revolution_start = start
    current = start
    yield current, False
    while True:
        nxt = (current + 1) % 12
        is_lob = False
        if nxt == revolution_start:
            nxt = (revolution_start + 6) % 12
            revolution_start = nxt
            is_lob = True
        current = nxt
        yield current, is_lob


def _build_level(
    start_sign: int,
    start_dt: datetime,
    duration_days: float,
    level: int,
    levels: int,
    target_dt: Optional[datetime],
    fortune_sign: int,
) -> "tuple[List[ZRPeriodModel], List[ZRPeriodModel]]":
    """Build the periods filling one parent span at ``level``.

    ``duration_days`` bounds the span to fill — for L1 it is the life cap, so the
    L1 horizon is honoured up front rather than overshot by a full sign period.
    The last period is truncated to fit. Children are expanded for every L2
    period, but for L3+ only along the period that contains ``target_dt`` —
    keeping the tree bounded.

    ``fortune_sign`` is the sign index of the natal Lot of Fortune: peak
    (angular) periods are always counted 1st/4th/7th/10th from Fortune,
    whichever lot is being released (Valens; Brennan, "Hellenistic Astrology").

    Returns ``(periods, current_path)``. The current path is computed here from
    the exact cursor datetimes (not the day-truncated display strings), so a
    target falling on a boundary date for a non-midnight birth still resolves to
    the period the deeper levels were actually built under.
    """
    periods: List[ZRPeriodModel] = []
    current_path: List[ZRPeriodModel] = []
    unit_days = TROPICAL_YEAR_DAYS / (12 ** (level - 1))
    cursor = start_dt
    produced = 0.0

    for sign_num, is_lob in _lob_sequence(start_sign):
        sign = SIGN_CODES[sign_num]
        full = GENERAL_YEARS[sign] * unit_days
        dur = min(full, duration_days - produced)
        if dur <= 1e-9:
            break

        end = cursor + timedelta(days=dur)
        contains_target = target_dt is not None and cursor <= target_dt < end

        children: List[ZRPeriodModel] = []
        child_path: List[ZRPeriodModel] = []
        if level < levels and (level < 2 or contains_target):
            children, child_path = _build_level(
                sign_num, cursor, dur, level + 1, levels, target_dt, fortune_sign
            )

        period = ZRPeriodModel(
            sign=sign,
            ruler=TRADITIONAL_RULERS[sign],
            level=level,
            start=cursor.date().isoformat(),
            end=end.date().isoformat(),
            years=GENERAL_YEARS[sign] / (12 ** (level - 1)),
            is_angular=((sign_num - fortune_sign) % 12) in (0, 3, 6, 9),
            is_loosing_the_bond=is_lob,
            subperiods=children,
        )
        periods.append(period)
        if contains_target:
            current_path = [period, *child_path]

        cursor = end
        produced += dur
        if produced >= duration_days - 1e-6:
            break

    return periods, current_path


class ZodiacalReleasingFactory:
    """Compute zodiacal releasing (aphesis) from a lot.

    Periods unfold from the lot's sign in zodiacal order, each sign ruling for
    its general years, subdividing into months, days, and finer levels, with the
    "loosing of the bond" jump applied as the sequence circles back.

    Example:
        >>> from kerykeion import AstrologicalSubjectFactory, ZodiacalReleasingFactory
        >>> subject = AstrologicalSubjectFactory.from_birth_data(
        ...     "Jane", 1990, 6, 15, 12, 0, lat=41.9, lng=12.5, tz_str="Europe/Rome")
        >>> zr = ZodiacalReleasingFactory.from_subject(subject, lot="fortune", target_date="2026-06-04")
        >>> zr.lot_sign, len(zr.periods) > 0
        (..., True)
    """

    @classmethod
    def from_subject(
        cls,
        subject: AstrologicalSubjectModel,
        *,
        lot: LotName = "fortune",
        levels: int = 2,
        target_date: Optional[str] = None,
        life_cap_years: int = DEFAULT_LIFE_CAP_YEARS,
    ) -> ZodiacalReleasingModel:
        """Build the zodiacal-releasing periods for a subject.

        Args:
            subject: The natal chart. Requires a known birth time (Ascendant).
            lot: ``"fortune"`` or ``"spirit"``.
            levels: How many subdivision levels to compute (1-4). L1 and L2 are
                built in full; deeper levels only along the target-date path.
            target_date: ISO date (``YYYY-MM-DD``) used to mark the current
                period chain. When omitted, no current path is reported and only
                full levels (≤ 2) are built.
            life_cap_years: How far the L1 timeline extends, in years of life.

        Returns:
            A :class:`ZodiacalReleasingModel`.

        Raises:
            KerykeionException: For an unknown ``lot``, an unresolvable lot
                (missing birth time), or an unparseable ``target_date``.
        """
        if lot not in ("fortune", "spirit"):
            raise KerykeionException(f"Unknown lot: {lot!r} (expected 'fortune' or 'spirit').")

        levels = max(1, min(4, levels))

        degree = _lot_degree(subject, lot)
        if degree is None:
            raise KerykeionException(
                "Cannot compute the lot: the Ascendant, Sun or Moon is unavailable "
                "(zodiacal releasing requires a known birth time)."
            )
        lot_sign_num = int(degree % 360.0 // 30)

        # Peak (angular) periods are counted from the natal Lot of FORTUNE
        # regardless of which lot is being released (Valens; Brennan,
        # "Hellenistic Astrology"). part_of_fortune_degree prefers the
        # subject's own pars_fortunae and otherwise applies the sect-aware
        # formula (day: Asc + Moon - Sun; night: Asc + Sun - Moon).
        fortune_degree = degree if lot == "fortune" else part_of_fortune_degree(subject)
        if fortune_degree is None:
            raise KerykeionException(
                "Cannot compute the Lot of Fortune (the angularity reference for "
                "peak periods): the Ascendant, Sun or Moon is unavailable."
            )
        fortune_sign_num = int(fortune_degree % 360.0 // 30)

        # Split-component subjects and ISO-only subjects (returns, Davison)
        # both resolve through the shared helper; midpoint composites are
        # rejected there — they have no single moment in time.
        birth_dt = resolve_subject_birth_datetime(subject)

        target_dt: Optional[datetime] = None
        if target_date is not None:
            try:
                target_dt = datetime.fromisoformat(target_date)
            except ValueError as exc:
                raise KerykeionException(
                    f"Invalid target_date {target_date!r} (expected ISO YYYY-MM-DD)."
                ) from exc
            # Birth datetimes are naive; a timezone-aware target would raise a raw
            # TypeError in the date math below. Reject it with a clear message.
            if target_dt.tzinfo is not None:
                raise KerykeionException(
                    f"target_date {target_date!r} must be timezone-naive "
                    "(pass a bare ISO date, e.g. '2026-06-04')."
                )

        # Extend the L1 timeline far enough to cover the target date plus a margin.
        life_cap_days = life_cap_years * TROPICAL_YEAR_DAYS
        if target_dt is not None:
            span = (target_dt - birth_dt).days + 10 * TROPICAL_YEAR_DAYS
            life_cap_days = max(life_cap_days, span)

        # L1 fills exactly the life cap (the last period is truncated to it), so
        # the documented horizon is honoured instead of overshot. The current
        # path is returned alongside, computed from exact datetimes.
        periods, current_path = _build_level(
            lot_sign_num, birth_dt, life_cap_days, 1, levels, target_dt, fortune_sign_num
        )

        return ZodiacalReleasingModel(
            lot=lot,
            lot_sign=SIGN_CODES[lot_sign_num],
            lot_degree=degree % 360.0,
            periods=periods,
            current_path=current_path,
        )
