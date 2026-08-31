---
title: 'Glyph Sizes'
tags: ['examples', 'charts', 'modern', 'glyphs', 'kerykeion']
order: 17
---

# Glyph Sizes

The modern wheel draws each point as a **cluster**: the glyph, the degree, the
sign, and a marker row for retrograde or station letters. `glyph_size` picks how
large that cluster is drawn, and the wheel's decluttering works to the size it
was given, so nothing collides at any of the three settings.

| `glyph_size` | What it draws |
| :--- | :--- |
| `"small"` | The medium cluster at 90%. More room between neighbours, useful for a chart with many active points. |
| `"medium"` | The default. |
| `"large"` | The planet glyph at the classic style's own size, in the default configuration — zodiac background ring on, per-glyph optical map applied. |

The option is **modern-only**: the classic wheel ignores it. Anything other than
those three raises `KerykeionException` — from the constructor and from every
render method alike.

## Setting the size

`glyph_size` is a constructor argument (a per-instance default) and a per-call
override on `save_svg`, `generate_svg_string`, `save_wheel_only_svg_file` and
`generate_wheel_only_svg_string`. A per-call value applies to that call only and
does not stick.

```python
from pathlib import Path

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer

subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    city="Liverpool", nation="GB",
    lng=-2.97794, lat=53.41058, tz_str="Europe/London",
    online=False,
)

chart_data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)

for size in ("small", "medium", "large"):
    drawer.save_svg(
        output_path=output_dir,
        filename=f"lennon-{size}",
        glyph_size=size,
    )
```

Give each render its own `filename`: without one they would all fall back to the
same default name and overwrite each other.

### Small

![Modern natal chart, small glyphs](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/alpha/v6/tests/data/svg/John%20Lennon%20-%20Natal%20Chart%20-%20Modern%20Small.svg)

### Medium (default)

![Modern natal chart, medium glyphs](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/alpha/v6/tests/data/svg/John%20Lennon%20-%20Natal%20Chart%20-%20Modern.svg)

### Large

![Modern natal chart, large glyphs](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/alpha/v6/tests/data/svg/John%20Lennon%20-%20Natal%20Chart%20-%20Modern%20Large.svg)

## Setting it once for a drawer

```python
big = ChartDrawer(chart_data, glyph_size="large")

# Both of these render large
wheel = big.generate_wheel_only_svg_string()
full = big.generate_svg_string()

# ...and this one does not: the per-call value wins for this call alone
small_once = big.generate_svg_string(glyph_size="small")
```

## Reading the size back out of the SVG

The wheel root carries `kr:glyphsize` when the size is not the default:

```python
import re

svg = ChartDrawer(chart_data).generate_svg_string(glyph_size="large")
root = re.search(r"<g kr:node=.ModernHoroscope.[^>]*>", svg)
print("kr:glyphsize" in root.group(0))
```

**Output:**
```
True
```

`"medium"` is written as absence, the same way `kr:oob` and `kr:retrograde` mark
only the exception. See
[Machine-Readable SVG Point Metadata](/content/docs/charts#machine-readable-svg-point-metadata).

## Choosing one

- Many active points, or a dual wheel — `"small"`, which buys separation.
- A chart printed beside a classic one — `"large"`, whose planet glyphs match the
  classic engine's own size.
- Anything else — the default.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
