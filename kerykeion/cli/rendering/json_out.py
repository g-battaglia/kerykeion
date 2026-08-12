# -*- coding: utf-8 -*-
"""JSON output.

Pydantic models serialise with their own ``model_dump_json`` (honours their
``model_config``, excludes ``None`` where the model asks for it, and round-trips
datetime/Decimal correctly). Lists of models become a JSON array. Anything else
falls back to :func:`json.dumps` with ``default=str``.
"""

from __future__ import annotations

import json
import sys
from typing import Any

import pydantic


def render_json(obj: Any) -> str:
    """Serialise *obj* to a pretty JSON string."""
    if isinstance(obj, pydantic.BaseModel):
        return obj.model_dump_json(indent=2)
    if isinstance(obj, (list, tuple)):
        items = [
            item.model_dump(mode="json") if isinstance(item, pydantic.BaseModel) else item
            for item in obj
        ]
        return json.dumps(items, indent=2, default=str)
    return json.dumps(obj, indent=2, default=str)


def emit_json(obj: Any) -> None:
    """Write *obj* as JSON to stdout, with a trailing newline."""
    sys.stdout.write(render_json(obj))
    sys.stdout.write("\n")
