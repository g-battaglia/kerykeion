# -*- coding: utf-8 -*-
"""Output rendering for the kerykeion CLI.

Split from the command modules because ``svg_out`` imports ``ChartDrawer`` (a
~5,700-line module) and must only load when ``--format svg`` is asked. The
format decider (:mod:`kerykeion.cli.rendering.formats`) has no heavy imports.

All output goes to **stdout** via ``sys.stdout.write`` / ``typer.echo`` — never
through ``rich.Console.print``, which wraps to the terminal width and applies
``highlight``, corrupting a fixed-column report and injecting ANSI into piped
JSON. Rich is reserved for chrome (help, error panels, progress) on stderr.
"""
