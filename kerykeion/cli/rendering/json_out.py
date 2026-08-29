# -*- coding: utf-8 -*-
"""JSON output: pydantic models through their own ``model_dump_json``; lists of models as arrays; anything else via ``json.dumps``."""

from __future__ import annotations

import json
from typing import Any

import pydantic


def render_json(obj: Any) -> str:
    if isinstance(obj, pydantic.BaseModel):
        return obj.model_dump_json(indent=2)
    if isinstance(obj, (list, tuple)):
        obj = [item.model_dump(mode="json") if isinstance(item, pydantic.BaseModel) else item for item in obj]
    return json.dumps(obj, indent=2, default=str)
