"""
Default settings and presets used by chart generation and calculation routines.

This module centralizes the static values that were previously stored in
`kerykeion.settings.legacy`. Keeping them here avoids scattering hard-coded
configuration across the codebase while still exposing them for reuse.
"""

from __future__ import annotations

from typing import Final, TypedDict


class _CelestialPointSettingRequired(TypedDict):
    """Required fields for celestial point settings."""

    id: int
    name: str
    color: str
    element_points: int
    label: str


class _CelestialPointSetting(_CelestialPointSettingRequired, total=False):
    """Celestial point settings with optional is_active and glyph_id fields."""

    is_active: bool
    # v6: when set, the SVG renderer uses this as the symbol reference
    # (xlink:href="#{glyph_id}") instead of the point name. Used to make
    # catalog fixed stars fall back to the generic "#FixedStar" symbol when
    # the template doesn't ship a per-star <symbol>.
    glyph_id: str


class _ChartAspectSettingRequired(TypedDict):
    """Required fields for chart aspect settings."""

    degree: int
    name: str
    is_major: bool
    color: str


class _ChartAspectSetting(_ChartAspectSettingRequired, total=False):
    """Chart aspect settings with optional orb field."""

    orb: float


DEFAULT_CHART_COLORS: Final[dict[str, str]] = {
    "paper_0": "var(--kerykeion-chart-color-paper-0)",
    "paper_1": "var(--kerykeion-chart-color-paper-1)",
    "zodiac_bg_0": "var(--kerykeion-chart-color-zodiac-bg-0)",
    "zodiac_bg_1": "var(--kerykeion-chart-color-zodiac-bg-1)",
    "zodiac_bg_2": "var(--kerykeion-chart-color-zodiac-bg-2)",
    "zodiac_bg_3": "var(--kerykeion-chart-color-zodiac-bg-3)",
    "zodiac_bg_4": "var(--kerykeion-chart-color-zodiac-bg-4)",
    "zodiac_bg_5": "var(--kerykeion-chart-color-zodiac-bg-5)",
    "zodiac_bg_6": "var(--kerykeion-chart-color-zodiac-bg-6)",
    "zodiac_bg_7": "var(--kerykeion-chart-color-zodiac-bg-7)",
    "zodiac_bg_8": "var(--kerykeion-chart-color-zodiac-bg-8)",
    "zodiac_bg_9": "var(--kerykeion-chart-color-zodiac-bg-9)",
    "zodiac_bg_10": "var(--kerykeion-chart-color-zodiac-bg-10)",
    "zodiac_bg_11": "var(--kerykeion-chart-color-zodiac-bg-11)",
    "zodiac_icon_0": "var(--kerykeion-chart-color-zodiac-icon-0)",
    "zodiac_icon_1": "var(--kerykeion-chart-color-zodiac-icon-1)",
    "zodiac_icon_2": "var(--kerykeion-chart-color-zodiac-icon-2)",
    "zodiac_icon_3": "var(--kerykeion-chart-color-zodiac-icon-3)",
    "zodiac_icon_4": "var(--kerykeion-chart-color-zodiac-icon-4)",
    "zodiac_icon_5": "var(--kerykeion-chart-color-zodiac-icon-5)",
    "zodiac_icon_6": "var(--kerykeion-chart-color-zodiac-icon-6)",
    "zodiac_icon_7": "var(--kerykeion-chart-color-zodiac-icon-7)",
    "zodiac_icon_8": "var(--kerykeion-chart-color-zodiac-icon-8)",
    "zodiac_icon_9": "var(--kerykeion-chart-color-zodiac-icon-9)",
    "zodiac_icon_10": "var(--kerykeion-chart-color-zodiac-icon-10)",
    "zodiac_icon_11": "var(--kerykeion-chart-color-zodiac-icon-11)",
    "zodiac_radix_ring_0": "var(--kerykeion-chart-color-zodiac-radix-ring-0)",
    "zodiac_radix_ring_1": "var(--kerykeion-chart-color-zodiac-radix-ring-1)",
    "zodiac_radix_ring_2": "var(--kerykeion-chart-color-zodiac-radix-ring-2)",
    "zodiac_transit_ring_0": "var(--kerykeion-chart-color-zodiac-transit-ring-0)",
    "zodiac_transit_ring_1": "var(--kerykeion-chart-color-zodiac-transit-ring-1)",
    "zodiac_transit_ring_2": "var(--kerykeion-chart-color-zodiac-transit-ring-2)",
    "zodiac_transit_ring_3": "var(--kerykeion-chart-color-zodiac-transit-ring-3)",
    "houses_radix_line": "var(--kerykeion-chart-color-houses-radix-line)",
    "houses_transit_line": "var(--kerykeion-chart-color-houses-transit-line)",
    "lunar_phase_0": "var(--kerykeion-chart-color-lunar-phase-0)",
    "lunar_phase_1": "var(--kerykeion-chart-color-lunar-phase-1)",
}


