<h1 align=center>Kerykeion</h1>
<div align="center">
    <a href="#">
        <img src="https://img.shields.io/github/contributors/g-battaglia/kerykeion?color=blue&logo=github" alt="contributors">
    </a>
    <a href="#">
        <img src="https://img.shields.io/github/stars/g-battaglia/kerykeion.svg?logo=github" alt="stars">
    </a>
    <a href="#">
        <img src="https://img.shields.io/github/forks/g-battaglia/kerykeion.svg?logo=github" alt="forks">
    </a>
    <a href="https://pypi.org/project/kerykeion" target="_blank">
        <img src="https://visitor-badge.laobi.icu/badge?page_id=g-battaglia.kerykeion" alt="visitors"/>
    </a>
    <a href="https://pypi.org/project/kerykeion" target="_blank">
        <img src="https://img.shields.io/pypi/v/kerykeion?label=pypi%20package" alt="Package version">
    </a>
    <a href="https://pypi.org/project/kerykeion" target="_blank">
        <img src="https://img.shields.io/pypi/pyversions/kerykeion.svg" alt="Supported Python versions">
    </a>
</div>

&nbsp;

Kerykeion is a python library for Astrology.
It can calculate all the planet and house position,
also it can calculate the aspects of a single persone or between two, you can set how many planets you
need in the settings in the utility module.
It also can generate an SVG of a birthchart, a synastry chart or a transit chart.

The core goal of this project is to provide a simple and easy approach to astrology in a data driven way.

Here's an example of a birthchart:

