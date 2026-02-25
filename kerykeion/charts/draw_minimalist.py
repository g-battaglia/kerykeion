# -*- coding: utf-8 -*-
"""
Minimalist Concentric Rings Chart Drawing Module
=================================================

This module provides all drawing functions for the minimalist chart style,
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
HOUSE_LINE_OUTER_Y = 6.5   # Just inside the ruler ring outer edge
HOUSE_LINE_INNER_Y = 28.0  # At the house ring boundary

# Angular houses (1, 4, 7, 10) use thicker lines
ANGULAR_HOUSES = {1, 4, 7, 10}
ANGULAR_STROKE_WIDTH = 0.6
NORMAL_STROKE_WIDTH = 0.07

# Planet cluster positioning
PLANET_CLUSTER_Y = 9.725
PLANET_CLUSTER_SCALE = 0.13
PLANET_MIN_SEPARATION = 8.0  # Minimum degrees between planet clusters

# Transit planet band (planets-only ring inside natal house ring)
# This band sits between the natal house ring outer edge and the aspect core.
# No background, no masks, no house numbers — just planet clusters.
TRANSIT_PLANET_GLYPH_Y = 29.5       # Y for transit planet glyph
TRANSIT_DEGREES_Y = 31.5            # Y for degrees text
TRANSIT_SIGN_Y = 33.5               # Y for sign glyph
TRANSIT_MINUTES_Y = 35.5            # Y for minutes text
TRANSIT_RX_Y = 37.5                 # Y for RX text
TRANSIT_INDICATOR_OUTER_Y = 28.0    # Where transit indicator lines start (house ring inner edge)
TRANSIT_INDICATOR_INNER_Y = 29.5    # Where transit indicator lines end
TRANSIT_ASPECT_CORE_R = 12.0        # Smaller aspect core for transit charts (makes room for transit band)

# Colors — use CSS custom properties to inherit from the active theme.
# Each theme CSS file can define --kerykeion-minimalist-* overrides.
# Fallback hex values provide a clean neutral default (works when no CSS is present).
COLOR_BACKGROUND = "var(--kerykeion-chart-color-paper-1, #ffffff)"
COLOR_PLANET_RING = "var(--kerykeion-minimalist-planet-ring, #e8e8ed)"
COLOR_HOUSE_RING = "var(--kerykeion-minimalist-house-ring, #d5d5dd)"
COLOR_STROKE = "var(--kerykeion-minimalist-stroke, #b0b0bf)"
COLOR_TEXT = "var(--kerykeion-chart-color-paper-0, #333333)"
COLOR_RETROGRADE = "var(--kerykeion-minimalist-retrograde, #c43a5e)"
COLOR_INDICATOR = "var(--kerykeion-minimalist-indicator, #8a8a9e)"
COLOR_WHITE = "var(--kerykeion-chart-color-paper-1, #ffffff)"
COLOR_ZODIAC_BG_OPACITY = "var(--kerykeion-minimalist-zodiac-bg-opacity, 0.5)"

# Font
FONT_FAMILY = "Rubik, -apple-system, Segoe UI, Helvetica Neue, Arial, sans-serif"

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


def _svg_arc_path(
    cx: float,
    cy: float,
    radius: float,
    start_angle: float,
    end_angle: float,
) -> str:
    """
    Generate SVG arc path data.

    Args:
        cx, cy: Center point.
        radius: Arc radius.
        start_angle: Start angle in degrees (0° = right).
        end_angle: End angle in degrees.

    Returns:
        SVG path 'd' attribute value for the arc.
    """
    start_rad = _deg_to_rad(start_angle)
    end_rad = _deg_to_rad(end_angle)

    x1 = cx + radius * math.cos(start_rad)
    y1 = cy + radius * math.sin(start_rad)
    x2 = cx + radius * math.cos(end_rad)
    y2 = cy + radius * math.sin(end_rad)

    diff = _normalize_angle(end_angle - start_angle)
    large_arc = 1 if diff > 180 else 0

    return f"M {x1:.6f} {y1:.6f} A {radius} {radius} 0 {large_arc} 1 {x2:.6f} {y2:.6f}"


# =============================================================================
# RING MASK DEFINITIONS
# =============================================================================

def _draw_ring_masks() -> str:
    """Generate SVG mask definitions for all concentric rings."""
    masks = [
        (0, R_ASPECT),           # Aspect core
        (R_HOUSE_INNER, R_HOUSE_OUTER),  # House ring
        (R_PLANET_INNER, R_PLANET_OUTER),  # Planet ring
        (R_RULER_INNER, R_RULER_OUTER),  # Ruler ring
        (R_CUSP_INNER, R_CUSP_OUTER),   # Cusp ring
    ]
    out = ""
    for inner_r, outer_r in masks:
        out += (
            f'<mask id="ring-{inner_r}-{outer_r}">'
            f'<circle fill="white" r="{outer_r}" cx="{CENTER}" cy="{CENTER}"/>'
            f'<circle fill="black" r="{inner_r}" cx="{CENTER}" cy="{CENTER}"/>'
            f'</mask>\n'
        )
    return out


# =============================================================================
# RING 1: ZODIAC BACKGROUND WEDGE RING (Optional)
# =============================================================================

_ZODIAC_SIGN_IDS = [
    "Ari", "Tau", "Gem", "Can", "Leo", "Vir",
    "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis",
]


def _draw_zodiac_background_ring(seventh_house_degree_ut: float) -> str:
    """
    Draw the fully colored zodiac background wedges in the outermost ring,
    with zodiac sign glyphs centered in each wedge.

    These are 12 pie slices corresponding to the 12 zodiac signs,
    masked to the R_ZODIAC_BG_INNER to R_ZODIAC_BG_OUTER annulus.
    Each slice is colored using the CSS variable --kerykeion-chart-color-zodiac-bg-N.
    Each wedge also gets a zodiac sign glyph at its center.
    """
    # Mask definition for the outer ring
    out = (
        f'<mask id="ring-zodiac-bg">'
        f'<circle fill="white" r="{R_ZODIAC_BG_OUTER}" cx="{CENTER}" cy="{CENTER}"/>'
        f'<circle fill="black" r="{R_ZODIAC_BG_INNER}" cx="{CENTER}" cy="{CENTER}"/>'
        f'</mask>\n'
    )
    
    out += f'<g kr:node="ZodiacBackgrounds" mask="url(#ring-zodiac-bg)">\n'
    
    # Midpoint radius for glyph placement
    r_mid = (R_ZODIAC_BG_INNER + R_ZODIAC_BG_OUTER) / 2.0
    glyph_scale = 0.09
    
    for sign_num in range(12):
        start_abs = sign_num * 30.0
        end_abs = (sign_num + 1) * 30.0
        mid_abs = start_abs + 15.0  # Center of the 30° wedge
        
        start_angle = _zodiac_to_wheel_angle(start_abs, seventh_house_degree_ut)
        end_angle = _zodiac_to_wheel_angle(end_abs, seventh_house_degree_ut)
        mid_angle = _zodiac_to_wheel_angle(mid_abs, seventh_house_degree_ut)
        
        
        color = f"var(--kerykeion-chart-color-zodiac-bg-{sign_num})"
        
        # Draw a polygon wedge covering the 30° sector for this sign.
        # The ring mask clips it to the annulus.
        # 
        # IMPORTANT: SVG rotate() treats 0° as 12 o'clock (top), but
        # cos/sin put 0° at 3 o'clock. Subtract 90° to align the polygon
        # coordinates with the SVG rotation used by the glyphs.
        half = 15.0
        a1_rad = math.radians(-(mid_angle - half) - 90)
        a2_rad = math.radians(-(mid_angle + half) - 90)
        mid_rad = math.radians(-mid_angle - 90)
        far = R_ZODIAC_BG_OUTER * 2  # overshoot; mask clips it
        fx1 = CENTER + far * math.cos(a1_rad)
        fy1 = CENTER + far * math.sin(a1_rad)
        fx2 = CENTER + far * math.cos(a2_rad)
        fy2 = CENTER + far * math.sin(a2_rad)
        fmx = CENTER + far * math.cos(mid_rad)
        fmy = CENTER + far * math.sin(mid_rad)
        out += (
            f'  <polygon points="{CENTER},{CENTER} '
            f'{fx1:.6f},{fy1:.6f} {fmx:.6f},{fmy:.6f} '
            f'{fx2:.6f},{fy2:.6f}" '
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
            f'rotate({counter_rot:.6f}) '
            f'scale({glyph_scale}) translate(-16 -16)">\n'
            f'      <use href="#{sign_id}" />\n'
            f'    </g>\n'
            f'  </g>\n'
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

    out += '</g>\n'
    return out


# =============================================================================
# RING 1: CUSP RING (zodiac signs + cusp degree data)
# =============================================================================

def _draw_cusp_ring(
    houses: list[KerykeionPointModel],
    seventh_house_degree_ut: float,
    show_zodiac_background_ring: bool = False,
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
    out = f'<g kr:node="CuspRing">\n'

    out += (
        f'<circle r="{R_CUSP_OUTER}" cx="{CENTER}" cy="{CENTER}" '
        f'fill="{COLOR_BACKGROUND}" mask="url(#ring-{R_CUSP_INNER:g}-{R_CUSP_OUTER:g})"/>\n'
    )

    for i, house in enumerate(houses):
        house_num = i + 1
        cusp_angle = _zodiac_to_wheel_angle(house.abs_pos, seventh_house_degree_ut)
        rotation = -cusp_angle

        # Next house for computing mid-angle (for zodiac sign glyph placement)
        next_house = houses[(i + 1) % 12]
        next_angle = _zodiac_to_wheel_angle(next_house.abs_pos, seventh_house_degree_ut)

        # Determine if a full zodiac sign boundary falls in this house
        # Place sign glyph at the house cusp
        sign_abbrev = house.sign
        degrees = int(house.position)
        minutes = int((house.position - degrees) * 60)

        # Cusp data text spacing around the cusp line
        text_offset = 4.669  # ~4.67° offset for degree/minute text

        # Determine layout: upper houses use one orientation, lower the alternate
        is_upper_half = (cusp_angle >= 0 and cusp_angle < 180)

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
                f'x="{CENTER}" y="2.75" font-size="1.2" fill="{COLOR_TEXT}" '
                f'font-family="{FONT_FAMILY}" font-weight="500" '
                f'transform="rotate({-text_offset:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright + text_offset:.6f} {CENTER} 2.75)">'
                f"{minutes}'</text>\n"
            )

            # Sign glyph
            final_scale = 0.12 * ZODIAC_OUTER_SCALE_MAP.get(sign_abbrev, 1.0)
            out += (
                f'    <g transform="translate({CENTER} 2.75) rotate({angle_upright:.6f}) scale({final_scale}) translate(-16 -16)">\n'
                f'      <use href="#{sign_abbrev}" fill="{COLOR_TEXT}" />\n'
                f'    </g>\n'
            )

            # Degrees text
            out += (
                f'    <text text-anchor="middle" dominant-baseline="middle" '
                f'x="{CENTER}" y="2.75" font-size="1.5" fill="{COLOR_TEXT}" '
                f'font-family="{FONT_FAMILY}" font-weight="500" '
                f'transform="rotate({text_offset:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright - text_offset:.6f} {CENTER} 2.75)">'
                f"{degrees}º</text>\n"
            )
        else:
            # Alternate layout for lower half (mirrored text order)
            # Minutes text
            out += (
                f'    <text text-anchor="middle" dominant-baseline="middle" '
                f'x="{CENTER}" y="2.75" font-size="1.2" fill="{COLOR_TEXT}" '
                f'font-family="{FONT_FAMILY}" font-weight="500" '
                f'transform="rotate({text_offset:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright - text_offset:.6f} {CENTER} 2.75)">'
                f"{minutes}'</text>\n"
            )

            # Sign glyph
            final_scale = 0.12 * ZODIAC_OUTER_SCALE_MAP.get(sign_abbrev, 1.0)
            out += (
                f'    <g transform="translate({CENTER} 2.75) rotate({angle_upright:.6f}) scale({final_scale}) translate(-16 -16)">\n'
                f'      <use href="#{sign_abbrev}" fill="{COLOR_TEXT}" />\n'
                f'    </g>\n'
            )

            # Degrees text
            out += (
                f'    <text text-anchor="middle" dominant-baseline="middle" '
                f'x="{CENTER}" y="2.75" font-size="1.5" fill="{COLOR_TEXT}" '
                f'font-family="{FONT_FAMILY}" font-weight="500" '
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
                    f'  <use href="#{sign_abbrev}" fill="{COLOR_TEXT}"/>\n'
                    f'</g>\n'
                )

    out += '</g>\n'
    return out


# =============================================================================
# RING 2: RULER RING (graduated scale)
# =============================================================================

def _draw_ruler_ring(
    houses: list[KerykeionPointModel],
    seventh_house_degree_ut: float,
) -> str:
    """
    Draw the graduated ruler scale ring with 3 levels of tick marks.

    Each house section gets three overlaid arc paths with different
    dash patterns representing 1°, 5°, and 10° graduations.

    Args:
        houses: List of 12 house KerykeionPointModel objects.
        seventh_house_degree_ut: 7th house cusp absolute degree.

    Returns:
        SVG group string for the ruler ring.
    """
    out = f'<g kr:node="RulerRing">\n'

    out += (
        f'<circle r="{R_RULER_OUTER}" cx="{CENTER}" cy="{CENTER}" '
        f'fill="{COLOR_WHITE}" mask="url(#ring-{R_RULER_INNER:g}-{R_RULER_OUTER:g})" '
        f'stroke="{COLOR_STROKE}" stroke-width="0.2"/>\n'
    )

    # For each house, draw graduated arcs
    for i, house in enumerate(houses):
        cusp_angle = _zodiac_to_wheel_angle(house.abs_pos, seventh_house_degree_ut)
        next_house = houses[(i + 1) % 12]
        next_angle = _zodiac_to_wheel_angle(next_house.abs_pos, seventh_house_degree_ut)

        house_span = _normalize_angle(next_angle - cusp_angle)
        if house_span == 0:
            house_span = 360.0

        rotation = -cusp_angle

        # Calculate radii for the 3 arc layers
        r_fine = R_RULER_INNER + 0.15     # 43.65
        r_medium = R_RULER_INNER + 0.35   # 43.85
        r_thick = R_RULER_INNER + 0.5     # 44.0

        # SVG arc start angle: -90° rotated by house cusp
        arc_start = cusp_angle - 90
        arc_end = arc_start + house_span

        # Calculate circumference sections for dash patterns
        circ_fine = 2 * math.pi * r_fine * (house_span / 360)
        circ_medium = 2 * math.pi * r_medium * (house_span / 360)
        circ_thick = 2 * math.pi * r_thick * (house_span / 360)

        # Number of degrees in this house
        n_degrees = house_span

        # Fine ticks (every 1°)
        if n_degrees > 0:
            dash_len_fine = 0.0975
            gap_fine = (circ_fine / n_degrees) - dash_len_fine
            if gap_fine > 0:
                path_fine = _svg_arc_path(CENTER, CENTER, r_fine, arc_start, arc_end)
                out += (
                    f'<path d="{path_fine}" fill="transparent" stroke="{COLOR_STROKE}" '
                    f'stroke-dasharray="{dash_len_fine:.4f} {gap_fine:.6f}" '
                    f'stroke-width="0.3"/>\n'
                )

        # Medium ticks (every 5°)
        n_5deg = n_degrees / 5
        if n_5deg > 0:
            dash_len_med = 0.13
            gap_med = (circ_medium / n_5deg) - dash_len_med
            if gap_med > 0:
                path_med = _svg_arc_path(CENTER, CENTER, r_medium, arc_start, arc_end)
                out += (
                    f'<path d="{path_med}" fill="transparent" stroke="{COLOR_STROKE}" '
                    f'stroke-dasharray="{dash_len_med:.3f} {gap_med:.6f}" '
                    f'stroke-width="0.7"/>\n'
                )

        # Thick ticks (every 10°)
        n_10deg = n_degrees / 10
        if n_10deg > 0:
            dash_len_thick = 0.26
            gap_thick = (circ_thick / n_10deg) - dash_len_thick
            if gap_thick > 0:
                path_thick = _svg_arc_path(CENTER, CENTER, r_thick, arc_start, arc_end)
                out += (
                    f'<path d="{path_thick}" fill="transparent" stroke="{COLOR_STROKE}" '
                    f'stroke-dasharray="{dash_len_thick:.2f} {gap_thick:.6f}" '
                    f'stroke-width="1"/>\n'
                )

    out += '</g>\n'
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
        Same list with added 'display_angle' and 'needs_indicator' keys.
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
        p["needs_indicator"] = False

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
                sorted_planets[indices[k_next]]["display_angle"]
                - sorted_planets[indices[k]]["display_angle"]
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

    # Mark planets that were moved significantly from their original position
    for p in sorted_planets:
        if abs(_normalize_angle(p["display_angle"] - p["angle"])) > 0.5:
            p["needs_indicator"] = True

    return sorted_planets


def _draw_planet_cluster(
    point: KerykeionPointModel,
    display_angle: float,
    counter_rotation: float,
    color: str,
) -> str:
    """
    Draw a single planet data cluster (glyph, degrees, sign, minutes, RX).

    Layout (from top to bottom in the cluster):
        - Planet glyph (largest, scale 0.28)
        - Degrees text (scale 0.28)
        - Sign glyph (scale 0.14)
        - Minutes text (scale 0.18)
        - RX text if retrograde (scale 0.12)

    Args:
        point: KerykeionPointModel for the planet.
        display_angle: Angle at which to display the cluster.
        counter_rotation: Angle to counter-rotate text for readability.
        color: Fill color for text and glyphs.

    Returns:
        SVG group string for the planet cluster.
    """
    degrees = int(point.position)
    minutes = int((point.position - degrees) * 60)
    sign = point.sign
    name_lower = point.name.lower().replace(" ", "_").replace("'", "").replace("'", "")
    is_retro = point.retrograde is True

    out = (
        f'<g kr:node="PlanetCluster" kr:planet="{point.name}" '
        f'transform="rotate(-{display_angle:.6f} {CENTER} {CENTER}) '
        f'translate({CENTER} {PLANET_CLUSTER_Y}) scale({PLANET_CLUSTER_SCALE}) '
        f'translate(-{CENTER} -{PLANET_CLUSTER_Y}) '
        f'translate({CENTER} {PLANET_CLUSTER_Y}) translate(-{CENTER} 0)">\n'
    )

    fill_color = COLOR_RETROGRADE if is_retro else color

    # RX text (bottom, smallest) — only if retrograde
    if is_retro:
        out += (
            f'  <text text-anchor="middle" dominant-baseline="middle" '
            f'dx="{CENTER}" dy="{CENTER}" font-size="50" fill="{fill_color}" '
            f'font-family="{FONT_FAMILY}" font-weight="500" '
            f'transform="translate({CENTER} 98) scale(0.12) translate(-{CENTER} -{CENTER}) '
            f'rotate({counter_rotation:.6f} {CENTER} {CENTER})">RX</text>\n'
        )

    # Minutes text
    out += (
        f'  <text text-anchor="middle" dominant-baseline="middle" '
        f'dx="{CENTER}" dy="{CENTER}" font-size="50" fill="{fill_color}" '
        f'font-family="{FONT_FAMILY}" font-weight="500" '
        f'transform="translate({CENTER} 82) scale(0.18) translate(-{CENTER} -{CENTER}) '
        f'rotate({counter_rotation:.6f} {CENTER} {CENTER})">{minutes}\'</text>\n'
    )

    # Sign glyph
    out += (
        f'  <use href="#{sign}" '
        f'transform="translate({CENTER} 65) scale(0.14) translate(-{CENTER} -{CENTER}) '
        f'rotate({counter_rotation:.6f} {CENTER} {CENTER})"/>\n'
    )

    # Degrees text
    out += (
        f'  <text text-anchor="middle" dominant-baseline="middle" '
        f'dx="{CENTER}" dy="{CENTER}" font-size="50" fill="{fill_color}" '
        f'font-family="{FONT_FAMILY}" font-weight="500" '
        f'transform="translate({CENTER} 43) scale(0.28) translate(-{CENTER} -{CENTER}) '
        f'rotate({counter_rotation:.6f} {CENTER} {CENTER})">{degrees}º</text>\n'
    )

    # Planet glyph (top, largest)
    out += (
        f'  <use href="#{point.name}" xlink:href="#{point.name}" '
        f'transform="translate({CENTER} 14) scale(0.28) translate(-{CENTER} -{CENTER}) '
        f'rotate({counter_rotation:.6f} {CENTER} {CENTER})"/>\n'
    )

    out += '</g>\n'
    return out


def _draw_indicator_line(
    real_angle: float,
    display_angle: float,
) -> str:
    """
    Draw a tether/indicator line from a displaced planet to its true position.

    The indicator is a thin path from the outer ruler ring edge to the
    planet's true degree position, with a small arc connecting to the
    display position if needed.

    Args:
        real_angle: True zodiacal angle of the planet.
        display_angle: Display angle after collision resolution.

    Returns:
        SVG group string for the indicator line.
    """
    out = (
        f'<g kr:node="Indicator" '
        f'transform="rotate(-{real_angle:.6f} {CENTER} {CENTER}) '
        f'translate({CENTER} {CENTER}) translate(-{CENTER} -{CENTER})">\n'
    )

    angle_diff = _normalize_angle(display_angle - real_angle)
    if angle_diff > 180:
        angle_diff -= 360

    if abs(angle_diff) < 0.5:
        # Simple straight indicator line
        out += (
            f'  <path d="M {CENTER} {HOUSE_LINE_OUTER_Y} l 0 1.075" '
            f'fill="transparent" stroke="{COLOR_INDICATOR}" stroke-width="0.1"/>\n'
        )
    else:
        # Line with arc to connect to displaced position
        r_arc = R_PLANET_OUTER - 1  # 42.425
        sweep = 0 if angle_diff > 0 else 1

        # Calculate arc endpoint (angle_diff > 0 is CCW, which in SVG with Y-down is -X direction)
        end_rad = _deg_to_rad(angle_diff)
        end_x = CENTER - r_arc * math.sin(end_rad)
        end_y = CENTER - r_arc * math.cos(end_rad)

        # Slightly inward endpoint
        end_x_inner = CENTER - (r_arc - 1.075) * math.sin(end_rad)
        end_y_inner = CENTER - (r_arc - 1.075) * math.cos(end_rad)

        out += (
            f'  <path '
            f'd="M {CENTER} {HOUSE_LINE_OUTER_Y} l 0 1.075 '
            f'A {r_arc} {r_arc} 0 0 {sweep} {end_x:.10f} {end_y:.10f} '
            f'L {end_x_inner:.10f} {end_y_inner:.10f}" '
            f'fill="transparent" stroke="{COLOR_INDICATOR}" stroke-width="0.1"/>\n'
        )

    out += '</g>\n'
    return out


def _draw_planet_ring(
    planets: list[KerykeionPointModel],
    planets_settings: list[dict],
    seventh_house_degree_ut: float,
    houses: list[KerykeionPointModel],
    min_separation: float = PLANET_MIN_SEPARATION,
) -> str:
    """
    Draw the planet ring with data clusters and indicator lines.

    Args:
        planets: List of active planet KerykeionPointModel objects.
        planets_settings: List of planet setting dicts (with 'name', 'color', 'id').
        seventh_house_degree_ut: 7th house cusp absolute degree.
        houses: List of 12 house KerykeionPointModel objects.

    Returns:
        SVG group string for the planet ring.
    """
    out = f'<g kr:node="PlanetRing">\n'

    out += (
        f'<circle r="{R_PLANET_OUTER}" cx="{CENTER}" cy="{CENTER}" '
        f'fill="{COLOR_PLANET_RING}" mask="url(#ring-{R_PLANET_INNER:g}-{R_PLANET_OUTER:g})" '
        f'stroke="{COLOR_STROKE}" stroke-width="0.25"/>\n'
    )

    # House division lines through the planet ring
    out += _draw_house_division_lines(houses, seventh_house_degree_ut)

    # Build planet angle data
    planets_with_angles = []
    color_map = {s["name"].lower().replace(" ", "_"): s.get("color", COLOR_TEXT) for s in planets_settings}

    for point in planets:
        angle = _zodiac_to_wheel_angle(point.abs_pos, seventh_house_degree_ut)
        name_key = point.name.lower().replace(" ", "_").replace("'", "").replace("'", "")
        color = color_map.get(name_key, COLOR_TEXT)
        planets_with_angles.append({
            "angle": angle,
            "point": point,
            "color": color,
        })

    # Resolve collisions
    resolved = _resolve_planet_collisions(planets_with_angles, min_separation=min_separation)

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
        # We need to use the actual planet name for the glyph href
        planet_svg = _draw_single_planet_in_ring(
            point=point,
            display_angle=display_angle,
            counter_rotation=counter_rotation,
            color=color,
        )
        out += planet_svg

        # Draw indicator line
        out += _draw_indicator_line(real_angle, display_angle)

    out += '</g>\n'
    return out


def _draw_single_planet_in_ring(
    point: KerykeionPointModel,
    display_angle: float,
    counter_rotation: float,
    color: str,
) -> str:
    """
    Draw a single planet with its data cluster in the planet ring.

    Args:
        point: Planet data.
        display_angle: Display angle after collision resolution.
        counter_rotation: Counter-rotation angle for text readability.
        color: Planet color.

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
    planet_scale = 0.10 * GLYPH_SCALE_MAP.get(planet_id, 1.0)
    out += (
        f'  <g transform="translate({CENTER} 11) rotate({counter_rotation:.6f}) scale({planet_scale}) translate(-14 -14)">\n'
        f'    <use href="#{planet_id}" kr:slug="{planet_id}" kr:node="Glyph" fill="{fill_color}" />\n'
        f'  </g>\n'
    )

    # Degrees text
    out += (
        f'  <text text-anchor="middle" dominant-baseline="middle" '
        f'x="{CENTER}" y="14.5" font-size="2.2" fill="{fill_color}" '
        f'font-family="{FONT_FAMILY}" font-weight="500" '
        f'transform="rotate({counter_rotation:.6f} {CENTER} 14.5)">{degrees}º</text>\n'
    )

    # Sign glyph
    sign_scale = 0.1 * ZODIAC_INNER_SCALE_MAP.get(sign, 1.0)
    out += (
        f'  <g transform="translate({CENTER} 18) rotate({counter_rotation:.6f}) scale({sign_scale}) translate(-16 -16)">\n'
        f'    <use href="#{sign}" fill="{fill_color}" />\n'
        f'  </g>\n'
    )

    # Minutes text
    out += (
        f'  <text text-anchor="middle" dominant-baseline="middle" '
        f'x="{CENTER}" y="22" font-size="1.5" fill="{fill_color}" '
        f'font-family="{FONT_FAMILY}" font-weight="500" '
        f'transform="rotate({counter_rotation:.6f} {CENTER} 22)">{minutes}\'</text>\n'
    )

    # RX text (innermost — near inner edge of planet ring)
    if is_retro:
        out += (
            f'  <text text-anchor="middle" dominant-baseline="middle" '
            f'x="{CENTER}" y="25" font-size="1.2" fill="{fill_color}" '
            f'font-family="{FONT_FAMILY}" font-weight="500" '
            f'transform="rotate({counter_rotation:.6f} {CENTER} 25)">RX</text>\n'
        )

    out += '</g>\n'
    return out


