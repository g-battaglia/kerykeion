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

import logging
import math
from typing import Optional

from kerykeion.charts.charts_utils import escape_svg_text, normalize_degree
from kerykeion.charts.glyph_ink_metrics import (
    GLYPH_INK_HALF_HEIGHT,
    GLYPH_INK_HALF_WIDTH,
    SIGN_INK_HALF_HEIGHT,
    SIGN_INK_HALF_WIDTH,
    TEXT_INK_HALF_HEIGHT,
    TEXT_INK_HALF_WIDTH,
    TEXT_INK_REFERENCE_FONT_SIZE,
)
from kerykeion.utilities import wrap_180
from kerykeion.schemas.kr_models import KerykeionPointModel
from kerykeion.settings.chart_defaults import resolve_glyph_id

logger = logging.getLogger(__name__)


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

# Minimum degrees between planet clusters in the natal ring — with
# content-aware separations, the per-pair ceiling.
#
# Measured, not guessed — see ``scripts/measure_modern_separation.py``, which
# renders the worst cluster the renderer can be asked to draw (every glyph it
# knows, all at 29º59' and retrograde, jammed to exactly this separation, at
# several wheel orientations) and reads the real ink boxes back out of a
# browser, in the wheel's pinned font stack. Ink first touches at 6.25°; the
# degree of slack this ceiling keeps above that floor is deliberate — it is
# also what absorbs a platform whose fallback sans inks wider than the
# measured stack. Every tenth of a degree above it is a cluster fanned wider
# than it needs to be, dragging its tether line with it.
#
# The binding row is the minutes text at y=22.0 — the smallest radius carrying
# a two-character string, so the least arc per degree. The glyphs, out at
# y=11.0, clear each other well before it does.
PLANET_MIN_SEPARATION = 7.25

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

# Ink-to-ink air left between neighbouring clusters when the separation is
# derived from their actual content, in wheel units. 0.45 units is ~2.2px in a
# default 480px chart — visibly apart, not merely non-touching. Calibrated with
# scripts/measure_modern_separation.py --mode adversarial, which renders mixed
# narrow/wide clusters and measures the real rendered gaps in a browser: at
# 0.35 the worst adversarial pair still came within 0.03 units at its worst
# wheel orientation (ink tables and probes disagree by ~a pixel of antialias),
# 0.45 keeps every measured pair at a quarter unit or more of daylight.
DEFAULT_CLUSTER_CLEARANCE = 0.45

# Text of the retrograde marker, shared by the renderer and the content-aware
# separation model so the reserved width can never diverge from the drawn text.
RETROGRADE_LABEL = "RX"

# The one font stack every modern-chart text renders in — declared on the
# wheel root here, and on the full-chart Main_Chart group by chart_drawer, so
# no text node can miss it. Without it the SVG inherits whatever the embedding
# page uses — the same chart came out serif standalone, sans in one host page,
# monospace in another — and no spacing model can reserve room for an unknown
# font. Arial, Helvetica and Liberation Sans are metric-compatible, and
# Liberation is named explicitly so Linux systems that have it never fall
# through to generic sans-serif (usually DejaVu Sans, whose digits run
# ~10-14% wider than the measured ink tables). A system with none of the
# three still resolves to its own sans and can render wider than reserved —
# that residual risk is the price of not padding every chart for the rarest
# platform.
#
# Liberation Sans is deliberately unquoted: CSS allows multi-word family
# names as bare identifiers, and the SVG post-processing rewrites double
# quotes to single quotes, which nested quotes would corrupt.
MODERN_TEXT_FONT_FAMILY = "Arial, Helvetica, Liberation Sans, sans-serif"

# Below this display offset from the true position, the indicator is drawn as
# a straight tick instead of a tether arc. Shared with the displacement report
# so its "straight" column counts the same population the renderer draws.
STRAIGHT_TETHER_THRESHOLD = 0.5

# Natal cluster row positions (Y in the wheel-local frame; radius = CENTER - y).
# The single source for the renderer, the content-aware profiles, and the row
# radii — the dual rings have their own SYN_* equivalents below.
NATAL_PLANET_GLYPH_Y = 11.0
NATAL_DEGREES_Y = 14.5
NATAL_SIGN_Y = 18.0
NATAL_MINUTES_Y = 22.0
NATAL_RX_Y = 25.0

# Minimum degrees between planet clusters in each dual ring, measured the same
# way as PLANET_MIN_SEPARATION (and, like it, the per-pair ceiling once
# content-aware separations kick in). The two rings differ by more than a
# rounding: the outer one carries its clusters at radii 41.0–31.5 and the
# inner one at 27.5–18.5, and arc length per degree falls with the radius, so
# the inner ring needs half again as much angle to buy the same gap. Ink first
# touches at 5.00° (outer) and 6.25° (inner); the slack these ceilings keep
# above the floors doubles as headroom for wider-inking fallback fonts.
#
# The binding row is the degrees text in both rings — unlike the natal ring,
# whose minutes row sits at a tighter radius than its degrees row.
SYN_OUTER_MIN_SEPARATION = 5.75
SYN_INNER_MIN_SEPARATION = 7.5

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

# Default scale factor for all zodiac sign glyphs
_ZODIAC_DEFAULT_SCALE = 0.9

# Zodiac sign abbreviations (ordered from Aries to Pisces)
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

# Zodiac signs in the outer cusp ring (paths are ~32x32)
ZODIAC_OUTER_SCALE_MAP = {sign: _ZODIAC_DEFAULT_SCALE for sign in _ZODIAC_SIGN_IDS}

# Zodiac signs in the inner planet ring (smaller base size)
ZODIAC_INNER_SCALE_MAP = {sign: _ZODIAC_DEFAULT_SCALE for sign in _ZODIAC_SIGN_IDS}


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


