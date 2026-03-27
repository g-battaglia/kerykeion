# Kerykeion v6.0 — Integration Test Report

> **Branch:** `tentative/v6`
> **Date:** 27 March 2026
> **Base:** `main` (v5.12.7, commit `bd60d88`)

---

## Merge Summary

All 15 feature branches were merged into `tentative/v6` in the recommended order.

| # | Branch | Merge Result | Conflicts |
|---|--------|-------------|-----------|
| 1 | `v6/feat/remove-backward-compat` | Fast-forward | None |
| 2 | `v6/feat/uranian-planets` | Auto-merge | None (auto-resolved kr_literals, kr_models) |
| 3 | `v6/feat/essential-dignities` | Auto-merge | None (auto-resolved factory, kr_models) |
| 4 | `v6/feat/nakshatra` | **Manual resolve** | `kr_models.py` (keep both dignity + nakshatra fields), `astrological_subject_factory.py` (keep both config flags + post-processing) |
| 5 | `v6/feat/planetary-phenomena` | Auto-merge | None |
| 6 | `v6/feat/eclipses` | **Manual resolve** | `__init__.py` (keep both import lines) |
| 7 | `v6/feat/planetary-nodes` | **Manual resolve** | `__init__.py` (same pattern) |
| 8 | `v6/feat/heliacal` | **Manual resolve** | `__init__.py` (same pattern) |
| 9 | `v6/feat/occultations` | **Manual resolve** | `__init__.py` (same pattern) |
| 10 | `v6/feat/davison-composite` | Auto-merge | None |
| 11 | `v6/feat/relocated-charts` | **Manual resolve** | `__init__.py` (same pattern) |
| 12 | `v6/feat/gauquelin` | **Manual resolve** | `kr_models.py` (add gauquelin_sector after nakshatra fields), `astrological_subject_factory.py` (add gauquelin config + post-processing) |
| 13 | `v6/feat/planetocentric` | Auto-merge | None |
| 14 | `v6/feat/heliocentric-returns` | Auto-merge | None |
| 15 | `v6/feat/transit-exactness` | Auto-merge | None |

### Post-merge fix
- **`kr_models.py` syntax fix:** The auto-resolve of gauquelin merge dropped a closing parenthesis on `nakshatra_lord` field. Fixed manually.

---

## Conflict Patterns

All conflicts follow two predictable patterns:

### Pattern 1: `__init__.py` import accumulation
Every standalone factory branch adds its import to the same "STANDALONE FACTORIES" section. Resolution: keep ALL import lines from both sides.

**Files affected:** `kerykeion/__init__.py` (import section + `__all__` list)
**Frequency:** 6 out of 15 merges
**Risk:** None — purely additive

### Pattern 2: `kr_models.py` / `astrological_subject_factory.py` field additions
Branches that add fields to `KerykeionPointModel` or config flags to `ChartConfiguration` conflict when merged after another branch that also adds fields at the same location.

**Files affected:** `kerykeion/schemas/kr_models.py`, `kerykeion/astrological_subject_factory.py`
**Frequency:** 2 out of 15 merges (nakshatra + gauquelin)
**Risk:** Low — but watch for missing closing parentheses in the auto-resolve

---

## Test Results

### New v6 Feature Tests: 171/171 PASSED

| Test File | Tests | Result |
|-----------|-------|--------|
| `test_uranian_planets.py` | 37 | PASSED |
| `test_dignities.py` | 21 | PASSED |
| `test_nakshatra.py` | 17 | PASSED |
| `test_planetary_phenomena.py` | 12 | PASSED |
| `test_eclipses.py` | 11 | PASSED |
| `test_planetary_nodes.py` | 8 | PASSED |
| `test_davison_composite.py` | 6 | PASSED |
| `test_relocated_chart.py` | 6 | PASSED |
| `test_heliacal.py` | 14 | PASSED |
| `test_occultations.py` | 13 | PASSED |
| `test_gauquelin.py` | 7 | PASSED |
| `test_planetocentric.py` | 6 | PASSED |
| `test_heliocentric_returns.py` | 6 | PASSED |
| `test_transit_exactness.py` | 7 | PASSED |
| **Total** | **171** | **ALL PASSED** |

