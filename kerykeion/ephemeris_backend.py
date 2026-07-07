# -*- coding: utf-8 -*-
"""
Ephemeris Backend Abstraction
=============================

This module provides a unified interface to the ephemeris calculation engine,
supporting two mutually exclusive backends:

- **libephemeris**: Pure-Python drop-in replacement using NASA JPL DE440/DE441
  via Skyfield. No C compiler needed; works everywhere Python runs.
  Licensed under AGPL-3.0 by the Kerykeion project.
- **swisseph** (``pyswisseph``): The traditional Swiss Ephemeris C library bindings.
  Requires compilation. Licensed under AGPL-3.0 by Astrodienst AG.

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

    from kerykeion.ephemeris_backend import ephe

    ephe.calc_ut(jd, planet_id, flags)
    ephe.houses_ex2(jd, lat, lon, hsys, flags)

The ``ephe`` object exposes the same API regardless of which backend is active.

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
from contextlib import contextmanager
from threading import RLock, local as _thread_local
import types
from typing import Iterator, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

# Per-thread nesting depth of ``ephemeris_session``. ``EPHEMERIS_LOCK`` is an
# RLock, so the same thread CAN re-enter a session, but the inner session's
# cleanup (``reset_ephemeris_session``) resets the sidereal/topo state the outer
# session configured — silently shifting every subsequent position in the outer
# session. No internal path nests, so this only guards raw callers; a warning is
# enough (raising would break re-entrancy the RLock otherwise permits).
_SESSION_DEPTH = _thread_local()

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
            f"KERYKEION_BACKEND={_forced_backend!r} is not valid. Choose one of: {', '.join(_VALID_BACKENDS)}"
        )
    try:
        _backend_module = importlib.import_module(_forced_backend)
        BACKEND_NAME = _forced_backend
    except ImportError as _exc:
        if isinstance(_exc, ModuleNotFoundError) and _exc.name == _forced_backend:
            # The backend package itself is genuinely not installed.
            raise ImportError(
                f"KERYKEION_BACKEND={_forced_backend!r} but the package is not installed.\n\n"
                f"Install it with:\n"
                f"  pip install {'pyswisseph' if _forced_backend == 'swisseph' else 'libephemeris'}\n"
            ) from None
        # Installed but broken (e.g. a failing transitive dependency):
        # keep the real cause in the chain.
        raise ImportError(
            f"KERYKEION_BACKEND={_forced_backend!r} is installed but failed to import: {_exc}"
        ) from _exc
    logger.info("Kerykeion ephemeris backend forced via KERYKEION_BACKEND: %s", BACKEND_NAME)
else:
    # Auto-detect: try libephemeris first (our own backend),
    # then fall back to swisseph (third-party, AGPL-3.0 by Astrodienst AG).
    for _candidate in ("libephemeris", "swisseph"):
        try:
            _backend_module = importlib.import_module(_candidate)
            BACKEND_NAME = _candidate
            break
        except ImportError as _exc:
            if isinstance(_exc, ModuleNotFoundError) and _exc.name == _candidate:
                continue  # genuinely not installed — try the next backend
            # Installed but broken: switching engines silently would change
            # results, so make the fallback visible.
            logger.warning(
                "Ephemeris backend %r is installed but failed to import (%s); trying next backend.",
                _candidate,
                _exc,
            )
            continue

    if _backend_module is None:
        raise ImportError(
            "Kerykeion requires an ephemeris backend but neither 'libephemeris' nor "
            "'pyswisseph' is installed.\n\n"
            "Install one of:\n"
            "  pip install libephemeris     # Pure Python (default)\n"
            "  pip install pyswisseph       # Swiss Ephemeris C bindings (AGPL-3.0)\n"
        )

    logger.debug("Kerykeion ephemeris backend (auto-detected): %s", BACKEND_NAME)


# ---------------------------------------------------------------------------
# Public API: the `ephe` object
# ---------------------------------------------------------------------------
# All kerykeion modules import this single object:
#
#     from kerykeion.ephemeris_backend import ephe
#
# It is the actual backend module (swisseph or libephemeris).
# As of libephemeris >= 1.0.0a1, both backends are fully API-compatible
# and no compatibility shims are required.

ephe = _backend_module


def _resolve_polar_houses_error_types() -> Tuple[type[BaseException], ...]:
    """Exception types the active backend raises when a house system is
    mathematically UNDEFINED inside the polar circle.

    Some quadrant house systems (Placidus 'P', Koch 'K') cannot be computed once
    the observer is inside the polar circle (|lat| beyond ~66.56° for the current
    obliquity); the Sunshine systems ('I'/'i') additionally fail whenever the Sun
    is circumpolar for the chart's date. The two backends signal this differently:

    - libephemeris raises a precise ``PolarCircleError``.
    - pyswisseph raises the generic ``swisseph.Error`` for the same failure.

    We prefer the most specific type available so genuine (non-polar) calculation
    errors are NOT swallowed by the polar-latitude fallback below.
    """
    specific = getattr(_backend_module, "PolarCircleError", None)
    if isinstance(specific, type) and issubclass(specific, BaseException):
        return (specific,)
    generic = getattr(_backend_module, "Error", None)
    if isinstance(generic, type) and issubclass(generic, BaseException):
        return (generic,)
    return ()


# Resolved once at import for the active backend (see the helper above).
POLAR_HOUSES_ERROR_TYPES: Tuple[type[BaseException], ...] = _resolve_polar_houses_error_types()


def houses_ex2_with_polar_fallback(
    tjdut: float,
    lat: float,
    lon: float,
    hsys: bytes,
    flags: int,
    *,
    context: str = "",
) -> Tuple[Sequence[float], Sequence[float], Sequence[float], Sequence[float]]:
    """Compute house cusps at the REAL latitude, clamping only when unavoidable.

    Calls ``ephe.houses_ex2`` at the real observer ``lat``. If — and only if — the
    backend reports the chosen house system is undefined inside the polar circle
    (see :data:`POLAR_HOUSES_ERROR_TYPES`), it retries once with the latitude
    clamped to the ±66° polar limit and logs a WARNING naming the system. Every
    house system that IS defined at all latitudes (Whole Sign, Equal, Porphyry,
    Morinus, Meridian/axial, …) therefore keeps the real latitude, and only the
    handful of quadrant systems that genuinely cannot be cast beyond the polar
    circle fall back — instead of the old global clamp that silently mis-cast
    every polar chart at 66°.

    Args:
        tjdut: Julian Day (UT).
        lat: The REAL observer latitude.
        lon: Observer longitude.
        hsys: House system identifier as a 1-byte value (e.g. ``b"P"``).
        flags: Ephemeris iflag.
        context: Optional label for the WARNING (e.g. the subject/relocation name).

    Returns:
        The 4-tuple ``(cusps, ascmc, cusps_speed, ascmc_speed)`` from
        ``ephe.houses_ex2``.
    """
    try:
        return ephe.houses_ex2(tjdut, lat, lon, hsys, flags)
    except POLAR_HOUSES_ERROR_TYPES:
        # Lazy import avoids an import cycle: utilities does not import this
        # module, but this module must not import utilities at load time.
        from kerykeion.utilities import check_and_adjust_polar_latitude

        clamped_lat = check_and_adjust_polar_latitude(lat)
        try:
            hsys_char = hsys.decode("ascii")
        except (UnicodeDecodeError, AttributeError):
            hsys_char = str(hsys)
        logger.warning(
            "House system %r is undefined inside the polar circle at latitude "
            "%.4f°%s; falling back to the ±%.0f° polar limit for the house cusps "
            "only (planetary positions and the persisted latitude keep the real "
            "value). Consider Whole Sign ('W'), Equal ('A') or Porphyry ('O'), "
            "which are defined at every latitude.",
            hsys_char,
            lat,
            f" for {context}" if context else "",
            abs(clamped_lat),
        )
        return ephe.houses_ex2(tjdut, clamped_lat, lon, hsys, flags)


# Swiss Ephemeris keeps mutable process-global state for sidereal mode,
# topocentric coordinates, and reset/close operations. Code that mutates that
# state must hold this lock until the dependent calculations have completed.
EPHEMERIS_LOCK = RLock()

# ---------------------------------------------------------------------------
# Ephemeris data path
# ---------------------------------------------------------------------------
# Override via ``KERYKEION_EPHE_PATH`` environment variable:
#
#     KERYKEION_EPHE_PATH=/path/to/ephe python my_script.py
#
# - libephemeris: manages its own data (~/.libephemeris/leb/); path is a no-op.
# - swisseph: needs .se1 files; without KERYKEION_EPHE_PATH, the default
#   download directory of ``python -m kerykeion.swisseph_setup`` is
#   auto-detected, then swisseph falls back to its built-in Moshier
#   analytical ephemeris (lower precision).

# Default target of `python -m kerykeion.swisseph_setup`; the shared constant
# lives in config_constants (dependency-free) so the setup script can use it
# without importing this module. Re-exported here for backward compatibility.
from kerykeion.settings.config_constants import DEFAULT_SWEPH_DOWNLOAD_DIR


def _dir_has_sweph_data(path: str) -> bool:
    try:
        return any(f.lower().endswith(".se1") for f in os.listdir(path))
    except OSError:
        return False


_user_ephe_path = os.environ.get("KERYKEION_EPHE_PATH", "").strip()

if _user_ephe_path:
    EPHE_DATA_PATH: str = _user_ephe_path
    if BACKEND_NAME == "swisseph" and not _dir_has_sweph_data(EPHE_DATA_PATH):
        logger.warning(
            "KERYKEION_EPHE_PATH=%r does not contain readable .se1 files. "
            "swisseph may fall back to Moshier analytical ephemeris.",
            EPHE_DATA_PATH,
        )
elif BACKEND_NAME == "swisseph":
    if _dir_has_sweph_data(DEFAULT_SWEPH_DOWNLOAD_DIR):
        EPHE_DATA_PATH = DEFAULT_SWEPH_DOWNLOAD_DIR
        logger.info(
            "Using Swiss Ephemeris data auto-detected in %s (set "
            "KERYKEION_EPHE_PATH to override).",
            DEFAULT_SWEPH_DOWNLOAD_DIR,
        )
    else:
        EPHE_DATA_PATH = ""
        logger.warning(
            "KERYKEION_EPHE_PATH not set. swisseph will use its internal Moshier "
            "analytical ephemeris (lower precision). Run "
            "`python -m kerykeion.swisseph_setup` to download the data files, or "
            "set KERYKEION_EPHE_PATH to a directory containing .se1 files."
        )
else:
    EPHE_DATA_PATH = ""

logger.debug("Ephemeris data path: %r", EPHE_DATA_PATH)

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

_PINNED_LEB_MODE: Optional[str] = None

if BACKEND_NAME == "libephemeris":
    _VALID_LEB_MODES = ("leb", "auto", "skyfield", "horizons")
    _PINNED_LEB_MODE = os.environ.get("KERYKEION_LEB_MODE", "leb").strip().lower()
    if _PINNED_LEB_MODE not in _VALID_LEB_MODES:
        raise ValueError(
            f"Invalid KERYKEION_LEB_MODE={_PINNED_LEB_MODE!r}. Must be one of {_VALID_LEB_MODES}."
        )
    _backend_module.set_calc_mode(_PINNED_LEB_MODE)
    logger.debug("libephemeris calc mode set to: %s", _PINNED_LEB_MODE)

# ---------------------------------------------------------------------------
# Startup log: backend identity, version, and format
# ---------------------------------------------------------------------------

if BACKEND_NAME == "libephemeris":
    _mode = _backend_module.get_calc_mode()
    _tier = _backend_module.get_precision_tier()
    _parts = [f"mode={_mode}", f"tier={_tier}"]
    logger.info(
        "kerykeion ephemeris: libephemeris %s (%s)",
        _backend_module.__version__,
        ", ".join(_parts),
    )
elif BACKEND_NAME == "swisseph":
    logger.warning(
        "kerykeion ephemeris: pyswisseph (Swiss Ephemeris by Astrodienst AG, AGPL-3.0). "
        "This is third-party code with AGPL network-disclosure obligations. "
        "Install libephemeris for the default backend."
    )

# ---------------------------------------------------------------------------
# Shared ephemeris session management
# ---------------------------------------------------------------------------


def reset_ephemeris_session() -> None:
    """Reset per-calculation ephemeris state without degrading the backend.

    Uses ``reset_session()`` when the backend provides it (libephemeris),
    which clears sidereal mode, topocentric coordinates and per-call flags
    while keeping the LEB reader, Skyfield timescale and SPK kernels alive.
    Falls back to ``close()`` on backends without ``reset_session()``
    (pyswisseph).

    Both reset paths clear the libephemeris calculation mode, so the mode
    pinned at import time (``KERYKEION_LEB_MODE``, default ``"leb"``) is
    re-applied afterwards — otherwise a single reset would silently re-enable
    the Skyfield auto-fallback this module explicitly disables.

    Callers must hold ``EPHEMERIS_LOCK``. Never call ``ephe.close()``
    directly; use this function (or ``ephemeris_session``) instead.
    """
    _reset = getattr(ephe, "reset_session", None) or ephe.close
    try:
        _reset()
    finally:
        # Re-pin the calc mode even if the reset itself raised — a session
        # left in "auto" mode would silently re-enable the Skyfield fallback.
        if BACKEND_NAME == "libephemeris" and _PINNED_LEB_MODE is not None:
            ephe.set_calc_mode(_PINNED_LEB_MODE)


@contextmanager
def ephemeris_session(
    *,
    zodiac_type: Optional[str] = None,
    sidereal_mode: Optional[str] = None,
    custom_ayanamsa_t0: Optional[float] = None,
    custom_ayanamsa_ayan_t0: Optional[float] = None,
    perspective_type: Optional[str] = None,
    topo: Optional[Tuple[float, float, float]] = None,
    ephe_path: Optional[str] = None,
) -> Iterator[int]:
    """Serialized, self-cleaning ephemeris calculation session.

    This is the single supported way for kerykeion code to touch the
    process-global ephemeris state (``set_ephe_path``, ``set_sid_mode``,
    ``set_topo``). It acquires ``EPHEMERIS_LOCK``, applies the requested
    configuration, yields the ``iflag`` to pass to ``ephe.calc_ut``-style
    functions, and on exit resets the session via
    :func:`reset_ephemeris_session` and releases the lock.

    Args:
        zodiac_type: ``"Tropical"`` (default) or ``"Sidereal"``. When sidereal,
            ``FLG_SIDEREAL`` is OR-ed into the yielded iflag and the sidereal
            mode is configured on the backend.
        sidereal_mode: Named ayanamsa (e.g. ``"LAHIRI"``) or ``"USER"``. Raw
            callers that leave it unset fall back to the shared
            ``DEFAULT_SIDEREAL_MODE`` (currently ``"FAGAN_BRADLEY"``) when
            ``zodiac_type`` is sidereal.
        custom_ayanamsa_t0: Reference epoch (JD) for ``sidereal_mode="USER"``.
        custom_ayanamsa_ayan_t0: Ayanamsa value (degrees) at ``t0`` for
            ``sidereal_mode="USER"``.
        perspective_type: One of ``"Apparent Geocentric"`` (default),
            ``"True Geocentric"``, ``"Heliocentric"``, ``"Topocentric"``,
            ``"Barycentric"``.
        topo: ``(lng, lat, altitude_m)`` observer tuple, required when
            ``perspective_type="Topocentric"``.
        ephe_path: Ephemeris data path; defaults to ``EPHE_DATA_PATH``.

    Yields:
        int: Base iflag (``FLG_SWIEPH | FLG_SPEED`` plus perspective/sidereal
        flags). OR in additional flags (e.g. ``FLG_EQUATORIAL``) as needed.

    Usage::

        from kerykeion.ephemeris_backend import ephemeris_session

        with ephemeris_session(zodiac_type=subject.zodiac_type,
                               sidereal_mode=subject.sidereal_mode) as iflag:
            lon = ephe.calc_ut(jd, ephe.SUN, iflag)[0][0]

    Notes:
        - ``EPHEMERIS_LOCK`` is re-entrant, but keep sessions as narrow as
          possible and do NOT build :class:`AstrologicalSubjectFactory`
          subjects (or call other factories) inside a session: the inner
          calculation's cleanup resets the sidereal/topo state configured by
          the outer session. Exit the session first, then build subjects.
        - ``sidereal_mode="USER"`` raises ``ValueError`` when the custom
          ayanamsa parameters are missing.
    """
    with EPHEMERIS_LOCK:
        depth = getattr(_SESSION_DEPTH, "value", 0)
        if depth > 0:
            logger.warning(
                "Nested ephemeris_session detected (depth %d): the inner session's "
                "cleanup will reset the sidereal/topocentric state configured by the "
                "outer session, silently shifting its subsequent positions. Exit the "
                "outer session before building subjects or calling other factories.",
                depth + 1,
            )
        _SESSION_DEPTH.value = depth + 1
        try:
            ephe.set_ephe_path(EPHE_DATA_PATH if ephe_path is None else ephe_path)
            iflag = ephe.FLG_SWIEPH | ephe.FLG_SPEED

            if perspective_type == "True Geocentric":
                iflag |= ephe.FLG_TRUEPOS
            elif perspective_type == "Heliocentric":
                iflag |= ephe.FLG_HELCTR
            elif perspective_type == "Barycentric":
                iflag |= ephe.FLG_BARYCTR
            elif perspective_type == "Topocentric":
                iflag |= ephe.FLG_TOPOCTR
                if topo is None:
                    raise ValueError("perspective_type='Topocentric' requires the topo=(lng, lat, alt) argument")
                ephe.set_topo(topo[0], topo[1], topo[2] or 0.0)

            if zodiac_type == "Sidereal":
                iflag |= ephe.FLG_SIDEREAL
                if sidereal_mode == "USER":
                    if custom_ayanamsa_t0 is None or custom_ayanamsa_ayan_t0 is None:
                        raise ValueError(
                            "sidereal_mode='USER' requires custom_ayanamsa_t0 and custom_ayanamsa_ayan_t0"
                        )
                    ephe.set_sid_mode(ephe.SIDM_USER, custom_ayanamsa_t0, custom_ayanamsa_ayan_t0)
                else:
                    # Defensive fallback for raw callers that bypass the model
                    # validator/factory; DEFAULT_SIDEREAL_MODE is the shared default.
                    from kerykeion.settings.config_constants import DEFAULT_SIDEREAL_MODE

                    sidm_name = f"SIDM_{sidereal_mode or DEFAULT_SIDEREAL_MODE}"
                    try:
                        sidm_const = getattr(ephe, sidm_name)
                    except AttributeError:
                        raise ValueError(
                            f"Unknown sidereal_mode {sidereal_mode!r}: the ephemeris backend "
                            f"has no ayanamsa constant {sidm_name!r}."
                        ) from None
                    ephe.set_sid_mode(sidm_const)

            yield iflag
        finally:
            _SESSION_DEPTH.value = getattr(_SESSION_DEPTH, "value", 1) - 1
            reset_ephemeris_session()


__all__ = [
    "ephe",
    "BACKEND_NAME",
    "EPHE_DATA_PATH",
    "EPHEMERIS_LOCK",
    "ephemeris_session",
    "reset_ephemeris_session",
]
