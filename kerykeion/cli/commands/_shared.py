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

from datetime import datetime
from typing import Optional

from kerykeion.cli import warnings
from kerykeion.cli.rendering import formats


def _emit(
    model: object, fmt: Optional[str], output: Optional[str], opts: object = None
) -> None:
    """Resolve the format and route the payload through the warnings funnel.

    *opts* is an optional ``RenderOptions`` with the report/chart knobs; commands
    that expose none simply omit it.
    """
    warnings.output_with_warnings(
        model, formats.resolve_format(fmt, output), output, opts=opts
    )


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
        raise ValueError(
            f"expected an ISO date or datetime (YYYY-MM-DD or YYYY-MM-DDThh:mm), got {value!r}"
        ) from exc


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
                f"--aspects: {raw_orb.strip()!r} is not a number for the orb of {name!r} "
                f"(use e.g. 'trine:6')"
            ) from None
    return parsed or None


def _aspect_names(
    parsed: Optional[list[tuple[str, Optional[float]]]], context: str
) -> Optional[list[str]]:
    """Aspect names only, for the factories that take no per-aspect orb."""
    if parsed is None:
        return None
    with_orb = [name for name, orb in parsed if orb is not None]
    if with_orb:
        raise ValueError(
            f"--aspects: {context} takes aspect names without an orb; drop the ':orb' "
            f"from {with_orb[0]!r}."
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
    defaults: dict[str, float] = {
        str(entry["name"]): float(entry["orb"]) for entry in cc.ALL_ACTIVE_ASPECTS
    }
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


# The render flags every chart-producing command exposes. Declared once: the
# commands must spell them in their signatures (typer reads the signature), but
# the *set* lives here so it cannot drift command by command.
_RENDER_FLAG_NAMES = (
    "no_aspects", "max_aspects", "envelope", "theme", "chart_language", "style",
    "custom_title", "padding", "external_view", "transparent_background",
    "cusp_position_comparison", "auto_size", "degree_indicators", "aspect_icons",
    "zodiac_ring", "diurnality", "house_position_comparison", "aspect_grid_type",
    "svg_variant", "chart_settings",
)


def _render_from(scope: dict) -> object:
    """Build ``RenderOptions`` from a command's ``locals()``.

    Reading the flags out of the calling frame keeps twenty ``name=name`` lines
    out of eight command bodies. The membership check is what makes that safe:
    a renamed or dropped parameter raises here instead of silently rendering with
    the flag ignored — the exact failure mode (a flag that quietly does nothing)
    this CLI's reviews kept finding.
    """
    missing = [name for name in _RENDER_FLAG_NAMES if name not in scope]
    if missing:
        raise AssertionError(
            f"render flags absent from the command signature: {', '.join(missing)}"
        )
    return _render_opts(**{name: scope[name] for name in _RENDER_FLAG_NAMES})


def _render_opts(
    *,
    no_aspects: Optional[bool] = None,
    max_aspects: Optional[int] = None,
    envelope: Optional[bool] = None,
    theme: Optional[str] = None,
    chart_language: Optional[str] = None,
    style: Optional[str] = None,
    custom_title: Optional[str] = None,
    padding: Optional[int] = None,
    external_view: Optional[bool] = None,
    transparent_background: Optional[bool] = None,
    cusp_position_comparison: Optional[bool] = None,
    auto_size: Optional[bool] = None,
    degree_indicators: Optional[bool] = None,
    aspect_icons: Optional[bool] = None,
    zodiac_ring: Optional[bool] = None,
    diurnality: Optional[bool] = None,
    house_position_comparison: Optional[bool] = None,
    aspect_grid_type: Optional[str] = None,
    svg_variant: Optional[str] = None,
    chart_settings: Optional[str] = None,
) -> object:
    """Translate the render flags into ``RenderOptions`` (``None`` if none were given).

    The flag names and the ``ChartDrawer`` parameter names differ on purpose —
    ``--degree-indicators`` reads better than ``--show-degree-indicators``, and the
    paired ``--x/--no-x`` form needs the short stem. That translation lives **only
    here**, so a command never has to know the library's parameter spelling.
    """
    from kerykeion.cli.rendering import options as render_options

    return render_options.build(
        # ``--no-aspects`` is the negative face of ReportGenerator's
        # ``include_aspects``; not passing it must stay "not given", not False.
        include_aspects=False if no_aspects else None,
        max_aspects=max_aspects,
        envelope=envelope,
        theme=theme,
        chart_language=chart_language,
        style=style,
        custom_title=custom_title,
        padding=padding,
        external_view=external_view,
        transparent_background=transparent_background,
        show_cusp_position_comparison=cusp_position_comparison,
        auto_size=auto_size,
        show_degree_indicators=degree_indicators,
        show_aspect_icons=aspect_icons,
        show_zodiac_background_ring=zodiac_ring,
        show_diurnality=diurnality,
        show_house_position_comparison=house_position_comparison,
        double_chart_aspect_grid_type=aspect_grid_type,
        svg_variant=svg_variant,
        chart_settings=chart_settings,
    )
