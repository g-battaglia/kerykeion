# Kerykeion v4 → v5 Migration Guide

This guide collects all breaking changes and step-by-step instructions to migrate your code from Kerykeion v4 to v5. It replaces the inlined migration notes that previously lived in README.md.

If you’re just looking for what’s new in v5, see the “Kerykeion v5.0 – What's New” section in README.md.

---

### 🚨 Breaking Changes

#### 1. Removed Legacy Classes

The following classes have been completely removed and must be replaced:

| Removed (v4)           | Replacement (v5)                               |
| ---------------------- | ---------------------------------------------- |
| `AstrologicalSubject`  | `AstrologicalSubjectFactory.from_birth_data()` |
| `KerykeionChartSVG`    | `ChartDrawer` + `ChartDataFactory`             |
| `NatalAspects`         | `AspectsFactory.single_chart_aspects()`        |
| `SynastryAspects`      | `AspectsFactory.dual_chart_aspects()`          |
| `relationship_score()` | `RelationshipScoreFactory`                     |

Note: The `kerykeion.backword` module provides temporary wrappers for `AstrologicalSubject` and `KerykeionChartSVG` with deprecation warnings. These will be removed in v6.0.

#### 2. Import Changes

Module structure has been completely reorganized:

Old imports (v4):

```python
from kerykeion import AstrologicalSubject, KerykeionChartSVG
from kerykeion.kr_types import KerykeionException
from kerykeion.kr_types.kr_literals import Planet, AxialCusps
```

New imports (v5):

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
from kerykeion.schemas import KerykeionException
from kerykeion.schemas.kr_literals import AstrologicalPoint
```

Backward compatibility (v5 only, removed in v6.0):

```python
# Old kr_types imports still work with deprecation warnings
from kerykeion.kr_types import Planet, AxialCusps  # Shows warning
from kerykeion.schemas import Planet, AxialCusps    # Works, no warning
```

#### 3. Type Aliases Unified

Old (v4): `Planet` and `AxialCusps` were separate types  
New (v5): Unified as `AstrologicalPoint`

```python
# v4
from kerykeion.kr_types.kr_literals import Planet, AxialCusps

# v5 (recommended)
from kerykeion.schemas.kr_literals import AstrologicalPoint

# v5 (transition, uses aliases)
from kerykeion.schemas import Planet, AxialCusps  # Still available
```

#### 4. Lunar Nodes Naming

All lunar node fields have been renamed for clarity:

| Old Name (v4)     | New Name (v5)           |
| ----------------- | ----------------------- |
| `Mean_Node`       | `Mean_North_Lunar_Node` |
| `True_Node`       | `True_North_Lunar_Node` |
| `Mean_South_Node` | `Mean_South_Lunar_Node` |
| `True_South_Node` | `True_South_Lunar_Node` |

Migration example:

```python
from kerykeion import AstrologicalSubject, AstrologicalSubjectFactory

# v4 alias (still available, emits DeprecationWarning)
legacy_subject = AstrologicalSubject(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
print(legacy_subject.mean_node)

# v5 canonical name
modern_subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
print(modern_subject.mean_north_lunar_node)
```

#### 5. Axis Orb Filtering

Modern default orbs now treat chart axes (ASC, MC, DSC, IC) exactly like planets. If you prefer a traditional, constrained approach, every public aspect factory exposes the keyword-only `axis_orb_limit` parameter so you can set a dedicated threshold when needed.

#### 6. Chart Generation Changes

The two-step process (data + rendering) is now required:

Old v4:

```python
from pathlib import Path
from kerykeion import AstrologicalSubject, KerykeionChartSVG

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)

