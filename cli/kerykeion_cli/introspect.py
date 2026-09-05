# -*- coding: utf-8 -*-
"""Type coercion and parameter description for ``kerykeion call``.

:func:`coerce_value` turns a CLI string into a parameter's annotated type;
:func:`explain` classifies each parameter (``cli`` / ``json-only`` /
``subject`` / ``unsupported``) so ``--explain`` says up front what a target
accepts. Subject parameters are bound from ``-s <profile>``, never parsed.
"""

from __future__ import annotations

import collections.abc
import difflib
import inspect
import json
import os
import types
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal, Union, get_args, get_origin

CLI = "cli"
JSON_ONLY = "json-only"
SUBJECT = "subject"
UNSUPPORTED = "unsupported"

_SCALARS = (bool, int, float, str, datetime, date)
_NO_MATCH = object()
# Abstract origins a comma-separated value satisfies (the API annotates several
# parameters ``Sequence[str]``); they cannot be instantiated, so they become a list.
_SEQUENCE_ORIGINS = (
    collections.abc.Sequence,
    collections.abc.MutableSequence,
    collections.abc.Iterable,
    collections.abc.Collection,
)


@dataclass(frozen=True)
class ParamInfo:
    name: str
    annotation: str
    classification: str
    default: str  # "<required>" or the repr of the default

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "annotation": self.annotation, "cli": self.classification, "default": self.default}


def _is_union(annotation: Any) -> bool:
    """``typing.Union`` and PEP 604 ``X | Y`` alike."""
    return get_origin(annotation) in (Union, types.UnionType)


def _union_args(annotation: Any) -> list[Any]:
    return [a for a in get_args(annotation) if a is not type(None)]


def _strip_optional(annotation: Any) -> Any:
    if _is_union(annotation) and len(_union_args(annotation)) == 1:
        return _union_args(annotation)[0]
    return annotation


def _is_subject(annotation: Any) -> bool:
    """A subject binding site: the subject model, or a Union with it as one arm (``AstrologicalSubjectModel | …``)."""
    if getattr(annotation, "__name__", None) == "AstrologicalSubjectModel":
        return True
    return _is_union(annotation) and any(_is_subject(arg) for arg in get_args(annotation))


def _is_pydantic_model(annotation: Any) -> bool:
    from pydantic import BaseModel

    return isinstance(annotation, type) and issubclass(annotation, BaseModel)


def _annotation_name(annotation: Any) -> str:
    if annotation is inspect.Parameter.empty:
        return "any"
    return annotation.__name__ if isinstance(annotation, type) else str(annotation).replace("typing.", "")


def coerce_scalar(raw: str) -> Any:
    """Best-effort scalar coercion: true/false, none/null, int, float, else the string (shared with ``--set``)."""
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"none", "null"}:
        return None
    for cast in (int, float):
        try:
            return cast(raw)
        except ValueError:
            pass
    return raw


def _coerce_bool(raw: str) -> Any:
    if raw.lower() in {"true", "yes", "1"}:
        return True
    if raw.lower() in {"false", "no", "0"}:
        return False
    return _NO_MATCH


def _coerce_literal(choices: list[Any], raw: str) -> Any:
    """A Literal member by value *and* type: ``1`` reaches ``Literal[1]`` as an int, and ``True``/``1`` do not collide."""
    if raw in choices:
        return raw
    for member in choices:
        if isinstance(member, bool):
            coerced = _coerce_bool(raw)
        elif isinstance(member, (int, float)):
            try:
                coerced = type(member)(raw)
            except ValueError:
                coerced = _NO_MATCH
        else:
            coerced = _NO_MATCH
        if coerced is not _NO_MATCH and coerced == member and type(coerced) is type(member):
            return coerced
    suggest = difflib.get_close_matches(raw, [str(c) for c in choices], n=1)
    hint = f" (did you mean {suggest[0]!r}?)" if suggest else ""
    raise ValueError(f"{raw!r} is not a valid choice; choose from {choices}{hint}")


