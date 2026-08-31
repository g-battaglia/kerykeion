"""
Kerykeion Utilities Module

This module provides utility functions for astrological calculations including:
- Zodiac position conversions and validations
- House position determinations
- Lunar phase calculations
- Angular mathematics (circular mean, sorting)
- Date/time conversions (Julian Day)
- SVG processing utilities

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

from kerykeion.schemas import (
    KerykeionPointModel,
    KerykeionException,
    ZodiacSignModel,
    AstrologicalSubjectModel,
    LunarPhaseModel,
    CompositeSubjectModel,
    PlanetReturnModel,
    ZodiacType,
)
from kerykeion.schemas.literals import (
    LunarPhaseEmoji,
    LunarPhaseName,
    LunarPhaseStage,
    PointType,
    AstrologicalPoint,
    Houses,
)
from kerykeion.settings.config_constants import POINT_NUMBER_MAP as _POINT_NUMBER_MAP_IMPORT
from typing import Any, Optional, Sequence, Union, cast, get_args
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL, basicConfig, getLogger
import math
import re
from datetime import datetime, timedelta, timezone, tzinfo as _tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


# __package__, not __name__: __package__ is "kerykeion.utilities" while __name__ is
# "kerykeion.utilities.core". The logger must keep the pre-move name, so that
# setup_logging() and every caplog filter naming it address the same one.
logger = getLogger(__package__)


# Pre-compiled regex patterns (invariant, compiled once at module load)
_CSS_VARIABLE_PATTERN = re.compile(r"--([a-zA-Z0-9_-]+)\s*:\s*([^;]+);")

# Cached get_args() tuples (type introspection is expensive, values are invariant)
_HOUSE_NAMES_TUPLE: tuple[Houses, ...] = get_args(Houses)
_LUNAR_PHASE_EMOJIS: tuple[LunarPhaseEmoji, ...] = get_args(LunarPhaseEmoji)
_LUNAR_PHASE_NAMES: tuple[LunarPhaseName, ...] = get_args(LunarPhaseName)


# Control characters illegal in XML 1.0 even when escaped (everything below
# 0x20 except tab/LF/CR, plus DEL/0x7F). Shared by the XML context serializer
# and the ASCII report generator so untrusted free-text fields (name/city/
# nation) cannot smuggle ESC/BEL/OSC terminal-control sequences or produce a
# document a conforming XML parser rejects.
_XML_ILLEGAL_CONTROL_CHARS = "".join(
    chr(c) for c in range(0x20) if c not in (0x09, 0x0A, 0x0D)
) + "\x7f"
_XML_ILLEGAL_TRANSLATION = {ord(c): None for c in _XML_ILLEGAL_CONTROL_CHARS}


def strip_illegal_control_chars(value) -> str:
    """Drop XML-1.0-illegal / terminal-control characters from a stringified value."""
    return str(value).translate(_XML_ILLEGAL_TRANSLATION)


# =============================================================================
# CONSTANTS AND MAPPINGS
# =============================================================================

# Maximum latitude for reliable house calculations
_POLAR_LATITUDE_LIMIT = 66.0

# Mapping of astrological point names to Swiss Ephemeris IDs.
# Canonical definition lives in `kerykeion.settings.config_constants.POINT_NUMBER_MAP`
# (shared with STANDARD_PLANETS in astrological_subject_factory). The historical
# module-private alias is preserved here for backward compatibility.
_POINT_NUMBER_MAP: dict[str, int] = _POINT_NUMBER_MAP_IMPORT

HOUSE_FIELD_NAMES: tuple[str, ...] = (
    "first_house", "second_house", "third_house", "fourth_house",
    "fifth_house", "sixth_house", "seventh_house", "eighth_house",
    "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
)

# Zodiac sign properties lookup table
_ZODIAC_SIGNS: dict[int, ZodiacSignModel] = {
    0: ZodiacSignModel(sign="Ari", quality="Cardinal", element="Fire", emoji="♈️", sign_num=0),
    1: ZodiacSignModel(sign="Tau", quality="Fixed", element="Earth", emoji="♉️", sign_num=1),
    2: ZodiacSignModel(sign="Gem", quality="Mutable", element="Air", emoji="♊️", sign_num=2),
    3: ZodiacSignModel(sign="Can", quality="Cardinal", element="Water", emoji="♋️", sign_num=3),
    4: ZodiacSignModel(sign="Leo", quality="Fixed", element="Fire", emoji="♌️", sign_num=4),
    5: ZodiacSignModel(sign="Vir", quality="Mutable", element="Earth", emoji="♍️", sign_num=5),
    6: ZodiacSignModel(sign="Lib", quality="Cardinal", element="Air", emoji="♎️", sign_num=6),
    7: ZodiacSignModel(sign="Sco", quality="Fixed", element="Water", emoji="♏️", sign_num=7),
    8: ZodiacSignModel(sign="Sag", quality="Mutable", element="Fire", emoji="♐️", sign_num=8),
    9: ZodiacSignModel(sign="Cap", quality="Cardinal", element="Earth", emoji="♑️", sign_num=9),
    10: ZodiacSignModel(sign="Aqu", quality="Fixed", element="Air", emoji="♒️", sign_num=10),
    11: ZodiacSignModel(sign="Pis", quality="Mutable", element="Water", emoji="♓️", sign_num=11),
}

# House name mappings
_HOUSE_NAMES: dict[int, Houses] = {
    1: "First_House",
    2: "Second_House",
    3: "Third_House",
    4: "Fourth_House",
    5: "Fifth_House",
    6: "Sixth_House",
    7: "Seventh_House",
    8: "Eighth_House",
    9: "Ninth_House",
    10: "Tenth_House",
    11: "Eleventh_House",
    12: "Twelfth_House",
}

_HOUSE_NUMBERS: dict[Houses, int] = {v: k for k, v in _HOUSE_NAMES.items()}


# =============================================================================
# LOGGING UTILITIES
# =============================================================================


def setup_logging(level: str) -> None:
    """
    Configure the root logger for consistent formatting across the library.

    Args:
        level: Logging level as string (debug, info, warning, error, critical).
               Case-insensitive. Defaults to INFO if invalid.
    """
    normalized_level = (level or "").strip().lower()
    level_map: dict[str, int] = {
        "debug": DEBUG,
        "info": INFO,
        "warning": WARNING,
        "error": ERROR,
        "critical": CRITICAL,
    }

    selected_level = level_map.get(normalized_level, INFO)
    basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=selected_level,
    )
    logger.setLevel(selected_level)


# =============================================================================
# ZODIAC AND POINT UTILITIES
# =============================================================================


def normalize_zodiac_type(value: str) -> ZodiacType:
    """
    Normalize a zodiac type string to its canonical representation.

    Handles case-insensitive matching and legacy formats like "tropic" or "Tropic",
    automatically converting them to the canonical forms "Tropical" or "Sidereal".

    Args:
        value: Input zodiac type string (case-insensitive).

    Returns:
        ZodiacType: Canonical zodiac type ("Tropical" or "Sidereal").

    Raises:
        ValueError: If `value` is not a recognized zodiac type.

    Examples:
        >>> normalize_zodiac_type("tropical")
        'Tropical'
        >>> normalize_zodiac_type("Tropic")
        'Tropical'
        >>> normalize_zodiac_type("SIDEREAL")
        'Sidereal'
    """
    value_lower = value.lower()

    if value_lower in ("tropical", "tropic"):
        return cast(ZodiacType, "Tropical")
    elif value_lower == "sidereal":
        return cast(ZodiacType, "Sidereal")
    else:
        raise ValueError(
            f"'{value}' is not a valid zodiac type. Accepted values are: Tropical, Sidereal "
            "(case-insensitive, 'tropic' also accepted as legacy)."
        )


def get_number_from_name(name: AstrologicalPoint) -> int:
    """
    Convert an astrological point name to its corresponding numerical identifier.

    Args:
        name: The name of the astrological point

    Returns:
        The numerical identifier used in Swiss Ephemeris calculations

    Raises:
        KerykeionException: If the name is not recognized
    """
    try:
        return _POINT_NUMBER_MAP[str(name)]
    except KeyError as exc:
        raise KerykeionException(f"Error in getting number from name! Name: {name}") from exc


def get_kerykeion_point_from_degree(
    degree: Union[int, float],
    name: Union[AstrologicalPoint, Houses],
    point_type: PointType,
    speed: Optional[float] = None,
    declination: Optional[float] = None,
    magnitude: Optional[float] = None,
    ecliptic_latitude: Optional[float] = None,
) -> KerykeionPointModel:
    """
    Create a KerykeionPointModel from a degree position.

    Args:
        degree: The degree position (0-360, negative values are converted to positive)
        name: The name of the celestial point or house
        point_type: The type classification of the point
        speed: The velocity/speed of the celestial point in degrees per day (optional)
        declination: The declination of the celestial point in degrees (optional)
        magnitude: The apparent visual magnitude for fixed stars (optional)
        ecliptic_latitude: The ecliptic latitude of the body in degrees (optional)

    Returns:
        A KerykeionPointModel with calculated zodiac sign, position, and properties

    Raises:
        KerykeionException: If degree is non-finite (NaN or infinite). Any finite
            degree (negative or >= 360) is wrapped into [0, 360), not rejected.
    """
    # A non-finite degree is a genuine calculation failure — fail loudly.
    if not math.isfinite(degree):
        raise KerykeionException(f"Error in calculating positions! Degrees: {degree}")

    # Normalize any finite degree into [0, 360). Modulo alone handles negatives
    # and values >= 360 (e.g. a positive exactly 360.0 from swe_degnorm rounding
    # on a non-pre-normalized point — axis/fixed-star/cusp — which used to abort
    # subject creation), but float64 `%` can itself return exactly 360.0 for a
    # tiny-negative input ((-1e-14) % 360 == 360.0), so fold that edge back.
    degree = degree % 360.0
    if degree >= 360.0:
        degree -= 360.0

    sign_index = int(degree // 30)
    sign_degree = degree % 30
    zodiac_sign = _ZODIAC_SIGNS[sign_index]

    return KerykeionPointModel(
        name=name,
        quality=zodiac_sign.quality,
        element=zodiac_sign.element,
        sign=zodiac_sign.sign,
        sign_num=zodiac_sign.sign_num,
        position=sign_degree,
        abs_pos=degree,
        emoji=zodiac_sign.emoji,
        point_type=point_type,
        speed=speed,
        declination=declination,
        magnitude=magnitude,
        ecliptic_latitude=ecliptic_latitude,
    )


# =============================================================================
# HOUSE UTILITIES
# =============================================================================


def is_point_between(
    start_angle: Union[int, float],
    end_angle: Union[int, float],
    candidate: Union[int, float],
    *,
    allow_reflex: bool = False,
) -> bool:
    """
    Check if a candidate angle lies on the clockwise arc from start to end angle.

    The arc is start-inclusive and end-exclusive: a candidate exactly on
    ``start`` belongs to the arc, one exactly on ``end`` does not.

    Args:
        start_angle: Starting angle in degrees
        end_angle: Ending angle in degrees
        candidate: Angle to check
        allow_reflex: When False (default) a span exceeding 180° is rejected with
            a ``KerykeionException`` (quadrant house systems never produce one).
            Set True to accept reflex arcs (> 180°), as needed by non-quadrant
            house systems (e.g. 'H' Horizon) whose cusps can span more than 180°.

    Returns:
        True if candidate is on the clockwise arc from start to end

    Raises:
        KerykeionException: If the arc exceeds 180° and ``allow_reflex`` is False
    """
    start = start_angle % 360
    end = end_angle % 360
    target = candidate % 360
    span = (end - start) % 360

    if span > 180 and not allow_reflex:
        raise KerykeionException(f"The angle between start and end point is not allowed to exceed 180°, yet is: {span}")
    if math.isclose(target, start, rel_tol=1e-9, abs_tol=1e-12):
        return True
    if math.isclose(target, end, rel_tol=1e-9, abs_tol=1e-12):
        return False
    distance_from_start = (target - start) % 360
    return distance_from_start < span


def normalize_degree(angle: Union[int, float]) -> float:
    """Normalize an angle to the range [0, 360).

    Args:
        angle (int | float): The input angle in degrees.

    Returns:
        float: The normalized angle in the range [0, 360), or NaN unchanged when
            the input is NaN - see the note below on why it is not turned into 0.
    """
    # The guard is on the *result*, not on `% 360 != 0`. For a tiny negative
    # input Python's float modulo returns exactly 360.0 (-1e-15 % 360 == 360.0),
    # which the old test read as "non-zero, therefore fine" and passed straight
    # through — breaking the [0, 360) contract this function exists to hold.
    # It matters downstream: draw_modern computes a house sector's span as
    # normalize_degree(next_cusp - cusp), so two cusps coinciding to within
    # float noise in the negative direction painted a 360° sector over the
    # whole chart instead of a degenerate one.
    result = angle % 360.0
    # `result < 360.0` is False for NaN as well as for 360.0, so a bare else
    # would quietly turn a NaN angle into 0° Aries — a plausible-looking wrong
    # position where the old expression let the NaN through to a visible `nan`
    # coordinate. Inf likewise: `inf % 360` is NaN. Propagate instead.
    if math.isnan(result):
        return result
    return result if result < 360.0 else 0.0


#: How far the twelve widths may miss a full circle and still count as covering
#: it once. Windings are 360 degrees apart, so anything short of a degree is
#: float noise rather than another turn.
_HOUSE_WINDING_TOLERANCE_DEGREES = 1e-4


#: Two longitudes closer than this are the same point: a thousandth of a
#: milliarcsecond, far below anything an ephemeris resolves or a wheel can draw.
#: It is the tolerance behind three separate questions that are really one — is
#: this point ON that cusp, are these two cusps the same cusp, is this angle its
#: own cusp — and they had three copies of the number between them.
ON_CUSP_TOLERANCE_DEGREES = 1e-9

#: Which cusp each angle IS, zero-based, in the systems that put it on one.
#:
#: Not a convention and not a lookup table of house-system identifiers kept
#: somewhere and left to rot: it is which cusp a chart's own numbers put the
#: angle on, and it is used only where that chart actually did. Quadrant systems
#: say yes for all four; equal houses say yes for the Ascendant and Descendant
#: only; whole sign, Morinus and meridian say no for one or both pairs, and there
#: the angle is a point of its own that can legitimately fall in a neighbouring
#: house.
ANGLE_CUSP_INDEX: dict[str, int] = {
    "ascendant": 0,
    "imum_coeli": 3,
    "descendant": 6,
    "medium_coeli": 9,
}


def house_spans(cusps: Sequence[float]) -> tuple[list[float], list[bool]]:
    """The twelve house widths, and which of them run against their own frame.

    Above roughly 67 degrees a Campanus, Regiomontanus, Sunshine, Polich/Page or
    APC chart puts its cusps in *descending* order, and a horizon chart does it
    on the equator: the houses genuinely run backwards through the signs. Read
    forwards, each house then measures some 354 degrees instead of 6, the twelve
    of them wind round the wheel eleven times instead of once, and everything
    that draws or centres on that span lands on the far side of the chart from
    the house it names.

    The direction belongs to the whole set and cannot be decided pair by pair.
    Reading each pair's shorter arc would answer a different question - one about
    two cusps rather than about twelve - and would have no way to tell a house
    that is genuinely wide from one that is being read backwards. Twelve widths
    cover the circle exactly once in whichever direction the houses run, so the
    total is what tells the two apart: 360 one way, 3960 the other.

    (Houses close on 180 degrees but do not pass it: the widest found by sweeping
    every system to 89.9 degrees of latitude is 179.995, under APC at 86N. The
    sibling reader get_planet_house relies on that, and this is the measurement
    behind it.)

    A third case has neither total. Polich/Page inside the polar circle returns
    cusps that are not ordered at all: at 70N the first runs backwards while the
    next five run forwards, so houses 1 and 2 overlap and no direction can make
    twelve wedges tile a circle. The chart is degenerate rather than reversed,
    and the least bad reading is to hold each wedge to its shorter arc: they
    still overlap, because the cusps do, but no single one swallows the wheel.

    Counted over 32,844 charts — all 23 systems, half a degree of latitude at a
    time, four times of day — six systems reverse outright (Campanus, horizon,
    Sunshine, Regiomontanus, Polich/Page, APC) and two go degenerate: Polich/Page
    again, and Sunshine/alt, which never reverses at all.

    Args:
        cusps: The twelve cusp positions, in house order, in any angular frame.

    Returns:
        The twelve widths, and for each the flag saying it was measured against
        the direction of the frame it was given.
    """
    forward = [normalize_degree(cusps[(index + 1) % 12] - cusps[index]) for index in range(12)]
    if abs(sum(forward) - 360.0) <= _HOUSE_WINDING_TOLERANCE_DEGREES:
        return forward, [False] * 12

    backward = [normalize_degree(cusps[index] - cusps[(index + 1) % 12]) for index in range(12)]
    if abs(sum(backward) - 360.0) <= _HOUSE_WINDING_TOLERANCE_DEGREES:
        return backward, [True] * 12

    # strict: all three are twelve long by construction, and a silent truncation
    # here would return a ring with fewer houses than it was given.
    shorter = [ahead <= behind for ahead, behind in zip(forward, backward, strict=True)]
    return (
        [
            ahead if pick else behind
            for ahead, behind, pick in zip(forward, backward, shorter, strict=True)
        ],
        [not pick for pick in shorter],
    )


def angular_separation(first_degree: float, second_degree: float) -> float:
    """How far apart two longitudes are, the short way round, in [0, 180]."""
    return abs((first_degree - second_degree + 180.0) % 360.0 - 180.0)


def angle_is_its_cusp(angle_degree: float, cusps: Sequence[float], cusp_index: int) -> bool:
    """Does this chart put this angle exactly on the cusp it shares a number with?

    Asked of the chart's own numbers rather than of a list of house-system
    identifiers: a system either lands the angle on that cusp or it does not, and
    the two longitudes say which without anyone having to maintain a table.

    ``cusp_index`` is the cusp's own index, zero-based — 0 for the Ascendant, 3
    for the Imum Coeli, 6 for the Descendant, 9 for the Midheaven, exactly as
    :data:`ANGLE_CUSP_INDEX` gives them.
    """
    return angular_separation(angle_degree, cusps[cusp_index]) < ON_CUSP_TOLERANCE_DEGREES


def angle_house_identities(
    cusps: Sequence[float], ascendant: float, medium_coeli: float
) -> dict[str, Houses]:
    """Which house each angle opens, for the angles this chart puts on a cusp.

    An angle that IS a cusp opens that house, and the chart knows which cusp each
    angle is at the moment the cusps are computed — so it says so, instead of
    handing the longitude back to a reader that has to find it again. The reader
    cannot always succeed: above the polar circle several systems crowd cusps onto
    one longitude, and Sunshine at 74.25 degrees north puts the second through the
    sixth on 316.971024. The Imum Coeli IS the fourth cusp there, bit for bit, and
    scanning twelve identical numbers answers with the earliest of them — the
    third house, in the report and in the context both.

    Nothing here invents an identity that the chart does not have. Whole sign,
    equal, Morinus and meridian charts put one or both pairs of angles off their
    numbered cusps, and for those this returns nothing and the shared reader
    answers, which is what those systems mean.

    The Descendant and the Imum Coeli are derived as the antipodes of the
    Ascendant and the Midheaven, the same way every factory derives them, so the
    identity is decided on the value the chart will actually carry.

    Args:
        cusps: The twelve cusp positions, in house order.
        ascendant: The Ascendant's longitude, as the ephemeris returned it.
        medium_coeli: The Midheaven's longitude, as the ephemeris returned it.

    Returns:
        A mapping from angle field name to the house it opens, holding only the
        angles this chart places on their own cusp. Empty for a chart that places
        none of them.
    """
    angles = {
        "ascendant": ascendant % 360.0,
        "descendant": (ascendant + 180.0) % 360.0,
        "medium_coeli": medium_coeli % 360.0,
        "imum_coeli": (medium_coeli + 180.0) % 360.0,
    }
    identities: dict[str, Houses] = {}
    for angle_name, cusp_index in ANGLE_CUSP_INDEX.items():
        if angle_is_its_cusp(angles[angle_name], cusps, cusp_index):
            identities[angle_name] = _HOUSE_NAMES_TUPLE[cusp_index]
    return identities


def cusps_are_a_house_division(cusps: Sequence[float]) -> bool:
    """Do these twelve arcs divide the circle into twelve houses?

    Asked of :func:`house_spans`, which is the library's answer to which way the
    ring runs, rather than counted here a second time.

    Covering the circle is necessary and not sufficient: a house of zero width
    adds nothing to the total, so twelve arcs can sum to 360 with two of the cusps
    on the same longitude. That is not a division into twelve houses — no point
    can ever be in a house that has no width — and it is the shape behind every
    angle filed in the wrong house.
    """
    spans, reversed_wedges = house_spans(cusps)
    if (
        len(set(reversed_wedges)) != 1
        or abs(sum(spans) - 360.0) > _HOUSE_WINDING_TOLERANCE_DEGREES
    ):
        return False
    return all(span > ON_CUSP_TOLERANCE_DEGREES for span in spans)


def coincident_cusp_groups(cusps: Sequence[float]) -> list[list[int]]:
    """The sets of house numbers whose cusps stand on the same longitude.

    House numbers are one-based, as a reader of a chart counts them. A chart whose
    twelve cusps are twelve distinct longitudes — every ordinary chart — returns an
    empty list, which is what makes this safe to carry on every subject.

    Grouping is by single linkage: a cusp joins a group when it coincides with any
    member. At a tolerance of a thousandth of a milliarcsecond the distinction from
    strict equivalence is theoretical, and the question being asked — which houses
    have no width — is answered the same way either round.
    """
    count = len(cusps)
    group_of: list[int] = list(range(count))

    def resolve(index: int) -> int:
        while group_of[index] != index:
            group_of[index] = group_of[group_of[index]]
            index = group_of[index]
        return index

    for first in range(count):
        for second in range(first + 1, count):
            if angular_separation(cusps[first], cusps[second]) < ON_CUSP_TOLERANCE_DEGREES:
                group_of[resolve(second)] = resolve(first)

    grouped: dict[int, list[int]] = {}
    for index in range(count):
        grouped.setdefault(resolve(index), []).append(index + 1)
    return sorted(
        (sorted(members) for members in grouped.values() if len(members) > 1),
        key=lambda members: members[0],
    )


def get_planet_house(planet_degree: Union[int, float], houses_degree_ut_list: list) -> Houses:
    """
    Determine which house contains a planet based on its degree position.

    Args:
        planet_degree: The planet's position in degrees (0-360)
        houses_degree_ut_list: List of house cusp degrees

    Returns:
        The house name containing the planet

    Raises:
        ValueError: If the planet's position doesn't fall within any house range
    """
    n = len(_HOUSE_NAMES_TUPLE)
    # A house is the arc from its own cusp to the NEXT cusp, but the cusps do
    # not always run in increasing longitude: some systems return them in
    # decreasing (clockwise) order — notably 'H' Horizon near the equator and
    # 'T' Polich-Page at high latitude — and quadrant systems can go
    # non-monotonic near the poles. Assuming a forward (increasing) arc there
    # turns house 1 into a ~350° reflex arc that swallows every planet. Instead,
    # a point belongs to the house whose cusp→next-cusp arc contains it via the
    # SHORTEST path (the real house span is always < 180°); a point exactly on a
    # cusp belongs to the house that cusp opens.
    # The NEAREST cusp within the tolerance, not the first one found. Above the
    # polar circle several systems crowd three cusps into a few hundredths of a
    # nanodegree: Sunshine at 89S puts the eighth, ninth and tenth within 6.6e-11
    # of each other, and the Midheaven is the tenth exactly. Scanning upwards and
    # taking the first match filed it in the eighth.
    #
    # Nearest is as far as twelve numbers can take it. Where several cusps are
    # bit-identical — Sunshine at 74.25 degrees north puts the second through the
    # sixth on one longitude — they are all equally near, and no rule written over
    # this list can say which of them a point standing there opens. The answer is
    # not in the list: it is in what the point IS, which the ephemeris knows when
    # it returns the cusps and the angles together. So the four angles do not come
    # through here any more; they are given their house by angle_house_identities
    # where the cusps are made. What still arrives here is an ordinary point
    # standing on a crowd of cusps, for which no answer is more right than
    # another, and it gets the lowest-numbered one.
    on_cusp = [(angular_separation(planet_degree, houses_degree_ut_list[i]), i) for i in range(n)]
    closest, index = min(on_cusp)
    if closest < ON_CUSP_TOLERANCE_DEGREES:
        return _HOUSE_NAMES_TUPLE[index]

    # Where the twelve ARE a house division, ask the one function that decides
    # that — the same one the wheel is drawn from. Choosing the shorter arc for
    # each pair independently is the right rule only on a ring that is not a
    # division: on one that is, it can contradict the division itself. Twelve
    # cusps at 0, 200, 210 … 300 run forwards and total 360, with a first house
    # 200 degrees wide; read pair by pair, that house becomes the opposite 160
    # degrees and longitude 100 — inside it, and drawn inside it — belongs to no
    # house at all. No real chart reaches this (the widest arc measured across 23
    # systems and nine latitudes is 179.2388 degrees) but the two functions
    # disagreeing about the same ring is worth closing, not documenting.
    spans, reversed_wedges = house_spans(houses_degree_ut_list)
    if len(set(reversed_wedges)) == 1 and abs(sum(spans) - 360.0) <= _HOUSE_WINDING_TOLERANCE_DEGREES:
        for i in range(n):
            if spans[i] <= 0.0:
                continue
            start = houses_degree_ut_list[i]
            offset = (start - planet_degree) % 360.0 if reversed_wedges[i] else (planet_degree - start) % 360.0
            if offset < spans[i]:
                return _HOUSE_NAMES_TUPLE[i]

    best_index = None
    best_span = 360.0 + 1.0
    for i in range(n):
        start = houses_degree_ut_list[i]
        end = houses_degree_ut_list[(i + 1) % n]
        fwd = (end - start) % 360.0
        if fwd == 0:
            continue  # coincident cusps can't contain a point in their arc
        # Distance from the cusp to the point, in whichever direction the arc
        # to the next cusp actually runs (forward if fwd is the short way,
        # backward otherwise).
        if fwd <= 180.0:
            inside = (planet_degree - start) % 360.0 < fwd
            span = fwd
        else:
            back = 360.0 - fwd
            inside = (start - planet_degree) % 360.0 < back
            span = back
        if inside and span < best_span:
            best_index = i
            best_span = span

    if best_index is not None:
        return _HOUSE_NAMES_TUPLE[best_index]

    raise ValueError(f"Error in house calculation, planet: {planet_degree}, houses: {houses_degree_ut_list}")


def get_house_name(house_number: int) -> Houses:
    """
    Convert a house number to its corresponding house name.

    Args:
        house_number: House number (1-12)

    Returns:
        The house name

    Raises:
        ValueError: If house_number is not in range 1-12
    """
    name = _HOUSE_NAMES.get(house_number, None)
    if name is None:
        raise ValueError(f"Invalid house number: {house_number}")
    return name


def get_house_number(house_name: Houses) -> int:
    """
    Convert a house name to its corresponding house number.

    Args:
        house_name: The house name

    Returns:
        House number (1-12)

    Raises:
        ValueError: If house_name is not recognized
    """
    number = _HOUSE_NUMBERS.get(house_name, None)
    if number is None:
        raise ValueError(f"Invalid house name: {house_name}")
    return number


def get_houses_list(
    subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
) -> list[KerykeionPointModel]:
    """
    Get a list of house objects in order from the subject.

    Args:
        subject: The astrological subject containing house data

    Returns:
        List of KerykeionPointModel objects representing the houses
    """
    houses_absolute_position_list = []
    for house in subject.houses_names_list:
        houses_absolute_position_list.append(subject[house.lower()])

    return houses_absolute_position_list


def get_available_astrological_points_list(subject: AstrologicalSubjectModel) -> list[KerykeionPointModel]:
    """
    Get a list of active astrological point objects from the subject.

    Args:
        subject: The astrological subject containing point data

    Returns:
        List of KerykeionPointModel objects for all active points
    """
    planets_absolute_position_list = []
    for planet in subject.active_points:
        planets_absolute_position_list.append(subject[planet.lower()])

    return planets_absolute_position_list


def find_common_active_points(
    first_points: list[AstrologicalPoint], second_points: list[AstrologicalPoint]
) -> list[AstrologicalPoint]:
    """
    Find astrological points that appear in both input lists.

    Args:
        first_points: First list of astrological points
        second_points: Second list of astrological points

    Returns:
        List of points common to both input lists (without duplicates),
        preserving the conventional astrological order of ``first_points``
        (Sun, Moon, Mercury, ...) rather than sorting alphabetically — so a
        dual chart's active_points read in the same order as a single chart's.
    """
    common = set(second_points)
    seen: set = set()
    result = []
    for point in first_points:
        if point in common and point not in seen:
            seen.add(point)
            result.append(point)
    return result


# =============================================================================
# LUNAR PHASE UTILITIES
# =============================================================================


# The name windows are CENTRED on the event they name, and each is exactly as
# wide as the name it replaces already was under the 28-bin scheme — only its
# position moved.
#
# The 1-28 lunation day is a bin index: bin 1 is [0°, 12.857°), so the old
# name lookup gave "New Moon" to the twelve and a half degrees that FOLLOW the
# conjunction and nothing before it, "Full Moon" to bin 14 = [167.143°, 180°)
# which ENDS at the opposition, and three bins each to the quarters, likewise
# offset. The measured cost: on the 365 historically-verified syzygies of
# tests/core/test_moon_phase_historical_verification.py, 95 instants carried
# the wrong name — a minute after the exact full moon the chart read "Waning
# Gibbous" beside an illumination of 100%.
#
# Half of one bin either side of the syzygies (12.857° in total, bin 1's width)
# and one and a half bins either side of the quarters (38.571° in total, the
# width of bins 7-9), so no window grew or shrank: 14.29% of the circle answers
# with a different name than it did, and the four events sit at the centre of
# the window that names them.
_LUNAR_BIN_WIDTH = 360.0 / 28.0
#: Half-width of the New/Full Moon windows — half a bin, i.e. bin 1's width shared.
_SYZYGY_HALF_WIDTH = _LUNAR_BIN_WIDTH / 2.0
#: Half-width of the quarter windows — one and a half bins, i.e. the three bins
#: the quarters already spanned, shared around 90° and 270°.
_QUARTER_HALF_WIDTH = 3.0 * _LUNAR_BIN_WIDTH / 2.0

#: Upper bound (exclusive) of each name's window, in the order of
#: :data:`_LUNAR_PHASE_NAMES`. The last window ends at 360° - half a bin; past it
#: the separation has wrapped back into the New Moon window that straddles 0°.
_LUNAR_PHASE_WINDOW_UPPER_BOUNDS: tuple[float, ...] = (
    _SYZYGY_HALF_WIDTH,  # New Moon      [353.571, 6.429)
    90.0 - _QUARTER_HALF_WIDTH,  # Waxing Crescent  [6.429, 70.714)
    90.0 + _QUARTER_HALF_WIDTH,  # First Quarter    [70.714, 109.286)
    180.0 - _SYZYGY_HALF_WIDTH,  # Waxing Gibbous   [109.286, 173.571)
    180.0 + _SYZYGY_HALF_WIDTH,  # Full Moon        [173.571, 186.429)
    270.0 - _QUARTER_HALF_WIDTH,  # Waning Gibbous   [186.429, 250.714)
    270.0 + _QUARTER_HALF_WIDTH,  # Last Quarter     [250.714, 289.286)
    360.0 - _SYZYGY_HALF_WIDTH,  # Waning Crescent  [289.286, 353.571)
)

#: The four major phases and the separation each happens at. Order matters: an
#: exactly equidistant separation (45°, 135°, 225°, 315°) resolves to the first
#: of the two it ties between, which is the behaviour the moon-phase overview
#: has always had.
_LUNAR_MAJOR_PHASES: tuple[tuple[float, LunarPhaseName], ...] = (
    (0.0, "New Moon"),
    (90.0, "First Quarter"),
    (180.0, "Full Moon"),
    (270.0, "Last Quarter"),
)


def lunar_phase_name_from_degrees(degrees: float) -> tuple[LunarPhaseName, LunarPhaseEmoji]:
    """
    Name and emoji of the lunar phase for a Sun-Moon separation.

    The eight windows are centred on the events they name: a separation within
    half a bin of 0° or 180° is a New or Full Moon, one within one and a half
    bins of 90° or 270° is a quarter, and the four intermediate names hold the
    rest. So a minute either side of an exact syzygy reads the same, which is
    what an ephemeris, an almanac and the illumination percentage all say.

    This is the source the name comes from. The 1-28 lunation day
    (:func:`get_moon_phase_name_from_phase_int`) is a coarser, offset partition
    of the same circle and is kept only for callers that have the integer and
    not the degrees.

    Args:
        degrees: Anti-clockwise separation Moon - Sun, in degrees. Any real
            number: it is reduced modulo 360 first.

    Returns:
        A ``(name, emoji)`` pair.
    """
    angle = degrees % 360.0
    for index, upper_bound in enumerate(_LUNAR_PHASE_WINDOW_UPPER_BOUNDS):
        if angle < upper_bound:
            return _LUNAR_PHASE_NAMES[index], _LUNAR_PHASE_EMOJIS[index]

    # Past the last bound the angle is in [353.571, 360) — the upper half of the
    # New Moon window, which straddles 0°.
    return _LUNAR_PHASE_NAMES[0], _LUNAR_PHASE_EMOJIS[0]


def lunar_major_phase_from_degrees(degrees: float) -> LunarPhaseName:
    """
    The nearest of the four major phases to a Sun-Moon separation.

    Unlike :func:`lunar_phase_name_from_degrees`, which can answer with any of
    the eight names, this always answers New Moon, First Quarter, Full Moon or
    Last Quarter — the quarter of the cycle the moment belongs to.

    Args:
        degrees: Anti-clockwise separation Moon - Sun, in degrees.

    Returns:
        One of the four major phase names.
    """
    angle = degrees % 360.0

    def angular_distance(a: float, b: float) -> float:
        diff = (a - b) % 360.0
        return min(diff, 360.0 - diff)

    return min(_LUNAR_MAJOR_PHASES, key=lambda item: angular_distance(angle, item[0]))[1]


def lunar_stage_from_degrees(degrees: float) -> LunarPhaseStage:
    """
    Whether the Moon is waxing or waning at a given Sun-Moon separation.

    Args:
        degrees: Anti-clockwise separation Moon - Sun, in degrees.

    Returns:
        ``"waxing"`` on [0°, 180°) — the light is growing — and ``"waning"``
        on [180°, 360°).
    """
    return "waxing" if 0.0 <= degrees % 360.0 < 180.0 else "waning"


def _get_lunar_phase_index(phase: int) -> int:
    """
    Get the index for lunar phase lookup based on phase number.

    Args:
        phase: The lunar phase number (1-28)

    Returns:
        Index (0-7) for lunar phase lookup arrays

    Raises:
        KerykeionException: If phase is outside valid range
    """
    if phase < 1:
        # Valid phases are 1-28; without this, phase <= 0 (and negatives) fell
        # through the `phase < 7` branch and returned Waxing Crescent instead
        # of raising as the docstring promises.
        raise KerykeionException(f"Error in lunar phase calculation! Phase: {phase}")
    if phase == 1:
        return 0
    elif phase < 7:
        return 1
    elif 7 <= phase <= 9:
        return 2
    elif phase < 14:
        return 3
    elif phase == 14:
        return 4
    elif phase < 20:
        return 5
    elif 20 <= phase <= 22:
        return 6
    elif phase <= 28:
        return 7
    else:
        raise KerykeionException(f"Error in lunar phase calculation! Phase: {phase}")


def get_moon_emoji_from_phase_int(phase: int) -> LunarPhaseEmoji:
    """
    Get the emoji representation of a lunation day.

    APPROXIMATE, and kept only for callers that hold the 1-28 integer and not
    the separation in degrees. The bins are offset from the events: bin 1 begins
    at the conjunction instead of straddling it and bin 14 ends at the
    opposition, so a full moon can land one bin past 🌕. Anything that has the
    degrees must call :func:`lunar_phase_name_from_degrees`, which is what
    :func:`calculate_moon_phase` does.

    Args:
        phase: The lunation day (1-28)

    Returns:
        The emoji for that lunation day, to a resolution of 12.857°

    Raises:
        KerykeionException: If phase is outside valid range
    """
    index = _get_lunar_phase_index(phase)
    return _LUNAR_PHASE_EMOJIS[index]


def get_moon_phase_name_from_phase_int(phase: int) -> LunarPhaseName:
    """
    Get the name of a lunar phase from its lunation day.

    APPROXIMATE, and kept only for callers that hold the 1-28 integer and not
    the separation in degrees — see :func:`get_moon_emoji_from_phase_int` for
    why the two disagree near an event. Anything that has the degrees must call
    :func:`lunar_phase_name_from_degrees`.

    Args:
        phase: The lunation day (1-28)

    Returns:
        The name for that lunation day, to a resolution of 12.857°

    Raises:
        KerykeionException: If phase is outside valid range
    """
    index = _get_lunar_phase_index(phase)
    return _LUNAR_PHASE_NAMES[index]


def validate_latitude(latitude: float) -> float:
    """
    Validate that a latitude lies within the geometrically-possible range.

    Returns the latitude UNCHANGED when valid. Unlike
    :func:`check_and_adjust_polar_latitude`, this does NOT clamp polar latitudes
    to the ±66° house-stability limit: the real observer latitude must survive
    into the persisted model, into the topocentric observer (``set_topo``), and
    into every house system that is defined at all latitudes (Whole Sign,
    Equal, Porphyry, Morinus, Meridian/axial, …). A house system that is
    undefined there is substituted *locally* at the house call — see
    :func:`kerykeion.ephemeris_backend.backend.houses_ex2_with_polar_fallback`.

    Args:
        latitude: The latitude value to validate.

    Returns:
        The latitude value unchanged.

    Raises:
        KerykeionException: If the latitude is geometrically impossible
            (outside [-90, 90]) — a corrupt/mistyped value, not a polar one.
    """
    # Reject geometrically-impossible latitudes (a mistyped lat=100 is a corrupt
    # value, not a polar one). The ephemeris backend validates this symmetrically
    # with longitude.
    if not -90.0 <= latitude <= 90.0:
        raise KerykeionException(
            f"Latitude {latitude} is out of range; it must be between -90 and 90 degrees."
        )
    return latitude


def validate_longitude(longitude: float) -> float:
    """Validate a geographic longitude without wrapping or clamping it.

    Args:
        longitude: Longitude in degrees, east positive.

    Returns:
        The longitude unchanged.

    Raises:
        KerykeionException: If the longitude is non-finite or outside
            the geometrically valid [-180, 180] interval.
    """
    if not -180.0 <= longitude <= 180.0:
        raise KerykeionException(
            f"Longitude {longitude} is out of range; it must be between -180 and 180 degrees."
        )
    return longitude


def check_and_adjust_polar_latitude(latitude: float) -> float:
    """
    Clamp a polar latitude to the ±66° limit for house-calculation stability.

    NARROW USE ONLY. This is no longer the general fallback for a quadrant house
    system inside the polar circle: moving the observer keeps the house count but
    reports cusps for a place the subject was not born in, so the house call now
    substitutes a system that IS defined at every latitude (see
    :func:`kerykeion.ephemeris_backend.backend.houses_ex2_with_polar_fallback`, whose
    default ``polar_strategy`` does exactly that) and records the substitution.

    The clamp survives only where substitution is impossible because the output
    shape itself is what the caller needs: the 36 Gauquelin sector cusps have no
    12-cusp equivalent, so that call opts back in explicitly. It must NOT be used
    to sanitise the observer latitude globally: doing so corrupts the persisted
    latitude, shifts the topocentric observer, and wrongly translates the cusps of
    house systems that ARE defined at every latitude. Use
    :func:`validate_latitude` for plain range validation.

    Args:
        latitude: The original latitude value

    Returns:
        The adjusted latitude value, clamped between -66° and 66°

    Raises:
        KerykeionException: If the latitude is geometrically impossible
            (outside [-90, 90]) — a corrupt/mistyped value, not a polar one.
    """
    latitude = validate_latitude(latitude)
    if latitude > _POLAR_LATITUDE_LIMIT:
        latitude = _POLAR_LATITUDE_LIMIT
        logger.info(f"Latitude capped at {_POLAR_LATITUDE_LIMIT:.0f}° to keep house calculations stable.")

    elif latitude < -_POLAR_LATITUDE_LIMIT:
        latitude = -_POLAR_LATITUDE_LIMIT
        logger.info(f"Latitude capped at -{_POLAR_LATITUDE_LIMIT:.0f}° to keep house calculations stable.")

    return latitude


def resolve_sect_is_diurnal(subject: Any) -> bool:
    """Sect (day/night) of a subject-like model, defaulting to day.

    ``is_diurnal`` may be absent (hand-built objects) or ``None`` (midpoint
    composites, which have no single sky). Both must resolve to the day-chart
    default: sect consumers historically used ``getattr(subject,
    "is_diurnal", True)``, and when the field became a declared
    ``Optional[bool]`` a bare ``bool(None)`` would silently flip those charts
    to the night branch (changing e.g. the Part of Fortune formula).
    """
    value = getattr(subject, "is_diurnal", None)
    return True if value is None else bool(value)


def resolve_subject_birth_datetime(subject: Any) -> datetime:
    """Local (naive) birth/anchor datetime of a subject-like model.

    ``AstrologicalSubjectModel`` carries split ``year/month/day/hour/minute``
    components; ``PlanetReturnModel`` and ``CompositeSubjectModel`` don't
    (getattr on them would raise a raw AttributeError), but a return or
    Davison chart is still a real moment in time — fall back to their local
    ISO timestamp. A midpoint composite carries neither and is rejected:
    it has no single moment for a time-lord timeline to anchor to.

    Raises:
        KerykeionException: When the subject has no usable moment or its
            fields cannot be parsed into one.
    """
    if getattr(subject, "year", None) is not None:
        try:
            return datetime(subject.year, subject.month, subject.day, subject.hour, subject.minute)
        except (TypeError, ValueError) as exc:
            raise KerykeionException(f"Invalid birth date on subject: {exc}") from exc

    iso = getattr(subject, "iso_formatted_local_datetime", None) or getattr(
        subject, "iso_formatted_utc_datetime", None
    )
    if iso is None:
        raise KerykeionException(
            "Subject carries neither birth-date components nor an ISO "
            "timestamp — cannot anchor a time-lord timeline (midpoint "
            "composites have no single moment in time)."
        )
    try:
        return datetime.fromisoformat(iso).replace(tzinfo=None)
    except ValueError as exc:
        raise KerykeionException(
            f"Cannot parse the subject's ISO timestamp {iso!r}: {exc}"
        ) from exc


def resolve_subject_local_now(subject: Any) -> datetime:
    """Current wall-clock time in the subject's own timezone, as a naive datetime.

    Time-lord timelines (profections, firdaria) are built from the subject's
    *local* birth moment, so "which period contains today" must compare
    against today in that same local frame — using the server's clock frame
    would shift period boundaries by up to a day. Falls back to UTC when the
    subject carries no usable timezone.
    """
    tz_str = getattr(subject, "tz_str", None)
    if tz_str:
        try:
            return datetime.now(ZoneInfo(tz_str)).replace(tzinfo=None)
        except (ZoneInfoNotFoundError, ValueError):
            # ZoneInfo raises ValueError for structurally invalid keys (e.g.
            # absolute paths, ".."), ZoneInfoNotFoundError for unknown zones —
            # both mean the same thing here: no usable subject timezone.
            logger.warning(f"Unknown timezone {tz_str!r} on subject; using UTC for the current moment.")
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── Proleptic-Gregorian civil-date helpers (BCE-safe) ────────────────────────
# Python's datetime/date stop at year 1, but supported subjects reach deep
# BCE (astronomical numbering: 0 = 1 BCE). Time-lord timelines therefore do
# their date arithmetic on Julian Days via the ephemeris backend, which is
# calendar-exact and unbounded, and only FORMAT dates as ISO strings.

_ANCIENT_ISO_RE = re.compile(
    r"^(?P<year>-?\d{1,6})-(?P<month>\d{2})-(?P<day>\d{2})"
    r"(?:[T ](?P<hour>\d{2}):(?P<minute>\d{2})(?::(?P<second>\d{2}(?:\.\d+)?))?)?"
)


def format_astronomical_iso_date(year: int, month: int, day: int) -> str:
    """``YYYY-MM-DD`` with astronomical year numbering (0 = 1 BCE, -1 = 2 BCE)."""
    if year < 0:
        return f"-{abs(year):04d}-{month:02d}-{day:02d}"
    return f"{year:04d}-{month:02d}-{day:02d}"


# JD of 0001-01-01 00:00 proleptic Gregorian — the seam of the engine's
# calendar convention (verified against ephe.julday(1, 1, 1, 0.0, GREG_CAL)).
_GREGORIAN_CE_EPOCH_JD = 1721425.5

_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def civil_leap_year(year: int) -> bool:
    """Leap rule in the engine's calendar convention for ``year``.

    Mirrors the subject factory's asymmetry: ``year < 1`` dates are
    Julian-calendar (leap every fourth astronomical year, century years
    included), ``year >= 1`` is proleptic Gregorian.
    """
    if year < 1:
        return year % 4 == 0
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def jd_to_iso_date(jd: float) -> str:
    """ISO date of a Julian Day in the engine's calendar convention (BCE-safe).

    Instants before 1 CE format as Julian-calendar dates, from 1 CE on as
    proleptic Gregorian — the same asymmetry the subject factory applies to
    its inputs, so a timeline's boundary dates and the chart's own dates
    share one convention. A timeline crossing 1 CE shows the calendar seam
    (Julian labels run about two days ahead there); the seam belongs to the
    convention, not to the arithmetic.
    """
    from kerykeion.ephemeris_backend.backend import ephe

    cal_flag = ephe.JUL_CAL if jd < _GREGORIAN_CE_EPOCH_JD else ephe.GREG_CAL
    year, month, day, _hour = ephe.revjul(jd, cal_flag)
    return format_astronomical_iso_date(int(year), int(month), int(day))


def jd_to_iso_datetime(jd: float) -> str:
    """ISO datetime (second resolution) of a Julian Day, BCE-safe.

    Same calendar convention as :func:`jd_to_iso_date`. The instant is
    rounded half-up to the whole second (a half-second nudge before the
    floor), so boundaries computed as fractional Julian Days serialize to
    the very instant a same-grid selection compares against.
    """
    from kerykeion.ephemeris_backend.backend import ephe

    nudged = jd + 0.5 / 86400.0
    cal_flag = ephe.JUL_CAL if nudged < _GREGORIAN_CE_EPOCH_JD else ephe.GREG_CAL
    year, month, day, dec_hour = ephe.revjul(nudged, cal_flag)
    total_seconds = int(dec_hour * 3600.0)
    hour, remainder = divmod(total_seconds, 3600)
    minute, second = divmod(remainder, 60)
    date_part = format_astronomical_iso_date(int(year), int(month), int(day))
    return f"{date_part}T{hour:02d}:{minute:02d}:{second:02d}"


def civil_jd(year: int, month: int, day: int, hour: float = 0.0) -> float:
    """Julian Day of a civil moment in the engine's calendar convention (BCE-safe).

    Mirrors the subject factory's asymmetric convention: components with
    ``year < 1`` are Julian-calendar dates (every BCE date predates the
    Gregorian reform), ``year >= 1`` is proleptic Gregorian. A single fixed
    calendar here would anchor a BCE timeline days away from the chart's
    own instant (six days at year -562).

    The backend's ``julday`` also normalizes overflowing components the way
    civil calendars do — February 29 of a common year rolls to March 1 —
    which is exactly the anniversary convention the time-lord techniques use.
    """
    from kerykeion.ephemeris_backend.backend import ephe

    cal_flag = ephe.JUL_CAL if year < 1 else ephe.GREG_CAL
    return ephe.julday(int(year), int(month), int(day), float(hour), cal_flag)


def parse_astronomical_iso_moment(value: str) -> tuple[int, int, int, float]:
    """Parse a timezone-naive ISO date/datetime, astronomical years included.

    ``datetime.fromisoformat`` rejects the astronomical year numbering
    (``-0550-10-07``) the engine itself emits for BCE moments, so target
    dates for the time-lord techniques go through this parser instead.
    Returns ``(year, month, day, hour_float)`` with seconds folded into the
    hour fraction. Timezone-aware values are rejected: the techniques
    compare in the subject's local civil frame, and an explicit offset
    would silently name a different instant.

    Raises:
        KerykeionException: On unparseable input, out-of-range components,
            or a timezone-aware value.
    """
    text = str(value).strip()
    match = _ANCIENT_ISO_RE.match(text)
    rest = text[match.end() :] if match else ""
    if match and rest and rest[0] in "+-Zz":
        raise KerykeionException(
            f"target_date {value!r} must be timezone-naive "
            "(pass a bare ISO date, e.g. '2026-06-04')."
        )
    if not match or rest:
        raise KerykeionException(
            f"Invalid target_date {value!r} (expected ISO YYYY-MM-DD; "
            "astronomical year numbering accepted, e.g. '-0550-10-07')."
        )
    year = int(match.group("year"))
    month = int(match.group("month"))
    day = int(match.group("day"))
    hour = int(match.group("hour") or 0)
    minute = int(match.group("minute") or 0)
    second = float(match.group("second") or 0.0)
    if not (1 <= month <= 12 and hour <= 23 and minute <= 59 and second < 60):
        raise KerykeionException(
            f"Invalid target_date {value!r}: date/time component out of range."
        )
    # Impossible calendar days (2026-02-31, 2025-02-29) must not silently
    # normalize into another date; the leap rule follows the calendar
    # convention of the year (Julian below 1 CE, Gregorian from 1 CE).
    days_in_month = 29 if month == 2 and civil_leap_year(year) else _DAYS_IN_MONTH[month - 1]
    if not (1 <= day <= days_in_month):
        raise KerykeionException(
            f"Invalid target_date {value!r}: date/time component out of range."
        )
    return year, month, day, hour + minute / 60.0 + second / 3600.0


def resolve_subject_local_moment(subject: Any) -> tuple[int, int, int, float]:
    """Local (wall-clock) birth/anchor components of a subject-like model.

    Returns ``(year, month, day, hour_float)`` without ever building a
    ``datetime``, so BCE subjects work. Split-component subjects are read
    directly; ISO-only subjects (returns, Davison) are parsed at face value,
    negative years included. Seconds are retained in the hour fraction: the
    subject model carries no split seconds field, so when the subject lacks
    a ``seconds`` attribute they are recovered from the local ISO timestamp
    (which preserves them). A midpoint composite carries neither and is
    rejected: it has no single moment for a time-lord timeline to anchor to.

    Raises:
        KerykeionException: When the subject has no usable moment.
    """
    if getattr(subject, "year", None) is not None:
        try:
            seconds = getattr(subject, "seconds", None)
            if seconds is None:
                iso_local = getattr(subject, "iso_formatted_local_datetime", None)
                iso_match = _ANCIENT_ISO_RE.match(str(iso_local)) if iso_local else None
                seconds = float(iso_match.group("second") or 0.0) if iso_match else 0.0
            return (
                int(subject.year),
                int(subject.month),
                int(subject.day),
                float(subject.hour) + float(subject.minute) / 60.0 + float(seconds) / 3600.0,
            )
        except (TypeError, ValueError) as exc:
            raise KerykeionException(f"Invalid birth date on subject: {exc}") from exc

    iso = getattr(subject, "iso_formatted_local_datetime", None) or getattr(
        subject, "iso_formatted_utc_datetime", None
    )
    if iso is None:
        raise KerykeionException(
            "Subject carries neither birth-date components nor an ISO "
            "timestamp — cannot anchor a time-lord timeline (midpoint "
            "composites have no single moment in time)."
        )
    match = _ANCIENT_ISO_RE.match(str(iso))
    if not match:
        raise KerykeionException(f"Cannot parse the subject's ISO timestamp {iso!r}.")
    hour = (
        int(match.group("hour") or 0)
        + int(match.group("minute") or 0) / 60.0
        + float(match.group("second") or 0.0) / 3600.0
    )
    return (int(match.group("year")), int(match.group("month")), int(match.group("day")), hour)


# Perspectives whose planet longitudes share the Earth frame of the angles
# and houses. Techniques built on house cusps, angles, house placements or
# sign rulership read the chart as seen from Earth; a chart measured from
# another origin (Heliocentric, Barycentric, Selenocentric, planetocentric)
# would feed them plausible-looking but frame-inconsistent data.
TERRESTRIAL_PERSPECTIVES = frozenset({"Apparent Geocentric", "True Geocentric", "Topocentric"})


def has_terrestrial_frame(subject: Any) -> bool:
    """Whether the subject's planet longitudes share the angles' Earth frame.

    A subject that carries no ``perspective_type`` at all is trusted:
    duck-typed inputs default to the geocentric contract.
    """
    perspective = getattr(subject, "perspective_type", None)
    return perspective is None or str(perspective) in TERRESTRIAL_PERSPECTIVES


def require_same_frame(first: Any, second: Any) -> None:
    """
    Reject two subjects whose astrological reference frame differs.

    Aspects, synastry, transits, relationship scores and house overlays between
    two charts are only meaningful when both charts are cast in the same
    reference frame. Mixing e.g. a Tropical chart with a Sidereal (Lahiri) one
    compares longitudes measured from different zero points and silently yields
    aspects/scores that look plausible but are astronomically meaningless (a
    tropical×sidereal pair reports dozens of spurious aspects for the same sky).

    Mirrors the frame checks ``CompositeSubjectFactory`` already performs:
    ``zodiac_type``, ``perspective_type`` and — only for Sidereal charts —
    ``sidereal_mode`` (plus the custom ayanamsa epoch/offset when
    ``sidereal_mode`` is ``'USER'``). The house-system identifier is NOT checked
    here: it is irrelevant to inter-chart aspects and house overlays legitimately
    compare two subjects using different house systems.

    Inputs that do not expose ``zodiac_type`` at all (e.g. ``None``) are
    rejected up front: hand-built ``CompositeSubjectModel`` /
    ``PlanetReturnModel`` inputs are fine (the frame fields live on the shared
    base model), but a non-subject input must fail here with a clear message
    rather than crash later with a raw ``AttributeError`` in a consumer.

    Args:
        first: The first subject (any model exposing the frame attributes).
        second: The second subject.

    Raises:
        KerykeionException: If either input is not a subject-like model
            (missing the frame attributes), or if the two subjects do not
            share the same frame.
    """
    _MISSING = object()
    first_zodiac = getattr(first, "zodiac_type", _MISSING)
    second_zodiac = getattr(second, "zodiac_type", _MISSING)
    if first_zodiac is _MISSING or second_zodiac is _MISSING:
        # Not a subject-like model at all (e.g. None). Without this check two
        # frameless inputs would compare equal (sentinel == sentinel) and slip
        # through, crashing later with a raw AttributeError deep in a consumer.
        _offenders = [
            type(obj).__name__
            for obj, zodiac in ((first, first_zodiac), (second, second_zodiac))
            if zodiac is _MISSING
        ]
        raise KerykeionException(
            f"require_same_frame: input(s) of type {_offenders} do not expose the "
            "chart frame attributes (zodiac_type/perspective_type); expected "
            "astrological subject models."
        )
    if first_zodiac != second_zodiac:
        raise KerykeionException(
            "Both subjects must share the same zodiac_type to be compared "
            f"(got {first_zodiac!r} and {second_zodiac!r}); a Tropical chart and "
            "a Sidereal chart measure longitudes from different zero points, so "
            "their aspects would be meaningless."
        )

    first_perspective = getattr(first, "perspective_type", _MISSING)
    second_perspective = getattr(second, "perspective_type", _MISSING)
    if first_perspective != second_perspective:
        raise KerykeionException(
            "Both subjects must share the same perspective_type to be compared "
            f"(got {first_perspective!r} and {second_perspective!r})."
        )

    # sidereal_mode / custom ayanamsa only pin the zero point for Sidereal charts.
    if first_zodiac == "Sidereal":
        first_mode = getattr(first, "sidereal_mode", None)
        second_mode = getattr(second, "sidereal_mode", None)
        if first_mode != second_mode:
            raise KerykeionException(
                "Both subjects must share the same sidereal_mode to be compared "
                f"(got {first_mode!r} and {second_mode!r})."
            )
        if first_mode == "USER" and (
            getattr(first, "custom_ayanamsa_t0", None) != getattr(second, "custom_ayanamsa_t0", None)
            or getattr(first, "custom_ayanamsa_ayan_t0", None) != getattr(second, "custom_ayanamsa_ayan_t0", None)
        ):
            raise KerykeionException(
                "Both subjects must share the same custom ayanamsa (t0 and offset) "
                "to be compared."
            )


def normalize_longitude(longitude: float) -> float:
    """Normalize a longitude to the [-180, 180) range the ephemeris backend expects.

    A caller passing an un-normalized longitude (e.g. 370° == 10° E, or -190°
    == 170° E) would otherwise leak a raw backend CoordinateError from the
    houses call. Wrap it into range instead, matching the astronomical meaning.

    A longitude already in range is returned UNCHANGED (no modulo round-off), so
    ordinary inputs keep their exact value.
    """
    if -180.0 <= longitude < 180.0:
        return longitude
    return (longitude + 180.0) % 360.0 - 180.0


def safe_timezone(tz_str: str) -> ZoneInfo:
    """Resolve an IANA timezone string, raising ``KerykeionException`` if invalid.

    Backed by :class:`zoneinfo.ZoneInfo`, which reads the platform TZif files in
    full and extrapolates beyond the last recorded transition from the zone's
    POSIX TZ rule. That matters for an ephemeris library: a transition table
    truncated to the 32-bit time_t range freezes the offset outside roughly
    1902-2037, so every chart cast for a future year keeps or loses DST at the
    wrong instant (in Rome, a year-5000 chart lands ~11.8° off on the
    Ascendant), and pre-1902 wall times silently reuse the 1902 offset instead
    of the zone's Local Mean Time record.

    Building a ``ZoneInfo`` can fail in four distinct ways where a single
    ``KeyError`` subclass used to cover everything: ``ZoneInfoNotFoundError``
    (unknown key), ``ValueError`` (empty string, absolute path, or a ``..``
    component in the key), ``TypeError`` (a non-string, e.g. ``None``) and
    ``OSError`` (the tz database entry exists but cannot be read). Neither of
    the last two is hypothetical: ``AstrologicalSubjectModel.tz_str`` is
    ``Optional[str]`` because composite charts have no single zone, and GeoNames
    can answer with an empty ``timezoneId`` (see ``fetch_geonames``). All four
    are wrapped here so every public entry point (from_iso_utc_time,
    from_current_time, EphemerisDataFactory, RelocatedChartFactory.relocate, and
    the timing factories via ``sun_times.resolve_timezone``) fails uniformly with
    the library's own exception. This is the ONE place that decides that set —
    ``resolve_timezone`` delegates here rather than keeping a second list that
    would drift.
    """
    try:
        return ZoneInfo(tz_str)
    except (ZoneInfoNotFoundError, ValueError, TypeError, OSError) as exc:
        raise KerykeionException(
            f"Unknown timezone: {tz_str!r}. Use a valid IANA timezone name "
            "(e.g. 'Europe/Rome', 'America/New_York')."
        ) from exc


def _zone_label(tz: _tzinfo) -> str:
    """Readable name for a zone, for error messages and logs.

    ``ZoneInfo`` carries the IANA key; a fixed-offset or hand-rolled ``tzinfo``
    does not, and ``str()`` is the closest it offers. Naming the zone is what
    makes a transition error actionable — "02:30 does not exist" is a riddle
    until the reader knows which clock it did not exist on.
    """
    return getattr(tz, "key", None) or str(tz)


def _fold_offsets(naive: datetime, tz: _tzinfo) -> tuple[Optional[timedelta], Optional[timedelta]]:
    """UTC offsets a wall time would get on each side of a nearby transition.

    ``fold`` (PEP 495) selects between the two interpretations of a wall time
    that a zone offers around a transition; away from one, both readings agree.
    Returned as a pair so callers can branch on ``off0 != off1`` — the single
    cheap test for "this wall time sits on a transition boundary at all".
    """
    return (
        naive.replace(tzinfo=tz, fold=0).utcoffset(),
        naive.replace(tzinfo=tz, fold=1).utcoffset(),
    )


def is_nonexistent(naive: datetime, tz: _tzinfo) -> bool:
    """Whether a naive wall time never occurred in ``tz`` (spring-forward gap).

    Detected by round-tripping through UTC: a wall time inside a gap has no UTC
    instant that maps back to it, so the round trip lands on a *different* wall
    time. An existing time round-trips exactly, ambiguous ones included.

    Must be tested BEFORE :func:`is_ambiguous`: a gap also reports two different
    fold offsets, so an ambiguity-first diagnosis would mislabel every gap.
    """
    off0, off1 = _fold_offsets(naive, tz)
    if off0 == off1:
        return False
    aware = naive.replace(tzinfo=tz, fold=0)
    try:
        return aware.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) != naive
    except (OverflowError, OSError):
        # Only reachable within a day of datetime.min/max, where no IANA zone
        # has a transition — so "not a gap" is also the correct answer.
        return False


def is_ambiguous(naive: datetime, tz: _tzinfo) -> bool:
    """Whether a naive wall time occurred twice in ``tz`` (fall-back fold).

    True only for a wall time that really repeats; a spring-forward gap, which
    also yields two different fold offsets, is excluded via
    :func:`is_nonexistent`.
    """
    off0, off1 = _fold_offsets(naive, tz)
    return off0 != off1 and not is_nonexistent(naive, tz)


# Below this instant a non-unique wall time is resolved, never rejected.
#
# Two independent facts put the line exactly here.
#
# Daylight saving did not exist yet. The earliest SEASONAL transition anywhere in
# the tz database — a shift that returns to the previous offset within a year —
# is from 1916. What sits below the horizon instead are the 19th-century
# adoptions of mean and standard time: one-off, permanent moves of a zone's
# clock. The database records them in the same shape as a seasonal shift, so they
# arrive here indistinguishable, and "was daylight saving in effect?" is not a
# question 1893 can answer. Asking a caller to answer it about their own birth
# certificate is asking for a guess.
#
# And it is where the previous backend's horizon already was. That transition
# table began at 1901-12-13 20:45:52 — the 32-bit ``time_t`` floor — with no
# recorded transition below it, so an earlier wall time fell through to the zone's
# opening mean-time record and was ALWAYS resolvable: measured at the midpoint of
# all 299 pre-1902 gap and fold windows, the old backend rejected none of them.
# Putting the horizon just above the floor restores that, and only that. The
# offsets themselves do NOT come back: where the truncated table had swallowed a
# real transition it also froze the answer, so e.g. Australia/Adelaide on
# 1899-05-01 read +09:14 there and reads its adopted +09:00 here — 14 minutes
# better, deliberately not restored.
#
# The 18 days between the floor and the constant are empty (zero transitions), so
# the two are behaviourally identical and the rounder date is the readable one.
# Not 1900, though: 43 transitions fall in ``[1900, 1902)`` — Asia/Shanghai's on
# 1900-12-31, the whole Alaska group on 1900-08-20 — and those resolved under the
# old backend too.
_PRE_DAYLIGHT_SAVING_HORIZON = datetime(1902, 1, 1)


def localize_naive(naive: datetime, tz: _tzinfo, *, is_dst: Optional[bool] = None) -> datetime:
    """Attach ``tz`` to a naive wall time, resolving DST transitions explicitly.

    ``is_dst`` disambiguates a wall time that a transition makes non-unique:

    * ``True``  → the reading with the LARGER UTC offset (clocks moved forward)
    * ``False`` → the reading with the SMALLER UTC offset
    * ``None``  → raise, rather than guess — but only above
      :data:`_PRE_DAYLIGHT_SAVING_HORIZON`, below which the question does not
      arise and the wall time resolves to the offset in force before the change.

    The clock decides, never the zone's ``dst()`` flag and never a fixed ``fold``
    index. Not the fold, because the correspondence between the two INVERTS
    between a fall-back and a gap: inside a fold ``fold=0`` is the summer
    reading, inside a spring-forward gap it is the winter one, so a hardcoded
    value would be right on one side of the year and wrong on the other.

    That warning does not touch the pre-1902 branch, which also hardcodes
    ``fold=0``: what inverts is the mapping from ``is_dst``, not the meaning of
    the index. PEP 495 defines ``fold=0`` as the EARLIER of the two readings in
    a fold and as the pre-transition offset in a gap — "what the clock showed
    before the change" — in both directions of the year alike.

    Not ``dst()``, because that flag is not portable. Different builds of the tz
    database record the same zone differently — for Ireland one encodes summer
    as ``dst()=+1h`` against a winter of ``0``, another encodes summer as ``0``
    against a winter of ``-1h``. Keying on the flag would hand the caller a
    different hour depending on which database the host ships, and this library
    is meant to give one answer for one birth. The offsets carry the same
    information without the encoding: measured across 23 zones and every
    transition from 1902 to 2037, on both encodings, the side with a positive
    ``dst()`` is always the side with the larger offset.

    One consequence is worth stating. A wall time can also repeat because the
    STANDARD offset changed rather than because summer time ended — a zone moved
    between administrations, say. Modern tz data flags neither reading as
    daylight saving there, so no "is DST in effect" answer exists to give; the
    rule still returns something deterministic, but the question does not really
    apply to that instant.

    An explicit ``is_dst`` never raises — the caller has already answered the
    only question a gap or a fold can ask.

    Args:
        naive: A wall time with ``tzinfo`` unset.
        tz: The zone to interpret it in.
        is_dst: Disambiguator; ``None`` means "reject anything non-unique".

    Raises:
        KerykeionException: If ``is_dst`` is None, the wall time is at or above
            :data:`_PRE_DAYLIGHT_SAVING_HORIZON`, and it either does not exist
            or occurs twice in ``tz``.
    """
    off0, off1 = _fold_offsets(naive, tz)

    # Dominant case: nowhere near a transition, both readings agree.
    if off0 == off1:
        return naive.replace(tzinfo=tz)

    if is_dst is None:
        # Before daylight saving existed there is nothing for is_dst to select,
        # so a birth date is answered rather than bounced back at the caller.
        if naive < _PRE_DAYLIGHT_SAVING_HORIZON:
            resolved = naive.replace(tzinfo=tz, fold=0)
            logger.info(
                f"{naive.isoformat()} falls on a pre-1902 change of civil time in "
                f"{_zone_label(tz)}; resolved to the offset in force before it "
                f"({resolved.utcoffset()})."
            )
            return resolved

        # Gap first: a non-existent wall time is ALSO reported as ambiguous.
        #
        # Both messages name daylight saving AND a change of standard time,
        # because which one it was is not decidable here: the tz database
        # records them in the same shape, and the dst() flag that would tell
        # them apart is encoded differently by different builds of it. Naming
        # only DST would be a confident answer we cannot back.
        if is_nonexistent(naive, tz):
            raise KerykeionException(
                f"Non-existent time error! The wall time {naive.isoformat()} never occurred in "
                f"{_zone_label(tz)}: the zone's clocks jumped forward across it, either for "
                "daylight saving or for a change of standard time. Please specify a valid time, "
                "or pass is_dst to choose a reading."
            )
        raise KerykeionException(
            f"Ambiguous time error! The wall time {naive.isoformat()} occurred twice in "
            f"{_zone_label(tz)}: the zone's clocks moved back across it, either for daylight "
            "saving or for a change of standard time. Please specify is_dst=True for the "
            "earlier reading (the larger UTC offset) or is_dst=False for the later one (the "
            "smaller)."
        )

    # Deliberately the offsets and NOT dst(): the flag is not portable. The same
    # zone is encoded differently by different builds of the tz database — for
    # Ireland one has summer at dst()=+1h and winter at 0, another has summer at
    # 0 and winter at -1h. Keying on "dst() is non-zero" therefore picks a
    # different side depending on which database the host happens to ship, which
    # is a one-hour error that only appears on some machines. Measured across 23
    # zones and every transition from 1902 to 2037, on both encodings, the side
    # carrying a POSITIVE dst() is always the side with the larger offset, so
    # consulting the flag could never have decided anything the clock does not.
    larger_fold = 0 if (off0 or timedelta()) > (off1 or timedelta()) else 1
    return naive.replace(tzinfo=tz, fold=larger_fold if is_dst else 1 - larger_fold)


# =============================================================================
# ANGULAR MATHEMATICS
# =============================================================================


def wrap_180(angle: Union[int, float]) -> float:
    """Wrap an angle in degrees into the signed range ``[-180, 180)``.

    Useful both for signed angular differences (``wrap_180(a - b)``) and for
    normalizing geographic longitudes; exactly 180° maps to -180° (the same
    meridian/separation).
    """
    return (angle + 180.0) % 360.0 - 180.0


def circular_mean(first_position: Union[int, float], second_position: Union[int, float]) -> float:
    """
    Calculate the circular mean of two angular positions.

    This method correctly handles positions that cross the 0°/360° boundary,
    avoiding errors that occur with simple arithmetic means.

    Exactly antipodal positions (180° apart) have no unique circular mean;
    they are resolved deterministically as the plain average of the
    normalized positions, ``((a + b) / 2) % 360``. This is the shorter-arc
    midpoint convention of the midpoint literature (Ebertin, Witte), and
    ``MidpointFactory._shorter_arc_midpoint`` delegates here.

    Args:
        first_position: First angular position in degrees (0-360)
        second_position: Second angular position in degrees (0-360)

    Returns:
        The circular mean position in degrees, always in the range [0, 360)
    """
    x = (math.cos(math.radians(first_position)) + math.cos(math.radians(second_position))) / 2
    y = (math.sin(math.radians(first_position)) + math.sin(math.radians(second_position))) / 2

    # Antipodal positions cancel out to a (near-)zero resultant vector, so
    # atan2 would return floating-point noise. Tie-break deterministically.
    if math.hypot(x, y) < 1e-12:
        return (((first_position % 360.0) + (second_position % 360.0)) / 2.0) % 360.0

    mean_position = math.degrees(math.atan2(y, x))

    if mean_position < 0:
        mean_position += 360

    # Float rounding can push the result to exactly 360.0 (e.g. 350° and 10°
    # yield 360 - 4.6e-15, which rounds to 360.0); normalize back to [0, 360)
    # so downstream consumers such as get_kerykeion_point_from_degree accept it.
    return mean_position % 360.0


def circular_sort(degrees: list[Union[int, float]]) -> list[Union[int, float]]:
    """
    Sort degrees in circular clockwise progression starting from the first element.

    Args:
        degrees: List of numeric degree values

    Returns:
        List sorted by clockwise distance from the first element

    Raises:
        ValueError: If the list is empty or contains non-numeric values
    """
    if not degrees:
        raise ValueError("Input list cannot be empty")

    if not all(isinstance(degree, (int, float)) for degree in degrees):
        invalid = next(d for d in degrees if not isinstance(d, (int, float)))
        raise ValueError(f"All elements must be numeric, found: {invalid} of type {type(invalid).__name__}")

    if len(degrees) <= 1:
        return degrees.copy()

    reference = degrees[0]

    def clockwise_distance(angle: Union[int, float]) -> Union[int, float]:
        ref_norm = reference % 360
        angle_norm = angle % 360
        distance = angle_norm - ref_norm
        if distance < 0:
            distance += 360
        return distance

    remaining = degrees[1:]
    sorted_remaining = sorted(remaining, key=clockwise_distance)

    return [reference] + sorted_remaining


# =============================================================================
# DATE/TIME UTILITIES
# =============================================================================


def format_iso_display(iso_datetime_string: str, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Format an ISO datetime string for display, supporting BCE dates.

    For modern dates (year >= 1), delegates to ``datetime.fromisoformat`` +
    ``strftime``.  For BCE dates (leading ``-``), parses the components
    manually and applies a subset of strftime-style directives.

    Supported format codes: ``%Y``, ``%m``, ``%d``, ``%H``, ``%M``, ``%S``.

    Args:
        iso_datetime_string: ISO 8601 string, possibly with a negative year.
        fmt: strftime-compatible format string.

    Returns:
        Formatted date/time string.
    """
    # BCE ("-YYYY-...") and ISO year 0 ("0000-...", i.e. 1 BCE) both fall outside
    # datetime.fromisoformat's range (its minimum year is 1); parse them manually.
    if not (iso_datetime_string.startswith("-") or iso_datetime_string.startswith("0000-")):
        return datetime.fromisoformat(iso_datetime_string).strftime(fmt)

    # Parse "[-]YYYY-MM-DDThh:mm:ss±HH:MM" manually
    negative = iso_datetime_string.startswith("-")
    rest = iso_datetime_string[1:] if negative else iso_datetime_string  # strip leading minus if present
    year_str, remainder = rest.split("-", 1)
    if negative:
        year_str = "-" + year_str  # e.g. "-0500"
    parts = remainder.split("T", 1)
    date_tokens = parts[0].split("-")  # ["03", "21"]
    time_str = parts[1] if len(parts) > 1 else "00:00:00"
    # Strip timezone offset for time parsing
    for i in range(len(time_str) - 1, 0, -1):
        if time_str[i] in ("+", "-"):
            time_str = time_str[:i]
            break
    time_tokens = time_str.split(":")  # ["12", "00", "00"]

    result = fmt
    result = result.replace("%Y", year_str)
    result = result.replace("%m", date_tokens[0] if len(date_tokens) > 0 else "01")
    result = result.replace("%d", date_tokens[1] if len(date_tokens) > 1 else "01")
    result = result.replace("%H", time_tokens[0] if len(time_tokens) > 0 else "00")
    result = result.replace("%M", time_tokens[1] if len(time_tokens) > 1 else "00")
    result = result.replace("%S", time_tokens[2] if len(time_tokens) > 2 else "00")
    return result


