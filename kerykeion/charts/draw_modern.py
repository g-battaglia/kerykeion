# -*- coding: utf-8 -*-
"""
Modern Concentric Rings Chart Drawing Module
=============================================

This module provides all drawing functions for the modern chart style,
which renders an astrological wheel as 5 concentric rings:

    Ring 1 (outer): House cusps with zodiac sign glyphs and degree/minute data
    Ring 2: Graduated ruler scale (1°/5°/10° ticks)
    Ring 3: Planet data clusters with indicator/tether lines
    Ring 4 (inner): House numbers (1-12)
    Ring 5 (core): Aspect lines with small glyphs at midpoints

The entire chart is rendered in a viewBox of "0 0 100 100" centered at (50, 50).
All positioning uses rotational transforms: rotate(-angle 50 50).

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import math
from typing import Union

from kerykeion.schemas.kr_models import KerykeionPointModel


# =============================================================================
# RING RADII CONSTANTS
# =============================================================================

CENTER = 50.0

# Ring 5: Aspect core
R_ASPECT = 19.5

# Ring 4: House numbers
R_HOUSE_INNER = 19.5
R_HOUSE_OUTER = 22.0

# Ring 3: Planet band
R_PLANET_INNER = 22.0
R_PLANET_OUTER = 43.5

# Ring 2: Graduated ruler
R_RULER_INNER = 43.5
R_RULER_OUTER = 44.5

# Ring 1: Cusp/zodiac ring
R_CUSP_INNER = 44.5
R_CUSP_OUTER = 50.0

# Ring 0 (optional): Zodiac background ring (outermost, outside cusp ring)
# When enabled, the existing chart is scaled to fit inside R_ZODIAC_BG_INNER,
# and the zodiac wedges occupy R_ZODIAC_BG_INNER to R_ZODIAC_BG_OUTER.
R_ZODIAC_BG_INNER = 46.0
R_ZODIAC_BG_OUTER = 50.0
ZODIAC_BG_SCALE = R_ZODIAC_BG_INNER / R_CUSP_OUTER  # 0.92

# House line endpoints
HOUSE_LINE_OUTER_Y = 6.5  # Just inside the ruler ring outer edge
HOUSE_LINE_INNER_Y = 28.0  # At the house ring boundary

# Angular houses (1, 4, 7, 10) use thicker lines
ANGULAR_HOUSES = {1, 4, 7, 10}
ANGULAR_STROKE_WIDTH = 0.6
NORMAL_STROKE_WIDTH = 0.07

PLANET_MIN_SEPARATION = 8.0  # Minimum degrees between planet clusters

# Cusp ring text size (degrees and minutes shown at each house cusp)
CUSP_FONT_SIZE = 2.0

# Planet cluster element sizes — descending visual hierarchy:
#   planet glyph (largest) > degrees text > zodiac sign > minutes text > RX text
# Note: planet glyphs are ~28px native, zodiac signs are ~32px native,
# so zodiac sign scale must be proportionally smaller to appear smaller.
PLANET_SCALE_BASE = 0.135  # Planet glyph: 28 * 0.135 ≈ 3.78 visual units
DEGREES_FONT_SIZE = 2  # Degrees text font size
SIGN_SCALE_BASE = 0.078  # Zodiac sign: 32 * 0.078 ≈ 2.50 visual units
MINUTES_FONT_SIZE = 1.85  # Minutes text font size
RX_FONT_SIZE = 1.6  # Retrograde indicator font size

# =============================================================================
# SYNASTRY MODE — Flat dual-ring layout constants
# =============================================================================
# Instead of nesting a scaled-down inner chart, synastry uses two equal-width
# planet rings side by side in the same coordinate space.

# Aspect core (smaller than natal to make room for dual planet rings)
SYN_R_ASPECT = 12.5

# House number ring (narrower, pushed inward)
SYN_R_HOUSE_INNER = 12.5
SYN_R_HOUSE_OUTER = 15.5

# Inner planet ring — Subject 1 (natal)
SYN_R_INNER_PLANET_INNER = 15.5
SYN_R_INNER_PLANET_OUTER = 29.5

# Outer planet ring — Subject 2 (synastry partner)
SYN_R_OUTER_PLANET_INNER = 29.5
SYN_R_OUTER_PLANET_OUTER = 43.5

# House division line endpoints (Subject 1's cusps drawn in both rings)
SYN_HOUSE_LINE_OUTER_Y1 = 6.5  # Outer ring: top (near ruler)
SYN_HOUSE_LINE_OUTER_Y2 = 20.5  # Outer ring: bottom (at boundary)
SYN_HOUSE_LINE_INNER_Y1 = 20.5  # Inner ring: top (at boundary)
SYN_HOUSE_LINE_INNER_Y2 = 34.5  # Inner ring: bottom (near house numbers)

# Indicator line geometry (all start at boundary y = 20.5)
SYN_INDICATOR_START_Y = 20.5
SYN_INDICATOR_TICK = 0.7
SYN_INDICATOR_ARC_R_OUTWARD = 30.2  # Arc for outer-ring ticks (just outside boundary, r > 29.5)
SYN_INDICATOR_ARC_R_INWARD = 28.8  # Arc for inner-ring ticks (just inside boundary, r < 29.5)

# Planet cluster Y-positioning within each 14-unit ring
# Outer ring (Subject 2) - glyphs near outer edge, all elements within 6.5-20.5
SYN_OUTER_PLANET_GLYPH_Y = 9.0
SYN_OUTER_DEGREES_Y = 12.0
SYN_OUTER_SIGN_Y = 14.5
SYN_OUTER_MINUTES_Y = 16.5
SYN_OUTER_RX_Y = 18.5

# Inner ring (Subject 1) - glyphs near outer edge, all elements within 20.5-34.5
SYN_INNER_PLANET_GLYPH_Y = 22.5
SYN_INNER_DEGREES_Y = 25.0
SYN_INNER_SIGN_Y = 27.5
SYN_INNER_MINUTES_Y = 29.5
SYN_INNER_RX_Y = 31.5

# Dual chart element sizes — slightly smaller than natal to fit in narrower rings
SYN_PLANET_SCALE = 0.115  # Planet glyph (outer ring)
SYN_PLANET_SCALE_INNER = 0.095  # Planet glyph (inner ring — slightly smaller)
SYN_DEGREES_FONT_SIZE_INNER = 1.6  # Degrees text (inner ring — slightly smaller)
SYN_DEGREES_FONT_SIZE = 1.9  # Degrees text
SYN_SIGN_SCALE = 0.062  # Zodiac sign
SYN_MINUTES_FONT_SIZE = 1.4  # Minutes text
SYN_RX_FONT_SIZE = 1.2  # Retrograde indicator

# Colors — use CSS custom properties to inherit from the active theme.
# Each theme CSS file can define --kerykeion-modern-* overrides.
# Fallback hex values provide a clean neutral default (works when no CSS is present).
COLOR_BACKGROUND = "var(--kerykeion-chart-color-paper-1, #ffffff)"
COLOR_PLANET_RING = "var(--kerykeion-modern-planet-ring, #e8e8ed)"
COLOR_OUTER_PLANET_RING = "var(--kerykeion-modern-planet-ring-outer, #d8d9e4)"
COLOR_HOUSE_RING = "var(--kerykeion-modern-house-ring, #d5d5dd)"
COLOR_STROKE = "var(--kerykeion-modern-stroke, #b0b0bf)"
COLOR_TEXT = "var(--kerykeion-chart-color-paper-0, #333333)"
COLOR_RETROGRADE = "var(--kerykeion-modern-retrograde, #c43a5e)"
COLOR_INDICATOR = "var(--kerykeion-modern-indicator, #8a8a9e)"
COLOR_WHITE = "var(--kerykeion-chart-color-paper-1, #ffffff)"
COLOR_ZODIAC_BG_OPACITY = "var(--kerykeion-modern-zodiac-bg-opacity, 0.5)"

# Size adjustments to normalize SVG paths that have different intrinsic bounds
GLYPH_SCALE_MAP = {
    # Planets (target: all render at roughly equal visual weight)
    "Sun": 1.1,
    "Moon": 1.0,
    "Mercury": 1.0,
    "Venus": 1.0,
    "Mars": 0.95,
    "Jupiter": 0.95,
    "Saturn": 0.95,
    "Uranus": 0.95,
    "Neptune": 0.95,
    "Pluto": 1.0,
    "Chiron": 0.95,
    "Mean_Lilith": 1.0,
    "True_Lilith": 1.0,
    "Mean_North_Lunar_Node": 0.95,
    "True_North_Lunar_Node": 0.95,
    "Ascendant": 0.95,
    "Medium_Coeli": 0.95,
}

# Zodiac signs in the outer cusp ring (paths are ~32x32)
ZODIAC_OUTER_SCALE_MAP = {
    "Ari": 0.9,
    "Tau": 0.9,
    "Gem": 0.9,
    "Can": 0.9,
    "Leo": 0.9,
    "Vir": 0.9,
    "Lib": 0.9,
    "Sco": 0.9,
    "Sag": 0.9,
    "Cap": 0.9,
    "Aqu": 0.9,
    "Pis": 0.9,
}

# Zodiac signs in the inner planet ring (smaller base size)
ZODIAC_INNER_SCALE_MAP = {
    "Ari": 0.9,
    "Tau": 0.9,
    "Gem": 0.9,
    "Can": 0.9,
    "Leo": 0.9,
    "Vir": 0.9,
    "Lib": 0.9,
    "Sco": 0.9,
    "Sag": 0.9,
    "Cap": 0.9,
    "Aqu": 0.9,
    "Pis": 0.9,
}


# =============================================================================
# MATH HELPERS
# =============================================================================


def _deg_to_rad(deg: float) -> float:
    """Convert degrees to radians."""
    return deg * math.pi / 180.0


def _point_on_circle(angle_deg: float, radius: float) -> tuple[float, float]:
    """
    Calculate a point on a circle centered at (CENTER, CENTER).

    The angle follows the same convention as SVG rotate(-angle):
    0° = top (12 o'clock), increasing angle goes counterclockwise.

    Args:
        angle_deg: Angle in degrees (0° = top/north, counterclockwise).
        radius: Distance from center.

    Returns:
        Tuple (x, y) coordinates.
    """
    rad = _deg_to_rad(-angle_deg - 90)  # Negate to match rotate(-angle) convention
    x = CENTER + radius * math.cos(rad)
    y = CENTER + radius * math.sin(rad)
    return x, y


def _normalize_angle(angle: float) -> float:
    """Normalize angle to 0-360 range."""
    return angle % 360.0


def _zodiac_to_wheel_angle(
    abs_pos: float,
    seventh_house_degree_ut: float,
) -> float:
    """
    Convert absolute zodiacal position to wheel rotation angle.

    The wheel is oriented so that the Ascendant (first house cusp) is at
    the left (9 o'clock position). The seventh_house_degree_ut determines
    the rotation offset for the entire wheel.

    Args:
        abs_pos: Absolute zodiacal position (0-360°).
        seventh_house_degree_ut: Absolute degree of the 7th house cusp.

    Returns:
        Rotation angle for SVG rotate() transform.
    """
    return _normalize_angle(abs_pos - seventh_house_degree_ut + 180)


# =============================================================================
# ANNULUS PATH HELPER (replaces SVG masks for CSS-transform compatibility)
# =============================================================================


def _annulus_path(outer_r: float, inner_r: float) -> str:
    """Return SVG path data for an annulus (donut) centered at CENTER.

    Uses two concentric circle subpaths with fill-rule='evenodd' to create
    the ring shape geometrically, without SVG masks.
    """
    # Outer circle: two semicircular arcs
    d = (
        f"M {CENTER - outer_r},{CENTER} "
        f"A {outer_r},{outer_r} 0 1,1 {CENTER + outer_r},{CENTER} "
        f"A {outer_r},{outer_r} 0 1,1 {CENTER - outer_r},{CENTER} "
    )
    if inner_r > 0:
        # Inner circle: two semicircular arcs (evenodd punches the hole)
        d += (
            f"M {CENTER - inner_r},{CENTER} "
            f"A {inner_r},{inner_r} 0 1,1 {CENTER + inner_r},{CENTER} "
            f"A {inner_r},{inner_r} 0 1,1 {CENTER - inner_r},{CENTER} "
        )
    d += "Z"
    return d


# =============================================================================
# RING 1: ZODIAC BACKGROUND WEDGE RING (Optional)
# =============================================================================

_ZODIAC_SIGN_IDS = [
    "Ari",
    "Tau",
    "Gem",
    "Can",
    "Leo",
    "Vir",
    "Lib",
    "Sco",
    "Sag",
    "Cap",
    "Aqu",
    "Pis",
]


def _draw_zodiac_background_ring(seventh_house_degree_ut: float) -> str:
    """
    Draw the fully colored zodiac background wedges in the outermost ring,
    with zodiac sign glyphs centered in each wedge.

    Each wedge is an annular sector <path> (arc from R_ZODIAC_BG_INNER to
    R_ZODIAC_BG_OUTER), geometrically confined to the ring without masks.
    Each slice is colored using the CSS variable --kerykeion-chart-color-zodiac-bg-N.
    Each wedge also gets a zodiac sign glyph at its center.
    """
    # No mask — each wedge is geometrically confined to the annulus
    out = '<g kr:node="ZodiacBackgrounds">\n'

    # Midpoint radius for glyph placement
    r_mid = (R_ZODIAC_BG_INNER + R_ZODIAC_BG_OUTER) / 2.0
    glyph_scale = 0.09

    for sign_num in range(12):
        start_abs = sign_num * 30.0
        end_abs = start_abs + 30.0
        mid_abs = start_abs + 15.0  # Center of the 30° wedge

        # Angles converted to wheel coordinates
        start_angle = _zodiac_to_wheel_angle(start_abs, seventh_house_degree_ut)
        end_angle = _zodiac_to_wheel_angle(end_abs, seventh_house_degree_ut)
        mid_angle = _zodiac_to_wheel_angle(mid_abs, seventh_house_degree_ut)

        color = f"var(--kerykeion-modern-zodiac-bg-{sign_num})"

        # Convert wheel angles to radians for cos/sin.
        # The parent group has rotate(-90), so we subtract 90 to align.
        a_start_rad = math.radians(-start_angle - 90)
        a_end_rad = math.radians(-end_angle - 90)

        # 4 points of the annular sector
        ox1 = CENTER + R_ZODIAC_BG_OUTER * math.cos(a_start_rad)  # outer start
        oy1 = CENTER + R_ZODIAC_BG_OUTER * math.sin(a_start_rad)
        ox2 = CENTER + R_ZODIAC_BG_OUTER * math.cos(a_end_rad)  # outer end
        oy2 = CENTER + R_ZODIAC_BG_OUTER * math.sin(a_end_rad)
        ix1 = CENTER + R_ZODIAC_BG_INNER * math.cos(a_end_rad)  # inner end (reversed)
        iy1 = CENTER + R_ZODIAC_BG_INNER * math.sin(a_end_rad)
        ix2 = CENTER + R_ZODIAC_BG_INNER * math.cos(a_start_rad)  # inner start
        iy2 = CENTER + R_ZODIAC_BG_INNER * math.sin(a_start_rad)

        # SVG arc path: annular sector of 30 degrees
        # M  outer_start
        # A  outer arc (r=R_ZODIAC_BG_OUTER) 30deg, sweep clockwise
        # L  inner_end
        # A  inner arc (r=R_ZODIAC_BG_INNER) 30deg, sweep counter-clockwise
        # Z  close
        out += (
            f'  <path d="'
            f"M {ox1:.6f},{oy1:.6f} "
            f"A {R_ZODIAC_BG_OUTER},{R_ZODIAC_BG_OUTER} 0 0,0 {ox2:.6f},{oy2:.6f} "
            f"L {ix1:.6f},{iy1:.6f} "
            f"A {R_ZODIAC_BG_INNER},{R_ZODIAC_BG_INNER} 0 0,1 {ix2:.6f},{iy2:.6f} "
            f'Z" '
            f'fill="{color}" style="fill-opacity: {COLOR_ZODIAC_BG_OPACITY}" />\n'
        )

        # Draw the zodiac glyph centered in the wedge
        sign_id = _ZODIAC_SIGN_IDS[sign_num]
        # The group is already rotated by -90°. Each glyph is placed via
        # rotate(-mid_angle) which points it to the correct angular position,
        # then translated to r_mid, then counter-rotated to stay upright.
        counter_rot = mid_angle + 90  # +90 to undo the parent -90° rotation
        out += (
            f'  <g transform="rotate({-mid_angle:.6f} {CENTER} {CENTER})">\n'
            f'    <g transform="translate({CENTER} {CENTER - r_mid}) '
            f"rotate({counter_rot:.6f}) "
            f'scale({glyph_scale}) translate(-16 -16)">\n'
            f'      <use xlink:href="#{sign_id}" />\n'
            f"    </g>\n"
            f"  </g>\n"
        )

    # Border circles at the inner and outer edges of the zodiac ring
    out += (
        f'  <circle r="{R_ZODIAC_BG_INNER}" cx="{CENTER}" cy="{CENTER}" '
        f'fill="none" stroke="{COLOR_STROKE}" stroke-width="0.15"/>\n'
    )
    out += (
        f'  <circle r="{R_ZODIAC_BG_OUTER}" cx="{CENTER}" cy="{CENTER}" '
        f'fill="none" stroke="{COLOR_STROKE}" stroke-width="0.15"/>\n'
    )

    out += "</g>\n"
    return out


# =============================================================================
# RING 1: CUSP RING (zodiac signs + cusp degree data)
# =============================================================================


def _draw_cusp_ring(
    houses: list[KerykeionPointModel],
    seventh_house_degree_ut: float,
    show_zodiac_background_ring: bool = True,
) -> str:
    """
    Draw the outermost ring with zodiac sign glyphs and cusp degree/minute data.

    Each house cusp gets: [degrees°] [sign_glyph] [minutes']
    The zodiac sign glyph appears centered on the cusp line.

    Args:
        houses: List of 12 house KerykeionPointModel objects.
        seventh_house_degree_ut: 7th house cusp absolute degree.

    Returns:
        SVG group string for the cusp ring.
    """
    out = '<g kr:node="CuspRing">\n'

    out += f'<path d="{_annulus_path(R_CUSP_OUTER, R_CUSP_INNER)}" fill="{COLOR_BACKGROUND}" fill-rule="evenodd"/>\n'

    for house in houses:
        cusp_angle = _zodiac_to_wheel_angle(house.abs_pos, seventh_house_degree_ut)

        # Determine if a full zodiac sign boundary falls in this house
        # Place sign glyph at the house cusp
        sign_abbrev = house.sign
        degrees = int(house.position)
        minutes = int((house.position - degrees) * 60)

        # Cusp data text spacing around the cusp line
        text_offset = 4.669  # ~4.67° offset for degree/minute text

        # Determine layout: upper houses use one orientation, lower the alternate
        is_upper_half = cusp_angle >= 0 and cusp_angle < 180

        # Upright angle counteracts global (-90) and group (-cusp_angle)
        angle_upright = 90 + cusp_angle

        out += (
            f'  <g kr:node="Cusp" kr:absoluteposition="{house.abs_pos}" '
            f'kr:signposition="{house.position}" kr:sign="{sign_abbrev}" '
            f'kr:slug="{house.name}" '
            f'transform="rotate(-{cusp_angle:.6f} {CENTER} {CENTER})">\n'
        )

        if is_upper_half:
            # Minutes text
            out += (
                f'    <text text-anchor="middle" dominant-baseline="middle" '
                f'x="{CENTER}" y="2.75" font-size="{CUSP_FONT_SIZE}" fill="{COLOR_TEXT}" '
                f'font-weight="500" '
                f'transform="rotate({-text_offset:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright + text_offset:.6f} {CENTER} 2.75)">'
                f"{minutes}'</text>\n"
            )

            # Sign glyph
            final_scale = 0.12 * ZODIAC_OUTER_SCALE_MAP.get(sign_abbrev, 1.0)
            out += (
                f'    <g transform="translate({CENTER} 2.75) rotate({angle_upright:.6f}) scale({final_scale}) translate(-16 -16)">\n'
                f'      <use xlink:href="#{sign_abbrev}" fill="{COLOR_TEXT}" />\n'
                f"    </g>\n"
            )

            # Degrees text
            out += (
                f'    <text text-anchor="middle" dominant-baseline="middle" '
                f'x="{CENTER}" y="2.75" font-size="{CUSP_FONT_SIZE}" fill="{COLOR_TEXT}" '
                f'font-weight="500" '
                f'transform="rotate({text_offset:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright - text_offset:.6f} {CENTER} 2.75)">'
                f"{degrees}º</text>\n"
            )
        else:
            # Alternate layout for lower half (mirrored text order)
            # Minutes text
            out += (
                f'    <text text-anchor="middle" dominant-baseline="middle" '
                f'x="{CENTER}" y="2.75" font-size="{CUSP_FONT_SIZE}" fill="{COLOR_TEXT}" '
                f'font-weight="500" '
                f'transform="rotate({text_offset:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright - text_offset:.6f} {CENTER} 2.75)">'
                f"{minutes}'</text>\n"
            )

            # Sign glyph
            final_scale = 0.12 * ZODIAC_OUTER_SCALE_MAP.get(sign_abbrev, 1.0)
            out += (
                f'    <g transform="translate({CENTER} 2.75) rotate({angle_upright:.6f}) scale({final_scale}) translate(-16 -16)">\n'
                f'      <use xlink:href="#{sign_abbrev}" fill="{COLOR_TEXT}" />\n'
                f"    </g>\n"
            )

            # Degrees text
            out += (
                f'    <text text-anchor="middle" dominant-baseline="middle" '
                f'x="{CENTER}" y="2.75" font-size="{CUSP_FONT_SIZE}" fill="{COLOR_TEXT}" '
                f'font-weight="500" '
                f'transform="rotate({-text_offset:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright + text_offset:.6f} {CENTER} 2.75)">'
                f"{degrees}º</text>\n"
            )

        out += "  </g>\n"

    # Only draw signs that are NOT already represented by a house cusp.
    # Skip entirely when the outer zodiac background ring is active,
    # since all 12 signs are already visible in that ring.
    if not show_zodiac_background_ring:
        cusp_signs = {h.sign_num for h in houses}
        zodiac_abbrevs = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]

        for sign_num in range(12):
            if sign_num not in cusp_signs:
                # This sign is "intercepted" (no house starts in it). We draw its glyph
                # exactly in the middle of its 30-degree span.
                mid_sign_abs = sign_num * 30.0 + 15.0
                sign_angle = _zodiac_to_wheel_angle(mid_sign_abs, seventh_house_degree_ut)
                sign_abbrev = zodiac_abbrevs[sign_num]
                upright_angle = 90 + sign_angle
                final_scale = 0.12 * ZODIAC_OUTER_SCALE_MAP.get(sign_abbrev, 1.0)

                out += (
                    f'<g transform="rotate(-{sign_angle:.6f} {CENTER} {CENTER}) '
                    f'translate({CENTER} 2.75) rotate({upright_angle:.6f}) scale({final_scale}) translate(-16 -16)">\n'
                    f'  <use xlink:href="#{sign_abbrev}" fill="{COLOR_TEXT}"/>\n'
                    f"</g>\n"
                )

    out += "</g>\n"
    return out


# =============================================================================
# RING 2: RULER RING (graduated scale)
# =============================================================================


def _draw_ruler_ring() -> str:
    """
    Draw the graduated ruler scale ring with 3 levels of tick marks.

    Each house section gets three overlaid arc paths with different
    dash patterns representing 1°, 5°, and 10° graduations.

    Returns:
        SVG group string for the ruler ring.
    """
    out = '<g kr:node="RulerRing">\n'

    out += (
        f'<path d="{_annulus_path(R_RULER_OUTER, R_RULER_INNER)}" '
        f'fill="{COLOR_WHITE}" fill-rule="evenodd" '
        f'stroke="{COLOR_STROKE}" stroke-width="0.2"/>\n'
    )

    # Draw 3 full-circle tick layers with uniform spacing.
    # Using full circles instead of per-house arcs ensures perfectly even
    # distribution regardless of house span sizes.

    # Radii for the 3 layers (stacked from inner to outer)
    r_fine = R_RULER_INNER + 0.15  # 43.65
    r_medium = R_RULER_INNER + 0.35  # 43.85
    r_thick = R_RULER_INNER + 0.5  # 44.0

    # Fine ticks (every 1°) — 360 ticks around the full circle
    circ_fine = 2 * math.pi * r_fine
    dash_len_fine = 0.0975
    gap_fine = (circ_fine / 360) - dash_len_fine
    out += (
        f'<circle r="{r_fine}" cx="{CENTER}" cy="{CENTER}" '
        f'fill="none" stroke="{COLOR_STROKE}" '
        f'stroke-dasharray="{dash_len_fine:.4f} {gap_fine:.6f}" '
        f'stroke-width="0.3"/>\n'
    )

    # Medium ticks (every 5°) — 72 ticks around the full circle
    circ_medium = 2 * math.pi * r_medium
    dash_len_med = 0.13
    gap_med = (circ_medium / 72) - dash_len_med
    out += (
        f'<circle r="{r_medium}" cx="{CENTER}" cy="{CENTER}" '
        f'fill="none" stroke="{COLOR_STROKE}" '
        f'stroke-dasharray="{dash_len_med:.4f} {gap_med:.6f}" '
        f'stroke-width="0.7"/>\n'
    )

    # Thick ticks (every 10°) — 36 ticks around the full circle
    circ_thick = 2 * math.pi * r_thick
    dash_len_thick = 0.26
    gap_thick = (circ_thick / 36) - dash_len_thick
    out += (
        f'<circle r="{r_thick}" cx="{CENTER}" cy="{CENTER}" '
        f'fill="none" stroke="{COLOR_STROKE}" '
        f'stroke-dasharray="{dash_len_thick:.4f} {gap_thick:.6f}" '
        f'stroke-width="1"/>\n'
    )

    out += "</g>\n"
    return out


# =============================================================================
# RING 3: PLANET RING (planet data clusters + indicators)
# =============================================================================


def _resolve_planet_collisions(
    planets_with_angles: list[dict],
    min_separation: float = PLANET_MIN_SEPARATION,
) -> list[dict]:
    """
    Resolve collisions between planet clusters by spreading cramped planets.

    When planets are too close together, their display positions are spread
    apart while maintaining tether lines to their true positions.

    Args:
        planets_with_angles: List of dicts with 'angle', 'point', 'color' keys.
        min_separation: Minimum degrees to maintain between planets.

    Returns:
        Same list with added 'display_angle' key.
    """
    if not planets_with_angles:
        return planets_with_angles

    # Cap the separation so it is physically possible to fit all planets
    max_possible_separation = 320.0 / len(planets_with_angles)
    sep = min(min_separation, max_possible_separation)

    # Sort by original angle and assign initial display angles
    sorted_planets = sorted(planets_with_angles, key=lambda p: p["angle"])
    n = len(sorted_planets)
    for p in sorted_planets:
        p["display_angle"] = p["angle"]

    # ── Spreading algorithm ─────────────────────────────────────────────
    # We run multiple passes.  Each pass:
    #   1. Sort all planets by their current display_angle.
    #   2. Find the largest gap — this is where we "cut" the circle into
    #      a linear sequence so forward pushing cascades into empty space.
    #   3. Walk forward from the planet after the gap, pushing each planet
    #      that is too close to the previous one.
    for _pass in range(5):
        changed = False

        # Sort indices by current display angle
        indices = sorted(range(n), key=lambda i: sorted_planets[i]["display_angle"])

        # Find the largest gap in display order
        best_gap = -1.0
        best_gap_pos = 0
        for k in range(n):
            k_next = (k + 1) % n
            gap = _normalize_angle(
                sorted_planets[indices[k_next]]["display_angle"] - sorted_planets[indices[k]]["display_angle"]
            )
            if gap > best_gap:
                best_gap = gap
                best_gap_pos = k

        # Walk forward starting after the largest gap
        start_k = (best_gap_pos + 1) % n
        walk = [(start_k + j) % n for j in range(n)]

        for j in range(1, n):
            prev_i = indices[walk[j - 1]]
            curr_i = indices[walk[j]]
            prev_a = sorted_planets[prev_i]["display_angle"]
            curr_a = sorted_planets[curr_i]["display_angle"]
            diff = _normalize_angle(curr_a - prev_a)
            if diff < sep:
                sorted_planets[curr_i]["display_angle"] = _normalize_angle(prev_a + sep)
                changed = True

        if not changed:
            break

    return sorted_planets


def _draw_indicator_line(
    real_angle: float,
    display_angle: float,
    start_y: float = HOUSE_LINE_OUTER_Y,
    tick_length: float = 1.075,
    arc_radius: Union[float, None] = None,
) -> str:
    """
    Draw a tether/indicator line from a displaced planet to its true position.

    The indicator is a thin path from a starting position, with a small arc
    connecting to the display position if needed.

    Args:
        real_angle: True zodiacal angle of the planet.
        display_angle: Display angle after collision resolution.
        start_y: Y coordinate where the indicator line starts (default 6.5).
        tick_length: Length and direction of the initial tick. Positive = downward,
                     negative = upward (default 1.075).
        arc_radius: Radius for the connecting arc. If None, uses R_PLANET_OUTER - 1.

    Returns:
        SVG group string for the indicator line.
    """
    if arc_radius is None:
        arc_radius = R_PLANET_OUTER - 1  # 42.5

    out = f'<g kr:node="Indicator" transform="rotate(-{real_angle:.6f} {CENTER} {CENTER})">\n'

    angle_diff = _normalize_angle(display_angle - real_angle)
    if angle_diff > 180:
        angle_diff -= 360

    if abs(angle_diff) < 0.5:
        # Simple straight indicator line
        out += (
            f'  <path d="M {CENTER} {start_y} l 0 {tick_length}" '
            f'fill="transparent" stroke="{COLOR_INDICATOR}" stroke-width="0.1"/>\n'
        )
    else:
        # Line with arc to connect to displaced position
        r_arc = arc_radius
        sweep = 0 if angle_diff > 0 else 1

        # Calculate arc endpoint (angle_diff > 0 is CCW, which in SVG with Y-down is -X direction)
        end_rad = _deg_to_rad(angle_diff)
        end_x = CENTER - r_arc * math.sin(end_rad)
        end_y = CENTER - r_arc * math.cos(end_rad)

        # Slightly inward/outward endpoint (in the direction of the tick)
        tick_sign = 1.0 if tick_length >= 0 else -1.0
        end_x_inner = CENTER - (r_arc - tick_sign * abs(tick_length)) * math.sin(end_rad)
        end_y_inner = CENTER - (r_arc - tick_sign * abs(tick_length)) * math.cos(end_rad)

        out += (
            f"  <path "
            f'd="M {CENTER} {start_y} l 0 {tick_length} '
            f"A {r_arc} {r_arc} 0 0 {sweep} {end_x:.10f} {end_y:.10f} "
            f'L {end_x_inner:.10f} {end_y_inner:.10f}" '
            f'fill="transparent" stroke="{COLOR_INDICATOR}" stroke-width="0.1"/>\n'
        )

    out += "</g>\n"
    return out


def _draw_planet_ring(
    planets: list[KerykeionPointModel],
    planets_settings: list[dict],
    seventh_house_degree_ut: float,
    houses: list[KerykeionPointModel],
    min_separation: float = PLANET_MIN_SEPARATION,
    ring_inner_r: float = R_PLANET_INNER,
    ring_outer_r: float = R_PLANET_OUTER,
    ring_fill_color: str = COLOR_PLANET_RING,
    line_outer_y: float = HOUSE_LINE_OUTER_Y,
    line_inner_y: float = HOUSE_LINE_INNER_Y,
    planet_y_config: Union[dict, None] = None,
    indicator_config: Union[dict, None] = None,
    horoscope_id: Union[str, None] = None,
    scale_config: Union[dict, None] = None,
) -> str:
    """
    Draw the planet ring with data clusters and indicator lines.

    Args:
        planets: List of active planet KerykeionPointModel objects.
        planets_settings: List of planet setting dicts (with 'name', 'color', 'id').
        seventh_house_degree_ut: 7th house cusp absolute degree.
        houses: List of 12 house KerykeionPointModel objects.
        min_separation: Minimum degrees between planet clusters.
        ring_inner_r: Inner radius of the planet ring (default 22.0).
        ring_outer_r: Outer radius of the planet ring (default 43.5).
        ring_fill_color: Fill color for the ring background.
        line_outer_y: Y for house division line outer end.
        line_inner_y: Y for house division line inner end.
        planet_y_config: Dict with glyph_y, degrees_y, sign_y, minutes_y, rx_y overrides.
        indicator_config: Dict with start_y, tick_length, arc_radius overrides.
        horoscope_id: Optional kr:horoscope attribute value ("0" or "1").
        scale_config: Dict with planet_scale_base, degrees_font_size, sign_scale_base,
                      minutes_font_size, rx_font_size overrides.

    Returns:
        SVG group string for the planet ring.
    """
    horoscope_attr = f' kr:horoscope="{horoscope_id}"' if horoscope_id else ""
    out = f'<g kr:node="PlanetRing"{horoscope_attr}>\n'

    out += (
        f'<path d="{_annulus_path(ring_outer_r, ring_inner_r)}" '
        f'fill="{ring_fill_color}" fill-rule="evenodd" '
        f'stroke="{COLOR_STROKE}" stroke-width="0.25"/>\n'
    )

    # House division lines through the planet ring
    out += _draw_house_division_lines(houses, seventh_house_degree_ut, line_outer_y, line_inner_y)

    # Build planet angle data
    planets_with_angles = []
    color_map = {s["name"].lower().replace(" ", "_"): s.get("color", COLOR_TEXT) for s in planets_settings}

    for point in planets:
        angle = _zodiac_to_wheel_angle(point.abs_pos, seventh_house_degree_ut)
        name_key = point.name.lower().replace(" ", "_").replace("'", "").replace("\u2019", "")
        color = color_map.get(name_key, COLOR_TEXT)
        planets_with_angles.append(
            {
                "angle": angle,
                "point": point,
                "color": color,
            }
        )

    # Resolve collisions
    resolved = _resolve_planet_collisions(planets_with_angles, min_separation=min_separation)

    # Prepare Y-position kwargs for planet clusters
    planet_kwargs = {}
    if planet_y_config:
        planet_kwargs = {
            "glyph_y": planet_y_config.get("glyph_y", 11.0),
            "degrees_y": planet_y_config.get("degrees_y", 14.5),
            "sign_y": planet_y_config.get("sign_y", 18.0),
            "minutes_y": planet_y_config.get("minutes_y", 22.0),
            "rx_y": planet_y_config.get("rx_y", 25.0),
        }

    # Prepare scale kwargs for planet element sizes
    if scale_config:
        planet_kwargs.update(
            {
                "planet_scale_base": scale_config.get("planet_scale_base", PLANET_SCALE_BASE),
                "degrees_font_size": scale_config.get("degrees_font_size", DEGREES_FONT_SIZE),
                "sign_scale_base": scale_config.get("sign_scale_base", SIGN_SCALE_BASE),
                "minutes_font_size": scale_config.get("minutes_font_size", MINUTES_FONT_SIZE),
                "rx_font_size": scale_config.get("rx_font_size", RX_FONT_SIZE),
            }
        )

    # Prepare indicator kwargs
    ind_kwargs = {}
    if indicator_config:
        ind_kwargs = {
            "start_y": indicator_config.get("start_y", HOUSE_LINE_OUTER_Y),
            "tick_length": indicator_config.get("tick_length", 1.075),
            "arc_radius": indicator_config.get("arc_radius", None),
        }

    # Draw planet clusters and indicators
    for p in resolved:
        display_angle = p["display_angle"]
        real_angle = p["angle"]
        point = p["point"]
        color = p["color"]

        # Counter-rotation to keep text upright against both group rotations
        # The main wheel is rotated by -90, and group by -display_angle
        counter_rotation = display_angle + 90

        # Draw the data cluster
        planet_svg = _draw_single_planet_in_ring(
            point=point,
            display_angle=display_angle,
            counter_rotation=counter_rotation,
            color=color,
            **planet_kwargs,
        )
        out += planet_svg

        # Draw indicator line
        out += _draw_indicator_line(real_angle, display_angle, **ind_kwargs)

    out += "</g>\n"
    return out


def _draw_single_planet_in_ring(
    point: KerykeionPointModel,
    display_angle: float,
    counter_rotation: float,
    color: str,
    glyph_y: float = 11.0,
    degrees_y: float = 14.5,
    sign_y: float = 18.0,
    minutes_y: float = 22.0,
    rx_y: float = 25.0,
    planet_scale_base: float = PLANET_SCALE_BASE,
    degrees_font_size: float = DEGREES_FONT_SIZE,
    sign_scale_base: float = SIGN_SCALE_BASE,
    minutes_font_size: float = MINUTES_FONT_SIZE,
    rx_font_size: float = RX_FONT_SIZE,
) -> str:
    """
    Draw a single planet with its data cluster in the planet ring.

    Elements are drawn in descending size order:
      planet glyph (largest) > degrees text > zodiac sign > minutes text > RX

    Args:
        point: Planet data.
        display_angle: Display angle after collision resolution.
        counter_rotation: Counter-rotation angle for text readability.
        color: Planet color.
        glyph_y: Y position for the planet glyph.
        degrees_y: Y position for the degrees text.
        sign_y: Y position for the zodiac sign glyph.
        minutes_y: Y position for the minutes text.
        rx_y: Y position for the retrograde indicator.
        planet_scale_base: Base scale for the planet glyph (multiplied by GLYPH_SCALE_MAP).
        degrees_font_size: Font size for degrees text.
        sign_scale_base: Base scale for the zodiac sign glyph (multiplied by ZODIAC_INNER_SCALE_MAP).
        minutes_font_size: Font size for minutes text.
        rx_font_size: Font size for the retrograde indicator.

    Returns:
        SVG string for the planet group.
    """
    degrees = int(point.position)
    minutes = int((point.position - degrees) * 60)
    sign = point.sign
    is_retro = point.retrograde is True
    fill_color = COLOR_RETROGRADE if is_retro else color

    # Use point.name directly - it matches the SVG symbol IDs in the template
    # e.g. "Sun", "Moon", "Mercury", "Mean_Lilith", etc.
    planet_id = point.name

    retro_attr = ' kr:retrograde="true"' if is_retro else ""

    out = (
        f'<g kr:node="ChartPoint" kr:house="{point.house}" '
        f'kr:sign="{sign}" kr:absoluteposition="{point.abs_pos}" '
        f'kr:signposition="{point.position}" kr:slug="{planet_id}"{retro_attr} '
        f'transform="rotate(-{display_angle:.6f} {CENTER} {CENTER})">\n'
    )

    # Planet glyph (outermost, largest — near outer edge of planet ring)
    planet_scale = planet_scale_base * GLYPH_SCALE_MAP.get(planet_id, 1.0)
    out += (
        f'  <g transform="translate({CENTER} {glyph_y}) rotate({counter_rotation:.6f}) scale({planet_scale}) translate(-14 -14)">\n'
        f'    <use xlink:href="#{planet_id}" kr:slug="{planet_id}" kr:node="Glyph" fill="{fill_color}" />\n'
        f"  </g>\n"
    )

    # Degrees text
    out += (
        f'  <text text-anchor="middle" dominant-baseline="middle" '
        f'x="{CENTER}" y="{degrees_y}" font-size="{degrees_font_size}" fill="{fill_color}" '
        f'font-weight="500" '
        f'transform="rotate({counter_rotation:.6f} {CENTER} {degrees_y})">{degrees}º</text>\n'
    )

    # Sign glyph
    sign_scale = sign_scale_base * ZODIAC_INNER_SCALE_MAP.get(sign, 1.0)
    out += (
        f'  <g transform="translate({CENTER} {sign_y}) rotate({counter_rotation:.6f}) scale({sign_scale}) translate(-16 -16)">\n'
        f'    <use xlink:href="#{sign}" fill="{fill_color}" />\n'
        f"  </g>\n"
    )

    # Minutes text
    out += (
        f'  <text text-anchor="middle" dominant-baseline="middle" '
        f'x="{CENTER}" y="{minutes_y}" font-size="{minutes_font_size}" fill="{fill_color}" '
        f'font-weight="500" '
        f'transform="rotate({counter_rotation:.6f} {CENTER} {minutes_y})">{minutes}\'</text>\n'
    )

    # RX text (innermost — near inner edge of planet ring)
    if is_retro:
        out += (
            f'  <text text-anchor="middle" dominant-baseline="middle" '
            f'x="{CENTER}" y="{rx_y}" font-size="{rx_font_size}" fill="{fill_color}" '
            f'font-weight="500" '
            f'transform="rotate({counter_rotation:.6f} {CENTER} {rx_y})">RX</text>\n'
        )

    out += "</g>\n"
    return out


# =============================================================================
# HOUSE DIVISION LINES (shared between rings)
# =============================================================================


def _draw_house_division_lines(
    houses: list[KerykeionPointModel],
    seventh_house_degree_ut: float,
    line_outer_y: float = HOUSE_LINE_OUTER_Y,
    line_inner_y: float = HOUSE_LINE_INNER_Y,
) -> str:
    """
    Draw house division lines that cross the planet ring.

    Angular houses (1, 4, 7, 10) get thicker lines.

    Args:
        houses: List of 12 house KerykeionPointModel objects.
        seventh_house_degree_ut: 7th house cusp absolute degree.
        line_outer_y: Y coordinate for the outer end of lines (default 6.5).
        line_inner_y: Y coordinate for the inner end of lines (default 28.0).

    Returns:
        SVG string with house division lines.
    """
    out = ""
    for i, house in enumerate(houses):
        house_num = i + 1
        cusp_angle = _zodiac_to_wheel_angle(house.abs_pos, seventh_house_degree_ut)
        stroke_w = ANGULAR_STROKE_WIDTH if house_num in ANGULAR_HOUSES else NORMAL_STROKE_WIDTH

        out += (
            f'<line x1="{CENTER}" y1="{line_outer_y}" '
            f'x2="{CENTER}" y2="{line_inner_y}" '
            f'stroke="{COLOR_STROKE}" stroke-width="{stroke_w}" '
            f'transform="rotate(-{cusp_angle:.6f} {CENTER} {CENTER})"/>\n'
        )

    return out


# =============================================================================
# RING 4: HOUSE RING (house numbers)
# =============================================================================


def _draw_house_ring(
    houses: list[KerykeionPointModel],
    seventh_house_degree_ut: float,
    line_inner_radius: float = R_HOUSE_INNER,  # stop exactly at the aspect core boundary
    show_numbers: bool = True,
    house_inner_r: float = R_HOUSE_INNER,
    house_outer_r: float = R_HOUSE_OUTER,
    text_y: float = 29.25,
) -> str:
    """
    Draw the house numbers ring with small numbers centered in each house sector.

    Args:
        houses: List of 12 house KerykeionPointModel objects.
        seventh_house_degree_ut: 7th house cusp absolute degree.
        line_inner_radius: The inner radius where the house division lines should stop.
        show_numbers: Whether to render house number text.
        house_inner_r: Inner radius of the house ring (default 19.5).
        house_outer_r: Outer radius of the house ring (default 22.0).
        text_y: Y position for house number text (default 29.25).

    Returns:
        SVG group string for the house ring.
    """
    out = '<g kr:node="HouseRing">\n'

    out += f'<path d="{_annulus_path(house_outer_r, house_inner_r)}" fill="{COLOR_HOUSE_RING}" fill-rule="evenodd"/>\n'

    for i, house in enumerate(houses):
        house_num = i + 1
        cusp_angle = _zodiac_to_wheel_angle(house.abs_pos, seventh_house_degree_ut)
        next_house = houses[(i + 1) % 12]
        next_angle = _zodiac_to_wheel_angle(next_house.abs_pos, seventh_house_degree_ut)

        # Angular span of this house sector
        span = _normalize_angle(next_angle - cusp_angle)
        # Absolute mid-angle of the sector
        mid_angle_abs = _normalize_angle(cusp_angle + span / 2)
        stroke_w = ANGULAR_STROKE_WIDTH if house_num in ANGULAR_HOUSES else NORMAL_STROKE_WIDTH

        # Divider line from house ring outer edge down to line_inner_radius
        house_line_y1 = CENTER - house_outer_r
        house_line_y2 = CENTER - line_inner_radius

        # Divider line at house boundary
        out += (
            f'<line x1="{CENTER}" y1="{house_line_y1}" '
            f'x2="{CENTER}" y2="{house_line_y2}" '
            f'stroke="{COLOR_STROKE}" stroke-width="{stroke_w}" '
            f'transform="rotate(-{cusp_angle:.6f} {CENTER} {CENTER})"/>\n'
        )

        # House number text centered in the sector
        if show_numbers:
            # Place at the absolute mid-angle, keep text upright
            angle_upright = 90 + mid_angle_abs
            out += (
                f'<text text-anchor="middle" dominant-baseline="middle" '
                f'x="{CENTER}" y="{text_y}" font-size="1.5" fill="{COLOR_TEXT}" '
                f'font-weight="500" '
                f'transform="rotate(-{mid_angle_abs:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright:.6f} {CENTER} {text_y})">'
                f"{house_num}</text>\n"
            )

    out += "</g>\n"
    return out


# =============================================================================
# RING 5: ASPECT CORE (aspect lines with small glyphs)
# =============================================================================

# Aspect name to SVG symbol ID mapping
# The defs use "orb{degrees}" format: orb0, orb30, orb45, orb60, orb72, orb90, orb120, orb135, orb144, orb150, orb180
ASPECT_DEGREE_MAP = {
    "conjunction": 0,
    "opposition": 180,
    "square": 90,
    "trine": 120,
    "sextile": 60,
    "semi-square": 45,
    "sesquiquadrate": 135,
    "inconjunct": 150,
    "quincunx": 150,
    "semi-sextile": 30,
    "quintile": 72,
    "bi-quintile": 144,
}


def _draw_aspect_core(
    aspects_list: list[dict],
    aspects_settings: list[dict],
    seventh_house_degree_ut: float,
    core_radius: float = R_ASPECT,
) -> str:
    """
    Draw aspect lines in the central core circle with small glyphs at midpoints.

    Each aspect is rendered as a line between two planet positions, with a
    small aspect glyph placed at the midpoint of the line.

    Args:
        aspects_list: List of aspect dicts from chart data.
        aspects_settings: List of aspect setting dicts (name, color, degree).
        seventh_house_degree_ut: 7th house cusp absolute degree.
        core_radius: Radius of the aspect core circle (default R_ASPECT).

    Returns:
        SVG group string for the aspect core.
    """
    out = '<g kr:node="AspectCore">\n'

    out += f'<path d="{_annulus_path(core_radius, 0)}" fill="{COLOR_BACKGROUND}" fill-rule="evenodd"/>\n'

    # Aspect color lookup
    color_map = {}
    for s in aspects_settings:
        color_map[s["name"]] = s.get("color", COLOR_STROKE)

    # Scale factor for aspect rendering inside the core
    aspect_scale = 0.37

    # Track rendered icon positions to avoid overlapping icons of the same aspect type
    rendered_icon_positions: list[tuple[float, float, str]] = []
    icon_collision_threshold = 8.0  # minimum distance between same-type icons

    for aspect in aspects_list:
        aspect_name = aspect.get("aspect", "")
        color = color_map.get(aspect_name, COLOR_STROKE)
        if not color:
            continue

        p1_abs = aspect.get("p1_abs_pos", 0)
        p2_abs = aspect.get("p2_abs_pos", 0)

        # Convert to wheel angles
        a1 = _zodiac_to_wheel_angle(p1_abs, seventh_house_degree_ut)
        a2 = _zodiac_to_wheel_angle(p2_abs, seventh_house_degree_ut)

        # Calculate line endpoints on a unit circle scaled to aspect core
        # Points on the edge of a circle of radius ~core_radius
        x1, y1 = _point_on_circle(a1, core_radius)
        x2, y2 = _point_on_circle(a2, core_radius)

        # Scale coordinates to the aspect group's local space
        # The group is translated to center and scaled by aspect_scale
        sx1 = (x1 - CENTER) / aspect_scale + CENTER
        sy1 = (y1 - CENTER) / aspect_scale + CENTER
        sx2 = (x2 - CENTER) / aspect_scale + CENTER
        sy2 = (y2 - CENTER) / aspect_scale + CENTER

        # Midpoint for glyph placement
        mx = (sx1 + sx2) / 2
        my = (sy1 + sy2) / 2

        # Get aspect symbol id (orb{degrees} format)
        aspect_degrees = ASPECT_DEGREE_MAP.get(aspect_name, "")
        symbol_id = f"orb{aspect_degrees}" if aspect_degrees != "" else ""

        # Extract metadata for kr: attributes
        p1_name = aspect.get("p1_name", "")
        p2_name = aspect.get("p2_name", "")
        orb = aspect.get("orbit", "")
        a_degrees = aspect.get("aspect_degrees", "")
        diff = aspect.get("diff", "")
        movement = aspect.get("aspect_movement", "")

        # Aspect group with scale transform and metadata
        out += (
            f'<g kr:node="Aspect" kr:aspectname="{aspect_name}" '
            f'kr:to="{p1_name}" kr:tooriginaldegrees="{p1_abs}" '
            f'kr:from="{p2_name}" kr:fromoriginaldegrees="{p2_abs}" '
            f'kr:orb="{orb}" kr:aspectdegrees="{a_degrees}" '
            f'kr:planetsdiff="{diff}" kr:aspectmovement="{movement}" '
            f'transform="translate({CENTER} {CENTER}) scale({aspect_scale}) '
            f'translate(-{CENTER} -{CENTER})">\n'
        )

        # Aspect line (drawn first so glyphs render on top)
        out += (
            f'  <line x1="{sx1:.6f}" y1="{sy1:.6f}" '
            f'x2="{sx2:.6f}" y2="{sy2:.6f}" '
            f'stroke="{color}" stroke-width="0.25"/>\n'
        )

        # Aspect glyph at midpoint — with deduplication
        if symbol_id:
            # Check collision with previously rendered icons OF THE SAME ASPECT TYPE
            should_render_icon = True
            for ex, ey, e_degrees in rendered_icon_positions:
                if e_degrees == aspect_degrees:
                    distance = ((mx - ex) ** 2 + (my - ey) ** 2) ** 0.5
                    if distance < icon_collision_threshold:
                        should_render_icon = False
                        break

            if should_render_icon:
                out += (
                    f'  <g transform="translate({mx:.6f} {my:.6f}) rotate(90) scale(0.45) translate(-5 -5)">\n'
                    f'    <use xlink:href="#{symbol_id}" fill="{color}"/>\n'
                    f"  </g>\n"
                )
                rendered_icon_positions.append((mx, my, aspect_degrees))

        out += "</g>\n"

    out += "</g>\n"
    return out


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def draw_modern_horoscope(
    planets: list[KerykeionPointModel],
    houses: list[KerykeionPointModel],
    aspects_list: list[dict],
    seventh_house_degree_ut: float,
    planets_settings: list[dict],
    aspects_settings: list[dict],
    show_zodiac_background_ring: bool = True,
) -> str:
    """
    Generate the complete modern concentric-rings horoscope SVG content.

    This is the main entry point that orchestrates all ring drawing functions
    into a single SVG group element.

    Args:
        planets: List of active celestial point models.
        houses: List of 12 house cusp point models.
        aspects_list: List of aspect data dicts.
        seventh_house_degree_ut: Absolute degree of the 7th house cusp.
        planets_settings: Planet configuration dicts (name, color, id).
        aspects_settings: Aspect configuration dicts (name, color, degree).
        show_zodiac_background_ring: If True, draws the outer colored zodiac boundaries.

    Returns:
        Complete SVG content string for the modern horoscope.
    """
    # Orient the entire wheel so that 0° (Ascendant) is at 9 o'clock (LEFT)
    # The SVG initial orientation puts 0° at TOP. We rotate the whole group by -90°.
    out = f'<g kr:node="ModernHoroscope" transform="rotate(-90 {CENTER} {CENTER})">\n'

    # If zodiac background ring is enabled, draw the outer colored wedges first,
    # then scale the entire chart content to fit inside the inner boundary.
    if show_zodiac_background_ring:
        out += _draw_zodiac_background_ring(seventh_house_degree_ut)
        # Scale existing chart to fit inside the zodiac background ring
        s = ZODIAC_BG_SCALE
        # translate to origin, scale, translate back
        tx = CENTER * (1 - s)
        ty = CENTER * (1 - s)
        out += f'<g transform="translate({tx:.6f} {ty:.6f}) scale({s:.6f})">\n'

    # Full background circle
    out += (
        f'<circle fill="{COLOR_BACKGROUND}" r="{R_CUSP_OUTER}" cx="{CENTER}" cy="{CENTER}" '
        f'stroke="{COLOR_STROKE}" stroke-width="0.15"/>\n'
    )

    # Draw rings from outside in
    out += _draw_cusp_ring(houses, seventh_house_degree_ut, show_zodiac_background_ring)
    out += _draw_ruler_ring()
    out += _draw_planet_ring(planets, planets_settings, seventh_house_degree_ut, houses)
    out += _draw_house_ring(houses, seventh_house_degree_ut)
    out += _draw_aspect_core(aspects_list, aspects_settings, seventh_house_degree_ut)

    if show_zodiac_background_ring:
        out += "</g>\n"  # Close the scale wrapper

    out += "</g>\n"
    return out


# =============================================================================
# DUAL CHART SUPPORT
# =============================================================================


def draw_modern_dual_horoscope(
    planets_1: list[KerykeionPointModel],
    houses_1: list[KerykeionPointModel],
    planets_2: list[KerykeionPointModel],
    aspects_list: list[dict],
    seventh_house_degree_ut: float,
    planets_settings: list[dict],
    aspects_settings: list[dict],
    chart_type: str = "Transit",
    show_zodiac_background_ring: bool = True,
) -> str:
    """
    Generate a dual modern chart with two concentric planet rings.

    Uses a flat dual-ring layout for all dual chart types (Transit, Synastry,
    DualReturnChart):
      - Subject 1 (natal) → inner planet ring (r 15.5-29.5) + shared cusps/ruler/houses
      - Subject 2 (transit/synastry) → outer planet ring (r 29.5-43.5)
      - Aspects → center core (r 0-12.5)

    Args:
        planets_1: 1st subject (natal) planets.
        houses_1: 1st subject houses.
        planets_2: 2nd subject planets.
        aspects_list: Cross-chart aspect dicts.
        seventh_house_degree_ut: 7th house cusp from 1st subject.
        planets_settings: Planet config dicts.
        aspects_settings: Aspect config dicts.
        chart_type: "Transit", "Synastry", or "DualReturnChart".
        show_zodiac_background_ring: If True, draw outer zodiac wedges.

    Returns:
        Complete SVG content string for the dual horoscope.
    """
    # ── FLAT CONCENTRIC DUAL-RING LAYOUT ──────────────────────────────────
    # Both rings exist at the same coordinate level, no nested scale() transforms.

    out = f'<g kr:node="ModernDualHoroscope" kr:charttype="{chart_type}" transform="rotate(-90 {CENTER} {CENTER})">\n'

    # Optional zodiac background ring (outermost)
    if show_zodiac_background_ring:
        out += _draw_zodiac_background_ring(seventh_house_degree_ut)
        s = ZODIAC_BG_SCALE
        tx = CENTER * (1 - s)
        ty = CENTER * (1 - s)
        out += f'<g transform="translate({tx:.6f} {ty:.6f}) scale({s:.6f})">\n'

    # Background circle
    out += f'<circle fill="{COLOR_BACKGROUND}" r="{R_CUSP_OUTER}" cx="{CENTER}" cy="{CENTER}" stroke="{COLOR_STROKE}" stroke-width="0.15"/>\n'

    # ─── CUSP RING (Subject 1's houses — shared, not duplicated) ────
    out += _draw_cusp_ring(houses_1, seventh_house_degree_ut, show_zodiac_background_ring)

    # ─── RULER RING (Subject 1's houses — shared) ───────────────────
    out += _draw_ruler_ring()

    # ─── OUTER PLANET RING (Subject 2) ──────────────────────────────
    out += _draw_planet_ring(
        planets=planets_2,
        planets_settings=planets_settings,
        seventh_house_degree_ut=seventh_house_degree_ut,
        houses=houses_1,  # Subject 1's houses for divider lines
        min_separation=10.0,
        ring_inner_r=SYN_R_OUTER_PLANET_INNER,
        ring_outer_r=SYN_R_OUTER_PLANET_OUTER,
        ring_fill_color=COLOR_OUTER_PLANET_RING,
        line_outer_y=SYN_HOUSE_LINE_OUTER_Y1,
        line_inner_y=SYN_HOUSE_LINE_OUTER_Y2,
        planet_y_config={
            "glyph_y": SYN_OUTER_PLANET_GLYPH_Y,
            "degrees_y": SYN_OUTER_DEGREES_Y,
            "sign_y": SYN_OUTER_SIGN_Y,
            "minutes_y": SYN_OUTER_MINUTES_Y,
            "rx_y": SYN_OUTER_RX_Y,
        },
        indicator_config={
            "start_y": SYN_INDICATOR_START_Y,
            "tick_length": -SYN_INDICATOR_TICK,  # tick outward (toward outer edge)
            "arc_radius": SYN_INDICATOR_ARC_R_OUTWARD,  # arc just outside boundary
        },
        horoscope_id="1",
        scale_config={
            "planet_scale_base": SYN_PLANET_SCALE,
            "degrees_font_size": SYN_DEGREES_FONT_SIZE,
            "sign_scale_base": SYN_SIGN_SCALE,
            "minutes_font_size": SYN_MINUTES_FONT_SIZE,
            "rx_font_size": SYN_RX_FONT_SIZE,
        },
    )

    # ─── INNER PLANET RING (Subject 1) ──────────────────────────────
    out += _draw_planet_ring(
        planets=planets_1,
        planets_settings=planets_settings,
        seventh_house_degree_ut=seventh_house_degree_ut,
        houses=houses_1,  # Subject 1's own houses
        min_separation=10.0,
        ring_inner_r=SYN_R_INNER_PLANET_INNER,
        ring_outer_r=SYN_R_INNER_PLANET_OUTER,
        ring_fill_color=COLOR_PLANET_RING,
        line_outer_y=SYN_HOUSE_LINE_INNER_Y1,
        line_inner_y=SYN_HOUSE_LINE_INNER_Y2,
        planet_y_config={
            "glyph_y": SYN_INNER_PLANET_GLYPH_Y,
            "degrees_y": SYN_INNER_DEGREES_Y,
            "sign_y": SYN_INNER_SIGN_Y,
            "minutes_y": SYN_INNER_MINUTES_Y,
            "rx_y": SYN_INNER_RX_Y,
        },
        indicator_config={
            "start_y": SYN_INDICATOR_START_Y,
            "tick_length": SYN_INDICATOR_TICK,  # tick inward (toward center)
            "arc_radius": SYN_INDICATOR_ARC_R_INWARD,  # arc just inside boundary
        },
        horoscope_id="0",
        scale_config={
            "planet_scale_base": SYN_PLANET_SCALE_INNER,
            "degrees_font_size": SYN_DEGREES_FONT_SIZE_INNER,
            "sign_scale_base": SYN_SIGN_SCALE,
            "minutes_font_size": SYN_MINUTES_FONT_SIZE,
            "rx_font_size": SYN_RX_FONT_SIZE,
        },
    )

    # ─── HOUSE NUMBER RING (Subject 1's houses — shared) ────────────
    out += _draw_house_ring(
        houses=houses_1,
        seventh_house_degree_ut=seventh_house_degree_ut,
        line_inner_radius=SYN_R_ASPECT,
        show_numbers=True,
        house_inner_r=SYN_R_HOUSE_INNER,
        house_outer_r=SYN_R_HOUSE_OUTER,
        text_y=36.0,
    )

    # ─── ASPECT CORE (cross-chart aspects) ──────────────────────────
    out += _draw_aspect_core(aspects_list, aspects_settings, seventh_house_degree_ut, core_radius=SYN_R_ASPECT)

    if show_zodiac_background_ring:
        out += "</g>\n"  # Close zodiac bg scale wrapper

    out += "</g>\n"  # Close main group
    return out
