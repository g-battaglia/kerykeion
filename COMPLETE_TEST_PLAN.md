# Modern Chart Style — Complete Test Plan

## Context

Kerykeion v5.11.0 introduces `style="modern"`, a concentric-ring chart rendering mode alternative to the traditional `style="classic"`. The modern renderer lives in `kerykeion/charts/draw_modern.py` (~1570 lines) and is dispatched from `ChartDrawer` methods in `chart_drawer.py`.

### Current Public API

The following `ChartDrawer` methods accept `style="modern"`:

| Method | Modern-specific params | Output |
|--------|----------------------|--------|
| `generate_svg_string(style=, show_zodiac_background_ring=)` | `show_zodiac_background_ring: bool = True` | SVG string |
| `save_svg(style=, show_zodiac_background_ring=)` | Same + filename suffix `" - Modern"` | File on disk |
| `generate_wheel_only_svg_string(style=, show_zodiac_background_ring=)` | Same | SVG string |
| `save_wheel_only_svg_file(style=, show_zodiac_background_ring=)` | Same + filename suffix `" - Modern Wheel Only"` | File on disk |

**Removed params** (commit `240c904`): `show_houses_1` and `show_cusp_ring_1` were removed from the entire API. The only modern-only toggle is `show_zodiac_background_ring`.

**Dispatch logic** (`_generate_modern_content`):
- `Natal`, `Composite`, `SingleReturnChart` → `draw_modern_horoscope()` (single ring)
- `Synastry`, `Transit`, `DualReturnChart` → `draw_modern_dual_horoscope()` (dual ring)

**No runtime validation**: passing an invalid `style` value (e.g., `style="foo"`) silently falls through to the classic renderer.

### Chart Types Supported

| Chart Type | Factory Method | Modern Dispatch |
|------------|---------------|-----------------|
| Natal | `create_natal_chart_data(subject)` | Single ring |
| Synastry | `create_synastry_chart_data(s1, s2)` | Dual ring |
| Transit | `create_transit_chart_data(s1, s2)` | Dual ring |
| Composite | `create_composite_chart_data(model)` | Single ring |
| SingleReturnChart (Solar/Lunar) | `create_single_wheel_return_chart_data(return_subj)` | Single ring |
| DualReturnChart (Solar/Lunar) | `create_return_chart_data(natal, return_subj)` | Dual ring |

### Rendering Differences: Classic vs Modern

| Aspect | Classic | Modern |
|--------|---------|--------|
| Coordinate space | ~800×800+ with translate offsets | 100×100 viewBox centered at (50,50) |
| Wheel structure | Zodiac ring + planet positions with lines | 5 concentric rings (6 for dual) |
| Planet display | Glyph + degree text, separate zone | Data cluster: glyph > degrees > sign > minutes > RX (stacked radially) |
| Zodiac signs | Colored wedge ring always shown | Optional background ring (Ring 0); or inline in cusp ring |
| Aspect rendering | Lines with optional icons in wheel area | Dedicated inner core circle (Ring 5) with midpoint glyphs |
| Template | `chart.xml` (classic groups filled) | `chart.xml` (classic groups blanked, modern content in `$background_circle`) |
| Wheel-only template | `wheel_only.xml` | `modern_wheel.xml` |

### SVG Markers

- Single chart: `kr:node="ModernHoroscope"`
- Dual chart: `kr:node="ModernDualHoroscope"`
- Retrograde: `kr:retrograde="true"` + "RX" text
- Classic groups (`makeZodiac`, `makePlanets`, `makeHouses`, `makeAspects`, etc.) are blanked to empty strings

---

## Current Test Coverage (22 methods, 27 instances)

All modern tests live in `TestModernChartStyle` in `tests/core/test_chart_drawer.py` (lines 1948–2128).

### By category

| Category | Methods | Instances | Notes |
|----------|:-------:|:---------:|-------|
| SVG baseline (line-by-line golden-file) | 17 | 17 | Strong regression coverage |
| Smoke test (`isinstance + "<svg>"`) | 3 | 8 | Weak — only proves no crash |
| Behavioral (file exists + `"<svg>"`) | 2 | 2 | Weak — no content verification |
| **Structural/Behavioral assertion** | **0** | **0** | **Critical gap** |

### By chart type

