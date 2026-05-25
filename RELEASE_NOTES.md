# Release Notes

## 6.0.0a47 — 2026-05-25

Minor public-API addition.

**Added**

- **`PTOLEMAIC_ASPECTS` re-exported from package root.** The canonical
  Ptolemaic aspect set (conjunction, sextile, square, trine, opposition) is
  now importable directly as `from kerykeion import PTOLEMAIC_ASPECTS`
  without reaching into the private `_predictive_utils` module.

**Backward compatible** — no existing imports break.

## 6.0.0a46 — 2026-05-25

Feature release: orb system overhaul + active midpoints + secondary
progressions improvements + dual-wheel rendering fixes.

**Added**

- **Per-point orb adjustments.** New `kerykeion.aspects.orb_utils` module
  with four combination strategies (`max_explicit` / `min_explicit` / `sum`
  / `none`) and a `point_orb_adjustments` parameter threaded through every
  aspect factory and `ChartDataFactory` method. Natal / synastry / composite
  pick up a default luminary bonus (Sun & Moon +1.5°, matching Astro-Seek).
  Transit / progression / returns stay on a flat tight orb. Negative
  adjustments per point work as expected (only explicitly configured points
  are considered before aggregation).
- **Active midpoints** as a dynamic rendering channel on
  `subject.active_midpoints`. Pass pair names (`["Sun_Moon",
  "Venus_Mars", ...]`) and they materialise as `KerykeionPointModel`
  entries with `point_type='Midpoint'`, get rendered as sensitive points on
  the wheel (new `<symbol id="Midpoint">` in all four SVG templates,
  per-subject scoping, dynamic glyph IDs).
- **`SecondaryProgressionFactory.compute_full()`** — full result model
  including progressed-to-natal aspects; default aspect set switched to
  the Ptolemaic five.
- **`SolarArcFactory.compute_directed_subject()`** — directed subject with
  quality / element / emoji / house recomputed when a directed point
  crosses a sign or house (previously inherited from natal).
- **Astro-Seek-aligned default orbs** across natal, synastry, transit,
  composite. New `PREDICTIVE_ACTIVE_ASPECTS` (3° flat) for transit /
  progression / returns.

**Changed (breaking — alpha channel)**

- `DEFAULT_ACTIVE_POINTS`: **18 → 14**. Removed `Descendant`, `Imum_Coeli`,
  `True_South_Lunar_Node`, `Mean_Lilith`. Opposite points are still
  computed on the subject model but no longer in the default `active_points`
  list — pass them explicitly to opt back in.
- `DEFAULT_ACTIVE_ASPECTS`: **6 → 5** (Ptolemaic only — quintile dropped).
- `DEFAULT_PREDICTIVE_POINTS`: **16 → 14** (South Node + Lilith dropped).
- **Default orbs changed across all chart types.** Aspect counts for any
  pre-existing chart will differ from `6.0.0a45`. Snapshot/baseline tests
  that compare aspect lists must be regenerated.
- **Unknown `point_orb_adjustment_strategy` now raises `ValueError`**
  (previously silently returned `0.0`, masking typos).
- **`RelationshipScoreFactory`** now passes `DISCEPOLO_SCORE_ACTIVE_ASPECTS`
  explicitly — the Discepolo affinity score is now a stable methodology
  independent of chart-display orb configuration. Baselines updated
  (Lennon/Ono: 8, Dario/Franca: 9).

**Fixed**

- Dual-wheel aspect grid in `table` mode dropped points active only on the
  second subject (e.g. a fixed star or active midpoint on the outer wheel),
  and aspects targeting them landed in nonexistent cells. `ChartDrawer`
  now sizes and draws the NxN grid against the union of both subjects.
- Secondary progression self-conjunction filter removed (natal ↔
  progressed-same-point conjunctions are meaningful and now appear).
- Solar arc directed subject recomputes `active_midpoints` (previously
  stale on rotation).
- Midpoint glyph visual redesign + `UnboundLocalError` in the chart drawer
  when a midpoint settings row was looked up by a renamed slug.
- `create_chart_data` + transit factory now honor chart-type-specific orb
  defaults (some entry points fell back to the natal-shaped table for
  predictive charts).

**Docs**

12 missing v6 factory pages added (astro-cartography, eclipse, fixed-star
discovery, heliacal, midpoint, occultation, planetary nodes, planetary
phenomena, primary directions, relocated chart, secondary progressions,
solar arc) plus comprehensive FAQ / glossary / examples updates.

**Migration notes**

- Regenerate any locally-pinned aspect baselines.
- If your code passes `active_points` and relied on opposite points being
  in the default, opt them back in explicitly.
- Validate any string passed as `point_orb_adjustment_strategy` against
  the four registered names.

10034 tests pass.

## 6.0.0a45 — 2026-05-18

Bugfix release for dual-wheel return charts + v6 flag propagation.

**Fixed**

- `IndexError` in dual solar/lunar return wheel rendering when the return
  subject collected fewer points than `active_points`. `ChartDrawer` now
  keeps a per-second-subject settings list aligned to the actual collected
  points; `_calculate_secondary_indicator_adjustments` / `_draw_secondary_points`
  add a defensive `min(len, len)` bound as a safety net.
- `PlanetaryReturnFactory` now propagates the six v6 calc kwargs to the
  return subject: `active_fixed_stars`, `calculate_dignities`,
  `calculate_nakshatra`, `calculate_gauquelin`, `calculate_nutation`,
  `calculate_local_space`. Previously the return chart silently dropped
  these enrichments even when the natal subject was built with them.
