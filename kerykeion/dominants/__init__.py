# -*- coding: utf-8 -*-
"""
Dominants calculator
====================

Compute the *dominants* of a natal chart — the dominant planet, sign, element,
modality, house (and, for the modern method, polarity, hemispheres and
quadrants) — under one of several interchangeable astrological "schools", or a
user-defined custom strategy.

Built-in schools (see :data:`~kerykeion.schemas.kr_literals.DominantMethod`):
    - ``"modern"``: modern weighted method (Astrotheme-style).
    - ``"almuten_figuris"``: traditional Almuten Figuris / Lord of the Geniture.
    - ``"elemental"``: simple elemental & modal balance.

Quick start:
    >>> from kerykeion import AstrologicalSubjectFactory, DominantsFactory
    >>> subject = AstrologicalSubjectFactory.from_birth_data(
    ...     "John Lennon", 1940, 10, 9, 18, 30,
    ...     lat=53.4084, lng=-2.9916, tz_str="Europe/London", online=False)
    >>> dominants = DominantsFactory.from_subject(subject, strategy="modern")
    >>> dominants.dominant_planet  # doctest: +SKIP
    'Pluto'

Extensibility — plug in a custom school via the Strategy pattern:
    >>> from kerykeion import BaseDominantStrategy, DominantsFactory
    >>> class MySchool(BaseDominantStrategy):
    ...     name = "my_school"
    ...     def compute(self, subject, config):
    ...         ...  # build and return a DominantsModel (helpers in the base class)
    >>> DominantsFactory.from_subject(subject, strategy=MySchool())  # doctest: +SKIP

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from kerykeion.dominants.base import (
    BaseDominantStrategy,
    BreakdownItem,
    Category,
    DominantsConfig,
    DominantStrategy,
)
from kerykeion.dominants.factory import DominantsFactory
from kerykeion.dominants.strategies import (
    AlmutenFigurisStrategy,
    ElementalBalanceStrategy,
    ModernDominantStrategy,
)

__all__ = [
    # Public entry point
    "DominantsFactory",
    # Strategy contract + optional base (custom-school extension point)
    "DominantStrategy",
    "BaseDominantStrategy",
    "DominantsConfig",
    # Built-in schools
    "ModernDominantStrategy",
    "AlmutenFigurisStrategy",
    "ElementalBalanceStrategy",
    # Internal value objects (useful when writing a custom strategy)
    "Category",
    "BreakdownItem",
]
