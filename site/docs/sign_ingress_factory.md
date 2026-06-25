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

## Methods

### `from_iso_range(start_date, end_date, planets=None)`

| Parameter    | Type              | Default | Description                                                                |
| :----------- | :---------------- | :------ | :------------------------------------------------------------------------ |
| `start_date` | str (ISO)         | --      | Range start (a date-only value starts at 00:00 UTC).                      |
| `end_date`   | str (ISO)         | --      | Range end (a date-only value is widened through the end of that UTC day). |
| `planets`    | list[str] or None | None    | Subset of planet names. Defaults to Sun–Pluto (Moon excluded unless requested). |

**Returns:** `SignIngressesCollectionModel`

### `from_julian_day(start_jd, end_jd, planets=None)`

Same as above with Julian Day (UT) bounds. **Raises** `KerykeionException` if the ephemeris backend fails mid-scan and `ValueError` for an unknown planet name or an over-large range.

## Data Models

### `SignIngressesCollectionModel`

| Field       | Type | Description                          |
| :---------- | :--- | :---------------------------------- |
| `ingresses` | list | Chronologically ordered ingresses.  |

Each ingress item exposes `iso_utc` (ISO 8601 UTC datetime of the exact ingress), `planet`, and `sign` (the sign being entered).

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
