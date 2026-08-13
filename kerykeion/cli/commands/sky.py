# -*- coding: utf-8 -*-
"""``kerykeion sky <sub>`` — astronomical events (sun, moon, planets).

Two input shapes meet here:

* **moment** commands (``sun-times``, ``hours``) take a single date/time and a
  location, given either inline (``--lat/--lng/--tz``) or derived from
  ``-s <profile>``;
* **range** commands (``lunations``, ``ingresses``, ``stations``, and ``voc``
  with ``--to``) take ``--from``/``--to`` and need no location;
* ``voc`` without ``--to`` and ``eclipses`` straddle the two.

The functions are decorator-free; :mod:`kerykeion.cli.app` registers the group.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from kerykeion.cli import subject_resolver, warnings
from kerykeion.cli.options import (
    CountOpt,
    FormatOpt,
    FromOpt,
    OutputOpt,
    PhaseOpt,
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
from kerykeion.cli.rendering import formats
from kerykeion.cli.typer_app import KerykeionTyper

sky_app = KerykeionTyper(
    name="sky",
    help="Astronomical events: sun, moon, eclipses, ingresses, stations.",
    no_args_is_help=True,
    add_completion=False,
)


def _emit(model: object, fmt: Optional[str], output: Optional[str]) -> None:
    warnings.output_with_warnings(model, formats.resolve_format(fmt, output), output)


def _split_csv(values: Optional[list[str]]) -> Optional[list[str]]:
    if values is None:
        return None
    out: list[str] = []
    for item in values:
        out.extend(part.strip() for part in item.split(",") if part.strip())
    return out or None


def _parse_dt(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"expected an ISO date or datetime (YYYY-MM-DD or YYYY-MM-DDThh:mm), got {value!r}"
        ) from exc


def _zodiac_kwargs(zodiac: Optional[str], sidereal_mode: Optional[str]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if zodiac is not None:
        # Case-insensitive, matching kerykeion.utilities.normalize_zodiac_type
        # (which the factories themselves call): the CLI must not be stricter
        # than the library and reject ``--zodiac tropical``/``SIDEREAL`` the
        # factory would accept. Map to the canonical Literal values.
        z = zodiac.strip().lower()
        if z in ("tropical", "tropic"):
            kwargs["zodiac_type"] = "Tropical"
        elif z == "sidereal":
            kwargs["zodiac_type"] = "Sidereal"
        else:
            raise ValueError("--zodiac must be Tropical or Sidereal")
    if sidereal_mode is not None:
        kwargs["sidereal_mode"] = sidereal_mode
    return kwargs


def _location(
    profile: Optional[str], lat: Optional[float], lng: Optional[float], tz: Optional[str], cmd: str
) -> tuple[float, float, str]:
    """Resolve (lat, lng, tz) from a profile or inline flags.

    Inline flags take precedence over the profile (universal CLI convention: an
    explicit value wins), so a relocated reading is honoured even when a profile
    supplies the birthplace — mirroring ``charts.transit``.
    """
    if profile:
        subject = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile)
        lat_v = lat if lat is not None else getattr(subject, "lat", None)
        lng_v = lng if lng is not None else getattr(subject, "lng", None)
        tz_v = tz if tz is not None else getattr(subject, "tz_str", None)
        if lat_v is None or lng_v is None or tz_v is None:
            raise ValueError(f"the {cmd} profile has no lat/lng/tz to derive a location from")
        return float(lat_v), float(lng_v), str(tz_v)
    if lat is None or lng is None or tz is None:
        raise ValueError(f"{cmd} needs -s <profile> or --lat/--lng/--tz")
    return lat, lng, tz


def _latlng(
    profile: Optional[str], lat: Optional[float], lng: Optional[float], cmd: str
) -> tuple[float, float]:
    """Resolve (lat, lng) only — for commands that take no timezone (eclipses).

    Inline flags take precedence over the profile (see :func:`_location`).
    """
    if profile:
        subject = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile)
        lat_v = lat if lat is not None else getattr(subject, "lat", None)
        lng_v = lng if lng is not None else getattr(subject, "lng", None)
        if lat_v is None or lng_v is None:
            raise ValueError(f"the {cmd} profile has no lat/lng to derive a location from")
        return float(lat_v), float(lng_v)
    if lat is None or lng is None:
        raise ValueError(f"{cmd} needs -s <profile> or --lat/--lng")
    return lat, lng


def _attach_tz_offset(value: str, tz_str: Optional[str], cmd: str) -> str:
    """Return *value* as an ISO string, attaching *tz_str*'s offset if naive.

    ``VoidOfCourseMoonFactory.from_iso_range`` is UTC-only: naive ISO bounds are
    read as UTC. When the user gives ``--tz`` (or ``-s`` a profile with a zone)
    we interpret a naive bound in that zone and emit an offset-aware ISO string,
    so the library converts it to the UTC instant the user meant.
    """
    if tz_str is None:
        return value
    dt = _parse_dt(value)
    if dt.tzinfo is not None:
        return value
    from zoneinfo import ZoneInfo

    try:
        tz = ZoneInfo(tz_str)
    except Exception:
        raise ValueError(f"{cmd}: unknown timezone {tz_str!r}") from None
    return dt.replace(tzinfo=tz).isoformat()


def _moment(value: Optional[str], cmd: str, tz_str: Optional[str] = None) -> datetime:
    """Parse ``--from`` into the wall-clock components the moment factories use.

    The moment factories (``from_datetime``/``from_date``) take naive year/month/
    day/hour/minute in ``tz_str``. An offset-bearing input (``...T12:30:00Z`` or
    ``...+01:00``) denotes an *absolute instant*; extracting its raw components
    and re-fitting them into ``tz_str`` would shift the moment by the offset
    (e.g. 12:30Z re-read as 12:30 Europe/Rome = 10:30Z — a two-hour error). When
    the input is offset-aware we convert the instant into ``tz_str`` first, so
    the wall-clock parts match what the user meant. A naive input is already
    wall-clock and is returned as-is.

    Seconds are truncated: the ``from_datetime`` factories do not accept them
    (sub-minute lunar motion, at most ~0.008°, is below their resolution).

    An aware instant that lands on the *second* reading of a DST fall-back
    (``fold=1``) cannot be carried through the naive components — the factories
    rebuild without ``fold`` and would silently pick the first reading, shifting
    the instant by one hour. That ambiguity is surfaced as an error instead of
    guessed.
    """
    if value is None:
        raise ValueError(f"{cmd} needs --from (an ISO date or datetime)")
    dt = _parse_dt(value)
    if dt.tzinfo is not None and tz_str:
        from zoneinfo import ZoneInfo

        local = dt.astimezone(ZoneInfo(tz_str))
        if local.fold:
            raise ValueError(
                f"{cmd}: {value!r} falls on an ambiguous wall time in "
                f"{tz_str!r} (the second reading of a DST fall-back). The moment "
                "factories take wall-clock components without DST disambiguation; "
                "use a non-ambiguous moment or drop the UTC offset."
            )
        dt = local.replace(tzinfo=None)
    return dt


@sky_app.command("sun-times")
def sun_times(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    lat: SubjectLat = None,  # type: ignore[assignment]
    lng: SubjectLng = None,  # type: ignore[assignment]
    tz: SubjectTz = None,  # type: ignore[assignment]
    from_: FromOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Sunrise, sunset, noon and twilight bands for a date and place."""
    from kerykeion import SunTimesFactory

    la, lo, tz_str = _location(profile, lat, lng, tz, "sun-times")
    moment = _moment(from_, "sun-times", tz_str)
    model = SunTimesFactory.from_date(
        moment.year, moment.month, moment.day, latitude=la, longitude=lo, tz_str=tz_str
    )
    _emit(model, fmt, output)


