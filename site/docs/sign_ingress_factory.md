---
title: 'Sign Ingresses'
description: 'Find the moments planets cross from one zodiac sign into the next within a date range.'
category: 'Forecasting'
tags: ['docs', 'ingress', 'sign change', 'transit', 'kerykeion']
order: 56
---

# Sign Ingresses

The `SignIngressFactory` finds **sign ingresses** -- the moments planets cross from one zodiac sign into the next -- within a date range, ordered chronologically. Dates are ISO strings treated as UTC. By default it scans Sun through Pluto (the fast-moving Moon is excluded unless explicitly requested).

## Basic Usage

```python
from kerykeion import SignIngressFactory

result = SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31")
for ingress in result.ingresses:
    print(ingress.iso_utc, ingress.planet, "->", ingress.sign)
```

Include the Moon, or restrict the set:

```python
moon = SignIngressFactory.from_iso_range("2026-01-01", "2026-01-31", planets=["Moon"])
```

Sidereal ingresses occur at different times because their 30-degree sign
boundaries are shifted by the ayanamsha. Pass both zodiac arguments for a
sidereal calendar:

```python
sidereal = SignIngressFactory.from_iso_range(
    "2026-01-01",
    "2026-12-31",
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
)
```

## Methods

### `from_iso_range(start_date, end_date, planets=None, zodiac_type="Tropical", sidereal_mode=None)`

| Parameter       | Type                   | Default      | Description                                                                |
| :-------------- | :--------------------- | :----------- | :------------------------------------------------------------------------- |
| `start_date`    | str (ISO)              | --           | Range start (a date-only value starts at 00:00 UTC).                      |
| `end_date`      | str (ISO)              | --           | Range end (a date-only value is widened through the end of that UTC day). |
| `planets`       | list[str] or None      | None         | Subset of planet names. Defaults to Sun–Pluto (Moon excluded unless requested). |
| `zodiac_type`   | `ZodiacType`           | `"Tropical"` | `"Tropical"` or `"Sidereal"`; sidereal sign-boundary times shift with the ayanamsha. |
| `sidereal_mode` | `SiderealMode` or None | None         | Required ayanamsha when `zodiac_type="Sidereal"`.                       |

**Returns:** `SignIngressesCollectionModel`

### `from_julian_day(start_jd, end_jd, planets=None, zodiac_type="Tropical", sidereal_mode=None)`

Same as above with Julian Day (UT) bounds. **Raises** `KerykeionException`
for an invalid zodiac configuration or if the ephemeris backend fails mid-scan,
and `ValueError` for an unknown planet name, a non-finite Julian bound, or an
over-large range.

## Data Models

### `SignIngressesCollectionModel`

| Field       | Type | Description                        |
| :---------- | :--- | :--------------------------------- |
| `start_jd`  | float | Requested Julian Day (UT) range start. |
| `end_jd`    | float | Requested Julian Day (UT) range end. |
| `ingresses` | list | Chronologically ordered ingresses. |

Each `IngressModel` item has:

| Field                | Type  | Description                                          |
| :------------------- | :---- | :-------------------------------------------------- |
| `planet`             | str   | Planet making the ingress.                          |
| `sign`               | str   | Sign being entered.                                 |
| `from_sign`          | str   | Sign being left.                                    |
| `sign_num`           | int   | Index of the entered sign (0–11).                   |
| `from_sign_num`      | int   | Index of the previous sign (0–11).                  |
| `retrograde`         | bool  | Whether the planet was retrograde at the ingress.   |
| `iso_utc`            | str   | ISO 8601 UTC datetime of the exact ingress.         |
| `julian_day`         | float | Julian Day (UT) of the ingress.                     |
| `ecliptic_longitude` | float | Absolute ecliptic longitude (0–360) at the ingress. |
| `season_marker`      | str or None | `march_equinox`, `june_solstice`, `september_equinox`, or `december_solstice` for tropical Sun ingresses at cardinal boundaries; otherwise `None`. |

`season_marker` is deliberately `None` for every sidereal ingress: a sidereal
cardinal-sign boundary is not the astronomical equinox or solstice.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
