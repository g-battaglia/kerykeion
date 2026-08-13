# Calendars, planetary hours and the Moon

Location/time utilities that need no natal chart (except the moon-phase
overview, which enriches an existing subject): moon-phase context, sunrise and
sunset, Chaldean planetary hours, and the void-of-course Moon. Sources:
`kerykeion/moon_phase_details/factory.py`, `kerykeion/sun_times/factory.py`,
`kerykeion/planetary_hours/factory.py`, `kerykeion/void_of_course_moon/factory.py`;
models in `kerykeion/schemas/models.py`. All factories and models named here are
top-level exports (`from kerykeion import ...`); the literals come from
`kerykeion.schemas` (e.g. `from kerykeion.schemas import LunarPhaseName`).

## MoonPhaseDetailsFactory

Classmethod `from_subject(subject, *, using_default_location=False,
location_precision=0)` → `MoonPhaseOverviewModel`. The two extras are
keyword-only metadata echoed into the result's `location` block.

Subjects carry `subject.lunar_phase` (`LunarPhaseModel`: `degrees_between_s_m`,
`moon_phase` int, `moon_emoji`, `moon_phase_name`) — but it is `None` when
`calculate_lunar_phase=False`, when Sun or Moon is not among the active points,
or in non-geo/topocentric perspectives (see `references/subjects.md`); guard
access. This factory builds a much richer, UI/API-oriented overview around
that instant:

- `MoonPhaseOverviewModel`: `timestamp` (Unix), `datestamp` (RFC-2822 style),
  `sun`, `moon`, `location`.
- `moon` (`MoonPhaseMoonSummaryModel`): `phase` (0–1 fraction of the cycle),
  `phase_name`, `major_phase` (nearest of the four quarters), `stage`
  (`"waxing"`/`"waning"`), `illumination` (e.g. `"51%"`), `age_days` /
  `age_days_precise` (days since last New Moon, exact ephemeris-based),
  `lunar_cycle`, `emoji`, `zodiac` (Sun/Moon signs), `next_lunar_eclipse`, and
  `detailed.upcoming_phases` — precise last/next instants for New Moon, First
  Quarter, Full Moon, Last Quarter (each with timestamp, datestamp and
  days_ago/days_ahead). `moonrise`/`moonset` fields exist but are not populated
  by this factory.
- `sun` (`MoonPhaseSunInfoModel`): `sunrise`, `sunset`, `solar_noon` as
  **subject-local** aware datetimes (unlike `SunTimesModel`, which is UTC),
  `day_length`, `position` (altitude/azimuth/distance), `next_solar_eclipse`.
  Fields degrade to `None` on polar day/night or missing location.

Literals (8 values each): `LunarPhaseEmoji` = 🌑 🌒 🌓 🌔 🌕 🌖 🌗 🌘;
`LunarPhaseName` = `"New Moon"`, `"Waxing Crescent"`, `"First Quarter"`,
`"Waxing Gibbous"`, `"Full Moon"`, `"Waning Gibbous"`, `"Last Quarter"`,
`"Waning Crescent"`.

```python
from kerykeion import AstrologicalSubjectFactory, MoonPhaseDetailsFactory
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT",
    online=False)
overview = MoonPhaseDetailsFactory.from_subject(subject)
m = overview.moon
print(m.phase_name, m.emoji, m.stage, m.illumination, m.age_days)
print(overview.sun.sunrise, overview.sun.day_length)   # subject-local tz
```

## SunTimesFactory

Classmethod `from_date(year, month, day, *, latitude, longitude, tz_str)` →
`SunTimesModel`. Location-only (no geolocation lookup, no subject); the civil
date is anchored to the IANA `tz_str`; keyword-only lat/lng/tz. Apparent
(refracted) upper-limb rise/set — the civil convention. Invalid tz or
out-of-range coordinates raise `KerykeionException`.

`SunTimesModel` — all instants timezone-aware **UTC** datetimes: `date`,
`timezone`, `latitude`, `longitude`, `sunrise`, `sunset`, `solar_noon`,
`day_length` (`timedelta`), `is_polar_day`, `is_polar_night`, plus twilight
pairs `civil_dawn`/`civil_dusk` (−6°), `nautical_dawn`/`nautical_dusk` (−12°),
`astronomical_dawn`/`astronomical_dusk` (−18°). Polar behavior: with no
sunrise→sunset pair, `day_length` is `None` and the matching polar flag is set,
but `solar_noon` is still reported (the Sun culminates even on a day it never
rises). On transition dates a paired sunset may fall past local midnight, so
`day_length` can exceed 24 hours.

## PlanetaryHoursFactory

