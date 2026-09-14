# -*- coding: utf-8 -*-
"""The ``kerykeion`` command: the console script and ``python -m kerykeion_cli`` both resolve to :func:`main`.

Shipped as the ``kerykeion-cli`` distribution, which the ``kerykeion[cli]``
extra installs — the library's own wheel carries no command. Built on the
standard library alone (argparse), so kerykeion is the whole dependency, and
``import kerykeion`` never imports this package.

(It is not *fast*: importing a submodule imports ``kerykeion`` first — about a
second of backend selection. Making that lazy is a change to ``kerykeion/__init__.py``.)
"""

from __future__ import annotations

import sys

__all__ = ["main"]


def main(argv: list[str] | None = None) -> int:
    """Console-script entry point: parse, dispatch, and turn anything that escapes into a classified exit."""
    from kerykeion_cli.app import run
    from kerykeion_cli.errors import handle_uncaught

    args = sys.argv[1:] if argv is None else list(argv)
    try:
        return run(args)
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001 — the whole point is to catch all
        handle_uncaught(exc)


if __name__ == "__main__":
    sys.exit(main())
