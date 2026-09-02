# -*- coding: utf-8 -*-
"""The command-line interface: ``kerykeion`` and ``python -m kerykeion`` both resolve to :func:`main`.

Built on the standard library alone (argparse), so the ``kerykeion[cli]``
extra — the documented way to install the interface — pulls in no third-party
package. ``import kerykeion`` never imports this package.

(It is not *fast*: importing a submodule imports ``kerykeion`` first — about a
second of backend selection. Making that lazy is a change to ``kerykeion/__init__.py``.)
"""

from __future__ import annotations

import sys

__all__ = ["main"]


def main(argv: list[str] | None = None) -> int:
    """Console-script entry point: parse, dispatch, and turn anything that escapes into a classified exit."""
    from kerykeion.extra.cli.app import run
    from kerykeion.extra.cli.errors import handle_uncaught

    args = sys.argv[1:] if argv is None else list(argv)
    try:
        return run(args)
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001 — the whole point is to catch all
        handle_uncaught(exc)


if __name__ == "__main__":
    sys.exit(main())
