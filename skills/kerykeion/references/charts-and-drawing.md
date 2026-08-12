# Charts and drawing

Chart generation is a strict two-step pipeline: `ChartDataFactory` (kerykeion/chart_data/factory.py) computes a pure-data `ChartDataModel` (subjects, aspects, distributions, angularities, stelliums, house comparison, relationship score), then `ChartDrawer` (kerykeion/charts/drawer.py) renders that model to SVG — the drawer performs no astrological calculation. Both classes are top-level exports (`from kerykeion import ChartDataFactory, ChartDrawer`). Aspect math details live in `references/aspects-and-orbs.md`; subject construction in `references/subjects.md`.

## Contents

- [ChartType](#charttype)
- [ChartDataFactory](#chartdatafactory)
- [Chart data models](#chart-data-models)
- [ChartDrawer](#chartdrawer)
- [Output methods and filenames](#output-methods-and-filenames)
- [Themes, styles, languages](#themes-styles-languages)
- [SVG metadata parsing](#svg-metadata-parsing)
- [Chart settings and translations](#chart-settings-and-translations)

## ChartType

`ChartType` (import `from kerykeion.schemas import ChartType`) is a `Literal` with exactly 7 values:

| Value | Wheel | Subjects | Data model |
|---|---|---|---|
| `"Natal"` | single | 1 | `SingleChartDataModel` |
| `"Composite"` | single | 1 (`CompositeSubjectModel`) | `SingleChartDataModel` |
| `"SingleReturnChart"` | single | 1 (`PlanetReturnModel`) | `SingleChartDataModel` |
| `"Synastry"` | dual | 2 | `DualChartDataModel` |
| `"Transit"` | dual | 2 | `DualChartDataModel` |
| `"DualReturnChart"` | dual | natal + `PlanetReturnModel` | `DualChartDataModel` |
| `"Progression"` | dual | natal + progressed | `DualChartDataModel` |

An unknown `chart_type` raises `KerykeionException` listing the valid values.

## ChartDataFactory

All methods are `@staticmethod`. The generic entry point:

```python
# doc-snippet: no-run
ChartDataFactory.create_chart_data(
    chart_type, first_subject, second_subject=None,
    active_points=None, active_aspects=None,
    include_house_comparison=True, include_relationship_score=False,
    *, axis_orb_limit=None, point_orb_adjustments=None,
    point_orb_adjustment_strategy="max_explicit",
    distribution_method="weighted", custom_distribution_weights=None,
) -> ChartDataModel
```

Typed wrappers (all forward to `create_chart_data`):

| Method | chart_type | Positional subjects |
|---|---|---|
| `create_natal_chart_data(subject, ...)` | `Natal` | 1 |
| `create_synastry_chart_data(first_subject, second_subject, ...)` | `Synastry` | 2 |
| `create_transit_chart_data(natal_subject, transit_subject, ...)` | `Transit` | 2 |
| `create_composite_chart_data(composite_subject, ...)` | `Composite` | 1, must be `CompositeSubjectModel` |
| `create_return_chart_data(natal_subject, return_subject, ...)` | `DualReturnChart` | 2, second must be `PlanetReturnModel` |
| `create_single_wheel_return_chart_data(return_subject, ...)` | `SingleReturnChart` | 1, must be `PlanetReturnModel` |
| `create_progression_chart_data(natal_subject, progressed_subject, ...)` | `Progression` | 2, both `AstrologicalSubjectModel` |

Shared kwargs (identical names on every method; keyword-only after `*`):

| Kwarg | Default | Semantics |
|---|---|---|
| `active_points` | `None` | `None` → subject's own `active_points`. An explicit list is INTERSECTED with the subject's (and, dual charts, the second subject's). An explicit `[]` is a real empty filter, not "everything". |
| `active_aspects` | `None` | `None` → per-chart-type default: `DEFAULT_ACTIVE_ASPECTS` for Natal/Synastry/Composite, `PREDICTIVE_ACTIVE_ASPECTS` (flat 3°) for every other type. |
| `include_house_comparison` | `True` | Dual charts only (absent from single-wheel wrappers). |
| `include_relationship_score` | `False` on `create_chart_data`; **`True` on `create_synastry_chart_data`** | Synastry only. Skipped with a warning if a partner has no Sun (non-geocentric perspective). |
| `axis_orb_limit` | `None` | When set, aspects involving Ascendant/Medium_Coeli/Descendant/Imum_Coeli are kept only below this orb. |
| `point_orb_adjustments` | `None` | `None` → `DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS` (`{"Sun": 1.5, "Moon": 1.5}`) for Natal/Synastry/Composite, `NO_POINT_ORB_ADJUSTMENTS` (`{}`) for the rest. Pass `{}` to disable explicitly. See `references/aspects-and-orbs.md`. |
| `point_orb_adjustment_strategy` | `"max_explicit"` | `OrbAdjustmentStrategy`. |
| `distribution_method` | `"weighted"` | `ElementQualityDistributionMethod = Literal["pure_count", "weighted"]`. **Subpackage import:** `from kerykeion.charts.utils import ElementQualityDistributionMethod` |
| `custom_distribution_weights` | `None` | `Mapping[str, float]` overrides for the weighted method. |

Internally the factory sets aspect-movement frames: Synastry treats both subjects as fixed (speeds zeroed); Transit/DualReturnChart/Progression fix the first (natal) subject and let the second move.

Semantics worth knowing before debugging output:

- The serialized `active_points` / `active_aspects` on the result come from the **aspects model**, not from the raw inputs: requested catalog fixed stars are appended to `active_points` (as plain strings) as considered participants — they appear even when they match no aspect — and `parallel`/`contra-parallel` names passed in `active_aspects` are dropped (the longitudinal engine ignores them — see `references/aspects-and-orbs.md`).
- Element/quality distributions for Transit/DualReturnChart/Progression are computed over the FIRST subject's own points intersected with the caller's explicit `active_points` filter — the second subject's (possibly smaller) tracking set never truncates the natal distribution. Synastry distributions instead use the common point set of both partners, and its per-subject angularities/stelliums honour that same common set.
- Failure modes (`KerykeionException`): unknown `chart_type`; missing `second_subject` for a dual type; wrong subject class for Composite / SingleReturnChart / DualReturnChart / Progression (see the wrapper table).

Typical dual-chart pipeline, data to drawing:

```python
# doc-snippet: no-run
transit_data = ChartDataFactory.create_transit_chart_data(natal_subject, transit_subject)
drawer = ChartDrawer(chart_data=transit_data, double_chart_aspect_grid_type="table")
drawer.save_svg(output_path=out_dir)   # "{name} - Transit Chart - Modern.svg"
```

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
first = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
second = AstrologicalSubjectFactory.from_birth_data(
    name="Second Person", year=1992, month=3, day=21, hour=8, minute=15,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
data = ChartDataFactory.create_synastry_chart_data(first, second)
assert data.chart_type == "Synastry"
assert data.relationship_score is not None   # synastry wrapper defaults it on
assert data.house_comparison is not None
assert data.first_subject_angularities is not None and data.aspects
```

## Chart data models

**CALLOUT — `ChartDataModel` is a `Union` type ALIAS**, `ChartDataModel = Union[SingleChartDataModel, DualChartDataModel]` (kerykeion/schemas/models.py) — a type alias, not a class you can construct or subclass. `isinstance(x, ChartDataModel)` works at runtime on all supported Pythons (3.12+); branching on `x.chart_type` or testing `isinstance(x, DualChartDataModel)` is the idiomatic way to tell the two shapes apart. All three names are top-level exports.

`SingleChartDataModel` fields:

| Field | Type |
|---|---|
| `chart_type` | `Literal["Natal", "Composite", "SingleReturnChart"]` |
| `subject` | `AnySubjectModel` |
| `aspects` | `list[AspectModel]` |
| `element_distribution` / `quality_distribution` | `ElementDistributionModel` / `QualityDistributionModel` |
| `angularities` | `list[AngularityModel]` (a83) |
| `stelliums` | `list[StelliumModel]` (a83) |
| `active_points` | `list[Union[AstrologicalPoint, str]]` (plain `str` = catalog fixed stars) |
| `active_aspects` | `list[ActiveAspect]` (declination names already dropped) |

`DualChartDataModel` fields: `chart_type` (`Literal["Transit", "Synastry", "DualReturnChart", "Progression"]`), `first_subject`, `second_subject`, `aspects`, `house_comparison: Optional[HouseComparisonModel]`, `relationship_score: Optional[RelationshipScoreModel]`, the two distributions, per-subject analyses `first_subject_angularities`, `first_subject_stelliums`, `second_subject_angularities`, `second_subject_stelliums`, plus `active_points` / `active_aspects`. Distribution semantics differ by type: **Synastry combines both partners' points; Transit/DualReturnChart/Progression describe the FIRST (natal) subject only.**

- `AngularityModel` — `point: str`, `angle: str`, `distance: float`. Classical seven planets vs the four angles, 8° orb, ALL in-orb pairs (not just each planet's nearest angle), sorted closest-first. Non-terrestrial perspectives yield `[]`.
- `StelliumModel` — `house: int` (1–12), `points: list[str]`. Houses holding ≥3 classical planets, biggest first.
- `ElementDistributionModel` — `fire/earth/air/water: float` (raw point totals) + `fire_percentage/earth_percentage/air_percentage/water_percentage: int` (normalized to 100).
- `QualityDistributionModel` — `cardinal/fixed/mutable: float` + `cardinal_percentage/fixed_percentage/mutable_percentage: int`.

## ChartDrawer

Constructor: `ChartDrawer(chart_data, *, ...)` — `chart_data` is the only positional argument; everything else is keyword-only.

| Kwarg | Default | Notes |
|---|---|---|
| `theme` | `"classic"` | `KerykeionChartTheme` or `None` (no CSS). Invalid value raises `KerykeionException`. |
| `double_chart_aspect_grid_type` | `"list"` | `"list"` or `"table"`; anything else raises. |
| `chart_language` | `"EN"` | `KerykeionChartLanguage`; unknown code raises unless `language_pack` supplies it. |
| `language_pack` | `None` | Partial pack merges over a bundled language; for a NEW code the pack must be complete (clone the EN block) or validation fails. |
| `external_view` | `False` | Natal only, classic style only. |
| `transparent_background` | `False` | Skip the theme background color. |
| `colors_settings` | `DEFAULT_CHART_COLORS` | `dict[str, str]`. |
| `celestial_points_settings` | `DEFAULT_CELESTIAL_POINTS_SETTINGS` | Sequence of point-setting dicts. |
| `aspects_settings` | `DEFAULT_CHART_ASPECTS_SETTINGS` | Sequence of `{degree, name, is_major, color}` dicts. |
| `custom_title` | `None` | Overrides the auto-generated title. |
| `show_house_position_comparison` | `True` | House comparison grid on supported dual charts. |
| `show_cusp_position_comparison` | `False` | Cusp comparison grid alongside it. |
| `auto_size` | `True` | Fit dimensions to content. |
| `padding` | `20` | Pixels. |
| `show_degree_indicators` | `True` | Classic style only. |
| `show_aspect_icons` | `True` | Classic style only. |
| `style` | `"modern"` | `KerykeionChartStyle` — wheel geometry default for render methods. |
| `show_zodiac_background_ring` | `True` | Colored zodiac wedges (modern only); overridable at render time. |
| `show_diurnality` | `True` | Diurnality line in the bottom-left info panel. |

**THE TRAP — `theme` vs `style` are orthogonal axes.** `theme` selects a CSS palette and defaults to `"classic"`; `style` selects the wheel geometry and defaults to `"modern"`. The default render is therefore classic *palette* on a modern *wheel*. `"classic"` appears in both literals but means different things; to get the traditional v5-style drawing pass `style="classic"` (theme choice is independent).

Classic-only options (`external_view`, `show_degree_indicators=False`, `show_aspect_icons=False`): the modern renderer ignores all three, logs one warning per option per drawer instance, and renders anyway. Pass `style="classic"` for them to take effect.

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
data = ChartDataFactory.create_natal_chart_data(subject)
svg = ChartDrawer(chart_data=data).generate_svg_string()
assert "<svg" in svg
```

## Output methods and filenames

| Method | Extra kwargs beyond `minify=False, remove_css_variables=False` | Returns |
|---|---|---|
| `set_up_theme(theme=None)` | — | `None` (loads `charts/themes/{theme}.css`; `None` clears CSS) |
| `generate_svg_string(...)` | `*, custom_title=None, style=<ctor>, show_zodiac_background_ring=<ctor>` | `str` |
| `save_svg(output_path=None, filename=None, ...)` | same as above | `None` |
| `generate_wheel_only_svg_string(...)` | `*, style=<ctor>, show_zodiac_background_ring=<ctor>` | `str` |
| `save_wheel_only_svg_file(output_path=None, filename=None, ...)` | same as above | `None` |
| `generate_aspect_grid_only_svg_string(...)` | — | `str` |
| `save_aspect_grid_only_svg_file(output_path=None, filename=None, ...)` | — | `None` |

`style=` at render time overrides the constructor default per call. `minify=True` strips whitespace/quotes; `remove_css_variables=True` inlines the CSS custom-property definitions (needed by SVG consumers that do not resolve `var(...)`, e.g. many raster converters). `output_path=None` writes to the user's HOME directory — always pass a directory. `filename` is the basename without `.svg`; user-supplied names are sanitized (path separators, `..`, leading dots become underscores) and the resolved path must stay inside the output directory or `KerykeionException` is raised.

Layout notes: with more than 24 active points the aspect list/grid moves to a full-height right-side panel instead of below the wheel. `double_chart_aspect_grid_type="table"` renders the dual-chart aspect grid as a matrix instead of the default column list.

Default filenames (a80 — style suffix included):

- Full chart: `"{name} - {chart_type} Chart - Modern.svg"` or `"... - Classic.svg"`
- Wheel only: `"{name} - {chart_type} Chart - {Modern|Classic} Wheel Only.svg"`
- Aspect grid: `"{name} - {chart_type} Chart - Aspect Grid Only.svg"`
- `DualReturnChart` inserts the English return label (e.g. `"... - DualReturnChart Chart - Solar Return - Modern.svg"`); Natal with `external_view=True` renames to `ExternalNatal` for classic wheel-only and grid-only exports only.

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
import tempfile
from pathlib import Path
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
data = ChartDataFactory.create_natal_chart_data(subject)
with tempfile.TemporaryDirectory() as tmp:
    ChartDrawer(chart_data=data).save_svg(output_path=tmp)
    names = sorted(p.name for p in Path(tmp).iterdir())
    assert names == ["Example Person - Natal Chart - Modern.svg"]
```

## Themes, styles, languages

- `KerykeionChartTheme` (6): `"light"`, `"dark"`, `"dark-high-contrast"`, `"classic"`, `"strawberry"`, `"black-and-white"` — CSS files in kerykeion/charts/themes/.
- `KerykeionChartStyle` (2): `"classic"` | `"modern"`.
- `KerykeionChartLanguage` (10): `"EN"`, `"FR"`, `"PT"`, `"IT"`, `"CN"`, `"ES"`, `"RU"`, `"TR"`, `"DE"`, `"HI"`.

All three literals import from `kerykeion.schemas`.

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(chart_data=data, theme="dark", chart_language="IT")
svg = drawer.generate_wheel_only_svg_string()
assert "<svg" in svg
```

## SVG metadata parsing

Rendered SVGs carry `kr:` metadata: each celestial point is a `<g kr:node="ChartPoint">` rotated to its display angle, each tether line a `<g kr:node="Indicator">` rotated to the true angle. Parse them back without regex of your own.

**Subpackage import:** `from kerykeion.charts.svg_metadata import ChartPointTag, IndicatorTag, parse_chart_points, parse_indicators`

- `parse_chart_points(svg: str) -> list[ChartPointTag]` — frozen dataclass with `slug: str`, `horoscope: str` (`"0"` single/inner ring, `"1"` dual outer ring), `display_angle: float` (post-decluttering wheel angle), `sign: Optional[str]`, `sign_position: Optional[float]`, `retrograde: bool`.
- `parse_indicators(svg: str) -> list[IndicatorTag]` — `slug`, `horoscope`, `true_angle: float` (the point's undisplaced angle).

## Chart settings and translations

`kerykeion.settings` `__all__` (verify-imported names):

| Name | What it is |
|---|---|
| `KerykeionSettingsModel` | Pydantic settings model (also a top-level `kerykeion` export). |
| `DEFAULT_CHART_COLORS` | `dict[str, str]` of chart color tokens. |
| `DEFAULT_CELESTIAL_POINTS_SETTINGS` | `list` of per-point setting dicts (name, id, color, ...). |
| `DEFAULT_CHART_ASPECTS_SETTINGS` | `list` of `{degree, name, is_major, color}` aspect settings. |
| `DEFAULT_ACTIVE_POINTS`, `ALL_ACTIVE_POINTS`, `V5_DEFAULT_ACTIVE_POINTS` | Point-set presets (see `references/subjects.md`). |
| `DEFAULT_ACTIVE_ASPECTS` | Aspect preset (see `references/aspects-and-orbs.md`). |
| `LANGUAGE_SETTINGS` | Bundled translation table keyed by language code. |
| `load_language_settings(overrides=None)` | Full table (deep copy) merged with optional overrides. |
| `load_language_pair(language, overrides=None)` | `(selected_language_data, english_fallback_data)` — the cheap two-block loader `ChartDrawer` uses. |
| `get_translations(value, default, *, language=None, language_dict=None, fallback_dict=None)` | Dot-path lookup (`"planets.Sun"`) with English fallback. |
| `SettingsSource` | Type alias `Optional[Mapping[str, Any]]`. |

Customization shapes (what `ChartDrawer` expects in its `*_settings` kwargs):

- `colors_settings` — `dict[str, str]` whose values are CSS tokens like `"var(--kerykeion-chart-color-paper-0)"`. Key families in `DEFAULT_CHART_COLORS`: `paper_0`/`paper_1`, `zodiac_bg_0`…`zodiac_bg_11`, `zodiac_icon_0`…`zodiac_icon_11`, `zodiac_radix_ring_0`–`2`, `zodiac_transit_ring_0`–`3`, `houses_radix_line`, `houses_transit_line`, `lunar_phase_0`/`lunar_phase_1`. Pass literal colors to override; pair with `remove_css_variables=True` if the consumer cannot resolve `var(...)`.
- `celestial_points_settings` — sequence of dicts with required keys `id: int`, `name: str`, `color: str`, `element_points: int`, `label: str`; optional `is_active: bool`, `glyph_id: str` (fallback SVG symbol reference for dynamic points).
- `aspects_settings` — sequence of dicts with required keys `degree: int`, `name: str`, `is_major: bool`, `color: str`; optional `orb: float`. An aspect name absent from this sequence cannot be computed or drawn (unknown `active_aspects` names are warned about and ignored).

`load_settings_mapping` is importable from `kerykeion.settings.loader` but deprecated (removal in 7.0.0) and deliberately excluded from `__all__` — see `references/migration-and-deprecations.md`.
