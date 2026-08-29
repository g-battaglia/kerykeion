# Subjects: building and reading

Everything starts with `AstrologicalSubjectFactory` (import from `kerykeion`), which returns an immutable-by-convention Pydantic `AstrologicalSubjectModel`; you never construct models by hand. This file covers the three constructors and every kwarg, the point/model field layout, the `AstrologicalPoint` literal, the two selection channels (`active_points` vs `active_fixed_stars`), point-set presets, enrichment flags, online/offline location rules, and `CompositeSubjectFactory`.

## Contents
- [The three constructors](#the-three-constructors)
- [`from_birth_data` kwargs](#from_birth_data-kwargs)
- [Online vs offline location](#online-vs-offline-location)
- [Historical dates and DST](#historical-dates-and-dst)
- [Reading the model](#reading-the-model)
- [`KerykeionPointModel` field groups](#kerykeionpointmodel-field-groups)
- [The `AstrologicalPoint` literal (76 values)](#the-astrologicalpoint-literal-76-values)
- [Other literals](#other-literals)
- [Two channels: `active_points` vs `active_fixed_stars`](#two-channels-active_points-vs-active_fixed_stars)
- [Point-set presets](#point-set-presets)
- [Enrichment flags](#enrichment-flags)
- [Composite subjects](#composite-subjects)

## The three constructors

All three are classmethods on `AstrologicalSubjectFactory` returning `AstrologicalSubjectModel`. Source: `kerykeion/astrological_subject/factory.py`.

| Constructor | Use case | Time input |
|---|---|---|
| `from_birth_data(...)` | natal/event charts (primary API) | local wall time (`year..minute`, kw-only `seconds`) |
| `from_iso_utc_time(name, iso_utc_time, ...)` | DB/API timestamps | ISO 8601 UTC string (`"1990-07-15T08:30:00Z"`) |
| `from_current_time(...)` | horary/"now" charts | captured at call time |

**Trap — `from_iso_utc_time` LACKS `is_dst`, `seconds`, and `cache_expire_after_days`** (seconds come from the timestamp; the fold side is derived from the unambiguous UTC instant). `from_current_time` lacks the same three. Both DO accept all v6 flags (`active_fixed_stars`, `calculate_dignities`, `calculate_nakshatra`, `calculate_gauquelin`, `calculate_nutation`, `calculate_local_space`) and forward them to `from_birth_data`. `from_iso_utc_time` quirks: `name` and `iso_utc_time` are required; `tz_str` defaults to `"Etc/GMT"` (the wall time is converted INTO this zone — pass the real zone); offset-less timestamps are read as UTC; malformed timestamps raise `KerykeionException`. UTC instants inside a historical double-DST fold are supported: the resolved offset is passed through and the exact UTC instant reconstructed (the fold only needs `is_dst` disambiguation in `from_birth_data`, where the input is the ambiguous WALL time).

```python
from kerykeion import AstrologicalSubjectFactory
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
    city="Rome", nation="IT", online=False)
print(subject.sun.sign, subject.sun.position)   # "Can" 22.6...
print(subject["moon"]["sign"])                  # subscript access works too
print(subject.moon.get("house"))                # .get() with default, dict-style
print(subject.iso_formatted_utc_datetime, subject.julian_day, subject.is_diurnal)
```

`from_current_time` notes: it captures the instant at execution time (seconds included) and, when online, resolves the timezone BEFORE reading the clock so the wall time matches the resolved zone. Passing `tz_str` together with `online=True` and a `city` is contradictory (the lookup may resolve a different zone than the one the clock was read in) — either give the full offline triple `lng`/`lat`/`tz_str` with `online=False`, or let the online lookup provide everything.

```python
from kerykeion import AstrologicalSubjectFactory
event = AstrologicalSubjectFactory.from_iso_utc_time(
    name="Event", iso_utc_time="1990-07-15T08:30:00Z",
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False)
print(event.iso_formatted_local_datetime)  # 1990-07-15T10:30:00+02:00 (UTC+2 applied)
print(event.hour, event.minute)            # 10 30 — local wall time, not the UTC one
```

## `from_birth_data` kwargs

| kwarg | default | notes |
|---|---|---|
| `name` | `"Now"` | label only |
| `year, month, day, hour, minute` | `None` | each `None` field falls back to the current instant in the subject's resolved timezone |
| `seconds` | `0` | **keyword-only** (after `*`) |
| `city` / `nation` | `None` → `"Greenwich"` / `"GB"` | used for GeoNames lookup when online; stored on the model either way |
| `lng` / `lat` | `None` → `0.0` / `51.5074` | decimal degrees, E/N positive; explicit values always win over the fetched centroid |
| `tz_str` | `None` → `"Etc/GMT"` | IANA identifier |
| `geonames_username` | `None` | fallback: env `KERYKEION_GEONAMES_USERNAME`, then shared `"century.boy"` (warns) |
| `online` | `True` | see next section |
| `zodiac_type` | `"Tropical"` | `"Sidereal"` needs no mode (auto `FAGAN_BRADLEY`); see `references/zodiac-houses-perspectives.md` |
| `sidereal_mode` | `None` | setting it with Tropical raises; `"USER"` requires both custom-ayanamsa kwargs |
| `houses_system_identifier` | `"P"` | Placidus |
| `perspective_type` | `"Apparent Geocentric"` | others: `"True Geocentric"`, `"Heliocentric"`, `"Topocentric"`, barycentric/planetocentric variants |
| `cache_expire_after_days` | `30` | GeoNames HTTP-cache TTL |
| `is_dst` | `None` | ambiguous wall time: `True` = larger UTC offset, `False` = smaller, `None` **raises** instead of guessing; also resolves non-existent (spring-forward) times; ignored before 1902 |
| `altitude` | `None` | meters, used by Topocentric |
| `active_points` | `None` → `DEFAULT_ACTIVE_POINTS` | `[]` raises — see two-channels section |
| `active_fixed_stars` | `None` | star names → `subject.fixed_stars` |
| `calculate_lunar_phase` | `True` | populated only if Sun+Moon active and perspective is geo/topocentric, else `None` |
| `calculate_dignities` … `calculate_local_space` | `False` | five enrichment flags, see below |
| `custom_ayanamsa_t0` / `custom_ayanamsa_ayan_t0` | `None` | required pair for `sidereal_mode="USER"` |
| `suppress_geonames_warning` | `False` | **keyword-only**; silences the default-username warning |

## Online vs offline location

- **Offline (`online=False`)**: `lng`, `lat` and `tz_str` are all required, else `KerykeionException`. Still pass `city`/`nation` — they are display metadata, and reports/charts will otherwise say "Greenwich, GB".
- **Online (`online=True`, the default)**: anything missing among `lng`/`lat`/`tz_str` is fetched from GeoNames by `city`/`nation`; explicit values are never overwritten. With explicit `lng`/`lat`, no `city`, and no `tz_str`, the timezone is resolved from the coordinates (timezoneJSON endpoint). Username resolution: `geonames_username` kwarg → env `KERYKEION_GEONAMES_USERNAME` → shared default (rate-limited, logs a warning unless `suppress_geonames_warning=True`).

```python
# doc-snippet: no-run  (network)
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Online", year=1990, month=7, day=15, hour=10, minute=30,
    city="Rome", nation="IT", geonames_username="your_username")  # lng/lat/tz fetched
```

### Historical dates and DST

- `is_dst` selects by **UTC offset**, not season: `True` = larger offset, `False` = smaller. It matters only when the wall time is ambiguous (fall-back fold) or non-existent (spring-forward gap); on an ambiguous time with `is_dst=None` the factory raises rather than guessing. Before 1902-01-01 the flag is moot (no DST existed) and nothing is rejected.
- Dates before a zone adopted standard time resolve via the IANA zone's synthetic "LMT" record; the factory re-derives the offset from the birth longitude, and `from_iso_utc_time` applies the same longitude-based LMT so both entry points agree.
- `seconds` (kw-only, `from_birth_data`) and `altitude` (all constructors; feeds Topocentric) are the precision knobs; `julian_day` on the model is the resulting exact instant.

**Subpackage import:** `from kerykeion.geonames import FetchGeonames`
`FetchGeonames(city_name, country_code, username="century.boy", cache_expire_after_days=30, cache_name=None)` is the underlying cached client. Key methods: `get_serialized_data()` (dict with `countryCode`, `timezonestr`, `lat`, `lng`), `get_timezone_for_coordinates(lat, lng)`, `close()`; it is a context manager (use `with`). Cache location: `~/.kerykeion/cache/kerykeion_geonames_cache` (TTL-suffixed sqlite), overridable via env `KERYKEION_GEONAMES_CACHE_NAME` or `FetchGeonames.set_default_cache_name(path)`. The package also exports `DEFAULT_GEONAMES_CACHE_NAME`, `GEONAMES_CACHE_ENV_VAR`, `TRANSIENT_GEONAMES_ERROR_CODES`.

## Reading the model

`AstrologicalSubjectModel` (from `kerykeion` or `kerykeion.schemas`) extends `SubscriptableBaseModel` (importable from `kerykeion.schemas`): every model in the library supports attribute access, subscript get/set/delete (`subject["sun"]`, `subject["name"] = ...`), and `.get(key, default)`. Being Pydantic models, they also serialize (`subject.model_dump()`, `subject.model_dump_json()`) and round-trip (`AstrologicalSubjectModel.model_validate_json(...)`) — the standard way to persist a subject without recomputing. `KerykeionException` (from `kerykeion` or `kerykeion.schemas`) is the library-wide error type — invalid config, missing offline data, ambiguous times, bad point names all raise it.

- **Houses are always present**: `first_house` … `twelfth_house` are required fields, plus `houses_names_list` (ordered `Houses` literal names `"First_House"` … `"Twelfth_House"`, which are also the values point `house` fields hold).
- **Every celestial point field is `Optional`** — a real field whose point was not computed reads as `None` (`subject.eris` on a default subject gives `None`, not an error). A misspelled or non-existent name instead raises `AttributeError` on both attribute and subscript access; only `.get("name", default)` returns a default. Membership in `subject.active_points` and field population are NOT the same set: the four axes are always populated, and Arabic-part formulas auto-populate their primaries (e.g. `active_points=["Pars_Amoris"]` also fills `sun` and `venus`) without adding them to `subject.active_points`.
- **Sun/Moon fail loudly**: a calculation failure on a luminary (typically a date outside loaded ephemeris coverage) raises `KerykeionException`; optional bodies degrade gracefully — dropped from `active_points` and recorded in `subject.ephemeris_warnings` (`EphemerisWarningModel`: `code`, `point_name`, `body_id`, `requested_jd`, `message`, optional `coverage_start_jd`/`coverage_end_jd`).
- Metadata: `name`, `city`, `nation`, `lng`, `lat`, `altitude`, `tz_str`, `year/month/day/hour/minute`, `iso_formatted_local_datetime`, `iso_formatted_utc_datetime`, `julian_day`, `day_of_week`, `is_diurnal` (sect), `zodiac_type`, `sidereal_mode`, `ayanamsa_value` (sidereal only), `nakshatra_ayanamsa` / `nakshatra_ayanamsa_value` (non-sidereal charts that computed nakshatras; `None` otherwise — and `None` on the legacy opt-out too, where `calculate_nakshatra=True` with `nakshatra_ayanamsa=None` DOES compute the nakshatras but records neither field, because no ayanamsa was applied), `houses_system_identifier` (the REQUEST), `houses_system_name`, `perspective_type`, `active_points`.
- Polar charts: `polar_house_fallbacks` records house-system substitutions; properties `effective_houses_system_identifier` / `effective_houses_system_name` give the system actually used (display those, not the request). `coincident_house_cusps` (`list[list[int]]`, 1-based house numbers) lists groups of cusps that stand on one longitude, so the houses between them have no width; empty for every ordinary chart. An angle that IS such a cusp is filed in the house that cusp opens (`imum_coeli.house == "Fourth_House"` when the IC is the fourth cusp), even where several cusps coincide.
- Extras: `lunar_phase` (`LunarPhaseModel`: `degrees_between_s_m`, `moon_phase` (1–28), `moon_emoji`, `moon_phase_name`, `major_phase` (nearest of the four syzygy/quadrature events), `stage` (`"waxing"`/`"waning"`) — or `None`), `fixed_stars` (list), `active_midpoints` (list, populated via `MidpointFactory`), `gauquelin_sector_cusps`, `nutation`.
- `is_out_of_bounds` is computed by default (no flag) for bodies with a declination; it stays `None` on the axes/cusps.
- `subject.find_fixed_star(name)` → `Optional[KerykeionPointModel]`: case-insensitive lookup in `fixed_stars`; spaces/dashes/underscores interchangeable (`"deneb algedi"` == `"Deneb_Algedi"`). Returns `None` when the star was not requested.

## `KerykeionPointModel` field groups

Each populated point/house/star is a `KerykeionPointModel` (also a `SubscriptableBaseModel`). Field groups:

| Group | Fields | Notes |
|---|---|---|
| Identity | `name`, `point_type`, `emoji` | `point_type`: `"AstrologicalPoint"` / `"House"` / `"Midpoint"` (the `PointType` literal) |
| Position & sign | `sign`, `sign_num` (0–11, the `SignNumbers` literal), `quality`, `element`, `position` (0–30 in sign), `abs_pos` (0–360), `house` | `house` is `Optional[Houses]`; house numbers 1–12 are the `HouseNumbers` literal |
| Motion | `retrograde`, `speed` (deg/day, negative = retrograde), `motion_state` | `motion_state` only for the ten planets in Earth-centred perspectives |
| Declination & latitude | `declination`, `ecliptic_latitude`, `is_out_of_bounds` | OOB = \|declination\| beyond the true obliquity |
| Star-only | `magnitude` | `None` for non-stars |
| Discovery-only | `near_point`, `orb`, `aspect`, `longitude`, `latitude`, `degree` | populated by `FixedStarDiscoveryFactory` results only |
| Dignities (flag) | `decan_number`, `decan_ruler`, `term_ruler`, `essential_dignity`, `dignity_score` (−9..+11) | `calculate_dignities=True` |
| Nakshatra (flag) | `nakshatra`, `nakshatra_number` (1–27), `nakshatra_pada` (1–4), `nakshatra_lord` | `calculate_nakshatra=True`; on a non-sidereal chart the longitudes are rotated by `nakshatra_ayanamsa` (default `"LAHIRI"`) first |
| Gauquelin (flag) | `gauquelin_sector` (1–36, fractional) | `calculate_gauquelin=True` |
| Local space (flag) | `azimuth`, `altitude_above_horizon` | `calculate_local_space=True` |
| Provenance | `source`, `precision_class`, `ephemeris_coverage_start_jd`, `ephemeris_coverage_end_jd`, `source_reviewed` | libephemeris backend only — semantics in `references/backends-and-provenance.md` |

## The `AstrologicalPoint` literal (76 values)

`from kerykeion.schemas import AstrologicalPoint` (defined in `kerykeion/schemas/literals.py`). Model field names are the lowercased literal names (`True_North_Lunar_Node` → `subject.true_north_lunar_node`).

| Group | Values |
|---|---|
| Planets (10) | `Sun` `Moon` `Mercury` `Venus` `Mars` `Jupiter` `Saturn` `Uranus` `Neptune` `Pluto` |
| Lunar nodes (4) | `Mean_North_Lunar_Node` `True_North_Lunar_Node` `Mean_South_Lunar_Node` `True_South_Lunar_Node` |
| Lilith family & special bodies (10) | `Chiron` `Mean_Lilith` `True_Lilith` `Interpolated_Lilith` `Mean_Priapus` `True_Priapus` `Interpolated_Perigee` `White_Moon` `Earth` `Pholus` |
| Asteroids (4) | `Ceres` `Pallas` `Juno` `Vesta` |
| TNOs (7) | `Eris` `Sedna` `Haumea` `Makemake` `Ixion` `Orcus` `Quaoar` |
| Fixed stars (23) — **do NOT use in `active_points`; use `active_fixed_stars`** | `Regulus` `Spica` `Aldebaran` `Antares` `Sirius` `Fomalhaut` `Algol` `Betelgeuse` `Canopus` `Procyon` `Arcturus` `Pollux` `Deneb` `Altair` `Rigel` `Achernar` `Capella` `Vega` `Alcyone` `Alphecca` `Algorab` `Deneb_Algedi` `Alkaid` |
| Uranian / Hamburg (8) | `Cupido` `Hades` `Zeus` `Kronos` `Apollon` `Admetos` `Vulkanus` `Poseidon` |
| Arabic parts (4) | `Pars_Fortunae` `Pars_Spiritus` `Pars_Amoris` `Pars_Fidei` |
| Axes / special (2) | `Vertex` `Anti_Vertex` |
| Axial cusps (4) | `Ascendant` `Medium_Coeli` `Descendant` `Imum_Coeli` |

The 23 star names remain in the literal only for v5 type-compatibility; passing them to `active_points` redirects them (see below). Arabic parts auto-activate their required base points; derived opposites (`Descendant`, `Imum_Coeli`, south nodes, Priapus points, `Anti_Vertex`) are computed from their primaries.

## Other literals

- `Sign`: 12 three-letter codes `"Ari" "Tau" "Gem" "Can" "Leo" "Vir" "Lib" "Sco" "Sag" "Cap" "Aqu" "Pis"`.
- `Element`: `"Air" "Fire" "Earth" "Water"`. `Quality`: `"Cardinal" "Fixed" "Mutable"`.
- `MotionState`: `"retrograde" "stationary" "slow" "average" "fast"` (speed classified against the body's mean daily motion).
- All importable from `kerykeion.schemas` (facade over `kerykeion/schemas/literals.py`).

Sign → element/quality mapping (what `point.element` / `point.quality` return):

| | Cardinal | Fixed | Mutable |
|---|---|---|---|
| **Fire** | Ari | Leo | Sag |
| **Earth** | Cap | Tau | Vir |
| **Air** | Lib | Aqu | Gem |
| **Water** | Can | Sco | Pis |

## Two channels: `active_points` vs `active_fixed_stars`

v6 rule: **planets/points go in `active_points` (typed `AstrologicalPoint` names); fixed stars go in `active_fixed_stars` (plain strings from the libephemeris star catalog — any catalog name is accepted, not just the 23 literal names; `kerykeion.fixed_stars.catalog.FixedStarCatalog` is the authority, and underscores in slugs are converted to spaces before lookup)**. Behaviors:

- `active_points=[]` raises `KerykeionException` (pass `None`/omit for defaults — an empty list would otherwise be read downstream as "no filter" and invert into a full chart).
- Unknown names (typos like `"Sunn"`) raise `KerykeionException` — they never vanish silently.
- Star names inside `active_points` are **redirected** to `active_fixed_stars` with a logged warning; if the list would empty out (stars only), it raises.
- Perspective-incompatible points are **dropped with a warning**: the center body of the perspective (Earth for geo/topocentric, Sun for heliocentric, the center planet for planetocentric), and the geocentric-only points (nodes, Lilith/apogee family) in non-geocentric frames. A list reduced to nothing raises.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.settings.config_constants import URANIAN_ACTIVE_POINTS
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT",
    online=False,
    active_points=["Sun", "Moon", "Eris", "Ceres", "Ascendant"] + URANIAN_ACTIVE_POINTS)
print(subject.eris.sign, subject.cupido.sign)   # populated now
print(subject.mercury)                          # None — not requested
```

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.settings.config_constants import ROYAL_FIXED_STARS
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
    active_fixed_stars=ROYAL_FIXED_STARS)
print(len(subject.fixed_stars))                       # 4
reg = subject.find_fixed_star("regulus")              # case-insensitive
print(reg.sign, reg.magnitude)
print(subject.find_fixed_star("Vega"))                # None — not requested
```

```python
# doc-snippet: no-run  (counter-examples: both raise KerykeionException)
AstrologicalSubjectFactory.from_birth_data(..., active_points=[])       # empty list
AstrologicalSubjectFactory.from_birth_data(..., active_points=["Sunn"]) # unknown name
```

## Point-set presets

| Preset | Size | Import | Purpose |
|---|---|---|---|
| `DEFAULT_ACTIVE_POINTS` | 14 | `from kerykeion.settings import ...` | v6 default: 10 planets + `True_North_Lunar_Node`, `Chiron`, `Ascendant`, `Medium_Coeli` |
| `ALL_ACTIVE_POINTS` | 53 | `from kerykeion.settings import ...` | every non-star point |
| `V5_DEFAULT_ACTIVE_POINTS` | 18 | `from kerykeion.settings import ...` | frozen v5 default — restores v5 results (see `references/migration-and-deprecations.md`) |
| `DEFAULT_ACTIVE_ASPECTS` | 5 | `from kerykeion.settings import ...` | aspect presets — see `references/aspects-and-orbs.md` |
| `TRADITIONAL_ASTROLOGY_ACTIVE_POINTS` | 9 | `from kerykeion.settings.config_constants import ...` | Sun–Saturn + true nodes |
| `URANIAN_ACTIVE_POINTS` | 8 | `from kerykeion.settings.config_constants import ...` | Hamburg-school hypotheticals |
| `ROYAL_FIXED_STARS` | 4 | `from kerykeion.settings.config_constants import ...` | for `active_fixed_stars` |
| `BEHENIAN_FIXED_STARS` | 15 | `from kerykeion.settings.config_constants import ...` | for `active_fixed_stars` |
| `DEFAULT_FIXED_STARS` | 23 | `from kerykeion.settings.config_constants import ...` | the v5.12 star set, for `active_fixed_stars` |

Only the first four are re-exported by the `kerykeion.settings` facade; the rest need the deep `config_constants` import.

## Enrichment flags

All default `False` except `calculate_lunar_phase` (default `True`); available on all three constructors.

| Flag | Populates | Trap |
|---|---|---|
| `calculate_dignities` | `decan_number/ruler`, `term_ruler`, `essential_dignity`, `dignity_score` on points | never on fixed stars (rulership undefined) |
| `calculate_nakshatra` | `nakshatra*` fields on points and stars | defined on the SIDEREAL zodiac — a non-sidereal chart's longitudes are rotated by `nakshatra_ayanamsa` (default `"LAHIRI"`) for the division only; `nakshatra_ayanamsa=None` restores the legacy uncorrected values (~24° off) and logs a warning |
| `calculate_gauquelin` | `gauquelin_sector` per point + `subject.gauquelin_sector_cusps` (36 longitudes) | true latitude-dependent sectors, not uniform 10° |
| `calculate_nutation` | `subject.nutation` (`NutationObliquityModel`: true/mean obliquity, nutation in longitude/obliquity) | |
| `calculate_local_space` | `azimuth`, `altitude_above_horizon` per point | Swiss convention: azimuth 0=South, 90=West |
| `calculate_lunar_phase` | `subject.lunar_phase` | requires Sun and Moon active AND a geo/topocentric perspective; otherwise silently `None` |

`nakshatra_ayanamsa` (`Optional[SiderealMode]`, default `"LAHIRI"`) rides with
`calculate_nakshatra` on all three constructors. It is a mode name in its own
right, unrelated to `sidereal_mode`, and is validated even on a Tropical chart
(`"USER"` still needs the two custom-ayanamsa kwargs — but only on a chart that
would actually cast it, so `calculate_nakshatra=False` never demands them). It is
IGNORED on a sidereal chart — those longitudes are already sidereal — and the
subject then records `nakshatra_ayanamsa=None`. Derived charts inherit it:
returns and secondary progressions copy the natal's value, and a Davison
composite adopts it only when both parents agree (otherwise it warns and falls
back to the default). For `"USER"` agreeing means agreeing on the DEFINITION —
`custom_ayanamsa_t0` and `custom_ayanamsa_ayan_t0` — which the composite then
carries over with the mode.
Only a mode actually used is inherited — a natal that computed no nakshatras
records `None` too, and that `None` is not the legacy opt-out, so
`PlanetaryReturnFactory(..., calculate_nakshatra=True)` on such a natal starts
from the `"LAHIRI"` default. `PlanetaryReturnFactory` also TAKES the kwarg
(right after `calculate_nakshatra`), and an explicit value outranks the natal —
`None` included, which is why its default is a sentinel rather than `None`.
Secondary progressions and the Davison composite take no such override; they
read the natal.

## Composite subjects

`CompositeSubjectFactory(first_subject, second_subject, chart_name=None, house_anchor="auto")` (import from `kerykeion`). Both subjects must share zodiac type, sidereal mode, house system, and perspective, or it raises; `active_points` are intersected (disjoint sets raise). Two methods, both returning `CompositeSubjectModel`:

- `get_midpoint_composite_subject_model()` — circular midpoints of points and cusps; not a real sky, so `is_diurnal` is `None` and provenance is absent. Composite cusps keep their own house numbers and are deliberately NOT re-sorted by longitude (re-sorting would swap the composite MC and IC).

  Where the two charts' angles are nearly opposed the twelve near midpoints stop running in order — about one pair in sixteen — and the cusps are repaired the way the field does it: one angle keeps its near midpoint and the others move onto their far one. `house_anchor` picks which: `"auto"` (default; whichever of the Ascendant and Midheaven has its base cusps closer together, matching Solar Fire), `"ascendant"` or `"midheaven"` (Kepler's two methods). Anything else raises `KerykeionException`.

  It is a request, not a guarantee: a frame can only be read where each parent is itself a house division and the two run the same way, and `house_frame` on the model says whether it was granted. Where it was not, every position is its own near midpoint — bar a cusp the parents put exactly opposite another, which is kept opposite it — and all three anchors give the same chart.

  The ring is reconciled with the angles by the ARC each angle stands at from the cusp it shares a number with, averaged from the two parents: zero is the case where the angle IS the cusp, and under whole sign, Morinus, meridian or Carter it is something else. An exact identity outranks an arc; where neither is exact the anchor breaks the tie.
- `get_davison_composite_subject_model(*, custom_ayanamsa_t0=None, custom_ayanamsa_ayan_t0=None)` — midpoint in time (mean Julian Day) and space, cast as a REAL chart at that moment (tz `Etc/GMT`); carries over enrichments both parents share; the keyword pair is required when `sidereal_mode="USER"`.

With `chart_name=None` the composite is named `"{first} and {second} Composite Chart"`.

`CompositeSubjectModel` adds `first_subject`, `second_subject`, `composite_chart_type` (values of the `CompositeChartType` literal: `"Midpoint"` | `"Davison"`), `Optional house_anchor` (which angle the caller ASKED to hold when the cusp ring was repaired; `None` on a Davison chart), `Optional house_frame` (what the twelve turned out to be — `"anchored"` if a frame was hung from that angle and the twelve cover the circle once, `"midpoints"` if no frame spans the two charts but they are still a house division, `"gapped"` if they are not; the two fields are recorded together or not at all, and an a86 payload carrying neither still validates), and `Optional is_diurnal`; location/time metadata fields are optional. It feeds `ChartDataFactory.create_composite_chart_data` — see `references/charts-and-drawing.md`.

```python
from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory
a = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
b = AstrologicalSubjectFactory.from_birth_data(
    name="Partner", year=1992, month=3, day=2, hour=4, minute=15,
    lng=-0.1278, lat=51.5074, tz_str="Europe/London", city="London", nation="GB", online=False)
factory = CompositeSubjectFactory(a, b)
mid = factory.get_midpoint_composite_subject_model()
dav = factory.get_davison_composite_subject_model()
print(mid.composite_chart_type, mid.sun.sign, mid.is_diurnal)   # Midpoint Tau None
print(dav.composite_chart_type, dav.iso_formatted_utc_datetime) # Davison 1991-05-09...
```
