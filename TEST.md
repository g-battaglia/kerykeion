# Test Suite Documentation

## Overview

Kerykeion's test suite lives in `tests/core/` with **102 test files** and parallel execution via `pytest-xdist` (`-n auto`).

Tests are run through **4 hierarchical tiers** (`core < base < medium < extended`). Without an explicit `--tier` option, the tier is auto-detected by probing the loaded ephemeris kernel, so a plain `pytest` run is green on any kernel; test cases for subjects outside the active tier are skipped (with a reason), not failed.

**The task name asks for a tier; the installed kernel decides which one you get.**
`poe test:extended` and `poe test:all` are both plain `pytest tests/ -m 'not online'`
and set no `LIBEPHEMERIS_PRECISION`, so on a default install the auto-detected tier
is `medium` and the extended-tier subjects are skipped rather than run. To really
run them, install the full-range kernel and set the variable:

```bash
uv run python -c "import libephemeris; libephemeris.download_leb_for_tier('extended')"
LIBEPHEMERIS_PRECISION=extended uv run poe test:extended
```

The `regenerate:*` tasks and `test:gates:extended` set
`LIBEPHEMERIS_PRECISION=extended` for themselves.

---

## Commands

```bash
# Test — 4 tiers, each includes everything from the previous one
poe test:core         # ~7,500 tests — every module, no exhaustive matrix
poe test:base         # full suite (~14,000 collected) — exhaustive matrix, DE440s subjects (1849-2150)
poe test:medium       # full suite — adds DE440 subjects (1550-2650)
poe test:extended     # full suite — all subjects, full ephemeris range

# Coverage — same tiers with terminal + HTML report (htmlcov/)
poe test:core:cov     # Coverage on core tier
poe test:base:cov     # Coverage on base tier
poe test:medium:cov   # Coverage on medium tier
poe test:extended:cov # Coverage on extended tier (full)
poe test:all:cov      # Alias of test:extended:cov, with an explicit --cov=kerykeion

# Backend-specific runs (same tests, different ephemeris engine)
poe test:lib          # core tests forced on libephemeris
poe test:swe          # core tests forced on swisseph (needs kerykeion[swiss])
poe test:compare      # the two backends compared head to head

# Regenerate golden standards — the full list
poe regenerate:svg            # SVG chart baselines (tests/data/svg/) — three scripts, then the eleven test-owned baselines via KERYKEION_REGEN_BASELINES
poe regenerate:reports        # Report golden files (tests/fixtures/)
poe regenerate:positions      # Expected positions & subjects (tests/data/expected_*.py)
poe regenerate:aspects        # Expected aspects (tests/data/expected_*_aspects.py)
poe regenerate:configurations # House-system, sidereal-mode, perspective, return, composite, ephemeris and Arabic-part fixtures
poe regenerate:docs-charts    # docs/charts/ — the README's showcase SVGs, embedded by raw URL
poe regenerate:gallery-v6     # tests/data/v6_gallery/ and its index page
poe regenerate:glyph-gallery  # The glyph poster and site/docs/chart-glyphs.md
poe regenerate:glyph-widths   # charts/glyph_metrics.py — per-character widths (macOS only)
poe regenerate:glyph-ink      # charts/glyph_ink_metrics.py — measured in a browser (interactive)
poe regenerate:all            # Everything above except the two glyph-measurement tasks
```

`regenerate:all` runs `regenerate:svg`, `regenerate:docs-charts`,
`regenerate:gallery-v6`, `regenerate:glyph-gallery`, `regenerate:reports`,
`regenerate:positions`, `regenerate:aspects` and `regenerate:configurations`.
The two glyph-measurement tasks are excluded on purpose: one needs macOS system
fonts, the other opens a browser.

---

## What Each Tier Tests

### `test:core` (~7,500 tests)

Runs **97 of the 102 test files** in `tests/core/` — 7,517 offline tests at the
time of writing; run `--collect-only` for today's figure — one per
module/concern. This tier exercises representative paths across Kerykeion:
subject creation, chart drawing, aspects, reports, composite subjects,
planetary returns, ephemeris data, transits, relationship scores, context
serialization, settings, utilities, Arabic parts, house comparison, moon
phases, geonames, eclipses, heliacal, occultations, planetary phenomena,
primary directions, secondary progressions, midpoints, astro-cartography, and
more.

