# Test Refactory Plan

## Objective

Reorganize the Kerykeion test suite into a **tiered architecture** in preparation for migrating from Swiss Ephemeris to JPL ephemeris files. The tiers validate library correctness across progressively wider date ranges corresponding to different JPL ephemeris files.

| Tier | Ephemeris | Date Range | Subjects |
|------|-----------|------------|----------|
| **core** | — | — | Hand-written essential tests with known values |
| **base** | DE440s | 1849–2150 | 11 temporal subjects |
| **medium** | DE440 | 1550–2650 (cumulative: includes base) | +5 subjects (16 total) |
| **extended** | DE441 | −13200–17191 (cumulative: includes all) | +9 subjects (25 total) |

---

## 1. Rebuild `tests/core/`

### 1.1 Current State (keep as-is)

These 11 files (7,207 lines) are well-written and stay unchanged:

| File | Lines | Coverage |
|------|-------|----------|
| `test_astrological_subject.py` | 1997 | AstrologicalSubjectFactory tropical (Johnny Depp), factory methods, edge cases, DST, Arabic Parts, Vertex, fixed stars, TNOs, error handling |
| `test_astrological_subject_jyotish.py` | 417 | Sidereal/Lahiri/Whole Sign (Johnny Depp) |
| `test_json_dump.py` | 104 | `model_dump_json()` serialization |
| `test_context_serializer.py` | 1237 | `to_context()` dispatcher, all 14 converter functions, XML output |
| `test_planetary_positions.py` | 426 | Data-driven planet positions (temporal + geographic subjects) |
| `test_houses_positions.py` | 449 | Data-driven house cusps (temporal + geographic subjects) |
| `test_arabic_parts.py` | 710 | Pars Fortunae/Spiritus/Amoris/Fidei formulas, day/night, sidereal, geographic edge cases |
| `test_moon_phase_details_factory_mocked.py` | 615 | MoonPhaseDetailsFactory with mocked Swiss Ephemeris |
| `test_moon_phase_historical_verification.py` | 1202 | ~230 known phase moments (2001–2040) from AstroPixels/NASA |
| `conftest.py` | 50 | Position comparison helpers (currently unused) |
| `__init__.py` | 0 | Package marker |

### 1.2 New Files to Add

16 new test files covering all library functionality not yet in `tests/core/`:

#### Aspects

| File | What it tests |
|------|---------------|
| `test_aspects.py` | `AspectsFactory.single_chart_aspects()` and `dual_chart_aspects()` with known expected values for Johnny Depp natal and John/Yoko synastry. Assert specific aspect pairs, orbs, movements. Import expected data from `data/expected_natal_aspects.py` and `data/expected_synastry_aspects.py`. |

#### Charts & SVG

| File | What it tests |
|------|---------------|
| `test_chart_data_factory.py` | `ChartDataFactory` — all 6 chart types (natal, synastry, transit, composite, single return, dual return). Element/quality distributions sum to 100%. Serialization roundtrip. Active points/aspects customization. |
| `test_chart_drawer.py` | `ChartDrawer` — SVG golden-file regression. Generate SVGs for all chart types × themes (classic, dark, dark-high-contrast, light, black-and-white) × options (wheel-only, aspect-grid-only, external view, minified). Compare line-by-line against baselines in `charts/svg/`. |
| `test_draw_planets.py` | `draw_planets()` function — unit tests with mock chart data. Planet glyph positioning, retrograde markers, degree labels. |
| `test_lunar_phase_svg.py` | Lunar phase SVG rendering — golden-file regression against baseline. |

#### Reports

| File | What it tests |
|------|---------------|
| `test_report.py` | `ReportGenerator` — golden-file snapshots for natal (Johnny Depp), synastry (John/Yoko), composite, solar return, transit reports. Full text comparison against `.txt` files in `reports/snapshots/`. Section presence, retrograde markers, aspect symbols, element/quality percentages. |

#### Factories

| File | What it tests |
|------|---------------|
| `test_composite_subject.py` | `CompositeSubjectFactory` — midpoint calculations with known values for John/Yoko. Commutativity (A+B = B+A). Composite with self equals natal. Incompatible config validation errors. |
| `test_planetary_return.py` | `PlanetaryReturnFactory` — offline solar/lunar returns. Sun position matches natal (< 0.1°). Yearly succession. Lunar cycle period (~27.3 days). Validation errors for invalid inputs. |
| `test_transits.py` | `TransitsTimeRangeFactory` — transit detection with known date range. Custom points/aspects. Empty data code path. |
| `test_ephemeris_data.py` | `EphemerisDataFactory` — daily/hourly generation. Planetary movement rates (Sun ~1°/day, Moon ~13°/day). Chronological ordering. Max limits. |
| `test_relationship_score.py` | `RelationshipScoreFactory` — score calculation for John/Yoko. Score description boundaries (6 categories). All evaluation methods (sun-sun, sun-moon, etc.). Score breakdown structure. |

