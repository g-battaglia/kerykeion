# -*- coding: utf-8 -*-
"""``kerykeion call`` — a guarded dispatcher over the public API.

    kerykeion call ProfectionsFactory.from_subject -s ada --param target_date=2025-06-01
    kerykeion call --list
    kerykeion call DominantsFactory.from_subject --explain

Safety is :mod:`kerykeion.extra.cli.registry`'s job (only ``__all__`` names, no
private members, no models/exceptions). Subject parameters are bound from
``-s``/``-S`` profiles; everything else comes as ``--param key=value`` with
type coercion from :mod:`kerykeion.extra.cli.introspect`.
"""

from __future__ import annotations

from typing import Annotated, Any, Optional

from kerykeion.extra.cli import introspect, registry, subject_resolver
from kerykeion.extra.cli.commands._shared import _emit
from kerykeion.extra.cli.options import (
    CallSubject2Opt,
    ExplainFlag,
    FormatOpt,
    JsonListFlag,
    ListFlag,
    OutputOpt,
    ParamOpt,
    SubjectProfile,
)
from kerykeion.extra.cli.parser import Arg
from kerykeion.extra.cli.rendering import formats


def _bind_subjects(
    target: registry.ResolvedTarget, kwargs: dict[str, Any], first: Optional[str], second: Optional[str]
) -> None:
    """Assign the -s/-S profiles to the target's subject parameters, in order."""
    slots = [p.name for p in introspect.explain(target) if p.classification == introspect.SUBJECT]
    for flag, spec, index in (("-s", first, 0), ("-S", second, 1)):
        if spec is None:
            continue
        if len(slots) <= index:
            raise ValueError(
                f"{target.spec} has {'no' if index == 0 else 'fewer than two'} subject parameter{'' if index == 0 else 's'}; {flag} is not used here."
            )
        kwargs[slots[index]] = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), spec)


def call(
    target_arg: Annotated[Optional[str], Arg(help="Call target: Factory.method or a bare function.")] = None,
    list_flag: ListFlag = None,
    json_flag: JsonListFlag = None,
    explain_flag: ExplainFlag = None,
    profile: SubjectProfile = None,
    subject2: CallSubject2Opt = None,
    param: ParamOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Any public factory method, for what has no command of its own."""
    listing_fmt = formats.resolve_format("json" if json_flag else fmt, output)
    if list_flag:
        _emit(registry.list_targets(), listing_fmt, output)
        return
    if target_arg is None:
        raise ValueError("call needs a target (Factory.method) or --list.")
    target = registry.resolve_target(target_arg)
    if explain_flag:
        _emit([p.as_dict() for p in introspect.explain(target)], listing_fmt, output)
        return

    known = {**target.init_params, **target.method_params}
    kwargs: dict[str, Any] = {}
    for item in param or []:
        if "=" not in item:
            raise ValueError(f"--param expects key=value, got {item!r}")
        key, raw_value = item.split("=", 1)
        key = key.strip()
        if key not in known:  # a typo must not run the library with defaults and no error
            raise ValueError(f"--param {key!r} is not a parameter of {target.spec} (known: {', '.join(sorted(known))})")
        kwargs[key] = introspect.coerce_value(known[key].annotation, raw_value)
    _bind_subjects(target, kwargs, profile, subject2)

    if target.needs_instance:
        owner = registry.public_names()[target.owner_name]
        instance = owner(**{k: v for k, v in kwargs.items() if k in target.init_params})
        result = getattr(instance, target.member_name)(**{k: v for k, v in kwargs.items() if k in target.method_params})  # type: ignore[arg-type]
    elif target.member_name:  # static or classmethod: through the owner so Python binds ``cls``
        result = getattr(registry.public_names()[target.owner_name], target.member_name)(**kwargs)
    else:
        result = target.callable_fn(**kwargs)
    _emit(result, fmt, output)
