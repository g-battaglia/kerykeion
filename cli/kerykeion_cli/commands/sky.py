# -*- coding: utf-8 -*-
"""``kerykeion sky <sub>`` — astronomical events (sun, moon, planets).

Moment commands (``sun-times``, ``hours``) take one date/time and a place —
inline ``--lat/--lng/--tz`` or from ``-s <profile>``; range commands
(``lunations``, ``ingresses``, ``stations``, ``mundane``, ``voc --to``) take
``--from``/``--to`` and no place; ``voc`` without ``--to`` and ``eclipses``
straddle the two.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional, overload

from kerykeion_cli import subject_resolver
from kerykeion_cli.commands._shared import _aspect_names, _emit, _given, _parse_aspects, _parse_dt, _split_csv
from kerykeion_cli.options import (
    AspectsOpt,
    CountOpt,
    FormatOpt,
    FromOpt,
    OutputOpt,
    PeriodsFlag,
    PhaseOpt,
    PlanetIdOpt,
    PlanetsOpt,
    SiderealSkyOpt,
    StartYearOpt,
    SubjectLat,
    SubjectLng,
    SubjectProfile,
    SubjectTz,
    ToOpt,
    ZodiacSkyOpt,
)



def _zodiac_kwargs(zodiac: Optional[str], sidereal_mode: Optional[str]) -> dict[str, Any]:
    """``--zodiac``/``--sidereal-mode`` as factory kwargs, spelled the way the library itself normalises them."""
    kwargs = _given(sidereal_mode=sidereal_mode)
    if zodiac is not None:
        from kerykeion.utilities import normalize_zodiac_type

        try:
            kwargs["zodiac_type"] = normalize_zodiac_type(zodiac)
        except ValueError:
            raise ValueError("--zodiac must be Tropical or Sidereal") from None
    return kwargs


@overload
def _location(
    profile: Optional[str], lat: Optional[float], lng: Optional[float], tz: Optional[str], cmd: str
) -> tuple[float, float, str]: ...


@overload
def _location(
    profile: Optional[str],
    lat: Optional[float],
    lng: Optional[float],
    tz: Optional[str],
    cmd: str,
    *,
    require_tz: Literal[False],
) -> tuple[float, float, Optional[str]]: ...


def _location(
    profile: Optional[str],
    lat: Optional[float],
    lng: Optional[float],
    tz: Optional[str],
    cmd: str,
    *,
    require_tz: bool = True,
) -> tuple[float, float, Optional[str]]:
    """A place from the inline flags first, then the profile (an explicit value wins, as in ``transit``).

    ``require_tz=False`` serves the commands that take no timezone (``eclipses``,
    ``occultations``). A fully inline place never materialises the profile.
    """
    wanted = ("--lat", "--lng", "--tz") if require_tz else ("--lat", "--lng")
    if lat is not None and lng is not None and (tz is not None or not require_tz):
        return lat, lng, tz
    if profile:
        subject = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile)
        lat = lat if lat is not None else getattr(subject, "lat", None)
        lng = lng if lng is not None else getattr(subject, "lng", None)
        tz = tz if tz is not None else getattr(subject, "tz_str", None)
        if lat is None or lng is None or (require_tz and tz is None):
            raise ValueError(f"the {cmd} profile has no {'/'.join(w[2:] for w in wanted)} to derive a location from")
        return float(lat), float(lng), str(tz) if tz is not None else None
    raise ValueError(f"{cmd} needs -s <profile> or {'/'.join(wanted)}")


def _profile_tz(profile: Optional[str], tz: Optional[str]) -> Optional[str]:
    """``--tz`` if given, else the profile's zone, else ``None``."""
    if tz is None and profile:
        return getattr(subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile), "tz_str", None)
    return tz


def _attach_tz_offset(value: str, tz_str: Optional[str], cmd: str) -> str:
    """A naive ISO bound with *tz_str*'s offset attached — ``from_iso_range`` reads naive bounds as UTC."""
    if tz_str is None:
        return value
    dt = _parse_dt(value)
    if dt.tzinfo is not None:
        return value
    from zoneinfo import ZoneInfo

    try:
        return dt.replace(tzinfo=ZoneInfo(tz_str)).isoformat()
    except Exception:
        raise ValueError(f"{cmd}: unknown timezone {tz_str!r}") from None