# =============================================================================
# HOUSE DIVISION LINES (shared between rings)
# =============================================================================

def _draw_house_division_lines(
    houses: list[KerykeionPointModel],
    seventh_house_degree_ut: float,
) -> str:
    """
    Draw house division lines that cross the planet ring.

    Angular houses (1, 4, 7, 10) get thicker lines.

    Args:
        houses: List of 12 house KerykeionPointModel objects.
        seventh_house_degree_ut: 7th house cusp absolute degree.

    Returns:
        SVG string with house division lines.
    """
    out = ""
    for i, house in enumerate(houses):
        house_num = i + 1
        cusp_angle = _zodiac_to_wheel_angle(house.abs_pos, seventh_house_degree_ut)
        stroke_w = ANGULAR_STROKE_WIDTH if house_num in ANGULAR_HOUSES else NORMAL_STROKE_WIDTH

        out += (
            f'<line x1="{CENTER}" y1="{HOUSE_LINE_OUTER_Y}" '
            f'x2="{CENTER}" y2="{HOUSE_LINE_INNER_Y}" '
            f'stroke="{COLOR_STROKE}" stroke-width="{stroke_w}" '
            f'transform="rotate(-{cusp_angle:.6f} {CENTER} {CENTER}) '
            f'translate({CENTER} {CENTER}) translate(-{CENTER} -{CENTER})"/>\n'
        )

    return out


