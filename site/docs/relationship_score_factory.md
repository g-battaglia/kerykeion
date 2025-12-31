---
title: 'Relationship Score Factory'
category: 'Analysis'
tags: ['docs', 'relationships', 'synastry', 'scores', 'kerykeion']
order: 8
---

# Relationship Score Factory

The `RelationshipScoreFactory` calculates a quantitative compatibility score between two subjects using the **Ciro Discepolo method**. It assigns points to specific inter-chart aspects and qualities.

## Basic Usage

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

-   `score_value` (float): The calculated number.
-   `score_description` (str): The category name.
-   `aspects` (list): All the aspects that contributed to the score.
-   `is_destiny_sign` (bool): Whether the "Destiny Sign" bonus was applied.
