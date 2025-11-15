---
layout: ../../layouts/DocLayout.astro
title: 'Relationship Score'
---

# Relationship

The `RelationshipScoreFactory` is a Python class within the Kerykeion library, designed to calculate the relevance of the relationship between two astrological subjects following the method of Ciro Discepolo. It evaluates the synastry aspects between two subjects and provides a numerical score along with a descriptive qualification.

### Description

The factory assigns a "relationship score" to two astrological subjects based on their synastry aspects. The scores are mapped to a descriptive qualification:

- **0 to 5**: Minimal relationship
- **5 to 10**: Medium relationship
- **10 to 15**: Important relationship
- **15 to 20**: Very important relationship
- **20 to 35**: Exceptional relationship
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

### Output

Returns an instance of `RelationshipScoreModel` containing:
- `score_value`: The numerical relationship score.
- `score_description`: The descriptive qualification.
- `is_destiny_sign`: Whether the subjects share the same Sun sign quality.
- `aspects`: A list of `RelationshipScoreAspectModel` detailing the synastry aspects.
- `subjects`: The two validated subject models.

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
    score_value=18,
    score_description='Very Important',
    is_destiny_sign=True,
    aspects=[
        RelationshipScoreAspectModel(p1_name='Sun', p2_name='Sun', aspect='conjunction', orbit=1.5),
        RelationshipScoreAspectModel(p1_name='Sun', p2_name='Moon', aspect='sextile', orbit=2.1),
        RelationshipScoreAspectModel(p1_name='Venus', p2_name='Mars', aspect='trine', orbit=3.4)
    ],
    subjects=[<AstrologicalSubjectModel of Person A>, <AstrologicalSubjectModel of Person B>]
)
```

### Additional Notes

- This implementation is based on the Ciro Discepolo method. Additional details can be found [here](http://www.cirodiscepolo.it/Articoli/Discepoloele.htm).
- Logging is available for debugging purposes, with detailed messages during aspect evaluations.

This class integrates seamlessly with Kerykeion v5 factories and models.
