"""
Utility functions for astrological chart generation and SVG drawing.

This module provides:
- Mathematical utilities for angle and coordinate calculations
- SVG drawing functions for chart elements (circles, slices, grids, etc.)
- Element and modality distribution calculations
- Coordinate conversion and formatting utilities

The module is organized in the following sections:
1. Constants (zodiac mappings, weights, layout thresholds)
2. Internal helper functions (weight preparation, distribution calculation)
3. Mathematical utilities (angles, coordinates, time conversion)
4. SVG drawing functions (circles, slices, rings, grids, aspects)
5. Element/modality distribution calculations
"""

import datetime
import math
import re
from typing import Literal, Mapping, Optional, Sequence, Union
from xml.sax.saxutils import escape as _xml_escape

from kerykeion.charts.glyph_metrics import estimate_text_width
from kerykeion.charts.spreading import spread_around_wheel
from kerykeion.schemas import ChartType, KerykeionException
from kerykeion.schemas.literals import AstrologicalPoint
from kerykeion.schemas.models import (
    AspectModel,
    AstrologicalSubjectModel,
    CompositeSubjectModel,
    HouseComparisonModel,
    KerykeionPointModel,
    PlanetReturnModel,
)
from kerykeion.schemas.settings_models import (
    KerykeionLanguageCelestialPointModel,
    KerykeionSettingsCelestialPointModel,
)
from kerykeion.settings.chart_defaults import resolve_glyph_id

# =============================================================================
# TYPE ALIASES
# =============================================================================

ElementQualityDistributionMethod = Literal["pure_count", "weighted"]
"""Supported strategies for calculating element and modality distributions."""

# Entities for quote characters, complementing the default &, <, > escaping.
_XML_TEXT_ENTITIES = {'"': "&quot;", "'": "&apos;"}

# Control characters illegal in XML 1.0 even when escaped (everything below
# 0x20 except tab/LF/CR). Escaping does not neutralize them, so a name/city
# containing one would make the SVG unparseable — strip them first. Mirrors
# context_serializer._strip_illegal.
_SVG_ILLEGAL_TRANSLATION = {c: None for c in range(0x20) if c not in (0x09, 0x0A, 0x0D)}


# The two stations, as chart tables have long abbreviated them. Both renderers
# mark a station, so the wording lives here rather than in either of them —
# and both marks are two characters wide, which is what lets the modern style
# reuse the retrograde row without remeasuring its separation model.
# Dash pattern for a separating aspect line in the classic wheel, whose
# aspect lines are drawn at stroke-width 1 in root units.
SEPARATING_DASH_ARRAY = "5 3.2"

# The one font stack every chart text renders in, in both styles, declared on
# the root of all four templates so no text node can miss it. Without it the
# SVG inherits whatever the embedding page uses — the same chart came out serif
# standalone, sans in one host page, monospace in another — and no spacing
# model can reserve room for an unknown font.
#
# Arial, Helvetica and Liberation Sans are metric-compatible, and Liberation is
# named explicitly so Linux systems that have it never fall through to generic
# sans-serif (usually DejaVu Sans, whose digits run ~10-14% wider than the
# measured ink tables). A system with none of the three still resolves to its
# own sans and can render wider than reserved — that residual risk is the price
# of not padding every chart for the rarest platform.
#
# Two of these three are also in the reference set glyph_metrics.py measured
# its width table against (Times, Helvetica, Arial Unicode), and that table is
# the per-character *maximum* over the set. Naming a font from inside the set
# therefore keeps every width estimate a valid upper bound and makes it tighter;
# naming one from outside would break the "never an underestimate" contract the
# panel's truncation relies on.
#
# Liberation Sans is deliberately unquoted: CSS allows multi-word family names
# as bare identifiers, and the SVG post-processing rewrites double quotes to
# single quotes, which nested quotes would corrupt.
CHART_TEXT_FONT_FAMILY = "Arial, Helvetica, Liberation Sans, sans-serif"


# Badge for an out-of-bounds body in the point tables. It sits past the
# retrograde glyph, in the gap before the next column, so a table that gains
# it keeps every column where it was.
OUT_OF_BOUNDS_BADGE = "OOB"
OUT_OF_BOUNDS_BADGE_X = 84


def out_of_bounds_badge_svg(point: object, text_color: str) -> str:
    """The OOB badge for *point*, or nothing when it is inside the bounds."""
    if not getattr(point, "is_out_of_bounds", None):
        return ""
    return (
        f'<text text-anchor="start" x="{OUT_OF_BOUNDS_BADGE_X}" '
        f'style="fill:{text_color}; font-size: 7px; font-weight: 700;">{OUT_OF_BOUNDS_BADGE}</text>'
    )


STATION_LABELS: dict[str, str] = {
    "stationary_retrograde": "SR",
    "stationary_direct": "SD",
}


def escape_svg_text(value: object) -> str:
    """Escape a plain-text value for safe embedding in SVG markup.

    Converts ``&``, ``<``, ``>`` and single/double quotes to their XML
    entities so user-supplied strings (subject names, cities, custom titles)
    cannot break the SVG structure or inject markup, and strips XML-1.0-illegal
    control characters that escaping cannot neutralize (which would otherwise
    make the SVG rejected by any conforming XML parser).

    A literal ``var(...)`` token in the text is defused (its ``(`` is entity-
    encoded) so the optional CSS-variable inliner — which runs a ``var(...)``
    regex over the whole document on the ``remove_css_variables=True`` path —
    cannot rewrite a person's name/city/title into a theme color value. The
    displayed text is unchanged (``&#40;`` renders as ``(``).

    Args:
        value: The value to escape; non-strings are converted with ``str()``.

    Returns:
        The escaped string, safe for use as XML text content or attribute value.
    """
    escaped = _xml_escape(str(value).translate(_SVG_ILLEGAL_TRANSLATION), _XML_TEXT_ENTITIES)
    # Break any 'var(' so the CSS-variable inliner's regex no longer matches it.
    return escaped.replace("var(", "var&#40;")


def _resolve_point_glyph_id(
    point_name: object,
    point_setting: Mapping[str, object] | None = None,
) -> str:
    """Resolve the SVG symbol id for a point or settings row."""
    if point_setting is not None:
        glyph_id = point_setting.get("glyph_id")
        if isinstance(glyph_id, str) and glyph_id:
            return glyph_id
    if not isinstance(point_name, str):
        return str(point_name)
    return resolve_glyph_id(point_name)


# =============================================================================
# ZODIAC ELEMENT AND QUALITY MAPPINGS
# =============================================================================

#: Maps zodiac sign index (0-11) to its element (fire, earth, air, water).

_SIGN_TO_ELEMENT: tuple[str, ...] = (
    "fire",  # Aries
    "earth",  # Taurus
    "air",  # Gemini
    "water",  # Cancer
    "fire",  # Leo
    "earth",  # Virgo
    "air",  # Libra
    "water",  # Scorpio
    "fire",  # Sagittarius
    "earth",  # Capricorn
    "air",  # Aquarius
    "water",  # Pisces
)

_SIGN_TO_QUALITY: tuple[str, ...] = (
    "cardinal",  # Aries
    "fixed",  # Taurus
    "mutable",  # Gemini
    "cardinal",  # Cancer
    "fixed",  # Leo
    "mutable",  # Virgo
    "cardinal",  # Libra
    "fixed",  # Scorpio
    "mutable",  # Sagittarius
    "cardinal",  # Capricorn
    "fixed",  # Aquarius
    "mutable",  # Pisces
)

#: Tuple of the four elements in standard order.
_ELEMENT_KEYS: tuple[str, ...] = ("fire", "earth", "air", "water")

#: Tuple of the three qualities/modalities in standard order.
_QUALITY_KEYS: tuple[str, ...] = ("cardinal", "fixed", "mutable")


# =============================================================================
# WEIGHT CONFIGURATION FOR ELEMENT/QUALITY CALCULATIONS
# =============================================================================

#: Default fallback weight for points not in the weight lookup.
_DEFAULT_WEIGHTED_FALLBACK: float = 1.0

#: Default weights for weighted element/quality distribution calculations.
#: Higher weights indicate more astrological significance.
DEFAULT_WEIGHTED_POINT_WEIGHTS: dict[str, float] = {
    # Core luminaries & angles
    "sun": 2.0,
    "moon": 2.0,
    "ascendant": 2.0,
    "medium_coeli": 1.5,
    "descendant": 1.5,
    "imum_coeli": 1.5,
    "vertex": 0.8,
    "anti_vertex": 0.8,
    # Personal planets
    "mercury": 1.5,
    "venus": 1.5,
    "mars": 1.5,
    # Social planets
    "jupiter": 1.0,
    "saturn": 1.0,
    # Outer/transpersonal
    "uranus": 0.5,
    "neptune": 0.5,
    "pluto": 0.5,
    # Lunar nodes (mean/true variants)
    "mean_north_lunar_node": 0.5,
    "true_north_lunar_node": 0.5,
    "mean_south_lunar_node": 0.5,
    "true_south_lunar_node": 0.5,
    # Chiron, Lilith variants
    "chiron": 0.6,
    "mean_lilith": 0.5,
    "true_lilith": 0.5,
    # Asteroids / centaurs
    "ceres": 0.5,
    "pallas": 0.4,
    "juno": 0.4,
    "vesta": 0.4,
    "pholus": 0.3,
    # Dwarf planets & TNOs
    "eris": 0.3,
    "sedna": 0.3,
    "haumea": 0.3,
    "makemake": 0.3,
    "ixion": 0.3,
    "orcus": 0.3,
    "quaoar": 0.3,
    # Arabic Parts
    "pars_fortunae": 0.8,
    "pars_spiritus": 0.7,
    "pars_amoris": 0.6,
    "pars_fidei": 0.6,
    # Fixed stars
    "regulus": 0.2,
    "spica": 0.2,
    "aldebaran": 0.2,
    "antares": 0.2,
    "sirius": 0.2,
    "fomalhaut": 0.2,
    "algol": 0.2,
    "betelgeuse": 0.2,
    "canopus": 0.2,
    "procyon": 0.2,
    "arcturus": 0.2,
    "pollux": 0.2,
    "deneb": 0.2,
    "altair": 0.2,
    "rigel": 0.2,
    "achernar": 0.2,
    "capella": 0.2,
    "vega": 0.2,
    "alcyone": 0.2,
    "alphecca": 0.2,
    "algorab": 0.2,
    "deneb_algedi": 0.2,
    "alkaid": 0.2,
    # Lilith/Priapus variants and lunar apse points
    "interpolated_lilith": 0.5,
    "mean_priapus": 0.5,
    "true_priapus": 0.5,
    "interpolated_perigee": 0.5,
    "white_moon": 0.5,
    # Uranian / Hamburg School hypothetical planets
    "cupido": 0.3,
    "hades": 0.3,
    "zeus": 0.3,
    "kronos": 0.3,
    "apollon": 0.3,
    "admetos": 0.3,
    "vulkanus": 0.3,
    "poseidon": 0.3,
    # Other
    "earth": 0.3,
}

#: Weight for active fixed stars that have no entry in the table above (the 23
#: traditional stars are listed at 0.2): stars must never inherit the generic
#: planet-grade fallback weight.
_FIXED_STAR_FALLBACK_WEIGHT: float = 0.2


# =============================================================================
# INTERNAL HELPER FUNCTIONS
# =============================================================================


def _prepare_weight_lookup(
    method: ElementQualityDistributionMethod,
    custom_weights: Optional[Mapping[str, float]] = None,
) -> tuple[dict[str, float], float, float]:
    """
    Normalize and merge default weights with any custom overrides.

    Args:
        method: Calculation strategy to use.
        custom_weights: Optional mapping of point name (case-insensitive) to weight.
                        Supports special key "__default__" as fallback weight.

    Returns:
        ``(weight_lookup, fallback_weight, star_fallback_weight)``. The star
        fallback is the weight for an active fixed star absent from the table:
        ``_FIXED_STAR_FALLBACK_WEIGHT`` (0.2) in weighted mode, but the plain
        ``fallback_weight`` (1.0) in ``pure_count`` — where every counted item
        must contribute exactly 1, stars included.
    """
    normalized_custom = {key.lower(): float(value) for key, value in custom_weights.items()} if custom_weights else {}

    if method == "weighted":
        weight_lookup: dict[str, float] = dict(DEFAULT_WEIGHTED_POINT_WEIGHTS)
        fallback_weight = _DEFAULT_WEIGHTED_FALLBACK
    else:
        weight_lookup = {}
        fallback_weight = 1.0

    fallback_weight = normalized_custom.get("__default__", fallback_weight)

    for key, value in normalized_custom.items():
        if key == "__default__":
            continue
        weight_lookup[key] = float(value)

    star_fallback_weight = _FIXED_STAR_FALLBACK_WEIGHT if method == "weighted" else fallback_weight

    return weight_lookup, fallback_weight, star_fallback_weight


def _calculate_distribution_for_subject(
    subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
    celestial_points_names: Sequence[str],
    sign_to_group_map: Sequence[str],
    group_keys: Sequence[str],
    weight_lookup: Mapping[str, float],
    fallback_weight: float,
    include_fixed_stars: bool = False,
    star_fallback_weight: float = _FIXED_STAR_FALLBACK_WEIGHT,
) -> dict[str, float]:
    """
    Accumulate distribution totals for a single subject.

    Args:
        subject: Subject providing planetary positions.
        celestial_points_names: Names of celestial points to consider (lowercase).
        sign_to_group_map: Mapping from sign index to element/modality key.
        group_keys: Iterable of expected keys for the resulting totals.
        weight_lookup: Precomputed mapping of weights per point.
        fallback_weight: Default weight if point missing in lookup.
        include_fixed_stars: Also count the subject's active fixed stars (which
            live in ``subject.fixed_stars``, not under ``celestial_points_names``).
        star_fallback_weight: Weight for an active fixed star absent from the
            table — 0.2 in weighted mode, ``fallback_weight`` (1.0) in
            pure_count so a star counts as one item like every other point.

    Returns:
        Dictionary with accumulated totals keyed by element/modality.
    """
    totals = {key: 0.0 for key in group_keys}

    def _accumulate(point, point_name: str, default_weight: float) -> None:
        sign_index = getattr(point, "sign_num", None)
        if sign_index is None or not (0 <= sign_index < len(sign_to_group_map)):
            return
        group_key = sign_to_group_map[sign_index]
        totals[group_key] += weight_lookup.get(point_name, default_weight)

    for point_name in celestial_points_names:
        point = subject.get(point_name)
        if point is None:
            continue
        _accumulate(point, point_name, fallback_weight)

    if include_fixed_stars:
        from kerykeion.fixed_stars.catalog import star_slug

        for star in subject.get("fixed_stars") or []:
            _accumulate(star, star_slug(star.name).lower(), star_fallback_weight)

    return totals


# =============================================================================
# CHART LAYOUT CONSTANTS
# =============================================================================

#: Column threshold indices for planet grid layout.
_SECOND_COLUMN_THRESHOLD: int = 20
_THIRD_COLUMN_THRESHOLD: int = 28
_FOURTH_COLUMN_THRESHOLD: int = 36

#: Chart types that use double-wheel (bi-wheel) layout.
DOUBLE_CHART_TYPES: tuple[ChartType, ...] = ("Synastry", "Transit", "DualReturnChart", "Progression")

#: Chart types that use transit-style secondary header formatting (offset title, no prefix).
_TRANSIT_LIKE_HEADER_TYPES: tuple[ChartType, ...] = ("Transit", "Progression")

#: Width in pixels of each column in the planet grid.
_GRID_COLUMN_WIDTH: int = 125

#: Right edge of a grid row's own content: the retrograde glyph sits at x=74 at
#: half scale, so the row's ink stops just past it — or past the OOB badge when
#: one is drawn.
_GRID_ROW_CONTENT_RIGHT: float = 87.0

#: Gap left between one column's content and the next column's name.
_GRID_COLUMN_GUTTER: float = 8.0


def label_separation_degrees(label_width_px: float, radius_px: float, gutter_px: float = 3.0) -> float:
    """Degrees two labels of this width need at this radius so their ink clears.

    An arc of one degree is ``2·pi·r/360`` long, so a label needs its own width
    plus a gap, divided by that. Radius matters as much as the font does: the
    same "11" that sits comfortably on the natal ring at r=192 has two thirds of
    the room on a biwheel's inner ring at r=156.
    """
    if radius_px <= 0:
        return 0.0
    arc_per_degree = 2.0 * math.pi * radius_px / 360.0
    return (label_width_px + gutter_px) / arc_per_degree if arc_per_degree else 0.0


def planet_grid_column_width(
    names: "Sequence[str]" = (),
    show_out_of_bounds: bool = False,
    font_size: float = 10.0,
) -> int:
    """Column stride wide enough that a name never lands on the row before it.

    A row draws rightward from its origin — glyph, degrees, sign, retrograde
    mark, and the out-of-bounds badge when asked for — while its *name* is
    right-aligned at that origin and therefore extends leftward, into whatever
    the previous column left behind. The fixed 125px stride works only while
    every name is short: it leaves 25px of room, and "N. Node (M)" wants 56, so
    two node labels printed on top of each other in the charts that carry both.

    Measured from the names actually being drawn rather than from the widest
    name imaginable, so an ordinary chart keeps the layout it always had.
    """
    content_right = _GRID_ROW_CONTENT_RIGHT
    if show_out_of_bounds:
        content_right = OUT_OF_BOUNDS_BADGE_X + estimate_text_width(OUT_OF_BOUNDS_BADGE, 7)
    widest_name = max((estimate_text_width(n, font_size) for n in names), default=0.0)
    return max(_GRID_COLUMN_WIDTH, math.ceil(content_right + widest_name + _GRID_COLUMN_GUTTER))


#: Where a planet-grid row ends its reading and starts the sign glyph after it.
#: The reading is anchored at its END, which is the whole trick: left-anchored,
#: it ran from x=19 to anywhere between 57 and 62.8 depending on how many digits
#: the degrees needed, so "29°59'59"" printed its seconds mark across the sign
#: glyph at 60 while "3°32'47"" left a hole beside it. Anchored at the end, every
#: row hands the sign glyph the same gap, and the digits line up in a column as
#: figures should.
#:
#: The room comes from the left, not the right. Everything after the sign — the
#: retrograde mark at 74, the out-of-bounds badge at 84 — is already as far
#: right as it can go: the houses grid is drawn immediately beside this one, and
#: pushing the badge out by six units put it 1.1 units into "Cusp 8:".
#: Right edge of the planet glyph that opens the row: drawn at x=5 at scale 0.4
#: in a 24-unit box, so its box ends at 14.6. The reading must start after it.
_GRID_PLANET_GLYPH_RIGHT: float = 14.6
_GRID_READING_RIGHT: int = 61
_GRID_SIGN_X: int = 63
_GRID_RETROGRADE_X: int = 74

