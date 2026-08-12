#!/usr/bin/env python3
"""Fail when an explicitly exported package API is absent from user docs.

The package root's ``__all__`` is Kerykeion's supported public surface.  Using
that explicit contract avoids treating helpers imported by implementation
modules as public API while still checking classes, models, literals, and
constants (not only functions/classes discovered by ``inspect``).
"""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path
from types import ModuleType


PROJECT_ROOT = Path(__file__).resolve().parent.parent
# The agent skill is checked twice: once inside the aggregate corpus below and
# once on its own. The aggregate check is a union — a name documented only in
# the README would satisfy it — while the skill is copied verbatim into
# third-party repos and must therefore cover every export by itself.
SKILL_TARGET = PROJECT_ROOT / "skills" / "kerykeion"
DOCUMENTATION_TARGETS = (
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "kerykeion" / "llms.txt",
    PROJECT_ROOT / "site" / "docs",
    PROJECT_ROOT / "site" / "examples",
    SKILL_TARGET,
)


def get_public_api_names(package: ModuleType) -> list[str]:
    """Return and validate the package's deliberately exported names."""
    exported = getattr(package, "__all__", None)
    if exported is None:
        raise RuntimeError(f"{package.__name__} does not define __all__; the public API contract is unknown")

    names = sorted(set(exported))
    missing_exports = [name for name in names if not hasattr(package, name)]
    if missing_exports:
        raise RuntimeError(
            f"{package.__name__}.__all__ contains missing attributes: {', '.join(missing_exports)}"
        )
    return names


def iter_documentation_files(targets: tuple[Path, ...] = DOCUMENTATION_TARGETS) -> list[Path]:
    """Return the maintained user-facing Markdown/text documentation corpus."""
    files: set[Path] = set()
    for target in targets:
        if target.is_file():
            files.add(target)
        elif target.is_dir():
            files.update(target.rglob("*.md"))
        else:
            raise FileNotFoundError(f"Documentation target not found: {target}")
    return sorted(files)


def load_documentation_content(files: list[Path]) -> str:
    """Load the documentation corpus as one searchable string."""
    return "\n".join(path.read_text(encoding="utf-8") for path in files)


def undocumented_names(public_names: list[str], docs_content: str) -> list[str]:
    """Return exported names that never occur as complete identifiers."""
    return [
        name
        for name in public_names
        if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", docs_content) is None
    ]


def main() -> int:
    """Run the public-API documentation coverage gate."""
    print("Starting Kerykeion Documentation Coverage Audit...")
    sys.path.insert(0, str(PROJECT_ROOT))

    package = importlib.import_module("kerykeion")
    public_names = get_public_api_names(package)
    documentation_files = iter_documentation_files()
    docs_content = load_documentation_content(documentation_files)
    missing = undocumented_names(public_names, docs_content)
    documented_count = len(public_names) - len(missing)
    coverage = documented_count / len(public_names) * 100 if public_names else 100.0

    print(f"Documentation files scanned: {len(documentation_files)}")
    print(f"Explicit public exports: {len(public_names)}")
    print(f"Documented exports: {documented_count}")
    print(f"Coverage: {coverage:.1f}%")

    # Standalone pass: the skill must cover every export on its own (it ships
    # into third-party repos without the rest of this corpus).
    skill_content = load_documentation_content(iter_documentation_files((SKILL_TARGET,)))
    missing_in_skill = undocumented_names(public_names, skill_content)
    skill_documented = len(public_names) - len(missing_in_skill)
    skill_coverage = skill_documented / len(public_names) * 100 if public_names else 100.0
    print(f"Agent-skill standalone coverage: {skill_coverage:.1f}%")

    if missing:
        print("\nMISSING PUBLIC API DOCUMENTATION:")
        print("=================================")
        for name in missing:
            print(f"  - {name}")

    if missing_in_skill:
        print("\nMISSING FROM THE AGENT SKILL (skills/kerykeion):")
        print("================================================")
        for name in missing_in_skill:
            print(f"  - {name}")

    if missing or missing_in_skill:
        return 1

    print("\nAll explicitly exported public APIs are documented.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
