# Kerykeion – Changelog (master → next)

**Release date:** 2025-08-20

## 🚀 Highlights
- **New factory-based API:** The library now revolves around factories and data models in `kerykeion.schemas`, making the API more consistent and easier to extend.
- **Aspects engine reworked:** `AspectsFactory` replaces the old `NatalAspects` and `SynastryAspects`, offering a unified interface for single-chart and dual-chart analysis.
- **Modern chart rendering:** New `ChartDrawer` creates clean SVG charts with multiple output options (`makeSVG`, `makeTemplate`, `makeWheelOnlySVG`, `makeWheelOnlyTemplate`, `makeAspectGridOnlySVG`, `makeAspectGridOnlyTemplate`), replacing the legacy `KerykeionChartSVG`.
- **New analysis tools:**
  - `HouseComparisonFactory` for comparing houses between two charts
  - `TransitsTimeRangeFactory` for generating transit moments across a period
  - `PlanetaryReturnFactory` with helpers for planetary returns (`next_return_from_year`, `next_return_from_month_and_year`, `next_return_from_iso_formatted_time`)
  - `ChartDataFactory` and `EphemerisDataFactory` to streamline data creation and ephemeris fetching
- **Schemas everywhere:** The old `kr_types` package is gone; models, literals and exceptions now live in `kerykeion.schemas`.

## 💥 Breaking Changes
- Removed `NatalAspects` and `SynastryAspects` → use `AspectsFactory` (legacy aliases `NatalAspectsModel` and `SynastryAspectsModel` are maintained for backward compatibility).
- Removed `AstrologicalSubject` → use `AstrologicalSubjectFactory`.
- Removed the `relationship_score` package and the `RelationshipScore` class → use `RelationshipScoreFactory`.
- Legacy modules removed: `ephemeris_data.py`, `transits_time_range.py`, `charts/kerykeion_chart_svg.py`.
- `kr_types` package moved to `schemas` → import everything from `kerykeion.schemas`.
- New constant `DEFAULT_AXIS_ORBIT` = 1: axis orbs are now explicitly defined (results may differ if you relied on defaults).

## ✨ Added
- `AspectsFactory`: unified aspects calculation (`single_chart_aspects`, `dual_chart_aspects`) with filters and dedicated axis orbs.
- `ChartDrawer`: generates SVG templates and wheels with multiple methods (`makeSVG`, `makeTemplate`, `makeWheelOnlySVG`, `makeWheelOnlyTemplate`, `makeAspectGridOnlySVG`, `makeAspectGridOnlyTemplate`).
- `PlanetaryReturnFactory`: helpers for planetary returns (`next_return_from_year`, `next_return_from_month_and_year`, `next_return_from_iso_formatted_time`).
- `TransitsTimeRangeFactory`: generate transits within a date range.
- `ChartDataFactory`: multiple creators (`create_chart_data`, `create_synastry_chart_data`, `create_return_chart_data`, …).
- `EphemerisDataFactory`: fetches ephemeris, also convertible into subject models.
- `HouseComparisonFactory`: compare house placements between two charts.
- Schemas package: unified home for models, literals, exceptions, and settings.
- Backward compatibility aliases: `NatalAspectsModel` and `SynastryAspectsModel` maintained as aliases to `SingleChartAspectsModel` and `DualChartAspectsModel`.
- Legacy settings presets: curated defaults for points, aspects and colors under `settings/legacy`.
- New configuration constants: `DEFAULT_ACTIVE_POINTS` and `DEFAULT_AXIS_ORBIT` for consistent defaults.
- Enhanced caching system with `@functools.lru_cache` for settings operations.

## 🔧 Changed
- `kerykeion/__init__.py` now exports all public factories, models, and settings.
- Aspect utilities now rely on `schemas` models and support composite and return subjects.
- Settings: `merge_settings` is now cached with `@functools.lru_cache`; `settings.__init__` exports `KerykeionSettingsModel` and `get_settings`.
- `fetch_geonames.py`: improved docs and caching for coordinates and timezones.
- Report module aligned with the new factories and models.