def extract_year_from_iso(iso_datetime_string: str) -> int:
    """Extract the year as an integer from an ISO datetime string, including BCE dates.

    Args:
        iso_datetime_string: ISO 8601 string, possibly with a negative year.

    Returns:
        Year as integer (e.g. -500, 0, 1940).
    """
    if iso_datetime_string.startswith("-"):
        rest = iso_datetime_string[1:]
        year_str, _ = rest.split("-", 1)
        return -int(year_str)
    # ISO 8601 represents year 0 (= 1 BCE) as the unsigned "0000"; datetime
    # cannot parse it (its minimum year is 1), so map it explicitly. The minus
    # sign is reserved for years <= -1, handled by the branch above.
    if iso_datetime_string.startswith("0000"):
        return 0
    return datetime.fromisoformat(iso_datetime_string).year


def format_absolute_degrees(value: float, decimals: int = 2) -> str:
    """Format a longitude so the number never contradicts the sign beside it.

    ``format_degrees_below_bound(value, 360.0)`` only guards the wrap at the end
    of the circle. The boundary that matters for a longitude printed next to a
    sign label is its own sign's ceiling: 149.99687 rounds to ``"150.00"``, which
    is zero degrees of Virgo, on a row that says Leo.
    """
    sign_ceiling = 30.0 * (int(value // 30.0) + 1)
    return format_degrees_below_bound(value, min(sign_ceiling, 360.0), decimals)


def format_degrees_below_bound(value: float, upper_bound: float, decimals: int = 2) -> str:
    """Format a degree value, guaranteeing the rounded string stays *below* ``upper_bound``.

    A within-sign ``position`` lives in ``[0, 30)`` and an ``abs_pos`` in ``[0, 360)``,
    but a point can sit within ~0.005° of the upper cusp. Naive ``f"{v:.2f}"`` rounds
    such a value UP across the boundary, printing an impossible ``"30.00"`` (that is 0°
    of the *next* sign) or an out-of-range ``"360.00"`` while the ``sign`` label still
    shows the current sign. Clamp the rounded value to the largest representable value
    strictly below the cusp so the number stays consistent with the sign — the chart
    drawing path floors for exactly this reason (see ``convert_decimal_to_degree_string``).

    Args:
        value: The degree value to format (assumed already normalized to ``[0, upper_bound)``).
        upper_bound: Exclusive upper cusp (``30.0`` for a within-sign position, ``360.0`` for abs_pos).
        decimals: Number of fractional digits (default 2).

    Returns:
        The formatted string, never equal to or above ``upper_bound``.
    """
    rounded = round(value, decimals)
    if rounded >= upper_bound:
        rounded = upper_bound - 10 ** (-decimals)
    return f"{rounded:.{decimals}f}"


def format_timedelta_hhmm(td: timedelta) -> str:
    """Render a duration as ``H:MM`` (rounded to whole minutes).

    Shared by the report and LLM-context serializers so both surfaces display a
    duration (e.g. the Sun's day length) in the same ``H:MM`` form rather than
    diverging into ``str(timedelta)`` (``H:MM:SS``).
    """
    # Half-up rounding to whole minutes (callers always pass non-negative
    # durations); avoids round()'s ties-to-even, which would render e.g. 0:30 as
    # 0:00 and 2:30 as 0:02.
    total_minutes = int(td.total_seconds() + 30) // 60
    return f"{total_minutes // 60}:{total_minutes % 60:02d}"


def _next_proleptic_julian_day(year: int, month: int, day: int) -> tuple[int, int, int]:
    """Return the calendar date one day after ``(year, month, day)``.

    Uses proleptic Julian-calendar rules (leap year when ``year % 4 == 0`` in
    astronomical numbering, where year 0 = 1 BCE), matching the ``JUL_CAL`` the
    BCE code path feeds into :func:`format_ancient_iso`. Crossing year 0 → 1 is
    the correct 1 BCE → 1 CE astronomical transition.
    """
    is_leap = (year % 4) == 0
    month_lengths = [31, 29 if is_leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day += 1
    if day > month_lengths[month - 1]:
        day = 1
        month += 1
        if month > 12:
            month = 1
            year += 1
    return year, month, day


def _days_in_proleptic_julian_month(year: int, month: int) -> int:
    """Days in ``month`` under proleptic Julian rules (leap when ``year % 4 == 0``,
    astronomical numbering where year 0 = 1 BCE). ``month`` must be 1..12.

    Matches the ``JUL_CAL`` leap rule ``ephe.julday`` applies on the BCE code
    path, so the BCE validation can reject impossible days (Feb-30, Apr-31,
    Feb-29 in a non-leap Julian year) that ``julday`` would otherwise silently
    roll into the next month.
    """
    is_leap = (year % 4) == 0
    return [31, 29 if is_leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]


def _split_decimal_hour_with_carry(
    year: int, month: int, day: int, decimal_hour: float
) -> tuple[int, int, int, int, int, int]:
    """Decompose ``decimal_hour`` into integer ``(year, month, day, h, m, s)``.

    Rounds to the nearest second (the BCE path feeds a float from ``ephe.revjul``
    that is almost never an exact integer, so truncating each component lost up to
    ~1 second) and carries a value within ~0.5 s of midnight (rounds to 86400)
    into the next proleptic-Julian day, so the result can never contain an invalid
    24:00:00 or a misdated 23:59:59.

    Shared by :func:`format_ancient_iso` and the BCE branch of
    ``RelocatedChartFactory`` so the stored integer h/m/s fields and the ISO
    string can never drift apart at a second boundary.
    """
    total_seconds = round(decimal_hour * 3600)
    if total_seconds >= 86400:
        total_seconds -= 86400
        year, month, day = _next_proleptic_julian_day(year, month, day)
    return year, month, day, total_seconds // 3600, (total_seconds % 3600) // 60, total_seconds % 60


def _assemble_ancient_iso(
    year: int, month: int, day: int, hour: int, minute: int, second: int, utc_offset_hours: float
) -> str:
    """Assemble an ISO 8601 extended-year string from already-split integer fields.

    Shared by :func:`format_ancient_iso` and the BCE branch of
    ``RelocatedChartFactory`` so a date already decomposed by
    :func:`_split_decimal_hour_with_carry` is not split a second time. The h/m/s
    values are taken verbatim — no rounding or carry happens here, so callers must
    pass fields that already encode any midnight rollover.
    """
    # ISO 8601 extended year: the minus sign is reserved for years <= -1. Year 0
    # (= 1 BCE) is the unsigned "0000" — sending it down the negative branch would
    # emit the non-conformant "-0000" that standards-based parsers reject.
    year_str = f"{year:04d}" if year >= 0 else f"-{abs(year):04d}"

    # UTC offset string, rendered at WHOLE-SECOND resolution — matching the CE LMT
    # path (astrological_subject_factory ~line 2009) and Python's datetime.isoformat:
    # "+HH:MM" for a whole-minute offset, "+HH:MM:SS" when it carries seconds. The
    # local ISO must display the SAME offset the caller used to derive the UTC
    # instant (a longitude-based LMT offset rounded only to the minute would make
    # this local string and the exact-offset UTC string disagree by up to ~30 s).
    if utc_offset_hours == 0.0:
        offset_str = "+00:00"
    else:
        sign = "+" if utc_offset_hours >= 0 else "-"
        # divmod on total seconds carries any 60 up into the next field, so no
        # ":60" can be emitted (minutes/seconds stay 0-59).
        total_seconds = round(abs(utc_offset_hours) * 3600)
        oh, rem = divmod(total_seconds, 3600)
        om, osec = divmod(rem, 60)
        offset_str = f"{sign}{oh:02d}:{om:02d}:{osec:02d}" if osec else f"{sign}{oh:02d}:{om:02d}"

    return f"{year_str}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}{offset_str}"


def format_ancient_iso(year: int, month: int, day: int, decimal_hour: float, utc_offset_hours: float) -> str:
    """Format a date with potentially negative year as an ISO 8601 extended-year string.

    Produces strings like ``"-0500-03-21T12:00:00+01:35"`` for dates that
    Python's ``datetime`` cannot represent (year < 1).

    Args:
        year: Calendar year in astronomical numbering (0 = 1 BCE, −1 = 2 BCE, etc.).
        month: Month (1–12).
        day: Day of month (1–31).
        decimal_hour: Hour as a decimal (e.g. 14.5 = 14:30:00).
        utc_offset_hours: UTC offset in decimal hours (east-positive).

    Returns:
        ISO 8601 formatted string with extended year.
    """
    # Round to the nearest second (with midnight day-carry) via the shared helper
    # so this and the BCE branch of RelocatedChartFactory decompose identically.
    year, month, day, h, m, s = _split_decimal_hour_with_carry(year, month, day, decimal_hour)
    return _assemble_ancient_iso(year, month, day, h, m, s, utc_offset_hours)


def datetime_to_julian(dt: datetime) -> float:
    """
    Convert a Python datetime object to Julian Day Number.

    The datetime is interpreted in the proleptic Gregorian calendar (the
    calendar Python's ``datetime`` uses), matching ``julian_to_datetime``
    so the two functions round-trip for all representable dates.

    Timezone-aware datetimes are converted to UTC first; naive datetimes
    are assumed to already be in UT.

    Args:
        dt: The datetime object to convert

    Returns:
        The corresponding Julian Day Number (JD) as a float
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)

    year = dt.year
    month = dt.month
    day = dt.day

    if month <= 2:
        year -= 1
        month += 12

    a = year // 100
    b = 2 - a + (a // 4)

    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5

    hour = dt.hour
    minute = dt.minute
    second = dt.second
    microsecond = dt.microsecond

    jd += (hour + minute / 60 + second / 3600 + microsecond / 3600000000) / 24

    return jd


def julian_to_datetime(jd: float) -> datetime:
    """
    Convert a Julian Day Number to a Python datetime object.

    The result is expressed in the proleptic Gregorian calendar — the
    calendar Python's ``datetime`` natively uses — for ALL dates, including
    those before the 1582 Gregorian reform. This makes the function the
    exact inverse of ``datetime_to_julian``; the historical Julian-calendar
    branch used previously broke the round trip by ~10 days for
    pre-1582 dates.

    Args:
        jd: Julian Day Number as a float

    Returns:
        The corresponding datetime object (proleptic Gregorian, UT)

    Raises:
        ValueError: For JDs before year 1 CE (datetime cannot represent
            BCE dates; use the ephemeris backend's ``revjul`` for those).
    """
    jd_plus = jd + 0.5

    Z = int(jd_plus)
    F = jd_plus - Z

    # math.floor (not int()) so the century correction also holds for early
    # CE dates, where these intermediates are negative.
    alpha = math.floor((Z - 1867216.25) / 36524.25)
    A = Z + 1 + alpha - math.floor(alpha / 4)

    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)

    day = B - D - int(30.6001 * E) + F
    day_int = int(day)

    day_frac = day - day_int

    if E < 14:
        month = E - 1
    else:
        month = E - 13

    if month > 2:
        year = C - 4716
    else:
        year = C - 4715

    if year < 1:
        # Explicit guard so the documented contract holds with a clear message,
        # rather than relying on datetime()'s terse "year 0 is out of range".
        raise ValueError(
            f"julian_to_datetime cannot represent JD {jd} (proleptic year {year} < 1 CE): "
            "Python's datetime has no BCE support. Use the ephemeris backend's "
            "revjul for BCE dates."
        )

    # Build from the integer date plus the day fraction so seconds/microseconds
    # carries normalize automatically (avoids a latent seconds==60 ValueError from
    # independent int() truncation of each component).
    return datetime(year, month, day_int) + timedelta(days=day_frac)


# =============================================================================
# SVG PROCESSING UTILITIES
# =============================================================================


def inline_css_variables_in_svg(svg_content: str) -> str:
    """
    Replace CSS custom properties (variables) with their values in SVG content.

    Extracts CSS variables from style blocks, replaces var() references with actual values,
    and removes all style blocks from the SVG.

    Args:
        svg_content: The original SVG string with CSS variables

    Returns:
        Modified SVG with CSS variables inlined and style blocks removed
    """
    css_variable_map = {}
    style_tag_pattern = re.compile(r"<style.*?>(.*?)</style>", re.DOTALL)
    style_blocks = style_tag_pattern.findall(svg_content)

    for style_block in style_blocks:
        for match in _CSS_VARIABLE_PATTERN.finditer(style_block):
            variable_name = match.group(1)
            variable_value = match.group(2).strip()
            css_variable_map[f"--{variable_name}"] = variable_value

    svg_without_style_blocks = style_tag_pattern.sub("", svg_content)

    def replace_css_variable_reference(match):
        variable_name = match.group(1).strip()
        fallback_value = match.group(3) if match.group(3) else None

        if variable_name in css_variable_map:
            return css_variable_map[variable_name]
        elif fallback_value:
            return fallback_value.strip()
        else:
            return ""

    # The fallback may itself contain one level of parentheses — a nested
    # ``var(--other, #hex)`` or an ``rgba(...)`` — so it is matched with
    # balanced parens rather than ``[^)]+``. The narrower pattern stopped at
    # the first ``)``, substituted the value, and left the outer ``)`` behind
    # as ``stroke='#81818d)'``: an invalid colour the browser drops, which is
    # what every modern-wheel cusp line did in the README's inlined charts.
    variable_usage_pattern = re.compile(r"var\(\s*(--[\w-]+)\s*(,\s*([^()]*(?:\([^()]*\)[^()]*)*))?\s*\)")

    processed_svg = svg_without_style_blocks
    # Nested var() references need repeated passes, but self-/mutually-
    # referential variables (e.g. --a: var(--a)) would loop forever: bound the
    # number of passes and stop early when a pass no longer changes the string.
    max_substitution_passes = 10
    for _ in range(max_substitution_passes):
        if not variable_usage_pattern.search(processed_svg):
            break
        substituted_svg = variable_usage_pattern.sub(replace_css_variable_reference, processed_svg)
        if substituted_svg == processed_svg:
            # Fixed point that still contains var() references (self-referential
            # variable): nothing more can be resolved.
            break
        processed_svg = substituted_svg
    else:
        logger.warning(
            "inline_css_variables_in_svg reached the substitution pass limit (%d); "
            "returning the partially inlined SVG (possible circular CSS variable references).",
            max_substitution_passes,
        )

    return processed_svg


# =============================================================================
# STATISTICAL UTILITIES
# =============================================================================


def distribute_percentages_to_100(values: dict[str, float]) -> dict[str, int]:
    """
    Distribute percentages so they sum to exactly 100.

    This function uses a largest remainder method to ensure that
    the percentage total equals 100 even after rounding.

    Args:
        values: Dictionary with keys and their raw percentage values

    Returns:
        Dictionary with the same keys and integer percentages that sum to 100
    """
    if not values:
        return {}

    total = sum(values.values())
    if total == 0:
        return {key: 0 for key in values.keys()}

    percentages = {key: value * 100 / total for key, value in values.items()}
    integer_parts = {key: int(value) for key, value in percentages.items()}
    remainders = {key: percentages[key] - integer_parts[key] for key in percentages.keys()}

    current_sum = sum(integer_parts.values())
    needed = 100 - current_sum

    sorted_by_remainder = sorted(remainders.items(), key=lambda x: x[1], reverse=True)

    result = integer_parts.copy()
    for i in range(needed):
        if i < len(sorted_by_remainder):
            key = sorted_by_remainder[i][0]
            result[key] += 1

    return result


def calculate_moon_phase(moon_abs_pos: float, sun_abs_pos: float) -> LunarPhaseModel:
    """
    Calculate lunar phase information from Sun and Moon positions.

    The lunation day (1-28) is the bin index and keeps its historical meaning.
    The name, the emoji, the major phase and the stage all come from the
    separation itself, through the windows centred on the events — the bin index
    is NOT their source, because its boundaries do not sit where the events do.

    Args:
        moon_abs_pos: Absolute position of the Moon in degrees
        sun_abs_pos: Absolute position of the Sun in degrees

    Returns:
        LunarPhaseModel containing phase data, emoji, and name
    """
    # Calculate the anti-clockwise degrees between the sun and moon
    degrees_between = (moon_abs_pos - sun_abs_pos) % 360

    # Calculate the lunation day (1-28) based on the degrees between the sun and moon
    moon_phase = int(degrees_between // _LUNAR_BIN_WIDTH) + 1

    phase_name, phase_emoji = lunar_phase_name_from_degrees(degrees_between)

    return LunarPhaseModel(
        degrees_between_s_m=degrees_between,
        moon_phase=moon_phase,
        moon_emoji=phase_emoji,
        moon_phase_name=phase_name,
        major_phase=lunar_major_phase_from_degrees(degrees_between),
        stage=lunar_stage_from_degrees(degrees_between),
    )