# =============================================================================
# RING 4: HOUSE RING (house numbers)
# =============================================================================

def _draw_house_ring(
    houses: list[KerykeionPointModel],
    seventh_house_degree_ut: float,
    line_inner_radius: float = R_HOUSE_INNER - 1.0,  # default extends just below the house numbers
    show_numbers: bool = True,
) -> str:
    """
    Draw the house numbers ring with small numbers centered in each house sector.

    Args:
        houses: List of 12 house KerykeionPointModel objects.
        seventh_house_degree_ut: 7th house cusp absolute degree.
        line_inner_radius: The inner radius where the house division lines should stop.

    Returns:
        SVG group string for the house ring.
    """
    out = f'<g kr:node="HouseRing">\n'

    out += (
        f'<circle r="{R_HOUSE_OUTER}" cx="{CENTER}" cy="{CENTER}" '
        f'fill="{COLOR_HOUSE_RING}" mask="url(#ring-{R_HOUSE_INNER:g}-{R_HOUSE_OUTER:g})"/>\n'
    )

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
        house_line_y1 = CENTER - R_HOUSE_OUTER  # 28
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
                f'x="{CENTER}" y="29.25" font-size="1.5" fill="{COLOR_TEXT}" '
                f'font-family="{FONT_FAMILY}" font-weight="500" '
                f'transform="rotate(-{mid_angle_abs:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright:.6f} {CENTER} 29.25)">'
                f'{house_num}</text>\n'
            )

    out += '</g>\n'
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
    out = f'<g kr:node="AspectCore">\n'

    out += (
        f'<circle r="{core_radius}" cx="{CENTER}" cy="{CENTER}" '
        f'fill="{COLOR_BACKGROUND}" mask="url(#ring-0-{core_radius:g})"/>\n'
    )

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
        r_line = core_radius / aspect_scale  # Scale to the local coordinate system

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
                    f'    <use href="#{symbol_id}" fill="{color}"/>\n'
                    f'  </g>\n'
                )
                rendered_icon_positions.append((mx, my, aspect_degrees))

        # Aspect line
        out += (
            f'  <line x1="{sx1:.6f}" y1="{sy1:.6f}" '
            f'x2="{sx2:.6f}" y2="{sy2:.6f}" '
            f'stroke="{color}" stroke-width="0.25"/>\n'
        )

        out += '</g>\n'

    out += '</g>\n'
    return out


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def draw_minimalist_horoscope(
    planets: list[KerykeionPointModel],
    houses: list[KerykeionPointModel],
    aspects_list: list[dict],
    seventh_house_degree_ut: float,
    planets_settings: list[dict],
    aspects_settings: list[dict],
    show_zodiac_background_ring: bool = False,
) -> str:
    """
    Generate the complete minimalist concentric-rings horoscope SVG content.

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
        Complete SVG content string for the minimalist horoscope.
    """
    # Orient the entire wheel so that 0° (Ascendant) is at 9 o'clock (LEFT)
    # The SVG initial orientation puts 0° at TOP. We rotate the whole group by -90°.
    out = f'<g kr:node="MinimalistHoroscope" transform="rotate(-90 {CENTER} {CENTER})">\n'

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
    out += _draw_ring_masks()
    out += (
        f'<circle fill="{COLOR_BACKGROUND}" r="{R_CUSP_OUTER}" cx="{CENTER}" cy="{CENTER}" '
        f'stroke="{COLOR_STROKE}" stroke-width="0.15"/>\n'
    )

    # Draw rings from outside in
    out += _draw_cusp_ring(houses, seventh_house_degree_ut, show_zodiac_background_ring)
    out += _draw_ruler_ring(houses, seventh_house_degree_ut)
    out += _draw_planet_ring(planets, planets_settings, seventh_house_degree_ut, houses)
    out += _draw_house_ring(houses, seventh_house_degree_ut)
    out += _draw_aspect_core(aspects_list, aspects_settings, seventh_house_degree_ut)

    if show_zodiac_background_ring:
        out += '</g>\n'  # Close the scale wrapper

    out += '</g>\n'
    return out