## 🗑 Removed
- `natal_aspects.py`, `synastry_aspects.py`, `transits_time_range.py`
- `astrological_subject.py` and `charts/kerykeion_chart_svg.py`
- `kr_types` (moved to `schemas`)
- `relationship_score` (replaced by `RelationshipScoreFactory`)
- Old enums module (functionality moved to `schemas/kr_literals.py`)

## 🔀 Moved/Renamed
- `kr_types/chart_types.py` → `schemas/chart_types.py`
- `kr_types/kerykeion_exception.py` → `schemas/kerykeion_exception.py`
- `kr_types/kr_literals.py` → `schemas/kr_literals.py`
- `kr_types/kr_models.py` → `schemas/kr_models.py`
- `kr_types/settings_models.py` → `schemas/settings_models.py`

## 🛠 Migration Guide

### Imports and core types
- **Before:** `from kerykeion.astrological_subject import AstrologicalSubject`
  
  **After:**  `from kerykeion import AstrologicalSubjectFactory`
- **Before:** `from kerykeion.kr_types import ...`
  
  **After:**  `from kerykeion.schemas import ...`

### Aspects
- **Before:**
    ```python
    from kerykeion.aspects import NatalAspects, SynastryAspects
    natal = NatalAspects(subject)
    syn = SynastryAspects(first, second)
    ```
- **After:**
    ```python
    from kerykeion import AspectsFactory
    natal = AspectsFactory.single_chart_aspects(subject)
    syn   = AspectsFactory.dual_chart_aspects(first, second)
    ```

Note: The new factory methods support multiple subject types including `AstrologicalSubjectModel`, `CompositeSubjectModel`, and `PlanetReturnModel`.

### Relationship score
- **Before:** `from kerykeion.relationship_score.relationship_score import RelationshipScore`
- **After:**  `from kerykeion import RelationshipScoreFactory`

### Chart drawing
- **Before:** `from kerykeion.charts.kerykeion_chart_svg import KerykeionChartSVG`
- **After:**  `from kerykeion import ChartDrawer`

Note: `ChartDrawer` requires pre-computed chart data from `ChartDataFactory`.

### Chart data creation (New)
- **New:** `from kerykeion import ChartDataFactory`
  ```python
  chart_data = ChartDataFactory.create_chart_data(subject)
  drawer = ChartDrawer(chart_data)
  ```

### Planetary returns
- **New:** `from kerykeion import PlanetaryReturnFactory`

### Transits in a time range
- **New:** `from kerykeion import TransitsTimeRangeFactory`

### Settings
- Import from `kerykeion.settings` (e.g., `KerykeionSettingsModel`, `get_settings`).
- Use new constants: `DEFAULT_ACTIVE_POINTS`, `DEFAULT_AXIS_ORBIT = 1`.
- Note: Stricter axis orb defaults may produce different aspect results compared to previous versions.

## 🧰 Utility Scripts
- `regenerate_expected_aspects.py` – rebuild natal aspect fixtures to match new API
- `regenerate_synastry_aspects.py` – rebuild synastry aspect fixtures to match new API  
- `regenerate_synastry_from_test.py` – regenerate synastry data from existing tests
- `regenerate_test_charts.py` – refresh test charts with updated configurations
- `test_markdown_snippets.py` – validate code examples in documentation

## ✅ Tests
- Updated across aspects, charts, settings, and reports.
- Fixtures regenerated to match new axis orb defaults and active points.

## 📋 Notes
- **API Stability**: Legacy type aliases (`NatalAspectsModel`, `SynastryAspectsModel`) are provided for backward compatibility during the transition period.
- **Chart Rendering**: `ChartDrawer` requires pre-computed data from `ChartDataFactory`, promoting better separation of concerns between calculation and visualization.
- **Orb Changes**: The new `DEFAULT_AXIS_ORBIT = 1` may produce different results than previous versions for aspects involving chart axes (ASC, MC, DSC, IC).
- **Settings Caching**: All settings functions now use `@functools.lru_cache` for improved performance in applications that create multiple charts.
