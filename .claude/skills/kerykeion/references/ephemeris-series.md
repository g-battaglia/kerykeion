# Time-series and predictive factories

All of these consume `AstrologicalSubjectModel` objects and produce Pydantic
models. Sources: `kerykeion/ephemeris_data_factory.py`,
`kerykeion/planetary_return_factory.py`,
`kerykeion/secondary_progressions/*.py`,
`kerykeion/transits_time_range_factory.py`.

## EphemerisDataFactory — positions over a date range

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory

factory = EphemerisDataFactory(
    start_datetime=datetime(2024, 1, 1),
    end_datetime=datetime(2024, 1, 31),
    step_type="days",          # "days" | "hours" | "minutes"
    step=1,                     # advance N units per sample (must be > 0)
    lat=41.9, lng=12.5, tz_str="Europe/Rome",
    zodiac_type="Tropical",
    houses_system_identifier="P",
    perspective_type="Apparent Geocentric",
    active_points=None,                 # None → DEFAULT_ACTIVE_POINTS
    active_fixed_stars=None,            # e.g. ["Regulus", "Spica"]
)
```

Two output methods:

- **`get_ephemeris_data(as_model=False)`** → list of plain dicts, one per sample:
  - `"date"` — ISO-8601 string
  - `"planets"` — list of `KerykeionPointModel`
  - `"houses"` — list of `KerykeionPointModel` (the cusps)
  - `"ephemeris_warnings"` — list (per-sample omitted optional points)
  - `"fixed_stars"` — **present only when `active_fixed_stars` is non-empty**.
    Without requested stars the key is absent (byte-compatible with older
    releases). With `as_model=True`, `fixed_stars` is always a list (empty when
    none requested).
- **`get_ephemeris_data_as_astrological_subjects()`** → list of full
  `AstrologicalSubjectModel`; stars are on each `subject.fixed_stars`.

Reading a sample:

```python
data = factory.get_ephemeris_data()
data[0]["planets"][0]["abs_pos"]   # first point's longitude (Sun by default)
data[0]["houses"][0]["abs_pos"]    # first house cusp
```

**Safety caps** (raise `ValueError` if exceeded): `max_days=730`,
`max_hours=8760`, `max_minutes=525600`. Set any to `None` to disable. A series
over 1000 points logs a warning. `step <= 0` raises.

**Match active_points with the consumer.** Aspects between a natal chart and the
series are only detectable for points present on **both** sides. If you feed the
series into `TransitsTimeRangeFactory` with asteroids/TNOs, pass the same
`active_points` list to `EphemerisDataFactory`.

## TransitsTimeRangeFactory — transits vs a natal chart

```python
from kerykeion import TransitsTimeRangeFactory

series = factory.get_ephemeris_data_as_astrological_subjects()
transits = TransitsTimeRangeFactory(
    natal_chart=natal_subject,
    ephemeris_data_points=series,
    active_points=None,        # defaults to DEFAULT_ACTIVE_POINTS
    active_aspects=None,       # defaults to tight predictive orbs
)
moments = transits.get_transit_moments()   # TransitsTimeRangeModel
events = transits.get_transit_events()     # aspect ingress/exact/egress events
```

The series' frame metadata (zodiac_type / sidereal_mode / perspective_type)
should match the natal chart; a mismatch logs a warning.

## PlanetaryReturnFactory — solar / lunar returns

```python
from kerykeion import PlanetaryReturnFactory

factory = PlanetaryReturnFactory(
    subject=natal_subject,
    lng=12.5, lat=41.9, tz_str="Europe/Rome",   # return location
    online=False,
)
solar_2024 = factory.next_return_from_year(2024, "Solar")   # PlanetReturnModel
```

`return_type` is the literal `"Solar"` | `"Lunar"` (anything else raises
`KerykeionException`). Other entry points:
`next_return_from_iso_formatted_time(...)`, `next_return_from_date(...)`,
`next_return_from_month_and_year(year, month, return_type)`. The constructor also
accepts the v6 enrichment flags (`active_fixed_stars`, `calculate_dignities`,
`calculate_nakshatra`, `calculate_gauquelin`, `calculate_nutation`,
`calculate_local_space`) so the return chart matches the natal enrichments.

## Secondary progressions and solar arc

Both are static `compute(...)` methods that copy all calculation settings
(zodiac/sidereal/house/perspective/active points) from the natal subject.

```python
from kerykeion import SecondaryProgressionFactory, SolarArcFactory

prog = SecondaryProgressionFactory.compute(
    natal_subject,
    target_year=2026,                         # or target_iso_utc_datetime="2026-04-25T00:00:00Z"
)   # → AstrologicalSubjectModel

arc = SolarArcFactory.compute(
    natal_subject,
    target_year=2026,
    compute_aspects=True,
    aspect_orb=3.0,
)   # → SolarArcSubjectModel (directed points + directed-to-natal aspects)
```

`target_iso_utc_datetime` and `target_year` are mutually exclusive; supplying
both or neither raises `KerykeionException`. Note the progression angle
convention: progressed angles/cusps are the real sky angles at the progressed
instant ("Q2 / daily houses", MC ≈ 360°/year), not the ~1°/year solar-arc angles
that astro.com reports by default. Progressed planet positions are unaffected.

## Other standalone predictive factories

Exported from the package top level (see `kerykeion/__init__.py`), each with its
own model: `LunationFinderFactory`, `RetrogradeStationFactory`,
`SignIngressFactory`, `MundaneAspectFactory`, `EclipseFactory`,
`PlanetaryNodesFactory`, `HeliacalFactory`, `OccultationFactory`,
`PlanetaryPhenomenaFactory`. They take Julian-Day or ISO ranges and reject
non-finite / out-of-range bounds with `ValueError` rather than returning a
plausible empty result.
