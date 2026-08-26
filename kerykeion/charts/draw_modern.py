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
from dataclasses import dataclass
from typing import Optional, Sequence

from kerykeion.charts.glyph_metrics import estimate_text_width
from kerykeion.charts.spreading import spread_around_wheel
from kerykeion.charts.utils import (
    CHART_TEXT_FONT_FAMILY,
    MINIMUM_WEDGE_SPAN_DEGREES,
    house_spans,
    label_separation_degrees,
    separate_collapsed_wedges,
    _wedges_overlap,
    STATION_LABELS,
    escape_svg_text,
    normalize_degree,
)
from kerykeion.charts.glyph_ink_metrics import (
    GLYPH_INK_HALF_HEIGHT,
    GLYPH_INK_HALF_WIDTH,
    SIGN_INK_HALF_HEIGHT,
    SIGN_INK_HALF_WIDTH,
    TEXT_INK_HALF_HEIGHT,
    TEXT_INK_HALF_WIDTH,
    TEXT_INK_REFERENCE_FONT_SIZE,
    TEXT_INK_CENTRE_Y,
)
from kerykeion.charts.svg_metadata import point_state_attributes
from kerykeion.utilities.core import wrap_180
from kerykeion.schemas.models import KerykeionPointModel
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
R_PLANET_OUTER = 44.652

# Ring 2: Graduated ruler
R_RULER_INNER = 44.652
R_RULER_OUTER = 45.652

# Ring 1: Cusp/zodiac ring
# Same visual thickness as the zodiac band: that band is 4.0 units deep in the
# outer frame, and this one lives inside the 0.92 wrapper, so it needs
# 4.0 / 0.92 = 4.348 of its own to look the same weight.
R_CUSP_INNER = 45.652
R_CUSP_OUTER = 50.0

# Ring 0 (optional): Zodiac background ring (outermost, outside cusp ring)
# When enabled, the existing chart is scaled to fit inside R_ZODIAC_BG_INNER,
# and the zodiac wedges occupy R_ZODIAC_BG_INNER to R_ZODIAC_BG_OUTER.
R_ZODIAC_BG_INNER = 46.0
R_ZODIAC_BG_OUTER = 50.0
ZODIAC_BG_SCALE = R_ZODIAC_BG_INNER / R_CUSP_OUTER  # 0.92

# The aspect core is drawn in its own frame: the group is scaled by
# ASPECT_CORE_SCALE, so a length written inside it lands on the wheel that much
# smaller — which is why both numbers below read thinner and smaller than they
# look. A line at 0.32 inks 0.118 wheel units and a glyph at 0.58 spans 2.15.
#
# Both went up together, on the drawing: the web is the one part of the wheel
# read at a glance rather than point by point, and at 0.25 / 0.45 the lines
# thinned out against the ring around them while the marks that name each aspect
# were too small to tell a square from a trine without looking twice. Raising
# only the glyph would have left it sitting on a thread; raising only the line
# would have made a denser chart look like a scribble.
ASPECT_CORE_SCALE = 0.37
ASPECT_LINE_WIDTH = 0.32
ASPECT_GLYPH_SCALE = 0.58

# House line endpoints
HOUSE_LINE_OUTER_Y = 5.348  # Just inside the ruler ring outer edge
HOUSE_LINE_INNER_Y = 28.0  # At the house ring boundary

# Angular houses (1, 4, 7, 10) use thicker lines
ANGULAR_HOUSES = {1, 4, 7, 10}
ANGULAR_STROKE_WIDTH = 0.6
NORMAL_STROKE_WIDTH = 0.07

# A cusp and a reading can occupy the same place: an angle's cluster sits on its
# own cusp by construction, and any point within a couple of degrees of one
# lands there too. Where that happens the line turns to a SOLID dimmed tone for
# the length of the reading — it passes behind the words rather than through
# them, so the axis stays whole and the text keeps the contrast of the ring
# under it. Solid, not translucent: the tone IS the old 0.35-opacity composite
# of the cusp colour over the ring it crosses, baked per ring and per theme —
# a stroke-opacity dim vanished on hosts that show through the chart (Studio's
# glass), because what it composited with was no longer the ring.
COLOR_CUSP_DIM = "var(--kerykeion-modern-cusp-dim, #c4c4cb)"
COLOR_CUSP_DIM_OUTER = "var(--kerykeion-modern-cusp-dim-outer, #babac6)"
# How close a mark must come before the line makes room: a hair past touching,
# not a clearance. Measured ink, so a wider tolerance dims lines that are still
# visibly clear of the text.
CUSP_DIM_TOLERANCE = 0.10
# Air left at each end of the dimmed stretch.
CUSP_DIM_MARGIN = 0.45

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
PLANET_MIN_SEPARATION = 7.75

# Cusp ring text size (degrees and minutes shown at each house cusp)
CUSP_FONT_SIZE = 1.9

#: How far the degree and minute texts sit either side of the cusp line, which
#: is what makes a cusp reading a band of ring rather than a point — and
#: therefore what two neighbouring cusps have to clear. At 4.0° the three parts
#: read as one reading, with about half a character of air between the glyph and
#: the digits either side; below 3.5° they start to touch.
CUSP_TEXT_OFFSET_DEGREES = 4.0

#: Scale of the sign glyph on the cusp line. Sized against the text beside it
#: rather than by eye: a sign glyph inks 13.45 units of half-height in its native
#: box against the 5.0-per-10-of-font a line of digits inks, so at 0.12 it stood
#: 1.61 times taller than the numbers it sits between — and that is the ordinary
#: case, not the worst, since seven of the twelve signs share that height. This
#: leaves it a little taller than the digits on purpose: matching the inked
#: extents exactly makes the glyph look smaller than them, because part of its
#: ink is a descender the numbers do not have.
CUSP_GLYPH_SCALE = 0.085

#: How far the ring will shrink once even the staggered lanes have run out.
#: Below this the text stops being worth reading, so the ring keeps the size
#: and takes the overlap.
CUSP_MIN_SCALE = 0.62

#: Distance of a cusp reading from the wheel's rim, in the 100-unit frame:
#: the middle of the band, so the reading has the same air above and below.
CUSP_LABEL_Y = (R_CUSP_OUTER - R_CUSP_INNER) / 2

#: Ink the ring has to hold, in wheel units at full scale. Measured extents,
#: not em boxes: a sign glyph inks about two thirds of its 32-unit box, and
#: sizing the lanes off the box would cost a third of the ring for nothing.
_CUSP_SIGN_HALF_HEIGHT = max(SIGN_INK_HALF_HEIGHT.values()) * CUSP_GLYPH_SCALE
_CUSP_TEXT_HALF_HEIGHT = (
    max(TEXT_INK_HALF_HEIGHT.values()) / TEXT_INK_REFERENCE_FONT_SIZE * CUSP_FONT_SIZE
)

#: Clear air between the ring's edge and a reading, and between the two lanes.
CUSP_RING_MARGIN = 0.15
CUSP_LANE_GUTTER = 0.3

#: The largest scale at which two lanes are actually two lanes.
#:
#: Staggering buys vertical room the ring does not have in unlimited supply:
#: it is 5.5 units deep, so a reading pushed outward must still stay inside the
#: rim, and one pushed inward must clear the ink its neighbour left on the
#: other lane. Both bounds move with the text size — larger text needs a bigger
#: offset and leaves less room for it — and they meet at exactly one scale.
#: Above it, staggering either pushes a glyph out of the ring or drops a
#: reading onto the neighbouring sign, so shrinking to here is the price of
#: using the lanes at all; below it there is slack, and the offset can stay put.
#:
#: The binding pair is a reading's text against the *next* cusp's sign glyph —
#: taller than a text and only a fraction of the offset away, so it needs more
#: separation than two texts do.
CUSP_STAGGER_SCALE = (CUSP_LABEL_Y - CUSP_RING_MARGIN - CUSP_LANE_GUTTER / 2) / (
    _CUSP_SIGN_HALF_HEIGHT + (_CUSP_SIGN_HALF_HEIGHT + _CUSP_TEXT_HALF_HEIGHT) / 2
)

#: How far a staggered reading moves off the centre line, either way: as far
#: as the rim allows at the scale above, which is also exactly as far as the
#: other lane needs. One value for every scale — a ring whose stagger depth
#: changed with the crowding would read as two different devices.
CUSP_LANE_OFFSET = CUSP_LABEL_Y - CUSP_RING_MARGIN - _CUSP_SIGN_HALF_HEIGHT * CUSP_STAGGER_SCALE


def _cusp_lanes(angles: Sequence[float], band: float) -> list[Optional[int]]:
    """Which radial lane each reading takes, or ``None`` to stay on the centre line.

    Only the readings that would actually print through a neighbour move.
    Staggering a cusp with clear air either side would push it off the line it
    describes to solve a problem it does not have, and a ring where every
    reading sits high or low reads as a wobble rather than as a device.

    Two lanes are enough for the ones that do move: a reading only has to clear
    the one before and the one after it. Crowded runs alternate, and a run ends
    wherever a gap is wide enough that the two readings clear anyway — which
    resets the alternation, so one tight pair does not stagger the whole ring.
    """
    count = len(angles)
    if count < 2:
        return [None] * count

    #: ``tight[i]``: readings *i* and *i+1* are closer than the band they occupy.
    # How far apart two readings are, not how far one is from the other going
    # forwards: above the polar circle several systems return their cusps in
    # decreasing order, and the one-way gap then reads a seven-degree crowd as
    # three hundred and fifty-two degrees of room. Nothing was ever staggered on
    # such a chart, and the readings sat on top of each other.
    tight = [
        abs(((angles[(index + 1) % count] - angles[index] + 180.0) % 360.0) - 180.0) < band
        for index in range(count)
    ]
    if not any(tight):
        return [None] * count

    # Walk from where a run starts, so the alternation never has to reconcile
    # two halves meeting at an arbitrary seam.
    start = next((index for index in range(count) if not tight[index - 1]), None)
    if start is None:
        # Every gap is tight, so there is no such place, and if the readings
        # are odd in number no walk can alternate all the way round anyway.
        # Begin just after the widest gap: whatever the seam costs, it costs
        # least there.
        start = max(range(count), key=lambda index: (angles[index] - angles[index - 1]) % 360.0)

    lanes: list[Optional[int]] = [None] * count
    for step in range(count):
        index = (start + step) % count
        previous = (index - 1) % count
        preceding = lanes[previous]
        if tight[previous] and preceding is not None:
            lanes[index] = 1 - preceding
        elif tight[index] or tight[previous]:
            lanes[index] = 0
    return lanes


