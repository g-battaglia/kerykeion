"""
Default settings and presets used by chart generation and calculation routines.

This module centralizes the static values that were previously stored in
`kerykeion.settings.legacy`. Keeping them here avoids scattering hard-coded
configuration across the codebase while still exposing them for reuse.
"""

from __future__ import annotations

from typing import Final, TypedDict


class _CelestialPointSetting(TypedDict, total=False):
    id: int
    name: str
    color: str
    element_points: int
    label: str
    is_active: bool


class _ChartAspectSetting(TypedDict, total=False):
    degree: int
    name: str
    is_major: bool
    color: str
    orb: int


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


__all__ = [
    "DEFAULT_CHART_COLORS",
    "DEFAULT_CELESTIAL_POINTS_SETTINGS",
    "DEFAULT_CHART_ASPECTS_SETTINGS",
]
