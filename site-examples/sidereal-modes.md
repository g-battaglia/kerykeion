---
layout: ../../layouts/DocLayout.astro
title: 'Sidereal Modes'
---

# Sidereal Modes

You can use the `Sidereal` mode to calculate the data. This mode is useful
for astrologers who prefer to use the sidereal zodiac instead of the tropical zodiac.

There are different `sidereal_modes`, to read the full list check here:
[Sidereal Modes Literals](https://www.kerykeion.net/pydocs/kerykeion/schemas/kr_literals.html#SiderealMode)

Here some examples

## Lahiri Birth Chart

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

sidereal_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Lahiri", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London",
    online=False, zodiac_type="Sidereal", sidereal_mode="LAHIRI",
)
data = ChartDataFactory.create_natal_chart_data(sidereal_subject)
ChartDrawer(data).save_svg(output_path=Path("charts_output"), filename="lennon-lahiri")
```

The output will be:

![John Lennon Lahiri](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20Lahiri%20-%20Natal%20Chart.svg)

## Lahiri AstrologicalSubject

```python
from kerykeion import AstrologicalSubjectFactory

johnny = AstrologicalSubjectFactory.from_birth_data(
    "Johnny Depp", 1963, 6, 9, 0, 0,
    lng=-87.1112,
    lat=37.7719,
    tz_str="America/Chicago",
    online=False,
    zodiac_type="Sidereal", sidereal_mode="LAHIRI",
)

