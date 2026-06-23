# -*- coding: utf-8 -*-
"""Essential dignities module for traditional astrological evaluation."""

from .dignity_factory import calculate_essential_dignity
from .triplicity_lords import get_triplicity_lords

__all__ = ["calculate_essential_dignity", "get_triplicity_lords"]
