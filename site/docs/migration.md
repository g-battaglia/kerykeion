---
title: 'Migration Guide (v4/v5 to v6)'
description: 'Step-by-step instructions to migrate your code from Kerykeion v4/v5 to v6'
category: 'Getting Started'
tags: ['docs', 'migration', 'v4', 'v5', 'v6', 'upgrade']
order: 2
---

# Migration Guide: v4/v5 to v6

This guide provides comprehensive instructions for migrating your code from Kerykeion v4 or v5 to v6. The v5 release introduced a factory-based architecture; v6 removes the v4 backward compatibility layer entirely and adds advanced calculation modules.

## Quick Reference

| v4 (Removed in v6) | v6 (Current) |
|:----------------|:-------------|
| `AstrologicalSubject()` | `AstrologicalSubjectFactory.from_birth_data()` |
| `KerykeionChartSVG()` | `ChartDataFactory` + `ChartDrawer` |
| `NatalAspects()` | `AspectsFactory.single_chart_aspects()` |
| `SynastryAspects()` | `AspectsFactory.dual_chart_aspects()` |
| `relationship_score()` | `RelationshipScoreFactory` |
| `kerykeion.kr_types` | `kerykeion.schemas` |
| `mean_node`, `true_node` | `mean_north_lunar_node`, `true_north_lunar_node` |

> **Note:** `kerykeion.kr_types` was a deprecated shim throughout v5 and is **removed in v6**. Import from `kerykeion.schemas` instead.

## Breaking Changes

### 1. Subject Creation

**v4 (Deprecated):**
```python
# doc-snippet: no-run — legacy v4 example (removed in v6)
from kerykeion import AstrologicalSubject

subject = AstrologicalSubject(
    "John", 1990, 1, 1, 12, 0,
    city="London", nat="GB"
)
```

**v6 (Current):**
```python
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)
```

Key differences:
- Use factory method `from_birth_data()` instead of direct instantiation
- `nat` parameter renamed to `nation`
- Recommended: Use offline mode with explicit coordinates

### 2. Chart Generation (Two-Step Process)

**v4 (Deprecated):**
```python
# doc-snippet: no-run — legacy v4 example (removed in v6)
from kerykeion import AstrologicalSubject, KerykeionChartSVG

subject = AstrologicalSubject("John", 1990, 1, 1, 12, 0, "London", "GB")
chart = KerykeionChartSVG(subject)
chart.makeSVG()
```

**v6 (Current):**
```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.charts.drawer import ChartDrawer

# Step 1: Create subject
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

# Step 2: Generate chart data
chart_data = ChartDataFactory.create_natal_chart_data(subject)

# Step 3: Render visualization
drawer = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
drawer.save_svg(output_path=output_dir, filename="john-natal")
```

The new architecture separates:
- **Data calculation** (`ChartDataFactory`) - Computes all astrological data
- **Visualization** (`ChartDrawer`) - Renders the SVG chart

### 3. Aspects Calculation

**v4 (Deprecated):**
```python
# doc-snippet: no-run — legacy v4 example (removed in v6)
from kerykeion import NatalAspects, SynastryAspects

natal_aspects = NatalAspects(subject)
synastry_aspects = SynastryAspects(subject1, subject2)

# Accessing aspects
for aspect in natal_aspects.relevant_aspects:
    print(aspect)
```

**v6 (Current):**
```python
from kerykeion import AspectsFactory

# Single chart (natal, composite, return)
natal_result = AspectsFactory.single_chart_aspects(subject)

# Dual chart (synastry, transit) — needs a second subject
subject2 = AstrologicalSubjectFactory.from_birth_data(
    "Jane", 1992, 5, 15, 10, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
    online=False
)
synastry_result = AspectsFactory.dual_chart_aspects(subject, subject2)

# Accessing aspects (unified list)
for aspect in natal_result.aspects:
    print(aspect)
```

Key changes:
- `relevant_aspects` and `all_aspects` unified into single `aspects` list
- Factory methods instead of class instantiation

### 4. Lunar Node Naming

All lunar node properties have been renamed for clarity:

| v4 Property | v5 Property |
|:------------|:------------|
| `subject.mean_node` | `subject.mean_north_lunar_node` |
| `subject.true_node` | `subject.true_north_lunar_node` |
| `subject.mean_south_node` | `subject.mean_south_lunar_node` |
| `subject.true_south_node` | `subject.true_south_lunar_node` |

