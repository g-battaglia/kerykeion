# -*- coding: utf-8 -*-
"""The knobs a command hands to the renderers.

:class:`RenderOptions` is one frozen value threaded from the command down to
``rendering.render``. Every field is ``Optional`` and ``None`` means "the user did
not ask": the ``*_kwargs`` helpers drop those, so the library's own defaults
decide and the CLI never restates a default it would have to keep in sync.
"""

from __future__ import annotations

import functools
import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Optional

# ``--chart-settings file.json`` keys: whitelisted so a typo is an error, not a silently ignored section.
CHART_SETTINGS_KEYS = ("colors_settings", "celestial_points_settings", "aspects_settings", "language_pack")

# ``--svg-variant`` → the ChartDrawer method that renders the string.
SVG_VARIANTS = {
    "full": "generate_svg_string",
    "wheel": "generate_wheel_only_svg_string",
    "aspect-grid": "generate_aspect_grid_only_svg_string",
}


@dataclass(frozen=True)
class RenderOptions:
    """Report and chart knobs for one render. ``None`` everywhere = library defaults."""

    # report (text)
    include_aspects: Optional[bool] = None
    max_aspects: Optional[int] = None
    # chart (svg) — named exactly as the ChartDrawer constructor parameters
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

    def chart_kwargs(self) -> dict[str, Any]:
        """ChartDrawer kwargs for the options actually given."""
        skip = {"include_aspects", "max_aspects", "svg_variant", "chart_settings"}
        kwargs = {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if f.name not in skip and getattr(self, f.name) is not None
        }
        kwargs.update(self.chart_settings or {})  # already whitelisted against CHART_SETTINGS_KEYS
        return kwargs

    def report_kwargs(self) -> dict[str, Any]:
        """ReportGenerator kwargs for the options actually given."""
        return {
            k: v
            for k, v in (("include_aspects", self.include_aspects), ("max_aspects", self.max_aspects))
            if v is not None
        }


@functools.cache
def chart_choices(param: str) -> tuple[str, ...]:
    """The values a ChartDrawer ``Literal`` parameter accepts, read from its signature so the CLI is never stricter.

    ``get_type_hints`` rather than the raw signature: ``chart_drawer`` uses
    ``from __future__ import annotations``, and an unevaluated forward-ref has
    no args — every value would be rejected.
    """
    import inspect
    import typing

    from kerykeion import ChartDrawer

    try:
        annotation = typing.get_type_hints(ChartDrawer.__init__)[param]
    except Exception:  # pragma: no cover
        annotation = inspect.signature(ChartDrawer.__init__).parameters[param].annotation
    found: list[str] = []

    def walk(node: Any) -> None:
        for arg in typing.get_args(node):
            if isinstance(arg, str):
                found.append(arg)
            elif typing.get_args(arg):
                walk(arg)  # Optional[Literal[...]] and friends

    walk(annotation)
    return tuple(found)


def _validate_choice(value: Optional[str], param: str, flag: str) -> Optional[str]:
    """Case-insensitive match against a ChartDrawer Literal's members."""
    if value is None:
        return None
    canonical = {choice.lower(): choice for choice in chart_choices(param)}
    match = canonical.get(str(value).strip().lower())
    if match is None:
        raise ValueError(f"{flag} must be one of {', '.join(sorted(canonical.values()))}, got {value!r}")
    return match


def read_chart_settings(path: Optional[str]) -> Optional[dict[str, Any]]:
    """``--chart-settings``: a JSON object of whitelisted sections, mapping sections merged over the library defaults.

    ChartDrawer wants complete settings: a partial palette would die on the
    first missing key deep inside the renderer, while overriding one colour is
    exactly what a user means. List sections (point/aspect tables) are replaced.
    """
    if path is None:
        return None
    try:
        data = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"--chart-settings: cannot read {path!r} ({exc.strerror})") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"--chart-settings: {path!r} is not valid JSON ({exc.msg})") from None
    if not isinstance(data, dict):
        raise ValueError(
            f"--chart-settings: {path!r} must hold a JSON object with any of: {', '.join(CHART_SETTINGS_KEYS)}"
        )
    unknown = [k for k in data if k not in CHART_SETTINGS_KEYS]
    if unknown:
        raise ValueError(
            f"--chart-settings: unknown key {unknown[0]!r}; valid keys are {', '.join(CHART_SETTINGS_KEYS)}"
        )
    import inspect

    from kerykeion import ChartDrawer

    params = inspect.signature(ChartDrawer.__init__).parameters
    merged: dict[str, Any] = {}
    for key, value in data.items():
        default = params[key].default if key in params else None
        merged[key] = {**default, **value} if isinstance(default, dict) and isinstance(value, dict) else value
    return merged


def build(**flags: Any) -> Optional[RenderOptions]:
    """:class:`RenderOptions` from a command's flags, or ``None`` if none were given."""
    variant = flags.pop("svg_variant", None)
    if variant is not None and variant not in SVG_VARIANTS:
        raise ValueError(f"--svg-variant must be one of {', '.join(sorted(SVG_VARIANTS))}, got {variant!r}")
    resolved = {
        **flags,
        "theme": _validate_choice(flags.get("theme"), "theme", "--theme"),
        "chart_language": _validate_choice(flags.get("chart_language"), "chart_language", "--chart-language"),
        "style": _validate_choice(flags.get("style"), "style", "--style"),
        "double_chart_aspect_grid_type": _validate_choice(
            flags.get("double_chart_aspect_grid_type"), "double_chart_aspect_grid_type", "--aspect-grid-type"
        ),
        "chart_settings": read_chart_settings(flags.get("chart_settings")),
        "svg_variant": variant,
    }
    return None if all(value is None for value in resolved.values()) else RenderOptions(**resolved)
