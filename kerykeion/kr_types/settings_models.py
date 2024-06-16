# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2024 Giacomo Battaglia
"""


from pydantic import Field
from typing import List
from kerykeion.kr_types.kr_models import SubscriptableBaseModel


class KerykeionSettingsCelestialPointModel(SubscriptableBaseModel):
    """
    Defines the model for a celestial point data.
    """

    id: int = Field(title="Celestial Point ID", description="Celestial Point ID according to Pyswisseph")
    name: str = Field(title="Celestial Point Name", description="Celestial Point Name")
    color: str = Field(title="Celestial Point Color", description="Celestial Point Color, used in the chart")
    is_active: bool = Field(title="Celestial Point is Active", description="Indicates if the celestial point is active in the chart")
    element_points: int = Field(title="Celestial Point Element Points", description="Element Points given to the celestial point")
    related_zodiac_signs: List[int] = Field(title="Celestial Point Related Zodiac Signs", description="Zodiac Signs related to the celestial point")
    label: str = Field(title="Celestial Point Label", description="The name of the celestial point in the chart, it can be different from the name")


# Chart Colors Settings
class KerykeionSettingsChartColorsModel(SubscriptableBaseModel):
    """
    Defines the model for the chart colors.
    """

    paper_0: str = Field(title="Paper Color 0", description="Paper Color 0")
    paper_1: str = Field(title="Paper Color 1", description="Paper Color 1")
    zodiac_bg_0: str = Field(title="Zodiac Background Color 0", description="Zodiac Background Color 0")
    zodiac_bg_1: str = Field(title="Zodiac Background Color 1", description="Zodiac Background Color 1")
    zodiac_bg_2: str = Field(title="Zodiac Background Color 2", description="Zodiac Background Color 2")
    zodiac_bg_3: str = Field(title="Zodiac Background Color 3", description="Zodiac Background Color 3")
    zodiac_bg_4: str = Field(title="Zodiac Background Color 4", description="Zodiac Background Color 4")
    zodiac_bg_5: str = Field(title="Zodiac Background Color 5", description="Zodiac Background Color 5")
    zodiac_bg_6: str = Field(title="Zodiac Background Color 6", description="Zodiac Background Color 6")
    zodiac_bg_7: str = Field(title="Zodiac Background Color 7", description="Zodiac Background Color 7")
    zodiac_bg_8: str = Field(title="Zodiac Background Color 8", description="Zodiac Background Color 8")
    zodiac_bg_9: str = Field(title="Zodiac Background Color 9", description="Zodiac Background Color 9")
    zodiac_bg_10: str = Field(title="Zodiac Background Color 10", description="Zodiac Background Color 10")
    zodiac_bg_11: str = Field(title="Zodiac Background Color 11", description="Zodiac Background Color 11")
    zodiac_icon_0: str = Field(title="Zodiac Icon Color 0", description="Zodiac Icon Color 0")
    zodiac_icon_1: str = Field(title="Zodiac Icon Color 1", description="Zodiac Icon Color 1")
    zodiac_icon_2: str = Field(title="Zodiac Icon Color 2", description="Zodiac Icon Color 2")
    zodiac_icon_3: str = Field(title="Zodiac Icon Color 3", description="Zodiac Icon Color 3")
    zodiac_icon_4: str = Field(title="Zodiac Icon Color 4", description="Zodiac Icon Color 4")
    zodiac_icon_5: str = Field(title="Zodiac Icon Color 5", description="Zodiac Icon Color 5")
    zodiac_icon_6: str = Field(title="Zodiac Icon Color 6", description="Zodiac Icon Color 6")
    zodiac_icon_7: str = Field(title="Zodiac Icon Color 7", description="Zodiac Icon Color 7")
    zodiac_icon_8: str = Field(title="Zodiac Icon Color 8", description="Zodiac Icon Color 8")
    zodiac_icon_9: str = Field(title="Zodiac Icon Color 9", description="Zodiac Icon Color 9")
    zodiac_icon_10: str = Field(title="Zodiac Icon Color 10", description="Zodiac Icon Color 10")
    zodiac_icon_11: str = Field(title="Zodiac Icon Color 11", description="Zodiac Icon Color 11")
    zodiac_radix_ring_0: str = Field(title="Zodiac Radix Ring Color 0", description="Zodiac Radix Ring Color 0")
    zodiac_radix_ring_1: str = Field(title="Zodiac Radix Ring Color 1", description="Zodiac Radix Ring Color 1")
    zodiac_radix_ring_2: str = Field(title="Zodiac Radix Ring Color 2", description="Zodiac Radix Ring Color 2")
    zodiac_transit_ring_0: str = Field(title="Zodiac Transit Ring Color 0", description="Zodiac Transit Ring Color 0")
    zodiac_transit_ring_1: str = Field(title="Zodiac Transit Ring Color 1", description="Zodiac Transit Ring Color 1")
    zodiac_transit_ring_2: str = Field(title="Zodiac Transit Ring Color 2", description="Zodiac Transit Ring Color 2")
    zodiac_transit_ring_3: str = Field(title="Zodiac Transit Ring Color 3", description="Zodiac Transit Ring Color 3")
    houses_radix_line: str = Field(title="Houses Radix Line Color", description="Houses Radix Line Color")
    houses_transit_line: str = Field(title="Houses Transit Line Color", description="Houses Transit Line Color")
    lunar_phase_0: str = Field(title="Lunar Phase Color 0", description="Lunar Phase Color 0")
    lunar_phase_1: str = Field(title="Lunar Phase Color 1", description="Lunar Phase Color 1")
    lunar_phase_2: str = Field(title="Lunar Phase Color 2", description="Lunar Phase Color 2")


# Aspect Settings
class KerykeionSettingsAspectModel(SubscriptableBaseModel):
    """
    Defines the model for an aspect.
    """

    degree: int = Field(title="Aspect Degrees", description="The degree of the aspect")
    name: str = Field(title="Aspect Name", description="The name of the aspect")
    is_active: bool = Field(title="Aspect is Active", description="Is the aspect active?")
    visible_grid: bool = Field(title="Aspect Visible Grid", description="Is the aspect visible in the grid?")
    is_major: bool = Field(title="Aspect is Major", description="Is the aspect major?")
    is_minor: bool = Field(title="Aspect is Minor", description="Is the aspect minor?")
    orb: int = Field(title="Aspect Orb", description="The orb of the aspect")
    color: str = Field(title="Aspect Color", description="The color of the aspect")


# Language Settings
class KerykeionLanguageCelestialPointModel(SubscriptableBaseModel):
    """
    This class is used to define the labels, show in the chart, for the celestial points.
    It is used to translate the celestial points in the language of the chart.
    """

    Sun: str = Field(title="Sun", description="The name of the Sun in the chart, in the language")
    Moon: str = Field(title="Moon", description="The name of the Moon in the chart, in the language")
    Mercury: str = Field(title="Mercury", description="The name of Mercury in the chart, in the language")
    Venus: str = Field(title="Venus", description="The name of Venus in the chart, in the language")
    Mars: str = Field(title="Mars", description="The name of Mars in the chart, in the language")
    Jupiter: str = Field(title="Jupiter", description="The name of Jupiter in the chart, in the language")
    Saturn: str = Field(title="Saturn", description="The name of Saturn in the chart, in the language")
    Uranus: str = Field(title="Uranus", description="The name of Uranus in the chart, in the language")
    Neptune: str = Field(title="Neptune", description="The name of Neptune in the chart, in the language")
    Pluto: str = Field(title="Pluto", description="The name of Pluto in the chart, in the language")
    True_Node: str = Field(title="True Node", description="The name of True Node in the chart, in the language")
    Mean_Node: str = Field(title="Mean Node", description="The name of Mean Node in the chart, in the language")
    Chiron: str = Field(title="Chiron", description="The name of Chiron in the chart, in the language")
    Asc: str = Field(title="Ascendant", description="The name of Ascendant in the chart, in the language")
    Mc: str = Field(title="Medium Coeli", description="The name of Medium Coeli in the chart, in the language")
    Dsc: str = Field(title="Descendant", description="The name of Descendant in the chart, in the language")
    Ic: str = Field(title="Imum Coeli", description="The name of Imum Coeli in the chart, in the language")


class KerykeionLanguageModel(SubscriptableBaseModel):
    """
    This model is used to store the language settings for the chart,
    it's used to translate the celestial points and the other labels
    """

    info: str = Field(title="Info", description="The name of the Info label in the chart, in the language")
    cusp: str = Field(title="Cusp", description="The name of the Cusp label in the chart, in the language")
    longitude: str = Field(title="Longitude", description="The name of the Longitude label in the chart, in the language")
    latitude: str = Field(title="Latitude", description="The name of the Latitude label in the chart, in the language")
    north: str = Field(title="North", description="The name of the North label in the chart, in the language")
    east: str = Field(title="East", description="The name of the East label in the chart, in the language")
    south: str = Field(title="South", description="The name of the South label in the chart, in the language")
    west: str = Field(title="West", description="The name of the West label in the chart, in the language")
    fire: str = Field(title="Fire", description="The name of the Fire label in the chart, in the language")
    earth: str = Field(title="Earth", description="The name of the Earth label in the chart, in the language")
    air: str = Field(title="Air", description="The name of the Air label in the chart, in the language")
    water: str = Field(title="Water", description="The name of the Water label in the chart, in the language")
    and_word: str = Field(title="And", description="The name of the And word in the chart, in the language")
    transits: str = Field(title="Transits", description="The name of the Transits label in the chart, in the language")
    type: str = Field(title="Type", description="The name of the Type label in the chart, in the language")
    aspects: str = Field(title="Aspects", description="The name of the Aspects label in the chart, in the language")
    planets_and_house: str = Field(title="Planets and Houses", description="The name of the Planets and Houses label in the chart, in the language")
    transit_name: str = Field(title="Transit Name", description="The name of the Transit Name label in the chart, in the language")
    lunar_phase: str = Field(title="Lunar Phase", description="The name of the Lunar Phase label in the chart, in the language")
    day: str = Field(title="Day", description="The name of the Day label in the chart, in the language")
    celestial_points: KerykeionLanguageCelestialPointModel


class KerykeionGeneralSettingsModel(SubscriptableBaseModel):
    axes_orbit: int = Field(title="Axes Orbit", description="The orbit of the axes in the chart")
    planet_in_zodiac_extra_points: int = Field(title="Planet in Zodiac Extra Points", description="The extra points of the planet in the zodiac")
    language: str = Field(title="Language", description="The language of the chart")

class KerykeionChartSettingsModel(SubscriptableBaseModel):
    basic_chart_viewBox: str = Field(title="Basic Chart ViewBox", description="The viewbox of the basic chart")
    wide_chart_viewBox: str = Field(title="Wide Chart ViewBox", description="The viewbox of the wide chart")

# Settings Model
class KerykeionSettingsModel(SubscriptableBaseModel):
    """
    This class is used to define the global settings for the Kerykeion.
    """

    chart_colors: KerykeionSettingsChartColorsModel = Field(title="Chart Colors", description="The colors of the chart")
    celestial_points: List[KerykeionSettingsCelestialPointModel] = Field(title="Celestial Points", description="The list of the celestial points of the chart")
    aspects: List[KerykeionSettingsAspectModel] = Field(title="Aspects", description="The list of the aspects of the chart")
    language_settings: dict[str, KerykeionLanguageModel] = Field(title="Language Settings", description="The language settings of the chart")
    general_settings: KerykeionGeneralSettingsModel = Field(title="General Settings", description="The general settings of the chart")
    chart_settings: KerykeionChartSettingsModel = Field(title="Chart Settings", description="The chart settings of the chart")