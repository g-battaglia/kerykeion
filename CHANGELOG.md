# Changelog

## 6.0.0a4

_2026-03-31_

**Remove `source` field from `KerykeionPointModel`.**

The `source` field added in 6.0.0a3 (`"ephemeris"`, `"derived"`, `"formula"`) has been removed. It provided redundant information -- the provenance of every point is already obvious from its name and type (e.g. Descendant is always derived from ASC+180, Pars Fortunae is always a formula). The field added noise to every API response without aiding actual debugging.

Ephemeris backend tracing (LEB vs Skyfield vs SPK vs Horizons) -- which is the genuinely useful debug information -- is handled at the API layer via an opt-in `X-Debug-Ephemeris` header that captures `libephemeris` log output. This keeps kerykeion clean and the debug infrastructure where it belongs.

### Breaking Changes

- **Removed `source` field** from `KerykeionPointModel`. Consumers that read `.source` on points will get an `AttributeError`. Since this field was only introduced in 6.0.0a3 (never in a stable release), the impact is minimal.
- **Removed `source` parameter** from `get_kerykeion_point_from_degree()` in `utilities.py`.

## 6.0.0a3

_2026-03-31_

**Ephemeris delegation refactor -- delegate derived/analytical points to backends, new celestial points.**

This release refactors how kerykeion computes derived and analytical astrological points, following the principle: _"Astronomical calculations belong to the backend. Astrological logic belongs to Kerykeion."_

### New Celestial Points

- **Interpolated Perigee** (`SE_INTP_PERG = 22`) -- the interpolated lunar perigee (closest approach), computed natively by the ephemeris backend. Not the same as `Lilith + 180` -- the actual perigee can differ by ~25° from the geometric opposite of the apogee.

- **White Moon / Selena** (`SE_WHITE_MOON = 56`) -- computed natively when the backend supports it; falls back to `Mean Lilith + 180` on backends that don't (e.g. swisseph). The fallback computes Mean Lilith locally without leaking it into the public model.

### Breaking Changes

- **Interpolated Lilith now uses `SE_INTP_APOG = 21`** instead of the previous naive `circular_mean(Mean, True)` formula. The new value is the astronomically correct interpolated apogee computed via the ELP2000-82B perturbation series (~50 terms). This is numerically different from the old formula and is no longer constrained to lie between Mean and True Lilith.

### `OPPOSITE_PAIRS` Consolidation

All `+180°` derived points are now declared in a single `OPPOSITE_PAIRS` dictionary and computed by one `_calculate_opposite_points()` method. This replaces ~7 separate inline blocks scattered across `_calculate_houses()` and `_calculate_planets()`.

Consolidated pairs: Descendant (from ASC), Imum Coeli (from MC), Anti-Vertex (from Vertex), Mean/True South Lunar Node (from North Nodes), Mean/True Priapus (from Mean/True Lilith).

### Bug Fixes

- **`SE_JUL_CAL` → `JUL_CAL`** -- fixed cross-backend compatibility for BCE date support. `swisseph` exposes `JUL_CAL`, `libephemeris` exposes both. Using `JUL_CAL` for compatibility. This fixes all 38 `test_bce_dates.py` failures on the swisseph backend.

- **Anti-Vertex with Vertex not requested** -- Vertex is now always computed and stored internally when either `Vertex` or `Anti_Vertex` is in `active_points`, so the opposite-pair derivation always has its primary available.

- **Descendant / Imum Coeli with ASC/MC not requested** -- ASC and MC are now always stored in `data` (they are already computed at zero cost by `houses_ex2`), so `active_points=["Descendant"]` or `["Imum_Coeli"]` works correctly. Only added to `active_points` output when explicitly requested.

- **White Moon fallback on swisseph** -- the fallback path now computes Mean Lilith locally via `swe.calc_ut(jd, 12, flags)` without writing it to the public model, preventing an unrequested `mean_lilith` field from leaking into the subject.

### Internal Changes