It **excludes** the 5 exhaustive matrix files that generate thousands of parametrized combinations:

| Excluded file | What it does |
|---------------|-------------|
| `test_houses_positions.py` | Every house system x temporal/geographic subject x cusp |
| `test_planetary_positions.py` | Every planet x temporal/geographic subject |
| `test_moon_phase_historical_verification.py` | 365 historical syzygies from the AstroPixels tables |
| `test_subject_factory_parametrized.py` | Every house system/sidereal mode/perspective x subjects |
| `test_chart_parametrized.py` | Temporal/geographic x themes/house systems cross-products |

Use `test:core` for fast local development feedback.

### `test:base`

Includes **all 102 test files** (core + the 5 matrix files above). The full suite always collects ~14,000 tests; the tier controls which temporal subjects actually run — cases for subjects outside the tier are skipped at runtime. `base` restricts temporal subjects to the **DE440s ephemeris** range (1849-2150, 11 subjects). This is the recommended local-validation tier — it catches regressions across the full matrix without requiring extended ephemeris files.

### `test:medium`

Same as `base`, but extends the temporal range to the **DE440 ephemeris** (1550-2650, 16 subjects). Adds Galileo, Newton, Enlightenment-era, and far-future (2200) subjects.

### `test:extended`

Runs everything with **all 25 temporal subjects** spanning from 500 BC to 2200 AD (DE441, full-range kernel required). SVG baseline tests gracefully skip when the expected file doesn't exist.

---

## Directory Structure

```
tests/
├── conftest.py              # Tier filtering (auto-detected), parametrized fixtures, session subjects
├── core/                    # All 102 test files (representative subset shown)
│   ├── conftest.py          # Session fixtures, SVG/report comparison helpers
│   ├── test_arabic_parts.py
│   ├── test_aspects.py
│   ├── test_astrological_subject.py
│   ├── test_astrological_subject_jyotish.py
│   ├── test_chart_data_factory.py
│   ├── test_chart_drawer.py
│   ├── test_chart_parametrized.py
│   ├── test_composite_subject.py
│   ├── test_context_serializer.py
│   ├── test_draw_planets.py
│   ├── test_ephemeris_data.py
│   ├── test_fetch_geonames.py
│   ├── test_house_comparison.py
│   ├── test_houses_positions.py
│   ├── test_json_dump.py
│   ├── test_lunar_phase_svg.py
│   ├── test_moon_phase_details_factory_mocked.py
│   ├── test_moon_phase_historical_verification.py
│   ├── test_planetary_positions.py
│   ├── test_planetary_return.py
│   ├── test_relationship_score.py
│   ├── test_report.py
│   ├── test_settings.py
│   ├── test_subject_factory_parametrized.py
│   ├── test_transits.py
│   ├── test_utilities.py
│   └── ...                  # (102 files total — see Test Files Reference below)
├── data/                    # Shared test data
│   ├── compare_svg_lines.py          # SVG line-by-line comparison utility
│   ├── expected_natal_aspects.py     # Golden natal aspect data
│   ├── expected_synastry_aspects.py  # Golden synastry aspect data
│   ├── expected_positions.py         # Expected planetary positions per subject
│   ├── expected_astrological_subjects.py
│   ├── expected_arabic_parts.py
│   ├── test_subjects_matrix.py       # Subject matrix: 25 temporal, 16 geographic
│   ├── configurations/               # Settings override JSON files
│   ├── svg/                           # 354 SVG baseline files
│   ├── golden_places.py              # frozen coordinates: golden charts never resolve a city online
│   ├── compare_svg_lines.py          # THE SVG comparison; there is one
│   └── regeneration_guard.py         # refuses to regenerate from another checkout's code
└── fixtures/                # Golden-file report snapshots (42 .txt files)
```

---

## Test Subjects Matrix

Defined in `tests/data/test_subjects_matrix.py`:

### Temporal Subjects (25)

Cover 2,700 years from 500 BC to 2200 AD, exercising all three ephemeris tiers:

