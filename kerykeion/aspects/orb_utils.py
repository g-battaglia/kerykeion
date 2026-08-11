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

A table entry can also vary by aspect. Instead of a single number, a point may
carry a mapping of aspect name → adjustment, with ``"*"`` as the default for
aspects not listed::

    {
        "Sun": 1.5,                              # every aspect
        "Moon": {"*": 1.5, "conjunction": 3.0},  # 3.0 for conjunctions, 1.5 otherwise
        "Ascendant": {"conjunction": -3.0},      # configured ONLY for conjunctions
    }

The explicit-only philosophy carries over per aspect: without a ``"*"`` key, a
point is *unconfigured* for the aspects it does not list (not ``0.0``), so a
trine to the Ascendant above resolves exactly as if the Ascendant were absent
from the table.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

import logging
import math
from numbers import Real
from typing import Iterable, Literal, Mapping, Optional, Union, get_args

from kerykeion.schemas.kr_literals import AspectName

logger = logging.getLogger(__name__)

OrbAdjustmentStrategy = Literal["max_explicit", "min_explicit", "sum", "none"]
"""How to combine the orb adjustments of the two points in a pair.

- ``max_explicit``: widest configured adjustment wins (reproduces the classic
  "if either point is a luminary, use the luminary orb" rule). Default.
- ``min_explicit``: tightest configured adjustment wins.
- ``sum``: adjustments of both configured points are added together.
- ``none``: adjustments are disabled (always resolves to ``0.0``).
"""

PointOrbAdjustment = Union[float, Mapping[str, float]]
"""A point's entry in an orb adjustment table.

Either a single number (an additive delta applied to every aspect's base orb)
or a mapping of aspect name → delta with the optional ``"*"`` key acting as
the default for aspects not listed. ``number`` and ``{"*": number}`` are
equivalent.
"""

ASPECT_ORB_WILDCARD = "*"
"""The aspect-map key that supplies the default delta for unlisted aspects."""

# Known aspect names, used to flag probable typos in aspect-keyed adjustment
# maps. A warning, not an error — mirroring how active_aspects treats unknown
# names — so a table can be shared across configurations that enable
# different aspect sets.
_KNOWN_ASPECT_NAMES: frozenset = frozenset(get_args(AspectName))


def _is_finite_real(value: object) -> bool:
    """Return whether *value* is a real number representable as a finite float.

    ``bool`` is excluded: it is technically a ``Real`` (``int`` subclass), but
    ``True``/``False`` as an orb adjustment is always a caller mistake.
    """
    if isinstance(value, bool) or not isinstance(value, Real):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError):
        return False


def validate_point_orb_adjustments(
    point_orb_adjustments: Optional[Mapping[str, PointOrbAdjustment]],
) -> None:
    """Validate every configured per-point orb adjustment once, up front.

    Accepts both entry forms: a plain number, or an aspect-keyed mapping
    (``{"conjunction": 3.0, "*": 1.5}``). Unknown aspect names in a mapping
    log a warning rather than raising — consistent with how unknown
    ``active_aspects`` names are treated — since the key may belong to an
    aspect set this configuration simply does not enable.
    """
    if point_orb_adjustments is None:
        return
    for point_name, adjustment in point_orb_adjustments.items():
        if not isinstance(point_name, str):
            raise ValueError(f"point_orb_adjustments keys must be point names, got {point_name!r}.")
        if isinstance(adjustment, Mapping):
            for aspect_key, leaf in adjustment.items():
                if not isinstance(aspect_key, str):
                    raise ValueError(
                        f"point_orb_adjustments[{point_name!r}] keys must be aspect names "
                        f"or '{ASPECT_ORB_WILDCARD}', got {aspect_key!r}."
                    )
                if aspect_key != ASPECT_ORB_WILDCARD and aspect_key not in _KNOWN_ASPECT_NAMES:
                    logger.warning(
                        "point_orb_adjustments[%r] has an unrecognized aspect name %r; "
                        "it will never match a computed aspect. Check for a typo.",
                        point_name,
                        aspect_key,
                    )
                if not _is_finite_real(leaf):
                    raise ValueError(
                        f"point_orb_adjustments[{point_name!r}][{aspect_key!r}] must be "
                        f"a finite number, got {leaf!r}."
                    )
        elif not _is_finite_real(adjustment):
            raise ValueError(
                f"point_orb_adjustments[{point_name!r}] must be a finite number, got {adjustment!r}."
            )


def lookup_point_adjustment(
    adjustment: Optional[PointOrbAdjustment],
    aspect_name: Optional[str] = None,
) -> Optional[float]:
    """Resolve one point's table entry for a specific aspect.

    Args:
        adjustment: The point's entry — a number, an aspect-keyed mapping, or
            ``None`` when the point is not in the table.
        aspect_name: The aspect being evaluated. ``None`` means "no aspect
            context": aspect-keyed mappings then fall back to their ``"*"``
            entry only, so legacy callers see per-aspect overrides as if they
            were not there.

    Returns:
        The resolved delta, or ``None`` when the point is unconfigured for
        this aspect (a missing point, an aspect absent from a mapping without
        ``"*"``, or an empty mapping). ``None`` is deliberately distinct from
        ``0.0`` — see the module docstring.

    Note:
        No finiteness validation happens here; callers validate the resolved
        value (``resolve_pair_orb_adjustment``) or the whole table up front
        (``validate_point_orb_adjustments``).
    """
    if adjustment is None or not isinstance(adjustment, Mapping):
        return adjustment
    if aspect_name is not None and aspect_name in adjustment:
        return adjustment[aspect_name]
    return adjustment.get(ASPECT_ORB_WILDCARD)


