"""Guard the agent skill against drift, license loss, and structural rot.

``skills/kerykeion/`` is the cross-platform Agent Skill (agentskills.io) that
teaches AI coding agents the current public API. Unlike the rest of the docs it
is copied verbatim into third-party repositories (``npx skills add
g-battaglia/kerykeion`` or a manual copy), so a stale version pin, a mangled
license, or a dangling reference file ships broken guidance to strangers with
no feedback channel. Prose coverage is enforced by ``poe docs:check`` and
snippet truth by ``poe docs:snippets``; this module enforces everything those
gates cannot see: frontmatter validity, the vendored license, reference
reachability in both directions, version-pin freshness, and that the bundled
scripts actually run.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
SKILL_DIR = REPO_ROOT / "skills" / "kerykeion"
SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCES_DIR = SKILL_DIR / "references"


def _skill_corpus() -> list[Path]:
    """Every text file that ships with the skill."""
    return sorted(
        path
        for path in SKILL_DIR.rglob("*")
        if path.is_file() and path.suffix in (".md", ".py", "")
    )


def _frontmatter() -> str:
    text = SKILL_MD.read_text(encoding="utf-8")
    assert text.startswith("---\n"), "SKILL.md must open with YAML frontmatter"
    end = text.index("\n---", 4)
    return text[4:end]


def test_the_skill_exists_and_is_not_vacuous():
    assert SKILL_MD.is_file(), "skills/kerykeion/SKILL.md is missing"
    references = list(REFERENCES_DIR.glob("*.md"))
    assert references, "the skill has no reference files at all"


def test_frontmatter_contract():
    frontmatter = _frontmatter()

    name_match = re.search(r"^name:\s*(\S+)\s*$", frontmatter, re.MULTILINE)
    assert name_match, "frontmatter has no name field"
    name = name_match.group(1)
    assert name == "kerykeion"
    assert re.fullmatch(r"[a-z0-9-]{1,64}", name)

    # description is a `>-` block scalar: gather its indented lines.
    description_match = re.search(
        r"^description:\s*>-?\n((?:[ \t]+\S.*\n)+)", frontmatter, re.MULTILINE
    )
    assert description_match, "frontmatter has no description block"
    description = " ".join(
        line.strip() for line in description_match.group(1).splitlines()
    )
    assert description, "description is empty"
    assert len(description) <= 1024, (
        f"description is {len(description)} chars; agentskills.io caps it at 1024"
    )

    license_match = re.search(r"^license:\s*(\S+)\s*$", frontmatter, re.MULTILINE)
    assert license_match, "frontmatter has no license field"
    assert license_match.group(1) == "AGPL-3.0"


def test_vendored_license_is_byte_identical_to_the_repo_license():
    vendored = SKILL_DIR / "LICENSE"
    assert vendored.is_file(), "the skill must vendor the AGPL license text"
    assert vendored.read_bytes() == (REPO_ROOT / "LICENSE").read_bytes(), (
        "skills/kerykeion/LICENSE has drifted from the repository LICENSE"
    )


def test_no_foreign_license_strings_in_the_skill():
    # The skill folder is AGPL-only; a stray permissive-license string is a
    # regression that has slipped into this project before.
    for path in _skill_corpus():
        content = path.read_text(encoding="utf-8", errors="ignore").lower()
        assert "apache" not in content, f"foreign license string in {path}"


def test_references_are_reachable_in_both_directions():
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    mentioned = set(re.findall(r"references/([a-z0-9-]+\.md)", skill_text))

    on_disk = {path.name for path in REFERENCES_DIR.glob("*.md")}

    dangling = mentioned - on_disk
    assert not dangling, f"SKILL.md points at missing reference files: {sorted(dangling)}"

    orphans = on_disk - mentioned
    assert not orphans, (
        f"reference files never mentioned in SKILL.md (agents will never load "
        f"them): {sorted(orphans)}"
    )


def test_version_pins_match_pyproject():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE).group(1)

    assert version in SKILL_MD.read_text(encoding="utf-8"), (
        f"SKILL.md must state the version it was verified against ({version}); "
        "update the 'Verified against' line in the same commit as the bump"
    )

    # Any fully-qualified alpha version mentioned anywhere in the skill must be
    # the current one. Bare history tags like "a75" deliberately do not match.
    for path in _skill_corpus():
        for pinned in re.findall(r"\b6\.0\.0a\d+\b", path.read_text(encoding="utf-8", errors="ignore")):
            assert pinned == version, (
                f"{path} pins {pinned} but pyproject says {version}"
            )


def test_install_doc_present():
    readme = SKILL_DIR / "README.md"
    assert readme.is_file(), "the skill needs its human-facing README"
    assert "npx skills add g-battaglia/kerykeion" in readme.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "script",
    sorted((SKILL_DIR / "scripts").glob("*.py"), key=lambda p: p.name),
    ids=lambda p: p.name,
)
def test_bundled_scripts_run(script: Path, tmp_path: Path):
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT))
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"{script.name} failed:\n{result.stdout}\n{result.stderr}"
    )
