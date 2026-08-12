#!/usr/bin/env python3
"""Render kerykeion's whole SVG surface, for looking at.

The test suite answers "did this change what it said it would". This answers a
different question — "does it *look* right" — which only an eye can settle, and
only if the eye is shown the awkward cases and not just the pretty ones.

So the sweep is organised by axis. Each section holds one dimension steady at
every value it can take while the rest stay at a sane default: all six themes,
all ten languages, all twenty-three house systems, all eleven perspectives, all
forty-eight sidereal modes, every chart type, every output template, every
opt-in mark. Then a handful of sections that are deliberately not defaults at
all — polar and equatorial latitudes, dates before the common era, charts with
a hundred and more active points — because that is where layout gives way.

A render that raises is recorded and shown as a failure card rather than
stopping the run: a gallery that omits what broke is worse than no gallery.

The output is a folder of SVGs plus an index page that opens any of them full
screen and steps through the whole sweep with a slider. It is not committed —
it is several hundred charts and tens of megabytes — but this script is, so any
checkout can rebuild it.

Usage:
    poe gallery                       # render everything, then write the page
    poe gallery:index                 # rewrite the page only, from cards.json
    python scripts/generate_svg_validation_gallery.py [output_dir] [--index-only]

Dates before about 1600 fall outside the default ephemeris tier and are drawn as
failure cards without it, so the poe task sets LIBEPHEMERIS_PRECISION=extended.
"""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, get_args

from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    ChartDrawer,
    CompositeSubjectFactory,
    MidpointFactory,
    PlanetaryReturnFactory,
    SecondaryProgressionFactory,
    SolarArcFactory,
)
from kerykeion.schemas.literals import (
    HousesSystemIdentifier,
    KerykeionChartLanguage,
    KerykeionChartTheme,
    PerspectiveType,
    SiderealMode,
)
from kerykeion.settings.chart_defaults import DEFAULT_CHART_COLORS
from kerykeion.settings.config_constants import (
    ALL_ACTIVE_ASPECTS,
    ALL_ACTIVE_POINTS,
    DEFAULT_FIXED_STARS,
    TRADITIONAL_ASTROLOGY_ACTIVE_POINTS,
    URANIAN_ACTIVE_POINTS,
)

_ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
INDEX_ONLY = "--index-only" in sys.argv
OUT = Path(_ARGS[0]) if _ARGS else Path(__file__).parent.parent / "svg_validation_gallery"
OUT.mkdir(parents=True, exist_ok=True)

THEMES = list(get_args(KerykeionChartTheme))
LANGUAGES = list(get_args(KerykeionChartLanguage))
HOUSE_SYSTEMS = list(get_args(HousesSystemIdentifier))
PERSPECTIVES = list(get_args(PerspectiveType))
SIDEREAL_MODES = list(get_args(SiderealMode))
STYLES = ["classic", "modern"]

ALL_MARKS = dict(
    show_motion_state=True,
    show_out_of_bounds=True,
    show_aspect_movement=True,
    show_relationship_score=True,
    show_ayanamsa_value=True,
    show_polar_fallback_note=True,
)


@dataclass
class Card:
    filename: str
    title: str
    detail: str
    aspect: str = "890/580"
    error: Optional[str] = None
    facts: dict = field(default_factory=dict)


def inspect_svg(svg: str) -> dict:
    """What the finished markup actually contains.

    Read back out of the rendered file rather than restated from the request:
    the point of a validation sweep is to describe what was produced, and a
    summary copied from the arguments would agree with itself even when the
    renderer disagreed with both.
    """
    facts: dict[str, Any] = {"bytes": len(svg.encode("utf-8"))}

    viewbox = re.search(r"viewBox='([^']+)'", svg)
    if viewbox:
        facts["viewBox"] = viewbox.group(1)

    try:
        ET.fromstring(svg)
        facts["xml"] = "well-formed"
    except ET.ParseError as exc:
        facts["xml"] = f"INVALID — {exc}"

    nodes = Counter(re.findall(r"kr:node='([A-Za-z_]+)'", svg))
    facts["nodes"] = dict(sorted(nodes.items(), key=lambda kv: (-kv[1], kv[0])))
    facts["kr attributes"] = sorted(set(re.findall(r"\bkr:([a-z]+)=", svg)))

    elements = Counter(re.findall(r"<([a-zA-Z]+)[ />]", svg))
    facts["elements"] = dict(sorted(elements.items(), key=lambda kv: (-kv[1], kv[0]))[:10])

    title = re.search(r"<title>([^<]*)</title>", svg)
    if title:
        facts["title"] = html.unescape(title.group(1))

    panel = [html.unescape(m.group(2)) for m in re.finditer(r"Bottom_Left_Text_(\d)'[^>]*>([^<]*)</text>", svg)]
    if any(panel):
        facts["info panel"] = panel
    top = [html.unescape(m.group(2)) for m in re.finditer(r"Top_Left_Text_(\d)'[^>]*>([^<]*)</text>", svg)]
    if any(top):
        facts["subject block"] = top

    facts["css variables"] = "inlined or absent" if "var(--" not in svg else f"{len(set(re.findall(r'var\((--[a-z0-9-]+)', svg)))} referenced"
    themed = re.search(r"kr:node='Theme_Colors_Tag'", svg)
    facts["theme block"] = "present" if themed else "none"
    return facts


@dataclass
class Section:
    name: str
    blurb: str
    cards: list[Card] = field(default_factory=list)


