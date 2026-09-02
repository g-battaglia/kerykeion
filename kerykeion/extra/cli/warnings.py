# -*- coding: utf-8 -*-
"""Collect and surface ephemeris warnings and polar-house fallbacks.

``ephemeris_warnings`` and ``polar_house_fallbacks`` live on every subject
model but not on the chart-data wrappers, whose subjects nest inside — so
collection walks the nested subjects (cycle-safe by object id). Warnings go
to **stderr** even with ``--format json``, so a piped payload stays clean;
``--warnings-as-errors`` turns them into exit 9 only after the payload is out.
"""

from __future__ import annotations

import sys
from typing import Any, Iterable, Tuple

from kerykeion.extra.cli import errors


def _field(obj: Any, key: str) -> Any:
    return obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)


def _as_iter(value: Any) -> Iterable[Any]:
    if value is None:
        return ()
    return value if isinstance(value, (list, tuple)) else (value,)


def _collect(obj: Any, eph: list, polar: list, seen: set[int]) -> None:
    if obj is None or id(obj) in seen:
        return
    seen.add(id(obj))
    eph.extend(_as_iter(getattr(obj, "ephemeris_warnings", None)))
    polar.extend(_as_iter(getattr(obj, "polar_house_fallbacks", None)))
    # Chart wrappers and composites nest their subjects; ``subjects`` (a list) is
    # what RelationshipScoreModel carries, and the list branch walks it.
    for attr in ("subject", "first_subject", "second_subject", "subjects"):
        _collect(getattr(obj, attr, None), eph, polar, seen)
    if isinstance(obj, (list, tuple)):
        for item in obj:
            _collect(item, eph, polar, seen)


def _dedup(models: list) -> list:
    seen: set = set()
    out: list = []
    for model in models:
        key = tuple(_field(model, k) for k in ("code", "point_name", "message"))
        if key not in seen:
            seen.add(key)
            out.append(model)
    return out


def collect_warnings(obj: Any) -> Tuple[list, list]:
    """Recursively collect ``(ephemeris_warnings, polar_house_fallbacks)``."""
    eph: list = []
    polar: list = []
    _collect(obj, eph, polar, set())
    return _dedup(eph), _dedup(polar)


def _fmt_ephemeris(w: Any) -> str:
    code, point, message = (_field(w, k) for k in ("code", "point_name", "message"))
    parts = [f"[{code}]" if code else "", point or "", message or ""]
    return " ".join(p for p in parts if p) or str(w)


def _fmt_polar(w: Any) -> str:
    message, strategy, used = (_field(w, k) for k in ("message", "strategy", "used_house_system_identifier"))
    head = f"house fallback ({strategy})" if strategy else "house fallback"
    head += f" → {used}" if used else ""
    return f"{head}: {message}" if message else head


def emit_warnings(eph: list, polar: list, stream=None) -> None:
    """Write every warning to *stream* — ``sys.stderr`` resolved at call time, so a redirected stderr is honoured."""
    stream = sys.stderr if stream is None else stream
    for w in eph:
        stream.write(f"kerykeion: warning: {_fmt_ephemeris(w)}\n")
    for w in polar:
        stream.write(f"kerykeion: warning: {_fmt_polar(w)}\n")


def _wrap_envelope(obj: Any, eph: list, polar: list) -> dict:
    """``--envelope``: the payload plus provenance and the warnings, in-band; ``data`` is the plain JSON output verbatim."""
    import json
    from datetime import datetime, timezone

    from kerykeion import BACKEND_NAME, __version__
    from kerykeion.extra.cli.rendering import render_json

    return {
        "kerykeion": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "version": __version__,
            "backend": BACKEND_NAME,
        },
        "warnings": [_fmt_ephemeris(w) for w in eph] + [_fmt_polar(w) for w in polar],
        "data": json.loads(render_json(obj)),
    }


def output_with_warnings(obj: Any, fmt: str, output: str | None, warning_source: Any = None, opts: Any = None) -> None:
    """Emit the payload, then the warnings; exit 9 if ``--warnings-as-errors``.

    *warning_source* (default *obj*) is what warnings are collected from, for a
    command that renders a derivative of the subject (``subject verify``). A
    render error is held so the warnings still surface and exit 9 still wins.
    """
    from kerykeion.extra.cli import rendering

    eph, polar = collect_warnings(obj if warning_source is None else warning_source)
    payload = obj
    if opts is not None and getattr(opts, "envelope", None):
        if fmt != "json":
            raise ValueError(
                "--envelope wraps the payload in a JSON object; it needs --format json "
                f"(or an -o path ending in .json), not {fmt!r}."
            )
        payload = _wrap_envelope(obj, eph, polar)
    render_error = None
    try:
        rendering.write_output(rendering.render(payload, fmt, opts), output)
    except Exception as exc:  # noqa: BLE001 — held, not swallowed
        render_error = exc
    finally:
        emit_warnings(eph, polar)
    if (eph or polar) and errors.warnings_as_errors():
        raise SystemExit(int(errors.ExitCode.WARNINGS_AS_ERRORS))
    if render_error is not None:
        raise render_error
