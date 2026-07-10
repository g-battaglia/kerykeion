---
title: 'Planetary Nodes & Apsides'
description: 'Calculate ascending/descending orbital nodes and perihelion/aphelion for any planet.'
category: 'Advanced Calculations'
tags: ['docs', 'nodes', 'apsides', 'perihelion', 'aphelion', 'kerykeion']
order: 47
---

# Planetary Nodes & Apsides

The `PlanetaryNodesFactory` calculates **planetary orbital nodes** (where the orbit crosses the ecliptic) and **apsides** (closest and farthest points from the Sun) for any planet.

## Concepts

- **Ascending Node**: where the orbit crosses the ecliptic northward
- **Descending Node**: where the orbit crosses the ecliptic southward
- **Perihelion**: closest point to the Sun
- **Aphelion**: farthest point from the Sun

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
    print(f"  Perihelion:      {node.perihelion.sign} {node.perihelion.position:.2f}")
    print(f"  Aphelion:        {node.aphelion.sign} {node.aphelion.position:.2f}")
```

## Methods

### `from_subject(subject, method, planets)`

Calculate nodes from an existing astrological subject.

| Parameter | Type                     | Default | Description                                |
| :-------- | :----------------------- | :------ | :----------------------------------------- |
| `subject` | AstrologicalSubjectModel | --      | An astrological subject                    |
| `method`  | str                      | "mean"  | "mean" or "osculating"                     |
| `planets` | List[str] or None        | None    | Planet names (defaults to Moon through Pluto; the Sun is deliberately excluded — it has no geocentric nodes) |

**Returns:** `PlanetaryNodesCollectionModel`

### `from_julian_day(julian_day, method, planets)`

Calculate nodes from a Julian Day number.

| Parameter    | Type              | Default | Description            |
| :----------- | :---------------- | :------ | :--------------------- |
| `julian_day` | float             | --      | Julian Day number      |
| `method`     | str               | "mean"  | "mean" or "osculating" |
| `planets`    | List[str] or None | None    | Planet names           |

**Returns:** `PlanetaryNodesCollectionModel`

## Data Models

### `PlanetaryNodeModel`

| Field              | Type               | Description                   |
| :----------------- | :----------------- | :---------------------------- |
| `planet_name`      | str                | Planet name                   |
| `ascending_node`   | KerykeionPointModel | Ascending node position      |
| `descending_node`  | KerykeionPointModel | Descending node position     |
| `perihelion`       | KerykeionPointModel | Perihelion position          |
| `aphelion`         | KerykeionPointModel | Aphelion position            |

### `PlanetaryNodesCollectionModel`

| Field          | Type                     | Description                               |
| :------------- | :----------------------- | :---------------------------------------- |
| `iso_datetime` | str                      | ISO datetime of the moment                |
| `julian_day`   | float                    | Julian Day number                         |
| `method`       | str                      | Calculation method: "mean" or "osculating"|
| `nodes`        | List[PlanetaryNodeModel] | Nodes for each planet                     |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more ->](/content/docs/astrologer-api)
