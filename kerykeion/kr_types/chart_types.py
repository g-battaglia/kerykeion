from typing_extensions import TypedDict


class ChartTemplateDictionary(TypedDict):
    transitRing: str
    degreeRing: str
    first_circle: str
    second_circle: str
    third_circle: str
    makeAspects: str
    makeAspectGrid: str
    makeDoubleChartAspectList: str
    makeHouseComparisonGrid: str
    chart_height: float
    chart_width: float
    viewbox: str
    stringTitle: str
    top_left_0: str
    bottom_left_0: str
    bottom_left_1: str
    bottom_left_2: str
    bottom_left_3: str
    bottom_left_4: str
    top_left_1: str
    top_left_2: str
    top_left_3: str
    top_left_4: str
    top_left_5: str

    # Font color
    paper_color_0: str
    # Background color of the chart
    paper_color_1: str

    # Planets colors, from 0 to 16 (0 is the Sun)
    planets_color_0: str
    planets_color_1: str
    planets_color_2: str
    planets_color_3: str
    planets_color_4: str
    planets_color_5: str
    planets_color_6: str
    planets_color_7: str
    planets_color_8: str
    planets_color_9: str
    planets_color_10: str
    planets_color_11: str
    planets_color_12: str
    planets_color_13: str
    planets_color_14: str
    planets_color_15: str
    planets_color_16: str

    # Zodiac colors, from 0 to 11 (0 is Aries)
    zodiac_color_0: str
    zodiac_color_1: str
    zodiac_color_2: str
    zodiac_color_3: str
    zodiac_color_4: str
    zodiac_color_5: str
    zodiac_color_6: str
    zodiac_color_7: str
    zodiac_color_8: str
    zodiac_color_9: str
    zodiac_color_10: str
    zodiac_color_11: str

    # Aspects colors, from 0 to 9 (0 is conjunction)
    orb_color_0: str
    orb_color_30: str
    orb_color_45: str
    orb_color_60: str
    orb_color_72: str
    orb_color_90: str
    orb_color_120: str
    orb_color_135: str
    orb_color_144: str
    orb_color_150: str
    orb_color_180: str

    cfgTranslate: str
    makeZodiac: str
    makeHouses: str
    makePlanets: str
    makePlanetGrid: str
    makeHousesGrid: str

    color_style_tag: str

    element_string: str
    fire_string: str
    earth_string: str
    air_string: str
    water_string: str

    quality_string: str
    cardinal_string: str
    fixed_string: str
    mutable_string: str

    makeLunarPhase: str
