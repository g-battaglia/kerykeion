# -*- coding: utf-8 -*-
"""Turn a profile + inline flags into an ``AstrologicalSubjectModel``.

Precedence, lowest to highest: library defaults → profile recipe → inline flags.
Every flag is ``Optional`` and ``None`` means "not given", so it overrides
nothing. Dates go through a regex, never ``date.fromisoformat`` (it rejects
year < 1, and BCE is a real case). No kerykeion import at module level: the
cold-import gate keeps ``import kerykeion_cli`` cheap.
"""

from __future__ import annotations

import difflib
import functools
import re
import typing
from dataclasses import dataclass, field
from typing import Any, Optional

_DATE_RE = re.compile(r"^\s*(-?\d{1,5})-(\d{1,2})-(\d{1,2})\s*$")
_TIME_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*$")

# Porphyry is "O" ("B" is Alcabitius); APC/topocentric is "Y". See HousesSystemIdentifier.
_HOUSES_BY_NAME = {
    "placidus": "P",
    "plac": "P",
    "koch": "K",
    "whole_sign": "W",
    "wholesign": "W",
    "whole": "W",
    "campanus": "C",
    "regiomontanus": "R",
    "equal": "A",
    "equal_house": "A",
    "morinus": "M",
    "porphyry": "O",
    "porphyrius": "O",
    "meridian": "X",
    "azimuthal": "H",
    "polich_page": "T",
    "apc": "Y",
}

_CALC_KEYS = {
    "lunar_phase": "calculate_lunar_phase",
    "dignities": "calculate_dignities",
    "nakshatra": "calculate_nakshatra",
    "gauquelin": "calculate_gauquelin",
    "nutation": "calculate_nutation",
    "local_space": "calculate_local_space",
}


# ── Parsing and canonicalisation ─────────────────────────────────────────────


def parse_date(value: str) -> tuple[int, int, int]:
    """``YYYY-MM-DD`` (negative year = BCE) → ints."""
    match = _DATE_RE.match(value)
    if match is None:
        raise ValueError(f"invalid date {value!r}; expected YYYY-MM-DD (negative year = BCE)")
    year, month, day = (int(g) for g in match.groups())
    if not 1 <= month <= 12:
        raise ValueError(f"month out of range in {value!r}")
    if not 1 <= day <= 31:
        raise ValueError(f"day out of range in {value!r}")
    return year, month, day


def parse_time(value: str) -> tuple[int, int, int]:
    """``HH:MM`` or ``HH:MM:SS`` → hour, minute, seconds."""
    match = _TIME_RE.match(value)
    if match is None:
        raise ValueError(f"invalid time {value!r}; expected HH:MM or HH:MM:SS")
    hour, minute, seconds = (int(g) if g is not None else 0 for g in match.groups())
    if not 0 <= hour <= 23:
        raise ValueError(f"hour out of range in {value!r}")
    if not 0 <= minute <= 59:
        raise ValueError(f"minute out of range in {value!r}")
    if not 0 <= seconds <= 59:
        raise ValueError(f"seconds out of range in {value!r}")
    return hour, minute, seconds


@functools.cache
def literal_values(name: str) -> frozenset[str]:
    """The members of a ``kerykeion.schemas.literals`` alias, imported lazily."""
    from kerykeion.schemas import literals

    return frozenset(typing.get_args(getattr(literals, name)))


def resolve_sidereal_mode(value: Optional[str]) -> Optional[str]:
    """Canonicalise a ``SiderealMode`` name case-insensitively; a typo is invalid input (exit 4)."""
    if value is None:
        return None
    modes = literal_values("SiderealMode")
    for candidate in (value.strip(), value.strip().upper()):
        if candidate in modes:
            return candidate
    close = difflib.get_close_matches(value.strip().upper(), modes, n=3, cutoff=0.5)
    hint = f" Did you mean: {', '.join(close)}?" if close else ""
    raise ValueError(
        f"unknown sidereal mode {value!r} (see `kerykeion info literals SiderealMode` for the valid names).{hint}"
    )


def resolve_perspective(value: Optional[str]) -> Optional[str]:
    """Canonicalise a ``PerspectiveType``: case-, space-, dash- and underscore-insensitive."""
    if value is None:
        return None
    valid = literal_values("PerspectiveType")
    key = value.strip().lower().replace("-", " ").replace("_", " ")
    match = {v.lower(): v for v in valid}.get(key)
    if match is None:
        raise ValueError(f"unknown perspective {value!r}; give one of: {', '.join(sorted(valid))}.")
    return match