### Full Regression Suite: 1472 passed, 3 failed, 22 skipped

```
FAILED tests/core/test_chart_drawer.py::TestNatalChart::test_natal_chart_classic
FAILED tests/core/test_chart_drawer.py::TestCompositeChart::test_composite_chart
FAILED tests/core/test_chart_parametrized.py::TestCrossCombinations::test_sidereal_theme_combinations[LAHIRI_strawberry]
```

### Failure Analysis

All 3 failures are in **SVG golden-file line count assertions**. These tests compare the number of lines in generated SVGs against a hardcoded expected count. The count changed because:

1. **Uranian planet SVG symbols** added 80 lines to each SVG template (8 planets × 10 lines each)
2. **Gauquelin sector placeholder** added ~4 lines to `chart.xml` and `wheel_only.xml`

**Impact:** None — these are test infrastructure issues, not functional regressions. The SVGs render correctly (verified with `qlmanage`).

**Fix:** Update the expected line counts in `test_chart_drawer.py` and `test_chart_parametrized.py` to reflect the new template sizes. This is a 3-line change.

### Non-SVG tests: 1472 PASSED (100%)

All calculation, aspect, model, serialization, and integration tests pass without any modification.

---

## Integration Verification

### Import check
```python
from kerykeion import (
    AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer,
    AspectsFactory, RelationshipScoreFactory, CompositeSubjectFactory,
    PlanetaryReturnFactory, EphemerisDataFactory, TransitsTimeRangeFactory,
    MoonPhaseDetailsFactory, HouseComparisonFactory, ReportGenerator,
    # New v6 factories
    PlanetaryPhenomenaFactory, EclipseFactory, PlanetaryNodesFactory,
    HeliacalFactory, OccultationFactory, RelocatedChartFactory,
)
# All imports successful
```

### Cross-feature test
```python
s = AstrologicalSubjectFactory.from_birth_data(
    "Full v6", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
    city="Rome", nation="IT", online=False,
    calculate_dignities=True,
    calculate_nakshatra=True,
    calculate_gauquelin=True,
    active_points=[..., "Cupido", "Hades", ...],  # Uranian planets
)
# Dignities + Nakshatra + Gauquelin + Uranian all work together
assert s.sun.essential_dignity is not None
assert s.moon.nakshatra is not None
assert s.mars.gauquelin_sector is not None
assert s.cupido is not None
```

---

## Remaining Work Before Release

1. **Update SVG golden-file line counts** in `test_chart_drawer.py` (3 test fixes)
2. **Version bump:** `pyproject.toml` → `version = "6.0.0"`
3. **CHANGELOG.md:** Add v6.0.0 entry
4. **MIGRATION_V5_TO_V6.md:** Create migration guide
5. **context_serializer.py:** Add XML serialization for new fields (dignity, nakshatra, gauquelin_sector)
6. **ROADMAP.md:** Mark v5.13-v5.17 items as DONE

---

## Branch Preservation

All 15 original feature branches are preserved and untouched:
```
v6/feat/remove-backward-compat
v6/feat/uranian-planets
v6/feat/essential-dignities
v6/feat/nakshatra
v6/feat/planetary-phenomena
v6/feat/eclipses
v6/feat/planetary-nodes
v6/feat/davison-composite
v6/feat/relocated-charts
v6/feat/heliacal
v6/feat/occultations
v6/feat/heliocentric-returns
v6/feat/gauquelin
v6/feat/planetocentric
v6/feat/transit-exactness
```

All milestone tags are preserved:
```
v6-milestone-remove-backward-compat
v6-milestone-uranian-planets
v6-milestone-essential-dignities
v6-milestone-nakshatra
v6-milestone-planetary-phenomena
v6-milestone-eclipses
v6-milestone-planetary-nodes
v6-milestone-davison-composite
v6-milestone-relocated-charts
v6-milestone-heliacal
v6-milestone-occultations
v6-milestone-heliocentric-returns
v6-milestone-gauquelin
v6-milestone-planetocentric
v6-milestone-transit-exactness
```
