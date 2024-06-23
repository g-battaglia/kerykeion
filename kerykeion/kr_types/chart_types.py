from typing import TypedDict


class ChartTemplateDictionary(TypedDict):
    transitRing: str
    degreeRing: str
    first_circle: str
    second_circle: str
    c3: str
    c3style: str
    makeAspects: str
    makeAspectGrid: str
    makePatterns: str
    chart_height: float
    chart_width: float
    circleX: str
    circleY: str
    svgWidth: str
    svgHeight: str
    viewbox: str
    stringTitle: str
    stringName: str
    bottomLeft0: str
    bottomLeft1: str
    bottomLeft2: str
    bottomLeft3: str
    bottomLeft4: str
    lunar_phase_fg: str
    lunar_phase_bg: str
    lunar_phase_cx: int
    lunar_phase_r: int
    lunar_phase_outline: str
    lunar_phase_rotate: float
    stringLocation: str
    stringDateTime: str
    stringLat: str
    stringLon: str
    stringPosition: str

    # Font color
    paper_color_0: str
    # Background color of the chart
    paper_color_1: str
    
    # Planets colors, from 1 to 15 (0 is the Sun)
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

    cfgZoom: str
    cfgRotate: str
    cfgTranslate: str
    makeZodiac: str
    makeHouses: str
    makePlanets: str
    elements_percentages: str
    makePlanetGrid: str
    makeHousesGrid: str