def has_aspect_keyed_adjustments(
    point_orb_adjustments: Optional[Mapping[str, PointOrbAdjustment]],
) -> bool:
    """Return whether any table entry varies by aspect (is a mapping).

    Callers use this once per calculation to decide between the scalar
    fast path (one resolve per pair) and the per-aspect path (one resolve
    per pair per aspect in play).
    """
    return bool(point_orb_adjustments) and any(
        isinstance(value, Mapping) for value in point_orb_adjustments.values()  # type: ignore[union-attr]
    )


def _validate_strategy(strategy: OrbAdjustmentStrategy) -> None:
    """Fail fast on a misspelled strategy rather than silently returning 0.0,
    which would quietly disable the orb adjustment and yield wrong aspects.
    """
    if strategy not in ("max_explicit", "min_explicit", "sum", "none"):
        raise ValueError(
            f"Unknown orb adjustment strategy: {strategy!r}. "
            "Expected one of: 'max_explicit', 'min_explicit', 'sum', 'none'."
        )


def resolve_pair_orb_adjustments_for_aspects(
    first_name: str,
    second_name: str,
    point_orb_adjustments: Optional[Mapping[str, PointOrbAdjustment]],
    strategy: OrbAdjustmentStrategy,
    aspect_names: Iterable[str],
) -> dict:
    """Resolve a pair's adjustment for each named aspect.

    Returns a plain ``{aspect_name: delta}`` dict — the ``"*"`` wildcard and
    the combination strategy are fully collapsed here, so the result can be
    fed directly to ``get_aspect_from_two_points`` as a per-aspect
    ``extra_orb``.
    """
    names = list(aspect_names)
    if not names:
        # No aspects in play, but the call must keep the scalar path's whole
        # contract — strategy validation AND the pair's wildcard-value checks.
        # ``number ≡ {"*": number}`` extends to the error behavior: a sum
        # overflow raises identically on both forms instead of the wildcard
        # one silently returning an empty result. Resolve once, discard.
        resolve_pair_orb_adjustment(first_name, second_name, point_orb_adjustments, strategy)
        return {}
    return {
        aspect_name: resolve_pair_orb_adjustment(
            first_name,
            second_name,
            point_orb_adjustments,
            strategy,
            aspect_name=aspect_name,
        )
        for aspect_name in names
    }


def resolve_pair_orb_adjustment(
    first_name: str,
    second_name: str,
    point_orb_adjustments: Optional[Mapping[str, PointOrbAdjustment]],
    strategy: OrbAdjustmentStrategy = "max_explicit",
    *,
    aspect_name: Optional[str] = None,
) -> float:
    """Resolve the additive orb adjustment for a pair of points.

    Args:
        first_name: Name of the first point (e.g. ``"Sun"``).
        second_name: Name of the second point.
        point_orb_adjustments: Mapping of point name → orb adjustment in
            degrees. Each entry is either a number or an aspect-keyed mapping
            (see :data:`PointOrbAdjustment`). ``None`` or empty disables
            adjustments.
        strategy: How to combine the two points' adjustments. See
            :data:`OrbAdjustmentStrategy`.
        aspect_name: The aspect the pair is being evaluated for. When ``None``
            (the default, and the behavior of every pre-existing caller),
            aspect-keyed entries resolve through their ``"*"`` key only.

    Returns:
        The orb adjustment in degrees to add to the aspect's base orb.
        ``0.0`` when no point in the pair is configured (for this aspect).

    Raises:
        ValueError: If ``strategy`` is not a recognised
            :data:`OrbAdjustmentStrategy` value.
    """
    # Validated *before* any early return so the error surfaces even when the
    # table is empty or the pair is unconfigured.
    _validate_strategy(strategy)

    if not point_orb_adjustments or strategy == "none":
        return 0.0

    v1 = lookup_point_adjustment(point_orb_adjustments.get(first_name), aspect_name)
    v2 = lookup_point_adjustment(point_orb_adjustments.get(second_name), aspect_name)

    # Direct callers of this resolver still get a safe boundary even when they
    # bypass the factory-level whole-mapping validation.
    for point_name, value in ((first_name, v1), (second_name, v2)):
        if value is not None and not _is_finite_real(value):
            raise ValueError(
                f"point_orb_adjustments[{point_name!r}] must be a finite number, got {value!r}."
            )

    if v1 is None and v2 is None:
        return 0.0

    if strategy == "max_explicit":
        if v1 is not None and v2 is not None:
            return v1 if v1 > v2 else v2
        return v1 if v1 is not None else v2  # type: ignore[return-value]
    if strategy == "min_explicit":
        if v1 is not None and v2 is not None:
            return v1 if v1 < v2 else v2
        return v1 if v1 is not None else v2  # type: ignore[return-value]

    # strategy == "sum" (the only remaining value after the check above).
    # Two individually finite floats can still overflow when combined.
    combined = (v1 or 0.0) + (v2 or 0.0)
    if not _is_finite_real(combined):
        raise ValueError(
            f"Combined point-orb adjustment for {first_name!r} and {second_name!r} "
            "must be finite."
        )
    return combined
