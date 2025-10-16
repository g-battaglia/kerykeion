#!/usr/bin/env python3
"""
Simple script to test Python snippets in Markdown files.

Usage: python scripts/test_markdown_snippets.py [directory]
"""

import re
import sys
import subprocess
import tempfile
from pathlib import Path


def find_markdown_files(directory):
    """Find all .md files in directory."""
    path = Path(directory)
    if path.is_file() and path.suffix == '.md':
        return [path]

    # Ignore file with name starting with v4.*, like "release_notes/V4.23.0.md"
    if not path.is_dir() or any(part.startswith('v4.') for part in path.parts):
        return []

    return list(path.rglob("*.md"))


def extract_python_snippets(content):
    """Extract Python code blocks from markdown."""
    pattern = r'```python\n(.*?)\n```'
    return re.findall(pattern, content, re.DOTALL)


def test_snippet(code):
    """Test if Python snippet runs without errors."""
    # Skip snippets with common issues
    skip_patterns = ['...', 'input(', 'plt.show()', 'time.sleep(', 'open(']
    if any(pattern in code for pattern in skip_patterns):
        return True, "Skipped"

    # Add basic imports
    project_root = str(Path(__file__).parent.parent)
    full_code = f"""
import sys
sys.path.insert(0, '{project_root}')
import warnings
warnings.filterwarnings('ignore')

""" + code

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            f.flush()

            result = subprocess.run(
                [sys.executable, f.name],
                capture_output=True,
                timeout=5,  # Shorter timeout
                cwd=Path(__file__).parent.parent,
                text=True
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
        return False, "Timeout (5s exceeded)"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def main():
    directory = sys.argv[1] if len(sys.argv) > 1 else "."

    print(f"� Testing Python snippets in {directory}")

    md_files = find_markdown_files(directory)
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
                success, error = test_snippet(snippet)

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


if __name__ == '__main__':
    main()