def _moment(value: Optional[str], cmd: str, tz_str: Optional[str] = None) -> datetime:
    """``--from`` as the naive wall-clock moment the ``from_datetime``/``from_date`` factories take in *tz_str*.

    An offset-bearing input is an absolute instant: it is converted into *tz_str*
    first, or its components would be re-read in the wrong zone (12:30Z as 12:30
    Rome is a two-hour error). Seconds are truncated (the factories take none).
    An instant on the second reading of a DST fall-back cannot survive the naive
    components, so it is refused rather than silently shifted by an hour.
    """
    if value is None:
        raise ValueError(f"{cmd} needs --from (an ISO date or datetime)")
    dt = _parse_dt(value)
    if dt.tzinfo is not None and tz_str:
        from zoneinfo import ZoneInfo

        local = dt.astimezone(ZoneInfo(tz_str))
        if local.fold:
            raise ValueError(
                f"{cmd}: {value!r} falls on an ambiguous wall time in {tz_str!r} (the second reading of a DST "
                "fall-back). The moment factories take wall-clock components without DST disambiguation; "
                "use a non-ambiguous moment or drop the UTC offset."
            )
        dt = local.replace(tzinfo=None)
    return dt


def _range_query(
    cmd: str,
    from_: Optional[str],
    to: Optional[str],
    zodiac: Optional[str],
    sidereal_mode: Optional[str],
    **lists: Optional[list[str]],
) -> tuple[str, str, dict[str, Any]]:
    """Validate ``--from``/``--to`` and assemble the kwargs a range search shares (*lists* under the factory's names)."""
    if from_ is None or to is None:
        raise ValueError(f"{cmd} needs --from and --to")
    return from_, to, {**_zodiac_kwargs(zodiac, sidereal_mode), **_given(**lists)}


