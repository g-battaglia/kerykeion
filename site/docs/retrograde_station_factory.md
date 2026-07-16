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
| `planets`       | list[str] or None      | None         | Subset of planet names. Defaults to Mercury–Pluto.                       |
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

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
