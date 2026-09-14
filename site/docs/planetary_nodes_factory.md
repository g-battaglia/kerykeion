---
title: 'Planetary Nodes & Apsides'
description: 'Calculate ascending/descending orbital nodes and the periapsis/apoapsis of any planet or the Moon.'
category: 'Advanced Calculations'
tags: ['docs', 'nodes', 'apsides', 'periapsis', 'apoapsis', 'perigee', 'apogee', 'kerykeion']
order: 47
---

# Planetary Nodes & Apsides

The `PlanetaryNodesFactory` calculates **orbital nodes** (where the orbit crosses the ecliptic) and **apsides** (the closest and farthest points of the orbit) for any planet, and for the Moon.

## Concepts

- **Ascending Node**: where the orbit crosses the ecliptic northward
- **Descending Node**: where the orbit crosses the ecliptic southward
- **Periapsis**: closest point of the orbit to the body it goes round
- **Apoapsis**: farthest point of the orbit from that body

The apsides are exposed under two pairs of names holding the same two points. `periapsis` / `apoapsis` are generic and always correct. `perihelion` / `aphelion` are the older fields, **deprecated**: they name the Sun, which is right for the eight planets and wrong for the Moon, which goes round the Earth. They are still populated with the very same objects, so the two names can never drift apart and nothing that reads them breaks.

`apsis_kind` says which reading applies: `"heliocentric"` for every planet, `"geocentric"` for the Moon alone. The Moon's apsides are the perigee and the apogee, and the far one is to the decimal the point the tradition calls the Black Moon Lilith — `mean_lilith` with `method="mean"`, `true_lilith` with `method="osculating"`.

Two calculation methods are available:
- **Mean**: average orbital elements (smoother, used for long-term analysis)
- **Osculating**: instantaneous orbital elements (more precise for a given moment)

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, PlanetaryNodesFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 6, 15, 14, 30,
    lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
)

results = PlanetaryNodesFactory.from_subject(subject, method="mean")

for node in results.nodes:
    print(f"\n{node.planet_name}:")
    print(f"  Ascending Node:  {node.ascending_node.sign} {node.ascending_node.position:.2f}")
    print(f"  Descending Node: {node.descending_node.sign} {node.descending_node.position:.2f}")
    print(f"  Periapsis:       {node.periapsis.sign} {node.periapsis.position:.2f}")
    print(f"  Apoapsis:        {node.apoapsis.sign} {node.apoapsis.position:.2f} ({node.apsis_kind})")
```

The Moon's apogee and the Black Moon Lilith are one point:

```python
from kerykeion import AstrologicalSubjectFactory, PlanetaryNodesFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 6, 15, 14, 30,
    lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
    active_points=["Sun", "Moon", "Mean_Lilith"],
)
moon = PlanetaryNodesFactory.from_subject(subject, method="mean", planets=["Moon"]).nodes[0]
print(moon.apsis_kind)                                       # geocentric
print(moon.apoapsis.abs_pos == subject.mean_lilith.abs_pos)   # True
```

## Methods

### `from_subject(subject, method, planets)`

Calculate nodes from an existing astrological subject.

The node and apsis longitudes -- and the sign metadata derived from them --
are computed in the subject's own zodiac frame: a sidereal subject gets
sidereal longitudes, consistent with the rest of its chart.

| Parameter | Type                     | Default | Description                                |
| :-------- | :----------------------- | :------ | :----------------------------------------- |
| `subject` | AstrologicalSubjectModel | --      | An astrological subject with a Julian Day (composites are rejected) |
| `method`  | str                      | "mean"  | "mean" or "osculating"; any other value raises `KerykeionException` |
| `planets` | List[str] or None        | None    | Planet names (defaults to Moon through Pluto; an unknown name raises `ValueError`). The Sun is deliberately excluded — it has no geocentric nodes — and requesting it raises `KerykeionException` |

**Returns:** `PlanetaryNodesCollectionModel`

### `from_julian_day(julian_day, method, planets)`

Calculate nodes from a Julian Day number. A bare instant carries no zodiac
frame, so the longitudes are always tropical -- pass a subject to
`from_subject` when sidereal ones are wanted.

| Parameter    | Type              | Default | Description            |
| :----------- | :---------------- | :------ | :--------------------- |
| `julian_day` | float             | --      | Finite Julian Day number |
| `method`     | str               | "mean"  | "mean" or "osculating"; any other value raises `KerykeionException` |
| `planets`    | List[str] or None | None    | Planet names; an unknown name raises `ValueError`, and "Sun" raises `KerykeionException` |

**Returns:** `PlanetaryNodesCollectionModel`

## Data Models

### `PlanetaryNodeModel`

| Field              | Type               | Description                   |
| :----------------- | :----------------- | :---------------------------- |
| `planet_name`      | str                | Planet name                   |
| `ascending_node`   | KerykeionPointModel | Ascending node position      |
| `descending_node`  | KerykeionPointModel | Descending node position     |
| `periapsis`        | KerykeionPointModel | Closest point of the orbit to the body it goes round |
| `apoapsis`         | KerykeionPointModel | Farthest point of the orbit from that body |
| `apsis_kind`       | ApsisKind           | `"heliocentric"` (every planet) or `"geocentric"` (the Moon) |
| `perihelion`       | KerykeionPointModel | **Deprecated**, use `periapsis`. Same object |
| `aphelion`         | KerykeionPointModel | **Deprecated**, use `apoapsis`. Same object |

### `PlanetaryNodesCollectionModel`

| Field          | Type                     | Description                               |
| :------------- | :----------------------- | :---------------------------------------- |
| `iso_datetime` | str                      | ISO datetime of the moment                |
| `julian_day`   | float                    | Julian Day number                         |
| `method`       | str                      | Calculation method: "mean" or "osculating"|
| `nodes`        | List[PlanetaryNodeModel] | Nodes for each planet                     |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more ->](/content/docs/astrologer-api)