Classmethod `from_datetime(year, month, day, hour, minute=0, *, latitude,
longitude, tz_str)` → `PlanetaryHoursModel`. A planetary day runs sunrise →
next sunrise: 12 equal day hours (sunrise→sunset) + 12 equal night hours
(sunset→next sunrise), generally unequal in length. Hour 1 is ruled by the
weekday planet (Monday→Moon, Tuesday→Mars, ...); each later hour steps down the
descending Chaldean order **Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon**,
cycling through all 24. A moment before the day's sunrise belongs to the
PREVIOUS planetary day (resolved automatically). Polar day/night raises
`KerykeionException` — planetary hours are undefined without a rise/set pair.

`PlanetaryHoursModel`: `date` (civil date of the day's sunrise), `timezone`,
`latitude`, `longitude`, `day_ruler`, `current_index` (1–24), `current_ruler`,
`sunrise`, `sunset`, `next_sunrise` (UTC), `hours` (24 × `PlanetaryHourModel`:
`index`, `ruler`, `is_diurnal`, `start`, `end` — UTC).

```python
from kerykeion import SunTimesFactory, PlanetaryHoursFactory
sun = SunTimesFactory.from_date(2024, 6, 21, latitude=41.9028,
                                longitude=12.4964, tz_str="Europe/Rome")
print(sun.sunrise, sun.solar_noon, sun.day_length, sun.civil_dawn)
ph = PlanetaryHoursFactory.from_datetime(2024, 6, 21, 11, 30,
    latitude=41.9028, longitude=12.4964, tz_str="Europe/Rome")
print(ph.day_ruler, ph.current_index, ph.current_ruler, len(ph.hours))
```

## VoidOfCourseMoonFactory

Classical VoC: the Moon is void from its last exact Ptolemaic aspect
(conjunction, sextile, square, trine, opposition) to a traditional planet (Sun,
Mercury, Venus, Mars, Jupiter, Saturn — outers intentionally excluded) while in
its current sign, until the next sign ingress. Geocentric longitudes only — no
observer location needed. Both zodiacs supported; aspect times are
zodiac-independent but sign boundaries (hence ingresses/windows) shift with the
ayanamsha; `sidereal_mode="USER"` rejected.

| Method (classmethod) | Signature → returns |
|---|---|
| `from_datetime` | `(year, month, day, hour, minute=0, *, tz_str, zodiac_type="Tropical", sidereal_mode=None)` → `VoidOfCourseMoonModel` |
| `from_iso_range` | `(start_date, end_date, *, zodiac_type="Tropical", sidereal_mode=None)` → `VoidOfCourseWindowsCollectionModel` |

`tz_str` is keyword-only and required — the clock time is civil local time.
`from_iso_range` follows the shared range convention (UTC; date-only end =
through end of that UTC day; malformed ISO → `KerykeionException`) and walks
the Moon sign by sign (~13.7 windows/month). Windows are **unclipped**: the
first may start before `start_date`, the last may end after `end_date`.

Models: `VoidOfCourseMoonModel` — `is_void_of_course`, `moon_sign`/`next_sign`
(3-letter `Sign` codes), `ingress` (== `void_end`), `void_start` (last in-sign
aspect, or sign entry for a whole-sign void), `void_end`, `last_aspect`,
`next_aspect` (first aspect after ingress; each `Optional`).
`VoidOfCourseWindowModel` — `moon_sign`, `next_sign`, `void_start`, `void_end`,
`duration_minutes`, `last_aspect` (`None` = whole-sign void).
`VoidOfCourseWindowsCollectionModel` — `start_jd`, `end_jd`, `windows`.
`VoidOfCourseAspectModel` — `planet: VocTargetPlanet`, `aspect: VocAspectName`,
`aspect_degrees` (0/60/90/120/180, validated against the name), `exact_time`
(UTC). Literals: `VocTargetPlanet` = the six traditional planets;
`VocAspectName` = the five Ptolemaic aspects.

```python
from kerykeion import VoidOfCourseMoonFactory
voc = VoidOfCourseMoonFactory.from_datetime(2024, 6, 21, 12, 0, tz_str="Europe/Rome")
print(voc.is_void_of_course, voc.moon_sign, voc.next_sign, voc.ingress)
wins = VoidOfCourseMoonFactory.from_iso_range("2024-06-01", "2024-06-07")
for w in wins.windows:
    print(w.moon_sign, "->", w.next_sign, round(w.duration_minutes, 1),
          w.last_aspect.aspect if w.last_aspect else "whole-sign void")
```

Cross-references: subject creation in `references/subjects.md`; lunations and
eclipses in `references/mundane-events.md`; sidereal modes in
`references/zodiac-houses-perspectives.md`.
