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
    """Every file that ships with the skill.

    Deliberately unfiltered by extension: the license and version-pin guards
    below must cover whatever the skill distributes, and an allow-list would
    silently exempt any future asset (JSON, .txt, YAML) from both. Callers
    read with ``errors="ignore"``, so a binary file is harmless here.
    """
    return sorted(path for path in SKILL_DIR.rglob("*") if path.is_file())


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
    """No dangling pointers anywhere, and no reference SKILL.md cannot reach.

    Links are checked across the whole corpus, not just SKILL.md: the
    references cross-link each other heavily, and a rename that updates only
    the router would leave those cross-links pointing at nothing while this
    gate stayed green.
    """
    on_disk = {path.name for path in REFERENCES_DIR.glob("*.md")}

    dangling: dict[str, list[str]] = {}
    for path in _skill_corpus():
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for target in set(re.findall(r"references/([a-z0-9-]+\.md)", text)):
            if target not in on_disk:
                dangling.setdefault(path.name, []).append(target)
    assert not dangling, f"pointers at missing reference files: {dangling}"

    # The router must still reach every reference directly: an agent loads
    # SKILL.md first, so a file only linked from a sibling is unreachable.
    from_router = set(
        re.findall(r"references/([a-z0-9-]+\.md)", SKILL_MD.read_text(encoding="utf-8"))
    )
    orphans = on_disk - from_router
    assert not orphans, (
        f"reference files never mentioned in SKILL.md (agents will never load "
        f"them): {sorted(orphans)}"
    )


def test_version_pins_match_pyproject():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE).group(1)

    assert version in SKILL_MD.read_text(encoding="utf-8"), (
        f"The skill claims a version it was not verified against. Fix by editing "
        f"the 'Verified against kerykeion X' line at the top of "
        f"skills/kerykeion/SKILL.md to read {version}.\n"
        f"This gate is intentional: a release bump is the moment to re-read the "
        f"skill for API drift, and nothing else forces that review."
    )

    # Any fully-qualified alpha version mentioned anywhere in the skill must be
    # the current one. Bare history tags like "a75" deliberately do not match.
    for path in _skill_corpus():
        for pinned in re.findall(r"\b6\.0\.0a\d+\b", path.read_text(encoding="utf-8", errors="ignore")):
            assert pinned == version, (
                f"{path} pins {pinned} but pyproject says {version}"
            )


def test_subpackage_imports_are_indexed():
    """Every API a reference documents as a subpackage import must have a row
    in api-index.md. The docs:check gate only audits ``kerykeion.__all__``,
    so without this check the index's completeness claim can silently rot as
    references document new subpackage-only names.
    """
    index_text = (REFERENCES_DIR / "api-index.md").read_text(encoding="utf-8")
    indexed = set(re.findall(r"^\| `([^`]+)` \|", index_text, re.MULTILINE))
    missing = []
    for ref in sorted(REFERENCES_DIR.glob("*.md")):
        if ref.name == "api-index.md":
            continue
        for match in re.finditer(
            r"\*\*Subpackage import:\*\*\s*`from\s+[\w.]+\s+import\s+([^`]+)`",
            ref.read_text(encoding="utf-8"),
        ):
            for name in re.findall(r"\w+", match.group(1)):
                if name not in indexed:
                    missing.append(f"{name} ({ref.name})")
    assert not missing, (
        f"subpackage APIs documented in references but absent from api-index.md: {missing}"
    )


def test_install_doc_present():
    readme = SKILL_DIR / "README.md"
    assert readme.is_file(), "the skill needs its human-facing README"
    assert "npx skills add g-battaglia/kerykeion" in readme.read_text(encoding="utf-8")


# Both scripts exit 0 by design (env_report is a report, not a gate), so a
# returncode assertion alone proves nothing. Each entry pins output that only
# a working run can produce.
_SCRIPT_EXPECTATIONS = {
    "quickstart.py": ("=== Subject ===", "Sun:", "Aspects found:", "OK — quickstart completed."),
    "env_report.py": ("=== Kerykeion environment report ===", "Backend:", "year 2024: OK"),
}


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

    expected = _SCRIPT_EXPECTATIONS.get(script.name)
    assert expected is not None, (
        f"{script.name} ships with the skill but has no output expectations; add "
        f"them to _SCRIPT_EXPECTATIONS so this test can actually fail"
    )
    for marker in expected:
        assert marker in result.stdout, (
            f"{script.name} ran but did not produce {marker!r}:\n{result.stdout}"
        )
    assert "Traceback" not in result.stderr, (
        f"{script.name} exited 0 but raised:\n{result.stderr}"
    )
