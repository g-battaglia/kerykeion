---
name: kerykeion
description: >-
  Write correct Python against the kerykeion astrology library (v6). Use this
  skill WHENEVER a task touches kerykeion — building an
  AstrologicalSubjectFactory subject; natal/synastry/transit/composite/return/
  progression/solar-arc charts; aspects; house systems; sidereal / ayanamsa
  charts; fixed stars; Arabic parts (lots); or time-series data via
  EphemerisDataFactory — even if the user only says "kerykeion", "astrological
  subject", "birth chart", "ephemeris", or pastes code that imports it. It
  pins the real contract: the minimal from_birth_data call, how to read points,
  the two ephemeris backends (libephemeris default / sealed-leb vs swisseph),
  and the a75 provenance + sealed-range rules so generated code reads points,
  warnings and precision metadata without inventing field names.
---

# Using Kerykeion

Kerykeion is a Python astrology library (requires **Python 3.12+**). Everything
starts from a **factory**: you never construct models by hand. The canonical
entry point is `AstrologicalSubjectFactory.from_birth_data(...)`, which returns
an `AstrologicalSubjectModel` — a Pydantic model whose planet/house fields are
`KerykeionPointModel` instances.

**Accuracy rule for you:** field names, point names, house codes, ayanamsa
names, and env-var behavior below are copied from the source. When you need a
detail not in this file, read the source (`kerykeion/astrological_subject_factory.py`,
`kerykeion/schemas/kr_models.py`, `kerykeion/schemas/kr_literals.py`,
`kerykeion/ephemeris_backend.py`) rather than guessing — the model has ~40
optional point fields and inventing one produces a silent `None`.

## Quick start

```bash
pip3 install kerykeion          # pulls libephemeris (default backend) too
pip3 install "kerykeion[swiss]" # optional: adds the Swiss Ephemeris C backend
```

```python
from kerykeion import AstrologicalSubjectFactory

# Offline is the reliable default: pass coordinates + IANA timezone and
# online=False. No network, no GeoNames account needed.
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person",
    year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
    online=False,
)
```

Read points by attribute **or** subscript — `KerykeionPointModel` subclasses a
subscriptable base model, so both styles work:

```python
subject.sun.sign          # "Can"          zodiac sign (3-letter)
subject.sun.abs_pos       # 112.34...      absolute longitude 0–360
subject.sun.position      # 22.34...       degrees within the sign (0–30)
subject.moon.element      # "Water"
subject.sun["retrograde"] # False          subscript access is equivalent
subject.first_house.sign  # houses: first_house ... twelfth_house
subject.ascendant.abs_pos # axes: ascendant, medium_coeli, descendant, imum_coeli
```

**Key nuance:** the 12 house cusps are always present. Almost every *point*
field (`sun`, `moon`, ... and the ~40 optional bodies) is `Optional` — it is
`None` unless that point was in `active_points`. Guard optional-point access.
The luminaries are the exception on the failure side: if Sun or Moon cannot be
computed (e.g. out-of-range date) the whole call raises `KerykeionException`
instead of returning `None`, because a chart without them is unusable.

Online mode (`online=True`) resolves `city`/`nation` via GeoNames and needs a
`geonames_username` (free at geonames.org) or the `KERYKEION_GEONAMES_USERNAME`
env var. Offline mode requires `lng`, `lat`, **and** `tz_str`.

### from_birth_data — the parameters that matter

Full signature is large; these are the ones you actually set:

| Param | Meaning | Default |
|---|---|---|
| `name` | label | `"Now"` |
| `year, month, day, hour, minute` | birth/event moment (local wall time) | current |
| `seconds` | keyword-only seconds | `0` |
| `lng, lat, tz_str` | required when `online=False` | — |
| `city, nation` | used when `online=True` | — |
| `online` | GeoNames lookup toggle | `True` |
| `zodiac_type` | `"Tropical"` / `"Sidereal"` | `"Tropical"` |
| `sidereal_mode` | ayanamsa name, only with Sidereal | `None` |
| `houses_system_identifier` | 1-char house-system code | `"P"` (Placidus) |
| `perspective_type` | `"Apparent Geocentric"` etc. | `"Apparent Geocentric"` |
| `active_points` | list of point names to compute | `None` → defaults |
| `active_fixed_stars` | list of star names (**separate channel**) | `None` |
| `altitude` | meters, for Topocentric | `None` |
| `calculate_dignities / _nakshatra / _gauquelin / _nutation / _local_space` | extra per-point enrichments | `False` |

