#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Execute every ``bash`` block in the CLI agent skill, and fail if one does not run.

``scripts/test_markdown_snippets.py`` executes ``python`` blocks; the CLI skill's
examples are shell, so nothing would check them. That gap matters more than
usual: the skill is copied verbatim into third-party repositories, where a
command that does not exist ships as confident instruction to a stranger with no
feedback channel.

Blocks run under ``bash -euo pipefail`` with a **per-file** temporary working
directory and ``XDG_CONFIG_HOME``: the blocks of one page execute in order and
share state, because that is how a reader uses a page — the setup block at the
top is expected to serve the examples below it. Pages never share with each
other, so a page that forgets its own setup fails here rather than passing on a
profile some other page happened to create.

Nothing touches the developer's real profile store (it holds birth data) and
nothing writes into the repository.

Blocks that cannot run in a sandbox (``pip install``, ``git clone``) opt out with
a ``# gate: skip`` line as their first line — visible in the rendered skill, so a
reader can see it is illustrative.

Usage:
    python scripts/test_skill_cli_snippets.py [--timeout SECONDS]
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = PROJECT_ROOT / "skills" / "kerykeion-cli"
SKIP_MARKER = "# gate: skip"

BASH_BLOCK = re.compile(r"```(?:bash|console|sh)\n(.*?)```", re.DOTALL)


def extract_blocks(text: str) -> list[str]:
    return [match.group(1) for match in BASH_BLOCK.finditer(text)]


def run_block(code: str, *, workdir: Path, timeout: float) -> tuple[bool, str]:
    """Run one block inside the page's sandbox; return (ok, detail)."""
    env = {
        **os.environ,
        "XDG_CONFIG_HOME": str(workdir / "config"),
        # Deterministic, non-interactive rendering, exactly as the CLI tests
        # pin it: Rich reads the width from the process's own fds.
        "NO_COLOR": "1",
        "TERM": "dumb",
        "COLUMNS": "100",
        "LINES": "40",
    }
    try:
        completed = subprocess.run(
            ["bash", "-euo", "pipefail", "-c", code],
            cwd=workdir,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout:g}s"
    if completed.returncode == 0:
        # ``jq -r .missing`` prints a bare ``null`` and exits 0: an example that
        # names a field the payload does not have would pass on exit code alone.
        if any(line.strip() == "null" for line in completed.stdout.splitlines()):
            return False, "prints a bare `null`: a jq path names a field the payload does not have"
        return True, ""
    tail = (completed.stderr or completed.stdout or "").strip().splitlines()
    detail = "\n      ".join(tail[-6:]) if tail else "(no output)"
    return False, f"exit {completed.returncode}\n      {detail}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=120.0,
                        help="Per-block timeout in seconds (default: 120).")
    args = parser.parse_args()

    if shutil.which("bash") is None:
        print("bash not found; cannot verify the CLI skill's examples.", file=sys.stderr)
        return 1
    if not SKILL_DIR.is_dir():
        print(f"missing skill directory: {SKILL_DIR}", file=sys.stderr)
        return 1

    total = skipped = failed = 0
    for path in sorted(SKILL_DIR.rglob("*.md")):
        blocks = extract_blocks(path.read_text(encoding="utf-8"))
        if not blocks:
            continue
        rel = path.relative_to(PROJECT_ROOT)
        print(f"\n📝 {rel} ({len(blocks)} block(s))")
        with tempfile.TemporaryDirectory(prefix="kerykeion-skill-") as tmp:
            workdir = Path(tmp)
            for index, code in enumerate(blocks, start=1):
                total += 1
                if code.lstrip().startswith(SKIP_MARKER):
                    skipped += 1
                    print(f"  ⏭  Block {index}: skipped ({SKIP_MARKER})")
                    continue
                ok, detail = run_block(code, workdir=workdir, timeout=args.timeout)
                if ok:
                    print(f"  ✅ Block {index}: OK")
                else:
                    failed += 1
                    print(f"  ❌ Block {index}: {detail}")

    ran = total - skipped
    print(f"\n📊 Results: {ran - failed}/{ran} runnable block(s) passed "
          f"({skipped} skipped, {total} total)")
    if failed:
        print("🚨 The CLI skill documents commands that do not run.")
        return 1
    if ran == 0:
        # A gate whose whole purpose is falsifiability must not be able to pass
        # vacuously: a renamed directory, a changed fence language, or every
        # block marked skip would otherwise report success having verified
        # nothing at all.
        print(
            "🚨 No runnable bash block was found. Either the skill lost its "
            "examples, the fences are no longer bash/console/sh, or every block "
            f"is marked '{SKIP_MARKER}'. Refusing to report success."
        )
        return 1
    print("🎉 Every runnable block in the CLI skill works.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