def coerce_value(annotation: Any, raw: str) -> Any:
    """Coerce the CLI string *raw* to *annotation*; a clearly wrong value raises ``ValueError``.

    Unknown structural types fall through to the raw string — the library then
    validates it, which is the safest default.
    """
    # Preserve the None arm long enough to recognise an explicit null. Stripping
    # Optional first would send e.g. Optional[int] + "none" through int().
    if (
        _is_union(annotation)
        and type(None) in get_args(annotation)
        and raw.lower() in {"none", "null"}
    ):
        return None
    annotation = _strip_optional(annotation)
    if annotation is inspect.Parameter.empty or annotation is Any:
        return coerce_scalar(raw)
    origin = get_origin(annotation)
    if _is_union(annotation):  # int | float and friends: the first member that accepts the value wins
        last_error: Exception | None = None
        for arg in _union_args(annotation):
            try:
                return coerce_value(arg, raw)
            except (ValueError, TypeError) as exc:
                last_error = exc
        names = [_annotation_name(a) for a in _union_args(annotation)]
        raise ValueError(f"{raw!r} matches none of {names}") from last_error
    if origin is Literal:
        return _coerce_literal([a for a in get_args(annotation) if not isinstance(a, type)], raw)
    if annotation is bool:
        value = _coerce_bool(raw)
        if value is _NO_MATCH:
            raise ValueError(f"{raw!r} is not a boolean; use true/false.")
        return value
    if annotation in (int, float, str):
        return annotation(raw)
    if annotation in (datetime, date):
        return annotation.fromisoformat(raw)
    if origin in (list, set, frozenset) or origin in _SEQUENCE_ORIGINS:
        factory = origin if origin in (list, set, frozenset) else list
        (inner,) = get_args(annotation) or (str,)
        return factory(coerce_value(inner, p.strip()) for p in raw.split(",") if p.strip())
    if origin is tuple:
        inner = get_args(annotation)
        parts = [p.strip() for p in raw.split(",")]
        if inner and ... not in inner:
            if len(parts) != len(inner):
                raise ValueError(f"expected {len(inner)} comma-separated values, got {len(parts)}")
            return tuple(coerce_value(t, p) for t, p in zip(inner, parts))
        return tuple(parts)
    if annotation is dict or origin in (dict, collections.abc.Mapping):  # --param custom_weights='{"Sun": 1.5}'
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{raw!r} is not valid JSON for a mapping parameter") from exc
        if not isinstance(parsed, dict):
            raise ValueError(f"{raw!r} parsed to a {type(parsed).__name__}, not a JSON object")
        return parsed
    if _is_pydantic_model(annotation):
        if not os.path.isfile(raw):
            raise ValueError(
                f"parameter of type {annotation.__name__} needs a path to a JSON file (got {raw!r}); "
                "produce one with the matching command and -f json, then pass its path here."
            )
        with open(raw, encoding="utf-8") as fh:
            return annotation.model_validate_json(fh.read())
    return raw


def _classify(annotation: Any) -> str:
    annotation = _strip_optional(annotation)
    if annotation is inspect.Parameter.empty or annotation is Any:
        return CLI
    if _is_subject(annotation):
        return SUBJECT
    if _is_pydantic_model(annotation):
        return JSON_ONLY
    origin = get_origin(annotation)
    if _is_union(annotation):
        arms = _union_args(annotation)
        return CLI if all(a in _SCALARS or get_origin(a) is Literal for a in arms) else JSON_ONLY
    if origin is Literal or annotation in _SCALARS:
        return CLI
    if origin in (list, set, frozenset, tuple) or origin in _SEQUENCE_ORIGINS:
        return CLI
    return JSON_ONLY  # Mapping / TypedDict / Protocol / custom: --param key='{...}'


def explain(target) -> list[ParamInfo]:  # type: ignore[no-untyped-def]
    """Describe every parameter of a resolved target (init + method)."""
    out: list[ParamInfo] = []
    for name, param in {**target.init_params, **target.method_params}.items():
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        out.append(
            ParamInfo(
                name=name,
                annotation=_annotation_name(param.annotation),
                classification=_classify(param.annotation),
                default="<required>" if param.default is inspect.Parameter.empty else repr(param.default),
            )
        )
    return out
