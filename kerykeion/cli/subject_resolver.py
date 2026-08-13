# -*- coding: utf-8 -*-
"""Turn a profile + inline flags into an :class:`AstrologicalSubjectModel`.

The merge precedence (lowest → highest): the library's own defaults → profile
recipe → inline flags. Because every CLI flag alias is ``Optional`` with a
``None`` default, "not given" is just ``None`` and overrides nothing — no need
to consult Click's parameter source for the standard flags.

Non-obvious mappings live here and nowhere else:

* ``--date`` → year/month/day via **regex**, never ``date.fromisoformat`` (which
  rejects year < 1; BCE dates are a real case);
* ``--time`` → hour/minute/seconds (``seconds`` is keyword-only in the factory);
* ``--houses placidus`` → ``P``; ``--points all`` → the full point-set constant;
* online default is False when lat+lng+tz are all known, else True;
* ``--set key=value`` is whitelisted against the factory signature and refuses
  underscore-prefixed (private) parameters.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

# ── Parsing helpers ──────────────────────────────────────────────────────────

_DATE_RE = re.compile(r"^\s*(-?\d{1,5})-(\d{1,2})-(\d{1,2})\s*$")
_TIME_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*$")

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
    # Porphyry is "O" — "B" is Alcabitius (see the HousesSystemIdentifier Literal
    # in kerykeion/schemas/literals.py). APC (topocentric) is "Y".
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


def parse_date(value: str) -> tuple[int, int, int]:
    """Split a ``YYYY-MM-DD`` string (negative year = BCE) into ints."""
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
    """Split ``HH:MM`` or ``HH:MM:SS`` into hour, minute, seconds."""
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


_VALID_HOUSE_LETTERS: Optional[frozenset[str]] = None


def _valid_house_letters() -> frozenset[str]:
    """The single-letter codes the factory accepts (``HousesSystemIdentifier``).

    Resolved lazily so this module stays free of a kerykeion import at module
    load (the cold-import invariant). Cached after first use.
    """
    global _VALID_HOUSE_LETTERS
    if _VALID_HOUSE_LETTERS is None:
        import typing

        from kerykeion.schemas.literals import HousesSystemIdentifier

        _VALID_HOUSE_LETTERS = frozenset(typing.get_args(HousesSystemIdentifier))
    return _VALID_HOUSE_LETTERS


def resolve_house_system(value: Optional[str]) -> Optional[str]:
    """Accept a single letter or a common house-system name; return the letter."""
    if value is None:
        return None
    v = value.strip()
    if len(v) == 1 and v.isalpha():
        up = v.upper()
        # Validate membership here rather than letting an unknown letter (G, J,
        # E, …) reach the factory, where it becomes a confusing pydantic
        # "input does not match the literal" ValidationError with no hint that
        # the house-system letter was the cause. (Note: "i" upper-cases to "I",
        # a distinct system — Sunshine vs Sunshine/alt.; that pre-exists.)
        if up not in _valid_house_letters():
            raise ValueError(
                f"unknown house-system letter {value!r}; give a valid letter "
                f"({', '.join(sorted(_valid_house_letters()))}) or a name "
                "(placidus, koch, whole-sign, porphyry, …)."
            )
        return up
    key = v.lower().replace("-", "_")
    if key in _HOUSES_BY_NAME:
        return _HOUSES_BY_NAME[key]
    raise ValueError(
        f"unknown house system {value!r}; give a letter (P, K, W, C, R, A, M, …) "
        "or a name (placidus, koch, whole-sign, …)."
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


def resolve_points(value: Optional[str]) -> Optional[list[str]]:
    """A preset alias, or a comma-separated list of point names."""
    if value is None:
        return None
    key = value.strip().lower()
    sets = _point_sets()
    if key in sets:
        return sets[key]
    parts = [p.strip() for p in value.split(",") if p.strip()]
    if not parts:
        raise ValueError(f"empty point set {value!r}")
    return parts


def _fixed_star_sets() -> dict[str, list[str]]:
    from kerykeion.settings import config_constants as cc

    return {
        "royal": list(cc.ROYAL_FIXED_STARS),
        "behenian": list(cc.BEHENIAN_FIXED_STARS),
        "default_stars": list(cc.DEFAULT_FIXED_STARS),
        "default-stars": list(cc.DEFAULT_FIXED_STARS),
    }


def resolve_fixed_stars(value: Optional[str]) -> Optional[list[str]]:
    if value is None:
        return None
    key = value.strip().lower().replace("-", "_")
    sets = _fixed_star_sets()
    if key in sets:
        return sets[key]
    parts = [p.strip() for p in value.split(",") if p.strip()]
    if not parts:
        raise ValueError(f"empty fixed-star set {value!r}")
    return parts


def _coerce_set_value(raw: str) -> Any:
    """Best-effort scalar coercion for ``--set key=value``."""
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"none", "null"}:
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def _coerce_set_value_typed(annotation: Any, raw: str) -> Any:
    """Coerce a ``--set`` value for a ``ProfileInput`` field of *annotation*.

    Scalar fields use :func:`_coerce_set_value` (so ``true``/``false``/``none``/
    ints/floats still work as before). List fields (``active_points``,
    ``active_fixed_stars`` — both ``Optional[list[str]]``) split a
    comma-separated value, so ``--set active_points=sun,moon`` persists
    ``["sun", "moon"]`` instead of a bare string the recipe then rejects. This
    matches how the dedicated ``--points`` flag and ``introspect.coerce_value``
    (``--param``) already handle lists, so the two advanced-parameter paths agree.
    """
    import typing

    origin = typing.get_origin(annotation)
    if origin is typing.Union:  # unwrap Optional[list[...]] -> list[...]
        non_none = [a for a in typing.get_args(annotation) if a is not type(None)]
        if len(non_none) == 1:
            annotation = non_none[0]
            origin = typing.get_origin(annotation)
    if origin in (list, set):
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        return origin(parts)
    return _coerce_set_value(raw)


# ── Flag collection ──────────────────────────────────────────────────────────


@dataclass
class SubjectFlags:
    """Inline subject flags gathered from a command (None = not given)."""

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
    points: Optional[str] = None
    fixed_stars: Optional[str] = None
    with_flags: list[str] = field(default_factory=list)
    without_flags: list[str] = field(default_factory=list)
    set_flags: list[str] = field(default_factory=list)
    # Commands that do not derive from a birth date (``now``) set this to
    # "current" so materialize() dispatches to from_current_time.
    mode_override: Optional[str] = None


def build_flags(
    *,
    name: Optional[str],
    date: Optional[str],
    time: Optional[str],
    seconds: Optional[int],
    iso_utc: Optional[str],
    lat: Optional[float],
    lng: Optional[float],
    tz: Optional[str],
    city: Optional[str],
    nation: Optional[str],
    online: Optional[bool],
    offline: Optional[bool],
    altitude: Optional[float],
    zodiac: Optional[str],
    sidereal_mode: Optional[str],
    houses: Optional[str],
    perspective: Optional[str],
    points: Optional[str],
    fixed_stars: Optional[str],
    with_flags: Optional[list[str]],
    without_flags: Optional[list[str]],
    set_flags: Optional[list[str]],
    mode_override: Optional[str] = None,
) -> SubjectFlags:
    """Gather the per-command subject parameters into a :class:`SubjectFlags`.

    Every subject-building command (``subject save``, ``natal``, ``synastry`` …)
    spells the same flags in its signature; this is the single place that knows
    how the keyword names map onto :class:`SubjectFlags` fields, so the mapping
    cannot drift between commands.
    """
    return SubjectFlags(
        name=name,
        date=date,
        time=time,
        seconds=seconds,
        iso_utc=iso_utc,
        lat=lat,
        lng=lng,
        tz=tz,
        city=city,
        nation=nation,
        online=online,
        offline=offline,
        altitude=altitude,
        zodiac=zodiac,
        sidereal_mode=sidereal_mode,
        houses=houses,
        perspective=perspective,
        points=points,
        fixed_stars=fixed_stars,
        with_flags=with_flags or [],
        without_flags=without_flags or [],
        set_flags=set_flags or [],
        mode_override=mode_override,
    )


def _profile_input_dict(profile_spec: Optional[str]) -> dict[str, Any]:
    """Load a profile recipe (if any) and return its non-None input fields."""
    if profile_spec is None:
        return {}
    from kerykeion.cli import profiles

    path = profiles.resolve_path(profile_spec)
    profile = profiles.load(path)
    base = profile.input.model_dump(exclude_none=True)
    # 'extra' holds --set-style advanced params persisted to the recipe.
    extra = base.pop("extra", None) or {}
    return {**base, **extra}


def _apply_calc_toggles(
    merged: dict[str, Any], flags: SubjectFlags
) -> None:
    """Fold ``--with`` / ``--without`` onto the calculate_* parameters."""
    current = {
        f"calculate_{k.replace('calculate_', '')}": merged.get(f"calculate_{k.replace('calculate_', '')}")
        for k in _CALC_KEYS
    }
    for feature in flags.with_flags:
        key = _calc_param_for(feature)
        current[key] = True
    for feature in flags.without_flags:
        key = _calc_param_for(feature)
        current[key] = False
    for key, value in current.items():
        if value is not None:
            merged[key] = value


def _calc_param_for(feature: str) -> str:
    key = feature.strip().lower().removeprefix("calculate_")
    if key not in _CALC_KEYS:
        raise ValueError(
            f"unknown feature {feature!r} for --with/--without; choose from "
            f"{', '.join(sorted(_CALC_KEYS))}."
        )
    return _CALC_KEYS[key]


def _apply_set_flags(merged: dict[str, Any], set_flags: list[str]) -> None:
    """Whitelisted advanced parameters from ``--set key=value``.

    The whitelist is the profile recipe shape (:class:`ProfileInput` fields),
    **not** the raw ``from_birth_data`` signature: ``--set`` values are persisted
    to the recipe, and factory-only keys like ``year``/``month``/``hour``/
    ``suppress_geonames_warning`` would either collide in :func:`materialize`
    (duplicate keyword) or break ``subject save`` (``ProfileInput`` rejects them).
    Use the dedicated flags (``--date``/``--time``/``--lat``…) for those.
    """
    if not set_flags:
        return
    from kerykeion.cli.profiles import ProfileInput

    allowed = set(ProfileInput.model_fields) - {"extra"}
    for item in set_flags:
        if "=" not in item:
            raise ValueError(f"--set expects key=value, got {item!r}")
        raw_key, raw_value = item.split("=", 1)
        key = raw_key.strip()
        if key.startswith("_"):
            raise ValueError(f"--set refuses private parameter {key!r}")
        if key not in allowed:
            raise ValueError(
                f"--set {key!r} is not a profile field "
                f"(known: {', '.join(sorted(allowed))})"
            )
        merged[key] = _coerce_set_value_typed(ProfileInput.model_fields[key].annotation, raw_value)


def merge_inputs(
    flags: SubjectFlags, profile_spec: Optional[str] = None
) -> dict[str, Any]:
    """Return the merged recipe dict (in ``ProfileInput`` field names).

    Every layer applied here, none in ``materialize``: profile base → inline flags
    → resolved structured flags (houses/points/fixed-stars) → calculate_* toggles
    → ``--set`` → online default → mode. ``date``/``time`` stay as strings — they
    are a recipe shape, not a factory call. ``materialize`` turns this dict into a
    subject; ``subject save`` persists it verbatim.
    """
    merged: dict[str, Any] = {}
    merged.update(_profile_input_dict(profile_spec))
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
    }
    for key, value in inline.items():
        if value is not None:
            merged[key] = value

    # Resolve structured flags into factory parameter names.
    houses = resolve_house_system(flags.houses) or merged.get("houses_system_identifier")
    if houses is not None:
        merged["houses_system_identifier"] = houses
    points = resolve_points(flags.points)
    if points is not None:
        merged["active_points"] = points
    fixed_stars = resolve_fixed_stars(flags.fixed_stars)
    if fixed_stars is not None:
        merged["active_fixed_stars"] = fixed_stars

    _apply_calc_toggles(merged, flags)
    _apply_set_flags(merged, flags.set_flags)

    # Decide online (explicit flag — including --no-online — > recipe > inferred
    # from coordinates). ``--no-online`` arrives as ``flags.online is False`` and
    # must override a profile's ``online=True``: a falsy flag is an explicit
    # choice, not "not given".
    if flags.online is True:
        merged["online"] = True
    elif flags.offline is True or flags.online is False:
        merged["online"] = False
    elif "online" not in merged:
        coords_complete = (
            merged.get("lat") is not None
            and merged.get("lng") is not None
            and merged.get("tz_str") is not None
        )
        merged["online"] = not coords_complete

    # Mode is derived from what is *actually* present, so a profile saved in one
    # mode cannot pin it: an inline --iso-utc forces iso_utc mode, inline
    # --date/--time force birth mode, and only when neither is given does the
    # profile's (or the default) mode survive. ``mode_override`` (the ``now``
    # command) always wins.
    if flags.mode_override:
        merged["mode"] = flags.mode_override
    elif flags.iso_utc is not None:
        merged["mode"] = "iso_utc"
    elif flags.date is not None or flags.time is not None:
        merged["mode"] = "birth"
    elif "mode" not in merged:
        merged["mode"] = "iso_utc" if merged.get("iso_utc_time") else "birth"
    return merged


def materialize(merged: dict[str, Any]):
    """Turn a merged recipe dict into an ``AstrologicalSubjectModel``.

    Raises ``ValueError`` with a readable message on any bad input; the command
    layer turns that into exit 4.
    """
    from kerykeion import AstrologicalSubjectFactory

    name = merged.get("name") or "Now"
    mode = merged.get("mode", "birth")
    iso_utc = merged.get("iso_utc_time")

    # The factory never wants to hear from GeoNames unprompted from a pipeline.
    factory_kwargs = {**merged, "suppress_geonames_warning": True}

    if mode == "iso_utc":
        if not iso_utc:
            raise ValueError("iso_utc mode needs --iso-utc")
        factory_kwargs.pop("date", None)
        factory_kwargs.pop("time", None)
        factory_kwargs.pop("seconds", None)
        factory_kwargs.pop("name", None)
        factory_kwargs.pop("mode", None)
        factory_kwargs.pop("iso_utc_time", None)
        return AstrologicalSubjectFactory.from_iso_utc_time(
            name=name, iso_utc_time=iso_utc, **_kwargs_for(factory_kwargs, "iso_utc")
        )

    if mode == "current":
        # from_current_time derives year/month/day/hour/minute from now(); the
        # birth-date fields are irrelevant and not accepted by its signature.
        for k in ("date", "time", "seconds", "iso_utc_time"):
            factory_kwargs.pop(k, None)
        factory_kwargs.pop("name", None)
        factory_kwargs.pop("mode", None)
        return AstrologicalSubjectFactory.from_current_time(
            name=name, **_kwargs_for(factory_kwargs, "current")
        )

    date_str = factory_kwargs.pop("date", None)
    time_str = factory_kwargs.pop("time", None)
    if not date_str:
        raise ValueError("birth mode needs --date (or a profile with a date)")
    if not time_str:
        # ``from_birth_data`` fills ``hour=minute=None`` from ``datetime.now()``,
        # which would make a date-only natal non-deterministic across runs. A
        # natal chart needs a birth time for the houses and Ascendant.
        raise ValueError(
            "birth mode needs --time (HH:MM[:SS]); a natal chart requires a birth "
            "time. Pass --time, or use `kerykeion now` for the current moment."
        )
    year, month, day = parse_date(date_str)
    seconds = factory_kwargs.pop("seconds", None)
    hour, minute, parsed_seconds = parse_time(time_str)
    seconds = seconds if seconds is not None else parsed_seconds
    if seconds:
        factory_kwargs["seconds"] = seconds
    # The birth date/time components are passed explicitly below; drop any
    # same-named keys (e.g. from a hand-edited profile's ``extra``) so they
    # cannot collide as duplicate keyword arguments.
    for k in ("name", "mode", "iso_utc_time", "year", "month", "day", "hour", "minute"):
        factory_kwargs.pop(k, None)
    return AstrologicalSubjectFactory.from_birth_data(
        name=name,
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        **_kwargs_for(factory_kwargs, "birth"),
    )


def resolve_subject(
    flags: SubjectFlags, profile_spec: Optional[str] = None
):
    """Build an ``AstrologicalSubjectModel`` from a profile plus inline flags."""
    return materialize(merge_inputs(flags, profile_spec))


_FACTORY_PARAMS: dict[str, set[str]] = {}


def _kwargs_for(merged: dict[str, Any], mode: str) -> dict[str, Any]:
    """Drop keys the chosen factory method does not accept.

    Guards against a recipe or --set carrying a key valid for ``from_birth_data``
    (e.g. ``is_dst``, ``cache_expire_after_days``) into ``from_iso_utc_time``,
    which would raise ``TypeError`` from an unexpected keyword.
    """
    import inspect

    from kerykeion import AstrologicalSubjectFactory

    method = (
        AstrologicalSubjectFactory.from_birth_data
        if mode == "birth"
        else AstrologicalSubjectFactory.from_current_time
        if mode == "current"
        else AstrologicalSubjectFactory.from_iso_utc_time
    )
    allowed = _FACTORY_PARAMS.setdefault(
        mode, set(inspect.signature(method).parameters)
    )
    return {k: v for k, v in merged.items() if k in allowed}
