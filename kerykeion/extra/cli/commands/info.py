# -*- coding: utf-8 -*-
"""``kerykeion info <sub>`` and ``kerykeion doctor`` — describe and check the install.

``info`` lists what the flags accept, derived at runtime from the library (the
literal aliases, the point/star presets, the dominant strategies), so it cannot
drift from what the flags validate against. ``doctor`` is ``status`` with a
verdict: the same probes plus a real calculation, and a non-zero exit when
something is actually broken.
"""

from __future__ import annotations

import difflib
import typing
from typing import Any, Optional

import typer

from kerykeion.extra.cli.commands._shared import _emit
from kerykeion.extra.cli.options import FormatOpt, OutputOpt
from kerykeion.extra.cli.typer_app import KerykeionTyper

info_app = KerykeionTyper(
    name="info",
    help="List what the flags accept: literals, point sets, fixed stars, methods.",
    no_args_is_help=True,
    add_completion=False,
)


def _literal_tables() -> dict[str, list[str]]:
    """Every public string ``Literal`` alias in ``kerykeion.schemas.literals``, by name."""
    from kerykeion.schemas import literals as module

    tables = {}
    for name in dir(module):
        args = typing.get_args(getattr(module, name)) if not name.startswith("_") else ()
        if args and all(isinstance(arg, str) for arg in args):
            tables[name] = list(args)
    return dict(sorted(tables.items()))


@info_app.command("literals")
def literals(
    name: Optional[str] = typer.Argument(None, help="One alias to show (e.g. HousesSystemIdentifier). Omit for all."),
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """The accepted values of every literal the flags validate against."""
    tables = _literal_tables()
    if name is None:
        _emit(tables, fmt, output)
        return
    match = {key.lower(): key for key in tables}.get(name.strip().lower())
    if match is None:
        close = difflib.get_close_matches(name, list(tables), n=1)
        hint = f" (did you mean {close[0]!r}?)" if close else ""
        raise ValueError(f"no literal named {name!r}{hint}. Run `kerykeion info literals` for the list.")
    _emit({match: tables[match]}, fmt, output)


@info_app.command("points")
def points(fmt: FormatOpt = None, output: OutputOpt = None) -> None:
    """The preset names --points accepts, and what each one contains."""
    from kerykeion.extra.cli import subject_resolver

    _emit(subject_resolver._point_sets(), fmt, output)


@info_app.command("stars")
def stars(fmt: FormatOpt = None, output: OutputOpt = None) -> None:
    """The preset names --fixed-stars accepts, and what each one contains."""
    from kerykeion.extra.cli import subject_resolver

    _emit(subject_resolver._fixed_star_sets(), fmt, output)


@info_app.command("houses")
def houses(fmt: FormatOpt = None, output: OutputOpt = None) -> None:
    """What --houses accepts: the system letters (case matters: i and I differ) and the names that map to them."""
    from kerykeion.extra.cli import subject_resolver

    letters = sorted(subject_resolver.literal_values("HousesSystemIdentifier"))
    _emit({"letters": letters, "names": dict(sorted(subject_resolver._HOUSES_BY_NAME.items()))}, fmt, output)


@info_app.command("methods")
def methods(fmt: FormatOpt = None, output: OutputOpt = None) -> None:
    """Strategy/method names the technique flags accept, as the library reports them."""
    from kerykeion import DominantsFactory
    from kerykeion.extra.cli.rendering.options import SVG_VARIANTS, chart_choices

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


def _checks(state: dict[str, Any]) -> list[dict[str, str]]:
    """The environment assertions: ``ok`` True passes, False fails, None is a warning."""
    out: list[dict[str, str]] = []

    def add(name: str, ok: bool | None, detail: str) -> None:
        out.append({"check": name, "status": "pass" if ok else ("warn" if ok is None else "fail"), "detail": detail})

    backend = state.get("backend")
    add("backend", bool(backend) and backend != "unknown", f"active backend: {backend}")

    eph = state.get("ephemeris") or {}
    if "error" in eph:
        add("ephemeris data", False, f"inventory error: {eph['error']}")
    elif backend == "libephemeris":
        ready = eph.get("ready")
        detail = (
            f"{eph.get('file_count', 0)} file(s) in {eph.get('data_dir')}"
            if ready
            else f"reader not ready in {eph.get('data_dir')}"
        )
        add("ephemeris data", bool(ready), detail)
    else:
        count = eph.get("se1_count", 0)
        add(
            "ephemeris data",
            True if count else None,
            f"{count} .se1 file(s) at {eph.get('data_path') or 'built-in Moshier'}",
        )

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
            name="doctor", year=2000, month=1, day=1, hour=12, minute=0, lat=51.5, lng=-0.12, tz_str="Europe/London",
            online=False, suppress_geonames_warning=True,
        )  # fmt: skip
        sun = getattr(subject, "sun", None)
        add(
            "sample calculation",
            getattr(sun, "sign", None) is not None,
            f"2000-01-01 natal: Sun in {getattr(sun, 'sign', '?')}",
        )
    except Exception as exc:
        add("sample calculation", False, f"{type(exc).__name__}: {exc}")
    return out


def doctor(fmt: FormatOpt = None, output: OutputOpt = None) -> None:
    """Check the install and exit non-zero if something is actually broken (warnings do not fail the run)."""
    from kerykeion.extra.cli import diagnostics, errors
    from kerykeion.extra.cli.rendering import formats

    state = diagnostics.gather_status()
    checks = _checks(state)
    failed = [c for c in checks if c["status"] == "fail"]
    if formats.resolve_format(fmt, output) == "text":
        marks = {"pass": "ok  ", "warn": "warn", "fail": "FAIL"}
        lines = [
            f"kerykeion {state.get('kerykeion_version')} — backend: {state.get('backend')}",
            "",
            *(f"  [{marks[c['status']]}] {c['check']}: {c['detail']}" for c in checks),
            "",
            "All checks passed." if not failed else f"{len(failed)} check(s) failed.",
        ]
        _emit(lines, fmt, output)
    else:
        body = {
            "ok": not failed,
            "kerykeion_version": state.get("kerykeion_version"),
            "backend": state.get("backend"),
            "checks": checks,
        }
        _emit(body, fmt, output)
    if failed:
        raise SystemExit(int(errors.ExitCode.EPHEMERIS))
