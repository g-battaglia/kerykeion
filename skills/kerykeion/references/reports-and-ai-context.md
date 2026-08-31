# Reports and AI context

Two text surfaces over the same models: `ReportGenerator`
(`kerykeion/report/generator.py`) renders ASCII-table reports for humans;
`to_context` (`kerykeion/context/serializer.py`) renders strictly factual,
non-interpretive XML for LLM prompts. Both are top-level imports
(`from kerykeion import ReportGenerator, to_context`); the fifteen named
serializers are subpackage-only (`kerykeion.context`).

## ReportGenerator

```python
# doc-snippet: no-run
from kerykeion import ReportGenerator
gen = ReportGenerator(model, include_aspects=True, max_aspects=None)
text = gen.generate_report()          # str
gen.print_report(max_aspects=10)      # prints to stdout
```

Constructor: `ReportGenerator(model, *, include_aspects: bool = True,
max_aspects: Optional[int] = None)`. Any other model type raises `TypeError`
naming the supported set. Accepted model types (verified against
`_resolve_model`):

| Model | Report kind |
|---|---|
| `SingleChartDataModel` | full single-chart report (points, lots, stars, midpoints, houses, dignities, distributions, angularities, stelliums, aspects) |
| `DualChartDataModel` | dual-chart report (both subjects + comparison, relationship score, aspects) |
| `AstrologicalSubjectModel` | subject-only report (no aspects/distributions — those live on chart data) |
| `CompositeSubjectModel` | treated as a subject |
| `PlanetReturnModel` | treated as a subject |
| `MoonPhaseOverviewModel` | moon summary, illumination, upcoming phases, eclipses, sun info |
| `ProfectionsModel` | current year + years table |
| `FirdariaModel` | summary, periods, current sub-periods |
| `HoraryIndicatorsModel` | significators, considerations, receptions |
| `MutualReceptionsModel` | receptions table |
| `DominantsModel` | summary + ranked category tables |
| `ZodiacalReleasingModel` | summary, L1 periods, current period chain |

(`ChartDataModel` in the annotation is the alias
`Union[SingleChartDataModel, DualChartDataModel]`.)

Methods:

- `generate_report(*, include_aspects: Optional[bool] = None, max_aspects:
  Optional[int] = None) -> str` — `None` means "use the constructor default".
  The two kwargs only affect single/dual chart-data reports; subject and
  technique reports ignore them.
- `print_report(*, include_aspects=None, max_aspects=None) -> None` — prints
  `generate_report(...)`.

Attribute after init: `gen.chart_type` (`"Natal"`, `"Synastry"`, `"Subject"`,
`"Profections"`, ...). Subject-provided strings (name/city/nation) are
sanitized against terminal-control characters before printing.

Rows a consumer should not be surprised by (both surfaces carry them, and both
are silent when the chart has nothing to say):

- The house line names the division ACTUALLY cast, not the request:
  `Porphyry (substituted for Placidus)` on a polar chart. The context emits a
  `<polar_house_fallback>` element beside it.
- **Cusps On One Longitude** lists the groups from `coincident_house_cusps` —
  houses with no width, which can never contain anything. The context emits one
  `<coincident_house_cusps houses="...">` per group. Empty on every ordinary
  chart, so nothing is printed there.
- A midpoint composite prints a **House Anchor** row saying whether the request
  was granted: `midheaven (not held: the twelve cusps are not a house division)`
  where `house_frame` is not `"anchored"`. The context carries `house_frame`
  beside `house_anchor` on its composite element. A Davison chart has neither
  and prints no such row.

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
chart_data = ChartDataFactory.create_natal_chart_data(
    AstrologicalSubjectFactory.from_birth_data(
        name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False))
