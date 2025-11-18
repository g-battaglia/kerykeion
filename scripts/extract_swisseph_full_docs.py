import swisseph as swe
import inspect
from pathlib import Path
import html
import argparse

# Minimal modern CSS for HTML output
CSS = """
body { font-family: system-ui, sans-serif; margin: 0; display: flex; background: #f9fafb; color: #222; }
nav { width: 280px; height: 100vh; overflow-y: auto; background: #fff; border-right: 1px solid #ddd; padding: 1rem; position: sticky; top: 0; }
nav h1 { font-size: 1.1rem; margin-bottom: 0.5rem; }
nav ul { list-style: none; padding: 0; margin: 0; }
nav li { margin: 0.3rem 0; }
nav a { color: #0366d6; text-decoration: none; }
nav a:hover { text-decoration: underline; }
main { flex: 1; padding: 2rem; overflow-y: auto; }
pre { background: #f5f5f5; border: 1px solid #ddd; padding: 0.7rem; border-radius: 6px; white-space: pre-wrap; }
table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
th, td { border: 1px solid #ddd; padding: 0.4rem 0.6rem; text-align: left; }
th { background: #f0f0f0; }
code { background: #eee; padding: 0.1rem 0.3rem; border-radius: 4px; font-family: monospace; }
"""

def collect_symbols(module):
    """Collect all public attributes (functions, constants, classes, etc.) from the module."""
    symbols = {}
    for name, value in module.__dict__.items():
        if name.startswith("_"):
            continue
        kind = type(value).__name__
        doc = inspect.getdoc(value)
        symbols[name] = {"type": kind, "value": value, "doc": doc}
    return symbols

def generate_html(symbols):
    """Generate a full HTML documentation page."""
    toc = []
    content = []

    toc.append("<ul>")
    for name in sorted(symbols.keys()):
        toc.append(f'<li><a href="#{name}"><code>{html.escape(name)}</code></a></li>')
    toc.append("</ul>")

    for name, data in sorted(symbols.items()):
        value = data["value"]
        doc = data["doc"]
        kind = data["type"]

        if isinstance(value, (int, float, str, tuple)):
            val_repr = html.escape(str(value))
        else:
            val_repr = html.escape(repr(value))

        content.append(f"<section id='{name}'>")
        content.append(f"<h2><code>{name}</code> <small>({kind})</small></h2>")
        content.append(f"<p><strong>Value:</strong> <code>{val_repr}</code></p>")
        if doc:
            content.append(f"<pre>{html.escape(doc)}</pre>")
        content.append("</section>")

    html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Full swisseph documentation</title>
<style>{CSS}</style>
</head>
<body>
<nav><h1>Index</h1>{''.join(toc)}</nav>
<main>
<h1>Full documentation of <code>swisseph</code></h1>
{''.join(content)}
</main>
</body>
</html>"""
    return html_page

def generate_markdown(symbols):
    """Generate a Markdown version of the documentation."""
    lines = []
    lines.append("# Full documentation of `swisseph`")
    lines.append("")
    lines.append("## Index")
    lines.append("")

    for name in sorted(symbols.keys()):
        anchor = name.lower()
        lines.append(f"- [`{name}`](#{anchor})")
    lines.append("")

    for name, data in sorted(symbols.items()):
        value = data["value"]
        doc = data["doc"]
        kind = data["type"]

        if isinstance(value, (int, float, str, tuple)):
            val_repr = str(value)
        else:
            val_repr = repr(value)

        lines.append(f"## `{name}` ({kind})")
        lines.append("")
        lines.append(f"- Type: `{kind}`")
        lines.append(f"- Value: `{val_repr}`")
        lines.append("")
        if doc:
            lines.append("```")
            lines.append(doc)
            lines.append("```")
            lines.append("")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(
        description="Extract all public symbols from swisseph and generate documentation."
    )
    parser.add_argument(
        "--markdown",
        "-m",
        action="store_true",
        help="Generate Markdown instead of HTML (default: HTML)",
    )
    args = parser.parse_args()

    symbols = collect_symbols(swe)

    if args.markdown:
        output = generate_markdown(symbols)
        out_path = Path("swisseph_full.md")
    else:
        output = generate_html(symbols)
        out_path = Path("swisseph_full.html")

    out_path.write_text(output, encoding="utf-8")
    print(f"✅ Created {out_path} with {len(symbols)} symbols.")

if __name__ == "__main__":
    main()
