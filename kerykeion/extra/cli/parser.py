# -*- coding: utf-8 -*-
"""argparse parsers built from function signatures.

A command is a plain function whose parameters are ``Annotated[T, Opt(...)]``
(or ``Annotated[T, Arg(...)]`` for a positional). :func:`add_command` reads
that signature and declares the matching arguments, so a flag is spelled once,
in :mod:`kerykeion.extra.cli.options`, and every command that takes it composes
its signature from the alias. Standard library only; nothing here imports kerykeion.
"""

from __future__ import annotations

import argparse
import inspect
import types
import typing
from dataclasses import dataclass
from typing import Any, Callable, Optional, Sequence


@dataclass(frozen=True)
class Opt:
    """An option's spellings and help; *group* is the help section it is listed under."""

    names: tuple[str, ...]
    help: str
    group: Optional[str] = None


@dataclass(frozen=True)
class Arg:
    """A positional argument's help."""

    help: str


_SCALARS: dict[Any, Callable[[str], Any]] = {str: str, int: int, float: float}


def _unwrap(annotation: Any) -> tuple[Any, Optional[Opt | Arg]]:
    """``(base type, metadata)`` for ``Annotated[Optional[T], Opt(...)]``; ``Optional`` is stripped."""
    meta: Optional[Opt | Arg] = None
    if typing.get_origin(annotation) is typing.Annotated:
        annotation, *extras = typing.get_args(annotation)
        meta = next((extra for extra in extras if isinstance(extra, (Opt, Arg))), None)
    if typing.get_origin(annotation) in (typing.Union, types.UnionType):
        arms = [arm for arm in typing.get_args(annotation) if arm is not type(None)]
        if len(arms) == 1:
            annotation = arms[0]
    return annotation, meta


def _add_argument(parser: argparse.ArgumentParser, groups: dict[str, Any], dest: str, annotation: Any, default: Any) -> None:
    base, meta = _unwrap(annotation)
    if meta is None:
        raise TypeError(f"parameter {dest!r} carries no Opt/Arg metadata")
    if isinstance(meta, Arg):
        if default is inspect.Parameter.empty:
            parser.add_argument(dest, help=meta.help)
        else:
            parser.add_argument(dest, nargs="?", default=default, help=meta.help)
        return
    target = parser if meta.group is None else groups.setdefault(meta.group, parser.add_argument_group(meta.group))
    default = None if default is inspect.Parameter.empty else default
    if base is bool:
        if "/" in meta.names[0]:  # --x/--no-x
            target.add_argument(meta.names[0].split("/")[0], dest=dest, action=argparse.BooleanOptionalAction, default=default, help=meta.help)
        else:
            target.add_argument(*meta.names, dest=dest, action="store_true", default=default, help=meta.help)
        return
    metavar = max(meta.names, key=len).lstrip("-").replace("-", "_").upper()
    if typing.get_origin(base) is list:
        (inner,) = typing.get_args(base) or (str,)
        target.add_argument(*meta.names, dest=dest, action="append", type=_SCALARS.get(inner, str), metavar=metavar, default=default, help=meta.help)
        return
    target.add_argument(*meta.names, dest=dest, type=_SCALARS.get(base, str), metavar=metavar, default=default, help=meta.help)


def summary(func: Callable[..., Any]) -> str:
    """The first line of *func*'s docstring: what the command list shows next to the name."""
    doc = inspect.getdoc(func) or ""
    return doc.splitlines()[0] if doc else ""


def add_command(subparsers: Any, name: str, func: Callable[..., Any]) -> argparse.ArgumentParser:
    """Declare *func* as the command *name*, its arguments read from the signature."""
    parser = subparsers.add_parser(name, help=summary(func), description=inspect.getdoc(func))
    hints = typing.get_type_hints(func, include_extras=True)
    groups: dict[str, Any] = {}
    for param_name, param in inspect.signature(func).parameters.items():
        if param_name == "opts":  # assembled by the dispatcher from the render flags
            continue
        _add_argument(parser, groups, param_name, hints.get(param_name, param.annotation), param.default)
    if getattr(func, "render_flags", False):
        from kerykeion.extra.cli.commands._shared import _RENDER_FLAGS

        for flag, (alias, _) in _RENDER_FLAGS.items():
            _add_argument(parser, groups, flag, alias, None)
    positionals = [f"[{a.dest}]" if a.nargs == "?" else a.dest for a in parser._get_positional_actions()]
    parser.usage = " ".join([parser.prog, *positionals, "[flags]"])  # not the forty-flag usage argparse would print
    parser.set_defaults(handler=func)
    return parser


def add_group(subparsers: Any, name: str, help: str, commands: Sequence[tuple[str, Any]]) -> None:
    """Declare the group *name* (``kerykeion technique <sub>``) with one sub-parser per command."""
    parser = subparsers.add_parser(name, help=help, description=help)
    parser.set_defaults(menu=parser)
    nested = parser.add_subparsers(metavar="<command>")
    for command_name, func in commands:
        add_command(nested, command_name, func)
