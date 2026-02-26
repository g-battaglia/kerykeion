# Changelog

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
