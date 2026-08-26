"""Derive the modern wheel's small and large cluster profiles from the shipped medium.

The medium cluster is not derived — it is the shipped, eye-tuned layout, and
its ten numbers per ring are the source this script reads. What IS derived is
how that layout stretches to another glyph size, by one rule:

    The five element sizes are multiplied by ``k``. Every quantity of AIR the
    cluster owns — the clearance from the tether's end to the glyph's corner,
    the four ink-to-ink gaps between the rows, the margin from the last row to
    the ring's inner edge, and the tether's own depth below its anchor — is
    multiplied by ``a = min(k, fit)``, where ``fit`` is the factor that makes
    the stack fill the band exactly. Rows are then laid out top-down from the
    tether's end. The tether's tab never drops below ``MIN_INDICATOR_TICK``;
    when that floor binds, ``fit`` is re-solved with the tab pinned.

``a = k`` when the ring can afford it, so ``small`` is a pure homothety: ink,
air and tether all shrink together and the cluster is exactly the medium
cluster at 90%. ``a = fit`` when it cannot, which is every ring at ``large``:
the growth is paid for out of the air between the rows, because the rings
cannot deepen — the natal band ends at the house ring and the dual bands at
each other, and taking depth from the aspect core instead was considered and
refused.

Ink is modelled the way the renderer draws it: a text row's ink is centred on
its anchor (that is what ``_text_ink_offset`` is for) and spans half its font
size either side; a sign glyph spans its measured half-height at the inner-map
scale; the planet glyph spans its worst measured half-height row-ward and its
worst CORNER reach tether-ward, because the tether runs along the cluster's
radius and meets the axis-aligned glyph box on the diagonal — the clearance
that was reopened and fixed once already (see NATAL_PLANET_GLYPH_Y's comment).

Self-checks, run on every invocation and pinned by the test suite:
  * each ring's decomposition telescopes back to its band exactly;
  * the rule at ``k = 1`` reproduces the shipped medium rows to 1e-9.

Output: a human table per ring and size, and the Python literal block pasted
into ``draw_modern.GLYPH_SIZE_PROFILES`` — the module literals are this
script's output, and ``test_derivation_reproduces_the_shipped_profiles`` keeps
them from drifting apart.

The ``min_separation`` this script prints is an ANALYTIC SEED, scaled from the
medium ceiling by the binding row's ink growth and radius loss. Seeds are for
sweeping, not for shipping: the shipped ceilings come from
``scripts/measure_modern_separation.py``, which reads real rendered ink out of
a browser. Re-run this script after any change to a cluster size, a row
position, a ring radius, a tether constant or the ink tables — and then re-run
the measurement harness, whose ceilings a profile change moves.

Usage:
    python scripts/derive_modern_cluster_profiles.py           # table + literals
    python scripts/derive_modern_cluster_profiles.py --check   # self-checks only

@module scripts.derive_modern_cluster_profiles
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

from kerykeion.charts import draw_modern as dm
from kerykeion.charts.glyph_ink_metrics import (
    GLYPH_INK_HALF_HEIGHT,
    GLYPH_INK_HALF_WIDTH,
    SIGN_INK_HALF_HEIGHT,
)

# ---------------------------------------------------------------------------
# Worst-case ink, in native units, over everything the ring can be asked to draw
# ---------------------------------------------------------------------------


def worst_glyph_corner() -> float:
    """Deepest diagonal reach of any planet glyph from its anchor, map applied.

    The tether ends on the cluster's own radius, and a radius that meets an
    axis-aligned box near 45° reaches the corner, not the edge: the clearance
    must hold against sqrt(hw² + hh²), which the Sun wins at 15.167.
    """
    return max(
        math.hypot(GLYPH_INK_HALF_WIDTH[g], GLYPH_INK_HALF_HEIGHT[g]) * dm.GLYPH_SCALE_MAP.get(g, 1.0)
        for g in GLYPH_INK_HALF_WIDTH
    )


def worst_glyph_half_height() -> float:
    """Deepest row-ward reach of any planet glyph, map applied (Sun, 10.725)."""
    return max(
        GLYPH_INK_HALF_HEIGHT[g] * dm.GLYPH_SCALE_MAP.get(g, 1.0) for g in GLYPH_INK_HALF_HEIGHT
    )


def worst_sign_half_height() -> float:
    """Deepest reach of any sign glyph at the inner-ring map scale (13.45 x 0.9)."""
    return max(SIGN_INK_HALF_HEIGHT.values()) * dm._ZODIAC_DEFAULT_SCALE


# ---------------------------------------------------------------------------
# Ring geometry, read from the shipped module
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RingGeometry:
    """One ring's shipped medium layout plus its fixed frame."""

    name: str
    start_y: float  # where the tether hangs from (ruler edge, or the ring's own edge)
    arc_drop: float  # r(start) - arc_radius at medium; scales with the air
    tick: float  # the tether's tab at medium; scales with the air, floored
    inner_edge_y: float  # B: the ring's inner boundary, in y
    sizes: tuple[float, float, float, float, float]  # base, deg, sign, min, rx
    rows: tuple[float, float, float, float, float]  # glyph, deg, sign, min, rx
    min_separation: float
    binding_row: int  # index into rows of the row the medium ceiling binds on


