# -*- coding: utf-8 -*-
"""Small helpers shared across the command modules.

These are the trivial compositions every command would otherwise duplicate
verbatim: resolving the output format and routing the payload through the
warnings funnel (:func:`_emit`), flattening a repeatable/CSV option
(:func:`_split_csv`), and parsing an ISO date/datetime (:func:`_parse_dt`).
Kept here so a behaviour change (e.g. a newly accepted datetime form) lands in
exactly one place rather than five.

This module is a leaf: it imports only the CLI ``warnings``/``formats`` helpers
and the stdlib, never another command module, so importing it can never cycle.
"""

from __future__ import annotations

import functools
import inspect
import typing
from datetime import datetime
from typing import Any, Callable, Optional, TypeVar

from kerykeion.cli import options, warnings
from kerykeion.cli.rendering import formats

_C = TypeVar("_C", bound=Callable[..., Any])


def _emit(model: object, fmt: Optional[str], output: Optional[str], opts: object = None) -> None:
    """Resolve the format and route the payload through the warnings funnel.

    *opts* is an optional ``RenderOptions`` with the report/chart knobs; commands
    that expose none simply omit it.
    """
    warnings.output_with_warnings(model, formats.resolve_format(fmt, output), output, opts=opts)


def _given(**flags: Any) -> dict[str, Any]:
    """The flags actually given, keyed by the library parameter they feed.

    ``None`` means "not asked for", so it is dropped and the library's own
    default decides — the CLI never restates a default it would have to keep in
    sync. This is the command-level twin of
    :func:`kerykeion.cli.subject_resolver._kwargs_for`.
    """
    return {name: value for name, value in flags.items() if value is not None}


def _split_csv(values: Optional[list[str]]) -> Optional[list[str]]:
    """Flatten a repeatable option that may also carry comma-separated tokens."""
    if values is None:
        return None
    out: list[str] = []
    for item in values:
        out.extend(part.strip() for part in item.split(",") if part.strip())
    return out or None


def _parse_dt(value: str) -> datetime:
    """Parse an ISO date or datetime, with a usable error otherwise."""
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"expected an ISO date or datetime (YYYY-MM-DD or YYYY-MM-DDThh:mm), got {value!r}") from exc


