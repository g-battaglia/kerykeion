# -*- coding: utf-8 -*-
"""Human-readable text: the library's own ASCII report where ``ReportGenerator`` supports the model, JSON otherwise.

The report is written verbatim (never reflowed). Anything the generator
rejects degrades to a generic rendering rather than a crash, so the ``call``
dispatcher always has a legible text path.
"""

from __future__ import annotations

from typing import Any

import pydantic

from kerykeion.extra.cli.rendering.json_out import render_json


def _report(model: pydantic.BaseModel, opts: Any = None) -> str | None:
    """The ASCII report for *model*, or ``None`` if the generator rejects it (a runtime probe, on purpose)."""
    from kerykeion import ReportGenerator

    try:
        return ReportGenerator(model, **(opts.report_kwargs() if opts is not None else {})).generate_report()  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def render_text(obj: Any, opts: Any = None) -> str:
    """Render *obj* as text; never raises on an unsupported shape."""
    if isinstance(obj, pydantic.BaseModel):
        report = _report(obj, opts)
        return render_json(obj) if report is None else report
    if isinstance(obj, (list, tuple)) and obj and all(isinstance(item, pydantic.BaseModel) for item in obj):
        # One block per item, headed by its model class; readable yet greppable.
        return "\n\n".join(f"# {type(item).__name__}\n{_report(item, opts) or render_json(item)}" for item in obj)
    if isinstance(obj, (list, tuple)) and all(isinstance(item, str) for item in obj):
        return "\n".join(obj)  # a plain list of names (``subject list``), one per line
    return render_json(obj)
