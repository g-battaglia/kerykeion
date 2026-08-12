# -*- coding: utf-8 -*-
"""XML output via :func:`kerykeion.to_context`.

``to_context`` accepts a different (and non-containing) model set than
``ReportGenerator``. On an unsupported model it raises ``TypeError``; we let it
propagate so the command layer can surface it as a real error (exit 4 with the
list of supported types) rather than silently switching formats — a surprise
format change would break pipelines.
"""

from __future__ import annotations

import sys
from typing import Any


def render_xml(obj: Any) -> str:
    """Serialise *obj* to the ``to_context`` XML string (raises TypeError)."""
    from kerykeion import to_context

    return to_context(obj)


def emit_xml(obj: Any) -> None:
    """Write *obj* as XML to stdout, with a trailing newline."""
    sys.stdout.write(render_xml(obj))
    sys.stdout.write("\n")
