---
title: 'Enums'
category: 'Reference'
description: 'Enumerations used throughout Kerykeion'
tags: ['docs', 'enums', 'constants', 'planets', 'signs', 'aspects']
order: 15
---

# Enums

This module (`kerykeion.enums`) defines standard enumerations for consistency.

## `Planets`

Constants for all celestial bodies supported by the Swiss Ephemeris.

| Planet / Point       | Enum Value                                                                    |
| :------------------- | :---------------------------------------------------------------------------- |
| **Luminaries**       | `SUN`, `MOON`                                                                 |
| **Planets**          | `MERCURY`, `VENUS`, `MARS`, `JUPITER`, `SATURN`, `URANUS`, `NEPTUNE`, `PLUTO` |
| **Asteroids/Points** | `CHIRON`, `MEAN_LILITH`, `TRUE_NODE`, `MEAN_NODE`                             |
| **Angles**           | `ASCENDANT`, `DESCENDANT`, `MEDIUM_COELI` (MC), `IMUM_COELI` (IC)             |

## `Signs`

The 12 Zodiac signs categorized by element.

| Sign      | Enum Value                                       |
| :-------- | :----------------------------------------------- |
| **Fire**  | `ARI` (Aries), `LEO` (Leo), `SAG` (Sagittarius)  |
| **Earth** | `TAU` (Taurus), `VIR` (Virgo), `CAP` (Capricorn) |
| **Air**   | `GEM` (Gemini), `LIB` (Libra), `AQU` (Aquarius)  |
| **Water** | `CAN` (Cancer), `SCO` (Scorpio), `PIS` (Pisces)  |

## `Aspects`

Standard specific angles between planets supported by Kerykeion.

| Type      | Examples                                                                                 |
| :-------- | :--------------------------------------------------------------------------------------- |
| **Major** | `CONJUNCTION` (0°), `OPPOSITION` (180°), `SQUARE` (90°), `TRINE` (120°), `SEXTILE` (60°) |
| **Minor** | `SEMI_SEXTILE` (30°), `QUINCUNX` (150°), `QUINTILE` (72°), `BIQUINTILE` (144°)           |