# Shared canonical implementation (see charts_utils.normalize_degree).
_normalize_angle = normalize_degree


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
        sign_id = _ZODIAC_SIGN_IDS[sign_num]
        out += f'  <g kr:node="ZodiacSign" kr:sign="{sign_id}" kr:signnumber="{sign_num}">\n'
        out += (
            f'  <path d="'
            f"M {ox1:.6f},{oy1:.6f} "
            f"A {R_ZODIAC_BG_OUTER},{R_ZODIAC_BG_OUTER} 0 0,0 {ox2:.6f},{oy2:.6f} "
            f"L {ix1:.6f},{iy1:.6f} "
            f"A {R_ZODIAC_BG_INNER},{R_ZODIAC_BG_INNER} 0 0,1 {ix2:.6f},{iy2:.6f} "
            f'Z" '
            f'fill="{color}" style="fill-opacity: {COLOR_ZODIAC_BG_OPACITY}" />\n'
        )

        # Highlight overlay — a full pie slice from chart center to the outer
        # zodiac boundary, invisible by default. Frontends can make it visible
        # via CSS (e.g. .chart-focused > [kr:highlight='sign-full']) to give
        # the modern ZodiacSign the same visual impact as the classic wedge
        # when a sign is focused. `pointer-events: none` so it never steals
        # clicks from the planet ring / aspect core sitting above it.
        cx1 = CENTER + R_ZODIAC_BG_OUTER * math.cos(a_start_rad)
        cy1 = CENTER + R_ZODIAC_BG_OUTER * math.sin(a_start_rad)
        cx2 = CENTER + R_ZODIAC_BG_OUTER * math.cos(a_end_rad)
        cy2 = CENTER + R_ZODIAC_BG_OUTER * math.sin(a_end_rad)
        out += (
            f'  <path kr:highlight="sign-full" d="'
            f"M {CENTER},{CENTER} "
            f"L {cx1:.6f},{cy1:.6f} "
            f"A {R_ZODIAC_BG_OUTER},{R_ZODIAC_BG_OUTER} 0 0,0 {cx2:.6f},{cy2:.6f} "
            f'Z" '
            f'fill="{color}" fill-opacity="0" pointer-events="none" />\n'
        )

        # Draw the zodiac glyph centered in the wedge
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
        out += "  </g>\n"  # close ZodiacSign group

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
    horoscope_id: Optional[str] = None,
) -> str:
    """
    Draw the outermost ring with zodiac sign glyphs and cusp degree/minute data.

    Each house cusp gets: [degrees°] [sign_glyph] [minutes']
    The zodiac sign glyph appears centered on the cusp line.

    Args:
        houses: List of 12 house KerykeionPointModel objects.
        seventh_house_degree_ut: 7th house cusp absolute degree.
        horoscope_id: Owner subject id emitted as kr:horoscope on each Cusp
            ("0" = first subject, "1" = second), matching the classic engine.

    Returns:
        SVG group string for the cusp ring.
    """
    horoscope_attr = f' kr:horoscope="{horoscope_id}"' if horoscope_id is not None else ""
    parts: list[str] = ['<g kr:node="CuspRing">\n']

    parts.append(
        f'<path d="{_annulus_path(R_CUSP_OUTER, R_CUSP_INNER)}" fill="{COLOR_BACKGROUND}" fill-rule="evenodd"/>\n'
    )

    for house in houses:
        cusp_angle = _zodiac_to_wheel_angle(house.abs_pos, seventh_house_degree_ut)

        # Determine if a full zodiac sign boundary falls in this house
        # Place sign glyph at the house cusp
        # (typed str: the intercepted-signs pass below reuses the variable with
        # plain-str ids from _ZODIAC_SIGN_IDS)
        sign_abbrev: str = house.sign
        degrees = int(house.position)
        minutes = int((house.position - degrees) * 60)

        # Cusp data text spacing around the cusp line
        text_offset = 4.669  # ~4.67° offset for degree/minute text

        # Determine layout: upper houses use one orientation, lower the alternate
        is_upper_half = cusp_angle >= 0 and cusp_angle < 180

        # Upright angle counteracts global (-90) and group (-cusp_angle)
        angle_upright = 90 + cusp_angle

        parts.append(
            f'  <g kr:node="Cusp" kr:absoluteposition="{house.abs_pos}" '
            f'kr:signposition="{house.position}" kr:sign="{sign_abbrev}" '
            f'kr:slug="{escape_svg_text(house.name)}"{horoscope_attr} '
            f'transform="rotate(-{cusp_angle:.6f} {CENTER} {CENTER})">\n'
        )

        if is_upper_half:
            # Minutes text
            parts.append(
                f'    <text text-anchor="middle" dominant-baseline="middle" '
                f'x="{CENTER}" y="2.75" font-size="{CUSP_FONT_SIZE}" fill="{COLOR_TEXT}" '
                f'font-weight="500" '
                f'transform="rotate({-text_offset:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright + text_offset:.6f} {CENTER} 2.75)">'
                f"{minutes}'</text>\n"
            )

            # Sign glyph
            final_scale = 0.12 * ZODIAC_OUTER_SCALE_MAP.get(sign_abbrev, 1.0)
            parts.append(
                f'    <g transform="translate({CENTER} 2.75) rotate({angle_upright:.6f}) scale({final_scale}) translate(-16 -16)">\n'
                f'      <use xlink:href="#{sign_abbrev}" fill="{COLOR_TEXT}" />\n'
                f"    </g>\n"
            )

            # Degrees text
            parts.append(
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
            parts.append(
                f'    <text text-anchor="middle" dominant-baseline="middle" '
                f'x="{CENTER}" y="2.75" font-size="{CUSP_FONT_SIZE}" fill="{COLOR_TEXT}" '
                f'font-weight="500" '
                f'transform="rotate({text_offset:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright - text_offset:.6f} {CENTER} 2.75)">'
                f"{minutes}'</text>\n"
            )

            # Sign glyph
            final_scale = 0.12 * ZODIAC_OUTER_SCALE_MAP.get(sign_abbrev, 1.0)
            parts.append(
                f'    <g transform="translate({CENTER} 2.75) rotate({angle_upright:.6f}) scale({final_scale}) translate(-16 -16)">\n'
                f'      <use xlink:href="#{sign_abbrev}" fill="{COLOR_TEXT}" />\n'
                f"    </g>\n"
            )

            # Degrees text
            parts.append(
                f'    <text text-anchor="middle" dominant-baseline="middle" '
                f'x="{CENTER}" y="2.75" font-size="{CUSP_FONT_SIZE}" fill="{COLOR_TEXT}" '
                f'font-weight="500" '
                f'transform="rotate({-text_offset:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright + text_offset:.6f} {CENTER} 2.75)">'
                f"{degrees}º</text>\n"
            )

        parts.append("  </g>\n")

    # Only draw signs that are NOT already represented by a house cusp.
    # Skip entirely when the outer zodiac background ring is active,
    # since all 12 signs are already visible in that ring.
    if not show_zodiac_background_ring:
        cusp_signs = {h.sign_num for h in houses}

        for sign_num in range(12):
            if sign_num not in cusp_signs:
                # This sign is "intercepted" (no house starts in it). We draw its glyph
                # exactly in the middle of its 30-degree span.
                mid_sign_abs = sign_num * 30.0 + 15.0
                sign_angle = _zodiac_to_wheel_angle(mid_sign_abs, seventh_house_degree_ut)
                sign_abbrev = _ZODIAC_SIGN_IDS[sign_num]
                upright_angle = 90 + sign_angle
                final_scale = 0.12 * ZODIAC_OUTER_SCALE_MAP.get(sign_abbrev, 1.0)

                parts.append(
                    f'<g transform="rotate(-{sign_angle:.6f} {CENTER} {CENTER}) '
                    f'translate({CENTER} 2.75) rotate({upright_angle:.6f}) scale({final_scale}) translate(-16 -16)">\n'
                    f'  <use xlink:href="#{sign_abbrev}" fill="{COLOR_TEXT}"/>\n'
                    f"</g>\n"
                )

    parts.append("</g>\n")
    return "".join(parts)


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


#: Total degrees the resolver may spend on separations around the full circle.
#: The 40° of slack keeps the wrap gap comfortably open even at maximum load;
#: with a uniform separation this reproduces the historical `min(sep, 320/n)`
#: cap exactly (scaling sep by 320/(n*sep) IS capping it at 320/n).
FEASIBLE_TOTAL_DEGREES = 320.0

#: Stand-in ink reach for a glyph, sign, or string the measured tables do not
#: know (a future symbol or text added without re-running the dump). The widest
#: measured entry cannot under-reserve for anything.
_FALLBACK_GLYPH_INK = (max(GLYPH_INK_HALF_WIDTH.values()), max(GLYPH_INK_HALF_HEIGHT.values()))
_FALLBACK_SIGN_INK = (max(SIGN_INK_HALF_WIDTH.values()), max(SIGN_INK_HALF_HEIGHT.values()))
_FALLBACK_TEXT_INK = (max(TEXT_INK_HALF_WIDTH.values()), max(TEXT_INK_HALF_HEIGHT.values()))


def _format_degrees_text(point: KerykeionPointModel) -> str:
    """The degrees line of a planet cluster, e.g. ``"23º"``."""
    return f"{int(point.position)}º"


def _format_minutes_text(point: KerykeionPointModel) -> str:
    """The minutes line of a planet cluster, e.g. ``"49'"``."""
    minutes = int((point.position - int(point.position)) * 60)
    return f"{minutes}'"


def _text_ink_reach(text: str, font_size: float) -> tuple[float, float]:
    """Measured ink reach of a text row's string, scaled to *font_size*."""
    scale = font_size / TEXT_INK_REFERENCE_FONT_SIZE
    half_width, half_height = (
        (TEXT_INK_HALF_WIDTH[text], TEXT_INK_HALF_HEIGHT[text])
        if text in TEXT_INK_HALF_WIDTH
        else _FALLBACK_TEXT_INK
    )
    return (half_width * scale, half_height * scale)


def _cluster_row_profile(
    point: KerykeionPointModel,
    planet_scale_base: float = PLANET_SCALE_BASE,
    degrees_font_size: float = DEGREES_FONT_SIZE,
    sign_scale_base: float = SIGN_SCALE_BASE,
    minutes_font_size: float = MINUTES_FONT_SIZE,
    rx_font_size: float = RX_FONT_SIZE,
) -> dict[str, tuple[float, float]]:
    """Ink reach ``(half_width, half_height)`` of each cluster row of *point*.

    This is what the content-aware separation works from: a planet at 4º07'
    reserves the ink of ``"4º"`` and ``"7'"``, not of the widest strings the
    rows could ever hold, and the ``rx`` row exists only when the point is
    actually retrograde. All values come from the browser-measured tables in
    :mod:`kerykeion.charts.glyph_ink_metrics`, in wheel units.

    Both axes matter: clusters stay upright while the wheel turns, so which
    axis two neighbours pinch on depends on where the pair sits (see
    ``required_separation`` in :func:`_resolve_planet_collisions`).

    The keyword defaults mirror the natal ring; dual rings pass their own
    scales, the same ones they hand to :func:`_draw_single_planet_in_ring`.
    """
    point_slug = point.name
    planet_id = point_slug if point.point_type == "House" else resolve_glyph_id(point_slug)
    glyph_scale = planet_scale_base * GLYPH_SCALE_MAP.get(planet_id, 1.0)
    glyph_half_width, glyph_half_height = (
        (GLYPH_INK_HALF_WIDTH[planet_id], GLYPH_INK_HALF_HEIGHT[planet_id])
        if planet_id in GLYPH_INK_HALF_WIDTH
        else _FALLBACK_GLYPH_INK
    )

    sign_scale = sign_scale_base * ZODIAC_INNER_SCALE_MAP.get(point.sign, 1.0)
    sign_half_width, sign_half_height = (
        (SIGN_INK_HALF_WIDTH[point.sign], SIGN_INK_HALF_HEIGHT[point.sign])
        if point.sign in SIGN_INK_HALF_WIDTH
        else _FALLBACK_SIGN_INK
    )

    profile = {
        "glyph": (glyph_half_width * glyph_scale, glyph_half_height * glyph_scale),
        "degrees": _text_ink_reach(_format_degrees_text(point), degrees_font_size),
        "sign": (sign_half_width * sign_scale, sign_half_height * sign_scale),
        "minutes": _text_ink_reach(_format_minutes_text(point), minutes_font_size),
    }
    if point.retrograde is True:
        profile["rx"] = _text_ink_reach(RETROGRADE_LABEL, rx_font_size)
    return profile

#: Fixed iteration count for the wraparound fallback's 1-D convex search.
#: Deterministic and precise far beyond the 1e-6 the placement needs.
_WRAP_SEARCH_ITERATIONS = 200

#: Bound on orientation-refinement rounds: a pair's separation depends on
#: where it sits on the wheel, which depends on the separations. Requirements
#: only ratchet upward and are capped, so the refinement converges; wide
#: clusters that fan across a quadrant genuinely need several rounds before
#: the orientations stop moving. The bound exists for pathology, not pacing —
#: exiting through it (instead of through convergence) is the failure mode.
_ORIENTATION_REFINEMENT_ROUNDS = 32


def _isotonic_non_decreasing(values: list[float]) -> list[tuple[float, int]]:
    """L2 isotonic regression of *values*, as PAVA merge blocks.

    Returns ``(block_mean, block_size)`` blocks whose expansion is the
    non-decreasing vector closest to *values* in least squares. Classic
    stack-based Pool Adjacent Violators: each new element opens a block, and
    while the previous block's mean exceeds the current one's, the two violate
    monotonicity and are pooled (their best common value is their joint mean).
    """
    blocks: list[tuple[float, int]] = []
    for value in values:
        merged_sum = value
        merged_size = 1
        while blocks and blocks[-1][0] > merged_sum / merged_size:
            previous_mean, previous_size = blocks.pop()
            merged_sum += previous_mean * previous_size
            merged_size += previous_size
        blocks.append((merged_sum / merged_size, merged_size))
    return blocks


def _pair_required_separation(
    first_profile: dict[str, tuple[float, float]],
    second_profile: dict[str, tuple[float, float]],
    pair_mid_angle: float,
    *,
    row_radii: dict[str, float],
    clearance: float,
    ceiling: float,
) -> float:
    """Degrees a specific pair needs, where it actually sits, so no ink touches.

    Clusters stay upright while the wheel turns, so two neighbours are two
    axis-aligned boxes, and which axis separates them depends on where the
    pair sits: near the top of the wheel neighbours sit side by side and the
    ink WIDTHS must clear; at the sides they stack vertically and the ink
    HEIGHTS must clear — a much smaller ask for text rows. A pair's screen
    offset per degree of separation is ``arc·|sin(mid)|`` horizontally and
    ``arc·|cos(mid)|`` vertically, and clearing either axis suffices, so each
    row takes the cheaper one. At the diagonal both components shrink and this
    degrades exactly to the all-orientation worst case,
    ``hypot(widths, heights)``.

    Args:
        first_profile: Row ink reaches of one cluster (:func:`_cluster_row_profile`).
        second_profile: Row ink reaches of its neighbour.
        pair_mid_angle: Wheel angle midway between the two display positions.
        row_radii: Radius of each cluster row, keyed like the profiles.
        clearance: Ink-to-ink air to keep, wheel units.
        ceiling: Hard cap, degrees — the measured always-safe separation.

    Returns:
        Degrees of separation this pair requires, at most *ceiling*.
    """
    horizontal_share = abs(math.sin(math.radians(pair_mid_angle)))
    vertical_share = abs(math.cos(math.radians(pair_mid_angle)))
    required = 0.0
    for row, radius in row_radii.items():
        if row not in first_profile or row not in second_profile:
            continue  # e.g. the rx row, present only for retrograde points
        width_needed = first_profile[row][0] + second_profile[row][0] + clearance
        height_needed = first_profile[row][1] + second_profile[row][1] + clearance
        arc_per_degree = radius * math.pi / 180.0
        separating_options = []
        if horizontal_share > 1e-9:
            separating_options.append(width_needed / (arc_per_degree * horizontal_share))
        if vertical_share > 1e-9:
            separating_options.append(height_needed / (arc_per_degree * vertical_share))
        required = max(required, min(separating_options))
    return min(ceiling, required)


def _resolve_planet_collisions(
    planets_with_angles: list[dict],
    min_separation: float = PLANET_MIN_SEPARATION,
    *,
    row_radii: Optional[dict[str, float]] = None,
    clearance: float = DEFAULT_CLUSTER_CLEARANCE,
) -> list[dict]:
    """
    Resolve collisions between planet clusters by spreading cramped planets.

    When planets are too close together, their display positions are spread
    apart while maintaining tether lines to their true positions. Each planet
    lands as close to its true position as the separations allow: cramped
    runs are centered on their true positions and spread both ways, never
    smeared forward.

    How much separation a pair needs depends on what the two clusters draw.
    When *row_radii* is given and both entries carry a ``"row_half_widths"``
    profile (see :func:`_cluster_row_profile`), each adjacent pair reserves
    just enough arc for its own ink plus *clearance* — capped at
    *min_separation*, which the measurement harness proved sufficient for the
    widest content possible. Entries without profiles, or a ``None``
    *row_radii*, fall back to the uniform *min_separation* everywhere.

    Args:
        planets_with_angles: List of dicts with 'angle', 'point', 'color' keys,
            optionally carrying 'row_half_widths'.
        min_separation: Degrees to maintain between planets; the ceiling for
            content-derived separations.
        row_radii: Radius of each cluster row (key matching the profiles),
            enabling content-aware separations.
        clearance: Ink-to-ink air added between neighbouring clusters, wheel
            units. Only used with content-aware separations.

    Returns:
        Same list with added 'display_angle' key.
    """
    if not planets_with_angles:
        return planets_with_angles

    def required_separation(first: dict, second: dict, pair_mid_angle: float) -> float:
        """This pair's separation: content-derived when both carry profiles."""
        first_profile = first.get("row_half_widths")
        second_profile = second.get("row_half_widths")
        if row_radii is None or first_profile is None or second_profile is None:
            return min_separation
        return _pair_required_separation(
            first_profile,
            second_profile,
            pair_mid_angle,
            row_radii=row_radii,
            clearance=clearance,
            ceiling=min_separation,
        )

    # Sort by true zodiacal angle. This order is the invariant we must preserve.
    sorted_planets = sorted(planets_with_angles, key=lambda p: p["angle"])
    n = len(sorted_planets)

    if n == 1:
        sorted_planets[0]["display_angle"] = sorted_planets[0]["angle"]
        return sorted_planets

    # ── Placement algorithm ─────────────────────────────────────────────
    # We work in an "unwrapped" linear coordinate along the circle. The
    # largest gap in the ORIGINAL (true) angles is where we cut the circle:
    # starting from the planet right after that cut, every other planet has
    # a non-decreasing forward zodiacal distance from it.
    #
    # The placement itself is a least-squares isotonic regression. With
    # cumulative separations S_j, requiring d_j - d_{j-1} >= sep_j is the
    # same as requiring y_j = d_j - S_j to be non-decreasing, so the
    # displacement-optimal layout is d = PAVA(x - S) + S: every cramped run
    # is drawn centered on the true positions of its members (sum of
    # displacements zero), sparse planets stay exactly where they are, and
    # zodiacal order is preserved because consecutive d differ by at least
    # sep_j > 0. The old forward-walk kept the first planet of a run fixed
    # and pushed everyone else forward — on a 52-point wheel the worst
    # planet ended up 30-43 degrees from its true position; centering
    # roughly halves that.
    best_gap = -1.0
    best_gap_pos = 0
    for k in range(n):
        k_next = (k + 1) % n
        gap = _normalize_angle(sorted_planets[k_next]["angle"] - sorted_planets[k]["angle"])
        if gap > best_gap:
            best_gap = gap
            best_gap_pos = k

    start_k = (best_gap_pos + 1) % n
    base_angle = sorted_planets[start_k]["angle"]

    # The same planets, walked forward from the cut, with their true positions
    # unwrapped onto a line.
    ordered = [sorted_planets[(start_k + j) % n] for j in range(n)]
    unwrapped_positions = [base_angle] + [
        base_angle + _normalize_angle(planet["angle"] - base_angle) for planet in ordered[1:]
    ]

    def place(pair_separations: list[float], wrap_separation: float) -> list[float]:
        """Displacement-optimal display positions for the given separations."""
        # Scale everything down together when the circle cannot hold it all.
        total_separation = sum(pair_separations) + wrap_separation
        if total_separation > FEASIBLE_TOTAL_DEGREES:
            feasibility_scale = FEASIBLE_TOTAL_DEGREES / total_separation
            pair_separations = [s * feasibility_scale for s in pair_separations]
            wrap_separation *= feasibility_scale

        reserved_before = [0.0]
        for separation in pair_separations:
            reserved_before.append(reserved_before[-1] + separation)

        # "Deflate" the mandatory separations out of the coordinates: requiring
        # display_j - display_{j-1} >= sep_j is the same as requiring the
        # deflated values to be non-decreasing, which is what PAVA solves.
        deflated_positions = [
            position - reserved for position, reserved in zip(unwrapped_positions, reserved_before)
        ]
        blocks = _isotonic_non_decreasing(deflated_positions)
        fitted_deflated = [block_mean for block_mean, block_size in blocks for _ in range(block_size)]

        # Wraparound guard: the optimum may stretch past the cut on either
        # side. The pair facing itself across the cut needs
        # 360 - (display_last - display_first) >= wrap_separation, i.e. the
        # fitted deflated vector must fit in a window of a fixed width. The
        # constrained optimum is the unconstrained one clipped into the
        # best-placed window (clipping preserves both monotonicity and the
        # pairwise gaps), and the window placement minimizes a sum of
        # per-element quadratics — convex as a SUM, though no single term is,
        # so resist the temptation to solve it per element. The window is at
        # least 40 degrees wide, because the feasibility cap keeps the total
        # separation at or under 320.
        window_width = (360.0 - wrap_separation) - reserved_before[-1]
        if fitted_deflated[-1] - fitted_deflated[0] > window_width:

            def cost_of_window(window_start: float) -> float:
                window_end = window_start + window_width
                return sum(
                    (min(max(fitted, window_start), window_end) - deflated) ** 2
                    for fitted, deflated in zip(fitted_deflated, deflated_positions)
                )

            search_low = min(deflated_positions) - window_width
            search_high = max(deflated_positions)
            for _ in range(_WRAP_SEARCH_ITERATIONS):
                step = (search_high - search_low) / 3.0
                if cost_of_window(search_low + step) <= cost_of_window(search_high - step):
                    search_high -= step
                else:
                    search_low += step
            best_window_start = (search_low + search_high) / 2.0
            best_window_end = best_window_start + window_width
            fitted_deflated = [
                min(max(fitted, best_window_start), best_window_end) for fitted in fitted_deflated
            ]

        # Back to angles. Blocks of one are planets nobody crowded: give them
        # their true angle verbatim rather than a value reconstructed through
        # the deflate/reinflate float round-trip. A final forward clamp
        # absorbs the few ulps of noise the block means can carry.
        display_positions = [
            fitted + reserved for fitted, reserved in zip(fitted_deflated, reserved_before)
        ]
        block_start = 0
        for block_mean, block_size in blocks:
            untouched_by_window_clip = fitted_deflated[block_start] == block_mean
            if block_size == 1 and untouched_by_window_clip:
                display_positions[block_start] = unwrapped_positions[block_start]
            block_start += block_size
        for j in range(1, n):
            minimum_allowed = display_positions[j - 1] + pair_separations[j - 1]
            if display_positions[j] < minimum_allowed:
                display_positions[j] = minimum_allowed
        return display_positions

    def pair_mid_angles(positions: list[float]) -> list[float]:
        """Midpoint angle of each adjacent pair (wrap pair last)."""
        adjacent = [(a + b) / 2.0 for a, b in zip(positions, positions[1:])]
        wrap_mid = positions[-1] + _normalize_angle(positions[0] - positions[-1]) / 2.0
        return adjacent + [wrap_mid]

    # A pair's requirement depends on where it sits, but where it sits depends
    # on the requirements: a spreading cluster rotates every pair it contains.
    # Solve the fixed point by refinement — place, re-evaluate at the placed
    # positions, repeat — with a ratchet (requirements only grow, capped at
    # min_separation) so the loop provably converges. The exit is
    # verification-shaped on purpose: a placement is only accepted after a
    # re-evaluation at its own orientations demanded nothing new, so no
    # unvalidated layout can escape the loop.
    mid_angles = pair_mid_angles(unwrapped_positions)
    pair_requirements = [
        required_separation(planet, follower, mid)
        for (planet, follower), mid in zip(zip(ordered, ordered[1:]), mid_angles)
    ]
    wrap_requirement = required_separation(ordered[-1], ordered[0], mid_angles[-1])
    requirements_settled = False
    for _ in range(_ORIENTATION_REFINEMENT_ROUNDS):
        display_positions = place(pair_requirements, wrap_requirement)
        mid_angles = pair_mid_angles(display_positions)
        refined = [
            max(current, required_separation(planet, follower, mid))
            for current, (planet, follower), mid in zip(
                pair_requirements, zip(ordered, ordered[1:]), mid_angles
            )
        ]
        refined_wrap = max(
            wrap_requirement, required_separation(ordered[-1], ordered[0], mid_angles[-1])
        )
        requirements_settled = refined_wrap <= wrap_requirement + 1e-3 and all(
            new <= old + 1e-3 for new, old in zip(refined, pair_requirements)
        )
        pair_requirements, wrap_requirement = refined, refined_wrap
        if requirements_settled:
            break
    if not requirements_settled:
        # The failure mode the round bound exists for: the last placement was
        # never re-validated against its own orientations, so some pair may sit
        # tighter than its ink requires. Say so — a silent near-collision is
        # indistinguishable from a correct render until someone looks.
        logger.warning(
            "Modern decluttering: orientation refinement did not converge in %d rounds "
            "for %d points; the rendered spacing may be tighter than the ink model requires.",
            _ORIENTATION_REFINEMENT_ROUNDS,
            n,
        )

    for planet, display in zip(ordered, display_positions):
        planet["display_angle"] = _normalize_angle(display)

    return sorted_planets


def _draw_indicator_line(
    real_angle: float,
    display_angle: float,
    start_y: float = HOUSE_LINE_OUTER_Y,
    tick_length: float = 1.075,
    arc_radius: Optional[float] = None,
    planet_slug: str = "",
    abs_pos: Optional[float] = None,
    horoscope_id: Optional[str] = None,
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
        planet_slug: Name of the celestial point (for kr:slug metadata).
        abs_pos: The owning ChartPoint's absolute position. Must be the SAME float
            the ChartPoint tag interpolates so the kr:absoluteposition strings are
            identical (downstream focus code matches them by string equality).
        horoscope_id: Owner subject id ("0"/"1") emitted as kr:horoscope in dual
            charts so the indicator can be tied to the correct ring.

    Returns:
        SVG group string for the indicator line.
    """
    if arc_radius is None:
        arc_radius = R_PLANET_OUTER - 1  # 42.5

    slug_attr = f' kr:slug="{escape_svg_text(planet_slug)}"' if planet_slug else ""
    pos_attr = f' kr:absoluteposition="{abs_pos}"' if abs_pos is not None else ""
    horoscope_attr = f' kr:horoscope="{horoscope_id}"' if horoscope_id is not None else ""
    out = f'<g kr:node="Indicator"{slug_attr}{pos_attr}{horoscope_attr} transform="rotate(-{real_angle:.6f} {CENTER} {CENTER})">\n'

    angle_diff = wrap_180(display_angle - real_angle)

    if abs(angle_diff) < STRAIGHT_TETHER_THRESHOLD:
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


def _draw_gauquelin_division_lines(
    line_outer_y: float = HOUSE_LINE_OUTER_Y,
    line_inner_y: float = HOUSE_LINE_INNER_Y,
    gauquelin_cusps: Optional[list[float]] = None,
    seventh_house_degree_ut: float = 0.0,
) -> str:
    """Draw 36 Gauquelin sector division lines through the planet ring.

    Replaces house division lines when Gauquelin mode is active.
    Angular sectors (1, 10, 19, 28) get thicker lines.
    """
    out = ""
    for i in range(36):
        if gauquelin_cusps is not None:
            angle = _zodiac_to_wheel_angle(gauquelin_cusps[i], seventh_house_degree_ut)
        else:
            # Descending fallback: ASC at wheel angle 0, diurnal direction.
            angle = (360.0 - i * 10.0) % 360.0
        is_angular = i % 9 == 0
        stroke_w = ANGULAR_STROKE_WIDTH if is_angular else NORMAL_STROKE_WIDTH

        out += (
            f'<line x1="{CENTER}" y1="{line_outer_y}" '
            f'x2="{CENTER}" y2="{line_inner_y}" '
            f'stroke="{COLOR_STROKE}" stroke-width="{stroke_w}" '
            f'transform="rotate(-{angle:.6f} {CENTER} {CENTER})"/>\n'
        )
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
    planet_y_config: Optional[dict] = None,
    indicator_config: Optional[dict] = None,
    horoscope_id: Optional[str] = None,
    scale_config: Optional[dict] = None,
    gauquelin_sectors: bool = False,
    gauquelin_cusps: Optional[list[float]] = None,
    show_zodiac_background_ring: bool = True,
    content_aware_separation: bool = True,
) -> str:
    """
    Draw the planet ring with data clusters and indicator lines.

    Args:
        planets: List of active planet KerykeionPointModel objects.
        planets_settings: List of planet setting dicts (with 'name', 'color', 'id').
        seventh_house_degree_ut: 7th house cusp absolute degree.
        houses: List of 12 house KerykeionPointModel objects.
        min_separation: Minimum degrees between planet clusters; with
            content-aware separation, the per-pair ceiling.
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
        gauquelin_sectors: If True, draw 36 sector lines instead of 12 house lines.
        gauquelin_cusps: 36 zodiacal longitudes for actual sector boundaries.
        content_aware_separation: Derive each pair's separation from the ink it
            actually draws (narrow content packs tighter, capped at
            min_separation). False falls back to the uniform separation —
            the measurement harness uses that to probe exact spacings.

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

    # Division lines through the planet ring
    if gauquelin_sectors:
        out += _draw_gauquelin_division_lines(line_outer_y, line_inner_y, gauquelin_cusps=gauquelin_cusps, seventh_house_degree_ut=seventh_house_degree_ut)
    else:
        out += _draw_house_division_lines(houses, seventh_house_degree_ut, line_outer_y, line_inner_y)

    # Row positions and element scales, resolved once: the renderer, the
    # content-aware profiles, and the row radii must all read the same values.
    planet_y_config = planet_y_config or {}
    row_positions = {
        "glyph_y": planet_y_config.get("glyph_y", NATAL_PLANET_GLYPH_Y),
        "degrees_y": planet_y_config.get("degrees_y", NATAL_DEGREES_Y),
        "sign_y": planet_y_config.get("sign_y", NATAL_SIGN_Y),
        "minutes_y": planet_y_config.get("minutes_y", NATAL_MINUTES_Y),
        "rx_y": planet_y_config.get("rx_y", NATAL_RX_Y),
    }
    scale_config = scale_config or {}
    element_scales = {
        "planet_scale_base": scale_config.get("planet_scale_base", PLANET_SCALE_BASE),
        "degrees_font_size": scale_config.get("degrees_font_size", DEGREES_FONT_SIZE),
        "sign_scale_base": scale_config.get("sign_scale_base", SIGN_SCALE_BASE),
        "minutes_font_size": scale_config.get("minutes_font_size", MINUTES_FONT_SIZE),
        "rx_font_size": scale_config.get("rx_font_size", RX_FONT_SIZE),
    }
    planet_kwargs = {**row_positions, **element_scales}

    # Build planet angle data
    planets_with_angles = []
    color_map = {s["name"].lower().replace(" ", "_"): s.get("color", COLOR_TEXT) for s in planets_settings}

    for point in planets:
        angle = _zodiac_to_wheel_angle(point.abs_pos, seventh_house_degree_ut)
        name_key = point.name.lower().replace(" ", "_").replace("'", "").replace("\u2019", "")
        color = color_map.get(name_key, COLOR_TEXT)
        planet_entry = {
            "angle": angle,
            "point": point,
            "color": color,
        }
        if content_aware_separation:
            planet_entry["row_half_widths"] = _cluster_row_profile(point, **element_scales)
        planets_with_angles.append(planet_entry)

    # Resolve collisions
    row_radii = {
        "glyph": CENTER - row_positions["glyph_y"],
        "degrees": CENTER - row_positions["degrees_y"],
        "sign": CENTER - row_positions["sign_y"],
        "minutes": CENTER - row_positions["minutes_y"],
        "rx": CENTER - row_positions["rx_y"],
    }
    resolved = _resolve_planet_collisions(
        planets_with_angles,
        min_separation=min_separation,
        row_radii=row_radii if content_aware_separation else None,
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
            horoscope_id=horoscope_id,
            show_zodiac_background_ring=show_zodiac_background_ring,
            **planet_kwargs,
        )
        out += planet_svg

        # Draw indicator line. abs_pos must be the same float the ChartPoint tag
        # interpolates so the kr:absoluteposition strings match exactly.
        out += _draw_indicator_line(
            real_angle,
            display_angle,
            planet_slug=point.name,
            abs_pos=point.abs_pos,
            horoscope_id=horoscope_id,
            **ind_kwargs,
        )

    out += "</g>\n"
    return out


def _draw_single_planet_in_ring(
    point: KerykeionPointModel,
    display_angle: float,
    counter_rotation: float,
    color: str,
    glyph_y: float = NATAL_PLANET_GLYPH_Y,
    degrees_y: float = NATAL_DEGREES_Y,
    sign_y: float = NATAL_SIGN_Y,
    minutes_y: float = NATAL_MINUTES_Y,
    rx_y: float = NATAL_RX_Y,
    planet_scale_base: float = PLANET_SCALE_BASE,
    degrees_font_size: float = DEGREES_FONT_SIZE,
    sign_scale_base: float = SIGN_SCALE_BASE,
    minutes_font_size: float = MINUTES_FONT_SIZE,
    rx_font_size: float = RX_FONT_SIZE,
    horoscope_id: Optional[str] = None,
    show_zodiac_background_ring: bool = True,
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
    # Shared with _cluster_row_profile, so the separation model reserves the
    # width of exactly what gets drawn.
    degrees_text = _format_degrees_text(point)
    minutes_text = _format_minutes_text(point)
    sign = point.sign
    is_retro = point.retrograde is True
    fill_color = COLOR_RETROGRADE if is_retro else color

    point_slug = point.name
    planet_id = point_slug if point.point_type == "House" else resolve_glyph_id(point_slug)

    retro_attr = ' kr:retrograde="true"' if is_retro else ""
    horoscope_attr = f' kr:horoscope="{horoscope_id}"' if horoscope_id else ""
    gauq = getattr(point, "gauquelin_sector", None)
    gauq_attr = f' kr:gauquelinsector="{gauq}"' if gauq is not None else ""

    # kr:cx / kr:cy — glyph center in the WHEEL-LOCAL 100-unit frame (the
    # ModernHoroscope group's own coordinate space, i.e. the viewBox of the
    # wheel-only output). This is exact for generate_wheel_only_svg_string
    # (viewBox 0 0 100 100). In the full-chart output chart_drawer wraps this
    # wheel in an outer scale + Full_Wheel translate and rebases these values
    # via _rebase_glyph_centers, so every final SVG carries true root-space
    # coordinates regardless of the consuming template.
    #
    # Three nested frames sit between the glyph and the wheel-local frame:
    #   1. ChartPoint          rotate(-display_angle, CENTER, CENTER)
    #   2. zodiac-bg wrapper    translate(off off) scale(s)   [only when the
    #                           zodiac background ring is drawn]
    #   3. ModernHoroscope      rotate(-90, CENTER, CENTER)
    # Undoing only (1) — as the old code did — left cx/cy in the PlanetRing
    # frame, ~90° (and, with the zodiac ring, ~8%) off the real glyph. Compose
    # all three so the emitted values locate the glyph in the wheel-local frame.
    angle_rad = math.radians(display_angle)
    dy = glyph_y - CENTER
    gx = CENTER + dy * math.sin(angle_rad)   # frame (1) undone: ChartPoint-parent coords
    gy = CENTER + dy * math.cos(angle_rad)
    if show_zodiac_background_ring:
        s = ZODIAC_BG_SCALE
        off = CENTER * (1 - s)
        gx = gx * s + off                     # frame (2): translate(off) scale(s)
        gy = gy * s + off
    # frame (3): rotate(-90, CENTER, CENTER) maps (x, y) -> (C + (y-C), C - (x-C))
    glyph_cx = CENTER + (gy - CENTER)
    glyph_cy = CENTER - (gx - CENTER)

    out = (
        f'<g kr:node="ChartPoint" kr:house="{point.house}" '
        f'kr:sign="{sign}" kr:absoluteposition="{point.abs_pos}" '
        f'kr:signposition="{point.position}" kr:slug="{escape_svg_text(point_slug)}"{retro_attr}{horoscope_attr}{gauq_attr} '
        f'kr:cx="{glyph_cx}" kr:cy="{glyph_cy}" '
        f'transform="rotate(-{display_angle:.6f} {CENTER} {CENTER})">\n'
    )

    # Planet glyph (outermost, largest — near outer edge of planet ring)
    planet_scale = planet_scale_base * GLYPH_SCALE_MAP.get(planet_id, 1.0)
    out += (
        f'  <g transform="translate({CENTER} {glyph_y}) rotate({counter_rotation:.6f}) scale({planet_scale}) translate(-14 -14)">\n'
        f'    <use xlink:href="#{planet_id}" kr:slug="{escape_svg_text(point_slug)}" kr:node="Glyph" fill="{fill_color}" />\n'
        f"  </g>\n"
    )

    # Degrees text
    out += (
        f'  <text text-anchor="middle" dominant-baseline="middle" '
        f'x="{CENTER}" y="{degrees_y}" font-size="{degrees_font_size}" fill="{fill_color}" '
        f'font-weight="500" '
        f'transform="rotate({counter_rotation:.6f} {CENTER} {degrees_y})">{degrees_text}</text>\n'
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
        f'transform="rotate({counter_rotation:.6f} {CENTER} {minutes_y})">{minutes_text}</text>\n'
    )

    # RX text (innermost — near inner edge of planet ring)
    if is_retro:
        out += (
            f'  <text text-anchor="middle" dominant-baseline="middle" '
            f'x="{CENTER}" y="{rx_y}" font-size="{rx_font_size}" fill="{fill_color}" '
            f'font-weight="500" '
            f'transform="rotate({counter_rotation:.6f} {CENTER} {rx_y})">{RETROGRADE_LABEL}</text>\n'
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


def _gauquelin_sector_mid_angle(
    cusps_wheel: list[float],
    i: int,
) -> float:
    """Compute the wheel-angle midpoint of Gauquelin sector i (0-indexed)."""
    a = cusps_wheel[i]
    b = cusps_wheel[(i + 1) % 36]
    span = (a - b) % 360
    return (b + span / 2) % 360


def _draw_gauquelin_cusp_ring(
    seventh_house_degree_ut: float,
    show_zodiac_background_ring: bool = True,
    gauquelin_cusps: Optional[list[float]] = None,
) -> str:
    """Draw 36 Gauquelin sector lines in the cusp ring area (replaces houses)."""
    out = ""
    ring_outer = R_CUSP_OUTER
    ring_inner = R_CUSP_INNER

    # Background ring
    out += (
        f'<path d="{_annulus_path(ring_outer, ring_inner)}" '
        f'fill="{COLOR_BACKGROUND}" fill-rule="evenodd" '
        f'stroke="{COLOR_STROKE}" stroke-width="0.25"/>\n'
    )

    text_r = (ring_outer + ring_inner) / 2  # midpoint of ring for text

    # Pre-compute wheel angles for all cusps
    if gauquelin_cusps is not None:
        cusps_wheel = [_zodiac_to_wheel_angle(c, seventh_house_degree_ut) for c in gauquelin_cusps]
    else:
        # Descending fallback: ASC at wheel angle 0, diurnal direction.
        cusps_wheel = [(360.0 - i * 10.0) % 360.0 for i in range(36)]

    for i in range(36):
        angle = cusps_wheel[i]
        is_angular = i % 9 == 0
        stroke_w = ANGULAR_STROKE_WIDTH if is_angular else 0.3

        # Division line
        out += (
            f'<line x1="{CENTER}" y1="{CENTER - ring_outer}" '
            f'x2="{CENTER}" y2="{CENTER - ring_inner}" '
            f'stroke="{COLOR_STROKE}" stroke-width="{stroke_w}" '
            f'transform="rotate(-{angle:.6f} {CENTER} {CENTER})"/>\n'
        )

        # Sector number text — rotate to midpoint of sector, counter-rotate text
        # (rotations sum to +90 to cancel the global rotate(-90) wheel group).
        mid_angle = _gauquelin_sector_mid_angle(cusps_wheel, i)
        fs = 2.5 if is_angular else 1.8
        fw = "bold" if is_angular else "normal"
        out += (
            f'<text x="{CENTER}" y="{CENTER - text_r}" '
            f'font-size="{fs}" fill="{COLOR_TEXT}" font-weight="{fw}" '
            f'text-anchor="middle" dominant-baseline="central" '
            f'transform="rotate(-{mid_angle:.6f} {CENTER} {CENTER}) '
            f'rotate({90 + mid_angle:.6f} {CENTER} {CENTER - text_r})">'
            f"{i + 1}</text>\n"
        )

    return out


def _draw_gauquelin_house_ring(
    seventh_house_degree_ut: float,
    gauquelin_cusps: Optional[list[float]] = None,
) -> str:
    """Draw 36 Gauquelin sector markers in the house ring (replaces house numbers)."""
    out = ""
    # Draw ring background
    out += (
        f'<path d="{_annulus_path(R_HOUSE_OUTER, R_HOUSE_INNER)}" '
        f'fill="{COLOR_HOUSE_RING}" fill-rule="evenodd" '
        f'stroke="{COLOR_STROKE}" stroke-width="0.15"/>\n'
    )

    # 36 sector division lines
    for i in range(36):
        if gauquelin_cusps is not None:
            angle = _zodiac_to_wheel_angle(gauquelin_cusps[i], seventh_house_degree_ut)
        else:
            # Descending fallback: ASC at wheel angle 0, diurnal direction.
            angle = (360.0 - i * 10.0) % 360.0
        is_angular = i % 9 == 0
        stroke_w = 0.5 if is_angular else 0.15

        out += (
            f'<line x1="{CENTER}" y1="{CENTER - R_HOUSE_OUTER}" '
            f'x2="{CENTER}" y2="{CENTER - R_HOUSE_INNER}" '
            f'stroke="{COLOR_STROKE}" stroke-width="{stroke_w}" '
            f'transform="rotate(-{angle:.6f} {CENTER} {CENTER})"/>\n'
        )

    return out


# =============================================================================
# RING 4: HOUSE RING (house numbers)
# =============================================================================


def _draw_house_sectors_modern(
    houses: list[KerykeionPointModel],
    seventh_house_degree_ut: float,
    inner_r: float = R_HOUSE_INNER,
    outer_r: float = R_CUSP_OUTER,
    horoscope_id: Optional[str] = None,
) -> str:
    """Draw transparent house sector wedges for interactive highlighting (modern style)."""
    horoscope_attr = f' kr:horoscope="{horoscope_id}"' if horoscope_id is not None else ""
    out = ""
    for i in range(12):
        next_i = (i + 1) % 12
        house_num = i + 1

        a_start = _zodiac_to_wheel_angle(houses[i].abs_pos, seventh_house_degree_ut)
        a_end = _zodiac_to_wheel_angle(houses[next_i].abs_pos, seventh_house_degree_ut)

        # Convert wheel angles to radians (parent group has rotate(-90), so subtract 90)
        r_start = math.radians(-a_start - 90)
        r_end = math.radians(-a_end - 90)

        # 4 corners of the annular sector
        ox1 = CENTER + outer_r * math.cos(r_start)
        oy1 = CENTER + outer_r * math.sin(r_start)
        ox2 = CENTER + outer_r * math.cos(r_end)
        oy2 = CENTER + outer_r * math.sin(r_end)
        ix1 = CENTER + inner_r * math.cos(r_start)
        iy1 = CENTER + inner_r * math.sin(r_start)
        ix2 = CENTER + inner_r * math.cos(r_end)
        iy2 = CENTER + inner_r * math.sin(r_end)

        # Angular span to determine large-arc flag
        span = _normalize_angle(houses[next_i].abs_pos - houses[i].abs_pos)
        large_arc = 1 if span > 180 else 0

        d = (
            f"M {ox1:.6f},{oy1:.6f} "
            f"A {outer_r},{outer_r} 0 {large_arc},0 {ox2:.6f},{oy2:.6f} "
            f"L {ix2:.6f},{iy2:.6f} "
            f"A {inner_r},{inner_r} 0 {large_arc},1 {ix1:.6f},{iy1:.6f} Z"
        )

        out += (
            f'<g kr:node="HouseSector" kr:house="{house_num}"{horoscope_attr}>'
            f'<path d="{d}" fill="transparent" stroke="none" pointer-events="all"/>'
            f"</g>\n"
        )

    return out


def _draw_gauquelin_sectors_modern(
    seventh_house_degree_ut: float,
    gauquelin_cusps: Optional[list[float]] = None,
    inner_r: float = R_HOUSE_INNER,
    outer_r: float = R_CUSP_OUTER,
) -> str:
    """Draw 36 transparent Gauquelin-sector wedges for interactive highlighting.

    The Gauquelin variant of ``_draw_house_sectors_modern``: on a Gauquelin chart
    the visible cusp/house rings are the 36-sector variants, so the click hit-
    areas must match them (12 house wedges would leave the ring un-clickable /
    mis-targeted). Each wedge is tagged ``kr:node="GauquelinSector"`` with its
    1-based sector number.
    """
    out = ""
    for i in range(36):
        next_i = (i + 1) % 36
        sector_num = i + 1

        if gauquelin_cusps is not None:
            start_deg = gauquelin_cusps[i]
            end_deg = gauquelin_cusps[next_i]
            a_start = _zodiac_to_wheel_angle(start_deg, seventh_house_degree_ut)
            a_end = _zodiac_to_wheel_angle(end_deg, seventh_house_degree_ut)
            # Gauquelin cusps DECREASE (diurnal direction), so the sector span is
            # start-minus-end (~10 deg); end-minus-start would wrap to ~350 and
            # wrongly set large_arc=1, making every hit-area cover the whole ring.
            span = _normalize_angle(start_deg - end_deg)
        else:
            # Descending fallback matching _draw_gauquelin_house_ring.
            a_start = (360.0 - i * 10.0) % 360.0
            a_end = (360.0 - next_i * 10.0) % 360.0
            span = 10.0

        r_start = math.radians(-a_start - 90)
        r_end = math.radians(-a_end - 90)

        ox1 = CENTER + outer_r * math.cos(r_start)
        oy1 = CENTER + outer_r * math.sin(r_start)
        ox2 = CENTER + outer_r * math.cos(r_end)
        oy2 = CENTER + outer_r * math.sin(r_end)
        ix1 = CENTER + inner_r * math.cos(r_start)
        iy1 = CENTER + inner_r * math.sin(r_start)
        ix2 = CENTER + inner_r * math.cos(r_end)
        iy2 = CENTER + inner_r * math.sin(r_end)

        large_arc = 1 if span > 180 else 0

        d = (
            f"M {ox1:.6f},{oy1:.6f} "
            f"A {outer_r},{outer_r} 0 {large_arc},0 {ox2:.6f},{oy2:.6f} "
            f"L {ix2:.6f},{iy2:.6f} "
            f"A {inner_r},{inner_r} 0 {large_arc},1 {ix1:.6f},{iy1:.6f} Z"
        )

        out += (
            f'<g kr:node="GauquelinSector" kr:sector="{sector_num}">'
            f'<path d="{d}" fill="transparent" stroke="none" pointer-events="all"/>'
            f"</g>\n"
        )

    return out


def _draw_house_ring(
    houses: list[KerykeionPointModel],
    seventh_house_degree_ut: float,
    line_inner_radius: float = R_HOUSE_INNER,  # stop exactly at the aspect core boundary
    show_numbers: bool = True,
    house_inner_r: float = R_HOUSE_INNER,
    house_outer_r: float = R_HOUSE_OUTER,
    text_y: float = 29.25,
    horoscope_id: Optional[str] = None,
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
        horoscope_id: Owner subject id emitted as kr:horoscope on each HouseNumber
            ("0" = first subject, "1" = second), matching the classic engine.

    Returns:
        SVG group string for the house ring.
    """
    horoscope_attr = f' kr:horoscope="{horoscope_id}"' if horoscope_id is not None else ""
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
                f'<g kr:node="HouseNumber" kr:house="{house_num}"{horoscope_attr}>'
                f'<text text-anchor="middle" dominant-baseline="middle" '
                f'x="{CENTER}" y="{text_y}" font-size="1.5" fill="{COLOR_TEXT}" '
                f'font-weight="500" '
                f'transform="rotate(-{mid_angle_abs:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright:.6f} {CENTER} {text_y})">'
                f"{house_num}</text>"
                f"</g>\n"
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
    "biquintile": 144,
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
    # Third element is the aspect's degrees: an int from ASPECT_DEGREE_MAP, or
    # "" when the aspect name is unknown.
    rendered_icon_positions: list[tuple[float, float, int | str]] = []
    icon_collision_threshold = 8.0  # minimum distance between same-type icons

    for aspect in aspects_list:
        aspect_name = aspect.get("aspect", "")
        if aspect_name not in color_map:
            # No settings entry (e.g. declination parallels with the default
            # set): drawing a longitude chord would misrepresent a declination
            # aspect — skip it, matching the classic wheel's name lookup.
            continue
        color = color_map[aspect_name]
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
            f'<g kr:node="Aspect" kr:aspectname="{escape_svg_text(aspect_name)}" '
            f'kr:to="{escape_svg_text(p1_name)}" kr:tooriginaldegrees="{p1_abs}" '
            f'kr:from="{escape_svg_text(p2_name)}" kr:fromoriginaldegrees="{p2_abs}" '
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
    gauquelin_sectors: bool = False,
    gauquelin_cusps: Optional[list[float]] = None,
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
        gauquelin_cusps: 36 zodiacal longitudes for actual Gauquelin sector boundaries.

    Returns:
        Complete SVG content string for the modern horoscope.
    """
    # Orient the entire wheel so that 0° (Ascendant) is at 9 o'clock (LEFT)
    # The SVG initial orientation puts 0° at TOP. We rotate the whole group by -90°.
    out = (
        f'<g kr:node="ModernHoroscope" font-family="{MODERN_TEXT_FONT_FAMILY}" '
        f'transform="rotate(-90 {CENTER} {CENTER})">\n'
    )

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
    if gauquelin_sectors:
        out += _draw_gauquelin_cusp_ring(seventh_house_degree_ut, show_zodiac_background_ring, gauquelin_cusps=gauquelin_cusps)
    else:
        out += _draw_cusp_ring(houses, seventh_house_degree_ut, show_zodiac_background_ring, horoscope_id="0")
    out += _draw_ruler_ring()
    out += _draw_planet_ring(
        planets, planets_settings, seventh_house_degree_ut, houses,
        gauquelin_sectors=gauquelin_sectors, gauquelin_cusps=gauquelin_cusps,
        show_zodiac_background_ring=show_zodiac_background_ring,
    )
    if gauquelin_sectors:
        out += _draw_gauquelin_house_ring(seventh_house_degree_ut, gauquelin_cusps=gauquelin_cusps)
    else:
        out += _draw_house_ring(houses, seventh_house_degree_ut, horoscope_id="0")
    # House sectors are click-only overlays; clip them to the inner edge of
    # the zodiac background ring when the zodiac is drawn, so a click on a
    # zodiac sign isn't intercepted by the house sector underneath. Falls
    # back to R_CUSP_OUTER when no zodiac ring is rendered.
    house_sector_outer_r = R_ZODIAC_BG_INNER if show_zodiac_background_ring else R_CUSP_OUTER
    if gauquelin_sectors:
        # Match the click hit-areas to the visible 36-sector rings above.
        out += _draw_gauquelin_sectors_modern(
            seventh_house_degree_ut, gauquelin_cusps=gauquelin_cusps, outer_r=house_sector_outer_r
        )
    else:
        out += _draw_house_sectors_modern(houses, seventh_house_degree_ut, outer_r=house_sector_outer_r)
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

    out = (
        f'<g kr:node="ModernDualHoroscope" kr:charttype="{chart_type}" '
        f'font-family="{MODERN_TEXT_FONT_FAMILY}" transform="rotate(-90 {CENTER} {CENTER})">\n'
    )

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
    out += _draw_cusp_ring(houses_1, seventh_house_degree_ut, show_zodiac_background_ring, horoscope_id="0")

    # ─── RULER RING (Subject 1's houses — shared) ───────────────────
    out += _draw_ruler_ring()

    # ─── OUTER PLANET RING (Subject 2) ──────────────────────────────
    out += _draw_planet_ring(
        planets=planets_2,
        planets_settings=planets_settings,
        seventh_house_degree_ut=seventh_house_degree_ut,
        houses=houses_1,  # Subject 1's houses for divider lines
        min_separation=SYN_OUTER_MIN_SEPARATION,
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
        show_zodiac_background_ring=show_zodiac_background_ring,
    )

    # ─── INNER PLANET RING (Subject 1) ──────────────────────────────
    out += _draw_planet_ring(
        planets=planets_1,
        planets_settings=planets_settings,
        seventh_house_degree_ut=seventh_house_degree_ut,
        houses=houses_1,  # Subject 1's own houses
        min_separation=SYN_INNER_MIN_SEPARATION,
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
        show_zodiac_background_ring=show_zodiac_background_ring,
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
        horoscope_id="0",
    )

    # ─── HOUSE SECTORS (transparent, for interactive highlighting) ───
    # Clip outer radius to the zodiac inner boundary when the zodiac ring is
    # drawn, so clicks on a zodiac sign aren't swallowed by the house sector.
    syn_house_sector_outer_r = R_ZODIAC_BG_INNER if show_zodiac_background_ring else R_CUSP_OUTER
    out += _draw_house_sectors_modern(
        houses_1,
        seventh_house_degree_ut,
        inner_r=SYN_R_HOUSE_INNER,
        outer_r=syn_house_sector_outer_r,
        horoscope_id="0",
    )

    # ─── ASPECT CORE (cross-chart aspects) ──────────────────────────
    out += _draw_aspect_core(aspects_list, aspects_settings, seventh_house_degree_ut, core_radius=SYN_R_ASPECT)

    if show_zodiac_background_ring:
        out += "</g>\n"  # Close zodiac bg scale wrapper

    out += "</g>\n"  # Close main group
    return out
