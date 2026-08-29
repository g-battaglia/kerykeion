# Utilities

Public helpers of `kerykeion.utilities` (a flat facade: `kerykeion/utilities/__init__.py`
re-exports everything from `kerykeion/utilities/core.py`), plus the motion-state
classifier from `kerykeion.motion`. **Subpackage import:** `from kerykeion.utilities
import wrap_180` — none of these names are in `kerykeion.__all__`, so `from kerykeion
import wrap_180` fails. The facade's `__all__` lists 47 functions and 2 constants;
underscore-prefixed re-exports are internal, do not use them.

## Validation and normalization

| Name | Signature | Purpose |
|---|---|---|
| `validate_latitude` | `(latitude: float) -> float` | Raise `KerykeionException` outside [-90, 90]; returns the value UNCHANGED (no polar clamp) |
| `validate_longitude` | `(longitude: float) -> float` | Raise `KerykeionException` outside [-180, 180]; no wrapping |
| `check_and_adjust_polar_latitude` | `(latitude: float) -> float` | Clamp to ±66° for house stability. NARROW USE (Gauquelin sectors); not a general polar fallback |
| `normalize_longitude` | `(longitude: float) -> float` | Wrap a geographic longitude into [-180, 180); in-range values returned bit-identical |
| `normalize_zodiac_type` | `(value: str) -> ZodiacType` | Case-insensitive → `"Tropical"`/`"Sidereal"` (legacy `"tropic"` accepted); else `ValueError` |

## Julian Day and ISO time (BCE-safe)

Two families, do not mix: `datetime_to_julian`/`julian_to_datetime` are proleptic
Gregorian for ALL dates and round-trip exactly (CE only); `civil_jd`/`jd_to_iso_*`
mirror the subject factory's asymmetric convention (Julian calendar for year < 1,
proleptic Gregorian from 1 CE) and handle BCE.

| Name | Signature | Purpose |
|---|---|---|
| `datetime_to_julian` | `(dt: datetime) -> float` | JD from datetime; aware → UTC first, naive = UT |
| `julian_to_datetime` | `(jd: float) -> datetime` | Inverse of the above; `ValueError` for JD before 1 CE |
| `civil_jd` | `(year, month, day, hour: float = 0.0) -> float` | JD of a civil moment, factory calendar convention; overflowing components roll over (Feb 29 → Mar 1) |
| `jd_to_iso_date` | `(jd: float) -> str` | `YYYY-MM-DD`, astronomical year numbering (0 = 1 BCE) |
| `jd_to_iso_datetime` | `(jd: float) -> str` | `...THH:MM:SS`, rounded half-up to the second |
| `civil_leap_year` | `(year: int) -> bool` | Leap rule of the convention (Julian < 1 CE, Gregorian ≥ 1 CE) |
| `format_astronomical_iso_date` | `(year, month, day) -> str` | Zero-padded ISO date, negative years allowed |
| `format_ancient_iso` | `(year, month, day, decimal_hour, utc_offset_hours) -> str` | Full ISO string with extended year and offset, e.g. `-0500-03-21T12:00:00+01:35` |
| `parse_astronomical_iso_moment` | `(value: str) -> tuple[int, int, int, float]` | Parse naive ISO date/datetime incl. negative years → `(y, m, d, hour_float)`; tz-aware or impossible dates raise `KerykeionException` |
| `extract_year_from_iso` | `(iso_datetime_string: str) -> int` | Year incl. BCE (`-0500...` → -500, `0000...` → 0) |
| `format_iso_display` | `(iso_datetime_string, fmt: str = "%Y-%m-%d %H:%M") -> str` | Display-format an ISO string, BCE tolerated |

```python
from datetime import datetime
from kerykeion.utilities import datetime_to_julian, julian_to_datetime, civil_jd, jd_to_iso_date
jd = datetime_to_julian(datetime(1990, 7, 15, 8, 30))    # naive = UT
assert abs(jd - civil_jd(1990, 7, 15, 8.5)) < 1e-6
back = julian_to_datetime(jd)                            # sub-second float error
assert abs((back - datetime(1990, 7, 15, 8, 30)).total_seconds()) < 0.001
print(jd, jd_to_iso_date(jd))                            # 2448087.854... 1990-07-15
```

## Timezone and DST

| Name | Signature | Purpose |
|---|---|---|
| `safe_timezone` | `(tz_str: str) -> ZoneInfo` | Resolve an IANA key; every failure mode wrapped as `KerykeionException` |
| `is_nonexistent` | `(naive: datetime, tz: tzinfo) -> bool` | Wall time inside a spring-forward gap. Test BEFORE `is_ambiguous` |
| `is_ambiguous` | `(naive: datetime, tz: tzinfo) -> bool` | Wall time that occurred twice (fall-back); gaps excluded |
| `localize_naive` | `(naive, tz, *, is_dst: Optional[bool] = None) -> datetime` | Attach tz. `is_dst=True` → larger UTC offset, `False` → smaller, `None` → raise `KerykeionException` on gap/fold (except pre-1902, which resolves to the pre-transition offset) |