#: Widest a point's name may print in a planet grid before it is abbreviated.
#: Sized on the names the grids were laid out for: the longest English label
#: ("N. Node (T)") inks 53 units at the grid's 10px, so 56 leaves every name the
#: layout was built around untouched and catches only the ones that outgrow it.
#: A translated name has no such ceiling — German prints "Nordknoten (T)" at 68
#: — and a name is the one thing in the row that grows leftward, into whatever
#: block the grid was placed beside.
_GRID_NAME_MAX_WIDTH: float = 56.0

#: Matches a trailing parenthesised marker, e.g. the "(T)"/"(M)" that separates
#: the true lunar node from the mean one.
_TRAILING_MARKER = re.compile(r"\s*(\([^()]{1,3}\))\s*$")


def abbreviate_point_name(
    name: str,
    max_width: float = _GRID_NAME_MAX_WIDTH,
    font_size: float = 10.0,
) -> str:
    """Shorten *name* with a full stop until it inks no wider than *max_width*.

    A trailing marker survives the cut, and the head is what gets shortened:
    "Nordknoten (T)" becomes "Nordkn. (T)", never "Nordknoten." — dropping the
    marker would merge the true lunar node with the mean one, which is the one
    distinction the parenthesis exists to make.

    Cutting by inked width rather than by a character count is what makes this
    work in every language the charts ship: ten Latin characters and ten CJK
    ones are not the same amount of room, and the grid cares about the room.
    """
    if estimate_text_width(name, font_size) <= max_width:
        return name

    marker_match = _TRAILING_MARKER.search(name)
    marker = f" {marker_match.group(1)}" if marker_match else ""
    head = name[: marker_match.start()] if marker_match else name

    budget = max_width - estimate_text_width(marker, font_size)
    # One character at a time, because the widths are per-character: cutting a
    # proportional share of the string overshoots on "Nordknoten" and undershoots
    # on a string of narrow letters.
    for cut in range(len(head) - 1, 0, -1):
        candidate = f"{head[:cut].rstrip()}."
        if estimate_text_width(candidate, font_size) <= budget:
            return f"{candidate}{marker}"
    return f"{head[:1]}.{marker}"


#: Width in pixels of each column in the Gauquelin unified grid.
_GAUQUELIN_COLUMN_WIDTH: int = 220

#: Room the OOB badge needs in the Gauquelin table. Its columns run right up to
#: their width — the declination text ends around x=186 and the right-aligned
#: sector value starts there — so unlike the standard grids, which have slack
#: after the retrograde glyph, this one has nowhere to put a badge and must be
#: widened for it.
_GAUQUELIN_OOB_BADGE_WIDTH: int = 26


def gauquelin_column_width(with_out_of_bounds: bool = False) -> int:
    """Width of one Gauquelin column, wider when it has to carry OOB badges.

    Shared with the drawer's width estimator: the grid and the canvas that has
    to hold it must be sized from the same number, or the table is drawn wider
    than the space reserved for it and the last column is clipped.
    """
    return _GAUQUELIN_COLUMN_WIDTH + (_GAUQUELIN_OOB_BADGE_WIDTH if with_out_of_bounds else 0)

#: Maximum rows per column in the Gauquelin unified grid.
_GAUQUELIN_MAX_ROWS: int = 18

#: Gauquelin plus zones — sectors near the four angles with enhanced statistical significance.
_GAUQUELIN_PLUS_ZONES: frozenset[int] = frozenset({36, 1, 9, 10, 18, 19, 27, 28})


def _select_planet_grid_thresholds(chart_type: ChartType, num_points: int = 0) -> tuple[int, int, int]:
    """
    Return column thresholds for the planet grids based on chart type and point count.

    For double-wheel charts (Synastry, Transit, DualReturnChart, Progression), returns very high
    thresholds to effectively disable multi-column layout.

    For single-wheel charts with many active points (> 20), computes balanced
    thresholds to distribute points evenly across columns, preventing visual
    overlap between the planet grid and the chart wheel.

    Args:
        chart_type: The type of chart being rendered.
        num_points: Total number of active celestial points. When > 20 in single-wheel
                   charts, triggers balanced multi-column distribution instead of the
                   fixed thresholds (20, 28, 36) which produce uneven columns.

    Returns:
        Tuple of (second, third, fourth) column thresholds.
    """
    if chart_type in DOUBLE_CHART_TYPES:
        return (
            1_000_000,  # effectively disable first column
            1_000_008,  # effectively disable second column
            1_000_016,  # effectively disable third column
        )

    # For <= 20 points, all fit in one column (original behavior preserved)
    if num_points <= _SECOND_COLUMN_THRESHOLD:
        return _SECOND_COLUMN_THRESHOLD, _THIRD_COLUMN_THRESHOLD, _FOURTH_COLUMN_THRESHOLD

    # Balanced distribution: spread points evenly across columns to prevent
    # uneven column heights and leftward overflow into the chart wheel area.
    # Example: 57 points → 3 columns of 19 rows each, instead of 20/8/8/21.
    max_rows = _SECOND_COLUMN_THRESHOLD  # 20 rows max per column
    num_columns = min(4, max(1, math.ceil(num_points / max_rows)))
    rows_per_col = math.ceil(num_points / num_columns)

    return rows_per_col, rows_per_col * 2, rows_per_col * 3


def _planet_grid_layout_position(
    index: int,
    thresholds: Optional[tuple[int, int, int]] = None,
    column_width: Optional[int] = None,
) -> tuple[int, int]:
    """
    Calculate the grid position for a planet at the given index.

    Args:
        index: Zero-based index of the planet in the list.
        thresholds: Optional tuple of (second, third, fourth) column thresholds.
                   If None, uses default thresholds.

    Returns:
        Tuple of (horizontal_offset, row_index) for positioning.
    """
    second_threshold, third_threshold, fourth_threshold = (
        thresholds
        if thresholds is not None
        else (_SECOND_COLUMN_THRESHOLD, _THIRD_COLUMN_THRESHOLD, _FOURTH_COLUMN_THRESHOLD)
    )

    if index < second_threshold:
        column = 0
        row = index
    elif index < third_threshold:
        column = 1
        row = index - second_threshold
    elif index < fourth_threshold:
        column = 2
        row = index - third_threshold
    else:
        column = 3
        row = index - fourth_threshold

    offset = -((column_width if column_width is not None else _GRID_COLUMN_WIDTH) * column)
    return offset, row


# =============================================================================
# LANGUAGE AND LOCALIZATION UTILITIES
# =============================================================================


def get_decoded_kerykeion_celestial_point_name(
    input_planet_name: str, celestial_point_language: KerykeionLanguageCelestialPointModel
) -> str:
    """
    Decode the given celestial point name based on the provided language model.

    Args:
        input_planet_name: The internal name of the celestial point to decode.
        celestial_point_language: The language model containing translated point names.

    Returns:
        The localized celestial point name, or the prettified slug for dynamic
        names (fixed stars, pair midpoints) that have no translation entries.
    """
    language_keys = celestial_point_language.model_dump().keys()

    if input_planet_name in language_keys:
        return celestial_point_language[input_planet_name]
    # v6: dynamic point names (fixed stars, pair midpoints such as
    # "Sun_Moon_Midpoint") are not in the translations table. Fall back to the
    # caller-provided slug with underscores replaced by spaces — labels remain
    # readable on the chart wheel without polluting the language model. Static
    # point names are Literal-validated upstream, so typos cannot reach here.
    return input_planet_name.replace("_", " ")


# =============================================================================
# MATHEMATICAL UTILITIES
# =============================================================================


def hms_to_decimal_hours(hours: int, minutes: int, seconds: int) -> float:
    """Combine an hours/minutes/seconds triple into a single decimal-hour value.

    Args:
        hours: Whole hours.
        minutes: Minutes component (0-59).
        seconds: Seconds component (0-59).

    Returns:
        The time expressed as decimal hours (e.g. ``12:30:00`` -> ``12.5``).
    """
    return hours + minutes / 60 + seconds / 3600


def degree_difference(a: Union[int, float], b: Union[int, float]) -> float:
    """Return the smallest absolute separation between two angles, in degrees.

    The result is symmetric and always lies in ``[0, 180]``; angles on opposite
    sides of the 0°/360° wrap-around (e.g. 350° and 10°) are handled correctly.

    Args:
        a: First angle in degrees.
        b: Second angle in degrees.

    Returns:
        The shortest angular distance between ``a`` and ``b`` (0 to 180).
    """
    # Reduce the raw gap into [0, 360), then take whichever way around the
    # circle is shorter.
    gap = math.fmod(abs(a - b), 360)
    return min(gap, 360 - gap)


def degree_sum(a: Union[int, float], b: Union[int, float]) -> float:
    """Calculate the sum of two angles in degrees, normalized to [0, 360).

    Args:
        a (int | float): first angle in degrees
        b (int | float): second angle in degrees

    Returns:
        float: normalized sum of a and b in the range [0, 360)
    """
    # Through normalize_degree rather than a second `% 360.0`: the modulo alone
    # returns exactly 360.0 for a tiny negative sum, which is outside the range
    # this docstring promises. That was the defect fixed fifteen lines below;
    # having the two share one implementation is what stops it being fixed once.
    return normalize_degree(a + b)


def normalize_degree(angle: Union[int, float]) -> float:
    """Normalize an angle to the range [0, 360).

    Args:
        angle (int | float): The input angle in degrees.

    Returns:
        float: The normalized angle in the range [0, 360).
    """
    # The guard is on the *result*, not on `% 360 != 0`. For a tiny negative
    # input Python's float modulo returns exactly 360.0 (-1e-15 % 360 == 360.0),
    # which the old test read as "non-zero, therefore fine" and passed straight
    # through — breaking the [0, 360) contract this function exists to hold.
    # It matters downstream: draw_modern computes a house sector's span as
    # normalize_degree(next_cusp - cusp), so two cusps coinciding to within
    # float noise in the negative direction painted a 360° sector over the
    # whole chart instead of a degenerate one.
    result = angle % 360.0
    # `result < 360.0` is False for NaN as well as for 360.0, so a bare else
    # would quietly turn a NaN angle into 0° Aries — a plausible-looking wrong
    # position where the old expression let the NaN through to a visible `nan`
    # coordinate. Inf likewise: `inf % 360` is NaN. Propagate instead.
    if math.isnan(result):
        return result
    return result if result < 360.0 else 0.0


def timedelta_to_decimal_hours(datetime_offset: Union[datetime.timedelta, None]) -> float:
    """Express a UTC offset, given as a ``timedelta``, in decimal hours.

    Args:
        datetime_offset: The offset to convert (e.g. ``timedelta(hours=2)``).

    Returns:
        The offset in decimal hours (e.g. ``+02:00`` -> ``2.0``).

    Raises:
        KerykeionException: If ``datetime_offset`` is ``None``.
    """
    if datetime_offset is None:
        raise KerykeionException("datetime_offset is None")

    # A timedelta stores whole days and leftover seconds separately; convert each
    # to hours and add them.
    return datetime_offset.days * 24 + datetime_offset.seconds / 3600


# =============================================================================
# COORDINATE CALCULATION UTILITIES
# =============================================================================


def wheel_x(sign_index: Union[int, float], radius: Union[int, float], offset: Union[int, float]) -> float:
    """
    Project a wheel position onto its horizontal (x) screen coordinate.

    Each ``sign_index`` step advances the position by one 30° sector; ``offset``
    rotates the whole wheel. The origin is shifted by ``radius`` so the returned
    value is always non-negative (the wheel's left edge sits at x=0).

    Args:
        sign_index: Sector index (0-11), where each unit equals 30°.
        radius: Circle radius in pixels.
        offset: Angular offset in degrees.

    Returns:
        X-coordinate on the circle.
    """
    angle = (math.pi / 6) * sign_index + (math.pi * offset) / 180
    return radius * (1 + math.cos(angle))


def wheel_y(sign_index: Union[int, float], radius: Union[int, float], offset: Union[int, float]) -> float:
    """
    Project a wheel position onto its vertical (y) screen coordinate.

    Mirrors :func:`wheel_x` for the vertical axis. The sine term is negated so
    the result follows the SVG convention (y grows downward), and the origin is
    shifted by ``radius`` so the value is non-negative (top edge at y=0).

    Args:
        sign_index: Sector index (0-11), where each unit equals 30°.
        radius: Circle radius in pixels.
        offset: Angular offset in degrees.

    Returns:
        Y-coordinate on the circle.
    """
    angle = (math.pi / 6) * sign_index + (math.pi * offset) / 180
    return radius * (1 - math.sin(angle))


# =============================================================================
# SVG DRAWING FUNCTIONS - ZODIAC SLICES
# =============================================================================


def draw_zodiac_slice(
    c1: Union[int, float],
    chart_type: ChartType,
    seventh_house_degree_ut: Union[int, float],
    num: int,
    r: Union[int, float],
    style: str,
    type: str,
) -> str:
    """
    Draw a zodiac sign slice with its symbol on the chart wheel.

    Creates an SVG path element for one of the 12 zodiac slices (30° each)
    and positions the corresponding zodiac symbol.

    Args:
        c1: Inner offset for single-wheel charts (ignored for double-wheel).
        chart_type: Type of chart being rendered.
        seventh_house_degree_ut: Degree of the 7th house cusp for alignment.
        num: Sign index (0-11, where 0=Aries).
        r: Chart radius in pixels.
        style: CSS inline style for the slice path.
        type: Sign symbol ID (e.g., "Ari", "Tau", etc.).

    Returns:
        SVG string containing the slice path and symbol elements.
    """
    # pie slices
    offset = 360 - seventh_house_degree_ut
    # check transit
    if chart_type in DOUBLE_CHART_TYPES:
        dropin: Union[int, float] = 0
    else:
        dropin = c1
    slice_path = f'<path d="M{str(r)},{str(r)} L{str(dropin + wheel_x(num, r - dropin, offset))},{str(dropin + wheel_y(num, r - dropin, offset))} A{str(r - dropin)},{str(r - dropin)} 0 0,0 {str(dropin + wheel_x(num + 1, r - dropin, offset))},{str(dropin + wheel_y(num + 1, r - dropin, offset))} z" style="{style}"/>'

    # symbols: nudge the angle by 15° to centre the glyph within its 30° sector.
    offset = offset + 15
    # ``dropin`` is a fixed inward radial inset (px) calibrated to the wheel
    # geometry; the translate(-16,-16) recentres the 32px glyph viewBox on its
    # anchor point. These are functional layout offsets, not creative values.
    if chart_type in DOUBLE_CHART_TYPES:
        dropin = 54
    else:
        dropin = 18 + c1
    sign = f'<g transform="translate(-16,-16)"><use x="{str(dropin + wheel_x(num, r - dropin, offset))}" y="{str(dropin + wheel_y(num, r - dropin, offset))}" xlink:href="#{type}" /></g>'

    return f'<g kr:node="ZodiacSign" kr:sign="{type}" kr:signnumber="{num}">' + slice_path + sign + "</g>"


# Span given to a wedge whose two cusps quantise onto the same whole degree, so
# the arc is still drawn and the house stays clickable. One degree is the
# resolution the classic engine works at, so nothing finer would survive anyway.
MINIMUM_WEDGE_SPAN_DEGREES = 1.0

#: How far the twelve widths may miss a full circle and still count as covering
#: it once. Windings are 360 degrees apart, so anything short of a degree is
#: float noise rather than another turn.
_HOUSE_WINDING_TOLERANCE_DEGREES = 1e-4


def house_spans(cusps: Sequence[float]) -> tuple[list[float], list[bool]]:
    """The twelve house widths, and which of them run against their own frame.

    Above roughly 68 degrees a Campanus, Regiomontanus, Sunshine, topocentric or
    APC chart puts its cusps in *descending* order, and a horizon chart does it
    on the equator: the houses genuinely run backwards through the signs. Read
    forwards, each house then measures some 354 degrees instead of 6, the twelve
    of them wind round the wheel eleven times instead of once, and everything
    that draws or centres on that span lands on the far side of the chart from
    the house it names.

    The direction belongs to the whole set and cannot be decided pair by pair: a
    single house may legitimately run past 180 degrees, which Placidus manages at
    high latitude, and taking the shorter arc there would cut it in half. Twelve
    widths cover the circle exactly once in whichever direction the houses run,
    so the total is what tells the two apart - 360 one way, 3960 the other.

    A third case has neither total. Polich/Page inside the polar circle returns
    cusps that are not ordered at all: at 70N the first runs backwards while the
    next five run forwards, so houses 1 and 2 overlap and no direction can make
    twelve wedges tile a circle. The chart is degenerate rather than reversed,
    and the least bad reading is to hold each wedge to its shorter arc: they
    still overlap, because the cusps do, but no single one swallows the wheel.

    Args:
        cusps: The twelve cusp positions, in house order, in any angular frame.

    Returns:
        The twelve widths, and for each the flag saying it was measured against
        the direction of the frame it was given.
    """
    forward = [normalize_degree(cusps[(index + 1) % 12] - cusps[index]) for index in range(12)]
    if abs(sum(forward) - 360.0) <= _HOUSE_WINDING_TOLERANCE_DEGREES:
        return forward, [False] * 12

    backward = [normalize_degree(cusps[index] - cusps[(index + 1) % 12]) for index in range(12)]
    if abs(sum(backward) - 360.0) <= _HOUSE_WINDING_TOLERANCE_DEGREES:
        return backward, [True] * 12

    shorter = [ahead <= behind for ahead, behind in zip(forward, backward)]
    return (
        [ahead if pick else behind for ahead, behind, pick in zip(forward, backward, shorter)],
        [not pick for pick in shorter],
    )