DEFAULT_CELESTIAL_POINTS_SETTINGS: Final[list[_CelestialPointSetting]] = [
    {
        "id": 0,
        "name": "Sun",
        "color": "var(--kerykeion-chart-color-sun)",
        "element_points": 40,
        "label": "Sun",
    },
    {
        "id": 1,
        "name": "Moon",
        "color": "var(--kerykeion-chart-color-moon)",
        "element_points": 40,
        "label": "Moon",
    },
    {
        "id": 2,
        "name": "Mercury",
        "color": "var(--kerykeion-chart-color-mercury)",
        "element_points": 15,
        "label": "Mercury",
    },
    {
        "id": 3,
        "name": "Venus",
        "color": "var(--kerykeion-chart-color-venus)",
        "element_points": 15,
        "label": "Venus",
    },
    {
        "id": 4,
        "name": "Mars",
        "color": "var(--kerykeion-chart-color-mars)",
        "element_points": 15,
        "label": "Mars",
    },
    {
        "id": 5,
        "name": "Jupiter",
        "color": "var(--kerykeion-chart-color-jupiter)",
        "element_points": 10,
        "label": "Jupiter",
    },
    {
        "id": 6,
        "name": "Saturn",
        "color": "var(--kerykeion-chart-color-saturn)",
        "element_points": 10,
        "label": "Saturn",
    },
    {
        "id": 7,
        "name": "Uranus",
        "color": "var(--kerykeion-chart-color-uranus)",
        "element_points": 10,
        "label": "Uranus",
    },
    {
        "id": 8,
        "name": "Neptune",
        "color": "var(--kerykeion-chart-color-neptune)",
        "element_points": 10,
        "label": "Neptune",
    },
    {
        "id": 9,
        "name": "Pluto",
        "color": "var(--kerykeion-chart-color-pluto)",
        "element_points": 10,
        "label": "Pluto",
    },
    {
        "id": 10,
        "name": "Mean_North_Lunar_Node",
        "color": "var(--kerykeion-chart-color-mean-node)",
        "element_points": 0,
        "label": "Mean_North_Lunar_Node",
    },
    {
        "id": 11,
        "name": "True_North_Lunar_Node",
        "color": "var(--kerykeion-chart-color-true-node)",
        "element_points": 0,
        "label": "True_North_Lunar_Node",
    },
    {
        "id": 12,
        "name": "Chiron",
        "color": "var(--kerykeion-chart-color-chiron)",
        "element_points": 0,
        "label": "Chiron",
    },
    {
        "id": 13,
        "name": "Ascendant",
        "color": "var(--kerykeion-chart-color-first-house)",
        "element_points": 40,
        "label": "Asc",
    },
    {
        "id": 14,
        "name": "Medium_Coeli",
        "color": "var(--kerykeion-chart-color-tenth-house)",
        "element_points": 20,
        "label": "Mc",
    },
    {
        "id": 15,
        "name": "Descendant",
        "color": "var(--kerykeion-chart-color-seventh-house)",
        "element_points": 0,
        "label": "Dsc",
    },
    {
        "id": 16,
        "name": "Imum_Coeli",
        "color": "var(--kerykeion-chart-color-fourth-house)",
        "element_points": 0,
        "label": "Ic",
    },
    {
        "id": 17,
        "name": "Mean_Lilith",
        "color": "var(--kerykeion-chart-color-mean-lilith)",
        "element_points": 0,
        "label": "Mean_Lilith",
    },
    {
        "id": 18,
        "name": "Mean_South_Lunar_Node",
        "color": "var(--kerykeion-chart-color-mean-node)",
        "element_points": 0,
        "label": "Mean_South_Lunar_Node",
    },
    {
        "id": 19,
        "name": "True_South_Lunar_Node",
        "color": "var(--kerykeion-chart-color-true-node)",
        "element_points": 0,
        "label": "True_South_Lunar_Node",
    },
    {
        "id": 20,
        "name": "True_Lilith",
        "color": "var(--kerykeion-chart-color-mean-lilith)",
        "element_points": 0,
        "label": "True_Lilith",
    },
    {
        "id": 21,
        "name": "Earth",
        "color": "var(--kerykeion-chart-color-earth)",
        "element_points": 0,
        "label": "Earth",
    },
    {
        "id": 22,
        "name": "Pholus",
        "color": "var(--kerykeion-chart-color-pholus)",
        "element_points": 0,
        "label": "Pholus",
    },
    {
        "id": 23,
        "name": "Ceres",
        "color": "var(--kerykeion-chart-color-ceres)",
        "element_points": 0,
        "label": "Ceres",
    },
    {
        "id": 24,
        "name": "Pallas",
        "color": "var(--kerykeion-chart-color-pallas)",
        "element_points": 0,
        "label": "Pallas",
    },
    {
        "id": 25,
        "name": "Juno",
        "color": "var(--kerykeion-chart-color-juno)",
        "element_points": 0,
        "label": "Juno",
    },
    {
        "id": 26,
        "name": "Vesta",
        "color": "var(--kerykeion-chart-color-vesta)",
        "element_points": 0,
        "label": "Vesta",
    },
    {
        "id": 27,
        "name": "Eris",
        "color": "var(--kerykeion-chart-color-eris)",
        "element_points": 0,
        "label": "Eris",
    },
    {
        "id": 28,
        "name": "Sedna",
        "color": "var(--kerykeion-chart-color-sedna)",
        "element_points": 0,
        "label": "Sedna",
    },
    {
        "id": 29,
        "name": "Haumea",
        "color": "var(--kerykeion-chart-color-haumea)",
        "element_points": 0,
        "label": "Haumea",
    },
    {
        "id": 30,
        "name": "Makemake",
        "color": "var(--kerykeion-chart-color-makemake)",
        "element_points": 0,
        "label": "Makemake",
    },
    {
        "id": 31,
        "name": "Ixion",
        "color": "var(--kerykeion-chart-color-ixion)",
        "element_points": 0,
        "label": "Ixion",
    },
    {
        "id": 32,
        "name": "Orcus",
        "color": "var(--kerykeion-chart-color-orcus)",
        "element_points": 0,
        "label": "Orcus",
    },
    {
        "id": 33,
        "name": "Quaoar",
        "color": "var(--kerykeion-chart-color-quaoar)",
        "element_points": 0,
        "label": "Quaoar",
    },
    {
        "id": 34,
        "name": "Regulus",
        "color": "var(--kerykeion-chart-color-regulus)",
        "element_points": 0,
        "label": "Regulus",
    },
    {
        "id": 35,
        "name": "Spica",
        "color": "var(--kerykeion-chart-color-spica)",
        "element_points": 0,
        "label": "Spica",
    },
    {
        "id": 36,
        "name": "Pars_Fortunae",
        "color": "var(--kerykeion-chart-color-pars-fortunae)",
        "element_points": 5,
        "label": "Fortune",
    },
    {
        "id": 37,
        "name": "Pars_Spiritus",
        "color": "var(--kerykeion-chart-color-pars-spiritus)",
        "element_points": 0,
        "label": "Spirit",
    },
    {
        "id": 38,
        "name": "Pars_Amoris",
        "color": "var(--kerykeion-chart-color-pars-amoris)",
        "element_points": 0,
        "label": "Love",
    },
    {
        "id": 39,
        "name": "Pars_Fidei",
        "color": "var(--kerykeion-chart-color-pars-fidei)",
        "element_points": 0,
        "label": "Faith",
    },
    {
        "id": 40,
        "name": "Vertex",
        "color": "var(--kerykeion-chart-color-vertex)",
        "element_points": 0,
        "label": "Vertex",
    },
    {
        "id": 41,
        "name": "Anti_Vertex",
        "color": "var(--kerykeion-chart-color-anti-vertex)",
        "element_points": 0,
        "label": "Anti_Vertex",
    },
    # Fixed Stars (v5.12 additions -- IDs 42-56)
    {
        "id": 42,
        "name": "Aldebaran",
        "color": "var(--kerykeion-chart-color-aldebaran)",
        "element_points": 0,
        "label": "Aldebaran",
    },
    {
        "id": 43,
        "name": "Antares",
        "color": "var(--kerykeion-chart-color-antares)",
        "element_points": 0,
        "label": "Antares",
    },
    {
        "id": 44,
        "name": "Sirius",
        "color": "var(--kerykeion-chart-color-sirius)",
        "element_points": 0,
        "label": "Sirius",
    },
    {
        "id": 45,
        "name": "Fomalhaut",
        "color": "var(--kerykeion-chart-color-fomalhaut)",
        "element_points": 0,
        "label": "Fomalhaut",
    },
    {
        "id": 46,
        "name": "Algol",
        "color": "var(--kerykeion-chart-color-algol)",
        "element_points": 0,
        "label": "Algol",
    },
    {
        "id": 47,
        "name": "Betelgeuse",
        "color": "var(--kerykeion-chart-color-betelgeuse)",
        "element_points": 0,
        "label": "Betelgeuse",
    },
    {
        "id": 48,
        "name": "Canopus",
        "color": "var(--kerykeion-chart-color-canopus)",
        "element_points": 0,
        "label": "Canopus",
    },
    {
        "id": 49,
        "name": "Procyon",
        "color": "var(--kerykeion-chart-color-procyon)",
        "element_points": 0,
        "label": "Procyon",
    },
    {
        "id": 50,
        "name": "Arcturus",
        "color": "var(--kerykeion-chart-color-arcturus)",
        "element_points": 0,
        "label": "Arcturus",
    },
    {
        "id": 51,
        "name": "Pollux",
        "color": "var(--kerykeion-chart-color-pollux)",
        "element_points": 0,
        "label": "Pollux",
    },
    {
        "id": 52,
        "name": "Deneb",
        "color": "var(--kerykeion-chart-color-deneb)",
        "element_points": 0,
        "label": "Deneb",
    },
    {
        "id": 53,
        "name": "Altair",
        "color": "var(--kerykeion-chart-color-altair)",
        "element_points": 0,
        "label": "Altair",
    },
    {
        "id": 54,
        "name": "Rigel",
        "color": "var(--kerykeion-chart-color-rigel)",
        "element_points": 0,
        "label": "Rigel",
    },
    {
        "id": 55,
        "name": "Achernar",
        "color": "var(--kerykeion-chart-color-achernar)",
        "element_points": 0,
        "label": "Achernar",
    },
    {
        "id": 56,
        "name": "Capella",
        "color": "var(--kerykeion-chart-color-capella)",
        "element_points": 0,
        "label": "Capella",
    },
    {
        "id": 57,
        "name": "Vega",
        "color": "var(--kerykeion-chart-color-vega)",
        "element_points": 0,
        "label": "Vega",
    },
    {
        "id": 58,
        "name": "Alcyone",
        "color": "var(--kerykeion-chart-color-alcyone)",
        "element_points": 0,
        "label": "Alcyone",
    },
    {
        "id": 59,
        "name": "Alphecca",
        "color": "var(--kerykeion-chart-color-alphecca)",
        "element_points": 0,
        "label": "Alphecca",
    },
    {
        "id": 60,
        "name": "Algorab",
        "color": "var(--kerykeion-chart-color-algorab)",
        "element_points": 0,
        "label": "Algorab",
    },
    {
        "id": 61,
        "name": "Deneb_Algedi",
        "color": "var(--kerykeion-chart-color-deneb_algedi)",
        "element_points": 0,
        "label": "Deneb Algedi",
    },
    {
        "id": 62,
        "name": "Alkaid",
        "color": "var(--kerykeion-chart-color-alkaid)",
        "element_points": 0,
        "label": "Alkaid",
    },
    # Lilith/Priapus variants (v6.0)
    {
        "id": 63,
        "name": "Interpolated_Lilith",
        "color": "var(--kerykeion-chart-color-mean-lilith)",
        "element_points": 0,
        "label": "Interp_Lilith",
    },
    {
        "id": 64,
        "name": "Mean_Priapus",
        "color": "var(--kerykeion-chart-color-mean-lilith)",
        "element_points": 0,
        "label": "Mean_Priapus",
    },
    {
        "id": 65,
        "name": "True_Priapus",
        "color": "var(--kerykeion-chart-color-mean-lilith)",
        "element_points": 0,
        "label": "True_Priapus",
    },
    # Lunar apse points (v6.0)
    {
        "id": 74,
        "name": "Interpolated_Perigee",
        "color": "var(--kerykeion-chart-color-mean-lilith)",
        "element_points": 0,
        "label": "Interp_Perigee",
    },
    {
        "id": 75,
        "name": "White_Moon",
        "color": "var(--kerykeion-chart-color-mean-lilith)",
        "element_points": 0,
        "label": "White_Moon",
    },
    # Uranian / Hamburg School hypothetical planets
    {
        "id": 66,
        "name": "Cupido",
        "color": "var(--kerykeion-chart-color-cupido)",
        "element_points": 0,
        "label": "Cupido",
    },
    {
        "id": 67,
        "name": "Hades",
        "color": "var(--kerykeion-chart-color-hades)",
        "element_points": 0,
        "label": "Hades",
    },
    {
        "id": 68,
        "name": "Zeus",
        "color": "var(--kerykeion-chart-color-zeus)",
        "element_points": 0,
        "label": "Zeus",
    },
    {
        "id": 69,
        "name": "Kronos",
        "color": "var(--kerykeion-chart-color-kronos)",
        "element_points": 0,
        "label": "Kronos",
    },
    {
        "id": 70,
        "name": "Apollon",
        "color": "var(--kerykeion-chart-color-apollon)",
        "element_points": 0,
        "label": "Apollon",
    },
    {
        "id": 71,
        "name": "Admetos",
        "color": "var(--kerykeion-chart-color-admetos)",
        "element_points": 0,
        "label": "Admetos",
    },
    {
        "id": 72,
        "name": "Vulkanus",
        "color": "var(--kerykeion-chart-color-vulkanus)",
        "element_points": 0,
        "label": "Vulkanus",
    },
    {
        "id": 73,
        "name": "Poseidon",
        "color": "var(--kerykeion-chart-color-poseidon)",
        "element_points": 0,
        "label": "Poseidon",
    },
]