- **Base (DE440s, 1849-2150, 11 subjects):** industrial_1850, einstein_1879, ww1_start_1914, yoko_ono_1933, john_lennon_1940, paul_mccartney_1942, johnny_depp_1963, millennium_2000, equinox_2020, future_2050, future_2100
- **Medium (DE440, 1550-2650, adds 5):** galileo_1564, newton_1643, enlightenment_1750, american_independence_1776, future_2200
- **Extended (DE441, adds 9):** ancient_500bc, ancient_200bc, roman_100ad, late_antiquity_400, early_medieval_800, high_medieval_1100, late_medieval_1300, early_renaissance_1450, columbus_1492

### Geographic Subjects (16)

Latitude diversity from 66°S to 66°N, plus date-line coverage:

- High northern (60°N-66°N): oslo_60n, reykjavik_64n, arctic_circle_66n
- Mid northern: london_51n, new_york_40n, tokyo_35n
- Equatorial: quito_equator, singapore_1n, nairobi_1s
- Mid southern: sydney_34s, buenos_aires_34s, cape_town_34s
- High southern: ushuaia_55s, antarctic_circle_66s
- Date line: fiji_dateline_east, samoa_dateline_west

### Configuration Axes

- **House Systems (23):** Placidus, Koch, Whole Sign, Equal, Campanus, Regiomontanus, Porphyry, Morinus, Alcabitius, Carter, Horizon, Sunshine, etc.
- **Sidereal Modes (20):** Lahiri, Fagan-Bradley, DeLuce, J2000, Raman, Ushashashi, Krishnamurti, Hipparchos, etc.
- **Perspective Types (4):** Apparent Geocentric, True Geocentric, Heliocentric, Topocentric
- **Synastry Pairs (6):** john_lennon_1940 + paul_mccartney_1942, john_lennon_1940 + yoko_ono_1933, johnny_depp_1963 + john_lennon_1940, einstein_1879 + galileo_1564, millennium_2000 + equinox_2020, ancient_500bc + roman_100ad

---

## Test Files Reference

### Core Functionality

| File | What it covers |
|------|----------------|
| `test_astrological_subject.py` | Subject creation, all planet/house accessors, zodiac configs, edge cases (midnight, leap year, DST), Arabic parts, vertex, fixed stars, TNOs, error handling, is_diurnal |
| `test_astrological_subject_jyotish.py` | Sidereal (Lahiri) subject with exact position regression values |
| `test_json_dump.py` | JSON serialization of subject data |
| `test_planetary_positions.py` | Parametrized exact planetary position validation against expected data |
| `test_houses_positions.py` | House position validation across temporal/geographic/system variations |

### Factories

| File | What it covers |
|------|----------------|
| `test_chart_data_factory.py` | Single/dual chart creation, all chart types (natal/synastry/transit/composite/return), element/quality distributions, aspect calculations, parameter validation, serialization, edge cases |
| `test_composite_subject.py` | Midpoint composite creation, commutativity, incompatible configs, custom names, planet/house attributes, Davison method, edge cases |
| `test_ephemeris_data.py` | Daily/hourly/minutely ephemeris, planetary movement rates, model output, step validation, cross-year boundary, configuration variants (sidereal, Koch, geocentric, DST) |
| `test_planetary_return.py` | Solar/lunar return calculation, return sun/moon position accuracy, house system variations, location variants, deprecated API tests, online mode validation |
| `test_relationship_score.py` | Score calculation, aspect evaluation rules, destiny sign, score descriptions, breakdown structure, exact regression scores for 4 canonical couples |
| `test_subject_factory_parametrized.py` | Cross-product: all house systems x subjects, all sidereal modes x subjects, all perspectives x subjects, temporal/geographic coverage, configuration consistency |
| `test_transits.py` | TransitsTimeRangeFactory initialization, transit detection, custom points/aspects, empty/single ephemeris edge cases |

### Aspects

| File | What it covers |
|------|----------------|
| `test_aspects.py` | Natal/synastry aspects with expected data, aspect types/degrees validation, movement calculation (applying/separating/static), edge cases (boundary crossing, retrograde, epsilon handling, non-standard aspects like quintile/septile), planet_id_decoder, axis orb filter |

### Charts & Visualization

