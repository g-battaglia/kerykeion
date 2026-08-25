# -*- coding: utf-8 -*-
"""Refuse to regenerate baselines from a different checkout's code.

An editable install puts ONE path on ``sys.path``, and it is the path the install
was made from. Run a regeneration script from a git worktree of the same
repository and ``import kerykeion`` still resolves to the original checkout — a
different branch, with different uncommitted work — while the script writes its
output into the worktree's ``tests/data/svg``.

That is not hypothetical. It happened here: sixty-four baselines were regenerated
against another branch's half-finished panel change, the diff looked like months
of accumulated staleness, and only the row order gave it away. The files were
plausible, idempotent on a second run, and wrong.

So the scripts ask, before they write anything: is the library I am about to draw
with the one that lives beside the folder I am about to write into? And is it
computing with the ephemeris the baselines are declared to come from? The
comparator only compares numbers on that backend, so a set of baselines written
by the other one would fail every run on the backend they claim as their own.
"""

from pathlib import Path


def require_library_from_this_checkout(script_file: str) -> None:
    """Raise unless the imported kerykeion is the one in this script's repository.

    Args:
        script_file: The regeneration script's ``__file__``.
    """
    import kerykeion

    repository_root = Path(script_file).resolve().parent.parent
    expected = repository_root / "kerykeion"
    imported = Path(kerykeion.__file__).resolve().parent

    if imported != expected:
        raise SystemExit(
            f"Refusing to regenerate: this script would draw with the kerykeion at\n"
            f"  {imported}\n"
            f"and write baselines into\n"
            f"  {repository_root / 'tests' / 'data'}\n"
            f"which belong to a different checkout. An editable install resolves to the "
            f"path it was installed from, so running this from a worktree silently uses "
            f"the original tree's code — including whatever is uncommitted there.\n"
            f"Run it with PYTHONPATH={repository_root} so the checkout you are in wins."
        )


def require_the_baseline_backend() -> None:
    """Raise unless the active ephemeris is the one the stored baselines come from."""
    from tests.data.compare_svg_lines import BASELINE_BACKEND, active_backend

    if active_backend() != BASELINE_BACKEND:
        raise SystemExit(
            f"Refusing to regenerate: the baselines are {BASELINE_BACKEND} charts and this "
            f"run is on {active_backend()}. Unset KERYKEION_BACKEND, or set it to "
            f"{BASELINE_BACKEND}, before regenerating."
        )