In active_points lists:

| v4 String | v5 String |
|:----------|:----------|
| `"Mean_Node"` | `"Mean_North_Lunar_Node"` |
| `"True_Node"` | `"True_North_Lunar_Node"` |

### 5. Import Path Changes

| v4 Import | v5 Import |
|:----------|:----------|
| `from kerykeion.kr_types import *` | `from kerykeion.schemas import *` |
| `from kerykeion.kr_types.kr_literals import Planet` | `from kerykeion.schemas.literals import AstrologicalPoint` |
| `from kerykeion.kr_types import KerykeionException` | `from kerykeion.schemas import KerykeionException` |

#### v5 → v6 module paths

v6 reorganised the package so that every domain lives in its own directory. **If you import only from the top level — `from kerykeion import X` — nothing changes.** These paths matter only if you imported a module directly.

| v5 module | v6 module |
|:----------|:----------|
| `kerykeion.astrological_subject_factory` | `kerykeion.astrological_subject.factory` |
| `kerykeion.chart_data_factory` | `kerykeion.chart_data.factory` |
| `kerykeion.composite_subject_factory` | `kerykeion.composite_subject.factory` |
| `kerykeion.planetary_return_factory` | `kerykeion.planetary_returns.factory` |
| `kerykeion.transits_time_range_factory` | `kerykeion.transits.factory` |
| `kerykeion.relationship_score_factory` | `kerykeion.relationship_score.factory` |
| `kerykeion.relocated_chart_factory` | `kerykeion.relocated_chart.factory` |
| `kerykeion.ephemeris_data_factory` | `kerykeion.ephemeris_data.factory` |
| `kerykeion.context_serializer` | `kerykeion.context.serializer` |
| `kerykeion.fetch_geonames` | `kerykeion.geonames.fetcher` |
| `kerykeion.charts.chart_drawer` | `kerykeion.charts.drawer` |
| `kerykeion.charts.charts_utils` | `kerykeion.charts.utils` |
| `kerykeion.aspects.aspects_factory` | `kerykeion.aspects.factory` |
| `kerykeion.aspects.aspects_utils` | `kerykeion.aspects.utils` |
| `kerykeion.house_comparison.house_comparison_factory` | `kerykeion.house_comparison.factory` |
| `kerykeion.house_comparison.house_comparison_utils` | `kerykeion.house_comparison.utils` |
| `kerykeion.schemas.kr_models` | `kerykeion.schemas.models` |
| `kerykeion.schemas.kr_literals` | `kerykeion.schemas.literals` |
| `kerykeion.schemas.kerykeion_exception` | `kerykeion.schemas.exceptions` |
| `kerykeion.settings.kerykeion_settings` | `kerykeion.settings.loader` |
| `kerykeion.kr_types` (and submodules) | `kerykeion.schemas` |

Unchanged, because they became packages under the same name: `kerykeion.report`, `kerykeion.utilities`, `kerykeion.ephemeris_backend`, `kerykeion.motion`, `kerykeion.swisseph_setup`.

The same domain packages also renamed their internal factory module (`eclipses.eclipse_factory` → `eclipses.factory`, and the same for `lunations`, `midpoints`, `occultations`, `heliacal`, `planetary_nodes`, `planetary_phenomena`, `primary_directions`, `retrograde_stations`, `sign_ingresses`, `astro_cartography`, `fixed_stars`, `dignities`, `secondary_progressions`). Every one of these classes is also exported from `kerykeion` directly, which is the import worth switching to.

### 6. Type Aliases

The `Planet` and `AxialCusps` types were unified into `AstrologicalPoint`:

```python
# v4 (removed in v6)
# from kerykeion.kr_types.kr_literals import Planet, AxialCusps

# v6 (correct)
from kerykeion.schemas.literals import AstrologicalPoint
```

The v5 model aliases `NatalAspectsModel` and `SynastryAspectsModel` were also removed — use `SingleChartAspectsModel` and `DualChartAspectsModel` instead.

### 7. Removed Parameters

| Parameter | Status | Replacement |
|:----------|:-------|:------------|
| `disable_chiron` | Removed | Use `active_points` to exclude |
| `disable_chiron_and_lilith` | Removed | Use `active_points` to exclude |
| `new_settings_file` | Removed | Use `language_pack` parameter |

## What Changes in the Results

