# -*- coding: utf-8 -*-
"""
Ephemeris Backend Abstraction
=============================

This module provides a unified interface to the ephemeris calculation engine,
supporting two mutually exclusive backends:

- **swisseph** (``pyswisseph``): The traditional Swiss Ephemeris C library bindings.
  Requires compilation; fastest option for supported platforms.
- **libephemeris**: Pure-Python drop-in replacement using NASA JPL DE440/DE441
  via Skyfield. No C compiler needed; works everywhere Python runs.

Installation
------------
A plain ``pip install kerykeion`` includes ``pyswisseph`` by default.
To use the pure-Python backend instead::

    pip install kerykeion[lib]      # libephemeris backend (pure Python)

Backend selection
-----------------
Set the ``KERYKEION_BACKEND`` environment variable to force a specific backend::

    KERYKEION_BACKEND=libephemeris python my_script.py
    KERYKEION_BACKEND=swisseph python my_script.py

When unset, auto-detection tries ``swisseph`` first (backward compatible),
then ``libephemeris``.

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
    print(BACKEND_NAME)  # "swisseph" or "libephemeris"

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
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

_VALID_BACKENDS = ("swisseph", "libephemeris")

_backend_module: Optional[types.ModuleType] = None
BACKEND_NAME: str = ""

# Check for explicit override via environment variable
_forced_backend = os.environ.get("KERYKEION_BACKEND", "").strip().lower()

if _forced_backend:
    if _forced_backend not in _VALID_BACKENDS:
        raise ValueError(
            f"KERYKEION_BACKEND={_forced_backend!r} is not valid. Choose one of: {', '.join(_VALID_BACKENDS)}"
        )
    try:
        _backend_module = importlib.import_module(_forced_backend)
        BACKEND_NAME = _forced_backend
    except ImportError:
        raise ImportError(
            f"KERYKEION_BACKEND={_forced_backend!r} but the package is not installed.\n\n"
            f"Install it with:\n"
            f"  pip install {'pyswisseph' if _forced_backend == 'swisseph' else 'kerykeion[lib]'}\n"
        ) from None
    logger.info("Kerykeion ephemeris backend forced via KERYKEION_BACKEND: %s", BACKEND_NAME)
else:
    # Auto-detect: try swisseph first (backward compatible default)
    try:
        _backend_module = importlib.import_module("swisseph")
        BACKEND_NAME = "swisseph"
    except ImportError:
        pass

    # Fall back to libephemeris
    if _backend_module is None:
        try:
            _backend_module = importlib.import_module("libephemeris")
            BACKEND_NAME = "libephemeris"
        except ImportError:
            pass

    if _backend_module is None:
        raise ImportError(
            "Kerykeion requires an ephemeris backend but neither 'pyswisseph' nor "
            "'libephemeris' is installed.\n\n"
            "Install one of:\n"
            "  pip install pyswisseph       # Swiss Ephemeris C bindings (included by default)\n"
            "  pip install kerykeion[lib]   # libephemeris (pure Python)\n"
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

__all__ = ["swe", "BACKEND_NAME"]
