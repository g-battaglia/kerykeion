# Mundane event factories

Subject-less factories driven by dates / Julian Day (UT) ranges plus (where
visibility matters) observer coordinates. They search the sky itself — eclipses,
lunations, stations, ingresses, planet-to-planet aspects, occultations, heliacal
events, fixed stars — and return Pydantic models. Most entry points are
`@staticmethod`s called on the class; the exceptions are `OccultationFactory`
and `HeliacalFactory`, which use INSTANCE methods (instantiate first).
`PlanetaryPhenomenaFactory`, `PlanetaryNodesFactory` and
`FixedStarDiscoveryFactory` can also start from an `AstrologicalSubjectModel`.
Source of each factory: `kerykeion/<subpackage>/factory.py` — subpackages
`eclipses`, `lunations`, `retrograde_stations`, `sign_ingresses`,
`mundane_aspects`, `planetary_phenomena`, `planetary_nodes`, `heliacal`,
`occultations`, `fixed_stars` (the last also has `catalog.py`).

## Contents

- [Shared range-factory contract](#shared-range-factory-contract)
- [EclipseFactory](#eclipsefactory)
- [LunationFinderFactory](#lunationfinderfactory)
- [RetrogradeStationFactory](#retrogradestationfactory)
- [SignIngressFactory](#signingressfactory)
- [MundaneAspectFactory](#mundaneaspectfactory)
- [PlanetaryPhenomenaFactory](#planetaryphenomenafactory)
- [PlanetaryNodesFactory](#planetarynodesfactory)
- [HeliacalFactory (instance)](#heliacalfactory-instance)
- [OccultationFactory (instance)](#occultationfactory-instance)
- [FixedStarDiscoveryFactory and FixedStarCatalog](#fixedstardiscoveryfactory-and-fixedstarcatalog)

## Shared range-factory contract

`LunationFinderFactory`, `RetrogradeStationFactory`, `SignIngressFactory` and
`MundaneAspectFactory` share one shape (all static):

- `from_iso_range(start_date, end_date, <filter>, zodiac_type="Tropical", sidereal_mode=None)`
  — ISO date/datetime strings treated as UTC (aware inputs converted); a
  **date-only `end_date` means "through the end of that UTC day"**. Malformed
  ISO raises `KerykeionException`.
- `from_julian_day(start_jd, end_jd, <filter>, ...)` — same, on JD (UT) floats.
- Filter list (`phases`/`planets`/`points`): `None` → documented default set;
  explicit `[]` → scan nothing; unknown names raise `ValueError` listing the
  valid vocabulary.
- Zodiac: `"Sidereal"` requires `sidereal_mode` (ayanamsha name);
  `sidereal_mode="USER"` is rejected. Event TIMES are zodiac-independent for
  lunations, stations, mundane aspects and eclipses (only reported signs
  shift); **`SignIngressFactory` times DO shift** under a sidereal zodiac (the
  30° boundaries move with the ayanamsha).
- Errors: `KerykeionException` for bad zodiac config or a backend failure
  mid-scan (usually a date outside the ephemeris range — results are never
  silently truncated); `ValueError` for non-finite JD bounds, over-large
  ranges/counts, or unknown filter names.
- Collections carry `start_jd`/`end_jd` plus a chronologically sorted list.

`EclipseFactory`, `OccultationFactory` and `HeliacalFactory` are count-based
("next N events from a start point") instead of range-based.

## EclipseFactory

Static methods; both return `EclipseSearchResultModel` with `solar_eclipses:
List[SolarEclipseModel]`, `lunar_eclipses: List[LunarEclipseModel]`, and (local
search only) `latitude`/`longitude`.

| Method | Signature |
|---|---|
| `search_from_location` | `(lat, lng, start_year=None, count=5, zodiac_type="Tropical", sidereal_mode=None)` |
| `search_global` | `(start_year=None, count=10, zodiac_type="Tropical", sidereal_mode=None)` |

`start_year=None` → current UTC year. `count` is per eclipse type (max 1000).
`lat`/`lng` are validated (±90 / ±180) to catch lat/lng swaps.

`SolarEclipseModel`: `type` (`total`/`annular`/`partial`/`annular-total`),
`maximum_jd`, `datestamp` (ISO UTC), `magnitude`, `obscuration`,
`sun_altitude`, `ecliptic_longitude`, `sign`, `sign_num`, `degree`, `saros`,
`inex`, `gamma`, `duration_minutes`.
`LunarEclipseModel`: `type` (`total`/`partial`/`penumbral`), `maximum_jd`,
`datestamp`, `magnitude_umbral`, `magnitude_penumbral`, zodiac fields, `saros`,
`inex`.

Traps: solar `magnitude`/`obscuration` are observer-dependent — `None` in
global searches, populated in local ones; lunar magnitudes are populated in
both. `gamma`/`duration_minutes` (totality/annularity minutes at greatest
eclipse, `None` for partials) come only from `search_global` on libephemeris.
`saros` is libephemeris-only (`None` on swisseph); `inex` is currently ALWAYS
`None`. Eclipse times are pure shadow geometry — zodiac choice shifts only the
reported sign/degree.

```python
from kerykeion import EclipseFactory
result = EclipseFactory.search_global(start_year=2024, count=2)
for ecl in result.solar_eclipses:
    print(ecl.type, ecl.datestamp, ecl.sign, ecl.degree)
for ecl in result.lunar_eclipses:
    print(ecl.type, ecl.datestamp, ecl.magnitude_umbral)
```

## LunationFinderFactory

Static; `from_iso_range(start_date, end_date, phases=None, zodiac_type="Tropical",
sidereal_mode=None)` and `from_julian_day(start_jd, end_jd, phases=None, ...)` →
`LunationsCollectionModel` (`start_jd`, `end_jd`, `lunations`). `phases` subset
of `"new"`, `"first_quarter"`, `"full"`, `"last_quarter"` (default all four).
`LunationModel`: `phase`, `julian_day`, `iso_utc`, `sun`, `moon` (both
`KerykeionPointModel` at the exact instant, ~1 s precision).

```python
from kerykeion import LunationFinderFactory
result = LunationFinderFactory.from_iso_range("2024-01-01", "2024-01-31")
for lun in result.lunations:
    print(lun.phase, lun.iso_utc, lun.moon.sign)
```

## RetrogradeStationFactory

Static; `from_iso_range(start_date, end_date, planets=None, zodiac_type="Tropical",
sidereal_mode=None)` / `from_julian_day(start_jd, end_jd, planets=None, ...)` →
`RetrogradeStationsCollectionModel` (`start_jd`, `end_jd`, `stations`).
`planets` default: `Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune,
Pluto` (Sun/Moon never station and are not accepted). `StationModel`: `planet`,
`station_type` (`"SR"` = turns retrograde, `"SD"` = turns direct),
`julian_day`, `iso_utc`, `sign`, `sign_num`, `degree`, `ecliptic_longitude`.

### Retrograde periods (a92)

`RetrogradeStationFactory.retrograde_periods_from_iso_range(start, end, planets=None, zodiac_type, sidereal_mode)`
/ `retrograde_periods_from_julian_day(...)` → `RetrogradePeriodsCollectionModel`
(`start_jd`, `end_jd`, `periods`). Each `RetrogradePeriodModel` is one retrograde
span clipped to the range: `planet`, `start_jd`, `end_jd`, `start`, `end`,
`start_clipped`, `end_clipped`. The motion state at the range start comes from
the speed there (a station on the first second decides it deterministically);
SR opens a span, SD closes it; clipped bounds are flagged and nothing is
searched outside the range. `"Chiron"` is accepted opt-in by both the station
finder and the periods (default set unchanged).

## SignIngressFactory

Static; same pair of entry points with `planets=None` →
`SignIngressesCollectionModel` (`start_jd`, `end_jd`, `ingresses`). Default
planets: Sun..Pluto; **Moon is opt-in** (list it explicitly — ~13
ingresses/month). A retrograde body can cross a boundary multiple times; every
crossing is reported. `IngressModel`: `planet`, `julian_day`, `iso_utc`, `sign`
(entered), `sign_num`, `from_sign`, `from_sign_num`, `retrograde`,
`ecliptic_longitude` (the 30° boundary crossed), `season_marker` — set only on
Sun ingresses at 0/90/180/270° with hemisphere-neutral values
`march_equinox`/`june_solstice`/`september_equinox`/`december_solstice`;
tropical-only (`None` on every sidereal ingress).

```python
from kerykeion import RetrogradeStationFactory, SignIngressFactory
st = RetrogradeStationFactory.from_iso_range("2024-01-01", "2024-12-31", planets=["Mercury"])
print([(s.station_type, s.iso_utc[:10], s.sign) for s in st.stations])
ing = SignIngressFactory.from_iso_range("2024-03-01", "2024-03-31", planets=["Sun"])
print([(i.sign, i.iso_utc[:16], i.season_marker) for i in ing.ingresses])
```

## MundaneAspectFactory

Static aspectarian: every exact transiting-to-transiting aspect in a range.
`from_iso_range(start_date, end_date, points=None, aspects=None,
zodiac_type="Tropical", sidereal_mode=None)` / `from_julian_day(start_jd,
end_jd, points=None, aspects=None, ...)` → `MundaneAspectsCollectionModel`
(`start_jd`, `end_jd`, `aspects`).

| Filter | Default | Full vocabulary |
|---|---|---|
| `points` | Sun, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto (**Moon opt-in**, ~75 events/month) | default + `Moon`, `Chiron`, `Mean_North_Lunar_Node`, `True_North_Lunar_Node` |
| `aspects` | conjunction, sextile, square, trine, opposition | + semi-sextile, semi-square, quintile, sesquiquadrate, biquintile, quincunx (longitude aspects only — no parallel/contra-parallel) |

`MundaneAspectModel`: `point_a`, `point_b` (`point_a` is always the faster body
— canonical fast-to-slow order, independent of your list order), `aspect`,
`aspect_degrees`, `julian_day`, `iso_utc`, `point_a_longitude`,
`point_b_longitude`, `point_a_sign`, `point_b_sign` (3-letter `Sign` codes),
`point_a_retrograde`, `point_b_retrograde`.

## PlanetaryPhenomenaFactory

Static; observational data (via `pheno_ut`) at ONE instant, not a range.
`from_subject(subject, planets=None, solar_phase_thresholds=None)` (rejects
composite subjects — `julian_day is None` → `KerykeionException`) and
`from_julian_day(julian_day, planets=None, solar_phase_thresholds=None)` →
`PlanetaryPhenomenaCollectionModel` (`iso_datetime` — empty string in the JD
path, `julian_day`, `phenomena`, `solar_phase_thresholds`). `planets`
vocabulary: Moon..Pluto, nine bodies, no Sun. `PlanetaryPhenomenaModel`:
`name`, `phase_angle`, `phase` (illuminated fraction 0–1), `elongation` (deg
from Sun), `apparent_diameter` (deg), `apparent_magnitude`,
`is_morning_star`/`is_evening_star` (Mercury/Venus only, else `None`),
`solar_phase`.

`solar_phase` (`SolarPhase` literal, from `kerykeion.schemas`) is the body's
condition relative to the Sun: `"cazimi"`, `"combust"`, `"under_the_beams"`,
`"free"`. It is read off the same rounded `elongation` the model publishes,
against the collection's `solar_phase_thresholds`
(`SolarPhaseThresholdsModel`, also from `kerykeion.schemas`: `cazimi_deg`
0.2833, `combust_deg` 8.5, `under_beams_deg` 17.0). Those cut-offs are
conventions, not measurements — pass your school's instance to either
constructor and the labels move with it; the instance used is echoed on the
collection, so a consumer never has to guess. The model rejects a set that does
not widen outwards. Named for every body in the set, the Moon included; what a
school does with a combust Moon is the school's business.

`is_morning_star`/`is_evening_star` are **purely geometric** — which side of the
Sun the planet stands on in longitude — and say nothing about visibility. A
planet one degree from the Sun is still an "evening star" here. Read
`solar_phase` for whether it can be seen.

```python
from kerykeion import PlanetaryPhenomenaFactory

coll = PlanetaryPhenomenaFactory.from_julian_day(2460466.0, planets=["Venus"])
venus = coll.phenomena[0]
print(venus.solar_phase, round(venus.elongation, 3))   # cazimi 0.077
print(coll.solar_phase_thresholds.combust_deg)          # 8.5
```

## PlanetaryNodesFactory

Static; orbital nodes + apsides at one instant.
`from_subject(subject, method="mean", planets=None)` — computed in the
subject's own zodiac frame; rejects composite subjects.
`from_julian_day(julian_day, method="mean", planets=None)` — always tropical.
`method` is `"mean"` or `"osculating"` (anything else, including `"Mean"`,
raises `KerykeionException`). Vocabulary: Moon..Pluto; requesting `"Sun"`
raises `KerykeionException` (no geocentric solar nodes/apsides). Returns
`PlanetaryNodesCollectionModel` (`iso_datetime`, `julian_day`, `method`,
`nodes`); `PlanetaryNodeModel` has `planet_name`, `apsis_kind`, and six
`KerykeionPointModel`s: `ascending_node`, `descending_node`, `periapsis`,
`apoapsis`, and the deprecated `perihelion`/`aphelion`.

The apsides carry two names for the same two points. `periapsis`/`apoapsis` are
generic and always correct. `perihelion`/`aphelion` are **deprecated** — they
name the Sun, which is right for the eight planets and wrong for the Moon, which
goes round the Earth. They are still populated (the same object, so the pairs can
never drift), so nothing that reads them breaks. `apsis_kind` (`ApsisKind`
literal, from `kerykeion.schemas`) says which reading is in force:
`"heliocentric"` for every planet, `"geocentric"` for the Moon alone — whose
apsides are the perigee and the apogee, the far one being to the decimal the
Black Moon Lilith (`method="mean"` → `mean_lilith`, `"osculating"` →
`true_lilith`).

```python
from kerykeion import PlanetaryNodesFactory

nodes = PlanetaryNodesFactory.from_julian_day(2451545.0, planets=["Moon", "Mars"])
for n in nodes.nodes:
    print(n.planet_name, n.apsis_kind, round(n.apoapsis.abs_pos, 4))
# Moon geocentric 263.4643
# Mars heliocentric 192.236
```

## HeliacalFactory (instance)

INSTANCE methods — construct first: `HeliacalFactory(ephe_path=None)`
(`ephe_path` is applied per calculation via the ephemeris session). SLOW:
each event is a full visibility search (can take >10 s per call on
libephemeris) — keep counts minimal.

**Subpackage import:** `from kerykeion.heliacal import HeliacalFactory, HeliacalEventModel, HELIACAL_RISING, HELIACAL_SETTING, EVENING_FIRST, MORNING_LAST`
(`HeliacalFactory`/`HeliacalEventModel` are also top-level; the four int
constants — values 1, 2, 3, 4 — are subpackage-only.)

| Method | Signature |
|---|---|
| `next_heliacal_rising` | `(julian_day, planet_name_or_star, geopos=None, atmo=None, observer=None, *, lat=None, lng=None, altitude=None)` → `HeliacalEventModel` |
| `search_events` | `(julian_day, geopos=None, count=5, planets=None, event_types=None, atmo=None, observer=None, *, lat=None, lng=None, altitude=None)` → `List[HeliacalEventModel]` |

Observer position: EITHER `geopos=(lng, lat, altitude_m)` — Swiss Ephemeris
order, **longitude FIRST** — OR the unambiguous keyword form `lat=`, `lng=`,
`altitude=` (altitude defaults to 0 m); passing both raises
`KerykeionException`. `atmo` defaults to `(1013.25, 15.0, 40.0, 0.2)`
(pressure mbar, temp C, humidity %, extinction); `observer` is a 6-tuple (age,
Snellen ratio, mono/binocular, magnification, aperture, transmission).
`search_events` planets default to Mercury, Venus, Mars, Jupiter, Saturn
(case-insensitive; planets only — fixed stars rejected); `event_types`
defaults to `[HELIACAL_RISING, HELIACAL_SETTING]`;
`EVENING_FIRST`/`MORNING_LAST` apply to Mercury/Venus only (skipped for outer
planets); `count` max 200. `next_heliacal_rising` additionally accepts
fixed-star names; "no event in window" and a mistyped body both surface as
`KerykeionException`. `HeliacalEventModel`: `event_type` (label string, e.g.
`"heliacal_rising"`), `julian_day`, `planet_name`, `datestamp` (`YYYY-MM-DD`).

```python
# doc-snippet: no-run  (heliacal searches take ~10-20 s each)
from kerykeion.ephemeris_backend.backend import ephe
from kerykeion.heliacal import HeliacalFactory, HELIACAL_RISING
factory = HeliacalFactory()
event = factory.next_heliacal_rising(ephe.julday(2024, 1, 1, 0.0), "Venus",
                                     lat=41.9028, lng=12.4964)
print(event.event_type, event.datestamp)  # heliacal_rising 2025-03-23
events = factory.search_events(ephe.julday(2024, 1, 1, 0.0), count=2,
                               planets=["Venus"], event_types=[HELIACAL_RISING],
                               lat=41.9028, lng=12.4964)
```

## OccultationFactory (instance)

CALLOUT: INSTANCE methods — `OccultationFactory().search_global(...)`, not
`OccultationFactory.search_global(...)`. Finds lunar occultations (Moon
passing in front of a planet); returns a plain `List[OccultationModel]`.

| Method | Signature |
|---|---|
| `search_global` | `(julian_day, planet_id, count=5)` |
| `search_local` | `(julian_day, planet_id, lat, lng, count=5)` |

`planet_id` is a backend body id int (e.g. `ephe.VENUS`) or a name string
(`"Venus"`). Accepted bodies: Sun, Mercury..Pluto, Chiron, Pholus, Ceres,
Pallas, Juno, Vesta — calculated points (nodes, Lilith, hypotheticals) raise
`KerykeionException`. `count` max 1000; fewer events than requested is a valid
terminal result. `OccultationModel`: `planet_name`, `type`
(`"Total"`/`"Annular"`/`"Partial"`/`"Unknown"`), `maximum_jd`, `datestamp`.

```python
from kerykeion.ephemeris_backend.backend import ephe
from kerykeion import OccultationFactory
factory = OccultationFactory()   # instance, not static
events = factory.search_global(ephe.julday(2024, 1, 1, 0.0), "Venus", count=2)
for occ in events:
    print(occ.planet_name, occ.type, occ.datestamp)
```

## FixedStarDiscoveryFactory and FixedStarCatalog

`FixedStarDiscoveryFactory.find_prominent_stars(subject, orb=1.0)` (static) →
`list[KerykeionPointModel]` of catalog stars conjunct any of the subject's
`active_points` within `orb` degrees, sorted brightest first. Each point
carries discovery extras: `near_point` (the natal point matched), `orb` (actual
separation), `aspect="conjunction"`, `house`, `magnitude`, `declination`, plus
provenance `source`/`precision_class` (libephemeris only). Star longitudes use
the subject's zodiac frame; composite subjects raise `KerykeionException`. On
the swisseph backend an empty result usually means the locally-managed
`sefstars.txt` is missing (a warning is logged).

The catalog holds ~1447 stars sourced from **libephemeris**
(`list_fixed_stars()`) — Swiss `sefstars.txt` is NOT used, for licensing
reasons.

**Subpackage import:** `from kerykeion.fixed_stars import FixedStarCatalog`
(not exported top-level; `FixedStarDiscoveryFactory` and
`FixedStarMetadataModel` are). The slug helper lives one level deeper:
`from kerykeion.fixed_stars.catalog import star_slug`.

| `FixedStarCatalog` static method | Returns |
|---|---|
| `list_all()` | full catalog, `list[FixedStarMetadataModel]` (fresh copy) |
| `count()` | number of stars (~1447) |
| `find(name)` | entry by IAU name or slug (case/`-`/`_`/space-insensitive) or `None` |
| `is_known_name(name)` | `bool`, O(1) |
| `known_slugs()` | `frozenset[str]` of all slugs |

`star_slug(name)` → canonical slug (strip; spaces/hyphens → underscores; case
preserved). `FixedStarMetadataModel` (frozen/immutable): `name`, `slug`,
`hip_number`, `nomenclature` (Bayer/Flamsteed, e.g. `alLeo`), `magnitude`,
`constellation` (full IAU name derived from the nomenclature, e.g. `"Leo"`;
`None` when the entry has no real designation).

```python
from kerykeion import AstrologicalSubjectFactory, FixedStarDiscoveryFactory
from kerykeion.fixed_stars import FixedStarCatalog
entry = FixedStarCatalog.find("Regulus")
print(entry.name, entry.constellation, entry.magnitude)  # Regulus Leo 1.4
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT",
    online=False)
stars = FixedStarDiscoveryFactory.find_prominent_stars(subject, orb=0.5)
print([(s.name, s.near_point, round(s.orb, 3)) for s in stars[:3]])
```

Cross-references: subjects in `references/subjects.md`; provenance in
`references/backends-and-provenance.md`; sidereal modes in
`references/zodiac-houses-perspectives.md`; VoC Moon / sun times / planetary
hours in `references/calendars-hours-moon.md`.

### Sign periods (a92)

`SignIngressFactory.sign_periods_from_iso_range(start, end, planets=None, zodiac_type, sidereal_mode)`
/ `sign_periods_from_julian_day(...)` → `SignPeriodsCollectionModel` (`start_jd`,
`end_jd`, `periods`). Per planet, contiguous `SignPeriodModel` stays covering
the whole range: `planet`, `sign`, `sign_num`, `start_jd`, `end_jd`, `start`,
`end`, `start_clipped`, `end_clipped`. The sign at the range start is read in
the same ephemeris session (same frame) as the ingress scan, so stays and
ingresses never disagree — a sidereal request yields sidereal stays. The Moon
is opt-in, as for ingresses.