# The natal tether: _draw_indicator_line's defaults, read from the module's
# own constants — the natal medium profile passes indicator=None and draws
# with exactly these. The duals pass their own dicts.
RINGS: dict[str, RingGeometry] = {
    "natal": RingGeometry(
        name="natal",
        start_y=dm.HOUSE_LINE_OUTER_Y,
        arc_drop=(50.0 - dm.HOUSE_LINE_OUTER_Y) - (dm.R_PLANET_OUTER - dm.NATAL_INDICATOR_ARC_DROP),
        tick=dm.NATAL_INDICATOR_TICK,
        inner_edge_y=50.0 - dm.R_PLANET_INNER,
        sizes=(
            dm.PLANET_SCALE_BASE,
            dm.DEGREES_FONT_SIZE,
            dm.SIGN_SCALE_BASE,
            dm.MINUTES_FONT_SIZE,
            dm.RX_FONT_SIZE,
        ),
        rows=(
            dm.NATAL_PLANET_GLYPH_Y,
            dm.NATAL_DEGREES_Y,
            dm.NATAL_SIGN_Y,
            dm.NATAL_MINUTES_Y,
            dm.NATAL_RX_Y,
        ),
        min_separation=dm.PLANET_MIN_SEPARATION,
        binding_row=3,  # the minutes text: smallest radius carrying two characters
    ),
    "dual_outer": RingGeometry(
        name="dual_outer",
        start_y=dm.SYN_INDICATOR_OUTER_START_Y,
        arc_drop=(50.0 - dm.SYN_INDICATOR_OUTER_START_Y) - dm.SYN_INDICATOR_OUTER_ARC_R,
        tick=dm.SYN_INDICATOR_OUTER_TICK,
        inner_edge_y=50.0 - dm.SYN_R_OUTER_PLANET_INNER,
        sizes=(
            dm.SYN_PLANET_SCALE,
            dm.SYN_DEGREES_FONT_SIZE,
            dm.SYN_SIGN_SCALE,
            dm.SYN_MINUTES_FONT_SIZE,
            dm.SYN_RX_FONT_SIZE,
        ),
        rows=(
            dm.SYN_OUTER_PLANET_GLYPH_Y,
            dm.SYN_OUTER_DEGREES_Y,
            dm.SYN_OUTER_SIGN_Y,
            dm.SYN_OUTER_MINUTES_Y,
            dm.SYN_OUTER_RX_Y,
        ),
        min_separation=dm.SYN_OUTER_MIN_SEPARATION,
        binding_row=1,  # the degrees text, per the SYN ceiling comment
    ),
    "dual_inner": RingGeometry(
        name="dual_inner",
        start_y=dm.SYN_INDICATOR_INNER_START_Y,
        arc_drop=(50.0 - dm.SYN_INDICATOR_INNER_START_Y) - dm.SYN_INDICATOR_INNER_ARC_R,
        tick=dm.SYN_INDICATOR_INNER_TICK,
        inner_edge_y=50.0 - dm.SYN_R_INNER_PLANET_INNER,
        sizes=(
            dm.SYN_PLANET_SCALE_INNER,
            dm.SYN_DEGREES_FONT_SIZE_INNER,
            dm.SYN_SIGN_SCALE,
            dm.SYN_MINUTES_FONT_SIZE,
            dm.SYN_RX_FONT_SIZE,
        ),
        rows=(
            dm.SYN_INNER_PLANET_GLYPH_Y,
            dm.SYN_INNER_DEGREES_Y,
            dm.SYN_INNER_SIGN_Y,
            dm.SYN_INNER_MINUTES_Y,
            dm.SYN_INNER_RX_Y,
        ),
        min_separation=dm.SYN_INNER_MIN_SEPARATION,
        binding_row=1,
    ),
}