def _parse_aspects(values: Optional[list[str]]) -> Optional[list[tuple[str, Optional[float]]]]:
    """Parse ``--aspects``: repeatable/CSV tokens of ``name`` or ``name:orb``.

    The library asks for aspects in two shapes — a plain list of names
    (``MundaneAspectFactory``, ``SolarArcFactory``, primary directions) and a
    list of ``ActiveAspect`` ``{name, orb}`` records (``AspectsFactory``). One
    flag, one syntax: the optional ``:orb`` suffix is what the second shape needs
    and the first cannot use, so :func:`_aspect_names` rejects it explicitly
    rather than dropping it. Two meanings for one flag name is precisely what the
    reviews of this CLI kept having to undo.
    """
    tokens = _split_csv(values)
    if tokens is None:
        return None
    parsed: list[tuple[str, Optional[float]]] = []
    for token in tokens:
        name, sep, raw_orb = token.partition(":")
        name = name.strip()
        if not name:
            raise ValueError(f"--aspects: empty aspect name in {token!r}")
        if not sep:
            parsed.append((name, None))
            continue
        try:
            parsed.append((name, float(raw_orb)))
        except ValueError:
            raise ValueError(
                f"--aspects: {raw_orb.strip()!r} is not a number for the orb of {name!r} (use e.g. 'trine:6')"
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


def _active_aspects(
    parsed: Optional[list[tuple[str, Optional[float]]]],
) -> Optional[list[dict[str, object]]]:
    """``ActiveAspect`` records; an omitted orb takes the library's own default."""
    if parsed is None:
        return None
    from kerykeion.settings import config_constants as cc

    # str keys on purpose: the user's token is an arbitrary string until it has
    # been checked against this table, which is exactly what the lookup below is.
    defaults: dict[str, float] = {str(entry["name"]): float(entry["orb"]) for entry in cc.ALL_ACTIVE_ASPECTS}
    out: list[dict[str, object]] = []
    for name, orb in parsed:
        if orb is None:
            if name not in defaults:
                raise ValueError(
                    f"--aspects: unknown aspect {name!r}; choose from "
                    f"{', '.join(sorted(defaults))} (or give an explicit orb, 'name:6')."
                )
            orb = defaults[name]
        out.append({"name": name, "orb": orb})
    return out


def _choose(value: object, allowed: tuple[str, ...], label: str) -> object:
    """Validate an enum-style flag case-insensitively, returning the canonical form.

    The rest of the CLI normalises case (``--zodiac tropical``, ``--houses
    PLACIDUS``, ``--points ALL``), so these flags must too: rejecting
    ``--lot Fortune`` while accepting ``--zodiac Tropical`` is one CLI with two
    rules.
    """
    if value is None:
        return None
    v = str(value).strip().lower()
    canonical = {choice.lower(): choice for choice in allowed}
    if v not in canonical:
        raise ValueError(f"--{label} must be {' or '.join(allowed)}, got {value!r}")
    return canonical[v]


# The subject flags a command must spell to build a subject inline. Same
# discipline as _RENDER_FLAGS below: the names live here, the commands spell
# them, and :func:`_subject_from` checks that the two still agree.
_SUBJECT_FLAGS = (
    "name",
    "date",
    "time",
    "seconds",
    "iso_utc",
    "lat",
    "lng",
    "tz",
    "city",
    "nation",
    "online",
    "offline",
    "altitude",
    "zodiac",
    "sidereal_mode",
    "houses",
    "perspective",
    "points",
    "fixed_stars",
    "with_flags",
    "without_flags",
    "set_flags",
)


def _subject_from(scope: dict, **overrides: object):
    """Build ``SubjectFlags`` from a command's ``locals()``.

    *overrides* replaces a flag the command does not expose — ``now`` has no
    ``--date``/``--time`` and passes ``mode_override="current"`` instead.
    """
    from kerykeion.cli import subject_resolver

    missing = [name for name in _SUBJECT_FLAGS if name not in scope and name not in overrides]
    if missing:
        raise AssertionError(f"subject flags absent from the command signature: {', '.join(missing)}")
    given = {name: scope.get(name) for name in _SUBJECT_FLAGS}
    return subject_resolver.build_flags(**{**given, **overrides})


# Every report/chart flag a chart-producing command exposes: the CLI flag name,
# the option alias typer reads, and the library parameter it feeds. One
# declaration for all three — adding a knob is one line here, and it appears on
# every decorated command at once.
#
# Flag and parameter names differ where the flag reads better short
# (``--degree-indicators`` over ``--show-degree-indicators``, and the paired
# ``--x/--no-x`` form needs the bare stem). ``no_aspects`` is the odd one out —
# the negative face of a positive library parameter — so it is translated in
# :func:`_render_options` rather than through this table.
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
    "house_position_comparison": (
        options.HousePositionComparisonFlag,
        "show_house_position_comparison",
    ),
    "aspect_grid_type": (options.AspectGridTypeOpt, "double_chart_aspect_grid_type"),
    "svg_variant": (options.SvgVariantOpt, "svg_variant"),
    "chart_settings": (options.ChartSettingsOpt, "chart_settings"),
}


def _render_options(given: dict[str, Any]) -> object:
    """Translate the render flags into ``RenderOptions`` (``None`` if none were given)."""
    from kerykeion.cli.rendering import options as render_options

    kwargs = {param: given[flag] for flag, (_, param) in _RENDER_FLAGS.items() if param}
    # ``--no-aspects`` is the negative face of ReportGenerator's
    # ``include_aspects``; not passing it must stay "not given", not False.
    kwargs["include_aspects"] = False if given["no_aspects"] else None
    return render_options.build(**kwargs)


def with_render_flags(command: _C) -> _C:
    """Give *command* the shared report/chart flags without spelling them out.

    Typer builds a command from its signature, so the twenty render flags have to
    *be* in that signature — but repeating them across eight commands is eight
    places to forget one, which is how a flag ends up quietly doing nothing. This
    appends them from :data:`_RENDER_FLAGS` and hands the command what it
    actually wants: the assembled ``RenderOptions``, as a keyword-only ``opts``.

    The decorated function therefore declares ``*, opts: object = None`` and its
    own flags, nothing else.
    """
    # ``get_type_hints``, not the raw signature: the command modules use
    # ``from __future__ import annotations``, so ``inspect.signature`` hands back
    # the *string* "SubjectProfile" — which typer would then try to resolve in
    # this module, where the alias does not exist, and silently fall back to a
    # bare ``--profile`` flag with no help. Resolving here, in the command's own
    # module namespace, keeps every flag exactly as declared.
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
    # Typer resolves annotations through ``get_type_hints`` on some paths, which
    # reads ``__annotations__`` rather than the signature; keep the two in step.
    wrapper.__annotations__ = {
        **{p.name: p.annotation for p in own},
        **{flag: alias for flag, (alias, _) in _RENDER_FLAGS.items()},
        "return": None,
    }
    return wrapper  # type: ignore[return-value]