# Raw: every backslash in here belongs to the CSS or the JavaScript. Without the
# r-prefix Python turned the JS "\n" escapes into real newlines, which broke the
# string literals they sat in and took the whole script down with them.
_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kerykeion SVG — validation sweep</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: #0e0f13; color: #e8e6e1;
         font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  body.locked {{ overflow: hidden; }}

  header {{ padding: 28px 32px 20px; border-bottom: 1px solid #24262e; }}
  h1 {{ margin: 0 0 6px; font-size: 22px; font-weight: 600; }}
  header p {{ margin: 0; color: #9aa0ab; max-width: 74ch; }}
  .totals {{ margin-top: 12px; font-size: 13px; color: #9aa0ab; }}
  .totals b {{ color: #e8e6e1; }}
  kbd {{ background: #23262f; border: 1px solid #343845; border-radius: 4px;
         padding: 1px 5px; font: 11px/1.4 ui-monospace, Menlo, monospace; color: #c6cad2; }}

  nav {{ position: sticky; top: 0; z-index: 5; display: flex; flex-wrap: wrap; gap: 6px;
         padding: 12px 32px; background: #14161c; border-bottom: 1px solid #24262e; }}
  nav a {{ color: #c6cad2; text-decoration: none; font-size: 12.5px; padding: 4px 10px;
           border: 1px solid #2c2f39; border-radius: 999px; }}
  nav a:hover {{ background: #1e212a; color: #fff; }}
  nav a em {{ font-style: normal; color: #7d838f; margin-left: 4px; }}

  section {{ padding: 30px 32px; border-bottom: 1px solid #1c1e25; }}
  h2 {{ margin: 0 0 4px; font-size: 18px; font-weight: 600; scroll-margin-top: 60px; }}
  .count {{ font-size: 12px; color: #7d838f; font-weight: 400; }}
  .failed {{ font-size: 12px; color: #ff8189; }}
  .blurb {{ margin: 0 0 18px; color: #9aa0ab; max-width: 82ch; font-size: 13.5px; }}

  .grid {{ display: grid; gap: 16px; grid-template-columns: repeat(auto-fill, minmax(430px, 1fr)); }}
  .card {{ margin: 0; background: #fff; border: 1px solid #2c2f39; border-radius: 8px;
           overflow: hidden; cursor: zoom-in; transition: border-color .12s, transform .12s; }}
  .card:hover, .card:focus-visible {{ border-color: #5c6270; transform: translateY(-1px); outline: none; }}
  .card:focus-visible {{ box-shadow: 0 0 0 2px #6f8cff; }}
  .card img {{ display: block; width: 100%; background: #fff; }}
  figcaption {{ background: #191c23; padding: 8px 12px; display: flex; flex-direction: column; gap: 2px; }}
  figcaption b {{ font-size: 13px; color: #f0eee9; font-weight: 600; }}
  figcaption span {{ font-size: 11.5px; color: #858b96;
                     font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
  .card.error {{ background: #1d1416; border-color: #5d2a30; cursor: default; }}
  .card.error pre {{ margin: 0; padding: 12px; color: #ff9ca3; font-size: 11.5px;
                     white-space: pre-wrap; word-break: break-word; }}

  /* ---- full-screen viewer ---- */
  /* minmax(0, …) rather than a bare 1fr: a bare fr track keeps an automatic
     minimum, so a tall chart grew the row and overflowed the screen instead of
     being scaled down into it. */
  .viewer {{ position: fixed; inset: 0; z-index: 50; display: none;
             grid-template-rows: auto minmax(0, 1fr) auto; background: #08090c; }}
  .viewer.open {{ display: grid; }}
  .viewer-bar {{ display: flex; align-items: center; gap: 14px; padding: 10px 16px;
                 background: #14161c; border-bottom: 1px solid #24262e; }}
  .viewer-bar .who {{ min-width: 0; flex: 1; }}
  .viewer-bar .who b {{ display: block; font-size: 14px; }}
  .viewer-bar .who span {{ display: block; font-size: 11.5px; color: #858b96;
                           font-family: ui-monospace, Menlo, monospace;
                           white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .viewer-bar .where {{ font-size: 12px; color: #7d838f; white-space: nowrap; }}
  .viewer-bar code {{ color: #b9c6ff; }}

  .facts {{ position: absolute; top: 52px; right: 14px; z-index: 2; width: min(560px, 92vw);
            max-height: calc(100vh - 150px); overflow: auto; padding: 14px 16px;
            background: #14161cf2; border: 1px solid #343845; border-radius: 8px;
            box-shadow: 0 18px 50px rgba(0,0,0,.6); backdrop-filter: blur(6px); }}
  .facts[hidden] {{ display: none; }}
  .facts dl {{ margin: 0; display: grid; grid-template-columns: max-content 1fr; gap: 5px 14px; }}
  .facts dt {{ font-size: 11.5px; color: #858b96; text-transform: lowercase; white-space: nowrap; }}
  .facts dd {{ margin: 0; font: 12px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace;
               color: #e8e6e1; word-break: break-word; }}
  .facts dd.bad {{ color: #ff9ca3; }}
  .viewer button {{ background: #23262f; color: #e8e6e1; border: 1px solid #343845;
                    border-radius: 6px; padding: 7px 13px; font-size: 14px; cursor: pointer; }}
  .viewer button:hover {{ background: #2e323d; }}
  .viewer button:disabled {{ opacity: .35; cursor: default; }}

  .viewer-stage {{ position: relative; min-height: 0; min-width: 0; overflow: hidden;
                   display: flex; align-items: center; justify-content: center;
                   padding: 18px; background: #08090c; }}
  /* White plate: most themes draw dark ink and would vanish on the dark ground.
     The plate tracks the scaled chart rather than the stage, so a wide chart
     does not sit on a tall white slab. */
  .viewer-stage img {{ max-width: 100%; max-height: 100%; width: auto; height: auto;
                       object-fit: contain; background: #fff;
                       border-radius: 6px; box-shadow: 0 12px 40px rgba(0,0,0,.55);
                       transform-origin: 0 0; will-change: transform; }}
  .viewer-stage.zoomed {{ cursor: grab; }}
  .viewer-stage.zoomed.dragging {{ cursor: grabbing; }}
  /* The edges step through the sweep; once zoomed they would fight the drag. */
  .viewer-stage.zoomed .edge {{ pointer-events: none; }}
  .zoom-badge {{ position: absolute; left: 14px; bottom: 14px; z-index: 3;
                 padding: 4px 9px; border-radius: 999px; background: #14161cd9;
                 border: 1px solid #343845; font: 11.5px/1 ui-monospace, Menlo, monospace;
                 color: #c6cad2; pointer-events: none; opacity: 0; transition: opacity .15s; }}
  .viewer-stage.zoomed .zoom-badge {{ opacity: 1; }}
  .viewer-stage .edge {{ position: absolute; top: 0; bottom: 0; width: 16%; border: 0;
                         background: transparent; border-radius: 0; }}
  .viewer-stage .edge:hover {{ background: linear-gradient(90deg, rgba(255,255,255,.05), transparent); }}
  .viewer-stage .edge.next {{ right: 0; }}
  .viewer-stage .edge.next:hover {{ background: linear-gradient(270deg, rgba(255,255,255,.05), transparent); }}
  .viewer-stage .edge.prev {{ left: 0; cursor: w-resize; }}
  .viewer-stage .edge.next {{ cursor: e-resize; }}

  .viewer-foot {{ display: flex; align-items: center; gap: 14px; padding: 12px 18px;
                  background: #14161c; border-top: 1px solid #24262e; }}
  .viewer-foot .idx {{ font: 12px/1 ui-monospace, Menlo, monospace; color: #9aa0ab;
                       white-space: nowrap; min-width: 78px; text-align: center; }}
  input[type=range] {{ flex: 1; accent-color: #6f8cff; height: 22px; }}

  @media (max-width: 720px) {{
    .grid {{ grid-template-columns: 1fr; }}
    section, header, nav {{ padding-left: 16px; padding-right: 16px; }}
    .viewer-bar .where {{ display: none; }}
  }}
</style></head><body>

<header>
  <h1>Kerykeion SVG — validation sweep</h1>
  <p>One section per axis: each holds a single dimension at every value it can take while the rest
     stay at a default. The last sections are deliberately not defaults — polar latitudes, dates
     before the common era, the heaviest chart the library can draw — because that is where layout
     gives way. Anything that raised is shown as a red card rather than left out.</p>
  <p class="totals"><b>{ok}</b> charts rendered · <b>{failed}</b> failed · {n_sections} sections
     &nbsp;·&nbsp; click any chart to open it full screen · <kbd>←</kbd> <kbd>→</kbd> to step,
     <kbd>Home</kbd>/<kbd>End</kbd> to jump, <kbd>i</kbd> for the technical details,
     <kbd>Esc</kbd> to close. Scroll to zoom, drag to pan, double-click to reset.</p>
</header>

<nav>{nav}</nav>
{body}

<div class="viewer" id="viewer" role="dialog" aria-modal="true" aria-label="Chart viewer">
  <div class="viewer-bar">
    <div class="who">
      <b id="v-title"></b>
      <span><code id="v-file"></code> · <span id="v-detail"></span></span>
    </div>
    <div class="where" id="v-section"></div>
    <button type="button" id="v-info" title="Technical details (i)" aria-expanded="false">ⓘ Details</button>
    <button type="button" id="v-close" title="Close (Esc)">Close ✕</button>
  </div>
  <aside class="facts" id="v-facts" hidden></aside>
  <div class="viewer-stage">
    <button type="button" class="edge prev" id="v-edge-prev" aria-label="Previous"></button>
    <img id="v-img" alt="">
    <button type="button" class="edge next" id="v-edge-next" aria-label="Next"></button>
    <div class="zoom-badge" id="v-zoom"></div>
  </div>
  <div class="viewer-foot">
    <button type="button" id="v-prev" title="Previous (←)">‹ Prev</button>
    <input type="range" id="v-range" min="0" value="0" step="1" aria-label="Scrub through every chart">
    <span class="idx" id="v-idx"></span>
    <button type="button" id="v-next" title="Next (→)">Next ›</button>
  </div>
</div>

<script>
const CHARTS = {charts};
const viewer = document.getElementById('viewer');
const img = document.getElementById('v-img');
const range = document.getElementById('v-range');
const elTitle = document.getElementById('v-title');
const elFile = document.getElementById('v-file');
const elFacts = document.getElementById('v-facts');
const btnInfo = document.getElementById('v-info');
const elDetail = document.getElementById('v-detail');
const elSection = document.getElementById('v-section');
const elIdx = document.getElementById('v-idx');
const btnPrev = document.getElementById('v-prev');
const btnNext = document.getElementById('v-next');

let at = 0;
range.max = String(CHARTS.length - 1);

function show(i) {{
  at = Math.max(0, Math.min(CHARTS.length - 1, i));
  const c = CHARTS[at];
  img.src = c.f;
  img.alt = c.t;
  elTitle.textContent = c.t;
  elFile.textContent = c.f;
  elDetail.textContent = c.d;
  elSection.textContent = c.s;
  renderFacts(c);
  elIdx.textContent = (at + 1) + ' / ' + CHARTS.length;
  range.value = String(at);
  btnPrev.disabled = at === 0;
  btnNext.disabled = at === CHARTS.length - 1;
  resetZoom();
}}

function fmt(v) {{
  if (Array.isArray(v)) return v.map(x => String(x) || '∅').join('\n');
  if (v && typeof v === 'object') {{
    return Object.entries(v).map(([k, n]) => k + ' × ' + n).join(', ');
  }}
  return String(v);
}}

function renderFacts(c) {{
  const x = c.x || {{}};
  const rows = [['file', c.f], ['section', c.s], ['rendered with', c.d]];
  for (const [k, v] of Object.entries(x)) {{
    if (k === 'bytes') {{ rows.push(['size', (v / 1024).toFixed(1) + ' KB (' + v + ' bytes)']); }}
    else rows.push([k, fmt(v)]);
  }}
  elFacts.innerHTML = '<dl>' + rows.map(([k, v]) => {{
    const bad = String(v).startsWith('INVALID') ? ' class="bad"' : '';
    const esc = s => String(s).replace(/[&<>]/g, ch => ({{'&': '&amp;', '<': '&lt;', '>': '&gt;'}})[ch]);
    return '<dt>' + esc(k) + '</dt><dd' + bad + '>' + esc(v).replace(/\n/g, '<br>') + '</dd>';
  }}).join('') + '</dl>';
}}

function toggleFacts(force) {{
  const show = force !== undefined ? force : elFacts.hidden;
  elFacts.hidden = !show;
  btnInfo.setAttribute('aria-expanded', String(show));
}}

// ---- zoom and pan -------------------------------------------------------
// A validation sweep is for looking closely: the interesting defects are a
// badge overlapping a column or a row running under the wheel, and neither is
// legible at fit-to-screen on a 1560-unit biwheel.
const stage = document.querySelector('.viewer-stage');
const zoomBadge = document.getElementById('v-zoom');
let scale = 1, tx = 0, ty = 0, dragging = false, lastX = 0, lastY = 0;

function applyTransform() {{
  img.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')';
  stage.classList.toggle('zoomed', scale !== 1);
  zoomBadge.textContent = Math.round(scale * 100) + '%';
}}

function resetZoom() {{
  scale = 1; tx = 0; ty = 0;
  applyTransform();
}}

stage.addEventListener('wheel', e => {{
  if (!viewer.classList.contains('open')) return;
  e.preventDefault();
  const rect = img.getBoundingClientRect();
  // Anchor on the cursor: zooming should magnify what is under the pointer,
  // not drift the chart away from it.
  const ox = e.clientX - rect.left;
  const oy = e.clientY - rect.top;
  const factor = Math.exp(-e.deltaY * 0.0015);
  const next = Math.min(12, Math.max(1, scale * factor));
  const ratio = next / scale;
  tx -= ox * (ratio - 1);
  ty -= oy * (ratio - 1);
  scale = next;
  if (scale === 1) {{ tx = 0; ty = 0; }}
  applyTransform();
}}, {{passive: false}});

stage.addEventListener('pointerdown', e => {{
  if (scale === 1) return;
  dragging = true; lastX = e.clientX; lastY = e.clientY;
  stage.classList.add('dragging');
  stage.setPointerCapture(e.pointerId);
}});
stage.addEventListener('pointermove', e => {{
  if (!dragging) return;
  tx += e.clientX - lastX; ty += e.clientY - lastY;
  lastX = e.clientX; lastY = e.clientY;
  applyTransform();
}});
for (const ev of ['pointerup', 'pointercancel']) {{
  stage.addEventListener(ev, () => {{ dragging = false; stage.classList.remove('dragging'); }});
}}
img.addEventListener('dblclick', resetZoom);

function open(i) {{
  show(i);
  viewer.classList.add('open');
  document.body.classList.add('locked');
  range.focus({{preventScroll: true}});
}}

function close() {{
  viewer.classList.remove('open');
  document.body.classList.remove('locked');
  // Leave the page where the chart being looked at actually is.
  const card = document.querySelector('.card[data-i="' + at + '"]');
  if (card) card.scrollIntoView({{block: 'center', behavior: 'instant'}});
}}

document.querySelectorAll('.card[data-i]').forEach(card => {{
  const i = Number(card.dataset.i);
  card.addEventListener('click', () => open(i));
  card.addEventListener('keydown', e => {{
    if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); open(i); }}
  }});
}});

range.addEventListener('input', () => show(Number(range.value)));
btnPrev.addEventListener('click', () => show(at - 1));
btnNext.addEventListener('click', () => show(at + 1));
document.getElementById('v-edge-prev').addEventListener('click', () => show(at - 1));
document.getElementById('v-edge-next').addEventListener('click', () => show(at + 1));
document.getElementById('v-close').addEventListener('click', close);
btnInfo.addEventListener('click', () => toggleFacts());

viewer.addEventListener('click', e => {{ if (e.target === viewer) close(); }});

document.addEventListener('keydown', e => {{
  if (!viewer.classList.contains('open')) return;
  if (e.key === 'Escape') {{ if (!elFacts.hidden) toggleFacts(false); else close(); }}
  else if (e.key === 'i' || e.key === 'I') {{ toggleFacts(); }}
  else if (e.key === 'ArrowRight' || e.key === 'PageDown') {{ e.preventDefault(); show(at + 1); }}
  else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{ e.preventDefault(); show(at - 1); }}
  else if (e.key === '0') {{ resetZoom(); }}
  else if (e.key === '+' || e.key === '=') {{ scale = Math.min(12, scale * 1.25); applyTransform(); }}
  else if (e.key === '-') {{ scale = Math.max(1, scale / 1.25); if (scale === 1) {{ tx = 0; ty = 0; }} applyTransform(); }}
  else if (e.key === 'Home') {{ e.preventDefault(); show(0); }}
  else if (e.key === 'End') {{ e.preventDefault(); show(CHARTS.length - 1); }}
}});
</script>
</body></html>
"""


def _check_script(page: str) -> None:
    """Parse the emitted JavaScript, when there is something around to parse it.

    The page is built by a Python format string, which is a fine way to produce
    a syntax error nobody notices: an escape eaten one level too early once
    turned a JS string literal into two lines and took the whole viewer down,
    and the page still looked perfectly fine until it was clicked. A parser
    catches in a second what reading cannot.
    """
    script = re.search(r"<script>(.*?)</script>", page, re.S)
    if not script:
        return
    if shutil.which("node") is None:
        print("  ..  node not found — the viewer script was not syntax-checked")
        return
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as handle:
        handle.write(script.group(1))
        path = handle.name
    try:
        result = subprocess.run(["node", "--check", path], capture_output=True, text=True)
        if result.returncode != 0:
            raise SystemExit(
                "The viewer script does not parse — the page would be dead on arrival:\n"
                + (result.stderr or result.stdout)
            )
        print("  ok  viewer script parses")
    finally:
        Path(path).unlink(missing_ok=True)


def build_index(out: Path) -> None:
    """Write index.html from cards.json, so the viewer can be reworked cheaply."""
    data = json.loads((out / "cards.json").read_text(encoding="utf-8"))

    def slug(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", name.lower())

    nav = "\n".join(
        f'<a href="#{slug(s["name"])}">{html.escape(s["name"])} <em>{len(s["cards"])}</em></a>'
        for s in data["sections"]
    )

    # Flat running order, so the viewer can walk the whole sweep in one sequence
    # rather than restarting at each section.
    flat: list[dict] = []
    for s in data["sections"]:
        for card in s["cards"]:
            if not card["error"]:
                flat.append(
                    {
                        "f": card["filename"] + ".svg",
                        "t": card["title"],
                        "d": card["detail"],
                        "s": s["name"],
                        "x": card.get("facts") or {},
                    }
                )
    index_of = {c["f"]: i for i, c in enumerate(flat)}

    body = []
    for s in data["sections"]:
        failed = sum(1 for c in s["cards"] if c["error"])
        badge = f' <span class="failed">{failed} failed</span>' if failed else ""
        body.append(
            f'<section id="{slug(s["name"])}"><h2>{html.escape(s["name"])} '
            f'<span class="count">{len(s["cards"])}</span>{badge}</h2>'
            f'<p class="blurb">{html.escape(s["blurb"])}</p><div class="grid">'
        )
        for card in s["cards"]:
            caption = (
                f'<figcaption><b>{html.escape(card["title"])}</b>'
                f'<span>{html.escape(card["detail"])}</span></figcaption>'
            )
            if card["error"]:
                body.append(
                    f'<figure class="card error">{caption}'
                    f'<pre>{html.escape(card["error"])}</pre></figure>'
                )
            else:
                name = card["filename"] + ".svg"
                body.append(
                    f'<figure class="card" data-i="{index_of[name]}" tabindex="0">{caption}'
                    f'<img loading="lazy" decoding="async" src="{name}" alt="{html.escape(card["title"])}" '
                    f'style="aspect-ratio: {card["aspect"]}"></figure>'
                )
        body.append("</div></section>")

    page = _PAGE.format(
            nav=nav,
            body="".join(body),
            ok=data["ok"],
            failed=data["failed"],
            n_sections=len(data["sections"]),
            charts=json.dumps(flat, ensure_ascii=False),
    )
    _check_script(page)
    (out / "index.html").write_text(page, encoding="utf-8")


sections: list[Section] = []
current: Optional[Section] = None
counters = {"ok": 0, "failed": 0}


def section(name: str, blurb: str) -> None:
    global current
    current = Section(name, blurb)
    sections.append(current)
    print(f"\n── {name}")


def emit(filename: str, title: str, detail: str, render: Callable[[], str]) -> None:
    """Render one card, keeping a failure visible instead of aborting the sweep."""
    assert current is not None
    try:
        svg = render()
    except Exception as exc:  # noqa: BLE001 — the point is to survive and report
        counters["failed"] += 1
        current.cards.append(
            Card(filename, title, detail, error=f"{type(exc).__name__}: {exc}".strip()[:400])
        )
        print(f"  !!  {filename}: {type(exc).__name__}")
        traceback.print_exc(limit=1, file=sys.stderr)
        return

    (OUT / f"{filename}.svg").write_text(svg, encoding="utf-8")
    match = re.search(r"viewBox='([-\d.]+)\s+([-\d.]+)\s+([\d.]+)\s+([\d.]+)'", svg[:900])
    aspect = f"{match.group(3)}/{match.group(4)}" if match else "890/580"
    counters["ok"] += 1
    current.cards.append(Card(filename, title, detail, aspect, facts=inspect_svg(svg)))
    print(f"  ok  {filename}")


if INDEX_ONLY:
    # Reworking the viewer should not cost a re-render of the whole sweep.
    build_index(OUT)
    print(f"Rewrote {OUT / 'index.html'} from cards.json")
    raise SystemExit(0)


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------

print("Building subjects…")


def subject(name: str, **kwargs: Any):
    base = dict(
        year=1940, month=10, day=9, hour=18, minute=30,
        lng=-2.9916, lat=53.4084, tz_str="Europe/London", city="Liverpool", nation="GB",
        online=False, suppress_geonames_warning=True,
    )
    base.update(kwargs)
    return AstrologicalSubjectFactory.from_birth_data(name, **base)


john = subject("John Lennon")
paul = subject("Paul McCartney", year=1942, month=6, day=18, hour=15, minute=30)

# Skies chosen for what they contain, not for who they belong to.
station = subject("Mercury Station", year=1990, month=8, day=25, hour=12, minute=0,
                  lng=-0.1276, lat=51.5074, city="London")
oob = subject("Out Of Bounds", year=1990, month=1, day=1, hour=12, minute=0,
              lng=-0.1276, lat=51.5074, city="London")
two_angles = subject("Two Angles", year=2000, month=1, day=16, hour=8, minute=0,
                     lng=18.95, lat=67.0, tz_str="UTC", city="Tromso", nation="NO")
polar = subject("Polar 78N", year=1990, month=6, day=15, hour=12, minute=0,
                lng=15.6, lat=78.2, tz_str="Arctic/Longyearbyen", city="Longyearbyen",
                nation="SJ", houses_system_identifier="P")
sidereal = subject("Sidereal Lahiri", zodiac_type="Sidereal", sidereal_mode="LAHIRI")
gauquelin = subject("Gauquelin", year=1990, month=1, day=1, hour=12, minute=0,
                    lng=-0.1276, lat=51.5074, city="London", calculate_gauquelin=True)
loaded = subject(
    "Every Point",
    active_points=list(ALL_ACTIVE_POINTS) + list(URANIAN_ACTIVE_POINTS),
    calculate_dignities=True, calculate_nakshatra=True, calculate_gauquelin=True,
    active_fixed_stars=list(DEFAULT_FIXED_STARS),
)

natal = ChartDataFactory.create_natal_chart_data(john)
synastry = ChartDataFactory.create_synastry_chart_data(john, paul)


# ---------------------------------------------------------------------------
# 1. Themes
# ---------------------------------------------------------------------------
section("Themes", "Every theme in both styles, plus the un-themed output that ships no CSS at all.")
for theme in THEMES:
    for style in STYLES:
        emit(f"theme_{theme}_{style}", f"{theme} · {style}", f"theme={theme}",
             lambda t=theme, s=style: ChartDrawer(natal, theme=t).generate_svg_string(style=s))
for style in STYLES:
    emit(f"theme_none_{style}", f"no theme · {style}", "theme=None — relies on the fallbacks in var()",
         lambda s=style: ChartDrawer(natal, theme=None).generate_svg_string(style=s))


# ---------------------------------------------------------------------------
# 2. Languages
# ---------------------------------------------------------------------------
section(
    "Languages",
    "All ten, in both styles. The info panel sits inside the wheel's chord, so this is "
    "where a translation runs under the wheel — read the bottom-left block, not the wheel.",
)
for language in LANGUAGES:
    for style in STYLES:
        emit(f"lang_{language}_{style}", f"{language} · {style}", f"chart_language={language}",
             lambda lang=language, s=style: ChartDrawer(natal, chart_language=lang).generate_svg_string(style=s))

section("Languages · dual wheel", "The same ten on a synastry, whose panel names both wheels.")
for language in LANGUAGES:
    emit(f"lang_dual_{language}", f"{language} · synastry", f"chart_language={language}",
         lambda lang=language: ChartDrawer(synastry, chart_language=lang).generate_svg_string())


# ---------------------------------------------------------------------------
# 3. Chart types
# ---------------------------------------------------------------------------
section("Chart types", "Every kind of chart the library draws, in both styles.")

returns = PlanetaryReturnFactory(john, lng=-2.9916, lat=53.4084, tz_str="Europe/London",
                                 city="Liverpool", nation="GB", online=False)
solar_return = returns.next_return_from_year(2025, "Solar")
lunar_return = returns.next_return_from_year(2025, "Lunar")
composite_mid = CompositeSubjectFactory(john, paul).get_midpoint_composite_subject_model()
composite_dav = CompositeSubjectFactory(john, paul).get_davison_composite_subject_model()
progressed = SecondaryProgressionFactory.compute(john, target_year=2000)

CHART_TYPES: list[tuple[str, str, Any]] = [
    ("natal", "Natal", natal),
    ("synastry", "Synastry", synastry),
    ("transit", "Transit", ChartDataFactory.create_transit_chart_data(john, paul)),
    ("composite_midpoint", "Composite (midpoint)", ChartDataFactory.create_composite_chart_data(composite_mid)),
    ("composite_davison", "Composite (Davison)", ChartDataFactory.create_composite_chart_data(composite_dav)),
    ("return_solar_single", "Solar return (single wheel)",
     ChartDataFactory.create_single_wheel_return_chart_data(solar_return)),
    ("return_solar_dual", "Solar return (biwheel)",
     ChartDataFactory.create_return_chart_data(john, solar_return)),
    ("return_lunar_single", "Lunar return (single wheel)",
     ChartDataFactory.create_single_wheel_return_chart_data(lunar_return)),
    ("return_lunar_dual", "Lunar return (biwheel)",
     ChartDataFactory.create_return_chart_data(john, lunar_return)),
    ("progression", "Secondary progression",
     ChartDataFactory.create_progression_chart_data(john, progressed)),
]
for slug, label, data in CHART_TYPES:
    for style in STYLES:
        emit(f"type_{slug}_{style}", f"{label} · {style}", slug,
             lambda d=data, s=style: ChartDrawer(d).generate_svg_string(style=s))


# ---------------------------------------------------------------------------
# 4. Output templates
# ---------------------------------------------------------------------------
section("Output templates", "The three things a drawer can hand back, on a single and a dual chart.")
for slug, data in (("natal", natal), ("synastry", synastry)):
    for style in STYLES:
        emit(f"tpl_wheel_{slug}_{style}", f"wheel only · {slug} · {style}", "generate_wheel_only_svg_string",
             lambda d=data, s=style: ChartDrawer(d).generate_wheel_only_svg_string(style=s))
    emit(f"tpl_grid_{slug}", f"aspect grid only · {slug}", "generate_aspect_grid_only_svg_string",
         lambda d=data: ChartDrawer(d).generate_aspect_grid_only_svg_string())


# ---------------------------------------------------------------------------
# 5. House systems
# ---------------------------------------------------------------------------
section(
    "House systems",
    f"All {len(HOUSE_SYSTEMS)} identifiers, at a temperate latitude where every one of them is defined.",
)
for identifier in HOUSE_SYSTEMS:
    emit(f"house_{identifier}", f"house system {identifier!r}", f"houses_system_identifier={identifier!r}",
         lambda i=identifier: ChartDrawer(
             ChartDataFactory.create_natal_chart_data(subject(f"Houses {i}", houses_system_identifier=i))
         ).generate_svg_string())

section(
    "House systems · inside the polar circle",
    "At 78°N most systems are undefined and another stands in. Switch the fallback note on and "
    "the domification line marks the substitution with an asterisk.",
)
for identifier in HOUSE_SYSTEMS:
    emit(f"house_polar_{identifier}", f"{identifier!r} at 78°N", f"houses_system_identifier={identifier!r}",
         lambda i=identifier: ChartDrawer(
             ChartDataFactory.create_natal_chart_data(
                 subject(f"Polar {i}", year=1990, month=6, day=15, hour=12, minute=0,
                         lng=15.6, lat=78.2, tz_str="Arctic/Longyearbyen", city="Longyearbyen",
                         nation="SJ", houses_system_identifier=i)
             ),
             show_polar_fallback_note=True,
         ).generate_svg_string())


# ---------------------------------------------------------------------------
# 6. Perspectives
# ---------------------------------------------------------------------------
section(
    "Perspectives",
    "All eleven. Motion state and out-of-bounds are geocentric facts, so the non-terrestrial "
    "ones state neither — the marks are switched on here precisely to show that absence.",
)
for perspective in PERSPECTIVES:
    slug = perspective.lower().replace(" ", "_")
    for style in STYLES:
        emit(f"persp_{slug}_{style}", f"{perspective} · {style}", f"perspective_type={perspective!r}",
             lambda p=perspective, s=style: ChartDrawer(
                 ChartDataFactory.create_natal_chart_data(subject(f"Perspective {p}", perspective_type=p)),
                 **ALL_MARKS,
             ).generate_svg_string(style=s))


# ---------------------------------------------------------------------------
# 7. Zodiac and ayanamsa
# ---------------------------------------------------------------------------
section(
    "Sidereal modes",
    f"All {len(SIDEREAL_MODES)} ayanamsas, with the offset printed next to each mode name.",
)
for mode in SIDEREAL_MODES:
    # USER is not a tabulated ayanamsa but a hook for defining one, so it is the
    # single mode that needs its epoch and offset supplied alongside it.
    custom = (
        dict(custom_ayanamsa_t0=2451545.0, custom_ayanamsa_ayan_t0=23.85)
        if mode == "USER"
        else {}
    )
    detail = f"sidereal_mode={mode!r}" + (" + custom t0/offset" if custom else "")
    emit(f"ayan_{mode}", mode, detail,
         lambda m=mode, c=custom: ChartDrawer(
             ChartDataFactory.create_natal_chart_data(
                 subject(f"Sidereal {m}", zodiac_type="Sidereal", sidereal_mode=m, **c)
             ),
             show_ayanamsa_value=True,
         ).generate_svg_string())


# ---------------------------------------------------------------------------
# 8. The opt-in marks
# ---------------------------------------------------------------------------
section(
    "Opt-in marks · one at a time",
    "Each mark alone, against the same chart with everything off. A mark draws nothing where "
    "there is nothing to mark, so each is paired with a sky that has its referent.",
)
MARK_SUBJECTS = [
    ("show_motion_state", "Station markers (SR/SD)", station, "Mercury stations on this date"),
    ("show_out_of_bounds", "Out-of-bounds badge", oob, "Uranus is past the obliquity"),
    ("show_aspect_movement", "Separating aspects dashed", station, "half this chart's aspects separate"),
    ("show_ayanamsa_value", "Ayanamsa offset", sidereal, "sidereal Lahiri"),
    ("show_polar_fallback_note", "Polar fallback note", polar, "Placidus undefined at 78°N"),
]
for style in STYLES:
    emit(f"mark_none_{style}", f"nothing on · {style}", "every mark off — the reference",
         lambda s=style: ChartDrawer(
             ChartDataFactory.create_natal_chart_data(station)).generate_svg_string(style=s))
for flag, label, subj, why in MARK_SUBJECTS:
    for style in STYLES:
        emit(f"mark_{flag}_{style}", f"{label} · {style}", f"{flag}=True — {why}",
             lambda f=flag, sub=subj, s=style: ChartDrawer(
                 ChartDataFactory.create_natal_chart_data(sub), **{f: True}
             ).generate_svg_string(style=s))
for style in STYLES:
    emit(f"mark_score_{style}", f"Relationship score · {style}", "show_relationship_score=True — synastry",
         lambda s=style: ChartDrawer(synastry, show_relationship_score=True).generate_svg_string(style=s))

section(
    "Opt-in marks · everything on",
    "Every option switched on at once, across subjects that between them carry every referent.",
)
for slug, label, subj in (
    ("station", "Station + out of bounds", station),
    ("oob", "Out of bounds", oob),
    ("two_angles", "A planet on two angles (67°N)", two_angles),
    ("polar", "Polar fallback (78°N)", polar),
    ("sidereal", "Sidereal", sidereal),
    ("gauquelin", "Gauquelin sectors", gauquelin),
    ("loaded", "Every active point", loaded),
):
    for style in STYLES:
        emit(f"all_marks_{slug}_{style}", f"{label} · {style}", "all six marks on",
             lambda sub=subj, s=style: ChartDrawer(
                 ChartDataFactory.create_natal_chart_data(sub), **ALL_MARKS
             ).generate_svg_string(style=s))
for style in STYLES:
    emit(f"all_marks_synastry_{style}", f"Synastry · {style}", "all six marks on",
         lambda s=style: ChartDrawer(synastry, **ALL_MARKS).generate_svg_string(style=s))


# ---------------------------------------------------------------------------
# 9. Geography
# ---------------------------------------------------------------------------
section(
    "Latitudes and longitudes",
    "From the pole to the equator and across the dateline. Extreme latitudes are where house "
    "systems give way and where the angles crowd together.",
)
PLACES = [
    ("north_pole_89", "89°N — Arctic Ocean", 89.0, 0.0, "UTC"),
    ("longyearbyen_78", "78°N — Longyearbyen", 78.2, 15.6, "Arctic/Longyearbyen"),
    ("tromso_69", "69°N — Tromsø", 69.6, 18.9, "Europe/Oslo"),
    ("arctic_circle_66", "66.5°N — the Arctic Circle", 66.5, 25.0, "Europe/Helsinki"),
    ("reykjavik_64", "64°N — Reykjavík", 64.1, -21.9, "Atlantic/Reykjavik"),
    ("london_51", "51°N — London", 51.5, -0.13, "Europe/London"),
    ("quito_0", "0° — Quito, on the equator", -0.18, -78.5, "America/Guayaquil"),
    ("nairobi_-1", "1°S — Nairobi", -1.29, 36.8, "Africa/Nairobi"),
    ("cape_town_-34", "34°S — Cape Town", -33.9, 18.4, "Africa/Johannesburg"),
    ("ushuaia_-55", "55°S — Ushuaia", -54.8, -68.3, "America/Argentina/Ushuaia"),
    ("antarctic_-78", "78°S — McMurdo", -77.8, 166.7, "Pacific/Auckland"),
    ("south_pole_-89", "89°S — the South Pole", -89.0, 0.0, "UTC"),
    ("dateline_east", "179°E — across the dateline", -16.5, 179.0, "Pacific/Fiji"),
    ("dateline_west", "170°W — the other side", -14.3, -170.7, "Pacific/Pago_Pago"),
]
for slug, label, lat, lng, tz in PLACES:
    emit(f"geo_{slug}", label, f"lat={lat} lng={lng}",
         lambda la=lat, ln=lng, t=tz, s=slug: ChartDrawer(
             ChartDataFactory.create_natal_chart_data(
                 subject(f"Geo {s}", year=1990, month=6, day=15, hour=12, minute=0,
                         lat=la, lng=ln, tz_str=t, city=s, nation="XX")
             ),
             **ALL_MARKS,
         ).generate_svg_string())


# ---------------------------------------------------------------------------
# 10. Dates
# ---------------------------------------------------------------------------
section(
    "Across time",
    "Two and a half millennia. The ayanamsa drifts, the obliquity changes, and the info panel "
    "has to keep printing a readable date.",
)
DATES = [
    ("bce_500", "500 BCE", -500, 3, 15),
    ("bce_44", "44 BCE", -44, 3, 15),
    ("ce_100", "100 CE", 100, 6, 1),
    ("ce_800", "800 CE — Charlemagne", 800, 12, 25),
    ("ce_1492", "1492", 1492, 10, 12),
    ("ce_1610", "1610 — Galileo's moons", 1610, 1, 7),
    ("ce_1900", "1900", 1900, 1, 1),
    ("ce_2000", "2000", 2000, 1, 1),
    ("ce_2026", "2026", 2026, 8, 12),
    ("ce_2100", "2100", 2100, 1, 1),
    ("ce_2400", "2400", 2400, 1, 1),
]
for slug, label, year, month, day in DATES:
    emit(f"date_{slug}", label, f"{year:+05d}-{month:02d}-{day:02d}",
         lambda y=year, m=month, d=day, s=slug: ChartDrawer(
             ChartDataFactory.create_natal_chart_data(
                 subject(f"Date {s}", year=y, month=m, day=d, hour=12, minute=0)
             ),
             **ALL_MARKS,
         ).generate_svg_string())


# ---------------------------------------------------------------------------
# 11. Active point sets
# ---------------------------------------------------------------------------
section(
    "How much is on the wheel",
    "From a bare traditional set to every point the library knows. The decluttering and the "
    "grid's column count are what to watch here.",
)
POINT_SETS = [
    ("traditional", "Traditional set",
     list(TRADITIONAL_ASTROLOGY_ACTIVE_POINTS) + ["Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli"]),
    ("default", "Default set", None),
    ("uranian", "Default + Uranian", None),
    ("all", "Every point", list(ALL_ACTIVE_POINTS)),
    ("all_uranian", "Every point + Uranian", list(ALL_ACTIVE_POINTS) + list(URANIAN_ACTIVE_POINTS)),
]
for slug, label, points in POINT_SETS:
    for style in STYLES:
        def render(p=points, sl=slug, st=style):
            kwargs: dict[str, Any] = {}
            if sl == "uranian":
                kwargs["active_points"] = None
            if p is not None:
                kwargs["active_points"] = p
            subj = subject(f"Points {sl}", **{k: v for k, v in kwargs.items() if v is not None})
            data = ChartDataFactory.create_natal_chart_data(subj)
            return ChartDrawer(data, **ALL_MARKS).generate_svg_string(style=st)

        emit(f"points_{slug}_{style}", f"{label} · {style}", slug, render)

emit("points_all_aspects", "Every point, every aspect", "active_aspects=ALL_ACTIVE_ASPECTS",
     lambda: ChartDrawer(
         ChartDataFactory.create_natal_chart_data(
             subject("Everything", active_points=list(ALL_ACTIVE_POINTS) + list(URANIAN_ACTIVE_POINTS)),
             active_aspects=list(ALL_ACTIVE_ASPECTS),
         ),
         **ALL_MARKS,
     ).generate_svg_string())


# ---------------------------------------------------------------------------
# 12. Optional calculations
# ---------------------------------------------------------------------------
section(
    "Optional calculations",
    "Channels a subject can switch on: Gauquelin sectors, which replace the point grid entirely; "
    "fixed stars; midpoints; dignities and nakshatras.",
)
EXTRAS = [
    ("gauquelin", "Gauquelin sectors", dict(calculate_gauquelin=True), None),
    ("fixed_stars", "Fixed stars", dict(active_fixed_stars=list(DEFAULT_FIXED_STARS)), None),
    ("midpoints", "Active midpoints", {}, ["Sun_Moon", "Venus_Mars"]),
    ("dignities", "Dignities + nakshatra", dict(calculate_dignities=True, calculate_nakshatra=True), None),
    ("everything", "All of them at once",
     dict(calculate_gauquelin=True, calculate_dignities=True, calculate_nakshatra=True,
          active_fixed_stars=list(DEFAULT_FIXED_STARS)), ["Sun_Moon"]),
]
for slug, label, kwargs, midpoints in EXTRAS:
    for style in STYLES:
        def render(k=kwargs, mp=midpoints, sl=slug, st=style):
            # Midpoints are attached to a built subject rather than requested
            # from the factory, so they are a second step, not a keyword.
            subj = subject(f"Extra {sl}", **k)
            if mp:
                subj.active_midpoints = MidpointFactory.compute_active_midpoint_points(subj, mp)
            return ChartDrawer(
                ChartDataFactory.create_natal_chart_data(subj), **ALL_MARKS
            ).generate_svg_string(style=st)

        detail = ", ".join(list(kwargs) + ([f"active_midpoints={midpoints}"] if midpoints else []))
        emit(f"extra_{slug}_{style}", f"{label} · {style}", detail, render)


# ---------------------------------------------------------------------------
# 13. Rendering options
# ---------------------------------------------------------------------------
section("Rendering options", "The rest of the drawer's surface, each against the same natal chart.")
OPTIONS: list[tuple[str, str, dict[str, Any]]] = [
    ("external_view", "External view (classic only)", dict(external_view=True)),
    ("no_degree_indicators", "No degree indicators", dict(show_degree_indicators=False)),
    ("no_aspect_icons", "No aspect icons", dict(show_aspect_icons=False)),
    ("no_diurnality", "No diurnality row", dict(show_diurnality=False)),
    ("transparent", "Transparent background", dict(transparent_background=True)),
    ("custom_title", "Custom title", dict(custom_title="A Chart With A Very Long Custom Title")),
    ("no_auto_size", "auto_size off", dict(auto_size=False)),
    ("padding_100", "padding=100", dict(padding=100)),
    ("grid_table", "Aspect grid as a table", dict(double_chart_aspect_grid_type="table")),
]
for slug, label, kwargs in OPTIONS:
    data = synastry if slug == "grid_table" else natal
    emit(f"opt_{slug}", label, ", ".join(f"{k}={v!r}" for k, v in kwargs.items()),
         lambda d=data, k=kwargs: ChartDrawer(d, **k).generate_svg_string())

emit("opt_no_zodiac_ring", "No zodiac background ring (modern)", "show_zodiac_background_ring=False",
     lambda: ChartDrawer(natal).generate_svg_string(style="modern", show_zodiac_background_ring=False))
emit("opt_house_comparison_off", "House comparison off (synastry)", "show_house_position_comparison=False",
     lambda: ChartDrawer(synastry, show_house_position_comparison=False).generate_svg_string())
emit("opt_cusp_comparison_on", "Cusp comparison on (synastry)", "show_cusp_position_comparison=True",
     lambda: ChartDrawer(synastry, show_cusp_position_comparison=True).generate_svg_string())


# ---------------------------------------------------------------------------
# 14. Combinations that stack
# ---------------------------------------------------------------------------
section(
    "Everything at once",
    "The stress cases: the heaviest chart the library can draw, in each theme and both styles, "
    "with every mark on. If the layout gives anywhere, it gives here.",
)
for theme in THEMES:
    for style in STYLES:
        emit(f"stress_{theme}_{style}", f"{theme} · {style}", "every point, every aspect, every mark",
             lambda t=theme, s=style: ChartDrawer(
                 ChartDataFactory.create_natal_chart_data(loaded, active_aspects=list(ALL_ACTIVE_ASPECTS)),
                 theme=t, **ALL_MARKS,
             ).generate_svg_string(style=s))

for language in LANGUAGES:
    emit(f"stress_lang_{language}", f"Heaviest chart · {language}", "every point + every mark",
         lambda lang=language: ChartDrawer(
             ChartDataFactory.create_natal_chart_data(loaded, active_aspects=list(ALL_ACTIVE_ASPECTS)),
             chart_language=lang, **ALL_MARKS,
         ).generate_svg_string())


# ---------------------------------------------------------------------------
# 15. Lunar phases
# ---------------------------------------------------------------------------
section(
    "Lunar phases",
    "The moon glyph is drawn, not picked from a set, so every phase is a different shape. "
    "Eight dates through one lunation, plus the two syzygies exactly.",
)
PHASES = [
    ("new", "New Moon", 2024, 1, 11),
    ("waxing_crescent", "Waxing Crescent", 2024, 1, 14),
    ("first_quarter", "First Quarter", 2024, 1, 18),
    ("waxing_gibbous", "Waxing Gibbous", 2024, 1, 22),
    ("full", "Full Moon", 2024, 1, 25),
    ("waning_gibbous", "Waning Gibbous", 2024, 1, 29),
    ("last_quarter", "Last Quarter", 2024, 2, 2),
    ("waning_crescent", "Waning Crescent", 2024, 2, 6),
]
for slug, label, year, month, day in PHASES:
    emit(f"moon_{slug}", label, f"{year}-{month:02d}-{day:02d} — read the glyph under the panel",
         lambda y=year, m=month, d=day, sl=slug: ChartDrawer(
             ChartDataFactory.create_natal_chart_data(
                 subject(f"Moon {sl}", year=y, month=m, day=d, hour=12, minute=0)
             )
         ).generate_svg_string())


# ---------------------------------------------------------------------------
# 16. Time of day
# ---------------------------------------------------------------------------
section(
    "Time of day",
    "The same date every three hours. Diurnality flips when the Sun crosses the horizon, and the "
    "whole wheel rotates with the Ascendant — this is where a chart drawn at the wrong hour shows.",
)
for hour in range(0, 24, 3):
    emit(f"hour_{hour:02d}", f"{hour:02d}:00", "diurnality and the Ascendant both turn on this",
         lambda h=hour: ChartDrawer(
             ChartDataFactory.create_natal_chart_data(
                 subject(f"Hour {h:02d}", year=1990, month=6, day=15, hour=h, minute=0)
             ),
             **ALL_MARKS,
         ).generate_svg_string())


# ---------------------------------------------------------------------------
# 17. Names and titles
# ---------------------------------------------------------------------------
section(
    "Names and titles",
    "Subject names and custom titles reach the markup as text, so this section is about escaping "
    "and truncation: scripts that are not Latin, characters that are markup, names longer than "
    "the block they sit in.",
)
NAMES = [
    ("plain", "A plain name", "Jane Doe"),
    ("accents", "Diacritics", "Zoë Ångström-Führer"),
    ("cyrillic", "Cyrillic", "Пётр Ильич Чайковский"),
    ("greek", "Greek", "Κλαύδιος Πτολεμαῖος"),
    ("cjk", "CJK", "李白 · 杜甫"),
    ("arabic", "Arabic (right to left)", "أبو معشر البلخي"),
    ("hebrew", "Hebrew (right to left)", "אברהם אבן עזרא"),
    ("devanagari", "Devanagari", "वराहमिहिर"),
    ("emoji", "Emoji", "Chart 🪐✨ Test"),
    ("markup", "Characters that are markup", "A <b>&amp;</b> \"quoted\" 'name'"),
    ("very_long", "Longer than its block", "Bartholomew Maximilian Fitzwilliam-Cholmondeley the Third of Aberystwyth"),
]
for slug, label, name in NAMES:
    emit(f"name_{slug}", label, name,
         lambda n=name, sl=slug: ChartDrawer(
             ChartDataFactory.create_natal_chart_data(
                 AstrologicalSubjectFactory.from_birth_data(
                     n, 1940, 10, 9, 18, 30, lng=-2.9916, lat=53.4084,
                     tz_str="Europe/London", city="Liverpool", nation="GB",
                     online=False, suppress_geonames_warning=True,
                 )
             )
         ).generate_svg_string())

for slug, label, title in (
    ("short", "Short custom title", "Natal"),
    ("long", "Custom title at the 40-char limit", "A Title That Runs To Forty Characters!!"),
    ("unicode", "Custom title, non-Latin", "出生図 · натальная карта"),
):
    emit(f"title_{slug}", label, f"custom_title={title!r}",
         lambda t=title: ChartDrawer(natal, custom_title=t).generate_svg_string())

emit("name_long_city", "A very long place name",
     "Llanfairpwllgwyngyll… — the location line, not the name",
     lambda: ChartDrawer(
         ChartDataFactory.create_natal_chart_data(
             AstrologicalSubjectFactory.from_birth_data(
                 "Long City", 1940, 10, 9, 18, 30, lng=-4.2, lat=53.22,
                 tz_str="Europe/London",
                 city="Llanfairpwllgwyngyllgogerychwyrndrobwllllantysiliogogogoch",
                 nation="GB", online=False, suppress_geonames_warning=True,
             )
         )
     ).generate_svg_string())


# ---------------------------------------------------------------------------
# 18. Aspect webs
# ---------------------------------------------------------------------------
section(
    "How dense the aspect web is",
    "From no aspects at all to every aspect the library knows at a wide orb. The lines converge "
    "on the middle of the wheel, so this is where the core turns into a solid disc.",
)
ASPECT_SETS = [
    ("none", "No aspects", []),
    ("conjunction_only", "Conjunctions only", [{"name": "conjunction", "orb": 6}]),
    ("tight", "Majors at a 2° orb", [{"name": n, "orb": 2} for n in
                                     ("conjunction", "opposition", "trine", "square", "sextile")]),
    ("default", "The default set", None),
    ("wide", "Majors at a 12° orb", [{"name": n, "orb": 12} for n in
                                     ("conjunction", "opposition", "trine", "square", "sextile")]),
    ("all", "Every aspect", list(ALL_ACTIVE_ASPECTS)),
    ("all_wide", "Every aspect, orbs doubled",
     [{**a, "orb": a["orb"] * 2} for a in ALL_ACTIVE_ASPECTS]),
]
for slug, label, aspects in ASPECT_SETS:
    for style in STYLES:
        emit(f"aspects_{slug}_{style}", f"{label} · {style}",
             "no aspects" if aspects == [] else f"{len(aspects)} kinds" if aspects else "default",
             lambda a=aspects, s=style: ChartDrawer(
                 ChartDataFactory.create_natal_chart_data(john, **({} if a is None else {"active_aspects": a})),
                 show_aspect_movement=True,
             ).generate_svg_string(style=s))


# ---------------------------------------------------------------------------
# 19. Orb configuration
# ---------------------------------------------------------------------------
section(
    "Orb rules",
    "The knobs that decide which contacts exist at all: a tighter limit on the axes, per-point "
    "adjustments, and the two strategies for combining them.",
)
ORB_CASES = [
    ("axis_1", "Axes limited to 1°", dict(axis_orb_limit=1.0)),
    ("axis_10", "Axes allowed 10°", dict(axis_orb_limit=10.0)),
    ("point_tight", "Outer planets tightened",
     dict(point_orb_adjustments={"Uranus": -3.0, "Neptune": -3.0, "Pluto": -3.0})),
    ("point_wide", "Luminaries widened",
     dict(point_orb_adjustments={"Sun": 4.0, "Moon": 4.0})),
    ("strategy_sum", "Adjustments summed",
     dict(point_orb_adjustments={"Sun": 3.0, "Moon": 2.0}, point_orb_adjustment_strategy="sum")),
    ("strategy_max", "The larger adjustment wins",
     dict(point_orb_adjustments={"Sun": 3.0, "Moon": 2.0}, point_orb_adjustment_strategy="max_explicit")),
    ("strategy_min", "The smaller adjustment wins",
     dict(point_orb_adjustments={"Sun": 3.0, "Moon": 2.0}, point_orb_adjustment_strategy="min_explicit")),
    ("strategy_none", "Adjustments ignored",
     dict(point_orb_adjustments={"Sun": 3.0, "Moon": 2.0}, point_orb_adjustment_strategy="none")),
]
for slug, label, kwargs in ORB_CASES:
    emit(f"orb_{slug}", label, ", ".join(f"{k}={v}" for k, v in kwargs.items()),
         lambda k=kwargs: ChartDrawer(
             ChartDataFactory.create_natal_chart_data(john, **k), show_aspect_movement=True
         ).generate_svg_string())


# ---------------------------------------------------------------------------
# 20. Element and quality distribution
# ---------------------------------------------------------------------------
section(
    "Distribution weighting",
    "The percentages under the title come from a weighting choice, so the same sky reports "
    "different balances depending on how the points are counted.",
)
for method in ("classic", "weighted", "traditional"):
    emit(f"dist_{method}", f"distribution: {method}", f"distribution_method={method!r}",
         lambda m=method: ChartDrawer(
             ChartDataFactory.create_natal_chart_data(john, distribution_method=m)
         ).generate_svg_string())
emit("dist_custom", "Custom weights", "custom_distribution_weights",
     lambda: ChartDrawer(
         ChartDataFactory.create_natal_chart_data(
             john, distribution_method="weighted",
             custom_distribution_weights={"Sun": 5.0, "Moon": 5.0, "Ascendant": 4.0},
         )
     ).generate_svg_string())


# ---------------------------------------------------------------------------
# 21. Return and directed charts
# ---------------------------------------------------------------------------
section(
    "Returns and directions",
    "Every return the factory computes and both directed techniques, single wheel and biwheel.",
)
# Heliocentric and node crossings are not `next_return_from_year` return types;
# they have their own entry points, and a heliocentric return needs a body that
# is not the origin — the Sun cannot return to itself.
RETURN_MOMENTS = {
    "Solar": lambda: returns.next_return_from_year(2025, "Solar"),
    "Lunar": lambda: returns.next_return_from_year(2025, "Lunar"),
    "Heliocentric": lambda: returns.next_heliocentric_return_from_year("Mars", 2025),
    "Lunar_Node_Crossing": lambda: returns.next_lunar_node_crossing_from_year(2025),
}
for return_type in RETURN_MOMENTS:
    for mode in ("single", "dual"):
        def render_return(rt=return_type, m=mode):
            moment = RETURN_MOMENTS[rt]()
            data = (
                ChartDataFactory.create_single_wheel_return_chart_data(moment)
                if m == "single"
                else ChartDataFactory.create_return_chart_data(john, moment)
            )
            return ChartDrawer(data, **ALL_MARKS).generate_svg_string()

        emit(f"return_{return_type.lower()}_{mode}", f"{return_type.replace('_', ' ')} · {mode}",
             f"return_type={return_type!r}", render_return)

solar_arc = SolarArcFactory.compute_directed_subject(john, target_year=2000)
emit("directed_solar_arc", "Solar arc directions", "SolarArcFactory.compute(target_year=2000)",
     lambda: ChartDrawer(
         ChartDataFactory.create_progression_chart_data(john, solar_arc), **ALL_MARKS
     ).generate_svg_string())
emit("directed_progression_dual", "Secondary progression · biwheel", "progressed to 2000",
     lambda: ChartDrawer(
         ChartDataFactory.create_progression_chart_data(john, progressed), **ALL_MARKS
     ).generate_svg_string(style="modern"))


# ---------------------------------------------------------------------------
# 22. Minimal charts
# ---------------------------------------------------------------------------
section(
    "How little can be on the wheel",
    "The other end of the load: a chart with one point, with two, with the angles alone. "
    "Grids and aspect tables have to hold their shape when there is almost nothing to put in them.",
)
MINIMAL = [
    ("one_point", "The Sun alone", ["Sun"]),
    ("two_points", "Sun and Moon", ["Sun", "Moon"]),
    ("angles_only", "The four angles", ["Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli"]),
    ("luminaries_angles", "Luminaries and angles",
     ["Sun", "Moon", "Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli"]),
    ("seven", "The seven classical", ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]),
]
for slug, label, points in MINIMAL:
    for style in STYLES:
        emit(f"minimal_{slug}_{style}", f"{label} · {style}", f"{len(points)} active points",
             lambda p=points, s=style, sl=slug: ChartDrawer(
                 ChartDataFactory.create_natal_chart_data(subject(f"Minimal {sl}", active_points=p)),
                 **ALL_MARKS,
             ).generate_svg_string(style=s))


# ---------------------------------------------------------------------------
# 23. Calendar edges
# ---------------------------------------------------------------------------
section(
    "Calendar and clock edges",
    "Moments that break date arithmetic: a leap day, both sides of midnight, the turn of a year, "
    "a daylight-saving jump, and the two extreme offsets from UTC.",
)
EDGES = [
    ("leap_day", "29 February", dict(year=2024, month=2, day=29, hour=12, minute=0)),
    ("midnight", "00:00 exactly", dict(year=1990, month=6, day=15, hour=0, minute=0)),
    ("one_minute_past", "00:01", dict(year=1990, month=6, day=15, hour=0, minute=1)),
    ("one_to_midnight", "23:59", dict(year=1990, month=6, day=15, hour=23, minute=59)),
    ("new_year", "1 January, 00:00", dict(year=2000, month=1, day=1, hour=0, minute=0)),
    ("new_year_eve", "31 December, 23:59", dict(year=1999, month=12, day=31, hour=23, minute=59)),
    ("dst_spring", "Into daylight saving", dict(year=2024, month=3, day=31, hour=2, minute=30)),
    ("dst_autumn", "Out of daylight saving", dict(year=2024, month=10, day=27, hour=2, minute=30)),
]
for slug, label, when in EDGES:
    emit(f"edge_{slug}", label, ", ".join(f"{k}={v}" for k, v in when.items()),
         lambda w=when, sl=slug: ChartDrawer(
             ChartDataFactory.create_natal_chart_data(subject(f"Edge {sl}", **w)), **ALL_MARKS
         ).generate_svg_string())

for slug, label, tz, lng in (
    ("utc_plus_14", "UTC+14 — Kiritimati", "Pacific/Kiritimati", -157.4),
    ("utc_minus_11", "UTC−11 — Niue", "Pacific/Niue", -169.9),
    ("utc_plus_0545", "UTC+5:45 — Kathmandu", "Asia/Kathmandu", 85.3),
    ("utc_plus_0845", "UTC+8:45 — Eucla", "Australia/Eucla", 128.9),
):
    emit(f"tz_{slug}", label, f"tz_str={tz!r}",
         lambda t=tz, ln=lng, sl=slug: ChartDrawer(
             ChartDataFactory.create_natal_chart_data(
                 subject(f"TZ {sl}", year=1990, month=6, day=15, hour=12, minute=0,
                         tz_str=t, lng=ln, lat=0.0, city=sl, nation="XX")
             )
         ).generate_svg_string())


# ---------------------------------------------------------------------------
# 24. Overrides
# ---------------------------------------------------------------------------
section(
    "Colour and label overrides",
    "Two hooks a caller can use to make the chart theirs: a partial colour override, which has to "
    "merge over the palette rather than replace it, and a language pack that renames anything.",
)
def palette(**overrides: str) -> dict:
    """A colour override merged over the defaults.

    ``colors_settings`` replaces the table wholesale and the renderer indexes it
    by key, so handing it a couple of entries raises KeyError partway through
    drawing. Callers that expose this option have to merge; so does this sweep.
    """
    return {**DEFAULT_CHART_COLORS, **overrides}


emit("override_colors_partial", "One colour overridden", 'colors_settings merged: paper_0="#8b0000"',
     lambda: ChartDrawer(natal, colors_settings=palette(paper_0="#8b0000")).generate_svg_string())
emit("override_colors_many", "A whole palette shifted",
     "paper, sun, moon and two aspects",
     lambda: ChartDrawer(natal, colors_settings=palette(
         paper_0="#1b2a41", paper_1="#f2efe6",
         sun="#e07a3f", moon="#5b8fa8",
         conjunction="#7a3f9d", opposition="#c2453d",
     )).generate_svg_string())
emit("override_language_pack", "A language pack", 'language_pack={"zodiac": "Rueda", …}',
     lambda: ChartDrawer(natal, language_pack={
         "zodiac": "Rueda", "tropical": "Trópico", "domification": "Casas",
         "perspective": "Perspectiva", "diurnality": "Sector",
     }).generate_svg_string())
emit("override_both", "Both at once", "colours plus labels",
     lambda: ChartDrawer(
         natal,
         colors_settings=palette(paper_0="#22303c"),
         language_pack={"zodiac": "Zodíaco", "domification": "Domificação"},
     ).generate_svg_string())


# ---------------------------------------------------------------------------
# 25. Post-processing
# ---------------------------------------------------------------------------
section(
    "Post-processing",
    "The same chart written four ways. Inlining the variables is what makes an SVG survive being "
    "embedded somewhere with no stylesheet; minifying is what makes it small.",
)
for slug, label, kwargs in (
    ("plain", "As rendered", {}),
    ("inlined", "CSS variables inlined", dict(remove_css_variables=True)),
    ("minified", "Minified", dict(minify=True)),
    ("both", "Inlined and minified", dict(remove_css_variables=True, minify=True)),
):
    emit(f"post_{slug}", label, ", ".join(f"{k}=True" for k in kwargs) or "no post-processing",
         lambda k=kwargs: ChartDrawer(natal).generate_svg_string(**k))


# ---------------------------------------------------------------------------
# 26. Zodiac types side by side
# ---------------------------------------------------------------------------
section(
    "Tropical against sidereal",
    "The same birth moment under both zodiacs and three ayanamsas — roughly 24° of difference, "
    "which moves nearly every point into the previous sign.",
)
for slug, label, kwargs in (
    ("tropical", "Tropical", dict(zodiac_type="Tropical")),
    ("lahiri", "Sidereal · Lahiri", dict(zodiac_type="Sidereal", sidereal_mode="LAHIRI")),
    ("fagan", "Sidereal · Fagan–Bradley", dict(zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY")),
    ("krishnamurti", "Sidereal · Krishnamurti", dict(zodiac_type="Sidereal", sidereal_mode="KRISHNAMURTI")),
):
    for style in STYLES:
        emit(f"zodiac_{slug}_{style}", f"{label} · {style}", ", ".join(f"{k}={v}" for k, v in kwargs.items()),
             lambda k=kwargs, sl=slug, s=style: ChartDrawer(
                 ChartDataFactory.create_natal_chart_data(subject(f"Zodiac {sl}", **k)),
                 show_ayanamsa_value=True,
             ).generate_svg_string(style=s))


# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------
print(f"\nWriting index for {counters['ok']} charts ({counters['failed']} failed)…")

# The sweep's metadata, so the page can be rebuilt without re-rendering 74MB of
# charts — iterating on the viewer should not cost five minutes of ephemeris.
(OUT / "cards.json").write_text(
    json.dumps(
        {
            "ok": counters["ok"],
            "failed": counters["failed"],
            "sections": [
                {
                    "name": s.name,
                    "blurb": s.blurb,
                    "cards": [vars(c) for c in s.cards],
                }
                for s in sections
            ],
        },
        indent=1,
    ),
    encoding="utf-8",
)

build_index(OUT)
print(f"\nDone — {counters['ok']} rendered, {counters['failed']} failed")
print(f"Open: {OUT / 'index.html'}")
