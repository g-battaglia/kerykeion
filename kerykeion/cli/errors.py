# -*- coding: utf-8 -*-
"""Exit codes, exception classification and the uncaught-error boundary.

Every exit code the CLI can produce is defined here exactly once. The contract:

    0  OK
    1  unexpected (a bug, or something we failed to name)
    2  usage — reserved for Click/typer, never raised by us
    3  the [cli] extra is missing
    4  invalid input (bad flag value, unknown profile, malformed date, …)
    5  a kerykeion-level error (``KerykeionException``)
    6  an ephemeris/backend error (out of coverage, unsupported body, …)
    7  a network error (GeoNames unreachable, …)
    8  a sampling limit (ephemeris series too long)
    9  warnings treated as errors (--warnings-as-errors)
    130  interrupted (Ctrl-C)

``classify`` turns a caught exception into one of these. The order matters:
backend hard-error types are matched **before** ``ValueError`` because Skyfield's
``EphemerisRangeError`` is a ``ValueError`` subclass — an out-of-coverage date is
an ephemeris problem (6), not bad input (4).
"""

from __future__ import annotations

import sys
import traceback as _traceback
from enum import IntEnum
from functools import wraps
from typing import Callable, NoReturn, Optional, Tuple, Type, TypeVar


class ExitCode(IntEnum):
    OK = 0
    UNEXPECTED = 1
    # 2 is reserved for Click/typer usage errors; never raised here.
    CLI_EXTRA_MISSING = 3
    INVALID_INPUT = 4
    KERYKEION_ERROR = 5
    EPHEMERIS = 6
    NETWORK = 7
    SAMPLING_LIMIT = 8
    WARNINGS_AS_ERRORS = 9
    INTERRUPTED = 130


# ── Global knobs set by the root callback ────────────────────────────────────

_traceback_enabled = False
_warnings_as_errors = False


def set_traceback_enabled(value: bool) -> None:
    global _traceback_enabled
    _traceback_enabled = value


def set_warnings_as_errors(value: bool) -> None:
    global _warnings_as_errors
    _warnings_as_errors = value


def warnings_as_errors() -> bool:
    return _warnings_as_errors


# ── Best-effort type discovery ───────────────────────────────────────────────
# Cached after first lookup so the hot path (every error) does not re-import.


_backend_types: Optional[Tuple[Type[BaseException], ...]] = None
_network_types: Optional[Tuple[Type[BaseException], ...]] = None


def _backend_error_types() -> Tuple[Type[BaseException], ...]:
    """Hard-error types from the active ephemeris backend, best-effort.

    kerykeion does not yet expose a stable ``BACKEND_ERROR_TYPES`` (tracked in
    ``MANDATORY_EVOLUTIONS.md §2``); until then we catch what we can reach. The
    important one is Skyfield's ``EphemerisRangeError`` (a ``ValueError``
    subclass), which we must classify before plain ``ValueError`` below.
    """
    global _backend_types
    if _backend_types is not None:
        return _backend_types
    found: list[Type[BaseException]] = []
    try:
        from skyfield.errors import EphemerisRangeError  # type: ignore[import-not-found]

        found.append(EphemerisRangeError)
    except Exception:  # pragma: no cover - skyfield is an indirect, optional dep
        pass
    # TODO(BACKEND_ERROR_TYPES): once kerykeion exposes the active backend's
    # hard-error types, extend this tuple so they map to exit 6 instead of 4.
    _backend_types = tuple(found)
    return _backend_types


def _network_error_types() -> Tuple[Type[BaseException], ...]:
    global _network_types
    if _network_types is not None:
        return _network_types
    found: list[Type[BaseException]] = []
    try:
        from requests.exceptions import RequestException

        found.append(RequestException)
    except Exception:  # pragma: no cover - requests is a core runtime dep
        pass
    try:
        from urllib.error import URLError

        found.append(URLError)
    except Exception:  # pragma: no cover - stdlib
        pass
    _network_types = tuple(found)
    return _network_types


def classify(exc: BaseException) -> ExitCode:
    """Map an exception to the exit code the CLI should return for it."""
    if isinstance(exc, KeyboardInterrupt):
        return ExitCode.INTERRUPTED
    backend = _backend_error_types()
    if backend and isinstance(exc, backend):
        return ExitCode.EPHEMERIS
    network = _network_error_types()
    if network and isinstance(exc, network):
        return ExitCode.NETWORK
    try:
        from kerykeion import KerykeionException

        if isinstance(exc, KerykeionException):
            return ExitCode.KERYKEION_ERROR
    except Exception:  # pragma: no cover - kerykeion is the core dep
        pass
    import pydantic

    if isinstance(exc, pydantic.ValidationError):
        return ExitCode.INVALID_INPUT
    if isinstance(exc, (ValueError, KeyError, FileNotFoundError)):
        # FileNotFoundError covers ProfileNotFound (unknown -s target): a missing
        # input file is a user-input problem, not an unexpected crash.
        return ExitCode.INVALID_INPUT
    return ExitCode.UNEXPECTED


# ── The boundary ─────────────────────────────────────────────────────────────


def _clean_message(exc: BaseException) -> str:
    """A one- or two-line human message for *exc*; never a full traceback."""
    import pydantic

    if isinstance(exc, pydantic.ValidationError):
        # Pydantic dumps a huge structured blob; surface the first error only.
        errors = exc.errors()
        if errors:
            first = errors[0]
            loc = ".".join(str(part) for part in first.get("loc", ()))
            return f"invalid input at {loc}: {first.get('msg', str(exc))}"
        return "invalid input"
    return str(exc).strip() or exc.__class__.__name__


def handle_uncaught(exc: BaseException) -> NoReturn:
    """Classify *exc*, print a clean message (or a traceback) and exit.

    Called from :func:`error_boundary` (around every command) and, as a last
    resort, from :func:`kerykeion.cli.app.run`.
    """
    code = classify(exc)
    show_trace = _traceback_enabled or code == ExitCode.UNEXPECTED
    if show_trace:
        _traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
    else:
        sys.stderr.write(f"kerykeion: error: {_clean_message(exc)}\n")
    if code == ExitCode.UNEXPECTED and not _traceback_enabled:
        sys.stderr.write("kerykeion: rerun with --traceback to see the full error.\n")
    raise SystemExit(int(code))


_F = TypeVar("_F", bound=Callable[..., object])


def error_boundary(func: _F) -> _F:
    """Decorate a command so any exception becomes a classified exit.

    Wrapping happens at command-registration time (see ``KerykeionTyper``), so
    the boundary covers both the real entry point and in-process
    ``CliRunner`` tests — which call ``app()`` directly and bypass ``run()``.
    """

    @wraps(func)
    def wrapper(*args: object, **kwargs: object) -> object:
        try:
            return func(*args, **kwargs)
        except SystemExit:
            raise
        except BaseException as exc:  # noqa: BLE001 — the whole point is to catch all
            handle_uncaught(exc)

    return wrapper  # type: ignore[return-value]
