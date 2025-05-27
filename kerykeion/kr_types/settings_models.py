# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""


from pydantic import Field
from typing import List, Optional, Union
from kerykeion.kr_types.kr_models import SubscriptableBaseModel


class KerykeionSettingsCelestialPointModel(SubscriptableBaseModel):
    """
    Defines the model for a celestial point data.
    """

    id: int = Field(title="Celestial Point ID", description="Celestial Point ID according to Pyswisseph")
    name: str = Field(title="Celestial Point Name", description="Celestial Point Name")
    color: str = Field(title="Celestial Point Color", description="Celestial Point Color, used in the chart")
    element_points: int = Field(title="Celestial Point Element Points", description="Element Points given to the celestial point")
    label: str = Field(title="Celestial Point Label", description="The name of the celestial point in the chart, it can be different from the name")
    is_active: Optional[bool] = Field(title="Celestial Point is Active", description="Indicates if the celestial point is active in the chart", default=None)

# Aspect Settings
class KerykeionSettingsAspectModel(SubscriptableBaseModel):
    """
    Defines the model for an aspect.
    """

    degree: int = Field(title="Aspect Degrees", description="The degree of the aspect")
    name: str = Field(title="Aspect Name", description="The name of the aspect")
    color: str = Field(title="Aspect Color", description="The color of the aspect")
    orb: Optional[int] = Field(title="Aspect Orb", description="The orb of the aspect", default=None)

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
    Ascendant: str = Field(title="Ascendant", description="The name of Ascendant in the chart, in the language")
    Descendant: str = Field(title="Descendant", description="The name of Descendant in the chart, in the language")
    Medium_Coeli: str = Field(title="Medium Coeli", description="The name of Medium Coeli in the chart, in the language")
    Imum_Coeli: str = Field(title="Imum Coeli", description="The name of Imum Coeli in the chart, in the language")
    Mean_Lilith: str = Field(title="Mean Lilith", description="The name of Mean Lilith in the chart, in the language")
    True_South_Node: str = Field(title="True South Node", description="The name of True South Node in the chart, in the language")
    Mean_South_Node: str = Field(title="Mean South Node", description="The name of Mean South Node in the chart, in the language")


class KerykeionLanguageModel(SubscriptableBaseModel):
    """
    This model is used to store the language settings for the chart,
    it's used to translate the celestial points and the other labels
    """

    info: str
    cusp: str
    longitude: str
    latitude: str
    north: str
    east: str
    south: str
    west: str
    fire: str
    earth: str
    air: str
    water: str
    and_word: str
    transits: str
    type: str
    couple_aspects: str
    transit_aspects: str
    planets_and_house: str
    transit_name: str
    lunar_phase: str
    lunation_day: str
    day: str
    celestial_points: KerykeionLanguageCelestialPointModel
    composite_chart: str
    midpoints: str
    north_letter: str
    east_letter: str
    south_letter: str
    west_letter: str
    tropical: str
    sidereal: str
    zodiac: str
    ayanamsa: str
    apparent_geocentric: str
    heliocentric: str
    topocentric: str
    true_geocentric: str
    new_moon: str
    waxing_crescent: str
    first_quarter: str
    waxing_gibbous: str
    full_moon: str
    waning_gibbous: str
    last_quarter: str
    waning_crescent: str
    houses: str
    houses_system_A: str
    houses_system_B: str
    houses_system_C: str
    houses_system_D: str
    houses_system_F: str
    houses_system_H: str
    houses_system_I: str
    houses_system_i: str
    houses_system_K: str
    houses_system_L: str
    houses_system_M: str
    houses_system_N: str
    houses_system_O: str
    houses_system_P: str
    houses_system_Q: str
    houses_system_R: str
    houses_system_S: str
    houses_system_T: str
    houses_system_U: str
    houses_system_V: str
    houses_system_W: str
    houses_system_X: str
    houses_system_Y: str
    Natal: str
    ExternalNatal: str
    Synastry: str
    Transit: str
    Composite: str
    Return: str
    return_aspects: str
    solar_return: str
    lunar_return: str
    inner_wheel: str
    outer_wheel: str
    house_position_comparison: str
    return_point: str
    natal: str
    perspective_type: str
    domification: str

class KerykeionGeneralSettingsModel(SubscriptableBaseModel):
    axes_orbit: int = Field(title="Axes Orbit", description="The orbit of the axes in the chart")


# Settings Model
class KerykeionSettingsModel(SubscriptableBaseModel):
    """
    This class is used to define the global settings for the Kerykeion.
    """
    aspects: List[KerykeionSettingsAspectModel] = Field(title="Aspects", description="The list of the aspects of the chart")
    language_settings: dict[str, KerykeionLanguageModel] = Field(title="Language Settings", description="The language settings of the chart")
    general_settings: KerykeionGeneralSettingsModel = Field(title="General Settings", description="The general settings of the chart")