![Kanye Birth Chart](https://www.kerykeion.net/docs/assets/img/examples/birth-chart.svg)

## Web API

If you want to use Kerykeion in a web application, I've created a web API for this purpose, you can find it here:

**[AstrologerAPI](https://rapidapi.com/gbattaglia/api/astrologer/pricing)**

It's [open source](https://github.com/g-battaglia/Astrologer-API), it's a way to support me and the project.

## Donate

Maintaining this project is a lot of work, the Astrologer API doesn't nearly cover the costs of a software engineer working on this project full time. I do this because I love it, but until I can make this my full time job, I won't be able to spend as much time on it.

If you want to support me, you can do it here:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/kerykeion)

## Installation

Kerykeion is a _Python 3.9_ package, make sure you have _Python 3.9_ or above installed on your system.

```bash
pip3 install kerykeion
```

## Basic Usage

The basic usage of the library is to create an instance of the AstrologicalSubject class and then access the properties of the instance to get the astrological information about the subject.

Here's an example:

```python

# Import the main class for creating a kerykeion instance:
from kerykeion import AstrologicalSubject

# Create a kerykeion instance:
# Args: Name, year, month, day, hour, minuts, city, nation
kanye = AstrologicalSubject("Kanye", 1977, 6, 8, 8, 45, "Atlanta", "US")

# Get the information about the sun in the chart:
# (The position of the planets always starts at 0)
kanye.sun

#> {'name': 'Sun', 'quality': 'Mutable', 'element': 'Air', 'sign': 'Gem', 'sign_num': 2, 'pos': 17.598992059774275, 'abs_pos': 77.59899205977428, 'emoji': '♊️', 'house': '12th House', 'retrograde': False}

# Get information about the first house:
kanye.first_house

#> {'name': 'First_House', 'quality': 'Cardinal', 'element': 'Water', 'sign': 'Can', 'sign_num': 3, 'pos': 17.995779673209114, 'abs_pos': 107.99577967320911, 'emoji': '♋️'}

# Get element of the moon sign:
kanye.moon.element

#> 'Water'

```

**To avoid connecting to GeoNames (eg. avoiding hourly limit or no internet connection) you should instance kerykeion like this:**

```python
kanye = AstrologicalSubject(
    "Kanye", 1977, 6, 8, 8, 45, lng=50, lat=50, tz_str="Europe/Rome", city="Rome"
)
```

The difference is that you have to pass the longitude, latitude and the timezone string, instead of the city and nation.
If you omit the nation, it will be set to "GB" by default, but the value is not used for calculations. It's better to set it to the correct value though.

## Generate a SVG Chart

### Birth Chart

```python
from kerykeion import AstrologicalSubject, KerykeionChartSVG


birth_chart = AstrologicalSubject("Kanye", 1977, 6, 8, 8, 45, "Atlanta", "US")
birth_chart_svg = KerykeionChartSVG(birth_chart)

birth_chart_svg.makeSVG()
```

The SVG file will be saved in the home directory.
![John Lennon Birth Chart](https://www.kerykeion.net/docs/assets/img/examples/birth-chart.svg)

### Synastry Chart

```python
from kerykeion import AstrologicalSubject, KerykeionChartSVG

first = AstrologicalSubject("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")
second = AstrologicalSubject("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

# Set the type, it can be Natal, Synastry or Transit
synastry_chart = KerykeionChartSVG(first, "Synastry", second)
synastry_chart.makeSVG()

```

![John Lennon and Paul McCartney Synastry](https://www.kerykeion.net/docs/assets/img/examples/synastry-chart.svg)

### Change the output directory

By default the output directory is the home directory, you can change it by passing the new_output_directory parameter to the KerykeionChartSVG class:

```python
from kerykeion import AstrologicalSubject, KerykeionChartSVG

first = AstrologicalSubject("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")
second = AstrologicalSubject("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

# Set the output directory to the current directory
synastry_chart = KerykeionChartSVG(first, "Synastry", second, new_output_directory=".")
synastry_chart.makeSVG()
```

### Change Language

You can change the language of the SVG by passing the `chart_language` parameter to the KerykeionChartSVG class:

```python
first = AstrologicalSubject("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB", chart_language="ES")
```
More details [here](https://www.kerykeion.net/docs/examples/chart-language).

## Report

To print a report of all the data:

```python
from kerykeion import Report, AstrologicalSubject

kanye = AstrologicalSubject("Kanye", 1977, 6, 8, 8, 45, "Atlanta", "US")
report = Report(kanye)
report.print_report()

```

Returns:

```txt
+- Kerykeion report for Kanye -+
+----------+------+-------------+-----------+----------+
| Date     | Time | Location    | Longitude | Latitude |
+----------+------+-------------+-----------+----------+
| 8/6/1977 | 8:45 | Atlanta, US | -84.38798 | 33.749   |
+----------+------+-------------+-----------+----------+
+-----------------+------+-------+------+----------------+
| Planet          | Sign | Pos.  | Ret. | House          |
+-----------------+------+-------+------+----------------+
| Sun             | Gem  | 17.6  | -    | Twelfth_House  |
| Moon            | Pis  | 16.43 | -    | Ninth_House    |
| Mercury         | Tau  | 26.29 | -    | Eleventh_House |
| Venus           | Tau  | 2.03  | -    | Tenth_House    |
| Mars            | Tau  | 1.79  | -    | Tenth_House    |
| Jupiter         | Gem  | 14.61 | -    | Eleventh_House |
| Saturn          | Leo  | 12.8  | -    | Second_House   |
| Uranus          | Sco  | 8.27  | R    | Fourth_House   |
| Neptune         | Sag  | 14.69 | R    | Fifth_House    |
| Pluto           | Lib  | 11.45 | R    | Fourth_House   |
| Mean_Node       | Lib  | 21.49 | R    | Fourth_House   |
| True_Node       | Lib  | 22.82 | R    | Fourth_House   |
| Mean_South_Node | Ari  | 21.49 | R    | Tenth_House    |
| True_South_Node | Ari  | 22.82 | R    | Tenth_House    |
| Chiron          | Tau  | 4.17  | -    | Tenth_House    |
+-----------------+------+-------+------+----------------+
+----------------+------+----------+
| House          | Sign | Position |
+----------------+------+----------+
| First_House    | Can  | 18.0     |
| Second_House   | Leo  | 9.51     |
| Third_House    | Vir  | 4.02     |
| Fourth_House   | Lib  | 3.98     |
| Fifth_House    | Sco  | 9.39     |
| Sixth_House    | Sag  | 15.68    |
| Seventh_House  | Cap  | 18.0     |
| Eighth_House   | Aqu  | 9.51     |
| Ninth_House    | Pis  | 4.02     |
| Tenth_House    | Ari  | 3.98     |
| Eleventh_House | Tau  | 9.39     |
| Twelfth_House  | Gem  | 15.68    |
+----------------+------+----------+

```

And if you want to export it to a file:

```bash
python3 your_script_name.py > file.txt
```

## Other examples of possible use cases:

```python
# Get all aspects between two persons:

from kerykeion import SynastryAspects, AstrologicalSubject
first = AstrologicalSubject("Jack", 1990, 6, 15, 15, 15, "Roma", "IT")
second = AstrologicalSubject("Jane", 1991, 10, 25, 21, 00, "Roma", "IT")

name = SynastryAspects(first, second)
aspect_list = name.get_relevant_aspects()
print(aspect_list[0])

#> Generating kerykeion object for Jack...
#> Generating kerykeion object for Jane...
#> {'p1_name': 'Sun', 'p1_abs_pos': 84.17867971515636, 'p2_name': 'Sun', 'p2_abs_pos': 211.90472999502984, 'aspect': 'trine', 'orbit': 7.726050279873476, 'aspect_degrees': 120, 'color': '#36d100', 'aid': 6, 'diff': 127.72605027987348, 'p1': 0, 'p2': 0}

```

## Ayanamsa (Sidereal Modes)

By default, the zodiac type is set to Tropic (Tropical).
You can set the zodiac type to Sidereal and the sidereal mode in the AstrologicalSubject class:

```python
johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", zodiac_type="Sidereal", sidereal_mode="LAHIRI")
```

More examples [here](https://www.kerykeion.net/docs/examples/sidereal-modes/).

Full list of supported sidereal modes [here](https://www.kerykeion.net/pydocs/kerykeion/kr_types/kr_literals.html#SiderealMode).

## Houses Systems

By default, the houses system is set to Placidus.
You can set the houses system in the AstrologicalSubject class:

```python
johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", houses_system="M")
```

More examples [here](https://www.kerykeion.net/docs/examples/houses-systems/).

Full list of supported house systems [here](https://www.kerykeion.net/pydocs/kerykeion/kr_types/kr_literals.html#HousesSystem).

So far all the available houses system in the Swiss Ephemeris are supported but the Gauquelin Sectors.

## Perspective Type

By default, the perspective type is set to Apparent Geocentric (the most common standard for astrology).
The perspective indicates the point of view from which the chart is calculated (Es. Apparent Geocentric, Heliocentric, etc.).
You can set the perspective type in the AstrologicalSubject class:

```python
johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", perspective_type="Heliocentric")
```

More examples [here](https://www.kerykeion.net/docs/examples/perspective-type/).

Full list of supported perspective types [here](https://www.kerykeion.net/pydocs/kerykeion/kr_types/kr_literals.html#PerspectiveType).

## Themes

You can now personalize your astrological charts with different themes! Four themes are available:

- **Classic** (default)
- **Dark**
- **Dark High Contrast**
- **Light**

Each theme offers a distinct visual style, allowing you to choose the one that best suits your preferences or presentation needs. If you prefer more control over the appearance, you can opt not to set any theme, making it easier to customize the chart by overriding the default CSS variables. For more detailed instructions on how to apply themes, check the [documentation](https://www.kerykeion.net/docs/examples/theming)

Here's an example of how to set the theme:

```python
from kerykeion import AstrologicalSubject, KerykeionChartSVG

dark_theme_subject = AstrologicalSubject("John Lennon - Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB")
dark_theme_natal_chart = KerykeionChartSVG(dark_high_contrast_theme_subject, theme="dark_high_contrast")
dark_theme_natal_chart.makeSVG()
```

![John Lennon](https://www.kerykeion.net/assets/img/showcase/John%20Lennon%20-%20Dark%20-%20Natal%20Chart.svg)

## Alternative Initialization

You can initialize the AstrologicalSubject from a **UTC** ISO 8601 string:

```python
subject = AstrologicalSubject.get_from_iso_utc_time(
    "Johnny Depp", "1963-06-09T05:00:00Z", "Owensboro", "US")
```

Note : The default time zone is UTC, with Greenwich longitude and latitude.

The default online/offline mode is set to offline, if you set it online the default latitude and longitude will be ignored and
calculated from the city and nation. Remember to pass also the geonames_username parameter if you want to use the online mode, like this:

```python
from kerykeion.astrological_subject import AstrologicalSubject

# Use the static method get_from_iso_utc_time to create an instance of AstrologicalSubject
subject = AstrologicalSubject.get_from_iso_utc_time(
    "Johnny Depp", "1963-06-09T05:00:00Z", "Owensboro", "US", online=True)
```

## Lunar Nodes (Rahu & Ketu)

The following are present:

- True North Lunar Node: Simply referred to as "true_node" (without the term "north") for backward compatibility.
- True South Lunar Node: Referred to as "true_south_node."
- Mean North Lunar Node: Referred to as "mean_node" (without the term "north") for backward compatibility.
- Mean South Lunar Node: Referred to as "mean_south_node."

In instances of the AstrologicalSubject class, all of them are active by default.

In instances of the classes used to generate aspects and SVG charts, only the mean nodes are active. To activate the true nodes, you need to edit the configuration file (kr.config.json).
Example:

```json
...
    {
      "id": 19,
      "name": "True_South_Node",
      "color": "var(--kerykeion-chart-color-true-node)",
      "is_active": true, // Set to true to activate the true node
      "element_points": 0,
      "related_zodiac_signs": [],
      "label": "True_South_Node"
    }
...
```

In the charts, by default, the mean nodes (M) are displayed, while the true nodes are not displayed. 
To display them, you need to edit the configuration file (kr.config.json).

## JSON Support

The astrological subject, which is the base of data used in the library, can be easily serialized to JSON with the `json` method.

```python
from kerykeion import AstrologicalSubject

johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US")

print(johnny.json(dump=False, indent=2))
```

## Documentation

Most of the functions and the classes are self documented by the types and have docstrings.
An auto-generated documentation [is available here](https://www.kerykeion.net/pydocs/kerykeion.html).

Sooner or later I'll try to write an extensive documentation.

## Development

You can clone this repository or download a zip file using the right side buttons.

## Integrate Kerykeion Functionalities in Your Project

If you are interested in integrating Kerykeion's astrological functionalities into your project, I would be happy to collaborate with you. Whether you need custom features, support, or consultation, feel free to reach out to me at my [email](mailto:kerykeion.astrology@gmail.com?subject=Integration%20Request) address.

## License

This project is licensed under the AGPL-3.0 License.
To understand how this impacts your use of the software, please see the [LICENSE](LICENSE) file for details.
If you have questions, you can reach out to me at my [email](mailto:kerykeion.astrology@gmail.com?subject=Kerykeion) address.
As a rule of thumb, if you are using this library in a project, you should open source the code of the project with a compatible license.

You can implement the logic of kerykeion in your project and also keep it closed source by using a third party API, like the [AstrologerAPI](https://rapidapi.com/gbattaglia/api/astrologer/). The AstrologerAPI is AGPL-3.0 compliant. Subscribing to the API is also, currently, the best way to support the project.

## Contributing

Feel free to contribute to the code!
