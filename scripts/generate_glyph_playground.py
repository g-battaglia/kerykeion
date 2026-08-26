#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the glyph playground: one self-contained page for tuning the modern cluster.

The cluster the modern wheel draws around each point — glyph, degrees, sign,
minutes, retrograde mark — is governed by numbers that only look right or wrong
on screen. Deriving them is the job of ``derive_modern_cluster_profiles.py``;
deciding what to derive *towards* is the job of an eye, and an eye needs to see
the alternatives side by side, on real charts, at real size.

So this page ships every alternative pre-drawn. It offers two knobs, and they are
not the same kind of knob:

**Air between clusters** is the renderer's own. Every adjacent pair of clusters
reserves the arc its ink needs plus ``DEFAULT_CLUSTER_CLEARANCE`` of daylight
(0.45 wheel units, about 2 px on a 480 px wheel), capped by the per-ring ceiling
``min_separation``. Neither is a parameter any public API exposes, so the page
cannot move them live: instead this script renders one real chart per value and
the page swaps between them. Nothing on that axis is simulated.

**Row spacing and cluster sizes** are rewritten in the browser, because they are
cheap to fake faithfully: a font-size is a font-size, a scale is a scale. The
page says so, and warns that the row positions a chosen size implies still have
to be re-derived by the script — the preview is honest about magnitudes and
optimistic about the air those magnitudes leave behind.

Two subjects, one single wheel and one dual wheel, three glyph sizes, nine air
steps per ring: 270 charts. Wheel-only, so the eye lands on the wheel.

**The ceiling, and why step 0 is marked.** Raising the air without raising the
ceiling saturates: past a point the cap, not the clearance, decides. So every
step above the first renders with the ceiling lifted out of the way, and the
first step is the chart exactly as the library ships it — measured ceiling
included. On most of these charts the two coincide (the ceiling never binds and
the marked step is simply the 0.45 chart); on the small synastry it genuinely
binds, and the page says so rather than hiding the discontinuity.

**How 270 charts fit in 1.8 MB.** Changing the air moves the planet ring and
nothing else, so each variant travels as a line-level diff against the shipped
chart of its own size — and since most changed lines differ only in one rotation
angle, each diff entry is stored as (line, prefix length, suffix length, the
middle). ``tests/core/test_glyph_playground.py`` pins the round trip: a diff
applied back to its base has to be the render it was taken from, byte for byte.
The page's own reassembly is the same algorithm in JavaScript, checked against
real renders in a browser when the page is built.

Output: ``scripts/glyph_playground.html``, a single file with no external
requests, openable straight from disk in any browser.

