# Backend Precision Comparison: swisseph vs libephemeris

Kerykeion supports two ephemeris backends that are **functionally equivalent**
and **100% API-compatible**. This document summarises the concrete numerical
and behavioural differences a user or contributor may encounter.

---

## At a glance

|                  | **swisseph**                             | **libephemeris**                    |
| ---------------- | ---------------------------------------- | ----------------------------------- |
| Language         | C bindings (`pyswisseph`)                | Pure Python                         |
| Ephemeris source | Swiss Ephemeris (Moshier / `.se1` files) | NASA JPL DE440 / DE441 via Skyfield |
| License          | AGPL-3.0                                 | AGPL-3.0                            |
| Install          | `pip install kerykeion[swiss]`           | Included by default                 |
| Date range       | Full (DE431 covers -13200 to +17191)     | Full (DE441 same range)             |
| Compilation      | Requires C compiler                      | None                                |

---

## Planetary longitude precision

Typical deltas measured across the full test matrix (11-25 subjects,
antiquity to 2650 CE):

| Body              | Typical delta           | Notes                                |
| ----------------- | ----------------------- | ------------------------------------ |
| Sun               | < 0.01 deg              |                                      |
| Moon              | < 0.02 deg              | Largest for fast-moving body         |
| Mercury - Neptune | < 0.01 deg              |                                      |
| Pluto             | < 0.02 deg              |                                      |
| True Node         | ~ 0.002 deg (~6 arcsec) | Different osculating-element methods |
| Chiron            | < 0.01 deg              |                                      |
| Mean Lilith       | < 0.01 deg              |                                      |

**For all practical astrological purposes the two backends are
indistinguishable**: differences stay well below 1 arcminute for major
planets and never cross zodiac-sign or house-cusp boundaries in any
tested scenario.

---

## House cusps

| Cusp                           | Typical delta |
| ------------------------------ | ------------- |
| Ascendant                      | < 0.02 deg    |
| Midheaven (MC)                 | < 0.02 deg    |
| Intermediate cusps (2-6, 8-12) | < 0.05 deg    |

All 23 supported house systems (Placidus, Koch, Whole Sign, Equal,
Porphyry, Regiomontanus, Campanus, etc.) behave identically on both
backends.

---

## Speeds and declinations

| Metric          | Typical delta  | Cause                                       |
| --------------- | -------------- | ------------------------------------------- |
| Planetary speed | < 0.01 deg/day | Analytical (swe) vs finite-difference (lib) |
| Declination     | < 0.01 deg     | Ephemeris source difference                 |

Retrograde status (`speed < 0`) always agrees between backends.

---

## Sidereal modes

All 47 named ayanamsa modes plus the custom `USER` mode (48 total) are
supported on both backends. The ayanamsa offset is computed via the same
`swe.get_ayanamsa_ex_ut()` API, so sidereal positions show the same
sub-0.02 deg deltas as tropical positions.

---

## Perspective types

| Perspective                   | swisseph | libephemeris |
| ----------------------------- | -------- | ------------ |
| Apparent Geocentric (default) | Full     | Full         |
| True Geocentric               | Full     | Full         |
| Heliocentric                  | Full     | Full         |
| Topocentric                   | Full     | Full         |
| Barycentric                   | Full     | Full         |

**Barycentric note**: libephemeris uses the JPL DE440 native barycentric
reference frame, which is the authoritative source for solar-system
barycenter coordinates. Swiss Ephemeris derives barycentric positions
from its internal heliocentric frame via a Sun-barycenter offset. The
two approaches produce noticeably different Sun positions (~24 deg in
tests) because the JPL definition of the solar-system barycenter
accounts for the full N-body gravitational dynamics, while Swiss
Ephemeris uses a simplified model. **For barycentric work,
libephemeris is the more accurate backend** as it relies directly on
JPL's numerical integration.

---

## Uranian / hypothetical planets

The 8 Hamburg School hypothetical planets (Cupido, Hades, Zeus, Kronos,
Apollon, Admetos, Vulkanus, Poseidon) are supported on both backends
via Swiss Ephemeris IDs 40-47.

Positions agree within ~1 deg. The larger tolerance is due to
differences in how each backend evaluates the hypothetical-planet
polynomial series.

---

## Historical dates and edge cases

Both backends are tested across three ephemeris tiers:

| Tier             | Range           | Subjects |
| ---------------- | --------------- | -------- |
| Base (DE440s)    | 1849 - 2150     | 11       |
| Medium (DE440)   | 1550 - 2650     | 16       |
| Extended (DE441) | -13200 - +17191 | 25       |

For very old dates (e.g. 100 AD, 400 AD) libephemeris may return `None`
for bodies whose ephemeris coverage doesn't extend that far (e.g. some
TNOs, Juno, Vesta). swisseph typically falls back to the Moshier
analytical ephemeris in such cases and still returns a value.

---

## Performance

| Backend      | Mode               | Relative speed            |
| ------------ | ------------------ | ------------------------- |
| swisseph     | `.se1` files       | Fastest (C library)       |
| libephemeris | `.leb` precomputed | ~14x faster than Skyfield |
| libephemeris | Skyfield / DE440   | Baseline                  |
| libephemeris | Horizons API       | Network-dependent         |

The libephemeris mode is controlled by the `KERYKEION_LEB_MODE` env var
(`leb` | `auto` | `skyfield` | `horizons`; default `leb`).

---

## Edge-case behavioural differences

These differences do not affect chart interpretation but are observable
in automated test comparisons:

| Area | Behaviour |
| ---- | --------- |
| **Aspect movement** | Very slow planet pairs (e.g. Pluto-Chiron) may be classified differently ("Static" vs "Applying") because tiny speed differences cross the threshold. |
| **Aspect list at orb boundaries** | A few aspects near the orb limit may appear in one backend and not the other, producing slightly different aspect tables. |
| **SVG chart layout** | Small position differences cause different overlap-resolution paths in the chart renderer, producing structurally different (but visually equivalent) SVG output. |
| **Minor bodies on ancient dates** | For dates before ~1550 CE, libephemeris may return `None` for TNOs (Eris, Sedna, etc.), Juno, and Vesta because the underlying SPK segments do not cover that range. swisseph falls back to its built-in Moshier analytical ephemeris and still returns a value. |
| **Uranian hypothetical planets** | Positions agree within ~1 deg. The larger tolerance reflects differences in how each backend evaluates the Hamburg School polynomial series for bodies 40-47. |

---

## Test suite tolerances

The cross-backend test tolerances used in the project reflect the
measured deltas:

| Context                   | swisseph tolerance | Cross-backend tolerance        |
| ------------------------- | ------------------ | ------------------------------ |
| Planet position / abs_pos | 0.01 deg           | 0.15 deg                       |
| Planet speed              | 0.0001 deg/day     | 0.05 deg/day                   |
| Declination               | 0.01 deg           | 0.15 deg                       |
| House cusps               | 0.01 deg           | 0.15 deg                       |
| SVG chart comparison      | exact (1e-10)      | 0.5 deg + structural tolerance |
| Report golden files       | exact string match | 10.0 numeric tolerance         |

---

## Summary

For natal chart interpretation, transit analysis, synastry, and all
standard astrological work, **both backends produce equivalent results**.
Choose based on your constraints:

- **libephemeris** (default): no C compiler, AGPL-3.0, pure Python, more accurate barycentric
- **swisseph**: fastest option (C), GPL-2.0, broader minor-body coverage on ancient dates
