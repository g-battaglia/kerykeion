---
layout: ../../layouts/DocLayout.astro
title: 'Birth Chart'
pubDate: 2025-01-01
description: 'How to create a birth chart with Kerykeion'
author: 'Giacomo Battaglia'
tags: ['astrology', 'birth chart', 'kerykeion', 'python']
---

# Birth Chart

The birth chart is the most common chart in astrology. It is a representation of the sky at the moment of birth of a person. The birth chart is a map of the sky at the time of birth, showing the positions of the planets in the zodiac signs and houses. The birth chart is also known as the natal chart.

## Standard Birth Chart

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Create a subject from birth data (offline example with manual coordinates)
subject = AstrologicalSubjectFactory.from_birth_data(
    "Kanye", 1977, 6, 8, 8, 45,
    lng=-84.38798,
    lat=33.7490,
    tz_str="America/New_York",
    online=False,
)

# Pre-compute natal chart data (calculations only)
chart_data = ChartDataFactory.create_natal_chart_data(subject)

# Render and save the SVG
drawer = ChartDrawer(chart_data=chart_data)
out_dir = Path("charts_output")
out_dir.mkdir(exist_ok=True)
drawer.save_svg(output_path=out_dir, filename="kanye-natal")
```

The output will be a SVG file in `charts_output/kanye-natal.svg`.

![Birth Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/Kanye%20-%20Natal%20Chart.svg)

## External Birth Chart

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

chart_data = ChartDataFactory.create_natal_chart_data(subject)

# External view with planets on the external ring
drawer = ChartDrawer(chart_data=chart_data, external_view=True)
out_dir = Path("charts_output")
out_dir.mkdir(exist_ok=True)
drawer.save_svg(output_path=out_dir, filename="john-lennon-external-natal")
```

The output will be a SVG file in `charts_output/kanye-external-natal.svg`.

![External Birth Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20-%20ExternalNatal%20-%20Natal%20Chart.svg)
