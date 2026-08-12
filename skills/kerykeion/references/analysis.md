# Analysis: dominants, relationship score, house comparison, midpoints

Chart-analysis factories that post-process already-built `AstrologicalSubjectModel` objects.
Sources: `kerykeion/dominants/`, `kerykeion/relationship_score/factory.py`,
`kerykeion/house_comparison/`, `kerykeion/midpoints/factory.py`. All four factories and
their main models are exported from the top-level `kerykeion` namespace; strategy
internals need subpackage imports (labeled below).

## DominantsFactory — dominant planet/sign/element/quality

Package: `kerykeion/dominants/`. Three built-in "schools" selected via the `strategy`
kwarg, plus a Protocol-based extension point.

- **`DominantsFactory.from_subject(subject, *, strategy="modern", active_points=None, distribution_method="weighted", custom_weights=None, include_accidental_dignities=False, include_score_breakdown=False)`** → `DominantsModel`
- **`DominantsFactory.from_birth_data(name, year, month, day, hour=12, minute=0, *, strategy=..., <same kwargs>, **subject_kwargs)`** — builds the subject first; `subject_kwargs` (e.g. `lat`, `lng`, `tz_str`, `online`) forwarded to `AstrologicalSubjectFactory.from_birth_data`
- **`DominantsFactory.available_methods()`** → `['almuten_figuris', 'elemental', 'modern']`

| kwarg | default | notes |
|---|---|---|
| `strategy` | `"modern"` | `DominantMethod` name or a `DominantStrategy` instance; unknown values raise `KerykeionException` |
| `active_points` | `None` | explicit subset of point names (honoured by the `elemental` school); `None` → the subject's own `active_points` |
| `distribution_method` | `"weighted"` | `DistributionMethod = Literal["pure_count", "weighted"]` for the element/modality tally |
| `custom_weights` | `None` | per-point weight overrides, case-insensitive names (element/modality tally) |
| `include_accidental_dignities` | `False` | Almuten Figuris only: adds house placement / day-ruler layer |
| `include_score_breakdown` | `False` | populates `score_breakdown` audit trail |

`DominantMethod = Literal["modern", "almuten_figuris", "elemental"]` (top-level export).
What each school populates:

| method | populated categories | notes |
|---|---|---|
| `modern` | all 8 (planets, signs, elements, qualities, houses, polarities, hemispheres, quadrants) | Astrotheme-style: angularity + aspects + dignity + rulership per planet |
| `almuten_figuris` | `planets` (7 classical, ranked by dignity totals) + single-entry winner placement categories | traditional Lord of the Geniture; traditionally tropical |
| `elemental` | `elements`, `qualities`, `polarities` only | weighted or pure count; other categories empty, `dominant_planet` is `None` |

Models (top-level exports): `DominantsModel` — fixed school-agnostic shape:
`strategy_name`, `method` (`None` for custom strategies), the 8 category lists of
`DominantScoreModel` (`name`, `score`, `percentage` — normalized to ~100 per category,
`rank` — 1-based, `is_dominant`), convenience winners `dominant_planet`, `dominant_sign`,
`dominant_element`, `dominant_quality`, `dominant_house` (each `None` when its category is
empty), and `score_breakdown` (list of `DominantBreakdownItemModel`: `category`, `target`,
`rule`, `points`, `detail` — only populated with `include_score_breakdown=True`).

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion import DominantsFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
print(DominantsFactory.available_methods())
for method in ("modern", "almuten_figuris", "elemental"):
    result = DominantsFactory.from_subject(subject, strategy=method)
    print(method, result.dominant_planet, result.dominant_element, result.dominant_quality)
```

### Custom strategies (extension contract)

`DominantStrategy` is a runtime-checkable `typing.Protocol`: any object with a `name: str`
attribute and `compute(subject, config) -> DominantsModel` qualifies — pass the instance as
`strategy=`. `BaseDominantStrategy` is an optional base class providing `build_model(...)`
(ranking, percentage normalization, winner selection). Both are top-level exports.

**Subpackage import:** `from kerykeion.dominants import DominantsConfig, ModernDominantStrategy, AlmutenFigurisStrategy, ElementalBalanceStrategy, Category, BreakdownItem`
**Subpackage import:** `from kerykeion.dominants.base import DistributionMethod`

`DominantsConfig` is the dataclass the factory hands to `compute` (fields mirror the
`from_subject` kwargs plus `dominant_planet_count`, default 2). `Category` (raw
`scores`/`dominant`/`tiebreak_order`) and `BreakdownItem` are the plain-dataclass value
objects a custom school feeds to `build_model`.

```python
# doc-snippet: no-run
from kerykeion import DominantsFactory
from kerykeion.dominants import BaseDominantStrategy, Category

class MySchool(BaseDominantStrategy):
    name = "my_school"
    def compute(self, subject, config):
        scores = {"Sun": 2.0, "Moon": 1.0}          # your scoring logic
        return self.build_model(
            categories={"planets": Category(scores=scores, dominant={"Sun"})})

