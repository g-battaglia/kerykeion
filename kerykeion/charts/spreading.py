# -*- coding: utf-8 -*-
"""Spreading labels around a wheel without letting them touch.

Anything drawn at an angle on a chart runs into the same problem: two things
close together in the sky are close together on the page, and at some point
their ink meets. Planets have had an answer for a while — the content-aware
model in :mod:`kerykeion.charts.draw_modern`, whose separations are measured in
a browser. House numbers had none at all, and it showed: at 66°S Placidus puts
"10" and "11" 13px apart at a 14px font, and Campanus manages the same at
Liverpool.

The two cases want the same mathematics and different inputs, so the maths
lives here. :func:`isotonic_non_decreasing` is the pool-adjacent-violators
algorithm both use; :func:`spread_around_wheel` is the whole answer for labels
of one uniform size, which is what a house number is.

Why isotonic regression rather than pushing each collision aside: it is the
placement that minimises total movement subject to the separation, so a tight
cluster is *centred* on where it really is instead of sliding off in whichever
direction the sweep happened to run, and the order is preserved by
construction — which for numbers running 1 to 12 is not a nicety.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

# The one rule, not a local restatement of it. This module used to carry a
# byte-identical twin, kept local because charts.utils imported spreading and
# not the reverse — an argument that stopped being true when normalize_degree
# moved to utilities.core, which imports nothing from charts at all.
from kerykeion.utilities.core import normalize_degree
from typing import Sequence

__all__ = ["isotonic_non_decreasing", "spread_around_wheel"]


def isotonic_non_decreasing(values: Sequence[float]) -> list[float]:
    """The closest non-decreasing sequence to *values* in least squares.

    Pool adjacent violators: walk left to right keeping blocks of equal value,
    and whenever a new value would go below the block before it, merge the two
    and give both their mean. What comes out is the unique minimiser of the
    squared distance among all non-decreasing sequences.
    """
    blocks: list[tuple[float, int]] = []
    for value in values:
        merged_sum = float(value)
        merged_size = 1
        while blocks and blocks[-1][0] > merged_sum / merged_size:
            previous_mean, previous_size = blocks.pop()
            merged_sum += previous_mean * previous_size
            merged_size += previous_size
        blocks.append((merged_sum / merged_size, merged_size))

    out: list[float] = []
    for mean, size in blocks:
        out.extend([mean] * size)
    return out


def spread_around_wheel(
    angles: Sequence[float],
    min_separation: float,
    half_extents: Sequence[float] | None = None,
) -> list[float]:
    """Angles moved as little as possible so consecutive ones sit apart.

    *angles* are degrees on the wheel in drawing order; the return is the same
    length and the same order, each entry normalised to ``[0, 360)``. An input
    already comfortable is returned unchanged, so a chart with evenly spaced
    houses keeps exactly the placement it had.

    *min_separation* is the room every pair needs, in degrees. Pass
    *half_extents* instead — one figure per label, how far its ink reaches to
    either side along the wheel, in degrees — when the labels are not all the
    same size or do not all face the same way. Then each pair is asked for the
    sum of its own two halves, and *min_separation* becomes a floor under that.

    Why that matters for a wheel: a label is drawn upright while the arc it sits
    on turns. Two labels at the top of the wheel stand side by side and have to
    clear each other's *width*; the same two on the flank stack one above the
    other and only have to clear their *height*. Sizing every pair by the width
    is safe and, on the flanks, a third too generous — enough to walk a crowd of
    house numbers out of the houses they belong to.

    The circle is cut at the widest existing gap before the row is straightened
    out. Cutting anywhere else can split a crowd across the seam, and the
    straight-line algorithm cannot see that its first and last entries are
    neighbours; the widest gap is the one place guaranteed not to be inside a
    crowd. When even the total will not fit — twelve labels wanting more than
    360° between them — the requirement is scaled down to what the circle has,
    which spreads the crowding evenly instead of piling it all at the seam. The
    budget is the circle itself: a crowd with empty wheel beside it is spread,
    not left as it was.
    """
    count = len(angles)
    if count < 2 or (min_separation <= 0 and not half_extents):
        return [normalize_degree(angle) for angle in angles]

    order = sorted(range(count), key=lambda i: normalize_degree(angles[i]))
    sorted_angles = [normalize_degree(angles[i]) for i in order]

    gaps = [
        normalize_degree(sorted_angles[(i + 1) % count] - sorted_angles[i])
        for i in range(count)
    ]
    cut = max(range(count), key=lambda i: gaps[i])

    # Unroll starting just after the widest gap, so the sequence is monotonic.
    rolled = [sorted_angles[(cut + 1 + i) % count] for i in range(count)]
    start = rolled[0]
    unrolled = [normalize_degree(angle - start) for angle in rolled]

    # What each consecutive pair needs, in the unrolled order.
    rolled_index = [order[(cut + 1 + i) % count] for i in range(count)]
    if half_extents is None:
        gaps_needed = [min_separation] * (count - 1)
    else:
        gaps_needed = [
            max(min_separation, half_extents[rolled_index[i]] + half_extents[rolled_index[i + 1]])
            for i in range(count - 1)
        ]

    # What the seam pair — last label back round to first — needs, on the same
    # terms as every other pair. It is not in `gaps_needed` (the isotonic fit
    # runs on the straightened row, which has no seam) but it does occupy room
    # on the circle, so the budget has to count it.
    if half_extents is None:
        seam_needed = min_separation
    else:
        seam_needed = max(
            min_separation, half_extents[rolled_index[-1]] + half_extents[rolled_index[0]]
        )

    # The budget is the circle, not the crowd. This used to compare `needed`
    # against `unrolled[-1] - unrolled[0]` — the span the labels already
    # occupied — so a tight cluster was told it had only its own width to work
    # with and scaled its requirement down to exactly the spacing it already
    # had. Twelve labels 3.6° apart asking for 4.31° came back untouched, with
    # 320° of the wheel standing empty beside them. Measured against 360° the
    # same case has room to spare and simply spreads.
    needed = sum(gaps_needed) + seam_needed
    shrink = 1.0
    if needed > 360.0:
        # More labels than the circle can hold at full separation: share the
        # shortfall rather than letting the last few pile up. Scaling the seam
        # along with the rest is what keeps the crowding even all the way round
        # instead of dumping it into the one gap the fit cannot see.
        shrink = 360.0 / needed
        gaps_needed = [gap * shrink for gap in gaps_needed]

    # Subtracting a ramp turns "at least this much apart" into "non decreasing",
    # which is what the isotonic fit solves; adding it back restores the
    # spacing. The ramp is cumulative, so it carries a different requirement per
    # pair just as happily as one shared by all.
    ramp = [0.0]
    for gap in gaps_needed:
        ramp.append(ramp[-1] + gap)
    fitted = isotonic_non_decreasing([value - offset for value, offset in zip(unrolled, ramp)])

    # The fit honours every gap it was given, but it was not given the seam — it
    # runs on the straightened row, where the last label has no neighbour. So it
    # will happily leave the row spanning more arc than the circle can spare, and
    # the overflow lands in the one gap it cannot see: the labels crowd the seam
    # instead of each other. The old code never hit this because it clamped the
    # requirement to the span already occupied, which meant the row could not
    # grow at all; letting it grow is the point of the change above, so the
    # ceiling has to be stated here instead.
    #
    # It is stated on `fitted`, not on the finished placement. The row's total
    # width is `(fitted[-1] - fitted[0]) + sum(gaps_needed)`: the ramp carries
    # every pair's requirement, and `fitted` carries only where the crowd chose
    # to sit. Squeezing the finished placement would scale both, taking pairs
    # below the separation they were promised — with half-extents of 90, 89 and
    # 1 degree, a pair owed 91° came out with 90.5°. Squeezing `fitted` alone
    # cannot: every gap stays `gaps_needed[i]` plus a non-negative amount,
    # because a non-decreasing sequence scaled about its centre stays
    # non-decreasing.
    max_span = 360.0 - (seam_needed * shrink)
    slack = max_span - sum(gaps_needed)
    fitted_span = fitted[-1] - fitted[0]
    if fitted_span > slack:
        centre = (fitted[0] + fitted[-1]) / 2.0
        # slack <= 0 means the gaps alone fill the budget: the crowd collapses
        # onto the ramp and every gap lands exactly on its requirement.
        squeeze = slack / fitted_span if slack > 0 else 0.0
        fitted = [centre + (value - centre) * squeeze for value in fitted]

    placed = [value + offset for value, offset in zip(fitted, ramp)]

    result = [0.0] * count
    for position, index in enumerate(order[(cut + 1) % count :] + order[: (cut + 1) % count]):
        result[index] = normalize_degree(placed[position] + start)
    return result
