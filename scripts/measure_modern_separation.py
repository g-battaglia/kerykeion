"""Measure how much angular separation each modern planet ring actually needs.

``draw_modern._resolve_planet_collisions`` pushes cramped clusters apart until a
fixed number of degrees separates them. Set it too low and glyphs overlap; too
high and every stellium is fanned wider than the ink requires, dragging long
tether lines behind it. This harness finds where the boundary really is, and is
the derivation behind ``PLANET_MIN_SEPARATION``, ``SYN_OUTER_MIN_SEPARATION``
and ``SYN_INNER_MIN_SEPARATION``.

**Re-run it after changing any ring radius, row position, font size or glyph
scale in draw_modern** — those are the inputs the separations were derived
from, and ``tests/core/test_modern_decluttering.py`` fails on purpose when they
move, to send you back here.

Why a browser rather than arithmetic. Two things defeat a
"glyph width / arc per degree" estimate:

1. **Nominal boxes lie.** A planet glyph is placed with ``translate(-14 -14)``,
   as if it filled a 28-unit box. Almost none do — the Sun is a stroked ``r=9``
   circle, 19.8 units of ink. Text is worse: a font's layout box runs from full
   ascent to full descent, a third taller than the marks "29º" actually draws.
2. **Glyphs stay upright, the wheel does not.** Each cluster is counter-rotated
   so its text reads horizontally, so two neighbouring clusters are two
   *axis-aligned* boxes whose offset direction depends on where the pair sits on
   the wheel. At the top of the wheel that offset is horizontal and width binds;
   on the diagonal the boxes slide past each other corner-first and the same
   separation buys more room.

A browser already answers both exactly, so the harness asks it: it renders the
adversarial cluster — every glyph the renderer knows, all at 29º59' and
retrograde so every row carries its widest content, jammed so consecutive pairs
sit at exactly the separation under test, repeated at several wheel
orientations — and reads back real ink boxes via ``getBoundingClientRect`` and
``measureText``. It reports, per ring and per separation, the smallest gap
between any two different clusters.

Usage::

    python3 scripts/measure_modern_separation.py                      # floor mode
    python3 scripts/measure_modern_separation.py --mode adversarial   # overlap check
    python3 scripts/measure_modern_separation.py --mode dump-ink      # write glyph_ink_metrics.py
    # then open the printed URL; results appear when the page finishes

Three modes, one server:

- **floor** — how tight can a separation constant go before ink touches
  (adversarial worst-content clusters at forced separations).
- **adversarial** — render mixed-content clusters (narrow next to wide,
  retrograde next to direct) with the renderer's *own* placement policy and
  assert no ink overlaps. Run after any change to the placement code.
- **dump-ink** — rasterize every symbol and write the measured ink extents to
  ``kerykeion/charts/glyph_ink_metrics.py`` (also: ``poe regenerate:glyph-ink``).

@module scripts.measure_modern_separation
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import re
import socketserver
import sys
import tempfile
import webbrowser
import xml.etree.ElementTree as ElementTree
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kerykeion.charts import draw_modern as dm
from kerykeion.schemas.models import KerykeionPointModel
from kerykeion.settings.chart_defaults import KNOWN_GLYPH_NAMES

TEMPLATE = Path(__file__).resolve().parent.parent / "kerykeion" / "charts" / "templates" / "modern_wheel.xml"

#: Every glyph the planet ring can be asked to draw. Unknown point names resolve
#: to "FixedStar", so it belongs in the set even though it is not a point name.
GLYPHS = sorted(KNOWN_GLYPH_NAMES | {"FixedStar"})

#: Glyphs per synthetic cluster. Beyond this the cluster wraps onto itself and
#: the resolver's ``320/n`` cap takes over from the separation under test.
CHUNK = 14

#: Cluster start angles, so each pair is also seen at several wheel
#: orientations. Denser than a quadrant sweep on purpose: separations are now
#: orientation-aware, so the probe must sample cardinal, diagonal, and
#: in-between placements rather than trust any single one.
BASE_ANGLES = (0.0, 13.0, 23.0, 37.0, 45.0, 58.0, 71.0, 84.0)

SEPARATIONS = [round(4.0 + 0.25 * i, 2) for i in range(29)]


def _fake_point(
    name: str,
    abs_pos: float,
    position: float = 29.983,
    retrograde: bool = True,
) -> KerykeionPointModel:
    """A synthetic point; the default content (29º59', retrograde) is the widest."""
    return KerykeionPointModel(
        name=name,
        quality="Fixed",
        element="Air",
        sign="Aqu",
        sign_num=10,
        position=position,
        abs_pos=abs_pos % 360.0,
        emoji="",
        point_type="AstrologicalPoint",
        house="First_House",
        retrograde=retrograde,
    )


def _fake_houses() -> list[KerykeionPointModel]:
    return [
        KerykeionPointModel(
            name="First_House",
            quality="Fixed",
            element="Air",
            sign="Aqu",
            sign_num=10,
            position=0.0,
            abs_pos=i * 30.0,
            emoji="",
            point_type="House",
        )
        for i in range(12)
    ]


_SETTINGS = [{"name": name, "color": "#333333", "id": i} for i, name in enumerate(GLYPHS)]

#: The three planet rings draw_modern lays out, with the arguments that make
#: _draw_planet_ring produce each one. Kept as references to the module's own
#: constants so this harness cannot drift from what the renderer does.
RINGS: dict[str, dict] = {
    "natal": {},
    "dual-outer": dict(
        ring_inner_r=dm.SYN_R_OUTER_PLANET_INNER,
        ring_outer_r=dm.SYN_R_OUTER_PLANET_OUTER,
        line_outer_y=dm.SYN_HOUSE_LINE_OUTER_Y1,
        line_inner_y=dm.SYN_HOUSE_LINE_OUTER_Y2,
        planet_y_config={
            "glyph_y": dm.SYN_OUTER_PLANET_GLYPH_Y,
            "degrees_y": dm.SYN_OUTER_DEGREES_Y,
            "sign_y": dm.SYN_OUTER_SIGN_Y,
            "minutes_y": dm.SYN_OUTER_MINUTES_Y,
            "rx_y": dm.SYN_OUTER_RX_Y,
        },
        scale_config={
            "planet_scale_base": dm.SYN_PLANET_SCALE,
            "degrees_font_size": dm.SYN_DEGREES_FONT_SIZE,
            "sign_scale_base": dm.SYN_SIGN_SCALE,
            "minutes_font_size": dm.SYN_MINUTES_FONT_SIZE,
            "rx_font_size": dm.SYN_RX_FONT_SIZE,
        },
    ),
    "dual-inner": dict(
        ring_inner_r=dm.SYN_R_INNER_PLANET_INNER,
        ring_outer_r=dm.SYN_R_INNER_PLANET_OUTER,
        line_outer_y=dm.SYN_HOUSE_LINE_INNER_Y1,
        line_inner_y=dm.SYN_HOUSE_LINE_INNER_Y2,
        planet_y_config={
            "glyph_y": dm.SYN_INNER_PLANET_GLYPH_Y,
            "degrees_y": dm.SYN_INNER_DEGREES_Y,
            "sign_y": dm.SYN_INNER_SIGN_Y,
            "minutes_y": dm.SYN_INNER_MINUTES_Y,
            "rx_y": dm.SYN_INNER_RX_Y,
        },
        scale_config={
            "planet_scale_base": dm.SYN_PLANET_SCALE_INNER,
            "degrees_font_size": dm.SYN_DEGREES_FONT_SIZE_INNER,
            "sign_scale_base": dm.SYN_SIGN_SCALE,
            "minutes_font_size": dm.SYN_MINUTES_FONT_SIZE,
            "rx_font_size": dm.SYN_RX_FONT_SIZE,
        },
    ),
}


#: The separation each ring's call site actually passes (draw_modern_dual_horoscope
#: hands the SYN_* constants to _draw_planet_ring; the natal path takes the default).
RING_SEPARATIONS = {
    "natal": lambda: dm.PLANET_MIN_SEPARATION,
    "dual-outer": lambda: dm.SYN_OUTER_MIN_SEPARATION,
    "dual-inner": lambda: dm.SYN_INNER_MIN_SEPARATION,
}

#: Content palette for the adversarial mode: (position within sign, retrograde).
#: Cycled across a cluster so neighbours mix narrow ("0º3'") against wide
#: ("29º58'") and retrograde against not — the pairs a content-aware separation
#: gets wrong first.
ADVERSARIAL_CONTENT = [
    (29.983, True),
    (0.05, False),
    (9.983, True),
    (14.5, False),
    (29.983, False),
    (1.9, True),
    (22.33, False),
    (5.75, True),
]

#: Spacing patterns for adversarial clusters, degrees between consecutive true
#: positions. "Jammed" forces every pair to the resolver's separation; "ragged"
#: mixes pairs the resolver must spread with pairs it must leave alone.
ADVERSARIAL_SPACINGS = {"jam": 0.01, "ragged": 3.0}


def _wheel_svg(body: str) -> str:
    head, _, _ = TEMPLATE.read_text().partition("</defs>")
    # The font pin matters as much here as in production: without it the probe
    # page's own CSS would bleed into the SVG under test and every gap would be
    # measured in a font no chart renders.
    wheel = (
        f'<g kr:node="ModernHoroscope" font-family="{dm.MODERN_TEXT_FONT_FAMILY}" '
        f'transform="rotate(-90 {dm.CENTER} {dm.CENTER})">\n{body}</g>\n'
    )
    return f"{head}</defs>\n{wheel}</svg>\n"


def build_svg(ring: str, separation: float, order: list[str], base_angle: float) -> str:
    """One ring holding *order*'s glyphs with adjacent pairs exactly *separation* apart."""
    # Hand the resolver a cluster far tighter than the separation, so it spreads
    # every pair to exactly that separation — the state the constant claims safe.
    points = [_fake_point(name, base_angle + i * 0.01) for i, name in enumerate(order)]
    body = dm._draw_planet_ring(
        planets=points,
        planets_settings=_SETTINGS,
        seventh_house_degree_ut=0.0,
        houses=_fake_houses(),
        min_separation=separation,
        show_zodiac_background_ring=False,
        content_aware_separation=False,  # floor mode probes EXACT spacings
        **RINGS[ring],
    )
    return _wheel_svg(body)


def build_adversarial_svg(ring: str, order: list[str], base_angle: float, step: float) -> str:
    """One ring rendered exactly as the library would, with mixed content.

    Unlike :func:`build_svg` this does not force a separation: it passes the
    ring's own constant, so whatever placement policy the renderer currently
    has (scalar or content-aware) is what gets validated.
    """
    points = [
        _fake_point(name, base_angle + i * step, position=pos, retrograde=retro)
        for i, (name, (pos, retro)) in enumerate(
            zip(order, (ADVERSARIAL_CONTENT[i % len(ADVERSARIAL_CONTENT)] for i in range(len(order))))
        )
    ]
    body = dm._draw_planet_ring(
        planets=points,
        planets_settings=_SETTINGS,
        seventh_house_degree_ut=0.0,
        houses=_fake_houses(),
        min_separation=RING_SEPARATIONS[ring](),
        show_zodiac_background_ring=False,
        **RINGS[ring],
    )
    return _wheel_svg(body)


def cluster_orders() -> list[list[str]]:
    """Glyph groupings that give each glyph several different neighbours."""
    orders: list[list[str]] = []
    for shift in range(0, len(GLYPHS), 7):
        rotated = GLYPHS[shift:] + GLYPHS[:shift]
        orders.extend(rotated[i : i + CHUNK] for i in range(0, len(rotated), CHUNK))
    return [chunk for chunk in orders if len(chunk) > 1]


PROBE_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>modern separation probe</title>
<style>body{font-family:monospace;margin:0;padding:12px}
#stage{width:900px;height:900px;position:absolute;left:-4000px;top:0}
#out{white-space:pre;font-size:13px}</style></head>
<body><div id="stage"></div><div id="out">measuring…</div>
<script>
const PX_PER_UNIT = 9;                       // 900px stage over a 100-unit viewBox
// Max stroke width of each symbol, native units: getBoundingClientRect
// excludes stroke, and half the glyphs are stroke-only, so their rects are
// padded by half the stroke at the on-screen scale.
const SYMBOL_STROKE_WIDTHS = __STROKE_WIDTHS__;
// The adversarial gate: the smallest gap any pair may show, wheel units.
// Zero would only prove "not literally touching"; the calibration promises
// visible daylight, and the probe and the ink tables disagree by about a
// pixel (~0.11 units), so anything below this is a regression to fail on.
const MIN_ACCEPTED_GAP = __MIN_ACCEPTED_GAP__;
const stage = document.getElementById('stage');
const ctx = document.createElement('canvas').getContext('2d');

// Real ink box of an SVG <text>, in screen pixels.
//
// getBoundingClientRect returns the font's layout box — full ascent to full
// descent — which for "29º" is a third taller than the marks actually drawn,
// so the ink is measured with canvas measureText instead. Crucially, at the
// SIZE THE TEXT ACTUALLY RENDERS: the element's font-size attribute is in SVG
// user units (e.g. "1.85"), and feeding that to measureText as pixels makes
// the font engine hint glyphs onto a couple of whole pixels — scaled back up,
// that error dwarfed the gaps this probe exists to measure.
function textInkRect(el) {
  const rect = el.getBoundingClientRect();
  const cs = getComputedStyle(el);
  const renderedPx = parseFloat(el.getAttribute('font-size')) * PX_PER_UNIT;
  ctx.font = `${cs.fontWeight} ${renderedPx}px ${cs.fontFamily}`;
  const m = ctx.measureText(el.textContent);
  const width = m.actualBoundingBoxLeft + m.actualBoundingBoxRight;
  const height = m.actualBoundingBoxAscent + m.actualBoundingBoxDescent;
  if (!(width > 0) || !(height > 0)) return rect;
  // Both boxes hang off the same baseline, so their centers differ by half the
  // difference of (ascent - descent).
  const shift = ((m.actualBoundingBoxAscent - m.actualBoundingBoxDescent)
               - (m.fontBoundingBoxAscent - m.fontBoundingBoxDescent)) / 2;
  const cx = (rect.left + rect.right) / 2, cy = (rect.top + rect.bottom) / 2 - shift;
  return {left: cx - width/2, right: cx + width/2, top: cy - height/2, bottom: cy + height/2};
}

// Positive is a gap, negative is penetration. Clearing on either axis is
// enough, so the axis that separates them furthest is the one that counts.
function gapBetween(a, b) {
  return Math.max(Math.max(a.left, b.left) - Math.min(a.right, b.right),
                  Math.max(a.top, b.top) - Math.min(a.bottom, b.bottom));
}

// Glyph rect, padded by the symbol's stroke reach: getBoundingClientRect is
// the geometry box, and a stroked circle inks half a stroke-width beyond it.
function glyphInkRect(el) {
  const href = el.getAttribute('xlink:href') || el.getAttribute('href') || '';
  const strokeWidth = SYMBOL_STROKE_WIDTHS[href.replace('#', '')] || 0;
  const rect = el.getBoundingClientRect();
  if (!strokeWidth) return rect;
  const ctm = el.getScreenCTM();
  const onScreenScale = ctm ? Math.hypot(ctm.a, ctm.b) : 0;
  const pad = strokeWidth / 2 * onScreenScale;
  return {left: rect.left - pad, right: rect.right + pad,
          top: rect.top - pad, bottom: rect.bottom + pad};
}

async function measure(entry) {
  entry.sep = entry.sep === undefined ? null : entry.sep;
  stage.innerHTML = await (await fetch(entry.file)).text();
  const root = stage.querySelector('svg');
  root.setAttribute('width', '900');
  root.setAttribute('height', '900');

  const points = [];
  for (const g of stage.querySelectorAll('g')) {
    if (g.getAttribute('kr:node') !== 'ChartPoint') continue;
    const rects = [];
    for (const el of g.querySelectorAll('use, text')) {
      const rect = el.tagName === 'text' ? textInkRect(el) : glyphInkRect(el);
      if (rect.right > rect.left && rect.bottom > rect.top) {
        rects.push({rect, row: el.tagName === 'text' ? 'text y=' + el.getAttribute('y') : 'glyph'});
      }
    }
    points.push({slug: g.getAttribute('kr:slug'), rects});
  }

  let best = {gap: Infinity, detail: ''};
  for (let i = 0; i < points.length; i++) for (let j = i + 1; j < points.length; j++) {
    for (const a of points[i].rects) for (const b of points[j].rects) {
      const gap = gapBetween(a.rect, b.rect);
      if (gap < best.gap) {
        best = {gap, detail: `${points[i].slug}/${a.row} vs ${points[j].slug}/${b.row}`};
      }
    }
  }
  stage.innerHTML = '';
  return {ring: entry.ring, sep: entry.sep, file: entry.file, gap: best.gap / PX_PER_UNIT, detail: best.detail};
}

(async () => {
  const manifest = await (await fetch('manifest.json')).json();
  const results = [];
  for (const entry of manifest) {
    results.push(await measure(entry));
    if (results.length % 100 === 0) {
      document.getElementById('out').textContent = `${results.length}/${manifest.length}`;
      await new Promise(r => setTimeout(r, 0));
    }
  }

  const rings = [...new Set(results.map(r => r.ring))];
  const lines = ['Smallest gap between any two clusters, in wheel units.',
                 'Negative means their ink overlaps.', ''];
  const isAdversarial = results.some(r => r.sep === null);
  if (isAdversarial) {
    // Adversarial mode: the renderer chose the separations itself; the gate
    // demands not just "no overlap" but the daylight the calibration promises.
    for (const ring of rings) {
      const rows = results.filter(r => r.ring === ring);
      const worstRow = rows.reduce((m, r) => r.gap < m.gap ? r : m);
      lines.push(`── ${ring}   worst gap ${worstRow.gap.toFixed(3)}   ${worstRow.detail}   (${worstRow.file})`);
      for (const r of rows.filter(r => r.gap < MIN_ACCEPTED_GAP)) {
        lines.push(`   BELOW ${MIN_ACCEPTED_GAP}: ${r.gap.toFixed(3)}  ${r.detail}  ${r.file}`);
      }
    }
    lines.push('', results.every(r => r.gap >= MIN_ACCEPTED_GAP)
      ? `PASS: every pair keeps at least ${MIN_ACCEPTED_GAP} units of daylight.`
      : `FAIL: pairs below the ${MIN_ACCEPTED_GAP}-unit daylight gate.`);
  } else {
    const worst = {};
    for (const r of results) {
      const key = r.ring + '|' + r.sep;
      if (!worst[key] || r.gap < worst[key].gap) worst[key] = r;
    }
    for (const ring of rings) {
      lines.push('── ' + ring);
      const rows = Object.values(worst).filter(r => r.ring === ring).sort((a, b) => a.sep - b.sep);
      for (const r of rows) {
        lines.push(`   ${r.sep.toFixed(2)}°  gap ${r.gap >= 0 ? ' ' : ''}${r.gap.toFixed(3)}   ${r.detail}`);
      }
      // A gap can dip again as clusters rearrange, so a separation only counts
      // when every larger one holds too.
      const safe = c => { for (let i = 0; i < rows.length; i++)
        if (rows.slice(i).every(r => r.gap >= c)) return rows[i].sep.toFixed(2) + '°'; return 'none'; };
      lines.push(`   first safe: touching ${safe(0)} · 0.25 units ${safe(0.25)} · 0.4 units ${safe(0.4)}`, '');
    }
  }
  document.getElementById('out').textContent = lines.join('\\n');
  window.RESULTS = results;
})();
</script></body></html>
"""


DUMP_HTML_TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"><title>glyph ink dump</title>
<style>body{font-family:monospace;padding:12px}#out{white-space:pre;font-size:13px}</style></head>
<body><div id="out">measuring…</div>
<script>
const PLANET_IDS = __PLANET_IDS__;
const SIGN_IDS = __SIGN_IDS__;
const TEXTS = __TEXTS__;                       // every string a cluster row can draw
const TEXT_FONT_SIZE = __TEXT_FONT_SIZE__;     // reference size; ink scales linearly
const PLANET_BOX = 28, SIGN_BOX = 32;   // native symbol boxes (translate(-14 -14) / (-16 -16))
const PAD = 8;                          // units of slack so ink outside the box is not clipped
const PXU = 20;                         // canvas pixels per native unit

// Ink extents by rasterizing and scanning pixels. getBBox and
// getBoundingClientRect both exclude stroke widths on SVG geometry, and half
// these glyphs are stroke-only (Sun, Uranus, Pluto...); for text, layout boxes
// and reference-font advance tables both disagree with what this browser's
// default font actually inks. Pixels are the only honest answer for either.
async function measureInk(content, box, pixelsPerUnit = PXU) {
  const side = Math.round((box + 2 * PAD) * pixelsPerUnit);
  // The wrapper pins the wheel's font stack: a standalone rasterized SVG has
  // no page context to inherit from, and six glyph symbols (As, Mc, Ds, Ic,
  // Av, Vx) are <text> that would otherwise measure in the browser's default
  // serif while production renders them in the pinned stack.
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${side}" height="${side}"` +
              ` font-family="__FONT_FAMILY__"` +
              ` viewBox="${-PAD} ${-PAD} ${box + 2 * PAD} ${box + 2 * PAD}">${content}</svg>`;
  const img = new Image();
  await new Promise((ok, err) => {
    img.onload = ok; img.onerror = err;
    img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
  });
  const canvas = document.createElement('canvas');
  canvas.width = side; canvas.height = side;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(img, 0, 0);
  const data = ctx.getImageData(0, 0, side, side).data;
  let xMin = side, xMax = -1, yMin = side, yMax = -1;
  // Any nonzero alpha counts as ink: the probes that later verify gaps use
  // Chrome's mathematical glyph outlines, which cover every antialiased
  // fringe pixel — a stricter threshold here made the tables read ~1px
  // smaller per side than what the probe (and the eye) sees.
  for (let y = 0; y < side; y++) for (let x = 0; x < side; x++) {
    if (data[(y * side + x) * 4 + 3] > 0) {
      if (x < xMin) xMin = x; if (x > xMax) xMax = x;
      if (y < yMin) yMin = y; if (y > yMax) yMax = y;
    }
  }
  if (xMax < 0) return null;   // nothing drawn
  return {
    xMin: xMin / pixelsPerUnit - PAD, xMax: (xMax + 1) / pixelsPerUnit - PAD,
    yMin: yMin / pixelsPerUnit - PAD, yMax: (yMax + 1) / pixelsPerUnit - PAD,
  };
}

// Widest reach of ink from the anchor point, per axis. Symmetric maxima,
// because a neighbour can sit on either side once the wheel rotates.
function reachFromAnchor(ink, anchorX, anchorY) {
  return {
    half_width: Math.max(anchorX - ink.xMin, ink.xMax - anchorX),
    half_height: Math.max(anchorY - ink.yMin, ink.yMax - anchorY),
  };
}

// Theme colors arrive as var(--...) with no fallback, which a standalone
// rasterized SVG cannot resolve — every paint is rewritten to opaque black,
// which changes nothing about coverage.
function paintedBlack(markup) {
  return markup.replace(/var\\([^)]*\\)/g, '#000');
}

(async () => {
  const templateText = await (await fetch('template.xml')).text();
  const doc = new DOMParser().parseFromString(templateText, 'image/svg+xml');
  const symbols = {};
  for (const s of doc.querySelectorAll('symbol')) symbols[s.getAttribute('id')] = s.innerHTML;

  const out = {planets: {}, signs: {}, texts: {}, text_font_size: TEXT_FONT_SIZE};
  const missing = [];
  const symbolJobs = [[PLANET_IDS, PLANET_BOX, out.planets], [SIGN_IDS, SIGN_BOX, out.signs]];
  for (const [ids, box, sink] of symbolJobs) {
    for (const id of ids) {
      const ink = id in symbols ? await measureInk(paintedBlack(symbols[id]), box) : null;
      if (!ink) { missing.push(id); continue; }
      sink[id] = reachFromAnchor(ink, box / 2, box / 2);
    }
  }

  // Text rows, rendered with the same attributes the wheel renders them with:
  // middle-anchored, weight 500, and the wheel root's pinned font stack —
  // pinning it is what makes these tables valid in every embedding context.
  // Measured at two raster scales and merged by the wider reach: at high
  // resolution hinting effects vanish, but the wheel actually renders these
  // strings at ~17px, where the font rasterizes proportionally wider. One
  // scale alone under-reserved.
  const TEXT_BOX = TEXT_FONT_SIZE * 4;
  const TEXT_SCALES = [PXU, 2];   // 2 px/unit puts the reference size at ~20px
  for (const text of TEXTS) {
    const center = TEXT_BOX / 2;
    const markup = `<text x="${center}" y="${center}" text-anchor="middle"` +
      ` dominant-baseline="middle" font-size="${TEXT_FONT_SIZE}" font-weight="500"` +
      ` fill="#000">${text}</text>`;
    let widest = null;
    for (const scale of TEXT_SCALES) {
      const ink = await measureInk(markup, TEXT_BOX, scale);
      if (!ink) continue;
      const reach = reachFromAnchor(ink, center, center);
      widest = widest === null ? reach : {
        half_width: Math.max(widest.half_width, reach.half_width),
        half_height: Math.max(widest.half_height, reach.half_height),
      };
    }
    if (!widest) { missing.push(JSON.stringify(text)); continue; }
    out.texts[text] = widest;
  }

  const response = await fetch('/ink', {method: 'POST', body: JSON.stringify(out)});
  document.getElementById('out').textContent =
    `measured ${Object.keys(out.planets).length} glyphs + ${Object.keys(out.signs).length} signs` +
    ` + ${Object.keys(out.texts).length} texts` +
    (missing.length ? `\\nMISSING: ${missing.join(', ')}` : '') +
    `\\nserver: ${await response.text()}`;
  window.DONE = true;
})();
</script></body></html>
"""

#: The reference font size text ink is measured at; consumers scale linearly.
TEXT_INK_REFERENCE_FONT_SIZE = 10.0


def _cluster_text_catalog() -> list[str]:
    """Every string a cluster's text rows can draw."""
    degrees_texts = [f"{degrees}º" for degrees in range(30)]
    minutes_texts = [f"{minutes}'" for minutes in range(60)]
    return degrees_texts + minutes_texts + [dm.RETROGRADE_LABEL]

#: Where the dump mode writes its result — a committed data module, so the
#: library never measures at runtime and every platform renders from the same
#: numbers.
INK_MODULE_PATH = Path(__file__).resolve().parent.parent / "kerykeion" / "charts" / "glyph_ink_metrics.py"


class _InkPayloadError(ValueError):
    """The POSTed measurement payload is not what the dump page produces."""


def _validated_ink_payload(data: object) -> dict:
    """The measurement payload, or _InkPayloadError if any part of it is off.

    The measurements travel through an HTTP endpoint any local page can reach,
    and they end up interpolated into generated Python source that executes at
    ``import kerykeion``. Every key must therefore be one this script itself
    asked the page to measure, and every value a plain finite number — nothing
    else gets near the generated module.
    """
    expected_keys = {
        "planets": set(GLYPHS),
        "signs": set(dm._ZODIAC_SIGN_IDS),
        "texts": set(_cluster_text_catalog()),
    }
    if not isinstance(data, dict):
        raise _InkPayloadError("payload is not an object")
    validated: dict = {}
    for section, allowed_names in expected_keys.items():
        entries = data.get(section)
        if not isinstance(entries, dict):
            raise _InkPayloadError(f"section {section!r} is not an object")
        validated[section] = {}
        for name, reach in entries.items():
            if name not in allowed_names:
                raise _InkPayloadError(f"unexpected {section} key {name!r}")
            if not isinstance(reach, dict):
                raise _InkPayloadError(f"{section}[{name!r}] is not an object")
            half_width = reach.get("half_width")
            half_height = reach.get("half_height")
            for value in (half_width, half_height):
                if not isinstance(value, (int, float)) or not 0 < value < 200:
                    raise _InkPayloadError(f"{section}[{name!r}] has a non-numeric or absurd reach")
            validated[section][name] = {"half_width": float(half_width), "half_height": float(half_height)}
    font_size = data.get("text_font_size")
    if not isinstance(font_size, (int, float)) or not 0 < font_size < 1000:
        raise _InkPayloadError("text_font_size is not a sane number")
    validated["text_font_size"] = float(font_size)
    return validated


def _format_ink_module(data: dict) -> str:
    def table(entries: dict, field: str) -> str:
        rows = "".join(f'    "{name}": {entries[name][field]:.3f},\n' for name in sorted(entries))
        return "{\n" + rows + "}"

    planets, signs, texts = data["planets"], data["signs"], data["texts"]
    return f'''"""Measured ink extents of everything a modern planet cluster draws.

Generated by ``scripts/measure_modern_separation.py --mode dump-ink`` — a
browser rasterizes every symbol in ``templates/modern_wheel.xml`` and every
string the text rows can hold, then scans the pixels. Rasterizing is not
pedantry: getBBox and getBoundingClientRect exclude stroke widths and half the
glyphs are stroke-only (Sun, Uranus, Pluto...), while for text both layout
boxes and reference-font advance tables disagree with what the browser's
default font actually inks. Regenerate with ``poe regenerate:glyph-ink``
whenever a symbol's artwork, a text row's styling, or the text catalog changes.

``*_HALF_WIDTH`` / ``*_HALF_HEIGHT`` are the widest reach of actual ink from
the element's anchor toward either side. Symmetric maxima on purpose: glyphs
are not all centered on their anchor (the Sun's ink spans 2.1–21.9 in its
28-unit box), and once the wheel rotates a neighbour can sit on any side.

Units: planet glyphs are native symbol units in a 28-unit box anchored at
(14, 14) (``translate(-14 -14)`` at the use site); zodiac signs a 32-unit box
anchored at (16, 16); texts are measured at font-size
``TEXT_INK_REFERENCE_FONT_SIZE`` with the renderer's attributes
(middle-anchored, weight 500) and scale linearly. Everything — symbols and
texts alike — is rasterized under the wheel's pinned font stack
(``draw_modern.MODERN_TEXT_FONT_FAMILY``), the one production renders in.

Consumed by ``draw_modern._cluster_row_profile`` to size content-aware cluster
separations.

@module kerykeion.charts.glyph_ink_metrics
"""

from __future__ import annotations

#: Font size the text tables were measured at; ink scales linearly with it.
TEXT_INK_REFERENCE_FONT_SIZE: float = {data["text_font_size"]:.1f}

#: Planet-glyph ink reach from the (14, 14) anchor, native units.
GLYPH_INK_HALF_WIDTH: dict[str, float] = {table(planets, "half_width")}

GLYPH_INK_HALF_HEIGHT: dict[str, float] = {table(planets, "half_height")}

#: Zodiac-sign ink reach from the (16, 16) anchor, native units.
SIGN_INK_HALF_WIDTH: dict[str, float] = {table(signs, "half_width")}

SIGN_INK_HALF_HEIGHT: dict[str, float] = {table(signs, "half_height")}

#: Text-row ink reach from the anchored center, per exact string drawn.
TEXT_INK_HALF_WIDTH: dict[str, float] = {table(texts, "half_width")}

TEXT_INK_HALF_HEIGHT: dict[str, float] = {table(texts, "half_height")}
'''


class _HarnessHandler(http.server.SimpleHTTPRequestHandler):
    """Static file server plus the one POST endpoint the dump page reports to."""

    def do_POST(self):  # noqa: N802 (http.server naming)
        if self.path != "/ink":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            data = _validated_ink_payload(json.loads(self.rfile.read(length)))
        except (ValueError, _InkPayloadError) as error:
            # Any local page can POST here while the server runs, and the
            # payload feeds generated Python source: reject everything that is
            # not exactly the dump page's own measurement shape.
            self.send_error(400, f"rejected ink payload: {error}")
            return
        INK_MODULE_PATH.write_text(_format_ink_module(data))
        message = f"wrote {INK_MODULE_PATH}"
        print(message)
        body = message.encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # keep the console readable
        pass


#: Smallest gap the adversarial gate accepts, wheel units. Zero would only
#: prove "not literally touching"; the calibration promises
#: DEFAULT_CLUSTER_CLEARANCE (0.45) of daylight, and probe and ink tables
#: disagree by about a pixel (~0.11 units at the probe's scale), so the gate
#: sits at the promise minus that disagreement, rounded down. The healthy
#: state measures 0.32+ everywhere; anything under this line is a regression.
ADVERSARIAL_MIN_GAP = 0.2


def _symbol_stroke_widths() -> dict[str, float]:
    """Max stroke width of each template symbol, native units.

    The probe pads glyph rects by half of this: getBoundingClientRect returns
    geometry boxes, and the stroke-only glyphs ink half a stroke beyond them.
    """
    svg_namespace = "{http://www.w3.org/2000/svg}"
    widths: dict[str, float] = {}
    for symbol in ElementTree.fromstring(TEMPLATE.read_text()).iter(f"{svg_namespace}symbol"):
        symbol_id = symbol.get("id")
        max_width = 0.0
        for element in symbol.iter():
            raw_width = element.get("stroke-width")
            if raw_width is None:
                style_match = re.search(r"stroke-width\s*:\s*([\d.]+)", element.get("style") or "")
                raw_width = style_match.group(1) if style_match else None
            stroke_paint = element.get("stroke") or ""
            if raw_width is not None and stroke_paint and "none" not in stroke_paint:
                max_width = max(max_width, float(raw_width))
        if symbol_id and max_width:
            widths[symbol_id] = max_width
    return widths


def _probe_page() -> str:
    """PROBE_HTML with its data placeholders filled in."""
    return PROBE_HTML.replace("__STROKE_WIDTHS__", json.dumps(_symbol_stroke_widths())).replace(
        "__MIN_ACCEPTED_GAP__", str(ADVERSARIAL_MIN_GAP)
    )


def build_harness(out_dir: Path) -> int:
    """Write the floor-measurement SVGs, manifest, and probe page into *out_dir*."""
    svg_dir = out_dir / "svg"
    svg_dir.mkdir(parents=True, exist_ok=True)
    orders = cluster_orders()

    manifest = []
    for ring in RINGS:
        for separation in SEPARATIONS:
            for index, order in enumerate(orders):
                name = f"{ring}_{separation:g}_{index}.svg"
                (svg_dir / name).write_text(build_svg(ring, separation, order, BASE_ANGLES[index % len(BASE_ANGLES)]))
                manifest.append({"ring": ring, "sep": separation, "file": f"svg/{name}"})

    (out_dir / "manifest.json").write_text(json.dumps(manifest))
    (out_dir / "index.html").write_text(_probe_page())
    return len(manifest)


def build_adversarial_harness(out_dir: Path) -> int:
    """Write mixed-content clusters placed by the renderer's own policy."""
    svg_dir = out_dir / "svg"
    svg_dir.mkdir(parents=True, exist_ok=True)
    orders = cluster_orders()

    manifest = []
    for ring in RINGS:
        for spacing_name, step in ADVERSARIAL_SPACINGS.items():
            for index, order in enumerate(orders):
                name = f"adv_{ring}_{spacing_name}_{index}.svg"
                svg = build_adversarial_svg(ring, order, BASE_ANGLES[index % len(BASE_ANGLES)], step)
                (svg_dir / name).write_text(svg)
                manifest.append({"ring": ring, "file": f"svg/{name}"})

    (out_dir / "manifest.json").write_text(json.dumps(manifest))
    (out_dir / "index.html").write_text(_probe_page())
    return len(manifest)


def build_dump_harness(out_dir: Path) -> int:
    """Write the ink-dump page (and the template it reads) into *out_dir*."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "template.xml").write_text(TEMPLATE.read_text())
    page = (
        DUMP_HTML_TEMPLATE.replace("__PLANET_IDS__", json.dumps(GLYPHS))
        .replace("__SIGN_IDS__", json.dumps(list(dm._ZODIAC_SIGN_IDS)))
        .replace("__TEXTS__", json.dumps(_cluster_text_catalog()))
        .replace("__TEXT_FONT_SIZE__", str(TEXT_INK_REFERENCE_FONT_SIZE))
        .replace("__FONT_FAMILY__", dm.MODERN_TEXT_FONT_FAMILY)
    )
    (out_dir / "index.html").write_text(page)
    return 1


_BUILDERS = {
    "floor": build_harness,
    "adversarial": build_adversarial_harness,
    "dump-ink": build_dump_harness,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--mode",
        choices=sorted(_BUILDERS),
        default="floor",
        help="floor: how tight can a separation constant go before ink touches; "
        "adversarial: does the renderer's own placement ever overlap, on mixed content; "
        "dump-ink: measure every symbol's ink and write glyph_ink_metrics.py",
    )
    parser.add_argument("--port", type=int, default=8777)
    parser.add_argument("--out", type=Path, help="where to write the harness (default: a temp dir)")
    parser.add_argument("--no-open", action="store_true", help="do not launch a browser")
    args = parser.parse_args()

    out_dir = args.out or Path(tempfile.mkdtemp(prefix="kr-modern-sep-"))
    count = _BUILDERS[args.mode](out_dir)
    print(f"{args.mode}: {count} file(s) in {out_dir}")

    handler = functools.partial(_HarnessHandler, directory=str(out_dir))
    with socketserver.TCPServer(("127.0.0.1", args.port), handler) as server:
        url = f"http://127.0.0.1:{args.port}/index.html"
        print(f"open {url} — results appear once the page finishes")
        print("ctrl-c to stop")
        if not args.no_open:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print()


if __name__ == "__main__":
    main()