- Added `Interpolated_Perigee` and `White_Moon` to: `AstrologicalPoint` literal type, `AstrologicalBaseModel`, `KerykeionLanguageCelestialPointModel`, `DEFAULT_CELESTIAL_POINTS_SETTINGS`, `ALL_ACTIVE_POINTS`, and all 10 language translation dictionaries.
- Updated `_POINT_NUMBER_MAP` in `utilities.py` with correct body IDs for `True_Lilith` (13), `Interpolated_Lilith` (21), `Interpolated_Perigee` (22), `White_Moon` (56).
- Regenerated all modern SVG chart baselines to reflect new points.
- Updated `test_lilith_variants.py` to reflect the new `SE_INTP_APOG` semantics.

## 6.0.0a2

_2026-03-30_

**BCE date support -- historical charts for dates before 1 AD.**

### BCE Date Support

- **Dates before 1 AD are now fully supported.** Pass negative years (astronomical year numbering: 0 = 1 BCE, -1 = 2 BCE, etc.) to `AstrologicalSubjectFactory.from_birth_data()` and all chart types work: natal, transit, synastry, with any house system or sidereal mode.

- **How it works:** For `year < 1`, Python's `datetime` is bypassed entirely. Julian Day is computed directly via `swe.julday()` with the Julian calendar (`SE_JUL_CAL`). Timezone offset uses Local Mean Time (LMT) based on longitude -- historically correct for dates predating standardized time zones.

- **Both backends supported:** Works identically with libephemeris and swisseph. Julian Day agreement < 1e-6, Sun position agreement < 0.1°.

- **Chart rendering:** SVG charts (natal, transit, synastry) render correctly for BCE dates. ISO 8601 extended year format (e.g. `-0500-03-21T12:00:00+01:35`) used throughout.

- **New utility functions:** `format_ancient_iso()`, `format_iso_display()`, `extract_year_from_iso()` in `kerykeion.utilities` for BCE-safe date formatting.

- **68 new tests** covering subject creation, Julian Day baselines, LMT offset, ISO formatting, day of week, planetary positions, SVG baselines (natal/transit/synastry), house systems, sidereal modes, backend comparison, report generation, and modern date regression.

#### Example

```python
from kerykeion import AstrologicalSubjectFactory

# Spring equinox in Ancient Greece, 501 BCE
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Ancient Greece",
    year=-500, month=3, day=21, hour=12, minute=0,
    lat=37.9838, lng=23.7275, tz_str="Europe/Athens",
    online=False,
)
print(subject.sun.sign)  # Pis
print(subject.julian_day)  # 1538512.934...
```

## 6.0.0a1

_2026-03-29_

**First alpha release of Kerykeion v6 -- major feature release with 22 new astrological features, 8 new standalone factories, and 11 new celestial points.**

All v6 features are **opt-in** -- existing code works unchanged with no breaking changes to the public API.

### New Standalone Factories

- **PrimaryDirectionsFactory** -- Placidus semi-arc primary directions with Ptolemy (1 deg = 1 year) and Naibod (0.9856 deg/year) rate keys. Computes speculum with equatorial coordinates, meridian distance, and semi-arc data.

- **AstroCartographyFactory** -- Planetary line mapping (ACG). Computes MC, IC, ASC, DSC lines globally with configurable step size, geographic tolerance, and latitude range.

- **EclipseFactory** -- Localized and global solar/lunar eclipse search. Returns eclipse type (total, annular, partial, penumbral), magnitude, obscuration, and sun altitude for visibility.

- **PlanetaryPhenomenaFactory** -- Observational phenomena: phase angle, illumination, elongation, apparent diameter/magnitude, and morning/evening star detection for Mercury and Venus.

- **PlanetaryNodesFactory** -- Ascending/descending nodes and perihelion/aphelion for all planets. Supports mean and osculating (instantaneous) calculation methods.

- **HeliacalFactory** -- Heliacal rising, setting, evening first, and morning last events. Customizable atmospheric conditions (pressure, temperature, humidity, extinction) and observer parameters.

- **OccultationFactory** -- Lunar occultation search (global and location-specific). Returns occultation type (total, partial, annular), maximum Julian Day, and datestamp.

- **FixedStarDiscoveryFactory** -- Auto-discover fixed stars near natal planets beyond the default 23. Configurable orb tolerance, accesses the full Swiss Ephemeris star catalog.

### New Chart Features