Everything above is about code that stops working: you get an `ImportError`, you fix the call, you move on. This section is about the opposite — code that keeps working and quietly returns **different numbers**.

It applies even if you were already using the v5 factory API correctly. Nothing raises, nothing warns; the output is simply not the same as before.

| What | v5 | v6 | What you see |
|:-----|:---|:---|:-------------|
| Default active points | 18 | 14 | Fewer points in charts and aspects |
| Default aspect orbs | conj/opp 10°, trine 8°, sextile 6°, square 5°, quintile 1° | conj/opp/trine/square 6°, sextile 5° | **Markedly fewer aspects**; quintiles disappear entirely |
| Orbs on non-natal charts | same defaults as natal | flat 3° (`PREDICTIVE_ACTIVE_ASPECTS`) | Transits, returns and progressions report far fewer aspects |
| Sun/Moon orb bonus | none | `+1.5°`, natal-family charts only | Slightly wider orbs for luminaries |
| Chart style | `"classic"` | `"modern"` | A different drawing, and a different filename |

These are deliberate v6 choices, not oversights. What follows is how to opt back into the old behaviour where you need continuity.

### Active points: 18 → 14

Four points left the default set: `Descendant`, `Imum_Coeli`, `True_South_Lunar_Node` and `Mean_Lilith`. They still exist — they are simply no longer computed unless you ask for them.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.settings import V5_DEFAULT_ACTIVE_POINTS

# v6 defaults: 14 points
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London", online=False,
)

# The v5 set, restored explicitly
subject_v5 = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London", online=False,
    active_points=V5_DEFAULT_ACTIVE_POINTS,
)

print(len(subject.active_points), len(subject_v5.active_points))
```

`V5_DEFAULT_ACTIVE_POINTS` is a frozen historical record: it will not track future changes to the default set. If you want the current defaults plus one point, build the list from `DEFAULT_ACTIVE_POINTS` instead.

### Aspect orbs

This is the largest silent change, and it has three separate parts. Expect **fewer** aspects after upgrading, not more.

**The default orbs shrank.** `DEFAULT_ACTIVE_ASPECTS` was rewritten:

| Aspect | v5 orb | v6 orb |
|:-------|-------:|-------:|
| conjunction | 10° | 6° |
| opposition | 10° | 6° |
| trine | 8° | 6° |
| sextile | 6° | 5° |
| square | 5° | 6° |
| quintile | 1° | *removed from the defaults* |

**Non-natal charts moved to a flat 3°.** In v5 every chart type used the same defaults. In v6 only the natal family (`Natal`, `Synastry`, `Composite`) uses `DEFAULT_ACTIVE_ASPECTS`; transits, returns and progressions use `PREDICTIVE_ACTIVE_ASPECTS`, which is 3° for all five aspects.

The difference is small on a natal chart and large everywhere else. On one sample chart: 38 natal aspects under v6 against 40 with the v5 orbs — but **19 transit aspects against 51**. If your code reads transits, returns or progressions, this is the change to look at first.

**Luminaries gained a 1.5° bonus — natal family only.** `DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS` widens aspects involving the Sun or the Moon. It applies *only* where `chart_type` is in the natal family; every other `create_*_chart_data` already uses no adjustment, so `point_orb_adjustments={}` is a no-op there.

To restore v5 orbs, pass the aspect list explicitly — this is the part `V5_DEFAULT_ACTIVE_POINTS` does *not* cover:

```python
from kerykeion import ChartDataFactory

V5_DEFAULT_ACTIVE_ASPECTS = [
    {"name": "conjunction", "orb": 10},
    {"name": "opposition", "orb": 10},
    {"name": "trine", "orb": 8},
    {"name": "sextile", "orb": 6},
    {"name": "square", "orb": 5},
    {"name": "quintile", "orb": 1},
]

# v6 defaults
chart_data = ChartDataFactory.create_natal_chart_data(subject)

# v5-equivalent orbs: the old aspect list, and no luminary bonus
chart_data_v5 = ChartDataFactory.create_natal_chart_data(
    subject,
    active_aspects=V5_DEFAULT_ACTIVE_ASPECTS,
    point_orb_adjustments={},
)

