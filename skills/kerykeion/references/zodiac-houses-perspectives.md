# Zodiac, ayanamsa, houses, perspectives, lots

Sources: `kerykeion/schemas/literals.py` (all literal types; also re-exported
from `kerykeion.schemas`), `kerykeion/astrological_subject/factory.py`
(validation, Arabic-part formulas, perspective drops),
`kerykeion/schemas/models.py` (`AstrologicalBaseModel`,
`PolarHouseFallbackModel`), `kerykeion/ephemeris_backend/backend.py` (polar
fallback mechanics). Covers `ZodiacType`, the 48 `SiderealMode` values, the 23
`HousesSystemIdentifier` codes, the 11 `PerspectiveType` values, polar-latitude
house fallbacks, Arabic parts, and `SIGN_CODES`.

## Tropical vs sidereal — coherence rules

`zodiac_type` is `"Tropical"` (default) or `"Sidereal"` (`ZodiacType` literal).

- Sidereal requires a `sidereal_mode`. The factory auto-defaults it to
  `FAGAN_BRADLEY` (`DEFAULT_SIDEREAL_MODE`); the model itself rejects a
  sidereal chart with `sidereal_mode=None` — be explicit when constructing
  models directly.
- Passing `sidereal_mode` with a Tropical chart raises `KerykeionException`
  ("You can't set a sidereal mode with a Tropical zodiac type!").
- The applied offset is reported on `subject.ayanamsa_value` (degrees; tropical
  0 Aries minus sidereal 0 Aries at the chart moment). `None` for tropical
  charts.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.schemas import SIGN_CODES
kwargs = dict(year=1990, month=7, day=15, hour=10, minute=30, lng=12.4964,
              lat=41.9028, tz_str="Europe/Rome", online=False)
trop = AstrologicalSubjectFactory.from_birth_data(name="Tropical", **kwargs)
sid = AstrologicalSubjectFactory.from_birth_data(
    name="Lahiri", zodiac_type="Sidereal", sidereal_mode="LAHIRI", **kwargs)
print(trop.sun.sign, trop.ayanamsa_value)             # Can None
print(sid.sun.sign, round(sid.ayanamsa_value, 3))     # Gem 23.729
assert SIGN_CODES[sid.sun.sign_num] == sid.sun.sign   # sign_num indexes SIGN_CODES
```

### USER ayanamsa

`sidereal_mode="USER"` requires BOTH `custom_ayanamsa_t0` (reference epoch as
Julian Day) and `custom_ayanamsa_ayan_t0` (ayanamsa in degrees at that epoch);
the factory raises `KerykeionException` if either is missing (the model and
`ephemeris_session` raise `ValueError`, and the model also rejects setting only
one of the two on any chart). The backend extrapolates other dates via its
precession model.

```python
from kerykeion import AstrologicalSubjectFactory
u = AstrologicalSubjectFactory.from_birth_data(
    name="Custom Ayanamsa", year=2000, month=1, day=1, hour=0, minute=0,
    lng=0.0, lat=51.5, tz_str="Etc/GMT", online=False,
    zodiac_type="Sidereal", sidereal_mode="USER",
    custom_ayanamsa_t0=2451545.0,     # J2000.0 epoch as Julian Day
    custom_ayanamsa_ayan_t0=23.5)     # ayanamsa in degrees at that epoch
print(u.sun.sign, round(u.ayanamsa_value, 2))
```

### `SiderealMode` — all 48 values

From `kerykeion/schemas/literals.py` (47 named + `USER`):

| Family | Values |
|---|---|
| Indian / Vedic | `LAHIRI` (Indian govt standard), `LAHIRI_1940`, `LAHIRI_ICRC`, `LAHIRI_VP285`, `KRISHNAMURTI` (KP), `KRISHNAMURTI_VP291`, `RAMAN`, `USHASHASHI`, `JN_BHASIN`, `YUKTESHWAR`, `ARYABHATA`, `ARYABHATA_522`, `ARYABHATA_MSUN`, `SURYASIDDHANTA`, `SURYASIDDHANTA_MSUN`, `SS_CITRA`, `SS_REVATI`, `TRUE_CITRA`, `TRUE_MULA`, `TRUE_PUSHYA`, `TRUE_REVATI`, `TRUE_SHEORAN` |
| Western sidereal | `FAGAN_BRADLEY` (default), `DELUCE`, `DJWHAL_KHUL`, `HIPPARCHOS`, `SASSANIAN` |
| Babylonian | `BABYL_KUGLER1`, `BABYL_KUGLER2`, `BABYL_KUGLER3`, `BABYL_HUBER`, `BABYL_ETPSC`, `BABYL_BRITTON` |
| Galactic | `GALCENT_0SAG`, `GALCENT_COCHRANE`, `GALCENT_MULA_WILHELM`, `GALCENT_RGILBRAND`, `GALEQU_FIORENZA`, `GALEQU_IAU1958`, `GALEQU_MULA`, `GALEQU_TRUE`, `GALALIGN_MARDYKS` |
| Reference frames | `J2000`, `J1900`, `B1950` |
| Astronomical | `ALDEBARAN_15TAU`, `VALENS_MOON` |
| User-defined | `USER` (requires the two custom ayanamsa kwargs) |

### Nakshatras on a non-sidereal chart

`calculate_nakshatra=True` fills `nakshatra`, `nakshatra_number` (1–27),
`nakshatra_pada` (1–4), `nakshatra_lord` (Vimsottari Dasha lord) on each point.
Nakshatras divide the **sidereal** zodiac. A sidereal chart supplies those
longitudes itself. Any other chart does not, so its longitudes are rotated by
`nakshatra_ayanamsa` (`Optional[SiderealMode]`, default `"LAHIRI"` — the
ayanamsa Jyotish uses, not the `FAGAN_BRADLEY` default of `sidereal_mode`) for
the 27-fold division only: the chart stays tropical, and its nakshatras match
the sidereal chart cast in the same mode exactly.

The subject records what was used: `nakshatra_ayanamsa` (the mode) and
`nakshatra_ayanamsa_value` (the degrees subtracted). Both are `None` on a
sidereal chart — where the field is ignored and `sidereal_mode` /
`ayanamsa_value` are the answer — and on a chart that computed no nakshatras.

`nakshatra_ayanamsa=None` restores the pre-v6 behaviour: tropical longitudes
fed straight to the sidereal division, every value about two nakshatras off, one
WARNING per subject. It exists only to reproduce values computed by earlier
versions.

```python
from kerykeion import AstrologicalSubjectFactory