- **Davison Composite Chart** -- New composite method that calculates the midpoint in both time and space (vs. existing zodiac-midpoint method). Available via `CompositeSubjectFactory.get_davison_composite_subject_model()`.

- **Relocated Charts** (`RelocatedChartFactory`) -- Recalculate houses and angles for a different geographic location while keeping all planetary positions unchanged.

### New Celestial Points

- **8 Uranian / Hamburg School hypothetical planets:** Cupido, Hades, Zeus, Kronos, Apollon, Admetos, Vulkanus, Poseidon. Full SVG symbols, CSS color variables (all 6 themes), and chart default settings included.

- **3 Lilith/Priapus variants:** Interpolated Lilith, Mean Priapus, and True Priapus (anti-Lilith points, opposite of Mean/True Lilith).

### New Calculation Options

All activated via `AstrologicalSubjectFactory.from_birth_data()` keyword arguments:

- **`calculate_dignities=True`** -- Ptolemaic essential dignities. New fields: `decan_number`, `decan_ruler`, `term_ruler`, `essential_dignity` ("Domicile"/"Exaltation"/"Detriment"/"Fall"/"Peregrine"), `dignity_score` (-5 to +5).

- **`calculate_nakshatra=True`** -- Vedic lunar mansions (27 Nakshatras). New fields: `nakshatra`, `nakshatra_number` (1-27), `nakshatra_pada` (1-4), `nakshatra_lord` (Vimsottari Dasha ruler).

- **`calculate_gauquelin=True`** -- Gauquelin 36-sector system for statistical astrology. New field: `gauquelin_sector` (1.0-36.99). Full SVG rendering with sector lines replacing house cusps in both classic and modern chart styles.

- **`calculate_local_space=True`** -- Horizon coordinates. New fields: `azimuth` (compass bearing 0-360) and `altitude_above_horizon` (degrees above/below horizon).

- **`calculate_nutation=True`** -- Earth's nutation model. New model-level field: `nutation` (`NutationObliquityModel` with `true_obliquity`, `mean_obliquity`, `nutation_longitude`, `nutation_obliquity`).

- **`active_fixed_stars=["Sirius", ...]`** -- Dynamically add fixed stars beyond the default 23-star catalog.

### New Perspective Types

- **Barycentric** perspective (solar system barycenter as origin). Added to the existing set: Apparent Geocentric, True Geocentric, Heliocentric, Topocentric, and 7 planetocentric variants (Seleno-, Mercury-, Venus-, Mars-, Jupiter-, Saturn-centric).

### New Aspect Types

- **Declination aspects:** `parallel` (same declination) and `contra_parallel` (opposite declination).

### Enhanced Returns & Transits

- **Heliocentric returns** and **Lunar Node Crossing** returns via `PlanetaryReturnFactory`.
- **Transit exactness refinement** via bisection: `refine_exact_moments=True` with configurable `refinement_iterations` (default 12 = ~0.244s precision).

### New Model Fields on KerykeionPointModel

- `is_out_of_bounds: Optional[bool]` -- True when declination exceeds the Sun's maximum (~23.44°), indicating a planet operating outside normal boundaries. Always populated when declination is available.
- All dignity, nakshatra, gauquelin, local space, and azimuth fields listed above.

### Bug Fixes

- **Modern style Gauquelin rendering:** Fixed three bugs that broke the modern chart wheel when Gauquelin sectors were active:
  - House division lines (12 thick lines crossing the planet ring) were still drawn instead of 36 sector lines. Now correctly draws Gauquelin sector divisions through the planet ring.
  - The inner house ring used wrong Y coordinates and inconsistent rotation sign, causing sector markers to render as a misplaced bar.
  - Added new `_draw_gauquelin_division_lines()` function for sector lines in the planet ring.

- **Multi-column grid headers:** When many active points cause the Gauquelin unified grid to split into multiple columns, the header row (Planet, Longitude, Decl., Sector) now appears on all columns instead of only the first.

- **SVG height for many active points:** The triangular aspect grid grows by 14px per point but the SVG height was only growing by 8px per point. With 55+ active points, the aspect grid was clipped at the top. Height calculation now accounts for the aspect grid's actual growth rate.

