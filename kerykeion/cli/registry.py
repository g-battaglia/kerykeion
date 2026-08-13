# -*- coding: utf-8 -*-
"""Security allowlist and target resolution for ``kerykeion call``.

``call`` exposes the library to arbitrary invocation, so the first question is
not "can we call it?" but "is it on the list?". The list is derived from
``kerykeion.__all__`` — anything not re-exported there is invisible to ``call``
by construction. That is what makes ``call os.system`` fail: ``os`` is not in
``__all__``, so it is rejected before any ``getattr`` runs.

On top of the allowlist:

* split a target on **one** ``.`` only — ``a.b.c`` is refused (no chained
  attribute access into nested objects);
* names and members starting with ``_`` are private — refused;
* Pydantic models, exceptions and Protocols are excluded as *call targets*
  (they are data shapes or contracts, not things you invoke);
* attribute lookup uses :func:`inspect.getattr_static` so no descriptor
  (``property``, custom ``__getattr__``) is triggered by the lookup itself.
"""

from __future__ import annotations

import functools
import inspect
from dataclasses import dataclass
from typing import Any, Callable, Optional

# Target kinds, in the order we detect them.
STATIC = "static"
CLASSMETHOD = "classmethod"
INSTANCE = "instance"
FUNCTION = "function"  # a bare top-level function, not a method


@dataclass(frozen=True)
class ResolvedTarget:
    """A callable the dispatcher may invoke, fully described."""

    spec: str
    owner_name: str  # the __all__ name (factory or function)
    member_name: Optional[str]  # None for a bare function
    kind: str  # one of the constants above
    callable_fn: Callable[..., Any]  # the underlying function to call
    needs_instance: bool  # True for instance methods
    init_params: dict[str, inspect.Parameter]  # __init__ params (instance only)
    method_params: dict[str, inspect.Parameter]  # the call signature


def _is_pydantic_model(obj: Any) -> bool:
    try:
        from pydantic import BaseModel
    except Exception:  # pragma: no cover
        return False
    return isinstance(obj, type) and issubclass(obj, BaseModel)


def _is_exception(obj: Any) -> bool:
    return isinstance(obj, type) and issubclass(obj, BaseException)


def _is_protocol(obj: Any) -> bool:
    return isinstance(obj, type) and bool(getattr(obj, "_is_protocol", False))


@functools.cache
def public_names() -> dict[str, Any]:
    """The ``__all__`` names usable as the *owner* of a call target.

    Excludes exceptions and Protocols outright. Pydantic models are kept in the
    map (so ``--explain`` can describe them) but :func:`resolve_target` refuses
    to invoke a bare model.
    """
    import kerykeion

    out: dict[str, Any] = {}
    for name in getattr(kerykeion, "__all__", []):
        if name.startswith("_"):
            continue
        obj = getattr(kerykeion, name, None)
        if obj is None:
            continue
        if _is_exception(obj) or _is_protocol(obj):
            continue
        out[name] = obj
    return out


def _params_of(fn: Callable[..., Any]) -> dict[str, inspect.Parameter]:
    """Signature parameters with annotations resolved to real types.

    The factory modules use ``from __future__ import annotations``, so the raw
    signature carries string forward-refs (``"AstrologicalSubjectModel"``) that
    our classifier cannot match. ``get_type_hints`` resolves them against the
    function's own module globals; on any resolution failure we fall back to
    the raw signature so a single unresolvable type never breaks the whole call.
    """
    import typing

    sig = inspect.signature(fn)
    try:
        hints = typing.get_type_hints(fn, include_extras=True)
    except Exception:
        hints = {}
    params: dict[str, inspect.Parameter] = {}
    for name, param in sig.parameters.items():
        if name in hints:
            param = param.replace(annotation=hints[name])
        params[name] = param
    return params