def resolve_house_system(value: Optional[str]) -> Optional[str]:
    """A single letter or a common name → the ``HousesSystemIdentifier`` letter.

    Case matters for letters ("i" and "I" are two systems): a letter valid as
    typed is kept, otherwise the upper-case form is tried, then rejected.
    """
    if value is None:
        return None
    v = value.strip()
    letters = literal_values("HousesSystemIdentifier")
    if len(v) == 1 and v.isalpha():
        if v in letters:
            return v
        if v.upper() in letters:
            return v.upper()
        raise ValueError(
            f"unknown house-system letter {value!r}; give a valid letter ({', '.join(sorted(letters))}) "
            "or a name (placidus, koch, whole-sign, porphyry, …)."
        )
    key = v.lower().replace("-", "_")
    if key in _HOUSES_BY_NAME:
        return _HOUSES_BY_NAME[key]
    raise ValueError(
        f"unknown house system {value!r}; give a letter (P, K, W, C, R, A, M, …) or a name (placidus, koch, whole-sign, …)."
    )


def _point_sets() -> dict[str, list[str]]:
    from kerykeion.settings import config_constants as cc

    return {
        "default": list(cc.DEFAULT_ACTIVE_POINTS),
        "all": list(cc.ALL_ACTIVE_POINTS),
        "traditional": list(cc.TRADITIONAL_ASTROLOGY_ACTIVE_POINTS),
        "v5": list(cc.V5_DEFAULT_ACTIVE_POINTS),
        "uranian": list(cc.URANIAN_ACTIVE_POINTS),
        "main": list(cc.MAIN_PLANETS),
        "nodes": list(cc.LUNAR_NODES),
        "axes": list(cc.AXIAL_POINTS),
    }


def _fixed_star_sets() -> dict[str, list[str]]:
    from kerykeion.settings import config_constants as cc

    return {
        "royal": list(cc.ROYAL_FIXED_STARS),
        "behenian": list(cc.BEHENIAN_FIXED_STARS),
        "default_stars": list(cc.DEFAULT_FIXED_STARS),
    }


def _preset_or_list(value: Optional[str], presets: dict[str, list[str]], label: str) -> Optional[list[str]]:
    """A preset alias (``all``, ``royal``, ``default-stars``…) or a comma-separated list of names."""
    if value is None:
        return None
    key = value.strip().lower().replace("-", "_")
    if key in presets:
        return presets[key]
    parts = [p.strip() for p in value.split(",") if p.strip()]
    if not parts:
        raise ValueError(f"empty {label} {value!r}")
    return parts


def resolve_points(value: Optional[str]) -> Optional[list[str]]:
    return _preset_or_list(value, _point_sets(), "point set")


def resolve_fixed_stars(value: Optional[str]) -> Optional[list[str]]:
    return _preset_or_list(value, _fixed_star_sets(), "fixed-star set")


def _coerce_set_value(annotation: Any, raw: str) -> Any:
    """Coerce a ``--set key=value`` for a ``ProfileInput`` field: lists split on commas, scalars as ``--param``."""
    from kerykeion_cli.introspect import coerce_scalar

    if typing.get_origin(annotation) is typing.Union:
        (annotation,) = [a for a in typing.get_args(annotation) if a is not type(None)] or (annotation,)
    if typing.get_origin(annotation) in (list, set):
        return [p.strip() for p in raw.split(",") if p.strip()]
    return coerce_scalar(raw)


# ── Flags → recipe → subject ─────────────────────────────────────────────────


@dataclass
class SubjectFlags:
    """Inline subject flags gathered from a command (``None`` = not given)."""

    name: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    seconds: Optional[int] = None
    iso_utc: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    tz: Optional[str] = None
    city: Optional[str] = None
    nation: Optional[str] = None
    online: Optional[bool] = None
    offline: Optional[bool] = None
    altitude: Optional[float] = None
    zodiac: Optional[str] = None
    sidereal_mode: Optional[str] = None
    houses: Optional[str] = None
    perspective: Optional[str] = None
    # No dedicated flags (``--set`` and the recipe carry them); ``transit``
    # inherits them so a natal cast with a USER ayanamsa still rebuilds.
    custom_ayanamsa_t0: Optional[float] = None
    custom_ayanamsa_ayan_t0: Optional[float] = None
    points: Optional[str] = None
    fixed_stars: Optional[str] = None
    with_flags: list[str] = field(default_factory=list)
    without_flags: list[str] = field(default_factory=list)
    set_flags: list[str] = field(default_factory=list)
    # ``now`` sets "current" so materialize() dispatches to from_current_time.
    mode_override: Optional[str] = None


