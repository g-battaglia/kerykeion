# Kerykeion

Kerykeion is a python utility library for Astrology.


```python

# Import the main class for creating a kerykeion instance:
>>> from kerykeion.astrocore import Calculator

# Create a kerykeion instance:
>>> kanye = Calculator("Kanye", 1977, 6, 8, 8, 45, "Atlanta")

# Get all the data:
>>> kanye.get_all()

# Get the information about the sun in the chart:
# (The position of the planets always starts at 0)
>>> kanye.sun
{'name': 'Sun', 'quality': 'Mutable', 'element': 'Air', 'sign': 'Gem', 'sign_num': 2, 'pos': 17.598992059774275, 'abs_pos': 77.59899205977428, 'emoji': '♊️', 'house': '12th House', 'retrograde': False}

# Get informations about the first house:
>>> kanye.fir_house
{'name': '1', 'quality': 'Cardinal', 'element': 'Water', 'sign': 'Can', 'sign_num': 3, 'pos': 17.995779673209114, 'abs_pos': 107.99577967320911, 'emoji': '♋️'}



# Example of a possible text output with information:

>>> from kerykeion.output import output

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


>>> print(kanye.houses()[3]) # Print the house information.
{'name': '4', 'quality': 'Cardinal', 'element': 'Air', 'sign': 'Lib', 'pos': 3.9766709280539203, 'abs_pos': 183.97667092805392, 'emoji': '♎️'}


>>> print(kanye.planets_house()[0]) # Print the planet information.
{'name': 'Sun', 'quality': 'Mutable', 'element': 'Air', 'sign': 'Gem', 'pos': 17.598990175203994, 'abs_pos': 77.598990175204, 'emoji': '♊️', 'house': '12th House'}

>>> print(kanye.aspects()['all']['Sun']) # Print aspects for the planet.
["('Square', 'Moon', 1.1735227310748542)", "('Semisquare', 'Venus', 0.5668097396966303)", "('Semisquare', 'Mars', 0.8092756679079827)", "('Conjuction', 'Jupiter', 2.992099853982751)", "('Oposition', 'Neptune', -2.906233250740513)", "('Trigon', 'Pluto', -6.153155598911468)", "('Conjuction', 'Juno', 0.0)", "('Semisextil', '1', 0.39678949800406826)", "('Oposition', '6', -1.917784119528534)", "('Quincunx', '7', -0.39678949800406826)", "('Conjuction', '12', 1.917784119528534)"]


```

## Documentation

Soon available.


## Installation

Kerykeion is a Python 3 package, make sure you have Python 3 installed on your system. 


## Development

You can clone this repository or download a zip file using the right side buttons. 
