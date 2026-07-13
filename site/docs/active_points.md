---
title: 'Active Points Reference'
description: 'Complete reference for 53 active chart points plus separately configured fixed stars.'
category: 'Reference'
tags: ['docs', 'points', 'planets', 'asteroids', 'configuration', 'kerykeion']
order: 14
---

# Active Points Reference

Kerykeion supports **53 non-star chart points** through the `active_points`
parameter. Fixed stars use the separate `active_fixed_stars` parameter and
fixed-star presets; they are not members of `ALL_ACTIVE_POINTS`. This page
documents both configuration mechanisms.

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

By default, only `True_North_Lunar_Node` is active (the South Node is not). You can switch to Mean nodes or enable more.

### Angles / Axial Cusps (4)

The four angles of the chart. These are always recommended to keep active.

| Point | Description |
| :---- | :---------- |
| `Ascendant` | Rising sign, the eastern horizon |
| `Medium_Coeli` | Midheaven, the highest point |
| `Descendant` | Setting point, the western horizon |
| `Imum_Coeli` | Nadir, the lowest point |

### Other Points (8)

| Point | Description |
| :---- | :---------- |
| `Chiron` | The "wounded healer" asteroid/comet |
| `Mean_Lilith` | Mean Black Moon Lilith (lunar apogee, averaged) |
| `True_Lilith` | True (oscillating) Black Moon Lilith |
| `Interpolated_Lilith` | Interpolated Black Moon Lilith (smoothed between mean and true) |
| `Mean_Priapus` | Mean Priapus (anti-Lilith, lunar perigee, averaged) |
| `True_Priapus` | True (oscillating) Priapus |
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

### Uranian / Hamburg School Planets (8)

Eight hypothetical trans-Neptunian points used in Uranian astrology. Pass them in `active_points` to include.

| Point | Description |
| :---- | :---------- |
| `Cupido` | Relationships, family, art, social connections |
| `Hades` | Hidden things, the past, degradation, research |
| `Zeus` | Directed energy, leadership, machinery, fire |
| `Kronos` | Authority, government, expertise, height |
| `Apollon` | Expansion, commerce, science, peace |
| `Admetos` | Depth, stagnation, concentration, beginnings/endings |
| `Vulkanus` | Mighty force, intensity, power |
| `Poseidon` | Idealism, spirituality, enlightenment, illusion |

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

> **Note:** Some TNOs may not have ephemeris data for very old or far-future dates. If calculation fails for a point, a warning is logged and the point is removed from the active points for that subject.

### Fixed Stars (23, configured separately)

All 15 Behenian stars of the medieval/Hermetic tradition are included, plus 8 additional bright stars. Fixed stars are inactive by default and are selected with `active_fixed_stars`, not `active_points`.

#### Royal Stars (4)

| Point | Magnitude | Description |
| :---- | :-------- | :---------- |
| `Regulus` | ~1.4 | Royal star, fame and success |
| `Aldebaran` | ~0.9 | Royal star, integrity and honor |
| `Antares` | ~1.1 | Royal star, intensity and obsession |
| `Fomalhaut` | ~1.2 | Royal star, idealism and vision |

#### Behenian Stars (12, not listed above)

| Point | Magnitude | Description |
| :---- | :-------- | :---------- |
| `Algol` | ~2.1 | Eclipsing binary, intensity and transformation |
| `Sirius` | -1.5 | Brightest star, ambition and fame |
| `Procyon` | 0.3 | Quick success |
| `Capella` | 0.1 | Shepherd star |
| `Spica` | 1.0 | Brilliance and gifts |
| `Arcturus` | -0.05 | Guardian of the bear |
| `Vega` | 0.0 | Artistry and charisma |
| `Alcyone` | ~2.9 | Brightest Pleiad, mysticism |
| `Alphecca` | ~2.2 | Gemma, the jewel in the crown |
| `Algorab` | ~2.9 | Delta Corvi, cunning |
| `Deneb_Algedi` | ~2.8 | Tail of the goat, law and justice |
| `Alkaid` | ~1.9 | Tip of Great Bear's tail, mourning and leadership |

#### Other Bright Stars (7)

| Point | Magnitude | Description |
| :---- | :-------- | :---------- |
| `Canopus` | -0.7 | Second brightest, pathfinding and navigation |
| `Rigel` | 0.1 | Knowledge and ambition |
| `Betelgeuse` | 0.4 | Fame and endings |
| `Achernar` | 0.5 | End of the river, transformation |
| `Altair` | 0.8 | Courage and daring |
| `Pollux` | 1.1 | Subtle influence |
| `Deneb` | 1.3 | Far-reaching impact |

### Arabic Parts / Lots (4)

Calculated points based on the formula involving the Ascendant, Sun, and other bodies. For `Pars_Fortunae` and `Pars_Spiritus`, the calculation depends on whether the chart is diurnal or nocturnal (the `is_diurnal` field on the subject model); `Pars_Amoris` and `Pars_Fidei` use a single formula regardless of sect.

| Point | Formula (Day) | Formula (Night) |
| :---- | :------------ | :-------------- |
| `Pars_Fortunae` | Asc + Moon - Sun | Asc + Sun - Moon |
| `Pars_Spiritus` | Asc + Sun - Moon | Asc + Moon - Sun |
| `Pars_Amoris` | Asc + Venus - Sun | Asc + Venus - Sun (same) |
| `Pars_Fidei` | Asc + Jupiter - Saturn | Asc + Jupiter - Saturn (same) |

### Special Points (4)

| Point | Description |
| :---- | :---------- |
| `Vertex` | A fated point on the western side of the chart |
| `Anti_Vertex` | The point opposite the Vertex |
| `Interpolated_Perigee` | Interpolated lunar perigee point |
| `White_Moon` | Selena / White Moon (hypothetical point) |

## Preset Configurations

Kerykeion provides three preset lists you can import and use directly.

### `DEFAULT_ACTIVE_POINTS` (14 points)

The default configuration used when no `active_points` parameter is specified.

Includes: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, True_North_Lunar_Node, Chiron, Ascendant, Medium_Coeli.

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

### `ALL_ACTIVE_POINTS` (53 points)

Every non-star active point enabled. Useful for research or comprehensive analysis; configure fixed stars separately with `active_fixed_stars`.

```python
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_points=ALL_ACTIVE_POINTS,
)
```

## Custom Configuration

You can build your own list by combining any of the available point names:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

# Classical planets + asteroids + Part of Fortune
custom_points = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn",
    "Ceres", "Pallas", "Juno", "Vesta",
    "Pars_Fortunae",
    "Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli",
]

subject = AstrologicalSubjectFactory.from_birth_data(
    "Custom Points", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
    active_points=custom_points,
)

chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_points=custom_points,
)

# Access the Part of Fortune
print(f"Pars Fortunae: {subject.pars_fortunae.sign} at {subject.pars_fortunae.position:.2f}°")
```

## Diurnal / Nocturnal Detection

Since v5.8.0, the `AstrologicalSubjectModel` includes an `is_diurnal` boolean field. This determines whether the chart is a day chart (Sun above the horizon) or a night chart (Sun below). It is used internally for Arabic Parts calculation (for `Pars_Fortunae` and `Pars_Spiritus` the formula reverses in night charts; `Pars_Amoris` and `Pars_Fidei` use the same formula regardless of sect, as shown in the table above).

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Day or Night", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
)

print(f"Is diurnal chart: {subject.is_diurnal}")
```

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
