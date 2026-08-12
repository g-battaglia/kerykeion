# -*- coding: utf-8 -*-
"""Enable ``python -m kerykeion``.

This module is executed ONLY by ``python -m kerykeion``; a plain
``import kerykeion`` runs ``kerykeion/__init__.py`` and never touches this file,
so adding it cannot pull the CLI (and typer) into the library's import path.
The import-graph cold-import gate skips every ``__main__`` for the same reason.
"""

from kerykeion.cli import main

raise SystemExit(main())
