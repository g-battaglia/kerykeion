---
title: 'Element & Quality Distribution'
description: 'Analyze the balance of elements and qualities in any chart. Explains weighted and pure count methods for calculating fire, earth, air, and water distribution.'
category: 'Analysis'
tags: ['docs', 'elements', 'qualities', 'statistics', 'kerykeion']
order: 10
---

# Element & Quality Distribution

Kerykeion calculates a balance report for Elements (Fire/Earth/Air/Water) and Qualities (Cardinal/Fixed/Mutable) for every chart. You can choose between a **Weighted** method (based on planetary importance) or a **Pure Count** method.

## Usage

Configure the distribution method when creating chart data via `ChartDataFactory`. Both `distribution_method` and `custom_distribution_weights` are **keyword-only** parameters available on all `ChartDataFactory` methods. `distribution_method` is `Literal["pure_count", "weighted"]` and defaults to `"weighted"`.

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

# Default: Weighted
data = ChartDataFactory.create_natal_chart_data(subject)
print(f"Fire: {data.element_distribution.fire_percentage}%")

# Option: Pure Count (1 point per planet, regardless of importance)
pure_data = ChartDataFactory.create_natal_chart_data(
    subject,
    distribution_method="pure_count"
)
```

**Expected Output (Weighted):**

```text
Fire: 9%
```

You can also access all element and quality percentages:

```python
print(f"Fire: {data.element_distribution.fire_percentage}%")
print(f"Earth: {data.element_distribution.earth_percentage}%")
print(f"Air: {data.element_distribution.air_percentage}%")
print(f"Water: {data.element_distribution.water_percentage}%")

print(f"Cardinal: {data.quality_distribution.cardinal_percentage}%")
print(f"Fixed: {data.quality_distribution.fixed_percentage}%")
print(f"Mutable: {data.quality_distribution.mutable_percentage}%")
```

**Expected Output:**

```text
Fire: 9%
Earth: 33%
Air: 33%
Water: 25%
Cardinal: 31%
Fixed: 15%
Mutable: 54%
```

## Weights System

In **Weighted** mode, points contribute different amounts to the score.

The table is `DEFAULT_WEIGHTED_POINT_WEIGHTS` in `kerykeion.charts.utils`, and it
covers every member of `AstrologicalPoint` — all 76 names, fixed stars included.

| Points                                                                     | Weight  |
| :------------------------------------------------------------------------- | :------ |
| `Sun`, `Moon`, `Ascendant`                                                 | **2.0** |
| `Mercury`, `Venus`, `Mars`, `Medium_Coeli`, `Descendant`, `Imum_Coeli`     | **1.5** |
| `Jupiter`, `Saturn`                                                        | **1.0** |
| `Vertex`, `Anti_Vertex`, `Pars_Fortunae`                                   | **0.8** |
| `Pars_Spiritus`                                                            | **0.7** |
| `Chiron`, `Pars_Amoris`, `Pars_Fidei`                                      | **0.6** |
| `Uranus`, `Neptune`, `Pluto`, the four lunar nodes, `Ceres`, the Lilith and Priapus variants, `Interpolated_Perigee`, `White_Moon` | **0.5** |
| `Pallas`, `Juno`, `Vesta`                                                  | **0.4** |
| `Pholus`, the seven TNOs (`Eris`, `Sedna`, `Haumea`, `Makemake`, `Ixion`, `Orcus`, `Quaoar`), the eight Uranian points, `Earth` | **0.3** |
| The 23 fixed stars of `DEFAULT_FIXED_STARS`                                | **0.2** |

A point outside the table takes the fallback weight, `1.0`. An **active fixed
star** outside the table is the one exception: it takes a dedicated star
fallback of `0.2`, so a catalog star can never inherit a planet-grade weight.
In `pure_count` mode both fallbacks are `1.0`, since every counted item must
contribute exactly one.

## Custom Weights

You can override specific weights while keeping others default.

```python
custom_data = ChartDataFactory.create_natal_chart_data(
    subject,
    distribution_method="weighted",
    custom_distribution_weights={
        "sun": 3.0,       # Emphasize Sun
        "chiron": 1.5,    # Emphasize Chiron
        "__default__": 1.0 # Fallback for points not in the default weight table
    }
)
```

> **Note:** In weighted mode, `__default__` only changes the fallback weight used for points that are **absent** from the built-in weight table. Points listed in the table keep their default weights unless you override them individually (like `sun` and `chiron` above).

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
