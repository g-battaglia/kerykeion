# -*- coding: utf-8 -*-
"""Human-readable text output.

For the models :class:`~kerykeion.ReportGenerator` supports, the report is the
verbatim ASCII report from the library — the CLI must never reflow it, so it
goes to stdout through :func:`sys.stdout.write`, not ``rich.Console.print``.

For anything else (models the report generator does not cover, plain dicts,
lists of small models) we degrade to a generic renderer rather than crash: the
``call`` dispatcher relies on a text path that always produces *something*
legible for any factory's return value.
"""

from __future__ import annotations

from typing import Any

import pydantic

from kerykeion.cli.rendering.json_out import render_json


def _try_report(model: pydantic.BaseModel, opts: Any = None) -> str | None:
    """The ASCII report for *model*, or ``None`` if the generator rejects it.

    ``ReportGenerator`` is typed for a narrow union of chart/technique models,
    but here we pass an arbitrary model *on purpose* — this is a runtime probe:
    accept-or-reject is exactly the question. The single ``type: ignore``
    encodes that deliberate widening; we never assume success and fall back to
    JSON on ``TypeError``/``ValueError``.

    *opts* carries ``--no-aspects`` / ``--max-aspects``; only the ones given are
    forwarded, so with no options the call is the plain ``ReportGenerator(model)``.
    """
    from kerykeion import ReportGenerator

    kwargs = opts.report_kwargs() if opts is not None else {}
    try:
        return ReportGenerator(model, **kwargs).generate_report()  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def render_text(obj: Any, opts: Any = None) -> str:
    """Render *obj* as text; never raises on an unsupported shape."""
    if isinstance(obj, pydantic.BaseModel):
        report = _try_report(obj, opts)
        if report is not None:
            return report
    if isinstance(obj, (list, tuple)) and obj and all(isinstance(item, pydantic.BaseModel) for item in obj):
        # One blank-line-separated block per item — readable in a terminal yet
        # greppable. The first line of each item is the model class for context.
        blocks = []
        for item in obj:
            cls = type(item).__name__
            report = _try_report(item, opts)
            if report is not None:
                blocks.append(f"# {cls}\n{report}")
            else:
                blocks.append(f"# {cls}\n{render_json(item)}")
        return "\n\n".join(blocks)
    if isinstance(obj, (list, tuple)) and all(isinstance(item, str) for item in obj):
        # A plain list of names (e.g. ``subject list``) reads best one per line.
        return "\n".join(obj)
    return render_json(obj)
