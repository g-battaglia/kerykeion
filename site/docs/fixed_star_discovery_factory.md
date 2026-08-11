---
title: 'Fixed Star Discovery'
description: 'Dynamically discover fixed stars conjunct natal planets within a configurable orb.'
category: 'Advanced Calculations'
tags: ['docs', 'fixed-stars', 'discovery', 'conjunction', 'kerykeion']
order: 51
---

# Fixed Star Discovery

The `FixedStarDiscoveryFactory` dynamically discovers **fixed stars conjunct natal planets** within a configurable orb. Unlike the per-subject stars requested via `active_fixed_stars` (none are computed by default), this factory scans the full star catalog provided by the ephemeris backend and returns only stars that are within orb of at least one active point.

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, FixedStarDiscoveryFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 6, 15, 14, 30,
    lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
)

# Find fixed stars within 1 degree of any natal planet
stars = FixedStarDiscoveryFactory.find_prominent_stars(subject, orb=1.0)

for star in stars:
    print(f"{star.name}: {star.sign} {star.position:.2f} (mag: {star.magnitude})")
    print(f"  Conjunct: {star.near_point} (orb: {star.orb:.2f})")
```

## Methods

### `find_prominent_stars(subject, orb)`

Find fixed stars conjunct natal planets within the given orb.

| Parameter | Type                     | Default | Description                                   |
| :-------- | :----------------------- | :------ | :-------------------------------------------- |
| `subject` | AstrologicalSubjectModel | --      | A natal chart with a finite Julian Day        |
| `orb`     | float                    | 1.0     | Finite, non-negative maximum conjunction orb in degrees |

**Returns:** `List[KerykeionPointModel]` sorted by magnitude (brightest first).

## Return Fields

Each returned `KerykeionPointModel` is enriched with discovery metadata:

| Field         | Description                                    |
| :------------ | :--------------------------------------------- |
| `name`        | Star name from the catalog                     |
| `sign`        | Zodiac sign                                    |
| `position`    | Position within the sign (0-30)                |
| `abs_pos`     | Absolute ecliptic longitude (0-360)            |
| `magnitude`   | Apparent visual magnitude                      |
| `declination` | Equatorial declination                         |
| `house`       | House placement (if house cusps are available)  |
| `near_point`  | Name of the nearest conjunct natal planet      |
| `orb`         | Orb of the conjunction in degrees              |

## Catalog Source

The catalog is sourced from **libephemeris** (the default backend). On the swisseph backend, the factory requires `sefstars.txt` to be present in the ephemeris data path (see [Swiss Ephemeris Configuration](/content/docs/swisseph_configuration) for details).

Catalog enumeration uses immutable `FixedStarMetadataModel` entries containing
`name`, canonical `slug`, optional Hipparcos number, nomenclature, visual
magnitude, and `constellation` (the IAU three-letter abbreviation of the star's
constellation, e.g. `"Ori"` for Orion, derived from the nomenclature; `None` when
the star has no standard constellation assignment). Discovery results remain
enriched `KerykeionPointModel` objects as described above.

## Wider Orb Example

```python
# Scan with a wider orb to find more stars
stars = FixedStarDiscoveryFactory.find_prominent_stars(subject, orb=2.0)
print(f"Found {len(stars)} stars within 2 degrees of natal planets")
```

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
