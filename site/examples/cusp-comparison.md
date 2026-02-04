---
title: 'Cusp Comparison Grids'
tags: ['examples', 'charts', 'houses', 'cusps', 'synastry', 'kerykeion']
order: 13
---

# Cusp Comparison Grids

Kerykeion introduces **cusp comparison grids** for Transit, Synastry, and Dual Return charts. These tables show how each subject's house cusps fall into the other subject's house system.

## Synastry Cusp Comparison

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

person_a = AstrologicalSubjectFactory.from_birth_data(
    name="Person A",
    year=1990, month=5, day=15,
    hour=10, minute=30,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)
person_b = AstrologicalSubjectFactory.from_birth_data(
    name="Person B",
    year=1992, month=8, day=23,
    hour=14, minute=45,
    lng=9.19,
    lat=45.4642,
    tz_str="Europe/Rome",
    online=False,
)

chart_data = ChartDataFactory.create_synastry_chart_data(
    first_subject=person_a,
    second_subject=person_b,
    include_house_comparison=True,
)

drawer = ChartDrawer(
    chart_data=chart_data,
    show_cusp_position_comparison=True,
)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)

drawer.save_svg(
    output_path=output_dir,
    filename="synastry-with-cusp-comparison",
)
```

This produces:

- two **house comparison tables** (points in partner houses)  
- two **cusp comparison tables** (cusps in partner houses), labelled with localized `"cusp"` and `"house"` strings  

### Synastry Chart with House Comparison

![Synastry Chart with House Comparison](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20-%20Synastry%20Chart%20-%20House%20Comparison%20Only.svg)

### Transit Chart with Cusp Comparison

![Transit Chart with Cusp Comparison](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20-%20Transit%20Chart%20-%20Cusp%20Comparison%20Only.svg)

## Accessing Cusp Comparison in Reports

When a dual chart includes house comparison, reports also expose cusp overlays:

```python
from kerykeion import ReportGenerator

report = ReportGenerator(chart_data)
text = report.generate_report()
print(text)
```

Look for sections such as:

- `"Person A cusps in Person B houses"`  
- `"Person B cusps in Person A houses"`  

