from .kr_models import SubscriptableBaseModel


class ChartTemplateModel(SubscriptableBaseModel):
    """
    Pydantic model for chart template variables used in SVG generation.

    This model contains all the template variables required to render
    astrological charts, including colors, dimensions, and SVG components.
    """

    transitRing: str
    """SVG markup for the transit ring"""

    degreeRing: str
    """SVG markup for the degree ring"""

    background_circle: str
    """SVG markup for the background circle"""

    first_circle: str
    """SVG markup for the first circle"""

    second_circle: str
    """SVG markup for the second circle"""

    third_circle: str
    """SVG markup for the third circle"""

    makeAspects: str
    """SVG markup for aspects"""

    makeAspectGrid: str
    """SVG markup for aspect grid"""

    makeDoubleChartAspectList: str
    """SVG markup for double chart aspect list"""

    makeHouseComparisonGrid: str
    """SVG markup for house comparison grid"""

    full_wheel_translate_y: int
    """Vertical translation for the full wheel group"""

    houses_and_planets_translate_y: int
    """Vertical translation for the houses and planets grid group"""

    aspect_grid_translate_y: int
    """Vertical translation for the aspect grid group"""

    aspect_list_translate_y: int
    """Vertical translation for the aspect list group"""

    title_translate_y: int
    """Vertical translation for the title and top-left text block"""

    elements_translate_y: int
    """Vertical translation for the elements summary block"""

    qualities_translate_y: int
    """Vertical translation for the qualities summary block"""

    lunar_phase_translate_y: int
    """Vertical translation for the lunar phase block"""

    bottom_left_translate_y: int
    """Vertical translation for the bottom-left info block"""

    chart_height: float
    """Chart height in pixels"""

    chart_width: float
    """Chart width in pixels"""

    viewbox: str
    """SVG viewBox attribute value"""

    stringTitle: str
    """Chart title string"""

    top_left_0: str
    """Top left panel content - line 0"""

    bottom_left_0: str
    """Bottom left panel content - line 0"""

    bottom_left_1: str
    """Bottom left panel content - line 1"""

    bottom_left_2: str
    """Bottom left panel content - line 2"""

    bottom_left_3: str
    """Bottom left panel content - line 3"""

    bottom_left_4: str
    """Bottom left panel content - line 4"""

    top_left_1: str
    """Top left panel content - line 1"""

    top_left_2: str
    """Top left panel content - line 2"""

    top_left_3: str
    """Top left panel content - line 3"""

    top_left_4: str
    """Top left panel content - line 4"""

    top_left_5: str
    """Top left panel content - line 5"""

    paper_color_0: str
    """Font color"""

    background_color: str
    """Dynamic background color (can be transparent or theme color)"""

    planets_color_0: str
    """Planet color for Sun (index 0)"""

    planets_color_1: str
    """Planet color for Moon (index 1)"""

    planets_color_2: str
    """Planet color for Mercury (index 2)"""

    planets_color_3: str
    """Planet color for Venus (index 3)"""

    planets_color_4: str
    """Planet color for Mars (index 4)"""

    planets_color_5: str
    """Planet color for Jupiter (index 5)"""

    planets_color_6: str
    """Planet color for Saturn (index 6)"""

    planets_color_7: str
    """Planet color for Uranus (index 7)"""

    planets_color_8: str
    """Planet color for Neptune (index 8)"""

    planets_color_9: str
    """Planet color for Pluto (index 9)"""

    planets_color_10: str
    """Planet color for North Node (index 10)"""

    planets_color_11: str
    """Planet color for South Node (index 11)"""

    planets_color_12: str
    """Planet color for Chiron (index 12)"""

    planets_color_13: str
    """Planet color for Ceres (index 13)"""

    planets_color_14: str
    """Planet color for Pallas (index 14)"""

    planets_color_15: str
    """Planet color for Juno (index 15)"""

    planets_color_16: str
    """Planet color for Vesta (index 16)"""

    planets_color_17: str
    """Planet color for Pars Fortunae (index 17)"""

    planets_color_18: str
    """Planet color for Draconic Moon (index 18)"""

    planets_color_19: str
    """Planet color for additional celestial point (index 19)"""

    planets_color_20: str
    """Planet color for celestial point (index 20)"""

    planets_color_21: str
    """Planet color for celestial point (index 21)"""

    planets_color_22: str
    """Planet color for celestial point (index 22)"""

    planets_color_23: str
    """Planet color for celestial point (index 23)"""

    planets_color_24: str
    """Planet color for celestial point (index 24)"""

    planets_color_25: str
    """Planet color for celestial point (index 25)"""

    planets_color_26: str
    """Planet color for celestial point (index 26)"""

    planets_color_27: str
    """Planet color for celestial point (index 27)"""

    planets_color_28: str
    """Planet color for celestial point (index 28)"""

    planets_color_29: str
    """Planet color for celestial point (index 29)"""

    planets_color_30: str
    """Planet color for celestial point (index 30)"""

    planets_color_31: str
    """Planet color for celestial point (index 31)"""

    planets_color_32: str
    """Planet color for celestial point (index 32)"""

    planets_color_33: str
    """Planet color for celestial point (index 33)"""

    planets_color_34: str
    """Planet color for celestial point (index 34)"""

    planets_color_35: str
    """Planet color for celestial point (index 35)"""

    planets_color_36: str
    """Planet color for celestial point (index 36)"""

    planets_color_37: str
    """Planet color for celestial point (index 37)"""

    planets_color_38: str
    """Planet color for celestial point (index 38)"""

    planets_color_39: str
    """Planet color for celestial point (index 39)"""

    planets_color_40: str
    """Planet color for celestial point (index 40)"""

    planets_color_41: str
    """Planet color for celestial point (index 41)"""

    zodiac_color_0: str
    """Zodiac color for Aries (index 0)"""

    zodiac_color_1: str
    """Zodiac color for Taurus (index 1)"""

    zodiac_color_2: str
    """Zodiac color for Gemini (index 2)"""

    zodiac_color_3: str
    """Zodiac color for Cancer (index 3)"""

    zodiac_color_4: str
    """Zodiac color for Leo (index 4)"""

    zodiac_color_5: str
    """Zodiac color for Virgo (index 5)"""

    zodiac_color_6: str
    """Zodiac color for Libra (index 6)"""

    zodiac_color_7: str
    """Zodiac color for Scorpio (index 7)"""

    zodiac_color_8: str
    """Zodiac color for Sagittarius (index 8)"""

    zodiac_color_9: str
    """Zodiac color for Capricorn (index 9)"""

    zodiac_color_10: str
    """Zodiac color for Aquarius (index 10)"""

    zodiac_color_11: str
    """Zodiac color for Pisces (index 11)"""

    orb_color_0: str
    """Aspect color for conjunction (0°)"""

    orb_color_30: str
    """Aspect color for semi-sextile (30°)"""

    orb_color_45: str
    """Aspect color for semi-square (45°)"""

    orb_color_60: str
    """Aspect color for sextile (60°)"""

    orb_color_72: str
    """Aspect color for quintile (72°)"""

    orb_color_90: str
    """Aspect color for square (90°)"""

    orb_color_120: str
    """Aspect color for trine (120°)"""

    orb_color_135: str
    """Aspect color for sesqui-quadrate (135°)"""

    orb_color_144: str
    """Aspect color for bi-quintile (144°)"""

    orb_color_150: str
    """Aspect color for quincunx (150°)"""

    orb_color_180: str
    """Aspect color for opposition (180°)"""

    makeZodiac: str
    """SVG markup for zodiac signs"""

    makeHouses: str
    """SVG markup for houses"""

    makePlanets: str
    """SVG markup for planets"""

    makeMainPlanetGrid: str
    """SVG markup for main planet grid"""

    makeSecondaryPlanetGrid: str
    """SVG markup for secondary planet grid"""

    makeMainHousesGrid: str
    """SVG markup for main houses grid"""

    makeSecondaryHousesGrid: str
    """SVG markup for secondary houses grid"""

    color_style_tag: str
    """CSS color style tag"""

    elements_string: str
    """Elements header string"""

    fire_string: str
    """Fire element string with percentage"""

    earth_string: str
    """Earth element string with percentage"""

    air_string: str
    """Air element string with percentage"""

    water_string: str
    """Water element string with percentage"""

    qualities_string: str
    """Qualities header string"""

    cardinal_string: str
    """Cardinal quality string with percentage"""

    fixed_string: str
    """Fixed quality string with percentage"""

    mutable_string: str
    """Mutable quality string with percentage"""

    makeLunarPhase: str
    """SVG markup for lunar phase"""