DEFAULT_CHART_ASPECTS_SETTINGS: Final[list[_ChartAspectSetting]] = [
    {
        "degree": 0,
        "name": "conjunction",
        "is_major": True,
        "color": "var(--kerykeion-chart-color-conjunction)",
    },
    {
        "degree": 30,
        "name": "semi-sextile",
        "is_major": False,
        "color": "var(--kerykeion-chart-color-semi-sextile)",
    },
    {
        "degree": 45,
        "name": "semi-square",
        "is_major": False,
        "color": "var(--kerykeion-chart-color-semi-square)",
    },
    {
        "degree": 60,
        "name": "sextile",
        "is_major": True,
        "color": "var(--kerykeion-chart-color-sextile)",
    },
    {
        "degree": 72,
        "name": "quintile",
        "is_major": False,
        "color": "var(--kerykeion-chart-color-quintile)",
    },
    {
        "degree": 90,
        "name": "square",
        "is_major": True,
        "color": "var(--kerykeion-chart-color-square)",
    },
    {
        "degree": 120,
        "name": "trine",
        "is_major": True,
        "color": "var(--kerykeion-chart-color-trine)",
    },
    {
        "degree": 135,
        "name": "sesquiquadrate",
        "is_major": False,
        "color": "var(--kerykeion-chart-color-sesquiquadrate)",
    },
    {
        "degree": 144,
        "name": "biquintile",
        "is_major": False,
        "color": "var(--kerykeion-chart-color-biquintile)",
    },
    {
        "degree": 150,
        "name": "quincunx",
        "is_major": False,
        "color": "var(--kerykeion-chart-color-quincunx)",
    },
    {
        "degree": 180,
        "name": "opposition",
        "is_major": True,
        "color": "var(--kerykeion-chart-color-opposition)",
    },
]


