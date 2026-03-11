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

Kerykeion is built on [Swiss Ephemeris](https://www.astro.com/swisseph/), which offers
far more computational power than the library currently exposes. Much of this roadmap
is about unlocking capabilities that Swiss Ephemeris already provides but Kerykeion
does not yet surface.

---

## Completed

-   [x] **Discepolo's Score in Synastry** — `RelationshipScoreFactory` with full Ciro Discepolo scoring, destiny sign evaluation, aspect breakdown, 6-tier descriptions. Shipped in v5.0.0, score breakdown added in v5.6.0.
-   [x] **Unit tests for polar circle edge cases** — Dedicated tests, parametrized fixtures, expected data for arctic/antarctic subjects across all house systems and sidereal modes.
-   [x] **`get_translations` function for multiple languages** — Multi-language support (EN, FR, PT, IT, CN, ES, RU, TR, DE, HI) with fallback logic, nested key access, and custom dictionary override.

---

## v5.12 — Enrich Existing Calculations

🟥 High — These changes make existing data richer without changing the public API. Users write the same code as before but get more information in the models they already use.

-   [ ] **House cusp speeds** — Populate the `speed` field (degrees/day) on house cusp points. The field already exists on `KerykeionPointModel` but is currently only populated for planets, not houses. House cusp velocities are useful for primary directions, secondary progressions, and for understanding how quickly a transiting planet crosses a house boundary.

-   [ ] **Expanded fixed stars (2 → 17)** — Add 15 traditional fixed stars to the calculation pipeline, plus a `magnitude` field for apparent visual brightness:

    | Star | Mag. | Tradition |
    |------|------|-----------|
    | Sirius | −1.46 | Brilliance, fame |
    | Canopus | −0.74 | Navigation, pathfinding |
    | Arcturus | −0.05 | Prosperity, guard |
    | Capella | +0.08 | Civic honor, curiosity |
    | Rigel | +0.13 | Teaching, ambition |
    | Procyon | +0.34 | Quick success, rash action |
    | Betelgeuse | +0.42 | Military honor, fortune |
    | Altair | +0.77 | Boldness, ambition |
    | Aldebaran | +0.86 | Royal Star — integrity |
    | Antares | +0.96 | Royal Star — courage |
    | Pollux | +1.14 | Spirited, subtle |
    | Fomalhaut | +1.16 | Royal Star — idealism |
    | Deneb | +1.25 | Ingenuity, talent |
    | Achernar | +0.46 | Royal honors |
    | Algol | +2.12 | Intensity, misfortune |

    The four "Royal Stars of Persia" (Aldebaran, Regulus, Antares, Fomalhaut) and Algol are among the most significant points in any chart. Currently only Regulus and Spica are supported.

-   [ ] **Expanded sidereal modes (20 → 48 + custom)** — Add all remaining ayanamsa supported by Swiss Ephemeris:

    | Category | Modes |
    |----------|-------|
    | Aryabhata school | `ARYABHATA`, `ARYABHATA_522`, `ARYABHATA_MSUN` |
    | Galactic Center | `GALCENT_0SAG`, `GALCENT_COCHRANE`, `GALCENT_MULA_WILHELM`, `GALCENT_RGILBRAND` |
    | Galactic Equator | `GALEQU_FIORENZA`, `GALEQU_IAU1958`, `GALEQU_MULA`, `GALEQU_TRUE` |
    | True star-based | `TRUE_CITRA`, `TRUE_MULA`, `TRUE_PUSHYA`, `TRUE_REVATI`, `TRUE_SHEORAN` |
    | Suryasiddhanta | `SURYASIDDHANTA`, `SURYASIDDHANTA_MSUN`, `SS_CITRA`, `SS_REVATI` |
    | Lahiri variants | `LAHIRI_1940`, `LAHIRI_ICRC`, `LAHIRI_VP285` |
    | Other | `BABYL_BRITTON`, `GALALIGN_MARDYKS`, `KRISHNAMURTI_VP291`, `VALENS_MOON` |
    | User-defined | `USER` — provide a reference epoch and ayanamsa value |

-   [ ] **Ayanamsa value exposure** — Expose the numeric ayanamsa offset (in degrees) in the subject model. Currently only the ayanamsa name is stored. Every sidereal astrologer needs this for verification and cross-system comparison.

---

## v5.13 — Vedic & Traditional Enrichment

🟧 Medium — Opt-in via configuration flags, zero overhead for users who don't need them.

-   [ ] **Nakshatra support (Vedic lunar mansions)** — For every astrological point, calculate the Nakshatra (1 of 27, each 13°20'), Pada (1–4, each 3°20'), and Vimsottari Dasha lord. Foundation of Vedic Jyotish: Dasha timing, Ashtakoot compatibility, and finer characterization than the 12 signs alone. No major Python astrology library currently calculates nakshatras natively.

    New fields on `KerykeionPointModel`:
    - `nakshatra: Optional[str]` — e.g., "Rohini"
    - `nakshatra_number: Optional[int]` — 1–27
    - `nakshatra_pada: Optional[int]` — 1–4
    - `nakshatra_lord: Optional[str]` — e.g., "Moon"

-   [ ] **Essential dignities (Egyptian Terms & Chaldean Decans)** — For every planet, calculate essential dignity status per the Ptolemaic/medieval tradition: Domicile (+5), Exaltation (+4), Triplicity (+3), Term/Bounds (+2), Face/Decan (+1), Peregrine (0), Fall (−4), Detriment (−5). Backbone of horary, electional, and traditional natal astrology.

    New fields on `KerykeionPointModel`:
    - `decan_number: Optional[int]` — 1–3
    - `decan_ruler: Optional[str]`
    - `term_ruler: Optional[str]`
    - `essential_dignity: Optional[str]` — highest active dignity name
    - `dignity_score: Optional[int]` — −5 to +5

---

## v5.14 — Observational Astronomy

🟧 Medium — New standalone factory classes for astronomical phenomena outside the context of a birth chart.

-   [ ] **Planetary phenomena (`PlanetaryPhenomenaFactory`)** — For each planet: elongation from the Sun, illumination fraction, phase angle, apparent diameter, apparent magnitude, and morning/evening star status. Elongation is fundamental for understanding planetary visibility — a planet within ~15° of the Sun is traditionally "combust."

-   [ ] **Localized eclipses (`EclipseFactory`)** — Search for upcoming solar and lunar eclipses, optionally filtered by geographic location. For each eclipse: type (total, annular, partial, penumbral), magnitude, duration, contact times, Sun/Moon altitude, obscuration percentage. Currently Kerykeion only calculates the date of the next global eclipse without details and without considering local visibility.

---

## v5.15 — Advanced Astrology

🟧 Medium — New domain factories for specialized astrological techniques.

-   [ ] **Planetary nodes and apsides (`PlanetaryNodesFactory`)** — For any planet (not just the Moon): ascending node, descending node, perihelion, aphelion — in both mean and osculating modes. Central to evolutionary astrology (Jeffrey Wolf Green, Steven Forrest). Perihelion/aphelion relevant in heliocentric astrology and cosmobiology.

-   [ ] **Relocated charts (`RelocatedChartFactory`)** — Keep all planetary positions from a birth chart but recalculate houses and angles for a different geographic location. Widely-used predictive technique and computational prerequisite for Astro*Carto*Graphy (ACG) lines.

---

## Exploring

Features under consideration — design and scope may change significantly.

-   [ ] **Uranian / Hamburg School planets** — The 8 hypothetical trans-Neptunian points (Cupido, Hades, Zeus, Kronos, Apollon, Admetos, Vulkanus, Poseidon). Swiss Ephemeris IDs 40–47.
-   [ ] **Gauquelin sectors** — House system `"G"` with 36 sectors. Michel Gauquelin's statistical research on the "Mars Effect."
-   [ ] **Heliocentric returns and lunar node crossing** — Extend `PlanetaryReturnFactory` with heliocentric returns and exact node crossing moments.
-   [ ] **Heliacal risings and settings** — First/last day of visibility of planets and fixed stars. Oldest form of astronomical observation (Babylonian, ~1800 BCE). No Python library currently calculates this.
-   [ ] **Lunar occultations** — When the Moon passes in front of a planet or fixed star. Traditionally "powered-up conjunctions."
-   [ ] **Planetocentric perspective** — Positions as seen from another planet. Niche research feature, unique to Kerykeion.

---

## v6.0 — Foundation Cleanup

🟨 Low — Breaking changes, deprecation removal, and precision improvements. Only after 5.x features are stable. Will include a migration guide.

-   [ ] **Replace manual utilities with Swiss Ephemeris natives** — Swap hand-written Julian Day conversion, sidereal time, and degree decomposition with `swe.julday`, `swe.revjul`, `swe.sidtime`, `swe.split_deg`, `swe.deg_midp`. Numeric precision may shift by microseconds.
-   [ ] **Remove v4 backward compatibility layer** — Remove `backword.py` and the four deprecated class aliases (`AstrologicalSubject`, `KerykeionChartSVG`, `NatalAspects`, `SynastryAspects`). Deprecated since v5.0.
-   [ ] **Support BCE dates** — Negative years for historical charts using Swiss Ephemeris native capabilities and precise Delta T calculation (`swe.deltat_ex`).
-   [ ] **Ephemeris file range validation** — Validate at calculation time that the requested date falls within the range covered by the loaded ephemeris files, raising a clear error instead of producing cryptic results.