- **Aspect grid / planet grid overlap:** With multi-column Gauquelin layouts, the planet grid extends leftward and could overlap the aspect grid. The aspect grid X position now shifts rightward together with the planet grid.

- **Gauquelin grid centering:** The unified Gauquelin grid (220px wide) now shifts 30px left for better visual symmetry.

### Ephemeris Backend Abstraction

- **Dual-backend architecture**: Kerykeion now supports two interchangeable ephemeris backends -- **libephemeris** (pure Python, AGPL-3.0, default) and **swisseph** (C bindings, GPL-2.0, optional). Both are 100% API-compatible; all features work identically on both.
- **libephemeris** uses NASA JPL DE440/DE441 ephemeris data via Skyfield. No C compiler required. Installed by default with `pip install kerykeion`.
- **swisseph** remains available via `pip install kerykeion[swiss]` for users who need maximum speed or have existing GPL workflows.
- Backend selection: auto-detected (libephemeris preferred) or explicit via `KERYKEION_BACKEND=swisseph|libephemeris` environment variable.
- **Barycentric precision**: libephemeris uses JPL DE440 native barycentric coordinates (N-body gravitational dynamics), making it the more accurate backend for barycentric work.
- Planetary longitude agreement < 0.02 deg across backends; house cusps < 0.05 deg; retrograde status always identical. See `site/docs/backend_precision_comparison.md` for full details.
- Three test suites: `poe test:swe` (swisseph, 8659 tests), `poe test:lib` (libephemeris, 2460+ tests), `poe test:compare` (cross-backend equivalence).

### Internal / Deprecations

- Removed v4 backward compatibility layer (`kr_types` module excluded from coverage, marked for deprecation).
- Removed stale v6 planning docs (all features implemented and tested).
- `SubscriptableBaseModel` added for dictionary-style field access on Pydantic models.
- 8700+ tests passing across both backends, including 50+ dedicated v6 feature tests and factory coverage at 98-100%.

## 5.12.0

_2026-03-18_

**New Features:**

- **Retrograde indicator on classic wheel (v5.12.7):** The ℞ (retrograde) symbol is now rendered next to retrograde planet glyphs directly on the classic style chart wheel. Previously, retrograde status was only visible in the sidebar grid and in modern style charts. The symbol appears at the bottom-right foot of each retrograde planet glyph on both inner-ring (natal) and outer-ring (transit/synastry) planets. A `kr:retrograde="true"` attribute is also added to the planet group elements for programmatic consumers.

- **House cusp speeds (v5.12.1):** Replaced `swe.houses_ex()` with `swe.houses_ex2()` to expose cusp velocities. All 12 house cusps and the 4 angular points (ASC, MC, DSC, IC) now carry a `speed` field (degrees/day) representing the real rate of diurnal motion. Useful for primary directions and profection techniques.

- **Expanded fixed stars (v5.12.2):** Grew the fixed star catalogue from 2 to 23 stars. The 21 new stars are: Aldebaran, Antares, Sirius, Fomalhaut, Algol, Betelgeuse, Canopus, Procyon, Arcturus, Pollux, Deneb, Altair, Rigel, Achernar, Capella, Vega, Alcyone, Alphecca, Algorab, Deneb_Algedi, and Alkaid. The set now includes all 15 Behenian stars of the medieval/Hermetic tradition and the 4 Royal Stars of Persian/Hellenistic astrology (Regulus, Aldebaran, Antares, Fomalhaut). Each fixed star now also reports apparent visual magnitude via `swe.fixstar2_mag()` and equatorial declination.

- **Expanded sidereal modes (v5.12.3):** Grew supported ayanamsa systems from 20 to 47 named modes plus a `USER` mode for custom ayanamsa definitions (48 total). New mode families include additional Indian/Vedic variants (Aryabhata, Suryasiddhanta, True Citra/Pushya/Revati, Lahiri sub-variants), Babylonian systems (Britton), galactic alignment systems, and the Valens Moon ayanamsa. The `USER` mode accepts `custom_ayanamsa_t0` (reference epoch as Julian Day) and `custom_ayanamsa_ayan_t0` (ayanamsa offset in degrees at that epoch).

