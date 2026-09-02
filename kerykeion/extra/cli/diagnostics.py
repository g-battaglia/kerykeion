# -*- coding: utf-8 -*-
"""``kerykeion status`` — what is in use, and with ``--check`` whether it works.

Stdlib only, and kerykeion itself is imported only inside :func:`gather_status`,
so the module loads on any install. Every probe is defensive: a failing
accessor becomes a labelled ``<error>`` field, never an abort — a diagnostic's
job is to surface state, not to crash on it. ``--check`` adds the assertions
(a real calculation included) and a non-zero exit when one fails.
"""

from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Callable

# Surfaced verbatim so the user sees what is actually in effect.
_KNOWN_ENV = (
    "KERYKEION_BACKEND",
    "KERYKEION_LEB_MODE",
    "KERYKEION_EPHE_PATH",
    "LIBEPHEMERIS_MODE",
    "LIBEPHEMERIS_DATA_DIR",
    "LIBEPHEMERIS_LEB",
    "LIBEPHEMERIS_PRECISION",
)


def _safe(fn: Callable[[], Any]) -> Any:
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 — diagnostics must not crash
        return {"_error": f"{type(exc).__name__}: {exc}"}


def _is_error(value: Any) -> bool:
    return isinstance(value, dict) and set(value) == {"_error"}


def _fmt(value: Any, missing: str = "unknown") -> str:
    if _is_error(value):
        return f"<{value['_error']}>"
    return missing if value is None or value == "" else str(value)


def _yesno(value: Any) -> str:
    if _is_error(value):
        return f"<{value['_error']}>"
    return "unknown" if value is None else ("yes" if value else "no")


# ── data collection ──────────────────────────────────────────────────────────


def _libephemeris_data_dir() -> str:
    """libephemeris has no public accessor for its data dir; this re-applies its rule."""
    return os.environ.get("LIBEPHEMERIS_DATA_DIR") or os.path.join(os.path.expanduser("~"), ".libephemeris")


def _libephemeris_detail(ephe: Any) -> dict[str, Any]:
    inventory = ephe.get_leb_inventory()
    if not isinstance(inventory, dict):
        return {"error": f"unexpected inventory type: {type(inventory).__name__}"}
    detail: dict[str, Any] = {"data_dir": _libephemeris_data_dir(), "ready": inventory.get("ready")}
    if inventory.get("error") is not None:
        detail["error"] = inventory["error"]
        return detail
    detail["file_count"] = len(inventory.get("files") or [])
    detail["body_count"] = inventory.get("body_count")
    return detail


def _swisseph_detail() -> dict[str, Any]:
    from kerykeion.ephemeris_backend import EPHE_DATA_PATH

    path = EPHE_DATA_PATH or ""
    se1_count = len(list(Path(path).glob("*.se1"))) if path and Path(path).is_dir() else 0
    return {
        "data_path": path or "(unset — pyswisseph falls back to its built-in Moshier ephemeris)",
        "se1_count": se1_count,
    }


def gather_status() -> dict[str, Any]:
    """The status payload: importing kerykeion pins the backend, so these are the *effective* values."""
    import kerykeion

    state: dict[str, Any] = {
        "kerykeion_version": _safe(lambda: kerykeion.__version__),
        "python_version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "executable": sys.executable,
        "backend": _safe(lambda: kerykeion.BACKEND_NAME),
    }

    def _ephe():
        from kerykeion.ephemeris_backend import ephe

        return ephe

    ephe = _safe(_ephe)
    state["backend_version"] = _safe(lambda: ephe.__version__)
    if state["backend"] == "libephemeris":  # calc mode / tier / policy are libephemeris concepts
        state["calc_mode"] = _safe(lambda: ephe.get_calc_mode())
        state["precision_tier"] = _safe(lambda: ephe.get_precision_tier())
        state["network_policy"] = _safe(lambda: ephe.get_network_policy())
        state["ephemeris"] = _safe(lambda: _libephemeris_detail(ephe))
    elif state["backend"] == "swisseph":
        state["ephemeris"] = _safe(_swisseph_detail)
    env: dict[str, Any] = {key: os.environ.get(key) for key in _KNOWN_ENV}
    # libephemeris loads a cwd ./.env at import; its presence is the useful signal.
    env["_cwd_env_present"] = (Path.cwd() / ".env").exists()
    state["env"] = env
    return state


# ── checks ───────────────────────────────────────────────────────────────────


