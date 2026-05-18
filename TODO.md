# TODO – Development Roadmap

**Legend:**

-   `[ ]` – To do
-   `[>]` – In progress
-   `[x]` – Completed
-   `[KO]` – Removed / No longer needed

**Priority levels:**

-   🟥 High
-   🟧 Medium
-   🟨 Low

**Guiding principles:**

- Every minor release (5.x) is fully backward compatible — no breaking changes.
- All new fields on existing models are `Optional` with default `None`.
- All new modules are additive — existing imports and workflows continue to work unchanged.
- Breaking changes are collected and shipped together in a single major release (6.0).

Kerykeion uses [libephemeris](https://github.com/g-battaglia/libephemeris) as its default backend
(with optional Swiss Ephemeris support). Much of this roadmap has been completed in v6.

---

## Completed

-   [x] **Discepolo's Score in Synastry** — `RelationshipScoreFactory` with full Ciro Discepolo scoring, destiny sign evaluation, aspect breakdown, 6-tier descriptions. Shipped in v5.0.0, score breakdown added in v5.6.0.
-   [x] **Unit tests for polar circle edge cases** — Dedicated tests, parametrized fixtures, expected data for arctic/antarctic subjects across all house systems and sidereal modes.
-   [x] **`get_translations` function for multiple languages** — Multi-language support (EN, FR, PT, IT, CN, ES, RU, TR, DE, HI) with fallback logic, nested key access, and custom dictionary override.

---

## v5.12 — Enrich Existing Calculations

🟥 High — These changes make existing data richer without changing the public API. Users write the same code as before but get more information in the models they already use.

-   [x] **House cusp speeds** — Populate the `speed` field (degrees/day) on house cusp points. Replaced `swe.houses_ex()` with `swe.houses_ex2()` so all 12 cusps and the 4 angular points (ASC, MC, DSC, IC) now carry a real `speed` value.

-   [x] **Expanded fixed stars (2 → 23)** — Added 21 traditional fixed stars to the calculation pipeline, plus a `magnitude` field for apparent visual brightness (includes all 15 Behenian stars):

    | Star | Mag. | Tradition |
    |------|------|-----------|
    | Sirius | −1.46 | Brilliance, fame |
    | Canopus | −0.74 | Navigation, pathfinding |
    | Arcturus | −0.05 | Prosperity, guard |
    | Vega | +0.03 | Behenian — charisma, magic |
    | Capella | +0.08 | Civic honor, curiosity |
    | Rigel | +0.13 | Teaching, ambition |
    | Procyon | +0.34 | Quick success, rash action |
    | Betelgeuse | +0.42 | Military honor, fortune |
    | Achernar | +0.46 | Royal honors |
    | Altair | +0.76 | Boldness, ambition |
    | Aldebaran | +0.87 | Royal Star — integrity |
    | Antares | +1.06 | Royal Star — courage |
    | Pollux | +1.14 | Spirited, subtle |
    | Fomalhaut | +1.16 | Royal Star — idealism |
    | Deneb | +1.25 | Ingenuity, talent |
    | Algol | +2.12 | Intensity, misfortune |
    | Alphecca | +2.22 | Behenian — artistry, honor |
    | Deneb Algedi | +2.83 | Behenian — justice, law |
    | Alcyone | +2.87 | Behenian — mysticism, vision |
    | Algorab | +2.94 | Behenian — scavenging, cunning |
    | Alkaid | +1.86 | Behenian — mourning, leadership |

    The four "Royal Stars of Persia" (Aldebaran, Regulus, Antares, Fomalhaut) and Algol are among the most significant points in any chart. All 23 fixed stars are now supported in v5.12.

-   [x] **Expanded sidereal modes (20 → 48 + custom)** — Added all remaining ayanamsa systems supported by Swiss Ephemeris (47 named modes + USER for custom ayanamsa definitions, 48 total). Includes Aryabhata, Suryasiddhanta, True star-based, Galactic Center/Equator, Lahiri variants, Babylonian Britton, and Valens Moon.

-   [x] **Ayanamsa value exposure** — Added `ayanamsa_value` field to `AstrologicalBaseModel`. For sidereal charts, contains the computed angular offset (in degrees) between tropical and sidereal 0° Aries. `None` for tropical charts. Calculated via `swe.get_ayanamsa_ex_ut()`.

---

## v5.13 — Vedic & Traditional Enrichment

🟧 Medium — Opt-in via configuration flags, zero overhead for users who don't need them.

-   [x] **Nakshatra support (Vedic lunar mansions)** — Implemented via `calculate_nakshatra=True` on `AstrologicalSubjectFactory`. Calculates Nakshatra, Pada, and Dasha lord for every point.

-   [x] **Essential dignities (Egyptian Terms & Chaldean Decans)** — Implemented via `calculate_dignities=True` on `AstrologicalSubjectFactory`. Calculates dignity scores per the Ptolemaic/medieval tradition.

---

## v5.14 — Observational Astronomy

🟧 Medium — New standalone factory classes for astronomical phenomena outside the context of a birth chart.

-   [x] **Planetary phenomena (`PlanetaryPhenomenaFactory`)** — Implemented. Calculates elongation, illumination, phase angle, apparent diameter/magnitude, and morning/evening star status.

-   [x] **Localized eclipses (`EclipseFactory`)** — Implemented. Searches for solar and lunar eclipses with local and global modes, type, magnitude, and contact times.

---

## v5.15 — Advanced Astrology

🟧 Medium — New domain factories for specialized astrological techniques.

-   [x] **Planetary nodes and apsides (`PlanetaryNodesFactory`)** — Implemented. Calculates ascending/descending nodes and perihelion/aphelion in mean and osculating modes.

-   [x] **Relocated charts (`RelocatedChartFactory`)** — Implemented. Recalculates houses and angles for a different geographic location while preserving planetary positions.

---

## Exploring

Features under consideration — design and scope may change significantly.

-   [x] **Uranian / Hamburg School planets** — Implemented. All 8 hypothetical trans-Neptunian points available via `active_points`.
-   [x] **Gauquelin sectors** — Implemented via `calculate_gauquelin=True`. 36-sector system.
-   [x] **Heliocentric returns and lunar node crossing** — Implemented in `PlanetaryReturnFactory`.
-   [x] **Heliacal risings and settings** — Implemented via `HeliacalFactory`.
-   [x] **Lunar occultations** — Implemented via `OccultationFactory`.
-   [x] **Planetocentric perspective** — Implemented. Selenocentric, Mercurycentric, Venuscentric, Marscentric, Jupitercentric, Saturncentric perspectives available.

---

## v6.0 — Foundation Cleanup

🟨 Low — Breaking changes, deprecation removal, and precision improvements. Only after 5.x features are stable. Will include a migration guide.

-   [ ] **Replace manual utilities with Swiss Ephemeris natives** — Swap hand-written Julian Day conversion, sidereal time, and degree decomposition with ephemeris backend natives. Numeric precision may shift by microseconds.
-   [x] **Remove v4 backward compatibility layer** — Done. `backword.py` and the four deprecated class aliases removed.
-   [x] **Support BCE dates** — Implemented. Negative years for historical charts.
-   [ ] **Ephemeris file range validation** — Validate at calculation time that the requested date falls within the range covered by the loaded ephemeris files, raising a clear error instead of producing cryptic results.


