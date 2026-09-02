# -*- coding: utf-8 -*-
"""Output: which format, and the payload rendered in it.

Format resolution: ``-f`` → the ``-o`` suffix → ``$KERYKEION_CLI_FORMAT`` →
text on a TTY, JSON when piped. Payloads go to stdout through
``sys.stdout.write``, verbatim: no wrapping, no colour. Every renderer that
needs the library imports it on the call, so this module loads on its own.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import pydantic

VALID_FORMATS = ("text", "json", "xml", "svg")
_SUFFIX_FORMATS = {"svg": "svg", "json": "json", "xml": "xml", "txt": "text", "text": "text"}


def stdout_is_tty() -> bool:
    """True when stdout is a terminal; the one seam the tests pin to flip the default format."""
    isatty = getattr(sys.stdout, "isatty", None)
    return bool(isatty()) if isatty is not None else False


def suffix_format(output_path: str) -> str | None:
    """A format inferred from an ``-o`` path's extension, if recognised."""
    return _SUFFIX_FORMATS.get(Path(output_path).suffix.lower().lstrip("."))


def resolve_format(explicit: str | None, output_path: str | None) -> str:
    if explicit:
        if explicit not in VALID_FORMATS:
            raise ValueError(f"unknown format {explicit!r}; choose from {', '.join(VALID_FORMATS)}")
        return explicit
    inferred = suffix_format(output_path) if output_path else None
    env = os.environ.get("KERYKEION_CLI_FORMAT")
    return inferred or (env if env in VALID_FORMATS else None) or ("text" if stdout_is_tty() else "json")


def render_json(obj: Any) -> str:
    """Pydantic models through their own ``model_dump_json``; lists of models as arrays; anything else via ``json.dumps``."""
    if isinstance(obj, pydantic.BaseModel):
        return obj.model_dump_json(indent=2)
    if isinstance(obj, (list, tuple)):
        obj = [item.model_dump(mode="json") if isinstance(item, pydantic.BaseModel) else item for item in obj]
    return json.dumps(obj, indent=2, default=str)


def _report(model: pydantic.BaseModel, opts: Any = None) -> str | None:
    """The ASCII report for *model*, or ``None`` if ``ReportGenerator`` rejects it (a runtime probe, on purpose)."""
    from kerykeion import ReportGenerator

    try:
        return ReportGenerator(model, **(opts.report_kwargs() if opts is not None else {})).generate_report()  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def render_text(obj: Any, opts: Any = None) -> str:
    """The library's own report where it supports the model, verbatim; JSON otherwise, so ``call`` always has a legible text path."""
    if isinstance(obj, pydantic.BaseModel):
        report = _report(obj, opts)
        return render_json(obj) if report is None else report
    if isinstance(obj, (list, tuple)) and obj and all(isinstance(item, pydantic.BaseModel) for item in obj):
        # One block per item, headed by its model class; readable yet greppable.
        return "\n\n".join(f"# {type(item).__name__}\n{_report(item, opts) or render_json(item)}" for item in obj)
    if isinstance(obj, (list, tuple)) and all(isinstance(item, str) for item in obj):
        return "\n".join(obj)  # a plain list of names (``subject list``), one per line
    return render_json(obj)


def render_xml(obj: Any) -> str:
    """``kerykeion.to_context``; an unsupported model raises ``TypeError`` (exit 4) rather than switching format."""
    from kerykeion import to_context

    return to_context(obj)


def render_svg(obj: Any, opts: Any = None) -> str:
    """A chart-data model through ``ChartDrawer.generate_*_svg_string`` — never ``save_svg``, which writes into the home directory."""
    from kerykeion import ChartDrawer, KerykeionException
    from kerykeion.extra.cli.render_options import SVG_VARIANTS

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


def render(obj: Any, fmt: str, opts: Any = None) -> str:
    """Render *obj* for *fmt* (no trailing newline); *opts* carries the report/chart knobs."""
    if fmt == "json":
        return render_json(obj)
    if fmt == "text":
        return render_text(obj, opts)
    if fmt == "xml":
        return render_xml(obj)
    return render_svg(obj, opts)


def write_output(content: str, output_path: str | None = None) -> None:
    """Write *content* (one trailing newline ensured) to stdout, or UTF-8 to *output_path*, creating its directory."""
    data = content if content.endswith("\n") else content + "\n"
    if not output_path:
        sys.stdout.write(data)
        return
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data, encoding="utf-8", newline="")  # no CRLF translation: byte-exact JSON/SVG