- **Ayanamsa value exposure (v5.12.4):** Added `ayanamsa_value` field to `AstrologicalBaseModel`. For sidereal charts, this contains the computed angular offset (in degrees) between tropical and sidereal 0 Aries at the chart's date/time. `None` for tropical charts. Calculated via `swe.get_ayanamsa_ex_ut()`.

- **SVG rendering for new stars:** Added SVG symbol definitions, CSS color variables (all 6 themes), chart default settings, and weighted point weights for all 21 new fixed stars. Each star has a unique icon representing its traditional astronomical/astrological character.

- **Right-panel aspect layout:** Charts with more than 24 active points now render the aspect list/grid to the right of the wheel instead of below it, preventing excessive vertical growth. Controlled by the internal `_RIGHT_PANEL_POINTS_THRESHOLD` constant.

- **Fixed star color contrast:** Darkened 7 fixed star colors in the classic theme (Sirius, Procyon, Canopus, Capella, Deneb, Altair, Pollux) for better visibility against white/light backgrounds.

- **`style` and `show_zodiac_background_ring` on constructor:** Promoted `style` and `show_zodiac_background_ring` from render-method-only arguments (v5.11) to `ChartDrawer.__init__()` keyword arguments. This allows setting a per-instance default that applies to all subsequent render calls, while still permitting per-render overrides via the `_UNSET` sentinel pattern.

**New Fields (all Optional, default None -- no breaking changes):**

- `KerykeionPointModel.speed` -- daily motion in degrees/day
- `KerykeionPointModel.declination` -- equatorial declination in degrees
- `KerykeionPointModel.magnitude` -- apparent visual magnitude (fixed stars only)
- `AstrologicalBaseModel.ayanamsa_value` -- ayanamsa offset in degrees (sidereal only)
- `AstrologicalBaseModel.aldebaran` through `.alkaid` -- 21 new fixed star fields
- `ChartConfiguration.custom_ayanamsa_t0` -- Julian Day reference epoch for USER mode
- `ChartConfiguration.custom_ayanamsa_ayan_t0` -- ayanamsa degrees at t0 for USER mode

**Documentation:**

- Comprehensive docstrings for all new/modified functions explaining Indian astrology concepts (ayanamsa, sidereal zodiac, precession) for Western astrology users
- `SiderealMode` literal now includes a full docstring with mode families, typical ayanamsa values, and USER mode usage
- `AstrologicalPoint` literal docstring corrected and expanded with fixed star categorization (Royal Stars, navigational stars)
- All factory methods (`from_birth_data`, `from_iso_utc_time`, `from_current_time`) document custom ayanamsa parameters
- `_calculate_houses` docstring documents `houses_ex2` switch and cusp speed semantics
- `_calculate_planets` fixed stars section updated for 23 stars with magnitude/declination
- `FIXED_STARS` constant annotated with star identifications and magnitudes
- `ALL_ACTIVE_POINTS` and `DEFAULT_ACTIVE_POINTS` organized with section comments

**Tests:**

- 266 dedicated v5.12 tests across 9 test classes covering house cusp speeds, expanded fixed stars, star magnitudes, star declinations, sidereal modes, USER-defined ayanamsa, ayanamsa value exposure, and guiding principles (no breaking changes)

## 5.11.0

_2026-03-18_

**New Features:**

- Added **modern chart style** — a concentric-ring layout alternative to the classic wheel. Pass `style="modern"` to `save_svg()`, `generate_svg_string()`, `save_wheel_only_svg_file()`, or `generate_wheel_only_svg_string()`. The modern layout renders 5 rings: cusp/zodiac signs, graduated ruler scale, planet data clusters, house numbers, and aspect lines with midpoint glyphs. Works with all six themes and all chart types (Natal, Synastry, Transit, Lunar/Solar Return, Composite).

- Added `show_zodiac_background_ring` parameter (modern style only) — when set to `False`, omits the colored zodiac wedges from the outer ring.

- Added `KerykeionChartStyle` literal type (`"classic"` | `"modern"`) to `kerykeion.schemas`.

- New drawing module `kerykeion.charts.draw_modern` with `draw_modern_horoscope()` and `draw_modern_dual_horoscope()` functions.

- New SVG template `kerykeion/charts/templates/modern_wheel.xml` for standalone modern wheel rendering.

