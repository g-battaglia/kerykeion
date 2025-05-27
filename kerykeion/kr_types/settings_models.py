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
    True_Lilith: str = Field(title="True Lilith", description="The name of True Lilith in the chart, in the language")
    Earth: str = Field(title="Earth", description="The name of Earth in the chart, in the language")
    Pholus: str = Field(title="Pholus", description="The name of Pholus in the chart, in the language")
    Ceres: str = Field(title="Ceres", description="The name of Ceres in the chart, in the language")
    Pallas: str = Field(title="Pallas", description="The name of Pallas in the chart, in the language")
    Juno: str = Field(title="Juno", description="The name of Juno in the chart, in the language")
    Vesta: str = Field(title="Vesta", description="The name of Vesta in the chart, in the language")
    Eris: str = Field(title="Eris", description="The name of Eris in the chart, in the language")
    Sedna: str = Field(title="Sedna", description="The name of Sedna in the chart, in the language")
    Haumea: str = Field(title="Haumea", description="The name of Haumea in the chart, in the language")
    Makemake: str = Field(title="Makemake", description="The name of Makemake in the chart, in the language")
    Ixion: str = Field(title="Ixion", description="The name of Ixion in the chart, in the language")
    Orcus: str = Field(title="Orcus", description="The name of Orcus in the chart, in the language")
    Quaoar: str = Field(title="Quaoar", description="The name of Quaoar in the chart, in the language")
    Regulus: str = Field(title="Regulus", description="The name of Regulus in the chart, in the language")
    Spica: str = Field(title="Spica", description="The name of Spica in the chart, in the language")
    Pars_Fortunae: str = Field(title="Part of Fortune", description="The name of Part of Fortune in the chart, in the language")
    Pars_Spiritus: str = Field(title="Part of Spirit", description="The name of Part of Spirit in the chart, in the language")
    Pars_Amoris: str = Field(title="Part of Love", description="The name of Part of Love in the chart, in the language")
    Pars_Fidei: str = Field(title="Part of Faith", description="The name of Part of Faith in the chart, in the language")
    Vertex: str = Field(title="Vertex", description="The name of Vertex in the chart, in the language")
    Anti_Vertex: str = Field(title="Anti-Vertex", description="The name of Anti-Vertex in the chart, in the language")

