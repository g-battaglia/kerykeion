# -*- coding: utf-8 -*-
"""Exit codes, exception classification and the uncaught-error boundary.

    0  OK                          5  a kerykeion-level error (KerykeionException)
    1  unexpected (a bug)          6  an ephemeris/backend error (out of coverage, unknown body…)
    2  usage — Click/typer's       7  a network error (GeoNames unreachable…)
    3  the [cli] extra is missing  8  a sampling limit (series too long)
    4  invalid input               9  warnings treated as errors      130  interrupted

Backend hard-error types are matched before ``ValueError``: Skyfield's
``EphemerisRangeError`` is a ``ValueError`` subclass, and an out-of-coverage
date is an ephemeris problem (6), not bad input (4).
"""

from __future__ import annotations

import os
import sys
import traceback
from enum import IntEnum
from functools import wraps
from typing import Callable, NoReturn, Optional, Tuple, Type, TypeVar


class ExitCode(IntEnum):
    OK = 0
    UNEXPECTED = 1
    CLI_EXTRA_MISSING = 3
    INVALID_INPUT = 4
    KERYKEION_ERROR = 5
    EPHEMERIS = 6
    NETWORK = 7
    SAMPLING_LIMIT = 8
    WARNINGS_AS_ERRORS = 9
    INTERRUPTED = 130


class SamplingLimitError(ValueError):
    """A requested series exceeds the library's sampling ceiling (exit 8); nothing was computed."""


# Set by the root callback before the chosen command runs.
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


# Discovered once; kerykeion exposes no stable BACKEND_ERROR_TYPES yet (MANDATORY_EVOLUTIONS.md §2).
_backend_types: Optional[Tuple[Type[BaseException], ...]] = None
_network_types: Optional[Tuple[Type[BaseException], ...]] = None


def _backend_error_types() -> Tuple[Type[BaseException], ...]:
    """The coverage/data error types of the reachable backends (exit 6)."""
    global _backend_types
    if _backend_types is None:
        found: list[Type[BaseException]] = []
        try:
            from skyfield.errors import EphemerisRangeError  # type: ignore[import-not-found]

            found.append(EphemerisRangeError)
        except Exception:  # pragma: no cover - optional indirect dependency
            pass
        try:
            from libephemeris.exceptions import DataNotFoundError, EphemerisRangeError as LebRangeError

            found += [LebRangeError, DataNotFoundError]
        except Exception:  # pragma: no cover - absent in a swisseph environment
            pass
        _backend_types = tuple(found)
    return _backend_types


def _network_error_types() -> Tuple[Type[BaseException], ...]:
    global _network_types
    if _network_types is None:
        from urllib.error import URLError

        found: list[Type[BaseException]] = [URLError]
        try:
            from requests.exceptions import RequestException

            found.append(RequestException)
        except Exception:  # pragma: no cover - requests is a core dependency
            pass
        _network_types = tuple(found)
    return _network_types


def classify(exc: BaseException) -> ExitCode:
    """Map an exception to the exit code the CLI should return for it."""
    import pydantic

    if isinstance(exc, KeyboardInterrupt):
        return ExitCode.INTERRUPTED
    if isinstance(exc, BrokenPipeError):
        return ExitCode.OK  # `… | head` closed the pipe: the payload that mattered was written
    if isinstance(exc, _backend_error_types()):
        return ExitCode.EPHEMERIS
    if isinstance(exc, _network_error_types()):
        return ExitCode.NETWORK
    from kerykeion import KerykeionException

    if isinstance(exc, KerykeionException):
        return ExitCode.KERYKEION_ERROR
    if isinstance(exc, SamplingLimitError):
        return ExitCode.SAMPLING_LIMIT
    # OSError: unknown profile, missing input file, -o on a directory or read-only path.
    # TypeError: a wrong/missing argument to a dispatched factory (`call`).
    if isinstance(exc, (pydantic.ValidationError, ValueError, KeyError, OSError, TypeError)):
        return ExitCode.INVALID_INPUT
    return ExitCode.UNEXPECTED


def _clean_message(exc: BaseException) -> str:
    """A one-line human message for *exc*; pydantic's blob is cut to its first error."""
    import pydantic

    if isinstance(exc, pydantic.ValidationError):
        first = next(iter(exc.errors()), None)
        if first is None:
            return "invalid input"
        return f"invalid input at {'.'.join(str(p) for p in first.get('loc', ()))}: {first.get('msg', exc)}"
    return str(exc).strip() or exc.__class__.__name__


def handle_uncaught(exc: BaseException) -> NoReturn:
    """Classify *exc*, print a clean message (or a traceback) and exit."""
    code = classify(exc)
    if isinstance(exc, BrokenPipeError):
        # Point stdout at devnull first, or the interpreter's shutdown flush raises a second one.
        try:
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        except (OSError, ValueError):
            pass
        raise SystemExit(0)
    if _traceback_enabled or code == ExitCode.UNEXPECTED:
        traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
    else:
        sys.stderr.write(f"kerykeion: error: {_clean_message(exc)}\n")
    if code == ExitCode.UNEXPECTED and not _traceback_enabled:
        sys.stderr.write("kerykeion: rerun with --traceback to see the full error.\n")
    raise SystemExit(int(code))


_F = TypeVar("_F", bound=Callable[..., object])


def error_boundary(func: _F) -> _F:
    """Wrap a command so any exception becomes a classified exit — also under an in-process ``CliRunner``."""

    @wraps(func)
    def wrapper(*args: object, **kwargs: object) -> object:
        try:
            return func(*args, **kwargs)
        except SystemExit:
            raise
        except BaseException as exc:  # noqa: BLE001 — the whole point is to catch all
            from typer import Exit

            if isinstance(exc, Exit):  # typer's control-flow signal, not a crash
                raise
            handle_uncaught(exc)

    return wrapper  # type: ignore[return-value]
