---
title: 'Relationship Score Factory'
description: 'Quantify relationship compatibility with the Relationship Score Factory. Implementation of the Ciro Discepolo method for numerical synastry analysis.'
category: 'Analysis'
tags: ['docs', 'relationships', 'synastry', 'scores', 'kerykeion']
order: 8
---

# Relationship Score Factory

The `RelationshipScoreFactory` calculates a quantitative compatibility score between two subjects using the **Ciro Discepolo method**. It assigns points to specific inter-chart aspects and qualities. This is the unchanged v1 API; the explicit [v2 opt-in](#opt-in-v2-since-61) is described below.

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

## Opt-in v2 (since 6.1)

Import `RelationshipScoreFactoryV2` from `kerykeion.relationship_score.v2` to use
the new fixed profile with two Tropical, Apparent Geocentric subjects. Each must
contain Sun, Moon, Ascendant, Venus and Mars. The constructor snapshots its inputs;
each `get_relationship_score()` call returns independent data. The existing
`RelationshipScoreFactory` and its configuration options keep their v1 behavior.

For calculations from known longitudes, use the pure numerical entry point.
Both subjects must supply Tropical, Apparent Geocentric longitudes: bare
numbers cannot verify their reference frame.

```python
from kerykeion.relationship_score.v2 import score_positions

first_positions = {"Sun": 10.0, "Moon": 53.0, "Ascendant": 101.0, "Venus": 203.0, "Mars": 254.0}
second_positions = {"Sun": 47.0, "Moon": 167.0, "Ascendant": 283.0, "Venus": 321.0, "Mars": 15.0}
v2_score = score_positions(first_positions, second_positions)
assert v2_score.score_value == sum(row.points for row in v2_score.score_breakdown)
print(v2_score.model_dump_json())
```

The profile evaluates all nine Sun/Moon/Ascendant pairs and both Venus–Mars
directions. Sun–Sun square/opposition and cross Sun–Moon conjunction receive an
8/11-point award replacing the ordinary four points. Sun–Sun conjunction is an
ordinary four-point contact. A special Sun–Sun award suppresses the matching
solar-modality bonus; other modality matches receive five points once.

The inclusive scoring orbs are conjunction 8°, semi-sextile 2°, semi-square 2°,
sextile 3°, square 5°, trine 7°, sesquiquadrate 2° and opposition 8°. Quintile and
quincunx do not score. The absolute longitude difference is rounded down before
wrapping values above 190°. Consequently a physical residual of 2.99° can earn
the tight-orb award. This is an explicit implementation policy, not a claim of
literal agreement with every published edition of the method.

`RelationshipScoreV2Model` extends the v1 result with `positions`, `subject_names`,
`contacts`, `metadata` and destiny-award/suppression flags. `ScoreContactV2Model`
retains unrounded physical `distance`/`orbit` separately from the `scoring_*`
values used for points. `ScoreMetadataV2Model.reference_verified` remains false:
the rule tests do not establish complete independent reference-output parity.
All three models are also available from `kerykeion.schemas` and
`kerykeion.relationship_score`, as lazy exports of the same classes.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
