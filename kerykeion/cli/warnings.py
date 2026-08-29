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
    # ``subjects`` (plural) is a list of subjects on models such as
    # ``RelationshipScoreModel``; the list/tuple branch below iterates it once
    # it is handed to _collect, so listing it here is enough to reach the
    # warnings on each nested subject — otherwise --warnings-as-errors (exit 9)
    # would be silently bypassed for relationship-score payloads.
    for attr in ("subject", "first_subject", "second_subject", "subjects"):
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
    parts = [
        p for p in ([f"[{code}]"] if code else []) + ([point] if point else []) + ([message] if message else []) if p
    ]
    return " ".join(parts) if parts else str(w)


def _fmt_polar(w: Any) -> str:
    message = _get(w, "message")
    strategy = _get(w, "strategy")
    used = _get(w, "used_house_system_identifier")
    head = f"house fallback ({strategy})" if strategy else "house fallback"
    detail = f" → {used}" if used else ""
    return f"{head}{detail}: {message}" if message else f"{head}{detail}"


def emit_warnings(eph: list, polar: list, stream=None) -> None:
    """Write every warning to *stream* (current ``sys.stderr`` by default)."""
    if stream is None:
        # Resolve at call time, not def time: a default argument of
        # ``stream=sys.stderr`` would bind the stream object present at module
        # import, so any later reassignment of ``sys.stderr`` (typer's
        # CliRunner, pytest capsys, an embedding host redirecting stderr) would
        # NOT redirect these warnings — they'd bypass the runner's buffer.
        stream = sys.stderr
    for w in eph:
        stream.write(f"kerykeion: warning: {_fmt_ephemeris(w)}\n")
    for w in polar:
        stream.write(f"kerykeion: warning: {_fmt_polar(w)}\n")


def _wrap_envelope(obj: Any, eph: list, polar: list) -> dict:
    """``--envelope``: the payload plus provenance and the warnings, in-band.

    The data half goes through :func:`render_json` and back, so the enveloped
    ``data`` is byte-for-byte what the un-enveloped payload would have been —
    the envelope cannot drift from the plain output by construction.

    The warnings are the same strings written to stderr, for a consumer that
    cannot read stderr (a pipeline, a CI step capturing only stdout).
    """
    import json
    from datetime import datetime, timezone

    from kerykeion.cli.rendering.json_out import render_json

    meta: dict[str, Any] = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    try:
        from kerykeion import BACKEND_NAME, __version__

        meta["version"] = __version__
        meta["backend"] = BACKEND_NAME
    except Exception:  # pragma: no cover - defensive; kerykeion is the core dep
        pass
    return {
        "kerykeion": meta,
        "warnings": [_fmt_ephemeris(w) for w in eph] + [_fmt_polar(w) for w in polar],
        "data": json.loads(render_json(obj)),
    }


def output_with_warnings(obj: Any, fmt: str, output: str | None, warning_source: Any = None, opts: Any = None) -> None:
    """Emit the payload, then warnings; exit 9 if ``--warnings-as-errors``.

    The payload is written first so it is never lost when a warning escalates.
    Warnings are emitted in a ``finally`` so a render error (e.g. SVG on a
    non-chart object) still surfaces them instead of swallowing them, and so
    ``--warnings-as-errors`` is not silently bypassed by a downstream crash.

    ``warning_source`` (default: *obj*) is what warnings are collected from. It
    differs from *obj* when a command renders a derivative of a subject (e.g.
    ``subject verify`` prints a compact summary but should still surface — and
    honour ``--warnings-as-errors`` for — the warnings on the materialised
    subject it was built from).
    """
    from kerykeion.cli.rendering import emit

    eph, polar = collect_warnings(warning_source if warning_source is not None else obj)
    payload = obj
    if opts is not None and getattr(opts, "envelope", None):
        if fmt != "json":
            raise ValueError(
                "--envelope wraps the payload in a JSON object; it needs --format json "
                f"(or an -o path ending in .json), not {fmt!r}."
            )
        payload = _wrap_envelope(obj, eph, polar)
    # The payload is rendered and written first, but a render crash (e.g. SVG on
    # a non-chart object) must NOT silently bypass ``--warnings-as-errors``. Hold
    # the render error, always emit warnings in the ``finally``, then: if there
    # are fatal warnings, exit 9 (honouring the user's explicit choice over the
    # secondary render failure); only otherwise re-raise the render error so it
    # reaches the error boundary as normal.
    render_error = None
    try:
        emit.write_output(emit.render(payload, fmt, opts), output)
    except Exception as exc:  # noqa: BLE001 — held, not swallowed
        render_error = exc
    finally:
        emit_warnings(eph, polar)
    if (eph or polar) and errors.warnings_as_errors():
        raise SystemExit(int(errors.ExitCode.WARNINGS_AS_ERRORS))
    if render_error is not None:
        raise render_error
