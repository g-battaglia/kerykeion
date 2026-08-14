# -*- coding: utf-8 -*-
"""Dispatch an object to the right renderer, and write rendered output.

:func:`render` turns an object into a string for a format; :func:`write_output`
puts that string on stdout or into ``-o``'s file. Commands never call the
per-format renderers directly — routing everything through this pair is what
keeps ``-o`` handling and the warnings funnel in one place (a helper that wrote
straight to ``sys.stdout`` would silently bypass both).

``xml`` and ``svg`` are wired lazily so their (heavier) modules only load when
asked for: ``svg_out`` imports the ~5,700-line ``ChartDrawer``.
"""

from __future__ import annotations

from typing import Any


def render(obj: Any, fmt: str, opts: Any = None) -> str:
    """Render *obj* for *fmt* and return the string (no trailing newline).

    *opts* is an optional :class:`~kerykeion.cli.rendering.options.RenderOptions`
    carrying the report/chart knobs. It defaults to ``None`` — "no options given"
    — so every caller that does not care keeps working unchanged.
    """
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
    """Write *content* to stdout, or to *output_path* if given.

    A single trailing newline is ensured. Files are written UTF-8. This is the
    only place a command should touch stdout for a payload, keeping the
    "never print payloads through Rich" invariant localised.
    """
    import sys
    from pathlib import Path

    data = content if content.endswith("\n") else content + "\n"
    if output_path:
        target = Path(output_path)
        # Create the parent directory so `-o path/in/a/new/dir/out.json` works,
        # mirroring ``profiles.save()`` (which mkdirs its parent). Without this a
        # missing directory raised FileNotFoundError → exit 4 "invalid input",
        # a confusing label for a normal create-on-write expectation.
        target.parent.mkdir(parents=True, exist_ok=True)
        # ``newline=""`` disables the platform default translation: on Windows
        # the default would turn every "\n" into "\r\n", corrupting byte-exact
        # JSON/SVG that pipelines, ``jq`` and hash-pinned checks compare against.
        target.write_text(data, encoding="utf-8", newline="")
    else:
        sys.stdout.write(data)