result = DominantsFactory.from_subject(subject, strategy=MySchool())
```

## RelationshipScoreFactory — Discepolo synastry score

Package: `kerykeion/relationship_score/`. Ciro Discepolo's method: weighted synastry
aspects between two natal charts.

Constructor: `RelationshipScoreFactory(first_subject, second_subject, use_only_major_aspects=True, *, axis_orb_limit=None)`.
The two subjects MUST share the same reference frame (zodiac type, sidereal mode,
perspective) — mixed frames raise `KerykeionException` at construction. Aspects are computed
with Discepolo's own fixed orb set (not the UI defaults). `axis_orb_limit` optionally
discards axis aspects at/above the threshold.

**`get_relationship_score()`** → `RelationshipScoreModel`: `score_value` (int),
`score_description` (`RelationshipScoreDescription`), `is_destiny_sign` (both Suns in the
same quality/mode group), `aspects` (list of `RelationshipScoreAspectModel`: `p1_name`,
`p2_name`, `aspect`, `orbit`), `score_breakdown` (list of `ScoreBreakdownItemModel`: `rule`,
`description`, `points`, `details`), `subjects`. Subjects built without the Sun raise
`KerykeionException`.

`RelationshipScoreDescription` — 6 tiers (import from `kerykeion.schemas`):

| score | tier |
|---|---|
| < 5 | `"Minimal"` |
| 5–10 | `"Medium"` |
| 10–15 | `"Important"` |
| 15–20 | `"Very Important"` |
| 20–30 | `"Exceptional"` |
| >= 30 | `"Rare Exceptional"` |

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion import RelationshipScoreFactory

a = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
b = AstrologicalSubjectFactory.from_birth_data(
    name="Second Person", year=1992, month=3, day=21, hour=8, minute=15,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
score = RelationshipScoreFactory(a, b).get_relationship_score()
print(score.score_value, score.score_description, score.is_destiny_sign)
print(len(score.aspects), len(score.score_breakdown))
```

## HouseComparisonFactory — bidirectional house overlays

Package: `kerykeion/house_comparison/`. Where each subject's points (and cusps) fall in the
OTHER subject's houses — the synastry "your Sun in my 7th house" analysis.

Constructor: `HouseComparisonFactory(first_subject, second_subject, active_points=DEFAULT_ACTIVE_POINTS)`.
Subjects can be `AstrologicalSubjectModel` or `PlanetReturnModel` (natal-vs-return overlays
work). Same-frame check as above (`KerykeionException` on mismatch); house SYSTEMS may
legitimately differ.

**`get_house_comparison()`** → `HouseComparisonModel`: `first_subject_name`,
`second_subject_name`, `first_points_in_second_houses`, `second_points_in_first_houses`,
`first_cusps_in_second_houses`, `second_cusps_in_first_houses` — all four lists of
`PointInHouseModel` (import from `kerykeion.schemas`): `point_name`, `point_degree` (within
sign), `point_sign`, `point_owner_name`, `point_owner_house_number/_name` (Optional),
`projected_house_number`, `projected_house_name`, `projected_house_owner_name`.

Helper functions (public, `kerykeion/house_comparison/utils.py`, not re-exported top-level):
`calculate_points_in_reciprocal_houses(point_subject, house_subject, active_points=DEFAULT_ACTIVE_POINTS)`
and `calculate_cusps_in_reciprocal_houses(cusp_subject, house_subject)` — each one direction,
returning `list[PointInHouseModel]`.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion import HouseComparisonFactory

a = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
b = AstrologicalSubjectFactory.from_birth_data(
    name="Second Person", year=1992, month=3, day=21, hour=8, minute=15,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
comparison = HouseComparisonFactory(a, b).get_house_comparison()
first = comparison.first_points_in_second_houses[0]
print(first.point_name, first.projected_house_number, first.projected_house_name)
print(len(comparison.first_cusps_in_second_houses))   # 12
```

## MidpointFactory — cosmobiology midpoints

Package: `kerykeion/midpoints/`. Shorter-arc midpoints of every unordered pair of active
points, with 90° dial positions and optional aspect activations.

- **`MidpointFactory.compute(subject, *, active_points=None, compute_aspects=True, aspect_orb=1.0, aspects=None)`** → `list[MidpointModel]`, one per pair, in deterministic input order. `active_points` defaults to `DEFAULT_PREDICTIVE_POINTS` (10 planets + True Node, Chiron, Asc, MC → 91 pairs); `aspects=None` allows every aspect in `DEFAULT_CHART_ASPECTS_SETTINGS` — pass a whitelist like `("conjunction", "opposition", "square")` for dial work.
- **`MidpointFactory.compute_active_midpoint_points(subject, pair_names)`** → `list[KerykeionPointModel]` with `name="A_B_Midpoint"`, `point_type="Midpoint"`, house assigned from the natal cusps. `pair_names` use the `"A_B"` form (`"Sun_Moon"`, `"Sun_True_North_Lunar_Node"`); pairs that do not resolve against `subject.active_points` are skipped with a warning. Used to render midpoints on charts (see `references/charts-and-drawing.md`).

`MidpointModel` fields: `point_a`, `point_b`, `point_a_abs_pos`, `point_b_abs_pos`,
`midpoint_abs_pos` (shorter arc), `midpoint_sign` (3-letter code), `midpoint_position`
(0–30 in sign), `midpoint_modulus_90` (90° dial), `aspects_to_midpoint` (list of
`MidpointAspectModel`: `point_name`, `point_abs_pos`, `aspect`, `aspect_degrees`, `orb` —
third points only, the two constituents are excluded).

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion import MidpointFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT", online=False)
midpoints = MidpointFactory.compute(
    subject, active_points=["Sun", "Moon", "Venus", "Mars"], aspect_orb=1.0)
print(len(midpoints))                                 # 6 pairs
m = midpoints[0]
print(m.point_a, m.point_b, m.midpoint_sign, round(m.midpoint_modulus_90, 2))
for a in m.aspects_to_midpoint:
    print(" ", a.point_name, a.aspect, round(a.orb, 2))
```

## Related

`TriplicityLordsModel` (top-level export) is the Dorothean triplicity-lords result
(`element`, `sect`, `primary` in-sect lord, `secondary`, `participating`) produced by
`get_triplicity_lords(element, is_diurnal)` in `kerykeion/dignities/` — see
`references/traditional.md`. Element/quality distribution models used by chart data live in
`references/charts-and-drawing.md`; synastry aspect grids in `references/aspects-and-orbs.md`.
