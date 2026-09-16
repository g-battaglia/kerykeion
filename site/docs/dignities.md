---
title: 'Essential Dignities'
description: 'Ptolemaic essential dignities — domicile, exaltation, triplicity, terms, face, detriment and fall — with scores.'
category: 'Analysis'
tags: ['docs', 'dignities', 'essential dignities', 'traditional', 'kerykeion']
order: 41
---

# Essential Dignities

**Essential dignities** evaluate how well a planet expresses itself in its zodiacal
position. Kerykeion implements the Ptolemaic scoring in `kerykeion.dignities`:

| Score | Dignity |
| :--- | :--- |
| +5 | Domicile (planet rules the sign) |
| +4 | Exaltation |
| +3 | Triplicity (by sect) |
| +2 | Term (Egyptian bounds) |
| +1 | Face (Chaldean decan) |
| 0 | Peregrine (no dignity) |
| −4 | Fall |
| −5 | Detriment |

## Basic Usage

Opt in per subject with `calculate_dignities=True`. Each point then carries
`essential_dignity` (highest active dignity) and `dignity_score` (sum of every
applicable dignity):

```python
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Jane", 1990, 7, 15, 10, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
    online=False, calculate_dignities=True,
)

print(subject.sun.essential_dignity, subject.sun.dignity_score)
```

Triplicity is sect-aware (day/night rulers from `triplicity_lords.py`), terms use
the Egyptian bounds and faces the Chaldean decans. Detriment and fall are derived
from the domicile and exaltation tables in `kerykeion/dignities/data.py`.

## Standalone functions

For one-off evaluation without building a subject:

```python
from kerykeion.dignities import calculate_essential_dignity

print(calculate_essential_dignity("Sun", "Leo", "Fire", 12.5, is_diurnal=True))
```

Related: [Astrological Subject Factory](/content/docs/astrological_subject_factory),
[Active Points](/content/docs/active_points), [Schemas](/content/docs/schemas).