#### Infrastructure

| File | What it tests |
|------|---------------|
| `test_utilities.py` | All ~20 utility functions — `calculate_position`, `calculate_moon_phase`, circular sort/mean, CSS inlining, Julian conversion, floating-point cusp boundary regression, polar latitude capping. |
| `test_settings.py` | `load_settings_mapping`, `load_language_settings`, `get_translations` with language overrides (EN, IT, CN, FR, ES). |
| `test_backward_compatibility.py` | `AstrologicalSubject`, `KerykeionChartSVG`, `NatalAspects`, `SynastryAspects` — all emit `DeprecationWarning`. `kr_types` module aliases. Full legacy pipeline (`makeTemplate`, `makeSVG`). |
| `test_fetch_geonames.py` | `@pytest.mark.online` — Roma lookup, error handling with mocks, cache configuration. |

### 1.3 Data & Golden Files

```
tests/core/
├── data/
│   └── expected_astrological_subjects.py    # EXISTS — Johnny Depp tropical + jyotish
├── aspects/
│   ├── expected_natal_aspects.py            # NEW — known natal aspect values
│   └── expected_synastry_aspects.py         # NEW — known synastry aspect values
├── charts/
│   ├── compare_svg_lines.py                 # NEW — SVG line-by-line comparison utility
│   └── svg/                                 # NEW — golden SVG baselines
│       ├── natal_classic.svg
│       ├── natal_dark.svg
│       ├── synastry_classic.svg
│       ├── transit_classic.svg
│       ├── composite_classic.svg
│       ├── ... (types × themes × options)
│       └── lunar_phase.svg
└── reports/
    └── snapshots/                           # NEW — golden report text files
        ├── natal_johnny_depp.txt
        ├── synastry_john_yoko.txt
        ├── composite_john_yoko.txt
        ├── solar_return_johnny_depp.txt
        └── transit_johnny_depp.txt
```

### 1.4 Rebuild `conftest.py`

Replace the current 50-line conftest with a more useful one:

- **Canonical subject fixtures** (session-scoped): `johnny_depp`, `john_lennon`, `yoko_ono`, `paul_mccartney` — created offline with `suppress_geonames_warning=True`
- **Position comparison helpers**: `assert_position_equal`, `assert_positions_match` (keep existing)
- **SVG comparison helper**: `assert_svg_matches_baseline(generated, baseline_path)`
- **Report comparison helper**: `assert_report_matches_snapshot(generated, snapshot_path)`
- **Tolerance constants**: `POSITION_TOLERANCE`, `SPEED_TOLERANCE`, `DECLINATION_TOLERANCE`
- **`@pytest.mark.online`** marker registration

### 1.5 Design Principles

1. **Self-contained**: Each test file creates its own subjects inline or uses conftest fixtures. No dependency on other test files.
2. **Offline by default**: All tests use `suppress_geonames_warning=True` with explicit coordinates. Only `test_fetch_geonames.py` hits the network.
3. **Golden-file regression**: SVGs compared line-by-line against baselines. Reports compared against text snapshots. Regeneration scripts provided.
4. **Known-value assertions**: Core tests assert specific numerical values, providing regression protection during the Swiss Ephemeris → JPL migration.
5. **Fast execution**: Core tests should complete in < 30 seconds total.

---

## 2. Tier Infrastructure

### 2.1 Add `"tier"` Field to `test_subjects_matrix.py`

Add a `"tier"` key to each entry in `TEMPORAL_SUBJECTS`:

