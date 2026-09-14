# -*- coding: utf-8 -*-
"""
Zodiacal Releasing (aphesis)
============================

Compute the Hellenistic time-lord technique of zodiacal releasing from a lot
(Fortune or Spirit). Life unfolds as a sequence of planetary periods beginning
at the lot's sign, each sign ruling for its general years and subdividing into
months, days and finer levels, with the "loosing of the bond" applied as the
sequence circles back to its starting sign.

Quick start:
    >>> from kerykeion import AstrologicalSubjectFactory, ZodiacalReleasingFactory
    >>> subject = AstrologicalSubjectFactory.from_birth_data(
    ...     "Jane", 1990, 6, 15, 12, 0,
    ...     lat=41.9, lng=12.5, tz_str="Europe/Rome", online=False)
    >>> zr = ZodiacalReleasingFactory.from_subject(
    ...     subject, lot="fortune", target_date="2026-06-04")
    >>> zr.lot_sign, len(zr.periods) > 0
    (..., True)
"""

from .factory import ZodiacalReleasingFactory

__all__ = ["ZodiacalReleasingFactory"]