def separate_collapsed_wedges(
    boundaries: Sequence[float],
    spans: Sequence[float],
    reversed_wedges: Sequence[bool],
    minimum: float,
) -> tuple[list[float], list[float]]:
    """Give every wedge at least *minimum* degrees, out of what the widest can spare.

    Two cusps inside the same whole degree collapse onto one offset when the ring
    is quantised, and an arc whose endpoints coincide is dropped by the SVG spec:
    a zero-area path that still declares ``pointer-events: all`` is a house that
    can never be clicked.

    The widths are adjusted and the boundaries rebuilt from them, walking the
    twelve in house order. That is what keeps the boundaries **shared** — wedge i
    ends exactly where wedge i+1 begins, so there is no overlap for the hit test
    to resolve and no gap to fall through — and it is why the twelve angles are
    not simply handed to ``spread_around_wheel``. That function sorts what it is
    given and breaks ties by list index, which is not the order round the wheel:
    where house 12 and house 1 shared a degree it returned them swapped, and the
    twelfth wedge was then drawn backwards across 359 degrees of the annulus,
    invisible, taking every click on the chart.

    A wedge that had to grow takes its room from the wedges with room to give, in
    proportion to what each has above the minimum, so the twelve still cover
    exactly 360 degrees. A boundary may end up as much as a couple of degrees off
    the cusp line it was quantised from — five cusps on one degree have to be
    spread five degrees wide before any of them is clickable — which is the price
    of the house existing on the wheel at all.

    Args:
        boundaries: The twelve offsets, in house order.
        spans: Their widths, from :func:`house_spans`.
        reversed_wedges: Their directions, from :func:`house_spans`.
        minimum: The narrowest wedge worth drawing, in degrees.

    Returns:
        The rebuilt boundaries and widths — the arguments themselves, unchanged
        and identical object for object, when nothing was below the minimum or
        the cusps are too tangled to have a direction in common.
    """
    unchanged = (list(boundaries), list(spans))
    deficit = sum(minimum - span for span in spans if span < minimum)
    if deficit <= 0.0:
        return unchanged
    if len(set(reversed_wedges)) != 1:
        # The cusps cross, so the houses do not tile and there is no order to
        # rebuild them in. Leave them: overlapping wedges are what the data says.
        return unchanged

    surplus = sum(span - minimum for span in spans if span > minimum)
    if surplus <= deficit:
        return unchanged

    shrink = 1.0 - deficit / surplus
    adjusted = [
        minimum if span <= minimum else minimum + (span - minimum) * shrink for span in spans
    ]
    step = -1.0 if reversed_wedges[0] else 1.0
    rebuilt = [float(boundaries[0])]
    for index in range(len(adjusted) - 1):
        rebuilt.append(rebuilt[-1] + step * adjusted[index])
    return rebuilt, adjusted


def draw_house_sectors(
    r: Union[int, float],
    houses_list: list[KerykeionPointModel],
    c1: Union[int, float],
    c3: Union[int, float],
    chart_type: ChartType,
    external_view: bool = False,
    horoscope_id: Union[str, None] = None,
    seventh_house_abs_override: Union[float, None] = None,
    outer_r_offset: Union[int, float, None] = None,
    inner_r_offset: Union[int, float, None] = None,
    quantize_offsets_to_whole_degrees: bool = True,
) -> str:
    """
    Draw transparent house sector wedges for interactive highlighting.

    Each sector is an annular wedge between the inner circle (c3) and the
    outer circle (c1), spanning from one house cusp to the next. The sectors
    are fully transparent by default and only become visible when the
    frontend applies a CSS class (.chart-focused).

    Args:
        r: Chart radius in pixels.
        houses_list: List of 12 house cusp models.
        c1: Outer boundary offset (first_circle_radius).
        c3: Inner boundary offset (third_circle_radius).
        chart_type: Type of chart being rendered.
        external_view: If True, adjusts radii for external view mode.
        horoscope_id: Subject identifier ("0" for first, "1" for second) or None.
        seventh_house_abs_override: Override for the 7th house position used to orient
            the wheel. When None, uses houses_list[6].abs_pos.
        quantize_offsets_to_whole_degrees: Truncate each offset to the whole degree,
            as ``draw_houses_cusps_and_text_number`` does for the inner ring. The wedge
            only has to agree with the line it bounds, and a dual chart draws its two
            rings with two different conventions: the first subject's cusps are
            truncated, the second subject's are not (see the ``t_offset`` branch
            there). Pass False for the outer ring, or the wedges drift off the
            lines they are supposed to follow.
        outer_r_offset: Override for the outer radius offset (distance from r).
        inner_r_offset: Override for the inner radius offset (distance from r).

    Returns:
        SVG string containing 12 house sector path elements.
    """
    seventh_house_abs = seventh_house_abs_override if seventh_house_abs_override is not None else houses_list[6].abs_pos

    # All chart circles are visually centered at (r, r) in SVG coordinates.
    # The visual radii match the <circle> elements drawn by draw_first_circle etc.
    if chart_type in DOUBLE_CHART_TYPES:
        outer_visual_r = r - (outer_r_offset if outer_r_offset is not None else 72)
        inner_visual_r = r - (inner_r_offset if inner_r_offset is not None else 160)
    else:
        outer_visual_r = r - c1  # outer boundary (c1=first_circle_radius)
        inner_visual_r = r - c3  # inner boundary (c3=third_circle_radius)

    # Match whichever convention the cusp lines of *this* ring use. The classic
    # engine quantises the inner ring to the whole degree (`-int(seventh) +
    # int(cusp)`, the same expression draw_planets uses for glyphs), and a wedge
    # that kept exact degrees sat up to 0.7° off the line it bounds — about 3px
    # at r=240, enough that a click just inside a cusp selected the neighbouring
    # house. The outer ring of a dual chart is drawn at full precision instead,
    # so quantising there would recreate the very drift this fixes, on the other
    # subject.
    if quantize_offsets_to_whole_degrees:
        boundaries = [
            float(-int(seventh_house_abs) + int(house.abs_pos)) for house in houses_list[:12]
        ]
    else:
        boundaries = [-seventh_house_abs + house.abs_pos for house in houses_list[:12]]

    # Which way the houses run, read once from all twelve. Above the polar circle
    # several quadrant systems reverse, and the wedge for a house that measures
    # 6 degrees backwards was being painted as the 354 degrees forwards: twelve
    # near-complete rings stacked on each other, each one invisible and each one
    # declaring pointer-events:all, so every click on the wheel was answered by
    # whichever was drawn last.
    #
    # Then any wedge too thin to be drawn is widened out of what the wide ones can
    # spare, in house order, so the boundaries stay shared and an ordinary chart
    # comes out of here with the same offsets its cusp lines were drawn from, to
    # the bit.
    spans, reversed_wedges = house_spans(boundaries)
    boundaries, spans = separate_collapsed_wedges(
        boundaries, spans, reversed_wedges, MINIMUM_WEDGE_SPAN_DEGREES
    )

    output = ""
    for i in range(12):
        next_i = (i + 1) % 12
        house_num = i + 1

        offset_start = boundaries[i]
        offset_end = boundaries[next_i]

        # Use wheel_x/Y (which has built-in +1 centering) + dropin offset.
        # This matches the cusp line coordinate system exactly.
        outer_dropin = r - outer_visual_r  # = c1 for natal, 72 for transit
        inner_dropin = r - inner_visual_r  # = c3 for natal, 160 for transit

        ox1 = wheel_x(0, outer_visual_r, offset_start) + outer_dropin
        oy1 = wheel_y(0, outer_visual_r, offset_start) + outer_dropin
        ox2 = wheel_x(0, outer_visual_r, offset_end) + outer_dropin
        oy2 = wheel_y(0, outer_visual_r, offset_end) + outer_dropin

        ix1 = wheel_x(0, inner_visual_r, offset_start) + inner_dropin
        iy1 = wheel_y(0, inner_visual_r, offset_start) + inner_dropin
        ix2 = wheel_x(0, inner_visual_r, offset_end) + inner_dropin
        iy2 = wheel_y(0, inner_visual_r, offset_end) + inner_dropin

        # From the truncated offsets, not the exact degrees: the flag has to agree
        # with the endpoints it is steering. Reading the exact span while the arc
        # ends on whole degrees puts them at odds either side of 180° — cusps at
        # 10.1° and 190.9° span 180.8° exactly (large_arc=1) but only 180° once
        # truncated, and SVG then takes the long way round, painting the wedge
        # over the opposite half of the wheel.
        # Through normalize_degree, not a bare `% 360`: for a span that comes out
        # a hair negative — two cusps coinciding to within float noise, in the
        # wrong order — the modulo alone returns exactly 360.0, which reads as
        # "more than half the circle" and paints the wedge the long way round
        # over the whole annulus. Invisible, and with pointer-events:all it then
        # takes every click meant for the houses drawn before it.
        #
        # The separation above already catches that input, so this is the second
        # line and not the first. It is here because the rule is the rule — a
        # bare `% 360` on an angle is the trap normalize_degree was rewritten to
        # close fifteen files away, and leaving one behind invites the next
        # person to copy it.
        span = spans[i]
        large_arc = 1 if span > 180 else 0
        outer_sweep, inner_sweep = (1, 0) if reversed_wedges[i] else (0, 1)

        # Path from cusp N to cusp N+1.
        # sweep=0 for outer arc, sweep=1 for inner arc → both curve outward
        # (convex away from chart center, following the concentric circles).
        # Both flip when the houses run backwards: the endpoints are the same two
        # points either way, and it is the pair (sweep, large_arc) that says which
        # of the two arcs between them the wedge is. Keeping sweep while the span
        # shortens would pick the arc off a mirrored circle and lift the wedge
        # clean off its own ring.
        d = (
            f"M {ox1},{oy1} "
            f"A {outer_visual_r},{outer_visual_r} 0 {large_arc},{outer_sweep} {ox2},{oy2} "
            f"L {ix2},{iy2} "
            f"A {inner_visual_r},{inner_visual_r} 0 {large_arc},{inner_sweep} {ix1},{iy1} Z"
        )

        horoscope_attr = f' kr:horoscope="{horoscope_id}"' if horoscope_id else ""
        output += (
            f'<g kr:node="HouseSector" kr:house="{house_num}"{horoscope_attr}>'
            f'<path d="{d}" style="fill: transparent; stroke: none; pointer-events: all;"/>'
            f"</g>"
        )

    return output


# =============================================================================
# COORDINATE STRING FORMATTING
# =============================================================================


def _convert_coordinate_to_string(coord: Union[int, float], positive_label: str, negative_label: str) -> str:
    """
    Convert a coordinate (latitude or longitude) to a formatted string with cardinal direction.

    Args:
        coord: Coordinate in decimal degrees (negative values use negative_label).
        positive_label: Label for positive direction (e.g., "N", "E").
        negative_label: Label for negative direction (e.g., "S", "W").

    Returns:
        Formatted string (e.g., "52°7'25\" N").
    """
    sign = positive_label
    if coord < 0.0:
        sign = negative_label
        coord = abs(coord)
    total_seconds = int(round(float(coord) * 3600))
    deg, rem = divmod(total_seconds, 3600)
    minutes, sec = divmod(rem, 60)
    return f"{deg}°{minutes}'{sec}\" {sign}"


def convert_latitude_coordinate_to_string(coord: Union[int, float], north_label: str, south_label: str) -> str:
    """
    Convert latitude to a formatted string with cardinal direction.

    Args:
        coord: Latitude in decimal degrees (negative for south).
        north_label: Label for north (e.g., "N").
        south_label: Label for south (e.g., "S").

    Returns:
        Formatted string (e.g., "52°7'25\" N").
    """
    return _convert_coordinate_to_string(coord, north_label, south_label)


def convert_longitude_coordinate_to_string(coord: Union[int, float], east_label: str, west_label: str) -> str:
    """
    Convert longitude to a formatted string with cardinal direction.

    Args:
        coord: Longitude in decimal degrees (negative for west).
        east_label: Label for east (e.g., "E").
        west_label: Label for west (e.g., "W").

    Returns:
        Formatted string (e.g., "2°59'30\" W").
    """
    return _convert_coordinate_to_string(coord, east_label, west_label)


# =============================================================================
# SVG DRAWING FUNCTIONS - ASPECT LINES
# =============================================================================


def draw_aspect_line(
    r: Union[int, float],
    ar: Union[int, float],
    aspect: Union[AspectModel, dict],
    color: str,
    seventh_house_degree_ut: Union[int, float],
    show_aspect_icon: bool = True,
    rendered_icon_positions: Optional[list[tuple[float, float, int]]] = None,
    icon_collision_threshold: float = 16.0,
    show_aspect_movement: bool = False,
) -> str:
    """Draws svg aspects: ring, aspect ring, degreeA degreeB

    Args:
        - r (Union[int, float]): The value of r.
        - ar (Union[int, float]): The value of ar.
        - aspect_dict (dict): The aspect dictionary.
        - color (str): The color of the aspect.
        - seventh_house_degree_ut (Union[int, float]): The degree of the seventh house.
        - show_aspect_icon (bool): Whether to show the aspect icon at the center of the line.
        - rendered_icon_positions (list | None): List to track rendered icon positions (x, y, aspect_degrees)
            for collision detection. Only icons of the same aspect type will be checked for collision.
        - icon_collision_threshold (float): Minimum distance in pixels between icons to avoid overlap.

    Returns:
        str: The SVG line element as a string.
    """

    if isinstance(aspect, dict):
        aspect = AspectModel(**aspect)

    first_offset = -int(seventh_house_degree_ut) + int(aspect["p1_abs_pos"])
    x1 = wheel_x(0, ar, first_offset) + (r - ar)
    y1 = wheel_y(0, ar, first_offset) + (r - ar)

    second_offset = -int(seventh_house_degree_ut) + int(aspect["p2_abs_pos"])
    x2 = wheel_x(0, ar, second_offset) + (r - ar)
    y2 = wheel_y(0, ar, second_offset) + (r - ar)

    # Build the aspect icon SVG element if enabled
    aspect_icon_svg = ""
    if show_aspect_icon:
        # Calculate icon position
        if aspect["aspect_degrees"] == 0:
            # For conjunctions, place on the same angle but at a slightly larger radius
            # Use circular mean to handle wrap-around at 0°/360° correctly
            p1_rad = math.radians(aspect["p1_abs_pos"])
            p2_rad = math.radians(aspect["p2_abs_pos"])
            avg_sin = (math.sin(p1_rad) + math.sin(p2_rad)) / 2
            avg_cos = (math.cos(p1_rad) + math.cos(p2_rad)) / 2
            avg_pos = math.degrees(math.atan2(avg_sin, avg_cos)) % 360

            offset = -int(seventh_house_degree_ut) + avg_pos
            # Place at radius ar + 4 pixels outward
            icon_radius = ar + 4
            mid_x = wheel_x(0, icon_radius, offset) + (r - icon_radius)
            mid_y = wheel_y(0, icon_radius, offset) + (r - icon_radius)
        else:
            # For other aspects, use the midpoint of the line
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2

        # Check for collision with previously rendered icons OF THE SAME ASPECT TYPE
        # Different aspect types (e.g., opposition vs quincunx) are allowed to overlap
        should_render_icon = True
        current_aspect_degrees = aspect["aspect_degrees"]
        if rendered_icon_positions is not None:
            for existing_x, existing_y, existing_aspect_degrees in rendered_icon_positions:
                # Only check collision for same aspect type
                if existing_aspect_degrees == current_aspect_degrees:
                    distance = math.sqrt((mid_x - existing_x) ** 2 + (mid_y - existing_y) ** 2)
                    if distance < icon_collision_threshold:
                        should_render_icon = False
                        break

        if should_render_icon:
            # The aspect icon symbol ID is "orb" followed by the aspect degrees
            aspect_symbol_id = f"orb{aspect['aspect_degrees']}"
            # Center the icon (symbols are roughly 12x12, so offset by -6)
            icon_offset = 6
            aspect_icon_svg = (
                f'<use x="{mid_x - icon_offset}" y="{mid_y - icon_offset}" xlink:href="#{aspect_symbol_id}" />'
            )
            # Track this position and aspect type for future collision detection
            if rendered_icon_positions is not None:
                rendered_icon_positions.append((mid_x, mid_y, current_aspect_degrees))

    # A separating aspect is dashed only on request: the movement has always
    # been in the metadata, but drawing it changes how every existing chart looks.
    dash_style = (
        f" stroke-dasharray: {SEPARATING_DASH_ARRAY};"
        if show_aspect_movement and str(aspect["aspect_movement"]).lower() == "separating"
        else ""
    )

    return (
        f'<g kr:node="Aspect" kr:aspectname="{escape_svg_text(aspect["aspect"])}" kr:to="{escape_svg_text(aspect["p1_name"])}" kr:tooriginaldegrees="{aspect["p1_abs_pos"]}" kr:from="{escape_svg_text(aspect["p2_name"])}" kr:fromoriginaldegrees="{aspect["p2_abs_pos"]}" kr:orb="{aspect["orbit"]}" kr:aspectdegrees="{aspect["aspect_degrees"]}" kr:planetsdiff="{aspect["diff"]}" kr:aspectmovement="{aspect["aspect_movement"]}">'
        f'<line class="aspect" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {color}; stroke-width: 1; stroke-opacity: .9;{dash_style}"/>'
        f"{aspect_icon_svg}"
        f"</g>"
    )


def convert_decimal_to_degree_string(dec: float, format_type: Literal["1", "2", "3"] = "3") -> str:
    """
    Converts a decimal float to a degrees string in the specified format.

    Args:
        dec (float): The decimal float to convert.
        format_type (str): The format type:
            - "1": a°
            - "2": a°b'
            - "3": a°b'c" (default)

    Returns:
        str: The degrees string in the specified format.
    """
    # Ensure the input is a float
    dec = float(dec)

    # All three formats floor (toward negative infinity) the displayed unit via math.floor/divmod.
    # Flooring is consistent across formats (a within-sign 29.9999° reads "29°" in
    # format "1" and "29°59'59\"" in format "3", never an out-of-sign "30°00'00\""),
    # avoids the malformed negative fields int() produced ("-5°-30'", a truncation
    # toward zero), and never emits an out-of-range 60' or 60".
    if format_type == "1":
        return f"{math.floor(dec)}°"
    elif format_type == "2":
        degrees, minutes = divmod(math.floor(dec * 60), 60)
        return f"{degrees}°{minutes:02d}'"
    else:  # format_type == "3" (default) — always return a str matching the annotation
        # Floor to the second and carry via divmod, so the result can never contain
        # an invalid 60" nor overshoot the sign boundary (e.g. 29.9999° ->
        # "29°59'59\"", not "30°00'00\"").
        total_seconds = math.floor(dec * 3600)
        d, rem = divmod(total_seconds, 3600)
        m, s = divmod(rem, 60)
        # The arc-seconds mark is emitted as &quot; (not a literal ") because the
        # result lands in SVG <text> nodes: the post-processing pass rewrites
        # every literal double quote to a single quote (attribute style), which
        # would corrupt the seconds mark into an apostrophe on every chart.
        return f"{d}°{m:02d}'{s:02d}&quot;"


