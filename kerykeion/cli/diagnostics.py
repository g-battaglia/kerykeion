# -*- coding: utf-8 -*-
"""The ``kerykeion status`` core — runtime introspection, stdlib-only.

This module is imported by BOTH paths that serve ``kerykeion status``:

* the Typer command (:mod:`kerykeion.cli.commands.status`) when the ``[cli]``
  extra is installed;
* the no-extra stdlib dispatch in :func:`kerykeion.cli.main` when it is not.

So it MUST NOT import typer or rich, and MUST NOT import kerykeion at module
level — ``import kerykeion`` pins the backend and pays a ~1.5 s init cost, which
``--version``/``--help`` (the other no-extra commands) deliberately avoid. Every
kerykeion / libephemeris symbol is imported lazily inside :func:`gather_status`.

Every probe is defensive: a single failing accessor never aborts the whole
report. The offending field is rendered as ``<…>`` (text) or ``{"_error": …}``
(JSON) and the rest is still shown. ``status`` is a diagnostic — its job is to
surface state, not to crash on it (e.g. missing LEB data files surface as an
"inventory error" line, not a traceback).
"""

from __future__ import annotations

import json as _json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Callable

# The environment knobs that influence backend selection and data resolution.
# Surfaced verbatim (set value, or "(unset)") so a user can see what is actually
# in effect — including, indirectly, the cwd ``.env`` trap (see _observed_env).
_KNOWN_ENV: tuple[str, ...] = (
    "KERYKEION_BACKEND",
    "KERYKEION_LEB_MODE",
    "KERYKEION_EPHE_PATH",
    "LIBEPHEMERIS_MODE",
    "LIBEPHEMERIS_DATA_DIR",
    "LIBEPHEMERIS_LEB",
    "LIBEPHEMERIS_PRECISION",
)


# ── defensive helpers ────────────────────────────────────────────────────────


def _safe(fn: Callable[[], Any]) -> Any:
    """Run *fn*; on any exception return an ``{"_error": str}`` marker.

    ``status`` must never crash: a broken accessor (a backend that doesn't
    expose one, a missing data file, a permission error) becomes a labeled
    field, not an abort.
    """
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 — diagnostics must not crash
        return {"_error": f"{type(exc).__name__}: {exc}"}


def _is_error(value: Any) -> bool:
    return isinstance(value, dict) and set(value.keys()) == {"_error"}


def _fmt(value: Any, missing: str = "unknown") -> str:
    """Render a status value for the text report."""
    if _is_error(value):
        return f"<{value['_error']}>"
    if value is None or value == "":
        return missing
    return str(value)


def _yesno(value: Any) -> str:
    if _is_error(value):
        return f"<{value['_error']}>"
    if value is None:
        return "unknown"
    return "yes" if value else "no"


def _human_bytes(n: Any) -> str:
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "?"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024.0:
            return f"{int(n)} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"


def _jd_to_year(jd: Any) -> int | None:
    """Approximate calendar year from a Julian Day (J2000.0 anchor).

    Good to within a day or so — enough to label ephemeris-file coverage as a
    human-readable year range. The JD start/end remain the source of truth in
    the JSON output.
    """
    if jd is None:
        return None
    try:
        return int(round(2000 + (float(jd) - 2_451_545.0) / 365.25))
    except (TypeError, ValueError):
        return None


def _file_coverage(file_info: dict[str, Any]) -> str | None:
    """``"1850-2150"`` (or ``"2000"``) from a file's body coverage range."""
    bodies = file_info.get("bodies") or []
    starts = [b.get("jd_start") for b in bodies if b.get("jd_start") is not None]
    ends = [b.get("jd_end") for b in bodies if b.get("jd_end") is not None]
    if not starts or not ends:
        return None
    y0, y1 = _jd_to_year(min(starts)), _jd_to_year(max(ends))
    if y0 is None or y1 is None:
        return None
    return f"{y0}" if y0 == y1 else f"{y0}-{y1}"


# ── data collection ──────────────────────────────────────────────────────────


def _import_ephe() -> Any:
    from kerykeion.ephemeris_backend import ephe

    return ephe


def _libephemeris_data_dir() -> str:
    """Resolve the LEB data directory the way libephemeris does.

    libephemeris has no public ``get_data_dir()`` accessor (its resolver is
    private), so we re-apply the same rule: ``LIBEPHEMERIS_DATA_DIR`` env var,
    else ``~/.libephemeris``. The per-file ``path`` entries returned by
    ``get_leb_inventory()`` are the authoritative locations; this is the
    summary line.
    """
    env = os.environ.get("LIBEPHEMERIS_DATA_DIR")
    if env:
        return env
    return os.path.join(os.path.expanduser("~"), ".libephemeris")


