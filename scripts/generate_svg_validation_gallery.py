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
import sys
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
)
from kerykeion.schemas.literals import (
    HousesSystemIdentifier,
    KerykeionChartLanguage,
    KerykeionChartTheme,
    PerspectiveType,
    SiderealMode,
)
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


@dataclass
class Section:
    name: str
    blurb: str
    cards: list[Card] = field(default_factory=list)


_PAGE = """<!doctype html>
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
                       border-radius: 6px; box-shadow: 0 12px 40px rgba(0,0,0,.55); }}
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
     <kbd>Home</kbd>/<kbd>End</kbd> to jump, <kbd>Esc</kbd> to close</p>
</header>

<nav>{nav}</nav>
{body}

<div class="viewer" id="viewer" role="dialog" aria-modal="true" aria-label="Chart viewer">
  <div class="viewer-bar">
    <div class="who"><b id="v-title"></b><span id="v-detail"></span></div>
    <div class="where" id="v-section"></div>
    <button type="button" id="v-close" title="Close (Esc)">Close ✕</button>
  </div>
  <div class="viewer-stage">
    <button type="button" class="edge prev" id="v-edge-prev" aria-label="Previous"></button>
    <img id="v-img" alt="">
    <button type="button" class="edge next" id="v-edge-next" aria-label="Next"></button>
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
  elDetail.textContent = c.d;
  elSection.textContent = c.s;
  elIdx.textContent = (at + 1) + ' / ' + CHARTS.length;
  range.value = String(at);
  btnPrev.disabled = at === 0;
  btnNext.disabled = at === CHARTS.length - 1;
}}

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

viewer.addEventListener('click', e => {{ if (e.target === viewer) close(); }});

document.addEventListener('keydown', e => {{
  if (!viewer.classList.contains('open')) return;
  if (e.key === 'Escape') {{ close(); }}
  else if (e.key === 'ArrowRight' || e.key === 'PageDown') {{ e.preventDefault(); show(at + 1); }}
  else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{ e.preventDefault(); show(at - 1); }}
  else if (e.key === 'Home') {{ e.preventDefault(); show(0); }}
  else if (e.key === 'End') {{ e.preventDefault(); show(CHARTS.length - 1); }}
}});
</script>
</body></html>
"""


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

    (out / "index.html").write_text(
        _PAGE.format(
            nav=nav,
            body="".join(body),
            ok=data["ok"],
            failed=data["failed"],
            n_sections=len(data["sections"]),
            charts=json.dumps(flat, ensure_ascii=False),
        ),
        encoding="utf-8",
    )


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
    current.cards.append(Card(filename, title, detail, aspect))
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
