---
title: 'Enums'
category: 'Reference'
description: 'Enumerations used throughout Kerykeion'
tags: ['docs', 'enums', 'constants', 'planets', 'signs', 'aspects']
order: 10
---

# Enums (`kerykeion.enums`)

This module defines standard enumerations used across the Kerykeion library to ensure consistency in identifying planets, signs, and aspects.

## `Planets`

Enumeration for celestial bodies and calculated points.

```python
from kerykeion.enums import Planets

# Example usage
sun = Planets.SUN
ascendant = Planets.ASCENDANT
```

### Values

- `SUN`, `MOON`, `MERCURY`, `VENUS`, `MARS`
- `JUPITER`, `SATURN`, `URANUS`, `NEPTUNE`, `PLUTO`
- `CHIRON`, `MEAN_LILITH`
- `TRUE_NODE`, `MEAN_NODE`
- `TRUE_SOUTH_NODE`, `MEAN_SOUTH_NODE`
- `ASCENDANT`, `DESCENDANT`, `MEDIUM_COELI`, `IMUM_COELI`

## `Signs`

Enumeration for the twelve Zodiac signs.

```python
from kerykeion.enums import Signs

aries = Signs.ARI
```

### Values

- `ARI` (Aries)
- `TAU` (Taurus)
- `GEM` (Gemini)
- `CAN` (Cancer)
- `LEO` (Leo)
- `VIR` (Virgo)
- `LIB` (Libra)
- `SCO` (Scorpio)
- `SAG` (Sagittarius)
- `CAP` (Capricorn)
- `AQU` (Aquarius)
- `PIS` (Pisces)

## `Aspects`

Enumeration for astrological aspects between points.

```python
from kerykeion.enums import Aspects

conjunction = Aspects.CONJUNCTION
```

### Values

**Major Aspects:**

- `CONJUNCTION` (0°)
- `OPPOSITION` (180°)
- `SQUARE` (90°)
- `TRINE` (120°)
- `SEXTILE` (60°)

**Minor Aspects:**

- `SEMI_SEXTILE` (30°)
- `QUINCUNX` (150°)
- `QUINTILE` (72°)
- `BIQUINTILE` (144°)
- `OCTILE` (45°) - Also known as Semi-Square
- `TRIOCTILE` (135°) - Also known as Sesquiquadrate
- `DECILE` (36°)
- `TRIDECILE` (108°)
- `SESQUIQUADRATE` (135°) - Synonym for Trioctile

**Special:**

- `NONE` (No aspect)
