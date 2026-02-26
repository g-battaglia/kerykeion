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

To calculate a score, create two `AstrologicalSubject` instances (one for each partner) and pass them to the factory.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.relationship_score_factory import RelationshipScoreFactory

# 1. Create Subjects
person_a = AstrologicalSubjectFactory.from_birth_data("Alice", 1990, 6, 15, 12, 0, "London", "GB")
person_b = AstrologicalSubjectFactory.from_birth_data("Bob", 1992, 8, 20, 14, 30, "Roma", "IT")

# 2. Calculate Score
factory = RelationshipScoreFactory(person_a, person_b)
score_model = factory.get_relationship_score()

print(f"Score: {score_model.score_value}")
print(f"Category: {score_model.score_description}")
```

**Expected Output:**

```text
Score: 18.0
Category: Very Important
```

You can also inspect which aspects contributed to the score:

```python
for aspect in score_model.aspects[:3]:
    print(f"{aspect.p1_name} {aspect.aspect} {aspect.p2_name}: +{aspect.score_contribution} points")
```

**Expected Output:**

```text
Sun conjunction Moon: +11 points
Venus trine Mars: +4 points
Moon sextile Ascendant: +4 points
```

## Constructor Parameters

| Parameter                | Type    | Default  | Description                                       |
| :----------------------- | :------ | :------- | :------------------------------------------------ |
| `first_subject`          | Model   | Required | First astrological subject.                       |
| `second_subject`         | Model   | Required | Second astrological subject.                      |
| `use_only_major_aspects` | `bool`  | `True`   | Only consider major aspects (conj, opp, sq, etc). |
| `axis_orb_limit`         | `float` | `None`   | Stricter orb for angles (Asc, MC).                |

## Score Categories

| Score       | Category         | Description                                     |
| :---------- | :--------------- | :---------------------------------------------- |
| **0 - 5**   | Minimal          | Low compatibility, few significant connections. |
| **5 - 10**  | Medium           | Moderate compatibility.                         |
| **10 - 15** | Important        | Strong compatibility, notable connections.      |
| **15 - 20** | Very Important   | High compatibility, significant harmony.        |
| **20 - 30** | Exceptional      | Outstanding compatibility.                      |
| **30+**     | Rare Exceptional | Extraordinary cosmic connection.                |

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
| **Other Sun/Moon**         | +4        | Other major aspects involving Luminaries.                     |

_Note: The system prioritizes "Luminaries" (Sun/Moon) and Angles._

## Return Model (`RelationshipScoreModel`)

The `get_relationship_score()` method returns a Pydantic model with:

- `score_value` (float): The calculated number.
- `score_description` (str): The category name.
- `aspects` (list): All the aspects that contributed to the score.
- `is_destiny_sign` (bool): Whether the "Destiny Sign" bonus was applied.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
