---
title: 'Mutual Receptions'
description: 'Detect mutual receptions (domicile and exaltation) among the seven classical planets.'
category: 'Analysis'
tags: ['docs', 'mutual receptions', 'dignities', 'traditional', 'kerykeion']
order: 62
---

# Mutual Receptions

**`MutualReceptionsFactory`** detects **mutual receptions** among the seven classical planets (Sun through Saturn). A mutual reception occurs when two planets each occupy a sign ruled by the other:

- **Domicile reception**: planet A sits in a sign that planet B rules, and planet B sits in a sign that planet A rules.
- **Exaltation reception**: planet A sits in the sign of planet B's exaltation, and vice versa.

Receptions are deduplicated per pair (A↔B counted once) and listed separately by type.

Only terrestrial (geocentric/topocentric) perspectives are accepted — receptions are a dignity technique defined on sign placements as seen from Earth.

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, MutualReceptionsFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Jane", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)

receptions = MutualReceptionsFactory.from_subject(subject)
for r in receptions.receptions:
    print(f"{r.first_planet} ↔ {r.second_planet} (by {r.reception_type})")
```

## Methods

### `from_subject(subject)`

Collect domicile and exaltation mutual receptions.

| Parameter | Type                       | Default | Description                                                         |
| :-------- | :------------------------- | :------ | :------------------------------------------------------------------ |
| `subject` | `AstrologicalSubjectModel` | --      | Any chart carrying the classical planets. Absent planets are skipped.|

**Returns:** `MutualReceptionsModel`

**Raises:** `KerykeionException` when the chart's perspective is not terrestrial (heliocentric, barycentric, selenocentric or planetocentric).

## Data Models

### `MutualReceptionsModel`

| Field       | Type                          | Description                                                   |
| :---------- | :---------------------------- | :------------------------------------------------------------ |
| `receptions`| `list[MutualReceptionModel]`  | One entry per deduplicated pair and reception type.            |

### `MutualReceptionModel`

| Field           | Type                                | Description                                   |
| :-------------- | :---------------------------------- | :-------------------------------------------- |
| `first_planet`  | `ClassicalPlanet`                   | One planet of the pair.                       |
| `second_planet` | `ClassicalPlanet`                   | The other planet.                             |
| `reception_type`| `"domicile"` \| `"exaltation"`      | Which dignity table produces the reception.   |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
