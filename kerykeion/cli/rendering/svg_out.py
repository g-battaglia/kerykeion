# -*- coding: utf-8 -*-
"""SVG chart output via :class:`kerykeion.ChartDrawer`.

The drawer accepts a ``ChartDataModel`` (single or dual — discriminated by its
``chart_type``) and returns an SVG string from ``generate_svg_string()``. We
**never** call ``save_svg()``: with ``output_path=None`` it writes into
``Path.home()`` under a derived name *and* prints a line to stdout, which would
both surprise the user and pollute a piped payload. We render to a string and
let :func:`kerykeion.cli.rendering.emit.write_output` handle the file/stdout
choice — exactly like the other formats.

A non-chart object (a plain subject, a summary dict, …) has no ``chart_type``;
asking for SVG there is a user error, surfaced as a clean message.
"""

from __future__ import annotations

from typing import Any


def render_svg(obj: Any) -> str:
    """Render *obj* (a ChartDataModel) to an SVG string via ChartDrawer."""
    from kerykeion import ChartDrawer, KerykeionException

    if not hasattr(obj, "chart_type"):
        raise KerykeionException(
            "SVG output needs a chart-data model, which only the chart commands "
            "(natal, synastry, transit, composite, return, progression) produce."
        )
    # ChartDrawer fixes theme/language/palette at construction. We expose the
    # common ones as CLI flags later; the defaults ("classic"/"EN"/"modern")
    # match what the library itself uses out of the box.
    return ChartDrawer(obj).generate_svg_string()


