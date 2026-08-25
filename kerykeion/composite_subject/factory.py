"""
Composite Subject Factory Module

This module provides functionality for creating composite astrological charts from two
individual astrological subjects. A composite chart represents the relationship between
two people by calculating midpoint positions between corresponding planetary placements
and house cusps.

The module implements the midpoint composite technique, which is the most commonly used
method for relationship astrology. This technique creates a single chart that symbolizes
the energy and dynamics of the relationship itself, rather than comparing individual charts.

Key Features:
- Midpoint calculation for all planetary positions
- Midpoint calculation for house cusp positions
- Proper handling of zodiacal boundary crossings (0°/360°)
- Validation of compatible astrological settings between subjects
- Lunar phase calculation for composite charts
- Support for all standard astrological points and house systems

Classes:
    CompositeSubjectFactory: Main factory class for creating composite charts

Dependencies:
    - AstrologicalSubjectFactory: For working with individual astrological subjects
    - Various schemas modules: For type definitions and models
    - utilities module: For astrological calculations and helper functions

Example Usage:
    >>> from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory
    >>> person1 = AstrologicalSubjectFactory.from_birth_data(...)
    >>> person2 = AstrologicalSubjectFactory.from_birth_data(...)
    >>> composite = CompositeSubjectFactory(person1, person2)
    >>> composite_chart = composite.get_midpoint_composite_subject_model()

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

import logging

from typing import Optional, Sequence, Union, get_args

# Fix the circular import by changing this import
from kerykeion.astrological_subject.factory import AstrologicalSubjectFactory, _GEO_TOPO_PERSPECTIVES
from kerykeion.predictive.utils import jd_to_ymd_hms
from kerykeion.settings.config_constants import OPPOSITE_POINTS
from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.schemas.models import CompositeSubjectModel, AstrologicalSubjectModel, PolarHouseFallbackModel
from kerykeion.schemas.literals import (
    CompositeHouseFrame,
    CompositeHouseAnchor,
    ZodiacType,
    PerspectiveType,
    HousesSystemIdentifier,
    SiderealMode,
    AstrologicalPoint,
    Houses,
    CompositeChartType,
)
from kerykeion.utilities.core import (
    _HOUSE_WINDING_TOLERANCE_DEGREES,
    house_spans,
    get_kerykeion_point_from_degree,
    get_planet_house,
    circular_mean,
    calculate_moon_phase,
    find_common_active_points,
)


#: Two cusps closer than this are the same point: a thousandth of a milliarcsecond,
#: far below anything an ephemeris resolves or a wheel can draw.
_COINCIDENT_CUSP_DEGREES = 1e-9


def _cusp_ring_winds_once(cusps: Sequence[float]) -> bool:
    """Do these twelve arcs cover the circle exactly once?

    Asked of ``house_spans``, which is the library's answer to this question,
    rather than counted here a second time. The copy that stood here summed the
    forward gaps with a bare ``% 360``, and for two cusps coincident to within
    float noise in the negative direction that returns exactly 360.0 instead of
    zero: a ring ``house_spans`` certifies at 360 came out at 720, so the "leave
    it alone" path was skipped and every cusp was rebuilt on a chart that needed
    nothing done to it.

    Real composite rings do reach it: 90 of 120,069 rings measured had two cusps
    at bit-identical longitudes. It is closed anyway, because the reason a
    particular ephemeris does or does not produce one is not a fact about this
    function, and because a bare ``% 360`` on an angle is the fourth of its kind
    this repository has had to find.

    Covering the circle is necessary and not sufficient: a house of zero width
    adds nothing to the total, so twelve arcs can sum to 360 with two of the
    cusps on the same longitude. That is not a division into twelve houses, and
    left uncaught it reaches ``get_planet_house``, whose exact-on-cusp rule then
    answers with the earlier of the two — a Midheaven that IS the tenth cusp,
    filed in the fourth. So the arcs must also be arcs.
    """
    spans, reversed_wedges = house_spans(cusps)
    if (
        len(set(reversed_wedges)) != 1
        or abs(sum(spans) - 360.0) > _HOUSE_WINDING_TOLERANCE_DEGREES
    ):
        return False
    return all(span > _COINCIDENT_CUSP_DEGREES for span in spans)


logger = logging.getLogger(__name__)


def _house_of(degree: float, cusps: list) -> str:
    """The library's house reader, with an answer for a ring that has gaps.

    Two charts whose houses do not run the same way can average into twelve cusps
    that are not a partition of the circle, and a longitude can then fall in a gap
    between them. It is rarely both charts crossing their own cusps: of the frames
    where a real point lands in a gap, 97% have one plain forward ring and one
    plain backward one, neither crossing anything. ``get_planet_house`` raises
    there, and rightly: for an ordinary chart that is a bug worth stopping on,
    which is what its own test holds it to.

    A composite is the one place the condition is reachable by construction, so
    it is the one place that answers instead of failing — with the house whose
    cusp the point last passed, which is what a reader would say looking at the
    wheel, and out loud, because a ring this shape is worth knowing about.

    Before the composite was taught to use the shared reader it had a private
    copy that silently returned the first house for these. The point of this is
    not to go back to that: it is to keep one reader and one place where its
    contract legitimately does not fit.
    """
    try:
        return get_planet_house(degree, cusps)
    except ValueError:
        behind = min(range(12), key=lambda index: (degree - cusps[index]) % 360.0)
        name = get_args(Houses)[behind]
        logger.warning(
            "These cusps do not partition the circle, so %.4f falls in a gap between "
            "them; reading it as the house whose cusp it last passed. No arrangement "
            "of midpoints between these two charts closes it — usually because one "
            "of them has a reversed ring and the other a plain one.",
            degree,
        )
        return name


def _rings_admit_a_common_frame(
    first_cusps: Sequence[float], second_cusps: Sequence[float]
) -> bool:
    """Can one frame be read from these two rings?

    Two conditions, and each has cost a defect on its own. Each ring has to be a
    house division: a parent whose own twelve neither tile nor agree on a
    direction gave a composite that came back anchored under one angle and gapped
    under another, on the same two subjects.

    And the two have to run the SAME way. Both winding once is not enough —
    forwards and backwards each wind once — and a frame spanning one of each
    measures an arc as a separation in one chart and as its complement in the
    other. On a horizon pair at 66S and the equator that came back claiming to be
    anchored under all three anchors while holding the Ascendant rotated every
    cusp half a circle and moved the Sun from the seventh house to the first.
    """
    first_spans, first_directions = house_spans(first_cusps)
    second_spans, second_directions = house_spans(second_cusps)

    def winds_once(spans: Sequence[float], directions: Sequence[bool]) -> bool:
        return (
            len(set(directions)) == 1
            and abs(sum(spans) - 360.0) <= _HOUSE_WINDING_TOLERANCE_DEGREES
            and all(span > _COINCIDENT_CUSP_DEGREES for span in spans)
        )

    if not winds_once(first_spans, first_directions):
        return False
    if not winds_once(second_spans, second_directions):
        return False
    return first_directions[0] == second_directions[0]


def _is_opposite(first: float, second: float) -> bool:
    """Are these two longitudes exactly half a circle apart?"""
    return abs(((second - first) % 360.0) - 180.0) < 1e-9


def _angle_is_its_cusp(
    first_angle: float,
    second_angle: float,
    first_cusps: Sequence[float],
    second_cusps: Sequence[float],
    cusp: int,
) -> bool:
    """Do both charts put this angle exactly on the cusp it shares a number with?

    Asked of the charts rather than of a list of house-system identifiers kept
    somewhere and left to rot. Quadrant systems say yes for all four angles;
    equal houses say yes for the Ascendant and the Descendant only; whole sign,
    Morinus and meridian say no for one or both pairs.

    ``cusp`` is the cusp's own index, zero-based: 0 for the Ascendant, 3 for the
    Imum Coeli, 6 for the Descendant, 9 for the Midheaven. It used to be the
    angle's index instead, folded to a cusp in here by ``0 if index == 0 else 9``
    — so a caller with four angles to ask about, passing the cusp numbers
    straight in, had the Imum Coeli and the Descendant both measured against the
    tenth cusp. They said no every time and never got the answer this predicate
    exists to give them. The fold is gone; there is one numbering now.
    """
    return (
        abs(((first_angle - first_cusps[cusp] + 180.0) % 360.0) - 180.0) < 1e-9
        and abs(((second_angle - second_cusps[cusp] + 180.0) % 360.0) - 180.0) < 1e-9
    )


def composite_frame(
    first_cusps: Sequence[float],
    second_cusps: Sequence[float],
    first_angles: tuple[float, float],
    second_angles: tuple[float, float],
    anchor: CompositeHouseAnchor = "auto",
) -> tuple[tuple[float, float, float, float], list[float], bool]:
    """The twelve composite cusps, and the frame everything else hangs from.

    Each composite cusp is the midpoint of the two charts' cusps of the SAME
    number, and keeps that number: the tenth cusp is the midpoint of the tenths,
    which is the composite Midheaven under any quadrant system. Re-sorting by
    longitude instead would file it into a lower slot and swap the Midheaven with
    the Imum Coeli.

    Between two points on a circle there are two midpoints, half a turn apart.
    Taking the nearer one is right, and taking it for each of the twelve
    *independently* is what breaks: when the two charts' angles are nearly
    opposed the separations straddle 180 degrees, the choice flips partway round
    the ring, and the twelve arcs come to 1080 degrees instead of 360. That is
    not a house division at all — measured here, about one couple in eighteen at
    ordinary latitudes.

    The profession's answer, and this one: hold one **angle** at its near midpoint
    and let everything else follow from it. Solar Fire calls the result adjusting
    cusps "to be long-arc midpoints instead of short-arc"; Kepler and Sirius call
    it "flipping the houses 180 degrees if necessary", and name their two methods
    after the angle each never flips. Which angle is held is the ``anchor``.

    It has to be the angle and not the cusp of the same number. Under a quadrant
    system they are one point and the distinction is idle, but under whole sign,
    equal, Morinus or meridian houses the first cusp is not the Ascendant — and
    anchoring on the cusp then makes the composite Ascendant itself depend on the
    house system, by exactly half a turn. Anchored on the angle, both angles come
    out house-system-independent (their arcs from each other are), while the
    identity with the cusp survives wherever the parents had it, because a cusp
    that IS its angle sits zero degrees from the origin in both charts.

    Every position is placed by measuring its arc from a held origin in each
    chart and averaging the two. Halving an arc taken modulo 360 lands on the
    near midpoint or the far one according to how many times the pair wrapped,
    and it is that count which carries one choice to everything on the wheel: so
    every position is still a midpoint of its own pair — the rule as Townley
    states it — while the twelve cusps cover the circle exactly once.

    A ring whose near midpoints already run in order needs no repair and keeps
    them — that is most of them. Not value for value, though, and in two sizes: a
    cusp the parents put exactly opposite another is snapped back onto it first,
    which moves it by up to about a thousandth of a degree on a near-antipodal
    pair; and where an angle that IS a cusp disagrees with the frame, the whole
    ring turns half a circle to meet it, in-order or not. That second one is most
    of the times it fires — 13 of 13 on one mixed-latitude sweep, 30 of 36 on a
    polar one — and it moves all twelve cusps, not one. The frame is still built
    and returned for these, because the angles hang from it and must not depend on
    whether the cusps happened to need repairing.

    Args:
        first_cusps: The first subject's twelve cusps, in house order.
        second_cusps: The second subject's twelve cusps, in house order.
        first_angles: The first subject's (Ascendant, Midheaven).
        second_angles: The second subject's (Ascendant, Midheaven).
        anchor: Which angle is held. See
            :data:`~kerykeion.schemas.literals.CompositeHouseAnchor`.

    Returns:
        The frame — ``(first_origin, second_origin, origin_midpoint, step)`` —
        the twelve cusps, and whether the frame is coherent: ``False`` when no
        one frame spans the two charts' houses, in which case a position placed
        on it does not belong to the ring returned beside it. Two charts running
        opposite ways do that, and so does a single parent inside the polar
        circle whose own cusps are not ordered at all.
    """
    midpoints = [
        circular_mean(first, second) for first, second in zip(first_cusps, second_cusps)
    ]

    # A cusp opposite another in both parents has to stay opposite it here, and
    # averaging the pair on its own does not keep it: where the two charts put a
    # cusp exactly half a circle apart, that pair and the opposite pair are the
    # SAME two longitudes, so any average of the set — symmetric, as it must be
    # for the composite of A and B to equal the composite of B and A — hands both
    # the same answer. Cusp 4 came out on cusp 10, and the Imum Coeli, derived
    # from the Midheaven as it should be, then sat half a circle from its own
    # fourth cusp. It is the four angles' own rule, which they have always had:
    # derive the opposite instead of averaging it.
    # Not only where it collapsed outright. A circular mean loses accuracy as its
    # two inputs approach half a circle apart — the same 1/cos mechanism the
    # rotation threshold below is set for — so a pair the parents put exactly
    # opposite can come back anywhere from a hair to 1.3e-03 degrees off it
    # without the average having flipped at all. Those are snapped too: on the
    # equal-houses pair in the tests all six pairs fire, none of them collapsed,
    # and it is what puts that chart's Descendant exactly on the seventh cusp
    # instead of 7.9e-04 degrees short of it — enough, on that ring, to be read
    # into the sixth house.
    # Which of the pair is the source matters: the first cusp is the Ascendant
    # and the TENTH is the Midheaven, so those two are what the other two hang
    # from. Derive the seventh from the first and the fourth from the tenth, and
    # both angles stay on their own cusps; derive them the other way round and
    # the Midheaven ends up half a circle from the tenth cusp, which is where
    # this started.
    for source, derived in ((0, 6), (9, 3), (1, 7), (2, 8), (4, 10), (5, 11)):
        # Both parents, not either: asking only the second makes the composite of
        # A and B differ from the composite of B and A — 1,872 ordered pairs of
        # 51,315 swept at the poles, by as much as 0.09 degrees.
        #
        # Which of a pair is the source is forced only for the two carrying an
        # angle. For the other four it is a convention and nothing observable
        # rests on it: neither cusp is an angle, and the two parents' separations
        # are equal by construction, so there is no better-determined one to
        # prefer. Flipping them moves those cusps by up to 6e-04 degrees and
        # breaks no invariant — it would show up in a stored baseline, which is
        # the only reason to leave it alone.
        if (
            _is_opposite(first_cusps[source], first_cusps[derived])
            and _is_opposite(second_cusps[source], second_cusps[derived])
            and not _is_opposite(midpoints[source], midpoints[derived])
        ):
            midpoints[derived] = (midpoints[source] + 180.0) % 360.0

    already_in_order = _cusp_ring_winds_once(midpoints)

    if anchor == "ascendant":
        held = 0
    elif anchor == "midheaven":
        held = 1
    else:
        # The better determined of the two: where the base angles sit closer
        # together, the midpoint between them is the less arbitrary one. Solar
        # Fire calls this the "strongest" midpoint and makes it the default.
        # Measured symmetrically, because which subject was named first must not
        # decide anything. Taking the signed difference modulo 360 and folding it
        # is arithmetic on ordered inputs: for a pair exactly half a circle apart
        # it returns 180.0 one way round and 179.99999999999997 the other, which
        # is enough to hold a different angle and turn the whole ring half a
        # circle. abs() first, and the two orders are the same float.
        separations = []
        for first, second in zip(first_angles, second_angles, strict=True):
            delta = abs(second - first) % 360.0
            separations.append(min(delta, 360.0 - delta))
        held = 0 if separations[0] <= separations[1] else 1


    # One direction for the pair, read from the houses themselves: above the
    # polar circle several systems return descending cusps, and reading those
    # forwards measures eleven turns where there is one. Two backward charts make
    # a backward composite. Measuring each parent in its own direction instead
    # breaks the very property this construction exists for — the arcs stop
    # adding up to a separation, and the position lands on neither midpoint.
    # A frame spans two charts, and whether it can is decided below, by asking
    # whether it keeps the identities the parents already have. Nothing here
    # tests the direction the houses run: an earlier version did, and measuring
    # showed the answer never changed anything the rotation check had not already
    # caught. The same went for placing positions backwards on a backward pair —
    # halving an arc taken modulo 360 gives the same answer either way, except
    # when one of the two arcs is exactly zero, which no pair of real charts
    # produced in 2,760 tries. Both are gone rather than left in looking useful.
    # A frame is a common reading of two rings, and there is nothing to read a
    # frame from unless each of them is a house division in the first place. A
    # parent whose own twelve neither tile nor agree on a direction — Polich/Page
    # at 68S manages 360.198 degrees with mixed directions — gave a composite
    # whose answer depended on the anchor: held on the Midheaven the ring came
    # back looking anchored and put the Sun in the second house, held on either
    # other angle it came back gapped with the Sun in the ninth. Nothing about the
    # two subjects changed between those three calls.
    coherent = _rings_admit_a_common_frame(first_cusps, second_cusps)

    # Two origins, one choice. The cusps hang from the cusp of the held angle's
    # house and the angles hang from the angle itself, because they are not the
    # same point: under whole sign, equal, Morinus or meridian houses the first
    # cusp is not the Ascendant. Hanging the angles from the cusp made the
    # composite Ascendant depend on the house system, by exactly half a turn;
    # hanging the cusps from the angle puts the cusp that straddles it a half
    # turn out and breaks the ring. Under a quadrant system the two origins are
    # the same point, so the identity between angle and cusp survives by
    # construction wherever the parents had it — and where they did not, the two
    # were never one thing to keep together.
    cusp_index = 0 if held == 0 else 9
    cusp_frame = (
        first_cusps[cusp_index],
        second_cusps[cusp_index],
        circular_mean(first_cusps[cusp_index], second_cusps[cusp_index]),
        1.0,
    )
    angle_frame = (
        first_angles[held],
        second_angles[held],
        circular_mean(first_angles[held], second_angles[held]),
        1.0,
    )

    # A repair is only a repair if the result is a house division, and the frame
    # does not guarantee one. Neither parent need be degenerate for that: Campanus
    # at 75N has twelve distinct cusps winding once backwards, and the equatorial
    # chart it is paired with winds once forwards. It is the placing that collapses
    # them — the two rings wrap the frame's origin a different number of times, so
    # the half-arc lands five antipodal pairs on each other, 2 on 8, 3 on 9, 4 on
    # 10, 5 on 11, 6 on 12 — and a ring with cusp 4 on cusp 10 is not twelve
    # houses. So place, then check, and where the check fails say that there was
    # nothing to repair *towards* rather than pretending otherwise.
    #
    # The plain midpoints are what this returned before there was a repair at
    # all, and they are the honest answer for those.
    # ``not coherent`` here is the parents themselves, decided above: a ring
    # placed on a frame that does not exist can still come out winding once by
    # accident, and then it is accepted, and the anchor — which decides nothing on
    # such a pair — silently decides everything. That is how one chart came back
    # anchored under the Midheaven and gapped under the other two.
    if already_in_order or not coherent:
        cusps = list(midpoints)
    else:
        placed = [
            place_on_composite_frame(first, second, cusp_frame)
            for first, second in zip(first_cusps, second_cusps)
        ]
        if _cusp_ring_winds_once(placed):
            cusps = placed
        else:
            cusps = list(midpoints)
            coherent = False

    # Where the parents put an angle exactly on a cusp, the composite has to as
    # well — under equal houses the first cusp IS the Ascendant, and a chart whose
    # Ascendant is drawn opposite its own first cusp is broken however sound the
    # ring is. The two can disagree because the anchor may hold the Midheaven
    # while it is the Ascendant that is a cusp.
    #
    # The whole ring turns half a circle to meet it. That is free: a rotation
    # leaves the twelve tiling exactly as they were, and half a turn takes each
    # cusp from one midpoint of its pair to the other, which is the only choice in
    # question anyway. It fires rarely — 4 charts in 240 under equal-type systems
    # — and never at all under a quadrant system, where the angle and the cusp
    # share an origin and cannot disagree.
    # Nothing rotates a ring the frame could not repair. The rotation exists to
    # make a framed ring agree with the frame; on a ring that is not on one it
    # only moves the cusp out from under an angle that cannot follow it, because
    # that angle is its own near midpoint. Ungate this and 26 frames in 148,005
    # draw an angle opposite the cusp it is.
    if coherent:
        identities = [
            (cusp, place_on_composite_frame(first_angles[index], second_angles[index], angle_frame))
            for index, cusp in ((0, 0), (1, 9))
            if _angle_is_its_cusp(
                first_angles[index], second_angles[index], first_cusps, second_cusps, cusp
            )
        ]
        # The only disagreement a rotation answers is half a turn. Everything else
        # is the near midpoint and the frame's own choice being the same point
        # reached two ways, and the arithmetic error between the two is not small:
        # a vector mean's resultant vanishes as a pair approaches half a circle
        # apart, so the error grows as one over the cosine of half the separation.
        # Bisecting a latitude towards that limit takes the gap from 8e-09 to
        # 2.8e-06 to **7.9e-04** degrees — nearly three arcseconds — on ordinary
        # float inputs to the public API. Any tolerance in that range reads it as
        # a broken identity and turns the whole ring half a circle to repair it,
        # which put the Ascendant of an Alcabitius composite in the seventh house.
        # Half a turn is the only thing worth answering, so ask at half of it.
        disagreeing = [
            cusp
            for cusp, placed in identities
            if abs(((cusps[cusp] - placed + 180.0) % 360.0) - 180.0) > 90.0
        ]
        if disagreeing and len(disagreeing) == len(identities):
            cusps = [(value + 180.0) % 360.0 for value in cusps]
        elif disagreeing:
            # One rotation would fix one identity and break the other. Two charts
            # running opposite ways are most of it, a single parent whose own
            # cusps are not ordered at all is most of the rest, and a few have two
            # plain rings running the same way, which is neither — the ratios move
            # with whatever grid you measure, but all three occur. Leave the ring
            # alone; the angles follow it below.
            coherent = False

    return angle_frame, cusps, coherent


def place_on_composite_frame(
    first_value: float, second_value: float, frame: tuple[float, float, float, float]
) -> float:
    """One position, placed on the frame :func:`composite_frame` returned.

    The arc from the held origin to the position, measured in each chart and
    averaged. Halving an arc taken modulo 360 lands on the near midpoint or the
    far one according to how many times the pair wrapped, and it is that count
    which carries one choice to everything on the wheel: the result is always a
    midpoint of the two positions, and the frame decides which of the two.
    """
    first_origin, second_origin, origin_midpoint, _step = frame
    first_arc = (first_value - first_origin) % 360.0
    second_arc = (second_value - second_origin) % 360.0
    return (origin_midpoint + (first_arc + second_arc) / 2.0) % 360.0


def composite_house_cusps(
    first_cusps: Sequence[float],
    second_cusps: Sequence[float],
    anchor: CompositeHouseAnchor = "auto",
    first_angles: Optional[tuple[float, float]] = None,
    second_angles: Optional[tuple[float, float]] = None,
) -> list[float]:
    """The twelve composite cusps. See :func:`composite_frame` for the reasoning.

    With the angles omitted the first and tenth cusps stand in for them, which is
    exact under any quadrant system and the best available when a caller has
    cusps and nothing else.
    """
    return composite_frame(
        first_cusps,
        second_cusps,
        first_angles if first_angles is not None else (first_cusps[0], first_cusps[9]),
        second_angles if second_angles is not None else (second_cusps[0], second_cusps[9]),
        anchor,
    )[1]


def _davison_midpoint_components(
    mid_jd: float, mid_lng: float
) -> tuple[int, int, int, int, int, int]:
    """Decompose a Davison midpoint JD into birth-data components (UTC).

    CE midpoints use the Gregorian calendar to match the proleptic-Gregorian
    datetimes used everywhere else in kerykeion. BCE midpoints must instead be
    the exact inverse of from_birth_data's BCE branch, which re-encodes year<1
    components in the JULIAN calendar and subtracts the longitude-LMT offset
    (ignoring tz_str) — so decompose the LMT-shifted instant in the Julian
    calendar or the Davison chart lands days away from the true time midpoint.
    """
    from kerykeion.ephemeris_backend.backend import ephe

    lmt_shift = mid_lng / 15.0 / 24.0  # days; mirrors _calculate_time_conversions_bce
    greg_cal = getattr(ephe, "GREG_CAL", 1)
    probe_year = int(ephe.revjul(mid_jd + lmt_shift, ephe.JUL_CAL)[0])
    if probe_year < 1:
        cal, jd_base = ephe.JUL_CAL, mid_jd + lmt_shift
    else:
        cal, jd_base = greg_cal, mid_jd

    # Nearest-second rounding with calendar-aware midnight carry, shared with
    # the event factories' timestamp formatting.
    year, month, day, hour, minute, seconds = jd_to_ymd_hms(jd_base, cal)

    # from_birth_data branches on year<1, so the components must land on the
    # same side the probe predicted. The only flips are second-rounding at the
    # 1 BCE/1 CE boundary and the ~2-day window before 1 CE Jan 1 (proleptic
    # Gregorian) that neither branch's components can represent.
    if probe_year < 1 and year >= 1:
        # Rounding rolled 1 BCE Dec 31 24:00 (Julian) into 1 CE — clamp to
        # 23:59:59 (<=1 s error) so the BCE branch is still taken.
        year, month, day, hour, minute, seconds = 0, 12, 31, 23, 59, 59
    elif probe_year >= 1 and year < 1:
        logging.warning(
            "Davison midpoint JD %.6f falls in the ~2-day gap before 1 CE "
            "Jan 1 (proleptic Gregorian) that birth-data components cannot "
            "represent; clamping to 0001-01-01T00:00:00Z (error < ~2.5 days).",
            mid_jd,
        )
        year, month, day, hour, minute, seconds = 1, 1, 1, 0, 0, 0

    return int(year), int(month), int(day), hour, minute, seconds


class CompositeSubjectFactory:
    """
    Factory class to create composite astrological charts from two astrological subjects.

    A composite chart represents the relationship between two people by calculating the midpoint
    between corresponding planetary positions and house cusps. This creates a single chart
    that symbolizes the energy of the relationship itself.

    Currently supports the midpoint method for composite chart calculation, where:
    - Planetary positions are calculated as the circular mean of corresponding planets
    - House cusps are calculated as the circular mean of corresponding houses
    - Each composite cusp keeps its own house number; cusps are deliberately NOT
      re-sorted by longitude (that would swap the composite MC and IC — see
      _calculate_midpoint_composite_points_and_houses)
    - Only common active points between both subjects are included

    The resulting composite chart maintains the zodiac type, sidereal mode, houses system,
    and perspective type of the input subjects (which must be identical between subjects).

    Attributes:
        model (CompositeSubjectModel | None): The generated composite subject model
        first_subject (AstrologicalSubjectModel): First astrological subject
        second_subject (AstrologicalSubjectModel): Second astrological subject
        name (str): Name of the composite chart
        composite_chart_type (CompositeChartType): Type of composite chart (currently "Midpoint")
        zodiac_type (ZodiacType): Zodiac system used (Tropical or Sidereal)
        sidereal_mode (SiderealMode | None): Sidereal calculation mode if applicable
        houses_system_identifier (HousesSystemIdentifier): House system identifier
        houses_system_name (str): Human-readable house system name
        perspective_type (PerspectiveType): Astrological perspective type
        houses_names_list (list[Houses]): List of house names
        active_points (list[AstrologicalPoint]): Common active planetary points

    Example:
        >>> first_person = AstrologicalSubjectFactory.from_birth_data(
        ...     "John", 1990, 1, 1, 12, 0, "New York", "US"
        ... )
        >>> second_person = AstrologicalSubjectFactory.from_birth_data(
        ...     "Jane", 1992, 6, 15, 14, 30, "Los Angeles", "US"
        ... )
        >>> composite = CompositeSubjectFactory(first_person, second_person)
        >>> composite_model = composite.get_midpoint_composite_subject_model()

    Raises:
        KerykeionException: When subjects have incompatible settings (different zodiac types,
                           sidereal modes, house systems, or perspective types)
    """

    model: Union[CompositeSubjectModel, None]
    first_subject: AstrologicalSubjectModel
    second_subject: AstrologicalSubjectModel
    name: str
    composite_chart_type: CompositeChartType
    zodiac_type: ZodiacType
    sidereal_mode: Union[SiderealMode, None]
    houses_system_identifier: HousesSystemIdentifier
    houses_system_name: str
    perspective_type: PerspectiveType
    houses_names_list: list[Houses]
    active_points: list[AstrologicalPoint]

    def __init__(
        self,
        first_subject: AstrologicalSubjectModel,
        second_subject: AstrologicalSubjectModel,
        chart_name: Union[str, None] = None,
        house_anchor: CompositeHouseAnchor = "auto",
    ):
        """
        Initialize the composite subject factory with two astrological subjects.

        Validates that both subjects have compatible settings and extracts common
        active points for composite chart calculation.

        Args:
            first_subject (AstrologicalSubjectModel): First astrological subject for the composite
            second_subject (AstrologicalSubjectModel): Second astrological subject for the composite
            chart_name (str | None, optional): Custom name for the composite chart.
                                             If None, generates name from subject names.
                                             Defaults to None.
            house_anchor (CompositeHouseAnchor, optional): Which angle keeps its near
                                             midpoint. It decides the frame every
                                             chart is placed on, not only the ones
                                             whose ring needs repairing: of 431
                                             composites needing no repair, 14 had an
                                             angle moved by it, every one of them by
                                             exactly half a circle. Defaults to "auto".

        Raises:
            KerykeionException: If either input is not an astrological subject model
                              (e.g. None), or if subjects have different zodiac types,
                              sidereal modes, house systems, house system names, or
                              perspective types.

        Note:
            Both subjects must have identical astrological calculation settings to ensure
            meaningful composite chart calculations.
        """
        self.model: Union[CompositeSubjectModel, None] = None
        self.composite_chart_type = "Midpoint"
        # Checked, because the branch that reads it treats everything it does not
        # recognise as "auto": a capital A in "Ascendant" would have been accepted
        # in silence and handed back a house frame half a turn from the one asked
        # for. This factory already refuses an unknown house system out loud.
        if house_anchor not in get_args(CompositeHouseAnchor):
            raise KerykeionException(
                f"'{house_anchor}' is not a valid composite house anchor! "
                f"Available anchors are: {get_args(CompositeHouseAnchor)}"
            )
        self.house_anchor: CompositeHouseAnchor = house_anchor

        for _label, _subject in (("first_subject", first_subject), ("second_subject", second_subject)):
            if getattr(_subject, "active_points", None) is None:
                # Fail with a clear message instead of a raw AttributeError on
                # `.active_points` below (e.g. when None is passed).
                raise KerykeionException(
                    f"CompositeSubjectFactory {_label} is not an astrological subject "
                    f"model (got {type(_subject).__name__!r})."
                )

        self.first_subject = first_subject
        self.second_subject = second_subject
        self.active_points = find_common_active_points(first_subject.active_points, second_subject.active_points)
        if not self.active_points:
            # Disjoint active_points -> empty intersection. Fail loudly: the two
            # composite paths would otherwise diverge silently (the midpoint loop
            # produces an empty chart, while the Davison path forwards [] to
            # from_birth_data where it is read as 'no filter' and expands to a
            # FULL chart). Same empty-explicit-list inversion guarded elsewhere.
            raise KerykeionException(
                "The two subjects share no common active points; a composite "
                "chart needs at least one. Align their active_points."
            )

        # Name
        if chart_name is None:
            self.name = f"{first_subject.name} and {second_subject.name} Composite Chart"
        else:
            self.name = chart_name

        # Zodiac Type
        if first_subject.zodiac_type != second_subject.zodiac_type:
            raise KerykeionException("Both subjects must have the same zodiac type")
        self.zodiac_type = first_subject.zodiac_type

        # Sidereal Mode
        if first_subject.sidereal_mode != second_subject.sidereal_mode:
            raise KerykeionException("Both subjects must have the same sidereal mode")

        self.sidereal_mode = first_subject.sidereal_mode

        # Custom ayanamsa (required by the model validator when sidereal_mode is
        # 'USER'): carry both subjects' values over so CompositeSubjectModel does
        # not reject the self-inconsistent state (mode='USER' but fields absent).
        if first_subject.sidereal_mode == "USER" and (
            first_subject.custom_ayanamsa_t0 != second_subject.custom_ayanamsa_t0
            or first_subject.custom_ayanamsa_ayan_t0 != second_subject.custom_ayanamsa_ayan_t0
        ):
            raise KerykeionException("Both subjects must have the same custom ayanamsa values")
        self.custom_ayanamsa_t0 = first_subject.custom_ayanamsa_t0
        self.custom_ayanamsa_ayan_t0 = first_subject.custom_ayanamsa_ayan_t0

        # Houses System
        if first_subject.houses_system_identifier != second_subject.houses_system_identifier:
            raise KerykeionException("Both subjects must have the same houses system")
        self.houses_system_identifier = first_subject.houses_system_identifier

        # Houses System Name
        if first_subject.houses_system_name != second_subject.houses_system_name:
            raise KerykeionException("Both subjects must have the same houses system name")
        self.houses_system_name = first_subject.houses_system_name

        # Perspective Type
        if first_subject.perspective_type != second_subject.perspective_type:
            raise KerykeionException("Both subjects must have the same perspective type")
        self.perspective_type = first_subject.perspective_type

        # Houses Names List
        self.houses_names_list = self.first_subject.houses_names_list

    def __str__(self):
        """
        Return string representation of the composite subject.

        Returns:
            str: Human-readable string describing the composite chart.
        """
        return f"Composite Chart Data for {self.name}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        """
        Check equality with another composite subject.

        Args:
            other (CompositeSubjectFactory): Another composite subject to compare with.

        Returns:
            bool: True if both subjects and chart name are identical.
        """
        if not isinstance(other, CompositeSubjectFactory):
            return NotImplemented
        return (
            self.first_subject == other.first_subject
            and self.second_subject == other.second_subject
            and self.name == other.name
            # Chart-defining, not a preference: two factories over the same pair
            # under different anchors can produce house frames half a turn apart,
            # so calling them equal collapses two different charts in any dict,
            # set or cache keyed on them.
            and self.house_anchor == other.house_anchor
        )

    def __hash__(self):
        """
        Generate hash for the composite subject.

        Hashes stable scalar identifiers instead of the subject models
        themselves: AstrologicalSubjectModel is a non-frozen Pydantic model,
        so hashing it raises TypeError. Consistent with __eq__ — equal
        factories have equal subjects (hence equal names/julian days) and
        equal chart names.

        Returns:
            int: Hash value based on both subjects' identity scalars and chart name.
        """
        return hash(
            (
                self.first_subject.name,
                self.first_subject.julian_day,
                self.second_subject.name,
                self.second_subject.julian_day,
                self.name,
                self.house_anchor,
            )
        )

    def __copy__(self):
        """
        Create a shallow copy of the composite subject.

        The anchor travels with it. Rebuilding without it silently reverts to
        ``"auto"``, and on a pair whose angles are opposed that turns the copy's
        cusp ring half a circle away from the original's.

        Returns:
            CompositeSubjectFactory: New instance with the same subjects, name
            and house anchor.
        """
        return CompositeSubjectFactory(
            self.first_subject,
            self.second_subject,
            self.name,
            house_anchor=self.house_anchor,
        )

    def __setitem__(self, key, value):
        """
        Set an attribute using dictionary-style access.

        Args:
            key (str): Attribute name to set.
            value: Value to assign to the attribute.
        """
        setattr(self, key, value)

    def __getitem__(self, key):
        """
        Get an attribute using dictionary-style access.

        Args:
            key (str): Attribute name to retrieve.

        Returns:
            Any: Value of the requested attribute.

        Raises:
            AttributeError: If the attribute doesn't exist.
        """
        return getattr(self, key)

    def _calculate_midpoint_composite_points_and_houses(self):
        """
        Calculate midpoint positions for all planets and house cusps in the composite chart.

        This method implements the midpoint composite technique by:
        1. Computing circular means of house cusp positions from both subjects
        2. Keeping each averaged cusp under its own house number (no re-sorting;
           see the implementation note below)
        3. Creating composite house cusps with calculated positions
        4. Computing circular means of planetary positions for common active points
        5. Assigning planets to their appropriate houses in the composite chart

        The circular mean calculation ensures proper handling of zodiacal positions
        around the 360-degree boundary (e.g., when one position is at 350° and
        another at 10°, the midpoint is correctly calculated as 0°).

        Side Effects:
            - Updates instance attributes with calculated house cusp positions
            - Updates instance attributes with calculated planetary positions
            - Sets house assignments for each planetary position

        Note:
            This is an internal method called by get_midpoint_composite_subject_model().
            Only planets that exist in both subjects' active_points are included.
        """
        # Houses: each composite cusp is the midpoint of the two subjects'
        # SAME-numbered cusps, and it KEEPS that house number. Do NOT re-sort by
        # longitude and re-label positionally: sorting files the averaged 10th
        # cusp (the composite Midheaven) into a lower slot, swapping it with the
        # Imum Coeli and corrupting every planet's house. The tenth cusp must stay
        # the mean of the tenth cusps.
        #
        # Which leaves the real repair to composite_house_cusps: where the two
        # charts' angles are nearly opposed, the near midpoints stop running in
        # order and the twelve arcs come to 1080 degrees instead of 360. It holds
        # one angle and moves the others onto their far midpoint, which is what
        # the profession does with this case.
        first_cusps = [
            self.first_subject[house.lower()]["abs_pos"]
            for house in self.first_subject.houses_names_list
        ]
        second_cusps = [
            self.second_subject[house.lower()]["abs_pos"]
            for house in self.second_subject.houses_names_list
        ]
        composite_angles_frame, house_degree_list_ut, frame_is_coherent = composite_frame(
            first_cusps,
            second_cusps,
            (self.first_subject["ascendant"]["abs_pos"], self.first_subject["medium_coeli"]["abs_pos"]),
            (self.second_subject["ascendant"]["abs_pos"], self.second_subject["medium_coeli"]["abs_pos"]),
            anchor=self.house_anchor,
        )
        # Recorded on the chart, not only said to the logger. `house_anchor` is
        # what the caller ASKED to hold, and where no frame spans the two charts
        # it holds nothing: all three anchors then return the same ring, and a
        # model carrying only the request describes a construction that did not
        # happen. Worse, on a ring with gaps every house name is the last-passed-
        # cusp reading rather than a containment, and nothing said so.
        ring_is_a_division = _cusp_ring_winds_once(house_degree_list_ut)
        if frame_is_coherent:
            self.house_frame: CompositeHouseFrame = "anchored"
        elif ring_is_a_division:
            self.house_frame = "midpoints"
        else:
            self.house_frame = "gapped"

        if not ring_is_a_division:
            # Said out loud as well. Two partners whose houses run opposite ways
            # are the common reason, a single parent whose own cusps are not
            # ordered accounts for most of the rest, and a few have two plain
            # rings running the same way.
            logger.info(
                "Composite house cusps do not cover the circle once: the two subjects' "
                "houses do not run the same way round the wheel, so this composite has "
                "no coherent house division. Its house names are the house whose cusp "
                "each point last passed; house_frame records this as 'gapped'."
            )

        for house_index, house_name in enumerate(self.first_subject.houses_names_list):
            house_lower = house_name.lower()
            self[house_lower] = get_kerykeion_point_from_degree(house_degree_list_ut[house_index], house_name, "House")

        # Planets
        planets = {}
        # The four angles are placed on the same frame as the cusps, not averaged
        # on their own. Averaged on their own they part company with the ring the
        # moment the ring is repaired: the repair flips whichever cusps the order
        # requires, and an angle that did not flip with them ends up half a circle
        # from the house it opens — on the Rome pair below, a whole-sign composite
        # came out with its Midheaven in the fourth house and its Ascendant where
        # the Descendant belongs.
        #
        # Read off the cusps instead — which is what this did first — and the
        # angles inherit the house system: the composite Ascendant moved by
        # exactly half a turn between Placidus and whole sign. The frame is hung
        # from an *angle* for that reason, so both angles come out independent of
        # the house system (their arcs from each other are), while a cusp that IS
        # its angle still lands on it, sitting zero degrees from the origin in
        # both charts.
        #
        # Only the Ascendant and the Midheaven are placed. The other two are
        # their opposites by definition, in the parents and here.
        angle_opposites = {"descendant": "ascendant", "imum_coeli": "medium_coeli"}
        placed_angles: dict[str, float] = {}
        for angle in ("ascendant", "medium_coeli"):
            if frame_is_coherent:
                placed_angles[angle] = place_on_composite_frame(
                    self.first_subject[angle]["abs_pos"],
                    self.second_subject[angle]["abs_pos"],
                    composite_angles_frame,
                )
                continue

            # No frame spans these two charts, so there is nothing to place a
            # position on — a position placed on one anyway is not the position
            # the ring shows: the composite Midheaven landed in the fourth house
            # on a chart whose twelve cusps tiled perfectly, and nothing anywhere
            # complained. Every position falls back to its own near midpoint — bar
            # a cusp kept opposite its partner, which the snap above has already
            # settled and which the angles inherit through their own opposites —
            # which is close to what this returned before there was a frame at all,
            # and which keeps an angle on its cusp wherever the parents put it
            # there, because then the two are the same average.
            #
            # That last part is why nothing rotates the ring once the frame is
            # known not to span the two charts: half a turn moves the cusp out
            # from under an angle that is not being placed on a frame and so
            # cannot follow it.
            placed_angles[angle] = circular_mean(
                self.first_subject[angle]["abs_pos"],
                self.second_subject[angle]["abs_pos"],
            )

        # The other two are opposites by definition, in the parents and here, and
        # are derived rather than averaged on their own. An earlier version did
        # average them, on the grounds that the near midpoint of two Descendants
        # need not be the near midpoint of two Ascendants plus half a turn. That
        # is true, and it is the reason not to: two angles half a circle apart
        # have two midpoints equally near, and the two calls pick opposite ones —
        # 2,835 pairs of 39,924 differ by more than a nanodegree and the largest
        # difference is exactly 180 degrees. Averaged separately, a Descendant
        # stops being opposite its own Ascendant.
        for opposite, angle in angle_opposites.items():
            placed_angles[opposite] = (placed_angles[angle] + 180.0) % 360.0

        # An angle that IS a cusp opens that house, and the composite knows which
        # cusp each angle is — so it says so, instead of handing the longitude
        # back to a reader that has to find it again. Scanning cannot always
        # succeed: where one parent's ring runs forward and the other's backward,
        # the near midpoints of the fourth cusps and of the tenth come out on the
        # same longitude, and the exact-on-cusp rule then answers with the earlier
        # of the two, filing a Midheaven that is the tenth cusp in the fourth
        # house. 468 charts of 178,416 read that way. The four numbers below are
        # not a convention: they are which cusp the parents put the angle on, and
        # they are used only where both parents did.
        #
        # Nothing here re-checks that this chart's angle really landed on that
        # cusp. It effectively always does: the ring derives an opposite cusp from
        # the one the angle is on, exactly as the angle derives its own opposite,
        # and across ordinary random input the worst drift measured was 2.4e-12
        # degrees. Bisect a latitude into the band where a circular mean's
        # resultant vanishes and it reaches 4.5e-09 — enough for the shared reader
        # to name the twelfth house for an Ascendant this files, correctly, in the
        # first. So this is the more accurate of the two answers there, not a
        # shortcut past one. What holds it is the tests, which assert the angle
        # against its cusp and not merely against a house name.
        angle_cusp_index = {"ascendant": 0, "imum_coeli": 3, "descendant": 6, "medium_coeli": 9}
        angle_houses: dict[str, str] = {}
        for angle, cusp in angle_cusp_index.items():
            if not _angle_is_its_cusp(
                self.first_subject[angle]["abs_pos"],
                self.second_subject[angle]["abs_pos"],
                first_cusps,
                second_cusps,
                cusp,
            ):
                continue
            angle_houses[angle] = get_args(Houses)[cusp]

        if not frame_is_coherent:
            logger.info(
                "No single frame spans these two subjects' houses, so this composite "
                "has none: every position is its own near midpoint except a cusp kept "
                "opposite its partner, and the angles "
                "follow the cusp ring where the subjects put them on a cusp."
            )

        # Every point the composite carries: the ones asked for, plus the derived
        # opposites of any of those, whether or not they were asked for.
        #
        # An ordinary subject and a Davison chart keep the Descendant, the Imum
        # Coeli and the south node even when those are not active — each is the
        # other end of a point that IS active, and the context promises a horizon,
        # a meridian and a node section unconditionally. The midpoint composite
        # materialised only `active_points`, so those three came back None and
        # vanished from its context while every other chart type showed them.
        #
        # Derived, not averaged. Two points half a circle apart are the same
        # unordered pair as their own opposites, so a symmetric mean — which it
        # must be, for the composite of A and B to equal the composite of B and A
        # — hands both the same longitude. Averaged on its own, a south node whose
        # parents sit at 190 and 10 came out on top of the north node, separation
        # zero. `active_points` is left alone: it says what was asked for, and the
        # display and aspect filters go on reading it.
        derived_points = {
            opposite: primary
            for opposite, primary in OPPOSITE_POINTS.items()
            if primary in self.active_points and opposite not in self.active_points
        }
        for planet in list(self.active_points) + list(derived_points):
            planet_lower = planet.lower()
            planets[planet_lower] = {}
            if planet in derived_points:
                planets[planet_lower]["abs_pos"] = (
                    planets[derived_points[planet].lower()]["abs_pos"] + 180.0
                ) % 360.0
                self[planet_lower] = get_kerykeion_point_from_degree(
                    planets[planet_lower]["abs_pos"], planet, "AstrologicalPoint"
                )
                self[planet_lower]["house"] = angle_houses.get(planet_lower) or _house_of(
                    self[planet_lower]["abs_pos"], house_degree_list_ut
                )
                continue
            if planet_lower in placed_angles:
                planets[planet_lower]["abs_pos"] = placed_angles[planet_lower]
            else:
                planets[planet_lower]["abs_pos"] = circular_mean(
                    self.first_subject[planet_lower]["abs_pos"],
                    self.second_subject[planet_lower]["abs_pos"],
                )
            self[planet_lower] = get_kerykeion_point_from_degree(
                planets[planet_lower]["abs_pos"], planet, "AstrologicalPoint"
            )
            # Through the library's own reader, not a copy of it. The copy here
            # measured every house as the arc running *forwards* from its cusp,
            # which is not how the cusps always run: average two polar charts and
            # the ring comes out descending, and then a six-degree house reads as
            # 354 and swallows most of the wheel. Ten points out of ten landed in
            # the wrong house, and the same model's own house-comparison field
            # disagreed with them, because that one already went through
            # get_planet_house. It carries the exact-on-cusp rule too, so wherever
            # the Midheaven IS the tenth cusp - every quadrant system - it still
            # opens the tenth house. Under equal or Carter houses it is a point of
            # its own and can fall in the ninth, which is what those systems mean.
            self[planet_lower]["house"] = angle_houses.get(planet_lower) or _house_of(
                self[planet_lower]["abs_pos"], house_degree_list_ut
            )

    def _calculate_composite_lunar_phase(self):
        """
        Calculate the lunar phase for the composite chart based on Sun-Moon midpoints.

        Uses the composite positions of the Sun and Moon to determine the lunar phase
        angle, representing the relationship's emotional and instinctual dynamics.

        Side Effects:
            Sets the lunar_phase attribute with the calculated phase information.

        Note:
            This method should be called after _calculate_midpoint_composite_points_and_houses()
            to ensure Sun and Moon composite positions are available.
        """
        # Lunar phase is a GEOCENTRIC quantity (the Sun-Earth-Moon angle); for a
        # non-geocentric composite the Moon-Sun elongation is a phantom. Guard to
        # geocentric/topocentric perspectives, matching the single-subject
        # factory (the Davison path already inherits the guard via from_birth_data).
        if getattr(self, "perspective_type", None) not in _GEO_TOPO_PERSPECTIVES:
            self.lunar_phase = None
            return
        moon = getattr(self, "moon", None)
        sun = getattr(self, "sun", None)
        if moon is None or sun is None:
            # Sun/Moon can be absent, e.g. when a planetocentric subject
            # excludes its center body from the active points.
            self.lunar_phase = None
            return
        self.lunar_phase = calculate_moon_phase(moon.abs_pos, sun.abs_pos)

    def _require_parents_to_share_a_house_division(self) -> None:
        """Reject parents whose cusps came from different house divisions.

        Each composite cusp is the circular mean of the two subjects' SAME-numbered
        cusps, so the result inherits whatever division produced them. Averaging a
        Porphyry third house with a Placidus third house yields a boundary that
        belongs to neither system — a number with no astrological reading — and no
        label on the output could make it one. The factory already refuses parents
        whose REQUESTED systems disagree; a substitution forced at one parent's
        latitude makes their ACTUAL systems disagree just as materially.

        This rule belongs only to midpoint composites. A Davison composite recasts
        a whole new chart at the midpoint moment and location, so it retains the
        requested system and lets that fresh cast decide for itself whether a polar
        substitution is needed.
        """
        first_effective = self.first_subject.effective_houses_system_identifier
        second_effective = self.second_subject.effective_houses_system_identifier
        if first_effective != second_effective:
            raise KerykeionException(
                "Both subjects must have the same houses system: "
                f"{self.first_subject.name}'s cusps were computed with "
                f"{self.first_subject.effective_houses_system_name!r} and "
                f"{self.second_subject.name}'s with "
                f"{self.second_subject.effective_houses_system_name!r}. "
                "A house system undefined at one subject's latitude was substituted there; "
                "see polar_house_fallbacks on that subject."
            )

    def _inherited_house_fallbacks(self) -> list[PolarHouseFallbackModel]:
        """The parents' house-substitution records, carried onto the composite.

        A midpoint composite has no latitude of its own — its cusps are circular
        means of cusps computed at two different places — so it cannot perform a
        substitution and cannot author a record of one. It can only inherit. These
        are the records that explain why the averaged cusps are Porphyry when
        Placidus is what the caller asked for, and carrying them is what lets the
        model's ``effective_houses_system_*`` view answer correctly without the
        requested identifier having to be overwritten.

        Only each parent's MAIN record travels. An ancillary one — the Gauquelin
        ring degrades on its own terms — describes a product the midpoint technique
        does not average, so passing it on would attach to the composite a claim
        nothing in it supports.
        """
        records = []
        for subject in (self.first_subject, self.second_subject):
            record = subject._main_house_fallback()
            if record is not None:
                records.append(record)
        return records

    def get_midpoint_composite_subject_model(self):
        """
        Generate the complete composite chart model using the midpoint technique.

        This is the main public method for creating a composite chart. It orchestrates
        the calculation of all composite positions and creates a complete CompositeSubjectModel
        containing all necessary astrological data for the relationship chart.

        The process includes:
        1. Calculating midpoint positions for all planets and house cusps
        2. Computing the composite lunar phase
        3. Assembling all data into a comprehensive model

        Returns:
            CompositeSubjectModel: Complete composite chart data model containing:
                - All calculated planetary positions and their house placements
                - House cusp positions maintaining proper house system order
                - Lunar phase information for the composite chart
                - All metadata from the original subjects (names, chart type, etc.)

        Example:
            >>> composite = CompositeSubjectFactory(person1, person2, "Our Relationship")
            >>> model = composite.get_midpoint_composite_subject_model()
            >>> print(f"Composite Sun at {model.sun.abs_pos}° in House {model.sun.house}")

        Note:
            This method performs all calculations internally and returns a complete,
            ready-to-use composite chart model suitable for analysis or chart drawing.
        """
        self._require_parents_to_share_a_house_division()
        self._calculate_midpoint_composite_points_and_houses()
        self._calculate_composite_lunar_phase()

        midpoint_data = self.__dict__.copy()
        # `houses_system_identifier` keeps the REQUEST, as it does on a subject: a
        # substitution forced by one parent's latitude is a fact about that parent,
        # not a preference the relationship has adopted, and the requested value is
        # what a relocation or a re-cast must start from. The substitution still has
        # to be visible, so the parents' own records travel with the composite and
        # drive the inherited `effective_houses_system_*` view.
        midpoint_data["polar_house_fallbacks"] = self._inherited_house_fallbacks()
        return CompositeSubjectModel(**midpoint_data)

    def get_davison_composite_subject_model(
        self,
        *,
        custom_ayanamsa_t0: Union[float, None] = None,
        custom_ayanamsa_ayan_t0: Union[float, None] = None,
    ) -> CompositeSubjectModel:
        """Generate a Davison composite chart.

        A Davison chart calculates the midpoint in **time** and **space**
        between two birth moments, then casts a standard natal chart for
        that derived moment and location.

        Unlike the midpoint composite (which averages planetary positions),
        the Davison chart is a real chart with valid astronomical positions
        that actually occurred at the computed date and location.

        Args:
            custom_ayanamsa_t0: Reference epoch (Julian Day) for the custom
                ayanamsa. Required when the subjects use ``sidereal_mode="USER"``.
            custom_ayanamsa_ayan_t0: Ayanamsa value (degrees) at ``t0``.
                Required when the subjects use ``sidereal_mode="USER"``.

        Returns:
            CompositeSubjectModel with composite_chart_type="Davison".
        """
        # The Davison chart is recomputed from scratch — USER sidereal mode
        # needs the custom ayanamsa definition to cast it.
        if self.sidereal_mode == "USER" and (custom_ayanamsa_t0 is None or custom_ayanamsa_ayan_t0 is None):
            raise KerykeionException(
                "get_davison_composite_subject_model requires both custom_ayanamsa_t0 and "
                "custom_ayanamsa_ayan_t0 when sidereal_mode='USER'."
            )

        s1 = self.first_subject
        s2 = self.second_subject

        # Midpoint in time (Julian Day)
        mid_jd = (s1.julian_day + s2.julian_day) / 2.0

        # Midpoint in space (latitude/longitude)
        mid_lat = (s1.lat + s2.lat) / 2.0
        mid_lng = circular_mean(s1.lng + 180.0, s2.lng + 180.0) - 180.0

        year, month, day, hour, minute, seconds = _davison_midpoint_components(
            mid_jd, mid_lng
        )

        extra_kwargs: dict = {}
        if custom_ayanamsa_t0 is not None:
            extra_kwargs["custom_ayanamsa_t0"] = custom_ayanamsa_t0
        if custom_ayanamsa_ayan_t0 is not None:
            extra_kwargs["custom_ayanamsa_ayan_t0"] = custom_ayanamsa_ayan_t0

        # The Davison is a real recomputable natal chart, so carry over the v6
        # enrichment flags BOTH parents requested (inferred from their populated
        # fields, since the flags aren't stored as booleans) — otherwise the
        # dignities/nakshatra/gauquelin/nutation/local-space/fixed-stars are
        # silently dropped. Parity with PlanetaryReturnFactory /
        # SecondaryProgressionFactory (which infer the same flags). Enable a
        # feature only when BOTH parents carried it, matching composite semantics.
        def _point_has(subject, attr: str) -> bool:
            for _name in ("sun", "moon", "mercury", "venus", "mars", "jupiter",
                          "saturn", "uranus", "neptune", "pluto"):
                _p = getattr(subject, _name, None)
                if _p is not None:
                    return getattr(_p, attr, None) is not None
            return False

        _shared_stars = sorted(
            {st.name for st in (s1.fixed_stars or [])} & {st.name for st in (s2.fixed_stars or [])}
        )
        extra_kwargs["calculate_dignities"] = _point_has(s1, "essential_dignity") and _point_has(s2, "essential_dignity")
        extra_kwargs["calculate_nakshatra"] = _point_has(s1, "nakshatra") and _point_has(s2, "nakshatra")
        extra_kwargs["calculate_local_space"] = _point_has(s1, "azimuth") and _point_has(s2, "azimuth")
        extra_kwargs["calculate_gauquelin"] = (
            s1.gauquelin_sector_cusps is not None and s2.gauquelin_sector_cusps is not None
        )
        extra_kwargs["calculate_nutation"] = s1.nutation is not None and s2.nutation is not None
        if _shared_stars:
            extra_kwargs["active_fixed_stars"] = _shared_stars

        # Cast a real natal chart at the midpoint moment/location.
        # ephe.revjul returns UTC, so use Etc/GMT to avoid double-conversion.
        davison_subject = AstrologicalSubjectFactory.from_birth_data(
            name=self.name,
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            seconds=seconds,
            lng=mid_lng,
            lat=mid_lat,
            tz_str="Etc/GMT",
            city=f"Davison({s1.city}-{s2.city})",
            nation=s1.nation,
            online=False,
            zodiac_type=self.zodiac_type,
            sidereal_mode=self.sidereal_mode,
            houses_system_identifier=self.houses_system_identifier,
            perspective_type=self.perspective_type,
            active_points=self.active_points,
            **extra_kwargs,
        )

        # Build composite model from the Davison chart data
        davison_data = davison_subject.model_dump()
        davison_data["first_subject"] = s1
        davison_data["second_subject"] = s2
        davison_data["composite_chart_type"] = "Davison"

        return CompositeSubjectModel(**davison_data)


if __name__ == "__main__":
    first = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")
    second = AstrologicalSubjectFactory.from_birth_data("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

    composite_chart = CompositeSubjectFactory(first, second)
    print(composite_chart.get_midpoint_composite_subject_model().model_dump_json(indent=4))