**Bugfixes:**

- Fixed modern chart zodiac background ring using only 2 alternating colors instead of the full per-element color cycle. The outer ring now matches the classic chart's 4-color element pattern (fire/earth/air/water) in the default theme, with all 12 `--kerykeion-modern-zodiac-bg-*` CSS variables properly defined across all 6 themes.
- Fixed ruler ring ticks to be uniformly spaced across the full 360° circle.
- Fixed planet cluster sub-element sizes and reduced size progression for better readability.

**Documentation:**

- Added 2×2 chart style showcase grid (classic/modern × default/dark) to README
- Added Modern Chart Style section to README with examples for Natal, Synastry, Transit, and Wheel-Only
- Added `site/examples/modern-charts.md` example page
- Added `site/docs/charts.md` documentation with modern style API reference
- Added several new example/documentation pages (active points, ephemeris data, house comparison, transits time range)
- Simplified `MIGRATION_V4_TO_V5.md` — content moved to main documentation site

**Tests:**

- Added 36+ comprehensive modern chart style tests covering all chart types, themes, and rendering modes
- Added tests for `show_zodiac_background_ring=False` across chart types
- Added modern SVG baselines to the regeneration pipeline (`regenerate:svg:modern` poe task)

**Maintenance:**

- Updated all 6 CSS themes with modern-style variables
- Added `scripts/generate_modern_baselines.py` and `scripts/regenerate_docs_charts.py`
- Added example script `examples/modern_chart_john_lennon.py`

## 5.10.0

_Released 26/02/2026_

**Breaking Changes:**

- **Context Serializer XML Migration:** The `to_context()` function and all `*_to_context()` helper functions now produce well-formed **XML output** instead of plain text. This affects all 13 converter functions. XML uses semantic tags with attributes (e.g. `<point name="Sun" sign="Capricorn" ... />`), self-closing tags for atomic data, and nested tags for structured data. Optional/`None` fields are omitted from the output rather than rendered as empty tags. All values are properly escaped via `xml.sax.saxutils`.

**New Features:**

- Added `moon_phase_overview_to_context()` — serializes `MoonPhaseOverviewModel` to XML with full support for all nested fields (moon summary, sun info, location, zodiac, upcoming phases, eclipses, visibility, illumination details, events)
- Added `MoonPhaseOverviewModel` support in the `to_context()` dispatcher

**Bugfixes:**

- Fixed house cusp sign abbreviation in context serializer output (e.g. `"Ari"` now correctly rendered as `"Aries"` via `SIGN_FULL_NAMES` mapping)
- Fixed `llms.txt` import example (added missing `AstrologicalSubjectFactory`, `ChartDataFactory` imports)

**Documentation:**

- Updated `README.md` AI Context Serializer section with XML output examples
- Updated `site/docs/context_serializer.md` with XML format documentation and examples
- Updated `kerykeion/llms.txt` Section 6 to document XML output format
- Updated `examples/context_serializer_example.py` with Element/Quality Distribution and Moon Phase Overview examples

**Tests:**

- Rewrote all context serializer test assertions for XML format in `tests/core/test_context_serializer.py`
- Added 17 tests for `MoonPhaseOverviewToContext` covering all nested branches (zodiac, moonrise/moonset, eclipses, detailed position, visibility, illumination, events, sun info, extended location)
- Extended `TestNonQualitativeOutput` to verify subject, natal chart, synastry chart, and moon phase overview outputs
- Added synastry relationship score, transit data, house comparison, and point-in-house assertion enhancements
- Removed 2 dead stub tests
- Updated 7 context serializer edge case test classes for XML assertions

## 5.9.0

_Released 26/02/2026_

**New Features:**

- Added `MoonPhaseDetailsFactory` — a new factory class that computes detailed moon phase information from an `AstrologicalSubjectModel`. Uses Swiss Ephemeris binary search (1-second precision) to find exact times of upcoming and previous New Moon, First Quarter, Full Moon, and Last Quarter. Also computes illumination percentage, waxing/waning stage, moon age, lunar cycle progress, next lunar/solar eclipses, sunrise/sunset, solar noon, day length, and Sun/Moon zodiac signs.