Run it with ``poe playground`` (the task pins the ephemeris tier the charts were
drawn with).
"""

import contextlib
import dataclasses
import difflib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tests.data.golden_places import golden_place

from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data.factory import ChartDataFactory
from kerykeion.charts import draw_modern as dm
from kerykeion.charts.drawer import ChartDrawer

OUTPUT = Path(__file__).parent / "glyph_playground.html"

#: Ink-to-ink air between neighbouring clusters, wheel units. The shipped value
#: (``DEFAULT_CLUSTER_CLEARANCE``) is the third entry, so the scale brackets it.
CLEARANCES = [0.20, 0.30, 0.45, 0.60, 0.80, 1.05, 1.35, 1.70]

#: Step 0 is the shipped chart; steps 1..8 are CLEARANCES with the ceiling lifted.
STEP_COUNT = len(CLEARANCES) + 1

#: A ceiling no content-derived separation on these charts can reach, so above
#: step 0 the clearance is the only thing deciding.
UNBOUND_CEILING = 25.0

SIZES = ["small", "medium", "large"]
RINGS = ("natal", "dual_outer", "dual_inner")

JOHN_LENNON_BIRTH_DATA = (1940, 10, 9, 18, 30)
PAUL_MCCARTNEY_BIRTH_DATA = (1942, 6, 18, 15, 30)
LIVERPOOL = golden_place("Liverpool", "GB")


# ── Rendering ───────────────────────────────────────────────────────────────


@contextlib.contextmanager
def _clearance_per_ring(clearances: list[float]):
    """Feed each planet ring its own clearance, in the order the renderer draws.

    The clearance reaches the resolver as a default argument bound when the
    module was imported, so rebinding the module constant would change nothing —
    the resolver itself has to be swapped, and only for as long as it takes to
    draw one chart. The rings come in a fixed order (the single wheel draws one,
    the dual wheel draws outer then inner), which is what makes a queue enough.
    """
    resolve = dm._resolve_planet_collisions
    queue = list(clearances)

    def resolve_with_queued_clearance(
        planets_with_angles,
        min_separation=dm.PLANET_MIN_SEPARATION,
        *,
        row_radii=None,
        clearance=dm.DEFAULT_CLUSTER_CLEARANCE,
    ):
        queued = queue.pop(0) if queue else clearance
        return resolve(planets_with_angles, min_separation=min_separation, row_radii=row_radii, clearance=queued)

    dm._resolve_planet_collisions = resolve_with_queued_clearance
    try:
        yield queue
    finally:
        dm._resolve_planet_collisions = resolve


@contextlib.contextmanager
def _ceiling_lifted(glyph_size: str, rings: tuple[str, ...]):
    """Put ``min_separation`` out of reach on the named rings, then put it back."""
    shipped = {ring: dm.GLYPH_SIZE_PROFILES[glyph_size][ring] for ring in rings}
    for ring, profile in shipped.items():
        dm.GLYPH_SIZE_PROFILES[glyph_size][ring] = dataclasses.replace(profile, min_separation=UNBOUND_CEILING)
    try:
        yield
    finally:
        for ring, profile in shipped.items():
            dm.GLYPH_SIZE_PROFILES[glyph_size][ring] = profile


def render(chart_data, glyph_size: str, clearances: list[float], unbound: tuple[str, ...] = ()) -> str:
    """One wheel-only SVG, drawn with the given air and the named ceilings lifted."""
    with _clearance_per_ring(clearances) as queue, _ceiling_lifted(glyph_size, unbound):
        svg = ChartDrawer(chart_data).generate_wheel_only_svg_string(style="modern", glyph_size=glyph_size)
    assert not queue, f"a ring went undrawn: {queue}"
    return svg


def step_clearance(step: int) -> float:
    """The air a step asks for. Step 0 asks for the shipped value."""
    return dm.DEFAULT_CLUSTER_CLEARANCE if step == 0 else CLEARANCES[step - 1]


def unbound_rings(*steps_and_rings: tuple[int, str]) -> tuple[str, ...]:
    """The rings whose ceiling this variant lifts: every ring above step 0."""
    return tuple(ring for step, ring in steps_and_rings if step > 0)


# ── Variants as diffs ───────────────────────────────────────────────────────


def lines_of(svg: str) -> list[str]:
    """Split the way the page does.

    ``str.split("\n")`` and JavaScript's ``String.prototype.split`` agree on
    everything, including the empty tail a trailing newline leaves behind;
    ``str.splitlines()`` quietly drops it, and the rebuilt chart would then be
    one byte short of the render it claims to be.
    """
    return svg.split("\n")


def compact_diff(base_lines: list[str], variant_lines: list[str]) -> list:
    """The variant as a list of edits against the base.

    Two shapes, told apart by the type of the first element:

    * ``[line, prefix_len, suffix_len, middle]`` — a line replaced by a line.
      Almost every edit is this, and almost every one of those differs in a
      single rotation angle, so only the angle is stored.
    * ``[tag, i1, i2, lines]`` — anything that changes the line count, which a
      per-line rewrite cannot express (a tether that grows an arc, say).
    """
    edits: list = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, base_lines, variant_lines, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace" and (i2 - i1) == (j2 - j1):
            for offset in range(i2 - i1):
                before, after = base_lines[i1 + offset], variant_lines[j1 + offset]
                prefix = 0
                while prefix < len(before) and prefix < len(after) and before[prefix] == after[prefix]:
                    prefix += 1
                suffix = 0
                while (
                    suffix < len(before) - prefix
                    and suffix < len(after) - prefix
                    and before[-1 - suffix] == after[-1 - suffix]
                ):
                    suffix += 1
                edits.append([i1 + offset, prefix, suffix, after[prefix : len(after) - suffix]])
        else:
            edits.append([tag, i1, i2, variant_lines[j1:j2]])
    return edits


def apply_diff(base_lines: list[str], edits: list) -> str:
    """The page's reassembly, in Python — the test compares it to a real render."""
    lines = list(base_lines)
    structural = []
    for edit in edits:
        if isinstance(edit[0], int):
            line, prefix, suffix, middle = edit
            text = lines[line]
            lines[line] = text[:prefix] + middle + text[len(text) - suffix :]
        else:
            structural.append(edit)
    if not structural:
        return "\n".join(lines)
    out: list[str] = []
    cursor = 0
    for tag, i1, i2, replacement in structural:
        out.extend(lines[cursor:i1])
        if tag != "delete":
            out.extend(replacement)
        cursor = i2
    out.extend(lines[cursor:])
    return "\n".join(out)


