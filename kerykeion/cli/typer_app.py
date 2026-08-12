# -*- coding: utf-8 -*-
"""The :class:`KerykeionTyper` base, kept out of :mod:`kerykeion.cli.app` on purpose.

``app`` runs ``_register_commands`` as a module-level side effect (it imports
every command module). If a command module imported ``KerykeionTyper`` *from*
``app``, the cold-import order chosen by the import-graph gate (command module
first) would make ``app`` look up ``subject_app`` before that module had defined
it — a classic partially-initialised circular import. Keeping the base class in
this command-free module breaks the cycle cleanly: command modules depend on
``typer_app``, never on ``app``.
"""

from __future__ import annotations

import typer

from kerykeion.cli.errors import error_boundary


class KerykeionTyper(typer.Typer):
    """Typer variant whose commands are wrapped in the CLI error boundary.

    Overriding ``command`` means every command — top-level (``natal``) and every
    sub-command of a registered group (``subject save`` …) — runs inside
    :func:`~kerykeion.cli.errors.error_boundary`. That keeps the boundary inside
    the app, so in-process ``CliRunner`` tests (which call ``app()`` directly and
    bypass :func:`~kerykeion.cli.app.run`) still see clean, classified exits
    instead of raw exceptions.
    """

    def command(self, name=None, **kwargs):  # type: ignore[override]
        # Bare ``@app.command`` (the callable form): wrap the function directly.
        if callable(name):
            return super().command(error_boundary(name))
        decorator = super().command(name, **kwargs)

        def register(func):
            return decorator(error_boundary(func))

        return register
