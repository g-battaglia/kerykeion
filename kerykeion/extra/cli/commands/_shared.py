# -*- coding: utf-8 -*-
"""Helpers shared across the command modules — everything a command would otherwise repeat.

A leaf module: it imports the CLI ``options``/``warnings``/``formats`` helpers
and the stdlib, never another command module, so importing it cannot cycle.
"""

from __future__ import annotations

import functools
import inspect
import typing
from datetime import datetime
from typing import Any, Callable, Optional, TypeVar

from kerykeion.extra.cli import options, warnings
from kerykeion.extra.cli.rendering import formats

_C = TypeVar("_C", bound=Callable[..., Any])


def _emit(model: object, fmt: Optional[str], output: Optional[str], opts: object = None) -> None:
    """Resolve the format and route the payload through the warnings funnel."""
    warnings.output_with_warnings(model, formats.resolve_format(fmt, output), output, opts=opts)


def _given(**flags: Any) -> dict[str, Any]:
    """The flags actually given, keyed by the library parameter they feed; ``None`` lets the library default decide."""
    return {name: value for name, value in flags.items() if value is not None}


def _stored_subject(spec: Optional[str], cmd: str, flag: str = "-s", **flags: Any):
    """The stored subject a command names with ``-s`` (or ``-S``), or a usable error."""
    if not spec:
        raise ValueError(f"{cmd} needs {flag} <profile>")
    from kerykeion.extra.cli import subject_resolver

    return subject_resolver.resolve_subject(subject_resolver.SubjectFlags(**flags), spec)


def _split_csv(values: Optional[list[str]]) -> Optional[list[str]]:
    """Flatten a repeatable option that may also carry comma-separated tokens."""
    if values is None:
        return None
    out = [part.strip() for item in values for part in item.split(",") if part.strip()]
    return out or None


def _parse_dt(value: str) -> datetime:
    """Parse an ISO date or datetime, with a usable error otherwise."""
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"expected an ISO date or datetime (YYYY-MM-DD or YYYY-MM-DDThh:mm), got {value!r}") from exc


def _choose(value: object, allowed: tuple[str, ...], label: str) -> object:
    """Validate an enum-style flag case-insensitively, returning the canonical form."""
    if value is None:
        return None
    canonical = {choice.lower(): choice for choice in allowed}
    if str(value).strip().lower() not in canonical:
        raise ValueError(f"--{label} must be {' or '.join(allowed)}, got {value!r}")
    return canonical[str(value).strip().lower()]


# ── --aspects: one syntax for the two shapes the library asks for ────────────
# A plain list of names (mundane, solar arc, primary directions) or a list of
# {name, orb} records (AspectsFactory). The optional ``:orb`` suffix is what the
# second shape needs and the first cannot use, so _aspect_names refuses it by name.


def _parse_aspects(values: Optional[list[str]]) -> Optional[list[tuple[str, Optional[float]]]]:
    """``--aspects`` tokens of ``name`` or ``name:orb`` → ``[(name, orb-or-None), …]``."""
    tokens = _split_csv(values)
    if tokens is None:
        return None
    parsed: list[tuple[str, Optional[float]]] = []
    for token in tokens:
        name, sep, raw_orb = token.partition(":")
        if not name.strip():
            raise ValueError(f"--aspects: empty aspect name in {token!r}")
        if not sep:
            parsed.append((name.strip(), None))
            continue
        try:
            parsed.append((name.strip(), float(raw_orb)))
        except ValueError:
            raise ValueError(
                f"--aspects: {raw_orb.strip()!r} is not a number for the orb of {name.strip()!r} (use e.g. 'trine:6')"
            ) from None
    return parsed or None


def _aspect_names(parsed: Optional[list[tuple[str, Optional[float]]]], context: str) -> Optional[list[str]]:
    """Aspect names only, for the factories that take no per-aspect orb."""
    if parsed is None:
        return None
    with_orb = [name for name, orb in parsed if orb is not None]
    if with_orb:
        raise ValueError(
            f"--aspects: {context} takes aspect names without an orb; drop the ':orb' from {with_orb[0]!r}."
        )
    return [name for name, _ in parsed]


def _active_aspects(parsed: Optional[list[tuple[str, Optional[float]]]]) -> Optional[list[dict[str, object]]]:
    """``ActiveAspect`` records; an omitted orb takes the library's own default."""
    if parsed is None:
        return None
    from kerykeion.settings import config_constants as cc

    defaults = {str(entry["name"]): float(entry["orb"]) for entry in cc.ALL_ACTIVE_ASPECTS}
    out: list[dict[str, object]] = []
    for name, orb in parsed:
        if orb is None and name not in defaults:
            raise ValueError(
                f"--aspects: unknown aspect {name!r}; choose from {', '.join(sorted(defaults))} "
                "(or give an explicit orb, 'name:6')."
            )
        out.append({"name": name, "orb": defaults[name] if orb is None else orb})
    return out


