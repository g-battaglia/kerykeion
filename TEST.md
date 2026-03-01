# Test Suite Documentation

## Overview

Kerykeion's test suite is organized in a single consolidated `tests/core/` directory with **27 semantic test files**, **7,977 collected tests** (7,917 passed / 60 skipped in offline mode), and parallel execution via `pytest-xdist` (`-n 8`).

Tests run in approximately **16 seconds** on 8 workers.

---

## Directory Structure

```
tests/
├── __init__.py
├── conftest.py              # Root: tier filtering, parametrized fixtures, session subjects
├── core/                    # All 27 test files
│   ├── __init__.py
│   ├── conftest.py          # Core: session fixtures, SVG/report comparison helpers
│   ├── test_arabic_parts.py
│   ├── test_aspects.py
│   ├── test_astrological_subject.py
│   ├── test_astrological_subject_jyotish.py
│   ├── test_backward_compatibility.py
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
│   └── test_utilities.py
├── data/                    # Shared test data
│   ├── __init__.py
│   ├── compare_svg_lines.py          # SVG line-by-line comparison utility
│   ├── expected_natal_aspects.py     # Golden natal aspect data
│   ├── expected_synastry_aspects.py  # Golden synastry aspect data
│   ├── expected_positions.py         # Expected planetary positions per subject
│   ├── expected_aspects.py           # Expected aspects per subject
│   ├── expected_astrological_subjects.py
│   ├── expected_arabic_parts.py
│   ├── test_subjects_matrix.py       # Subject matrix: 24 temporal, 16 geographic
│   ├── configurations/               # Settings override JSON files
│   └── svg/                           # 286 SVG baseline files
└── fixtures/                # Golden-file report snapshots (36 .txt files)
```

---

## Running Tests

### Quick Commands

```bash
# All tests (parallel, offline)
pytest

# Core tests only (verbose)
pytest tests/core/ -v -m 'not online'

# Tier-based (see "Temporal Tiers" below)
pytest tests/ --tier=base -v -m 'not online'
pytest tests/ --tier=medium -v -m 'not online'
pytest tests/ --tier=extended -v -m 'not online'

# Online-only (requires network + GeoNames account)
pytest tests/ -v -m 'online'

# With coverage
pytest --cov=kerykeion --cov-config=pyproject.toml --cov-report=html --cov-report=term --cov-report=xml
```

### Poe Task Runner

```bash
# Test — 4 levels, hierarchy: core < base < medium < extended
poe test:core         # ~1,750 tests — all modules, no exhaustive matrix
poe test:base         # ~6,300 tests — includes matrix, DE440s subjects (1849-2150)
poe test:medium       # ~7,000 tests — adds DE440 subjects (1550-2650)
poe test:extended     # ~7,900 tests — all subjects, full ephemeris range

# Regenerate golden standards — one command per category
poe regenerate:svg        # SVG chart baselines (tests/data/svg/)
poe regenerate:reports    # Report golden files (tests/fixtures/)
poe regenerate:positions  # Expected positions & subjects (tests/data/expected_positions.py, ...)
poe regenerate:aspects    # Expected aspects (tests/data/expected_*_aspects.py)
```

---

## Temporal Tiers

Tests use subjects spanning different historical periods. Each period requires a different JPL ephemeris file. The `--tier` flag filters subjects cumulatively:

| Tier | Ephemeris | Year Range | Subjects | Passed | Skipped |
|------|-----------|------------|----------|--------|---------|
| `core` | — | — | — | 1,752 | 5 |
| `base` | DE440s | 1849-2150 | 11 | 6,308 | 1,669 |
| `medium` | DE440 | 1550-2650 | 16 | 6,976 | 1,001 |
| `extended` | DE441 | full range | 24 | 7,917 | 60 |

`core` runs all 22 non-matrix test files — it covers every module and code path without the exhaustive subject × planet × house parametrized combinations. The matrix files (`test_houses_positions.py`, `test_planetary_positions.py`, `test_moon_phase_historical_verification.py`, `test_subject_factory_parametrized.py`, `test_chart_parametrized.py`) are included starting from `base`.

---

## Test Subjects Matrix

Defined in `tests/data/test_subjects_matrix.py`:

### Temporal Subjects (24)

Cover centuries from 100 AD to 2200 AD, exercising all three ephemeris tiers:

