# Migration and deprecations (v5 → v6)

v6 removed the four v5 entry-point classes, renamed the schemas module, and — separately — changed calculation defaults so that even a correctly ported call produces different numbers. This file lists the removed names and their replacements, the result-level changes, the currently deprecated methods scheduled for removal in 7.0.0, and older v4 renames. Full guide: https://www.kerykeion.net/content/docs/migration. All snippets here show old API on purpose and are not runnable.

## The four removed names — ImportError, not AttributeError

`kerykeion/__init__.py` defines a PEP 562 module `__getattr__`: the names in `_V5_REMOVED_NAMES` raise **`ImportError`** with a migration message (plus the behaviour-changes note below, `_BEHAVIOUR_CHANGES_NOTE`). `ImportError` was chosen so `from kerykeion import AstrologicalSubject` surfaces the message verbatim instead of Python's generic "cannot import name".

| Removed (v5) | Replacement (v6) |
|---|---|
| `AstrologicalSubject` | `AstrologicalSubjectFactory.from_birth_data(...)` |
| `KerykeionChartSVG` | `ChartDataFactory.create_natal_chart_data(subject)` then `ChartDrawer(chart_data).generate_svg_string()` |
| `NatalAspects` | `AspectsFactory.single_chart_aspects(subject)` |
| `SynastryAspects` | `AspectsFactory.dual_chart_aspects(first_subject, second_subject)` |

```python
# doc-snippet: no-run  (v5 API — raises ImportError with the migration message)
from kerykeion import AstrologicalSubject          # ImportError
subject = AstrologicalSubject("John", 1990, 1, 1, 12, 0)
```

```python
# doc-snippet: no-run  (v6 replacement pattern)
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
subject = AstrologicalSubjectFactory.from_birth_data(...)
chart_data = ChartDataFactory.create_natal_chart_data(subject)
svg = ChartDrawer(chart_data).generate_svg_string()
```

### The `hasattr()` / `getattr(default)` trap

Because the removed names raise `ImportError` (not `AttributeError`), `hasattr(kerykeion, "AstrologicalSubject")` and `getattr(kerykeion, "AstrologicalSubject", None)` **also raise** instead of returning `False`/the default. Feature-detect with try/except:

```python
# doc-snippet: no-run
try:
    from kerykeion import AstrologicalSubject   # v5
    HAS_V5 = True
except ImportError:
    HAS_V5 = False                              # v6: use AstrologicalSubjectFactory
```

## Results changed too — porting the imports is not enough

v6 changed defaults that alter the OUTPUT of already-correct code (documented in the removal message itself):

- **Active points: 18 → 14.** `Descendant`, `Imum_Coeli`, `True_South_Lunar_Node`, `Mean_Lilith` are no longer in `DEFAULT_ACTIVE_POINTS`. Restore the old set with `V5_DEFAULT_ACTIVE_POINTS` (a frozen historical record, importable `from kerykeion.settings`):

```python
# doc-snippet: no-run
from kerykeion.settings import V5_DEFAULT_ACTIVE_POINTS
subject = AstrologicalSubjectFactory.from_birth_data(..., active_points=V5_DEFAULT_ACTIVE_POINTS)
```

- **Narrower orbs, fewer aspects.** Quintile dropped from the defaults; the v6 `DEFAULT_ACTIVE_ASPECTS` is conjunction 6° / opposition 6° / trine 6° / sextile 5° / square 6° (v5 used 10° conjunction/opposition), and transits/returns/progressions now use a flat 3° orb (`PREDICTIVE_ACTIVE_ASPECTS`). Expect FEWER aspects than v5; the migration guide lists the v5 aspect set. See `references/aspects-and-orbs.md`.
- **Chart style: `"classic"` → `"modern"`.** To keep the v5 wheel geometry pass `style="classic"` to `ChartDrawer` (the `theme` kwarg only controls the palette and already defaults to `"classic"`) — see `references/charts-and-drawing.md`.

To branch on library generation at runtime, prefer the try/except probe above (or `importlib.metadata.version("kerykeion")` / `kerykeion.__version__`) — never `hasattr`, for the reason given.

## `kerykeion.kr_types` is gone