from kerykeion import ReportGenerator
report = ReportGenerator(chart_data, max_aspects=3).generate_report()
print(report[:800])
```

## to_context — the XML dispatcher

`to_context(model) -> str`. Dispatch order (isinstance checks, verified):

| Accepted type (in dispatch order) | Routed to |
|---|---|
| `SingleChartDataModel` | `single_chart_data_to_context` |
| `DualChartDataModel` | `dual_chart_data_to_context` |
| `TransitsTimeRangeModel` | `transits_time_range_to_context` |
| `TransitMomentModel` | `transit_moment_to_context` |
| `MoonPhaseOverviewModel` | `moon_phase_overview_to_context` |
| `AstrologicalSubjectModel` / `CompositeSubjectModel` / `PlanetReturnModel` | `astrological_subject_to_context` |
| `KerykeionPointModel` | `kerykeion_point_to_context` |
| `LunarPhaseModel` | `lunar_phase_to_context` |
| `AspectModel` | `aspect_to_context` |
| `ElementDistributionModel` | `element_distribution_to_context` |
| `QualityDistributionModel` | `quality_distribution_to_context` |
| `PointInHouseModel` | `point_in_house_to_context` |
| `HouseComparisonModel` | `house_comparison_to_context` |
| `SolarArcSubjectModel` | `solar_arc_to_context` |
| non-empty `list[MidpointModel]` | `midpoints_to_context` |

Anything else raises `TypeError` listing the supported types.

**TRAP — empty list raises `TypeError`.** `to_context([])` cannot tell an
empty midpoints list from an empty aspects list, so it raises instead of
guessing. For an intentionally empty midpoints set call
`midpoints_to_context([])` directly (it accepts `[]` and emits
`<midpoints_analysis count="0" ...>`).

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion import to_context
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
    city="Rome", nation="IT", online=False)
ctx = to_context(subject)          # <chart> XML: metadata, points, houses, lunar phase
print(ctx[:400])
```

## Named serializers

**Subpackage import:** `from kerykeion.context import midpoints_to_context`
(only `to_context` itself is re-exported at top level). `kerykeion.context.__all__`
has 16 names: `to_context` plus the 15 below. All return XML strings.

| Function | Signature beyond the model | Serializes |
|---|---|---|
| `kerykeion_point_to_context(point)` | — | one `KerykeionPointModel` |
| `lunar_phase_to_context(lunar_phase)` | — | `LunarPhaseModel` |
| `aspect_to_context(aspect, is_synastry=False, is_transit=False)` | role flags change owner labeling | `AspectModel` |
| `point_in_house_to_context(point_in_house, is_transit=False, transit_subject_name=None)` | — | `PointInHouseModel` |
| `house_comparison_to_context(house_comparison, is_transit=False)` | — | `HouseComparisonModel` |
| `element_distribution_to_context(distribution)` | — | `ElementDistributionModel` |
| `quality_distribution_to_context(distribution)` | — | `QualityDistributionModel` |
| `astrological_subject_to_context(subject, is_transit_subject=False)` | also takes composite/return models | full `<chart>` element |
| `single_chart_data_to_context(chart_data)` | — | `SingleChartDataModel` |
| `dual_chart_data_to_context(chart_data)` | — | `DualChartDataModel` |
| `transit_moment_to_context(transit)` | — | `TransitMomentModel` |
| `transits_time_range_to_context(transits)` | — | `TransitsTimeRangeModel` |
| `moon_phase_overview_to_context(overview)` | — | `MoonPhaseOverviewModel` |
| `solar_arc_to_context(model)` | — | `SolarArcSubjectModel` |
| `midpoints_to_context(midpoints)` | accepts `[]` | `list[MidpointModel]` |

Use a named serializer instead of `to_context` when you need the extra kwargs
(synastry/transit labeling) or an empty midpoints list.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.context import lunar_phase_to_context, midpoints_to_context
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
    city="Rome", nation="IT", online=False)
print(lunar_phase_to_context(subject.lunar_phase))
print(midpoints_to_context([]))     # legal; to_context([]) would raise TypeError
```

Related: chart-data inputs come from `ChartDataFactory` (see
`references/charts-and-drawing.md`); an end-to-end run lives in
`scripts/quickstart.py`.
