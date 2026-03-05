---
title: 'Active Points Reference'
description: 'Complete reference for all 42 celestial points available in Kerykeion: planets, asteroids, TNOs, Arabic parts, fixed stars, and special points.'
category: 'Reference'
tags: ['docs', 'points', 'planets', 'asteroids', 'configuration', 'kerykeion']
order: 14
---

# Active Points Reference

Kerykeion supports **42 celestial points** that can be individually enabled or disabled via the `active_points` parameter. This page documents every available point and the preset configurations.

## Available Points

### Main Planets (10)

The classical and modern planets, always available.

| Point | Description |
| :---- | :---------- |
| `Sun` | The luminary representing core identity |
| `Moon` | The luminary representing emotions and instincts |
| `Mercury` | Communication, intellect |
| `Venus` | Love, beauty, values |
| `Mars` | Action, drive, aggression |
| `Jupiter` | Expansion, luck, philosophy |
| `Saturn` | Structure, discipline, limits |
| `Uranus` | Innovation, rebellion, sudden change |
| `Neptune` | Spirituality, illusion, dreams |
| `Pluto` | Transformation, power, the unconscious |

### Lunar Nodes (4)

Two calculation methods are available: **True** (oscillating, astronomically precise) and **Mean** (smoothed average).

| Point | Description |
| :---- | :---------- |
| `True_North_Lunar_Node` | True (oscillating) North Node / Rahu |
| `True_South_Lunar_Node` | True (oscillating) South Node / Ketu |
| `Mean_North_Lunar_Node` | Mean (averaged) North Node |
| `Mean_South_Lunar_Node` | Mean (averaged) South Node |

By default, only the True nodes are active. You can switch to Mean nodes or enable both.

### Angles / Axial Cusps (4)

The four angles of the chart. These are always recommended to keep active.

| Point | Description |
| :---- | :---------- |
| `Ascendant` | Rising sign, the eastern horizon |
| `Medium_Coeli` | Midheaven, the highest point |
| `Descendant` | Setting point, the western horizon |
| `Imum_Coeli` | Nadir, the lowest point |

### Other Points (5)

| Point | Description |
| :---- | :---------- |
| `Chiron` | The "wounded healer" asteroid/comet |
| `Mean_Lilith` | Mean Black Moon Lilith (lunar apogee, averaged) |
| `True_Lilith` | True (oscillating) Black Moon Lilith |
| `Earth` | Useful for heliocentric charts |
| `Pholus` | Centaur object associated with catalytic events |

### Asteroids (4)

The four major asteroids in the main belt.

| Point | Description |
| :---- | :---------- |
| `Ceres` | Nurturing, agriculture, cycles of loss and return |
| `Pallas` | Wisdom, strategy, creative intelligence |
| `Juno` | Partnership, commitment, marriage |
| `Vesta` | Devotion, focus, sacred service |

### Trans-Neptunian Objects (7)

Distant objects beyond Neptune. Ephemeris data may not be available for all historical dates.

| Point | Description |
| :---- | :---------- |
| `Eris` | Discord, competition, marginalization |
| `Sedna` | Extreme isolation, deep transformation |
| `Haumea` | Fertility, creation, rebirth |
| `Makemake` | Environmental awareness, primal creativity |
| `Ixion` | Lawlessness, boundary-pushing |
| `Orcus` | Oaths, the underworld, accountability |
| `Quaoar` | Creation myths, primordial forces |

> **Note:** Some TNOs may not have ephemeris data for very old or very future dates. If calculation fails for a point, it is silently removed from the active points for that subject.

### Fixed Stars (2)

| Point | Description |
| :---- | :---------- |
| `Regulus` | Royal star at ~0° Virgo, associated with fame and success |
| `Spica` | Star at ~24° Libra, associated with brilliance and gifts |

### Arabic Parts / Lots (4)

Calculated points based on the formula involving the Ascendant, Sun, and other bodies. Their calculation depends on whether the chart is diurnal or nocturnal (the `is_diurnal` field on the subject model).

| Point | Formula (Day) | Formula (Night) |
| :---- | :------------ | :-------------- |
| `Pars_Fortunae` | Asc + Moon - Sun | Asc + Sun - Moon |
| `Pars_Spiritus` | Asc + Sun - Moon | Asc + Moon - Sun |
| `Pars_Amoris` | Asc + Venus - Sun | Asc + Sun - Venus |
| `Pars_Fidei` | Asc + Mercury - Moon | Asc + Moon - Mercury |

### Special Points (2)

| Point | Description |
| :---- | :---------- |
| `Vertex` | A fated point on the western side of the chart |
| `Anti_Vertex` | The point opposite the Vertex |

## Preset Configurations

Kerykeion provides three preset lists you can import and use directly.

### `DEFAULT_ACTIVE_POINTS` (18 points)

The default configuration used when no `active_points` parameter is specified.

Includes: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, True_North_Lunar_Node, True_South_Lunar_Node, Chiron, Mean_Lilith, Ascendant, Medium_Coeli, Descendant, Imum_Coeli.

### `TRADITIONAL_ASTROLOGY_ACTIVE_POINTS` (9 points)

The seven classical planets plus both True lunar nodes. Useful for traditional/Hellenistic astrology.

Includes: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, True_North_Lunar_Node, True_South_Lunar_Node.

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
```

### `ALL_ACTIVE_POINTS` (42 points)

Every available point enabled. Useful for research or comprehensive analysis.

```python
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_points=ALL_ACTIVE_POINTS,
)
```

## Custom Configuration

You can build your own list by combining any of the 42 available point names:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Custom Points", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
)

# Classical planets + asteroids + Part of Fortune
custom_points = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn",
    "Ceres", "Pallas", "Juno", "Vesta",
    "Pars_Fortunae",
    "Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli",
]

chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_points=custom_points,
)

# Access the Part of Fortune
print(f"Pars Fortunae: {subject.pars_fortunae.sign} at {subject.pars_fortunae.position:.2f}°")
```

## Diurnal / Nocturnal Detection

Since v5.8.0, the `AstrologicalSubjectModel` includes an `is_diurnal` boolean field. This determines whether the chart is a day chart (Sun above the horizon) or a night chart (Sun below). It is used internally for Arabic Parts calculation (the formula reverses for night charts).

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Day or Night", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
)

print(f"Is diurnal chart: {subject.is_diurnal}")
```

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
