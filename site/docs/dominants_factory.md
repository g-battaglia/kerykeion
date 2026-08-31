---
title: 'Chart Dominants'
description: 'Compute a chart''s dominant planet, sign, element and quality with modern, Almuten Figuris, or elemental scoring schools.'
category: 'Analysis'
tags: ['docs', 'dominants', 'almuten', 'analysis', 'kerykeion']
order: 52
---

# Chart Dominants

The `DominantsFactory` computes the **dominants** of a chart -- the most emphasised planet, sign, element and quality -- using a selectable scoring school. It supports three built-in schools and fully custom strategies.

## Schools (strategies)

| Strategy            | Description                                                                 |
| :------------------ | :-------------------------------------------------------------------------- |
| `"modern"`          | Default. Weighted emphasis across planets, signs, elements and qualities.  |
| `"almuten_figuris"` | Traditional/medieval "Lord of the Geniture" via essential dignities.       |
| `"elemental"`       | Simple element and modality balance (weighted or pure count).              |
| custom              | Any object implementing the `DominantStrategy` protocol.                    |

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, DominantsFactory

subject = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")

dominants = DominantsFactory.from_subject(subject, strategy="modern")
print(dominants.dominant_planet, dominants.dominant_sign)
print(dominants.dominant_element, dominants.dominant_quality)
```

A convenience constructor builds the subject for you:

```python
dominants = DominantsFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30, lat=53.4084, lng=-2.9916, tz_str="Europe/London", online=False
)
```

## Methods

### `from_subject(subject, *, strategy="modern", active_points=None, distribution_method="weighted", custom_weights=None, include_accidental_dignities=False, include_score_breakdown=False)`

Compute the dominants of an already-calculated subject.

| Parameter                      | Type                                  | Default      | Description                                                                 |
| :----------------------------- | :------------------------------------ | :----------- | :-------------------------------------------------------------------------- |
| `subject`                      | `AstrologicalSubjectModel`            | --           | The natal/event chart to analyse.                                          |
| `strategy`                     | `"modern"`/`"almuten_figuris"`/`"elemental"` or `DominantStrategy` | `"modern"` | Built-in school name or a custom strategy object.                          |
| `active_points`                | list[str] or None                     | None         | Explicit subset of points (used by the elemental school).                  |
| `distribution_method`          | `"weighted"` / `"pure_count"`         | `"weighted"` | Element/modality tally mode.                                               |
| `custom_weights`               | dict[str, float] or None              | None         | Per-point weight overrides (case-insensitive names).                       |
| `include_accidental_dignities` | bool                                  | False        | Add the Almuten Figuris accidental-dignity layer.                          |
| `include_score_breakdown`      | bool                                  | False        | Populate `score_breakdown` with a per-rule audit trail.                    |

**Returns:** `DominantsModel`

### `from_birth_data(name, year, month, day, hour=12, minute=0, *, strategy="modern", ..., **subject_kwargs)`

A thin convenience over `from_subject` that first builds the subject from birth data (extra keyword args such as `lat`, `lng`, `tz_str`, `city`, `nation`, `online` are forwarded to `AstrologicalSubjectFactory`).

### `available_methods()`

Returns the sorted list of built-in strategy identifiers: `["almuten_figuris", "elemental", "modern"]`. Useful for building selectors or validating user input.

## Data Model

### `DominantsModel`

| Field               | Type            | Description                                              |
| :------------------ | :-------------- | :------------------------------------------------------ |
| `strategy_name`     | str             | Human-readable name of the strategy used.               |
| `method`            | `DominantMethod` or None | Built-in method identifier (or `None` for custom). |
| `planets`           | list[`DominantScoreModel`] | Ranked planetary/point dominants.              |
| `signs`             | list[`DominantScoreModel`] | Ranked sign dominants.                         |
| `elements`          | list[`DominantScoreModel`] | Ranked element dominants (Fire/Earth/Air/Water). |
| `qualities`         | list[`DominantScoreModel`] | Ranked mode/quality dominants (Cardinal/Fixed/Mutable). |
| `houses`            | list[`DominantScoreModel`] | Ranked house dominants.                        |
| `polarities`        | list[`DominantScoreModel`] | Ranked polarity dominants (Yang/Yin, i.e. masculine/feminine). |
| `hemispheres`       | list[`DominantScoreModel`] | Ranked hemisphere dominants (N/S, E/W).        |
| `quadrants`         | list[`DominantScoreModel`] | Ranked quadrant dominants.                     |
| `dominant_planet`   | str or None     | Convenience winner of `planets`.                        |
| `dominant_sign`     | `Sign` or None  | Convenience winner of `signs`.                          |
| `dominant_element`  | `Element` or None | Convenience winner of `elements`.                     |
| `dominant_quality`  | `Quality` or None | Convenience winner of `qualities`.                    |
| `dominant_house`    | `Houses` or None | Convenience winner of `houses`.                        |
| `score_breakdown`   | list[`DominantBreakdownItemModel`] | Per-rule audit trail; empty unless `include_score_breakdown=True`. |

Every category is always present as a list, so the shape of the model is the
same for every school: one that does not compute a category leaves the list
empty and the matching `dominant_*` winner `None` (the `elemental` school, for
instance, returns empty `planets` and `houses` and a `None` `dominant_planet`).

`DominantScoreModel` gives every ranked item a `name`, raw `score`, normalized
`percentage`, 1-based `rank`, and `is_dominant` flag. Each
`DominantBreakdownItemModel` records the scoring `category`, `target`, `rule`,
signed `points`, and optional detail. The `DominantMethod` literal contains the
three built-in identifiers.

Custom strategies implement the runtime-checkable `DominantStrategy` protocol.
Subclass `BaseDominantStrategy` when its shared validation and result-building
helpers are useful, or provide any independent object satisfying the protocol.

The related essential-dignity helper,
`get_triplicity_lords(element, is_diurnal)` from `kerykeion.dignities`, returns
a `TriplicityLordsModel` whose `primary`, `secondary`, and `participating`
rulers are ordered for the requested day/night sect. `element` is one of
`"Fire"`, `"Earth"`, `"Air"`, `"Water"` — anything else raises
`KerykeionException` — and `is_diurnal` selects which lord is `primary`:

```python
from kerykeion.dignities import get_triplicity_lords

lords = get_triplicity_lords("Fire", True)
print(lords.primary, lords.secondary, lords.participating)
```

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