def _cusp_cluster_span(scale: float) -> float:
    """Degrees of ring one cusp reading occupies at *scale*.

    The two texts sit a fixed angular distance either side of the line, so the
    band is that distance doubled plus the arc the outermost string itself
    covers — and all three shrink together.
    """
    return 2.0 * CUSP_TEXT_OFFSET_DEGREES * scale + label_separation_degrees(
        estimate_text_width("59'", CUSP_FONT_SIZE * scale), R_CUSP_OUTER - 2.75, gutter_px=0.4
    )

# Native drawing box of a planet-family symbol, from ``scripts.glyph_catalog``.
# The glyph is centred on it at the use site; anchoring it on the 28-unit box
# the set used before the symbols were redrawn left every mark riding two units
# high and left of its own row, which the eye reads as uneven cluster spacing.
PLANET_GLYPH_BOX = 24

# Planet cluster element sizes — descending visual hierarchy:
#   planet glyph (largest) > degrees text > zodiac sign > minutes text > RX text
# Note: planet glyphs are 24 units native, zodiac signs 32,
# so zodiac sign scale must be proportionally smaller to appear smaller.
PLANET_SCALE_BASE = 0.18144  # Planet glyph: 24 * 0.18144 ≈ 4.35 visual units
DEGREES_FONT_SIZE = 2.24  # Degrees text font size
# The sign glyph carries its size differently from everything around it: a thin
# outline beside solid figures reads smaller than it measures, and at 0.08736 it
# was the one mark in the cluster that looked undersized. Up 18%, and it costs
# nothing at the ruler — it sits in the middle of the block, so it grows into
# the air between the rows rather than into the tether's room. The planet glyph
# was left alone for exactly that reason: it is the row nearest the ruler, and
# it would have had to move inward again to pay for its own growth.
SIGN_SCALE_BASE = 0.10309  # Zodiac sign: 32 * 0.10309 ≈ 3.30 visual units
MINUTES_FONT_SIZE = 2.072  # Minutes text font size
RX_FONT_SIZE = 1.792  # Retrograde indicator font size

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
# Flush against the ruler, as the natal planet ring is. It used to be 43.5,
# which was the ruler's inner edge the day it was written; when the ruler moved
# out to 44.652 this stayed behind, and a band of bare background 1.152 wide
# opened between the outer ring and the ticks. Nothing was drawn in it and
# nothing meant anything by it.
SYN_R_OUTER_PLANET_OUTER = R_RULER_INNER

# House division line endpoints (Subject 1's cusps drawn in both rings)
# Outer ring: top AT the ruler's inner edge, the same anchor the natal lines
# and every tether hang from. It sat at 6.5 — 1.15 units short of the ruler —
# and the axes of a dual wheel visibly stopped mid-air (Giacomo, on the
# rendered chart: «assi e cuspidi non arrivano in fondo, solo nelle doppie»).
SYN_HOUSE_LINE_OUTER_Y1 = HOUSE_LINE_OUTER_Y
SYN_HOUSE_LINE_OUTER_Y2 = 20.5  # Outer ring: bottom (at boundary)
SYN_HOUSE_LINE_INNER_Y1 = 20.5  # Inner ring: top (at boundary)
SYN_HOUSE_LINE_INNER_Y2 = 34.5  # Inner ring: bottom (near house numbers)

# Indicator line geometry, per ring.
#
# An indicator is a tether: it starts at the ruler-side edge of its own ring and
# runs inward to the cluster, so a reader can see which reading belongs to which
# degree. The natal wheel states that as start_y = HOUSE_LINE_OUTER_Y, the inner
# edge of the graduated ruler.
#
# Both dual rings used to start at y = 20.5. For the inner ring (r 15.5-29.5)
# that is its outer edge and correct. For the outer ring (r 29.5-43.5) it is the
# INNER edge — the far end from its glyph at r 41.62 — so its tether was drawn
# twelve units away from the planet it belongs to, on the boundary between the
# rings, pointing outward at nothing. Two symptoms, one cause: the outer ring
# looked as though it had no indicators at all, and the boundary carried two
# families of identical brackets back to back, so the inner ring's own tether
# looked as if it pointed the wrong way.
#
# The cluster rows were translated between the rings; these constants had been
# mirrored instead. A mirror is not a translation.
#
# The outer ring is anchored to the ruler rather than to its own edge, which is
# what the natal ring means by "start_y" anyway. It also spends the 1.152 units
# of background that opened up between SYN_R_OUTER_PLANET_OUTER and the ruler
# when the ruler moved, and that is what buys the tether the same clearance the
# natal one has: it stops 0.30 short of the glyph, against the natal 0.31.
SYN_INDICATOR_OUTER_START_Y = HOUSE_LINE_OUTER_Y  # inner edge of the ruler
SYN_INDICATOR_OUTER_TICK = 0.7
SYN_INDICATOR_OUTER_ARC_R = 43.952  # = r(start) - tick

# The inner ring cannot be re-anchored — it has no ruler beside it, and y = 20.5
# is already its outer edge — so the only lever is length, and length is bought
# from the cluster: see SYN_INNER_PLANET_GLYPH_Y, which steps 0.30 further in to
# pay for this. At 0.7 the tether finished 0.85 INSIDE the glyph; at 0.30 it
# stops 0.25 short of it, the same clearance the last row has at the other end.
SYN_INDICATOR_INNER_START_Y = 20.5  # outer edge of the inner ring
SYN_INDICATOR_INNER_TICK = 0.3
SYN_INDICATOR_INNER_ARC_R = 29.2  # = r(start) - tick

# Planet cluster Y-positioning within each 14-unit ring
# Outer ring (Subject 2) - glyphs near outer edge, all elements within 6.5-20.5
# Placed from the ink, not spaced by hand: each row's half-height at the size it
# is drawn, laid out so the air between every pair comes out the same 1.27 and
# the block sits centred in its ring with 0.55 to spare at either end. Spacing
# the anchors evenly instead — which is what the round numbers here used to be —
# left 1.09 between the glyph and the degrees and 0.60 between the sign and the
# minutes, because a sign glyph inks a thin band in a tall box while a line of
# digits fills its own.
SYN_OUTER_PLANET_GLYPH_Y = 8.38
SYN_OUTER_DEGREES_Y = 11.82
SYN_OUTER_SIGN_Y = 14.76
SYN_OUTER_MINUTES_Y = 17.37
SYN_OUTER_RX_Y = 19.54

# Inner ring (Subject 1) - glyphs near outer edge, all elements within 20.5-34.5
# The same block as the outer ring, moved inward by the 14 units between the two
# — same sizes mean the same spacing, and a reader comparing the two wheels
# compares like with like — and then 0.30 further in.
#
# That last nudge is for the tether. The inner ring has no ruler beside it, so
# its indicator has only the ring's own edge to hang from and only the air
# between that edge and the glyph to live in: 0.547, against the 2.12 the natal
# wheel has. A tether spends twice its tick, so at any length worth seeing it
# was landing on the glyph. Moving the block in splits the difference — 0.25
# clear above the glyph, 0.25 below the last row — and lets the tick go to 0.30,
# which is a mark a reader can find rather than a dash on the boundary.
SYN_INNER_PLANET_GLYPH_Y = 22.68
SYN_INNER_DEGREES_Y = 26.12
SYN_INNER_SIGN_Y = 29.06
SYN_INNER_MINUTES_Y = 31.67
SYN_INNER_RX_Y = 33.84

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

# The two stations reuse that same marker row. They can: a body at a station
# is turning, and the classification treats "about to turn" and "moving
# backwards" as one question with one answer, so the two markers are mutually
# exclusive and the row's reserved ink is unchanged. Both labels are two
# characters wide, like RX, so the measured separation model still holds.
# Dash pattern for a separating aspect line, in the aspect group's own units
# (that group carries a 0.37 scale, so these are not wheel units). Sized
# against the 0.25 stroke so the gaps read as deliberate rather than as a
# rendering artefact.
#: Size the house numbers are drawn at, in the wheel's 100-unit frame.
HOUSE_NUMBER_FONT_SIZE = 1.5

SEPARATING_DASH_ARRAY_SCALED = "1.5 1"

def motion_marker(point: KerykeionPointModel, show_motion_state: bool = False) -> Optional[str]:
    """Label for *point*'s marker row, or ``None`` when the row stays empty.

    A named station wins over plain retrograde: it is the rarer and more
    specific event, and the reader who turned the option on turned it on to
    see exactly this. Both the renderer and the separation model call it, so
    the reserved width can never disagree with the drawn text.
    """
    if show_motion_state:
        station = STATION_LABELS.get(getattr(point, "motion_state", None) or "")
        if station is not None:
            return station
    return RETROGRADE_LABEL if point.retrograde is True else None

# Kept as the name the modern renderer and its measurement harness use; the
# stack itself is chart-wide and lives with the other shared chart constants.
MODERN_TEXT_FONT_FAMILY = CHART_TEXT_FONT_FAMILY

# Below this display offset from the true position, the indicator is drawn as
# a straight tick instead of a tether arc. Shared with the displacement report
# so its "straight" column counts the same population the renderer draws.
STRAIGHT_TETHER_THRESHOLD = 0.5

# The natal tether at medium: the defaults _draw_indicator_line falls back to
# when a ring passes no indicator_config — which is what the natal medium
# profile does (indicator=None). Named constants rather than signature
# literals so the profile derivation reads the SAME numbers the renderer
# draws with, and _MEASURED_GEOMETRY can pin them: change either and the
# small/large natal profiles must be re-derived, not just the medium render.
NATAL_INDICATOR_TICK = 1.075
NATAL_INDICATOR_ARC_DROP = 1.0  # r(ruler edge) - arc_radius