def _profile_input_dict(profile_spec: Optional[str]) -> dict[str, Any]:
    """The non-None recipe fields of a profile, with its ``extra`` (``--set`` values) folded in."""
    if profile_spec is None:
        return {}
    from kerykeion_cli import profiles

    base = profiles.load(profiles.resolve_path(profile_spec)).input.model_dump(exclude_none=True)
    extra = base.pop("extra", None) or {}
    return {**base, **extra}


def _calc_param(feature: str) -> str:
    key = feature.strip().lower().removeprefix("calculate_")
    if key not in _CALC_KEYS:
        raise ValueError(
            f"unknown feature {feature!r} for --with/--without; choose from {', '.join(sorted(_CALC_KEYS))}."
        )
    return _CALC_KEYS[key]


def _apply_set_flags(merged: dict[str, Any], set_flags: list[str]) -> None:
    """``--set key=value``, whitelisted against the recipe shape (``ProfileInput``), never the raw factory signature."""
    if not set_flags:
        return
    from kerykeion_cli.profiles import ProfileInput

    allowed = set(ProfileInput.model_fields) - {"extra"}
    for item in set_flags:
        if "=" not in item:
            raise ValueError(f"--set expects key=value, got {item!r}")
        key, raw_value = (part.strip() for part in item.split("=", 1))
        if key.startswith("_"):
            raise ValueError(f"--set refuses private parameter {key!r}")
        if key not in allowed:
            raise ValueError(f"--set {key!r} is not a profile field (known: {', '.join(sorted(allowed))})")
        merged[key] = _coerce_set_value(ProfileInput.model_fields[key].annotation, raw_value)


def merge_inputs(flags: SubjectFlags, profile_spec: Optional[str] = None) -> dict[str, Any]:
    """The merged recipe dict, in ``ProfileInput`` field names.

    Profile → inline flags → structured flags → ``--with``/``--without`` →
    ``--set`` → online default → mode. ``date``/``time`` stay strings (it is a
    recipe, not a factory call); ``materialize`` turns it into a subject and
    ``subject save`` persists it verbatim. Every check here fails as invalid
    input (exit 4) rather than inside the factory (exit 5).
    """
    merged = _profile_input_dict(profile_spec)
    inline = {
        "name": flags.name,
        "date": flags.date,
        "time": flags.time,
        "seconds": flags.seconds,
        "iso_utc_time": flags.iso_utc,
        "lat": flags.lat,
        "lng": flags.lng,
        "tz_str": flags.tz,
        "city": flags.city,
        "nation": flags.nation,
        "altitude": flags.altitude,
        "zodiac_type": flags.zodiac,
        "sidereal_mode": flags.sidereal_mode,
        "perspective_type": flags.perspective,
        "custom_ayanamsa_t0": flags.custom_ayanamsa_t0,
        "custom_ayanamsa_ayan_t0": flags.custom_ayanamsa_ayan_t0,
        "houses_system_identifier": resolve_house_system(flags.houses),
        "active_points": resolve_points(flags.points),
        "active_fixed_stars": resolve_fixed_stars(flags.fixed_stars),
    }
    merged.update({key: value for key, value in inline.items() if value is not None})
    for feature in flags.with_flags:
        merged[_calc_param(feature)] = True
    for feature in flags.without_flags:
        merged[_calc_param(feature)] = False
    _apply_set_flags(merged, flags.set_flags)

    # Enum-shaped values are canonicalised wherever they came from (flag, recipe or --set).
    if merged.get("sidereal_mode") is not None:
        merged["sidereal_mode"] = resolve_sidereal_mode(str(merged["sidereal_mode"]))
    if merged.get("perspective_type") is not None:
        merged["perspective_type"] = resolve_perspective(str(merged["perspective_type"]))

    # A partial coordinate group would silently blend with the geocoded defaults.
    partial = [
        flag for flag, key in (("--lat", "lat"), ("--lng", "lng"), ("--tz", "tz_str")) if merged.get(key) is not None
    ]
    if 0 < len(partial) < 3:
        raise ValueError(
            f"coordinates are all-or-nothing: only {', '.join(partial)} given. Pass --lat, --lng and --tz "
            "together, or none of them (and let the city/geocode default supply the place); a partial group "
            "silently mixes your values with geocoded defaults."
        )

    # Online: explicit flag (--no-online included) > recipe > inferred from coordinates.
    if flags.online is True and flags.offline is True:
        raise ValueError(
            "--online and --offline are mutually exclusive; pass one (or use --no-online, which means the same as --offline)."
        )
    if flags.online is True:
        merged["online"] = True
    elif flags.offline is True or flags.online is False:
        merged["online"] = False
    elif "online" not in merged:
        merged["online"] = any(merged.get(key) is None for key in ("lat", "lng", "tz_str"))

    # A city and coordinates are two answers to one question; a city offline has none.
    if merged.get("city") is not None and any(merged.get(key) is not None for key in ("lat", "lng", "tz_str")):
        raise ValueError(
            "pass either --city or --lat/--lng/--tz, not both: mixing them silently picks one place and drops the other."
        )
    if merged.get("city") is not None and merged.get("online") is False:
        raise ValueError(
            "--city cannot be resolved with --offline; drop it (geocoding needs the network) or pass "
            "--lat/--lng/--tz for an offline subject."
        )

    # Mode follows what is actually present, so a profile saved in one mode cannot pin it.
    if flags.mode_override:
        merged["mode"] = flags.mode_override
    elif flags.iso_utc is not None:
        merged["mode"] = "iso_utc"
    elif flags.date is not None or flags.time is not None:
        merged["mode"] = "birth"
    elif "mode" not in merged:
        merged["mode"] = "iso_utc" if merged.get("iso_utc_time") else "birth"
    return merged


