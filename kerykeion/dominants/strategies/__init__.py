# -*- coding: utf-8 -*-
"""
Built-in dominant-calculation strategies (the "schools").

Each module here implements one citable school behind the shared
:class:`~kerykeion.dominants.base.DominantStrategy` contract:

- :class:`~kerykeion.dominants.strategies.elemental.ElementalBalanceStrategy`
- :class:`~kerykeion.dominants.strategies.almuten_figuris.AlmutenFigurisStrategy`
- :class:`~kerykeion.dominants.strategies.modern.ModernDominantStrategy`

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from kerykeion.dominants.strategies.almuten_figuris import AlmutenFigurisStrategy
from kerykeion.dominants.strategies.elemental import ElementalBalanceStrategy
from kerykeion.dominants.strategies.modern import ModernDominantStrategy

__all__ = [
    "ElementalBalanceStrategy",
    "AlmutenFigurisStrategy",
    "ModernDominantStrategy",
]
