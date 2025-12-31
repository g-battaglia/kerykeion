---
title: 'Charts Module - ChartDrawer'
category: 'Core'
tags: ['docs', 'charts', 'svg', 'visual', 'kerykeion']
order: 4
---

# Charts Visualization

The `ChartDrawer` class is the generic visualization engine. It renders professional SVG charts from pre-calculated data.

## Design Philosophy

Kerykeion follows a **separation of concerns** principle:

-   **`ChartDataFactory`** handles all astronomical calculations (planetary positions, aspects, elements, etc.)
-   **`ChartDrawer`** focuses purely on visualization (drawing wheels, aspect grids, labels)

This decoupling means you can:

-   Generate chart data once and render it in multiple formats/themes
-   Perform calculations without needing visual output
-   Swap visualization engines without touching calculation logic

## Standard Workflow

Creating any chart follows the same 3-step process:

1.  **Create Subject(s)**: Use `AstrologicalSubjectFactory`.
2.  **Generate Data**: Use `ChartDataFactory` to calculate positions and aspects.
3.  **Draw**: Use `ChartDrawer` to render the SVG.

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# 1. Subject
subject = AstrologicalSubjectFactory.from_birth_data("Alice", 1990, 6, 15, 12, 0, "London", "GB")

# 2. Data
chart_data = ChartDataFactory.create_natal_chart_data(subject)

# 3. Draw
drawer = ChartDrawer(chart_data)
svg_content = drawer.generate_svg_string()
```

## Chart Types

The drawing process is identical for all types; only the _Data Generation_ step changes.

### Synastry (Comparison)

Synastry charts overlay two users' planetary positions to visualize their relationship. The outer wheel shows the second subject's planets.

```python
# Create chart data for two subjects
synastry_data = ChartDataFactory.create_synastry_chart_data(subject_a, subject_b)
drawer = ChartDrawer(synastry_data)
```

### Transits

Transit charts compare a static natal chart (inner wheel) against the current moving sky (outer wheel) to analyze current astrological influences.

```python
# Compare natal chart against current time
transit_data = ChartDataFactory.create_transit_chart_data(natal_subject, current_time_subject)
drawer = ChartDrawer(transit_data)
```

### Composite (Midpoint)

Composite charts display a single wheel calculated from the midpoints of two subjects, representing the relationship as a unified entity.

```python
from kerykeion.composite_subject_factory import CompositeSubjectFactory

# Create composite subject first
composite_sub = CompositeSubjectFactory(subject_a, subject_b).get_midpoint_composite_subject_model()
composite_data = ChartDataFactory.create_composite_chart_data(composite_sub)
drawer = ChartDrawer(composite_data)
```

## Configuration & Customization

The `ChartDrawer` accepts several parameters to customize the visual output.

```python
drawer = ChartDrawer(
    chart_data=chart_data,
    theme="dark",
    chart_language="IT",
    show_aspect_icons=True
)
```

### Themes

-   `"classic"` (Default): White background, traditional look.
-   `"dark"`: Modern dark mode.
-   `"light"`: Minimalist light mode.
-   `"strawberry"`: Pink/Red color palette.
-   `"dark-high-contrast"`: Accessibility focused.
-   `"black-and-white"`: High contrast monochrome for print.

### Languages

Supported: `EN`, `IT`, `FR`, `ES`, `PT`, `CN`, `RU`, `TR`, `DE`, `HI`.

## Output Methods & API Reference

### 1. Generating Strings (Web/API)

Methods to get the raw SVG code as a string.

```python
# Full Chart
svg = drawer.generate_svg_string()

# Components
wheel_only = drawer.generate_wheel_only_svg_string()
grid_only = drawer.generate_aspect_grid_only_svg_string()
```

### 2. Saving to File (CLI/Scripts)

Methods to write the SVG directly to disk.

```python
from pathlib import Path

# Full Chart
drawer.save_svg(Path("./output"), filename="natal_chart")

# Components
drawer.save_wheel_only_svg_file(Path("./output"), filename="wheel_only")
drawer.save_aspect_grid_only_svg_file(Path("./output"), filename="grid_only")
```

### Class `ChartDrawer`

**Constructor Parameters:**

| Parameter                       | Type                     | Default      | Description                                 |
| :------------------------------ | :----------------------- | :----------- | :------------------------------------------ |
| `chart_data`                    | `ChartDataModel`         | **Required** | Pre-computed data from a Factory.           |
| `theme`                         | `KerykeionChartTheme`    | `"classic"`  | Visual theme (e.g. `"dark"`).               |
| `chart_language`                | `KerykeionChartLanguage` | `"EN"`       | Label language (`"IT"`, `"ES"`, etc).       |
| `transparent_background`        | `bool`                   | `False`      | Remove background color.                    |
| `external_view`                 | `bool`                   | `False`      | Place planets on outer ring (Single chart). |
| `show_aspect_icons`             | `bool`                   | `True`       | Show symbol icons in aspect grid.           |
| `show_degree_indicators`        | `bool`                   | `True`       | Show degree ticks on the wheel.             |
| `custom_title`                  | `str`                    | `None`       | Override the default chart title.           |
| `double_chart_aspect_grid_type` | `"list"`, `"table"`      | `"list"`     | Grid style for Synastry/Transit.            |
| `auto_size`                     | `bool`                   | `True`       | Automatically adjust chart dimensions.      |
| `padding`                       | `int`                    | `20`         | Padding around the SVG content.             |

**Public Methods:**

-   `generate_svg_string() -> str`
-   `generate_wheel_only_svg_string() -> str`
-   `generate_aspect_grid_only_svg_string() -> str`
-   `save_wheel_only_svg_file(output_path, filename)`
-   `save_aspect_grid_only_svg_file(output_path, filename)`

## Helper Functions (`charts_utils`)

Import from: `kerykeion.charts.charts_utils`

Utility functions used in SVG generation that can be helpful for custom rendering logic.

| Function                     | Description                                        |
| :--------------------------- | :------------------------------------------------- |
| `degreeDiff(a, b)`           | Smallest difference between two angles (0-180°).   |
| `degreeSum(a, b)`            | Sum of two angles normalized to 0-360°.            |
| `normalizeDegree(angle)`     | Constrains any angle to 0-360° range.              |
| `sliceToX(slice, r, offset)` | Calculates X coordinate for a circle slice (1-12). |
| `sliceToY(slice, r, offset)` | Calculates Y coordinate for a circle slice (1-12). |

```python
from kerykeion.charts.charts_utils import degreeDiff

diff = degreeDiff(350, 10) # Returns 20.0
```
