# Changelog

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