# ── Data ────────────────────────────────────────────────────────────────────


def build_data() -> dict:
    """Every chart the page can show: three shipped bases, 264 diffs from them."""
    john = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True, **LIVERPOOL
    )
    paul = AstrologicalSubjectFactory.from_birth_data(
        "Paul McCartney", *PAUL_MCCARTNEY_BIRTH_DATA, suppress_geonames_warning=True, **LIVERPOOL
    )
    natal = ChartDataFactory.create_natal_chart_data(john)
    synastry = ChartDataFactory.create_synastry_chart_data(john, paul)

    bases: dict[str, str] = {}
    diffs: dict[str, list] = {}
    ceiling_binds: dict[str, dict[str, bool]] = {}

    for size in SIZES:
        shipped_air = [dm.DEFAULT_CLUSTER_CLEARANCE]
        natal_base = render(natal, size, shipped_air)
        synastry_base = render(synastry, size, shipped_air * 2)
        bases[f"natal__{size}"] = natal_base
        bases[f"synastry__{size}"] = synastry_base

        # Does the shipped ceiling actually cap anything here? The page tells the
        # reader, because where it does, step 0 is not on the same curve as the rest.
        ceiling_binds[size] = {
            "natal": render(natal, size, shipped_air, ("natal",)) != natal_base,
            "synastry": render(synastry, size, shipped_air * 2, ("dual_outer", "dual_inner")) != synastry_base,
        }

        natal_lines = lines_of(natal_base)
        for step in range(1, STEP_COUNT):
            variant = render(natal, size, [step_clearance(step)], ("natal",))
            diffs[f"natal__{size}__c{step}"] = compact_diff(natal_lines, lines_of(variant))

        synastry_lines = lines_of(synastry_base)
        for outer in range(STEP_COUNT):
            for inner in range(STEP_COUNT):
                if outer == inner == 0:
                    continue
                variant = render(
                    synastry,
                    size,
                    [step_clearance(outer), step_clearance(inner)],
                    unbound_rings((outer, "dual_outer"), (inner, "dual_inner")),
                )
                diffs[f"synastry__{size}__o{outer}_i{inner}"] = compact_diff(synastry_lines, lines_of(variant))

    return {
        "manifest": {
            "clearances": CLEARANCES,
            "shippedClearance": dm.DEFAULT_CLUSTER_CLEARANCE,
            "sizes": SIZES,
            "ceilingBinds": ceiling_binds,
            "shippedSeparation": {
                size: {ring: dm.GLYPH_SIZE_PROFILES[size][ring].min_separation for ring in RINGS} for size in SIZES
            },
        },
        "bases": bases,
        "diffs": diffs,
    }


# ── The page ────────────────────────────────────────────────────────────────

PAGE_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Modern cluster playground</title>
<!--
  Generated by scripts/generate_glyph_playground.py — edit the script, not this
  file. Everything the page needs is inlined: no fetch, no external asset, so it
  opens straight from disk in any browser.