@sky_app.command("hours")
def hours(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    lat: SubjectLat = None,  # type: ignore[assignment]
    lng: SubjectLng = None,  # type: ignore[assignment]
    tz: SubjectTz = None,  # type: ignore[assignment]
    from_: FromOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Planetary hours and the day/hour rulers for a moment."""
    from kerykeion import PlanetaryHoursFactory

    la, lo, tz_str = _location(profile, lat, lng, tz, "hours")
    moment = _moment(from_, "hours", tz_str)
    model = PlanetaryHoursFactory.from_datetime(
        moment.year, moment.month, moment.day, moment.hour, moment.minute,
        latitude=la, longitude=lo, tz_str=tz_str,
    )
    _emit(model, fmt, output)


@sky_app.command("voc")
def voc(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    tz: SubjectTz = None,  # type: ignore[assignment]
    from_: FromOpt = None,  # type: ignore[assignment]
    to: ToOpt = None,  # type: ignore[assignment]
    zodiac: ZodiacSkyOpt = None,  # type: ignore[assignment]
    sidereal_mode: SiderealSkyOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Void-of-Course Moon: the status at a moment, or the windows in a range.

    With ``--to`` it lists VoC windows across the range; without it, the Moon's
    status at ``--from`` (needs ``--tz`` or ``-s``).
    """
    from kerykeion import VoidOfCourseMoonFactory

    extra = _zodiac_kwargs(zodiac, sidereal_mode)
    model: object
    if to is not None:
        if from_ is None:
            raise ValueError("voc --to also needs --from")
        # from_iso_range is UTC-only; honour --tz (or a profile's timezone) by
        # attaching that zone's offset to naive bounds so the library converts
        # them to the intended UTC instants rather than reading them as UTC.
        range_tz = tz
        if range_tz is None and profile:
            subject = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile)
            range_tz = getattr(subject, "tz_str", None)
        start_iso = _attach_tz_offset(from_, range_tz, "voc")
        end_iso = _attach_tz_offset(to, range_tz, "voc")
        model = VoidOfCourseMoonFactory.from_iso_range(start_iso, end_iso, **extra)
    else:
        tz_str = tz
        if tz_str is None and profile:
            subject = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile)
            tz_str = getattr(subject, "tz_str", None)
        if tz_str is None:
            raise ValueError("voc at a moment needs --tz (or -s a profile with a timezone)")
        moment = _moment(from_, "voc", tz_str)
        model = VoidOfCourseMoonFactory.from_datetime(
            moment.year, moment.month, moment.day, moment.hour, moment.minute,
            tz_str=tz_str, **extra,
        )
    _emit(model, fmt, output)


