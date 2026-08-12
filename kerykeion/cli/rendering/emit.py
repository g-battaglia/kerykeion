# -*- coding: utf-8 -*-
"""Dispatch an object to the right renderer and write it to stdout.

This is the single funnel every command uses once it has a result and a format.
``xml`` and ``svg`` are wired lazily so their (heavier) modules only load when
asked for: ``svg_out`` imports the ~5,700-line ``ChartDrawer``.
"""

from __future__ import annotations

from typing import Any


def render(obj: Any, fmt: str) -> str:
    """Render *obj* for *fmt* and return the string (no trailing newline)."""
    if fmt == "json":
        from kerykeion.cli.rendering.json_out import render_json

        return render_json(obj)
    if fmt == "text":
        from kerykeion.cli.rendering.text import render_text

        return render_text(obj)
    if fmt == "xml":
        from kerykeion.cli.rendering.xml_out import render_xml

        return render_xml(obj)
    if fmt == "svg":
        from kerykeion.cli.rendering.svg_out import render_svg

        return render_svg(obj)
    raise ValueError(f"unsupported format {fmt!r}")  # pragma: no cover - resolve_format guards


def emit(obj: Any, fmt: str) -> None:
    """Render *obj* for *fmt* and write the result to stdout."""
    write_output(render(obj, fmt))


def write_output(content: str, output_path: str | None = None) -> None:
    """Write *content* to stdout, or to *output_path* if given.

    A single trailing newline is ensured. Files are written UTF-8. This is the
    only place a command should touch stdout for a payload, keeping the
    "never print payloads through Rich" invariant localised.
    """
    import sys
    from pathlib import Path

    data = content if content.endswith("\n") else content + "\n"
    if output_path:
        # ``newline=""`` disables the platform default translation: on Windows
        # the default would turn every "\n" into "\r\n", corrupting byte-exact
        # JSON/SVG that pipelines, ``jq`` and hash-pinned checks compare against.
        Path(output_path).write_text(data, encoding="utf-8", newline="")
    else:
        sys.stdout.write(data)