| File | What it covers |
|------|----------------|
| `test_chart_drawer.py` | All chart types (natal, synastry, transit, composite, return), all themes (classic, dark, B&W), all sidereal modes (20 parametrized), all house systems (23 parametrized), 9 parametrized languages plus default English, partial views (wheel-only, aspect-grid-only), chart options (padding, CSS, minify, custom title, indicators), SVG baseline comparison, save methods, error handling, large aspect lists, overlapping planets, composite location |
| `test_chart_parametrized.py` | Temporal x themes cross-product, geographic x house systems, extreme latitude whole-sign, sidereal x theme combinations, house system synastry/transit |
| `test_draw_planets.py` | Planet glyph positioning, retrograde markers, degree labels, planet grouping/overlap handling, edge cases (empty list, single planet, zero/359 degrees), SVG output structure, chart type variants, internal helpers |
| `test_lunar_phase_svg.py` | All 8 standard moon phases match reference SVG sheet |
| `test_glyph_system.py` | One declared glyph set: no hand-edit survives inside the generated `<symbol>` block, no symbol silently deleted, one weight and one colour per glyph |
| `test_wheel_growth.py` | The modern wheel grows only on the two canvas shapes that have room for it, and stays byte-identical below that |
| `test_modern_cusp_dimming.py` | A cusp line dims for exactly the span of the reading written across it — all of it or none |
| `test_house_number_spread.py` | How far apart two house numbers are pushed when a quadrant system crowds four cusps into three degrees |
| `test_house_sector_wedges.py` | The invisible clickable house wedge sits under the cusp line the reader sees, so a click near a cusp selects the right house |
| `test_grid_point_labels.py` | The name a planet-grid row prints and the room it leaves — a translated name may not overrun the block beside it |
| `test_diurnality_svg.py` | The info panel's diurnality line: neutral wording, and absent rather than guessed where it has no referent |
| `test_optional_chart_marks.py` | The six opt-in marks (stations, out-of-bounds, separating dashes, relationship score, ayanamsa, polar fallback): off is genuinely off, on draws the mark |
| `test_optional_mark_baselines.py` | The twenty optional-mark SVG baselines that nothing was comparing |
| `test_translation_coverage.py` | Every label a chart can print exists in all ten language packs |
| `test_glyph_playground.py` | The 264 diffs in `scripts/glyph_playground.html` round-trip to real renders |

### Reports

| File | What it covers |
|------|----------------|
| `test_report.py` | Subject/natal/synastry/transit/composite/return reports, moon phase overview, golden-file snapshots (42 baseline files), section presence, content formatting (retrograde markers, aspect symbols, movement, speed, declination, position, dates, coordinates), element/quality percentage sums, max_aspects truncation, sidereal mode display, empty data paths, relationship score content, cusp comparison, active points/aspects presets, geographic/temporal diversity, private helpers, parametrized sweeps, composite houses, subject-only mode |

### Backward Compatibility

> **Note:** `test_backward_compatibility.py` was removed in v6 along with the backward compatibility layer (`backword.py`). Legacy class aliases no longer exist.

### Context Serializer

| File | What it covers |
|------|----------------|
| `test_context_serializer.py` | Point/lunar phase/aspect/element/quality/subject/chart data to XML context, transit moments, transits time range, house comparison context, return subject context, moon phase overview, dispatcher, non-qualitative output validation |

### Settings & Configuration

| File | What it covers |
|------|----------------|
| `test_settings.py` | Default/custom settings loading, language settings, translations (nested keys, missing keys, fallbacks, explicit language dict, loaded overrides), settings file validation |

### Utilities

| File | What it covers |
|------|----------------|
| `test_utilities.py` | `get_number_from_name`, `get_kerykeion_point_from_degree`, logging setup, `is_point_between`, `get_planet_house` (including floating-point cusp boundary regression), `circular_mean`/`circular_sort`, moon emoji/name, polar latitude adjustment, `find_common_active_points`, Julian day conversion, `calculate_moon_phase`, `inline_css_variables_in_svg` (including no-style-block and no-fallback edge cases), `distribute_percentages_to_100`, house name/number conversion, chart utils internal functions, planet grid layout, element/quality distribution |

### External Services

| File | What it covers |
|------|----------------|
| `test_fetch_geonames.py` | Online lookup (marked `@pytest.mark.online`), mocked basic/error paths, cache filtering (transient errors, valid responses, invalid JSON, timezone), env config, private error paths (malformed payloads) |

