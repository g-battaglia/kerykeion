---
title: 'Modern Charts'
tags: ['examples', 'charts', 'modern', 'svg', 'kerykeion']
order: 15
---

# Modern Charts

Kerykeion supports a **modern concentric-ring** chart style as an alternative to the classic wheel. The modern style renders charts with graduated ruler scales, clean aspect lines with midpoint glyphs, and a distinct visual hierarchy.

All chart types and all six themes work with the modern style.

## Modern Natal Chart

Pass `style="modern"` to `save_svg()` or `generate_svg_string()`.

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London", online=False,
)

chart_data = ChartDataFactory.create_natal_chart_data(subject)
chart = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
chart.save_svg(output_path=output_dir, filename="lennon-modern-natal", style="modern")
```

![Modern Natal Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/main/tests/data/svg/John%20Lennon%20-%20Natal%20Chart%20-%20Modern.svg)

## Modern Synastry Chart

Dual-wheel modern charts show two subjects with distinct inner and outer planet rings.

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

john = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London", online=False,
)
yoko = AstrologicalSubjectFactory.from_birth_data(
    "Yoko Ono", 1933, 2, 18, 20, 30,
    lng=139.6917, lat=35.6895, tz_str="Asia/Tokyo", online=False,
)

chart_data = ChartDataFactory.create_synastry_chart_data(john, yoko)
chart = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
chart.save_svg(output_path=output_dir, filename="lennon-ono-modern-synastry", style="modern")
```

![Modern Synastry Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/main/tests/data/svg/John%20Lennon%20-%20Synastry%20Chart%20-%20Modern.svg)

## Modern Transit Chart

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London", online=False,
)

transit = AstrologicalSubjectFactory.from_birth_data(
    "Transit", 2025, 3, 4, 12, 0,
    lng=-2.9833, lat=53.4, tz_str="Europe/London", online=False,
)

chart_data = ChartDataFactory.create_transit_chart_data(subject, transit)
chart = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
chart.save_svg(output_path=output_dir, filename="lennon-modern-transit", style="modern")
```

![Modern Transit Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/main/tests/data/svg/John%20Lennon%20-%20Transit%20Chart%20-%20Modern.svg)

## Modern Wheel Only

The wheel-only output (without aspect grid) also supports the modern style:

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London", online=False,
)

chart_data = ChartDataFactory.create_natal_chart_data(subject)
chart = ChartDrawer(chart_data=chart_data, theme="dark")

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
chart.save_wheel_only_svg_file(
    output_path=output_dir,
    filename="lennon-modern-wheel-dark",
    style="modern",
)
```

![Modern Wheel Only](https://raw.githubusercontent.com/g-battaglia/kerykeion/main/tests/data/svg/John%20Lennon%20-%20Natal%20Chart%20-%20Modern%20Wheel%20Only.svg)

## Modern-Only Parameters

These keyword arguments are specific to the modern style and are ignored when `style="classic"`:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `show_zodiac_background_ring` | `bool` | `True` | Draw colored zodiac wedges behind the outer planet ring |

Example disabling the zodiac background:

```python
chart.save_svg(
    output_path=output_dir,
    filename="modern-no-zodiac-bg",
    style="modern",
    show_zodiac_background_ring=False,
)
```

## Classic vs Modern Comparison

Both styles share the same underlying `ChartDataFactory` data. Only the rendering differs:

| Feature | Classic | Modern |
| :--- | :--- | :--- |
| Layout | Traditional wheel with sectors | Concentric rings |
| Aspect display | Grid/list panel | Lines with midpoint glyphs in the core ring |
| Degree indicators | Ticks around the wheel | Graduated ruler ring (1°/5°/10° ticks) |
| Dual chart layout | Inner/outer wheel | Flat dual-ring with shared ruler |
| All themes supported | Yes | Yes |
| All chart types supported | Yes | Yes |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
