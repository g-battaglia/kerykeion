---
title: 'Vedic Nakshatras'
description: 'Nakshatra, pada and Vimshottari lord calculation for sidereal charts and tropical charts with an explicit ayanamsa.'
category: 'Analysis'
tags: ['docs', 'vedic', 'nakshatra', 'sidereal', 'kerykeion']
order: 42
---

# Vedic Nakshatras

**Nakshatras** divide the sidereal zodiac into 27 equal segments of 13°20'.
Kerykeion computes them in `kerykeion/vedic` via `calculate_nakshatra()`, which
takes a sidereal longitude and returns the nakshatra name, number (1–27), pada
(quarter 1–4) and Vimshottari Dasha lord. The function applies no ayanamsa of
its own: the caller must hand it a sidereal longitude.

## Basic Usage

On a sidereal chart, opt in with `calculate_nakshatra=True`:

```python
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Jane", 1990, 7, 15, 10, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
    online=False, zodiac_type="Sidereal", sidereal_mode="LAHIRI",
    calculate_nakshatra=True,
)

print(subject.moon.nakshatra, subject.moon.nakshatra_pada, subject.moon.nakshatra_lord)
```

On a non-sidereal chart the same flag works, but the nakshatras are placed with
`nakshatra_ayanamsa` (default Lahiri): a tropical longitude passed in raw would
land about two nakshatras off, so always set the ayanamsa explicitly.

Each point then carries `nakshatra`, `nakshatra_number`, `nakshatra_pada` and
`nakshatra_lord`; the subject records which ayanamsa was used in
`nakshatra_ayanamsa` / `nakshatra_ayanamsa_value`.

Related: [Astrological Subject Factory](/content/docs/astrological_subject_factory),
[Sidereal Modes](/content/examples/sidereal-modes), [Schemas](/content/docs/schemas).