```python
# Base tier (DE440s: 1849–2150) — 11 subjects
"industrial_1850":            {"tier": "base", ...}
"einstein_1879":              {"tier": "base", ...}
"ww1_start_1914":             {"tier": "base", ...}
"yoko_ono_1933":              {"tier": "base", ...}
"john_lennon_1940":           {"tier": "base", ...}
"paul_mccartney_1942":        {"tier": "base", ...}
"johnny_depp_1963":           {"tier": "base", ...}
"millennium_2000":            {"tier": "base", ...}
"equinox_2020":               {"tier": "base", ...}
"future_2050":                {"tier": "base", ...}
"future_2100":                {"tier": "base", ...}

# Medium tier (DE440: 1550–2650) — 5 additional subjects
"galileo_1564":               {"tier": "medium", ...}
"newton_1643":                {"tier": "medium", ...}
"enlightenment_1750":         {"tier": "medium", ...}
"american_independence_1776": {"tier": "medium", ...}
"future_2200":                {"tier": "medium", ...}

# Extended tier (DE441: −13200–17191) — 9 additional subjects
"ancient_500bc":              {"tier": "extended", ...}
"ancient_200bc":              {"tier": "extended", ...}
"roman_100ad":                {"tier": "extended", ...}
"late_antiquity_400":         {"tier": "extended", ...}
"early_medieval_800":         {"tier": "extended", ...}
"high_medieval_1100":         {"tier": "extended", ...}
"late_medieval_1300":         {"tier": "extended", ...}
"early_renaissance_1450":     {"tier": "extended", ...}
"columbus_1492":              {"tier": "extended", ...}
```

Add helper constants and function:

```python
BASE_SUBJECT_IDS = [k for k, v in TEMPORAL_SUBJECTS.items() if v["tier"] == "base"]
MEDIUM_SUBJECT_IDS = [k for k, v in TEMPORAL_SUBJECTS.items() if v["tier"] in ("base", "medium")]
EXTENDED_SUBJECT_IDS = list(TEMPORAL_SUBJECTS.keys())  # all

def get_subjects_for_tier(tier: str) -> dict:
    """Return subjects for a tier (cumulative)."""
    if tier == "base":
        return {k: v for k, v in TEMPORAL_SUBJECTS.items() if v["tier"] == "base"}
    elif tier == "medium":
        return {k: v for k, v in TEMPORAL_SUBJECTS.items() if v["tier"] in ("base", "medium")}
    else:  # extended
        return TEMPORAL_SUBJECTS
```

### 2.2 Add Tier Filtering to `tests/conftest.py`

```python
def pytest_addoption(parser):
    parser.addoption(
        "--tier",
        action="store",
        default=None,
        choices=["base", "medium", "extended"],
        help="Run only tests for the specified ephemeris tier (cumulative)",
    )

def pytest_collection_modifyitems(config, items):
    tier = config.getoption("--tier")
    if tier is None:
        return

    from tests.data.test_subjects_matrix import get_subjects_for_tier
    allowed_ids = set(get_subjects_for_tier(tier).keys())

    # Filter parametrized tests whose node ID contains a subject ID
    # that is NOT in the allowed set for this tier
    skip = pytest.mark.skip(reason=f"Subject not in tier '{tier}'")
    for item in items:
        node_id = item.nodeid
        for subject_id in TEMPORAL_SUBJECTS:
            if subject_id in node_id and subject_id not in allowed_ids:
                item.add_marker(skip)
                break
```

### 2.3 Register Markers

In `pyproject.toml` under `[tool.pytest.ini_options]`:

```toml
markers = [
    "online: tests requiring network access (GeoNames API)",
    "core: hand-written essential tests with known values",
    "base: DE440s tier (1849-2150)",
    "medium: DE440 tier (1550-2650, cumulative)",
    "extended: DE441 tier (full range, cumulative)",
]
```

### 2.4 Poe Tasks

```toml
[tool.poe.tasks."test:core"]
cmd = "pytest tests/core/ -v -m 'not online'"
help = "Run core hand-written tests (offline only)"

[tool.poe.tasks."test:base"]
cmd = "pytest tests/ --tier=base -v -m 'not online'"
help = "Run base tier tests (DE440s: 1849-2150)"

[tool.poe.tasks."test:medium"]
cmd = "pytest tests/ --tier=medium -v -m 'not online'"
help = "Run medium tier tests (DE440: 1550-2650, cumulative)"

[tool.poe.tasks."test:extended"]
cmd = "pytest tests/ --tier=extended -v -m 'not online'"
help = "Run extended tier tests (DE441: full range, cumulative)"

[tool.poe.tasks."test:online"]
cmd = "pytest tests/ -v -m 'online'"
help = "Run online-only tests (GeoNames API)"
```

---

## 3. Golden-File Report Snapshots

### 3.1 Coverage

Every temporal subject gets a full-text golden snapshot for the natal report. Additional chart types get snapshots for canonical subjects:

