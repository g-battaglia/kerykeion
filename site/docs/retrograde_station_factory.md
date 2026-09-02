---
title: 'Retrograde Stations'
description: 'Find planetary retrograde and direct stations within a date range.'
category: 'Forecasting'
tags: ['docs', 'retrograde', 'station', 'direct', 'mercury retrograde', 'kerykeion']
order: 55
---

# Retrograde Stations

The `RetrogradeStationFactory` finds planetary **stations** -- the moments a planet turns retrograde (SR) or direct (SD) -- within a date range, ordered chronologically. Dates are ISO strings treated as UTC. The default planet set is Mercury through Pluto.

## Basic Usage

```python
from kerykeion import RetrogradeStationFactory

result = RetrogradeStationFactory.from_iso_range("2026-01-01", "2026-12-31")
for station in result.stations:
    print(station.iso_utc, station.planet, station.station_type)  # station_type: 'SR' (turns retrograde) / 'SD' (turns direct)
```

Restrict to specific planets:

```python
mercury = RetrogradeStationFactory.from_iso_range("2026-01-01", "2026-12-31", planets=["Mercury"])
```

For sidereal output, provide an ayanamsha. A station is the instant a planet's
longitudinal speed crosses zero, so its time is zodiac-independent; the
reported longitude and sign use the requested zodiac.

```python
sidereal = RetrogradeStationFactory.from_iso_range(
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
| `planets`       | list[str] or None      | None         | Subset of planet names. Defaults to Mercury–Pluto; `"Chiron"` is accepted on request. Any other name (the Sun and the Moon included, since they never station) raises `ValueError`. |
| `zodiac_type`   | `ZodiacType`           | `"Tropical"` | `"Tropical"` or `"Sidereal"`; affects reported longitude/sign, not station time. |
| `sidereal_mode` | `SiderealMode` or None | None         | Required ayanamsha when `zodiac_type="Sidereal"`.                       |

**Returns:** `RetrogradeStationsCollectionModel`

### `from_julian_day(start_jd, end_jd, planets=None, zodiac_type="Tropical", sidereal_mode=None)`

Same as above with Julian Day (UT) bounds. **Raises** `KerykeionException`
for an invalid zodiac configuration or if the ephemeris backend fails mid-scan,
and `ValueError` for an unknown planet name, a non-finite Julian bound, or an
over-large range.

## Data Models

### `RetrogradeStationsCollectionModel`

| Field      | Type | Description                        |
| :--------- | :--- | :--------------------------------- |
| `start_jd` | float | Requested Julian Day (UT) range start. |
| `end_jd`   | float | Requested Julian Day (UT) range end. |
| `stations` | list | Chronologically ordered stations.  |

Each `StationModel` item has:

| Field                | Type  | Description                                          |
| :------------------- | :---- | :-------------------------------------------------- |
| `planet`             | str   | Planet that stationed.                              |
| `station_type`       | str   | `"SR"` (turns retrograde) or `"SD"` (turns direct). |
| `iso_utc`            | str   | ISO 8601 UTC datetime of the exact station.         |
| `julian_day`         | float | Julian Day (UT) of the station.                     |
| `sign`               | str   | Zodiac sign at the station.                          |
| `sign_num`           | int   | Sign index (0–11).                                  |
| `degree`             | float | Degree within the sign (0–30).                      |
| `ecliptic_longitude` | float | Absolute ecliptic longitude (0–360).                |

## Retrograde Periods

Stations answer *when did the motion turn?*. Retrograde periods answer *was
this planet retrograde on that date?* -- the spans of retrograde motion
themselves, so a planet that neither turned retrograde nor turned direct
inside the range is still reported, with both bounds flagged as the range
edges. A retrograde station opens a span, a direct station closes it, and the
range clips whatever it cuts.

```python
from kerykeion import RetrogradeStationFactory

periods = RetrogradeStationFactory.retrograde_periods_from_iso_range(
    "2026-01-01", "2026-12-31", planets=["Mercury"]
)
for period in periods.periods:
    print(period.planet, period.start, "->", period.end, period.start_clipped, period.end_clipped)
# Mercury 2026-02-26T06:48:10Z -> 2026-03-20T19:32:50Z False False
# Mercury 2026-06-29T17:35:55Z -> 2026-07-23T22:57:51Z False False
# Mercury 2026-10-24T07:12:42Z -> 2026-11-13T15:53:52Z False False
```

`"Chiron"` is opt-in here too, and its slow retrograde arcs show the clipping:

```python
chiron = RetrogradeStationFactory.retrograde_periods_from_iso_range(
    "2026-01-01", "2026-12-31", planets=["Chiron"]
)
first = chiron.periods[0]
print(first.start, first.start_clipped)  # 2026-01-01T00:00:00Z True
```

### `retrograde_periods_from_iso_range(start_date, end_date, planets=None, zodiac_type="Tropical", sidereal_mode=None)`

Same parameters as `from_iso_range`. **Returns:** `RetrogradePeriodsCollectionModel`.

### `retrograde_periods_from_julian_day(start_jd, end_jd, planets=None, zodiac_type="Tropical", sidereal_mode=None)`

Same as above with Julian Day (UT) bounds. **Raises** the same
`KerykeionException` / `ValueError` as `from_julian_day`, plus a
`KerykeionException` when the stations of one planet do not alternate (a
retrograde station while already retrograde, or a direct station while
direct).

### `RetrogradePeriodsCollectionModel`

| Field      | Type  | Description                                          |
| :--------- | :---- | :--------------------------------------------------- |
| `start_jd` | float | Requested Julian Day (UT) range start.               |
| `end_jd`   | float | Requested Julian Day (UT) range end.                 |
| `periods`  | list  | The `RetrogradePeriodModel` spans, planet by planet. |

Each `RetrogradePeriodModel` item has:

| Field           | Type  | Description                                                          |
| :-------------- | :---- | :------------------------------------------------------------------- |
| `planet`        | str   | Planet the span belongs to.                                          |
| `start_jd`      | float | Julian Day (UT) the retrograde motion begins, clipped to the range start. |
| `end_jd`        | float | Julian Day (UT) the retrograde motion ends, clipped to the range end. |
| `start`         | str   | ISO 8601 UTC of `start_jd`.                                          |
| `end`           | str   | ISO 8601 UTC of `end_jd`.                                            |
| `start_clipped` | bool  | True when the planet was already retrograde at the range start.      |
| `end_clipped`   | bool  | True when the planet is still retrograde at the range end.           |

A period carries no sign: a station instant is the same in every zodiac, so
`zodiac_type` and `sidereal_mode` change nothing in the output beyond being
validated.

**Clipping and the range edges.** A clipped bound says where the range cut the
span, not where the real station is: nothing is searched outside the range
except a single edge probe. That probe reaches a solver's resolution -- 50 ms,
ten times the bisection's own error and twenty times finer than the second the
ISO strings resolve -- past either bound, so a range whose bound is a station
instant this library reported behaves as intended: a station on the range
start sets the initial motion (rather than the sign of a speed that is
numerically zero there) and a station on the range end closes its span
unclipped. A station any farther from a bound, however close, is a real
station. Spans within the range are exactly the instants `from_julian_day`
reports for the same range. An empty or inverted range yields no periods, and
only a zero-length span is dropped.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