```python
from datetime import datetime
from zoneinfo import ZoneInfo
from kerykeion.utilities import is_nonexistent, is_ambiguous, localize_naive
tz = ZoneInfo("Europe/Rome")
gap = datetime(2024, 3, 31, 2, 30)                 # clocks jumped 02:00 -> 03:00
print(is_nonexistent(gap, tz), is_ambiguous(gap, tz))   # True False
try:
    localize_naive(gap, tz)                        # is_dst=None on a gap -> raises
except Exception as exc:
    print(type(exc).__name__)                      # KerykeionException
print(localize_naive(gap, tz, is_dst=True).utcoffset())  # 2:00:00
```

## Angle arithmetic

| Name | Signature | Purpose |
|---|---|---|
| `wrap_180` | `(angle) -> float` | Into [-180, 180); use for signed differences `wrap_180(a - b)` |
| `circular_mean` | `(first_position, second_position) -> float` | Shorter-arc midpoint in [0, 360); antipodal pair resolved as plain average |
| `circular_sort` | `(degrees: list) -> list` | Clockwise order starting from the first element; empty/non-numeric → `ValueError` |
| `is_point_between` | `(start_angle, end_angle, candidate, *, allow_reflex: bool = False) -> bool` | Start-inclusive, end-exclusive arc test; span > 180° raises unless `allow_reflex=True` |

## Chart and point lookups

| Name | Signature | Purpose |
|---|---|---|
| `get_kerykeion_point_from_degree` | `(degree, name, point_type, speed=None, declination=None, magnitude=None, ecliptic_latitude=None) -> KerykeionPointModel` | Build a point from a longitude; finite degrees wrapped into [0, 360), non-finite raise |
| `get_planet_house` | `(planet_degree, houses_degree_ut_list: list) -> Houses` | House containing a longitude (12 cusp degrees in). Direction-aware: several house systems return descending cusps above the polar circle |
| `house_spans` | `(cusps: Sequence[float]) -> tuple[list[float], list[bool]]` | The twelve house widths and which run against the frame given. Six systems reverse above ~68°, two cross |
| `normalize_degree` | `(angle: float) -> float` | Into [0, 360). Use instead of `% 360`, which answers exactly 360.0 for a hair-negative angle; propagates NaN |
| `get_house_name` | `(house_number: int) -> Houses` | 1–12 → `"First_House"`...; else `ValueError` |
| `get_house_number` | `(house_name: Houses) -> int` | Inverse of the above |
| `get_number_from_name` | `(name: AstrologicalPoint) -> int` | Point name → ephemeris body id; unknown → `KerykeionException` |
| `get_houses_list` | `(subject) -> list[KerykeionPointModel]` | The 12 cusps in order (subject, composite or return model) |
| `get_available_astrological_points_list` | `(subject) -> list[KerykeionPointModel]` | The subject's `active_points` as models |
| `find_common_active_points` | `(first_points, second_points) -> list[AstrologicalPoint]` | Intersection, deduplicated, in `first_points` order |
| `HOUSE_FIELD_NAMES` | `tuple[str, ...]` | The 12 lowercase house attribute names (`"first_house"`, ...) |

## Subject frame and sect helpers

| Name | Signature | Purpose |
|---|---|---|
| `resolve_sect_is_diurnal` | `(subject) -> bool` | `subject.is_diurnal` with missing/`None` → `True` (day-chart default) |
| `resolve_subject_birth_datetime` | `(subject) -> datetime` | Naive local birth moment; ISO fallback for return/Davison models; midpoint composites raise `KerykeionException` |
| `resolve_subject_local_moment` | `(subject) -> tuple[int, int, int, float]` | Same, as components — BCE-safe (no `datetime` built) |
| `resolve_subject_local_now` | `(subject) -> datetime` | "Now" in the subject's timezone, naive; UTC fallback |
| `has_terrestrial_frame` | `(subject) -> bool` | Perspective in `TERRESTRIAL_PERSPECTIVES` (missing attribute → trusted True) |
| `require_same_frame` | `(first, second) -> None` | Raise `KerykeionException` unless both share zodiac_type/perspective_type (+ sidereal_mode and custom ayanamsa when Sidereal) |
| `TERRESTRIAL_PERSPECTIVES` | `frozenset[str]` | `{"Apparent Geocentric", "True Geocentric", "Topocentric"}` |

## Moon phase

| Name | Signature | Purpose |
|---|---|---|
| `calculate_moon_phase` | `(moon_abs_pos: float, sun_abs_pos: float) -> LunarPhaseModel` | Full `LunarPhaseModel` from two longitudes: `degrees_between_s_m`, `moon_phase` (1–28), `moon_emoji`, `moon_phase_name`, `major_phase`, `stage` |
| `get_moon_emoji_from_phase_int` | `(phase: int) -> LunarPhaseEmoji` | Phase 1–28 → emoji; out of range raises `KerykeionException` |
| `get_moon_phase_name_from_phase_int` | `(phase: int) -> LunarPhaseName` | Phase 1–28 → name (e.g. `"Full Moon"`) |

