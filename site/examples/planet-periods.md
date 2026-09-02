---
title: 'Retrograde and Sign Periods'
tags: ['examples', 'retrograde', 'ingress', 'calendar', 'forecasting', 'kerykeion']
order: 19
---

# Retrograde and Sign Periods

Two factories answer "when did it turn?" and "when did it change sign?" — and
each has a second method that answers the interval question instead of the
moment one: how long the retrograde lasted, how long the planet stayed in the
sign. Both interval methods return **periods**, and a period that runs past the
edge of the range you asked for says so rather than being silently trimmed away.

## Retrograde periods

`RetrogradeStationFactory.from_iso_range` returns the stations themselves;
`retrograde_periods_from_iso_range` pairs them into complete retrograde arcs.

```python
from kerykeion import RetrogradeStationFactory

periods = RetrogradeStationFactory.retrograde_periods_from_iso_range(
    "2026-01-01", "2026-12-31", planets=["Mercury"]
)

for period in periods.periods:
    print(f"{period.planet}: {period.start} -> {period.end}")
```

**Output:**
```
Mercury: 2026-02-26T06:48:10Z -> 2026-03-20T19:32:50Z
Mercury: 2026-06-29T17:35:55Z -> 2026-07-23T22:57:51Z
Mercury: 2026-10-24T07:12:42Z -> 2026-11-13T15:53:52Z
```

The stations that bound them, if you want the turning points rather than the
spans:

```python
stations = RetrogradeStationFactory.from_iso_range(
    "2026-01-01", "2026-12-31", planets=["Mercury"]
)

for station in stations.stations[:4]:
    print(f"{station.station_type} {station.iso_utc} {station.sign} {station.degree:.2f}°")
```

**Output:**
```
SR 2026-02-26T06:48:10Z Pis 22.57°
SD 2026-03-20T19:32:50Z Pis 8.49°
SR 2026-06-29T17:35:55Z Can 26.26°
SD 2026-07-23T22:57:51Z Can 16.32°
```

`SR` opens the retrograde phase and `SD` closes it — the same two labels the
chart renderer writes when `show_motion_state=True`.

### Chiron is opt-in

`planets=None` scans Mercury through Pluto. The Sun and the Moon never station
and are refused, as is any other name; `"Chiron"` is accepted **on request**,
and its slow arcs are where the clip flags earn their place.

```python
chiron = RetrogradeStationFactory.retrograde_periods_from_iso_range(
    "2026-01-01", "2026-12-31", planets=["Chiron"]
)

for period in chiron.periods:
    print(f"{period.start} -> {period.end} "
          f"(clipped: start={period.start_clipped}, end={period.end_clipped})")
```

**Output:**
```
2026-01-01T00:00:00Z -> 2026-01-02T14:37:23Z (clipped: start=True, end=False)
2026-08-03T20:10:11Z -> 2027-01-01T00:00:00Z (clipped: start=False, end=True)
```

A `True` flag means the boundary shown is the **range edge**, not a station: the
first retrograde had already begun on 1 January and the second had not ended by
31 December. Read the flag before treating either timestamp as a turning point.

## Sign periods

`SignIngressFactory.from_iso_range` returns the ingress moments;
`sign_periods_from_iso_range` returns the stays between them, with the same clip
flags.

```python
from kerykeion import SignIngressFactory

periods = SignIngressFactory.sign_periods_from_iso_range(
    "2026-01-01", "2026-12-31", planets=["Mars"]
)

for period in periods.periods[:4]:
    print(f"{period.planet} in {period.sign}: {period.start} -> {period.end} "
          f"(clipped: {period.start_clipped}/{period.end_clipped})")
```

**Output:**
```
Mars in Cap: 2026-01-01T00:00:00Z -> 2026-01-23T09:16:45Z (clipped: True/False)
Mars in Aqu: 2026-01-23T09:16:45Z -> 2026-03-02T14:15:50Z (clipped: False/False)
Mars in Pis: 2026-03-02T14:15:50Z -> 2026-04-09T19:36:09Z (clipped: False/False)
Mars in Ari: 2026-04-09T19:36:09Z -> 2026-05-18T22:25:28Z (clipped: False/False)
```

Mars was already in Capricorn when the range opened, so that first period's
start is the range edge.

## Both methods take the same arguments

`(start_date, end_date, planets=None, zodiac_type="Tropical", sidereal_mode=None)`

A sidereal scan moves every sign boundary by the ayanamsa, so the sign periods
shift with it while the retrograde stations — which are about motion, not
longitude — do not.

```python
sidereal = SignIngressFactory.sign_periods_from_iso_range(
    "2026-01-01", "2026-06-30",
    planets=["Sun"],
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
)
print(f"{len(sidereal.periods)} sidereal Sun periods in the first half of 2026")
```

Each collection also carries the requested `start_jd` and `end_jd`, so the range
a result came from travels with it.

See [Retrograde Station Factory](/content/docs/retrograde_station_factory) and
[Sign Ingress Factory](/content/docs/sign_ingress_factory) for the full field
reference.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