# =============================================================================
# TRANSIT PLANET BAND (planets-only ring for transit charts)
# =============================================================================

def _draw_single_transit_planet(
    point: KerykeionPointModel,
    display_angle: float,
    counter_rotation: float,
    color: str,
) -> str:
    """
    Draw a single transit planet cluster (glyph, degrees, sign, minutes, RX).

    Uses the TRANSIT_* Y constants for positioning inside the natal house ring.
    Slightly smaller than natal planets to visually distinguish the two layers.
    """
    degrees = int(point.position)
    minutes = int((point.position - degrees) * 60)
    sign = point.sign
    is_retro = point.retrograde is True
    fill_color = COLOR_RETROGRADE if is_retro else color
    planet_id = point.name

    retro_attr = ' kr:retrograde="true"' if is_retro else ""

    out = (
        f'<g kr:node="TransitPoint" kr:sign="{sign}" '
        f'kr:absoluteposition="{point.abs_pos}" '
        f'kr:signposition="{point.position}" kr:slug="{planet_id}"{retro_attr} '
        f'transform="rotate(-{display_angle:.6f} {CENTER} {CENTER})">\n'
    )

    # Planet glyph
    planet_scale = 0.055 * GLYPH_SCALE_MAP.get(planet_id, 1.0)
    out += (
        f'  <g transform="translate({CENTER} {TRANSIT_PLANET_GLYPH_Y}) '
        f'rotate({counter_rotation:.6f}) scale({planet_scale}) translate(-14 -14)">\n'
        f'    <use href="#{planet_id}" kr:slug="{planet_id}" kr:node="Glyph" fill="{fill_color}" />\n'
        f'  </g>\n'
    )

    # Degrees text
    out += (
        f'  <text text-anchor="middle" dominant-baseline="middle" '
        f'x="{CENTER}" y="{TRANSIT_DEGREES_Y}" font-size="1.3" fill="{fill_color}" '
        f'font-family="{FONT_FAMILY}" font-weight="500" '
        f'transform="rotate({counter_rotation:.6f} {CENTER} {TRANSIT_DEGREES_Y})">{degrees}º</text>\n'
    )

    # Sign glyph
    sign_scale = 0.055 * ZODIAC_INNER_SCALE_MAP.get(sign, 1.0)
    out += (
        f'  <g transform="translate({CENTER} {TRANSIT_SIGN_Y}) '
        f'rotate({counter_rotation:.6f}) scale({sign_scale}) translate(-16 -16)">\n'
        f'    <use href="#{sign}" fill="{fill_color}" />\n'
        f'  </g>\n'
    )

    # Minutes text
    out += (
        f'  <text text-anchor="middle" dominant-baseline="middle" '
        f'x="{CENTER}" y="{TRANSIT_MINUTES_Y}" font-size="0.9" fill="{fill_color}" '
        f'font-family="{FONT_FAMILY}" font-weight="500" '
        f'transform="rotate({counter_rotation:.6f} {CENTER} {TRANSIT_MINUTES_Y})">{minutes}\'</text>\n'
    )

    # RX text
    if is_retro:
        out += (
            f'  <text text-anchor="middle" dominant-baseline="middle" '
            f'x="{CENTER}" y="{TRANSIT_RX_Y}" font-size="0.75" fill="{fill_color}" '
            f'font-family="{FONT_FAMILY}" font-weight="500" '
            f'transform="rotate({counter_rotation:.6f} {CENTER} {TRANSIT_RX_Y})">RX</text>\n'
        )

    out += '</g>\n'
    return out


