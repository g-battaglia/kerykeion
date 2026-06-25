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
    print(station.iso_utc, station.planet, station.station_type)  # station_type: retrograde / direct
```

Restrict to specific planets:

```python
mercury = RetrogradeStationFactory.from_iso_range("2026-01-01", "2026-12-31", planets=["Mercury"])
```

## Methods

### `from_iso_range(start_date, end_date, planets=None)`

| Parameter    | Type              | Default | Description                                                                |
| :----------- | :---------------- | :------ | :------------------------------------------------------------------------ |
| `start_date` | str (ISO)         | --      | Range start (a date-only value starts at 00:00 UTC).                      |
| `end_date`   | str (ISO)         | --      | Range end (a date-only value is widened through the end of that UTC day). |
| `planets`    | list[str] or None | None    | Subset of planet names. Defaults to Mercury–Pluto.                       |

**Returns:** `RetrogradeStationsCollectionModel`

### `from_julian_day(start_jd, end_jd, planets=None)`

Same as above with Julian Day (UT) bounds. **Raises** `KerykeionException` if the ephemeris backend fails mid-scan and `ValueError` for an unknown planet name or an over-large range.

## Data Models

### `RetrogradeStationsCollectionModel`

| Field      | Type | Description                          |
| :--------- | :--- | :---------------------------------- |
| `stations` | list | Chronologically ordered stations.   |

Each station item exposes `iso_utc` (ISO 8601 UTC datetime of the exact station), `planet`, and `station_type` (`retrograde` / `direct`).

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
