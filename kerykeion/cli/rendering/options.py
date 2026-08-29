# -*- coding: utf-8 -*-
"""The knobs a command hands to the renderers.

Rendering used to take only ``(obj, fmt)``, which is why the report and chart
options were never wired: there was nowhere to put them. :class:`RenderOptions`
is that place — one frozen value object threaded from the command down to
:func:`kerykeion.cli.rendering.emit.render`.

**Every field is ``Optional`` and defaults to ``None``, and ``None`` means "the
user did not ask".** The ``*_kwargs`` helpers below drop those fields entirely
rather than forwarding them, so the library's own defaults decide — the CLI
never restates a default it would then have to keep in sync. This is the same
discipline :func:`kerykeion.cli.subject_resolver._kwargs_for` applies to the
subject factories.
"""

from __future__ import annotations

import functools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

# ChartDrawer parameters we expose one-to-one as flags. The names match the
# constructor exactly, so the mapping is the identity — no translation table to
# drift. Structural settings (palettes, point/aspect tables, language packs)
# arrive as a whole file instead; see ``chart_settings``.
_CHART_FIELDS = (
    "theme",
    "chart_language",
    "style",
    "custom_title",
    "padding",
    "external_view",
    "transparent_background",
    "auto_size",
    "show_degree_indicators",
    "show_aspect_icons",
    "show_zodiac_background_ring",
    "show_diurnality",
    "show_house_position_comparison",
    "show_cusp_position_comparison",
    "double_chart_aspect_grid_type",
)

# The keys ``--chart-settings file.json`` may carry. Whitelisted so a typo is an
# error naming the valid keys, not a silently ignored section.
CHART_SETTINGS_KEYS = (
    "colors_settings",
    "celestial_points_settings",
    "aspects_settings",
    "language_pack",
)

# ``--svg-variant`` picks which ChartDrawer method renders the string.
SVG_VARIANTS = {
    "full": "generate_svg_string",
    "wheel": "generate_wheel_only_svg_string",
    "aspect-grid": "generate_aspect_grid_only_svg_string",
}


@dataclass(frozen=True)
class RenderOptions:
    """Report and chart knobs for one render. ``None`` everywhere = library defaults."""

    # ── report (text format) ──
    include_aspects: Optional[bool] = None
    max_aspects: Optional[int] = None

    # ── chart (svg format) ──
    theme: Optional[str] = None
    chart_language: Optional[str] = None
    style: Optional[str] = None
    custom_title: Optional[str] = None
    padding: Optional[int] = None
    external_view: Optional[bool] = None
    transparent_background: Optional[bool] = None
    auto_size: Optional[bool] = None
    show_degree_indicators: Optional[bool] = None
    show_aspect_icons: Optional[bool] = None
    show_zodiac_background_ring: Optional[bool] = None
    show_diurnality: Optional[bool] = None
    show_house_position_comparison: Optional[bool] = None
    show_cusp_position_comparison: Optional[bool] = None
    double_chart_aspect_grid_type: Optional[str] = None
    svg_variant: Optional[str] = None
    chart_settings: Optional[dict[str, Any]] = None

    # ── payload shape ──
    envelope: Optional[bool] = None

    def chart_kwargs(self) -> dict[str, Any]:
        """ChartDrawer kwargs for the options actually given (others omitted)."""
        kwargs: dict[str, Any] = {
            name: getattr(self, name) for name in _CHART_FIELDS if getattr(self, name) is not None
        }
        if self.chart_settings:
            # Already whitelisted against CHART_SETTINGS_KEYS when the file was
            # read, so this cannot smuggle an arbitrary constructor argument.
            kwargs.update(self.chart_settings)
        return kwargs

    def report_kwargs(self) -> dict[str, Any]:
        """ReportGenerator kwargs for the options actually given."""
        kwargs: dict[str, Any] = {}
        if self.include_aspects is not None:
            kwargs["include_aspects"] = self.include_aspects
        if self.max_aspects is not None:
            kwargs["max_aspects"] = self.max_aspects
        return kwargs


