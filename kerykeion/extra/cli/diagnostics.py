# -*- coding: utf-8 -*-
"""The ``kerykeion status`` core — runtime introspection, stdlib-only.

Shared by the Typer command and the no-extra dispatch in ``kerykeion.extra.cli.main``,
so it imports neither typer nor rich; kerykeion itself is imported only inside
:func:`gather_status`, so the module loads on any install. Every
probe is defensive: a failing accessor becomes a labelled ``<error>`` field,
never an abort — a diagnostic's job is to surface state, not to crash on it.
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


def _human_bytes(n: Any) -> str:
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "?"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024.0:
            return f"{int(n)} B" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"


def _file_coverage(file_info: dict[str, Any]) -> str | None:
    """``"1850-2150"`` (or ``"2000"``) from a file's body coverage, years approximated from the Julian Days."""
    bodies = file_info.get("bodies") or []
    starts = [b["jd_start"] for b in bodies if b.get("jd_start") is not None]
    ends = [b["jd_end"] for b in bodies if b.get("jd_end") is not None]
    if not starts or not ends:
        return None
    try:
        y0, y1 = (int(round(2000 + (float(jd) - 2_451_545.0) / 365.25)) for jd in (min(starts), max(ends)))
    except (TypeError, ValueError):
        return None
    return f"{y0}" if y0 == y1 else f"{y0}-{y1}"


# ── data collection ──────────────────────────────────────────────────────────


def _libephemeris_data_dir() -> str:
    """libephemeris has no public accessor for its data dir; this re-applies its rule."""
    return os.environ.get("LIBEPHEMERIS_DATA_DIR") or os.path.join(os.path.expanduser("~"), ".libephemeris")


def _libephemeris_detail(ephe: Any) -> dict[str, Any]:
    inv = ephe.get_leb_inventory()
    if not isinstance(inv, dict):
        return {"error": f"unexpected inventory type: {type(inv).__name__}"}
    if inv.get("error") is not None:
        return {"data_dir": _libephemeris_data_dir(), "ready": inv.get("ready"), "error": inv["error"]}
    files = [
        {
            "name": f.get("name"),
            "path": f.get("path"),
            "group": f.get("group"),
            "size_bytes": f.get("size_bytes") or 0,
            "body_count": f.get("body_count"),
            "coverage": _file_coverage(f),
        }
        for f in inv.get("files") or []
    ]
    return {
        "data_dir": _libephemeris_data_dir(),
        "ready": inv.get("ready"),
        "reader_type": inv.get("reader_type"),
        "precision_tier": inv.get("precision_tier"),
        "network_policy_effective": inv.get("network_policy_effective"),
        "body_count": inv.get("body_count"),
        "file_count": len(files),
        "total_size_bytes": sum(f["size_bytes"] for f in files),
        "files": files,
    }


def _swisseph_detail() -> dict[str, Any]:
    from kerykeion.ephemeris_backend import EPHE_DATA_PATH

    path = EPHE_DATA_PATH or ""
    se1 = sorted(f.name for f in Path(path).glob("*.se1")) if path and Path(path).is_dir() else []
    return {
        "data_path": path or "(unset — pyswisseph falls back to its built-in Moshier ephemeris)",
        "data_path_env": os.environ.get("KERYKEION_EPHE_PATH"),
        "se1_files": se1,
        "se1_count": len(se1),
    }


def _swisseph_availability() -> dict[str, Any]:
    """Detect pyswisseph without making it the active backend."""
    import importlib.util

    if importlib.util.find_spec("swisseph") is None:
        return {"installed": False}
    try:
        import swisseph  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        return {"installed": True, "import_error": str(exc)}
    return {"installed": True, "version": getattr(swisseph, "version", None)}


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
    state["swisseph_available"] = _safe(_swisseph_availability)
    env: dict[str, Any] = {k: os.environ.get(k) for k in _KNOWN_ENV}
    # libephemeris loads a cwd ./.env at import; its presence is the useful signal.
    env["_cwd_env_present"] = (Path.cwd() / ".env").exists()
    state["env"] = env
    return state


# ── text rendering ───────────────────────────────────────────────────────────


def _render_ephemeris(out: list[str], backend: str, eph: dict[str, Any]) -> None:
    if backend == "swisseph":
        out += [
            "Ephemeris data (Swiss Ephemeris):",
            f"  data path:       {_fmt(eph.get('data_path'))}",
            f"  .se1 files:      {_fmt(eph.get('se1_count'))}",
        ]
        return
    out += [
        "Ephemeris data (libephemeris LEB):",
        f"  data dir:        {_fmt(eph.get('data_dir'))}",
        f"  ready:           {_yesno(eph.get('ready'))}",
    ]
    if eph.get("error"):
        out.append(f"  inventory error: {eph['error']}")
        return
    out.append(f"  reader:          {_fmt(eph.get('reader_type'))}")
    out.append(
        f"  files:           {eph.get('file_count', 0)} ({_human_bytes(eph.get('total_size_bytes', 0))}), "
        f"{_fmt(eph.get('body_count'))} bodies"
    )
    files = eph.get("files") or []
    for f in files[:8]:
        out.append(
            f"    - {str(f.get('name') or '?'):<26} {_human_bytes(f.get('size_bytes', 0)):>10}   {f.get('coverage') or ''}"
        )
    if len(files) > 8:
        out.append(f"    ... {len(files) - 8} more")


def _render_swisseph_available(out: list[str], sw: dict[str, Any]) -> None:
    out.append("Swiss Ephemeris:")
    if not sw.get("installed"):
        out.append("  pyswisseph:      not installed (optional: pip install kerykeion[swiss])")
    elif sw.get("import_error"):
        out.append(f"  pyswisseph:      installed but import failed: {sw['import_error']}")
    else:
        ver = sw.get("version")
        ver_s = ".".join(str(p) for p in ver) if isinstance(ver, (list, tuple)) else (str(ver) if ver else "")
        out.append(f"  pyswisseph:      installed {ver_s}".rstrip())


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
    eph = state.get("ephemeris")
    if isinstance(eph, dict) and not _is_error(eph) and backend in ("libephemeris", "swisseph"):
        _render_ephemeris(out, backend, eph)
        out.append("")
    sw = state.get("swisseph_available")
    if isinstance(sw, dict) and not _is_error(sw):
        _render_swisseph_available(out, sw)
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
    out.append('Full CLI:  pip install "kerykeion[cli]"  (natal, transit, synastry, ...)')
    return "\n".join(out) + "\n"


def render(json_out: bool = False) -> None:
    """Gather the status and write it to stdout as text or JSON."""
    state = gather_status()
    sys.stdout.write(json.dumps(state, indent=2, default=str) + "\n" if json_out else format_status_text(state))
