---
layout: ../../layouts/DocLayout.astro
title: 'Minimalist Charts & Aspect Table'
---

# Minimalist Charts & Aspect Table

The Minimalist Charts & Aspect Table functionality allows you to generate simplified versions of astrological charts. This includes generating a wheel-only natal chart and an aspect grid-only natal chart. These features provide a cleaner and more focused view of the chart elements.

## Wheel Natal Only Chart

You can generate a wheel-only natal chart, which includes only the wheel and strips away any extra details. This is useful for a minimalist presentation of the natal chart.

### Example Usage

Here is an example of how to generate a wheel-only natal chart:

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Wheel Natal Only Chart
subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Wheel Only", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London", online=False,
)
data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(data)

out_dir = Path("charts_output")
out_dir.mkdir(exist_ok=True)
drawer.save_wheel_only_svg_file(output_path=out_dir)
```

## Aspect Grid Only Natal Chart

You can generate an aspect grid-only natal chart, which focuses solely on the aspect grid. This is useful for a detailed analysis of the aspects without the distraction of other chart elements.

### Example Usage

Here is an example of how to generate an aspect grid-only natal chart:

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Aspect Grid Only Natal Chart
subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Aspect Grid Only", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London", online=False,
)
data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(data)

out_dir = Path("charts_output")
out_dir.mkdir(exist_ok=True)
drawer.save_aspect_grid_only_svg_file(output_path=out_dir)
```