def _draw_transit_planet_band(
    planets: list[KerykeionPointModel],
    planets_settings: list[dict],
    seventh_house_degree_ut: float,
) -> str:
    """
    Draw the transit planet band — a transparent ring of planet clusters only.

    No background circle, no house division lines, no ring masks.
    Positioned inside the natal house ring, above the aspect core.
    """
    out = f'<g kr:node="TransitPlanetBand">\n'

    # Build planet angle data
    planets_with_angles = []
    color_map = {s["name"].lower().replace(" ", "_"): s.get("color", COLOR_TEXT) for s in planets_settings}

    for point in planets:
        angle = _zodiac_to_wheel_angle(point.abs_pos, seventh_house_degree_ut)
        name_key = point.name.lower().replace(" ", "_").replace("'", "").replace("\u2019", "")
        color = color_map.get(name_key, COLOR_TEXT)
        planets_with_angles.append({
            "angle": angle,
            "point": point,
            "color": color,
        })

    # Resolve collisions with a much wider separation requirement since the 
    # transit band is drawn closer to the center, so angular displacement 
    # yields less physical distance.
    resolved = _resolve_planet_collisions(planets_with_angles, min_separation=12.0)

    # Draw transit planet clusters and indicators
    for p in resolved:
        display_angle = p["display_angle"]
        real_angle = p["angle"]
        point = p["point"]
        color = p["color"]

        counter_rotation = display_angle + 90

        out += _draw_single_transit_planet(
            point=point,
            display_angle=display_angle,
            counter_rotation=counter_rotation,
            color=color,
        )

        # No indicator lines for transit chart by design

    out += '</g>\n'
    return out


