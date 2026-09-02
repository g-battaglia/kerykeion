# -*- coding: utf-8 -*-
"""SVG chart output via ``ChartDrawer.generate_*_svg_string`` — never ``save_svg``, which writes into the home directory and prints to stdout."""

from __future__ import annotations

from typing import Any


def render_svg(obj: Any, opts: Any = None) -> str:
    """Render a ``ChartDataModel`` to an SVG string; only the options actually given reach the drawer."""
    from kerykeion import ChartDrawer, KerykeionException
    from kerykeion.extra.cli.rendering.options import SVG_VARIANTS

    if not hasattr(obj, "chart_type"):
        raise KerykeionException(
            "SVG output needs a chart-data model, which only the chart commands "
            "(natal, synastry, transit, composite, return, progression) produce."
        )
    variant = (getattr(opts, "svg_variant", None) or "full") if opts is not None else "full"
    if variant not in SVG_VARIANTS:
        raise ValueError(f"--svg-variant must be one of {', '.join(sorted(SVG_VARIANTS))}, got {variant!r}")
    drawer = ChartDrawer(obj, **(opts.chart_kwargs() if opts is not None else {}))
    return getattr(drawer, SVG_VARIANTS[variant])()
