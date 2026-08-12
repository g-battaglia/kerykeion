---
title: 'Relationship Score'
tags: ['examples', 'relationships', 'synastry', 'scores', 'kerykeion']
order: 6
---

# Relationship

The `RelationshipScoreFactory` is a Python class within the Kerykeion library, designed to calculate the relevance of the relationship between two astrological subjects following the method of Ciro Discepolo. It evaluates the synastry aspects between two subjects and provides a numerical score along with a descriptive qualification.

### Description

The factory assigns a "relationship score" to two astrological subjects based on their synastry aspects. The scores are mapped to a descriptive qualification:

- **0 to 5**: Minimal relationship
- **5 to 10**: Medium relationship
- **10 to 15**: Important relationship
- **15 to 20**: Very important relationship
- **20 to 30**: Exceptional relationship
- **30 and above**: Rare exceptional relationship

The calculations consider aspects between planets (like Sun-Sun, Sun-Moon, Sun-Ascendant, etc.). Major aspects (conjunction, opposition, square, trine, sextile) are primarily used unless otherwise specified.

### Key Features

1. **Destiny Sign Evaluation**:
   - Adds 5 points if the subjects share the same Sun sign quality (cardinal, fixed, mutable).

2. **Major and Other Aspects**:
   - Evaluates specific planetary aspects with assigned point values.
   - Example aspects include:
     - Sun-Sun main and other aspects
     - Sun-Moon conjunction and other aspects
     - Sun-Ascendant aspects
     - Moon-Ascendant aspects
     - Venus-Mars aspects

3. **Relationship Description**:
   - Maps the final score to a descriptive qualification (e.g., "Minimal," "Important").
   
4. **Flexible Aspect Evaluation**:
   - Option to evaluate only major aspects or include all aspects.

5. **Result Model**:
   - Provides a structured output with score value, description, destiny sign status, and aspect details.

### Arguments

Constructor parameters:
- `first_subject` (AstrologicalSubjectModel): First subject instance.
- `second_subject` (AstrologicalSubjectModel): Second subject instance.
- `use_only_major_aspects` (bool, default=True): Consider only major aspects when True.
- `axis_orb_limit` (float, default=None): Stricter orb limit for angles (Ascendant, MC). When set, angular aspects must be within this orb.

### Output

Returns an instance of `RelationshipScoreModel` containing:
- `score_value` (`int`): The numerical relationship score.
- `score_description` (`RelationshipScoreDescription`): The descriptive qualification.
- `is_destiny_sign` (`bool`): Whether the subjects share the same Sun sign quality.
- `aspects` (`list[RelationshipScoreAspectModel]`): Synastry aspects with `p1_name`, `p2_name`, `aspect`, and `orbit`.
- `score_breakdown` (`list[ScoreBreakdownItemModel]`): Detailed breakdown of how each scoring rule contributed points.
- `subjects` (`list[AstrologicalSubjectModel]`): The two validated subject models.

### Example Usage

```python
from kerykeion import AstrologicalSubjectFactory, RelationshipScoreFactory

# Create two astrological subjects (offline example)
subject1 = AstrologicalSubjectFactory.from_birth_data(
    "Person A", 1993, 6, 10, 12, 15,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
)
subject2 = AstrologicalSubjectFactory.from_birth_data(
    "Person B", 1949, 6, 17, 9, 40,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London", online=False,
)

# Instantiate the factory and calculate
factory = RelationshipScoreFactory(subject1, subject2, use_only_major_aspects=True)
relationship_score = factory.get_relationship_score()

print(relationship_score)
```

### Example Output

```plaintext
RelationshipScoreModel(
    score_value=25,
    score_description='Exceptional',
    is_destiny_sign=True,
    aspects=[
        RelationshipScoreAspectModel(p1_name='Sun', p2_name='Sun', aspect='conjunction', orbit=6.27),
        RelationshipScoreAspectModel(p1_name='Sun', p2_name='Ascendant', aspect='sextile', orbit=1.97),
        RelationshipScoreAspectModel(p1_name='Moon', p2_name='Sun', aspect='trine', orbit=3.84),
        RelationshipScoreAspectModel(p1_name='Ascendant', p2_name='Moon', aspect='opposition', orbit=2.67)
    ],
    score_breakdown=[...],
    subjects=[<AstrologicalSubjectModel of Person A>, <AstrologicalSubjectModel of Person B>]
)
```

### Additional Notes

- To print the score on the chart itself, pass `show_relationship_score=True` to `ChartDrawer`. The line takes one of the two rows the synastry info panel leaves empty and reads `Relationship Score: 16 (Very Important)` — the number travels with its band, since a count of weighted contacts means nothing without the scale it sits on. It needs a score on the chart data, which `create_synastry_chart_data` computes unless `include_relationship_score=False`; a chart drawn from the generic factory path prints nothing rather than a zero it never measured.
- This implementation is based on the Ciro Discepolo method. Additional details can be found [here](http://www.cirodiscepolo.it/Articoli/Discepoloele.htm).
- Logging is available for debugging purposes, with detailed messages during aspect evaluations.

This class integrates seamlessly with Kerykeion factories and models.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