-->
<style>
  :root{
    --bg:#f4f4f6; --panel:#ffffff; --ink:#22222a; --muted:#71717f;
    --line:#e2e2e8; --accent:#7f3f00; --chip:#eeeef3;
  }
  *{box-sizing:border-box}
  body{margin:0;font:13px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
       color:var(--ink);background:var(--bg);display:flex;min-height:100vh}
  aside{width:390px;flex:0 0 390px;background:var(--panel);border-right:1px solid var(--line);
        padding:18px 18px 40px;overflow-y:auto;height:100vh}
  main{flex:1;display:flex;flex-direction:column;align-items:center;
       padding:24px;gap:14px;overflow-y:auto;height:100vh}
  h1{font-size:15px;margin:0 0 2px;letter-spacing:.2px}
  h2{font-size:11px;text-transform:uppercase;letter-spacing:.8px;color:var(--muted);
     margin:22px 0 8px;padding-bottom:5px;border-bottom:1px solid var(--line)}
  p.hint{color:var(--muted);font-size:11.5px;margin:0 0 4px}
  .seg{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
  .seg button{flex:1;min-width:78px;padding:7px 6px;border:1px solid var(--line);background:#fff;
              border-radius:7px;cursor:pointer;font:inherit;font-size:12px;color:var(--ink)}
  .seg button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
  fieldset{border:1px solid var(--line);border-radius:9px;padding:10px 12px 12px;margin:0 0 12px}
  legend{font-size:11px;font-weight:600;color:var(--accent);padding:0 5px;text-transform:uppercase;letter-spacing:.6px}
  .row{display:grid;grid-template-columns:58px 1fr 118px;align-items:center;gap:8px;margin:5px 0}
  .row label{font-size:12px}
  .row output{font-variant-numeric:tabular-nums;font-size:11px;color:var(--muted);text-align:right}
  .row output b{color:var(--ink);font-weight:600}
  input[type=range]{width:100%;accent-color:var(--accent)}
  .btns{display:flex;gap:8px;margin-top:6px}
  .btns button{padding:6px 10px;border:1px solid var(--line);background:#fff;border-radius:7px;
               cursor:pointer;font:inherit;font-size:12px}
  .btns button:hover{border-color:var(--accent);color:var(--accent)}
  #stage{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px;
         box-shadow:0 1px 3px rgba(0,0,0,.05)}
  #stage svg{display:block}
  .stagebar{display:flex;gap:10px;align-items:center;color:var(--muted);font-size:11.5px}
  .stagebar select{font:inherit;padding:3px 6px;border-radius:6px;border:1px solid var(--line);background:#fff}
  textarea{width:100%;height:190px;font:11.5px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;
           border:1px solid var(--line);border-radius:8px;padding:9px;resize:vertical;background:#fbfbfd}
  .note{font-size:11px;color:var(--muted);background:var(--chip);border-radius:7px;padding:8px 10px;margin:10px 0 0}
  .note.binds{background:#fff4e5;color:#7a4a00}
  code{font:11.5px ui-monospace,Menlo,monospace;background:var(--chip);padding:1px 4px;border-radius:4px}
</style>
</head>
<body>
<aside>
  <h1>Modern cluster playground</h1>
  <p class="hint">Real <b>wheel-only</b> SVGs, modern style, light theme.</p>

  <h2>Chart</h2>
  <div class="seg" id="chartSeg"></div>
  <div class="seg" id="sizeSeg"></div>

  <h2>Air between clusters</h2>
  <p class="hint">Redrawn by the renderer: every notch is a chart kerykeion actually
     produced, not a stretched one.</p>
  <div id="airControls"></div>

  <h2>Cluster sizes</h2>
  <p class="hint">Multipliers on the current render (1.00 = as it draws today).</p>
  <div id="sizeControls"></div>

  <h2>Row spacing</h2>
  <p class="hint">Squeezes or opens the gaps between glyph, degrees, sign, minutes
     and ℞, holding the glyph still.</p>
  <div id="leadControls"></div>

  <div class="btns">
    <button id="resetView">Reset this view</button>
    <button id="resetAll">Reset everything</button>
  </div>

  <h2>Summary</h2>
  <textarea id="recap" readonly></textarea>
  <div class="btns"><button id="copyRecap">Copy to clipboard</button></div>

  <div class="note" id="ceilingNote"></div>
  <div class="note">Air is a real render. Sizes and row spacing are rewritten in the
     browser: faithful about magnitudes, but the row positions a chosen size implies
     still have to come back out of <code>derive_modern_cluster_profiles.py</code>.</div>
</aside>

<main>
  <div class="stagebar">
    <span id="crumb"></span>
    <label>view <select id="zoom">
      <option value="520">520 px</option>
      <option value="640" selected>640 px</option>
      <option value="800">800 px</option>
      <option value="960">960 px</option>
    </select></label>
  </div>
  <div id="stage"></div>
</main>

<script>
/* ══ Data ══════════════════════════════════════════════════════════════════
   DATA.bases  — the shipped chart for each chart+size, as SVG text.
   DATA.diffs  — every other variant, as edits against its base (see the
                 script's docstring for the two edit shapes).
   DATA.manifest — the numbers the UI quotes back: the air scale, the shipped
                 clearance, the per-ring ceilings, and where the ceiling binds. */
__PLAYGROUND_DATA__
const M = DATA.manifest;
const AIR = M.clearances, SHIPPED_AIR = M.shippedClearance;
const AIR_STEPS = AIR.length + 1;         // step 0 is the shipped chart
const PX_PER_UNIT = 4.8;                  // a 100-unit viewBox on a 480 px wheel

const ELEMENTS = [
  {key:'glyph',   label:'glyph'},
  {key:'degrees', label:'degrees'},
  {key:'sign',    label:'sign'},
  {key:'minutes', label:'minutes'},
  {key:'rx',      label:'℞'},
];
const CHARTS = [{id:'natal', label:'Natal'}, {id:'synastry', label:'Synastry'}];
const SIZES  = M.sizes.map(id => ({id, label: id[0].toUpperCase() + id.slice(1)}));
const RINGS  = {
  natal:    [{id:'natal', label:'wheel'}],
  synastry: [{id:'outer', label:'outer ring'}, {id:'inner', label:'inner ring'}],
};

/* ══ State ═════════════════════════════════════════════════════════════════
   Every chart+size pair keeps its own knobs, so switching away and back does
   not throw away a comparison in progress. */
const state = {chart:'natal', size:'medium', views:{}};
const viewKey = () => state.chart + '/' + state.size;

function view(){
  if(!state.views[viewKey()]){
    const fresh = {air:{}, mult:{}, lead:{}};
    for(const ring of RINGS[state.chart]){
      fresh.air[ring.id] = 0;
      fresh.lead[ring.id] = 1;
      fresh.mult[ring.id] = Object.fromEntries(ELEMENTS.map(e => [e.key, 1]));
    }
    state.views[viewKey()] = fresh;
  }
  return state.views[viewKey()];
}

/* ══ Variant assembly ══════════════════════════════════════════════════════ */
const CACHE = new Map();

function assemble(baseLines, edits){
  const lines = baseLines.slice();
  const structural = [];
  for(const edit of edits){
    if(typeof edit[0] === 'number'){
      const [index, prefix, suffix, middle] = edit;
      const text = lines[index];
      lines[index] = text.slice(0, prefix) + middle + text.slice(text.length - suffix);
    } else {
      structural.push(edit);          // changes the line count: applied below
    }
  }
  if(structural.length === 0) return lines.join('\n');
  const out = [];
  let cursor = 0;
  for(const [tag, i1, i2, replacement] of structural){
    while(cursor < i1) out.push(lines[cursor++]);
    if(tag !== 'delete') for(const line of replacement) out.push(line);
    cursor = i2;
  }
  while(cursor < lines.length) out.push(lines[cursor++]);
  return out.join('\n');
}

function variant(key){
  if(CACHE.has(key)) return CACHE.get(key);
  const base = DATA.bases[key.slice(0, key.lastIndexOf('__'))];
  if(base === undefined) throw new Error('no base for ' + key);
  const edits = DATA.diffs[key];
  const svg = edits ? assemble(base.split('\n'), edits) : base;
  CACHE.set(key, svg);
  return svg;
}

function currentKey(){
  const v = view();
  return state.chart === 'natal'
    ? `natal__${state.size}__c${v.air.natal}`
    : `synastry__${state.size}__o${v.air.outer}_i${v.air.inner}`;
}

/* ══ Reading the markup ════════════════════════════════════════════════════
   A cluster is a <g kr:node='ChartPoint'> holding up to five rows. Which row
   is which is legible from the markup itself: the two glyph groups carry the
   symbol's own centring translate, and the three texts are told apart by what
   they say. */
function classify(node){
  if(node.tagName === 'text'){
    const text = (node.textContent || '').trim();
    if(text.includes('º') || text.includes('°')) return 'degrees';
    if(text.includes("'")) return 'minutes';
    return 'rx';
  }
  const transform = node.getAttribute('transform') || '';
  if(transform.includes('translate(-12 -12)')) return 'glyph';
  if(transform.includes('translate(-16 -16)')) return 'sign';
  return null;
}

function firstTranslateY(transform){
  const match = transform.match(/translate\(\s*(-?[\d.]+)[\s,]+(-?[\d.]+)\s*\)/);
  return match ? parseFloat(match[2]) : null;
}

function indexClusters(svg){
  const clusters = [];
  svg.querySelectorAll("g[kr\\:node='ChartPoint']").forEach(group => {
    const ring = state.chart === 'natal' ? 'natal'
               : (group.getAttribute('kr:horoscope') === '1' ? 'outer' : 'inner');
    const rows = [];
    group.querySelectorAll(':scope > g, :scope > text').forEach(el => {
      const kind = classify(el);
      if(!kind) return;
      const transform = el.getAttribute('transform') || '';
      // The pristine values: every rewrite starts from these, never from the
      // last rewrite, so dragging a slider back and forth cannot drift.
      el.dataset.t0 = transform;
      el.dataset.y0 = el.tagName === 'text' ? el.getAttribute('y') : firstTranslateY(transform);
      if(el.tagName === 'text') el.dataset.fs0 = el.getAttribute('font-size');
      rows.push({kind, el, y0: parseFloat(el.dataset.y0)});
    });
    if(rows.length) clusters.push({ring, rows, anchor: Math.min(...rows.map(r => r.y0))});
  });
  return clusters;
}

/* ══ Rewriting ═════════════════════════════════════════════════════════════
   Size scales the mark; row spacing moves it along the radius. The glyph is
   the anchor — it sits closest to the tether and is the row parity pins — so
   spacing pushes the other rows towards or away from it. */
function rewrite(row, y, mult){
  const el = row.el, original = el.dataset.t0;
  if(el.tagName === 'text'){
    const size = parseFloat(el.dataset.fs0) * mult;
    el.setAttribute('font-size', size.toFixed(4));
    el.setAttribute('y', y.toFixed(4));
    // The rotate pivot follows the row, and the baseline nudge is a tenth of
    // the font size, so it scales with it.
    let transform = original.replace(/rotate\(\s*(-?[\d.]+)[\s,]+(-?[\d.]+)[\s,]+(-?[\d.]+)\s*\)/,
                                     (m, angle, cx) => `rotate(${angle} ${cx} ${y.toFixed(4)})`);
    transform = transform.replace(/translate\(\s*(-?[\d.]+)[\s,]+(-?[\d.]+)\s*\)/,
                                  (m, x, dy) => `translate(${x} ${(parseFloat(dy) * mult).toFixed(4)})`);
    el.setAttribute('transform', transform);
  } else {
    // Glyph groups: the leading translate places the row, the scale sizes it,
    // and the trailing translate(-12 -12) centres the symbol and stays put.
    let transform = original.replace(/translate\(\s*(-?[\d.]+)[\s,]+(-?[\d.]+)\s*\)/,
                                     (m, x) => `translate(${x} ${y.toFixed(4)})`);
    transform = transform.replace(/scale\(\s*(-?[\d.]+)\s*\)/,
                                  (m, s) => `scale(${(parseFloat(s) * mult).toFixed(6)})`);
    el.setAttribute('transform', transform);
  }
}

function repaint(){
  const v = view();
  for(const cluster of clusters){
    const lead = v.lead[cluster.ring], mult = v.mult[cluster.ring];
    for(const row of cluster.rows){
      rewrite(row, cluster.anchor + (row.y0 - cluster.anchor) * lead, mult[row.kind]);
    }
  }
}

/* ══ What the current chart actually draws ═════════════════════════════════
   Read back off the SVG rather than tabulated here: the summary then quotes
   the renderer, not this file's idea of it. */
function measure(){
  const found = {};
  for(const cluster of clusters){
    const ring = found[cluster.ring] || (found[cluster.ring] = {anchor: cluster.anchor, rows: {}});
    for(const row of cluster.rows){
      if(ring.rows[row.kind]) continue;
      const el = row.el;
      const scale = (el.dataset.t0.match(/scale\(\s*(-?[\d.]+)\s*\)/) || [null, '0'])[1];
      ring.rows[row.kind] = el.tagName === 'text'
        ? {unit:'font-size', base: parseFloat(el.dataset.fs0), y0: row.y0}
        : {unit:'scale', base: parseFloat(scale), y0: row.y0};
    }
  }
  return found;
}
const metric = (ring, kind) => measures[ring] && measures[ring].rows[kind];

/* ══ Controls ══════════════════════════════════════════════════════════════ */
let clusters = [], measures = {};

function segmented(host, items, current, pick){
  host.innerHTML = '';
  for(const item of items){
    const button = document.createElement('button');
    button.textContent = item.label;
    button.setAttribute('aria-pressed', String(item.id === current));
    button.onclick = () => pick(item.id);
    host.appendChild(button);
  }
}

function airLabel(step){
  if(step === 0){
    return `★ as shipped · air ${SHIPPED_AIR.toFixed(2)} (${(SHIPPED_AIR * PX_PER_UNIT).toFixed(1)} px at 480) with the measured ceiling`;
  }
  const air = AIR[step - 1];
  return `air ${air.toFixed(2)} · ${(air * PX_PER_UNIT).toFixed(1)} px at 480 · ceiling lifted`;
}

function slider(host, {label, min, max, step, value, format, on}){
  const row = document.createElement('div');
  row.className = 'row';
  const name = document.createElement('label');
  name.textContent = label;
  const input = document.createElement('input');
  Object.assign(input, {type:'range', min, max, step, value});
  const readout = document.createElement('output');
  readout.innerHTML = format(value);
  input.oninput = () => {
    const next = parseFloat(input.value);
    readout.innerHTML = format(next);
    on(next);
  };
  row.append(name, input, readout);
  host.appendChild(row);
}

function sizeReadout(ring, key, value){
  const m = metric(ring, key);
  if(!m) return `<b>${value.toFixed(2)}×</b>`;
  return `<b>${value.toFixed(2)}×</b> → ${(m.base * value).toFixed(m.unit === 'scale' ? 5 : 3)}`;
}

function buildControls(){
  const v = view(), rings = RINGS[state.chart];

  const air = document.getElementById('airControls');
  air.innerHTML = '';
  for(const ring of rings){
    const box = document.createElement('fieldset');
    box.innerHTML = `<legend>${ring.label}</legend>`;
    slider(box, {
      label:'air', min:0, max:AIR_STEPS - 1, step:1, value:v.air[ring.id],
      format: x => `<b>${x === 0 ? SHIPPED_AIR.toFixed(2) + ' ★' : AIR[x - 1].toFixed(2)}</b>`,
      on: x => { v.air[ring.id] = x; document.getElementById('airLabel-' + ring.id).textContent = airLabel(x); show(); },
    });
    const caption = document.createElement('div');
    caption.className = 'hint';
    caption.id = 'airLabel-' + ring.id;
    caption.textContent = airLabel(v.air[ring.id]);
    box.appendChild(caption);
    air.appendChild(box);
  }

  const sizes = document.getElementById('sizeControls');
  const leads = document.getElementById('leadControls');
  sizes.innerHTML = leads.innerHTML = '';
  for(const ring of rings){
    const sizeBox = document.createElement('fieldset');
    sizeBox.innerHTML = `<legend>${ring.label}</legend>`;
    for(const element of ELEMENTS){
      slider(sizeBox, {
        label: element.label, min:0.6, max:1.4, step:0.01, value:v.mult[ring.id][element.key],
        format: x => sizeReadout(ring.id, element.key, x),
        on: x => { v.mult[ring.id][element.key] = x; repaint(); recap(); },
      });
    }
    sizes.appendChild(sizeBox);

    const leadBox = document.createElement('fieldset');
    leadBox.innerHTML = `<legend>${ring.label}</legend>`;
    slider(leadBox, {
      label:'rows', min:0.7, max:1.3, step:0.01, value:v.lead[ring.id],
      format: x => `<b>${x.toFixed(2)}×</b>`,
      on: x => { v.lead[ring.id] = x; repaint(); recap(); },
    });
    leads.appendChild(leadBox);
  }

  document.getElementById('crumb').textContent = `${state.chart} · ${state.size} · wheel only`;
  const binds = M.ceilingBinds[state.size][state.chart];
  const note = document.getElementById('ceilingNote');
  note.className = 'note' + (binds ? ' binds' : '');
  note.innerHTML = binds
    ? `Here the measured ceiling (<code>min_separation</code>) really does cap the
       separation: ★ is the only notch that respects it, the others lift it so the
       air is what decides.`
    : `Here the measured ceiling never binds: ★ and the ${SHIPPED_AIR.toFixed(2)} notch
       draw the same chart.`;
}

function refreshSizeReadouts(){
  const v = view();
  document.querySelectorAll('#sizeControls fieldset').forEach((box, index) => {
    const ring = RINGS[state.chart][index].id;
    box.querySelectorAll('.row').forEach((row, position) => {
      const key = ELEMENTS[position].key;
      row.querySelector('output').innerHTML = sizeReadout(ring, key, v.mult[ring][key]);
    });
  });
}

/* ══ Showing a chart ═══════════════════════════════════════════════════════ */
function show(){
  const stage = document.getElementById('stage');
  stage.innerHTML = variant(currentKey());
  const svg = stage.querySelector('svg');
  const px = document.getElementById('zoom').value;
  svg.setAttribute('width', px);
  svg.setAttribute('height', px);
  clusters = indexClusters(svg);
  measures = measure();
  repaint();
  refreshSizeReadouts();
  recap();
}

/* ══ Summary ═══════════════════════════════════════════════════════════════
   Written to be pasted back into a conversation about the numbers: it carries
   the multipliers, what they resolve to, the rows they imply, and the shipped
   ceilings for context. */
function recap(){
  const v = view(), rings = RINGS[state.chart], lines = [];
  lines.push(`chart: ${state.chart} · glyph size: ${state.size} · wheel only`);
  lines.push('');
  lines.push('air between clusters (clearance, wheel units):');
  for(const ring of rings){
    const step = v.air[ring.id];
    lines.push(`  ${ring.label}: ` + (step === 0
      ? `${SHIPPED_AIR.toFixed(2)}  (as shipped, measured ceiling)`
      : `${AIR[step - 1].toFixed(2)}  (ceiling lifted)`));
  }
  lines.push('');
  lines.push('sizes (multiplier, and what it resolves to):');
  for(const ring of rings){
    lines.push(`  ${ring.label}:`);
    for(const element of ELEMENTS){
      const m = metric(ring.id, element.key);
      const value = v.mult[ring.id][element.key];
      const digits = m && m.unit === 'scale' ? 6 : 4;
      const resolved = m ? `${m.unit} ${m.base.toFixed(digits)} → ${(m.base * value).toFixed(digits)}` : '—';
      lines.push(`    ${element.label.padEnd(7)} ${value.toFixed(2)}×   ${resolved}`);
    }
  }
  lines.push('');
  lines.push('row spacing (multiplier on the gaps, glyph held still):');
  for(const ring of rings){
    const found = measures[ring.id];
    const rows = found ? '   rows → ' + ELEMENTS.map(element => {
      const m = found.rows[element.key];
      return m ? (found.anchor + (m.y0 - found.anchor) * v.lead[ring.id]).toFixed(4) : '—';
    }).join(' / ') : '';
    lines.push(`  ${ring.label}: ${v.lead[ring.id].toFixed(2)}×${rows}`);
  }
  lines.push('');
  const shipped = M.shippedSeparation[state.size];
  lines.push('for context — separation ceiling shipped at this size:');
  lines.push(state.chart === 'natal'
    ? `  wheel: ${shipped.natal}°`
    : `  outer: ${shipped.dual_outer}°   inner: ${shipped.dual_inner}°`);
  document.getElementById('recap').value = lines.join('\n');
}

/* ══ Boot ══════════════════════════════════════════════════════════════════ */
function renderSegments(){
  segmented(document.getElementById('chartSeg'), CHARTS, state.chart, id => {
    if(id === state.chart) return;
    state.chart = id;
    renderSegments(); buildControls(); show();
  });
  segmented(document.getElementById('sizeSeg'), SIZES, state.size, id => {
    if(id === state.size) return;
    state.size = id;
    renderSegments(); buildControls(); show();
  });
}

document.getElementById('zoom').onchange = () => {
  const svg = document.querySelector('#stage svg');
  if(!svg) return;
  const px = document.getElementById('zoom').value;
  svg.setAttribute('width', px);
  svg.setAttribute('height', px);
};
document.getElementById('resetView').onclick = () => {
  delete state.views[viewKey()];
  buildControls(); show();
};
document.getElementById('resetAll').onclick = () => {
  state.views = {};
  buildControls(); show();
};
document.getElementById('copyRecap').onclick = () => {
  const box = document.getElementById('recap');
  box.select();
  document.execCommand('copy');
};

renderSegments();
buildControls();
show();
</script>
</body>
</html>
"""


def main() -> None:
    # The charts are the point, so they must come from the library next door and
    # not from whatever an editable install left on sys.path.
    from tests.data.regeneration_guard import require_library_from_this_checkout

    require_library_from_this_checkout(__file__)

    data = build_data()
    blob = json.dumps(json.dumps(data, separators=(",", ":")))
    # A literal "</" would end the script element early, whatever it belongs to.
    blob = blob.replace("</", "<\\/")
    page = PAGE_TEMPLATE.replace("__PLAYGROUND_DATA__", "const DATA = JSON.parse(" + blob + ");")
    OUTPUT.write_text(page, encoding="utf-8")
    variants = len(data["bases"]) + len(data["diffs"])
    print(
        f"  OK  {OUTPUT.relative_to(Path(__file__).parent.parent)} ({variants} charts, {OUTPUT.stat().st_size / 1e6:.1f} MB)"
    )


if __name__ == "__main__":
    main()