- Added `MoonPhaseOverviewModel` report support in `ReportGenerator` — a new `"moon_phase_overview"` report kind that renders all moon phase details as a human-readable text report with sections for Moon Summary, Illumination Details, Upcoming Phases, Next Lunar Eclipse, Sun Info, Next Solar Eclipse, and Location.

**Documentation:**

- Added `moon_phase_details_factory.md` documentation page with API reference, nested data access patterns, JSON serialization, precision notes, and edge cases
- Added `moon-phase-details.md` examples page with practical usage examples (basic usage, upcoming phases, eclipses, sun times, report generation, JSON export, zodiac info, location metadata)
- Updated `report.md` with Moon Phase Overview Report section and configuration table
- Updated `index.md` with Moon Phase Details Factory link in the Forecasting section
- Updated `README.md` with Moon Phase Details section, code example, and links to documentation

**Tests:**

- Added 54 mocked unit tests for `MoonPhaseDetailsFactory` (helper functions, full `from_subject()` with mocked Swiss Ephemeris layer, null/failure edge cases, phase angle boundary tests)
- Added 21 report tests with golden snapshot fixture for moon phase overview
- Added 2042 historical verification tests against AstroPixels reference data (2001–2040), covering angle accuracy, phase names, emojis, factory major_phase, illumination, waxing/waning stage, upcoming phases, eclipse predictions, synodic month bounds, and 28-phase boundary mapping

**Bugfixes:**

- Fixed `ReportGenerator` crash when `_primary_subject` is `None` (added defensive `assert` guards in `_build_subject_report`, `_build_single_chart_report`, and `_build_dual_chart_report`)
- Fixed pre-existing `RelationshipScoreFactory` code snippet bug in `README.md` (wrong method name and field names)
- Fixed frontmatter ordering collision between `transits_time_range_factory.md` and `ephemeris_data_factory.md`

**Maintenance:**

- Added `charts_output/` to `.gitignore`
- Added example scripts: `moon_phase_report_example.py`, `moon_phase_json_example.py`

## 5.8.1

_Released 26/02/2026_

**Bugfixes:**

- Fixed degree label rotation on SVG chart outer ring.

**Maintenance:**

- Removed legacy chart drawing module (`draw_planets_legacy.py`)

## 5.8.0

_Released 24/02/2026_

**New Features:**

- Added `is_diurnal` field to `AstrologicalSubjectModel` — a boolean indicating whether the chart is diurnal (Sun above horizon) or nocturnal (Sun below horizon). This sect classification is calculated using the Sun's geometric altitude via `swe.azalt()`, making it independent of house system, zodiac type, and perspective type.

- Added `--arabic-parts` option to `regenerate_all.py` for generating Arabic Parts snapshots (`expected_arabic_parts.py`)

**Bugfixes:**

- Fixed day/night chart detection for Arabic Parts (Pars Fortunae, Spiritus). The previous logic used house position (`house < 7`) which was astronomically inverted — houses 1-6 are below the horizon (night), not above. The fix uses the Sun's geometric altitude, which is astronomically precise and house-system independent.

- Fixed Arabic Parts calculation for sidereal and heliocentric charts. Previously, the day/night detection used the Sun's position from the chart's coordinate system (sidereal or heliocentric), which gave incorrect results. Now it always uses a tropical geocentric reference position.

**Improvements:**

- Refactored `regenerate_all.py` to use `model_dump(exclude_none=True)` instead of manual field extraction, making it future-proof for new model fields

- Simplified `_compute_is_diurnal()` with a single fallback to `True` (diurnal) when calculation fails, with clear warning logging

- Added comprehensive test coverage for `is_diurnal` (15 tests) and Arabic Parts (68 tests total)

## 5.7.3

_Released 18/02/2026_

**Bugfixes:**

- Fixed floating point comparison in `is_point_between()` function that caused `ValueError` crashes when a planet falls exactly on a house cusp (difference ~1e-15°). The fix uses `math.isclose()` instead of exact equality (`==`). This affected Carter, Krusinski, and Uranian house systems.

## 5.7.2

_Released 05/02/2026_

**New Features:**

- Added support for `KERYKEION_GEONAMES_USERNAME` environment variable to configure GeoNames API username without code changes

