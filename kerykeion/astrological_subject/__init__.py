# -*- coding: utf-8 -*-
"""
Astrological Subject

The core of the library: builds a subject from birth data, resolving the
moment and place, then computing points, houses, angles and the derived
chart attributes.

The main entry point is:
    - AstrologicalSubjectFactory
"""

from .factory import AstrologicalSubjectFactory

__all__ = ["AstrologicalSubjectFactory"]