`hour`/`minute` are **local** wall-clock time in `tz_str`; kerykeion handles the
DST/UTC conversion. Do not pre-convert to UTC.

## The two ephemeris backends

Kerykeion computes through one of two mutually exclusive backends, selected by
the `KERYKEION_BACKEND` env var (auto-detect tries `libephemeris` first):

- **`libephemeris`** (default) — pure Python, NASA JPL DE440/DE441 via Skyfield
  plus precomputed `.leb` binary files. No C compiler. This is the only backend
  that populates **provenance metadata** (`source`, `precision_class`, coverage
  window, `source_reviewed`) on points.
- **`swisseph`** (`pip install "kerykeion[swiss]"`) — the Swiss Ephemeris C
  bindings. Needs `.se1` data files or silently falls back to the lower-precision
  Moshier analytical ephemeris. Provenance fields stay `None` here.

Detect the active backend at runtime:

```python
from kerykeion import BACKEND_NAME   # "libephemeris" or "swisseph"
```

On libephemeris the **calculation mode** is pinned by `KERYKEION_LEB_MODE`
(default `"leb"`), which requires `.leb` files and enforces a **sealed** network
policy — no silent download, no silent fallback to Skyfield. That is why an
out-of-range date raises instead of degrading (see Provenance below).

Full backend matrix, all env vars (`KERYKEION_BACKEND`, `KERYKEION_LEB_MODE`,
`KERYKEION_EPHE_PATH`), sealed-mode semantics, and tier downloads live in
**`references/backends.md`** — read it when the task is about backend choice,
precision, offline packaging, or Swiss Ephemeris setup.

## active_points vs active_fixed_stars — do not mix them

These are **two different channels**. Fixed stars are NOT astrological "points"
in v6.

- `active_points` takes names from the `AstrologicalPoint` literal
  (`kerykeion/schemas/kr_literals.py`): planets, lunar nodes, Lilith/Priapus
  variants, Chiron, asteroids (`Ceres`, `Pallas`, `Juno`, `Vesta`), TNOs
  (`Eris`, `Sedna`, `Haumea`, `Makemake`, `Ixion`, `Orcus`, `Quaoar`), Uranian
  bodies, Arabic parts, axes, and cusps. Default (`None`) computes
  `DEFAULT_ACTIVE_POINTS`: Sun–Pluto, `True_North_Lunar_Node`, `Chiron`,
  `Ascendant`, `Medium_Coeli`.
- `active_fixed_stars` takes star names (e.g. `["Regulus", "Aldebaran"]`).
  Results land in **`subject.fixed_stars`** (a list), looked up with
  `subject.find_fixed_star("regulus")` (case-insensitive; spaces, dashes and
  underscores are interchangeable).

```python
from kerykeion.settings.config_constants import (
    ROYAL_FIXED_STARS, BEHENIAN_FIXED_STARS, DEFAULT_FIXED_STARS,
)
subject = AstrologicalSubjectFactory.from_birth_data(
    "Star Chart", 1990, 7, 15, 10, 30,
    lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
    active_points=["Sun", "Moon", "Mercury", "Venus", "Mars", "Ascendant"],
    active_fixed_stars=ROYAL_FIXED_STARS,
)
regulus = subject.find_fixed_star("Regulus")   # KerykeionPointModel, has .magnitude
```

Guardrails the factory enforces (so know them, don't fight them):

- `active_points=[]` (empty list) → `KerykeionException`. Pass `None` for
  defaults; an empty list would otherwise be read as "no filter" = full chart.
- Star names passed inside `active_points` (v5 habit) are **redirected** to
  `active_fixed_stars` with a warning; an all-stars `active_points` raises.
- Unknown point names raise `KerykeionException` — a typo like `"Sunn"` fails
  loudly instead of silently vanishing.
- The perspective's center body is dropped (Earth in geocentric, Sun in
  heliocentric); geocentric-only points (nodes, Lilith/apogee) are dropped in
  non-geocentric perspectives, each with a warning.

