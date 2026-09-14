#!/usr/bin/env python3
"""
Simple script to test Python snippets in Markdown files.

Common usages:
  - README only:                 python scripts/test_markdown_snippets.py --readme
  - Site docs only:              python scripts/test_markdown_snippets.py --docs
  - Site examples only:          python scripts/test_markdown_snippets.py --examples
  - AI Agent Guide only:         python scripts/test_markdown_snippets.py --ai-guide
  - All (incl. release notes):   python scripts/test_markdown_snippets.py --all
  - All (exclude release notes): python scripts/test_markdown_snippets.py --all-no-release
"""

import argparse
import re
import sys
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import textwrap
from typing import Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = PROJECT_ROOT / "skills" / "kerykeion"


def find_markdown_files(
    targets: list[Path],
    *,
    exclude_release_notes: bool = False,
) -> list[Path]:
    """Collect markdown files from the provided targets.

    A target that cannot contribute files raises instead of being skipped: a
    silently empty corpus reports "all snippets passed" while verifying nothing.
    That covers three cases, not just the obvious one — a missing path, an
    existing file with a suffix this runner does not read (``README.mdx``), and
    an existing directory holding no markdown at all (a renamed docs folder).

    A relative target is tried against the caller's working directory first and
    then against the repository root. Rebasing unconditionally would silently
    scan the wrong corpus where both exist — this repository has ``docs/`` *and*
    ``site/docs/``, so ``test_markdown_snippets.py docs`` run from ``site/``
    would have verified the other one without a word.
    """
    markdown_files: set[Path] = set()

    for target in targets:
        if target.is_absolute():
            path = target.resolve()
        else:
            local = (Path.cwd() / target).resolve()
            path = local if local.exists() else (PROJECT_ROOT / target).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Snippet target not found: {path}")
        # Explicit files: accept markdown and markdown-formatted .txt
        # (kerykeion/llms.txt is the AI-agent guide with ```python blocks).
        if path.is_file():
            if path.suffix.lower() not in (".md", ".txt"):
                raise ValueError(
                    f"Snippet target {path} is not a markdown (.md/.txt) file; it "
                    f"would contribute no snippets and pass silently."
                )
            markdown_files.add(path)
            continue

        if not path.is_dir():
            continue

        if not any(path.rglob("*.md")):
            raise FileNotFoundError(f"Snippet target {path} holds no markdown files")

        for md_file in path.rglob("*.md"):
            if md_file.name.lower().startswith("v4."):
                continue
            if exclude_release_notes and "release_notes" in md_file.parts:
                continue
            markdown_files.add(md_file)

    return sorted(markdown_files)


def extract_python_snippets(content):
    """Extract runnable Python code blocks from markdown.

    A block whose first line contains the marker ``doc-snippet: no-run`` is
    illustrative (pseudo-fragment, deliberately-old API on migration pages,
    external-service call) and is excluded from execution. The marker lives in
    a Python comment so site renderers are unaffected.
    """
    pattern = r"```python[^\n]*\n(.*?)\n[ \t]*```"
    snippets = re.findall(pattern, content, re.DOTALL)
    return [
        snippet for snippet in snippets
        if "doc-snippet: no-run" not in snippet.split("\n", 1)[0]
    ]


