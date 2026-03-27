# -*- coding: utf-8 -*-
"""
Occultations sub-package.

Provides the :class:`OccultationFactory` for searching lunar occultation
events via the Swiss Ephemeris.
"""

from .occultation_factory import OccultationFactory, OccultationModel

__all__ = ["OccultationFactory", "OccultationModel"]
