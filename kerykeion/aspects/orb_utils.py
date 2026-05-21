# -*- coding: utf-8 -*-
"""
Per-point orb adjustment resolver.

Astrological practice varies the orb of an aspect depending on which points
form it — most commonly, a wider orb when the Sun or Moon is involved. This
module resolves a single additive orb adjustment for a *pair* of points from
a per-point adjustment table.

The resolver only looks at points that are *explicitly* present in the table.
Missing points are not treated as ``0.0`` until after the explicit values are
collected — this is what makes negative adjustments behave correctly. For
example, with ``{"Pluto": -2.0}`` and the pair ``(Pluto, Saturn)``, the
``max_explicit`` strategy resolves to ``-2.0`` (only Pluto is configured), so
the effective orb is tightened. A naive ``max(adj_a, adj_b)`` over defaulted
values would yield ``max(-2.0, 0.0) == 0.0`` and silently drop the tightening.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from typing import Literal, Mapping, Optional

OrbAdjustmentStrategy = Literal["max_explicit", "min_explicit", "sum", "none"]
"""How to combine the orb adjustments of the two points in a pair.

- ``max_explicit``: widest configured adjustment wins (reproduces the classic
  "if either point is a luminary, use the luminary orb" rule). Default.
- ``min_explicit``: tightest configured adjustment wins.
- ``sum``: adjustments of both configured points are added together.
- ``none``: adjustments are disabled (always resolves to ``0.0``).
"""


def resolve_pair_orb_adjustment(
    first_name: str,
    second_name: str,
    point_orb_adjustments: Optional[Mapping[str, float]],
    strategy: OrbAdjustmentStrategy = "max_explicit",
) -> float:
    """Resolve the additive orb adjustment for a pair of points.

    Args:
        first_name: Name of the first point (e.g. ``"Sun"``).
        second_name: Name of the second point.
        point_orb_adjustments: Mapping of point name → orb adjustment in
            degrees. ``None`` or empty disables adjustments.
        strategy: How to combine the two points' adjustments. See
            :data:`OrbAdjustmentStrategy`.

    Returns:
        The orb adjustment in degrees to add to the aspect's base orb.
        ``0.0`` when no point in the pair is configured.
    """
    if not point_orb_adjustments or strategy == "none":
        return 0.0

    values = [
        point_orb_adjustments[name]
        for name in (first_name, second_name)
        if name in point_orb_adjustments
    ]

    if not values:
        return 0.0

    if strategy == "max_explicit":
        return max(values)
    if strategy == "min_explicit":
        return min(values)
    if strategy == "sum":
        return sum(values)

    return 0.0