# =============================================================================
# SVG DRAWING FUNCTIONS - DEGREE RINGS AND MARKERS
# =============================================================================


def draw_transit_ring_degree_steps(r: Union[int, float], seventh_house_degree_ut: Union[int, float]) -> str:
    """
    Draw degree tick marks around the transit ring.

    Creates 72 tick marks at 5° intervals for visual reference.

    Args:
        r: Chart radius in pixels.
        seventh_house_degree_ut: 7th house position for alignment.

    Returns:
        SVG group element containing the tick marks.
    """
    out = '<g id="transitRingDegreeSteps">'
    for i in range(72):
        offset = float(i * 5) - seventh_house_degree_ut
        if offset < 0:
            offset = offset + 360.0
        elif offset > 360:
            offset = offset - 360.0
        x1 = wheel_x(0, r, offset)
        y1 = wheel_y(0, r, offset)
        x2 = wheel_x(0, r + 2, offset) - 2
        y2 = wheel_y(0, r + 2, offset) - 2
        out += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: #F00; stroke-width: 1px; stroke-opacity:.9;"/>'
    out += "</g>"

    return out


def draw_degree_ring(
    r: Union[int, float], c1: Union[int, float], seventh_house_degree_ut: Union[int, float], stroke_color: str
) -> str:
    """
    Draw degree tick marks around the main chart ring.

    Creates 72 tick marks at 5° intervals for visual reference.

    Args:
        r: Chart radius in pixels.
        c1: Inner offset in pixels.
        seventh_house_degree_ut: 7th house position for alignment.
        stroke_color: Color for the tick marks.

    Returns:
        str: The SVG path of the degree ring.
    """
    out = '<g id="degreeRing">'
    for i in range(72):
        offset = float(i * 5) - seventh_house_degree_ut
        if offset < 0:
            offset = offset + 360.0
        elif offset > 360:
            offset = offset - 360.0
        x1 = wheel_x(0, r - c1, offset) + c1
        y1 = wheel_y(0, r - c1, offset) + c1
        x2 = wheel_x(0, r + 2 - c1, offset) - 2 + c1
        y2 = wheel_y(0, r + 2 - c1, offset) - 2 + c1

        out += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {stroke_color}; stroke-width: 1px; stroke-opacity:.9;"/>'
    out += "</g>"

    return out


# =============================================================================
# SVG DRAWING FUNCTIONS - STRUCTURAL CIRCLES
# =============================================================================


def draw_transit_ring(r: Union[int, float], paper_1_color: str, zodiac_transit_ring_3_color: str) -> str:
    """
    Draw the transit ring for double-wheel charts.

    Args:
        r: Chart radius in pixels.
        paper_1_color: Color for the inner ring fill.
        zodiac_transit_ring_3_color: Color for the outer ring stroke.

    Returns:
        SVG circle elements for the transit ring.
    """
    radius_offset = 18

    out = f'<circle cx="{r}" cy="{r}" r="{r - radius_offset}" style="fill: none; stroke: {paper_1_color}; stroke-width: 36px; stroke-opacity: .4;"/>'
    out += f'<circle cx="{r}" cy="{r}" r="{r}" style="fill: none; stroke: {zodiac_transit_ring_3_color}; stroke-width: 1px; stroke-opacity: .6;"/>'

    return out


def draw_first_circle(
    r: Union[int, float], stroke_color: str, chart_type: ChartType, c1: Union[int, float, None] = None
) -> str:
    """
    Draw the first (outer) structural circle of the chart.

    Args:
        r: Chart radius in pixels.
        stroke_color: Stroke color for the circle.
        chart_type: Type of chart being rendered.
        c1: Inner offset (required for single-wheel charts).

    Returns:
        SVG circle element.

    Raises:
        KerykeionException: If c1 is None for single-wheel charts.
    """
    if chart_type in DOUBLE_CHART_TYPES:
        return f'<circle cx="{r}" cy="{r}" r="{r - 36}" style="fill: none; stroke: {stroke_color}; stroke-width: 1px; stroke-opacity:.4;" />'
    else:
        if c1 is None:
            raise KerykeionException("c1 is None")

        return (
            f'<circle cx="{r}" cy="{r}" r="{r - c1}" style="fill: none; stroke: {stroke_color}; stroke-width: 1px; " />'
        )


def draw_background_circle(r: Union[int, float], stroke_color: str, fill_color: str) -> str:
    """
    Draws the background circle.

    Args:
        - r (Union[int, float]): The value of r.
        - stroke_color (str): The color of the stroke.
        - fill_color (str): The color of the fill.

    Returns:
        str: The SVG path of the background circle.
    """
    return (
        f'<circle cx="{r}" cy="{r}" r="{r}" style="fill: {fill_color}; stroke: {stroke_color}; stroke-width: 1px;" />'
    )


def draw_second_circle(
    r: Union[int, float], stroke_color: str, fill_color: str, chart_type: ChartType, c2: Union[int, float, None] = None
) -> str:
    """
    Draws the second circle.

    Args:
        - r (Union[int, float]): The value of r.
        - stroke_color (str): The color of the stroke.
        - fill_color (str): The color of the fill.
        - chart_type (ChartType): The type of chart.
        - c2 (Union[int, float]): The value of c2.

    Returns:
        str: The SVG path of the second circle.
    """

    if chart_type in DOUBLE_CHART_TYPES:
        return f'<circle cx="{r}" cy="{r}" r="{r - 72}" style="fill: {fill_color}; fill-opacity:.4; stroke: {stroke_color}; stroke-opacity:.4; stroke-width: 1px" />'

    else:
        if c2 is None:
            raise KerykeionException("c2 is None")

        return f'<circle cx="{r}" cy="{r}" r="{r - c2}" style="fill: {fill_color}; fill-opacity:.2; stroke: {stroke_color}; stroke-opacity:.4; stroke-width: 1px" />'


def draw_third_circle(
    radius: Union[int, float], stroke_color: str, fill_color: str, chart_type: ChartType, c3: Union[int, float]
) -> str:
    """
    Draws the third circle in an SVG chart.

    Parameters:
    - radius (Union[int, float]): The radius of the circle.
    - stroke_color (str): The stroke color of the circle.
    - fill_color (str): The fill color of the circle.
    - chart_type (ChartType): The type of the chart.
    - c3 (Union[int, float, None], optional): The radius adjustment for non-Synastry and non-Transit charts.

    Returns:
    - str: The SVG element as a string.
    """
    if chart_type in DOUBLE_CHART_TYPES:
        # For double-wheel charts, use a fixed radius adjustment of 160
        return f'<circle cx="{radius}" cy="{radius}" r="{radius - 160}" style="fill: {fill_color}; fill-opacity:.8; stroke: {stroke_color}; stroke-width: 1px" />'

    else:
        return f'<circle cx="{radius}" cy="{radius}" r="{radius - c3}" style="fill: {fill_color}; fill-opacity:.8; stroke: {stroke_color}; stroke-width: 1px" />'


def draw_aspect_grid(
    stroke_color: str,
    available_planets: list,
    aspects: list,
    x_start: int = 510,
    y_start: int = 468,
    aspects_settings: Union[list, None] = None,
) -> str:
    """
    Draw the triangular aspect grid showing relationships between planets.

    This function generates a diagonal grid where each cell represents the
    aspect relationship between two planets. The grid is triangular because
    aspects are symmetric (A-B is the same as B-A).

    Args:
        stroke_color: CSS color for the grid lines.
        available_planets: List of planet dictionaries. Only planets with
            "is_active" set to True will be included in the grid.
        aspects: List of aspect dictionaries containing p1, p2, and aspect_degrees.
        x_start: X-coordinate for the bottom-left corner of the grid.
        y_start: Y-coordinate for the bottom-left corner of the grid.
        aspects_settings: Optional aspect settings list; when provided, aspects
            whose name has no settings entry (e.g. declination parallels, which
            have no orb glyph and would render as a conjunction) are skipped.

    Returns:
        SVG string containing the aspect grid rectangles and symbols.
    """
    style = f"stroke:{stroke_color}; stroke-width: 0.5px; fill:none"
    box_size = 14

    # Filter active planets
    active_planets = [planet for planet in available_planets if planet["is_active"]]

    # Reverse the list of active planets for the first iteration
    reversed_planets = active_planets[::-1]

    # Aspects without a settings entry share aspect_degrees with real aspects
    # (parallel has degree 0, same as conjunction): filter them out up front so
    # the grid can't draw the wrong glyph. None (no settings supplied) keeps
    # every aspect, preserving the legacy behaviour for external callers.
    known_aspect_names = {setting["name"] for setting in aspects_settings} if aspects_settings is not None else None

    # Pre-index aspects by unordered pair (O(k)) so the grid loop can look up aspects
    # in O(1) instead of scanning the full aspects list for every cell (was O(n^2 * k)).
    # Preserve original order when multiple aspects exist for the same pair (synastry).
    aspect_lookup: dict[tuple[int, int], list] = {}
    for aspect in aspects:
        if known_aspect_names is not None and aspect["aspect"] not in known_aspect_names:
            continue
        p1 = aspect["p1"]
        p2 = aspect["p2"]
        key = (p1, p2) if p1 <= p2 else (p2, p1)
        aspect_lookup.setdefault(key, []).append(aspect)

    parts: list[str] = []
    for index, planet_a in enumerate(reversed_planets):
        # Draw the grid box for the planet
        parts.append(
            f'<rect kr:node="AspectsGridRect" x="{x_start}" y="{y_start}" width="{box_size}" height="{box_size}" style="{style}"/>'
        )
        # v6: dynamic points fall back to their shared generic symbols.
        glyph_a = _resolve_point_glyph_id(planet_a["name"], planet_a)
        parts.append(
            f'<use transform="scale(0.4)" x="{(x_start + 2) * 2.5}" y="{(y_start + 1) * 2.5}" xlink:href="#{glyph_a}" />'
        )

        # Update the starting coordinates for the next box
        x_start += box_size
        y_start -= box_size

        # Coordinates for the aspect symbols
        x_aspect = x_start
        y_aspect = y_start + box_size

        planet_a_id = planet_a["id"]
        # Iterate over the remaining planets
        for planet_b in reversed_planets[index + 1 :]:
            # Draw the grid box for the aspect
            parts.append(
                f'<rect kr:node="AspectsGridRect" x="{x_aspect}" y="{y_aspect}" width="{box_size}" height="{box_size}" style="{style}"/>'
            )
            x_aspect += box_size

            # Check for aspects between the planets via pre-built index
            planet_b_id = planet_b["id"]
            key = (planet_a_id, planet_b_id) if planet_a_id <= planet_b_id else (planet_b_id, planet_a_id)
            matches = aspect_lookup.get(key)
            if matches:
                for aspect in matches:
                    parts.append(
                        f'<use  x="{x_aspect - box_size + 1}" y="{y_aspect + 1}" xlink:href="#orb{aspect["aspect_degrees"]}" />'
                    )

    return "".join(parts)


#: Cap height of a digit as a fraction of the font size. Figures in the fonts
#: these charts pin have no descender, so this is their whole inked height.
_DIGIT_CAP_HEIGHT_RATIO: float = 0.716

#: Font size the house numbers are drawn at, and the air wanted between two of
#: them. The gutter is halved into each label's own half-extent, so a pair gets
#: the whole of it and a label at the seam is not charged for a neighbour twice.
#:
#: Nothing, not three: when four cusps share three degrees the numbers have
#: nowhere honest to go, and Giacomo's call is that they should sit against each
#: other rather than march away from the houses they name. Zero here means the
#: inked figures just touch — the reach is a cap height, and figures carry no
#: descender, so touching is the tightest a stack can be drawn and still be
#: read. What a reader cannot do is work out which of four lines "11" belongs
#: to once it has been pushed a house away.
_HOUSE_NUMBER_FONT_SIZE: float = 14.0
_HOUSE_NUMBER_GUTTER: float = 0.0


def _house_number_half_extents(wanted_angles: "Sequence[float]", radius_px: float) -> list[float]:
    """How far each house number reaches along the wheel, in degrees.

    A number is drawn upright while the arc it sits on turns, so what one of
    them has to clear depends on where it is: at the top of the wheel two
    numbers stand side by side and their widths meet, on the flank they stack
    and only their heights do. Projecting the label box onto the tangent gives
    both ends of that and everything between — and the flanks are exactly where
    a quadrant system at high latitude piles four cusps into three degrees, so
    charging those pairs a full "12" of width walked the crowd out of its own
    houses.

    Measured at the angle each number *wants*, not the one it ends up at: the
    spread has to know the requirement before it can satisfy it. A label that
    moves far enough to change which way it stacks is one already inside a crowd
    being spread, where the estimate is a shade generous rather than short.
    """
    arc_per_degree = 2.0 * math.pi * radius_px / 360.0
    if arc_per_degree <= 0:
        return [0.0] * len(wanted_angles)

    half_height = _HOUSE_NUMBER_FONT_SIZE * _DIGIT_CAP_HEIGHT_RATIO / 2.0
    out = []
    for index, angle in enumerate(wanted_angles):
        half_width = estimate_text_width(str(index + 1), _HOUSE_NUMBER_FONT_SIZE) / 2.0
        radians = math.radians(angle)
        # The tangent at this angle is (-sin, -cos) in the drawing's frame, so
        # the width counts by |sin| and the height by |cos|.
        reach = half_width * abs(math.sin(radians)) + half_height * abs(math.cos(radians))
        out.append((reach + _HOUSE_NUMBER_GUTTER / 2.0) / arc_per_degree)
    return out