# The three glyph sizes. Large is defined by classic parity: the planet glyph
# renders at the classic engine's own size — scale 1.0 (24 units) on a single
# wheel, 0.8 (19.2) on a dual — through the 0.92 zodiac-ring wrapper and the
# 4.8 page scale of the default template.
#
# On the dual rings the two factors SPLIT at large. Parity is the glyph's
# contract alone: the dual reading — degrees, sign, minutes, ℞ — follows the
# SINGLE wheel's typographic progression (the natal k) instead of the dual
# glyph's ×1.372. The dual cluster is text-heavy by construction (its reading
# stands at 0.67 of its glyph against the natal 0.51), and one factor for
# everything made the dual degree numerals at large larger than the single
# wheel's — judged on the rendered gallery, and refused: a reader should meet
# the same type ramp on every wheel, and only the glyph has a parity to chase.
def size_factors(ring_name: str) -> dict[str, tuple[float, float]]:
    """Per size for *ring_name*: ``(k_glyph, k_text)`` multipliers."""
    base = RINGS[ring_name].sizes[0]
    classic_scale = 1.0 if ring_name == "natal" else 0.8
    parity_base = classic_scale / (dm.ZODIAC_BG_SCALE * dm.MODERN_PAGE_SCALE)
    k_glyph_large = parity_base / base
    natal_base = RINGS["natal"].sizes[0]
    natal_k_large = (1.0 / (dm.ZODIAC_BG_SCALE * dm.MODERN_PAGE_SCALE)) / natal_base
    k_text_large = k_glyph_large if ring_name == "natal" else natal_k_large
    return {
        "small": (0.9, 0.9),
        "medium": (1.0, 1.0),
        "large": (k_glyph_large, k_text_large),
    }


# ---------------------------------------------------------------------------
# Decomposition and derivation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Decomposition:
    """The shipped medium layout of one ring, split into ink and air."""

    tether_reach: float  # T: deepest y the tether touches at medium
    corner_clearance: float  # c_top: T to the glyph's corner reach
    gaps: tuple[float, float, float, float]  # ink-to-ink air between the rows
    bottom: float  # last row's ink edge to the ring's inner edge
    ink: float  # everything the k-multiplier scales
    air: float  # everything the a-multiplier scales (corner + gaps + bottom)
    band: float  # inner_edge_y - T


def _ink_half_heights(
    ring: RingGeometry, k_glyph: float = 1.0, k_text: float | None = None
) -> tuple[float, ...]:
    """Row-ward ink half-heights of the five rows, per-element factors applied.

    The glyph row scales by ``k_glyph``; the reading — degrees, sign, minutes,
    ℞ — by ``k_text`` (defaults to ``k_glyph``: one factor, the single-wheel
    case).
    """
    if k_text is None:
        k_text = k_glyph
    base, deg, sign, minutes, rx = ring.sizes
    return (
        worst_glyph_half_height() * base * k_glyph,
        0.5 * deg * k_text,
        worst_sign_half_height() * sign * k_text,
        0.5 * minutes * k_text,
        0.5 * rx * k_text,
    )


def decompose(ring: RingGeometry) -> Decomposition:
    """Split *ring*'s shipped medium band into ink and air, exactly."""
    tether_reach = ring.start_y + ring.arc_drop + ring.tick
    halves = _ink_half_heights(ring)
    corner = worst_glyph_corner() * ring.sizes[0]
    corner_clearance = ring.rows[0] - tether_reach - corner
    gaps = tuple(
        (ring.rows[i + 1] - halves[i + 1]) - (ring.rows[i] + halves[i]) for i in range(4)
    )
    bottom = ring.inner_edge_y - (ring.rows[4] + halves[4])
    ink = corner + halves[0] + 2 * sum(halves[1:])
    air = corner_clearance + sum(gaps) + bottom
    band = ring.inner_edge_y - tether_reach
    residual = (ink + air) - band
    if abs(residual) > 1e-9:
        raise AssertionError(
            f"{ring.name}: ink {ink:.9f} + air {air:.9f} does not telescope back "
            f"to the band {band:.9f} (off by {residual:.2e}) — the model no "
            "longer describes the shipped medium."
        )
    return Decomposition(tether_reach, corner_clearance, gaps, bottom, ink, air, band)  # type: ignore[arg-type]


#: How far every DERIVED cluster slides outward, toward its indicator, in
#: wheel units. Giacomo's call on the rendered dual wheels: the ℞ row must not
#: sit on the ring's inner edge, and the space to buy it from is the tether's
#: side, where the tab leaves slack. The whole cluster moves together and the
#: tab shortens by the same amount (floored at MIN_INDICATOR_TICK), so the
#: tab-to-glyph distance stays as designed wherever the floor does not bind.
#: Where it DOES bind, the shift is capped by the tether-side slack: the tab
#: must never reach the glyph's row-ward ink (TETHER_INK_GAP_MIN of daylight
#: kept) — without the cap, the small dual-inner ring's tether would land
#: 0.13 units INSIDE its glyph's ink. Applied to every ring and every derived
#: size — all chart types, one treatment — and NEVER to medium, which is the
#: byte-identity anchor.
OUTWARD_SHIFT = 0.3

