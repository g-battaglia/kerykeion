# -*- coding: utf-8 -*-
"""Security allowlist and target resolution for ``kerykeion call``.

The list is ``kerykeion.__all__``: anything not re-exported there is invisible
to ``call`` by construction (``call os.system`` fails before any ``getattr``).
On top: one ``.`` only, no ``_`` names, no models/exceptions/Protocols as
targets, and ``getattr_static`` lookups so no descriptor runs.
"""

from __future__ import annotations

import functools
import inspect
import types
import typing
from dataclasses import dataclass
from typing import Any, Callable, Optional

STATIC = "static"
CLASSMETHOD = "classmethod"
INSTANCE = "instance"
FUNCTION = "function"


@dataclass(frozen=True)
class ResolvedTarget:
    """A callable the dispatcher may invoke, fully described."""

    spec: str
    owner_name: str  # the __all__ name (factory or function)
    member_name: Optional[str]  # None for a bare function
    kind: str
    callable_fn: Callable[..., Any]
    needs_instance: bool
    init_params: dict[str, inspect.Parameter]  # __init__ params (instance methods only)
    method_params: dict[str, inspect.Parameter]


def _is_pydantic_model(obj: Any) -> bool:
    from pydantic import BaseModel

    return isinstance(obj, type) and issubclass(obj, BaseModel)


@functools.cache
def public_names() -> types.MappingProxyType[str, Any]:
    """The ``__all__`` names usable as a target's owner, read-only and shared.

    Exceptions and Protocols are dropped; pydantic models stay so ``--explain``
    can describe them, but :func:`resolve_target` refuses to invoke one.
    """
    import kerykeion

    out: dict[str, Any] = {}
    for name in getattr(kerykeion, "__all__", []):
        obj = getattr(kerykeion, name, None)
        if name.startswith("_") or obj is None:
            continue
        if isinstance(obj, type) and (issubclass(obj, BaseException) or getattr(obj, "_is_protocol", False)):
            continue
        out[name] = obj
    return types.MappingProxyType(out)


def _params_of(fn: Callable[..., Any]) -> dict[str, inspect.Parameter]:
    """Signature parameters with the ``from __future__`` string annotations resolved to real types (best effort)."""
    try:
        hints = typing.get_type_hints(fn, include_extras=True)
    except Exception:
        hints = {}
    return {
        name: param.replace(annotation=hints[name]) if name in hints else param
        for name, param in inspect.signature(fn).parameters.items()
    }


def _classify_member(owner: type, member: str) -> tuple[str, Callable[..., Any]]:
    """``(kind, underlying function)`` for *member* on *owner*; a missing member is invalid input, not a crash."""
    try:
        raw = inspect.getattr_static(owner, member)
    except AttributeError:
        public = sorted(m for m in dir(owner) if not m.startswith("_"))
        raise ValueError(
            f"{owner.__name__} has no public member {member!r}; "
            f"choose from: {', '.join(public[:24])}{' …' if len(public) > 24 else ''}"
        ) from None
    if isinstance(raw, staticmethod):
        return STATIC, raw.__func__
    if isinstance(raw, classmethod):
        return CLASSMETHOD, raw.__func__
    if inspect.isfunction(raw):
        first = next(iter(inspect.signature(raw).parameters), None)
        return (INSTANCE if first == "self" else STATIC), raw
    if callable(raw):
        return STATIC, raw
    raise ValueError(f"{owner.__name__}.{member} is not callable")


def resolve_target(spec: str) -> ResolvedTarget:
    """``Factory.method`` (or a bare ``function``) → :class:`ResolvedTarget`; anything off-list raises ``ValueError``."""
    if not spec or spec.startswith(("-", ".")) or spec.endswith("."):
        raise ValueError(f"invalid call target {spec!r}")
    parts = spec.split(".")
    if len(parts) > 2:
        raise ValueError(f"call target {spec!r} has more than one '.'; expected 'Factory.method' or 'function'")
    owner_name = parts[0]
    if owner_name not in public_names():
        raise ValueError(
            f"{owner_name!r} is not in the kerykeion public API; `kerykeion call` only dispatches to names in kerykeion.__all__."
        )
    owner = public_names()[owner_name]

    if len(parts) == 1:
        if isinstance(owner, type):
            raise ValueError(f"{owner_name} is a class — call a method: `kerykeion call {owner_name}.<method>`.")
        if not callable(owner):
            raise ValueError(f"{owner_name} is not callable.")
        return ResolvedTarget(spec, owner_name, None, FUNCTION, owner, False, {}, _params_of(owner))

    member = parts[1]
    if member.startswith("_"):
        raise ValueError(f"{member!r} is private; call targets must not start with '_'.")
    if not isinstance(owner, type):
        raise ValueError(f"{owner_name} is not a class, so .{member} is not a method.")
    if _is_pydantic_model(owner):
        raise ValueError(f"{owner_name} is a data model, not a factory; it has no callable methods to dispatch.")
    kind, fn = _classify_member(owner, member)
    init_params: dict[str, inspect.Parameter] = {}
    if kind == INSTANCE:
        init_params = {
            k: v
            for k, v in _params_of(owner.__init__).items()
            if k != "self" and v.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        }
    method_params = {k: v for k, v in _params_of(fn).items() if k not in ("self", "cls")}
    return ResolvedTarget(spec, owner_name, member, kind, fn, kind == INSTANCE, init_params, method_params)


def list_targets() -> list[dict[str, object]]:
    """Every dispatchable target as ``{owner, kind, members}`` — the same answer :func:`resolve_target` gives."""
    targets: list[dict[str, object]] = []
    for owner_name, owner in sorted(public_names().items()):
        if isinstance(owner, type):
            if _is_pydantic_model(owner):
                continue
            members = []
            for name in dir(owner):
                if name.startswith("_"):
                    continue
                try:
                    members.append({"name": name, "kind": _classify_member(owner, name)[0]})
                except (ValueError, AttributeError):
                    continue
            targets.append({"owner": owner_name, "kind": "class", "members": members})
        elif callable(owner):
            targets.append({"owner": owner_name, "kind": "function", "members": []})
    return targets