**Bugfixes:**

- Regenerated extended chart SVG baselines (strawberry theme, sidereal×theme combinations, house system×chart type combinations) to align with the precise orb comparison fix from v5.7.1
- Updated relationship score test expectations to reflect stricter aspect filtering
- Fixed `regenerate:all` task to include `regenerate_test_charts_extended.py` script, preventing future baseline drift

**Maintenance:**

- Added `regenerate:charts-extended` poe task for regenerating extended test charts

## 4.2.0

_Released 08/01/2023_

**Bugfixes:**

- fixing float-int presidence bug

**Dependency Updates:**

- Updated `pydantic` to `2.5`

**Credits:**

- Thanks to @jackklika for the PR, more details [here](https://github.com/g-battaglia/kerykeion/pull/98)

## 4.4.0

_Released 05/03/2024_

**New Features:**

Allow UTC datetime to be passed in the constructor as an alternative to year, month, day, hour, minute and timezone (#108)

**Credits:**

- Thanks to @jackklika for the PR, more details [here](https://github.com/g-battaglia/kerykeion/pull/108)

## 4.5.0

- _AstrologicalSubject_ Is now possible to disable Chiron calculation with `disable_chiron=True` for better compatibility with older dates.
- New module enums added for better type hinting, still to be expanded and really used.

## 4.5.1

- Fixed | bug for compatibility with Python 3.9

## 4.6.0

- Now the `lunar_phase` contains also the `lunar_phase_name` property, which is a string representation of the phase.
- Minor general cleanup and refactoring of the codebase.

## 4.7.0

A lot of refactoring and clean up.
`Fix`: In the old version the 4 last planets of the Transit chart were always removed, now we check if those are Axes and then
remove them.

## 4.8.0

Added the optional `minify` argument to makeTemplate in the charts module.

## 4.10.0

- Added the `sidereal_mode` argument to the `AstrologicalChart` class to allow differet Ayanamsa calculation methods.

## 4.11.0

- Added different House Systems to the `AstrologicalChart` class.

## 4.14.0

- Added Lilith to astrological calculations and chart rendering.
- Deprecated `disable_chiron` in favor of `disable_chiron_and_lilith` with deprecation warning.
- Updated configuration in `kr.config.json` for Lilith settings.

## 4.16.0

- Added themed astrological charts (`theme` parameter), including Classic, Dark, Dark High Contrast, and Light themes.
- Added wheel-only charts and separate aspect table SVG.
- Added grid view for aspect tables in synastry and transit charts.

## 4.17.0

- Added `chart_language` parameter to set chart language (EN, FR, PT, ES, TR, RU, IT, CN, DE).
- Enhanced `get_settings` function to accept a dictionary or `KerykeionSettingsModel` instance.

## 4.19.0

- Added support for True and Mean Lunar Nodes (`true_node`, `true_south_node`, `mean_node`, `mean_south_node`).
- Default activation of mean nodes; configurable activation of true nodes via `kr.config.json`.

## 4.21.0

- Customizable Geonames cache timeout (default extended from 24 hours to 30 days).

**Credits:**

- Thanks to @tomshaffner for the idea and implementation.

## 4.22.0

- Explicit calculation of Ascendant (AC), Descendant (DC), Midheaven (MC), and Imum Coeli (IC) axes.
- Introduced `axial_cusps_names_list` parameter and replaced `check_if_between` with `is_point_between` utility.
- Configuration updates for axes in `kr.config.json`.

**Credits:**

- Thanks to @fkostadinov for implementing these changes in PR #138.

## 4.23.0

- Added `active_points` parameter to `KerykeionChartSVG` for runtime specification of active planets and axial cusps.

## 4.24.0

- Added `active_aspects` parameter to `KerykeionChartSVG` for runtime specification of active aspects and orbs.

## 4.25.0

- Added composite charts feature: create composite subjects and charts using the midpoint method.

## 4.26.0

- Introduced `TransitsTimeRangeFactory` for calculating transit events across specified time ranges.
- Added `get_ephemeris_data_as_astrological_subjects` method in `EphemerisDataFactory`.
- Added `p*_owner` fields in aspect models for subject identification in `natal_aspects` and `synastry_aspects`.