# =============================================================================
# Dynamic fixed-star settings (v6)
# =============================================================================
# Catalog fixed stars passed via ``active_fixed_stars`` may not have a dedicated
# entry in ``DEFAULT_CELESTIAL_POINTS_SETTINGS``. The chart drawer extends
# its settings list at runtime with synthetic entries produced here, so any
# star from the libephemeris catalog can render on the wheel with a fallback
# glyph and a default color.

DYNAMIC_FIXED_STAR_SETTING_ID_BASE: Final[int] = 1000
"""Base ID for synthetic fixed-star settings. Chosen well above the highest
static ID in DEFAULT_CELESTIAL_POINTS_SETTINGS (~75)."""


DEFAULT_FIXED_STAR_COLOR: Final[str] = "var(--kerykeion-chart-color-fixed-star-default, #d4a053)"
"""Fallback color for dynamic fixed stars without a dedicated CSS variable."""


#: Names that ship with their own ``<symbol id="...">`` in the SVG templates.
#: Anything not in this set falls back to the generic ``#FixedStar`` glyph.
KNOWN_GLYPH_NAMES: Final[frozenset[str]] = frozenset({
    # Planets
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Pluto",
    # Lunar nodes
    "Mean_North_Lunar_Node", "True_North_Lunar_Node",
    "Mean_South_Lunar_Node", "True_South_Lunar_Node",
    # Centaurs / Lilith / minor bodies
    "Chiron", "Pholus", "Mean_Lilith", "True_Lilith", "Earth",
    # Asteroids
    "Ceres", "Pallas", "Juno", "Vesta",
    # TNOs
    "Eris", "Sedna", "Haumea", "Makemake", "Ixion", "Orcus", "Quaoar",
    # Hardcoded fixed stars with dedicated glyphs
    "Regulus", "Spica", "Aldebaran", "Antares", "Sirius", "Fomalhaut",
    "Algol", "Betelgeuse", "Canopus", "Procyon", "Arcturus", "Pollux",
    "Deneb", "Altair", "Rigel", "Achernar", "Capella", "Vega",
    "Alcyone", "Alphecca", "Algorab", "Deneb_Algedi", "Alkaid",
    # Arabic parts
    "Pars_Fortunae", "Pars_Spiritus", "Pars_Amoris", "Pars_Fidei",
    # Axes / extras
    "Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli",
    "Vertex", "Anti_Vertex", "East_Point",
    # Uranian hypotheticals
    "Cupido", "Hades", "Zeus", "Kronos", "Apollon", "Admetos",
    "Vulkanus", "Poseidon",
})


