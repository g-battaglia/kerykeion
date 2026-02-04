---
title: 'Migration Guide v4 to v5'
description: 'Step-by-step instructions to migrate your code from Kerykeion v4 to v5'
category: 'Getting Started'
tags: ['docs', 'migration', 'v4', 'v5', 'upgrade']
order: 2
---

# Migration Guide: v4 to v5

This guide provides comprehensive instructions for migrating your code from Kerykeion v4 to v5. The v5 release introduces a new factory-based architecture that provides better separation of concerns, improved type safety, and more flexibility.

## Quick Reference

| v4 (Deprecated) | v5 (Current) |
|:----------------|:-------------|
| `AstrologicalSubject()` | `AstrologicalSubjectFactory.from_birth_data()` |
| `KerykeionChartSVG()` | `ChartDataFactory` + `ChartDrawer` |
| `NatalAspects()` | `AspectsFactory.single_chart_aspects()` |
| `SynastryAspects()` | `AspectsFactory.dual_chart_aspects()` |
| `relationship_score()` | `RelationshipScoreFactory` |
| `kerykeion.kr_types` | `kerykeion.schemas` |
| `mean_node`, `true_node` | `mean_north_lunar_node`, `true_north_lunar_node` |

## Breaking Changes

### 1. Subject Creation

**v4 (Deprecated):**
```python
from kerykeion import AstrologicalSubject

subject = AstrologicalSubject(
    "John", 1990, 1, 1, 12, 0,
    city="London", nat="GB"
)
```

**v5 (Current):**
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
from kerykeion import AstrologicalSubject, KerykeionChartSVG

subject = AstrologicalSubject("John", 1990, 1, 1, 12, 0, "London", "GB")
chart = KerykeionChartSVG(subject)
chart.makeSVG()
```

**v5 (Current):**
```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

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
from kerykeion import NatalAspects, SynastryAspects

natal_aspects = NatalAspects(subject)
synastry_aspects = SynastryAspects(subject1, subject2)

# Accessing aspects
for aspect in natal_aspects.relevant_aspects:
    print(aspect)
```

**v5 (Current):**
```python
from kerykeion import AspectsFactory

# Single chart (natal, composite, return)
natal_result = AspectsFactory.single_chart_aspects(subject)

# Dual chart (synastry, transit)
synastry_result = AspectsFactory.dual_chart_aspects(subject1, subject2)

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
| `from kerykeion.kr_types.kr_literals import Planet` | `from kerykeion.schemas.kr_literals import AstrologicalPoint` |
| `from kerykeion.kr_types import KerykeionException` | `from kerykeion.schemas import KerykeionException` |

### 6. Type Aliases

The `Planet` and `AxialCusps` types are now unified:

```python
# v4
from kerykeion.kr_types.kr_literals import Planet, AxialCusps

# v5 (recommended)
from kerykeion.schemas.kr_literals import AstrologicalPoint

# v5 (aliases still available for transition)
from kerykeion.schemas import Planet, AxialCusps  # Aliases
```

### 7. Removed Parameters

| Parameter | Status | Replacement |
|:----------|:-------|:------------|
| `disable_chiron` | Removed | Use `active_points` to exclude |
| `disable_chiron_and_lilith` | Removed | Use `active_points` to exclude |
| `new_settings_file` | Removed | Use `language_pack` parameter |

## Backward Compatibility Layer

For gradual migration, v5 includes a compatibility layer in `kerykeion.backword`:

```python
# These still work but emit DeprecationWarning
from kerykeion import AstrologicalSubject, KerykeionChartSVG, NatalAspects

subject = AstrologicalSubject(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

# Old node properties still work via wrapper
print(subject.mean_node)  # Maps to mean_north_lunar_node
```

> **Warning:** The backward compatibility layer will be **removed in v6.0**. Plan to migrate your code before then.

## Step-by-Step Migration

### Step 1: Update Imports

```python
# Old
from kerykeion import AstrologicalSubject, KerykeionChartSVG

# New
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
```

### Step 2: Update Subject Creation

```python
# Old
subject = AstrologicalSubject("John", 1990, 1, 1, 12, 0, "London", "GB")

# New
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)
```

### Step 3: Update Chart Generation

```python
# Old
chart = KerykeionChartSVG(subject)
chart.makeSVG()

# New
chart_data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(chart_data=chart_data)
drawer.save_svg(output_path=Path("output"), filename="chart")
```

### Step 4: Update Lunar Node References

```python
# Old
mean_node = subject.mean_node

# New
mean_node = subject.mean_north_lunar_node
```

### Step 5: Update Aspect Access

```python
# Old
aspects = NatalAspects(subject)
for a in aspects.relevant_aspects:
    print(a)

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
| **v5.x** | Current - Backward compatibility available |
| **v6.0** | Future - All deprecated items will be removed |

## Getting Help

If you encounter issues during migration:

1. Check the [Troubleshooting & FAQ](/content/docs/faq) page
2. Review the [API documentation](/content/docs/)
3. Open an issue on [GitHub](https://github.com/g-battaglia/kerykeion/issues)
