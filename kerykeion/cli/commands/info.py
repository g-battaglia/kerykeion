# -*- coding: utf-8 -*-
"""``kerykeion info <sub>`` and ``kerykeion doctor`` — describe and check the install.

The CLI validates ``--houses``, ``--zodiac``, ``--sidereal-mode``, ``--points``
and friends against the library's own literals: 23 house systems, 48 ayanamsas,
11 perspectives, 76 points. Until now it could reject a value without ever being
able to *list* the valid ones, which left reading the source as the only way to
find them. ``info`` closes that, and with ``-f json`` it is the machine-readable
source an agent (or a script) can consult instead of hard-coding tables that
drift.

Everything here is **derived at runtime** from the library — the literal aliases
via :func:`typing.get_args`, the point/star presets from the resolver's own
tables, the dominant strategies from ``DominantsFactory.available_methods()``.
Nothing is transcribed, so ``info`` cannot fall out of step with what the flags
actually accept.

``doctor`` is the counterpart for the environment: ``status`` reports, ``doctor``
judges — it runs the same probes plus a real calculation and exits non-zero when
something is actually broken.
"""

from __future__ import annotations

import typing
from typing import Any, Optional

import typer

from kerykeion.cli.commands._shared import _emit
from kerykeion.cli.options import FormatOpt, OutputOpt
from kerykeion.cli.typer_app import KerykeionTyper

info_app = KerykeionTyper(
    name="info",
    help="List what the flags accept: literals, point sets, fixed stars, methods.",
    no_args_is_help=True,
    add_completion=False,
)


def _literal_tables() -> dict[str, list[str]]:
    """Every public ``Literal`` alias in ``kerykeion.schemas.literals``, by name."""
    from kerykeion.schemas import literals

    tables: dict[str, list[str]] = {}
    for name in dir(literals):
        if name.startswith("_"):
            continue
        args = typing.get_args(getattr(literals, name))
        if args and all(isinstance(arg, str) for arg in args):
            tables[name] = list(args)
    return dict(sorted(tables.items()))