def run_checks(state: dict[str, Any]) -> list[dict[str, str]]:
    """The install assertions: ``pass``, ``fail``, or ``warn`` for a finding that does not break anything."""
    out: list[dict[str, str]] = []

    def add(name: str, ok: bool | None, detail: str) -> None:
        out.append({"check": name, "status": "pass" if ok else ("warn" if ok is None else "fail"), "detail": detail})

    backend = state.get("backend")
    add("backend", bool(backend) and backend != "unknown", f"active backend: {backend}")

    ephemeris = state.get("ephemeris") or {}
    if "error" in ephemeris:
        add("ephemeris data", False, f"inventory error: {ephemeris['error']}")
    elif backend == "libephemeris":
        ready = ephemeris.get("ready")
        where = ephemeris.get("data_dir")
        detail = f"{ephemeris.get('file_count', 0)} file(s) in {where}" if ready else f"reader not ready in {where}"
        add("ephemeris data", bool(ready), detail)
    else:
        count = ephemeris.get("se1_count", 0)
        add("ephemeris data", True if count else None, f"{count} .se1 file(s) at {ephemeris.get('data_path') or 'built-in Moshier'}")

    try:  # the store holds birth data: a widened mode is worth a warning
        from kerykeion.extra.cli import config

        store = config.profiles_dir()
        if store.is_dir():
            mode = store.stat().st_mode & 0o777
            add(
                "profile store permissions",
                mode == 0o700 or None,
                f"{store} is {oct(mode)}" + ("" if mode == 0o700 else " (expected 0o700)"),
            )
        else:
            add("profile store permissions", None, f"{store} does not exist yet")
    except Exception as exc:  # pragma: no cover
        add("profile store permissions", None, f"could not stat the store: {exc}")

    if (state.get("env") or {}).get("_cwd_env_present"):  # libephemeris loads ./.env at import
        add(
            "working-directory .env",
            None,
            "a .env in the current directory is loaded at import and may repoint LIBEPHEMERIS_* settings",
        )

    try:  # the one check that exercises the whole stack
        from kerykeion import AstrologicalSubjectFactory

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="check", year=2000, month=1, day=1, hour=12, minute=0, lat=51.5, lng=-0.12, tz_str="Europe/London",
            online=False, suppress_geonames_warning=True,
        )  # fmt: skip
        sun = getattr(subject, "sun", None)
        add("sample calculation", getattr(sun, "sign", None) is not None, f"2000-01-01 natal: Sun in {getattr(sun, 'sign', '?')}")
    except Exception as exc:
        add("sample calculation", False, f"{type(exc).__name__}: {exc}")
    return out


# ── text rendering ───────────────────────────────────────────────────────────


def format_status_text(state: dict[str, Any]) -> str:
    """The status payload as a plain-text, ANSI-free report."""
    out = [
        f"kerykeion {_fmt(state.get('kerykeion_version'))} - status",
        "",
        f"Python:   {_fmt(state.get('python_version'))} ({_fmt(state.get('implementation'))}) on {_fmt(state.get('platform'))}",
    ]
    if state.get("executable"):
        out.append(f"          {state['executable']}")
    backend = _fmt(state.get("backend"))
    out += ["", f"Backend:  {backend} {_fmt(state.get('backend_version'))}"]
    if "calc_mode" in state:
        out.append(f"  calc mode:       {_fmt(state.get('calc_mode'))}    (LEB mode)")
    if "precision_tier" in state:
        out.append(f"  precision tier:  {_fmt(state.get('precision_tier'))}")
    if "network_policy" in state:
        out.append(f"  network policy:  {_fmt(state.get('network_policy'))}")
    out.append("")
    ephemeris = state.get("ephemeris")
    if isinstance(ephemeris, dict) and not _is_error(ephemeris):
        if backend == "swisseph":
            out += [
                "Ephemeris data (Swiss Ephemeris):",
                f"  data path:       {_fmt(ephemeris.get('data_path'))}",
                f"  .se1 files:      {_fmt(ephemeris.get('se1_count'))}",
            ]
        else:
            out += [
                "Ephemeris data (libephemeris LEB):",
                f"  data dir:        {_fmt(ephemeris.get('data_dir'))}",
                f"  ready:           {_yesno(ephemeris.get('ready'))}",
            ]
            if ephemeris.get("error"):
                out.append(f"  inventory error: {ephemeris['error']}")
            else:
                out.append(f"  files:           {ephemeris.get('file_count', 0)}, {_fmt(ephemeris.get('body_count'))} bodies")
        out.append("")
    env = state.get("env")
    if isinstance(env, dict) and not _is_error(env):
        out.append("Environment:")
        out += [f"  {key:<24} {'(unset)' if env.get(key) is None else env[key]}" for key in _KNOWN_ENV]
        if env.get("_cwd_env_present"):
            out.append(
                "  Note: a ./.env file is present in the current directory; libephemeris\n"
                "        loads it at import (cwd ./.env before ~/.libephemeris/.env), so\n"
                "        LIBEPHEMERIS_* keys in it affect the backend. KERYKEION_LEB_MODE\n"
                "        still pins the calc mode regardless."
            )
        out.append("")
    return "\n".join(out) + "\n"


def format_checks_text(checks: list[dict[str, str]]) -> str:
    marks = {"pass": "ok  ", "warn": "warn", "fail": "FAIL"}
    failed = sum(1 for check in checks if check["status"] == "fail")
    lines = ["Checks:", *(f"  [{marks[c['status']]}] {c['check']}: {c['detail']}" for c in checks), ""]
    lines.append("All checks passed." if not failed else f"{failed} check(s) failed.")
    return "\n".join(lines) + "\n"


def render(json_out: bool = False, check: bool = False) -> int:
    """Write the status (and the checks, with *check*) to stdout; the exit code is 6 when a check fails."""
    state = gather_status()
    if not check:
        sys.stdout.write(json.dumps(state, indent=2, default=str) + "\n" if json_out else format_status_text(state))
        return 0
    checks = run_checks(state)
    failed = any(c["status"] == "fail" for c in checks)
    if json_out:
        sys.stdout.write(json.dumps({**state, "ok": not failed, "checks": checks}, indent=2, default=str) + "\n")
    else:
        sys.stdout.write(format_status_text(state) + format_checks_text(checks))
    return 6 if failed else 0
