# -*- coding: utf-8 -*-
"""
Report

Plain-text reports for astrological subjects and charts: point tables,
house tables, aspect grids and the narrative sections that accompany them.

The main entry point is:
    - ReportGenerator
"""

from .generator import (
    ASPECT_SYMBOLS,
    HORARY_CONSIDERATION_LABELS,
    MOVEMENT_SYMBOLS,
    LiteralReportKind,
    ReportGenerator,
    SubjectLike,
)

__all__ = [
    "ReportGenerator",
    # The three symbol tables are peers and were all importable from
    # `kerykeion.report` before it became a package; exporting two of them
    # would be an oversight, not a decision. Same for the two type aliases.
    "ASPECT_SYMBOLS",
    "MOVEMENT_SYMBOLS",
    "HORARY_CONSIDERATION_LABELS",
    "SubjectLike",
    "LiteralReportKind",
]
