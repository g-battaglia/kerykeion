---
title: 'Element & Quality Distribution'
category: 'Analysis'
tags: ['docs', 'elements', 'qualities', 'statistics', 'kerykeion']
order: 10
---

# Element & Quality Distribution

Kerykeion calculates a balance report for Elements (Fire/Earth/Air/Water) and Qualities (Cardinal/Fixed/Mutable) for every chart. You can choose between a **Weighted** method (based on planetary importance) or a **Pure Count** method.

## Usage

Configure the distribution method when creating chart data.

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data("Alice", 1990, 6, 15, 12, 0, "London", "GB")

# Default: Weighted
data = ChartDataFactory.create_natal_chart_data(subject)
print(f"Fire: {data.element_distribution.fire_percentage}%")

# Option: Pure Count (1 point per planet)
pure_data = ChartDataFactory.create_natal_chart_data(
    subject,
    distribution_method="pure_count"
)
```

## Weights System

In **Weighted** mode, points contribute different amounts to the score.

| Points                                         | Weight  |
| :--------------------------------------------- | :------ |
| `Sun`, `Moon`, `Ascendant`                     | **2.0** |
| `Mercury`, `Venus`, `Mars`, `MC`, `Desc`, `IC` | **1.5** |
| `Jupiter`, `Saturn`                            | **1.0** |
| `Vertex`, `Fortuna`, `Nodes`                   | **0.8** |
| `Chiron`                                       | **0.6** |
| `Uranus`, `Neptune`, `Pluto`                   | **0.5** |
| `Asteroids`                                    | **0.4** |

## Custom Weights

You can override specific weights while keeping others default.

```python
custom_data = ChartDataFactory.create_natal_chart_data(
    subject,
    distribution_method="weighted",
    custom_distribution_weights={
        "sun": 3.0,       # Emphasize Sun
        "chiron": 1.5,    # Emphasize Chiron
        "__default__": 1.0 # Everything else
    }
)
```
