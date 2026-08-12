# -*- coding: utf-8 -*-
"""SVG chart output.

Wired in the chart phase (renders via ``ChartDrawer.generate_svg_string``).
Until then, asking for SVG explicitly raises a clear error instead of producing
a half-built file. The dispatcher never routes a non-chart command here, so this
only fires if a user combines ``-f svg`` with a command that has no chart.
"""

from __future__ import annotations

from typing import Any

_NOT_WIRED = (
    "SVG output is produced by chart commands (natal, synastry, transit, …) "
    "with -f svg, and is wired in the chart phase of the CLI build-out."
)


def render_svg(_obj: Any) -> str:
    raise NotImplementedError(_NOT_WIRED)


def emit_svg(_obj: Any) -> None:
    raise NotImplementedError(_NOT_WIRED)