tropical = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
    calculate_nakshatra=True,
)
sidereal = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
    zodiac_type="Sidereal", sidereal_mode="LAHIRI",
    calculate_nakshatra=True,
)
print(tropical.nakshatra_ayanamsa, round(tropical.nakshatra_ayanamsa_value, 4))
# LAHIRI 23.7273
print(tropical.moon.nakshatra == sidereal.moon.nakshatra)   # True
print(tropical.moon.sign, sidereal.moon.sign)               # Pis Aqu — the chart is untouched
```

## House systems

`houses_system_identifier` is a single-character code from the
`HousesSystemIdentifier` literal (23 codes; note the lowercase `"i"`). Names
below are the backend's own (`ephe.house_name`), stored on
`subject.houses_system_name`:

| Code | System | | Code | System |
|---|---|---|---|---|
| `A` | equal | | `O` | Porphyry |
| `B` | Alcabitius | | `P` | Placidus (default) |
| `C` | Campanus | | `Q` | Pullen SR |
| `D` | equal (MC) | | `R` | Regiomontanus |
| `F` | Carter poli-equ. | | `S` | Sripati |
| `H` | horizon/azimut | | `T` | Polich/Page |
| `I` | Sunshine | | `U` | Krusinski-Pisa-Goelzer |
| `i` | Sunshine/alt. | | `V` | equal/Vehlow |
| `K` | Koch | | `W` | equal/whole sign |
| `L` | Pullen SD | | `X` | axial rotation/Meridian |
| `M` | Morinus | | `Y` | APC houses |
| `N` | equal/1=Aries | | | |

Read cusps via `subject.first_house` … `subject.twelfth_house` (always
present) and the axes via `subject.ascendant`, `subject.medium_coeli`,
`subject.descendant`, `subject.imum_coeli`. An invalid code raises
`KerykeionException` listing the valid ones.

### Requested vs effective system

`houses_system_identifier`/`houses_system_name` record what was **asked for**
(and are fed back into relocation/returns on purpose). The
`AstrologicalBaseModel` properties `effective_houses_system_identifier` and
`effective_houses_system_name` answer what the cusps were **really computed
with** — they differ from the requested pair only when a polar fallback fired
for the chart's own house system. Anything displaying a chart should read the
effective pair.

### Polar-latitude fallback — `polar_house_fallbacks`

Quadrant systems (Placidus `P`, Koch `K`) are mathematically undefined inside
the polar circle (|lat| beyond ~66.56° for the current obliquity — the exact
threshold is 90° minus the epoch's obliquity and is backend-reported when
known). When — and only when — the backend raises one of
`POLAR_HOUSES_ERROR_TYPES`, kerykeion retries once and appends a
`PolarHouseFallbackModel` to `subject.polar_house_fallbacks` (empty for every
chart outside the polar circle). Two strategies:

- `substitute_system` (default): recompute the cusps with **Porphyry (`O`) at
  the REAL latitude**. The angles (Ascendant, MC, Descendant, IC, Vertex) stay
  exact — they are horizon/meridian intersections independent of any house
  system — so `affects == ["house_cusps"]` and `used_latitude == latitude`.
- `clamp_latitude`: keep the requested system, retry just inside the polar
  limit (backend-reported threshold when available, else the ±66° rule of
  thumb). Chosen automatically for Gauquelin sectors (`G`, a 36-sector
  division no 12-cusp substitute can represent); there
  `affects == ["house_cusps", "angles"]`.

Model fields: `strategy`, `requested_house_system_identifier`/`_name`,
`used_house_system_identifier`/`_name`, `latitude`, `used_latitude`,
`threshold`, `obliquity`, `affects`, `message`. A WARNING is logged either
way. Planetary positions and the persisted latitude always keep the real
value. Systems defined at every latitude (Whole Sign `W`, Equal `A`, Porphyry
`O`, Morinus `M`, Meridian `X`, …) never fall back — prefer them for polar
charts. Raw access: `houses_ex2_with_polar_fallback_ex` in
`kerykeion.ephemeris_backend` (see `references/backends-and-provenance.md`).

```python
from kerykeion import AstrologicalSubjectFactory
s = AstrologicalSubjectFactory.from_birth_data(
    name="Polar", year=1990, month=7, day=15, hour=10, minute=30,
    lng=18.95, lat=69.65, tz_str="Europe/Oslo", city="Tromso", online=False)