def draw_houses_cusps_and_text_number(
    r: Union[int, float],
    first_subject_houses_list: list[KerykeionPointModel],
    standard_house_cusp_color: str,
    first_house_color: str,
    tenth_house_color: str,
    seventh_house_color: str,
    fourth_house_color: str,
    c1: Union[int, float],
    c3: Union[int, float],
    chart_type: ChartType,
    second_subject_houses_list: Union[list[KerykeionPointModel], None] = None,
    transit_house_cusp_color: Union[str, None] = None,
    external_view: bool = False,
) -> str:
    """
    Draw the house cusp lines and house numbers for a chart.

    This function renders the 12 house cusp lines radiating from the center
    of the chart, with special colors for angular houses (1st, 4th, 7th, 10th).
    For dual-wheel charts, it also draws the secondary subject's house cusps.

    Args:
        r: Radius of the chart in pixels.
        first_subject_houses_list: List of house models for the primary subject.
        standard_house_cusp_color: Default CSS color for house cusp lines.
        first_house_color: CSS color for the Ascendant (1st house) cusp.
        tenth_house_color: CSS color for the Midheaven (10th house) cusp.
        seventh_house_color: CSS color for the Descendant (7th house) cusp.
        fourth_house_color: CSS color for the IC (4th house) cusp.
        c1: Inner radius offset for cusp lines.
        c3: Outer radius offset for cusp lines.
        chart_type: Type of chart being rendered.
        second_subject_houses_list: House models for secondary subject (Transit/Synastry).
        transit_house_cusp_color: CSS color for transit house cusps.
        external_view: If True, renders for external/traditional view mode.

    Returns:
        SVG string containing house cusp lines and numbered labels.

    Raises:
        KerykeionException: If chart_type requires second_subject_houses_list
            or transit_house_cusp_color but they are None.
    """

    parts: list[str] = []
    xr = 12

    # Where each house number wants to sit, and where it can actually go.
    #
    # The wanted angle is the middle of the sector, and the forward arc is what
    # defines that middle — not `degree_difference`, which returns the *shorter*
    # way round and so placed the number outside its own house whenever a house
    # ran past 180°, reachable with Placidus at high latitude. The halves are
    # kept as floats too: rounding each to a whole degree drifted every number
    # the same way by up to a third of its own width.
    #
    # Quadrant systems make houses wildly unequal — Campanus manages it at
    # Liverpool, Placidus inside the polar circle — and three or four numbers
    # then want the same few degrees. They are spread apart by the least
    # movement that separates them, which keeps a crowd centred on the houses
    # it belongs to instead of sliding it into the neighbouring quadrant.
    # Measured on the ring the number is drawn on, which is not the one the cusp
    # line ends at. A label's reach in degrees is its reach in pixels over the arc
    # a degree covers, so the radius divides straight into the answer: taken at
    # the line's inner end (r - c3 = 120 on a natal wheel) instead of the text's
    # own ring (r - 48 = 192), every extent came out 1.6x too large, and 1.95x on
    # a dual chart's inner ring. That is a wider push than the uniform figure this
    # replaced, so the crowd ended up further out of its houses than before.
    _number_dropin = 100 if external_view else (84 if chart_type in DOUBLE_CHART_TYPES else 48)
    _label_radius = r - _number_dropin
    # Truncated, like the cusp lines these numbers label. A truncated base with an
    # exact span sat the number up to half a degree off the middle of its own
    # wedge, and where two cusps share a whole degree - so their bases coincide -
    # the two half spans were the only thing separating them: the wheel read 10
    # before 9, and 4 before 3. The middle is measured in the direction the houses
    # run, which above the polar circle is not always forwards.
    _cusps = [float(int(_house.abs_pos)) for _house in first_subject_houses_list[:xr]]
    _spans, _reversed = house_spans(_cusps)
    _zero = -int(first_subject_houses_list[int(xr / 2)].abs_pos)
    _wanted = [
        _zero + _cusps[_i] + (-0.5 if _reversed[_i] else 0.5) * _spans[_i] for _i in range(xr)
    ]
    _placed = spread_around_wheel(
        _wanted,
        0.0,
        half_extents=_house_number_half_extents(_wanted, max(_label_radius, 1.0)),
    )

    # The outer wheel of a dual chart draws its own set, on a wider ring.
    _placed_second: list[float] = []
    if second_subject_houses_list is not None:
        # Exact, because the outer ring's cusp lines are: t_offset below keeps the
        # fraction. Truncating the base here while the line does not drifts the
        # number off its own line by up to a degree - four pixels out at this
        # radius - which is the mismatch draw_house_sectors already guards with
        # quantize_offsets_to_whole_degrees, one function over.
        _second_cusps = [_house.abs_pos for _house in second_subject_houses_list[:xr]]
        _second_spans, _second_reversed = house_spans(_second_cusps)
        _second_zero = -first_subject_houses_list[int(xr / 2)].abs_pos
        _second_wanted = [
            _second_zero
            + _second_cusps[_i]
            + (-0.5 if _second_reversed[_i] else 0.5) * _second_spans[_i]
            for _i in range(xr)
        ]
        _placed_second = spread_around_wheel(
            _second_wanted,
            0.0,
            half_extents=_house_number_half_extents(_second_wanted, max(r - 8, 1.0)),
        )

    for i in range(xr):
        # Determine offsets based on chart type
        dropin, roff, t_roff = (
            (160, 72, 36) if chart_type in DOUBLE_CHART_TYPES else (c3, c1, False)
        )

        # Calculate the offset for the current house cusp
        offset = -int(first_subject_houses_list[int(xr / 2)].abs_pos) + int(first_subject_houses_list[i].abs_pos)

        # Calculate the coordinates for the house cusp lines
        x1 = wheel_x(0, (r - dropin), offset) + dropin
        y1 = wheel_y(0, (r - dropin), offset) + dropin
        x2 = wheel_x(0, r - roff, offset) + roff
        y2 = wheel_y(0, r - roff, offset) + roff

        # Where the number goes, after spreading (see above).
        text_offset = _placed[i]

        # Determine the line color based on the house index
        linecolor = {0: first_house_color, 9: tenth_house_color, 6: seventh_house_color, 3: fourth_house_color}.get(
            i, standard_house_cusp_color
        )

        if chart_type in DOUBLE_CHART_TYPES:
            if second_subject_houses_list is None or transit_house_cusp_color is None:
                raise KerykeionException(
                    "second_subject_houses_list or transit_house_cusp_color is None for dual-wheel chart"
                )

            # Calculate the offset for the second subject's house cusp
            zeropoint = 360 - first_subject_houses_list[6].abs_pos
            t_offset = (zeropoint + second_subject_houses_list[i].abs_pos) % 360

            # Calculate the coordinates for the second subject's house cusp lines
            t_x1 = wheel_x(0, (r - t_roff), t_offset) + t_roff
            t_y1 = wheel_y(0, (r - t_roff), t_offset) + t_roff
            t_x2 = wheel_x(0, r, t_offset)
            t_y2 = wheel_y(0, r, t_offset)

            # Where the outer wheel's number goes, spread the same way (see above).
            t_text_offset = _placed_second[i]
            t_linecolor = linecolor if i in [0, 9, 6, 3] else transit_house_cusp_color
            xtext = wheel_x(0, (r - 8), t_text_offset) + 8
            ytext = wheel_y(0, (r - 8), t_text_offset) + 8

            # Add the house number text for the second subject
            fill_opacity = "0" if chart_type == "Transit" else ".4"
            parts.append(f'<g kr:node="HouseNumber" kr:house="{i + 1}" kr:horoscope="1">')
            parts.append(
                f'<text style="fill: var(--kerykeion-chart-color-house-number); fill-opacity: {fill_opacity}; font-size: 14px"><tspan x="{xtext - 3}" y="{ytext + 3}">{i + 1}</tspan></text>'
            )
            parts.append("</g>")

            # Add the house cusp line for the second subject
            stroke_opacity = "0" if chart_type == "Transit" else ".3"
            parts.append(
                f'<g kr:node="Cusp" kr:absoluteposition="{second_subject_houses_list[i].abs_pos}" kr:signposition="{second_subject_houses_list[i].position}" kr:sign="{second_subject_houses_list[i].sign}" kr:slug="{escape_svg_text(second_subject_houses_list[i].name)}" kr:horoscope="1">'
            )
            parts.append(
                f"<line x1='{t_x1}' y1='{t_y1}' x2='{t_x2}' y2='{t_y2}' style='stroke: {t_linecolor}; stroke-width: 1px; stroke-opacity:{stroke_opacity};'/>"
            )
            parts.append("</g>")

        # The same inset the extents above were measured at, so the room a label
        # was given is the room it has where it lands.
        dropin = _number_dropin
        xtext = wheel_x(0, (r - dropin), text_offset) + dropin
        ytext = wheel_y(0, (r - dropin), text_offset) + dropin

        # Add the house cusp line for the first subject
        parts.append(
            f'<g kr:node="Cusp" kr:absoluteposition="{first_subject_houses_list[i].abs_pos}" kr:signposition="{first_subject_houses_list[i].position}" kr:sign="{first_subject_houses_list[i].sign}" kr:slug="{escape_svg_text(first_subject_houses_list[i].name)}" kr:horoscope="0">'
        )
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {linecolor}; stroke-width: 1px; stroke-dasharray:3,2; stroke-opacity:.4;"/>'
        )
        parts.append("</g>")

        # Add the house number text for the first subject
        parts.append(f'<g kr:node="HouseNumber" kr:house="{i + 1}" kr:horoscope="0">')
        parts.append(
            f'<text style="fill: var(--kerykeion-chart-color-house-number); fill-opacity: .6; font-size: 14px"><tspan x="{xtext - 3}" y="{ytext + 3}">{i + 1}</tspan></text>'
        )
        parts.append("</g>")

    return "".join(parts)


