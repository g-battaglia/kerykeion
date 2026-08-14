#!/usr/bin/env python3
"""Generate a versioned, self-contained glyph gallery (SVG poster + Markdown page)
that illustrates every chart glyph Kerykeion renders. Pure illustration — glyph +
name + id, grouped by family. The SVG carries its own light background so it
renders identically on GitHub, MkDocs and any docs theme.

The contents come from `glyph_catalog.py`, the same list the templates are built
from, so a symbol cannot ship without being documented. It used to carry its own
section table and its own copy of the box rule, and by the time anyone looked it
was missing five points — Interpolated Lilith, Mean/True Priapus, White Moon,
Interpolated Perigee — and describing a set the library no longer drew.

Colours are resolved from the light theme rather than flattened to one ink. That
is not decoration: six of the lunar-apside points wear two shapes between them
and are told apart by colour alone, so a monochrome poster would print three
identical Liliths and three identical perigee marks.

Writes the Kerykeion docs by default. Pass --api-docs-dir to ALSO write the page
into another docs tree (opt-in; nothing outside this repo is touched otherwise):

  uv run python scripts/generate_glyph_gallery.py
  uv run python scripts/generate_glyph_gallery.py --api-docs-dir ../some-api/RapidAPI_Docs
"""
from __future__ import annotations
import argparse
import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from glyph_catalog import IDS, box_of, families  # noqa: E402

TPL = ROOT / "kerykeion/charts/templates/chart.xml"
THEME = ROOT / "kerykeion/charts/themes/light.css"

defs = TPL.read_text(encoding="utf-8")
defs = defs[defs.index("GLYPHS:BEGIN"):defs.index("GLYPHS:END")]
_matches = re.findall(r'<symbol id="([^"]+)">(.*?)</symbol>', defs, re.S)
_ids = [sid for sid, _ in _matches]
_dupes = sorted({sid for sid in _ids if _ids.count(sid) > 1})
if _dupes:
    raise ValueError(f"duplicate glyph ids in {TPL}: {', '.join(_dupes)}")
if _ids != IDS:
    raise ValueError(
        "the templates and glyph_catalog.py disagree. Missing from the templates: "
        f"{[i for i in IDS if i not in _ids]}; not in the catalog: "
        f"{[i for i in _ids if i not in IDS]}. Run build_chart_glyphs.py first."
    )
SYM = dict(_matches)


# ---- colour ----------------------------------------------------------------
_DECL = re.compile(r"(--kerykeion-[a-z0-9-]+)\s*:\s*([^;]+);")
_VAR = re.compile(r"var\(\s*(--[a-z0-9-]+)\s*(?:,\s*([^)]*))?\)")
THEME_VARS = dict(_DECL.findall(THEME.read_text(encoding="utf-8")))


def resolve(value: str, depth: int = 0) -> str:
    """Substitute `var(--x, fallback)` against the light theme, recursively.

    Theme variables are defined in terms of one another (`--...-mean-lilith:
    var(--kerykeion-color-secondary)`), so one pass is not enough. The depth cap
    is a cycle guard, not a policy: a self-referential declaration would
    otherwise hang the docs build.
    """
    if depth > 10:
        raise ValueError(f"cyclic CSS variable while resolving {value!r}")

    def sub(match: re.Match) -> str:
        name, fallback = match.group(1), (match.group(2) or "").strip()
        if name in THEME_VARS:
            return resolve(THEME_VARS[name].strip(), depth + 1)
        if fallback:
            return resolve(fallback, depth + 1)
        raise KeyError(f"{name} is used by a glyph but undefined in {THEME.name}")

    return _VAR.sub(sub, value)


def paint(inner: str) -> str:
    """The symbol as it renders under the light theme."""
    return resolve(inner)


# ---- labels ----------------------------------------------------------------
def caption(sid: str, label: str) -> str:
    """`orb144` -> "Biquintile 144°". The angle is in the id; a second table
    listing it again is a second thing to forget to update."""
    return f"{label} {sid[3:]}°" if sid.startswith("orb") else label


SECTIONS = [(family, [(sid, caption(sid, label)) for sid, label in items])
            for family, items in families()]

# ---- poster geometry -------------------------------------------------------
INK = "#1f2433"
SUB = "#8a8a9e"
CARD = "#fafafe"
BORDER = "#ececf2"
BG = "#ffffff"
RULE = "#e2e2ec"
COLS = 6
M = 28
CW = 168
DISP = 64
CH = 128
HDR = 48
TITLE = 78
GAP = 8