fb = s.polar_house_fallbacks[0]
print(fb.strategy, fb.requested_house_system_identifier, "->",
      fb.used_house_system_identifier, fb.affects)   # substitute_system P -> O ['house_cusps']
print(round(fb.threshold, 3), fb.used_latitude == fb.latitude)  # 66.558 True
print(s.houses_system_identifier, s.effective_houses_system_identifier)   # P O
print(s.effective_houses_system_name)                # Porphyry
```

## Perspectives

`perspective_type`, from the `PerspectiveType` literal (11 values):
`"Apparent Geocentric"` (default), `"True Geocentric"`, `"Heliocentric"`,
`"Topocentric"`, `"Barycentric"` (financial astrology, v6.0), and the
planetocentric frames `"Selenocentric"`, `"Mercurycentric"`, `"Venuscentric"`,
`"Marscentric"`, `"Jupitercentric"`, `"Saturncentric"`.

- **Topocentric** uses the observer's location; pass `altitude` (meters) for
  the full correction.
- **Center body dropped, with warning**: a body has no position as seen from
  itself, so Earth is dropped in geocentric/topocentric charts, the Sun in
  heliocentric, the center planet in planetocentric. An `active_points` list
  containing ONLY center bodies raises `KerykeionException` (an emptied list
  would silently invert into "no filter" = full chart). Barycentric has no
  single center body — nothing is dropped on that account.
- **Geocentric-only points dropped, with warning**, in every perspective
  except Apparent/True Geocentric and Topocentric: lunar nodes
  (`Mean_`/`True_North_Lunar_Node` + south), Lilith/apogee variants
  (`Mean_`/`True_`/`Interpolated_Lilith`, `Mean_`/`True_Priapus`,
  `Interpolated_Perigee`). Same raise-if-emptied rule.
- Arabic parts are skipped entirely in non-geocentric/topocentric
  perspectives (their formula mixes the geocentric Ascendant with planetary
  longitudes — blending frames would emit a phantom).
- Planetocentric positions come from `ephe.calc_pctr` (TT Julian Day);
  `ephemeris_session` accepts the names but sets no flag for them.

## Arabic parts (lots)

Four lots, none in `DEFAULT_ACTIVE_POINTS` — request them via `active_points`.
Day/night (sect) is decided by the Sun's geometric altitude above the horizon
(computed tropically/geocentrically regardless of the chart's zodiac or
perspective):

| Lot | Required points | Day formula | Night formula |
|---|---|---|---|
| `Pars_Fortunae` | Ascendant, Sun, Moon | ASC + Moon − Sun | ASC + Sun − Moon |
| `Pars_Spiritus` | Ascendant, Sun, Moon | ASC + Sun − Moon | ASC + Moon − Sun |
| `Pars_Amoris` | Ascendant, Venus, Sun | ASC + Venus − Sun (always) | — |
| `Pars_Fidei` | Ascendant, Jupiter, Saturn | ASC + Jupiter − Saturn (always) | — |

Each lot auto-computes any required base point missing from your
`active_points` (the base points are populated on the model, e.g.
`subject.sun`, though not appended to the final `subject.active_points`
list). Lots are never retrograde. On libephemeris a lot carries
`source="Derived"` with precision/coverage/reviewed inherited from its
formula's primaries (see `references/backends-and-provenance.md`).

```python
from kerykeion import AstrologicalSubjectFactory
lots = AstrologicalSubjectFactory.from_birth_data(
    name="Lots", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
    active_points=["Sun", "Moon", "Ascendant", "Pars_Fortunae", "Pars_Spiritus"])
pf = lots.pars_fortunae
print(pf.sign, round(pf.abs_pos, 2), pf.source)   # Gem 75.23 Derived
print(lots.pars_spiritus.house)
```

## `SIGN_CODES` (new in a84)

Ordered tuple of the 12 three-letter sign codes, Aries → Pisces:
`("Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu",
"Pis")` — the canonical order behind `sign_num` (0–11), typed as
`tuple[Sign, ...]`. Not re-exported at the package top level.

**Subpackage import:** `from kerykeion.schemas import SIGN_CODES`

Use it to map any point's `sign_num` back to its code
(`SIGN_CODES[point.sign_num] == point.sign` — demonstrated in the first
snippet above) or to build stable sign-indexed tables.
