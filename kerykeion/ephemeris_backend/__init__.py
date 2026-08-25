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
    POLAR_HOUSES_ERROR_TYPES,
    ephe,
    ephemeris_session,
    houses_ex2_with_polar_fallback,
    houses_ex2_with_polar_fallback_ex,
    houses_ring_with_polar_fallback,
    HouseRing,
    reset_ephemeris_session,
)

__all__ = [
    "ephe",
    "BACKEND_NAME",
    "EPHE_DATA_PATH",
    "EPHEMERIS_LOCK",
    "ephemeris_session",
    "reset_ephemeris_session",
    # Below: not in the module's original __all__, but importable from this
    # dotted path before it became a package. The path did not change, so
    # nothing would signal the break -- and dropping them would narrow the
    # surface silently, which is the failure this whole refactor set out to
    # avoid. The polar helpers matter especially: they are the only public way
    # to compute houses above the polar circle, and the docstrings of
    # validate_latitude / check_and_adjust_polar_latitude send callers here.
    "DEFAULT_SWEPH_DOWNLOAD_DIR",
    "houses_ex2_with_polar_fallback",
    "houses_ex2_with_polar_fallback_ex",
    "houses_ring_with_polar_fallback",
    "HouseRing",
    "POLAR_HOUSES_ERROR_TYPES",
]
