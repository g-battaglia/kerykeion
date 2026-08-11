# -*- coding: utf-8 -*-
"""
Ephemeris Backend

Selects and configures the ephemeris engine (libephemeris by default,
swisseph on request) and exposes it as a single shared module object,
plus the locking primitives that serialize access to it.

The package name keeps the "backend" in it on purpose: it sits next to
``ephemeris_data``, and a bare ``ephemeris`` would blur the two.

Re-exporting ``ephe`` is safe: it is a module object bound once at import
time, so a test patching ``kerykeion.ephemeris_backend.backend.ephe.calc_ut``
mutates the very object every caller holds — unlike a re-exported value,
which would leave the patch stranded on the package namespace.

The main entry points are:
    - ephe
    - BACKEND_NAME
"""

from .backend import (
    BACKEND_NAME,
    DEFAULT_SWEPH_DOWNLOAD_DIR,
    EPHE_DATA_PATH,
    EPHEMERIS_LOCK,
    ephe,
    ephemeris_session,
    reset_ephemeris_session,
)

__all__ = [
    "ephe",
    "BACKEND_NAME",
    "EPHE_DATA_PATH",
    "EPHEMERIS_LOCK",
    "ephemeris_session",
    "reset_ephemeris_session",
    # Not part of the module's original __all__, but backend.py re-exports it
    # from config_constants explicitly "for backward compatibility". Leaving it
    # off this facade would break `from kerykeion.ephemeris_backend import
    # DEFAULT_SWEPH_DOWNLOAD_DIR` and quietly undo that stated intent.
    "DEFAULT_SWEPH_DOWNLOAD_DIR",
]