def draw_transit_aspect_list(
    grid_title: str,
    aspects_list: Union[list[AspectModel], list[dict]],
    celestial_point_language: Union[
        KerykeionLanguageCelestialPointModel, Mapping[str, Mapping[str, str]], Sequence[Mapping[str, str]]
    ],
    aspects_settings: Sequence[Mapping[str, str]],
    *,
    aspects_per_column: int = 14,
    column_width: int = 100,
    line_height: int = 14,
    max_columns: int = 6,
    chart_height: Optional[Union[int, float]] = None,
    x_offset: int = 565,
    y_offset: int = 273,
) -> str:
    """
    Generate SVG output for the aspect list panel in transit/synastry charts.

    This function creates a multi-column list showing all active aspects
    between planets, with their orbs and aspect symbols. The layout
    dynamically adjusts columns based on the number of aspects.

    Args:
        grid_title: Title displayed above the aspect list.
        aspects_list: List of AspectModel instances or aspect dictionaries.
        celestial_point_language: Language model for translating planet names.
        aspects_settings: Dictionary mapping aspect names to their settings.
        aspects_per_column: Maximum aspects per column before wrapping.
        column_width: Width of each column in pixels.
        line_height: Vertical spacing between aspect rows in pixels.
        max_columns: Maximum columns before using vertical space optimization.
        chart_height: Total chart height for calculating extended column capacity.
        x_offset: Horizontal origin of the aspect list group (default 565).
        y_offset: Vertical origin of the aspect list group (default 273).

    Returns:
        SVG string containing the formatted aspect list with title.
    """

    if isinstance(celestial_point_language, dict):
        celestial_point_language = KerykeionLanguageCelestialPointModel(**celestial_point_language)

    # If not instance of AspectModel, convert to AspectModel
    if aspects_list and isinstance(aspects_list[0], dict):
        aspects_list = [AspectModel(**aspect) for aspect in aspects_list]  # type: ignore

    # Type narrowing: at this point aspects_list contains AspectModel instances
    typed_aspects_list: list[AspectModel] = aspects_list  # type: ignore

    translate_x = x_offset
    translate_y = y_offset
    title_clearance = 18
    top_limit_y: float = -translate_y + title_clearance
    bottom_padding = 40
    baseline_index = aspects_per_column - 1
    top_limit_index = math.ceil(top_limit_y / line_height)
    # `top_limit_index` identifies the highest row index we can reach without
    # touching the title block. Combined with the baseline index we know how many
    # rows a "tall" column may contain.
    max_capacity_by_top = baseline_index - top_limit_index + 1

    inner_path = ""

    full_height_column_index = 10  # 0-based index → 11th column onward
    if chart_height is not None:
        available_height = max(chart_height - translate_y - bottom_padding, line_height)
        allowed_capacity = max(aspects_per_column, int(available_height // line_height))
        full_height_capacity = max(aspects_per_column, min(allowed_capacity, max_capacity_by_top))
    else:
        full_height_capacity = aspects_per_column

    # Bucket aspects into columns while respecting the capacity of each column.
    columns: list[list[AspectModel]] = []
    column_capacities: list[int] = []

    for aspect in typed_aspects_list:
        if not columns or len(columns[-1]) >= column_capacities[-1]:
            new_col_index = len(columns)
            capacity = aspects_per_column if new_col_index < full_height_column_index else full_height_capacity
            capacity = max(capacity, 1)
            columns.append([])
            column_capacities.append(capacity)
        columns[-1].append(aspect)

    for col_idx, column in enumerate(columns):
        capacity = column_capacities[col_idx]
        horizontal_position = col_idx * column_width
        column_len = len(column)

        for row_idx, aspect in enumerate(column):
            # Default top-aligned placement
            vertical_position = row_idx * line_height

            # Full-height columns reuse the shared baseline so every column
            # finishes at the same vertical position and grows upwards.
            if col_idx >= full_height_column_index:
                vertical_index = baseline_index - (column_len - 1 - row_idx)
                vertical_position = vertical_index * line_height
            # Legacy overflow columns (before the 12th) keep the older behaviour:
            # once we exceed the configured column count, bottom-align the content
            # so the shorter columns do not look awkwardly padded at the top.
            elif col_idx >= max_columns and capacity == aspects_per_column:
                top_offset_lines = max(0, capacity - len(column))
                vertical_position = (top_offset_lines + row_idx) * line_height

            inner_path += f'<g transform="translate({horizontal_position},{vertical_position})">'

            p1_glyph = _resolve_point_glyph_id(aspect["p1_name"])
            p2_glyph = _resolve_point_glyph_id(aspect["p2_name"])

            # First planet symbol
            inner_path += f'<use transform="scale(0.4)" x="0" y="3" xlink:href="#{p1_glyph}" />'

            # Aspect symbol. Aspects without a settings entry (e.g.
            # parallel/contra-parallel with the default set) have no orb glyph
            # in the template: skip the symbol instead of emitting a dangling
            # xlink:href="#orbNone", matching _draw_all_aspects_lines.
            aspect_name = aspect["aspect"]
            id_value = next((a["degree"] for a in aspects_settings if a["name"] == aspect_name), None)  # type: ignore
            if id_value is not None:
                inner_path += f'<use x="15" y="0" xlink:href="#orb{id_value}" />'

            # Second planet symbol
            inner_path += '<g transform="translate(30,0)">'
            inner_path += f'<use transform="scale(0.4)" x="0" y="3" xlink:href="#{p2_glyph}" />'
            inner_path += "</g>"

            # Difference in degrees
            inner_path += f'<text y="8" x="45" style="fill: var(--kerykeion-chart-color-paper-0); font-size: 10px;">{convert_decimal_to_degree_string(aspect["orbit"])}</text>'

            inner_path += "</g>"

    out = f'<g transform="translate({translate_x},{translate_y})">'
    out += (
        f'<text y="-15" x="0" style="fill: var(--kerykeion-chart-color-paper-0); font-size: 14px;">{escape_svg_text(grid_title)}:</text>'
    )
    out += inner_path
    out += "</g>"

    return out


def calculate_moon_phase_chart_params(degrees_between_sun_and_moon: float) -> dict:
    """
    Calculate normalized parameters used by the moon phase icon.

    This function computes the geometric parameters needed to render an accurate
    lunar phase visualization based on the angular separation between the Sun
    and Moon.

    Args:
        degrees_between_sun_and_moon: The elongation (angular separation) between
            the Sun and Moon in degrees. Values are normalized to 0-360 range.

    Returns:
        Dictionary containing:
            - phase_angle: Normalized angle (0-360 degrees)
            - illuminated_fraction: Fraction of moon illuminated (0.0 to 1.0)
            - shadow_ellipse_rx: Horizontal radius for the shadow ellipse

    Raises:
        KerykeionException: If degrees_between_sun_and_moon is not a finite number.
    """
    if not math.isfinite(degrees_between_sun_and_moon):
        raise KerykeionException(f"Invalid degree value: {degrees_between_sun_and_moon}")

    phase_angle = degrees_between_sun_and_moon % 360.0
    radians = math.radians(phase_angle)
    cosine = math.cos(radians)
    illuminated_fraction = (1.0 - cosine) / 2.0

    # Guard against floating point spillover outside [0, 1].
    illuminated_fraction = max(0.0, min(1.0, illuminated_fraction))

    return {
        "phase_angle": phase_angle,
        "illuminated_fraction": illuminated_fraction,
        "shadow_ellipse_rx": 10.0 * cosine,
    }


# =============================================================================
# SVG DRAWING FUNCTIONS - HOUSE GRIDS
# Note: draw_main_house_grid and draw_secondary_house_grid are kept separate
# for API compatibility, though they share the same implementation logic.
# =============================================================================


def draw_main_house_grid(
    main_subject_houses_list: list[KerykeionPointModel],
    house_cusp_generale_name_label: str = "Cusp",
    text_color: str = "#000000",
    x_position: int = 750,
    y_position: int = 30,
) -> str:
    """
    Generate SVG code for a grid of astrological houses for the main subject.

    Parameters:
    - main_subject_houses_list (list[KerykeionPointModel]): List of houses for the main subject.
    - house_cusp_generale_name_label (str): Label for the house cusp. Defaults to "Cusp".
    - text_color (str): Color of the text. Defaults to "#000000".
    - x_position (int): X position for the grid. Defaults to 750.
    - y_position (int): Y position for the grid. Defaults to 30.

    Returns:
    - str: The SVG code for the grid of houses.
    """
    svg_output = f'<g transform="translate({x_position},{y_position})">'

    line_increment = 10
    for i, house in enumerate(main_subject_houses_list):
        cusp_number = f"&#160;&#160;{i + 1}" if i < 9 else str(i + 1)
        svg_output += (
            f'<g transform="translate(0,{line_increment})">'
            f'<text text-anchor="end" x="40" style="fill:{text_color}; font-size: 10px;">{escape_svg_text(house_cusp_generale_name_label)} {cusp_number}:</text>'
            f'<g transform="translate(40,-8)"><use transform="scale(0.3)" xlink:href="#{house["sign"]}" /></g>'
            f'<text x="53" style="fill:{text_color}; font-size: 10px;"> {convert_decimal_to_degree_string(house["position"])}</text>'
            f"</g>"
        )
        line_increment += 14

    svg_output += "</g>"
    return svg_output


def draw_secondary_house_grid(
    secondary_subject_houses_list: list[KerykeionPointModel],
    house_cusp_generale_name_label: str = "Cusp",
    text_color: str = "#000000",
    x_position: int = 1015,
    y_position: int = 30,
) -> str:
    """
    Generate SVG code for a grid of astrological houses for the secondary subject.

    Parameters:
    - secondary_subject_houses_list (list[KerykeionPointModel]): List of houses for the secondary subject.
    - house_cusp_generale_name_label (str): Label for the house cusp. Defaults to "Cusp".
    - text_color (str): Color of the text. Defaults to "#000000".
    - x_position (int): X position for the grid. Defaults to 1015.
    - y_position (int): Y position for the grid. Defaults to 30.

    Returns:
    - str: The SVG code for the grid of houses.
    """
    svg_output = f'<g transform="translate({x_position},{y_position})">'

    line_increment = 10
    for i, house in enumerate(secondary_subject_houses_list):
        cusp_number = f"&#160;&#160;{i + 1}" if i < 9 else str(i + 1)
        svg_output += (
            f'<g transform="translate(0,{line_increment})">'
            f'<text text-anchor="end" x="40" style="fill:{text_color}; font-size: 10px;">{escape_svg_text(house_cusp_generale_name_label)} {cusp_number}:</text>'
            f'<g transform="translate(40,-8)"><use transform="scale(0.3)" xlink:href="#{house["sign"]}" /></g>'
            f'<text x="53" style="fill:{text_color}; font-size: 10px;"> {convert_decimal_to_degree_string(house["position"])}</text>'
            f"</g>"
        )
        line_increment += 14

    svg_output += "</g>"
    return svg_output


def _gauquelin_grid_thresholds(n: int) -> tuple[int, int, int]:
    """Return column thresholds for the Gauquelin unified grid.

    Uses balanced distribution across columns, with a maximum of
    ``_GAUQUELIN_MAX_ROWS`` rows per column.

    Args:
        n: Total number of Gauquelin points.

    Returns:
        Tuple of (second, third, fourth) column thresholds.
    """
    if n <= _GAUQUELIN_MAX_ROWS:
        return (_GAUQUELIN_MAX_ROWS, _GAUQUELIN_MAX_ROWS * 2, _GAUQUELIN_MAX_ROWS * 3)
    num_cols = min(4, max(1, math.ceil(n / _GAUQUELIN_MAX_ROWS)))
    rows_per_col = math.ceil(n / num_cols)
    return (rows_per_col, rows_per_col * 2, rows_per_col * 3)


def _gauquelin_grid_layout_position(index: int, thresholds: tuple[int, int, int], column_width: Optional[int] = None) -> tuple[int, int]:
    """Calculate grid position for a point in the Gauquelin unified grid.

    Args:
        index: Zero-based index of the point.
        thresholds: Column thresholds from ``_gauquelin_grid_thresholds``.

    Returns:
        Tuple of (horizontal_offset, row_index).
    """
    t2, t3, t4 = thresholds
    if index < t2:
        col, row = 0, index
    elif index < t3:
        col, row = 1, index - t2
    elif index < t4:
        col, row = 2, index - t3
    else:
        col, row = 3, index - t4
    offset = -((column_width if column_width is not None else _GAUQUELIN_COLUMN_WIDTH) * col)
    return offset, row


def draw_gauquelin_unified_grid(
    celestial_points: list,
    text_color: str = "#000000",
    x_position: int = 645,
    y_position: int = 0,
    celestial_point_language: Optional["KerykeionLanguageCelestialPointModel"] = None,
    plus_zone_color: str = "var(--kerykeion-color-warning, #e6a817)",
    show_out_of_bounds: bool = False,
) -> str:
    """Unified Gauquelin table replacing both planet grid and house cusp grid.

    Renders a single table showing for each celestial point:
    Name | Sign Glyph | Longitude | R | Declination | Sector

    Supports multi-column layout for >18 points (columns extend leftward,
    using the same pattern as the standard planet grid). Sector values in
    "plus zones" (36, 1, 9, 10, 18, 19, 27, 28) are highlighted.

    Args:
        celestial_points: All active KerykeionPointModel instances.
        text_color: Default text fill color.
        x_position: SVG X offset for the table.
        y_position: SVG Y offset for the table.
        celestial_point_language: Language model for localized point names.
        plus_zone_color: Color for plus-zone sector highlighting.

    Returns:
        SVG string with the unified Gauquelin table.
    """
    gauq_points = [p for p in celestial_points if hasattr(p, "gauquelin_sector") and p.gauquelin_sector is not None]
    if not gauq_points:
        return ""

    n = len(gauq_points)

    # Adaptive sizing based on point count
    if n <= 16:
        row_h = 14
        fs = 10
        glyph_s = 0.3
        max_name_len = 10
    elif n <= 24:
        row_h = 12
        fs = 9
        glyph_s = 0.27
        max_name_len = 9
    else:
        row_h = 10
        fs = 8
        glyph_s = 0.22
        max_name_len = 8

    # Column positions within each ~220px column
    COL_NAME_END = 55  # Name text-anchor="end"
    COL_SIGN = 58  # Sign glyph
    COL_LONG = 70  # Longitude text start
    COL_DECL = 135  # Declination text start
    COL_SECTOR_END = 212  # Sector text-anchor="end"

    # The badge only earns its extra width when a body actually needs it, so
    # switching the option on for a table with nothing out of bounds leaves the
    # layout exactly as it was.
    badge_shown = show_out_of_bounds and any(getattr(p, "is_out_of_bounds", None) for p in gauq_points)
    COL_SECTOR_END = COL_SECTOR_END + (_GAUQUELIN_OOB_BADGE_WIDTH if badge_shown else 0)
    column_width = gauquelin_column_width(badge_shown)

    # Multi-column thresholds
    thresholds = _gauquelin_grid_thresholds(n)

    # Determine number of columns for header replication
    t2, t3, t4 = thresholds
    if n <= t2:
        num_cols = 1
    elif n <= t3:
        num_cols = 2
    elif n <= t4:
        num_cols = 3
    else:
        num_cols = 4

    svg = f'<g transform="translate({x_position},{y_position})">'

    # Title
    svg += f'<text style="fill:{text_color}; font-size:{fs + 2}px; font-weight:bold;" y="12">Gauquelin Sectors</text>'

    # Column headers — draw for each column so all columns have labels
    hdr_y = 24
    hdr_fs = max(fs - 1, 7)
    for col in range(num_cols):
        col_offset = -(column_width * col)
        svg += (
            f'<g transform="translate({col_offset},{hdr_y})" opacity="0.55">'
            f'<text text-anchor="end" x="{COL_NAME_END}" style="fill:{text_color}; font-size:{hdr_fs}px;">Planet</text>'
            f'<text x="{COL_LONG}" style="fill:{text_color}; font-size:{hdr_fs}px;">Longitude</text>'
            f'<text x="{COL_DECL}" style="fill:{text_color}; font-size:{hdr_fs}px;">Decl.</text>'
            f'<text text-anchor="end" x="{COL_SECTOR_END}" style="fill:{text_color}; font-size:{hdr_fs}px;">Sector</text>'
            f"</g>"
        )

    BASE_Y = 30  # Below title + header

    for i, point in enumerate(gauq_points):
        offset, row_index = _gauquelin_grid_layout_position(i, thresholds, column_width)
        y = BASE_Y + 10 + row_index * row_h

        # Get display name (localized, with fallback)
        if celestial_point_language is not None:
            try:
                name = get_decoded_kerykeion_celestial_point_name(point.name, celestial_point_language)
            except Exception:
                name = point.name.replace("_", " ")
        else:
            name = point.name.replace("_", " ")
        if len(name) > max_name_len:
            name = name[: max_name_len - 1] + "."

        # Longitude string + retrograde marker
        long_str = convert_decimal_to_degree_string(point.position)
        r_str = " R" if point.retrograde else ""
        # Out of bounds is a claim about the declination, so it rides on that
        # column instead of asking the table for a new one.
        oob_str = " OOB" if show_out_of_bounds and getattr(point, "is_out_of_bounds", None) else ""

        # Declination in DMS
        decl = getattr(point, "declination", None)
        if decl is not None:
            da = abs(decl)
            dd = int(da)
            dm = int((da - dd) * 60)
            ds = int(((da - dd) * 60 - dm) * 60)
            decl_dir = "N" if decl >= 0 else "S"
            # &quot; instead of a literal ": see convert_decimal_to_degree_string.
            decl_str = f"{dd:02d}°{dm:02d}'{ds:02d}&quot;{decl_dir}"
        else:
            decl_str = ""

        # Sector with plus-zone highlighting
        sector = point.gauquelin_sector
        sector_int = int(sector)
        sector_str = f"{sector:.2f}"
        is_plus = sector_int in _GAUQUELIN_PLUS_ZONES
        sec_color = plus_zone_color if is_plus else text_color
        sec_weight = "bold" if is_plus else "normal"

        glyph_y = int(glyph_s * 24)

        svg += f'<g transform="translate({offset},{y})">'
        # Planet name (right-aligned)
        svg += f'<text text-anchor="end" x="{COL_NAME_END}" style="fill:{text_color}; font-size:{fs}px;">{escape_svg_text(name)}</text>'
        # Sign glyph
        svg += (
            f'<g transform="translate({COL_SIGN},-{glyph_y})">'
            f'<use transform="scale({glyph_s})" xlink:href="#{point.sign}" /></g>'
        )
        # Longitude + retrograde
        svg += f'<text x="{COL_LONG}" style="fill:{text_color}; font-size:{fs}px;">{long_str}{r_str}</text>'
        # Declination
        svg += f'<text x="{COL_DECL}" style="fill:{text_color}; font-size:{fs}px;">{decl_str}{oob_str}</text>'
        # Sector (highlighted if plus zone)
        svg += (
            f'<text text-anchor="end" x="{COL_SECTOR_END}" '
            f'style="fill:{sec_color}; font-size:{fs}px; font-weight:{sec_weight};">'
            f"{sector_str}</text>"
        )
        svg += "</g>"

    svg += "</g>"
    return svg


# =============================================================================
# SVG DRAWING FUNCTIONS - PLANET GRIDS
# Functions for rendering planet information tables in the chart sidebar.
# =============================================================================


def _grid_point_label(point_name: str, celestial_point_language) -> str:
    """The name a planet grid prints: decoded for the language, then capped.

    One function for both grids and for the stride that spaces their columns —
    a stride measured on the full name while the row draws the short one leaves
    a gap nobody asked for, and the reverse overlaps.
    """
    return abbreviate_point_name(
        get_decoded_kerykeion_celestial_point_name(point_name, celestial_point_language)
    )


def draw_main_planet_grid(
    planets_and_houses_grid_title: str,
    subject_name: str,
    available_kerykeion_celestial_points: list[KerykeionPointModel],
    chart_type: ChartType,
    celestial_point_language: KerykeionLanguageCelestialPointModel,
    text_color: str = "#000000",
    x_position: int = 645,
    y_position: int = 0,
    show_out_of_bounds: bool = False,
) -> str:
    """
    Draw the planet grid (main subject) and optional title.

    The entire output is wrapped in a single SVG group `<g>` so the
    whole block can be repositioned by changing the group transform.

    Args:
        planets_and_houses_grid_title: Title prefix to show for eligible chart types.
        subject_name: Subject name to append to the title.
        available_kerykeion_celestial_points: Celestial points to render in the grid.
        chart_type: Chart type identifier (Literal string).
        celestial_point_language: Language model for celestial point decoding.
        text_color: Text color for labels (default: "#000000").
        x_position: X translation applied to the outer `<g>` (default: 645).
        y_position: Y translation applied to the outer `<g>` (default: 0).

    Returns:
        SVG string for the main planet grid wrapped in a `<g>`.
    """
    # Layout constants (kept identical to previous behavior)
    BASE_Y = 30
    HEADER_Y = 15  # Title baseline inside the wrapper
    LINE_START = 10
    LINE_STEP = 14

    # Wrap everything inside a single group so position can be changed once
    svg_output = f'<g transform="translate({x_position},{y_position})">'

    # Add title only for specific chart types
    if chart_type in DOUBLE_CHART_TYPES:
        svg_output += (
            f'<g transform="translate(0, {HEADER_Y})">'
            f'<text style="fill:{text_color}; font-size: 14px;">{escape_svg_text(planets_and_houses_grid_title)} {escape_svg_text(subject_name)}</text>'
            f"</g>"
        )

    end_of_line = "</g>"

    column_thresholds = _select_planet_grid_thresholds(chart_type, len(available_kerykeion_celestial_points))

    # Sized from the names this grid will actually print, so a chart of short
    # names keeps the stride it always had and one carrying "N. Node (M)" gets
    # the room that name needs.
    column_width = planet_grid_column_width(
        [_grid_point_label(p["name"], celestial_point_language) for p in available_kerykeion_celestial_points],
        show_out_of_bounds,
    )

    for i, planet in enumerate(available_kerykeion_celestial_points):
        offset, row_index = _planet_grid_layout_position(i, column_thresholds, column_width)
        line_height = LINE_START + (row_index * LINE_STEP)

        decoded_name = _grid_point_label(planet["name"], celestial_point_language)

        # v6: dynamic points without dedicated symbols fall back to shared glyphs.
        planet_glyph = _resolve_point_glyph_id(planet["name"])
        svg_output += (
            f'<g transform="translate({offset},{BASE_Y + line_height})">'
            f'<text text-anchor="end" style="fill:{text_color}; font-size: 10px;">{escape_svg_text(decoded_name)}</text>'
            f'<g transform="translate(5,-8)"><use transform="scale(0.4)" xlink:href="#{planet_glyph}" /></g>'
            f'<text text-anchor="end" x="{_GRID_READING_RIGHT}" style="fill:{text_color}; font-size: 10px;">{convert_decimal_to_degree_string(planet["position"])}</text>'
            f'<g transform="translate({_GRID_SIGN_X},-8)"><use transform="scale(0.3)" xlink:href="#{planet["sign"]}" /></g>'
        )

        if planet["retrograde"]:
            svg_output += f'<g transform="translate({_GRID_RETROGRADE_X},-6)"><use transform="scale(.5)" xlink:href="#retrograde" /></g>'

        if show_out_of_bounds:
            svg_output += out_of_bounds_badge_svg(planet, text_color)

        svg_output += end_of_line

    # Close the wrapper group
    svg_output += "</g>"

    return svg_output


def draw_secondary_planet_grid(
    planets_and_houses_grid_title: str,
    second_subject_name: str,
    second_subject_available_kerykeion_celestial_points: list[KerykeionPointModel],
    chart_type: ChartType,
    celestial_point_language: KerykeionLanguageCelestialPointModel,
    text_color: str = "#000000",
    x_position: int = 910,
    y_position: int = 0,
    show_out_of_bounds: bool = False,
) -> str:
    """
    Draw the planet grid for the secondary subject and its title.

    The entire output is wrapped in a single SVG group `<g>` so the
    whole block can be repositioned by changing the group transform.

    Args:
        planets_and_houses_grid_title: Title prefix (used except for Transit charts).
        second_subject_name: Name of the secondary subject.
        second_subject_available_kerykeion_celestial_points: Celestial points to render for the secondary subject.
        chart_type: Chart type identifier (Literal string).
        celestial_point_language: Language model for celestial point decoding.
        text_color: Text color for labels (default: "#000000").
        x_position: X translation applied to the outer `<g>` (default: 910).
        y_position: Y translation applied to the outer `<g>` (default: 0).

    Returns:
        SVG string for the secondary planet grid wrapped in a `<g>`.
    """
    # Layout constants
    BASE_Y = 30
    HEADER_Y = 15
    LINE_START = 10
    LINE_STEP = 14

    # Open wrapper group
    svg_output = f'<g transform="translate({x_position},{y_position})">'

    # Title content and its relative x offset
    _transit_like = chart_type in _TRANSIT_LIKE_HEADER_TYPES
    header_text = (
        second_subject_name if _transit_like else f"{planets_and_houses_grid_title} {second_subject_name}"
    )
    header_x_offset = -50 if _transit_like else 0

    svg_output += (
        f'<g transform="translate({header_x_offset}, {HEADER_Y})">'
        f'<text style="fill:{text_color}; font-size: 14px;">{escape_svg_text(header_text)}</text>'
        f"</g>"
    )

    # Grid rows
    line_height = LINE_START
    end_of_line = "</g>"

    column_thresholds = _select_planet_grid_thresholds(
        chart_type, len(second_subject_available_kerykeion_celestial_points)
    )

    # Sized from the names this grid will actually print, so a chart of short
    # names keeps the stride it always had and one carrying "N. Node (M)" gets
    # the room that name needs.
    column_width = planet_grid_column_width(
        [_grid_point_label(p["name"], celestial_point_language) for p in second_subject_available_kerykeion_celestial_points],
        show_out_of_bounds,
    )

    for i, t_planet in enumerate(second_subject_available_kerykeion_celestial_points):
        offset, row_index = _planet_grid_layout_position(i, column_thresholds, column_width)
        line_height = LINE_START + (row_index * LINE_STEP)

        second_decoded_name = _grid_point_label(t_planet["name"], celestial_point_language)
        t_planet_glyph = _resolve_point_glyph_id(t_planet["name"])
        svg_output += (
            f'<g transform="translate({offset},{BASE_Y + line_height})">'
            f'<text text-anchor="end" style="fill:{text_color}; font-size: 10px;">{escape_svg_text(second_decoded_name)}</text>'
            f'<g transform="translate(5,-8)"><use transform="scale(0.4)" xlink:href="#{t_planet_glyph}" /></g>'
            f'<text text-anchor="end" x="{_GRID_READING_RIGHT}" style="fill:{text_color}; font-size: 10px;">{convert_decimal_to_degree_string(t_planet["position"])}</text>'
            f'<g transform="translate({_GRID_SIGN_X},-8)"><use transform="scale(0.3)" xlink:href="#{t_planet["sign"]}" /></g>'
        )

        if t_planet["retrograde"]:
            svg_output += f'<g transform="translate({_GRID_RETROGRADE_X},-6)"><use transform="scale(.5)" xlink:href="#retrograde" /></g>'

        if show_out_of_bounds:
            svg_output += out_of_bounds_badge_svg(t_planet, text_color)

        svg_output += end_of_line

    # Close wrapper group
    svg_output += "</g>"

    return svg_output


# =============================================================================
# SVG DRAWING FUNCTIONS - ASPECT GRIDS
# Functions for rendering aspect relationship grids in natal and transit charts.
# =============================================================================


def draw_transit_aspect_grid(
    stroke_color: str,
    available_planets: list,
    aspects: list,
    x_indent: int = 50,
    y_indent: int = 250,
    box_size: int = 14,
    aspects_settings: Union[list, None] = None,
) -> str:
    """
    Draw a rectangular aspect grid for transit charts.

    Unlike the triangular natal aspect grid, this grid shows all planet
    combinations in a full matrix format, suitable for comparing aspects
    between natal and transit planets.

    Args:
        stroke_color: CSS color for the grid lines.
        available_planets: List of planet dictionaries. Only planets with
            "is_active" set to True will be included.
        aspects: List of aspect dictionaries containing p1, p2, and aspect_degrees.
        x_indent: X-coordinate for the grid's left edge.
        y_indent: Y-coordinate for the grid's top edge.
        box_size: Width and height of each grid cell in pixels.
        aspects_settings: Optional aspect settings list; when provided, aspects
            whose name has no settings entry (e.g. declination parallels, which
            have no orb glyph and would render as a conjunction) are skipped.

    Returns:
        SVG string containing the transit aspect grid.
        str: SVG string representing the aspect grid.
    """
    svg_output = ""
    style = f"stroke:{stroke_color}; stroke-width: 0.5px; fill:none"
    x_start = x_indent
    y_start = y_indent

    # Filter active planets
    active_planets = [planet for planet in available_planets if planet["is_active"]]

    # Same up-front filter as draw_aspect_grid: settings-less aspects (e.g.
    # declination parallels) would resolve to the wrong orb glyph.
    known_aspect_names = {setting["name"] for setting in aspects_settings} if aspects_settings is not None else None

    # Index aspects by (p1, p2) pair for O(1) lookup per grid cell instead of
    # scanning the whole aspect list for every cell. The key is ordered:
    # p1 belongs to the first subject (rows), p2 to the second (columns).
    aspects_by_pair: dict = {}
    for aspect in aspects:
        if known_aspect_names is not None and aspect["aspect"] not in known_aspect_names:
            continue
        aspects_by_pair.setdefault((aspect["p1"], aspect["p2"]), []).append(aspect)

    # Reverse the list of active planets for the first iteration
    reversed_planets = active_planets[::-1]
    for index, planet_a in enumerate(reversed_planets):
        planet_glyph = _resolve_point_glyph_id(planet_a["name"], planet_a)
        # Draw the grid box for the planet
        svg_output += f'<rect x="{x_start}" y="{y_start}" width="{box_size}" height="{box_size}" style="{style}"/>'
        svg_output += f'<use transform="scale(0.4)" x="{(x_start + 2) * 2.5}" y="{(y_start + 1) * 2.5}" xlink:href="#{planet_glyph}" />'
        x_start += box_size

    x_start = x_indent - box_size
    y_start = y_indent - box_size

    for index, planet_a in enumerate(reversed_planets):
        planet_glyph = _resolve_point_glyph_id(planet_a["name"], planet_a)
        # Draw the grid box for the planet
        svg_output += f'<rect x="{x_start}" y="{y_start}" width="{box_size}" height="{box_size}" style="{style}"/>'
        svg_output += f'<use transform="scale(0.4)" x="{(x_start + 2) * 2.5}" y="{(y_start + 1) * 2.5}" xlink:href="#{planet_glyph}" />'
        y_start -= box_size

    x_start = x_indent
    y_start = y_indent
    y_start = y_start - box_size

    for index, planet_a in enumerate(reversed_planets):
        # Draw the grid box for the planet
        svg_output += f'<rect x="{x_start}" y="{y_start}" width="{box_size}" height="{box_size}" style="{style}"/>'

        # Update the starting coordinates for the next box
        y_start -= box_size

        # Coordinates for the aspect symbols
        x_aspect = x_start
        y_aspect = y_start + box_size

        # Iterate over the remaining planets
        for planet_b in reversed_planets:
            # Draw the grid box for the aspect
            svg_output += (
                f'<rect x="{x_aspect}" y="{y_aspect}" width="{box_size}" height="{box_size}" style="{style}"/>'
            )
            x_aspect += box_size

            # Check for aspects between the planets
            for aspect in aspects_by_pair.get((planet_a["id"], planet_b["id"]), ()):
                svg_output += f'<use  x="{x_aspect - box_size + 1}" y="{y_aspect + 1}" xlink:href="#orb{aspect["aspect_degrees"]}" />'

    return svg_output


# =============================================================================
# FORMATTING UTILITIES
# Helper functions for formatting location and datetime strings for display.
# =============================================================================


def format_location_string(location: str, max_length: int = 35) -> str:
    """
    Format a location string to ensure it fits within a specified maximum length.

    If the location is longer than max_length, it attempts to shorten by using only
    the first and last parts separated by commas. If still too long, it truncates
    and adds ellipsis.

    Args:
        location: The original location string
        max_length: Maximum allowed length for the output string (default: 35)

    Returns:
        Formatted location string that fits within max_length
    """
    if len(location) > max_length:
        split_location = location.split(",")
        if len(split_location) > 1:
            shortened = split_location[0] + ", " + split_location[-1]
            if len(shortened) > max_length:
                return shortened[:max_length] + "..."
            return shortened
        else:
            return location[:max_length] + "..."
    return location


def format_datetime_with_timezone(iso_datetime_string: str) -> str:
    """
    Format an ISO datetime string with a custom format that includes properly formatted timezone.

    Supports BCE dates (negative years in ISO 8601 extended format) that Python's
    ``datetime.fromisoformat`` cannot parse.

    Args:
        iso_datetime_string: ISO formatted datetime string

    Returns:
        Formatted datetime string with properly formatted timezone offset (HH:MM)
    """
    # BCE dates: negative-year ISO strings like "-0500-03-21T12:00:00+01:35",
    # and ISO year 0 ("0000-...", i.e. 1 BCE) — Python's datetime.fromisoformat
    # cannot handle either (its minimum year is 1). Parse them manually.
    if iso_datetime_string.startswith("-") or iso_datetime_string.startswith("0000-"):
        # Split off the year field. For "-0500-..." strip the leading minus first
        # (year is negative); for "0000-..." the year is already the leading token.
        negative = iso_datetime_string.startswith("-")
        rest = iso_datetime_string[1:] if negative else iso_datetime_string  # "0500-03-21T..." / "0000-06-15T..."
        year_str, remainder = rest.split("-", 1)  # "0500", "03-21T..." / "0000", "06-15T..."
        if negative:
            year_str = "-" + year_str  # "-0500"

        # Extract date and time parts
        date_part, time_with_tz = remainder.split("T", 1)  # "03-21", "12:00:00+01:35"
        month_day = date_part  # "03-21"

        # Extract timezone offset (last +HH:MM or -HH:MM)
        for tz_sep_idx in range(len(time_with_tz) - 1, -1, -1):
            if time_with_tz[tz_sep_idx] in ("+", "-"):
                time_part = time_with_tz[:tz_sep_idx]  # "12:00:00"
                tz_part = time_with_tz[tz_sep_idx:]  # "+01:35"
                break
        else:
            time_part = time_with_tz
            tz_part = ""

        hm = time_part[:5]  # "12:00"
        return f"{year_str}-{month_day} {hm} [{tz_part}]"

    dt = datetime.datetime.fromisoformat(iso_datetime_string)
    # Format the UTC offset as [±HH:MM]. Derive it from utcoffset() rather than
    # slicing strftime("%z"): %z emits "+HHMMSS" for sub-minute offsets (e.g.
    # longitude-based LMT like +00:39:58), which the old colon-insertion mangled
    # into "+0039:58". Rounding to the minute keeps the label clean and matches
    # the historical [+HH:MM] convention. (The chart calculation still uses the
    # full-precision offset; only this label is minute-rounded.)
    offset = dt.utcoffset() or datetime.timedelta(0)
    total_minutes = round(offset.total_seconds() / 60)
    sign = "-" if total_minutes < 0 else "+"
    hours, minutes = divmod(abs(total_minutes), 60)
    return f"{dt.strftime('%Y-%m-%d %H:%M')} [{sign}{hours:02d}:{minutes:02d}]"


# =============================================================================
# ELEMENT AND MODALITY DISTRIBUTION CALCULATIONS
# Functions for calculating elemental (Fire, Earth, Air, Water) and
# modality/quality (Cardinal, Fixed, Mutable) distributions in charts.
# =============================================================================


def calculate_element_points(
    planets_settings: Sequence[KerykeionSettingsCelestialPointModel],
    celestial_points_names: Sequence[str],
    subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
    *,
    method: ElementQualityDistributionMethod = "weighted",
    custom_weights: Optional[Mapping[str, float]] = None,
    include_fixed_stars: bool = False,
) -> dict[str, float]:
    """
    Calculate elemental totals for a subject using the selected strategy.

    Args:
        planets_settings: Planet configuration list (kept for API compatibility).
        celestial_points_names: Celestial point names to include.
        subject: Astrological subject with planetary data.
        method: Calculation method (pure_count or weighted). Defaults to weighted.
        custom_weights: Optional overrides for point weights keyed by name.
        include_fixed_stars: Also count the subject's active fixed stars (weight
            0.2 unless overridden in the table); off by default so the totals
            cover exactly the named points.

    Returns:
        Dictionary mapping each element to its accumulated total.
    """
    normalized_names = [name.lower() for name in celestial_points_names]
    weight_lookup, fallback_weight, star_fallback_weight = _prepare_weight_lookup(method, custom_weights)

    return _calculate_distribution_for_subject(
        subject,
        normalized_names,
        _SIGN_TO_ELEMENT,
        _ELEMENT_KEYS,
        weight_lookup,
        fallback_weight,
        include_fixed_stars=include_fixed_stars,
        star_fallback_weight=star_fallback_weight,
    )


def calculate_synastry_element_points(
    planets_settings: Sequence[KerykeionSettingsCelestialPointModel],
    celestial_points_names: Sequence[str],
    subject1: AstrologicalSubjectModel,
    subject2: AstrologicalSubjectModel,
    *,
    method: ElementQualityDistributionMethod = "weighted",
    custom_weights: Optional[Mapping[str, float]] = None,
    include_fixed_stars: bool = False,
    as_percentages: bool = True,
) -> dict[str, float]:
    """
    Calculate combined element points for a synastry chart.

    With ``as_percentages=True`` (default, backward-compatible) the returned
    values are percentages summing to 100. With ``as_percentages=False`` they
    are the raw combined weighted point totals of both subjects — matching what
    every single-subject distribution helper returns, so a caller (the chart
    data factory) can populate the model's documented "points total" fields
    consistently and derive percentages itself.

    Args:
        planets_settings: Planet configuration list (unused but preserved).
        celestial_points_names: Celestial point names to process.
        subject1: First astrological subject.
        subject2: Second astrological subject.
        method: Calculation strategy (pure_count or weighted).
        custom_weights: Optional overrides for point weights.
        include_fixed_stars: Also count each subject's active fixed stars
            (weight 0.2 unless overridden); off by default so the totals cover
            exactly the named points.

    Returns:
        Dictionary with element percentages summing to 100.
    """
    normalized_names = [name.lower() for name in celestial_points_names]
    weight_lookup, fallback_weight, star_fallback_weight = _prepare_weight_lookup(method, custom_weights)

    subject1_totals = _calculate_distribution_for_subject(
        subject1,
        normalized_names,
        _SIGN_TO_ELEMENT,
        _ELEMENT_KEYS,
        weight_lookup,
        fallback_weight,
        include_fixed_stars=include_fixed_stars,
        star_fallback_weight=star_fallback_weight,
    )
    subject2_totals = _calculate_distribution_for_subject(
        subject2,
        normalized_names,
        _SIGN_TO_ELEMENT,
        _ELEMENT_KEYS,
        weight_lookup,
        fallback_weight,
        include_fixed_stars=include_fixed_stars,
        star_fallback_weight=star_fallback_weight,
    )

    combined_totals = {key: subject1_totals[key] + subject2_totals[key] for key in _ELEMENT_KEYS}
    total_points = sum(combined_totals.values())

    if not as_percentages:
        return combined_totals

    if total_points == 0:
        return {key: 0.0 for key in _ELEMENT_KEYS}

    return {key: (combined_totals[key] / total_points) * 100.0 for key in _ELEMENT_KEYS}


# =============================================================================
# SVG DRAWING FUNCTIONS - HOUSE COMPARISON GRIDS
# Functions for rendering house position comparisons between two charts,
# used in synastry, return charts, and transits.
# =============================================================================


#: The comparison tables put a glyph, a name and one or two house numbers on a
#: row, and printed their headers at fixed offsets that only ever fitted the
#: English words: "Progressed Point" inks 79 units at the bold 10px these
#: headers use, and the next column started at 77, so the two ran together.
#: Sizing the columns from what is actually printed fixes every language at
#: once, and keeps the header over the values it names rather than 13 units to
#: their left, which is where the old constants had it.
_HOUSE_COMPARISON_NAME_X: float = 15.0
_HOUSE_COMPARISON_GUTTER: float = 8.0

#: Bold text inks wider than the same string at the same size in book weight.
#: The estimator measures book weight, so the headers get this on top.
_BOLD_WIDTH_FACTOR: float = 1.06


def _house_comparison_columns(
    headers: "Sequence[str]",
    names: "Sequence[str]",
    minimum_x: "Sequence[float]",
    font_size: float = 10.0,
) -> list[float]:
    """Where each column after the name starts, header and values alike.

    *minimum_x* is what the layout used before, kept as a floor so a table of
    short English words is drawn exactly where it always was and only the ones
    that outgrew their offsets move.
    """
    widest_name = max((estimate_text_width(n, font_size) for n in names), default=0.0)
    columns: list[float] = []
    left = max(
        _HOUSE_COMPARISON_NAME_X + widest_name,
        estimate_text_width(headers[0], font_size) * _BOLD_WIDTH_FACTOR,
    )
    for index, floor in enumerate(minimum_x):
        x = max(floor, left + _HOUSE_COMPARISON_GUTTER)
        columns.append(x)
        # A house number is at most two figures; the header above it is what
        # sets the stride to the next column.
        left = x + max(
            estimate_text_width(headers[index + 1], font_size) * _BOLD_WIDTH_FACTOR,
            estimate_text_width("12", font_size),
        )
    return columns


def draw_house_comparison_grid(
    house_comparison: "HouseComparisonModel",
    celestial_point_language: KerykeionLanguageCelestialPointModel,
    active_points: list[AstrologicalPoint],
    *,
    points_owner_subject_number: Literal[1, 2] = 1,
    text_color: str = "var(--kerykeion-color-neutral-content)",
    house_position_comparison_label: str = "House Position Comparison",
    return_point_label: str = "Return Point",
    return_label: str = "DualReturnChart",
    radix_label: str = "Radix",
    x_position: int = 1100,
    y_position: int = 0,
) -> str:
    """
    Generate SVG code for displaying a comparison of points across houses between two charts.

    Parameters:
    - house_comparison ("HouseComparisonModel"): Model containing house comparison data,
      including first_subject_name, second_subject_name, and points in houses.
    - celestial_point_language (KerykeionLanguageCelestialPointModel): Language model for celestial points
    - active_celestial_points (list[KerykeionPointModel]): List of active celestial points to display
    - text_color (str): Color for the text elements

    Returns:
    - str: SVG code for the house comparison grid.
    """
    if points_owner_subject_number == 1:
        comparison_data = house_comparison.first_points_in_second_houses
    else:
        comparison_data = house_comparison.second_points_in_first_houses

    svg_output = f'<g transform="translate({x_position},{y_position})">'

    # Add title
    svg_output += f'<text text-anchor="start" x="0" y="-15" style="fill:{text_color}; font-size: 14px;">{escape_svg_text(house_position_comparison_label)}</text>'

    # Create a dictionary to store all points by name for combined display
    all_points_by_name = {}

    for point in comparison_data:
        # Only process points that are active
        if point.point_name in active_points and point.point_name not in all_points_by_name:
            all_points_by_name[point.point_name] = {
                "name": point.point_name,
                "secondary_house": point.projected_house_number,
                "native_house": point.point_owner_house_number,
            }

    # Columns sized from what this table actually prints — headers included.
    _decoded_names = [
        get_decoded_kerykeion_celestial_point_name(name, celestial_point_language)
        for name in all_points_by_name
    ]
    _native_x, _secondary_x = _house_comparison_columns(
        [return_point_label, return_label, radix_label], _decoded_names, (90.0, 140.0)
    )

    # Add column headers
    line_increment = 10
    svg_output += (
        f'<g transform="translate(0,{line_increment})">'
        f'<text text-anchor="start" x="0" style="fill:{text_color}; font-weight: bold; font-size: 10px;">{escape_svg_text(return_point_label)}</text>'
        f'<text text-anchor="start" x="{_native_x:.1f}" style="fill:{text_color}; font-weight: bold; font-size: 10px;">{escape_svg_text(return_label)}</text>'
        f'<text text-anchor="start" x="{_secondary_x:.1f}" style="fill:{text_color}; font-weight: bold; font-size: 10px;">{escape_svg_text(radix_label)}</text>'
        f"</g>"
    )
    line_increment += 15

    # Display all points organized by name
    for name, point_data in all_points_by_name.items():
        native_house = point_data.get("native_house", "-")
        secondary_house = point_data.get("secondary_house", "-")
        point_glyph = _resolve_point_glyph_id(name)

        svg_output += (
            f'<g transform="translate(0,{line_increment})">'
            f'<g transform="translate(0,-9)"><use transform="scale(0.4)" xlink:href="#{point_glyph}" /></g>'
            f'<text text-anchor="start" x="15" style="fill:{text_color}; font-size: 10px;">{escape_svg_text(get_decoded_kerykeion_celestial_point_name(name, celestial_point_language))}</text>'
            f'<text text-anchor="start" x="{_native_x:.1f}" style="fill:{text_color}; font-size: 10px;">{native_house}</text>'
            f'<text text-anchor="start" x="{_secondary_x:.1f}" style="fill:{text_color}; font-size: 10px;">{secondary_house}</text>'
            f"</g>"
        )
        line_increment += 12

    svg_output += "</g>"

    return svg_output


def draw_single_house_comparison_grid(
    house_comparison: "HouseComparisonModel",
    celestial_point_language: KerykeionLanguageCelestialPointModel,
    active_points: list[AstrologicalPoint],
    *,
    points_owner_subject_number: Literal[1, 2] = 1,
    text_color: str = "var(--kerykeion-color-neutral-content)",
    house_position_comparison_label: str = "House Position Comparison",
    return_point_label: str = "Return Point",
    natal_house_label: str = "Natal House",
    x_position: int = 1030,
    y_position: int = 0,
) -> str:
    """
    Generate SVG code for displaying celestial points and their house positions.

    Parameters:
    - house_comparison ("HouseComparisonModel"): Model containing house comparison data,
      including first_subject_name, second_subject_name, and points in houses.
    - celestial_point_language (KerykeionLanguageCelestialPointModel): Language model for celestial points
    - active_points (list[AstrologicalPoint]): List of active celestial points to display
    - points_owner_subject_number (Literal[1, 2]): Which subject's points to display (1 for first, 2 for second)
    - text_color (str): Color for the text elements
    - house_position_comparison_label (str): Label for the house position comparison grid
    - return_point_label (str): Label for the return point column
    - house_position_label (str): Label for the house position column
    - x_position (int): X position for the grid
    - y_position (int): Y position for the grid

    Returns:
    - str: SVG code for the house position grid.
    """
    if points_owner_subject_number == 1:
        comparison_data = house_comparison.first_points_in_second_houses
    else:
        comparison_data = house_comparison.second_points_in_first_houses

    svg_output = f'<g transform="translate({x_position},{y_position})">'

    # Add title
    svg_output += f'<text text-anchor="start" x="0" y="-15" style="fill:{text_color}; font-size: 14px;">{escape_svg_text(house_position_comparison_label)}</text>'

    # Create a dictionary to store all points by name for combined display
    all_points_by_name = {}

    for point in comparison_data:
        # Only process points that are active
        if point.point_name in active_points and point.point_name not in all_points_by_name:
            all_points_by_name[point.point_name] = {"name": point.point_name, "house": point.projected_house_number}

    # Columns sized from what this table actually prints — headers included.
    _decoded_names = [
        get_decoded_kerykeion_celestial_point_name(name, celestial_point_language)
        for name in all_points_by_name
    ]
    (_house_x,) = _house_comparison_columns(
        [return_point_label, natal_house_label], _decoded_names, (90.0,)
    )

    # Add column headers
    line_increment = 10
    svg_output += (
        f'<g transform="translate(0,{line_increment})">'
        f'<text text-anchor="start" x="0" style="fill:{text_color}; font-weight: bold; font-size: 10px;">{escape_svg_text(return_point_label)}</text>'
        f'<text text-anchor="start" x="{_house_x:.1f}" style="fill:{text_color}; font-weight: bold; font-size: 10px;">{escape_svg_text(natal_house_label)}</text>'
        f"</g>"
    )
    line_increment += 15

    # Display all points organized by name
    for name, point_data in all_points_by_name.items():
        house = point_data.get("house", "-")
        point_glyph = _resolve_point_glyph_id(name)

        svg_output += (
            f'<g transform="translate(0,{line_increment})">'
            f'<g transform="translate(0,-9)"><use transform="scale(0.4)" xlink:href="#{point_glyph}" /></g>'
            f'<text text-anchor="start" x="15" style="fill:{text_color}; font-size: 10px;">{escape_svg_text(get_decoded_kerykeion_celestial_point_name(name, celestial_point_language))}</text>'
            f'<text text-anchor="start" x="{_house_x:.1f}" style="fill:{text_color}; font-size: 10px;">{house}</text>'
            f"</g>"
        )
        line_increment += 12

    svg_output += "</g>"

    return svg_output


def draw_cusp_comparison_grid(
    house_comparison: "HouseComparisonModel",
    celestial_point_language: "KerykeionLanguageCelestialPointModel",
    *,
    cusps_owner_subject_number: Literal[1, 2] = 1,
    text_color: str = "var(--kerykeion-color-neutral-content)",
    cusp_position_comparison_label: str = "Cusp Position Comparison",
    owner_cusp_label: str = "Owner Cusp",
    projected_house_label: str = "Projected House",
    x_position: int = 1030,
    y_position: int = 0,
) -> str:
    """
    Generate SVG code for displaying house cusps and their positions in reciprocal houses.

    Parameters:
    - house_comparison (HouseComparisonModel): House comparison data
    - celestial_point_language (KerykeionLanguageCelestialPointModel): Language settings
    - cusps_owner_subject_number (int): Which subject's cusps to display (1 or 2)
    - text_color (str): Color for text elements
    - cusp_position_comparison_label (str): Label for the comparison section
    - owner_cusp_label (str): Label for owner cusp column
    - projected_house_label (str): Label for projected house column
    - x_position (int): X position for the grid
    - y_position (int): Y position for the grid

    Returns:
    - str: SVG representation of the cusp comparison grid
    """
    # Select the appropriate cusp data based on subject number
    if cusps_owner_subject_number == 1:
        cusps_data = house_comparison.first_cusps_in_second_houses
    else:
        cusps_data = house_comparison.second_cusps_in_first_houses

    if not cusps_data:
        return ""

    svg_output = (
        f'<g transform="translate({x_position},{y_position})">'
        f'<text text-anchor="start" x="0" y="-15" style="fill:{text_color}; font-size: 12px; font-weight: bold;">{escape_svg_text(cusp_position_comparison_label)}</text>'
    )

    # Add column headers with the same vertical spacing pattern as draw_house_comparison_grid
    line_increment = 10
    svg_output += (
        f'<g transform="translate(0,{line_increment})">'
        f'<text text-anchor="start" x="0" style="fill:{text_color}; font-weight: bold; font-size: 10px;">{escape_svg_text(owner_cusp_label)}</text>'
        f'<text text-anchor="start" x="70" style="fill:{text_color}; font-weight: bold; font-size: 10px;">{escape_svg_text(projected_house_label)}</text>'
        f"</g>"
    )
    line_increment += 15

    # Derive a short cusp label (e.g. "Cusp", "Cuspide") from the owner column header.
    cusp_cell_label = owner_cusp_label.split()[-1] if owner_cusp_label else "Cusp"

    for cusp in cusps_data:
        # Use numeric house identifiers to avoid exposing internal names like "First_House".
        owner_house_number = cusp.point_owner_house_number or 0
        owner_house_display = f"{cusp_cell_label} {owner_house_number}" if owner_house_number else "-"
        projected_house_display = str(cusp.projected_house_number)

        svg_output += (
            f'<g transform="translate(0,{line_increment})">'
            f'<text text-anchor="start" x="0" style="fill:{text_color}; font-size: 10px;">{escape_svg_text(owner_house_display)}</text>'
            f'<text text-anchor="start" x="70" style="fill:{text_color}; font-size: 10px;">{projected_house_display}</text>'
            f"</g>"
        )
        line_increment += 12

    svg_output += "</g>"

    return svg_output


def draw_single_cusp_comparison_grid(
    house_comparison: "HouseComparisonModel",
    celestial_point_language: "KerykeionLanguageCelestialPointModel",
    *,
    cusps_owner_subject_number: Literal[1, 2] = 1,
    text_color: str = "var(--kerykeion-color-neutral-content)",
    cusp_position_comparison_label: str = "Cusp Position Comparison",
    owner_cusp_label: str = "Owner Cusp",
    projected_house_label: str = "Projected House",
    x_position: int = 1030,
    y_position: int = 0,
) -> str:
    """
    Generate SVG code for displaying house cusps and their positions in reciprocal houses (single grid).

    Parameters:
    - house_comparison (HouseComparisonModel): House comparison data
    - celestial_point_language (KerykeionLanguageCelestialPointModel): Language settings
    - cusps_owner_subject_number (int): Which subject's cusps to display (1 or 2)
    - text_color (str): Color for text elements
    - cusp_position_comparison_label (str): Label for the comparison section
    - owner_cusp_label (str): Label for owner cusp column
    - projected_house_label (str): Label for projected house column
    - x_position (int): X position for the grid
    - y_position (int): Y position for the grid

    Returns:
    - str: SVG representation of the cusp comparison grid
    """
    return draw_cusp_comparison_grid(
        house_comparison=house_comparison,
        celestial_point_language=celestial_point_language,
        cusps_owner_subject_number=cusps_owner_subject_number,
        text_color=text_color,
        cusp_position_comparison_label=cusp_position_comparison_label,
        owner_cusp_label=owner_cusp_label,
        projected_house_label=projected_house_label,
        x_position=x_position,
        y_position=y_position,
    )


# =============================================================================
# MOON PHASE CALCULATIONS AND RENDERING
# Functions for calculating lunar phase geometry and generating SVG moon icons.
# =============================================================================


def make_lunar_phase(degrees_between_sun_and_moon: float, latitude: float) -> str:
    """Build the SVG fragment that renders the Moon's illuminated phase.

    The phase geometry is derived purely from the Sun-Moon elongation; the
    terminator is drawn as an ellipse whose width tracks the illuminated
    fraction.

    Args:
        degrees_between_sun_and_moon: Sun-Moon elongation in degrees (0 = new
            moon, 180 = full moon).
        latitude: Observer's latitude. Unused; retained for backward
            compatibility with older call sites.

    Returns:
        An SVG string drawing the Moon disc with its bright/shadow regions.
    """
    params = calculate_moon_phase_chart_params(degrees_between_sun_and_moon)

    phase_angle = params["phase_angle"]
    # NOTE: this is the DARK fraction (1 - illuminated).
    dark_fraction = 1.0 - params["illuminated_fraction"]
    shadow_ellipse_rx = abs(params["shadow_ellipse_rx"])

    radius = 10.0
    center_x = 20.0
    center_y = 10.0

    bright_color = "var(--kerykeion-chart-color-lunar-phase-1)"
    shadow_color = "var(--kerykeion-chart-color-lunar-phase-0)"

    is_waxing = phase_angle < 180.0

    if dark_fraction <= 1e-6:
        # Exact full moon: fully bright disc (was inverted to all-shadow,
        # a hard discontinuity against the ~179.9 deg rendering).
        base_fill = bright_color
        overlay_path = ""
        overlay_fill = ""
    elif 1.0 - dark_fraction <= 1e-6:
        # Exact new moon: fully dark disc.
        base_fill = shadow_color
        overlay_path = ""
        overlay_fill = ""
    else:
        is_lit_major = dark_fraction >= 0.5
        if is_lit_major:
            base_fill = bright_color
            overlay_fill = shadow_color
            overlay_side = "left" if is_waxing else "right"
        else:
            base_fill = shadow_color
            overlay_fill = bright_color
            overlay_side = "right" if is_waxing else "left"

        # The illuminated limb is the orthographic projection of the lunar terminator;
        # it appears as an ellipse with vertical radius equal to the lunar radius and
        # horizontal radius scaled by |cos(phase)|.
        def build_lune_path(side: str, ellipse_rx: float) -> str:
            ellipse_rx = max(0.0, min(radius, ellipse_rx))
            top_y = center_y - radius
            bottom_y = center_y + radius
            circle_sweep = 1 if side == "right" else 0

            if ellipse_rx <= 1e-6:
                return (
                    f"M {center_x:.4f} {top_y:.4f}"
                    f" A {radius:.4f} {radius:.4f} 0 0 {circle_sweep} {center_x:.4f} {bottom_y:.4f}"
                    f" L {center_x:.4f} {top_y:.4f}"
                    " Z"
                )

            return (
                f"M {center_x:.4f} {top_y:.4f}"
                f" A {radius:.4f} {radius:.4f} 0 0 {circle_sweep} {center_x:.4f} {bottom_y:.4f}"
                f" A {ellipse_rx:.4f} {radius:.4f} 0 0 {circle_sweep} {center_x:.4f} {top_y:.4f}"
                " Z"
            )

        overlay_path = build_lune_path(overlay_side, shadow_ellipse_rx)

    svg_lines = [
        '<g transform="rotate(0 20 10)">',
        "    <defs>",
        '        <clipPath id="moonPhaseCutOffCircle">',
        '            <circle cx="20" cy="10" r="10" />',
        "        </clipPath>",
        "    </defs>",
        f'    <circle cx="20" cy="10" r="10" style="fill: {base_fill}" />',
    ]

    if overlay_path:
        svg_lines.append(
            f'    <path d="{overlay_path}" style="fill: {overlay_fill}" clip-path="url(#moonPhaseCutOffCircle)" />'
        )

    svg_lines.append(
        '    <circle cx="20" cy="10" r="10" style="fill: none; stroke: var(--kerykeion-chart-color-lunar-phase-0); stroke-width: 0.5px; stroke-opacity: 0.5" />'
    )
    svg_lines.append("</g>")

    return "\n".join(svg_lines)


def calculate_quality_points(
    planets_settings: Sequence[KerykeionSettingsCelestialPointModel],
    celestial_points_names: Sequence[str],
    subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
    *,
    method: ElementQualityDistributionMethod = "weighted",
    custom_weights: Optional[Mapping[str, float]] = None,
    include_fixed_stars: bool = False,
) -> dict[str, float]:
    """
    Calculate modality totals for a subject using the selected strategy.

    Args:
        planets_settings: Planet configuration list (kept for API compatibility).
        celestial_points_names: Celestial point names to include.
        subject: Astrological subject with planetary data.
        method: Calculation method (pure_count or weighted). Defaults to weighted.
        custom_weights: Optional overrides for point weights keyed by name.
        include_fixed_stars: Also count the subject's active fixed stars (weight
            0.2 unless overridden in the table); off by default so the totals
            cover exactly the named points.

    Returns:
        Dictionary mapping each modality to its accumulated total.
    """
    normalized_names = [name.lower() for name in celestial_points_names]
    weight_lookup, fallback_weight, star_fallback_weight = _prepare_weight_lookup(method, custom_weights)

    return _calculate_distribution_for_subject(
        subject,
        normalized_names,
        _SIGN_TO_QUALITY,
        _QUALITY_KEYS,
        weight_lookup,
        fallback_weight,
        include_fixed_stars=include_fixed_stars,
        star_fallback_weight=star_fallback_weight,
    )


def calculate_synastry_quality_points(
    planets_settings: Sequence[KerykeionSettingsCelestialPointModel],
    celestial_points_names: Sequence[str],
    subject1: AstrologicalSubjectModel,
    subject2: AstrologicalSubjectModel,
    *,
    method: ElementQualityDistributionMethod = "weighted",
    custom_weights: Optional[Mapping[str, float]] = None,
    include_fixed_stars: bool = False,
    as_percentages: bool = True,
) -> dict[str, float]:
    """
    Calculate combined modality points for a synastry chart.

    With ``as_percentages=True`` (default) the values are percentages summing to
    100; with ``as_percentages=False`` they are raw combined point totals (see
    :func:`calculate_synastry_element_points`).

    Args:
        planets_settings: Planet configuration list (unused but preserved).
        celestial_points_names: Celestial point names to process.
        subject1: First astrological subject.
        subject2: Second astrological subject.
        method: Calculation strategy (pure_count or weighted).
        custom_weights: Optional overrides for point weights.
        include_fixed_stars: Also count each subject's active fixed stars
            (weight 0.2 unless overridden); off by default so the totals cover
            exactly the named points.

    Returns:
        Dictionary with modality percentages summing to 100.
    """
    normalized_names = [name.lower() for name in celestial_points_names]
    weight_lookup, fallback_weight, star_fallback_weight = _prepare_weight_lookup(method, custom_weights)

    subject1_totals = _calculate_distribution_for_subject(
        subject1,
        normalized_names,
        _SIGN_TO_QUALITY,
        _QUALITY_KEYS,
        weight_lookup,
        fallback_weight,
        include_fixed_stars=include_fixed_stars,
        star_fallback_weight=star_fallback_weight,
    )
    subject2_totals = _calculate_distribution_for_subject(
        subject2,
        normalized_names,
        _SIGN_TO_QUALITY,
        _QUALITY_KEYS,
        weight_lookup,
        fallback_weight,
        include_fixed_stars=include_fixed_stars,
        star_fallback_weight=star_fallback_weight,
    )

    combined_totals = {key: subject1_totals[key] + subject2_totals[key] for key in _QUALITY_KEYS}
    total_points = sum(combined_totals.values())

    if not as_percentages:
        return combined_totals

    if total_points == 0:
        return {key: 0.0 for key in _QUALITY_KEYS}

    return {key: (combined_totals[key] / total_points) * 100.0 for key in _QUALITY_KEYS}


# =============================================================================
# GAUQUELIN SECTORS — replaces house cusp lines when active
# =============================================================================


def _classic_gauquelin_mid_offset(
    offsets: list[float],
    i: int,
) -> float:
    """Compute the offset midpoint of Gauquelin sector i (0-indexed) for the classic chart.

    Gauquelin cusps are numbered in the diurnal (clockwise) direction, so
    consecutive offsets DESCEND; the midpoint must be taken on the a→b
    descending arc or every label lands in the diametrically opposite sector.
    """
    a = offsets[i]
    b = offsets[(i + 1) % 36]
    span = (a - b) % 360
    return (b + span / 2) % 360


def draw_gauquelin_sectors(
    r: Union[int, float],
    inner_r: Union[int, float],
    outer_r: Union[int, float],
    seventh_house_degree_ut: float,
    color: str = "var(--kerykeion-color-secondary)",
    gauquelin_cusps: Optional[list[float]] = None,
) -> str:
    """Draw 36 Gauquelin sector divisions, replacing the 12-house system.

    The Gauquelin system divides the diurnal circle into 36 sectors
    numbered clockwise from the Ascendant (east horizon).
    When ``gauquelin_cusps`` are provided, sector lines are drawn at the
    actual diurnal-arc cusp positions (unequal zodiacal spacing).

    Args:
        r: Main chart radius (same as for house cusps).
        inner_r: Inner radius offset (first_circle_radius).
        outer_r: Outer radius offset (third_circle_radius).
        seventh_house_degree_ut: Descendant degree for chart orientation.
        color: CSS color for sector cusp lines.
        gauquelin_cusps: 36 zodiacal longitudes for actual sector boundaries.

    Returns:
        SVG string with 36 sector lines + sector numbers (replaces makeHouses).
    """
    output = ""

    if gauquelin_cusps is not None:
        offsets = [(-seventh_house_degree_ut) + c for c in gauquelin_cusps]
    else:
        # Equal 10° pseudo-cusps anchored at the ASC (offset -180 = screen
        # left), descending in the diurnal direction like real cusps.
        offsets = [-180.0 - i * 10.0 for i in range(36)]

    for i in range(36):
        offset = offsets[i]

        x1 = wheel_x(0, (r - outer_r), offset) + outer_r
        y1 = wheel_y(0, (r - outer_r), offset) + outer_r
        x2 = wheel_x(0, r - inner_r, offset) + inner_r
        y2 = wheel_y(0, r - inner_r, offset) + inner_r

        is_quadrant = i % 9 == 0
        if is_quadrant:
            stroke_width = 1.8
            stroke_opacity = 1.0
        else:
            stroke_width = 0.6
            stroke_opacity = 0.7

        output += (
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'style="stroke:{color}; stroke-width:{stroke_width}px; '
            f'stroke-opacity:{stroke_opacity}; pointer-events:none;" />\n'
        )

        mid_offset = _classic_gauquelin_mid_offset(offsets, i)
        text_r_factor = (r - inner_r) + (inner_r - outer_r) * 0.5
        tx = wheel_x(0, text_r_factor, mid_offset) + (r - text_r_factor)
        ty = wheel_y(0, text_r_factor, mid_offset) + (r - text_r_factor)
        sector_num = i + 1

        font_size = 8 if is_quadrant else 6
        font_weight = "bold" if is_quadrant else "normal"

        output += (
            f'<text x="{tx:.2f}" y="{ty:.2f}" '
            f'style="fill:{color}; font-size:{font_size}px; font-weight:{font_weight}; '
            f'opacity:0.9; text-anchor:middle; dominant-baseline:central; pointer-events:none;">'
            f"{sector_num}</text>\n"
        )

    return output


def draw_gauquelin_sector_hit_areas(
    r: Union[int, float],
    c1: Union[int, float],
    c3: Union[int, float],
    seventh_house_degree_ut: float,
    gauquelin_cusps: Optional[list[float]] = None,
) -> str:
    """Draw 36 transparent annular wedges for interactive Gauquelin sector highlighting.

    Each wedge spans a Gauquelin sector between the outer circle (c1)
    and the inner circle (c3). When ``gauquelin_cusps`` are provided,
    wedge boundaries match the actual diurnal-arc cusp positions.

    Args:
        r: Chart radius in pixels.
        c1: Outer boundary dropin offset (first_circle_radius).
        c3: Inner boundary dropin offset (third_circle_radius).
        seventh_house_degree_ut: Descendant absolute position for wheel orientation.
        gauquelin_cusps: 36 zodiacal longitudes for actual sector boundaries.

    Returns:
        SVG string containing 36 transparent annular wedge elements.
    """
    outer_visual_r = r - c1
    inner_visual_r = r - c3
    outer_dropin = c1
    inner_dropin = c3

    if gauquelin_cusps is not None:
        offsets = [(-seventh_house_degree_ut) + c for c in gauquelin_cusps]
    else:
        # Same ASC-anchored descending fallback as draw_gauquelin_sectors.
        offsets = [-180.0 - i * 10.0 for i in range(36)]

    output = ""

    for i in range(36):
        sector_num = i + 1
        offset_start = offsets[i]
        offset_end = offsets[(i + 1) % 36]

        ox1 = wheel_x(0, outer_visual_r, offset_start) + outer_dropin
        oy1 = wheel_y(0, outer_visual_r, offset_start) + outer_dropin
        ox2 = wheel_x(0, outer_visual_r, offset_end) + outer_dropin
        oy2 = wheel_y(0, outer_visual_r, offset_end) + outer_dropin
        ix1 = wheel_x(0, inner_visual_r, offset_start) + inner_dropin
        iy1 = wheel_y(0, inner_visual_r, offset_start) + inner_dropin
        ix2 = wheel_x(0, inner_visual_r, offset_end) + inner_dropin
        iy2 = wheel_y(0, inner_visual_r, offset_end) + inner_dropin

        # Sweep flags for DESCENDING cusps: start→end runs clockwise on
        # screen (the 12-house version traverses the opposite way).
        d = (
            f"M {ox1},{oy1} "
            f"A {outer_visual_r},{outer_visual_r} 0 0,1 {ox2},{oy2} "
            f"L {ix2},{iy2} "
            f"A {inner_visual_r},{inner_visual_r} 0 0,0 {ix1},{iy1} Z"
        )

        output += (
            f'<g kr:node="GauquelinSector" kr:sector="{sector_num}">'
            f'<path d="{d}" style="fill: transparent; stroke: none; pointer-events: all;"/>'
            f"</g>"
        )

    return output