def _libephemeris_detail(ephe: Any) -> dict[str, Any]:
    inv = ephe.get_leb_inventory()
    if not isinstance(inv, dict):
        return {"error": f"unexpected inventory type: {type(inv).__name__}"}
    if inv.get("error") is not None:  # reader surfaced a RuntimeError
        return {
            "data_dir": _libephemeris_data_dir(),
            "ready": inv.get("ready"),
            "error": inv["error"],
        }
    files: list[dict[str, Any]] = []
    total = 0
    for f in inv.get("files") or []:
        size = f.get("size_bytes") or 0
        total += size
        files.append(
            {
                "name": f.get("name"),
                "path": f.get("path"),
                "group": f.get("group"),
                "size_bytes": size,
                "body_count": f.get("body_count"),
                "coverage": _file_coverage(f),
            }
        )
    return {
        "data_dir": _libephemeris_data_dir(),
        "ready": inv.get("ready"),
        "reader_type": inv.get("reader_type"),
        "precision_tier": inv.get("precision_tier"),
        "network_policy_effective": inv.get("network_policy_effective"),
        "body_count": inv.get("body_count"),
        "file_count": len(files),
        "total_size_bytes": total,
        "files": files,
    }


def _swisseph_detail() -> dict[str, Any]:
    from kerykeion.ephemeris_backend import EPHE_DATA_PATH

    path = EPHE_DATA_PATH or ""
    se1: list[str] = []
    if path:
        p = Path(path)
        if p.is_dir():
            se1 = sorted(f.name for f in p.glob("*.se1"))
    return {
        "data_path": path or "(unset — pyswisseph falls back to its built-in Moshier ephemeris)",
        "data_path_env": os.environ.get("KERYKEION_EPHE_PATH"),
        "se1_files": se1,
        "se1_count": len(se1),
    }


def _swisseph_availability() -> dict[str, Any]:
    """Detect pyswisseph without forcing it to be the active backend."""
    import importlib.util as _iu

    if _iu.find_spec("swisseph") is None:
        return {"installed": False}
    try:
        import swisseph  # type: ignore[import-not-found]

        # pyswisseph exposes ``version`` as the string "2.10.03"; keep it raw.
        ver = getattr(swisseph, "version", None)
    except Exception as exc:  # noqa: BLE001
        return {"installed": True, "import_error": str(exc)}
    return {"installed": True, "version": ver}


def _observed_env() -> dict[str, Any]:
    env: dict[str, Any] = {k: os.environ.get(k) for k in _KNOWN_ENV}
    # libephemeris loads a cwd ./.env at import (before ~/.libephemeris/.env).
    # Surfacing its presence turns the known trap into a visible signal — we
    # cannot tell which keys came from it vs the shell, but presence alone is
    # the useful diagnostic.
    env["_cwd_env_present"] = (Path.cwd() / ".env").exists()
    return env


def gather_status() -> dict[str, Any]:
    """Build the status payload by introspecting kerykeion and its backend.

    Importing kerykeion triggers backend selection and (for libephemeris) the
    LEB calc-mode pin, so the values here are the *effective* runtime state,
    not the defaults.
    """
    import kerykeion  # noqa: F401 — pins the backend; exposes __version__/BACKEND_NAME

    state: dict[str, Any] = {
        "kerykeion_version": _safe(lambda: kerykeion.__version__),
        "python_version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "executable": sys.executable,
    }

    backend_name = _safe(lambda: kerykeion.BACKEND_NAME)
    state["backend"] = backend_name

    ephe = _safe(_import_ephe)
    state["backend_version"] = _safe(lambda: ephe.__version__)

    # calc_mode / precision_tier / network_policy are libephemeris concepts;
    # query them only when that is the active backend so the swisseph path does
    # not fill the report with <error> markers for accessors it lacks.
    if backend_name == "libephemeris":
        state["calc_mode"] = _safe(lambda: ephe.get_calc_mode())
        state["precision_tier"] = _safe(lambda: ephe.get_precision_tier())
        state["network_policy"] = _safe(lambda: ephe.get_network_policy())
        state["ephemeris"] = _safe(lambda: _libephemeris_detail(ephe))
    elif backend_name == "swisseph":
        state["ephemeris"] = _safe(_swisseph_detail)

    # Swiss Ephemeris availability is useful even when libephemeris is active
    # (it tells the user whether ``KERYKEION_BACKEND=swisseph`` would work).
    state["swisseph_available"] = _safe(_swisseph_availability)
    state["env"] = _observed_env()
    return state


# ── text rendering ───────────────────────────────────────────────────────────