The v5 module path `kerykeion.kr_types` (and `kr_types.kr_models` / `kr_types.kr_literals`) no longer exists in v6 — there is no shim; a clean install raises `ModuleNotFoundError`. Import models, literals, and `KerykeionException` from **`kerykeion.schemas`** (files `kerykeion/schemas/models.py`, `kerykeion/schemas/literals.py`):

```python
# doc-snippet: no-run
from kerykeion.kr_types import KerykeionException, AstrologicalSubjectModel   # v5 — ModuleNotFoundError
from kerykeion.schemas import KerykeionException, AstrologicalSubjectModel    # v6
```

## Deprecated now, removed in 7.0.0 (DeprecationWarning sites)

Every current `DeprecationWarning` in the package, each a working alias that warns and delegates:

| Deprecated | Where | Use instead |
|---|---|---|
| `AspectsFactory.natal_aspects(subject, ...)` | `kerykeion/aspects/factory.py` | `AspectsFactory.single_chart_aspects(subject, ...)` |
| `AspectsFactory.synastry_aspects(a, b, ...)` | `kerykeion/aspects/factory.py` | `AspectsFactory.dual_chart_aspects(a, b, ...)` |
| `PlanetaryReturnFactory.next_return_from_year(year, return_type)` | `kerykeion/planetary_returns/factory.py` | `next_return_from_date(year, 1, 1, return_type=...)` |
| `PlanetaryReturnFactory.next_return_from_month_and_year(year, month, return_type)` | `kerykeion/planetary_returns/factory.py` | `next_return_from_date(year, month, 1, return_type=...)` |
| `load_settings_mapping(...)` | `kerykeion/settings/loader.py` | `kerykeion.settings.translations.load_language_settings` |

```python
# doc-snippet: no-run  (deprecated return methods → replacement)
ret = factory.next_return_from_year(2025, "Solar")                 # warns
ret = factory.next_return_from_month_and_year(2025, 3, "Lunar")    # warns
ret = factory.next_return_from_date(2025, 3, 1, return_type="Lunar")  # v6 way
```

Notes:

- The two `AspectsFactory` aliases keep the modern keyword-only signature (`active_points`, `active_aspects`, `axis_orb_limit`) and delegate 1:1, so switching is a pure rename.
- The two `PlanetaryReturnFactory` aliases delegate to `next_return_from_date`, which additionally accepts `day` and keyword-only `backwards` — see `references/predictive.md`.
- `load_settings_mapping` is importable for compatibility but deliberately excluded from `kerykeion.settings.__all__` (born deprecated; a new major does not freeze dead API).

## Deep module paths are not stable

Public API lives in the top-level `kerykeion` namespace (plus documented subpackage imports like `kerykeion.settings` and `kerykeion.geonames`). v6's package-layout refactor turned former modules into subpackages (e.g. the subject factory now lives at `kerykeion/astrological_subject/factory.py`, the chart renderer at `kerykeion/charts/drawer.py`), so any v5-era deep import path found in old code should be replaced with the top-level import, not "fixed" path-by-path.

## v4 → v6 renames

Old v4 spellings, long gone but still common in found code:

| v4 | v6 |
|---|---|
| `nat` kwarg | `nation` |
| `subject.mean_node` | `subject.mean_north_lunar_node` (`active_points` name `Mean_North_Lunar_Node`) |
| `subject.true_node` | `subject.true_north_lunar_node` (`active_points` name `True_North_Lunar_Node`) |

South nodes are separate points (`Mean_South_Lunar_Node`, `True_South_Lunar_Node`), no longer implied by the north node. Fixed-star point access also moved: v5 typed per-star fields (e.g. `subject.regulus`) are gone — stars live in the `subject.fixed_stars` list, looked up with `subject.find_fixed_star("Regulus")`.

## Migration checklist

1. Replace the four removed classes per the table above (the `ImportError` message itself contains the replacement).
2. Decide whether you need v5-identical RESULTS; if yes, pass `V5_DEFAULT_ACTIVE_POINTS`, the v5 aspect list from the guide, and the classic chart theme.
3. Point `kr_types` imports at `kerykeion.schemas`.
4. Silence 7.0.0 removals by switching to the replacements in the DeprecationWarning table.
5. Fixed stars moved out of `active_points` into `active_fixed_stars` — v5-style star names in `active_points` still work but are redirected with a warning; see `references/subjects.md`.

Guide: https://www.kerykeion.net/content/docs/migration