`moon_phase_name` and `moon_emoji` come from windows **centred on the syzygies**:
New and Full span ±6.4286° of the exact aspect, the two quarters ±19.2857°, and
the four crescent/gibbous names fill the rest. The name therefore tracks the
event — "Full Moon" means near the opposition, not merely inside bin 15. The
`moon_phase` index (1–28) is unchanged. `major_phase` is the nearest of the four
syzygies and `stage` is `"waxing"` or `"waning"`.

The two `*_from_phase_int` helpers take only the 1–28 index, so they cannot use
those windows: they are the older 28-bin approximation, kept for callers that
have an index and nothing else, and they disagree with the model's own
`moon_phase_name` near a boundary. Read the fields off `LunarPhaseModel` when
you have it.

## Formatting and misc

| Name | Signature | Purpose |
|---|---|---|
| `setup_logging` | `(level: str) -> None` | Configure root logger; `"debug"`/`"info"`/`"warning"`/`"error"`/`"critical"`, invalid → INFO |
| `strip_illegal_control_chars` | `(value) -> str` | Drop XML-1.0-illegal / terminal-control chars from untrusted strings |
| `format_degrees_below_bound` | `(value, upper_bound, decimals: int = 2) -> str` | Round without crossing the cusp (never prints `"30.00"`/`"360.00"`) |
| `format_timedelta_hhmm` | `(td: timedelta) -> str` | `H:MM`, half-up to whole minutes |
| `inline_css_variables_in_svg` | `(svg_content: str) -> str` | Inline `var(...)` values and strip `<style>` blocks (for SVG consumers without CSS-variable support) |
| `distribute_percentages_to_100` | `(values: dict[str, float]) -> dict[str, int]` | Largest-remainder rounding to integer percentages summing to exactly 100 |

## Motion state (`kerykeion.motion`)

**Subpackage import:** `from kerykeion.motion import classify_motion_state`.

`classify_motion_state(point_name: str, speed: Optional[float]) -> Optional[MotionState]`
— `MotionState = Literal["retrograde", "stationary", "slow", "average", "fast"]`;
returns `None` for bodies without a tabulated mean motion (nodes, asteroids,
fixed stars, cusps) or unknown speed. Also exported: `MEAN_DAILY_MOTION_DEGREES`
(dict of mean motions), thresholds `STATIONARY_FRACTION` (0.05), `SLOW_FRACTION`
(0.8), `FAST_FRACTION` (1.2), and the `MotionState` alias. Subjects already
carry `point.motion_state` when computed; call this only for raw speeds.

## Solar-phase classifier (`kerykeion.planetary_phenomena.factory`)

**Module import** (not in the subpackage's `__all__`): `from
kerykeion.planetary_phenomena.factory import classify_solar_phase`.

`classify_solar_phase(elongation: float, thresholds: SolarPhaseThresholdsModel)
-> SolarPhase` — names a body's condition near the Sun: `"cazimi"`, `"combust"`,
`"under_the_beams"`, `"free"`. The cut-offs are walked from the inside out and
every comparison is strict, so a body exactly on one takes the outer name.
`elongation` is the TRUE angular separation the ephemeris reports (latitude
included), not the difference in ecliptic longitude. `SolarPhaseThresholdsModel`
and the `SolarPhase` literal come from `kerykeion.schemas`; the defaults are
0.2833° / 8.5° / 17°, and the model rejects a set that does not widen outwards.
`PlanetaryPhenomenaFactory` already fills `solar_phase` per body — call this
only for a raw elongation.

```python
from kerykeion.planetary_phenomena.factory import classify_solar_phase
from kerykeion.schemas import SolarPhaseThresholdsModel

t = SolarPhaseThresholdsModel()
print(classify_solar_phase(0.1, t), classify_solar_phase(20.0, t))
# cazimi free
```

## Rise and set (`kerykeion.moon_phase_details.utils`)

**Module import** (not in the subpackage's `__all__`, but in the module's):
`from kerykeion.moon_phase_details.utils import compute_rise_set_ephe`.

`compute_rise_set_ephe(jd_midnight: float, latitude: float, longitude: float,
body: Optional[int] = None) -> tuple[Optional[float], Optional[float]]` —
`(rise_jd, set_jd)` from the backend's `rise_trans`: refracted upper limb,
standard atmosphere, topocentric parallax for the Moon. `body` defaults to
`ephe.SUN`, resolved at call time; pass `ephe.MOON` for moonrise/moonset. The
Julian Day is local midnight expressed in UT, and each result is the NEXT event
after it — for the Moon that routinely falls on the following civil day, so the
caller must window it itself. `None` where the backend finds no event (polar
day/night). `compute_sun_rise_set_ephe(jd_midnight, latitude, longitude)` is the
unchanged Sun-only alias, kept for existing callers and patch targets. Call
inside an open `ephemeris_session()` — the helper mutates the global ephemeris
path. `MoonPhaseDetailsFactory` already does all of this; see
`references/calendars-hours-moon.md`.

Cross-references: provenance/backends in `references/backends-and-provenance.md`;
polar-house behavior in `references/zodiac-houses-perspectives.md`; the moon-phase
factory in `references/calendars-hours-moon.md`.