def _render_libephemeris(out: list[str], eph: dict[str, Any]) -> None:
    out.append("Ephemeris data (libephemeris LEB):")
    out.append(f"  data dir:        {_fmt(eph.get('data_dir'))}")
    out.append(f"  ready:           {_yesno(eph.get('ready'))}")
    if eph.get("error"):
        out.append(f"  inventory error: {eph['error']}")
        return
    out.append(f"  reader:          {_fmt(eph.get('reader_type'))}")
    out.append(
        f"  files:           {eph.get('file_count', 0)} "
        f"({_human_bytes(eph.get('total_size_bytes', 0))}), "
        f"{_fmt(eph.get('body_count'))} bodies"
    )
    files = eph.get("files") or []
    for f in files[:8]:
        name = str(f.get("name") or "?")
        cov = f.get("coverage") or ""
        out.append(
            f"    - {name:<26} {_human_bytes(f.get('size_bytes', 0)):>10}   {cov}"
        )
    if len(files) > 8:
        out.append(f"    ... {len(files) - 8} more")


def _render_swisseph(out: list[str], eph: dict[str, Any]) -> None:
    out.append("Ephemeris data (Swiss Ephemeris):")
    out.append(f"  data path:       {_fmt(eph.get('data_path'))}")
    out.append(f"  .se1 files:      {_fmt(eph.get('se1_count'))}")


def _render_swisseph_available(out: list[str], sw: dict[str, Any]) -> None:
    out.append("Swiss Ephemeris:")
    if sw.get("installed"):
        ver = sw.get("version")
        # pyswisseph ``version`` is a string ("2.10.03"); defend against any
        # iterable shape so the renderer never explodes it into characters.
        if isinstance(ver, str):
            ver_s = ver
        elif isinstance(ver, (list, tuple)):
            ver_s = ".".join(str(p) for p in ver)
        else:
            ver_s = str(ver) if ver else ""
        if sw.get("import_error"):
            out.append(f"  pyswisseph:      installed but import failed: {sw['import_error']}")
        else:
            out.append(f"  pyswisseph:      installed {ver_s}".rstrip())
    else:
        out.append("  pyswisseph:      not installed (optional: pip install kerykeion[swiss])")


def _render_env(out: list[str], env: dict[str, Any]) -> None:
    out.append("Environment:")
    for key in _KNOWN_ENV:
        val = env.get(key)
        out.append(f"  {key:<24} {val if val is not None else '(unset)'}")
    if env.get("_cwd_env_present"):
        out.append(
            "  Note: a ./.env file is present in the current directory; libephemeris\n"
            "        loads it at import (cwd ./.env before ~/.libephemeris/.env), so\n"
            "        LIBEPHEMERIS_* keys in it affect the backend. KERYKEION_LEB_MODE\n"
            "        still pins the calc mode regardless."
        )


def format_status_text(state: dict[str, Any]) -> str:
    """Render the status payload as a plain-text, ANSI-free report."""
    out: list[str] = []
    out.append(f"kerykeion {_fmt(state.get('kerykeion_version'))} - status")
    out.append("")
    out.append(
        f"Python:   {_fmt(state.get('python_version'))} "
        f"({_fmt(state.get('implementation'))}) on {_fmt(state.get('platform'))}"
    )
    exe = state.get("executable")
    if exe:
        out.append(f"          {exe}")
    out.append("")

    backend = _fmt(state.get("backend"))
    out.append(f"Backend:  {backend} {_fmt(state.get('backend_version'))}")
    # calc_mode/precision_tier/network_policy are present only for libephemeris.
    if "calc_mode" in state:
        out.append(f"  calc mode:       {_fmt(state.get('calc_mode'))}    (LEB mode)")
    if "precision_tier" in state:
        out.append(f"  precision tier:  {_fmt(state.get('precision_tier'))}")
    if "network_policy" in state:
        out.append(f"  network policy:  {_fmt(state.get('network_policy'))}")
    out.append("")

    eph = state.get("ephemeris")
    if isinstance(eph, dict) and not _is_error(eph):
        if backend == "libephemeris":
            _render_libephemeris(out, eph)
        elif backend == "swisseph":
            _render_swisseph(out, eph)
        out.append("")

    sw = state.get("swisseph_available")
    if isinstance(sw, dict) and not _is_error(sw):
        _render_swisseph_available(out, sw)
        out.append("")

    env = state.get("env")
    if isinstance(env, dict) and not _is_error(env):
        _render_env(out, env)
        out.append("")

    out.append('Full CLI:  pip install "kerykeion[cli]"  (natal, transit, synastry, ...)')
    return "\n".join(out) + "\n"


# ── entry point shared by both paths ─────────────────────────────────────────


def render(json_out: bool = False) -> None:
    """Gather the status and write it to stdout as text or JSON."""
    state = gather_status()
    if json_out:
        sys.stdout.write(_json.dumps(state, indent=2, default=str) + "\n")
    else:
        sys.stdout.write(format_status_text(state))