### Specialized

| File | What it covers |
|------|----------------|
| `test_arabic_parts.py` | Formula correctness (Pars Fortunae/Spiritus/Amoris/Fidei), day/night symmetry, result properties, auto-activation of dependencies, day/night detection (Sun altitude), geographic edge cases, sidereal mode, `is_diurnal` field, single-part-only activation |
| `test_house_comparison.py` | Cusps/points in reciprocal houses, limited active points, HouseComparisonFactory end-to-end, malformed data handling |
| `test_moon_phase_details_factory_mocked.py` | Moon phase details factory with mocked ephemeris backend, phase identification, illumination, upcoming phases, eclipses, integration test |
| `test_moon_phase_historical_verification.py` | 365 historical syzygies (AstroPixels, 2001-2040) verified for angle, illumination and synodic month |
| `test_v512_features.py` | Regression tests for v5.12 features (house cusp speeds, expanded fixed stars, sidereal modes, ayanamsa value) |
| `test_profections.py` | Annual profections against the Lennon chart: one house per year, the sign on the profected cusp, the Lord of the Year, birthday boundaries |
| `test_firdaria.py` | Firdaria invariants: the opening lord matches the chart's sect luminary, the 75-year cycle is contiguous, node periods carry no sub-periods |
| `test_receptions_horary.py` | Mutual receptions, horary indicators, and the rulership lookups both build on |
| `test_lunar_phase_windows.py` | The phase name is a window *centred* on the event it names, not a bin starting at it |
| `test_point_and_chartdata_enrichments.py` | The v6 enrichments: per-point `motion_state`, star constellation, chart angularities and stelliums, progressed points, precise lunar age |
| `test_timezone_correctness.py` | The civil-time layer: offsets outside the tz database's recorded range, spring-forward gaps and fall-back folds |

### v6 Advanced Features

| File | What it covers |
|------|----------------|
| `test_astro_cartography.py` | AstroCartographyFactory ACG line computation |
| `test_backend_comparison.py` | libephemeris vs swisseph results comparison |
| `test_barycentric.py` | Barycentric perspective calculations |
| `test_bce_dates.py` | BCE/negative year date handling |
| `test_davison_composite.py` | Davison composite chart method |
| `test_deep_check_regressions.py` | Regression cases from the deep-check review campaigns |
| `test_dignities.py` | Essential dignities scoring |
| `test_dominants.py` | Chart dominants (planetary strength ranking) |
| `test_dynamic_fixed_stars.py` | FixedStarDiscoveryFactory and catalog |
| `test_eclipses.py` | EclipseFactory solar/lunar eclipse search |
| `test_ephemeris_backend_path.py` | EPHE_DATA_PATH resolution per backend |
| `test_gauquelin.py` | Gauquelin 36-sector calculation |
| `test_heliacal.py` | HeliacalFactory risings/settings |
| `test_heliocentric_returns.py` | Heliocentric planetary returns |
| `test_lilith_variants.py` | True/Mean/Interpolated Lilith and Priapus |
| `test_local_space.py` | Azimuth & altitude calculations |
| `test_lunar_phase_search_directions.py` | Lunar phase search direction handling |
| `test_lunations.py` | LunationFactory new/full moon search |
| `test_modern_decluttering.py` | Modern chart style declutter logic |
| `test_mundane_aspects.py` | MundaneAspectFactory exact transiting-to-transiting aspect search |
| `test_nakshatra.py` | Vedic nakshatra calculation |
| `test_nutation.py` | Nutation model computation |
| `test_occultations.py` | OccultationFactory lunar occultations |
| `test_oob_and_declination_aspects.py` | Out-of-bounds and declination aspects |
| `test_planetary_hours_factory.py` | Planetary hours calculation |
| `test_planetary_nodes.py` | PlanetaryNodesFactory nodes/apsides |
| `test_planetary_phenomena.py` | PlanetaryPhenomenaFactory elongation/phase |
| `test_planetary_return_backwards.py` | Backward-looking return searches |
| `test_planetocentric.py` | Planetocentric perspective calculations |
| `test_predictive_factories.py` | SecondaryProgressionFactory, SolarArcFactory, MidpointFactory |
| `test_primary_directions.py` | PrimaryDirectionsFactory Placidus semi-arc |
| `test_public_api_surface.py` | Public API surface guard (exports/introspection) |
| `test_reference_validation.py` | Validation against external reference values |
| `test_relocated_chart.py` | RelocatedChartFactory house recalculation |
| `test_review_regressions.py` | Regression cases from fresh review campaigns |
| `test_retrograde_stations.py` | Retrograde station search |
| `test_sign_ingresses.py` | Sign ingress search |
| `test_sun_times_factory.py` | SunTimesFactory sunrise/sunset/twilight |
| `test_svg_focus_contract.py` | Modern SVG focus-mode contract |
| `test_timing_factories_concurrency.py` | Thread-safety of the timing factories |
| `test_transit_exactness.py` | Transit event detection precision |
| `test_transit_refinement.py` | Bisection refinement for exact moments |
| `test_triplicity_lords.py` | Triplicity lords (dignities) |
| `test_uranian_planets.py` | 8 Hamburg School hypothetical points |
| `test_v5_migration_errors.py` | v5-to-v6 migration error messages |
| `test_void_of_course_moon_factory.py` | Void-of-course Moon detection |
| `test_zodiacal_releasing.py` | Zodiacal releasing (aphesis) periods |
| `test_retrograde_periods.py` | `RetrogradeStationFactory.retrograde_periods_*` — retrograde spans clipped to a range |
| `test_sign_periods.py` | `SignIngressFactory.sign_periods_*` — contiguous sign stays clipped to a range |
| `test_planetary_return_roundtrip.py` | A reported return instant re-fed as the seed of the next search finds the *next* return, not the same one |
| `test_polar_house_invariants.py` | What must still hold when a house system is undefined inside the polar circle |
| `test_sun_times_anchors.py` | Sunrise, sunset and solar noon against two national observatories — hand-transcribed values no script may rewrite |
| `test_sun_times_altitude_invariant.py` | The Sun-vs-horizon geometry re-measured as an angle by a second implementation, where near-polar clock comparisons stop being meaningful |
| `test_ephemeris_provenance.py` | Source propagation and sealed-LEB coverage behaviour |