print(johnny.model_dump_json(indent=2))
```

The output will be:

```json
{
  "name": "Johnny Depp",
  "year": 1963,
  "month": 6,
  "day": 9,
  "hour": 0,
  "minute": 0,
  "city": "Owensboro",
  "nation": "US",
  "lng": -87.11333,
  "lat": 37.77422,
  "tz_str": "America/Chicago",
  "zodiac_type": "Sidereal",
  "sidereal_mode": "LAHIRI",
  "houses_system_identifier": "P",
  "houses_system_name": "Placidus",
  "local_time": 0.0,
  "utc_time": 5.0,
  "julian_day": 2438189.7083333335,
  "sun": {
    "name": "Sun",
    "quality": "Fixed",
    "element": "Earth",
    "sign": "Tau",
    "sign_num": 1,
    "position": 24.317935282538365,
    "abs_pos": 54.317935282538365,
    "emoji": "♉️",
    "point_type": "Planet",
    "house": "Fourth_House",
    "retrograde": false
  },
  "moon": {
    "name": "Moon",
    "quality": "Mutable",
    "element": "Fire",
    "sign": "Sag",
    "sign_num": 8,
    "position": 15.393407769812256,
    "abs_pos": 255.39340776981226,
    "emoji": "♐️",
    "point_type": "Planet",
    "house": "Eleventh_House",
    "retrograde": false
  },
  "mercury": {
    "name": "Mercury",
    "quality": "Fixed",
    "element": "Earth",
    "sign": "Tau",
    "sign_num": 1,
    "position": 1.6601115634957395,
    "abs_pos": 31.66011156349574,
    "emoji": "♉️",
    "point_type": "Planet",
    "house": "Third_House",
    "retrograde": false
  },
  "venus": {
    "name": "Venus",
    "quality": "Fixed",
    "element": "Earth",
    "sign": "Tau",
    "sign_num": 1,
    "position": 2.261987799143135,
    "abs_pos": 32.261987799143135,
    "emoji": "♉️",
    "point_type": "Planet",
    "house": "Third_House",
    "retrograde": false
  },
  "mars": {
    "name": "Mars",
    "quality": "Fixed",
    "element": "Fire",
    "sign": "Leo",
    "sign_num": 4,
    "position": 9.66990440647615,
    "abs_pos": 129.66990440647615,
    "emoji": "♌️",
    "point_type": "Planet",
    "house": "Seventh_House",
    "retrograde": false
  },
  "jupiter": {
    "name": "Jupiter",
    "quality": "Mutable",
    "element": "Water",
    "sign": "Pis",
    "sign_num": 11,
    "position": 20.5691867703203,
    "abs_pos": 350.5691867703203,
    "emoji": "♓️",
    "point_type": "Planet",
    "house": "Second_House",
    "retrograde": false
  },
  "saturn": {
    "name": "Saturn",
    "quality": "Cardinal",
    "element": "Earth",
    "sign": "Cap",
    "sign_num": 9,
    "position": 29.741745558866683,
    "abs_pos": 299.7417455588667,
    "emoji": "♑️",
    "point_type": "Planet",
    "house": "First_House",
    "retrograde": true
  },
  "uranus": {
    "name": "Uranus",
    "quality": "Fixed",
    "element": "Fire",
    "sign": "Leo",
    "sign_num": 4,
    "position": 8.224871884627646,
    "abs_pos": 128.22487188462765,
    "emoji": "♌️",
    "point_type": "Planet",
    "house": "Seventh_House",
    "retrograde": false
  },
  "neptune": {
    "name": "Neptune",
    "quality": "Cardinal",
    "element": "Air",
    "sign": "Lib",
    "sign_num": 6,
    "position": 20.081715978211292,
    "abs_pos": 200.0817159782113,
    "emoji": "♎️",
    "point_type": "Planet",
    "house": "Ninth_House",
    "retrograde": true
  },
  "pluto": {
    "name": "Pluto",
    "quality": "Fixed",
    "element": "Fire",
    "sign": "Leo",
    "sign_num": 4,
    "position": 16.283875920811937,
    "abs_pos": 136.28387592081194,
    "emoji": "♌️",
    "point_type": "Planet",
    "house": "Seventh_House",
    "retrograde": false
  },
  "chiron": {
    "name": "Chiron",
    "quality": "Fixed",
    "element": "Air",
    "sign": "Aqu",
    "sign_num": 10,
    "position": 21.532200152946757,
    "abs_pos": 321.53220015294676,
    "emoji": "♒️",
    "point_type": "Planet",
    "house": "First_House",
    "retrograde": false
  },
  "first_house": {
    "name": "First_House",
    "quality": "Cardinal",
    "element": "Earth",
    "sign": "Cap",
    "sign_num": 9,
    "position": 27.35490680258141,
    "abs_pos": 297.3549068025814,
    "emoji": "♑️",
    "point_type": "House"
  },
  "second_house": {
    "name": "Second_House",
    "quality": "Mutable",
    "element": "Water",
    "sign": "Pis",
    "sign_num": 11,
    "position": 13.30148162599977,
    "abs_pos": 343.30148162599977,
    "emoji": "♓️",
    "point_type": "House"
  },
  "third_house": {
    "name": "Third_House",
    "quality": "Cardinal",
    "element": "Fire",
    "sign": "Ari",
    "sign_num": 0,
    "position": 17.873648488471723,
    "abs_pos": 17.873648488471723,
    "emoji": "♈️",
    "point_type": "House"
  },
  "fourth_house": {
    "name": "Fourth_House",
    "quality": "Fixed",
    "element": "Earth",
    "sign": "Tau",
    "sign_num": 1,
    "position": 13.245983424363494,
    "abs_pos": 43.245983424363494,
    "emoji": "♉️",
    "point_type": "House"
  },
  "fifth_house": {
    "name": "Fifth_House",
    "quality": "Mutable",
    "element": "Air",
    "sign": "Gem",
    "sign_num": 2,
    "position": 5.000428496260554,
    "abs_pos": 65.00042849626055,
    "emoji": "♊️",
    "point_type": "House"
  },
  "sixth_house": {
    "name": "Sixth_House",
    "quality": "Mutable",
    "element": "Air",
    "sign": "Gem",
    "sign_num": 2,
    "position": 27.64896604114807,
    "abs_pos": 87.64896604114807,
    "emoji": "♊️",
    "point_type": "House"
  },
  "seventh_house": {
    "name": "Seventh_House",
    "quality": "Cardinal",
    "element": "Water",
    "sign": "Can",
    "sign_num": 3,
    "position": 27.35490680258141,
    "abs_pos": 117.35490680258141,
    "emoji": "♋️",
    "point_type": "House"
  },
  "eighth_house": {
    "name": "Eighth_House",
    "quality": "Mutable",
    "element": "Earth",
    "sign": "Vir",
    "sign_num": 5,
    "position": 13.30148162599977,
    "abs_pos": 163.30148162599977,
    "emoji": "♍️",
    "point_type": "House"
  },
  "ninth_house": {
    "name": "Ninth_House",
    "quality": "Cardinal",
    "element": "Air",
    "sign": "Lib",
    "sign_num": 6,
    "position": 17.8736484884717,
    "abs_pos": 197.8736484884717,
    "emoji": "♎️",
    "point_type": "House"
  },
  "tenth_house": {
    "name": "Tenth_House",
    "quality": "Fixed",
    "element": "Water",
    "sign": "Sco",
    "sign_num": 7,
    "position": 13.245983424363487,
    "abs_pos": 223.2459834243635,
    "emoji": "♏️",
    "point_type": "House"
  },
  "eleventh_house": {
    "name": "Eleventh_House",
    "quality": "Mutable",
    "element": "Fire",
    "sign": "Sag",
    "sign_num": 8,
    "position": 5.000428496260554,
    "abs_pos": 245.00042849626055,
    "emoji": "♐️",
    "point_type": "House"
  },
  "twelfth_house": {
    "name": "Twelfth_House",
    "quality": "Mutable",
    "element": "Fire",
    "sign": "Sag",
    "sign_num": 8,
    "position": 27.64896604114807,
    "abs_pos": 267.64896604114807,
    "emoji": "♐️",
    "point_type": "House"
  },
  "mean_node": {
    "name": "Mean_Node",
    "quality": "Mutable",
    "element": "Air",
    "sign": "Gem",
    "sign_num": 2,
    "position": 28.911462076788297,
    "abs_pos": 88.9114620767883,
    "emoji": "♊️",
    "point_type": "Planet",
    "house": "Sixth_House",
    "retrograde": true
  },
  "true_node": {
    "name": "True_Node",
    "quality": "Mutable",
    "element": "Air",
    "sign": "Gem",
    "sign_num": 2,
    "position": 27.29795396305248,
    "abs_pos": 87.29795396305248,
    "emoji": "♊️",
    "point_type": "Planet",
    "house": "Fifth_House",
    "retrograde": true
  },
  "lunar_phase": {
    "degrees_between_s_m": 201.07547248727388,
    "moon_phase": 16,
    "sun_phase": 15,
    "moon_emoji": "🌖",
    "moon_phase_name": "Waning Gibbous"
  }
}
❯
```
