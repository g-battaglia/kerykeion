---
title: 'Active Points'
tags: ['examples', 'points', 'asteroids', 'tno', 'arabic parts', 'kerykeion']
order: 16
---

# Active Points

Kerykeion supports 62 celestial points that can be individually enabled or disabled. This page shows practical examples.

For the full reference of all available points, see [Active Points Reference](/content/docs/active_points).

## Using the Traditional Preset

The `TRADITIONAL_ASTROLOGY_ACTIVE_POINTS` preset includes only the 7 classical planets plus True lunar nodes (9 points total).

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.settings.config_constants import TRADITIONAL_ASTROLOGY_ACTIVE_POINTS

subject = AstrologicalSubjectFactory.from_birth_data(
    "Traditional Chart", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
)

chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS,
)

# Only classical planets and nodes will appear
for point_name in ["sun", "moon", "mars", "jupiter", "saturn"]:
    point = getattr(subject, point_name)
    print(f"{point.name}: {point.sign} at {point.position:.2f}°")
```

## Enabling Asteroids

Add the four major asteroids to the default set:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS

subject = AstrologicalSubjectFactory.from_birth_data(
    "With Asteroids", 1986, 4, 12, 8, 45,
    lng=11.3426, lat=44.4949, tz_str="Europe/Rome", online=False,
)

# Add asteroids to the default list
points_with_asteroids = DEFAULT_ACTIVE_POINTS + ["Ceres", "Pallas", "Juno", "Vesta"]

chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_points=points_with_asteroids,
)

# Access asteroid data
print(f"Ceres: {subject.ceres.sign} at {subject.ceres.position:.2f}°")
print(f"Juno: {subject.juno.sign} at {subject.juno.position:.2f}°")
print(f"Vesta: {subject.vesta.sign} at {subject.vesta.position:.2f}°")
print(f"Pallas: {subject.pallas.sign} at {subject.pallas.position:.2f}°")
```

## Enabling Arabic Parts

Arabic Parts (Lots) are calculated points. Their formula reverses for night charts, using the `is_diurnal` field.

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS

subject = AstrologicalSubjectFactory.from_birth_data(
    "With Arabic Parts", 1990, 3, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
)

# Add Arabic Parts
points_with_lots = DEFAULT_ACTIVE_POINTS + [
    "Pars_Fortunae",
    "Pars_Spiritus",
    "Pars_Amoris",
    "Pars_Fidei",
]

chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_points=points_with_lots,
)

print(f"Chart is diurnal: {subject.is_diurnal}")
print(f"Part of Fortune: {subject.pars_fortunae.sign} at {subject.pars_fortunae.position:.2f}°")
print(f"Part of Spirit: {subject.pars_spiritus.sign} at {subject.pars_spiritus.position:.2f}°")
```

## Enabling All Points

Use the `ALL_ACTIVE_POINTS` preset to enable everything:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS
from pathlib import Path

subject = AstrologicalSubjectFactory.from_birth_data(
    "All Points", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
)

chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_points=ALL_ACTIVE_POINTS,
)

# Generate a chart with all 62 points
chart = ChartDrawer(chart_data=chart_data)
output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
chart.save_svg(output_path=output_dir, filename="all-points-chart")
```

## Including Fixed Stars

v5.12 added 22 fixed stars (all 15 Behenian + 4 Royal Stars + more). Fixed stars are computed for every subject but excluded from chart rendering and aspects by default. Add them to `active_points` to include them:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS

subject = AstrologicalSubjectFactory.from_birth_data(
    "With Stars", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
)

# Add the 4 Royal Stars to the default set
points_with_stars = DEFAULT_ACTIVE_POINTS + [
    "Regulus", "Aldebaran", "Antares", "Fomalhaut",
]

chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_points=points_with_stars,
)

# Access fixed star data (always available, even without active_points)
print(f"Regulus: {subject.regulus.sign} at {subject.regulus.position:.2f}°")
print(f"  Magnitude: {subject.regulus.magnitude}")
print(f"  Declination: {subject.regulus.declination:.2f}°")
print(f"  Speed: {subject.regulus.speed:.4f}°/day")
```

## Switching Between True and Mean Nodes

By default, Kerykeion uses True (oscillating) lunar nodes. To use Mean nodes instead:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Mean Nodes", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
)

mean_node_points = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "Mean_North_Lunar_Node",  # instead of True_North_Lunar_Node
    "Mean_South_Lunar_Node",  # instead of True_South_Lunar_Node
    "Chiron", "Mean_Lilith",
    "Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli",
]

chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_points=mean_node_points,
)

print(f"Mean North Node: {subject.mean_north_lunar_node.sign}")
```

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
