# -*- coding: utf-8 -*-
"""Command groups for the kerykeion CLI.

Each module here owns one Typer sub-app (``subject``, ``charts``, …) and is
registered by :mod:`kerykeion.cli.app`. These modules may import ``typer`` at
module level (it is the CLI extra) but must import kerykeion symbols lazily, so
the import-graph gate stays green.
"""