def test_snippet(code: str, *, timeout: float, bare: bool = False) -> Tuple[bool, Optional[str]]:
    """Test if Python snippet runs without errors.

    With ``bare=True`` no import prelude is injected: the block must import
    everything it uses itself (harness plumbing — sys.path and the warnings
    filter — is still applied). This is the contract for the agent skill,
    whose blocks are copy-pasted individually into foreign codebases.
    """
    # Normalize indentation for nested code blocks
    code = textwrap.dedent(code)

    project_root = str(Path(__file__).parent.parent)
    prelude = f"""
import sys
sys.path.insert(0, '{project_root}')
import warnings
warnings.filterwarnings('ignore')
"""
    if not bare:
        prelude += """
# Common imports for kerykeion
from typing import Literal, Union
from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    ChartDrawer,
    CompositeSubjectFactory,
    KerykeionSettingsModel,
)
"""
    full_code = prelude + code

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(full_code)
            f.flush()

            result = subprocess.run(
                [sys.executable, f.name],
                capture_output=True,
                timeout=timeout,
                cwd=Path(__file__).parent.parent,
                text=True,
            )

            Path(f.name).unlink()  # Clean up

            # Check if it's just a geonames warning (not a real error)
            error_output = result.stderr or result.stdout
            if result.returncode != 0:
                # Ignore pure geonames-username warnings — but never mask a
                # real crash: a traceback in the output is a genuine failure
                # even when the warning also fired earlier in the run.
                if (
                    "NO GEONAMES USERNAME SET" in error_output
                    and "WARNING:root:" in error_output
                    and "Traceback" not in error_output
                ):
                    return True, "Success (geonames warning ignored)"
                return False, error_output

            return True, None

    except subprocess.TimeoutExpired:
        return False, f"Timeout ({timeout}s exceeded)"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description="Execute Python snippets embedded in markdown files.")
    # Corpus selectors are mutually exclusive: the branches below are checked in
    # a fixed order, so a silently-shadowed flag would run a different corpus
    # than the caller asked for (--skill --readme used to run README.md without
    # even setting the isolation --skill implies).
    corpus = parser.add_mutually_exclusive_group()
    corpus.add_argument(
        "-a", "--all", dest="all_files", action="store_true", help="Run snippets for every markdown file."
    )
    corpus.add_argument(
        "-an",
        "--all-no-release",
        dest="all_no_release",
        action="store_true",
        help="Run snippets for all markdown files excluding release notes.",
    )
    corpus.add_argument(
        "-r", "--readme", dest="readme_only", action="store_true", help="Run snippets only for README.md."
    )
    corpus.add_argument(
        "-d", "--docs", dest="docs_only", action="store_true", help="Run snippets only for site-docs folder."
    )
    corpus.add_argument(
        "-e",
        "--examples",
        dest="examples_only",
        action="store_true",
        help="Run snippets only for site-examples folder.",
    )
    corpus.add_argument(
        "-ai", "--ai-guide", dest="ai_guide_only", action="store_true", help="Run snippets only for the AI-agent guide (kerykeion/llms.txt)."
    )
    corpus.add_argument(
        "--skill", dest="skill_only", action="store_true",
        help="Run snippets only for the agent skill (skills/kerykeion); implies --isolated.",
    )
    parser.add_argument(
        "--isolated", dest="isolated", action="store_true",
        help=(
            "Run each snippet in its own process with no shared page context. "
            "Skill-corpus snippets additionally run without the import prelude."
        ),
    )
    parser.add_argument("--timeout", type=float, default=20.0, help="Per-snippet timeout in seconds (default: 20).")
    parser.add_argument("paths", nargs="*", type=Path, help="Optional paths to scan (defaults depend on flags).")
    args = parser.parse_args()

    if args.readme_only:
        targets = [Path("README.md")]
        exclude_release_notes = False
        mode_description = "README.md only"
    elif args.docs_only:
        targets = [Path("site/docs")]
        exclude_release_notes = True
        mode_description = "site/docs folder only"
    elif args.examples_only:
        targets = [Path("site/examples")]
        exclude_release_notes = True
        mode_description = "site/examples folder only"
    elif args.ai_guide_only:
        targets = [Path("kerykeion/llms.txt")]
        exclude_release_notes = False
        mode_description = "kerykeion/llms.txt only"
    elif args.skill_only:
        targets = [Path("skills/kerykeion")]
        exclude_release_notes = False
        # Skill blocks are copy-pasted individually into foreign codebases, so
        # the gate must prove each one stands alone.
        args.isolated = True
        mode_description = "skills/kerykeion only (isolated blocks, no import prelude)"
    elif args.all_files:
        targets = args.paths or [Path(".")]
        exclude_release_notes = False
        mode_description = "all markdown files"
    elif args.all_no_release:
        targets = args.paths or [Path(".")]
        exclude_release_notes = True
        mode_description = "all markdown files (excluding release notes)"
    else:
        # Default: README, llms.txt, and site/docs (or user-specified paths if provided)
        if args.paths:
            targets = args.paths
            # Report what was actually scanned: printing the default corpus for
            # an explicit path list misnames the run in its own log.
            mode_description = ", ".join(str(p) for p in args.paths)
        else:
            targets = [Path("README.md"), Path("kerykeion/llms.txt"), Path("site/docs"), Path("site/examples"), Path("skills/kerykeion")]
            mode_description = (
                "README.md, kerykeion/llms.txt, site/docs, site/examples, and "
                "skills/kerykeion (default; skill blocks always run isolated)"
            )
        exclude_release_notes = True

    print(f"� Testing Python snippets in {mode_description}")

    md_files = find_markdown_files(targets, exclude_release_notes=exclude_release_notes)
    print(f"📄 Found {len(md_files)} markdown files")

    total_snippets = 0
    failed_snippets = 0

    for md_file in md_files:
        try:
            # Explicit UTF-8: the corpus contains em-dashes, arrows and emoji,
            # so a non-UTF-8 locale would otherwise raise UnicodeDecodeError
            # and be swallowed as a skipped file.
            content = md_file.read_text(encoding="utf-8")
            snippets = extract_python_snippets(content)

            if not snippets:
                continue

            print(f"\n📝 {md_file} ({len(snippets)} snippets)")

            # Skill blocks are copy-pasted one at a time into foreign
            # codebases, so they always run isolated (bare, decided below)
            # whatever mode is running.
            isolated = args.isolated or md_file.is_relative_to(SKILL_DIR)

            # Snippets on one page often build on each other. A single clean
            # page-level execution proves the same sequential contract as the
            # old cumulative N executions, without quadratic process startup.
            # If it fails (or hits the narrowly ignored GeoNames-warning path),
            # replay cumulatively to identify the exact failing block(s).
            dedented_snippets = [textwrap.dedent(snippet) for snippet in snippets]

            if isolated:
                # Isolation means "own process, no shared page context". Only
                # the skill corpus additionally runs bare: its blocks must
                # stand alone when pasted into a foreign codebase, while the
                # docs corpus is authored against the injected prelude —
                # stripping it there reports a healthy corpus as broken.
                bare = md_file.is_relative_to(SKILL_DIR)
                # Each isolated snippet already runs in its own subprocess with
                # its own tempfile and timeout, so the runs share no state;
                # dispatching them through a pool just stops dozens of
                # sequential interpreter startups from being one long
                # single-core wait.
                with ThreadPoolExecutor(max_workers=8) as pool:
                    outcomes = list(
                        pool.map(
                            lambda code: test_snippet(code, timeout=args.timeout, bare=bare),
                            dedented_snippets,
                        )
                    )
                for i, (success, error) in enumerate(outcomes, 1):
                    total_snippets += 1
                    if success:
                        print(f"  ✅ Snippet {i}: {error if error else 'OK'}")
                    else:
                        print(f"  ❌ Snippet {i}:")
                        print(f"     {error if error else 'Unknown error'}")
                        failed_snippets += 1
                continue

            combined_success, combined_error = test_snippet(
                "\n".join(dedented_snippets), timeout=args.timeout
            )
            total_snippets += len(snippets)
            if combined_success and combined_error is None:
                print(f"  ✅ All {len(snippets)} snippets: OK")
                continue

            print("  Page-level run failed; replaying snippets for diagnostics")
            page_context = ""
            for i, dedented in enumerate(dedented_snippets, 1):
                # Dedent the snippet BEFORE concatenation: the joint dedent
                # inside test_snippet is a no-op once the accumulated context
                # is flush-left, which would leave an indented snippet
                # syntactically absorbed by the last context block.
                success, error = test_snippet(page_context + "\n" + dedented, timeout=args.timeout)

                if success:
                    status = error if error else "OK"
                    print(f"  ✅ Snippet {i}: {status}")
                    if error is None:
                        # Only a genuinely clean run may feed the page context;
                        # a masked pass (ignored warning) could poison every
                        # later snippet on the page.
                        page_context += "\n" + dedented
                else:
                    # Show full error for debugging
                    error_msg = error if error else "Unknown error"
                    print(f"  ❌ Snippet {i}:")
                    print(f"     {error_msg}")
                    failed_snippets += 1

        except Exception as e:
            # A file we cannot even read is a gate failure, not a skip:
            # counting it keeps the run from reporting a green 0/0.
            print(f"❌ Error reading {md_file}: {e}")
            failed_snippets += 1
            total_snippets += 1

    print(f"\n📊 Results: {total_snippets - failed_snippets}/{total_snippets} snippets passed")

    if failed_snippets > 0:
        print(f"❌ {failed_snippets} snippets failed")
        sys.exit(1)
    if total_snippets == 0:
        # The corpus resolved to files, but none of them held a runnable block.
        # Reporting success here is the same lie as an empty corpus: a renamed
        # fence language or a docs reshuffle would verify nothing, loudly green.
        print("❌ No snippets were found to run; refusing to report success.")
        sys.exit(1)
    print("🎉 All snippets passed!")


if __name__ == "__main__":
    main()
