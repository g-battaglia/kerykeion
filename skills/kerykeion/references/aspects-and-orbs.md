# Aspects and orbs

`AspectsFactory` (kerykeion/aspects/factory.py; top-level export `from kerykeion import AspectsFactory`) computes ecliptic (longitudinal) and declination aspects for single charts and chart pairs. The a82 per-point orb matrix (kerykeion/aspects/orb_utils.py) adds additive per-point, optionally per-aspect, orb deltas with explicit-only semantics. `ChartDataFactory` builds on these methods — see `references/charts-and-drawing.md`.

## AspectsFactory methods

All are `@staticmethod`; subjects are `AstrologicalSubjectModel | CompositeSubjectModel | PlanetReturnModel`.

| Method | Keyword-only kwargs (defaults) | Returns |
|---|---|---|
| `single_chart_aspects(subject, ...)` | `active_points=None, active_aspects=None, axis_orb_limit=None, point_orb_adjustments=None, point_orb_adjustment_strategy="max_explicit"` | `SingleChartAspectsModel` |
| `dual_chart_aspects(first_subject, second_subject, ...)` | same, plus `first_subject_is_fixed=False, second_subject_is_fixed=False` | `DualChartAspectsModel` |
| `single_chart_declination_aspects(subject, ...)` | `active_points=None, orb=1.0` | `list[AspectModel]` |
| `dual_chart_declination_aspects(first_subject, second_subject, ...)` | `active_points=None, orb=1.0` | `list[AspectModel]` |

Semantics that matter:

- `active_points=None` → the subject's own `active_points`; an explicit list is intersected with them (dual charts intersect both subjects). Catalog fixed stars carried on `subject.fixed_stars` always participate as a separate channel regardless of `active_points`; star–star pairs are skipped (mutually static, zero information).
- `active_aspects=None` → `DEFAULT_ACTIVE_ASPECTS`. **Unlike `ChartDataFactory`, these methods apply NO luminary orb widening by default** — to reproduce `ChartDataFactory` natal output pass `point_orb_adjustments=DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS`. Duplicate names in `active_aspects`: the FIRST orb wins. Names without an entry in `DEFAULT_CHART_ASPECTS_SETTINGS` log a warning and are ignored.
- `axis_orb_limit` keeps aspects where either endpoint is an axis (Ascendant/Medium_Coeli/Descendant/Imum_Coeli) only below the given orb; must be a finite positive number when provided, else `KerykeionException`.
- `first_subject_is_fixed` / `second_subject_is_fixed` zero that subject's point speeds before computing `aspect_movement` (synastry: both fixed; transit-like: first fixed, second moving — the convention `ChartDataFactory` applies automatically). Cross-chart axis–axis pairs are always `"Static"`.
- `dual_chart_aspects` raises `KerykeionException` on mixed reference frames (e.g. Tropical × Sidereal).
- Declination methods take only `orb` (finite, non-negative; default 1.0) — no `active_aspects`, no orb matrix.

Artifact-pair suppression (single-chart paths only, both longitudinal and declination): geometrically locked opposite pairs (each derived point rigid at primary + 180° — Descendant/Ascendant, Imum_Coeli/Medium_Coeli, Anti-Vertex/Vertex, South/North node ends, Priapus/Lilith) and mean×true lunar-node combinations are skipped — they would report permanent 0-orb oppositions or permanent parallels. Cross-chart pairs (synastry, transits) are meaningful and are NOT skipped.

Declination geometry: a **parallel** is two declinations of the same sign within `orb` of each other; a **contra-parallel** is opposite signs with magnitudes within `orb`. Each pair reports at most one of the two.

Deprecated (DeprecationWarning, removal in 7.0.0): `natal_aspects` → `single_chart_aspects`, `synastry_aspects` → `dual_chart_aspects` — see `references/migration-and-deprecations.md`.

```python
from kerykeion import AspectsFactory
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
model = AspectsFactory.single_chart_aspects(subject)
assert model.aspects and model.subject.name == "Example Person"
assert all(a.aspect_movement in ("Applying", "Separating", "Static") for a in model.aspects)
```

```python
from kerykeion import AspectsFactory
first = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
second = AstrologicalSubjectFactory.from_birth_data(
    name="Second Person", year=1992, month=3, day=21, hour=8, minute=15,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
synastry = AspectsFactory.dual_chart_aspects(
    first, second, first_subject_is_fixed=True, second_subject_is_fixed=True)
assert synastry.aspects[0].p1_owner == "Example Person"
assert synastry.aspects[0].p2_owner == "Second Person"
```

## Entry-point defaults compared

The same subjects produce DIFFERENT aspect lists depending on which factory computes them — the defaults differ:

