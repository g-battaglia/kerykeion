# -*- coding: utf-8 -*-
"""The ``KerykeionTyper`` base — in its own command-free module so command modules never import ``app`` (a cycle)."""

from __future__ import annotations

import typer

from kerykeion.extra.cli.errors import error_boundary


class KerykeionTyper(typer.Typer):
    """A Typer whose every command — top-level or in a group — runs inside the CLI error boundary.

    Keeping the boundary inside the app means in-process ``CliRunner`` tests,
    which bypass ``run()``, still see clean, classified exits. ``-h`` is a help
    flag here as it is on the no-extra path, and child contexts inherit it.
    """

    def __init__(self, **kwargs):  # type: ignore[no-untyped-def]
        kwargs.setdefault("context_settings", {"help_option_names": ["-h", "--help"]})
        super().__init__(**kwargs)

    def command(self, name=None, **kwargs):  # type: ignore[override]
        if callable(name):  # bare ``@app.command``
            return super().command()(error_boundary(name))
        decorator = super().command(name, **kwargs)
        return lambda func: decorator(error_boundary(func))
