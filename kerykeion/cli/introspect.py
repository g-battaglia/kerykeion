# -*- coding: utf-8 -*-
"""Type coercion and parameter description for ``kerykeion call``.

Two jobs:

* :func:`coerce_value` turns a CLI string into the parameter's annotated Python
  type. The common scalars are exact; container types (``list``, ``Literal``,
  ``datetime``) are handled; anything we cannot name safely stays a string and
  the caller treats that as best-effort.
* :func:`explain` classifies each parameter as ``cli`` / ``json-only`` /
  ``subject`` / ``unsupported`` so ``--explain`` can tell the user up front what
  a target accepts, instead of failing mid-call.

The annotations come from :func:`inspect.signature` (the resolver already
unwrapped ``self``). :class:`AstrologicalSubjectModel` parameters are marked
``subject``: they are bound from ``-s <profile>`` by the command, never from a
raw string.
"""

from __future__ import annotations

import collections.abc
import inspect
import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal, Union, get_args, get_origin

# Parameter classes for --explain.
CLI = "cli"
JSON_ONLY = "json-only"
SUBJECT = "subject"
UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ParamInfo:
    name: str
    annotation: str
    classification: str
    default: str  # "<required>" or the repr of the default

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "annotation": self.annotation,
            "cli": self.classification,
            "default": self.default,
        }