| Default | `AspectsFactory` methods | `ChartDataFactory` (Natal/Synastry/Composite) | `ChartDataFactory` (other types) |
|---|---|---|---|
| `active_aspects` | `DEFAULT_ACTIVE_ASPECTS` | `DEFAULT_ACTIVE_ASPECTS` | `PREDICTIVE_ACTIVE_ASPECTS` (flat 3°) |
| `point_orb_adjustments` | none (`None`) | `DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS` (Sun/Moon +1.5°) | `NO_POINT_ORB_ADJUSTMENTS` |
| fixed-subject flags | both `False` | set per chart type automatically | set per chart type automatically |

So `AspectsFactory.single_chart_aspects(subject)` finds FEWER Sun/Moon aspects than `ChartDataFactory.create_natal_chart_data(subject).aspects` unless you pass the luminary table yourself. In dual-chart results, `p1_*` fields always belong to the first subject and `p2_*` to the second — direction is positional, and `p1_owner`/`p2_owner` carry the subject names for display.

## Models and literals

`AspectModel` (top-level export) fields:

| Field | Type | Meaning |
|---|---|---|
| `p1_name`, `p2_name` | `str` | Point names. |
| `p1_owner`, `p2_owner` | `str` | Owning subject's `name` (same subject twice for single charts). |
| `p1_abs_pos`, `p2_abs_pos` | `float` | Ecliptic longitudes 0–360. |
| `aspect` | `str` | An `AspectName` value. |
| `orbit` | `float` | Deviation from exact, degrees. |
| `aspect_degrees` | `int` | Exact angle of the aspect type (0 for declination aspects). |
| `diff` | `float` | Angular difference between the points. |
| `p1`, `p2` | `int` | Numeric point ids (0 for unknown/fixed stars). |
| `p1_speed`, `p2_speed` | `float` (default 0.0) | Daily motion; zeroed for fixed subjects. |
| `aspect_movement` | `AspectMovementType` | `"Applying"` \| `"Separating"` \| `"Static"`. |

Container models (both top-level exports):

| Model | Fields |
|---|---|
| `SingleChartAspectsModel` | `subject`, `aspects: list[AspectModel]`, `active_points: list[Union[AstrologicalPoint, str]]` (plain strings = catalog fixed stars), `active_aspects: list[ActiveAspect]` (only names actually computed) |
| `DualChartAspectsModel` | `first_subject`, `second_subject`, `aspects`, `active_points`, `active_aspects` — same conventions |

`p1`/`p2` numeric ids come from the `id` field of `DEFAULT_CELESTIAL_POINTS_SETTINGS` entries; points without an entry (catalog fixed stars) report `0`.

Field reading notes:

- `orbit` is the deviation from the exact aspect angle; `diff` is the raw angular separation between the two points along the ecliptic.
- For declination aspects `orbit` and `diff` are both the declination difference (rounded to 6 decimals), `aspect_degrees` is `0`, and `p1_speed`/`p2_speed` are `0.0`.
- `p1_abs_pos`/`p2_abs_pos` stay ecliptic longitudes even for declination aspects (useful for locating the points on a wheel).
- `AspectName` (`from kerykeion.schemas import AspectName`) — 11 ecliptic values: `conjunction`, `semi-sextile`, `semi-square`, `sextile`, `quintile`, `square`, `trine`, `sesquiquadrate`, `biquintile`, `quincunx`, `opposition`; plus `parallel` and `contra-parallel`, which exist ONLY via the declination methods. Putting `parallel`/`contra-parallel` in `active_aspects` logs a warning, computes nothing, and drops them from the serialized `active_aspects`.
- `AspectMovementType` (`from kerykeion.schemas import AspectMovementType`) = `Literal["Applying", "Separating", "Static"]` — derived from positions and (possibly zeroed) speeds. Declination aspects are always `"Static"`; points lacking a `declination` value are silently skipped by the declination methods.
- `ActiveAspect` (`from kerykeion.schemas import ActiveAspect`; defined in kerykeion/schemas/models.py) — `TypedDict` `{name: AspectName, orb: float}`.
- `PTOLEMAIC_ASPECTS` — top-level export (`from kerykeion import PTOLEMAIC_ASPECTS`, home kerykeion/predictive/utils.py): `tuple` of the five names `("conjunction", "opposition", "trine", "sextile", "square")` — names only, no orbs; not an `active_aspects` value.

```python
from kerykeion import AspectsFactory
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
decl = AspectsFactory.single_chart_declination_aspects(subject, orb=1.0)
assert all(a.aspect in ("parallel", "contra-parallel") for a in decl)
assert all(a.aspect_movement == "Static" for a in decl)
```

## The orb matrix (a82)

**Subpackage import:** `from kerykeion.aspects.orb_utils import PointOrbAdjustment, OrbAdjustmentStrategy, resolve_pair_orb_adjustment, validate_point_orb_adjustments`

