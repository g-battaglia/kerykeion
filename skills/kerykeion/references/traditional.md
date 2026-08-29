# Traditional techniques

Time-lord systems (annual profections, firdaria, zodiacal releasing), horary
indicators, primary directions, mutual receptions, the essential-dignities
toolbox and the Vedic nakshatra helpers. Every factory consumes an
`AstrologicalSubjectModel` (see `references/subjects.md`) and returns Pydantic
models; all factories and result models named here are importable from the
top-level `kerykeion` package unless marked **Subpackage import**. Each feature
lives in its own subpackage: `kerykeion/{profections,firdaria,
zodiacal_releasing,horary,primary_directions,receptions}/factory.py`, plus
`kerykeion/dignities/` and `kerykeion/vedic/`.

## Contents

- [Frame prerequisites and refusals](#frame-prerequisites-and-refusals)
- [ProfectionsFactory — annual profections](#profectionsfactory--annual-profections)
- [FirdariaFactory — Persian time lords](#firdariafactory--persian-time-lords)
- [ZodiacalReleasingFactory — aphesis from a lot](#zodiacalreleasingfactory--aphesis-from-a-lot)
- [HoraryIndicatorsFactory — significators and considerations](#horaryindicatorsfactory--significators-and-considerations)
- [PrimaryDirectionsFactory — Placidus semi-arc directions](#primarydirectionsfactory--placidus-semi-arc-directions)
- [MutualReceptionsFactory — dignity exchanges](#mutualreceptionsfactory--dignity-exchanges)
- [Dignities toolbox](#dignities-toolbox)
- [Vedic helpers](#vedic-helpers)

## Frame prerequisites and refusals

Each factory validates its own prerequisites and raises `KerykeionException`. Verified in 6.0.0a90:

| Factory | Heliocentric / barycentric / selenocentric / planetocentric subject | Midpoint composite subject |
|---|---|---|
| `HoraryIndicatorsFactory` | **raises** (explicit terrestrial-frame gate) | accepted (works on cusps present) |
| `MutualReceptionsFactory` | **raises** (explicit terrestrial-frame gate) | accepted |
| `FirdariaFactory` | accepted (sect is computed geocentrically at birth) | **raises** — no boolean `is_diurnal` |
| `ProfectionsFactory` | accepted (houses are still cast for the birthplace) | **raises** — no birth moment to anchor |
| `ZodiacalReleasingFactory` | **raises** for Heliocentric and Selenocentric (the dropped center body — Sun or Moon — makes the lot unresolvable) | **raises** — no birth moment |
| `PrimaryDirectionsFactory` | accepted (session forwards the subject's own frame) | **raises** — `julian_day` is `None` |

The explicit gate is `has_terrestrial_frame` (`kerykeion/utilities/core.py`):
allowed `perspective_type` values are `"Apparent Geocentric"`, `"True
Geocentric"`, `"Topocentric"` (a subject with no `perspective_type` attribute
is trusted). `FirdariaFactory` additionally requires `subject.is_diurnal` to be
a real `bool` — a midpoint composite carries `None` and is refused, never guessed.

## ProfectionsFactory — annual profections

`ProfectionsFactory.from_subject(subject, *, target_date=None, years_before=3, years_after=4)` → `ProfectionsModel`

| Kwarg | Default | Meaning |
|---|---|---|
| `target_date` | `None` | ISO `YYYY-MM-DD`; astronomical year numbering accepted (`'-0550-10-07'`). `None` → today in the subject's timezone |
| `years_before` | `3` | Past years in the table (negative clamped to 0) |
| `years_after` | `4` | Future years in the table (negative clamped to 0) |

Profected house = `(age % 12) + 1` counted from the Ascendant; the sign is read
from that house's cusp **in the subject's own house system** (whole-sign charts
profect through whole signs by construction); the Lord of the Year is
`get_domicile_ruler(sign)`. Age increments at the civil birthday anniversary; a
Feb-29 birthday rolls to Mar-1 in common years. Raises when any of the twelve
cusps is missing, `target_date` is unparseable, or it precedes birth.

`ProfectionsModel`: `current: ProfectionYearModel`, `years:
list[ProfectionYearModel]` (`years_before + years_after + 1` entries).
`ProfectionYearModel`: `age: int`, `house: int` (1–12), `sign`, `lord`
(classical planet), `year_start`/`year_end` (ISO anniversary dates).

## FirdariaFactory — Persian time lords

`FirdariaFactory.from_subject(subject, *, target_date=None, life_cap_years=120)` → `FirdariaModel`

| Kwarg | Default | Meaning |
|---|---|---|
| `target_date` | `None` | ISO date **or datetime**; astronomical numbering accepted. `None` → now in the subject's timezone |
| `life_cap_years` | `120` | How far the timeline unrolls (min clamp 1); the 75-year cycle repeats past 75 |

Day charts open with the Sun (`Sun 10, Venus 8, Mercury 13, Moon 9, Saturn 11,
Jupiter 12, Mars 7, North_Node 3, South_Node 2` years); night charts start the
same ring at the Moon. Each planetary period divides into 7 equal sub-periods
starting from its own lord; the two node periods are **not** subdivided. A
firdaria "year" is the Julian year (365.25 d), and boundaries fall at the birth
time of day, not midnight. Boundary containment is decided on a whole-second
grid, so a serialized `start`/`end` fed back as `target_date` selects that
period consistently. BCE-safe (pure Julian-Day arithmetic).

`FirdariaModel`: `is_diurnal: bool`, `periods`, `current`, `current_sub` (both
Optional). `FirdariaPeriodModel`: `lord: str` (classical planet or
`North_Node`/`South_Node`), `years: int`, `age_start`, `age_end`, `start`/`end`
(local ISO datetime), `sub_periods: list[FirdariaSubPeriodModel]` — each with
`lord` (classical planet), `start`, `end`.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion import ProfectionsFactory, FirdariaFactory
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT",
    online=False)
prof = ProfectionsFactory.from_subject(subject, target_date="2025-09-01")
print(prof.current.age, prof.current.house, prof.current.sign, prof.current.lord)
# 35 12 Leo Sun
fir = FirdariaFactory.from_subject(subject, target_date="2025-09-01")
print(fir.is_diurnal, fir.current.lord, fir.current_sub.lord)
# True Moon Mars
```

## ZodiacalReleasingFactory — aphesis from a lot

`ZodiacalReleasingFactory.from_subject(subject, *, lot="fortune", levels=2, target_date=None, life_cap_years=100)` → `ZodiacalReleasingModel`

| Kwarg | Default | Meaning |
|---|---|---|
| `lot` | `"fortune"` | `"fortune"` or `"spirit"`; anything else raises |
| `levels` | `2` | Subdivision depth, clamped to 1–4. L1/L2 built in full; L3–L4 only along the target-date path |
| `target_date` | `None` | ISO `YYYY-MM-DD`, **timezone-naive** (aware raises). `None` → no `current_path`, only levels ≤ 2 built |
| `life_cap_years` | `100` | L1 horizon in years of life; auto-extended to cover `target_date` + ~10 y |

**Subpackage import:** `from kerykeion.zodiacal_releasing.factory import LotName`
— `LotName = Literal["fortune", "spirit"]` (the type alias is not re-exported
anywhere else).

Fortune reuses the subject's own `pars_fortunae` when present, else the
sect-aware formula; Spirit is `Asc + Sun − Moon` by day, `Asc + Moon − Sun` by
night. Periods run in zodiacal order from the lot's sign for the Valens general
years (Ari 15, Tau 8, Gem 20, Can 25, Leo 19, Vir 20, Lib 8, Sco 15, Sag 12,
Cap 27, Aqu 30, Pis 12); a year here is tropical (365.2422 d — deliberately not
unified with firdaria's Julian year). `is_angular` (peak periods) is counted
1st/4th/7th/10th **from the natal Lot of Fortune** whichever lot is released.
Raises when Asc/Sun/Moon are unavailable (unknown birth time, heliocentric).

`ZodiacalReleasingModel`: `lot`, `lot_sign`, `lot_degree: float`,
`periods: list[ZRPeriodModel]` (L1), `current_path: list[ZRPeriodModel]` (L1 →
deepest computed level; empty without `target_date`). `ZRPeriodModel`: `sign`,
`ruler` (domicile lord), `level: int`, `start`/`end` (ISO **date only**),
`years: float`, `is_angular`, `is_loosing_the_bond`, `subperiods` (nested).

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion import ZodiacalReleasingFactory
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT",
    online=False)
zr = ZodiacalReleasingFactory.from_subject(
    subject, lot="spirit", levels=3, target_date="2025-09-01")
print(zr.lot_sign, [(p.sign, p.level) for p in zr.current_path])
# Sag [('Cap', 1), ('Lib', 2), ('Sag', 3)]
```

## HoraryIndicatorsFactory — significators and considerations

`HoraryIndicatorsFactory.from_subject(subject, *, is_moon_void=None)` → `HoraryIndicatorsModel`

`is_moon_void: Optional[bool]` — pass the result of the separate void-of-course
search (`VoidOfCourseMoonFactory`, see `references/calendars-hours-moon.md`);
`None` simply omits both Moon considerations. Refuses non-terrestrial charts
(see table above).

`HoraryIndicatorsModel`: `querent` / `quesited` (`HorarySignificatorModel` for
houses 1 and 7), `ascendant_degree: Optional[float]` (0–30, read from the true
Ascendant point, **not** the first-house cusp — under Whole Sign the cusp sits
at 0° and would flag every chart "too early"), `considerations:
list[HoraryConsiderationModel]`, `mutual_receptions: list[MutualReceptionModel]`.

`HorarySignificatorModel`: `house: int`, `sign`, `ruler` (domicile lord of the
cusp sign), `ruler_sign`, `ruler_house`, `ruler_house_number` (1–12),
`ruler_retrograde`, `essential_dignity` (only with `calculate_dignities=True`).

`HoraryConsiderationModel` carries a stable `key` + `status`
(`"favorable" | "caution" | "neutral"`) — wording belongs to the consumer.
Keys: `asc_early_degree` (< 3°), `asc_late_degree` (≥ 27°), `asc_judgeable`,
`moon_void`, `moon_not_void`, `saturn_in_first`, `saturn_in_seventh`.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion import HoraryIndicatorsFactory
question = AstrologicalSubjectFactory.from_birth_data(
    name="Question", year=2025, month=6, day=4, hour=15, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT",
    online=False)
ind = HoraryIndicatorsFactory.from_subject(question, is_moon_void=False)
print(ind.querent.ruler, ind.quesited.ruler, round(ind.ascendant_degree, 2))
# Venus Mars 14.3
print([(c.key, c.status) for c in ind.considerations])
# [('asc_judgeable', 'favorable'), ('moon_not_void', 'favorable')]
```

## PrimaryDirectionsFactory — Placidus semi-arc directions

`PrimaryDirectionsFactory.compute(subject, *, max_years=100, rate_key="ptolemy", aspects=None)` → `List[PrimaryDirectionModel]`

| Kwarg | Default | Meaning |
|---|---|---|
| `max_years` | `100` (float) | Keep directions with `0.1 < years <= max_years`; negative/non-finite raises |
| `rate_key` | `"ptolemy"` | `"ptolemy"` (1° = 1 y) or `"naibod"` (0.98564° = 1 y); anything else raises |
| `aspects` | `None` | Subset of `conjunction, sextile, square, trine, opposition`; `None` → all five; a bare string or unknown name raises |

Points directed (`DIRECTION_POINTS`): Sun–Saturn + `Ascendant` +
`Medium_Coeli`, every pair in both roles; sextile/square/trine direct both the
dexter and sinister aspect points. Results are sorted by `direction_years`.
**Trap:** `is_converse=True` arcs are the arithmetic complement `360 − direct`,
NOT the classical converse method — treat converse timings as approximate.
Sidereal and non-geocentric frames are forwarded to the ephemeris session.
Raises when `julian_day`/`lat`/`lng` are missing (midpoint composites).

`PrimaryDirectionModel`: `promissor`, `significator`, `aspect`, `arc: float`
(degrees of RA), `direction_years: float`, `rate_key`, `is_converse: bool`.

`PrimaryDirectionsFactory.compute_speculum(subject)` → `List[SpeculumEntryModel]`
with per-point `name`, `ecliptic_longitude`, `right_ascension`, `declination`,
`meridian_distance` (signed, from MC), `semi_arc`, `is_above_horizon`, `pole`
(Placidian "under the pole"), `oblique_ascension` (OA east / OD west).

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion import PrimaryDirectionsFactory
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT",
    online=False)
directions = PrimaryDirectionsFactory.compute(subject, max_years=30, rate_key="naibod")
first = directions[0]
print(first.promissor, first.aspect, first.significator, first.direction_years)
speculum = PrimaryDirectionsFactory.compute_speculum(subject)
print(speculum[0].name, speculum[0].is_above_horizon)  # Sun True
```

## MutualReceptionsFactory — dignity exchanges

`MutualReceptionsFactory.from_subject(subject)` → `MutualReceptionsModel`

Scans the seven classical planets only (no nodes, no outers); planets absent
from the subject are skipped. Detects `"domicile"` (each in a sign the other
rules) and `"exaltation"` (each in the other's exaltation sign), one
`MutualReceptionModel` per deduplicated pair and type: `first_planet`,
`second_planet`, `reception_type: Literal["domicile", "exaltation"]`. Refuses
non-terrestrial charts; an empty `receptions` list is a normal result.

## Dignities toolbox

**Subpackage import:** `from kerykeion.dignities import calculate_essential_dignity, get_domicile_ruler, get_exaltation_ruler, get_triplicity_lords`
(the package `__all__`, none re-exported top-level).

| Helper | Signature | Returns |
|---|---|---|
| `calculate_essential_dignity` | `(planet_name: str, sign: str, element: str, position: float, is_diurnal: bool)` | dict: `decan_number`, `decan_ruler`, `term_ruler`, `essential_dignity`, `dignity_score` — all `None` for non-classical planets |
| `get_domicile_ruler` | `(sign: Sign)` | `ClassicalPlanet` — traditional ruler, never a modern co-ruler |
| `get_exaltation_ruler` | `(sign: Sign)` | `Optional[ClassicalPlanet]` — `None` for signs without a classical exaltation |
| `get_triplicity_lords` | `(element: Element, is_diurnal: bool)` | `TriplicityLordsModel`: `element`, `sect`, `primary` (in-sect), `secondary`, `participating`; bad element raises |

Ptolemaic scoring: +5 domicile, +4 exaltation, +3 triplicity (in-sect lord
only), +2 Egyptian term, +1 Chaldean face, −4 fall, −5 detriment;
`essential_dignity` is the single highest label (`"Peregrine"` when none),
`dignity_score` the net sum. `position` is the degree **within** the sign
(0–30), not the absolute longitude. Building a subject with
`calculate_dignities=True` runs this same function per classical planet and
stores the five keys on each `KerykeionPointModel` (see
`references/subjects.md`).

## Vedic helpers

**Subpackage import:** `from kerykeion.vedic import calculate_nakshatra`
(package `__all__` contains only this). `get_dasha_lord` is one level deeper:
`from kerykeion.vedic.nakshatra_data import get_dasha_lord`.

- `calculate_nakshatra(abs_pos: float) -> dict` — keys `nakshatra` (name),
  `nakshatra_number` (1–27), `nakshatra_pada` (1–4), `nakshatra_lord`
  (Vimsottari Dasha lord). It divides the circle and applies no ayanamsa of its
  own, so it expects a **sidereal** longitude; a tropical one passed in lands
  about two nakshatras off.
- `get_dasha_lord(nakshatra_index: int) -> str` — 0-based index into the
  repeating 9-lord Vimsottari sequence (Ketu, Venus, Sun, Moon, Mars, Rahu,
  Jupiter, Saturn, Mercury).

Building a subject with `calculate_nakshatra=True` stores the four keys on
every point, and the factory supplies the sidereal longitude either way: a
sidereal chart's own, or a non-sidereal chart's rotated by `nakshatra_ayanamsa`
(default `"LAHIRI"`) for the division only. Call the helper directly and the
rotation is yours to do. See `references/zodiac-houses-perspectives.md`.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion import MutualReceptionsFactory
from kerykeion.dignities import (calculate_essential_dignity,
    get_domicile_ruler, get_triplicity_lords)
from kerykeion.vedic import calculate_nakshatra
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT",
    online=False)
print(MutualReceptionsFactory.from_subject(subject).receptions)  # [] (none here)
print(get_domicile_ruler("Sco"))                                 # Mars
print(get_triplicity_lords("Fire", is_diurnal=True).primary)     # Sun
dig = calculate_essential_dignity(planet_name="Mars", sign="Ari",
    element="Fire", position=5.0, is_diurnal=True)
print(dig["essential_dignity"], dig["dignity_score"])            # Domicile 6
print(calculate_nakshatra(45.0)["nakshatra"])                    # Rohini
```
