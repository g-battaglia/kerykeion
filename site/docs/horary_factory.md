---
title: 'Horary Indicators'
description: 'Assemble horary significators, classical considerations before judgment, and mutual receptions for a question chart.'
category: 'Analysis'
tags: ['docs', 'horary', 'significators', 'considerations', 'traditional', 'kerykeion']
order: 63
---

# Horary Indicators

**`HoraryIndicatorsFactory`** assembles the core components an astrologer evaluates when reading a horary chart: the **significators** of the querent (1st house) and quesited (7th house), the **classical considerations before judgment**, and the **mutual receptions** among classical planets.

The Ascendant degree is read from the true Ascendant point (not the first-house cusp), so Whole Sign charts — where the cusp sits at 0° of the rising sign — are correctly handled.

Only terrestrial (geocentric/topocentric) perspectives are accepted.

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, HoraryIndicatorsFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Question", 2026, 6, 4, 15, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)

indicators = HoraryIndicatorsFactory.from_subject(subject, is_moon_void=False)
print(f"Querent ruler: {indicators.querent.ruler}")
print(f"Quesited ruler: {indicators.quesited.ruler}")
for c in indicators.considerations:
    print(f"  [{c.status}] {c.key}")
```

## Methods

### `from_subject(subject, *, is_moon_void=None)`

Build the indicators for a question chart.

| Parameter     | Type                       | Default | Description                                                                                                     |
| :------------ | :------------------------- | :------ | :-------------------------------------------------------------------------------------------------------------- |
| `subject`     | `AstrologicalSubjectModel` | --      | The chart cast for the moment of the question.                                                                  |
| `is_moon_void`| `bool \| None`             | None    | Whether the Moon is void of course (from a separate void-of-course calculation). `None` omits the Moon void considerations. |

**Returns:** `HoraryIndicatorsModel`

**Raises:** `KerykeionException` when the chart's perspective is not terrestrial.

## Data Models

### `HoraryIndicatorsModel`

| Field               | Type                              | Description                                                    |
| :------------------ | :-------------------------------- | :------------------------------------------------------------- |
| `querent`           | `HorarySignificatorModel`         | Significator of the 1st house.                                 |
| `quesited`          | `HorarySignificatorModel`         | Significator of the 7th house.                                 |
| `ascendant_degree`  | `float \| None`                   | Ascendant degree within its sign (0-30), from the true Ascendant point. |
| `considerations`    | `list[HoraryConsiderationModel]`  | Classical considerations before judgment.                      |
| `mutual_receptions` | `list[MutualReceptionModel]`      | Mutual receptions among the classical planets.                 |

### `HorarySignificatorModel`

| Field              | Type                  | Description                                                   |
| :----------------- | :-------------------- | :------------------------------------------------------------ |
| `house`            | `int`                 | House the significator describes (1 = querent, 7 = quesited). |
| `sign`             | `Sign \| None`        | Sign on that house cusp.                                      |
| `ruler`            | `ClassicalPlanet \| None` | Traditional ruler of that sign — the significator planet.  |
| `ruler_sign`       | `Sign \| None`        | Sign the ruler occupies in the chart.                         |
| `ruler_house`      | `Houses \| None`      | House the ruler occupies.                                     |
| `ruler_house_number` | `int \| None`       | Same house as a number (1-12).                                |
| `ruler_retrograde` | `bool \| None`        | Whether the ruler is retrograde.                              |
| `essential_dignity` | `str \| None`        | The ruler's essential dignity (requires `calculate_dignities=True`). |

### `HoraryConsiderationModel`

The model carries a stable key, not display prose: wording belongs to the consuming product (and its active school), the engine states the fact.

| Field    | Type     | Description                                    |
| :------- | :------- | :--------------------------------------------- |
| `key`    | Literal  | Which consideration fired (see table below).   |
| `status` | Literal  | Classical reading: `"favorable"`, `"caution"`, or `"neutral"`. |

**Consideration keys:**

| Key                  | Status      | Meaning                                              |
| :------------------- | :---------- | :--------------------------------------------------- |
| `asc_early_degree`   | `caution`   | Ascendant < 3° — the matter may be too early to judge. |
| `asc_late_degree`    | `caution`   | Ascendant ≥ 27° — the matter may already be decided. |
| `asc_judgeable`      | `favorable` | Ascendant at a judgeable degree.                     |
| `moon_void`          | `caution`   | Moon is void of course.                              |
| `moon_not_void`      | `favorable` | Moon is not void of course.                          |
| `saturn_in_first`    | `caution`   | Saturn in the 1st house.                             |
| `saturn_in_seventh`  | `caution`   | Saturn in the 7th house.                             |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