- `AstrologicalSubjectFactory.from_iso_utc_time` now accepts the same six
  v6 kwargs and forwards them to `from_birth_data`.

**Backward compatible**

Defaults preserve pre-`a45` behaviour: a caller that doesn't opt into the
v6 flags continues to get a bare return chart.

## 6.0.0a44 — 2026-05-18

Regression fix + visual unification for fixed stars.

**Fixed (regression)**

Catalog fixed stars (any name outside the legacy 23 hardcoded) were
silently excluded from aspect calculation in `6.0.0a43`. The extended
`celestial_points` list was not propagated from `single_chart_aspects` /
`dual_chart_aspects` down to `get_active_points_list`. Same bug applied
to declination aspects. Fixed across 6 call sites in
`aspects_factory.py`. Regression test added.

**Visual — unified fixed-star glyph**

All fixed stars now render with a single generic
`<symbol id="FixedStar">` (5-point star, colored via the
`--kerykeion-chart-color-fixed-star-default` CSS variable). The 23
per-star dedicated symbols and CSS variables (Regulus, Spica, Aldebaran,
…) have been removed across templates, themes, and settings. The
fixed-star architectural cleanup started in `6.0.0a43` is now complete:
no asymmetry between "hardcoded" and "catalog" stars at any layer.

**Breaking (visual / CSS)**

- Custom themes overriding `--kerykeion-chart-color-regulus` etc. must
  migrate to `--kerykeion-chart-color-fixed-star-default`.
- SVG references `xlink:href="#Regulus"` (and the 22 others) replaced
  by `xlink:href="#FixedStar"`. `kr:slug="Regulus"` preserved on the
  wrapping `<g>`.

All chart SVG baselines regenerated. 9100 tests pass.

## 6.0.0a43 — 2026-05-18

Fixed-star subsystem refactor — single unified channel via the libephemeris
catalog (single source of truth, 116 stars today, scales to thousands).

**Breaking changes** (alpha — accepted):

- `subject.regulus` / `subject.spica` / the other 21 typed star fields are
  removed. Use `subject.find_fixed_star("Regulus")` or iterate
  `subject.fixed_stars` (`list[KerykeionPointModel]`).
- `active_points=["Regulus", ...]` no longer triggers star calculation.
  Pass star names to the new keyword argument
  `active_fixed_stars=["Regulus", ...]` on the factory constructors.
- `FixedStarDiscoveryFactory.find_prominent_stars()` no longer accepts
  the `catalog_path` keyword (the catalog is now read exclusively from
  libephemeris, regardless of the active backend).

Highlights:

- Stars now participate in aspect calculations natively without needing
  to be listed in `active_points`.
- New `kerykeion.fixed_stars.FixedStarCatalog` exposes the libephemeris
  catalog (`list_all`, `find`, `known_slugs`).
- Chart wheel SVG renders catalog stars via a new generic
  `<symbol id="FixedStar">` glyph (colored via the
  `--kerykeion-chart-color-fixed-star-default` CSS variable). The 23
  traditional stars keep their dedicated glyphs.
- swisseph backend: `sefstars.txt` is required for fixed-star calculation
  and is not bundled (licensed by Astrodienst). Missing-file scenarios
  now emit a single actionable WARNING. See
  [site/docs/swisseph_configuration.md](site/docs/swisseph_configuration.md#fixed-stars-catalog-sefstarstxt).

## 6.0.0a42 — 2026-05-15

Updated `libephemeris` to 2.0.0.

Highlights:

- Upstream library simplified its public API by removing legacy prefixed
  aliases. The canonical bare-name API used by kerykeion (`calc_ut`,
  `houses`, `SUN`, `FLG_SPEED`, ...) is unchanged.
- Adds a new `libephemeris.contrib` submodule with extended astrology
  helpers (zodiac, nakshatra, aspect constants and functions).

No API changes. Backward-compatible.

## 6.0.0a41 — 2026-05-14

Updated `libephemeris` to 1.6.0 with critical LEB fast-path bug fixes.

Highlights:

- `lun_occult_when_loc()` no longer crashes in LEB mode (was
  `NameError: ts`).
- Heliacal calculations no longer fail after `close()` (was
  `TypeError` on closed mmap).
- `set_leb_file()` and `clear_caches()` now properly clean up stale
  LEB reader state.

No API changes. Backward-compatible.

## 6.0.0a40 — 2026-05-10

Clean ephemeris packaging and new Swiss Ephemeris setup utility.

Highlights:

- Swiss Ephemeris data files are no longer shipped in the wheel. The
  default backend (`libephemeris`) works out of the box without them.
- New `python -m kerykeion.swisseph_setup` command for users who want
  the optional Swiss Ephemeris backend: downloads data files with
  license confirmation (AGPL-3.0, Astrodienst AG).
- `EPHE_DATA_PATH` is now backend-aware (empty string default).
- PyPI license classifier corrected to AGPL-3.0.
- New Swiss Ephemeris Configuration guide in docs.

No API changes. Backward-compatible.

## 6.0.0a38 — 2026-05-08

Kerykeion 6.0.0a38 reduces startup memory by removing the import-time
LEB reader opening.

Highlights:

- `ephemeris_backend.py` no longer calls `get_leb_reader()` at import time.
  Previously this opened four companion mmap files just to log the format
  string (LEB1/LEB2), causing unnecessary memory allocation before any
  calculation.
- Updated `libephemeris` dependency to 1.3.0, which removes global
  `madvise(MADV_WILLNEED)` and adds selective mmap preloading via `warm()`.

No API changes. Backward-compatible.