| Snapshot File | Subject | Chart Type |
|---------------|---------|------------|
| `natal_johnny_depp.txt` | Johnny Depp | Natal |
| `natal_john_lennon.txt` | John Lennon | Natal |
| `natal_yoko_ono.txt` | Yoko Ono | Natal |
| `synastry_john_yoko.txt` | John + Yoko | Synastry |
| `composite_john_yoko.txt` | John + Yoko | Composite |
| `solar_return_johnny_depp.txt` | Johnny Depp | Solar Return |
| `transit_johnny_depp.txt` | Johnny Depp | Transit |
| `natal_{subject_id}.txt` | Each temporal subject | Natal |

### 3.2 Generation

A regeneration script (or poe task) generates all golden files:

```toml
[tool.poe.tasks."regenerate:core-snapshots"]
cmd = "python scripts/regenerate_core_snapshots.py"
help = "Regenerate golden-file report snapshots for tests/core/"
```

### 3.3 Test Pattern

```python
def test_natal_report_johnny_depp(johnny_depp):
    report = ReportGenerator(johnny_depp).get_full_report()
    snapshot_path = SNAPSHOTS_DIR / "natal_johnny_depp.txt"
    assert report == snapshot_path.read_text(), (
        f"Report mismatch. Regenerate with: poe regenerate:core-snapshots"
    )
```

---

## 4. Implementation Order

| Step | Action | Est. Lines |
|------|--------|------------|
| **1** | Rebuild `tests/core/conftest.py` with fixtures + helpers | ~120 |
| **2** | Add `test_aspects.py` + expected data files | ~300 |
| **3** | Add `test_chart_data_factory.py` | ~400 |
| **4** | Add `test_chart_drawer.py` + SVG baselines + comparison utility | ~600 + baselines |
| **5** | Add `test_draw_planets.py` | ~500 |
| **6** | Add `test_lunar_phase_svg.py` | ~60 |
| **7** | Add `test_report.py` + report snapshots | ~300 + snapshots |
| **8** | Add `test_composite_subject.py` | ~250 |
| **9** | Add `test_planetary_return.py` | ~300 |
| **10** | Add `test_transits.py` | ~150 |
| **11** | Add `test_ephemeris_data.py` | ~200 |
| **12** | Add `test_relationship_score.py` | ~250 |
| **13** | Add `test_utilities.py` | ~200 |
| **14** | Add `test_settings.py` | ~80 |
| **15** | Add `test_backward_compatibility.py` | ~250 |
| **16** | Add `test_fetch_geonames.py` (`@pytest.mark.online`) | ~60 |
| **17** | Add `"tier"` field to `test_subjects_matrix.py` + helpers | ~50 |
| **18** | Add tier filtering to `tests/conftest.py` | ~40 |
| **19** | Update `pyproject.toml` (markers + poe tasks) | ~30 |
| **20** | Run `poe test:core` — fix any failures | — |
| **21** | Run `poe test:base` — verify tier filtering works | — |

**Total estimated new code: ~3,500+ lines** (excluding golden files)

---

## 5. Canonical Test Subjects

All core tests use these subjects (created offline):

| Name | Year | Month | Day | Hour | Min | City | Nation | Lat | Lng |
|------|------|-------|-----|------|-----|------|--------|-----|-----|
| Johnny Depp | 1963 | 6 | 9 | 0 | 0 | Owensboro | US | 37.7742 | -87.1133 |
| John Lennon | 1940 | 10 | 9 | 18 | 30 | Liverpool | GB | 53.4084 | -2.9916 |
| Yoko Ono | 1933 | 2 | 18 | 20 | 30 | Tokyo | JP | 35.6762 | 139.6503 |
| Paul McCartney | 1942 | 6 | 18 | 14 | 0 | Liverpool | GB | 53.4084 | -2.9916 |

---

## 6. Notes

- The exported tests in `/Users/giacomo/dev/tests/` are **outdated** and will NOT be used. The current `tests/core/` files (which are improved versions) are the starting point.
- Online-dependent tests (`test_fetch_geonames.py`) are marked `@pytest.mark.online` and excluded from default `test:core` runs.
- The `test_planetary_positions.py` and `test_houses_positions.py` files depend on generated expected data (`tests/data/expected_positions.py`). They gracefully skip if the data hasn't been generated.
- The `test_moon_phase_historical_verification.py` is marked as "TEMPORARY" in its docstring but is kept because it provides valuable regression data (230 known phase moments from NASA/AstroPixels).
- All the golden-files must be regenerable with a set of "regenerate_*" scripts, similar to the existing regenerate_* files
