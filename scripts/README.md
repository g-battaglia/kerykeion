# scripts/

Developer tooling. Nothing here ships in the package — these build the fixtures
the tests compare against, guard the parts of the codebase a type checker cannot
see, and produce the artefacts the documentation embeds.

Almost every script has a `poe` task. **Prefer the task**: several of them set
environment the script depends on (the extended ephemeris tier, most often), and
running the file directly quietly produces different output.

---

## Regenerating golden data

The test suite compares against committed fixtures. When an intended change moves
them, regenerate — and read the diff, because that diff is the change.

| Script | `poe` task | What it rewrites |
| :-- | :-- | :-- |
| `regenerate_all.py` | `regenerate:all` | Everything below, in dependency order. |
| `regenerate_test_charts.py` | `regenerate:svg:base` | The core SVG baselines in `tests/data/svg/`. The subject's name becomes the filename, so a variant is named by naming its subject. |
| `regenerate_test_charts_extended.py` | `regenerate:svg:extended` | The rest of `tests/data/svg/`: themes, 2 700 years of dates, and geographic sweeps. |
| `generate_modern_baselines.py` | `regenerate:svg:modern` | The modern-style baselines. Filenames are explicit here, not derived. |
| `regenerate_stale_baselines.py` | — | Only the baselines `test_chart_parametrized.py` found stale. A repair tool, not part of the regular sweep. |
| `regenerate_expected_subjects.py` | `regenerate:positions` | `tests/data/expected_astrological_subjects.py` — the positions themselves. |
| `regenerate_expected_aspects.py` | `regenerate:aspects:natal` | `tests/data/expected_natal_aspects.py`. |
| `regenerate_synastry_aspects.py` | `regenerate:aspects:synastry` | `tests/data/expected_synastry_aspects.py`. |
| `regenerate_report_snapshots.py` | `regenerate:reports:snapshots` | The text-report golden files in `tests/fixtures/`. |
| `regenerate_test_output.py` | `regenerate:reports:output` | The report-snapshot output fixtures. |
| `regenerate_docs_charts.py` | — | `docs/charts/`, which the README embeds by raw URL. Run it after anything that changes how a chart looks, or the README shows a chart the library no longer draws. |
| `generate_v6_test_gallery.py` | — | `tests/data/v6_gallery/` and its index page. |

`regenerate:svg`, `regenerate:reports`, `regenerate:positions` and
`regenerate:aspects` run the groups above and set
`LIBEPHEMERIS_PRECISION=extended` — without it, dates before roughly 1600 fall
outside the loaded ephemeris and their fixtures are silently left stale.

## Looking at the output

| Script | `poe` task | What it produces |
| :-- | :-- | :-- |
| `generate_svg_validation_gallery.py` | `gallery`, `gallery:index` | The visual validation sweep (see below). |
| `generate_glyph_gallery.py` | — | A self-contained poster of every chart glyph, plus its Markdown page. |
| `report_modern_displacement.py` | — | How far the modern decluttering moves each planet from its true position. Reads the SVG back through `charts.svg_metadata`, so it measures what was drawn rather than what was intended. |
| `benchmark.py` | `benchmark` | Timings for subject creation, aspects and SVG rendering. |

## Gates

Run in CI-equivalent form by `poe check` and `poe quality`. Each exists because
something once passed the type checker and the test suite and was still wrong.

| Script | `poe` task | What it refuses to let through |
| :-- | :-- | :-- |
| `check_documentation_coverage.py` | `docs:check` | An export in `kerykeion.__all__` that no user-facing page documents. |
| `test_markdown_snippets.py` | `docs:snippets` | A ` ```python ` block in any Markdown file that does not run. Offline: a snippet needing the network has to say `online=False`. |
| `check_import_graph.py` | `imports`, `imports:fresh` | Module paths, patch targets and logger names that drifted from the package layout — the things a rename breaks silently. `imports:fresh` additionally imports every module in a cold interpreter, which is what catches leaf-first cycles. |
| `quality_check.py` | `quality` | The aggregate gate. |
| `build_smoke_check.py` | `build:smoke` | A wheel that imports but cannot render, because a template or theme was left out of the package data. |

## Generated source

These write files that are committed and then read as code. The marker comments
in the targets say so; edit the script, never the output.

| Script | `poe` task | Target |
| :-- | :-- | :-- |
| `build_chart_glyphs.py` | — | The `<symbol>` definitions between the `GLYPHS:BEGIN`/`GLYPHS:END` markers in all four SVG templates. |
| `regenerate_glyph_widths.py` | `regenerate:glyph-widths` | `charts/glyph_metrics.py` — the per-character width tables the info panel measures rows against. Reads the reference fonts, so macOS only. |
| `measure_modern_separation.py` | `regenerate:glyph-ink` | `charts/glyph_ink_metrics.py` — the ink extents of every modern glyph, measured in a real browser. Interactive: it opens a page. The modern wheel's spacing is derived from these numbers, so changing a glyph without re-measuring invalidates the separation model. |
| `extract_swisseph_full_docs.py` | — | One-off extraction of upstream ephemeris documentation. |

---

## The validation gallery

`poe gallery` writes several hundred charts into `svg_validation_gallery/`
(gitignored) with a page that opens any of them full screen and steps through
the whole sweep with a slider, the arrow keys or the screen edges. `i` shows the
technical details of the chart on screen — its size, viewBox, node and element
counts, the `kr:` attributes it carries, its info-panel lines, and whether it
parses as XML — all **read back out of the rendered file**, never restated from
the arguments, so the panel cannot agree with a request the renderer ignored.

It is organised by axis. Each section holds one dimension at every value it can
take while the rest stay at a default:

- **themes** (all six, plus the un-themed output), **languages** (all ten, single
  and dual wheel), **chart types** (natal through both composites, all four
  returns, progressions and solar arc), **output templates**
- **house systems** — all twenty-three, then all twenty-three again inside the
  polar circle where most are undefined and another stands in
- **perspectives** (all eleven), **sidereal modes** (all forty-eight),
  **tropical against sidereal** side by side
- **the opt-in marks**, one at a time against an unmarked reference, then all of
  them together on subjects that between them carry every referent

And the sections that are deliberately not defaults, because that is where
layout gives way:

- **latitudes** from 89°N to 89°S and both sides of the dateline; **dates** from
  500 BCE to 2400; **times of day** every three hours, where diurnality flips
- **names and titles** in Cyrillic, Greek, CJK, Arabic, Hebrew, Devanagari, with
  emoji, with characters that are markup, and longer than the block they sit in
- **aspect webs** from none at all to every aspect at double orb; **orb rules**;
  **distribution weighting**
- **calendar edges** — a leap day, both sides of midnight, daylight-saving jumps,
  UTC+14 to UTC−11
- **minimal charts**, down to a single point; **the heaviest chart** the library
  can draw, in every theme and every language
- **overrides** (partial palettes, language packs) and **post-processing**
  (variables inlined, minified)

A render that raises becomes a red card rather than stopping the run: a sweep
that omits what broke is worse than none. The sweep writes `cards.json`, and
`poe gallery:index` rebuilds the page from that alone — reworking the viewer
costs a second instead of a full re-render.