# =============================================================================
# DUAL CHART SUPPORT
# =============================================================================

# Radial budget for dual charts (fractions of the total R_CUSP_OUTER radius)
# Outer subject: 50% of the space (cusp + ruler + planets + optional house ring)
# Inner subject: 50% of the space (cusp + ruler + planets + house ring + aspect core)
DUAL_OUTER_SCALE = 1.0       # outer subject draws at full size
DUAL_INNER_SCALE = 0.56      # inner subject is 56% of full size (occupies inner 56% of radius)

# The boundary between outer and inner subject rings
DUAL_BOUNDARY_R = CENTER * DUAL_INNER_SCALE  # ~28 in 100x100 viewBox


def _draw_subject_rings(
    planets: list[KerykeionPointModel],
    houses: list[KerykeionPointModel],
    seventh_house_degree_ut: float,
    planets_settings: list[dict],
    show_cusp_ring: bool = True,
    show_house_ring: bool = True,
    show_zodiac_background_ring: bool = False,
    subject_label: str = "Subject1",
) -> str:
    """
    Draw all rings for a single subject (cusp ring, ruler, planets, house ring).

    This is a helper that draws the same ring set as the single-chart function
    but without the aspect core and without the outer wrapper group.

    Args:
        planets: Active planet models for this subject.
        houses: 12 house cusp models for this subject.
        seventh_house_degree_ut: 7th house cusp absolute degree.
        planets_settings: Planet config dicts.
        show_cusp_ring: Whether to draw the cusp ring (togglable).
        show_house_ring: Whether to draw the house number ring.
        show_zodiac_background_ring: If True, skip intercepted signs in cusp ring.
        subject_label: Label for the kr:node attribute.

    Returns:
        SVG group string for this subject's rings.
    """
    out = f'<g kr:node="{subject_label}Rings">\n'

    # Ring masks (needed for this subject's rings)
    out += _draw_ring_masks()
    out += f'<circle fill="{COLOR_BACKGROUND}" r="{R_CUSP_OUTER}" cx="{CENTER}" cy="{CENTER}" stroke="{COLOR_STROKE}" stroke-width="0.15"/>\n'

    if show_cusp_ring:
        out += _draw_cusp_ring(houses, seventh_house_degree_ut, show_zodiac_background_ring)
    out += _draw_ruler_ring(houses, seventh_house_degree_ut)
    out += _draw_planet_ring(planets, planets_settings, seventh_house_degree_ut, houses)
    if show_house_ring:
        out += _draw_house_ring(houses, seventh_house_degree_ut)

    out += '</g>\n'
    return out