| Chart Type | Baseline Tests | Themes Covered | Languages | Wheel-Only | Notes |
|------------|:-:|:-:|:-:|:-:|------|
| Natal | 6 | All 6 | None | 2 (default, dark) | Missing: sidereal, languages |
| Synastry | 2 | default, dark | None | 1 | Missing: 4 themes, languages |
| Transit | 2 | default, dark | None | 1 | Missing: 4 themes, languages |
| Composite | 1 | default only | None | 0 | Missing: themes, wheel-only, languages |
| DualReturn Solar | 1 | default only | — | 0 | Missing: themes |
| DualReturn Lunar | **0** | — | — | — | **Completely absent** |
| SingleReturn Solar | 1 | default only | — | 0 | Missing: themes, wheel-only |
| SingleReturn Lunar | **0** | — | — | — | **Completely absent** |

### Identified gaps (what the tests do NOT verify)

1. **No test verifies modern ≠ classic** — a bug routing modern to classic would pass all tests (after baseline regen).
2. **`show_zodiac_background_ring` is only smoke-tested** — no test asserts it actually changes the SVG output.
3. **No structural SVG assertions** — no test checks for `kr:node="ModernHoroscope"`, blanked classic groups, or any modern-specific element.
4. **No error/edge-case tests** — invalid style fallback, classic ignoring modern kwargs, crowded active points.
5. **No filename convention tests** — default `" - Modern"` / `" - Modern Wheel Only"` suffix untested.
6. **Lunar return charts entirely missing** — both SingleReturn and DualReturn with `return_type="Lunar"`.
7. **Theme coverage shallow beyond Natal** — Synastry/Transit only test dark; Composite and Returns test no theme variants.
8. **No language tests** — classic tests 9 languages; modern tests zero.
9. **No sidereal tests** — classic tests 20 sidereal modes; modern tests zero.

---

## Plan

### Section A — Baseline Tests (golden-file comparison)

These tests generate SVG with `style="modern"` and compare line-by-line against a saved baseline file. They require generating new SVG baseline files in `tests/data/svg/`.

#### A1. Synastry — 4 new tests

| Test | Theme/Variant | Baseline filename |
|------|--------------|-------------------|
| `test_modern_synastry_light_theme` | light | `John Lennon - Light Theme Synastry - Synastry Chart - Modern.svg` |
| `test_modern_synastry_bw_theme` | black-and-white | `John Lennon - BW Theme Synastry - Synastry Chart - Modern.svg` |
| `test_modern_synastry_strawberry_theme` | strawberry | `John Lennon - Strawberry Theme Synastry - Synastry Chart - Modern.svg` |
| `test_modern_synastry_french` | default, language=FR | `Jeanne Moreau Synastry - Synastry Chart - Modern.svg` |

#### A2. Transit — 4 new tests

| Test | Theme/Variant | Baseline filename |
|------|--------------|-------------------|
| `test_modern_transit_light_theme` | light | `John Lennon - Light Theme Transit - Transit Chart - Modern.svg` |
| `test_modern_transit_bw_theme` | black-and-white | `John Lennon - BW Theme Transit - Transit Chart - Modern.svg` |
| `test_modern_transit_strawberry_theme` | strawberry | `John Lennon - Strawberry Theme Transit - Transit Chart - Modern.svg` |
| `test_modern_transit_spanish` | default, language=ES | `Antonio Banderas Transit - Transit Chart - Modern.svg` |

#### A3. Composite — 5 new tests

| Test | Theme/Variant | Baseline filename |
|------|--------------|-------------------|
| `test_modern_composite_dark_theme` | dark | `Angelina Jolie and Brad Pitt Composite Chart - Dark Theme - Composite Chart - Modern.svg` |
| `test_modern_composite_bw_theme` | black-and-white | `Angelina Jolie and Brad Pitt Composite Chart - BW Theme - Composite Chart - Modern.svg` |
| `test_modern_composite_strawberry_theme` | strawberry | `Angelina Jolie and Brad Pitt Composite Chart - Strawberry Theme - Composite Chart - Modern.svg` |
| `test_modern_composite_wheel_only` | default, wheel_only | `Angelina Jolie and Brad Pitt Composite Chart - Composite Chart - Modern Wheel Only.svg` |
| `test_modern_composite_italian` | default, language=IT | `Sophia Loren Composite - Composite Chart - Modern.svg` |

#### A4. DualReturn Solar — 2 new tests

