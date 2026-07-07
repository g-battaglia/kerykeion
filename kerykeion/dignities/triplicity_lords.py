# -*- coding: utf-8 -*-
"""Classical (Dorothean) triplicity lords.

Exposes the three triplicity rulers of an element, ordered by sect. This is the
rulership set used for the traditional triplicity-lords technique (e.g. dividing
a topic into thirds of time). It is deliberately kept separate from the
essential-dignity *score*, which credits only the in-sect lord with +3 — see
``kerykeion.dignities.dignity_data.TRIPLICITY_RULERS`` and ``_compute_dignity``.
"""

from __future__ import annotations

from typing import Literal

from kerykeion.schemas import KerykeionException
from kerykeion.schemas.kr_literals import Element
from kerykeion.schemas.kr_models import TriplicityLordsModel

from .dignity_data import TRIPLICITY_RULERS


def get_triplicity_lords(element: Element, is_diurnal: bool) -> TriplicityLordsModel:
    """Return the three Dorothean triplicity lords of ``element``, ordered by sect.

    Args:
        element: Triplicity element — ``"Fire"``, ``"Earth"``, ``"Air"`` or ``"Water"``.
        is_diurnal: ``True`` for a day chart, ``False`` for a night chart. This
            selects which lord is ``primary`` (in-sect) and which is ``secondary``
            (out-of-sect); the participating lord is the same for both sects.

    Returns:
        A :class:`~kerykeion.schemas.kr_models.TriplicityLordsModel` with
        ``primary`` (in-sect lord), ``secondary`` (out-of-sect lord) and
        ``participating`` (active in both sects).

    Raises:
        KerykeionException: If ``element`` is not one of the four classical elements.
    """
    try:
        rulers = TRIPLICITY_RULERS[element]
    except KeyError as exc:
        raise KerykeionException(
            f"Invalid triplicity element: {element!r}. Expected one of {sorted(TRIPLICITY_RULERS)}."
        ) from exc
    sect: Literal["day", "night"] = "day" if is_diurnal else "night"
    # Derive the out-of-sect lord from the single source of truth (`sect`) so the
    # two cannot drift if the sect convention ever changes.
    other_sect: Literal["day", "night"] = "night" if sect == "day" else "day"
    return TriplicityLordsModel(
        element=element,
        sect=sect,
        primary=rulers[sect],
        secondary=rulers[other_sect],
        participating=rulers["participating"],
    )