class KerykeionLanguageModel(SubscriptableBaseModel):
    """
    This model is used to store the language settings for the chart,
    it's used to translate the celestial points and the other labels
    """

    info: str = Field(title="Info", description="The info label in the chart, in the language")
    cusp: str = Field(title="Cusp", description="The cusp label in the chart, in the language")
    longitude: str = Field(title="Longitude", description="The longitude label in the chart, in the language")
    latitude: str = Field(title="Latitude", description="The latitude label in the chart, in the language")
    north: str = Field(title="North", description="The north label in the chart, in the language")
    east: str = Field(title="East", description="The east label in the chart, in the language")
    south: str = Field(title="South", description="The south label in the chart, in the language")
    west: str = Field(title="West", description="The west label in the chart, in the language")
    fire: str = Field(title="Fire", description="The fire element label in the chart, in the language")
    earth: str = Field(title="Earth", description="The earth element label in the chart, in the language")
    air: str = Field(title="Air", description="The air element label in the chart, in the language")
    water: str = Field(title="Water", description="The water element label in the chart, in the language")
    and_word: str = Field(title="And", description="The 'and' word in the chart, in the language")
    transits: str = Field(title="Transits", description="The transits label in the chart, in the language")
    type: str = Field(title="Type", description="The type label in the chart, in the language")
    couple_aspects: str = Field(title="Couple Aspects", description="The couple aspects label in the chart, in the language")
    transit_aspects: str = Field(title="Transit Aspects", description="The transit aspects label in the chart, in the language")
    planets_and_house: str = Field(title="Planets and House", description="The planets and house label in the chart, in the language")
    transit_name: str = Field(title="Transit Name", description="The transit name label in the chart, in the language")
    lunar_phase: str = Field(title="Lunar Phase", description="The lunar phase label in the chart, in the language")
    lunation_day: str = Field(title="Lunation Day", description="The lunation day label in the chart, in the language")
    day: str = Field(title="Day", description="The day label in the chart, in the language")
    celestial_points: KerykeionLanguageCelestialPointModel = Field(title="Celestial Points", description="The celestial points translations in the chart, in the language")
    composite_chart: str = Field(title="Composite Chart", description="The composite chart label in the chart, in the language")
    midpoints: str = Field(title="Midpoints", description="The midpoints label in the chart, in the language")
    north_letter: str = Field(title="North Letter", description="The north letter in the chart, in the language")
    east_letter: str = Field(title="East Letter", description="The east letter in the chart, in the language")
    south_letter: str = Field(title="South Letter", description="The south letter in the chart, in the language")
    west_letter: str = Field(title="West Letter", description="The west letter in the chart, in the language")
    tropical: str = Field(title="Tropical", description="The tropical zodiac label in the chart, in the language")
    sidereal: str = Field(title="Sidereal", description="The sidereal zodiac label in the chart, in the language")
    zodiac: str = Field(title="Zodiac", description="The zodiac label in the chart, in the language")
    ayanamsa: str = Field(title="Ayanamsa", description="The ayanamsa label in the chart, in the language")
    apparent_geocentric: str = Field(title="Apparent Geocentric", description="The apparent geocentric label in the chart, in the language")
    heliocentric: str = Field(title="Heliocentric", description="The heliocentric label in the chart, in the language")
    topocentric: str = Field(title="Topocentric", description="The topocentric label in the chart, in the language")
    true_geocentric: str = Field(title="True Geocentric", description="The true geocentric label in the chart, in the language")
    new_moon: str = Field(title="New Moon", description="The new moon label in the chart, in the language")
    waxing_crescent: str = Field(title="Waxing Crescent", description="The waxing crescent label in the chart, in the language")
    first_quarter: str = Field(title="First Quarter", description="The first quarter label in the chart, in the language")
    waxing_gibbous: str = Field(title="Waxing Gibbous", description="The waxing gibbous label in the chart, in the language")
    full_moon: str = Field(title="Full Moon", description="The full moon label in the chart, in the language")
    waning_gibbous: str = Field(title="Waning Gibbous", description="The waning gibbous label in the chart, in the language")
    last_quarter: str = Field(title="Last Quarter", description="The last quarter label in the chart, in the language")
    waning_crescent: str = Field(title="Waning Crescent", description="The waning crescent label in the chart, in the language")
    houses: str = Field(title="Houses", description="The houses label in the chart, in the language")
    domification: str = Field(title="Domification", description="The domification label in the chart, in the language")
    houses_system_A: str = Field(title="Houses System A", description="The houses system A label in the chart, in the language")
    houses_system_B: str = Field(title="Houses System B", description="The houses system B label in the chart, in the language")
    houses_system_C: str = Field(title="Houses System C", description="The houses system C label in the chart, in the language")
    houses_system_D: str = Field(title="Houses System D", description="The houses system D label in the chart, in the language")
    houses_system_F: str = Field(title="Houses System F", description="The houses system F label in the chart, in the language")
    houses_system_H: str = Field(title="Houses System H", description="The houses system H label in the chart, in the language")
    houses_system_I: str = Field(title="Houses System I", description="The houses system I label in the chart, in the language")
    houses_system_i: str = Field(title="Houses System i", description="The houses system i label in the chart, in the language")
    houses_system_K: str = Field(title="Houses System K", description="The houses system K label in the chart, in the language")
    houses_system_L: str = Field(title="Houses System L", description="The houses system L label in the chart, in the language")
    houses_system_M: str = Field(title="Houses System M", description="The houses system M label in the chart, in the language")
    houses_system_N: str = Field(title="Houses System N", description="The houses system N label in the chart, in the language")
    houses_system_O: str = Field(title="Houses System O", description="The houses system O label in the chart, in the language")
    houses_system_P: str = Field(title="Houses System P", description="The houses system P label in the chart, in the language")
    houses_system_Q: str = Field(title="Houses System Q", description="The houses system Q label in the chart, in the language")
    houses_system_R: str = Field(title="Houses System R", description="The houses system R label in the chart, in the language")
    houses_system_S: str = Field(title="Houses System S", description="The houses system S label in the chart, in the language")
    houses_system_T: str = Field(title="Houses System T", description="The houses system T label in the chart, in the language")
    houses_system_U: str = Field(title="Houses System U", description="The houses system U label in the chart, in the language")
    houses_system_V: str = Field(title="Houses System V", description="The houses system V label in the chart, in the language")
    houses_system_W: str = Field(title="Houses System W", description="The houses system W label in the chart, in the language")
    houses_system_X: str = Field(title="Houses System X", description="The houses system X label in the chart, in the language")
    houses_system_Y: str = Field(title="Houses System Y", description="The houses system Y label in the chart, in the language")
    Natal: str = Field(title="Natal", description="The natal chart label in the chart, in the language")
    ExternalNatal: str = Field(title="External Natal", description="The external natal chart label in the chart, in the language")
    Synastry: str = Field(title="Synastry", description="The synastry chart label in the chart, in the language")
    Transit: str = Field(title="Transit", description="The transit chart label in the chart, in the language")
    Composite: str = Field(title="Composite", description="The composite chart label in the chart, in the language")
    Return: str = Field(title="Return", description="The return chart label in the chart, in the language")
    return_aspects: str = Field(title="Return Aspects", description="The return aspects label in the chart, in the language")
    solar_return: str = Field(title="Solar Return", description="The solar return label in the chart, in the language")
    lunar_return: str = Field(title="Lunar Return", description="The lunar return label in the chart, in the language")
    inner_wheel: str = Field(title="Inner Wheel", description="The inner wheel label in the chart, in the language")
    outer_wheel: str = Field(title="Outer Wheel", description="The outer wheel label in the chart, in the language")
    house_position_comparison: str = Field(title="House Position Comparison", description="The house position comparison label in the chart, in the language")
    return_point: str = Field(title="Return Point", description="The return point label in the chart, in the language")
    natal: str = Field(title="Natal", description="The natal label in the chart, in the language")
    perspective_type: str = Field(title="Perspective Type", description="The perspective type label in the chart, in the language")

# Settings Model
class KerykeionSettingsModel(SubscriptableBaseModel):
    """
    This class is used to define the global settings for the Kerykeion.
    """
    language_settings: dict[str, KerykeionLanguageModel] = Field(title="Language Settings", description="The language settings of the chart")
