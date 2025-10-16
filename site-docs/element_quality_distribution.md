# Element & Quality Distribution

Kerykeion v5 introduces a flexible weighting system for the element (fire/earth/air/water) and quality (cardinal/fixed/mutable) statistics that every `ChartDataModel` exposes. The feature is available through `ChartDataFactory` and all of its convenience helpers, letting you pick between an observationally driven weighted balance or an even, point-per-body approach.

## Distribution methods

`ChartDataFactory.create_chart_data()` (and the helper constructors such as `create_natal_chart_data`, `create_synastry_chart_data`, etc.) now accept two keyword-only parameters:

- `distribution_method`: one of `"weighted"` (default) or `"pure_count"`.
- `custom_distribution_weights`: optional mapping that overrides the default weights.

Both parameters cascade through every chart flavour (natal, synastry, transit, composite, single/dual returns), so you can enforce a single policy throughout an application.

### Weighted mode (default)

The weighted strategy encodes the relative emphasis that astrologers typically assign to different points. The lookup is case-insensitive and covers every point shipped in the default settings. Highlights include:

- **2.0** – `sun`, `moon`, `ascendant`
- **1.5** – `medium_coeli`, `descendant`, `imum_coeli`, `mercury`, `venus`, `mars`
- **1.0** – `jupiter`, `saturn`
- **0.8** – `vertex`, `anti_vertex`, `pars_fortunae`
- **0.6** – `chiron`
- **0.5** – `uranus`, `neptune`, `pluto`, lunar nodes (`mean_*`, `true_*`), `mean_lilith`, `true_lilith`
- **0.4** – `pallas`, `juno`, `vesta`
- **0.3** – trans-neptunian objects (`eris`, `sedna`, `haumea`, `makemake`, `ixion`, `orcus`, `quaoar`), `pholus`, `earth`

Any point that does not appear in the table falls back to `1.0`, unless you override the default fallback via `{"__default__": value}`.

### Pure count mode

Setting `distribution_method="pure_count"` neutralises the weights—every active point contributes **exactly one unit** to its element and modality bucket. This is convenient when you want to mirror old-school tallying systems or when you are building analytics where each point should be treated equally.

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Ada Lovelace", 1815, 12, 10, 4, 20, "London", "GB"
)

pure_data = ChartDataFactory.create_natal_chart_data(
    subject,
    distribution_method="pure_count",
)

assert (
    pure_data.element_distribution.fire
    + pure_data.element_distribution.earth
    + pure_data.element_distribution.air
    + pure_data.element_distribution.water
) == len(pure_data.active_points)
```

### Custom overrides

Use `custom_distribution_weights` to adjust individual values without touching the global defaults. Keys are matched in lowercase, and the special `"__default__"` entry lets you update the fallback applied to unspecified points.

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Grace Hopper", 1906, 12, 9, 11, 30, "New York", "US"
)

custom_data = ChartDataFactory.create_natal_chart_data(
    subject,
    distribution_method="weighted",
    custom_distribution_weights={
        "sun": 3.0,          # emphasise the Sun even more
        "chiron": 1.2,       # elevate a specific point
        "__default__": 0.75, # lower everything else slightly
    },
)

print(custom_data.element_distribution.fire_percentage)
```

When you provide overrides, only the specified entries change—the rest of the curated map remains intact.

### Working with dual charts

The same parameters apply to synastry, transit, and dual return charts:

```python
first = AstrologicalSubjectFactory.from_birth_data("Person A", 1990, 6, 15, 14, 30, "Rome", "IT")
second = AstrologicalSubjectFactory.from_birth_data("Person B", 1992, 11, 5, 9, 30, "Milan", "IT")

synastry_data = ChartDataFactory.create_synastry_chart_data(
    first,
    second,
    distribution_method="weighted",
    custom_distribution_weights={"venus": 2.5, "mars": 2.5},
)

print(synastry_data.element_distribution.air_percentage)
```

Totals for dual charts are normalised to 100% after combining both subjects, so percentages remain comparable regardless of the weighting scheme you choose.

## Tips

- All keys are lowercase; the factory normalises `"Sun"` to `"sun"` internally.
- Combining `distribution_method="pure_count"` with a `custom_distribution_weights` mapping is allowed, but only the fallback (`"__default__"`) will have an effect because every individual point is forced to 1.0 in pure-count mode.
- The default weight map is exported as `DEFAULT_WEIGHTED_POINT_WEIGHTS` in `kerykeion.charts.charts_utils` if you need to introspect it programmatically.
