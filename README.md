<div align="center">
    <img src="https://img.shields.io/badge/Python-3.9-FF1493.svg" alt="python version">
    <img src="https://img.shields.io/github/contributors/g-battaglia/kerykeion?color=blue&logo=github" alt="contributors">
    <img src="https://img.shields.io/github/stars/g-battaglia/kerykeion.svg?logo=github" alt="stars">
    <img src="https://img.shields.io/github/forks/g-battaglia/kerykeion.svg?logo=github" alt="forks">
    <img src="https://visitor-badge.laobi.icu/badge?page_id=g-battaglia.kerykeion" alt="visitors"/>
</div>

# Kerykeion

Kerykeion is a python library for Astrology.
It can calculate all the planet and house position,
also it can calculate the aspects of a single persone or between two, you can set how many planets you
need in the settings in the utility module.
It also can generate an SVG of a birthchart, a composite chart or a transit chart.

Here some examples:

```python

# Import the main class for creating a kerykeion instance:
>>> from kerykeion import KrInstance

# Create a kerykeion instance:
# Args: Name, year, month, day, hour, minuts, city, nation(optional)
>>> kanye = KrInstance("Kanye", 1977, 6, 8, 8, 45, "Atlanta")

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

```
>>> import kerykeion as kr
>>> from kerykeion.utilities.charts import MakeSvgInstance

>>> first = kr.KrInstance("Jack", 1990, 6, 15, 15, 15, "Roma")
>>> second = kr.KrInstance("Jane", 1991, 10, 25, 21, 00, "Roma")

# Set the type, it can be Natal, Composite or Transit

>>> name = MakeSvgInstance(first, chart_type="Composite", second_obj=second)
>>> name.makeSVG()
>>> print(len(name.aspects_list))
>>> Generating kerykeion object for Jack...
Generating kerykeion object for Jane...
Jack birth location: Roma, 41.89193, 12.51133
SVG Generated Correctly
38

```

![alt text](http://centuryboy.altervista.org/JackComposite_Chart.svg)

# Example of a possible text output with information:

```


>>> from kerykeion import output, KrInstance

>>> kanye = KrInstance("Kanye", 1977, 6, 8, 8, 45, "Atlanta")

>>> print(output(kanye))
-----------------------------------------------------
NAME: Kanye
PLANET     POSITION

Sun:       Gem 17.599 in 12th House
Moon:      Pis 16.425 in 9th House
Mercury:   Tau 26.286 in 11th House
Venus:     Tau 2.032 in 10th House
Mars:      Tau 1.79 in 10th House
Jupiter:   Gem 14.607 in 11th House
Saturn:    Leo 12.799 in 2nd House
Uranus:    Sco 8.273 in 4th House
Neptune:   Sag 14.693 in 5th House
Pluto:     Lib 11.446 in 4th House

PLACIDUS HAUSES
House Cusp 1:     Can  17.996
House Cusp 2:     Leo  9.506
House Cusp 3:     Vir  4.022
House Cusp 4:     Lib  3.977
House Cusp 5:     Sco  9.393
House Cusp 6:     Sag  15.681
House Cusp 7:     Cap  17.996
House Cusp 8:     Aqu  9.506
House Cusp 9:     Pis  4.022
House Cusp 10:    Ari  3.977
House Cusp 11:    Tau  9.393
House Cusp 12:    Gem  15.681

```

## Other exeples of possibles usecase

```


>>> print(kanye.houses()[3]) # Print the house information.
{'name': '4', 'quality': 'Cardinal', 'element': 'Air', 'sign': 'Lib', 'pos': 3.9766709280539203, 'abs_pos': 183.97667092805392, 'emoji': '♎️'}


>>> print(kanye.planets_house()[0]) # Print the planet information.
{'name': 'Sun', 'quality': 'Mutable', 'element': 'Air', 'sign': 'Gem', 'pos': 17.598990175203994, 'abs_pos': 77.598990175204, 'emoji': '♊️', 'house': '12th House'}

>>> print(kanye.aspects()['all']['Sun']) # Print aspects for the planet.
["('Square', 'Moon', 1.1735227310748542)", "('Semisquare', 'Venus', 0.5668097396966303)", "('Semisquare', 'Mars', 0.8092756679079827)", "('Conjuction', 'Jupiter', 2.992099853982751)", "('Oposition', 'Neptune', -2.906233250740513)", "('Trigon', 'Pluto', -6.153155598911468)", "('Conjuction', 'Juno', 0.0)", "('Semisextil', '1', 0.39678949800406826)", "('Oposition', '6', -1.917784119528534)", "('Quincunx', '7', -0.39678949800406826)", "('Conjuction', '12', 1.917784119528534)"]

# Get all aspects between two persons:

>>> import kerykeion as kr
>>> from kerykeion.utilities import CompositeAspects
>>> first = kr.KrInstance("Jack", 1990, 6, 15, 15, 15, "Roma")
>>> second = kr.KrInstance("Jane", 1991, 10, 25, 21, 00, "Roma")

>>> name = CompositeAspects(first, second)
>>> aspect_list = name.get_aspects()
>>> print(aspect_list[0])

Generating kerykeion object for Jack...
Generating kerykeion object for Jane...
{'p1_name': 'Sun', 'p1_abs_pos': 84.17867971515636, 'p2_name': 'Sun', 'p2_abs_pos': 211.90472999502984, 'aspect': 'trine', 'orbit': 7.726050279873476, 'aspect_degrees': 120, 'color': '#36d100', 'aid': 6, 'diff': 127.72605027987348, 'p1': 0, 'p2': 0}

```

## Documentation

Most of the functions and the classes are self documented by the types and have docstrings.
An auto-generated documentation is available in the docs folder.
Sooner or later I'll try to write an extensive documentation.

## Installation

Kerykeion is a Python 3 package, make sure you have Python 3 installed on your system.

## Development

You can clone this repository or download a zip file using the right side buttons.

## Contributing

Feel free to contribute to the code!