## House systems and sidereal charts

`houses_system_identifier` is a **single character**. Common ones: `"P"`
Placidus (default), `"K"` Koch, `"A"` Equal, `"W"` Whole Sign, `"O"` Porphyry,
`"R"` Regiomontanus, `"C"` Campanus. (Full A–Y table in the reference.)

For sidereal work, `zodiac_type` and `sidereal_mode` must be **coherent**:

- `zodiac_type="Sidereal"` requires a `sidereal_mode` (e.g. `"LAHIRI"`,
  `"FAGAN_BRADLEY"`). The model rejects a sidereal chart with no ayanamsa.
- Setting `sidereal_mode` while `zodiac_type` is Tropical raises
  `KerykeionException` ("You can't set a sidereal mode with a Tropical zodiac
  type!").
- `sidereal_mode="USER"` requires `custom_ayanamsa_t0` (reference-epoch Julian
  Day) **and** `custom_ayanamsa_ayan_t0` (offset in degrees at that epoch).
- The resulting offset is reported on `subject.ayanamsa_value`.

Polar caveat: quadrant systems (Placidus `P`, Koch `K`) are undefined inside the
polar circle; kerykeion falls back to the ±66° limit for cusps **with a
WARNING** (planet positions keep the real latitude). Use `W`/`A`/`O` for polar
charts. The full ayanamsa list, house table, perspectives, and the nakshatra
sidereal caveat are in **`references/sidereal-and-houses.md`**.

## Arabic parts (lots)

`Pars_Fortunae`, `Pars_Spiritus`, `Pars_Amoris`, `Pars_Fidei` are not in the
defaults — add them to `active_points`. They auto-activate the base points their
formula needs (Sun/Moon/Ascendant, day/night aware). Read via
`subject.pars_fortunae`, etc. On libephemeris they are labelled
`source="Derived"` with provenance inherited from their formula primaries.

## Provenance and sealed-range contracts (a75)

On the **libephemeris** backend, ephemeris-backed points carry provenance you can
serialize and trust:

| Field on `KerykeionPointModel` | Meaning |
|---|---|
| `source` | selected source: `"LEB"`, `"SPK"`, `"Skyfield"`, `"Keplerian"`, `"ASSIST"`, `"Analytical"`, `"Derived"`. **Not exhaustive** — treat it as an opaque label, never `assert point.source in {...}` |
| `precision_class` | machine label: `ephemeris`, `analytical`, `approximate`, `numerical-model`, `mixed`, `unverified-local` |
| `ephemeris_coverage_start_jd` / `ephemeris_coverage_end_jd` | backend-reported coverage window (JD) |
| `source_reviewed` | did the active source artifact pass the backend's pinned review gate |

`source` → `precision_class` is a coarse mapping from the source name:
`Keplerian*` → `approximate`, `Analytical*` → `analytical`,
`LEB`/`SPK`/`Skyfield` → `ephemeris`, and any other label (e.g. `ASSIST`, the
live n-body integration fallback) → `numerical-model` — an unrecognized source
is never promoted to `ephemeris`. For `source == "LEB"` the backend's per-body
coverage class then overrides it.

`"Keplerian"` is **not** an exotic edge case: it is what the *default* point set
produces whenever a body falls outside its LEB coverage — e.g. Chiron on a
16th-century chart comes back `source="Keplerian"`, `precision_class="approximate"`.
Code that matches exhaustively on the source values will break on it.

These stay `None` on swisseph, and are **intentionally** `None` even on
libephemeris for points derived from house geometry (Ascendant, Medium Coeli,
Vertex, house cusps) and for fixed stars — they have no per-body coverage
inventory. There is no "every point has provenance" guarantee.

**Derived points inherit** provenance from their primaries: antipodes (South
Nodes, Priapus variants, Descendant, Imum Coeli, Anti-Vertex) inherit from their
single primary; Arabic parts inherit from all primaries in their formula —
`source="Derived"`, `precision_class` collapses to `"mixed"` when the primaries
disagree, coverage is the **intersection** (max start, min end),
`source_reviewed` is the AND of the primaries.

**Omitted optional points → `subject.ephemeris_warnings`** (a list of
`EphemerisWarningModel`). When an *optional* body cannot be produced by any
permitted source, it is removed from `active_points` and a structured warning is
appended with `code` / `point_name` / `body_id` / `requested_jd` / `message` /
`coverage_start_jd` / `coverage_end_jd`. Codes include
`date_outside_ephemeris_coverage`, `ephemeris_calculation_failed`,
`unsupported_by_backend`. Check this list rather than assuming every requested
point exists:

```python
for w in subject.ephemeris_warnings:
    print(w.point_name, w.code, w.message)
```

**Sealed tier boundary (new in a75).** A fresh install covers only **1849–2150**
(JPL DE440s). The medium LEB core covers `[1550-01-01, 2650-01-01)` — JD
`[2287185.5, 2688952.5)`, **upper bound exclusive**. Dates at or beyond the
boundary now raise the typed `EphemerisRangeError` (wrapped in
`KerykeionException` for the luminaries) **instead of silently substituting a
lower-precision source**. To chart wider ranges, install a wider tier first:

```python
import libephemeris
libephemeris.download_leb_for_tier("medium")     # 1550–2650 (through 2649-12-31)
libephemeris.download_leb_for_tier("extended")   # full range, incl. BCE dates
```

## Common traps

1. **Stars in the wrong channel.** Fixed stars go in `active_fixed_stars` and
   come back on `subject.fixed_stars` — not in `active_points`/`subject.sun`-style
   attributes. Mixing them triggers a warning-redirect at best, an exception at
   worst.
2. **Empty `active_points` list.** Raises. Use `None` for the defaults.
3. **Sidereal without an ayanamsa / ayanamsa with Tropical.** Both are errors —
   keep `zodiac_type` and `sidereal_mode` coherent.
4. **Expecting provenance/warnings on swisseph.** They only populate on
   libephemeris. Branch on `BACKEND_NAME` if the code must handle both.
5. **Out-of-range dates.** Luminaries raise `KerykeionException`; optional bodies
   land in `ephemeris_warnings`; past the medium tier bound you get
   `EphemerisRangeError`. Install a wider tier — do not expect silent degradation.
6. **Optional points are `None`.** Only requested points exist; guard access.
   Houses always exist; luminaries raise rather than return `None`.
7. **Nested ephemeris sessions.** `ephemeris_session()` rejects same-thread
   nesting with `RuntimeError`; never build a subject or call another factory
   from inside an open session.
8. **Time is local.** Pass local wall-clock `hour`/`minute` with `tz_str`; do not
   pre-convert to UTC.

## Building charts, aspects, and series

- SVG: `ChartDataFactory.create_natal_chart_data(subject)` →
  `ChartDrawer(chart_data=...)` → `.save_svg(output_path=dir, filename="x")` or
  `.generate_svg_string()`. Other builders: `create_synastry_chart_data`,
  `create_transit_chart_data`, `create_composite_chart_data`,
  `create_return_chart_data`, `create_progression_chart_data`.
- Aspects: `AspectsFactory.single_chart_aspects(subject)` and
  `AspectsFactory.dual_chart_aspects(first, second)`.
- Returns / progressions / solar arc / transit series and the full
  `EphemerisDataFactory` contract (including the `fixed_stars` sample key and the
  point caps) are in **`references/ephemeris-series.md`**.

## Reference index

- `references/backends.md` — libephemeris vs swisseph, env vars, sealed leb mode,
  provenance availability, tier downloads, Swiss Ephemeris data setup.
- `references/ephemeris-series.md` — `EphemerisDataFactory`,
  `PlanetaryReturnFactory`, secondary progressions, solar arc, transit ranges.
- `references/sidereal-and-houses.md` — zodiac/ayanamsa coherence, the full
  house-system table, perspectives, Arabic parts, nakshatra caveat.
