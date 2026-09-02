# -*- coding: utf-8 -*-
"""XML output via ``kerykeion.to_context``; an unsupported model raises ``TypeError`` (exit 4) rather than switching format."""

from __future__ import annotations

from typing import Any


def render_xml(obj: Any) -> str:
    from kerykeion import to_context

    return to_context(obj)