#: The hair of daylight the tab keeps from the glyph's row-ward ink when the
#: outward shift is capped by the tick floor.
TETHER_INK_GAP_MIN = 0.05


@dataclass(frozen=True)
class DerivedProfile:
    """One ring's layout at one glyph size, as the rule lays it out."""

    name: str
    k: float
    k_text: float
    a: float
    sizes: tuple[float, float, float, float, float]
    rows: tuple[float, float, float, float, float]
    start_y: float
    tick: float
    arc_radius: float
    min_separation_seed: float
    gaps: tuple[float, float, float, float]
    bottom_margin: float


def derive(ring: RingGeometry, k: float, k_text: float | None = None) -> DerivedProfile:
    """Lay *ring* out under the one documented rule.

    ``k`` scales the planet glyph; ``k_text`` (default ``k``) scales the
    reading — degrees, sign, minutes, ℞. They split only on the dual rings at
    large, where parity belongs to the glyph alone and the reading follows the
    single wheel's progression. The air factor caps at the LARGER of the two:
    small stays a pure homothety, and a ring that cannot afford its ink pays
    from the air exactly as before.
    """
    if k_text is None:
        k_text = k
    d = decompose(ring)
    halves = _ink_half_heights(ring, k, k_text)
    corner = worst_glyph_corner() * ring.sizes[0] * k
    ink_k = corner + halves[0] + 2 * sum(halves[1:])
    tether_span = ring.arc_drop + ring.tick
    room = ring.inner_edge_y - ring.start_y

    # fit: start + a*(tether + air) + ink == inner edge
    fit = (room - ink_k) / (tether_span + d.air)
    if fit * ring.tick < dm.MIN_INDICATOR_TICK:
        # The tab has hit its floor: pin it and re-solve for the rest.
        fit = (room - dm.MIN_INDICATOR_TICK - ink_k) / (ring.arc_drop + d.air)
    a = min(max(k, k_text), fit)

    # The outward shift: everything but medium slides toward the indicator.
    # k == k_text == 1 is the medium fixed point and must reproduce the
    # shipped constants exactly, so the shift is zero there by definition.
    #
    # While the tab is above its floor, tab and cluster retreat together and
    # the tab-to-ink gap is unchanged; once the floor binds, every further
    # unit of shift eats the gap one for one. The cap solves that in closed
    # form: s_free is the shift the tab can absorb, and beyond it the shift
    # may spend the gap down to TETHER_INK_GAP_MIN and no further.
    if k == k_text == 1.0:
        shift = 0.0
    else:
        tick0 = max(a * ring.tick, dm.MIN_INDICATOR_TICK)
        row0_glyph = ring.start_y + a * ring.arc_drop + tick0 + a * d.corner_clearance + corner
        gap0 = (row0_glyph - halves[0]) - (ring.start_y + a * ring.arc_drop + tick0)
        s_free = max(a * ring.tick - dm.MIN_INDICATOR_TICK, 0.0)
        s_max = s_free + max(gap0 - TETHER_INK_GAP_MIN, 0.0)
        shift = min(OUTWARD_SHIFT, s_max)

    tick = max(a * ring.tick - shift, dm.MIN_INDICATOR_TICK)
    arc_radius = (50.0 - ring.start_y) - a * ring.arc_drop
    tether_reach = ring.start_y + a * ring.arc_drop + tick

    rows = [tether_reach + a * d.corner_clearance + corner - (shift - (max(a * ring.tick, dm.MIN_INDICATOR_TICK) - tick))]
    for i in range(4):
        rows.append(rows[i] + halves[i] + a * d.gaps[i] + halves[i + 1])
    bottom_margin = ring.inner_edge_y - (rows[4] + halves[4])

    # The ceiling seed: the medium ceiling, scaled by the binding row's ink
    # growth and by the arc it loses moving inward. A seed, not a measurement.
    # The binding row is text on every ring, so it grows by k_text.
    r_med = 50.0 - ring.rows[ring.binding_row]
    r_new = 50.0 - rows[ring.binding_row]
    seed = ring.min_separation * k_text * (r_med / r_new)

    sizes = (
        ring.sizes[0] * k,
        ring.sizes[1] * k_text,
        ring.sizes[2] * k_text,
        ring.sizes[3] * k_text,
        ring.sizes[4] * k_text,
    )
    return DerivedProfile(
        ring.name, k, k_text, a, sizes, tuple(rows), ring.start_y, tick, arc_radius, seed,  # type: ignore[arg-type]
        d.gaps if a == k == k_text else tuple(g * a for g in d.gaps), bottom_margin,  # type: ignore[arg-type]
    )