def resolve_glyph_id(name: str) -> str:
    """Resolve the SVG ``<symbol>`` id for a given point name.

    Returns the name itself for known glyphs, or ``"FixedStar"`` as a
    catch-all for catalog fixed stars (and any other future dynamic point)
    that doesn't ship a dedicated symbol in the templates.
    """
    return name if name in KNOWN_GLYPH_NAMES else "FixedStar"


def build_dynamic_fixed_star_settings(
    star_names: "list[str]",
    existing_settings: "list | tuple",
) -> "list[_CelestialPointSetting]":
    """Build per-star ``_CelestialPointSetting`` entries for dynamic catalog stars.

    Skips names that already appear in ``existing_settings`` (e.g. the 23
    hardcoded entries) so they keep their dedicated colors and labels.

    Args:
        star_names: Catalog star names (IAU canonical, with spaces). The
            resulting setting uses the same string for both ``name`` and
            ``label`` and tags ``glyph_id="FixedStar"`` for the generic glyph.
        existing_settings: Current celestial-point settings list; entries
            with matching names are skipped.
    """
    existing_names = {body.get("name") for body in existing_settings}
    extras: list[_CelestialPointSetting] = []
    for i, name in enumerate(star_names):
        if name in existing_names:
            continue
        entry: _CelestialPointSetting = {
            "id": DYNAMIC_FIXED_STAR_SETTING_ID_BASE + i,
            "name": name,
            "color": DEFAULT_FIXED_STAR_COLOR,
            "element_points": 0,
            "label": name.replace("_", " "),
            "glyph_id": "FixedStar",
        }
        extras.append(entry)
    return extras


#: Default active points for predictive factories (midpoints, solar arcs, etc.).
DEFAULT_PREDICTIVE_POINTS: Final[tuple[str, ...]] = (
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
    "True_North_Lunar_Node",
    "True_South_Lunar_Node",
    "Chiron",
    "Mean_Lilith",
    "Ascendant",
    "Medium_Coeli",
)


__all__ = [
    "DEFAULT_CHART_COLORS",
    "DEFAULT_CELESTIAL_POINTS_SETTINGS",
    "DEFAULT_CHART_ASPECTS_SETTINGS",
    "DEFAULT_PREDICTIVE_POINTS",
    "DYNAMIC_FIXED_STAR_SETTING_ID_BASE",
    "DEFAULT_FIXED_STAR_COLOR",
    "build_dynamic_fixed_star_settings",
    "KNOWN_GLYPH_NAMES",
    "resolve_glyph_id",
]
