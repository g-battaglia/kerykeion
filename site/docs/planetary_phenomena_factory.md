---
title: 'Planetary Phenomena Factory'
description: 'Calculate observational planetary phenomena: elongation, illumination, phase angle, apparent magnitude, morning/evening star status, and the solar phase.'
category: 'Advanced Calculations'
tags: ['docs', 'phenomena', 'elongation', 'magnitude', 'cazimi', 'combust', 'kerykeion']
order: 46
---

# Planetary Phenomena Factory

The `PlanetaryPhenomenaFactory` calculates **observational phenomena** for planets using the ephemeris backend's `ephe.pheno_ut()` function (libephemeris by default). It computes elongation, illumination fraction, phase angle, apparent diameter/magnitude, morning/evening star status, and the body's condition relative to the Sun (`solar_phase`).

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, PlanetaryPhenomenaFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 2025, 4, 1, 12, 0,
    lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
)

results = PlanetaryPhenomenaFactory.from_subject(subject)

for p in results.phenomena:
    print(f"{p.name}: elongation={p.elongation:.1f}, mag={p.apparent_magnitude:.1f}")
    if p.is_morning_star:
        print(f"  Morning star")
    elif p.is_evening_star:
        print(f"  Evening star")
    if p.solar_phase != "free":
        print(f"  {p.solar_phase}")
```

## Solar Phase

Every phenomenon carries `solar_phase`: the classical reading of how near the Sun a body stands, as a condition of visibility rather than a bare number of degrees.

| Value               | Meaning                                                  | Default cut-off |
| :------------------ | :------------------------------------------------------- | :-------------- |
| `"cazimi"`          | In the heart of the Sun                                   | below 0.2833° (17 arcminutes) |
| `"combust"`         | Burnt — close enough that the body cannot be seen at all  | below 8.5°      |
| `"under_the_beams"` | Within the Sun's rays; not yet out of the twilight        | below 17°       |
| `"free"`            | Far enough from the Sun to be seen in a dark sky          | 17° or more     |

The label is read off the same rounded `elongation` the model publishes, so a value that rounds onto a cut-off is never named one thing in the field and another in the phase. The comparisons are strict: a body sitting exactly on a cut-off takes the outer name. The quantity compared is the **true angular separation** the ephemeris reports, latitude included — not the difference in ecliptic longitude, which is what the tradition's tables were built on. The two part company for a body off the ecliptic.

The three cut-offs are conventions, not measurements, and the schools disagree on all three. Pass your own `SolarPhaseThresholdsModel` to either constructor; the instance actually used is echoed on the returned collection, so a consumer never has to guess which convention produced a label. A set that does not widen outwards is rejected.

```python
from kerykeion import PlanetaryPhenomenaFactory
from kerykeion.schemas import SolarPhaseThresholdsModel

# Venus at its 2024 superior conjunction.
default = PlanetaryPhenomenaFactory.from_julian_day(2460466.0, planets=["Venus"])
print(default.phenomena[0].solar_phase, round(default.phenomena[0].elongation, 3))
# cazimi 0.077