- **Base (DE440s, 1849-2150):** modern_1990, john_lennon_1940, einstein_1879, ww2_end_1945, moon_landing_1969, y2k_2000, near_future_2030, mid_future_2050, late_future_2100, early_modern_1900, late_victorian_1880
- **Medium (DE440, 1550-2650):** renaissance_1600, galileo_1564, newton_1643, far_future_2200, distant_future_2500
- **Extended (DE441):** ancient_rome_100ad, medieval_800, viking_era_1000, crusades_1200, columbus_1492, bach_1685, napoleon_1769, deep_future_2650

### Geographic Subjects (16)

Latitude diversity from 66°S to 66°N:

- Equatorial: quito_equator, singapore_1n, nairobi_1s
- Tropical: mumbai_19n
- Mid-latitude: rome_41n, new_york_40n, tokyo_35n, london_51n, berlin_52n, sydney_34s, buenos_aires_34s, cape_town_34s
- High-latitude: stockholm_59n, anchorage_61n
- Polar-adjacent: antarctic_circle_66s, ushuaia_55s

### Configuration Axes

- **House Systems (23):** Placidus, Koch, Whole Sign, Equal, Campanus, Regiomontanus, Porphyry, Morinus, Alcabitius, Carter, Horizon, Sunshine, etc.
- **Sidereal Modes (20):** Lahiri, Fagan-Bradley, DeLuce, J2000, Raman, Ushashashi, Krishnamurti, Hipparchos, etc.
- **Perspective Types (4):** Apparent Geocentric, True Geocentric, Heliocentric, Topocentric
- **Synastry Pairs (6):** john_lennon + yoko_ono, john_lennon + paul_mccartney, etc.

---

## Test Files Reference

### Core Functionality

| File | Tests | What it covers |
|------|-------|----------------|
| `test_astrological_subject.py` | 101 | Subject creation, all planet/house accessors, zodiac configs, edge cases (midnight, leap year, DST), Arabic parts, vertex, fixed stars, TNOs, error handling, is_diurnal |
| `test_astrological_subject_jyotish.py` | 31 | Sidereal (Lahiri) subject with exact position regression values |
| `test_json_dump.py` | 24 | JSON serialization of subject data |
| `test_planetary_positions.py` | 14 | Parametrized exact planetary position validation against expected data |
| `test_houses_positions.py` | 16 | House position validation across temporal/geographic/system variations |

### Factories

| File | Tests | What it covers |
|------|-------|----------------|
| `test_chart_data_factory.py` | 75 | Single/dual chart creation, all chart types (natal/synastry/transit/composite/return), element/quality distributions, aspect calculations, parameter validation, serialization, edge cases |
| `test_composite_subject.py` | 68 | Midpoint composite creation, commutativity, incompatible configs, custom names, planet/house attributes, Davison method, edge cases |
| `test_ephemeris_data.py` | 34 | Daily/hourly/minutely ephemeris, planetary movement rates, model output, step validation, cross-year boundary, configuration variants (sidereal, Koch, geocentric, DST) |
| `test_planetary_return.py` | 62 | Solar/lunar return calculation, return sun/moon position accuracy, house system variations, location variants, deprecated API tests, online mode validation |
| `test_relationship_score.py` | 63 | Score calculation, aspect evaluation rules, destiny sign, score descriptions, breakdown structure, exact regression scores for 4 canonical couples |
| `test_subject_factory_parametrized.py` | 18 | Cross-product: all house systems x subjects, all sidereal modes x subjects, all perspectives x subjects, temporal/geographic coverage, configuration consistency |
| `test_transits.py` | 17 | TransitsTimeRangeFactory initialization, transit detection, custom points/aspects, empty/single ephemeris edge cases |

### Aspects

| File | Tests | What it covers |
|------|-------|----------------|
| `test_aspects.py` | 66 | Natal/synastry aspects with expected data, aspect types/degrees validation, movement calculation (applying/separating/static), edge cases (boundary crossing, retrograde, epsilon handling, non-standard aspects like quintile/septile), planet_id_decoder, axis orb filter |

### Charts & Visualization

