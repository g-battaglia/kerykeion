# Changelog

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