- `PointOrbAdjustment = Union[float, Mapping[str, float]]` — a point's entry: either one additive delta for every aspect, or a per-aspect mapping whose `"*"` key is the default for unlisted aspects (`1.5` ≡ `{"*": 1.5}`). Without `"*"`, the point is *unconfigured* for unlisted aspects — NOT `0.0`.
- `OrbAdjustmentStrategy = Literal["max_explicit", "min_explicit", "sum", "none"]` — how the two points' deltas combine. A misspelled strategy raises `ValueError` (never silently disables).
- **EXPLICIT-ONLY semantics**: a point missing from the table contributes nothing rather than `0.0`. With `{"Pluto": -2.0}` and pair (Pluto, Saturn), `max_explicit` resolves to `-2.0` — the orb TIGHTENS; a naive `max(-2.0, 0.0)` would have silently dropped it. Negative deltas tighten, positive widen; the resolved delta is added to the aspect's base orb.
- Validation: non-finite numbers and `bool` values raise `ValueError`; unknown aspect names inside a mapping only log a warning (the table may serve configurations enabling different aspect sets).

Strategy outcomes for the pair (Sun, Saturn) with table `{"Sun": 1.5, "Saturn": -1.0}` versus `{"Sun": 1.5}`:

| Strategy | Both configured | Only Sun configured |
|---|---|---|
| `max_explicit` (default) | `1.5` | `1.5` (the classic "either point is a luminary" rule) |
| `min_explicit` | `-1.0` | `1.5` (the single explicit value, not `min(1.5, 0.0)`) |
| `sum` | `0.5` | `1.5` |
| `none` | `0.0` | `0.0` |

The resolver itself is public:

```python
# doc-snippet: no-run
from kerykeion.aspects.orb_utils import resolve_pair_orb_adjustment
delta = resolve_pair_orb_adjustment(
    "Sun", "Saturn", {"Sun": {"*": 1.5, "conjunction": 3.0}},
    strategy="max_explicit", aspect_name="conjunction")   # -> 3.0
```

APIs accepting `point_orb_adjustments` + `point_orb_adjustment_strategy`: `AspectsFactory.single_chart_aspects` / `dual_chart_aspects` (default `None` = no adjustment), every `ChartDataFactory` method (default `None` = Sun/Moon +1.5° for Natal/Synastry/Composite, none otherwise), `SecondaryProgressionFactory.compute_full`, and `SolarArcFactory.compute` (see `references/predictive.md`). The declination methods do not accept them.

```python
from kerykeion import AspectsFactory
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
model = AspectsFactory.single_chart_aspects(
    subject,
    active_aspects=[{"name": "conjunction", "orb": 6}, {"name": "opposition", "orb": 6}],
    point_orb_adjustments={"Sun": {"*": 1.5, "conjunction": 3.0}, "Pluto": -2.0},
)
assert all(a.aspect in ("conjunction", "opposition") for a in model.aspects)
assert [a["name"] for a in model.active_aspects] == ["conjunction", "opposition"]
```

## Aspect-set presets

`DEFAULT_ACTIVE_ASPECTS` imports from `kerykeion.settings`; the rest are deep imports.

**Subpackage import:** `from kerykeion.settings.config_constants import PREDICTIVE_ACTIVE_ASPECTS, ALL_ACTIVE_ASPECTS, DISCEPOLO_SCORE_ACTIVE_ASPECTS, DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS, NO_POINT_ORB_ADJUSTMENTS`

| Constant | Contents |
|---|---|
| `DEFAULT_ACTIVE_ASPECTS` | conjunction/opposition/trine/square 6°, sextile 5°. Natal-family default. |
| `PREDICTIVE_ACTIVE_ASPECTS` | The five Ptolemaic aspects, flat 3°. Default for transits, returns, progressions. |
| `ALL_ACTIVE_ASPECTS` | Majors 6° (sextile 5°) plus quintile, semi-sextile, semi-square, sesquiquadrate, biquintile, quincunx at 2°. |
| `DISCEPOLO_SCORE_ACTIVE_ASPECTS` | Ciro Discepolo's scoring orbs: conjunction/opposition 8°, trine 7°, square 5°, sextile 4°, semi-sextile/semi-square/sesquiquadrate 2°. |
| `DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS` | `{"Sun": 1.5, "Moon": 1.5}` — luminary widening (6° base → 7.5°). |
| `NO_POINT_ORB_ADJUSTMENTS` | `{}` — flat orbs for predictive work. |

Downstream consumers of these presets and of `AspectModel` lists: `ChartDataFactory` (see `references/charts-and-drawing.md`), `TransitsTimeRangeFactory` transit events (see `references/predictive.md`), and the relationship score / house comparison factories (see `references/analysis.md`).
