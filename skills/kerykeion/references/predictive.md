# Predictive: ephemeris series, transits, returns, progressions, solar arc

Time-series and predictive factories. All consume `AstrologicalSubjectModel` objects and
produce Pydantic models. Sources: `kerykeion/ephemeris_data/factory.py`,
`kerykeion/transits/factory.py`, `kerykeion/planetary_returns/factory.py`,
`kerykeion/secondary_progressions/factory.py`, `kerykeion/secondary_progressions/solar_arc.py`,
shared helpers in `kerykeion/predictive/utils.py`. All factories here are exported from the
top-level `kerykeion` namespace unless labeled otherwise.

## Contents

- [EphemerisDataFactory](#ephemerisdatafactory--positions-over-a-date-range)
- [TransitsTimeRangeFactory](#transitstimerangefactory--transits-vs-a-natal-chart)
- [PlanetaryReturnFactory](#planetaryreturnfactory--returns-and-node-crossings)
- [SecondaryProgressionFactory](#secondaryprogressionfactory--day-for-a-year-progressions)
- [SolarArcFactory](#solararcfactory--solar-arc-directions)
- [Other predictive factories](#other-predictive-factories)

## EphemerisDataFactory — positions over a date range

Constructor (`kerykeion/ephemeris_data/factory.py`):

| kwarg | default | notes |
|---|---|---|
| `start_datetime`, `end_datetime` | required | `datetime`; naive values are read in `tz_str` |
| `step_type` | `"days"` | `"days" \| "hours" \| "minutes"` (anything else raises `ValueError`) |
| `step` | `1` | units per sample; `<= 0` raises `ValueError` |
| `lat`, `lng` | `51.4769`, `0.0005` | Greenwich — override for any real use |
| `tz_str` | `"Etc/UTC"` | IANA zone |
| `is_dst` | `False` | fold disambiguation for non-unique wall times: `True` = larger UTC offset |
| `zodiac_type` | `"Tropical"` | plus `sidereal_mode` (default `None`) |
| `houses_system_identifier` | `"P"` | Placidus |
| `perspective_type` | `"Apparent Geocentric"` | |
| `max_days` / `max_hours` / `max_minutes` | `730` / `8760` / `525600` | safety caps, checked BEFORE materializing; exceeding raises `ValueError`; `None` disables |
| `custom_ayanamsa_t0`, `custom_ayanamsa_ayan_t0` | `None` | only with `sidereal_mode="USER"` |
| `active_points` | `None` | `None` → `DEFAULT_ACTIVE_POINTS`; pass the SAME list you give the consumer |
| `active_fixed_stars` | `None` | star names as in `AstrologicalSubjectFactory.from_birth_data` |

Daily steps advance by LOCAL calendar day at fixed wall time (DST-safe); hour/minute steps
advance in UTC. A series over 1000 points logs a warning.

Output methods:

- **`get_ephemeris_data(as_model=False)`** → list of dicts, one per sample:
  - `"date"` — ISO-8601 string; `"planets"` / `"houses"` — lists of `KerykeionPointModel`
  - `"ephemeris_warnings"` — ALWAYS present since a75 (list of `EphemerisWarningModel`, empty when nothing omitted)
  - `"polar_house_fallbacks"` — ALWAYS present (list of `PolarHouseFallbackModel`, empty when no polar/Gauquelin fallback)
  - `"fixed_stars"` — key present ONLY when `active_fixed_stars` is non-empty
  - With `as_model=True` → list of `EphemerisDictModel` instead; there `fixed_stars` is always a list (empty when none requested). `EphemerisWarningModel`/`PolarHouseFallbackModel` import from `kerykeion.schemas`.
- **`get_ephemeris_data_as_astrological_subjects()`** → list of full
  `AstrologicalSubjectModel` (stars on `subject.fixed_stars`). Heavier; required input for
  `TransitsTimeRangeFactory`. Its `as_model` parameter is retained but ignored.

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory

factory = EphemerisDataFactory(
    start_datetime=datetime(2025, 1, 1),
    end_datetime=datetime(2025, 1, 5),
    step_type="days", step=1,
    lat=41.9028, lng=12.4964, tz_str="Europe/Rome",
)
samples = factory.get_ephemeris_data(as_model=True)
print(len(samples))                                   # 5
first = samples[0]
print(first.date, first.planets[0].name, round(first.planets[0].abs_pos, 2))
print(len(first.houses), first.ephemeris_warnings, first.polar_house_fallbacks)
```

**Match `active_points` with the consumer.** Transit aspects are only detectable for points
present on BOTH the natal chart and the series subjects. Asteroids/TNOs in the transit
request must also be passed to `EphemerisDataFactory` (and to the natal subject factory).

## TransitsTimeRangeFactory — transits vs a natal chart

Constructor (`kerykeion/transits/factory.py`):

| kwarg | default | notes |
|---|---|---|
| `natal_chart` | required | `AstrologicalSubjectModel` |
| `ephemeris_data_points` | required | list of `AstrologicalSubjectModel`, chronological |
| `active_points` | `None` | `None` → `DEFAULT_ACTIVE_POINTS` |
| `active_aspects` | `None` | `None` → `PREDICTIVE_ACTIVE_ASPECTS` (5 Ptolemaic aspects, tight 3° orb) |
| `settings_file` | `None` | `Path \| KerykeionSettingsModel \| dict \| None` |
| `axis_orb_limit` (kw-only) | `None` | discard transit-to-axis aspects with orb >= limit; non-finite or `<= 0` raises `KerykeionException` |

Construction-time `logging.warning`s (misconfigurations, not errors): frame mismatch between
natal and series (`zodiac_type`/`sidereal_mode`/`perspective_type`/custom ayanamsa);
non-chronological series; points requested but missing from one or both sides.

- **`get_transit_moments()`** → `TransitsTimeRangeModel`: `dates` (list of ISO strings),
  `subject` (the natal), `transits` (list of `TransitMomentModel`: `date` + `aspects`, the
  raw per-sample aspect snapshots).
- **`get_transit_events(*, refine_exact_moments=False, refinement_iterations=21)`** →
  `TransitEventsTimeRangeModel` (`events` sorted by `exact_moment`, `subject`). Groups
  samples into per-pass events (recurring aspects split whenever the gap exceeds ~1.5x the
  median sampling step; a sub-orb retrograde loop yields one event per local orb minimum).
  With `refine_exact_moments=True` a ternary search refines `exact_moment`/`min_orb` to
  sub-step precision (21 iterations ≈ sub-minute for daily steps); refinement only runs for
  `"Apparent Geocentric"` / `"True Geocentric"` perspectives (otherwise coarse values are kept
  and an info line is logged).

`TransitEventModel` fields:

| field | type | meaning |
|---|---|---|
| `p1_name` / `p2_name` | `str` | transit point / natal point |
| `aspect` | `str` | e.g. `"conjunction"` |
| `applying_start` | `Optional[str]` | first in-orb sample; `None` if the applying phase was not sampled (range-truncated or undersampled) |
| `exact_moment` | `str` | ISO datetime of minimum orb |
| `separating_end` | `Optional[str]` | last in-orb sample; `None` when truncated at range end |
| `min_orb` | `float` | degrees at `exact_moment` |
| `orb_rate` | `Optional[float]` | degrees/day right after exact; `None` at series end |

**Sampling-resolution trap:** detection is sample-based. The Moon (~13.2°/day) stays inside a
3° orb ~5.5 h per side — daily sampling skips or merges lunar aspects. Keep the step below
`orb / speed` of the fastest active point (a `logging.warning` fires when the coarsest gap
exceeds it). Use `step_type="hours", step=4` for series that include the Moon.

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory, TransitsTimeRangeFactory

natal = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
series = EphemerisDataFactory(
    datetime(2025, 3, 1), datetime(2025, 3, 4), step_type="days",
    lat=natal.lat, lng=natal.lng, tz_str=natal.tz_str,
).get_ephemeris_data_as_astrological_subjects()
factory = TransitsTimeRangeFactory(natal_chart=natal, ephemeris_data_points=series)
events = factory.get_transit_events(refine_exact_moments=False)
for ev in events.events[:3]:
    print(ev.p1_name, ev.aspect, ev.p2_name, ev.exact_moment, ev.min_orb)
```

## PlanetaryReturnFactory — returns and node crossings

Constructor (`kerykeion/planetary_returns/factory.py`) — first arg `subject` (the natal
`AstrologicalSubjectModel`), then the RETURN LOCATION:

| kwarg | default | notes |
|---|---|---|
| `city`, `nation` | `None` | required when `online=True` (geocoded via Geonames) |
| `lng`, `lat`, `tz_str` | `None` | required when `online=False` |
| `online` | `True` | pass `False` + coordinates for offline work |
| `geonames_username` | `None` | default username + warning if omitted online |
| `cache_expire_after_days` (kw-only) | `30` | Geonames cache |
| `altitude` | `None` | meters; only affects Topocentric perspective |
| `custom_ayanamsa_t0`, `custom_ayanamsa_ayan_t0` | `None` | fall back to the values on the subject; both required for `sidereal_mode="USER"` |
| `active_fixed_stars`, `calculate_dignities`, `calculate_nakshatra`, `calculate_gauquelin`, `calculate_nutation`, `calculate_local_space` | `None`/`False` | v6 enrichment flags; when not passed they are INFERRED from the natal subject's populated fields |

The return chart copies the natal frame (`zodiac_type`, `sidereal_mode`,
`houses_system_identifier`, `perspective_type`, `active_points`) and is cast at the
factory's location. All methods return **`PlanetReturnModel`** — a full chart model with the
`AstrologicalSubjectModel` field layout plus `return_type: ReturnType` and
`is_diurnal: Optional[bool]`. `ReturnType = Literal["Lunar", "Solar", "Heliocentric",
"Lunar_Node_Crossing"]` (import: `from kerykeion.schemas import ReturnType`).

**Subpackage import:** `from kerykeion.planetary_returns.factory import SolarLunarReturnType`
— the narrow `Literal["Solar", "Lunar"]` accepted by the geocentric Solar/Lunar entry points
(other values raise `KerykeionException`).

The 10 active `next_*` methods (every `backwards=` defaults to `False`; `backwards=True`
searches backward in time and requires the libephemeris backend — pyswisseph raises
`KerykeionException`):

| method | signature | notes |
|---|---|---|
| `next_return_from_iso_formatted_time` | `(iso_formatted_time, return_type, backwards=False)` | Solar/Lunar; naive ISO read as UTC |
| `next_return_from_date` | `(year, month, day=1, *, return_type, backwards=False)` | search from 00:00 UTC of that date |
| `next_heliocentric_return` | `(planet_name, start_jd, backwards=False)` | Julian Day input; `"Sun"`/`"Moon"` raise (undefined heliocentrically) |
| `next_heliocentric_return_from_iso_formatted_time` | `(planet_name, iso_formatted_time, backwards=False)` | |
| `next_heliocentric_return_from_year` | `(planet_name, year)` | from Jan 1 UTC; no `backwards` |
| `next_heliocentric_return_from_date` | `(planet_name, year, month, day=1, backwards=False)` | |
| `next_lunar_node_crossing` | `(start_jd, backwards=False)` | Moon crosses its own node (latitude 0) |
| `next_lunar_node_crossing_from_iso_formatted_time` | `(iso_formatted_time, backwards=False)` | |
| `next_lunar_node_crossing_from_year` | `(year)` | no `backwards` |
| `next_lunar_node_crossing_from_date` | `(year, month, day=1, backwards=False)` | |

Searches that walk off the ephemeris date range raise `KerykeionException`. Sidereal
subjects are searched in sidereal longitude (the crossing tracks the drifting ayanamsa).

Deprecated (DeprecationWarning, removal in 7.0.0 — see `references/migration-and-deprecations.md`):
`next_return_from_year(year, return_type)` and
`next_return_from_month_and_year(year, month, return_type)` → use `next_return_from_date`.

```python
from kerykeion import PlanetaryReturnFactory

natal = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
factory = PlanetaryReturnFactory(
    natal, lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False)
sr = factory.next_return_from_date(2025, 1, 1, return_type="Solar")
print(sr.return_type, sr.iso_formatted_utc_datetime)     # Solar 2025-07-15T...
print(sr.sun.sign, round(sr.sun.abs_pos - natal.sun.abs_pos, 3))  # ~0.0
```

## SecondaryProgressionFactory — day-for-a-year progressions

**Subpackage:** `kerykeion/secondary_progressions/` (factory + models re-exported top-level).
Static methods; year unit is the mean tropical year (365.24219 days).

- **`compute(natal_subject, *, target_iso_utc_datetime=None, target_year=None, progressed_subject_name=None)`**
  → `AstrologicalSubjectModel` for the progressed instant at the natal location. Exactly ONE
  of `target_iso_utc_datetime` (ISO-8601 WITH `Z`/offset, e.g. `"2026-04-25T00:00:00Z"`) or
  `target_year` (Jan 1 00:00 UTC of that year) must be passed — both or neither raise
  `KerykeionException`. All frame settings and enrichments are copied/inferred from the natal.
  Default name: `"<natal.name> (Progressed YYYY-MM-DD)"`.
- **`compute_full(natal_subject, *, target_iso_utc_datetime=None, target_year=None, progressed_subject_name=None, active_points=None, compute_aspects=True, aspect_orb=3.0, aspects=None, point_orb_adjustments=None, point_orb_adjustment_strategy="max_explicit")`**
  → `SecondaryProgressionsResultModel`. `active_points` defaults to
  `DEFAULT_PREDICTIVE_POINTS` (10 planets + True Node, Chiron, Asc, MC); `aspects` defaults to
  `PTOLEMAIC_ASPECTS` (top-level export: conjunction/opposition/trine/sextile/square);
  orb-adjustment kwargs as in `SolarArcFactory` (see `references/aspects-and-orbs.md`).

Models: `SecondaryProgressionsResultModel` — `natal_name`, `target_iso_utc_datetime` (the
requested real-world date), `ephemeris_iso_utc_datetime` (the actual ephemeris date, ~1 day
per year after birth), `progressed_subject`, `progressed_points`
(list of `ProgressedPointModel`: `name`, `natal_abs_pos`, `progressed_abs_pos`, `natal_sign`,
`progressed_sign`, `sign_changed`), `progressed_to_natal_aspects` (list of
`ProgressedToNatalAspectModel`: `progressed_point`, `natal_point`, `progressed_abs_pos`,
`natal_abs_pos`, `aspect`, `aspect_degrees`, `orb`).

**Progressed-angle convention (verify against expectations):** angles/cusps are the REAL sky
angles at the progressed instant ("Q2 / daily houses", progressed MC ≈ 360°/year) — NOT the
solar-arc-advanced angles (~1°/year) that astro.com/Astro-Seek report by default. Progressed
planet positions are identical under both conventions; only angles, cusps and house
placements differ.

```python
from kerykeion import SecondaryProgressionFactory

natal = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
result = SecondaryProgressionFactory.compute_full(natal, target_year=2026)
print(result.ephemeris_iso_utc_datetime)          # ~36 days after birth
prog = result.progressed_subject
print(prog.sun.sign, prog.moon.sign)
for hit in result.progressed_to_natal_aspects[:2]:
    print(hit.progressed_point, hit.aspect, hit.natal_point, round(hit.orb, 2))
```

## SolarArcFactory — solar arc directions

Same subpackage (`kerykeion/secondary_progressions/solar_arc.py`). Static methods; target
kwargs behave exactly as in `SecondaryProgressionFactory` (one of
`target_iso_utc_datetime` XOR `target_year`).

- **`compute(natal_subject, *, target_iso_utc_datetime=None, target_year=None, active_points=None, compute_aspects=True, aspect_orb=3.0, aspects=None, point_orb_adjustments=None, point_orb_adjustment_strategy="max_explicit")`**
  → `SolarArcSubjectModel`: `natal_name`, `target_iso_utc_datetime`, `solar_arc` (degrees,
  forward, `[0, 360)`), `directed_points` (list of `SolarArcDirectedPointModel`: `name`,
  `natal_abs_pos`, `directed_abs_pos`, `natal_sign`, `directed_sign`, `directed_position`,
  `sign_changed`), `directed_to_natal_aspects` (list of `SolarArcDirectedAspectModel`:
  `directed_point`, `natal_point`, `directed_abs_pos`, `natal_abs_pos`, `aspect`,
  `aspect_degrees`, `orb`). Tautological self-conjunctions (tiny arc) are skipped.
- **`compute_directed_subject(natal_subject, *, target_iso_utc_datetime=None, target_year=None)`**
  → a deep copy of the natal `AstrologicalSubjectModel` (name suffixed `" (directed)"`) with
  every directable point AND the four angles (Asc/MC/Desc/IC) shifted by the arc; house CUSPS
  stay natal (biwheel: inner natal, outer directed, natal house grid). Position-derived
  enrichments (dignities, decan/term, nakshatra, azimuth/altitude, Gauquelin sector) are
  nulled on shifted points; house placement is recomputed against the natal cusps.

```python
from kerykeion import SolarArcFactory

natal = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
directed = SolarArcFactory.compute_directed_subject(natal, target_year=2026)
print(directed.name)                                        # Example Person (directed)
arc = (directed.sun.abs_pos - natal.sun.abs_pos) % 360
print(round(arc, 2))                                        # ~35.5 for 2026
print(directed.first_house.abs_pos == natal.first_house.abs_pos)  # True (cusps stay natal)
```

## Other predictive factories

Standalone range/event factories (lunations, eclipses, sign ingresses, retrograde stations,
mundane aspects, planetary nodes/apsides, heliacal phenomena, occultations) live in their own
subpackages and are covered in `references/mundane-events.md`. Shared predictive helpers
(`PTOLEMAIC_ASPECTS`, Julian-day validation, `gather_active_points`) live in
`kerykeion/predictive/utils.py`; only `PTOLEMAIC_ASPECTS` is re-exported top-level.
For zodiacal releasing and other traditional timing techniques see
`references/traditional.md`; for chart-ready transit data (`ChartDataFactory` transit charts)
see `references/charts-and-drawing.md`.