def chunks(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


# compute layout & height
rows = []
y = TITLE
for title, items in SECTIONS:
    rows.append(("hdr", title, y))
    y += HDR
    for row in chunks(items, COLS):
        rows.append(("row", (title, row), y))
        y += CH
    y += GAP
H = y + M - GAP
W = M * 2 + COLS * CW


def glyph_g(sid, family, gx, gy):
    b = box_of(family)
    s = DISP / b
    return f'<g transform="translate({gx:.1f},{gy:.1f}) scale({s:.4f})">{paint(SYM[sid])}</g>'


parts = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="{BG}"/>',
         f'<text x="{M}" y="40" font-family="-apple-system,Segoe UI,Roboto,sans-serif" font-size="26" font-weight="700" fill="{INK}">Kerykeion — Chart Glyphs</text>',
         f'<text x="{M}" y="62" font-family="-apple-system,Segoe UI,Roboto,sans-serif" font-size="13" fill="{SUB}">Astrological symbols rendered in Kerykeion charts, in the colours of the light theme.</text>']

for kind, payload, yy in rows:
    if kind == "hdr":
        parts.append(f'<text x="{M}" y="{yy + 30:.0f}" font-family="-apple-system,Segoe UI,Roboto,sans-serif" font-size="16" font-weight="600" fill="{INK}">{html.escape(payload)}</text>')
        parts.append(f'<line x1="{M}" y1="{yy + 38:.0f}" x2="{W - M}" y2="{yy + 38:.0f}" stroke="{RULE}" stroke-width="1"/>')
    else:
        family, row = payload
        for col, (sid, label) in enumerate(row):
            cl = M + col * CW
            parts.append(f'<rect x="{cl + 6}" y="{yy:.0f}" width="{CW - 12}" height="{CH - 12}" rx="9" fill="{CARD}" stroke="{BORDER}"/>')
            parts.append(glyph_g(sid, family, cl + (CW - DISP) / 2, yy + 10))
            cx = cl + CW / 2
            parts.append(f'<text x="{cx:.1f}" y="{yy + DISP + 30:.0f}" text-anchor="middle" font-family="-apple-system,Segoe UI,Roboto,sans-serif" font-size="13" font-weight="600" fill="{INK}">{html.escape(label)}</text>')
            parts.append(f'<text x="{cx:.1f}" y="{yy + DISP + 46:.0f}" text-anchor="middle" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="9.5" fill="{SUB}">{html.escape(sid)}</text>')

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'font-family="sans-serif">\n' + "\n".join(parts) + "\n</svg>\n")


# ---- markdown page ---------------------------------------------------------
def md(img_rel):
    lines = ["# Chart Glyphs", "",
             "Visual reference for the astrological glyphs used in Kerykeion charts: "
             "planets, lunar nodes and apsides, centaurs, asteroids, Trans-Neptunian and "
             "Uranian points, Arabic parts, angles, zodiac signs and aspects.", "",
             "Every glyph is geometry — no font is needed to render a chart. The colours "
             "shown are the light theme's; each is a CSS variable a theme can override.", "",
             f"![Kerykeion chart glyphs]({img_rel})", "",
             "## Glyphs by family", ""]
    for title, items in SECTIONS:
        lines += [f"### {title}", "", "| Glyph (id) | Name |", "|---|---|"]
        lines += [f"| `{sid}` | {label} |" for sid, label in items]
        lines.append("")
    return "\n".join(lines)


# ---- writers ---------------------------------------------------------------
def write_docs(docs_dir: pathlib.Path, md_name: str) -> list[str]:
    assets = docs_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "chart-glyphs.svg").write_text(svg, encoding="utf-8")
    (docs_dir / md_name).write_text(md("assets/chart-glyphs.svg"), encoding="utf-8")
    return [str(assets / "chart-glyphs.svg"), str(docs_dir / md_name)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the chart-glyph gallery (SVG poster + Markdown).")
    parser.add_argument(
        "--api-docs-dir", type=pathlib.Path, default=None,
        help="Optional extra docs directory (e.g. an Astrologer-API RapidAPI_Docs/) to also "
             "write 'Chart_Glyphs.md' + assets into. Opt-in; nothing outside this repo otherwise.",
    )
    args = parser.parse_args()

    written = write_docs(ROOT / "site" / "docs", "chart-glyphs.md")
    if args.api_docs_dir is not None:
        if args.api_docs_dir.is_dir():
            written += write_docs(args.api_docs_dir, "Chart_Glyphs.md")
        else:
            print(f"  --api-docs-dir not found, skipped: {args.api_docs_dir}")

    print(f"poster {W}x{H}px, {sum(len(items) for _, items in SECTIONS)} glyphs")
    for w in written:
        print("  wrote", w)


if __name__ == "__main__":
    main()
