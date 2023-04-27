from typing import Literal, Union, Optional
from pydantic import BaseModel


class ChartTemplateModel(BaseModel):
    """Pydantic model for the chart template."""

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    transitRing: str
    degreeRing: str
    c1: str
    c1style: str
    c2: str
    c2style: str
    c3: str
    c3style: str
    makeAspects: bool
    makeAspectGrid: bool
    makePatterns: bool
    chart_width: int
    circleX: int
    circleY: int
    svgWidth: int
    svgHeight: int
    viewbox: str
    stringTitle: str
    stringName: str
    bottomLeft1: str
    bottomLeft2: str
    bottomLeft3: str
    bottomLeft4: str
    lunar_phase_fg: str
    lunar_phase_bg: str
    lunar_phase_cx: int
    lunar_phase_r: int
    lunar_phase_outline: str
    lunar_phase_rotate: int
    stringLocation: str
    stringDateTime: str
    stringLat: str
    stringLon: str
    stringPosition: str
    paper_color_0: str
    paper_color_1: str
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
    cfgZoom: float
    cfgRotate: int
    cfgTranslate: str
    makeZodiac: bool
    makeHouses: bool
    makePlanets: bool
    makeElements: bool
    makePlanetGrid: bool
    makeHousesGrid: bool
