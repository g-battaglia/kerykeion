# -*- coding: utf-8 -*-
"""Dispatch an object to the right renderer, and write the rendered output.

Commands never call the per-format renderers directly: routing everything
through this pair keeps ``-o`` handling and the warnings funnel in one place.
``svg`` loads lazily — it imports the ~5,700-line ``ChartDrawer``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


def render(obj: Any, fmt: str, opts: Any = None) -> str:
    """Render *obj* for *fmt* (no trailing newline); *opts* carries the report/chart knobs."""
    if fmt == "json":
        from kerykeion.cli.rendering.json_out import render_json

        return render_json(obj)
    if fmt == "text":
        from kerykeion.cli.rendering.text import render_text

        return render_text(obj, opts)
    if fmt == "xml":
        from kerykeion.cli.rendering.xml_out import render_xml

        return render_xml(obj)
    if fmt == "svg":
        from kerykeion.cli.rendering.svg_out import render_svg

        return render_svg(obj, opts)
    raise ValueError(f"unsupported format {fmt!r}")  # pragma: no cover - resolve_format guards


def write_output(content: str, output_path: str | None = None) -> None:
    """Write *content* (one trailing newline ensured) to stdout, or UTF-8 to *output_path*, creating its directory."""
    data = content if content.endswith("\n") else content + "\n"
    if not output_path:
        sys.stdout.write(data)
        return
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data, encoding="utf-8", newline="")  # no CRLF translation: byte-exact JSON/SVG