def self_check() -> None:
    """The rule is a fixed point at ``k = 1``: it must reproduce the shipped rows."""
    for ring in RINGS.values():
        decompose(ring)  # raises if ink + air != band
        reproduced = derive(ring, 1.0, 1.0)
        for shipped, derived in zip(ring.rows, reproduced.rows):
            if abs(shipped - derived) > 1e-9:
                raise AssertionError(
                    f"{ring.name}: the rule at k=1 lays a row at {derived:.9f} "
                    f"where the shipped medium has {shipped}: the derivation no "
                    "longer reproduces the layout it claims to scale."
                )
        if abs(reproduced.tick - ring.tick) > 1e-9 or abs(
            reproduced.arc_radius - ((50.0 - ring.start_y) - ring.arc_drop)
        ) > 1e-9:
            raise AssertionError(f"{ring.name}: the tether at k=1 is not the shipped tether.")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _fmt_sizes(p: DerivedProfile) -> str:
    return " / ".join(f"{v:.6f}" for v in p.sizes)


def _fmt_rows(p: DerivedProfile) -> str:
    return " / ".join(f"{v:.4f}" for v in p.rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="run the self-checks and exit")
    args = parser.parse_args()

    self_check()
    if args.check:
        print("self-checks passed: ink+air telescopes, and k=1 reproduces the shipped medium.")
        return

    for ring_name, ring in RINGS.items():
        d = decompose(ring)
        print(f"\n=== {ring_name} ===")
        print(
            f"band {d.band:.4f}  ink {d.ink:.4f} ({d.ink / d.band:.1%})  air {d.air:.4f}"
            f"  [corner {d.corner_clearance:+.4f}, gaps {', '.join(f'{g:.4f}' for g in d.gaps)},"
            f" bottom {d.bottom:.4f}]"
        )
        for size, (k, k_text) in size_factors(ring_name).items():
            p = derive(ring, k, k_text)
            print(
                f"{size:>7}: k={p.k:.6f} k_text={p.k_text:.6f} a={p.a:.4f}  rows {_fmt_rows(p)}\n"
                f"         sizes {_fmt_sizes(p)}  tick {p.tick:.4f} arc {p.arc_radius:.4f}"
                f"  sep-seed {p.min_separation_seed:.2f}  bottom {p.bottom_margin:.4f}"
            )

    print("\n--- literals for draw_modern.GLYPH_SIZE_PROFILES " + "-" * 30)
    for size in ("small", "large"):
        for ring_name, ring in RINGS.items():
            k, k_text = size_factors(ring_name)[size]
            p = derive(ring, k, k_text)
            var = f"_{size.upper()}_{ring_name.upper()}"
            classic_scale = "1.0" if ring_name == "natal" else "0.8"
            base_expr = (
                f"{classic_scale} / (ZODIAC_BG_SCALE * MODERN_PAGE_SCALE)"
                if size == "large"
                else f"{p.sizes[0]:.6f}"
            )
            indicator = (
                f'{{\n        "start_y": {"HOUSE_LINE_OUTER_Y" if ring.start_y == dm.HOUSE_LINE_OUTER_Y else p.start_y},\n'
                f'        "tick_length": {p.tick:.4f},\n'
                f'        "arc_radius": {p.arc_radius:.4f},\n    }}'
            )
            print(
                f"{var} = ClusterProfile(\n"
                f"    planet_scale_base={base_expr},\n"
                f"    degrees_font_size={p.sizes[1]:.6f},\n"
                f"    sign_scale_base={p.sizes[2]:.6f},\n"
                f"    minutes_font_size={p.sizes[3]:.6f},\n"
                f"    rx_font_size={p.sizes[4]:.6f},\n"
                f"    glyph_y={p.rows[0]:.4f},\n"
                f"    degrees_y={p.rows[1]:.4f},\n"
                f"    sign_y={p.rows[2]:.4f},\n"
                f"    minutes_y={p.rows[3]:.4f},\n"
                f"    rx_y={p.rows[4]:.4f},\n"
                f"    min_separation={p.min_separation_seed:.2f},  # analytic seed — harness re-measures\n"
                f"    indicator={indicator},\n"
                f")"
            )


if __name__ == "__main__":
    main()
