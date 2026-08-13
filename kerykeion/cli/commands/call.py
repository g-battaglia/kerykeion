# -*- coding: utf-8 -*-
"""``kerykeion call`` — a guarded dispatcher over the public API.

Lets you reach any ``Factory.method`` (or bare function) in ``kerykeion.__all__``
without writing Python:

    kerykeion call ProfectionsFactory.from_subject --subject ada --param target_date=2025-06-01
    kerykeion call DominantsFactory.from_subject --subject ada
    kerykeion call --list
    kerykeion call DominantsFactory.from_subject --explain

Safety is :mod:`kerykeion.cli.registry`'s job: only ``__all__`` names, one split
on ``.``, no private members, no models/exceptions/protocols, ``getattr_static``
lookups. ``kerykeion call os.system --cmd ls`` fails because ``os`` is not in
``__all__`` — that is the test this command exists to pass.

Subject parameters (``AstrologicalSubjectModel``) are bound from ``-s``/``-S``
profiles rather than parsed strings. Everything else flows through
``--param key=value`` with type coercion from :mod:`kerykeion.cli.introspect`.
"""

from __future__ import annotations

from typing import Any, Optional

import typer

from kerykeion.cli import introspect, registry, subject_resolver
from kerykeion.cli.commands._shared import _emit
from kerykeion.cli.options import (
    CallSubject2Opt,
    ExplainFlag,
    FormatOpt,
    JsonListFlag,
    ListFlag,
    OutputOpt,
    ParamOpt,
    SubjectProfile,
)
from kerykeion.cli.rendering import formats


def _list_targets() -> list[dict[str, object]]:
    """Build the list of {owner, kind, members} for ``--list``."""
    targets: list[dict[str, object]] = []
    for owner_name, owner in sorted(registry.public_names().items()):
        if isinstance(owner, type):
            # Pydantic models are kept in public_names() so ``--explain`` can
            # describe them, but they are not dispatchable (resolve_target
            # refuses them). Listing model_validate/model_dump here would
            # advertise targets the command cannot deliver.
            if registry._is_pydantic_model(owner):  # type: ignore[attr-defined]
                continue
            members = []
            for name in dir(owner):
                if name.startswith("_"):
                    continue
                try:
                    kind, _fn = registry._classify_member(owner, name)  # type: ignore[attr-defined]
                except ValueError:
                    continue
                except AttributeError:
                    continue
                members.append({"name": name, "kind": kind})
            targets.append({"owner": owner_name, "kind": "class", "members": members})
        elif callable(owner):
            targets.append({"owner": owner_name, "kind": "function", "members": []})
    return targets


def _annotation_for(target: registry.ResolvedTarget, key: str) -> Any:
    """Look up a parameter's annotation across init + method params."""
    if key in target.method_params:
        return target.method_params[key].annotation
    if key in target.init_params:
        return target.init_params[key].annotation
    # Unknown parameter: let coerce_value fall back to a raw string, which the
    # library will then reject with its own message. We don't fail here so that
    # a typo surfaces as the library's error, not ours.
    return Any


def _bind_subjects(
    target: registry.ResolvedTarget,
    kwargs: dict[str, Any],
    subject: Optional[str],
    subject2: Optional[str],
) -> None:
    """Assign -s/-S profiles to the target's subject parameters."""
    subject_params = [p.name for p in introspect.explain(target) if p.classification == introspect.SUBJECT]
    if subject is not None:
        if not subject_params:
            raise ValueError(f"{target.spec} has no subject parameter; -s is not used here.")
        kwargs[subject_params[0]] = subject_resolver.resolve_subject(
            subject_resolver.SubjectFlags(), subject
        )
    if subject2 is not None:
        if len(subject_params) < 2:
            raise ValueError(f"{target.spec} has fewer than two subject parameters; -S is not used here.")
        kwargs[subject_params[1]] = subject_resolver.resolve_subject(
            subject_resolver.SubjectFlags(), subject2
        )


def call(
    target_arg: str = typer.Argument(None, help="Call target: Factory.method or a bare function."),
    list_flag: ListFlag = None,  # type: ignore[assignment]
    json_flag: JsonListFlag = None,  # type: ignore[assignment]
    explain_flag: ExplainFlag = None,  # type: ignore[assignment]
    profile: SubjectProfile = None,  # type: ignore[assignment]
    subject2: CallSubject2Opt = None,  # type: ignore[assignment]
    param: ParamOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Dispatch to any public kerykeion factory method or function."""
    if list_flag:
        resolved = formats.resolve_format("json" if json_flag else fmt, output)
        _emit(_list_targets(), resolved, output)
        return

    if target_arg is None:
        raise ValueError("call needs a target (Factory.method) or --list.")

    target = registry.resolve_target(target_arg)

    if explain_flag:
        resolved = formats.resolve_format("json" if json_flag else fmt, output)
        _emit([p.as_dict() for p in introspect.explain(target)], resolved, output)
        return

    kwargs: dict[str, Any] = {}
    for item in param or []:
        if "=" not in item:
            raise ValueError(f"--param expects key=value, got {item!r}")
        raw_key, raw_value = item.split("=", 1)
        key = raw_key.strip()
        annotation = _annotation_for(target, key)
        kwargs[key] = introspect.coerce_value(annotation, raw_value)

    _bind_subjects(target, kwargs, profile, subject2)

    # Reject unknown --param keys up front. For instance-method targets the
    # init/method split below would otherwise silently drop a key in neither set
    # (e.g. a typo), and the library would run with defaults — a wrong result
    # with no error. For the static/function paths Python would raise TypeError
    # anyway; this gives a uniform, clean exit-4 message.
    known = set(target.method_params) | set(target.init_params)
    unknown = [k for k in kwargs if k not in known]
    if unknown:
        raise ValueError(
            f"--param {unknown[0]!r} is not a parameter of {target.spec} "
            f"(known: {', '.join(sorted(known))})"
        )

    if target.needs_instance:
        owner = registry.public_names()[target.owner_name]
        init_kwargs = {k: v for k, v in kwargs.items() if k in target.init_params}
        method_kwargs = {k: v for k, v in kwargs.items() if k in target.method_params}
        instance = owner(**init_kwargs)  # type: ignore[misc]
        result = getattr(instance, target.member_name)(**method_kwargs)  # type: ignore[arg-type]
    elif target.member_name:
        # static or classmethod: go through the owner so Python binds ``cls``
        # (classmethods) or hands back the plain function (staticmethods).
        owner = registry.public_names()[target.owner_name]
        result = getattr(owner, target.member_name)(**kwargs)
    else:
        # bare top-level function
        result = target.callable_fn(**kwargs)

    _emit(result, fmt, output)
