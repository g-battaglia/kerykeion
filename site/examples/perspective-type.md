---
layout: ../../layouts/DocLayout.astro
title: 'Perspective Type'
---

# Perspective Type

The `PerspectiveType` class is used to define the perspective of the chart.

Full list of `PerspectiveType` literals can be found here:
https://www.kerykeion.net/pydocs/kerykeion/schemas/kr_literals.html#PerspectiveType

## Heliocentric Birth Chart

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Heliocentric", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London",
    online=False, perspective_type="Heliocentric",
)
data = ChartDataFactory.create_natal_chart_data(subject)
chart = ChartDrawer(data)
chart.save_svg(output_path=Path("charts_output"), filename="lennon-heliocentric")
```

The output will be:

![John Lennon Heliocentric](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20-%20Heliocentric%20-%20Natal%20Chart.svg)

## Helio AstrologicalSubject

```python
from kerykeion import AstrologicalSubjectFactory

johnny = AstrologicalSubjectFactory.from_birth_data(
    "Johnny Depp", 1963, 6, 9, 0, 0,
    lng=-87.1112,
    lat=37.7719,
    tz_str="America/Chicago",
    online=False,
    perspective_type="Heliocentric",
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
    "zodiac_type": "Tropic",
    "houses_system_identifier": "P",
    "houses_system_name": "Placidus",
    "perspective_type": "Heliocentric",
    "iso_formatted_local_datetime": "1963-06-09T00:00:00-05:00",
    "iso_formatted_utc_datetime": "1963-06-09T05:00:00+00:00",
    "julian_day": 2438189.7083333335,
    "sun": {
        "name": "Sun",
        "quality": "Cardinal",
        "element": "Fire",
        "sign": "Ari",
        "sign_num": 0,
        "position": 0.0,
        "abs_pos": 0.0,
        "emoji": "♈️",
        "point_type": "Planet",
        "house": "First_House",
        "retrograde": false
    },
    "moon": {
        "name": "Moon",
        "quality": "Mutable",
        "element": "Fire",
        "sign": "Sag",
        "sign_num": 8,
        "position": 17.71293280048576,
        "abs_pos": 257.71293280048576,
        "emoji": "♐️",
        "point_type": "Planet",
        "house": "Tenth_House",
        "retrograde": false
    },
    "mercury": {
        "name": "Mercury",
        "quality": "Cardinal",
        "element": "Earth",
        "sign": "Cap",
        "sign_num": 9,
        "position": 29.31965968245555,
        "abs_pos": 299.31965968245555,
        "emoji": "♑️",
        "point_type": "Planet",
        "house": "Twelfth_House",
        "retrograde": false
    },
    "venus": {
        "name": "Venus",
        "quality": "Cardinal",
        "element": "Fire",
        "sign": "Ari",
        "sign_num": 0,
        "position": 23.843575319691585,
        "abs_pos": 23.843575319691585,
        "emoji": "♈️",
        "point_type": "Planet",
        "house": "Second_House",
        "retrograde": false
    },
    "mars": {
        "name": "Mars",
        "quality": "Cardinal",
        "element": "Air",
        "sign": "Lib",
        "sign_num": 6,
        "position": 9.908686490882815,
        "abs_pos": 189.90868649088281,
        "emoji": "♎️",
        "point_type": "Planet",
        "house": "Eighth_House",
        "retrograde": false
    },
    "jupiter": {
        "name": "Jupiter",
        "quality": "Cardinal",
        "element": "Fire",
        "sign": "Ari",
        "sign_num": 0,
        "position": 3.3225824822577104,
        "abs_pos": 3.3225824822577104,
        "emoji": "♈️",
        "point_type": "Planet",
        "house": "First_House",
        "retrograde": false
    },
    "saturn": {
        "name": "Saturn",
        "quality": "Fixed",
        "element": "Air",
        "sign": "Aqu",
        "sign_num": 10,
        "position": 17.726400222248685,
        "abs_pos": 317.7264002222487,
        "emoji": "♒️",
        "point_type": "Planet",
        "house": "Twelfth_House",
        "retrograde": false
    },
    "uranus": {
        "name": "Uranus",
        "quality": "Mutable",
        "element": "Earth",
        "sign": "Vir",
        "sign_num": 5,
        "position": 4.621984499731468,
        "abs_pos": 154.62198449973147,
        "emoji": "♍️",
        "point_type": "Planet",
        "house": "Seventh_House",
        "retrograde": false
    },
    "neptune": {
        "name": "Neptune",
        "quality": "Fixed",
        "element": "Water",
        "sign": "Sco",
        "sign_num": 7,
        "position": 14.498716498461278,
        "abs_pos": 224.49871649846128,
        "emoji": "♏️",
        "point_type": "Planet",
        "house": "Ninth_House",
        "retrograde": false
    },
    "pluto": {
        "name": "Pluto",
        "quality": "Mutable",
        "element": "Earth",
        "sign": "Vir",
        "sign_num": 5,
        "position": 11.420394744365211,
        "abs_pos": 161.4203947443652,
        "emoji": "♍️",
        "point_type": "Planet",
        "house": "Seventh_House",
        "retrograde": false
    },
    "chiron": {
        "name": "Chiron",
        "quality": "Mutable",
        "element": "Water",
        "sign": "Pis",
        "sign_num": 11,
        "position": 11.572185162993549,
        "abs_pos": 341.57218516299355,
        "emoji": "♓️",
        "point_type": "Planet",
        "house": "First_House",
        "retrograde": false
    },
    "first_house": {
        "name": "First_House",
        "quality": "Fixed",
        "element": "Air",
        "sign": "Aqu",
        "sign_num": 10,
        "position": 20.696672272096748,
        "abs_pos": 320.69667227209675,
        "emoji": "♒️",
        "point_type": "House"
    },
    "second_house": {
        "name": "Second_House",
        "quality": "Cardinal",
        "element": "Fire",
        "sign": "Ari",
        "sign_num": 0,
        "position": 6.643247095515116,
        "abs_pos": 6.643247095515116,
        "emoji": "♈️",
        "point_type": "House"
    },
    "third_house": {
        "name": "Third_House",
        "quality": "Fixed",
        "element": "Earth",
        "sign": "Tau",
        "sign_num": 1,
        "position": 11.215413957987053,
        "abs_pos": 41.21541395798705,
        "emoji": "♉️",
        "point_type": "House"
    },
    "fourth_house": {
        "name": "Fourth_House",
        "quality": "Mutable",
        "element": "Air",
        "sign": "Gem",
        "sign_num": 2,
        "position": 6.587748893878825,
        "abs_pos": 66.58774889387882,
        "emoji": "♊️",
        "point_type": "House"
    },
    "fifth_house": {
        "name": "Fifth_House",
        "quality": "Mutable",
        "element": "Air",
        "sign": "Gem",
        "sign_num": 2,
        "position": 28.34219396577589,
        "abs_pos": 88.34219396577589,
        "emoji": "♊️",
        "point_type": "House"
    },
    "sixth_house": {
        "name": "Sixth_House",
        "quality": "Cardinal",
        "element": "Water",
        "sign": "Can",
        "sign_num": 3,
        "position": 20.99073151066341,
        "abs_pos": 110.99073151066341,
        "emoji": "♋️",
        "point_type": "House"
    },
    "seventh_house": {
        "name": "Seventh_House",
        "quality": "Fixed",
        "element": "Fire",
        "sign": "Leo",
        "sign_num": 4,
        "position": 20.696672272096748,
        "abs_pos": 140.69667227209675,
        "emoji": "♌️",
        "point_type": "House"
    },
    "eighth_house": {
        "name": "Eighth_House",
        "quality": "Cardinal",
        "element": "Air",
        "sign": "Lib",
        "sign_num": 6,
        "position": 6.6432470955151075,
        "abs_pos": 186.6432470955151,
        "emoji": "♎️",
        "point_type": "House"
    },
    "ninth_house": {
        "name": "Ninth_House",
        "quality": "Fixed",
        "element": "Water",
        "sign": "Sco",
        "sign_num": 7,
        "position": 11.215413957987039,
        "abs_pos": 221.21541395798704,
        "emoji": "♏️",
        "point_type": "House"
    },
    "tenth_house": {
        "name": "Tenth_House",
        "quality": "Mutable",
        "element": "Fire",
        "sign": "Sag",
        "sign_num": 8,
        "position": 6.587748893878825,
        "abs_pos": 246.58774889387882,
        "emoji": "♐️",
        "point_type": "House"
    },
    "eleventh_house": {
        "name": "Eleventh_House",
        "quality": "Mutable",
        "element": "Fire",
        "sign": "Sag",
        "sign_num": 8,
        "position": 28.34219396577589,
        "abs_pos": 268.3421939657759,
        "emoji": "♐️",
        "point_type": "House"
    },
    "twelfth_house": {
        "name": "Twelfth_House",
        "quality": "Cardinal",
        "element": "Earth",
        "sign": "Cap",
        "sign_num": 9,
        "position": 20.99073151066341,
        "abs_pos": 290.9907315106634,
        "emoji": "♑️",
        "point_type": "House"
    },
    "mean_node": {
        "name": "Mean_Node",
        "quality": "Cardinal",
        "element": "Fire",
        "sign": "Ari",
        "sign_num": 0,
        "position": 0.0,
        "abs_pos": 0.0,
        "emoji": "♈️",
        "point_type": "Planet",
        "house": "First_House",
        "retrograde": false
    },
    "true_node": {
        "name": "True_Node",
        "quality": "Cardinal",
        "element": "Fire",
        "sign": "Ari",
        "sign_num": 0,
        "position": 0.0,
        "abs_pos": 0.0,
        "emoji": "♈️",
        "point_type": "Planet",
        "house": "First_House",
        "retrograde": false
    },
    "lunar_phase": {
        "degrees_between_s_m": 257.71293280048576,
        "moon_phase": 21,
        "sun_phase": 20,
        "moon_emoji": "🌗",
        "moon_phase_name": "Last Quarter"
    }
}
```
