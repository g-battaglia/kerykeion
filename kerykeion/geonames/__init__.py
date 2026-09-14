# -*- coding: utf-8 -*-
"""
Geonames

Online lookup of city coordinates and timezone against the GeoNames web
service, with an on-disk HTTP cache.

The main entry point is:
    - FetchGeonames

Note: only the public surface is re-exported here. Third-party names the
implementation imports (``CachedSession``, ``Request``, ...) are deliberately
left out — re-exporting them would let a ``mock.patch`` target the package
attribute while the code keeps reading the one bound in ``fetcher``, and the
patch would silently do nothing. Patch ``kerykeion.geonames.fetcher.<name>``.
"""

from .fetcher import (
    DEFAULT_GEONAMES_CACHE_NAME,
    GEONAMES_CACHE_ENV_VAR,
    TRANSIENT_GEONAMES_ERROR_CODES,
    FetchGeonames,
)

__all__ = [
    "FetchGeonames",
    "DEFAULT_GEONAMES_CACHE_NAME",
    "GEONAMES_CACHE_ENV_VAR",
    "TRANSIENT_GEONAMES_ERROR_CODES",
]
