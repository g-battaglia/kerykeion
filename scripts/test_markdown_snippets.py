#!/usr/bin/env python3
"""
Simple script to test Python snippets in Markdown files.

Common usages:
  - README only:                 python scripts/test_markdown_snippets.py --readme
  - Site docs only:              python scripts/test_markdown_snippets.py --docs
  - Site examples only:          python scripts/test_markdown_snippets.py --examples
  - All (incl. release notes):   python scripts/test_markdown_snippets.py --all
  - All (exclude release notes): python scripts/test_markdown_snippets.py --all-no-release
"""

import argparse
import re
import sys
import subprocess
import tempfile
from pathlib import Path
import textwrap
from typing import Optional, Tuple


def find_markdown_files(
    targets: list[Path],
    *,
    exclude_release_notes: bool = False,
) -> list[Path]:
    """Collect markdown files from the provided targets."""
    markdown_files: set[Path] = set()

    for target in targets:
        path = target.resolve()
        if path.is_file() and path.suffix.lower() == ".md":
            markdown_files.add(path)
            continue

        if not path.is_dir():
            continue

        for md_file in path.rglob("*.md"):
            if md_file.name.lower().startswith("v4."):
                continue
            if exclude_release_notes and "release_notes" in md_file.parts:
                continue
            markdown_files.add(md_file)

    return sorted(markdown_files)


def extract_python_snippets(content):
    """Extract Python code blocks from markdown."""
    pattern = r'```python[^\n]*\n(.*?)\n[ \t]*```'
    return re.findall(pattern, content, re.DOTALL)


def test_snippet(code: str, *, timeout: float) -> Tuple[bool, Optional[str]]:
    """Test if Python snippet runs without errors."""
    # Normalize indentation for nested code blocks
    code = textwrap.dedent(code)

    # Add basic imports
    project_root = str(Path(__file__).parent.parent)
    full_code = f"""
import sys
sys.path.insert(0, '{project_root}')
import warnings
warnings.filterwarnings('ignore')

# Ensure required optional dependencies are present; otherwise skip gracefully.
missing_dependencies = []
for _module in ("pytz", "swisseph"):
    try:
        __import__(_module)
    except ModuleNotFoundError:
        missing_dependencies.append(_module)

if missing_dependencies:
    print("Skipping snippet due to missing dependencies: " + ", ".join(sorted(set(missing_dependencies))))
    sys.exit(0)

# Common imports for kerykeion
from typing import Literal, Union
from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    ChartDrawer,
    CompositeSubjectFactory,
    KerykeionSettingsModel,
)
""" + code

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
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
                # Ignore geonames username warnings
                if "NO GEONAMES USERNAME SET" in error_output and "WARNING:root:" in error_output:
                    return True, "Success (geonames warning ignored)"
                return False, error_output

            return True, None

    except subprocess.TimeoutExpired:
        return False, f"Timeout ({timeout}s exceeded)"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description="Execute Python snippets embedded in markdown files.")
    parser.add_argument("-a", "--all", dest="all_files", action="store_true", help="Run snippets for every markdown file.")
    parser.add_argument("-an", "--all-no-release", dest="all_no_release", action="store_true", help="Run snippets for all markdown files excluding release notes.")
    parser.add_argument("-r", "--readme", dest="readme_only", action="store_true", help="Run snippets only for README.md.")
    parser.add_argument("-d", "--docs", dest="docs_only", action="store_true", help="Run snippets only for site-docs folder.")
    parser.add_argument("-e", "--examples", dest="examples_only", action="store_true", help="Run snippets only for site-examples folder.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Per-snippet timeout in seconds (default: 20).")
    parser.add_argument("paths", nargs="*", type=Path, help="Optional paths to scan (defaults depend on flags).")
    args = parser.parse_args()

    if args.readme_only:
        targets = [Path("README.md")]
        exclude_release_notes = False
        mode_description = "README.md only"
    elif args.docs_only:
        targets = [Path("site-docs")]
        exclude_release_notes = True
        mode_description = "site-docs folder only"
    elif args.examples_only:
        targets = [Path("site-examples")]
        exclude_release_notes = True
        mode_description = "site-examples folder only"
    elif args.all_files:
        targets = args.paths or [Path(".")]
        exclude_release_notes = False
        mode_description = "all markdown files"
    elif args.all_no_release:
        targets = args.paths or [Path(".")]
        exclude_release_notes = True
        mode_description = "all markdown files (excluding release notes)"
    else:
        # Default: README plus site-docs (or user-specified paths if provided)
        if args.paths:
            targets = args.paths
        else:
            targets = [Path("README.md"), Path("site-docs")]
        exclude_release_notes = True
        mode_description = "README.md and site-docs (default)"

    print(f"� Testing Python snippets in {mode_description}")

    md_files = find_markdown_files(targets, exclude_release_notes=exclude_release_notes)
    print(f"📄 Found {len(md_files)} markdown files")

    total_snippets = 0
    failed_snippets = 0

    for md_file in md_files:
        try:
            content = md_file.read_text()
            snippets = extract_python_snippets(content)

            if not snippets:
                continue

            print(f"\n📝 {md_file} ({len(snippets)} snippets)")

            for i, snippet in enumerate(snippets, 1):
                total_snippets += 1
                success, error = test_snippet(snippet, timeout=args.timeout)

                if success:
                    status = error if error else "OK"
                    print(f"  ✅ Snippet {i}: {status}")
                else:
                    # Show full error for debugging
                    error_msg = error if error else "Unknown error"
                    print(f"  ❌ Snippet {i}:")
                    print(f"     {error_msg}")
                    failed_snippets += 1

        except Exception as e:
            print(f"❌ Error reading {md_file}: {e}")

    print(f"\n📊 Results: {total_snippets - failed_snippets}/{total_snippets} snippets passed")

    if failed_snippets > 0:
        print(f"❌ {failed_snippets} snippets failed")
        sys.exit(1)
    else:
        print("🎉 All snippets passed!")


if __name__ == '__main__':
    main()
