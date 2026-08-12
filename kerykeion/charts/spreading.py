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


def spread_around_wheel(angles: Sequence[float], min_separation: float) -> list[float]:
    """Angles moved as little as possible so consecutive ones sit apart.

    *angles* are degrees on the wheel in drawing order; the return is the same
    length and the same order, each entry normalised to ``[0, 360)``. An input
    already comfortable is returned unchanged, so a chart with evenly spaced
    houses keeps exactly the placement it had.

    The circle is cut at the widest existing gap before the row is straightened
    out. Cutting anywhere else can split a crowd across the seam, and the
    straight-line algorithm cannot see that its first and last entries are
    neighbours; the widest gap is the one place guaranteed not to be inside a
    crowd. When even the total will not fit — twelve labels wanting more than
    360° between them — the requirement is scaled down to what the circle has,
    which spreads the crowding evenly instead of piling it all at the seam.
    """
    count = len(angles)
    if count < 2 or min_separation <= 0:
        return [angle % 360.0 for angle in angles]

    order = sorted(range(count), key=lambda i: angles[i] % 360.0)
    sorted_angles = [angles[i] % 360.0 for i in order]

    gaps = [
        (sorted_angles[(i + 1) % count] - sorted_angles[i]) % 360.0
        for i in range(count)
    ]
    cut = max(range(count), key=lambda i: gaps[i])

    # Unroll starting just after the widest gap, so the sequence is monotonic.
    rolled = [sorted_angles[(cut + 1 + i) % count] for i in range(count)]
    start = rolled[0]
    unrolled = [(angle - start) % 360.0 for angle in rolled]

    separation = min_separation
    needed = separation * (count - 1)
    available = unrolled[-1] - unrolled[0]
    if needed > available and needed > 0:
        # More labels than the arc can hold at full separation: share the
        # shortfall rather than letting the last few pile up.
        separation = available / (count - 1) if count > 1 else 0.0

    # Subtracting a ramp turns "at least `separation` apart" into "non
    # decreasing", which is what the isotonic fit solves; adding it back
    # restores the spacing.
    ramp = [i * separation for i in range(count)]
    fitted = isotonic_non_decreasing([value - offset for value, offset in zip(unrolled, ramp)])
    placed = [value + offset for value, offset in zip(fitted, ramp)]

    result = [0.0] * count
    for position, index in enumerate(order[(cut + 1) % count :] + order[: (cut + 1) % count]):
        result[index] = (placed[position] + start) % 360.0
    return result