def draw_minimalist_dual_horoscope(
    planets_1: list[KerykeionPointModel],
    houses_1: list[KerykeionPointModel],
    planets_2: list[KerykeionPointModel],
    houses_2: list[KerykeionPointModel],
    aspects_list: list[dict],
    seventh_house_degree_ut: float,
    planets_settings: list[dict],
    aspects_settings: list[dict],
    chart_type: str = "Transit",
    show_houses_1: bool = True,
    show_houses_2: bool = True,
    show_cusp_ring_1: bool = True,
    show_cusp_ring_2: bool = True,
    show_zodiac_background_ring: bool = True,
    transit_style: bool | None = None,
) -> str:
    """
    Generate a dual minimalist chart with two concentric ring sets.

    Subject 1 (natal/inner) occupies the inner rings.
    Subject 2 (transit/synastry/outer) occupies the outer rings.
    Aspects are cross-chart only (connecting subject 1 to subject 2).

    Args:
        planets_1: 1st subject (natal) planets.
        houses_1: 1st subject houses.
        planets_2: 2nd subject planets.
        houses_2: 2nd subject houses.
        aspects_list: Cross-chart aspect dicts.
        seventh_house_degree_ut: 7th house cusp from 1st subject.
        planets_settings: Planet config dicts.
        aspects_settings: Aspect config dicts.
        chart_type: "Transit", "Synastry", or "DualReturnChart".
        show_houses_1: Show 1st subject house ring (default True).
        show_houses_2: Show 2nd subject house ring (default True, False for transit-style).
        show_cusp_ring_1: Toggle 1st subject cusp ring.
        show_cusp_ring_2: Toggle 2nd subject cusp ring.
        show_zodiac_background_ring: If True, draw outer zodiac wedges.
        transit_style: If True, draw the second chart as an inner transit planet band instead of a
                       miniaturized chart. If None, defaults to True if chart_type == "Transit".

    Returns:
        Complete SVG content string for the dual horoscope.
    """
    if transit_style is None:
        transit_style = (chart_type == "Transit")

    # For transit charts, default to hiding 2nd subject houses and inner cusp ring
    if transit_style:
        # Unless explicitly overridden, transits don't show houses for 2nd subject
        show_houses_2 = show_houses_2 if show_houses_2 is not True else False
        # Unless explicitly overridden, transits don't show cusp ring for 2nd subject
        show_cusp_ring_2 = show_cusp_ring_2 if show_cusp_ring_2 is not True else False

    # ── TRANSIT MODE ──────────────────────────────────────────────────────
    # Transit style charts use a completely different layout:
    #   - Natal (subject 1) is the full outer wheel (cusps + ruler + planets + houses)
    #   - Transit (subject 2) planets are drawn as a transparent band inside the
    #     natal house ring, with NO background, NO duplicate rings, NO scaling.
    #   - Aspects are drawn at full scale in the core.
    if transit_style:
        out = f'<g kr:node="MinimalistDualHoroscope" kr:charttype="{chart_type}" transform="rotate(-90 {CENTER} {CENTER})">\n'

        # Optional zodiac background ring (outermost)
        if show_zodiac_background_ring:
            out += _draw_zodiac_background_ring(seventh_house_degree_ut)
            s = ZODIAC_BG_SCALE
            tx = CENTER * (1 - s)
            ty = CENTER * (1 - s)
            out += f'<g transform="translate({tx:.6f} {ty:.6f}) scale({s:.6f})">\n'

        # ─── NATAL RING SET (full size) ─────────────────────────
        out += f'<g kr:node="OuterSubject">\n'
        out += f'<circle fill="{COLOR_BACKGROUND}" r="{R_CUSP_OUTER}" cx="{CENTER}" cy="{CENTER}" stroke="{COLOR_STROKE}" stroke-width="0.15"/>\n'
        out += _draw_ring_masks()
        # Extra mask for the smaller transit aspect core
        out += (
            f'<mask id="ring-0-{TRANSIT_ASPECT_CORE_R:g}">'
            f'<circle fill="white" r="{TRANSIT_ASPECT_CORE_R}" cx="{CENTER}" cy="{CENTER}"/>'
            f'</mask>\n'
        )

        if show_cusp_ring_1:
            out += _draw_cusp_ring(houses_1, seventh_house_degree_ut, show_zodiac_background_ring)
        out += _draw_ruler_ring(houses_1, seventh_house_degree_ut)
        out += _draw_planet_ring(planets_1, planets_settings, seventh_house_degree_ut, houses_1)

        if show_houses_1:
            out += _draw_house_ring(
                houses_1, 
                seventh_house_degree_ut, 
                line_inner_radius=TRANSIT_ASPECT_CORE_R, 
                show_numbers=False,
            )

        out += '</g>\n'

        # ─── TRANSIT PLANET BAND (no background, full scale) ────
        out += _draw_transit_planet_band(planets_2, planets_settings, seventh_house_degree_ut)

        # ─── ASPECT CORE (smaller, to make room for transit band) ────
        out += _draw_aspect_core(aspects_list, aspects_settings, seventh_house_degree_ut, core_radius=TRANSIT_ASPECT_CORE_R)

        if show_zodiac_background_ring:
            out += '</g>\n'  # Close zodiac bg scale wrapper

        out += '</g>\n'  # Close main group
        return out

    # ── SYNASTRY / RETURN MODE ───────────────────────────────────────────
    # For Synastry/Returns: outer is Subject 2, inner is Subject 1 (scaled)
    outer_planets = planets_2
    outer_houses = houses_2 if show_houses_2 else houses_1
    outer_show_houses = show_houses_2
    outer_show_cusps = show_cusp_ring_2

    inner_planets = planets_1
    inner_houses = houses_1
    inner_show_houses = show_houses_1
    inner_show_cusps = show_cusp_ring_1
    inner_show_bg = True
    inner_show_ruler = True

    s_inner = 0.39 if outer_show_houses else 0.44

    out = f'<g kr:node="MinimalistDualHoroscope" kr:charttype="{chart_type}" transform="rotate(-90 {CENTER} {CENTER})">\n'

    # Optional zodiac background ring (outermost)
    if show_zodiac_background_ring:
        out += _draw_zodiac_background_ring(seventh_house_degree_ut)
        s = ZODIAC_BG_SCALE
        tx = CENTER * (1 - s)
        ty = CENTER * (1 - s)
        out += f'<g transform="translate({tx:.6f} {ty:.6f}) scale({s:.6f})">\n'

    # ─── OUTER RING SET ─────────────────────────────────────
    out += f'<g kr:node="OuterSubject">\n'

    # Background circle for the outer ring area
    out += f'<circle fill="{COLOR_BACKGROUND}" r="{R_CUSP_OUTER}" cx="{CENTER}" cy="{CENTER}" stroke="{COLOR_STROKE}" stroke-width="0.15"/>\n'
    out += _draw_ring_masks()

    if outer_show_cusps:
        out += _draw_cusp_ring(outer_houses, seventh_house_degree_ut, show_zodiac_background_ring)
    out += _draw_ruler_ring(outer_houses, seventh_house_degree_ut)
    out += _draw_planet_ring(outer_planets, planets_settings, seventh_house_degree_ut, outer_houses)

    if outer_show_houses:
        out += _draw_house_ring(outer_houses, seventh_house_degree_ut)

    out += '</g>\n'

    # ─── INNER RING SET ─────────────────────────────────────
    tx_inner = CENTER * (1 - s_inner)
    ty_inner = CENTER * (1 - s_inner)
    out += f'<g kr:node="InnerSubject" transform="translate({tx_inner:.6f} {ty_inner:.6f}) scale({s_inner:.6f})">\n'

    if inner_show_bg:
        # Draw background to hide what's underneath
        out += f'<circle fill="{COLOR_BACKGROUND}" r="{R_CUSP_OUTER}" cx="{CENTER}" cy="{CENTER}" stroke="{COLOR_STROKE}" stroke-width="0.15"/>\n'

    if inner_show_cusps:
        out += _draw_cusp_ring(inner_houses, seventh_house_degree_ut, show_zodiac_background_ring)

    if inner_show_ruler:
        out += _draw_ruler_ring(inner_houses, seventh_house_degree_ut)

    out += _draw_planet_ring(
        inner_planets, 
        planets_settings, 
        seventh_house_degree_ut, 
        inner_houses, 
        min_separation=10.0
    )

    if inner_show_houses:
        out += _draw_house_ring(inner_houses, seventh_house_degree_ut)

    # Aspect core connects inner and outer
    out += _draw_aspect_core(aspects_list, aspects_settings, seventh_house_degree_ut)

    out += '</g>\n'  # Close inner subject

    if show_zodiac_background_ring:
        out += '</g>\n'  # Close zodiac bg scale wrapper

    out += '</g>\n'  # Close main group
    return out