# Natal cluster row positions (Y in the wheel-local frame; radius = CENTER - y).
# The single source for the renderer, the content-aware profiles, and the row
# radii — the dual rings have their own SYN_* equivalents below.
# The glyph row sits nearest the graduated ruler, and two things share that
# margin with it: the reading below and the indicator's tab, the little tick the
# displaced-planet tether drops inward from the ruler. At the +20% glyph size
# it left 0.41 to the tab — under a quarter of any other gap in the cluster, so
# the two touched on screen — while opening 2.43 down to the degrees, the widest
# gap of the four when the rows below run 2.03 and 1.99. Moving the row 0.90
# inward spends the wrong margin on the right one: 1.31 to the tab, 1.53 to the
# degrees. That leaves the glyph the tightest row of the cluster, which is
# deliberate and Giacomo's call — it is also the largest mark, and a big shape
# carries a closer neighbour than a line of digits does.
#
# Radius falls with the move, so the glyph covers slightly more degrees of arc
# than it did further out. It does not bind: at the shipped separations the
# tight pair is always text against text, and the glyph row still has room.
# Then 0.65 further in again, and the degrees 0.40 with it. A glyph is drawn
# upright inside an axis-aligned box while the tether that points at it runs
# along the cluster's own radius, and a radius that meets that box on the
# diagonal reaches the corner — 2.66 units out for the widest symbol against the
# 2.15 the row was placed for. The tether was ending inside the glyph on any
# cluster sitting near 45 degrees, which is most of them on a crowded wheel.
#
# Only these two rows move. The sign, the minutes and the retrograde mark stay:
# they are nowhere near the ruler, and moving them would spend the balance
# between the rows for a clearance problem that only exists at the top.
NATAL_PLANET_GLYPH_Y = 10.22
# Degrees and sign are nudged off their round numbers to even out the air the
# reader actually sees. Measured on the rendered ink of nine clusters (the
# rasterised difference between the wheel and the same wheel without that
# cluster), the three gaps ran 1.86 / 1.35 / 1.95: the sign sat almost against
# the degrees while the rows either side had half a unit more. The row centres
# are evenly spaced, but the ink inside them is not — a sign glyph inks a thin
# band high in its 32-unit box, a line of digits fills most of its own. Moving
# the degrees 0.14 out and the sign 0.23 in brings all three to 1.72.
NATAL_DEGREES_Y = 14.21
NATAL_SIGN_Y = 17.89
NATAL_MINUTES_Y = 21.89
NATAL_RX_Y = 25.25

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
#
# Re-measured after the dual rings took the natal treatment: bigger glyph,
# bigger degrees, one size for both wheels. Ink now touches at 5.25° outside and
# 8.25° inside, against 5.00° and 6.25° before, so the inner ceiling had to rise
# from 7.5 — which the enlargement had left below the point where its own
# degrees text overlaps. The outer one already stood where it needed to.
SYN_OUTER_MIN_SEPARATION = 5.75
SYN_INNER_MIN_SEPARATION = 9.0

# Dual chart element sizes — smaller than natal to fit in narrower rings, but
# not by as much as they used to be. The glyph and the degrees are what a reader
# goes to first, and at 0.115 / 1.9 they were the two hardest things on the
# drawing to make out; the minutes and the retrograde mark are what a reader
# consults after, so they give the room back.
#
# One size for both rings. The inner ring used to draw everything smaller again
# — 0.095 and 1.6 — on the reasoning that its radius is shorter, and the effect
# was that the same planet looked like two different weights of information
# depending on whose wheel it was in. Room was never the constraint: with the
# rows placed by their ink both rings clear 1.27 units between every pair, and
# the inner ring has the deeper margin of the two.
SYN_PLANET_SCALE = 0.132  # Planet glyph, both rings
SYN_PLANET_SCALE_INNER = SYN_PLANET_SCALE
SYN_DEGREES_FONT_SIZE = 2.12  # Degrees text, both rings
SYN_DEGREES_FONT_SIZE_INNER = SYN_DEGREES_FONT_SIZE
SYN_SIGN_SCALE = 0.062  # Zodiac sign
SYN_MINUTES_FONT_SIZE = 1.22  # Minutes text
SYN_RX_FONT_SIZE = 1.02  # Retrograde indicator

# Colors — use CSS custom properties to inherit from the active theme.
# Each theme CSS file can define --kerykeion-modern-* overrides.
# Fallback hex values provide a clean neutral default (works when no CSS is present).
COLOR_BACKGROUND = "var(--kerykeion-chart-color-paper-1, #ffffff)"
COLOR_PLANET_RING = "var(--kerykeion-modern-planet-ring, #e8e8ed)"
COLOR_OUTER_PLANET_RING = "var(--kerykeion-modern-planet-ring-outer, #d8d9e4)"
COLOR_HOUSE_RING = "var(--kerykeion-modern-house-ring, #d5d5dd)"
COLOR_STROKE = "var(--kerykeion-modern-stroke, #b0b0bf)"
# A house or sector boundary is read, not merely seen: it says where one house
# ends and the next begins, so WCAG 1.4.11 asks 3:1 of it. The ring outlines
# that share COLOR_STROKE are decoration and stay as pale as the palette likes.
# The fallback chain keeps a hand-written theme that only knows the old variable
# working exactly as before.
#
# One known exception, taken deliberately. An angle's cluster sits on its own
# cusp by construction, so the reading "As 19º ♈ 45'" is always laid across the
# angular line — and a line at 3:1 from the ring is a mid tone, which caps any
# ink resting on it at 5.5:1 in the light theme and 4.2:1 in the dark one. No
# colour clears the 7:1 the rest of the text carries: the ink that wins on the
# line loses on the ring, since the two grounds pull opposite ways. Measured
# alternatives (repainting the angles, haloing the text, breaking the line
# behind it) were rendered and rejected on Giacomo's reading: the axis is to
# stay exactly as drawn, whole and plainly visible. So the crossing keeps the
# contrast it has, and this note is the record of the trade rather than a gap
# nobody noticed.
COLOR_CUSP = "var(--kerykeion-modern-cusp, var(--kerykeion-modern-stroke, #81818d))"
COLOR_TEXT = "var(--kerykeion-chart-color-paper-0, #333333)"
COLOR_RETROGRADE = "var(--kerykeion-modern-retrograde, #c43a5e)"
COLOR_STATIONARY = "var(--kerykeion-modern-stationary, #c07c1e)"
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
# GLYPH-SIZE PROFILES
# =============================================================================

#: Page scale the full-chart template applies to the 100-unit modern wheel:
#: chart.xml draws it at 2 * main_radius = 480px, so one wheel unit is 4.8px
#: at the default page. Named here because classic parity is stated through it:
#: the large profiles' planet base is written as classic_scale / (0.92 * 4.8).
MODERN_PAGE_SCALE = 4.8

#: Shortest tab a tether may draw. The tab scales with the cluster's air, and
#: below a quarter unit it is under 1.2px at the default page — a stray dot,
#: not a mark a reader can find. When the floor binds, the profile derivation
#: pins the tab and pays the difference out of the remaining air instead.
MIN_INDICATOR_TICK = 0.25


@dataclass(frozen=True)
class ClusterProfile:
    """One planet ring's cluster — sizes, row anchors, spacing — at one glyph size.

    The five sizes and the five rows are the same ten numbers the renderer has
    always read; the profile only gathers them so the wheel can be asked for at
    more than one size. The ``medium`` entries REFERENCE the module constants
    rather than restating them: the default path reads the very floats it read
    before profiles existed, which is what keeps every existing baseline
    byte-identical — and what lets ``test_measured_geometry_is_unchanged`` keep
    guarding the profiles without knowing they exist.

    ``indicator`` is the tether geometry (``start_y`` / ``tick_length`` /
    ``arc_radius``), or ``None`` for a ring whose call site passes nothing and
    leaves ``_draw_indicator_line`` on its own defaults — which is what the
    natal ring has always done, so its medium entry keeps the
    ``if indicator_config:`` branch falsy exactly as before.
    """

    planet_scale_base: float
    degrees_font_size: float
    sign_scale_base: float
    minutes_font_size: float
    rx_font_size: float
    glyph_y: float
    degrees_y: float
    sign_y: float
    minutes_y: float
    rx_y: float
    min_separation: float
    indicator: Optional[dict] = None

    def scale_config(self) -> dict:
        """The five element sizes, keyed as ``_draw_planet_ring`` reads them."""
        return {
            "planet_scale_base": self.planet_scale_base,
            "degrees_font_size": self.degrees_font_size,
            "sign_scale_base": self.sign_scale_base,
            "minutes_font_size": self.minutes_font_size,
            "rx_font_size": self.rx_font_size,
        }

    def planet_y_config(self) -> dict:
        """The five row anchors, keyed as ``_draw_planet_ring`` reads them."""
        return {
            "glyph_y": self.glyph_y,
            "degrees_y": self.degrees_y,
            "sign_y": self.sign_y,
            "minutes_y": self.minutes_y,
            "rx_y": self.rx_y,
        }

    def indicator_config(self) -> Optional[dict]:
        """A fresh copy of the tether geometry, or None for the natal default.

        A copy for the same reason the two methods above build fresh dicts:
        the profiles are module singletons, and handing the renderer the
        stored dict itself would let any caller's mutation poison every
        later render process-wide.
        """
        return dict(self.indicator) if self.indicator is not None else None


_MEDIUM_NATAL = ClusterProfile(
    planet_scale_base=PLANET_SCALE_BASE,
    degrees_font_size=DEGREES_FONT_SIZE,
    sign_scale_base=SIGN_SCALE_BASE,
    minutes_font_size=MINUTES_FONT_SIZE,
    rx_font_size=RX_FONT_SIZE,
    glyph_y=NATAL_PLANET_GLYPH_Y,
    degrees_y=NATAL_DEGREES_Y,
    sign_y=NATAL_SIGN_Y,
    minutes_y=NATAL_MINUTES_Y,
    rx_y=NATAL_RX_Y,
    min_separation=PLANET_MIN_SEPARATION,
    indicator=None,
)

_MEDIUM_DUAL_OUTER = ClusterProfile(
    planet_scale_base=SYN_PLANET_SCALE,
    degrees_font_size=SYN_DEGREES_FONT_SIZE,
    sign_scale_base=SYN_SIGN_SCALE,
    minutes_font_size=SYN_MINUTES_FONT_SIZE,
    rx_font_size=SYN_RX_FONT_SIZE,
    glyph_y=SYN_OUTER_PLANET_GLYPH_Y,
    degrees_y=SYN_OUTER_DEGREES_Y,
    sign_y=SYN_OUTER_SIGN_Y,
    minutes_y=SYN_OUTER_MINUTES_Y,
    rx_y=SYN_OUTER_RX_Y,
    min_separation=SYN_OUTER_MIN_SEPARATION,
    indicator={
        "start_y": SYN_INDICATOR_OUTER_START_Y,
        "tick_length": SYN_INDICATOR_OUTER_TICK,  # inward, toward its own cluster
        "arc_radius": SYN_INDICATOR_OUTER_ARC_R,
    },
)

