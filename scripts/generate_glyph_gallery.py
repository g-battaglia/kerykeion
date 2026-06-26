#!/usr/bin/env python3
"""Generate a versioned, self-contained glyph gallery (SVG poster + Markdown page)
that illustrates every chart glyph Kerykeion renders. Pure illustration — glyph +
name + id, grouped by category. The SVG carries its own light background so it
renders identically on GitHub, MkDocs and any docs theme.

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

ROOT = pathlib.Path(__file__).resolve().parent.parent
TPL = ROOT / "kerykeion/charts/templates/chart.xml"

defs = TPL.read_text(encoding="utf-8")
defs = defs[defs.index("GLYPHS:BEGIN"):defs.index("GLYPHS:END")]
_matches = re.findall(r'<symbol id="([^"]+)">(.*?)</symbol>', defs, re.S)
_ids = [sid for sid, _ in _matches]
_dupes = sorted({sid for sid in _ids if _ids.count(sid) > 1})
if _dupes:
    raise ValueError(f"duplicate glyph ids in {TPL}: {', '.join(_dupes)}")
SYM = dict(_matches)

SIGNS = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]


def box(i):
    return 32 if i in SIGNS else (10 if i.startswith("orb") else (12 if i == "retrograde" else 24))


NAME = {
 "Sun": "Sun", "Moon": "Moon", "Mercury": "Mercury", "Venus": "Venus", "Mars": "Mars", "Jupiter": "Jupiter",
 "Saturn": "Saturn", "Uranus": "Uranus", "Neptune": "Neptune", "Pluto": "Pluto", "Chiron": "Chiron",
 "Earth": "Earth", "Mean_Lilith": "Mean Lilith", "True_Lilith": "True Lilith",
 "Mean_North_Lunar_Node": "Mean North Node", "True_North_Lunar_Node": "True North Node",
 "Mean_South_Lunar_Node": "Mean South Node", "True_South_Lunar_Node": "True South Node",
 "Ceres": "Ceres", "Pallas": "Pallas", "Juno": "Juno", "Vesta": "Vesta", "Pholus": "Pholus",
 "Eris": "Eris", "Sedna": "Sedna", "Haumea": "Haumea", "Makemake": "Makemake", "Ixion": "Ixion", "Orcus": "Orcus", "Quaoar": "Quaoar",
 "Cupido": "Cupido", "Hades": "Hades", "Zeus": "Zeus", "Kronos": "Kronos", "Apollon": "Apollon", "Admetos": "Admetos", "Vulkanus": "Vulkanus", "Poseidon": "Poseidon",
 "Ascendant": "Ascendant", "Medium_Coeli": "Medium Coeli", "Descendant": "Descendant", "Imum_Coeli": "Imum Coeli",
 "Vertex": "Vertex", "Anti_Vertex": "Anti-Vertex", "East_Point": "East Point", "FixedStar": "Fixed Star", "Midpoint": "Midpoint",
 "Pars_Fortunae": "Pars Fortunae", "Pars_Spiritus": "Pars Spiritus", "Pars_Amoris": "Pars Amoris", "Pars_Fidei": "Pars Fidei",
 "Ari": "Aries", "Tau": "Taurus", "Gem": "Gemini", "Can": "Cancer", "Leo": "Leo", "Vir": "Virgo",
 "Lib": "Libra", "Sco": "Scorpio", "Sag": "Sagittarius", "Cap": "Capricorn", "Aqu": "Aquarius", "Pis": "Pisces",
 "orb0": "Conjunction", "orb30": "Semi-sextile", "orb45": "Semi-square", "orb60": "Sextile", "orb72": "Quintile",
 "orb90": "Square", "orb120": "Trine", "orb135": "Sesquiquadrate", "orb144": "Biquintile", "orb150": "Quincunx", "orb180": "Opposition", "retrograde": "Retrograde",
}
ANGLE = {"orb0": "0°", "orb30": "30°", "orb45": "45°", "orb60": "60°", "orb72": "72°", "orb90": "90°",
         "orb120": "120°", "orb135": "135°", "orb144": "144°", "orb150": "150°", "orb180": "180°"}

SECTIONS = [
 ("Luminaries & planets", ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]),
 ("Minor bodies & Lilith", ["Chiron", "Earth", "Mean_Lilith", "True_Lilith", "Ceres", "Pallas", "Juno", "Vesta", "Pholus"]),
 ("Lunar nodes", ["Mean_North_Lunar_Node", "True_North_Lunar_Node", "Mean_South_Lunar_Node", "True_South_Lunar_Node"]),
 ("Trans-Neptunian objects", ["Eris", "Sedna", "Haumea", "Makemake", "Ixion", "Orcus", "Quaoar"]),
 ("Uranian points", ["Cupido", "Hades", "Zeus", "Kronos", "Apollon", "Admetos", "Vulkanus", "Poseidon"]),
 ("Arabic parts (Lots)", ["Pars_Fortunae", "Pars_Spiritus", "Pars_Amoris", "Pars_Fidei"]),
 ("Angles & special points", ["Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli", "Vertex", "Anti_Vertex", "East_Point", "FixedStar", "Midpoint"]),
 ("Zodiac signs", SIGNS),
 ("Aspects", ["orb0", "orb30", "orb45", "orb60", "orb72", "orb90", "orb120", "orb135", "orb144", "orb150", "orb180"]),
 ("Other", ["retrograde"]),
]

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


def ink(inner):  # neutralise theme variables for a standalone poster
    return re.sub(r'var\([^)]*\)', INK, inner)


# compute layout & height
rows = []
y = TITLE
for title, ids in SECTIONS:
    rows.append(("hdr", title, y))
    y += HDR
    for row in chunks(ids, COLS):
        rows.append(("row", row, y))
        y += CH
    y += GAP
H = y + M - GAP
W = M * 2 + COLS * CW


def glyph_g(i, gx, gy):
    b = box(i)
    s = DISP / b
    return f'<g transform="translate({gx:.1f},{gy:.1f}) scale({s:.4f})">{ink(SYM[i])}</g>'


parts = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="{BG}"/>',
         f'<text x="{M}" y="40" font-family="-apple-system,Segoe UI,Roboto,sans-serif" font-size="26" font-weight="700" fill="{INK}">Kerykeion — Chart Glyphs</text>',
         f'<text x="{M}" y="62" font-family="-apple-system,Segoe UI,Roboto,sans-serif" font-size="13" fill="{SUB}">Astrological symbols rendered in Kerykeion charts — planets, points, zodiac signs and aspects.</text>']

for kind, payload, yy in rows:
    if kind == "hdr":
        parts.append(f'<text x="{M}" y="{yy + 30:.0f}" font-family="-apple-system,Segoe UI,Roboto,sans-serif" font-size="16" font-weight="600" fill="{INK}">{html.escape(payload)}</text>')
        parts.append(f'<line x1="{M}" y1="{yy + 38:.0f}" x2="{W - M}" y2="{yy + 38:.0f}" stroke="{RULE}" stroke-width="1"/>')
    else:
        for col, i in enumerate(payload):
            cl = M + col * CW
            parts.append(f'<rect x="{cl + 6}" y="{yy:.0f}" width="{CW - 12}" height="{CH - 12}" rx="9" fill="{CARD}" stroke="{BORDER}"/>')
            parts.append(glyph_g(i, cl + (CW - DISP) / 2, yy + 10))
            cx = cl + CW / 2
            label = NAME.get(i, i) + (f" {ANGLE[i]}" if i in ANGLE else "")
            parts.append(f'<text x="{cx:.1f}" y="{yy + DISP + 30:.0f}" text-anchor="middle" font-family="-apple-system,Segoe UI,Roboto,sans-serif" font-size="13" font-weight="600" fill="{INK}">{html.escape(label)}</text>')
            parts.append(f'<text x="{cx:.1f}" y="{yy + DISP + 46:.0f}" text-anchor="middle" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="9.5" fill="{SUB}">{html.escape(i)}</text>')

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'font-family="sans-serif">\n' + "\n".join(parts) + "\n</svg>\n")


# ---- markdown page ---------------------------------------------------------
def md(img_rel):
    lines = ["# Chart Glyphs", "",
             "Visual reference for the astrological glyphs used in Kerykeion charts: "
             "planets, points, lunar nodes, asteroids, Trans-Neptunian and Uranian points, "
             "Arabic parts, zodiac signs and aspects.", "",
             f"![Kerykeion chart glyphs]({img_rel})", "",
             "## Glyphs by category", ""]
    for title, ids in SECTIONS:
        lines.append(f"### {title}")
        lines.append("")
        lines.append("| Glyph (id) | Name |")
        lines.append("|---|---|")
        for i in ids:
            nm = NAME.get(i, i) + (f" {ANGLE[i]}" if i in ANGLE else "")
            lines.append(f"| `{i}` | {nm} |")
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

    print(f"poster {W}x{H}px, {sum(len(ids) for _, ids in SECTIONS)} glyphs")
    for w in written:
        print("  wrote", w)


if __name__ == "__main__":
    main()