| File | Tests | What it covers |
|------|-------|----------------|
| `test_chart_drawer.py` | 193 | All chart types (natal, synastry, transit, composite, return), all themes (classic, dark, light, high-contrast, B&W, strawberry), all sidereal modes (18 parametrized), all house systems (23 parametrized), 10 languages, partial views (wheel-only, aspect-grid-only), chart options (padding, CSS, minify, custom title, indicators), SVG baseline comparison, save methods, error handling, large aspect lists, overlapping planets, composite location |
| `test_chart_parametrized.py` | 9 | Temporal x themes cross-product, geographic x house systems, extreme latitude whole-sign, sidereal x theme combinations, house system synastry/transit |
| `test_draw_planets.py` | 75 | Planet glyph positioning, retrograde markers, degree labels, planet grouping/overlap handling, edge cases (empty list, single planet, zero/359 degrees), SVG output structure, chart type variants, internal helpers |
| `test_lunar_phase_svg.py` | 5 | All 8 standard moon phases match reference SVG sheet |

### Reports

| File | Tests | What it covers |
|------|-------|----------------|
| `test_report.py` | 110 | Subject/natal/synastry/transit/composite/return reports, moon phase overview, golden-file snapshots (36 baseline files), section presence, content formatting (retrograde markers, aspect symbols, movement, speed, declination, position, dates, coordinates), element/quality percentage sums, max_aspects truncation, sidereal mode display, empty data paths, relationship score content, cusp comparison, active points/aspects presets, geographic/temporal diversity, private helpers, parametrized sweeps, composite houses, subject-only mode |

### Backward Compatibility

| File | Tests | What it covers |
|------|-------|----------------|
| `test_backward_compatibility.py` | 66 | Legacy `AstrologicalSubject` wrapper, `KerykeionChartSVG` wrapper, `NatalAspects`/`SynastryAspects` wrappers, `kr_types` module aliases, deprecation warnings, migration path examples, `disable_chiron` params, zodiac type normalization, settings file param warnings, custom active aspects, legacy chart type validation, `SubscriptableBaseModel` operations, ISO datetime parsing with Z suffix, active aspects passthrough |

### Context Serializer

| File | Tests | What it covers |
|------|-------|----------------|
| `test_context_serializer.py` | 72 | Point/lunar phase/aspect/element/quality/subject/chart data to XML context, transit moments, transits time range, house comparison context, return subject context, moon phase overview, dispatcher, non-qualitative output validation |

### Settings & Configuration

| File | Tests | What it covers |
|------|-------|----------------|
| `test_settings.py` | 30 | Default/custom settings loading, language settings, translations (nested keys, missing keys, fallbacks, explicit language dict, loaded overrides), settings file validation |

### Utilities

| File | Tests | What it covers |
|------|-------|----------------|
| `test_utilities.py` | 91 | `get_number_from_name`, `get_kerykeion_point_from_degree`, logging setup, `is_point_between`, `get_planet_house` (including floating-point cusp boundary regression), `circular_mean`/`circular_sort`, moon emoji/name, polar latitude adjustment, `find_common_active_points`, Julian day conversion, `calculate_moon_phase`, `inline_css_variables_in_svg` (including no-style-block and no-fallback edge cases), `distribute_percentages_to_100`, house name/number conversion, chart utils internal functions, planet grid layout, element/quality distribution |

### External Services

| File | Tests | What it covers |
|------|-------|----------------|
| `test_fetch_geonames.py` | 18 | Online lookup (marked `@pytest.mark.online`), mocked basic/error paths, cache filtering (transient errors, valid responses, invalid JSON, timezone), env config, private error paths (malformed payloads) |

### Specialized

| File | Tests | What it covers |
|------|-------|----------------|
| `test_arabic_parts.py` | 54 | Formula correctness (Pars Fortunae/Spiritus/Amoris/Fidei), day/night symmetry, result properties, auto-activation of dependencies, day/night detection (Sun altitude), geographic edge cases, sidereal mode, `is_diurnal` field, single-part-only activation |
| `test_house_comparison.py` | 7 | Cusps/points in reciprocal houses, limited active points, HouseComparisonFactory end-to-end, malformed data handling |
| `test_moon_phase_details_factory_mocked.py` | 35 | Moon phase details factory with mocked Swiss Ephemeris, phase identification, illumination, upcoming phases, eclipses, integration test |
| `test_moon_phase_historical_verification.py` | 18 | 2042-case historical moon phase verification |