@functools.cache
def chart_choices(param: str) -> tuple[str, ...]:
    """The values a ChartDrawer ``Literal`` parameter accepts, read from its signature.

    Read, never transcribed: a hand-copied list would silently reject a value the
    library added (the CLI must not be stricter than the library it drives), and
    ``info literals`` shows the same source.

    Resolution goes through :func:`typing.get_type_hints`, not the raw signature:
    ``chart_drawer`` uses ``from __future__ import annotations``, so some
    parameters carry an *unevaluated string* forward-ref (``style`` is annotated
    ``KerykeionChartStyle``) whose ``get_args`` is empty — which would present as
    "no valid values" and reject everything. Same trap, same remedy as
    :func:`kerykeion.cli.registry._params_of`; the raw signature is the fallback.
    """
    import inspect
    import typing

    from kerykeion import ChartDrawer

    try:
        annotation = typing.get_type_hints(ChartDrawer.__init__)[param]
    except Exception:  # pragma: no cover - defensive; falls back to the raw form
        annotation = inspect.signature(ChartDrawer.__init__).parameters[param].annotation
    found: list[str] = []

    def walk(node: Any) -> None:
        for arg in typing.get_args(node):
            if isinstance(arg, str):
                found.append(arg)
            elif typing.get_args(arg):
                walk(arg)  # unwrap Optional[Literal[...]] and friends

    walk(annotation)
    return tuple(found)


def _validate_choice(value: Optional[str], param: str, flag: str) -> Optional[str]:
    """Case-insensitively match *value* against a ChartDrawer Literal's members."""
    if value is None:
        return None
    canonical = {choice.lower(): choice for choice in chart_choices(param)}
    match = canonical.get(str(value).strip().lower())
    if match is None:
        raise ValueError(f"{flag} must be one of {', '.join(sorted(canonical.values()))}, got {value!r}")
    return match


def read_chart_settings(path: Optional[str]) -> Optional[dict[str, Any]]:
    """Load ``--chart-settings``: a JSON object with a whitelisted set of keys."""
    if path is None:
        return None
    try:
        raw = Path(path).expanduser().read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"--chart-settings: cannot read {path!r} ({exc.strerror})") from None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--chart-settings: {path!r} is not valid JSON ({exc.msg})") from None
    if not isinstance(data, dict):
        raise ValueError(
            f"--chart-settings: {path!r} must hold a JSON object with any of: {', '.join(CHART_SETTINGS_KEYS)}"
        )
    unknown = [k for k in data if k not in CHART_SETTINGS_KEYS]
    if unknown:
        # Named, not ignored: a typoed section that silently does nothing is the
        # failure mode this whitelist exists to prevent.
        raise ValueError(
            f"--chart-settings: unknown key {unknown[0]!r}; valid keys are {', '.join(CHART_SETTINGS_KEYS)}"
        )
    return _merge_over_defaults(data)


def _merge_over_defaults(data: dict[str, Any]) -> dict[str, Any]:
    """Overlay the user's sections on the library's own defaults.

    ChartDrawer wants **complete** settings: handing it ``{"paper_0": "#101010"}``
    as ``colors_settings`` replaces the whole palette and the drawer then dies on
    the first key it cannot find (``KeyError: 'zodiac_icon_0'``) — deep inside the
    renderer, far from the flag that caused it. Overriding one colour is the
    obvious thing a user means by a settings file, so mapping sections are merged
    over the defaults read from the constructor's own signature.

    List-shaped sections (the point and aspect tables) are *replaced*, not merged:
    they are ordered records with no key to merge on, so a partial list can only
    mean "use exactly these".
    """
    import inspect

    from kerykeion import ChartDrawer

    params = inspect.signature(ChartDrawer.__init__).parameters
    merged: dict[str, Any] = {}
    for key, value in data.items():
        default = params[key].default if key in params else None
        if isinstance(default, dict) and isinstance(value, dict):
            merged[key] = {**default, **value}
        else:
            merged[key] = value
    return merged


def build(**flags: Any) -> Optional[RenderOptions]:
    """Build :class:`RenderOptions` from a command's flags, or ``None`` if none were given.

    Returning ``None`` when nothing was passed keeps the "no options" path
    byte-identical to the behaviour before the knobs existed.
    """
    settings = read_chart_settings(flags.pop("chart_settings", None))
    variant = flags.pop("svg_variant", None)
    if variant is not None and variant not in SVG_VARIANTS:
        raise ValueError(f"--svg-variant must be one of {', '.join(sorted(SVG_VARIANTS))}, got {variant!r}")
    resolved = {
        "theme": _validate_choice(flags.pop("theme", None), "theme", "--theme"),
        "chart_language": _validate_choice(flags.pop("chart_language", None), "chart_language", "--chart-language"),
        "style": _validate_choice(flags.pop("style", None), "style", "--style"),
        "double_chart_aspect_grid_type": _validate_choice(
            flags.pop("double_chart_aspect_grid_type", None),
            "double_chart_aspect_grid_type",
            "--aspect-grid-type",
        ),
        "chart_settings": settings,
        "svg_variant": variant,
        **flags,
    }
    if all(value is None for value in resolved.values()):
        return None
    return RenderOptions(**resolved)