@info_app.command("literals")
def literals(
    name: Optional[str] = typer.Argument(
        None, help="One alias to show (e.g. HousesSystemIdentifier). Omit for all."
    ),
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """The accepted values of every literal the flags validate against."""
    tables = _literal_tables()
    if name is None:
        _emit(tables, fmt, output)
        return
    # Case-insensitive, like the flags themselves.
    match = {key.lower(): key for key in tables}.get(name.strip().lower())
    if match is None:
        import difflib

        close = difflib.get_close_matches(name, list(tables), n=1)
        hint = f" (did you mean {close[0]!r}?)" if close else ""
        raise ValueError(
            f"no literal named {name!r}{hint}. Run `kerykeion info literals` for the list."
        )
    _emit({match: tables[match]}, fmt, output)


@info_app.command("points")
def points(
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """The preset names ``--points`` accepts, and what each one contains."""
    from kerykeion.cli import subject_resolver

    _emit(subject_resolver._point_sets(), fmt, output)


@info_app.command("stars")
def stars(
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """The preset names ``--fixed-stars`` accepts, and what each one contains."""
    from kerykeion.cli import subject_resolver

    _emit(subject_resolver._fixed_star_sets(), fmt, output)


@info_app.command("houses")
def houses(
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """What ``--houses`` accepts: the system letters, and the names that map to them.

    Case matters for the letters: ``i`` (Sunshine/alt.) and ``I`` (Sunshine) are
    different systems, so both appear.
    """
    from kerykeion.cli import subject_resolver

    _emit(
        {
            "letters": sorted(subject_resolver._valid_house_letters()),
            "names": dict(sorted(subject_resolver._HOUSES_BY_NAME.items())),
        },
        fmt,
        output,
    )


@info_app.command("methods")
def methods(
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Strategy/method names the technique flags accept, as the library reports them."""
    from kerykeion import DominantsFactory
    from kerykeion.cli.rendering.options import SVG_VARIANTS, chart_choices

    _emit(
        {
            "dominants_method": list(DominantsFactory.available_methods()),
            "lot": ["fortune", "spirit"],
            "directions_rate": ["ptolemy", "naibod"],
            "nodes_method": ["mean", "osculating"],
            "chart_theme": list(chart_choices("theme")),
            "chart_language": list(chart_choices("chart_language")),
            "chart_style": list(chart_choices("style")),
            "svg_variant": sorted(SVG_VARIANTS),
        },
        fmt,
        output,
    )


# ── doctor ───────────────────────────────────────────────────────────────────


def _checks(state: dict[str, Any]) -> list[dict[str, str]]:
    """Run the environment assertions; each is (name, status, detail)."""
    out: list[dict[str, str]] = []

    def add(name: str, ok: bool | None, detail: str) -> None:
        out.append(
            {"check": name, "status": "pass" if ok else ("warn" if ok is None else "fail"),
             "detail": detail}
        )

    backend = state.get("backend")
    add("backend", bool(backend) and backend != "unknown", f"active backend: {backend}")

    ephemeris = state.get("ephemeris") or {}
    if "error" in ephemeris:
        add("ephemeris data", False, f"inventory error: {ephemeris['error']}")
    elif backend == "libephemeris":
        ready = ephemeris.get("ready")
        add(
            "ephemeris data",
            bool(ready),
            f"{ephemeris.get('file_count', 0)} file(s) in {ephemeris.get('data_dir')}"
            if ready
            else f"reader not ready in {ephemeris.get('data_dir')}",
        )
    else:
        count = ephemeris.get("se1_count", 0)
        add(
            "ephemeris data",
            None if not count else True,
            f"{count} .se1 file(s) at {ephemeris.get('data_path') or 'built-in Moshier'}",
        )

    # The store holds birth data; a widened mode is worth flagging even though
    # nothing is broken.
    try:
        from kerykeion.cli import config

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
    except Exception as exc:  # pragma: no cover - defensive
        add("profile store permissions", None, f"could not stat the store: {exc}")

    # The .env trap: libephemeris loads ./.env at import, so a stray file in the
    # working directory can silently repoint the data dir or the calc mode.
    if (state.get("env") or {}).get("_cwd_env_present"):
        add(
            "working-directory .env",
            None,
            "a .env in the current directory is loaded at import and may repoint "
            "LIBEPHEMERIS_* settings",
        )

    # The one check that exercises the whole stack rather than inspecting it.
    try:
        from kerykeion import AstrologicalSubjectFactory

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="doctor", year=2000, month=1, day=1, hour=12, minute=0,
            lat=51.5, lng=-0.12, tz_str="Europe/London", online=False,
            suppress_geonames_warning=True,
        )
        sun = getattr(subject, "sun", None)
        add(
            "sample calculation",
            sun is not None and getattr(sun, "sign", None) is not None,
            f"2000-01-01 natal: Sun in {getattr(sun, 'sign', '?')}",
        )
    except Exception as exc:
        add("sample calculation", False, f"{type(exc).__name__}: {exc}")

    return out


def doctor(
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Check the install and exit non-zero if something is actually broken.

    ``status`` reports the environment; ``doctor`` judges it — same probes, plus a
    real chart calculation, plus a verdict. Warnings (a widened store mode, a
    stray ``.env``) do not fail the run; a dead backend or a calculation that
    raises does.
    """
    from kerykeion.cli import diagnostics, errors
    from kerykeion.cli.rendering import formats

    state = diagnostics.gather_status()
    checks = _checks(state)
    failed = [c for c in checks if c["status"] == "fail"]
    body = {
        "ok": not failed,
        "kerykeion_version": state.get("kerykeion_version"),
        "backend": state.get("backend"),
        "checks": checks,
    }
    if formats.resolve_format(fmt, output) == "text":
        # A diagnostic read on a terminal, not a JSON dump. The text renderer
        # prints a list of strings one per line, so hand it lines.
        marks = {"pass": "ok  ", "warn": "warn", "fail": "FAIL"}
        lines = [
            f"kerykeion {body['kerykeion_version']} — backend: {body['backend']}",
            "",
            *(f"  [{marks[c['status']]}] {c['check']}: {c['detail']}" for c in checks),
            "",
            "All checks passed." if not failed else f"{len(failed)} check(s) failed.",
        ]
        _emit(lines, fmt, output)
    else:
        _emit(body, fmt, output)
    if failed:
        raise SystemExit(int(errors.ExitCode.EPHEMERIS))