@sky_app.command("eclipses")
def eclipses(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    lat: SubjectLat = None,  # type: ignore[assignment]
    lng: SubjectLng = None,  # type: ignore[assignment]
    start_year: StartYearOpt = None,  # type: ignore[assignment]
    count: CountOpt = None,  # type: ignore[assignment]
    zodiac: ZodiacSkyOpt = None,  # type: ignore[assignment]
    sidereal_mode: SiderealSkyOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Solar and lunar eclipses. Located (with -s/--lat/--lng) or global."""
    from kerykeion import EclipseFactory

    extra = _zodiac_kwargs(zodiac, sidereal_mode)
    # A partially-supplied location (only one of --lat/--lng) is almost certainly
    # a typo; don't silently fall back to a global search that ignores the coord.
    if (lat is None) != (lng is None):
        raise ValueError(
            "eclipses needs both --lat and --lng (or neither, for a global search)."
        )
    has_loc = (lat is not None and lng is not None) or profile is not None
    if has_loc:
        la, lo = _latlng(profile, lat, lng, "eclipses")
        kwargs: dict[str, Any] = {}
        if start_year is not None:
            kwargs["start_year"] = start_year
        if count is not None:
            kwargs["count"] = count
        model = EclipseFactory.search_from_location(la, lo, **kwargs, **extra)
    else:
        kwargs = {}
        if start_year is not None:
            kwargs["start_year"] = start_year
        if count is not None:
            kwargs["count"] = count
        model = EclipseFactory.search_global(**kwargs, **extra)
    _emit(model, fmt, output)


def _range_factory_call(from_: Optional[str], to: Optional[str], cmd: str):
    """Validate the --from/--to pair and return (start, end) as ISO strings."""
    if from_ is None or to is None:
        raise ValueError(f"{cmd} needs --from and --to")
    return from_, to


@sky_app.command("lunations")
def lunations(
    from_: FromOpt = None,  # type: ignore[assignment]
    to: ToOpt = None,  # type: ignore[assignment]
    phase: PhaseOpt = None,  # type: ignore[assignment]
    zodiac: ZodiacSkyOpt = None,  # type: ignore[assignment]
    sidereal_mode: SiderealSkyOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """New and quarter moons in a range (filterable with --phase)."""
    from kerykeion import LunationFinderFactory

    start, end = _range_factory_call(from_, to, "lunations")
    extra = _zodiac_kwargs(zodiac, sidereal_mode)
    phases = _split_csv(phase)
    if phases is not None:
        extra["phases"] = phases
    _emit(LunationFinderFactory.from_iso_range(start, end, **extra), fmt, output)


@sky_app.command("ingresses")
def ingresses(
    from_: FromOpt = None,  # type: ignore[assignment]
    to: ToOpt = None,  # type: ignore[assignment]
    planets: PlanetsOpt = None,  # type: ignore[assignment]
    zodiac: ZodiacSkyOpt = None,  # type: ignore[assignment]
    sidereal_mode: SiderealSkyOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Sign ingresses of the planets in a range."""
    from kerykeion import SignIngressFactory

    start, end = _range_factory_call(from_, to, "ingresses")
    extra = _zodiac_kwargs(zodiac, sidereal_mode)
    active = _split_csv(planets)
    if active is not None:
        extra["planets"] = active
    _emit(SignIngressFactory.from_iso_range(start, end, **extra), fmt, output)


@sky_app.command("stations")
def stations(
    from_: FromOpt = None,  # type: ignore[assignment]
    to: ToOpt = None,  # type: ignore[assignment]
    planets: PlanetsOpt = None,  # type: ignore[assignment]
    zodiac: ZodiacSkyOpt = None,  # type: ignore[assignment]
    sidereal_mode: SiderealSkyOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Retrograde/direct stations of the planets in a range."""
    from kerykeion import RetrogradeStationFactory

    start, end = _range_factory_call(from_, to, "stations")
    extra = _zodiac_kwargs(zodiac, sidereal_mode)
    active = _split_csv(planets)
    if active is not None:
        extra["planets"] = active
    _emit(RetrogradeStationFactory.from_iso_range(start, end, **extra), fmt, output)