def _strip_optional(annotation: Any) -> Any:
    """Unwrap ``Optional[X]`` / ``Union[X, None]`` → ``X`` (best effort)."""
    origin = get_origin(annotation)
    if origin is Union:
        args = [a for a in get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


def _is_subject(annotation: Any) -> bool:
    if getattr(annotation, "__name__", None) == "AstrologicalSubjectModel":
        return True
    # A subject parameter is frequently typed as a Union of the subject-like
    # models — ``AstrologicalSubjectModel | CompositeSubjectModel |
    # PlanetReturnModel`` (see ``kerykeion/aspects/factory.py``). A Union has no
    # ``__name__``, so the plain check above misses it and the parameter would be
    # misclassified JSON_ONLY, breaking ``call -s`` for every such target. Treat
    # a Union as a subject binding site when any arm is one.
    origin = get_origin(annotation)
    if origin is Union:
        return any(_is_subject(arg) for arg in get_args(annotation))
    return False


def _is_pydantic_model(annotation: Any) -> bool:
    try:
        from pydantic import BaseModel
    except Exception:  # pragma: no cover
        return False
    return isinstance(annotation, type) and issubclass(annotation, BaseModel)


def _annotation_name(annotation: Any) -> str:
    if annotation is inspect.Parameter.empty:
        return "any"
    if isinstance(annotation, type):
        return annotation.__name__
    return str(annotation).replace("typing.", "")


def coerce_value(annotation: Any, raw: str) -> Any:
    """Coerce the CLI string *raw* to *annotation*.

    Raises :class:`ValueError` on a clearly wrong value (bad Literal, bad int,
    unparseable datetime). Unknown / structural types fall through to the raw
    string — the library then validates it, which is the safest default.
    """
    annotation = _strip_optional(annotation)
    if annotation is inspect.Parameter.empty or annotation is Any:
        return _coerce_scalar(raw)

    origin = get_origin(annotation)
    if origin is Union:
        # A multi-type union like ``int | float`` (after Optional stripping):
        # try each member until one accepts the value.
        args = [a for a in get_args(annotation) if a is not type(None)]
        last_error: Exception | None = None
        for arg in args:
            try:
                return coerce_value(arg, raw)
            except (ValueError, TypeError) as exc:
                last_error = exc
        raise ValueError(
            f"{raw!r} matches none of {[_annotation_name(a) for a in args]}"
        ) from last_error
    if origin is Literal:
        choices = [a for a in get_args(annotation) if not isinstance(a, type)]
        if raw in choices:
            return raw
        import difflib

        suggest = difflib.get_close_matches(raw, [str(c) for c in choices], n=1)
        hint = f" (did you mean {suggest[0]!r}?)" if suggest else ""
        raise ValueError(f"{raw!r} is not a valid choice; choose from {choices}{hint}")
    if annotation is bool:
        if raw.lower() in {"true", "yes", "1"}:
            return True
        if raw.lower() in {"false", "no", "0"}:
            return False
        raise ValueError(f"{raw!r} is not a boolean; use true/false.")
    if annotation is int:
        return int(raw)
    if annotation is float:
        return float(raw)
    if annotation is str:
        return raw
    if annotation is datetime:
        return datetime.fromisoformat(raw)
    if annotation is date:
        return date.fromisoformat(raw)
    if origin in (list, set, frozenset):
        (inner,) = get_args(annotation) or (str,)
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        return origin(coerce_value(inner, p) for p in parts)
    if origin is tuple:
        inner = get_args(annotation)
        parts = [p.strip() for p in raw.split(",")]
        if inner and ... not in inner:
            if len(parts) != len(inner):
                raise ValueError(f"expected {len(inner)} comma-separated values, got {len(parts)}")
            return tuple(coerce_value(t, p) for t, p in zip(inner, parts))
        return tuple(parts)
    if annotation is dict or origin in (dict, collections.abc.Mapping):
        # Structural params like ``custom_weights: Dict[str, float]``: parse the
        # raw value as JSON so ``--param custom_weights='{"sun":1.5}'`` reaches
        # the factory as a dict instead of the literal string (which the factory
        # would reject with a confusing TypeError). ``--explain`` already marks
        # these ``json-only``; this is the coercion that honours that hint.
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{raw!r} is not valid JSON for a mapping parameter") from exc
        if not isinstance(parsed, dict):
            raise ValueError(f"{raw!r} parsed to a {type(parsed).__name__}, not a JSON object")
        return parsed
    if _is_pydantic_model(annotation):
        return _load_model_file(annotation, raw)
    # Unknown structural type (Mapping, TypedDict, Protocol, custom class): leave
    # as a string and let the library validate. Json for the complex ones.
    return raw


def _coerce_scalar(raw: str) -> Any:
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def _load_model_file(model: Any, raw: str) -> Any:
    import os

    if not os.path.isfile(raw):
        raise ValueError(
            f"parameter of type {model.__name__} needs a path to a JSON file (got {raw!r}); "
            "produce one with the matching command and -f json, then pass its path here."
        )
    with open(raw, encoding="utf-8") as fh:
        return model.model_validate_json(fh.read())


def _classify(annotation: Any) -> str:
    annotation = _strip_optional(annotation)
    if annotation is inspect.Parameter.empty or annotation is Any:
        return CLI
    if _is_subject(annotation):
        return SUBJECT
    if _is_pydantic_model(annotation):
        return JSON_ONLY
    origin = get_origin(annotation)
    if origin is Literal:
        return CLI
    if origin is Union:
        args = [a for a in get_args(annotation) if a is not type(None)]
        if all(
            a in (bool, int, float, str, datetime, date) or get_origin(a) is Literal for a in args
        ):
            return CLI
        return JSON_ONLY
    if annotation in (bool, int, float, str, datetime, date):
        return CLI
    if origin in (list, set, frozenset, tuple):
        return CLI
    # Mapping / TypedDict / Protocol / custom: we forward the raw string; mark
    # json-only so --explain tells the user to use --param key='{...}' JSON.
    return JSON_ONLY


def explain(target) -> list[ParamInfo]:  # type: ignore[no-untyped-def]
    """Describe every parameter of a resolved target (init + method)."""
    out: list[ParamInfo] = []
    seen: set[str] = set()

    def _add(name: str, param: inspect.Parameter) -> None:
        if name in seen or param.kind in (
            inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD
        ):
            return
        seen.add(name)
        annotation = param.annotation
        out.append(
            ParamInfo(
                name=name,
                annotation=_annotation_name(annotation),
                classification=_classify(annotation),
                default="<required>" if param.default is inspect.Parameter.empty else repr(param.default),
            )
        )

    for name, param in target.init_params.items():
        _add(name, param)
    for name, param in target.method_params.items():
        _add(name, param)
    return out
