# Zodiac, ayanamsa, houses, perspectives, lots

Sources: `kerykeion/schemas/kr_literals.py` (literals),
`kerykeion/astrological_subject_factory.py` (validation),
`kerykeion/settings/config_constants.py` (Arabic-part formulas).

## Tropical vs sidereal — coherence rules

`zodiac_type` is `"Tropical"` (default) or `"Sidereal"`.

- Sidereal requires a `sidereal_mode`. The factory auto-defaults it, but the
  model itself rejects a sidereal chart with `sidereal_mode=None` — be explicit.
- Passing `sidereal_mode` with a Tropical chart raises `KerykeionException`
  ("You can't set a sidereal mode with a Tropical zodiac type!").
- The applied offset is reported on `subject.ayanamsa_value` (degrees; tropical
  0 Aries minus sidereal 0 Aries). `None` for tropical charts.

### USER ayanamsa

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Custom Ayanamsa", 2000, 1, 1, 0, 0,
    lng=0.0, lat=51.5, tz_str="Etc/GMT", online=False,
    zodiac_type="Sidereal", sidereal_mode="USER",
    custom_ayanamsa_t0=2451545.0,     # reference epoch as Julian Day (J2000.0 here)
    custom_ayanamsa_ayan_t0=23.5,     # ayanamsa in degrees at that epoch
)
```

Both `custom_ayanamsa_t0` and `custom_ayanamsa_ayan_t0` are required for USER
mode (missing → error); the backend extrapolates other dates via its precession
model.

### Named `sidereal_mode` values

48 total. Common ones: `FAGAN_BRADLEY` (Western sidereal default), `LAHIRI`
(Indian government standard), `KRISHNAMURTI` (KP), `RAMAN`, `DELUCE`,
`TRUE_CITRA`, `TRUE_REVATI`, `GALCENT_0SAG`, `J2000`, `B1950`, `USER`.

Full family list (from `kr_literals.py`):

- **Indian / Vedic**: `LAHIRI`, `LAHIRI_1940`, `LAHIRI_ICRC`, `LAHIRI_VP285`,
  `KRISHNAMURTI`, `KRISHNAMURTI_VP291`, `RAMAN`, `USHASHASHI`, `JN_BHASIN`,
  `YUKTESHWAR`, `ARYABHATA`, `ARYABHATA_522`, `ARYABHATA_MSUN`, `SURYASIDDHANTA`,
  `SURYASIDDHANTA_MSUN`, `SS_CITRA`, `SS_REVATI`, `TRUE_CITRA`, `TRUE_MULA`,
  `TRUE_PUSHYA`, `TRUE_REVATI`, `TRUE_SHEORAN`
- **Western sidereal**: `FAGAN_BRADLEY`, `DELUCE`, `DJWHAL_KHUL`, `HIPPARCHOS`,
  `SASSANIAN`
- **Babylonian**: `BABYL_KUGLER1`, `BABYL_KUGLER2`, `BABYL_KUGLER3`,
  `BABYL_HUBER`, `BABYL_ETPSC`, `BABYL_BRITTON`
- **Galactic alignment**: `GALCENT_0SAG`, `GALCENT_COCHRANE`,
  `GALCENT_MULA_WILHELM`, `GALCENT_RGILBRAND`, `GALEQU_FIORENZA`,
  `GALEQU_IAU1958`, `GALEQU_MULA`, `GALEQU_TRUE`, `GALALIGN_MARDYKS`
- **Reference frames**: `J2000`, `J1900`, `B1950`
- **Astronomical**: `ALDEBARAN_15TAU`, `VALENS_MOON`
- **User-defined**: `USER`

### Nakshatra caveat

`calculate_nakshatra=True` computes Vedic nakshatra/pada/dasha-lord per point.
Nakshatras are defined on the **sidereal** zodiac. With a Tropical (or any
non-sidereal) chart the values are derived from tropical longitudes — offset by
the ayanamsa (~24°, roughly two nakshatras) — and a warning is logged. Use
`zodiac_type="Sidereal"` for astronomically meaningful nakshatras.

## House systems

`houses_system_identifier` is a single-character code from the
`HousesSystemIdentifier` literal:

| Code | System | | Code | System |
|---|---|---|---|---|
| `A` | Equal | | `O` | Porphyry |
| `B` | Alcabitius | | `P` | Placidus (default) |
| `C` | Campanus | | `Q` | Pullen SR |
| `D` | Equal (MC) | | `R` | Regiomontanus |
| `F` | Carter poli-equ. | | `S` | Sripati |
| `H` | Horizon / azimuth | | `T` | Polich/Page |
| `I` | Sunshine | | `U` | Krusinski-Pisa-Goelzer |
| `i` | Sunshine / alt. | | `V` | Equal / Vehlow |
| `K` | Koch | | `W` | Whole Sign |
| `L` | Pullen SD | | `X` | Axial rotation / Meridian |
| `M` | Morinus | | `Y` | APC houses |
| `N` | Equal / 1=Aries | | | |

Read cusps via `subject.first_house` … `subject.twelfth_house` (always present),
and the derived axes via `subject.ascendant`, `subject.medium_coeli`,
`subject.descendant`, `subject.imum_coeli`. `subject.houses_system_name` gives
the human-readable name.

### Polar-latitude fallback

Quadrant systems (Placidus `P`, Koch `K`) are mathematically undefined inside
the polar circle (|lat| beyond ~66.56°). Kerykeion computes cusps at the real
latitude and, only when the backend reports the system is undefined there,
retries once clamped to the ±66° limit **and logs a WARNING** naming the system.
Planetary positions and the persisted latitude keep the real value — only the
cusps/angles are clamped. Systems defined at every latitude (Whole Sign `W`,
Equal `A`, Porphyry `O`, Morinus `M`, Meridian `X`, …) always use the real
latitude. Prefer `W`/`A`/`O` for polar charts.

## Perspectives

`perspective_type` from the `PerspectiveType` literal: `"Apparent Geocentric"`
(default), `"True Geocentric"`, `"Heliocentric"`, `"Topocentric"`,
`"Barycentric"` (financial astrology), and the planetocentric frames
`"Selenocentric"`, `"Mercurycentric"`, `"Venuscentric"`, `"Marscentric"`,
`"Jupitercentric"`, `"Saturncentric"`.

- **Topocentric** uses the observer's location; pass `altitude` (meters) for the
  full correction.
- The center body of a perspective has no position from itself and is dropped
  from `active_points` (Earth in geocentric/topocentric, Sun in heliocentric,
  the center planet in a planetocentric chart), with a warning.
- Geocentric-only points (lunar nodes, Lilith/apogee variants) are dropped in
  non-geocentric/topocentric perspectives, with a warning.

## Arabic parts (lots)

Four lots: `Pars_Fortunae`, `Pars_Spiritus`, `Pars_Amoris`, `Pars_Fidei`. They
are not in `DEFAULT_ACTIVE_POINTS` — add them to `active_points`:

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Lots", 1990, 7, 15, 10, 30,
    lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
    active_points=["Sun", "Moon", "Ascendant", "Pars_Fortunae", "Pars_Spiritus"],
)
subject.pars_fortunae.abs_pos
```

Each lot auto-activates the base points its day/night formula needs (Sun, Moon,
Ascendant) on demand, so you don't have to list them yourself — but listing them
is harmless. On the libephemeris backend a lot is labelled `source="Derived"`
with precision/coverage/reviewed inherited from the ephemeris-backed points in
its formula (see the provenance section in SKILL.md). Relocated charts preserve
this inherited lot provenance.