strict = PlanetaryPhenomenaFactory.from_julian_day(
    2460466.0, planets=["Venus"],
    solar_phase_thresholds=SolarPhaseThresholdsModel(cazimi_deg=0.05),
)
print(strict.phenomena[0].solar_phase)          # combust
print(strict.solar_phase_thresholds.cazimi_deg)  # 0.05
```

The phase is named for every supported body, the Moon included: its elongation is the same astronomical quantity, and the names still describe what they always describe — the dark of the Moon is exactly the interval in which it is under the beams. What a given school does with a combust Moon is the school's business, not the library's.

A central solar eclipse is **not** a promise of `"cazimi"`, and the reason is the frame. The published `elongation` is **geocentric**; an eclipse is a **topocentric** alignment, seen by an observer standing under the shadow, and lunar parallax between the two reaches about a degree. The 2026-08-12 total eclipse bottoms out at a geocentric `0.891865°` — `"combust"` — while the 2027-08-02 totality reaches `0.144957°` and does read `"cazimi"`. Cazimi at the moment of totality is what the observer under the shadow sees; the number this factory publishes is what the Earth's centre sees.

`is_morning_star` and `is_evening_star` are a different question, and are **purely geometric**: which side of the Sun the planet stands on in longitude, with no visibility threshold of any kind. A planet one degree from the Sun is still an "evening star" there — invisible, but east of it. Read `solar_phase` for whether it can be seen.

## Methods

### `from_subject(subject, planets, solar_phase_thresholds)`

Calculate phenomena from an existing astrological subject.

| Parameter | Type                     | Default | Description                      |
| :-------- | :----------------------- | :------ | :------------------------------- |
| `subject` | AstrologicalSubjectModel | --      | An astrological subject          |
| `planets` | List[str] or None        | None    | Planet names (defaults to all)   |
| `solar_phase_thresholds` | SolarPhaseThresholdsModel or None | None | Cut-offs for `solar_phase`; defaults to the classical 0.2833° / 8.5° / 17° |

**Returns:** `PlanetaryPhenomenaCollectionModel`

**Raises:** `KerykeionException` if the subject has no Julian Day — a composite
subject has no single moment in time and is not supported here. An unknown or
mistyped planet name raises `ValueError` (names are case-sensitive).

### `from_julian_day(julian_day, planets, solar_phase_thresholds)`

Calculate phenomena from a Julian Day number.

| Parameter    | Type              | Default | Description                    |
| :----------- | :---------------- | :------ | :----------------------------- |
| `julian_day` | float             | --      | Finite Julian Day number       |
| `planets`    | List[str] or None | None    | Planet names (defaults to all) |
| `solar_phase_thresholds` | SolarPhaseThresholdsModel or None | None | Cut-offs for `solar_phase`; defaults to the classical 0.2833° / 8.5° / 17° |

**Returns:** `PlanetaryPhenomenaCollectionModel`

**Raises:** `ValueError` for an unknown or mistyped planet name (names are
case-sensitive) or a non-finite `julian_day`, and `KerykeionException` if every
requested planet fails, which usually means the ephemeris backend is unavailable
or the moment is out of its range.

## Supported Planets

Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto.

Morning/evening star status is calculated only for the inferior planets (Mercury, Venus).

## Data Models

### `PlanetaryPhenomenaModel`

| Field                | Type          | Description                                       |
| :------------------- | :------------ | :------------------------------------------------ |
| `name`               | str           | Planet name                                       |
| `phase_angle`        | float         | Phase angle in degrees                            |
| `phase`              | float         | Illuminated fraction (0.0 to 1.0)                 |
| `elongation`         | float         | Angular distance from the Sun in degrees          |
| `apparent_diameter`  | float         | Apparent diameter in degrees                      |
| `apparent_magnitude` | float         | Apparent visual magnitude                         |
| `is_morning_star`    | Optional[bool] | Geometric: the planet is west of the Sun and so rises before it. `None` for planets other than Mercury/Venus |
| `is_evening_star`    | Optional[bool] | Geometric: the planet is east of the Sun and so sets after it. `None` for planets other than Mercury/Venus   |
| `solar_phase`        | SolarPhase    | `"cazimi"`, `"combust"`, `"under_the_beams"` or `"free"` |

### `PlanetaryPhenomenaCollectionModel`

| Field          | Type                            | Description                |
| :------------- | :------------------------------ | :------------------------- |
| `iso_datetime` | str                             | ISO datetime of moment     |
| `julian_day`   | float                           | Julian Day number          |
| `phenomena`    | List[PlanetaryPhenomenaModel]   | Phenomena for each planet  |
| `solar_phase_thresholds` | SolarPhaseThresholdsModel | The cut-offs every `solar_phase` in this collection was labelled with |

### `SolarPhaseThresholdsModel`

Import from `kerykeion.schemas`. Each value is a half-width in degrees, measured from the Sun's centre; they must widen outwards or the model raises.

| Field              | Type  | Default  | Description                                        |
| :----------------- | :---- | :------- | :------------------------------------------------- |
| `cazimi_deg`       | float | `0.2833` | Below this separation the body is in the heart of the Sun |
| `combust_deg`      | float | `8.5`    | Below this separation the body is burnt             |
| `under_beams_deg`  | float | `17.0`   | Below this separation the body is still in the rays |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more ->](/content/docs/astrologer-api)
