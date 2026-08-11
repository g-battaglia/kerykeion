# -*- coding: utf-8 -*-
"""Public lookups for classical sign rulerships.

Single source of truth for "who rules this sign" questions, built on the
reference tables in :mod:`kerykeion.dignities.data`. Techniques that
display a period or house lord (zodiacal releasing, annual profections,
firdaria, horary significators) resolve it here instead of keeping a private
copy of the table.
"""

from typing import Optional, cast

from kerykeion.schemas.literals import ClassicalPlanet, Sign

from .data import DOMICILE_RULERS, EXALTATION_TABLE

__all__ = ["get_domicile_ruler", "get_exaltation_ruler"]


def get_domicile_ruler(sign: Sign) -> ClassicalPlanet:
    """Traditional (domicile) ruler of ``sign``.

    The dignity table lists the traditional ruler first; modern co-rulers are
    not part of the classical scheme and are never returned here.

    Example:
        >>> from kerykeion.dignities import get_domicile_ruler
        >>> get_domicile_ruler("Sco")
        'Mars'
    """
    return cast(ClassicalPlanet, DOMICILE_RULERS[sign][0])


def get_exaltation_ruler(sign: Sign) -> Optional[ClassicalPlanet]:
    """Planet exalted in ``sign``, or ``None`` for signs with no classical exaltation.

    Example:
        >>> from kerykeion.dignities import get_exaltation_ruler
        >>> get_exaltation_ruler("Lib")
        'Saturn'
        >>> get_exaltation_ruler("Leo") is None
        True
    """
    return cast(Optional[ClassicalPlanet], EXALTATION_TABLE[sign][0])