| Test | Theme/Variant | Baseline filename |
|------|--------------|-------------------|
| `test_modern_dual_return_solar_dark` | dark | `John Lennon - Dark Theme - DualReturnChart Chart - Solar Return - Modern.svg` |
| `test_modern_dual_return_solar_bw` | black-and-white | `John Lennon - BW Theme - DualReturnChart Chart - Solar Return - Modern.svg` |

#### A5. DualReturn Lunar — 3 new tests (chart type currently absent)

| Test | Theme/Variant | Baseline filename |
|------|--------------|-------------------|
| `test_modern_dual_return_lunar` | default | `John Lennon - DualReturnChart Chart - Lunar Return - Modern.svg` |
| `test_modern_dual_return_lunar_dark` | dark | `John Lennon - Dark Theme - DualReturnChart Chart - Lunar Return - Modern.svg` |
| `test_modern_dual_return_lunar_bw` | black-and-white | `John Lennon - BW Theme - DualReturnChart Chart - Lunar Return - Modern.svg` |

Uses: `_make_return_factory(john)` → `factory.next_return_from_iso_formatted_time(RETURN_ISO, return_type="Lunar")` → `ChartDataFactory.create_return_chart_data(john, lr)`.

#### A6. SingleReturn Solar — 2 new tests

| Test | Theme/Variant | Baseline filename |
|------|--------------|-------------------|
| `test_modern_single_return_solar_dark` | dark | `John Lennon Solar Return - Dark Theme - SingleReturnChart Chart - Modern.svg` |
| `test_modern_single_return_solar_wheel_only` | default, wheel_only | `John Lennon Solar Return - SingleReturnChart Chart - Modern Wheel Only.svg` |

#### A7. SingleReturn Lunar — 3 new tests (chart type currently absent)

| Test | Theme/Variant | Baseline filename |
|------|--------------|-------------------|
| `test_modern_single_return_lunar` | default | `John Lennon Lunar Return - SingleReturnChart Chart - Modern.svg` |
| `test_modern_single_return_lunar_dark` | dark | `John Lennon Lunar Return - Dark Theme - SingleReturnChart Chart - Modern.svg` |
| `test_modern_single_return_lunar_wheel_only` | default, wheel_only | `John Lennon Lunar Return - SingleReturnChart Chart - Modern Wheel Only.svg` |

#### A8. Natal — 2 new tests (sidereal + language)

| Test | Variant | Baseline filename |
|------|---------|-------------------|
| `test_modern_natal_sidereal_lahiri` | sidereal=LAHIRI | `John Lennon Sidereal LAHIRI - Natal Chart - Modern.svg` |
| `test_modern_natal_french` | language=FR | `Jeanne Moreau - Natal Chart - Modern.svg` |

**Section A total: 25 new baseline tests → 25 new SVG files to generate**

---

### Section B — Behavioral & Structural Tests (no baselines needed)

These tests verify correctness through assertions on SVG content, equality/inequality checks, and file system validation — no golden-file baselines required.

#### B1. Modern ≠ Classic (2 tests)

```text
test_modern_differs_from_classic_natal
    Generate same natal chart with style="classic" and style="modern".
    Assert the two SVG strings are different.

test_modern_differs_from_classic_synastry
    Generate same synastry chart with style="classic" and style="modern".
    Assert the two SVG strings are different (exercises dual-chart dispatch).
```

#### B2. `show_zodiac_background_ring` changes output (2 tests)

```text
test_zodiac_bg_ring_changes_output_natal
    Generate natal modern SVG with show_zodiac_background_ring=True and =False.
    Assert the two outputs differ.

test_zodiac_bg_ring_changes_output_synastry
    Same test on synastry chart (dual-ring path).
```

#### B3. SVG contains modern-specific markers (3 tests)

```text
test_modern_natal_contains_horoscope_node
    Assert 'kr:node="ModernHoroscope"' is present in modern natal SVG.

test_modern_synastry_contains_dual_node
    Assert 'kr:node="ModernDualHoroscope"' is present in modern synastry SVG.

test_modern_blanks_classic_groups
    Assert modern SVG does NOT contain classic group content (e.g., zodiac ring paths),
    while classic SVG DOES contain them.
```

#### B4. Edge cases & robustness (4 tests)

```text
test_modern_kwargs_ignored_by_classic
    Generate classic SVG with and without show_zodiac_background_ring=False.
    Assert outputs are identical (kwarg is silently ignored).

test_modern_all_active_points_does_not_crash
    Create natal chart with ALL_ACTIVE_POINTS (62 points).
    Generate modern SVG, assert isinstance(str) and len > 100.

test_save_svg_default_filename_modern_suffix
    Call save_svg(style="modern") without explicit filename.
    Assert the generated file has " - Modern" in its name.

test_save_wheel_only_default_filename_modern_suffix
    Call save_wheel_only_svg_file(style="modern") without explicit filename.
    Assert the generated file has " - Modern Wheel Only" in its name.
```

