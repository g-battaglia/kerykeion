# -*- coding: utf-8 -*-
"""
Fixed Stars module (v6)

Exposes:
- ``FixedStarCatalog``: read-only accessor over the libephemeris star catalog.
- ``FixedStarMetadata``: typed entry model.
- ``FixedStarDiscoveryFactory``: scan-and-find conjunctions to natal points.

The Swiss Ephemeris ``sefstars.txt`` file is NOT used (licensing). All
catalog data comes from libephemeris.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from .catalog import FixedStarCatalog, FixedStarMetadata
from .discovery_factory import FixedStarDiscoveryFactory

__all__ = ["FixedStarCatalog", "FixedStarMetadata", "FixedStarDiscoveryFactory"]
