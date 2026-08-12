# -*- coding: utf-8 -*-
"""Collect and surface ephemeris warnings and polar-house fallbacks.

Two field families live on the subject models:

* ``ephemeris_warnings`` — :class:`~kerykeion.schemas.models.EphemerisWarningModel`
  (a date outside coverage, a body the backend cannot compute, …);
* ``polar_house_fallbacks`` — :class:`~kerykeion.schemas.models.PolarHouseFallbackModel`
  (the requested house system is unavailable near a pole and a substitute was used).

They are declared on ``AstrologicalBaseModel`` (so on every subject, composite and
return model) but **not** on the chart-data wrappers: a ``DualChartDataModel``
carries its warnings on ``first_subject`` / ``second_subject``. So collection is a
recursive walk through the nested subjects, with cycle protection by object id.

Warnings always go to **stderr** — even with ``--format json`` — so a payload
piped to ``jq`` stays clean. ``--warnings-as-errors`` turns them into exit 9,
but only *after* the payload has been emitted.
"""

from __future__ import annotations

import sys
from typing import Any, Iterable, Tuple

from kerykeion.cli import errors


def _as_iter(value: Any) -> Iterable[Any]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return value
    return (value,)


def _warn_key(model: Any) -> Any:
    if hasattr(model, "model_dump"):
        d = model.model_dump()
        return (d.get("code"), d.get("point_name"), d.get("message"))
    if isinstance(model, dict):
        return (model.get("code"), model.get("point_name"), model.get("message"))
    return str(model)


def _collect(obj: Any, eph: list, polar: list, seen: set[int]) -> None:
    if obj is None:
        return
    obj_id = id(obj)
    if obj_id in seen:  # cycle / already visited (composite inherits sub-warnings)
        return
    seen.add(obj_id)

    for item in _as_iter(getattr(obj, "ephemeris_warnings", None)):
        eph.append(item)
    for item in _as_iter(getattr(obj, "polar_house_fallbacks", None)):
        polar.append(item)

    # Chart-data wrappers and composite subjects nest their subjects directly.
    for attr in ("subject", "first_subject", "second_subject"):
        child = getattr(obj, attr, None)
        if child is not None:
            _collect(child, eph, polar, seen)

    if isinstance(obj, (list, tuple)):
        for item in obj:
            _collect(item, eph, polar, seen)


def _dedup(models: list) -> list:
    seen: set = set()
    out: list = []
    for model in models:
        key = _warn_key(model)
        if key in seen:
            continue
        seen.add(key)
        out.append(model)
    return out


def collect_warnings(obj: Any) -> Tuple[list, list]:
    """Recursively collect ``(ephemeris_warnings, polar_house_fallbacks)``."""
    eph: list = []
    polar: list = []
    _collect(obj, eph, polar, set())
    return _dedup(eph), _dedup(polar)


def _get(obj: Any, key: str) -> Any:
    if hasattr(obj, key):
        return getattr(obj, key, None)
    if isinstance(obj, dict):
        return obj.get(key)
    return None


def _fmt_ephemeris(w: Any) -> str:
    code = _get(w, "code")
    point = _get(w, "point_name")
    message = _get(w, "message")
    parts = [p for p in ([f"[{code}]"] if code else []) + ([point] if point else []) + ([message] if message else []) if p]
    return " ".join(parts) if parts else str(w)


def _fmt_polar(w: Any) -> str:
    message = _get(w, "message")
    strategy = _get(w, "strategy")
    used = _get(w, "used_house_system_identifier")
    head = f"house fallback ({strategy})" if strategy else "house fallback"
    detail = f" → {used}" if used else ""
    return f"{head}{detail}: {message}" if message else f"{head}{detail}"


def emit_warnings(eph: list, polar: list, stream=sys.stderr) -> None:
    """Write every warning to *stream* (stderr by default), one per line."""
    for w in eph:
        stream.write(f"kerykeion: warning: {_fmt_ephemeris(w)}\n")
    for w in polar:
        stream.write(f"kerykeion: warning: {_fmt_polar(w)}\n")


def output_with_warnings(obj: Any, fmt: str, output: str | None) -> None:
    """Emit the payload, then warnings; exit 9 if ``--warnings-as-errors``.

    The payload is written first so it is never lost when a warning escalates.
    Warnings are emitted in a ``finally`` so a render error (e.g. SVG on a
    non-chart object) still surfaces them instead of swallowing them, and so
    ``--warnings-as-errors`` is not silently bypassed by a downstream crash.
    """
    from kerykeion.cli.rendering import emit

    eph, polar = collect_warnings(obj)
    # The payload is rendered and written first, but a render crash (e.g. SVG on
    # a non-chart object) must NOT silently bypass ``--warnings-as-errors``. Hold
    # the render error, always emit warnings in the ``finally``, then: if there
    # are fatal warnings, exit 9 (honouring the user's explicit choice over the
    # secondary render failure); only otherwise re-raise the render error so it
    # reaches the error boundary as normal.
    render_error = None
    try:
        emit.write_output(emit.render(obj, fmt), output)
    except Exception as exc:  # noqa: BLE001 — held, not swallowed
        render_error = exc
    finally:
        emit_warnings(eph, polar)
    if (eph or polar) and errors.warnings_as_errors():
        raise SystemExit(int(errors.ExitCode.WARNINGS_AS_ERRORS))
    if render_error is not None:
        raise render_error
