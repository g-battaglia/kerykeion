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


class SamplingLimitError(ValueError):
    """A requested ephemeris/transit series exceeds the sampling ceiling.

    Raised **before** the heavy computation runs: the sample count is
    pre-computed from the factory's own step defaults (read off the signature
    via ``inspect``), so the user gets a fast, clear message instead of a run
    that churns for minutes and then fails — or worse, silently consumes all
    memory. Mapped to exit 8 (:attr:`ExitCode.SAMPLING_LIMIT`).

    Subclasses :class:`ValueError` so that, should the explicit ``classify``
    branch ever be missed, it still falls through to a sane exit (4) rather
    than exit 1.
    """


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
    ``MANDATORY_EVOLUTIONS.md §2``); until then we register the concrete
    coverage/data error types we can reach from each backend, best-effort. The
    important Skyfield one is ``EphemerisRangeError`` (a ``ValueError``
    subclass), which we must classify before plain ``ValueError`` below. With the
    v6 default ``libephemeris`` backend, its ``EphemerisRangeError`` and
    ``DataNotFoundError`` (the base of SPK/Star/Unknown-body-not-found) are the
    analogues — both subclass ``libephemeris.Error`` (not ``ValueError``), so
    without this they would fall through to exit 5/4 instead of the documented
    exit 6. Ambiguous types (input validation, polar circle, network-sealed) are
    deliberately left out so they keep their clearer codes.
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
    try:
        from libephemeris.exceptions import DataNotFoundError, EphemerisRangeError as _LibEphRangeError

        found.append(_LibEphRangeError)
        found.append(DataNotFoundError)
    except Exception:  # pragma: no cover - libephemeris may be absent (swisseph env)
        pass
    # TODO(BACKEND_ERROR_TYPES): once kerykeion exposes the active backend's
    # hard-error types itself, prefer that tuple over backend-specific probing.
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
    if isinstance(exc, SamplingLimitError):
        return ExitCode.SAMPLING_LIMIT
    import pydantic

    if isinstance(exc, pydantic.ValidationError):
        return ExitCode.INVALID_INPUT
    if isinstance(exc, (ValueError, KeyError, OSError, TypeError)):
        # OSError covers ProfileNotFound (unknown -s target), a missing input
        # file (FileNotFoundError), `-o` pointed at a directory or a read-only
        # path (IsADirectoryError/PermissionError): all user-input problems, not
        # unexpected crashes. TypeError covers a wrong/missing argument to a
        # dispatched factory (``call``), which is bad input, not a bug in the CLI.
        return ExitCode.INVALID_INPUT
    return ExitCode.UNEXPECTED


def _is_typer_exit(exc: BaseException) -> bool:
    """True if *exc* is typer's/click's control-flow ``Exit`` signal.

    ``typer.Exit`` is a ``RuntimeError`` (not ``SystemExit``): if it reached
    :func:`error_boundary`'s ``except BaseException`` it would be classified as
    UNEXPECTED (exit 1). The caller re-raises it so click/typer's outer handler
    converts it to the intended ``SystemExit(code)``. typer is imported lazily so
    this module keeps no module-level typer dependency.
    """
    try:
        from typer import Exit
    except Exception:  # pragma: no cover - typer is a hard [cli] dependency
        return False
    return isinstance(exc, Exit)


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
            # ``typer.Exit`` is a control-flow signal carrying an exit code, not a
            # crash; let it propagate to click/typer's outer handler. Without
            # this it would fall through to ``handle_uncaught`` and misclassify
            # as UNEXPECTED (exit 1).
            if _is_typer_exit(exc):
                raise
            handle_uncaught(exc)

    return wrapper  # type: ignore[return-value]
