# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from typing import List

from kerykeion.dignities.rulers import get_domicile_ruler, get_exaltation_ruler
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_models import (
    AstrologicalSubjectModel,
    KerykeionPointModel,
    MutualReceptionModel,
    MutualReceptionsModel,
)
from kerykeion.utilities import has_terrestrial_frame

# Subject fields of the seven classical planets — the only participants in
# classical reception (no nodes, no outer planets).
CLASSICAL_PLANET_FIELDS: tuple[str, ...] = (
    "sun",
    "moon",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
)


class MutualReceptionsFactory:
    """Find every mutual reception among a chart's classical planets.

    Example:
        >>> from kerykeion import AstrologicalSubjectFactory, MutualReceptionsFactory
        >>> subject = AstrologicalSubjectFactory.from_birth_data(
        ...     "Jane", 1990, 6, 15, 12, 0, lat=41.9, lng=12.5, tz_str="Europe/Rome")
        >>> receptions = MutualReceptionsFactory.from_subject(subject)
        >>> isinstance(receptions.receptions, list)
        True
    """

    @classmethod
    def from_subject(cls, subject: AstrologicalSubjectModel) -> MutualReceptionsModel:
        """Collect domicile and exaltation mutual receptions.

        Args:
            subject: Any chart carrying the classical planets. Planets absent
                from the subject are simply skipped.

        Returns:
            A :class:`MutualReceptionsModel`, one entry per deduplicated pair
            and reception type.

        Raises:
            KerykeionException: When the chart's perspective is not
                terrestrial: reception is a dignity technique defined on
                sign placements as seen from Earth, and a heliocentric or
                planetocentric chart's signs live in another frame (the
                heliocentric one even lacks the Sun).
        """
        if not has_terrestrial_frame(subject):
            raise KerykeionException(
                "Mutual receptions are a terrestrial dignity technique: sign "
                "placements are read as seen from Earth, but this chart's "
                f"perspective ({getattr(subject, 'perspective_type', None)!r}) "
                "measures its longitudes from another origin. Cast the chart "
                "geocentrically (or topocentrically)."
            )

        planets: List[KerykeionPointModel] = []
        for field in CLASSICAL_PLANET_FIELDS:
            point = getattr(subject, field, None)
            if point is not None:
                planets.append(point)

        receptions: List[MutualReceptionModel] = []
        for i in range(len(planets)):
            for j in range(i + 1, len(planets)):
                first, second = planets[i], planets[j]
                first_name, second_name = str(first.name), str(second.name)

                # Domicile: each planet rules the sign the other occupies.
                if (
                    get_domicile_ruler(first.sign) == second_name
                    and get_domicile_ruler(second.sign) == first_name
                ):
                    receptions.append(
                        MutualReceptionModel(
                            first_planet=first_name,  # type: ignore[arg-type]
                            second_planet=second_name,  # type: ignore[arg-type]
                            reception_type="domicile",
                        )
                    )

                # Exaltation: each planet is exalted in the other's sign.
                if (
                    get_exaltation_ruler(first.sign) == second_name
                    and get_exaltation_ruler(second.sign) == first_name
                ):
                    receptions.append(
                        MutualReceptionModel(
                            first_planet=first_name,  # type: ignore[arg-type]
                            second_planet=second_name,  # type: ignore[arg-type]
                            reception_type="exaltation",
                        )
                    )

        return MutualReceptionsModel(receptions=receptions)