def sun_times(
    profile: SubjectProfile = None,
    lat: SubjectLat = None,
    lng: SubjectLng = None,
    tz: SubjectTz = None,
    from_: FromOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Sunrise, sunset, noon and twilights for a date and place."""
    from kerykeion import SunTimesFactory

    la, lo, tz_str = _location(profile, lat, lng, tz, "sun-times")
    m = _moment(from_, "sun-times", tz_str)
    _emit(SunTimesFactory.from_date(m.year, m.month, m.day, latitude=la, longitude=lo, tz_str=tz_str), fmt, output)


def hours(
    profile: SubjectProfile = None,
    lat: SubjectLat = None,
    lng: SubjectLng = None,
    tz: SubjectTz = None,
    from_: FromOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Planetary hours and rulers for a moment."""
    from kerykeion import PlanetaryHoursFactory

    la, lo, tz_str = _location(profile, lat, lng, tz, "hours")
    m = _moment(from_, "hours", tz_str)
    model = PlanetaryHoursFactory.from_datetime(
        m.year, m.month, m.day, m.hour, m.minute, latitude=la, longitude=lo, tz_str=tz_str
    )
    _emit(model, fmt, output)


def voc(
    profile: SubjectProfile = None,
    tz: SubjectTz = None,
    from_: FromOpt = None,
    to: ToOpt = None,
    zodiac: ZodiacSkyOpt = None,
    sidereal_mode: SiderealSkyOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Void-of-course Moon: the windows in a range, or the state at a moment.

    With --from and --to, the windows in the range; with --from alone, the
    state at that moment (needs --tz or -s).
    """
    from kerykeion import VoidOfCourseMoonFactory

    extra = _zodiac_kwargs(zodiac, sidereal_mode)
    tz_str = _profile_tz(profile, tz)
    if to is not None:
        if from_ is None:
            raise ValueError("voc --to also needs --from")
        start, end = _attach_tz_offset(from_, tz_str, "voc"), _attach_tz_offset(to, tz_str, "voc")
        _emit(VoidOfCourseMoonFactory.from_iso_range(start, end, **extra), fmt, output)
        return
    if tz_str is None:
        raise ValueError("voc at a moment needs --tz (or -s a profile with a timezone)")
    m = _moment(from_, "voc", tz_str)
    _emit(
        VoidOfCourseMoonFactory.from_datetime(m.year, m.month, m.day, m.hour, m.minute, tz_str=tz_str, **extra),
        fmt,
        output,
    )


def eclipses(
    profile: SubjectProfile = None,
    lat: SubjectLat = None,
    lng: SubjectLng = None,
    start_year: StartYearOpt = None,
    count: CountOpt = None,
    zodiac: ZodiacSkyOpt = None,
    sidereal_mode: SiderealSkyOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Solar and lunar eclipses, global or as seen from a place."""
    from kerykeion import EclipseFactory

    if (lat is None) != (lng is None):  # a half-given place is a typo, not a global search
        raise ValueError("eclipses needs both --lat and --lng (or neither, for a global search).")
    kwargs = {**_given(start_year=start_year, count=count), **_zodiac_kwargs(zodiac, sidereal_mode)}
    if lat is not None or profile is not None:
        la, lo, _ = _location(profile, lat, lng, None, "eclipses", require_tz=False)
        _emit(EclipseFactory.search_from_location(la, lo, **kwargs), fmt, output)
    else:
        _emit(EclipseFactory.search_global(**kwargs), fmt, output)


def lunations(
    from_: FromOpt = None,
    to: ToOpt = None,
    phase: PhaseOpt = None,
    zodiac: ZodiacSkyOpt = None,
    sidereal_mode: SiderealSkyOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """New, quarter and full moons in a range."""
    from kerykeion import LunationFinderFactory

    start, end, extra = _range_query("lunations", from_, to, zodiac, sidereal_mode, phases=_split_csv(phase))
    _emit(LunationFinderFactory.from_iso_range(start, end, **extra), fmt, output)


def ingresses(
    from_: FromOpt = None,
    to: ToOpt = None,
    planets: PlanetsOpt = None,
    periods: PeriodsFlag = None,
    zodiac: ZodiacSkyOpt = None,
    sidereal_mode: SiderealSkyOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Sign ingresses in a range, or the sign stays with --periods."""
    from kerykeion import SignIngressFactory

    start, end, extra = _range_query("ingresses", from_, to, zodiac, sidereal_mode, planets=_split_csv(planets))
    search = SignIngressFactory.sign_periods_from_iso_range if periods else SignIngressFactory.from_iso_range
    _emit(search(start, end, **extra), fmt, output)


def stations(
    from_: FromOpt = None,
    to: ToOpt = None,
    planets: PlanetsOpt = None,
    periods: PeriodsFlag = None,
    zodiac: ZodiacSkyOpt = None,
    sidereal_mode: SiderealSkyOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Retrograde and direct stations in a range, or the spans with --periods."""
    from kerykeion import RetrogradeStationFactory

    start, end, extra = _range_query("stations", from_, to, zodiac, sidereal_mode, planets=_split_csv(planets))
    search = (
        RetrogradeStationFactory.retrograde_periods_from_iso_range
        if periods
        else RetrogradeStationFactory.from_iso_range
    )
    _emit(search(start, end, **extra), fmt, output)


def mundane(
    from_: FromOpt = None,
    to: ToOpt = None,
    planets: PlanetsOpt = None,
    aspects: AspectsOpt = None,
    zodiac: ZodiacSkyOpt = None,
    sidereal_mode: SiderealSkyOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Exact planet-to-planet aspects in a range."""
    from kerykeion import MundaneAspectFactory

    start, end, extra = _range_query(
        "mundane",
        from_,
        to,
        zodiac,
        sidereal_mode,
        points=_split_csv(planets),
        aspects=_aspect_names(_parse_aspects(aspects), "mundane aspects"),  # names only: no per-aspect orb here
    )
    _emit(MundaneAspectFactory.from_iso_range(start, end, **extra), fmt, output)


def phenomena(
    profile: SubjectProfile = None,
    planets: PlanetsOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Phase, elongation, magnitude and diameter of the planets."""
    from kerykeion import PlanetaryPhenomenaFactory

    if not profile:
        raise ValueError("phenomena needs -s <profile> for the moment to describe")
    subject = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile)
    _emit(PlanetaryPhenomenaFactory.from_subject(subject, _split_csv(planets)), fmt, output)  # type: ignore[arg-type]


def occultations(
    profile: SubjectProfile = None,
    lat: SubjectLat = None,
    lng: SubjectLng = None,
    planet: PlanetIdOpt = None,
    count: CountOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Lunar occultations of a body, from the subject's moment on.

    The search starts from ``-s``'s moment (the library exposes no public
    date-to-JD helper). Give ``--lat/--lng`` — or a profile that has them — for
    a local search.
    """
    from kerykeion import OccultationFactory

    if not profile:
        raise ValueError(
            "occultations needs -s <profile> to fix the moment to search from "
            "(use `subject save now-ish ...` for an arbitrary date)."
        )
    if planet is None:  # no honest default: the Moon is the occulter, not the occulted
        raise ValueError(
            "occultations needs --planet: the body being occulted by the Moon (e.g. Venus, Mars, Aldebaran)."
        )
    if (lat is None) != (lng is None):
        raise ValueError("occultations needs both --lat and --lng (or neither).")
    subject = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile)
    julian_day = getattr(subject, "julian_day", None)
    if julian_day is None:
        raise ValueError("the subject has no julian_day to search occultations from")
    kwargs: dict[str, Any] = {"planet_id": planet, **_given(count=count)}
    la = lat if lat is not None else getattr(subject, "lat", None)
    lo = lng if lng is not None else getattr(subject, "lng", None)
    factory = OccultationFactory()
    if la is not None and lo is not None:
        _emit(factory.search_local(julian_day, lat=float(la), lng=float(lo), **kwargs), fmt, output)
    else:
        _emit(factory.search_global(julian_day, **kwargs), fmt, output)


COMMANDS = [
    ("sun-times", sun_times),
    ("hours", hours),
    ("voc", voc),
    ("eclipses", eclipses),
    ("lunations", lunations),
    ("ingresses", ingresses),
    ("stations", stations),
    ("mundane", mundane),
    ("phenomena", phenomena),
    ("occultations", occultations),
]
