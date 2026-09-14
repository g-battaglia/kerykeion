---
title: 'Relationship Score Factory'
description: 'Quantify relationship compatibility with the Relationship Score Factory. Implementation of the Ciro Discepolo method for numerical synastry analysis.'
category: 'Analysis'
tags: ['docs', 'relationships', 'synastry', 'scores', 'kerykeion']
order: 8
---

# Relationship Score Factory

The `RelationshipScoreFactory` calculates a quantitative compatibility score between two subjects using the **Ciro Discepolo method**. It assigns points to specific inter-chart aspects and qualities.

## What Is Relationship Scoring?

While most synastry analysis is qualitative (describing the nature of aspects), the **Discepolo method** provides a numerical compatibility score. This score focuses on traditional "destiny indicators":

**The Method Prioritizes:**

- **Luminaries** (Sun and Moon) - Core identity and emotional nature
- **Angles** (Ascendant, MC) - How individuals meet the world
- **Venus-Mars** - Romantic and sexual compatibility
- **Orb Precision** - Tighter aspects score higher (±2° gets bonus points)
- **Quality Matching** - Same modality (Cardinal/Fixed/Mutable) adds points

This numerical approach is useful for:

- Comparing multiple potential partners objectively
- Research into relationship longevity patterns
- Quick compatibility screening in dating applications

## Basic Usage

To calculate a score, create two astrological subjects via `AstrologicalSubjectFactory` (one for each partner) and pass them to the factory.

```python
from kerykeion import AstrologicalSubjectFactory, RelationshipScoreFactory

# 1. Create Subjects (offline mode: explicit coordinates, no GeoNames lookup)
person_a = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    lng=-0.1278, lat=51.5074, tz_str="Europe/London", online=False,
)
person_b = AstrologicalSubjectFactory.from_birth_data(
    "Bob", 1992, 8, 20, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
)

# 2. Calculate Score
factory = RelationshipScoreFactory(person_a, person_b)
score_model = factory.get_relationship_score()

print(f"Score: {score_model.score_value}")
print(f"Category: {score_model.score_description}")
```

**Expected Output:**

```text
Score: 8
Category: Medium
```

You can also inspect which aspects contributed to the score:

```python
for aspect in score_model.aspects[:3]:
    print(f"{aspect.p1_name} {aspect.aspect} {aspect.p2_name} (orb: {aspect.orbit}°)")
```

**Expected Output:**

```text
Sun sextile Sun (orb: 3.6354400137083758°)
Ascendant trine Moon (orb: 2.242423320728676°)
```

## Constructor Parameters

| Parameter                | Type    | Default  | Description                                       |
| :----------------------- | :------ | :------- | :------------------------------------------------ |
| `first_subject`          | Model   | Required | First astrological subject.                       |
| `second_subject`         | Model   | Required | Second astrological subject.                      |
| `use_only_major_aspects` | `bool`  | `True`   | Only consider major aspects (conj, opp, sq, etc). |
| `axis_orb_limit`         | `float` | `None`   | Finite, positive stricter orb for angles (Asc, MC). Keyword-only.  |

## Raises

`KerykeionException` is raised when:

- The two subjects do not share the same reference frame — zodiac type,
  perspective type, and (for sidereal charts) sidereal mode. The check runs in
  the constructor, before any aspect is computed. House systems are not
  compared, and are allowed to differ.
- Either input is not a subject-like model at all (it does not expose the frame
  attributes).
- `axis_orb_limit` is given but is not a finite, positive number.
- Either subject was built without the Sun in its active points. The Discepolo
  method is defined on the Sun (destiny sign) and the luminary aspects, so
  `get_relationship_score()` fails rather than returning a partial score.

## Score Categories

Each bound is strict: a category applies while `score_value` is **below** its
threshold, so a score of exactly 5 is Medium, and exactly 20 is Exceptional.

| Score         | Category         | Description                                     |
| :------------ | :--------------- | :---------------------------------------------- |
| **< 5**       | Minimal          | Low compatibility, few significant connections. |
| **5 - < 10**  | Medium           | Moderate compatibility.                         |
| **10 - < 15** | Important        | Strong compatibility, notable connections.      |
| **15 - < 20** | Very Important   | High compatibility, significant harmony.        |
| **20 - < 30** | Exceptional      | Outstanding compatibility.                      |
| **>= 30**     | Rare Exceptional | Extraordinary cosmic connection.                |

## Scoring System Details

The algorithm awards points for specific "Destiny" indicators and aspects.

| Indicator                  | Points    | Note                                                          |
| :------------------------- | :-------- | :------------------------------------------------------------ |
| **Destiny Sign**           | +5        | If Sun signs share the same quality (Cardinal/Fixed/Mutable). |
| **Sun-Sun** (Conj/Opp/Sqr) | +8 or +11 | +11 if orb ≤ 2°, else +8.                                     |
| **Sun-Moon** (Conj)        | +8 or +11 | +11 if orb ≤ 2°, else +8.                                     |
| **Sun-Ascendant**          | +4        | Any major aspect.                                             |
| **Moon-Ascendant**         | +4        | Any major aspect.                                             |
| **Venus-Mars**             | +4        | Any major aspect.                                             |
| **Sun-Sun** (other)        | +4        | Any Sun-Sun aspect other than conjunction, opposition or square. |
| **Sun-Moon** (other)       | +4        | Any Sun-Moon aspect other than conjunction.                   |

_Note: The system prioritizes "Luminaries" (Sun/Moon) and Angles. Moon-Moon
aspects carry no rule and score nothing._

## Return Model (`RelationshipScoreModel`)

The `get_relationship_score()` method returns a Pydantic model with:

- `score_value` (`int`): The calculated score.
- `score_description` (`RelationshipScoreDescription`): The category name (e.g. `"Very Important"`).
- `is_destiny_sign` (`bool`): Whether the "Destiny Sign" bonus was applied.
- `aspects` (`list[RelationshipScoreAspectModel]`): Aspects that contributed to the score. Each has `p1_name`, `p2_name`, `aspect`, and `orbit`.
- `score_breakdown` (`list[ScoreBreakdownItemModel]`): Detailed breakdown of how each rule contributed points.
- `subjects` (`list[AstrologicalSubjectModel]`): The two validated subject models.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
