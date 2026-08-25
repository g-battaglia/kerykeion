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

    from kerykeion.ephemeris_backend.backend import ephe

    ephe.calc_ut(jd, planet_id, flags)
    ephe.houses_ex2(jd, lat, lon, hsys, flags)

The ``ephe`` object exposes the same API regardless of which backend is active.

Detecting the active backend
----------------------------
::

    from kerykeion.ephemeris_backend.backend import BACKEND_NAME
    print(BACKEND_NAME)  # "libephemeris" or "swisseph"

Author: Giacomo Battaglia
Copyright: (C) 2025-2026 Kerykeion Project
License: AGPL-3.0
"""

from __future__ import annotations

import importlib
import logging
import math
import os
from contextlib import contextmanager
from threading import RLock, local as _thread_local
import types
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterator, Optional, Sequence, Tuple

if TYPE_CHECKING:
    from kerykeion.schemas.literals import Houses
    # Type-only: the runtime import lives inside the polar fallback branch below,
    # because the models package imports back into kerykeion at load time.
    from kerykeion.schemas.models import PolarHouseFallbackModel

logger = logging.getLogger(__name__)

# Per-thread nesting depth of ``ephemeris_session``. ``EPHEMERIS_LOCK`` is an
# RLock so the same thread can acquire it recursively, but a nested session is
# not semantically safe: the inner cleanup resets the sidereal/topocentric state
# configured by the outer session. Reject nesting before touching backend state,
# so an accidental inner factory call cannot corrupt the still-active session.
_SESSION_DEPTH = _thread_local()

_VALID_SESSION_ZODIACS = (None, "Tropical", "Sidereal")
_VALID_SESSION_PERSPECTIVES = (
    None,
    "Apparent Geocentric",
    "True Geocentric",
    "Heliocentric",
    "Topocentric",
    "Barycentric",
    "Selenocentric",
    "Mercurycentric",
    "Venuscentric",
    "Marscentric",
    "Jupitercentric",
    "Saturncentric",
)

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
        raise ImportError(f"KERYKEION_BACKEND={_forced_backend!r} is installed but failed to import: {_exc}") from _exc
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
#     from kerykeion.ephemeris_backend.backend import ephe
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
    obliquity). Some backends additionally fail the Sunshine systems ('I'/'i')
    when the Sun is circumpolar for the chart's date, but that is
    backend-dependent (libephemeris does NOT raise for Sunshine at, e.g., 78°N in
    the cases tested). The two backends signal a polar failure differently:

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

# The house system substituted when the requested one is undefined inside the
# polar circle. Porphyry trisects the quadrants the ANGLES already define, so
# cusps[0] == ascmc[0] and cusps[9] == ascmc[1] exactly, at every latitude we can
# cast (verified through ±90°). It therefore preserves the ASC/MC/DSC/IC frame a
# quadrant-system user is asking for, unlike Whole Sign or Equal whose first cusp
# leaves the Ascendant. It is also cheaper than the systems it replaces.
_POLAR_FALLBACK_HSYS = b"O"

# House identifiers whose output is NOT the 12-cusp quadrant division, and which
# therefore cannot accept a 12-cusp substitute: Gauquelin ('G') returns 36 sectors,
# so swapping in Porphyry would silently change the SHAPE of the result rather
# than only its values. These clamp the latitude instead, keeping the requested
# division intact — the trade the substitution avoids everywhere else.
_NON_QUADRANT_HOUSE_SYSTEMS = frozenset({b"G"})

_POLAR_STRATEGIES = ("substitute_system", "clamp_latitude")


def _house_system_name(hsys: bytes) -> Optional[str]:
    """Human-readable name for a house identifier, or None if unavailable.

    Purely descriptive: it decorates the fallback record, so a backend that does
    not expose ``house_name`` must not turn a successful chart into an error.
    """
    getter = getattr(ephe, "house_name", None)
    if getter is None:
        return None
    try:
        return getter(hsys)
    except Exception:
        return None


def _clamp_inside_polar_limit(lat: float, clamped_lat: float, threshold: Optional[float]) -> float:
    """Latitude to retry at when the requested house division must be preserved.

    ``clamped_lat`` is the ±66° rule of thumb. When the backend reported the
    threshold it actually applied, honour that instead whenever it is TIGHTER:
    the polar circle sits at 90° − obliquity, and obliquity varies with the epoch
    (~24.15° in deep antiquity, putting the limit near 65.85°), so retrying at a
    fixed 66° would fail exactly as the first call did. A micro-degree is stepped
    off the threshold because the backend rejects the limit itself; 0.0036" is
    four orders of magnitude finer than anything the resulting cusps resolve.
    """
    if threshold is None or abs(clamped_lat) <= abs(threshold):
        return clamped_lat
    return math.copysign(abs(threshold) - 1e-6, lat)


def houses_ex2_with_polar_fallback_ex(
    tjdut: float,
    lat: float,
    lon: float,
    hsys: bytes,
    flags: int,
    *,
    context: str = "",
    polar_strategy: str = "substitute_system",
) -> Tuple[
    Sequence[float], Sequence[float], Sequence[float], Sequence[float], Optional["PolarHouseFallbackModel"]
]:
    """Compute house cusps at the REAL latitude, substituting the SYSTEM if needed.

    Calls ``ephe.houses_ex2`` at the real observer ``lat``. If — and only if — the
    backend reports the chosen house system is undefined inside the polar circle
    (see :data:`POLAR_HOUSES_ERROR_TYPES`), it retries once and returns a record
    describing what was traded away. Every house system that IS defined at all
    latitudes (Whole Sign, Equal, Porphyry, Morinus, Meridian/axial, …) keeps the
    real latitude untouched.

    The default ``substitute_system`` strategy retries with Porphyry at the REAL
    latitude. This matters beyond tidiness: the Ascendant is the intersection of
    the ecliptic with the horizon, so it is a function of latitude alone and
    cannot depend on which house system was requested. Retrying at a clamped
    latitude — the previous behaviour — pushed the substituted latitude into
    ``ascmc`` and hence into the reported angles, so one place and instant
    yielded a DIFFERENT Ascendant under Placidus than under Whole Sign, and every
    latitude beyond the circle collapsed onto the same frozen 66° value.
    Substituting the system leaves the angles exact and confines the
    approximation to the intermediate cusps, which is where the ambiguity
    genuinely lives.

    ``clamp_latitude`` keeps the requested system and retries just inside the
    polar limit — the backend-reported threshold when it names one, the ±66° rule
    of thumb otherwise, whichever is tighter, since the limit is 90° − obliquity
    and so moves with the epoch.
    It is the honest choice only where the output has no angles to protect
    and no equivalent substitute — Gauquelin's 36 sectors — and is selected
    automatically for those identifiers.

    Args:
        tjdut: Julian Day (UT).
        lat: The REAL observer latitude.
        lon: Observer longitude.
        hsys: House system identifier as a 1-byte value (e.g. ``b"P"``).
        flags: Ephemeris iflag.
        context: Optional label for the WARNING (e.g. the subject/relocation name).
        polar_strategy: ``"substitute_system"`` (default) or ``"clamp_latitude"``.

    Returns:
        The 5-tuple ``(cusps, ascmc, cusps_speed, ascmc_speed, fallback)`` where
        ``fallback`` is a ``PolarHouseFallbackModel`` describing the substitution,
        or ``None`` when the requested system computed normally.
    """
    if polar_strategy not in _POLAR_STRATEGIES:
        raise ValueError(f"polar_strategy must be one of {_POLAR_STRATEGIES}, got {polar_strategy!r}")

    try:
        cusps, ascmc, cusps_speed, ascmc_speed = ephe.houses_ex2(tjdut, lat, lon, hsys, flags)
        return cusps, ascmc, cusps_speed, ascmc_speed, None
    except POLAR_HOUSES_ERROR_TYPES as original_exc:
        # Lazy imports avoid an import cycle: utilities does not import this
        # module, but this module must not import utilities at load time, and the
        # models package imports back into kerykeion.
        from kerykeion.utilities.core import _POLAR_LATITUDE_LIMIT, check_and_adjust_polar_latitude
        from kerykeion.schemas.models import PolarHouseFallbackModel

        # The threshold and obliquity are knowable only from the backend that
        # measured them; libephemeris' PolarCircleError carries both, while the
        # swisseph backend's generic Error carries neither. The latitude and the
        # requested system come from our own call arguments, which are
        # authoritative on every backend.
        threshold = getattr(original_exc, "threshold", None)
        obliquity = getattr(original_exc, "obliquity", None)

        # Decide with the LIMIT, not with the clamp helper: that helper logs
        # "Latitude capped at 66°" as a side effect, and on the substitution path
        # nothing is capped — the retry happens at the real latitude. Calling it
        # merely to ask a question would put a line in the log that the fallback
        # record and the warning below both contradict.
        clamped_lat = max(-_POLAR_LATITUDE_LIMIT, min(_POLAR_LATITUDE_LIMIT, lat))
        if threshold is None and clamped_lat == lat:
            # No measured threshold AND outside the ±66° rule of thumb, so nothing
            # identifies this as a polar-undefined failure. Only reachable on the
            # swisseph backend, whose generic Error cannot tell a polar failure
            # apart from any other houses failure; re-raise the real error
            # unchanged instead of emitting a spurious polar warning and retrying
            # at an unchanged latitude.
            #
            # ±66° is a rule of thumb, NOT the limit: the polar circle sits at
            # 90° − obliquity, and obliquity varies with the epoch (~24.15° around
            # 3000 BCE, so the limit drops to ~65.85°). Gating on the clamp alone
            # would re-raise for every deep-antiquity chart in that band — exactly
            # the case the fallback exists for — so a backend-reported threshold
            # always wins over the constant.
            raise
        try:
            hsys_char = hsys.decode("ascii")
        except (UnicodeDecodeError, AttributeError):
            hsys_char = str(hsys)

        # A 12-cusp substitute cannot represent a 36-sector division, so those
        # identifiers clamp regardless of what the caller asked for.
        strategy = "clamp_latitude" if hsys in _NON_QUADRANT_HOUSE_SYSTEMS else polar_strategy

        if strategy == "substitute_system":
            retry_hsys, retry_lat = _POLAR_FALLBACK_HSYS, lat
            affects = ["house_cusps"]
        else:
            # Only here is a latitude actually capped, so this is where the
            # helper — and the log line it emits — belongs.
            retry_hsys, retry_lat = hsys, _clamp_inside_polar_limit(
                lat, check_and_adjust_polar_latitude(lat), threshold
            )
            affects = ["house_cusps", "angles"]

        try:
            cusps, ascmc, cusps_speed, ascmc_speed = ephe.houses_ex2(tjdut, retry_lat, lon, retry_hsys, flags)
        except Exception as retry_exc:
            # The retry also failed; the ORIGINAL error for the requested system
            # at the real latitude is the meaningful diagnostic (the retry only
            # varied the system or the latitude), so surface it, chaining the
            # retry as the cause.
            raise original_exc from retry_exc

        used_char = retry_hsys.decode("ascii") if strategy == "substitute_system" else hsys_char
        requested_name = _house_system_name(hsys)
        used_name = _house_system_name(retry_hsys)
        where = f" for {context}" if context else ""

        if strategy == "substitute_system":
            message = (
                f"House system {hsys_char!r} is undefined inside the polar circle at latitude "
                f"{lat:.4f}°{where}; the house cusps were computed with {used_char!r} "
                f"({used_name or 'Porphyry'}) at the REAL latitude instead. The Ascendant, MC, "
                f"Descendant, IC and Vertex are unaffected: they are intersections of the ecliptic "
                f"with the horizon and the meridian, independent of any house system."
            )
        else:
            message = (
                f"House system {hsys_char!r} is undefined inside the polar circle at latitude "
                f"{lat:.4f}°{where}; it has no equivalent at every latitude, so its division was "
                f"computed at {retry_lat:.4f}°, just inside the polar limit. The cusps and the angles "
                f"derived from this call are approximate; planetary positions and the persisted "
                f"latitude keep the real value."
            )

        logger.warning("%s", message)

        fallback = PolarHouseFallbackModel(
            strategy=strategy,
            requested_house_system_identifier=hsys_char,
            requested_house_system_name=requested_name,
            used_house_system_identifier=used_char,
            used_house_system_name=used_name,
            latitude=lat,
            used_latitude=retry_lat,
            threshold=threshold,
            obliquity=obliquity,
            affects=affects,
            message=message,
        )
        return cusps, ascmc, cusps_speed, ascmc_speed, fallback


@dataclass(frozen=True)
class HouseRing:
    """Everything one house call knows about the ring it just produced.

    The cusps and the angles come out of the same ephemeris call, and that is the
    only moment at which anything knows both. Twelve numbers on their own cannot
    say which house a Midheaven standing on a crowd of identical cusps opens —
    the information is not in them — so it is recorded here, once, instead of
    being re-derived by each factory or guessed at by each reader.
    """

    cusps: Sequence[float]
    ascmc: Sequence[float]
    cusps_speed: Sequence[float]
    ascmc_speed: Sequence[float]
    polar_fallback: Optional["PolarHouseFallbackModel"] = None
    #: Angle field name -> the house that angle opens, for the angles this chart
    #: puts on their own cusp: all four under the quadrant systems, the Ascendant
    #: and Descendant only under equal houses, the Midheaven and Imum Coeli only
    #: under meridian houses, none under whole sign, Vehlow or Morinus.
    angle_houses: dict[str, "Houses"] = field(default_factory=dict)
    #: One-based house numbers whose cusps share a longitude. Empty for every
    #: chart whose twelve cusps are twelve distinct points.
    coincident_cusps: list[list[int]] = field(default_factory=list)


def houses_ring_with_polar_fallback(
    tjdut: float,
    lat: float,
    lon: float,
    hsys: bytes,
    flags: int,
    *,
    context: str = "",
    polar_strategy: str = "substitute_system",
) -> HouseRing:
    """The house ring, with what only this call can know recorded on it.

    Same computation and same polar substitution as
    :func:`houses_ex2_with_polar_fallback_ex` — this adds the two facts that are
    knowable here and nowhere downstream: which house each angle opens, and which
    cusps stand on top of each other. The natal factory calls this; the relocated
    chart, which has to shift the ring by the ayanamsa first, asks the same two
    questions of the shifted ring itself. The tuple-returning siblings stay for
    callers that want neither.
    """
    # Lazy, for the import cycle documented on the sibling below: utilities does
    # not import this module, and this module must not import utilities at load.
    from kerykeion.utilities.core import angle_house_identities, coincident_cusp_groups

    cusps, ascmc, cusps_speed, ascmc_speed, polar_fallback = houses_ex2_with_polar_fallback_ex(
        tjdut, lat, lon, hsys, flags, context=context, polar_strategy=polar_strategy
    )
    return HouseRing(
        cusps=cusps,
        ascmc=ascmc,
        cusps_speed=cusps_speed,
        ascmc_speed=ascmc_speed,
        polar_fallback=polar_fallback,
        angle_houses=angle_house_identities(cusps, ascmc[0], ascmc[1]),
        coincident_cusps=coincident_cusp_groups(cusps),
    )


def houses_ex2_with_polar_fallback(
    tjdut: float,
    lat: float,
    lon: float,
    hsys: bytes,
    flags: int,
    *,
    context: str = "",
) -> Tuple[Sequence[float], Sequence[float], Sequence[float], Sequence[float]]:
    """Backwards-compatible view of :func:`houses_ex2_with_polar_fallback_ex`.

    Same behaviour, minus the fallback record: callers that have nowhere to put a
    ``PolarHouseFallbackModel`` still get the corrected cusps and the WARNING.

    Returns:
        The 4-tuple ``(cusps, ascmc, cusps_speed, ascmc_speed)``.
    """
    return houses_ex2_with_polar_fallback_ex(tjdut, lat, lon, hsys, flags, context=context)[:4]


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
            "Using Swiss Ephemeris data auto-detected in %s (set KERYKEION_EPHE_PATH to override).",
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
        raise ValueError(f"Invalid KERYKEION_LEB_MODE={_PINNED_LEB_MODE!r}. Must be one of {_VALID_LEB_MODES}.")
    _backend_module.set_calc_mode(_PINNED_LEB_MODE)
    if _PINNED_LEB_MODE == "leb":
        if not hasattr(_backend_module, "set_network_policy"):
            raise RuntimeError(
                "Kerykeion LEB mode requires a libephemeris release with "
                "sealed-network support. Upgrade the pinned dependency."
            )
        _backend_module.set_network_policy("sealed")
    logger.debug("libephemeris calc mode set to: %s", _PINNED_LEB_MODE)

# ---------------------------------------------------------------------------
# Startup log: backend identity, version, and format
# ---------------------------------------------------------------------------

if BACKEND_NAME == "libephemeris":
    _mode = _backend_module.get_calc_mode()
    _tier = _backend_module.get_precision_tier()
    _network = _backend_module.get_network_policy() if hasattr(_backend_module, "get_network_policy") else "unknown"
    _parts = [f"mode={_mode}", f"tier={_tier}", f"network={_network}"]
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
            ``"Barycentric"``, or a supported planetocentric perspective.
        topo: ``(lng, lat, altitude_m)`` observer tuple, required when
            ``perspective_type="Topocentric"``.
        ephe_path: Ephemeris data path; defaults to ``EPHE_DATA_PATH``.

    Yields:
        int: Base iflag (``FLG_SWIEPH | FLG_SPEED`` plus perspective/sidereal
        flags). OR in additional flags (e.g. ``FLG_EQUATORIAL``) as needed.

    Usage::

        from kerykeion.ephemeris_backend.backend import ephemeris_session

        with ephemeris_session(zodiac_type=subject.zodiac_type,
                               sidereal_mode=subject.sidereal_mode) as iflag:
            lon = ephe.calc_ut(jd, ephe.SUN, iflag)[0][0]

    Notes:
        - Nested sessions on the same thread raise ``RuntimeError`` before the
          inner session mutates backend state. Keep sessions as narrow as
          possible and exit the outer session before building subjects or
          calling another factory that opens its own session.
        - Unknown zodiac/perspective names raise ``ValueError`` rather than
          silently selecting the apparent-tropical defaults.
        - Planetocentric perspective names (``"Selenocentric"``,
          ``"Marscentric"``, ...) are accepted as valid, but the session sets
          no calculation flag for them: ``calc_ut`` inside such a session still
          returns geocentric positions. Planetocentric positions must be
          fetched with ``ephe.calc_pctr`` (TT Julian Day), as the subject and
          primary-directions factories do.
        - ``sidereal_mode="USER"`` raises ``ValueError`` when the custom
          ayanamsa parameters are missing or non-finite.
    """
    with EPHEMERIS_LOCK:
        depth = getattr(_SESSION_DEPTH, "value", 0)
        if depth > 0:
            raise RuntimeError(
                "Nested ephemeris_session is not supported: an inner session's cleanup "
                "would reset the sidereal/topocentric state configured by the outer "
                "session. Exit the outer session before building subjects or calling "
                "other factories."
            )
        _SESSION_DEPTH.value = depth + 1
        try:
            if zodiac_type not in _VALID_SESSION_ZODIACS:
                raise ValueError(f"Unknown zodiac_type {zodiac_type!r}: expected 'Tropical', 'Sidereal', or None.")
            if perspective_type not in _VALID_SESSION_PERSPECTIVES:
                valid_perspectives = ", ".join(repr(value) for value in _VALID_SESSION_PERSPECTIVES if value)
                raise ValueError(
                    f"Unknown perspective_type {perspective_type!r}: expected one of {valid_perspectives}, or None."
                )
            if sidereal_mode == "USER":
                if custom_ayanamsa_t0 is None or custom_ayanamsa_ayan_t0 is None:
                    raise ValueError("sidereal_mode='USER' requires custom_ayanamsa_t0 and custom_ayanamsa_ayan_t0")
                if not math.isfinite(custom_ayanamsa_t0) or not math.isfinite(custom_ayanamsa_ayan_t0):
                    raise ValueError("sidereal_mode='USER' custom ayanamsa parameters must be finite numbers")
            if perspective_type == "Topocentric":
                if topo is None:
                    raise ValueError("perspective_type='Topocentric' requires the topo=(lng, lat, alt) argument")
                if len(topo) != 3 or not all(math.isfinite(value) for value in topo):
                    raise ValueError("topo must contain three finite numbers: (lng, lat, altitude_m)")
                if not -180.0 <= topo[0] <= 180.0:
                    raise ValueError("topo longitude must be between -180 and 180 degrees")
                if not -90.0 <= topo[1] <= 90.0:
                    raise ValueError("topo latitude must be between -90 and 90 degrees")

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
                assert topo is not None  # validated above
                ephe.set_topo(topo[0], topo[1], topo[2] or 0.0)

            if zodiac_type == "Sidereal":
                iflag |= ephe.FLG_SIDEREAL
                if sidereal_mode == "USER":
                    assert custom_ayanamsa_t0 is not None
                    assert custom_ayanamsa_ayan_t0 is not None
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