**Section B total: 11 behavioral/structural tests, 0 SVG baselines needed**

---

## Summary

| Section | Tests | New SVG Baselines | Priority |
|---------|:-----:|:-----------------:|----------|
| A1. Synastry (themes + language) | 4 | 4 | High |
| A2. Transit (themes + language) | 4 | 4 | High |
| A3. Composite (themes + wheel-only + language) | 5 | 5 | High |
| A4. DualReturn Solar (themes) | 2 | 2 | High |
| A5. DualReturn Lunar (from zero) | 3 | 3 | High |
| A6. SingleReturn Solar (theme + wheel-only) | 2 | 2 | High |
| A7. SingleReturn Lunar (from zero) | 3 | 3 | High |
| A8. Natal (sidereal + language) | 2 | 2 | Medium |
| B1. Modern ≠ Classic | 2 | 0 | High |
| B2. show_zodiac_bg_ring changes output | 2 | 0 | High |
| B3. Modern-specific SVG markers | 3 | 0 | Medium |
| B4. Edge cases (kwargs, active points, filenames) | 4 | 0 | Medium |
| **Total** | **36** | **25** | |

### After implementation: coverage per chart type

| Chart Type | Before | After |
|------------|:------:|:-----:|
| Natal | 6 baseline + 2 smoke | 8 baseline + 2 smoke + 5 behavioral |
| Synastry | 2 baseline + 1 smoke | 6 baseline + 1 smoke + 4 behavioral |
| Transit | 2 baseline | 6 baseline + 2 behavioral |
| Composite | 1 baseline | 6 baseline (incl. wheel-only + language) |
| DualReturn Solar | 1 baseline | 3 baseline |
| DualReturn Lunar | **0** | **3 baseline** |
| SingleReturn Solar | 1 baseline | 3 baseline (incl. wheel-only) |
| SingleReturn Lunar | **0** | **3 baseline** (incl. wheel-only) |

---

## Execution Steps

1. Add the 36 test methods to `TestModernChartStyle` in `tests/core/test_chart_drawer.py`
2. Write a script to generate the 25 new SVG baselines in `tests/data/svg/`
3. Run the generation script
4. Update Section 14 of `scripts/regenerate_test_charts.py` with the new charts
5. Run `pytest tests/core/test_chart_drawer.py -v` → verify 0 failures
6. Run `pytest tests/ -q` → verify no pre-existing tests are broken
7. Stage and commit

### Implementation Notes

- **Lunar return pattern**: reuse `_make_return_factory(john)` helper (line 135) with `factory.next_return_from_iso_formatted_time("2025-01-09T18:30:00+01:00", return_type="Lunar")`, same as `TestReturnCharts._lunar_return()` (line 1124).
- **Language subjects**: reuse birth data patterns from `TestNatalChartLanguages` (line 724+). E.g., Jeanne Moreau for FR, Antonio Banderas for ES, Sophia Loren for IT.
- **ALL_ACTIVE_POINTS**: import from `kerykeion.settings.active_points` (verify the import path is already present in the test file).
- **Baseline filenames**: follow the existing naming convention — `"{subject.name} - {Chart Type} Chart - Modern.svg"`. For wheel-only: `"... - Modern Wheel Only.svg"`. The exact filenames will depend on the subject names used; the table above lists expected patterns.

---

## Relevant Files

| File | Role |
|------|------|
| `tests/core/test_chart_drawer.py` | Test file — `TestModernChartStyle` class at line 1948 |
| `tests/data/svg/` | SVG baseline directory (currently 17 modern files) |
| `kerykeion/charts/chart_drawer.py` | `ChartDrawer` class — public API entry points |
| `kerykeion/charts/draw_modern.py` | Modern renderer — `draw_modern_horoscope()`, `draw_modern_dual_horoscope()` |
| `kerykeion/chart_data_factory.py` | `ChartDataFactory` — chart data creation methods |
| `kerykeion/planetary_return_factory.py` | `PlanetaryReturnFactory` — solar/lunar return computation |
| `scripts/regenerate_test_charts.py` | Baseline regeneration script (Section 14 = modern charts) |