---

## Infrastructure

### Root conftest (`tests/conftest.py`)

- **Tier filtering:** `pytest_addoption` adds `--tier` option; `pytest_collection_modifyitems` skips subjects outside the selected tier
- **Session-scoped subjects:** `john_lennon`, `paul_mccartney`, `johnny_depp` (shared across all tests)
- **Parametrized fixtures:** `temporal_subject_data`, `geographic_subject_data`, `house_system`, `sidereal_mode`, `perspective_type`, `synastry_pair_ids`, `planet_name`, `house_name`, `angle_name`, etc.
- **Chart/aspect fixtures:** `natal_chart_data`, `transit_chart_data`, `synastry_chart_data`, `natal_aspects`
- **Edge-case fixtures:** `polar_latitude_subjects`, `leap_year_subject`, `midnight_subject`

### Core conftest (`tests/core/conftest.py`)

- **Session-scoped subjects:** `johnny_depp`, `john_lennon`, `yoko_ono`, `paul_mccartney` (using `AstrologicalSubjectFactory.from_birth_data` with explicit coordinates, `online=False`)
- **Comparison helpers:** `assert_position_equal`, `assert_positions_match`, `assert_svg_matches_baseline`, `assert_report_matches_snapshot`
- **Tolerance constants:** `POSITION_TOLERANCE=0.01`, `SPEED_TOLERANCE=0.01`, `DECLINATION_TOLERANCE=0.01`, `ORB_TOLERANCE=0.1`, `PERCENTAGE_TOLERANCE=0.5`
- **SVG comparison:** imports `compare_svg_lines` from `tests.data.compare_svg_lines`

### Markers (`pyproject.toml`)

```ini
[tool.pytest.ini_options]
markers = [
    "online: requires network access (GeoNames API)",
    "core: core functionality tests",
    "base: DE440s ephemeris tier (1849-2150)",
    "medium: DE440 ephemeris tier (1550-2650)",
    "extended: DE441 ephemeris tier (full range)",
]
addopts = "-n 8"
testpaths = "tests"
```

### Golden-File Testing

SVG baseline files live in `tests/data/svg/` (286 files). Tests compare generated SVGs line-by-line using `compare_svg_lines()`, which applies numeric tolerance for floating-point coordinates. If a baseline file is missing, the test is skipped gracefully.

Report golden files live in `tests/fixtures/` (36 `.txt` files). The `assert_report_matches_snapshot` helper compares generated report output against these files. Golden files can be regenerated via:

```bash
poe regenerate:svg        # SVG baselines
poe regenerate:reports    # Report snapshots
poe regenerate:positions  # Expected positions & subjects
poe regenerate:aspects    # Expected aspects
```

---

## Design Principles

1. **Offline by default.** All subjects use `online=False, suppress_geonames_warning=True` with explicit `lat`, `lng`, `tz_str` coordinates. Only tests marked `@pytest.mark.online` require network access.

2. **Parallel-safe.** No shared mutable state between tests. Session-scoped fixtures create immutable subjects. Tests are distributed across 8 workers by default.

3. **Tiered ephemeris.** Historical and future test subjects are stratified by the JPL ephemeris file required. CI can run `--tier=base` for fast validation and `--tier=extended` for full coverage.

4. **Graceful skip on missing baselines.** SVG golden-file tests skip (not fail) when the expected baseline doesn't exist, allowing new chart types to be added without immediately generating baselines.

5. **Semantic file organization.** Each test file maps to a specific module or concern (e.g., `test_chart_drawer.py` covers `kerykeion.charts.chart_drawer`, `test_aspects.py` covers `kerykeion.aspects`).

6. **Parametrized coverage explosion.** Configuration axes (house systems, sidereal modes, perspectives, temporal subjects, geographic subjects) are combined via `pytest.mark.parametrize` to achieve broad coverage with minimal test code.

---

## Known Follow-ups

- **README/docs SVG URLs.** Approximately 45 image URLs in `README.md`, `docs/`, and `site/` reference the old path `tests/charts/svg/`. These should be updated to `tests/data/svg/` in a separate documentation PR.
- **Docstring provenance comments.** Core test files contain comments noting which old files they consolidated (e.g., "Consolidates tests from: tests/aspects/..."). These are historical provenance and have no runtime impact.