print(len(chart_data.aspects), len(chart_data_v5.aspects))
```

For a transit chart, pass the same `active_aspects` to `create_transit_chart_data` — there `point_orb_adjustments` is already empty, so only the aspect list matters.

`AspectsFactory.single_chart_aspects` applies no orb adjustment by default, so it and `ChartDataFactory` can disagree on the same subject unless you pass the same arguments to both.

### Chart style

`ChartDrawer` now defaults to `style="modern"`. The v5 drawing is still available, and the saved filename reflects the style (`"... - Classic.svg"` vs `"... - Modern.svg"`), so scripts that look for a fixed filename need updating either way.

```python
from kerykeion import ChartDrawer

drawer = ChartDrawer(chart_data, style="classic")  # the v5 look
svg = drawer.generate_svg_string()
```

Note that `external_view` only takes effect in the classic style.

## Backward Compatibility Layer (Removed in v6)

v5 included a compatibility layer in `kerykeion.backword` that allowed gradual migration. **This layer has been removed in v6.0.**

```python
# v5 ONLY (no longer works in v6):
# from kerykeion import AstrologicalSubject, KerykeionChartSVG, NatalAspects
# These imports now raise ImportError in v6.
```

> **Warning:** The backward compatibility layer has been **removed in v6.0**. The legacy imports (`AstrologicalSubject`, `KerykeionChartSVG`, `NatalAspects`, `SynastryAspects`) will raise `ImportError`. Use the factory-based API shown above.

## Step-by-Step Migration

### Step 1: Update Imports

```python
# Old (removed in v6)
# from kerykeion import AstrologicalSubject, KerykeionChartSVG

# New
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.charts.drawer import ChartDrawer
```

### Step 2: Update Subject Creation

```python
# Old (removed in v6)
# subject = AstrologicalSubject("John", 1990, 1, 1, 12, 0, "London", "GB")

# New
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)
```

### Step 3: Update Chart Generation

```python
# Old (removed in v6)
# chart = KerykeionChartSVG(subject)
# chart.makeSVG()

# New
chart_data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(chart_data=chart_data)
output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
drawer.save_svg(output_path=output_dir, filename="chart")
```

### Step 4: Update Lunar Node References

```python
# Old (removed in v6)
# mean_node = subject.mean_node

# New
mean_node = subject.mean_north_lunar_node
```

### Step 5: Update Aspect Access

```python
# Old (removed in v6)
# aspects = NatalAspects(subject)
# for a in aspects.relevant_aspects:
#     print(a)

# New
result = AspectsFactory.single_chart_aspects(subject)
for a in result.aspects:
    print(a)
```

## Automated Migration Script

Use this bash script to update common patterns:

```bash
#!/bin/bash
# Update lunar node references
find . -name "*.py" -type f -exec sed -i.bak \
    -e 's/\.mean_node/.mean_north_lunar_node/g' \
    -e 's/\.true_node/.true_north_lunar_node/g' \
    -e 's/\.mean_south_node/.mean_south_lunar_node/g' \
    -e 's/\.true_south_node/.true_south_lunar_node/g' \
    -e 's/"Mean_Node"/"Mean_North_Lunar_Node"/g' \
    -e 's/"True_Node"/"True_North_Lunar_Node"/g' \
    {} \;

echo "Migration complete. Review changes before committing."
```

> **Important:** Always review automated changes and test thoroughly.

## Migration Checklist

- [ ] Update imports to use new module paths
- [ ] Replace `AstrologicalSubject` with `AstrologicalSubjectFactory.from_birth_data()`
- [ ] Replace `KerykeionChartSVG` with `ChartDataFactory` + `ChartDrawer`
- [ ] Replace `NatalAspects` with `AspectsFactory.single_chart_aspects()`
- [ ] Replace `SynastryAspects` with `AspectsFactory.dual_chart_aspects()`
- [ ] Update lunar node property names
- [ ] Update `kr_types` imports to `schemas`
- [ ] Remove deprecated parameters (`disable_chiron`, etc.)
- [ ] Update aspect access from `relevant_aspects` to `aspects`
- [ ] Test all chart generation and data access

## Timeline

| Version | Status |
|:--------|:-------|
| **v5.x** | Legacy - Backward compatibility was available |
| **v6.0** | Current - All deprecated items have been removed |

## Getting Help

If you encounter issues during migration:

1. Check the [Troubleshooting & FAQ](/content/docs/faq) page
2. Review the [API documentation](/content/docs/)
3. Open an issue on [GitHub](https://github.com/g-battaglia/kerykeion/issues)

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