_MEDIUM_DUAL_INNER = ClusterProfile(
    planet_scale_base=SYN_PLANET_SCALE_INNER,
    degrees_font_size=SYN_DEGREES_FONT_SIZE_INNER,
    sign_scale_base=SYN_SIGN_SCALE,
    minutes_font_size=SYN_MINUTES_FONT_SIZE,
    rx_font_size=SYN_RX_FONT_SIZE,
    glyph_y=SYN_INNER_PLANET_GLYPH_Y,
    degrees_y=SYN_INNER_DEGREES_Y,
    sign_y=SYN_INNER_SIGN_Y,
    minutes_y=SYN_INNER_MINUTES_Y,
    rx_y=SYN_INNER_RX_Y,
    min_separation=SYN_INNER_MIN_SEPARATION,
    indicator={
        "start_y": SYN_INDICATOR_INNER_START_Y,
        "tick_length": SYN_INDICATOR_INNER_TICK,  # inward, toward its own cluster
        "arc_radius": SYN_INDICATOR_INNER_ARC_R,
    },
)

# The small and large profiles below are OUTPUT, not opinion: they are what
# ``scripts/derive_modern_cluster_profiles.py`` prints, and a test re-runs the
# derivation and refuses any hand edit that drifts from it. The one exception
# is min_separation, which no formula owns: each value below is MEASURED, by
# ``scripts/measure_modern_separation.py --glyph-size <size>`` under the same
# policy the medium constants embody — the first separation from which every
# larger one keeps at least 0.25 wheel units of daylight between adversarial
# worst-content clusters (the harness's "0.25 units" column). Touch floors per
# size live in tests/core/test_modern_decluttering.py::_TOUCHING_SEPARATION. The rule, in one
# line: sizes scale by k, every quantity of air scales by a = min(k, fit), rows
# are laid top-down from the tether's end, and the tab never drops below
# MIN_INDICATOR_TICK. Small is k = 0.9 — a pure homothety, the medium cluster
# at 90%. Large is classic parity, Giacomo's call on both counts: the planet
# glyph at the classic engine's own size (scale 1.0 single, 0.8 dual, through
# the 0.92 wrapper and the 4.8 page), written as that expression so the parity
# is exact and not a rounded decimal. On the dual rings the factors SPLIT at
# large: parity is the glyph's contract alone (×1.372), while the reading —
# degrees, sign, minutes, ℞ — stays at the MEDIUM size (k_text = 1.0),
# Giacomo's pick on a rendered four-way comparison: the dual cluster is
# text-heavy by construction (reading at 0.67 of its glyph against the natal
# 0.51) and every larger ramp read oversized in the dual rings' packed
# context. A large dual wheel grows its glyphs to classic parity and keeps
# the reading it always had — which also hands the air back: the single ring
# affords large at a = 0.65, the dual rings at a = 0.78 / 0.72. The bands
# cannot deepen: below the dual rings there is only the aspect core, and
# taking depth from it was considered and refused.
# Every derived cluster also slides 0.3 units OUTWARD, toward its indicator
# (Giacomo's call: the ℞ row must not sit on the ring's inner edge, and the
# tether side has the slack) — the END tab shortens with it so the tab-to-
# glyph distance holds, floored at MIN_INDICATOR_TICK and capped where the
# floor binds so the tab never reaches the glyph's ink. The VISIBLE dash
# (start_tick_length: the straight tether's body, and the arc case's mark at
# the true position) keeps its rule length — a dash cut to the floor read as
# a stray dot, Giacomo's second call on the rendered wheel. Medium does not
# move.

_SMALL_NATAL = ClusterProfile(
    planet_scale_base=0.163296,
    degrees_font_size=2.016,
    sign_scale_base=0.092781,
    minutes_font_size=1.8648,
    rx_font_size=1.6128,
    glyph_y=9.4328,
    degrees_y=13.0238,
    sign_y=16.3358,
    minutes_y=19.9358,
    rx_y=22.9598,
    min_separation=6.75,
    indicator={
        "start_y": HOUSE_LINE_OUTER_Y,
        "tick_length": 0.6675,
        "start_tick_length": 1.075,
        "arc_radius": 43.752,
    },
)

_SMALL_DUAL_OUTER = ClusterProfile(
    planet_scale_base=0.1188,
    degrees_font_size=1.908,
    sign_scale_base=0.0558,
    minutes_font_size=1.098,
    rx_font_size=0.918,
    glyph_y=7.7768,
    degrees_y=10.8728,
    sign_y=13.5188,
    minutes_y=15.8678,
    rx_y=17.8208,
    min_separation=5.0,
    indicator={
        "start_y": SYN_INDICATOR_OUTER_START_Y,
        "tick_length": 0.33,
        "start_tick_length": 0.5769,
        "arc_radius": 44.022,
    },
)

_SMALL_DUAL_INNER = ClusterProfile(
    planet_scale_base=0.1188,
    degrees_font_size=1.908,
    sign_scale_base=0.0558,
    minutes_font_size=1.098,
    rx_font_size=0.918,
    glyph_y=22.3441,
    degrees_y=25.4401,
    sign_y=28.0861,
    minutes_y=30.4351,
    rx_y=32.3881,
    min_separation=8.0,
    indicator={
        "start_y": SYN_INDICATOR_INNER_START_Y,
        "tick_length": MIN_INDICATOR_TICK,  # the shift is capped here: 0.05 to the glyph ink
        "arc_radius": 29.23,
    },
)

_LARGE_NATAL = ClusterProfile(
    planet_scale_base=1.0 / (ZODIAC_BG_SCALE * MODERN_PAGE_SCALE),
    degrees_font_size=2.79567,
    sign_scale_base=0.128663,
    minutes_font_size=2.585995,
    rx_font_size=2.236536,
    glyph_y=9.8551,
    degrees_y=14.2798,
    sign_y=18.0845,
    minutes_y=22.0458,
    rx_y=25.3815,
    min_separation=9.5,
    indicator={
        "start_y": HOUSE_LINE_OUTER_Y,
        "tick_length": 0.3959,
        "start_tick_length": 1.0224,
        "arc_radius": 44.0046,
    },
)

# The large dual reading IS the medium reading — Giacomo's pick on a rendered
# four-way comparison — so the four text sizes REFERENCE the SYN_* constants,
# the same referenced-not-retyped virtue the medium profiles carry: only the
# glyph chases classic parity.
_LARGE_DUAL_OUTER = ClusterProfile(
    planet_scale_base=0.8 / (ZODIAC_BG_SCALE * MODERN_PAGE_SCALE),
    degrees_font_size=SYN_DEGREES_FONT_SIZE,
    sign_scale_base=SYN_SIGN_SCALE,
    minutes_font_size=SYN_MINUTES_FONT_SIZE,
    rx_font_size=SYN_RX_FONT_SIZE,
    glyph_y=8.6024,
    degrees_y=12.3607,
    sign_y=15.0559,
    minutes_y=17.3951,
    rx_y=19.3375,
    min_separation=7.5,  # measured — the parity glyph is the binding row now
    indicator={
        "start_y": SYN_INDICATOR_OUTER_START_Y,
        "tick_length": MIN_INDICATOR_TICK,
        "start_tick_length": 0.4567,
        "arc_radius": 44.1037,
    },
)

_LARGE_DUAL_INNER = ClusterProfile(
    planet_scale_base=0.8 / (ZODIAC_BG_SCALE * MODERN_PAGE_SCALE),
    degrees_font_size=SYN_DEGREES_FONT_SIZE_INNER,
    sign_scale_base=SYN_SIGN_SCALE,
    minutes_font_size=SYN_MINUTES_FONT_SIZE,
    rx_font_size=SYN_RX_FONT_SIZE,
    glyph_y=23.1094,
    degrees_y=26.8099,
    sign_y=29.4375,
    minutes_y=31.7019,
    rx_y=33.5815,
    min_separation=11.5,  # measured — the parity glyph is the binding row now
    indicator={
        "start_y": SYN_INDICATOR_INNER_START_Y,
        "tick_length": MIN_INDICATOR_TICK,  # the floor binds; the corner budget gives the dash nothing either
        "arc_radius": 29.283,
    },
)

