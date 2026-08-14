# Locational techniques

Relocation (same instant, new place) and astro-cartography (planetary angle
lines across the globe). Both are top-level exports of `kerykeion`. Sources:
`kerykeion/relocated_chart/factory.py`, `kerykeion/astro_cartography/factory.py`.

## RelocatedChartFactory — recast houses for a new place

`RelocatedChartFactory.relocate(subject, new_lat, new_lng, new_city="Relocated", new_nation="", new_tz_str=None)` → `AstrologicalSubjectModel`

Static method; the location parameters are positional. `new_nation=""` falls
back to `subject.nation`; `new_tz_str=None` keeps the original `tz_str`.

Semantics — the UTC instant and `julian_day` are unchanged:

- **Unchanged:** every planetary position (identical `abs_pos`), zodiac,
  sidereal mode, provenance fields of the points.
- **Recomputed:** the twelve cusps and ASC/MC/DSC/IC for `new_lat`/`new_lng`
  (same house system; sidereal cusps shifted by the subject's stored
  `ayanamsa_value`); Vertex/Anti-Vertex; `is_diurnal` (sect follows the new
  horizon and can flip); essential dignities when the natal subject carried
  them; the Ascendant-based Arabic parts with the day/night formula re-selected
  from the new sect — the relocated lots keep the natal part's provenance
  fields (`source`, `precision_class`, coverage window) since relocation moves
  houses, not planetary primaries. Every non-axial point (including fixed stars
  and active midpoints) is reassigned to its new house.
- **Reset to `None` (not recomputed):** per-point `azimuth`,
  `altitude_above_horizon`, `gauquelin_sector`, and the subject-level
  `gauquelin_sector_cusps` — they described the natal horizon.
- **Replaced:** `polar_house_fallbacks` records only the relocated house call
  (relocating into a polar latitude may substitute the house system; the
  requested one stays in `houses_system_identifier`).
- Local date fields (`year`…`seconds`, `iso_formatted_local_datetime`,
  `day_of_week`) are recomputed only when `new_tz_str` is given (always for
  BCE subjects, which use Local Mean Time from the new longitude).

Raises `KerykeionException` for a `"Topocentric"` subject (its planet positions
embed the natal observer's parallax — re-create the subject at the new
coordinates instead), for `|lat| > 90`, or when the new local wall time would
leave the representable range. Longitudes outside [-180, 180) are wrapped.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion import RelocatedChartFactory
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT",
    online=False)
ny = RelocatedChartFactory.relocate(
    subject, 40.7128, -74.0060, new_city="New York", new_nation="US",
    new_tz_str="America/New_York")
print(subject.ascendant.sign, "->", ny.ascendant.sign)   # Vir -> Can
print(subject.sun.abs_pos == ny.sun.abs_pos, ny.hour)    # True 4
```

## AstroCartographyFactory — ACG lines

`AstroCartographyFactory.compute(subject, *, step=1.0, tolerance=None, lat_range=(-66, 66), planets=None)` → `List[ACGLineModel]`

| Kwarg | Default | Meaning |
|---|---|---|
| `step` | `1.0` | Latitude scan step in degrees; must be finite and > 0 |
| `tolerance` | `None` | **Unused since v6** (horizon equation solved exactly); accepted for backward compatibility |
| `lat_range` | `(-66, 66)` | `(min, max)` within −90…90, min ≤ max |
| `planets` | `None` | Subset of Sun…Pluto (10 bodies); `None` → all; unknown names or a bare string raise |

Lines are computed **in mundo** from true equatorial coordinates: tropical and
sidereal charts of the same instant produce identical lines, and bodies with
ecliptic latitude land where Jim Lewis / astro.com maps draw them. Geometric
horizon, no refraction. Per planet the result holds an MC and an IC line
(vertical meridians over the full latitude grid) and, when the body crosses the
horizon at some scanned latitude, an ASC and a DSC line; circumpolar latitudes
contribute no ASC/DSC points. Planets missing from the subject are skipped
(empty selection returns `[]`). Guards: a grid projecting more than
`MAX_PROJECTED_POINTS` (1,000,000) points raises, as do malformed
`step`/`lat_range`/`planets` and a midpoint composite (`julian_day` is `None`).

Models (also importable from `kerykeion.astro_cartography`):

- `ACGLineModel`: `planet: str`, `line_type: Literal["ASC", "DSC", "MC", "IC"]`,
  `points: List[ACGLinePointModel]`.
- `ACGLinePointModel`: `longitude: float` (−180…180), `latitude: float`.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion import AstroCartographyFactory
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT",
    online=False)
lines = AstroCartographyFactory.compute(
    subject, step=5.0, planets=["Sun", "Moon", "Jupiter"])
print(len(lines))                                    # 12 (4 line types x 3)
sun_mc = next(l for l in lines if l.planet == "Sun" and l.line_type == "MC")
print(round(sun_mc.points[0].longitude, 1))          # constant lng meridian
```

Relocating onto a line: pick a coordinate from an `ACGLineModel` and feed it to
`RelocatedChartFactory.relocate` to inspect the chart there. For subject
construction flags see `references/subjects.md`; for rendering a relocated
chart see `references/charts-and-drawing.md`.
