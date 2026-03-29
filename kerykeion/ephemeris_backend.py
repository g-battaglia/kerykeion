# -*- coding: utf-8 -*-
"""
Ephemeris Backend Abstraction
=============================

This module provides a unified interface to the ephemeris calculation engine,
supporting two mutually exclusive backends:

- **libephemeris**: Pure-Python drop-in replacement using NASA JPL DE440/DE441
  via Skyfield. No C compiler needed; works everywhere Python runs.
  Licensed under AGPL-3.0 by the Kerykeion project — safe for dual-licensing.
- **swisseph** (``pyswisseph``): The traditional Swiss Ephemeris C library bindings.
  Requires compilation; fastest option for supported platforms. GPL-licensed.

Installation
------------
A plain ``pip install kerykeion`` includes ``libephemeris`` by default.
To use the C-based backend instead::

    pip install kerykeion[swiss]    # Swiss Ephemeris C bindings (GPL)

Backend selection
-----------------
Set the ``KERYKEION_BACKEND`` environment variable to force a specific backend::

    KERYKEION_BACKEND=swisseph python my_script.py
    KERYKEION_BACKEND=libephemeris python my_script.py

When unset, auto-detection tries ``libephemeris`` first (default),
then ``swisseph``.

libephemeris calculation mode
-----------------------------
When libephemeris is active, the calculation mode defaults to ``"leb"``
(mandatory .leb binary ephemeris files) for maximum performance.
Override via ``KERYKEION_LEB_MODE``::

    KERYKEION_LEB_MODE=auto python my_script.py      # LEB if available, else Skyfield
    KERYKEION_LEB_MODE=skyfield python my_script.py   # Always Skyfield/DE440
    KERYKEION_LEB_MODE=leb python my_script.py        # Require .leb (default)

Usage
-----
All kerykeion internals import from this module instead of importing
``swisseph`` or ``libephemeris`` directly::

    from kerykeion.ephemeris_backend import swe

    swe.calc_ut(jd, planet_id, flags)
    swe.houses_ex2(jd, lat, lon, hsys, flags)

The ``swe`` object exposes the same API regardless of which backend is active.

Detecting the active backend
----------------------------
::

    from kerykeion.ephemeris_backend import BACKEND_NAME
    print(BACKEND_NAME)  # "libephemeris" or "swisseph"

Author: Giacomo Battaglia
Copyright: (C) 2025-2026 Kerykeion Project
License: AGPL-3.0
"""

from __future__ import annotations

import importlib
import logging
import os
import types
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Backend detection
# ---------------------------------------------------------------------------

_VALID_BACKENDS = ("libephemeris", "swisseph")

_backend_module: Optional[types.ModuleType] = None
BACKEND_NAME: str = ""

# Check for explicit override via environment variable
_forced_backend = os.environ.get("KERYKEION_BACKEND", "").strip().lower()

if _forced_backend:
    if _forced_backend not in _VALID_BACKENDS:
        raise ValueError(
            f"KERYKEION_BACKEND={_forced_backend!r} is not valid. "
            f"Choose one of: {', '.join(_VALID_BACKENDS)}"
        )
    try:
        _backend_module = importlib.import_module(_forced_backend)
        BACKEND_NAME = _forced_backend
    except ImportError:
        raise ImportError(
            f"KERYKEION_BACKEND={_forced_backend!r} but the package is not installed.\n\n"
            f"Install it with:\n"
            f"  pip install {'pyswisseph' if _forced_backend == 'swisseph' else 'libephemeris'}\n"
        ) from None
    logger.info("Kerykeion ephemeris backend forced via KERYKEION_BACKEND: %s", BACKEND_NAME)
else:
    # Auto-detect: try libephemeris first (default, AGPL-3.0 safe for dual-licensing),
    # then fall back to swisseph (GPL, requires user to accept GPL terms).
    for _candidate in ("libephemeris", "swisseph"):
        try:
            _backend_module = importlib.import_module(_candidate)
            BACKEND_NAME = _candidate
            break
        except ImportError:
            continue

    if _backend_module is None:
        raise ImportError(
            "Kerykeion requires an ephemeris backend but neither 'libephemeris' nor "
            "'pyswisseph' is installed.\n\n"
            "Install one of:\n"
            "  pip install libephemeris     # Pure Python, AGPL-3.0 (included by default)\n"
            "  pip install pyswisseph       # Swiss Ephemeris C bindings (GPL)\n"
        )

    logger.debug("Kerykeion ephemeris backend (auto-detected): %s", BACKEND_NAME)


# ---------------------------------------------------------------------------
# Public API: the `swe` object
# ---------------------------------------------------------------------------
# All kerykeion modules import this single object:
#
#     from kerykeion.ephemeris_backend import swe
#
# It is the actual backend module (swisseph or libephemeris).
# As of libephemeris >= 1.0.0a1, both backends are fully API-compatible
# and no compatibility shims are required.

swe = _backend_module

# ---------------------------------------------------------------------------
# libephemeris: enforce .leb binary ephemeris mode
# ---------------------------------------------------------------------------
# When libephemeris is active, force the "leb" calculation mode so that
# precomputed Chebyshev polynomials (.leb files) are always used for
# maximum performance and offline operation.
#
# Configurable via KERYKEION_LEB_MODE env var (default: "leb").
# Valid values: "leb" (mandatory .leb), "auto", "skyfield", "horizons".
#
# In "leb" mode, libephemeris raises RuntimeError if no .leb file is
# found — this is intentional: we want a clear failure rather than a
# silent fallback to Skyfield (which would require downloading DE440).

if BACKEND_NAME == "libephemeris":
    _leb_mode = os.environ.get("KERYKEION_LEB_MODE", "leb").strip().lower()
    _backend_module.set_calc_mode(_leb_mode)
    logger.debug("libephemeris calc mode set to: %s", _leb_mode)

__all__ = ["swe", "BACKEND_NAME"]