#: Every cluster profile the renderer can draw, by glyph size and ring.
#: Keyed by plain strings on purpose: ``draw_modern`` stays importable without
#: ``kerykeion.schemas``, and the drawer — the public gate — validates the size
#: before it ever reaches this dict.
GLYPH_SIZE_PROFILES: dict[str, dict[str, ClusterProfile]] = {
    "small": {
        "natal": _SMALL_NATAL,
        "dual_outer": _SMALL_DUAL_OUTER,
        "dual_inner": _SMALL_DUAL_INNER,
    },
    "medium": {
        "natal": _MEDIUM_NATAL,
        "dual_outer": _MEDIUM_DUAL_OUTER,
        "dual_inner": _MEDIUM_DUAL_INNER,
    },
    "large": {
        "natal": _LARGE_NATAL,
        "dual_outer": _LARGE_DUAL_OUTER,
        "dual_inner": _LARGE_DUAL_INNER,
    },
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

    # A cusp's reading is not one string but a spread: minutes at -4.67°, the
    # sign glyph on the line, degrees at +4.67°, so each one occupies about
    # thirteen degrees of ring. Two cusps closer together than that interleave —
    # with Campanus at Liverpool four of the twelve houses are under eight
    # degrees wide, so their readings printed through each other by construction
    # rather than by bad luck.
    #
    # The ring answers by resizing itself rather than by the readings stepping
    # aside from their own cusps. Moving them was tried and reads worse: a
    # number that has slid two degrees off the line it describes is a number
    # attached to the wrong house, and on a quadrant chart the eye has nothing
    # else to go on. Smaller text on a crowded chart still says exactly what it
    # belongs to.
    #
    # One factor for all twelve, not per-cusp: a ring of readings at four
    # different sizes looks like a mistake even when each one is individually
    # correct.
    #
    # Shrinking is the first answer and, past a point, the wrong one — four
    # degrees of house would take the text below legibility. So it stops at the
    # scale where a second device takes over: the crowded readings alternate
    # between two radial lanes, one a little nearer the rim and the next a
    # little nearer the wheel, and two that cannot be pulled apart sideways
    # simply pass each other. What each reading then has to clear is not its
    # neighbour — that one is on the other lane — but the one two cusps along,
    # which is two gaps away rather than one.
    #
    # Hence the three cases below, in the order a chart meets them: room enough
    # already; not enough, but a modest shrink is all it takes; or crowded past
    # that, where the ring stops at the largest size two lanes physically fit
    # and lets the stagger finish the job. Only the last of the three still has
    # a floor, for skies no arrangement can fix.
    angles = [_zodiac_to_wheel_angle(house.abs_pos, seventh_house_degree_ut) for house in houses]
    count = len(angles)
    # The same correction, and for the twelve it is `house_spans` that knows: it
    # reads the direction from all of them at once and returns each wedge's real
    # width, whichever way the ring runs.
    if count > 1:
        gaps = house_spans(angles)[0] if count == 12 else [
            abs(((angles[(i + 1) % count] - angles[i] + 180.0) % 360.0) - 180.0)
            for i in range(count)
        ]
    else:
        gaps = [360.0]
    nominal_span = _cusp_cluster_span(1.0)
    shrink_alone = min(gaps) / nominal_span

    if shrink_alone >= 1.0:
        fit = 1.0
    elif shrink_alone >= CUSP_STAGGER_SCALE:
        fit = shrink_alone
    else:
        two_gaps = min(gaps[i] + gaps[(i + 1) % count] for i in range(count))
        fit = min(CUSP_STAGGER_SCALE, max(CUSP_MIN_SCALE, two_gaps / nominal_span))

    # Rounded, not formatted to a fixed width: at full size these have to come
    # out as the very strings the nominal constants produce, or every chart with
    # a cusp ring shows a diff for a number that did not change.
    font_size = round(CUSP_FONT_SIZE * fit, 4)
    text_offset = CUSP_TEXT_OFFSET_DEGREES * fit
    glyph_scale = round(CUSP_GLYPH_SCALE * fit, 4)

    # Which readings stagger is decided at the size they end up drawn, and only
    # the ones that would otherwise print through a neighbour move: everything
    # with clear air either side stays on the centre line where it belongs.
    lanes = _cusp_lanes(angles, _cusp_cluster_span(fit))

    for house, cusp_angle, lane in zip(houses, angles, lanes):
        label_y = CUSP_LABEL_Y if lane is None else round(
            CUSP_LABEL_Y + (CUSP_LANE_OFFSET if lane else -CUSP_LANE_OFFSET), 4
        )

        # Determine if a full zodiac sign boundary falls in this house
        # Place sign glyph at the house cusp
        # (typed str: the intercepted-signs pass below reuses the variable with
        # plain-str ids from _ZODIAC_SIGN_IDS)
        sign_abbrev: str = house.sign
        degrees = int(house.position)
        minutes = int((house.position - degrees) * 60)

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
                f'x="{CENTER}" y="{label_y}" font-size="{font_size}" fill="{COLOR_TEXT}" '
                f'font-weight="500" '
                f'transform="rotate({-text_offset:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright + text_offset:.6f} {CENTER} {label_y})">'
                f"{minutes}'</text>\n"
            )

            # Sign glyph
            final_scale = round(glyph_scale * ZODIAC_OUTER_SCALE_MAP.get(sign_abbrev, 1.0), 4)
            parts.append(
                f'    <g transform="translate({CENTER} {label_y}) rotate({angle_upright:.6f}) scale({final_scale}) translate(-16 -16)">\n'
                f'      <use xlink:href="#{sign_abbrev}" fill="{COLOR_TEXT}" />\n'
                f"    </g>\n"
            )

            # Degrees text
            parts.append(
                f'    <text text-anchor="middle" dominant-baseline="middle" '
                f'x="{CENTER}" y="{label_y}" font-size="{font_size}" fill="{COLOR_TEXT}" '
                f'font-weight="500" '
                f'transform="rotate({text_offset:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright - text_offset:.6f} {CENTER} {label_y})">'
                f"{degrees}º</text>\n"
            )
        else:
            # Alternate layout for lower half (mirrored text order)
            # Minutes text
            parts.append(
                f'    <text text-anchor="middle" dominant-baseline="middle" '
                f'x="{CENTER}" y="{label_y}" font-size="{font_size}" fill="{COLOR_TEXT}" '
                f'font-weight="500" '
                f'transform="rotate({text_offset:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright - text_offset:.6f} {CENTER} {label_y})">'
                f"{minutes}'</text>\n"
            )

            # Sign glyph
            final_scale = round(glyph_scale * ZODIAC_OUTER_SCALE_MAP.get(sign_abbrev, 1.0), 4)
            parts.append(
                f'    <g transform="translate({CENTER} {label_y}) rotate({angle_upright:.6f}) scale({final_scale}) translate(-16 -16)">\n'
                f'      <use xlink:href="#{sign_abbrev}" fill="{COLOR_TEXT}" />\n'
                f"    </g>\n"
            )

            # Degrees text
            parts.append(
                f'    <text text-anchor="middle" dominant-baseline="middle" '
                f'x="{CENTER}" y="{label_y}" font-size="{font_size}" fill="{COLOR_TEXT}" '
                f'font-weight="500" '
                f'transform="rotate({-text_offset:.6f} {CENTER} {CENTER}) '
                f'rotate({angle_upright + text_offset:.6f} {CENTER} {label_y})">'
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
                final_scale = round(glyph_scale * ZODIAC_OUTER_SCALE_MAP.get(sign_abbrev, 1.0), 4)

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
    show_motion_state: bool = False,
) -> dict[str, tuple[float, float]]:
    """Ink reach ``(half_width, half_height)`` of each cluster row of *point*.

    This is what the content-aware separation works from: a planet at 4º07'
    reserves the ink of ``"4º"`` and ``"7'"``, not of the widest strings the
    rows could ever hold, and the marker row exists only when the point
    actually carries a marker. All values come from the browser-measured tables in
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
    marker = motion_marker(point, show_motion_state)
    if marker is not None:
        profile["rx"] = _text_ink_reach(marker, rx_font_size)
    return profile

#: Fixed iteration count for the wraparound fallback's 1-D convex search.
#: Deterministic and precise far beyond the 1e-6 the placement needs.
_WRAP_SEARCH_ITERATIONS = 200

#: Bisection steps for the clearance an over-subscribed wheel can still afford.
#: 40 halvings take the interval below a millionth of a wheel unit — far past
#: anything a renderer can draw, and cheap: each step is one pass over the pairs.
_CLEARANCE_SEARCH_ITERATIONS = 40

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

    def required_separation(
        first: dict, second: dict, pair_mid_angle: float, air: Optional[float] = None
    ) -> float:
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
            clearance=clearance if air is None else air,
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

    # ── The air yields before the positions do ──────────────────────────
    # Every pair asks for its ink plus `clearance` of daylight, and on a full
    # wheel the sum of those asks can exceed what a circle has. `place` handles
    # that by scaling every separation down together, which compresses the ink
    # reservations — so clusters overlap AND land far from their true degrees:
    # at 52 points the worst was 35 degrees out before any of this.
    #
    # But the two things being compressed are not worth the same. The ink
    # reservation is what keeps a reading legible; the clearance on top of it is
    # air, and air is the cheaper thing to spend. So when the wheel is
    # over-subscribed, give up the clearance first — as much of it as it takes,
    # down to none — and only then let `place` fall back to compressing what is
    # left. Uncrowded wheels never reach this: the default fourteen points ask
    # for about a quarter of the budget, and nothing here moves them.
    #
    # Solved once, on the true orientations, so the refinement below still has a
    # fixed clearance to ratchet against and still provably converges.
    effective_clearance = clearance

    def total_demand(air: float) -> float:
        pairs = zip(zip(ordered, ordered[1:]), mid_angles)
        return sum(
            required_separation(planet, follower, mid, air) for (planet, follower), mid in pairs
        ) + required_separation(ordered[-1], ordered[0], mid_angles[-1], air)

    if row_radii is not None and total_demand(clearance) > FEASIBLE_TOTAL_DEGREES:
        # Demand rises monotonically with the air asked for, so the largest
        # clearance that still fits is a bisection away. Zero is always feasible
        # to *ask* for; whether the ink itself fits is `place`'s problem.
        too_much, enough = clearance, 0.0
        for _ in range(_CLEARANCE_SEARCH_ITERATIONS):
            trial = (enough + too_much) / 2.0
            if total_demand(trial) > FEASIBLE_TOTAL_DEGREES:
                too_much = trial
            else:
                enough = trial
        effective_clearance = enough
        logger.info(
            "Modern decluttering: %d points ask for more arc than the wheel has; "
            "the air between clusters was reduced from %.2f to %.2f wheel units so "
            "the points could stay nearer their true degrees.",
            n,
            clearance,
            effective_clearance,
        )

    pair_requirements = [
        required_separation(planet, follower, mid, effective_clearance)
        for (planet, follower), mid in zip(zip(ordered, ordered[1:]), mid_angles)
    ]
    wrap_requirement = required_separation(ordered[-1], ordered[0], mid_angles[-1], effective_clearance)
    requirements_settled = False
    for _ in range(_ORIENTATION_REFINEMENT_ROUNDS):
        display_positions = place(pair_requirements, wrap_requirement)
        mid_angles = pair_mid_angles(display_positions)
        refined = [
            max(current, required_separation(planet, follower, mid, effective_clearance))
            for current, (planet, follower), mid in zip(
                pair_requirements, zip(ordered, ordered[1:]), mid_angles
            )
        ]
        refined_wrap = max(
            wrap_requirement,
            required_separation(ordered[-1], ordered[0], mid_angles[-1], effective_clearance),
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
    tick_length: float = NATAL_INDICATOR_TICK,
    arc_radius: Optional[float] = None,
    planet_slug: str = "",
    abs_pos: Optional[float] = None,
    horoscope_id: Optional[str] = None,
    start_tick_length: Optional[float] = None,
) -> str:
    """
    Draw a tether/indicator line from a displaced planet to its true position.

    The indicator is a thin path from a starting position, with a small arc
    connecting to the display position if needed.

    Args:
        real_angle: True zodiacal angle of the planet.
        display_angle: Display angle after collision resolution.
        start_y: Y coordinate where the indicator line starts (default: the
                 ruler's inner edge, HOUSE_LINE_OUTER_Y).
        tick_length: Length and direction of the initial tick. Positive = downward,
                     negative = upward (default NATAL_INDICATOR_TICK).
        arc_radius: Radius for the connecting arc. If None, uses
                    R_PLANET_OUTER - NATAL_INDICATOR_ARC_DROP.
        planet_slug: Name of the celestial point (for kr:slug metadata).
        abs_pos: The owning ChartPoint's absolute position. Must be the SAME float
            the ChartPoint tag interpolates so the kr:absoluteposition strings are
            identical (downstream focus code matches them by string equality).
        horoscope_id: Owner subject id ("0"/"1") emitted as kr:horoscope in dual
            charts so the indicator can be tied to the correct ring.
        start_tick_length: Length of the INITIAL dash — the mark hanging from
            start_y at the true position (and the straight tether's whole
            body). None means tick_length, the historical behaviour. The two
            lengths split on the derived glyph sizes: the outward cluster
            shift shortens the END segment (whose reach the corner guard
            owns) while the visible dash keeps its rule length.

    Returns:
        SVG group string for the indicator line.
    """
    if arc_radius is None:
        arc_radius = R_PLANET_OUTER - NATAL_INDICATOR_ARC_DROP
    if start_tick_length is None:
        start_tick_length = tick_length

    slug_attr = f' kr:slug="{escape_svg_text(planet_slug)}"' if planet_slug else ""
    pos_attr = f' kr:absoluteposition="{abs_pos}"' if abs_pos is not None else ""
    horoscope_attr = f' kr:horoscope="{horoscope_id}"' if horoscope_id is not None else ""
    out = f'<g kr:node="Indicator"{slug_attr}{pos_attr}{horoscope_attr} transform="rotate(-{real_angle:.6f} {CENTER} {CENTER})">\n'

    angle_diff = wrap_180(display_angle - real_angle)

    if abs(angle_diff) < STRAIGHT_TETHER_THRESHOLD:
        # Simple straight indicator line
        out += (
            f'  <path d="M {CENTER} {start_y} l 0 {start_tick_length}" '
            f'fill="transparent" stroke="{COLOR_INDICATOR}" stroke-width="0.1"/>\n'
        )
    else:
        # Line with arc to connect to displaced position
        r_arc = arc_radius
        sweep = 0 if angle_diff > 0 else 1

        # The initial dash must MEET the arc it hands off to: an A-segment
        # forced through a point off its own circle bends into a visible kink
        # (the derived sizes lengthened the dash for the straight case, where
        # there is no arc to meet — at medium all lengths coincided and the
        # question never arose). Cap the dash at the arc's depth, never below
        # the end tab's length, the historical minimum; at medium the cap is
        # exactly tick_length and the emitted bytes do not move.
        arc_start_tick = round(
            min(start_tick_length, max((CENTER - r_arc) - start_y, tick_length)), 4
        )

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
            f'd="M {CENTER} {start_y} l 0 {arc_start_tick} '
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
    clusters: Sequence[dict] = (),
    row_radii: Optional[dict[str, float]] = None,
    dim_stroke: str = COLOR_CUSP_DIM,
) -> str:
    """Draw 36 Gauquelin sector division lines through the planet ring.

    Replaces house division lines when Gauquelin mode is active.
    Angular sectors (1, 10, 19, 28) get thicker lines. Like the house cusps,
    a sector line dims where a reading is written across it.
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
        out += _cusp_line_svg(angle, stroke_w, line_outer_y, line_inner_y,
                              clusters, row_radii, dim_stroke)
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
    show_motion_state: bool = False,
    content_aware_separation: bool = True,
    cusp_dim_stroke: str = COLOR_CUSP_DIM,
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
            planet_entry["row_half_widths"] = _cluster_row_profile(
                point, show_motion_state=show_motion_state, **element_scales
            )
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

    # The cusps are drawn after the clusters are resolved, not before: a line
    # has to know what is written across it before it can step out of the way.
    # Nothing about the clusters changes — only the order the two are worked out
    # in, and the cusps still come first in the markup, under the readings.
    if gauquelin_sectors:
        out += _draw_gauquelin_division_lines(
            line_outer_y, line_inner_y, gauquelin_cusps=gauquelin_cusps,
            seventh_house_degree_ut=seventh_house_degree_ut,
            clusters=resolved, row_radii=row_radii, dim_stroke=cusp_dim_stroke)
    else:
        out += _draw_house_division_lines(
            houses, seventh_house_degree_ut, line_outer_y, line_inner_y,
            clusters=resolved, row_radii=row_radii, dim_stroke=cusp_dim_stroke)


    # Prepare indicator kwargs
    ind_kwargs = {}
    if indicator_config:
        ind_kwargs = {
            "start_y": indicator_config.get("start_y", HOUSE_LINE_OUTER_Y),
            "tick_length": indicator_config.get("tick_length", NATAL_INDICATOR_TICK),
            "arc_radius": indicator_config.get("arc_radius", None),
            "start_tick_length": indicator_config.get("start_tick_length", None),
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
            show_motion_state=show_motion_state,
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


def _text_ink_offset(text: str, font_size: float) -> float:
    """How far to slide *text* so its ink lands on the cluster's axis.

    ``dominant-baseline="middle"`` centres the em box, and an em box is not ink:
    digits have no descenders, so "16º" inks a whole native unit ABOVE where it
    is anchored — 0.22 wheel units at this size — while a glyph sits on its
    centre. A column of rows drawn as anchored therefore leans: glyphs on the
    axis, numbers beside it, which reads as a crooked skewer rather than as a
    mistake anyone can name.

    The offset is across the row, not along it: a reading is drawn upright while
    its column runs radially, so what pushes it off the skewer is the baseline
    and never the advance width. (Measuring the horizontal centre first, and
    correcting with it, moved every row along its own length and changed nothing
    at all.)

    Returns 0.0 for a string the tables have never seen, which is the honest
    answer: better a mark on its anchor than one moved by a guess.
    """
    return -TEXT_INK_CENTRE_Y.get(text, 0.0) / TEXT_INK_REFERENCE_FONT_SIZE * font_size


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
    show_motion_state: bool = False,
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
    marker = motion_marker(point, show_motion_state)
    # A station is the rarer event and takes the colour as well as the label:
    # a reader who asked to see stations should not have to tell one apart
    # from an ordinary retrograde by reading the two letters.
    if marker in STATION_LABELS.values():
        fill_color = COLOR_STATIONARY
    elif is_retro:
        fill_color = COLOR_RETROGRADE
    else:
        fill_color = color

    point_slug = point.name
    planet_id = point_slug if point.point_type == "House" else resolve_glyph_id(point_slug)

    retro_attr = ' kr:retrograde="true"' if is_retro else ""
    horoscope_attr = f' kr:horoscope="{horoscope_id}"' if horoscope_id else ""
    gauq = getattr(point, "gauquelin_sector", None)
    gauq_attr = f' kr:gauquelinsector="{gauq}"' if gauq is not None else ""
    state_attrs = point_state_attributes(point)

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
        f'kr:signposition="{point.position}" kr:slug="{escape_svg_text(point_slug)}"{retro_attr}{horoscope_attr}{gauq_attr}{state_attrs} '
        f'kr:cx="{glyph_cx}" kr:cy="{glyph_cy}" '
        f'transform="rotate(-{display_angle:.6f} {CENTER} {CENTER})">\n'
    )

    # Planet glyph (outermost, largest — near outer edge of planet ring)
    planet_scale = planet_scale_base * GLYPH_SCALE_MAP.get(planet_id, 1.0)
    out += (
        f'  <g transform="translate({CENTER} {glyph_y}) rotate({counter_rotation:.6f}) scale({planet_scale}) translate(-{PLANET_GLYPH_BOX / 2:g} -{PLANET_GLYPH_BOX / 2:g})">\n'
        f'    <use xlink:href="#{planet_id}" kr:slug="{escape_svg_text(point_slug)}" kr:node="Glyph" fill="{fill_color}" />\n'
        f"  </g>\n"
    )

    # Degrees text
    out += (
        f'  <text text-anchor="middle" dominant-baseline="middle" '
        f'x="{CENTER}" y="{degrees_y}" font-size="{degrees_font_size}" fill="{fill_color}" '
        f'font-weight="500" '
        f'transform="rotate({counter_rotation:.6f} {CENTER} {degrees_y}) translate(0 {_text_ink_offset(degrees_text, degrees_font_size):.4f})">{degrees_text}</text>\n'
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
        f'transform="rotate({counter_rotation:.6f} {CENTER} {minutes_y}) translate(0 {_text_ink_offset(minutes_text, minutes_font_size):.4f})">{minutes_text}</text>\n'
    )

    # Marker text (innermost — near inner edge of planet ring): RX for a plain
    # retrograde, SR/SD for a named station.
    if marker is not None:
        out += (
            f'  <text text-anchor="middle" dominant-baseline="middle" '
            f'x="{CENTER}" y="{rx_y}" '
            f'font-size="{rx_font_size}" fill="{fill_color}" '
            f'font-weight="500" '
            f'transform="rotate({counter_rotation:.6f} {CENTER} {rx_y}) translate(0 {_text_ink_offset(marker, rx_font_size):.4f})">{marker}</text>\n'
        )

    out += "</g>\n"
    return out


# =============================================================================
# HOUSE DIVISION LINES (shared between rings)
# =============================================================================


def _reading_span_on_line(
    line_angle: float,
    y_top: float,
    y_bottom: float,
    clusters: Sequence[dict],
    row_radii: dict[str, float],
) -> Optional[tuple[float, float]]:
    """The stretch of a cusp line that a cluster's reading lies across.

    A cusp runs radially while the readings stay upright for the reader, so
    which side of a mark faces the line changes with the angle: on the horizon
    the line runs the LENGTH of "As 19º ♈ 45'" and only the text's height keeps
    them apart, at the Midheaven it crosses the words and their width does. The
    projection ``half_w·|sin θ| + half_h·|cos θ|`` carries both, and every angle
    between; width alone makes a mark look narrow exactly where it is widest.

    All or nothing per reading: one row touching commits the whole cluster, from
    its first mark to its last. A stretch dimmed under some rows and solid under
    the others reads as a defect rather than as a decision.

    Returns ``None`` when no reading touches this segment — which is the common
    case, and is why an ordinary cusp is drawn in one piece.
    """
    spans: list[tuple[float, float]] = []
    for cluster in clusters:
        profile = cluster.get("row_half_widths")
        if not profile:
            continue
        angle = cluster["display_angle"]
        gap = abs((line_angle - angle + 180.0) % 360.0 - 180.0)
        if gap >= 90.0:  # the far side of the wheel: its sine is small for the
            continue     # wrong reason, and 180° away is not "close"
        here = []
        for row, (half_w, half_h) in profile.items():
            radius = row_radii.get(row)
            if radius is None:
                continue
            top, bottom = CENTER - radius - half_h, CENTER - radius + half_h
            if bottom > y_top and top < y_bottom:
                here.append((top, bottom, half_w, half_h, radius))
        if not here:
            continue
        theta = math.radians(angle)
        if any(abs(radius * math.sin(math.radians(gap)))
               <= half_w * abs(math.sin(theta)) + half_h * abs(math.cos(theta)) + CUSP_DIM_TOLERANCE
               for _, _, half_w, half_h, radius in here):
            spans.append((min(r[0] for r in here), max(r[1] for r in here)))
    if not spans:
        return None
    return (max(y_top, min(a for a, _ in spans) - CUSP_DIM_MARGIN),
            min(y_bottom, max(b for _, b in spans) + CUSP_DIM_MARGIN))


def _cusp_line_svg(
    cusp_angle: float,
    stroke_w: float,
    line_outer_y: float,
    line_inner_y: float,
    clusters: Sequence[dict] = (),
    row_radii: Optional[dict[str, float]] = None,
    dim_stroke: str = COLOR_CUSP_DIM,
) -> str:
    """One cusp line, dimmed over the stretch a reading is written across it.

    The line is never broken: the dimmed stretch is drawn in *dim_stroke*, the
    SOLID pre-composited tone of the cusp colour over this ring's fill, so the
    axis stays continuous and passes behind the words instead of through them
    — and stays visible on hosts that show through the chart, where a
    stroke-opacity dim used to vanish. Without clusters to consult — the
    measurement harness, a ring drawn before its points are resolved — it
    comes out whole, exactly as before.
    """
    y_top, y_bottom = sorted((line_outer_y, line_inner_y))
    head = f'<line x1="{CENTER}" y1="{{y1}}" x2="{CENTER}" y2="{{y2}}" '
    tail = (f'stroke="{{stroke}}" stroke-width="{stroke_w}" '
            f'transform="rotate(-{cusp_angle:.6f} {CENTER} {CENTER})"/>\n')

    span = (_reading_span_on_line(cusp_angle, y_top, y_bottom, clusters, row_radii)
            if clusters and row_radii else None)
    if span is None:
        return (head + tail).format(y1=line_outer_y, y2=line_inner_y, stroke=COLOR_CUSP)

    lo, hi = span
    pieces = []
    if lo > y_top + 0.05:
        pieces.append((y_top, lo, COLOR_CUSP))
    pieces.append((lo, hi, dim_stroke))
    if hi < y_bottom - 0.05:
        pieces.append((hi, y_bottom, COLOR_CUSP))
    return "".join((head + tail).format(y1=f"{a:.3f}", y2=f"{b:.3f}", stroke=stroke)
                   for a, b, stroke in pieces)


def _draw_house_division_lines(
    houses: list[KerykeionPointModel],
    seventh_house_degree_ut: float,
    line_outer_y: float = HOUSE_LINE_OUTER_Y,
    line_inner_y: float = HOUSE_LINE_INNER_Y,
    clusters: Sequence[dict] = (),
    row_radii: Optional[dict[str, float]] = None,
    dim_stroke: str = COLOR_CUSP_DIM,
) -> str:
    """
    Draw house division lines that cross the planet ring.

    Angular houses (1, 4, 7, 10) get thicker lines.

    Args:
        houses: List of 12 house KerykeionPointModel objects.
        seventh_house_degree_ut: 7th house cusp absolute degree.
        line_outer_y: Y coordinate for the outer end of lines (default 6.5).
        line_inner_y: Y coordinate for the inner end of lines (default 28.0).
        clusters: Resolved point clusters of this ring, so a line can step out
            of the way of a reading written across it. Empty draws whole lines.
        row_radii: Radius of each cluster row, matching *clusters*.

    Returns:
        SVG string with house division lines.
    """
    out = ""
    for i, house in enumerate(houses):
        house_num = i + 1
        cusp_angle = _zodiac_to_wheel_angle(house.abs_pos, seventh_house_degree_ut)
        stroke_w = ANGULAR_STROKE_WIDTH if house_num in ANGULAR_HOUSES else NORMAL_STROKE_WIDTH
        out += _cusp_line_svg(cusp_angle, stroke_w, line_outer_y, line_inner_y,
                              clusters, row_radii, dim_stroke)

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
            f'stroke="{COLOR_CUSP}" stroke-width="{stroke_w}" '
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
            f'stroke="{COLOR_CUSP}" stroke-width="{stroke_w}" '
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
    # Which way the houses run, read once from all twelve. Several quadrant
    # systems put them in descending order above the polar circle, and the
    # horizon system does it on the equator. The Gauquelin variant below is
    # always descending, by construction, and says so where it draws.
    wheel_angles = [
        _zodiac_to_wheel_angle(house.abs_pos, seventh_house_degree_ut) for house in houses[:12]
    ]
    spans, reversed_wedges = house_spans(wheel_angles)
    # Kept before the widening below rewrites them: these are the arcs the house
    # reader measures, and where the wedges overlap it is the reader the paint
    # order has to agree with.
    true_spans = list(spans)
    # A wedge narrower than the minimum is widened so it can be clicked at all,
    # and a widened wedge necessarily covers longitudes outside its own arc: on a
    # crossing ring where it is also the narrowest, it is painted on top and
    # answers for them. Polich/Page at 70.5N has an eleventh house 0.348 degrees
    # wide, so it answers for up to 0.652 degrees either side that the reader
    # gives its neighbour.
    #
    # Painting the widened ones underneath instead was tried and is worse: the
    # tenth house crosses the eleventh on that same ring, so the eleventh loses
    # its own middle and goes back to being unclickable, which is the defect the
    # widening exists for. No single paint order settles both. The slop is bounded
    # by the minimum width, and that is the trade.
    #
    # A click exactly ON a cusp is outside all of this: an SVG path is closed, so
    # both wedges that share a boundary contain it, and no linear order of twelve
    # cyclic wedges can give every cusp to the house it opens. The reader does —
    # it has an exact-on-cusp rule — so the two differ on a set of measure zero.
    # And any house too thin to click gets the same minimum the classic engine
    # gives it. This ring keeps its exact degrees, so nothing quantises two cusps
    # together here — but Campanus inside the polar circle brings two of them
    # arbitrarily close on its own: sweeping five latitudes between 67N and 69N at
    # five-minute steps, the closest pair measured 0.0002 degrees. That is a house
    # no pointer will ever find.
    wheel_angles, spans = separate_collapsed_wedges(
        wheel_angles, spans, reversed_wedges, MINIMUM_WEDGE_SPAN_DEGREES
    )
    sectors: list[str] = []
    for i in range(12):
        next_i = (i + 1) % 12
        house_num = i + 1

        a_start = wheel_angles[i]
        a_end = wheel_angles[next_i]
        span = spans[i]

        # The one case the separation above cannot repair: where the cusps cross
        # rather than merely run backwards, the twelve do not tile and there is no
        # width to trade between them. A wedge left at zero puts both ends of its
        # arc on one point, SVG drops the arc, and a path of no area is left
        # declaring pointer-events:all — a house that can never be clicked. So it
        # takes its degree and moves only its own end, overlapping the neighbour
        # it already overlaps. On a ring that tiles, this never fires.
        if span < MINIMUM_WEDGE_SPAN_DEGREES:
            span = MINIMUM_WEDGE_SPAN_DEGREES
            a_end = a_start + (-span if reversed_wedges[i] else span)

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

        # Angular span to determine large-arc flag. Both sweeps flip with the
        # direction: the endpoints are the same two points either way, and it is
        # the pair (sweep, large_arc) that says which of the two arcs between them
        # the wedge is.
        large_arc = 1 if span > 180 else 0
        outer_sweep, inner_sweep = (1, 0) if reversed_wedges[i] else (0, 1)

        d = (
            f"M {ox1:.6f},{oy1:.6f} "
            f"A {outer_r},{outer_r} 0 {large_arc},{outer_sweep} {ox2:.6f},{oy2:.6f} "
            f"L {ix2:.6f},{iy2:.6f} "
            f"A {inner_r},{inner_r} 0 {large_arc},{inner_sweep} {ix1:.6f},{iy1:.6f} Z"
        )

        sectors.append(
            f'<g kr:node="HouseSector" kr:house="{house_num}"{horoscope_attr}>'
            f'<path d="{d}" fill="transparent" stroke="none" pointer-events="all"/>'
            f"</g>\n"
        )

    # Widest first, so the narrowest is on top — the same rule the house reader
    # applies, and the one the classic engine now paints by. It matters only where
    # the wedges overlap, which is where the ring is not a house division: a point
    # under houses 7, 9 and 12 was answered as the twelfth by the wheel and the
    # ninth by the model. A ring that tiles is painted in house order, unchanged.
    if _wedges_overlap(true_spans, reversed_wedges):
        sectors = [
            sectors[index]
            for index in sorted(range(12), key=lambda index: (-true_spans[index], -index))
        ]

    return "".join(sectors)


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

        # Both sweeps flipped, because these cusps descend. Correcting the span
        # alone leaves the endpoints where they were and moves the arc onto the
        # mirrored circle SVG puts through any two points at a given radius —
        # measured on the gallery's Gauquelin charts, the thirty-six wedges sat
        # on circles up to 92 units from a wheel whose radius is 50. The classic
        # engine's twin has always used this pair; only this one did not.
        d = (
            f"M {ox1:.6f},{oy1:.6f} "
            f"A {outer_r},{outer_r} 0 {large_arc},1 {ox2:.6f},{oy2:.6f} "
            f"L {ix2:.6f},{iy2:.6f} "
            f"A {inner_r},{inner_r} 0 {large_arc},0 {ix1:.6f},{iy1:.6f} Z"
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

    # Quadrant house systems make sectors wildly unequal — Campanus does it at
    # Liverpool, Placidus inside the polar circle — and three or four numbers
    # then want the same few degrees of a ring only 14 to 21 units across. They
    # are spread by the least movement that separates them, which keeps a crowd
    # centred on the houses it belongs to instead of sliding it sideways.
    label_radius = CENTER - text_y
    # In the direction the houses run, which above the polar circle is not always
    # the direction the wheel angles increase in: read forwards, a six-degree
    # house measures 354 and its number is centred on the far side of the chart.
    wheel_angles = [
        _zodiac_to_wheel_angle(sector.abs_pos, seventh_house_degree_ut) for sector in houses[:12]
    ]
    ring_spans, ring_reversed = house_spans(wheel_angles)
    wanted = [
        _normalize_angle(
            wheel_angles[index] + (-0.5 if ring_reversed[index] else 0.5) * ring_spans[index]
        )
        for index in range(12)
    ]
    # The widest label the ring carries, measured at the size it is drawn. The
    # estimator scales with the font size and carries no unit of its own, so it
    # answers in the wheel's 100-unit frame here just as it answers in pixels
    # for the panel.
    label_width = estimate_text_width("12", HOUSE_NUMBER_FONT_SIZE)
    placed = spread_around_wheel(wanted, label_separation_degrees(label_width, max(label_radius, 0.1), gutter_px=0.3))

    for i, house in enumerate(houses):
        house_num = i + 1
        cusp_angle = _zodiac_to_wheel_angle(house.abs_pos, seventh_house_degree_ut)
        # Where the number goes, after spreading (see above).
        mid_angle_abs = placed[i]
        stroke_w = ANGULAR_STROKE_WIDTH if house_num in ANGULAR_HOUSES else NORMAL_STROKE_WIDTH

        # Divider line from house ring outer edge down to line_inner_radius
        house_line_y1 = CENTER - house_outer_r
        house_line_y2 = CENTER - line_inner_radius

        # Divider line at house boundary
        out += (
            f'<line x1="{CENTER}" y1="{house_line_y1}" '
            f'x2="{CENTER}" y2="{house_line_y2}" '
            f'stroke="{COLOR_CUSP}" stroke-width="{stroke_w}" '
            f'transform="rotate(-{cusp_angle:.6f} {CENTER} {CENTER})"/>\n'
        )

        # House number text centered in the sector
        if show_numbers:
            # Place at the absolute mid-angle, keep text upright
            angle_upright = 90 + mid_angle_abs
            out += (
                f'<g kr:node="HouseNumber" kr:house="{house_num}"{horoscope_attr}>'
                f'<text text-anchor="middle" dominant-baseline="middle" '
                f'x="{CENTER}" y="{text_y}" font-size="{HOUSE_NUMBER_FONT_SIZE}" fill="{COLOR_TEXT}" '
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
    show_aspect_movement: bool = False,
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
    aspect_scale = ASPECT_CORE_SCALE

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

        # Aspect line (drawn first so glyphs render on top). A separating
        # aspect is dashed only on request: the movement has always been in
        # the metadata, but drawing it changes how every existing chart looks.
        dash_attr = (
            f' stroke-dasharray="{SEPARATING_DASH_ARRAY_SCALED}"'
            if show_aspect_movement and str(movement).lower() == "separating"
            else ""
        )
        out += (
            f'  <line x1="{sx1:.6f}" y1="{sy1:.6f}" '
            f'x2="{sx2:.6f}" y2="{sy2:.6f}" '
            f'stroke="{color}" stroke-width="{ASPECT_LINE_WIDTH}"{dash_attr}/>\n'
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
                    f'  <g transform="translate({mx:.6f} {my:.6f}) rotate(90) '
                    f'scale({ASPECT_GLYPH_SCALE}) translate(-5 -5)">\n'
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
    show_motion_state: bool = False,
    show_aspect_movement: bool = False,
    gauquelin_sectors: bool = False,
    gauquelin_cusps: Optional[list[float]] = None,
    glyph_size: str = "medium",
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
        glyph_size: Which cluster profile to draw — "small", "medium" or
            "large" (see GLYPH_SIZE_PROFILES). The drawer validates the value;
            an unknown key raises here.

    Returns:
        Complete SVG content string for the modern horoscope.
    """
    # Orient the entire wheel so that 0° (Ascendant) is at 9 o'clock (LEFT)
    # The SVG initial orientation puts 0° at TOP. We rotate the whole group by -90°.
    # Non-default sizes stamp themselves on the root so a consumer holding only
    # the SVG (hit-area injection downstream, a saved file, a cached render) can
    # tell which profile drew it. Medium stays unstamped on purpose: the
    # attribute's absence IS the default, and the default render stays
    # byte-identical to every chart drawn before sizes existed.
    size_attr = "" if glyph_size == "medium" else f' kr:glyphsize="{glyph_size}"'
    out = (
        f'<g kr:node="ModernHoroscope"{size_attr} font-family="{MODERN_TEXT_FONT_FAMILY}" '
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
    profile = GLYPH_SIZE_PROFILES[glyph_size]["natal"]
    out += _draw_planet_ring(
        planets, planets_settings, seventh_house_degree_ut, houses,
        min_separation=profile.min_separation,
        planet_y_config=profile.planet_y_config(),
        indicator_config=profile.indicator_config(),
        scale_config=profile.scale_config(),
        gauquelin_sectors=gauquelin_sectors, gauquelin_cusps=gauquelin_cusps,
        show_zodiac_background_ring=show_zodiac_background_ring,
        show_motion_state=show_motion_state,
    )
    if gauquelin_sectors:
        out += _draw_gauquelin_house_ring(seventh_house_degree_ut, gauquelin_cusps=gauquelin_cusps)
    else:
        out += _draw_house_ring(houses, seventh_house_degree_ut, horoscope_id="0")
    # House sectors are click-only overlays and must not reach into the zodiac
    # background ring, or a click on a sign is intercepted by the house under it.
    # R_CUSP_OUTER is what does that, in both cases: when the ring is drawn these
    # overlays are already inside the scale(0.92) wrapper that shrinks the whole
    # chart to fit, so 50 here renders at 46 — exactly the ring's inner edge.
    # Passing R_ZODIAC_BG_INNER applied that scale a second time and stopped the
    # hit areas at a rendered 42.32, leaving 3.68 units of chart with no house
    # under the pointer at all.
    house_sector_outer_r = R_CUSP_OUTER
    if gauquelin_sectors:
        # Match the click hit-areas to the visible 36-sector rings above.
        out += _draw_gauquelin_sectors_modern(
            seventh_house_degree_ut, gauquelin_cusps=gauquelin_cusps, outer_r=house_sector_outer_r
        )
    else:
        out += _draw_house_sectors_modern(houses, seventh_house_degree_ut, outer_r=house_sector_outer_r)
    out += _draw_aspect_core(
        aspects_list, aspects_settings, seventh_house_degree_ut, show_aspect_movement=show_aspect_movement
    )

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
    show_motion_state: bool = False,
    show_aspect_movement: bool = False,
    glyph_size: str = "medium",
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
        glyph_size: Which cluster profile both rings draw — "small", "medium"
            or "large" (see GLYPH_SIZE_PROFILES). The drawer validates the
            value; an unknown key raises here.

    Returns:
        Complete SVG content string for the dual horoscope.
    """
    # ── FLAT CONCENTRIC DUAL-RING LAYOUT ──────────────────────────────────
    # Both rings exist at the same coordinate level, no nested scale() transforms.

    # See draw_modern_horoscope: non-default sizes are stamped, medium is not.
    size_attr = "" if glyph_size == "medium" else f' kr:glyphsize="{glyph_size}"'
    out = (
        f'<g kr:node="ModernDualHoroscope" kr:charttype="{chart_type}"{size_attr} '
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

    outer_profile = GLYPH_SIZE_PROFILES[glyph_size]["dual_outer"]
    inner_profile = GLYPH_SIZE_PROFILES[glyph_size]["dual_inner"]

    # ─── OUTER PLANET RING (Subject 2) ──────────────────────────────
    out += _draw_planet_ring(
        planets=planets_2,
        planets_settings=planets_settings,
        seventh_house_degree_ut=seventh_house_degree_ut,
        houses=houses_1,  # Subject 1's houses for divider lines
        min_separation=outer_profile.min_separation,
        ring_inner_r=SYN_R_OUTER_PLANET_INNER,
        ring_outer_r=SYN_R_OUTER_PLANET_OUTER,
        ring_fill_color=COLOR_OUTER_PLANET_RING,
        line_outer_y=SYN_HOUSE_LINE_OUTER_Y1,
        line_inner_y=SYN_HOUSE_LINE_OUTER_Y2,
        cusp_dim_stroke=COLOR_CUSP_DIM_OUTER,
        planet_y_config=outer_profile.planet_y_config(),
        indicator_config=outer_profile.indicator_config(),
        horoscope_id="1",
        scale_config=outer_profile.scale_config(),
        show_zodiac_background_ring=show_zodiac_background_ring,
        show_motion_state=show_motion_state,
    )

    # ─── INNER PLANET RING (Subject 1) ──────────────────────────────
    out += _draw_planet_ring(
        planets=planets_1,
        planets_settings=planets_settings,
        seventh_house_degree_ut=seventh_house_degree_ut,
        houses=houses_1,  # Subject 1's own houses
        min_separation=inner_profile.min_separation,
        ring_inner_r=SYN_R_INNER_PLANET_INNER,
        ring_outer_r=SYN_R_INNER_PLANET_OUTER,
        ring_fill_color=COLOR_PLANET_RING,
        line_outer_y=SYN_HOUSE_LINE_INNER_Y1,
        line_inner_y=SYN_HOUSE_LINE_INNER_Y2,
        planet_y_config=inner_profile.planet_y_config(),
        indicator_config=inner_profile.indicator_config(),
        horoscope_id="0",
        scale_config=inner_profile.scale_config(),
        show_zodiac_background_ring=show_zodiac_background_ring,
        show_motion_state=show_motion_state,
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
    # R_CUSP_OUTER in both cases: with the zodiac ring drawn these overlays sit
    # inside the scale(0.92) wrapper, so 50 renders at 46, the ring's inner edge.
    # See the single-chart path for what applying that scale twice cost.
    syn_house_sector_outer_r = R_CUSP_OUTER
    out += _draw_house_sectors_modern(
        houses_1,
        seventh_house_degree_ut,
        inner_r=SYN_R_HOUSE_INNER,
        outer_r=syn_house_sector_outer_r,
        horoscope_id="0",
    )

    # ─── ASPECT CORE (cross-chart aspects) ──────────────────────────
    out += _draw_aspect_core(
        aspects_list,
        aspects_settings,
        seventh_house_degree_ut,
        core_radius=SYN_R_ASPECT,
        show_aspect_movement=show_aspect_movement,
    )

    if show_zodiac_background_ring:
        out += "</g>\n"  # Close zodiac bg scale wrapper

    out += "</g>\n"  # Close main group
    return out
