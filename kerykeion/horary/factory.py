# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from typing import List, Optional

from kerykeion.dignities.rulers import get_domicile_ruler
from kerykeion.receptions import MutualReceptionsFactory
from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.schemas.models import (
    AstrologicalSubjectModel,
    HoraryConsiderationModel,
    HoraryIndicatorsModel,
    HorarySignificatorModel,
    KerykeionPointModel,
)
from kerykeion.utilities.core import has_terrestrial_frame

# House cusp fields in house order, and the engine house-name → number map.
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
HOUSE_NAME_TO_NUMBER: dict[str, int] = {
    "First_House": 1,
    "Second_House": 2,
    "Third_House": 3,
    "Fourth_House": 4,
    "Fifth_House": 5,
    "Sixth_House": 6,
    "Seventh_House": 7,
    "Eighth_House": 8,
    "Ninth_House": 9,
    "Tenth_House": 10,
    "Eleventh_House": 11,
    "Twelfth_House": 12,
}

# The classical degree thresholds on the Ascendant: too early to judge below
# 3°, already decided (or too late) at 27° and beyond.
EARLY_ASC_DEGREE = 3.0
LATE_ASC_DEGREE = 27.0


def _house_number(point: Optional[KerykeionPointModel]) -> Optional[int]:
    if point is None or point.house is None:
        return None
    return HOUSE_NAME_TO_NUMBER.get(str(point.house))


def _significator(subject: AstrologicalSubjectModel, house: int) -> HorarySignificatorModel:
    """Build the significator of ``house`` via classical rulership."""
    cusp: Optional[KerykeionPointModel] = getattr(subject, HOUSE_CUSP_FIELDS[house - 1], None)
    if cusp is None:
        return HorarySignificatorModel(house=house)

    ruler = get_domicile_ruler(cusp.sign)
    ruler_point: Optional[KerykeionPointModel] = getattr(subject, ruler.lower(), None)
    return HorarySignificatorModel(
        house=house,
        sign=cusp.sign,
        ruler=ruler,
        ruler_sign=ruler_point.sign if ruler_point is not None else None,
        ruler_house=ruler_point.house if ruler_point is not None else None,
        ruler_house_number=_house_number(ruler_point),
        ruler_retrograde=ruler_point.retrograde if ruler_point is not None else None,
        essential_dignity=getattr(ruler_point, "essential_dignity", None),
    )


class HoraryIndicatorsFactory:
    """Assemble horary significators, considerations, and receptions.

    Example:
        >>> from kerykeion import AstrologicalSubjectFactory, HoraryIndicatorsFactory
        >>> subject = AstrologicalSubjectFactory.from_birth_data(
        ...     "Question", 2026, 6, 4, 15, 30, lat=41.9, lng=12.5, tz_str="Europe/Rome")
        >>> indicators = HoraryIndicatorsFactory.from_subject(subject)
        >>> indicators.querent.house, indicators.quesited.house
        (1, 7)
    """

    @classmethod
    def from_subject(
        cls,
        subject: AstrologicalSubjectModel,
        *,
        is_moon_void: Optional[bool] = None,
    ) -> HoraryIndicatorsModel:
        """Build the indicators for a question chart.

        Args:
            subject: The chart cast for the moment of the question.
            is_moon_void: Whether the Moon is void of course, when the caller
                knows it (it comes from the void-of-course search, a separate
                calculation). ``None`` simply omits the two Moon
                considerations rather than guessing.

        Returns:
            A :class:`HoraryIndicatorsModel`.

        Raises:
            KerykeionException: When the chart's perspective is not
                terrestrial (heliocentric, barycentric, selenocentric or
                planetocentric): significators, house considerations and
                receptions read house cusps, angles and sign rulership as
                seen from Earth, and a chart measured from another origin
                would produce plausible but frame-inconsistent indicators
                (a heliocentric chart even lacks the Sun). Refused, never
                mixed.
        """
        if not has_terrestrial_frame(subject):
            raise KerykeionException(
                "Horary indicators are a terrestrial technique: house cusps, "
                "angles and rulership placements are read as seen from Earth, "
                f"but this chart's perspective "
                f"({getattr(subject, 'perspective_type', None)!r}) measures its "
                "longitudes from another origin. Cast the question chart "
                "geocentrically (or topocentrically)."
            )

        # Read the Ascendant degree from the true Ascendant point, NOT the
        # first-house cusp: under Whole Sign the cusp sits at 0° of the rising
        # sign, which would flag every Whole Sign chart as "too early". Fall
        # back to the cusp only when the point is absent (elsewhere they
        # coincide).
        ascendant: Optional[KerykeionPointModel] = getattr(subject, "ascendant", None) or getattr(
            subject, "first_house", None
        )
        ascendant_degree = ascendant.position if ascendant is not None else None

        considerations: List[HoraryConsiderationModel] = []
        if ascendant_degree is not None:
            if ascendant_degree < EARLY_ASC_DEGREE:
                considerations.append(
                    HoraryConsiderationModel(key="asc_early_degree", status="caution")
                )
            elif ascendant_degree >= LATE_ASC_DEGREE:
                considerations.append(
                    HoraryConsiderationModel(key="asc_late_degree", status="caution")
                )
            else:
                considerations.append(
                    HoraryConsiderationModel(key="asc_judgeable", status="favorable")
                )

        if is_moon_void is True:
            considerations.append(HoraryConsiderationModel(key="moon_void", status="caution"))
        elif is_moon_void is False:
            considerations.append(HoraryConsiderationModel(key="moon_not_void", status="favorable"))

        saturn_house = _house_number(getattr(subject, "saturn", None))
        if saturn_house == 1:
            considerations.append(HoraryConsiderationModel(key="saturn_in_first", status="caution"))
        elif saturn_house == 7:
            considerations.append(
                HoraryConsiderationModel(key="saturn_in_seventh", status="caution")
            )

        return HoraryIndicatorsModel(
            querent=_significator(subject, 1),
            quesited=_significator(subject, 7),
            ascendant_degree=ascendant_degree,
            considerations=considerations,
            mutual_receptions=MutualReceptionsFactory.from_subject(subject).receptions,
        )