def _classify_member(owner: type, member: str) -> tuple[str, Callable[..., Any]]:
    """Return (kind, underlying_function) for *member* on *owner*.

    Uses ``getattr_static`` so we see the raw descriptor without triggering it.
    Raises :class:`ValueError` (→ clean exit 4) for a missing member rather than
    letting the ``AttributeError`` from ``getattr_static`` fall through to
    :func:`errors.classify`, which does not list it and would exit 1 ("a bug").
    """
    try:
        raw = inspect.getattr_static(owner, member)
    except AttributeError:
        public = sorted(m for m in dir(owner) if not m.startswith("_"))
        raise ValueError(
            f"{owner.__name__} has no public member {member!r}; "
            f"choose from: {', '.join(public[:24])}{' …' if len(public) > 24 else ''}"
        ) from None
    if isinstance(raw, staticmethod):
        return STATIC, raw.__func__  # type: ignore[attr-defined]
    if isinstance(raw, classmethod):
        return CLASSMETHOD, raw.__func__  # type: ignore[attr-defined]
    if inspect.isfunction(raw):
        sig = inspect.signature(raw)
        first = next(iter(sig.parameters), None)
        return (INSTANCE if first == "self" else STATIC), raw
    # callables like a plain object with __call__ — rare; treat as instance-less.
    if callable(raw):
        return STATIC, raw  # type: ignore[return-value]
    raise ValueError(f"{owner.__name__}.{member} is not callable")


def resolve_target(spec: str) -> ResolvedTarget:
    """Turn ``Factory.method`` (or a bare ``function``) into a ResolvedTarget.

    Raises :class:`ValueError` with a precise message for anything off-list,
    private, or shaped wrong — the error boundary turns that into exit 4.
    """
    if not spec or spec.startswith(("-", ".")) or spec.endswith("."):
        raise ValueError(f"invalid call target {spec!r}")
    parts = spec.split(".")
    if len(parts) > 2:
        raise ValueError(
            f"call target {spec!r} has more than one '.'; expected 'Factory.method' or 'function'"
        )

    names = public_names()
    owner_name = parts[0]
    if owner_name not in names:
        # The headline security guarantee: anything not in __all__ is refused.
        raise ValueError(
            f"{owner_name!r} is not in the kerykeion public API; "
            "`kerykeion call` only dispatches to names in kerykeion.__all__."
        )
    owner = names[owner_name]

    # Bare function target (no member).
    if len(parts) == 1:
        if isinstance(owner, type):
            raise ValueError(
                f"{owner_name} is a class — call a method: `kerykeion call {owner_name}.<method>`."
            )
        if not callable(owner):
            raise ValueError(f"{owner_name} is not callable.")
        return ResolvedTarget(
            spec=spec, owner_name=owner_name, member_name=None, kind=FUNCTION,
            callable_fn=owner, needs_instance=False, init_params={}, method_params=_params_of(owner),
        )

    member = parts[1]
    if member.startswith("_"):
        raise ValueError(f"{member!r} is private; call targets must not start with '_'.")
    if not isinstance(owner, type):
        raise ValueError(f"{owner_name} is not a class, so .{member} is not a method.")
    if _is_pydantic_model(owner):
        raise ValueError(
            f"{owner_name} is a data model, not a factory; it has no callable methods to dispatch."
        )

    kind, fn = _classify_member(owner, member)
    init_params: dict[str, inspect.Parameter] = {}
    needs_instance = kind == INSTANCE
    if needs_instance:
        init_sig = getattr(owner, "__init__", None)
        if init_sig is not None:
            init_params = {
                k: v for k, v in _params_of(init_sig).items() if k != "self" and v.kind not in (
                    inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD
                )
            }
    return ResolvedTarget(
        spec=spec, owner_name=owner_name, member_name=member, kind=kind,
        callable_fn=fn, needs_instance=needs_instance, init_params=init_params,
        method_params={
            k: v for k, v in _params_of(fn).items() if k not in ("self", "cls")
        },
    )