### Gates

These run in `poe check` / `poe quality` and fail on documentation and baseline
rot rather than on a calculation.

| File | What it covers |
|------|----------------|
| `test_agent_skill_contract.py` | `skills/kerykeion/` against version drift, license loss and dangling reference files — it is copied verbatim into third-party repos |
| `test_every_baseline_has_a_reader.py` | A stored SVG baseline that no test compares. Twenty were unread when it was written |
| `test_golden_charts_are_hermetic.py` | A golden chart asking GeoNames where it was cast; both network doors are refused for the whole golden suite |
| `test_baseline_freshness.py` | A committed baseline missing an info-panel row the template now emits — how fifty-one baselines, eleven of them README images, were left behind |

---

## Infrastructure

### Root conftest (`tests/conftest.py`)

- **Tier filtering:** `pytest_addoption` adds `--tier` option (auto-detected from the loaded ephemeris kernel when omitted); `pytest_collection_modifyitems` skips subjects outside the selected tier
- **Session-scoped subjects:** `john_lennon`, `paul_mccartney`, `johnny_depp` (shared across all tests)
- **Parametrized fixtures:** `temporal_subject_data`, `geographic_subject_data`, `house_system`, `sidereal_mode`, `perspective_type`, `synastry_pair_ids`, `planet_name`, `house_name`, `angle_name`, etc.
- **Chart/aspect fixtures:** `natal_chart_data`, `transit_chart_data`, `synastry_chart_data`, `natal_aspects`
- **Edge-case fixtures:** `polar_latitude_subjects`, `leap_year_subject`, `midnight_subject`

### Core conftest (`tests/core/conftest.py`)

