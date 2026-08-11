---
title: 'Report'
tags: ['examples', 'reports', 'cli', 'kerykeion']
order: 14
---

# Generate a text Report

This is a simple example of how to generate a report using the `ReportGenerator` class.

```python
from kerykeion import ReportGenerator, AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Kanye", 1977, 6, 8, 8, 45,
    lng=-84.38798, lat=33.7490, tz_str="America/New_York", online=False,
)

# Subject-only report
ReportGenerator(subject).print_report(include_aspects=False)

# Or generate from chart data with aspects
natal = ChartDataFactory.create_natal_chart_data(subject)
ReportGenerator(natal).print_report(max_aspects=10)
```

The output in the terminal will be:

```plaintext
======================
Kanye — Subject Report
======================

+Astrological Subject — Birth Data---------------+
| Field              | Value                     |
+--------------------+---------------------------+
| Name               | Kanye                     |
| Date               | 08/06/1977                |
| Time               | 08:45                     |
| City               | Greenwich                 |
| Nation             | GB                        |
| Latitude           | 33.7490°                  |
| Longitude          | -84.3880°                 |
| Timezone           | America/New_York          |
| Day of Week        | Wednesday                 |
| ISO Local Datetime | 1977-06-08T08:45:00-04:00 |
| Diurnality         | Diurnal                   |
+--------------------+---------------------------+

+Astrological Subject — Settings------------+
| Setting             | Value               |
+---------------------+---------------------+
| Zodiac Type         | Tropical            |
| Houses System       | Placidus            |
| Perspective Type    | Apparent Geocentric |
| Julian Day          | 2443303.031250      |
| Active Points Count | 14                  |
+---------------------+---------------------+

+Celestial Points-------+--------+----------+--------------+------------+---------+------+----------------+
| Point                 | Sign   | Position | Speed        | Motion     | Decl.   | Ret. | House          |
+-----------------------+--------+----------+--------------+------------+---------+------+----------------+
| Ascendant             | Can ♋ | 18.00°   | +306.3499°/d | -          | N/A     | -    | First House    |
| Medium Coeli          | Ari ♈ | 3.98°    | +393.1543°/d | -          | N/A     | -    | Tenth House    |
| Sun                   | Gem ♊ | 17.60°   | +0.9564°/d   | Average    | +22.86° | -    | Twelfth House  |
| Moon                  | Pis ♓ | 16.43°   | +12.8096°/d  | Average    | -2.54°  | -    | Ninth House    |
| Mercury               | Tau ♉ | 26.29°   | +1.5275°/d   | Average    | +16.98° | -    | Eleventh House |
| Venus                 | Tau ♉ | 2.03°    | +0.9041°/d   | Slow       | +9.85°  | -    | Tenth House    |
| Mars                  | Tau ♉ | 1.79°    | +0.7428°/d   | Fast       | +11.13° | -    | Tenth House    |
| Jupiter               | Gem ♊ | 14.61°   | +0.2323°/d   | Fast       | +22.07° | -    | Eleventh House |
| Saturn                | Leo ♌ | 12.80°   | +0.0906°/d   | Fast       | +17.91° | -    | Second House   |
| Uranus                | Sco ♏ | 8.27°    | -0.0295°/d   | Retrograde | -13.84° | R    | Fourth House   |
| Neptune               | Sag ♐ | 14.69°   | -0.0270°/d   | Retrograde | -21.04° | R    | Fifth House    |
| Pluto                 | Lib ♎ | 11.45°   | -0.0071°/d   | Retrograde | +11.36° | R    | Fourth House   |
| True North Lunar Node | Lib ♎ | 22.82°   | -0.0023°/d   | -          | -8.87°  | R    | Fourth House   |
| Chiron                | Tau ♉ | 4.17°    | +0.0482°/d   | -          | +12.60° | -    | Tenth House    |
+-----------------------+--------+----------+--------------+------------+---------+------+----------------+

+Houses (Placidus)--------+----------+-------------------+
| House          | Sign   | Position | Absolute Position |
+----------------+--------+----------+-------------------+
| First House    | Can ♋ | 18.00°   | 108.00°           |
| Second House   | Leo ♌ | 9.51°    | 129.51°           |
| Third House    | Vir ♍ | 4.02°    | 154.02°           |
| Fourth House   | Lib ♎ | 3.98°    | 183.98°           |
| Fifth House    | Sco ♏ | 9.39°    | 219.39°           |
| Sixth House    | Sag ♐ | 15.68°   | 255.68°           |
| Seventh House  | Cap ♑ | 18.00°   | 288.00°           |
| Eighth House   | Aqu ♒ | 9.51°    | 309.51°           |
| Ninth House    | Pis ♓ | 4.02°    | 334.02°           |
| Tenth House    | Ari ♈ | 3.98°    | 3.98°             |
| Eleventh House | Tau ♉ | 9.39°    | 39.39°            |
| Twelfth House  | Gem ♊ | 15.68°   | 75.68°            |
+----------------+--------+----------+-------------------+

+Lunar Phase--------------+-----------------+
| Lunar Phase Information | Value           |
+-------------------------+-----------------+
| Phase Name              | Last Quarter 🌗 |
| Sun-Moon Angle          | 268.83°         |
| Lunation Day            | 21              |
+-------------------------+-----------------+
==========================
Kanye — Natal Chart Report
==========================

+Natal — Birth Data--+---------------------------+
| Field              | Value                     |
+--------------------+---------------------------+
| Name               | Kanye                     |
| Date               | 08/06/1977                |
| Time               | 08:45                     |
| City               | Greenwich                 |
| Nation             | GB                        |
| Latitude           | 33.7490°                  |
| Longitude          | -84.3880°                 |
| Timezone           | America/New_York          |
| Day of Week        | Wednesday                 |
| ISO Local Datetime | 1977-06-08T08:45:00-04:00 |
| Diurnality         | Diurnal                   |
+--------------------+---------------------------+

+Natal — Settings-----+---------------------+
| Setting             | Value               |
+---------------------+---------------------+
| Zodiac Type         | Tropical            |
| Houses System       | Placidus            |
| Perspective Type    | Apparent Geocentric |
| Julian Day          | 2443303.031250      |
| Active Points Count | 14                  |
+---------------------+---------------------+

+Natal Celestial Points-+--------+----------+--------------+------------+---------+------+----------------+
| Point                 | Sign   | Position | Speed        | Motion     | Decl.   | Ret. | House          |
+-----------------------+--------+----------+--------------+------------+---------+------+----------------+
| Ascendant             | Can ♋ | 18.00°   | +306.3499°/d | -          | N/A     | -    | First House    |
| Medium Coeli          | Ari ♈ | 3.98°    | +393.1543°/d | -          | N/A     | -    | Tenth House    |
| Sun                   | Gem ♊ | 17.60°   | +0.9564°/d   | Average    | +22.86° | -    | Twelfth House  |
| Moon                  | Pis ♓ | 16.43°   | +12.8096°/d  | Average    | -2.54°  | -    | Ninth House    |
| Mercury               | Tau ♉ | 26.29°   | +1.5275°/d   | Average    | +16.98° | -    | Eleventh House |
| Venus                 | Tau ♉ | 2.03°    | +0.9041°/d   | Slow       | +9.85°  | -    | Tenth House    |
| Mars                  | Tau ♉ | 1.79°    | +0.7428°/d   | Fast       | +11.13° | -    | Tenth House    |
| Jupiter               | Gem ♊ | 14.61°   | +0.2323°/d   | Fast       | +22.07° | -    | Eleventh House |
| Saturn                | Leo ♌ | 12.80°   | +0.0906°/d   | Fast       | +17.91° | -    | Second House   |
| Uranus                | Sco ♏ | 8.27°    | -0.0295°/d   | Retrograde | -13.84° | R    | Fourth House   |
| Neptune               | Sag ♐ | 14.69°   | -0.0270°/d   | Retrograde | -21.04° | R    | Fifth House    |
| Pluto                 | Lib ♎ | 11.45°   | -0.0071°/d   | Retrograde | +11.36° | R    | Fourth House   |
| True North Lunar Node | Lib ♎ | 22.82°   | -0.0023°/d   | -          | -8.87°  | R    | Fourth House   |
| Chiron                | Tau ♉ | 4.17°    | +0.0482°/d   | -          | +12.60° | -    | Tenth House    |
+-----------------------+--------+----------+--------------+------------+---------+------+----------------+

+Natal Houses (Placidus)--+----------+-------------------+
| House          | Sign   | Position | Absolute Position |
+----------------+--------+----------+-------------------+
| First House    | Can ♋ | 18.00°   | 108.00°           |
| Second House   | Leo ♌ | 9.51°    | 129.51°           |
| Third House    | Vir ♍ | 4.02°    | 154.02°           |
| Fourth House   | Lib ♎ | 3.98°    | 183.98°           |
| Fifth House    | Sco ♏ | 9.39°    | 219.39°           |
| Sixth House    | Sag ♐ | 15.68°   | 255.68°           |
| Seventh House  | Cap ♑ | 18.00°   | 288.00°           |
| Eighth House   | Aqu ♒ | 9.51°    | 309.51°           |
| Ninth House    | Pis ♓ | 4.02°    | 334.02°           |
| Tenth House    | Ari ♈ | 3.98°    | 3.98°             |
| Eleventh House | Tau ♉ | 9.39°    | 39.39°            |
| Twelfth House  | Gem ♊ | 15.68°   | 75.68°            |
+----------------+--------+----------+-------------------+

+Lunar Phase--------------+-----------------+
| Lunar Phase Information | Value           |
+-------------------------+-----------------+
| Phase Name              | Last Quarter 🌗 |
| Sun-Moon Angle          | 268.83°         |
| Lunation Day            | 21              |
+-------------------------+-----------------+

+Element Distribution-----------+
| Element  | Count | Percentage |
+----------+-------+------------+
| Fire 🔥  | 3.0   | 18%        |
| Earth 🌍 | 5.1   | 31%        |
| Air 💨   | 4.0   | 24%        |
| Water 💧 | 4.5   | 27%        |
| Total    | 16.6  | 100%       |
+----------+-------+------------+

+Quality Distribution-----------+
| Quality  | Count | Percentage |
+----------+-------+------------+
| Cardinal | 4.5   | 27%        |
| Fixed    | 6.6   | 40%        |
| Mutable  | 5.5   | 33%        |
| Total    | 16.6  | 100%       |
+----------+-------+------------+

+Active Celestial Points-----+
| #  | Active Point          |
+----+-----------------------+
| 1  | Sun                   |
| 2  | Moon                  |
| 3  | Mercury               |
| 4  | Venus                 |
| 5  | Mars                  |
| 6  | Jupiter               |
| 7  | Saturn                |
| 8  | Uranus                |
| 9  | Neptune               |
| 10 | Pluto                 |
| 11 | True_North_Lunar_Node |
| 12 | Chiron                |
| 13 | Ascendant             |
| 14 | Medium_Coeli          |
+----+-----------------------+

+-------------+---------+
| Aspect      | Orb (°) |
+-------------+---------+
| conjunction | 6.0     |
| opposition  | 6.0     |
| trine       | 6.0     |
| sextile     | 5.0     |
| square      | 6.0     |
+-------------+---------+

+Aspects (showing 10 of 21)-----------------------+-------+--------------+
| Point 1 | Aspect        | Point 2               | Orb   | Movement     |
+---------+---------------+-----------------------+-------+--------------+
| Sun     | square □      | Moon                  | 1.17° | Applying →   |
| Sun     | conjunction ☌ | Jupiter               | 2.99° | Separating ← |
| Sun     | sextile ⚹     | Saturn                | 4.80° | Separating ← |
| Sun     | opposition ☍  | Neptune               | 2.91° | Separating ← |
| Sun     | trine △       | Pluto                 | 6.15° | Separating ← |
| Sun     | trine △       | True North Lunar Node | 5.22° | Applying →   |
| Moon    | square □      | Jupiter               | 1.83° | Separating ← |
| Moon    | square □      | Neptune               | 1.74° | Separating ← |
| Moon    | trine △       | Ascendant             | 1.56° | Separating ← |
| Venus   | conjunction ☌ | Mars                  | 0.24° | Separating ← |
+---------+---------------+-----------------------+-------+--------------+
```

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
