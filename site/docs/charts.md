---
title: 'Charts Module - ChartDrawer'
category: 'Core'
tags: ['docs', 'charts', 'svg', 'visual', 'kerykeion']
order: 4
---

# Charts Visualization

The `ChartDrawer` class is the generic visualization engine. It renders professional SVG charts from pre-calculated data. It is decoupled from astronomical calculations — it simply draws what `ChartDataFactory` provides.

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

```python
# Create chart data for two subjects
synastry_data = ChartDataFactory.create_synastry_chart_data(subject_a, subject_b)
drawer = ChartDrawer(synastry_data)
```

### Transits

```python
# Compare natal chart against current time
transit_data = ChartDataFactory.create_transit_chart_data(natal_subject, current_time_subject)
drawer = ChartDrawer(transit_data)
```

### Composite (Midpoint)

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

### Languages

Supported: `EN`, `IT`, `FR`, `ES`, `PT`, `CN`, `RU`, `TR`, `DE`, `HI`.

## Output Methods

### 1. Generate String (For Web/API)

Returns the SVG code as a string.

```python
svg = drawer.generate_svg_string()

# Variations
wheel_only = drawer.generate_wheel_only_svg_string()
aspects_grid = drawer.generate_aspect_grid_only_svg_string()
```

### 2. Save to File (For CLI/Scripts)

Writes the SVG directly to disk.

```python
from pathlib import Path
output_dir = Path("./output")

drawer.save_svg(output_dir)
# Saves: ./output/Name_Type_Date.svg
```