subject = AstrologicalSubject(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
chart = KerykeionChartSVG(subject, new_output_directory=output_dir)
chart.makeSVG()
```

New v5:

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
chart_data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
drawer.save_svg(output_path=output_dir, filename="john-v5-demo")
```

#### 7. Aspects API Changes

Aspects are now calculated through the factory:

Old v4:

```python
from kerykeion import AstrologicalSubjectFactory, NatalAspects, SynastryAspects

subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
subject1 = subject
subject2 = AstrologicalSubjectFactory.from_birth_data(
    "Jane", 1990, 6, 5, 8, 30,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)

natal_aspects = NatalAspects(subject)
synastry_aspects = SynastryAspects(subject1, subject2)
```

New v5:

```python
from kerykeion import AstrologicalSubjectFactory, AspectsFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
subject1 = subject
subject2 = AstrologicalSubjectFactory.from_birth_data(
    "Jane", 1990, 6, 5, 8, 30,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)

natal_aspects = AspectsFactory.single_chart_aspects(subject)
synastry_aspects = AspectsFactory.dual_chart_aspects(subject1, subject2)
```

Note (v5.1): The two lists `relevant_aspects` and `all_aspects` were unified into a single, cleaned list: `aspects`. If you previously used either property, switch to `aspects`. The legacy properties still work via the backward-compatibility layer but both return the same unified list.

---

### 🔄 Migration Guide

#### Using the Backward Compatibility Layer

For a gradual migration, use the `kerykeion.backword` module:

```python
from kerykeion import AstrologicalSubject  # Legacy wrapper

subject = AstrologicalSubject(
    "John Doe", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)

# These still work but show DeprecationWarnings
print(subject.mean_node)  # Maps to mean_north_lunar_node
print(subject.true_node)  # Maps to true_north_lunar_node
```

Warning: This compatibility layer will be removed in v6.0.

#### Step-by-Step Migration

1. Update imports

```python
# Old (v4)
from kerykeion import AstrologicalSubject, KerykeionChartSVG

# New (v5)
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
```

2. Update subject creation

```python
from kerykeion import AstrologicalSubject, AstrologicalSubjectFactory

# Old (v4)
subject = AstrologicalSubject(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)

# New (v5)
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
```

3. Update chart generation

```python
from pathlib import Path
from kerykeion import AstrologicalSubject, AstrologicalSubjectFactory, ChartDataFactory, KerykeionChartSVG
from kerykeion.charts.chart_drawer import ChartDrawer

# Old (v4)
legacy_subject = AstrologicalSubject(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)

chart = KerykeionChartSVG(legacy_subject, new_output_directory=output_dir)
chart.makeSVG()

# New (v5)
modern_subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
chart_data = ChartDataFactory.create_natal_chart_data(modern_subject)
drawer = ChartDrawer(chart_data=chart_data)
drawer.save_svg(output_path=output_dir, filename="john-v5-migration")
```

4. Update field access (lunar nodes)

```python
from kerykeion import AstrologicalSubject, AstrologicalSubjectFactory

# Old (v4)
legacy_subject = AstrologicalSubject(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
legacy_mean_node = legacy_subject.mean_node
print(getattr(legacy_mean_node, "position", "Legacy mean node not active"))

# New (v5)
modern_subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
modern_mean_node = modern_subject.mean_north_lunar_node
print(getattr(modern_mean_node, "position", "Modern mean node not active"))
```

5. Update aspects

```python
from kerykeion import AstrologicalSubject, AstrologicalSubjectFactory, NatalAspects, AspectsFactory

# Old (v4)
legacy_subject = AstrologicalSubject(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
legacy_aspects = NatalAspects(legacy_subject)
print(f"Legacy aspects count: {len(legacy_aspects.relevant_aspects)}")

# New (v5)
modern_subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
modern_aspects = AspectsFactory.single_chart_aspects(modern_subject)
print(f"Modern aspects count: {len(modern_aspects.aspects)}")
```

#### Automated Migration Script

Use this sed script to update Python files automatically:

```bash
# Update lunar node references
find . -name "*.py" -type f -exec sed -i.bak \
    -e 's/\.mean_node/.mean_north_lunar_node/g' \
    -e 's/\.true_node/.true_north_lunar_node/g' \
    -e 's/\.mean_south_node/.mean_south_lunar_node/g' \
    -e 's/\.true_south_node/.true_south_lunar_node/g' \
    -e 's/"Mean_Node"/"Mean_North_Lunar_Node"/g' \
    -e 's/"True_Node"/"True_North_Lunar_Node"/g' \
    -e 's/"Mean_South_Node"/"Mean_South_Lunar_Node"/g' \
    -e 's/"True_South_Node"/"True_South_Lunar_Node"/g' \
    {} \;
```

Note: Always review automated changes and test thoroughly before committing.

---

### 🗓️ Migration Timeline

- v5.0: Current — Backward compatibility layer available
- v6.0: Future — Compatibility layer will be removed