@functools.cache
def _factory_params(mode: str) -> frozenset[str]:
    """The parameter names the factory method for *mode* accepts (read once, shared read-only)."""
    import inspect

    from kerykeion import AstrologicalSubjectFactory

    methods: dict[str, Any] = {
        "birth": AstrologicalSubjectFactory.from_birth_data,
        "current": AstrologicalSubjectFactory.from_current_time,
    }
    return frozenset(inspect.signature(methods.get(mode, AstrologicalSubjectFactory.from_iso_utc_time)).parameters)


def _kwargs_for(merged: dict[str, Any], mode: str) -> dict[str, Any]:
    """Drop the keys the chosen factory method does not accept (a recipe may carry birth-only keys)."""
    allowed = _factory_params(mode)
    return {k: v for k, v in merged.items() if k in allowed}


def materialize(merged: dict[str, Any]):
    """A merged recipe → ``AstrologicalSubjectModel``; bad input raises ``ValueError`` (exit 4)."""
    from kerykeion import AstrologicalSubjectFactory as Factory

    name = merged.get("name") or "Now"
    mode = merged.get("mode", "birth")
    kwargs = {**merged, "suppress_geonames_warning": True}
    # The moment is passed explicitly below; same-named recipe keys must not collide.
    for key in ("name", "mode", "date", "time", "seconds", "iso_utc_time", "year", "month", "day", "hour", "minute"):
        kwargs.pop(key, None)

    if mode == "iso_utc":
        if not merged.get("iso_utc_time"):
            raise ValueError("iso_utc mode needs --iso-utc")
        return Factory.from_iso_utc_time(
            name=name, iso_utc_time=merged["iso_utc_time"], **_kwargs_for(kwargs, "iso_utc")
        )
    if mode == "current":
        return Factory.from_current_time(name=name, **_kwargs_for(kwargs, "current"))
    if not merged.get("date"):
        raise ValueError("birth mode needs --date (or a profile with a date)")
    if not merged.get("time"):
        # The factory would fill hour/minute from now(), making a date-only natal nondeterministic.
        raise ValueError(
            "birth mode needs --time (HH:MM[:SS]); a natal chart requires a birth time. "
            "Pass --time, or use `kerykeion now` for the current moment."
        )
    year, month, day = parse_date(merged["date"])
    hour, minute, parsed_seconds = parse_time(merged["time"])
    seconds = merged["seconds"] if merged.get("seconds") is not None else parsed_seconds
    return Factory.from_birth_data(
        name=name,
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        seconds=seconds,
        **_kwargs_for(kwargs, "birth"),
    )


def resolve_subject(flags: SubjectFlags, profile_spec: Optional[str] = None):
    """Build the subject from a profile plus inline flags."""
    return materialize(merge_inputs(flags, profile_spec))
