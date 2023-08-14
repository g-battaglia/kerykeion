# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2023 Giacomo Battaglia

    Kerykeion is a python library for Astrology.
    It can calculate all the planet and house position,
    also it can calculate the aspects of a single persone or between two, you can set how many planets you
    need in the settings in the utility module.
    It also can generate an SVG of a birthchart, a synastry chart or a transit chart.

    Here some examples:

    ```python

    # Import the main class for creating a kerykeion instance:
    >>> from kerykeion import AstrologicalSubject

    # Create a kerykeion instance:
    # Args: Name, year, month, day, hour, minuts, city, nation(optional)
    >>> kanye = AstrologicalSubject("Kanye", 1977, 6, 8, 8, 45, "Atlanta")

    # Get the information about the sun in the chart:
    # (The position of the planets always starts at 0)
    >>> kanye.sun
    {'name': 'Sun', 'quality': 'Mutable', 'element': 'Air', 'sign': 'Gem', 'sign_num': 2, 'pos': 17.598992059774275, 'abs_pos': 77.59899205977428, 'emoji': '♊️', 'house': '12th House', 'retrograde': False}

    # Get informations about the first house:
    >>> kanye.first_house
    {'name': '1', 'quality': 'Cardinal', 'element': 'Water', 'sign': 'Can', 'sign_num': 3, 'pos': 17.995779673209114, 'abs_pos': 107.99577967320911, 'emoji': '♋️'}

    # Get element of the moon sign:
    >>> kanye.moon.get("element")
    'Water'

    ```

    ## Generate a SVG of the birthchart:

    ```python
    >>> from kerykeion import AstrologicalSubject, KerykeionChartSVG

    >>> first = AstrologicalSubject("Jack", 1990, 6, 15, 15, 15, "Roma")
    >>> second = AstrologicalSubject("Jane", 1991, 10, 25, 21, 00, "Roma")

    # Set the type, it can be Natal, Synastry or Transit

    >>> name = KerykeionChartSVG(first, chart_type="Synastry", second_obj=second)
    >>> name.makeSVG()
    >>> print(len(name.aspects_list))
    >>> Generating kerykeion object for Jack...
    Generating kerykeion object for Jane...
    Jack birth location: Roma, 41.89193, 12.51133
    SVG Generated Correctly
    38

    ```

    ![alt text](http://centuryboy.altervista.org/JackSynastry_Chart.svg)


    ## Other exeples of possibles usecase

    ```python
    # Get all aspects between two persons:

    >>> from kerykeion import SynastryAspects, AstrologicalSubject
    >>> first = AstrologicalSubject("Jack", 1990, 6, 15, 15, 15, "Roma")
    >>> second = AstrologicalSubject("Jane", 1991, 10, 25, 21, 00, "Roma")

    >>> name = SynastryAspects(first, second)
    >>> aspect_list = name.get_relevant_aspects()
    >>> print(aspect_list[0])

    Generating kerykeion object for Jack...
    Generating kerykeion object for Jane...
    {'p1_name': 'Sun', 'p1_abs_pos': 84.17867971515636, 'p2_name': 'Sun', 'p2_abs_pos': 211.90472999502984, 'aspect': 'trine', 'orbit': 7.726050279873476, 'aspect_degrees': 120, 'color': '#36d100', 'aid': 6, 'diff': 127.72605027987348, 'p1': 0, 'p2': 0}

    ```

    ## Documentation

    Most of the functions and the classes are self documented by the types and have docstrings.
    An auto-generated documentation [is available here](https://g-battaglia.github.io/kerykeion).

    Sooner or later I'll try to write an extensive documentation.

    ## Installation

    Kerykeion is a Python 3 package, make sure you have Python 3 installed on your system.

    ## Development

    You can clone this repository or download a zip file using the right side buttons.

    ## Contributing

    Feel free to contribute to the code!

"""

# Local
from .astrological_subject import AstrologicalSubject
from .charts.kerykeion_chart_svg import KerykeionChartSVG
from .kr_types import *
from .relationship_score import RelationshipScore
from .aspects import SynastryAspects, NatalAspects
from .report import Report
from .settings import KerykeionSettingsModel, get_settings_dict