# ── Signature helpers: the shared flag sets are declared once, here ──────────
# typer builds a command from its signature, so the commands must spell the
# flags; these keep the *set* in one place and turn a dropped flag into a loud
# failure instead of one that quietly does nothing.

_SUBJECT_FLAGS = (
    "name", "date", "time", "seconds", "iso_utc", "lat", "lng", "tz", "city", "nation", "online", "offline",
    "altitude", "zodiac", "sidereal_mode", "houses", "perspective", "points", "fixed_stars", "with_flags",
    "without_flags", "set_flags",
)  # fmt: skip


def _subject_from(scope: dict, **overrides: object):
    """``SubjectFlags`` from a command's ``locals()``; *overrides* replace flags the command does not expose."""
    from kerykeion.extra.cli import subject_resolver

    missing = [name for name in _SUBJECT_FLAGS if name not in scope and name not in overrides]
    if missing:
        raise AssertionError(f"subject flags absent from the command signature: {', '.join(missing)}")
    given: dict[str, Any] = {**{name: scope.get(name) for name in _SUBJECT_FLAGS}, **overrides}
    for name in ("with_flags", "without_flags", "set_flags"):  # repeatable options arrive as None
        given[name] = given[name] or []
    return subject_resolver.SubjectFlags(**given)


# CLI flag → (option alias, library parameter). Flag and parameter differ where
# the flag reads better short and where the paired --x/--no-x form needs the
# bare stem; ``no_aspects`` (the negative face of ``include_aspects``) is
# translated in _render_options instead.
_RENDER_FLAGS: dict[str, tuple[Any, Optional[str]]] = {
    "no_aspects": (options.NoAspectsFlag, None),
    "max_aspects": (options.MaxAspectsOpt, "max_aspects"),
    "envelope": (options.EnvelopeFlag, "envelope"),
    "theme": (options.ThemeOpt, "theme"),
    "chart_language": (options.ChartLanguageOpt, "chart_language"),
    "style": (options.ChartStyleOpt, "style"),
    "custom_title": (options.CustomTitleOpt, "custom_title"),
    "padding": (options.PaddingOpt, "padding"),
    "external_view": (options.ExternalViewFlag, "external_view"),
    "transparent_background": (options.TransparentBackgroundFlag, "transparent_background"),
    "cusp_position_comparison": (options.CuspComparisonFlag, "show_cusp_position_comparison"),
    "auto_size": (options.AutoSizeFlag, "auto_size"),
    "degree_indicators": (options.DegreeIndicatorsFlag, "show_degree_indicators"),
    "aspect_icons": (options.AspectIconsFlag, "show_aspect_icons"),
    "zodiac_ring": (options.ZodiacRingFlag, "show_zodiac_background_ring"),
    "diurnality": (options.DiurnalityFlag, "show_diurnality"),
    "house_position_comparison": (options.HousePositionComparisonFlag, "show_house_position_comparison"),
    "aspect_grid_type": (options.AspectGridTypeOpt, "double_chart_aspect_grid_type"),
    "svg_variant": (options.SvgVariantOpt, "svg_variant"),
    "chart_settings": (options.ChartSettingsOpt, "chart_settings"),
}


def _render_options(given: dict[str, Any]) -> object:
    """The render flags → ``RenderOptions`` (``None`` if none were given)."""
    from kerykeion.extra.cli.rendering import options as render_options

    kwargs = {param: given[flag] for flag, (_, param) in _RENDER_FLAGS.items() if param}
    kwargs["include_aspects"] = False if given["no_aspects"] else None  # not passing it stays "not given"
    return render_options.build(**kwargs)


def with_render_flags(command: _C) -> _C:
    """Append the shared report/chart flags to *command*'s signature and hand it the assembled ``RenderOptions``.

    The decorated function declares its own flags plus ``*, opts: object = None``.
    Annotations are resolved here, in the command's own module: with
    ``from __future__ import annotations`` the signature carries strings that
    typer could not resolve from this module and would silently turn into bare,
    help-less flags.
    """
    hints = typing.get_type_hints(command, include_extras=True)
    signature = inspect.signature(command)
    own = [
        p.replace(annotation=hints.get(name, p.annotation))
        for name, p in signature.parameters.items()
        if name != "opts"
    ]
    injected = [
        inspect.Parameter(flag, inspect.Parameter.KEYWORD_ONLY, default=None, annotation=alias)
        for flag, (alias, _) in _RENDER_FLAGS.items()
    ]

    @functools.wraps(command)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        given = {flag: kwargs.pop(flag, None) for flag in _RENDER_FLAGS}
        return command(*args, **kwargs, opts=_render_options(given))

    wrapper.__signature__ = signature.replace(parameters=[*own, *injected])  # type: ignore[attr-defined]
    wrapper.__annotations__ = {
        **{p.name: p.annotation for p in own},
        **{flag: alias for flag, (alias, _) in _RENDER_FLAGS.items()},
        "return": None,
    }
    return wrapper  # type: ignore[return-value]
