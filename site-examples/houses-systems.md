---
layout: ../../layouts/DocLayout.astro
title: 'Houses Systems'
---

# Houses Systems

You can use the different houses system to calculate the data.

There are different `houses_systems`:

```txt
A = equal
B = Alcabitius
C = Campanus
D = equal (MC)
F = Carter poli-equ.
H = horizon/azimut
I = Sunshine
i = Sunshine/alt.
K = Koch
L = Pullen SD
M = Morinus
N = equal/1=Aries
O = Porphyry
P = Placidus
Q = Pullen SR
R = Regiomontanus
S = Sripati
T = Polich/Page
U = Krusinski-Pisa-Goelzer
V = equal/Vehlow
W = equal/whole sign
X = axial rotation system/Meridian houses
Y = APC houses
```

Here some examples:

## Birth Chart with Morinus House System

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

morinus_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Morinus", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London",
    online=False,
    houses_system_identifier="M",
)
data = ChartDataFactory.create_natal_chart_data(morinus_subject)
chart = ChartDrawer(data)

out_dir = Path("charts_output")
out_dir.mkdir(exist_ok=True)
chart.save_svg(output_path=out_dir, filename="john-lennon-morinus")
```

The output will be:

![John Lennon - House System Morinus](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20-%20House%20System%20Morinus%20-%20Natal%20Chart.svg)

## Check House System Name on a Subject

```python
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Johnny Depp", 1963, 6, 9, 0, 0,
    lng=-87.1112,
    lat=37.7719,
    tz_str="America/Chicago",
    online=False,
    houses_system_identifier="P",  # Placidus
)

print(subject.houses_system_name)
```