- **Session-scoped subjects:** `johnny_depp`, `john_lennon`, `yoko_ono`, `paul_mccartney` (using `AstrologicalSubjectFactory.from_birth_data` with explicit coordinates, `online=False`)
- **Comparison helpers:** `assert_position_equal`, `assert_positions_match`, `assert_report_matches_snapshot`
- **Tolerance constants:** `POSITION_TOLERANCE=1e-2` (0.01°), `SPEED_TOLERANCE=1e-4`, `DECLINATION_TOLERANCE=1e-2`, `ORB_TOLERANCE=1e-2`, `PERCENTAGE_TOLERANCE=2` (integer percentages, ±2)
- **SVG comparison:** the golden tests import `compare_svg_file` from `tests.data.compare_svg_lines` — the single implementation; the conftest imports only `numbers_are_comparable()`, `active_backend()` and `BASELINE_BACKEND` from it, for the `reference_backend_only` skip and its message. Three other copies of it lived in the test tree, each with its own tolerance; the loosest returned without asserting on any structural difference and allowed 50% on every number.

### Golden-File Testing

SVG baseline files live in `tests/data/svg/` (354 files). Tests compare generated SVGs through `compare_svg_file()` in `tests/data/compare_svg_lines.py`, which is the only such comparison in the repository.

**Structure is fatal, on every backend.** Line count, the count of numbers in a line, and the line with its numbers blanked out must all match. A missing baseline fails and names `uv run poe regenerate:svg`. The extended parametrized matrix alone skips a combination whose baseline was never generated.

**Numbers are compared with `rel_tol=0.0, abs_tol=1e-4`**, and only on the backend the baselines were generated with (`libephemeris`). On another backend the structural assertions still run and the test then reports SKIPPED with the reason: the two backends compute different charts, not less precise ones, and one tolerance wide enough to cover that is the `rel_tol=0.5` this replaced.

A few golden charts cast two millennia back differ STRUCTURALLY between the backends — an aspect falls in or out of orb. Those carry `@pytest.mark.reference_backend_only`, one at a time and with a reason.

**Every baseline has a reader.** `tests/core/test_every_baseline_has_a_reader.py` fails if a stored baseline is compared by no test; twenty were, when it was written. It finds out by running every golden test with the comparison replaced by a recorder (`tests/data/golden_drive.py` — parametrized cases expanded, `setup_class` called, skips survived), plus the source lines that hand a name to a comparison; a name that is merely mentioned, in a docstring or an exemption table, is not a reader. On the default (medium) kernel the baselines of extended-tier subjects are exempt by tier, so a lost reader for one of them is invisible there; `poe check` therefore also runs `test:gates:extended`, the same gates under `LIBEPHEMERIS_PRECISION=extended`, where only what the backend cannot compute is exempt — and the run fails if the extended kernel it asked for is not the one installed.

**Golden charts are hermetic.** They are cast at coordinates frozen in `tests/data/golden_places.py`, never resolved through GeoNames — `from_birth_data` defaults to `online=True`, so the whole golden suite used to depend on what a remote service answered that minute. `tests/core/test_golden_charts_are_hermetic.py` fails if one reaches for the network: it drives every golden test in all five golden modules through the same driver with both GeoNames doors — the city lookup and the timezone-for-coordinates lookup — refused.

Report golden files live in `tests/fixtures/` (42 `.txt` files). The `assert_report_matches_snapshot` helper compares generated report output against these files.

---

## Design Principles

1. **Offline by default.** All subjects use `online=False, suppress_geonames_warning=True` with explicit `lat`, `lng`, `tz_str` coordinates. Only tests marked `@pytest.mark.online` require network access.

2. **Parallel-safe.** No shared mutable state between tests. Session-scoped fixtures create immutable subjects. Tests are distributed with `-n auto --dist loadgroup` (one worker per core) by default.

3. **Tiered ephemeris.** Historical and future test subjects are stratified by the JPL ephemeris file required. Run `test:base` for fast validation and `test:extended` for full coverage.

4. **Explicit baseline policy.** SVG golden tests fail when an expected baseline is missing, when the line count differs, when a line's number count differs, and when a line differs anywhere it has no numbers. The extended parametrized matrix alone skips combinations that do not have an intentionally generated baseline.

5. **Semantic file organization.** Each test file maps to a specific module or concern (e.g., `test_chart_drawer.py` covers `kerykeion.charts.chart_drawer`, `test_aspects.py` covers `kerykeion.aspects`).

6. **Parametrized coverage explosion.** Configuration axes (house systems, sidereal modes, perspectives, temporal subjects, geographic subjects) are combined via `pytest.mark.parametrize` to achieve broad coverage with minimal test code.
