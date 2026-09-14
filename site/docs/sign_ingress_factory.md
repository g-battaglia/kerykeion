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

## Sign Periods

Ingresses answer *when does the sign change?*. Sign periods answer *which sign
is this planet in on that date?* -- the stays themselves, so a planet that does
not change sign at all inside the range is still reported, as a single stay
covering the whole range. Per planet the stays are contiguous and ordered: the
`end` of one is the `start` of the next, which is the ingress instant, and
together they cover the range from bound to bound.

```python
from kerykeion import SignIngressFactory

periods = SignIngressFactory.sign_periods_from_iso_range(
    "2026-01-01", "2026-12-31", planets=["Jupiter"]
)
for period in periods.periods:
    print(period.planet, period.sign, period.start, "->", period.end, period.start_clipped, period.end_clipped)
# Jupiter Can 2026-01-01T00:00:00Z -> 2026-06-30T05:52:22Z True False
# Jupiter Leo 2026-06-30T05:52:22Z -> 2027-01-01T00:00:00Z False True
```

The Moon is opt-in here as well (`planets=[..., "Moon"]`), and gives roughly
thirteen stays a month.

### `sign_periods_from_iso_range(start_date, end_date, planets=None, zodiac_type="Tropical", sidereal_mode=None)`

Same parameters as `from_iso_range`. **Returns:** `SignPeriodsCollectionModel`.

### `sign_periods_from_julian_day(start_jd, end_jd, planets=None, zodiac_type="Tropical", sidereal_mode=None)`

Same as above with Julian Day (UT) bounds, and the same
`KerykeionException` / `ValueError` as `from_julian_day`.

### `SignPeriodsCollectionModel`

| Field      | Type  | Description                                    |
| :--------- | :---- | :--------------------------------------------- |
| `start_jd` | float | Requested Julian Day (UT) range start.         |
| `end_jd`   | float | Requested Julian Day (UT) range end.           |
| `periods`  | list  | The `SignPeriodModel` stays, planet by planet. |

Each `SignPeriodModel` item has:

| Field           | Type  | Description                                                    |
| :-------------- | :---- | :-------------------------------------------------------------- |
| `planet`        | str   | Planet the stay belongs to.                                    |
| `sign`          | str   | Sign the planet is in for the whole stay.                      |
| `sign_num`      | int   | Index of that sign (0–11, 0 = Aries).                          |
| `start_jd`      | float | Julian Day (UT) the stay begins, clipped to the range start.   |
| `end_jd`        | float | Julian Day (UT) the stay ends, clipped to the range end.       |
| `start`         | str   | ISO 8601 UTC of `start_jd`.                                    |
| `end`           | str   | ISO 8601 UTC of `end_jd`.                                      |
| `start_clipped` | bool  | True when the sign was entered before the range.               |
| `end_clipped`   | bool  | True when the sign is left after the range.                    |

The sign at the range start is read inside the same ephemeris session, and so
in the same zodiac frame, as the ingress scan: a sidereal request yields
sidereal stays with sidereal ingress instants, and the first stay can never
disagree with the ingresses that follow it.

**Clipping and the range edges.** A clipped bound is the range edge, not an
ingress; nothing is searched outside the range except a single edge probe.
That probe reaches a solver's resolution -- 50 ms, ten times the bisection's
own error and twenty times finer than the second the ISO strings resolve --
past either bound, so a range that starts or ends on an ingress instant this
library reported opens or closes the stay there unclipped, instead of emitting
a hair-thin stay on the wrong side of the crossing. An ingress any farther
from a bound, inside or outside the range, is what it is: a boundary between
two stays, or out of range. Ingresses within the range are exactly the
instants `from_julian_day` reports for the same range. An empty or inverted
range yields no periods.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
