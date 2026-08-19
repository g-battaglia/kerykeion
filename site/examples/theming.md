---
title: 'Theming'
tags: ['examples', 'charts', 'theming', 'css', 'kerykeion']
order: 11
---

# Theming

## Overview

A chart is an SVG whose every colour comes from a CSS custom property. A theme
is nothing more than a file that sets those properties on `:root`, which the
drawer copies into the document it produces. Three themes ship with the library,
and the fourth option is to ship none at all and dress the drawing yourself.

| `theme` | what it is |
| --- | --- |
| `"classic"` | The default: a light chart with the rainbow zodiac band. |
| `"dark"` | For dark backgrounds and low light. |
| `"black-and-white"` | Monochrome, for printing and for photocopies. |
| `None` | No stylesheet is emitted. The drawing takes its colours from the document that hosts it. |

All three shipped themes meet WCAG AAA on everything a reader reads — degrees,
minutes, house numbers and percentages at 7:1 — and the AA 3:1 floor on the marks
a reader looks at: aspect lines, sign icons against their own band, the degree
indicator and the house cusps.

## Applying a theme

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data.factory import ChartDataFactory
from kerykeion.charts.drawer import ChartDrawer

subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London", online=False,
)
data = ChartDataFactory.create_natal_chart_data(subject)

out_dir = Path("charts_output")
out_dir.mkdir(exist_ok=True)

for theme in ("classic", "dark", "black-and-white"):
    ChartDrawer(data, theme=theme).save_svg(output_path=out_dir)
```

Passing a name that is not one of the three raises `KerykeionException`. There is
no silent fallback: a misspelt theme is a bug you want to hear about, not a chart
that quietly comes out in the wrong colours.

## Making your own

### The mechanism

Pass `theme=None` and the SVG carries no `<style>` block of its own. Every colour
then resolves against whatever the surrounding document defines, so you style the
chart the way you style anything else on the page:

```python
chart = ChartDrawer(data, theme=None)
```

```html
<style>
  :root {
    --kerykeion-chart-color-paper-1: #fdf6e3;
    --kerykeion-chart-color-sun: #b58900;
    --kerykeion-chart-color-moon: #6c71c4;
    --kerykeion-modern-planet-ring: #eee8d5;
  }
</style>
```

The other way round works too: keep a shipped theme and override the few
properties you want, since your rule comes after the one the drawer emitted.

### The families of names

There are around a hundred properties, and they are named rather than numbered,
so it is the families that are worth knowing:

| family | what it paints |
| --- | --- |
| `--kerykeion-chart-color-<point>` | A point's ink: `sun`, `moon`, `mercury`, … and also `first-house`, `tenth-house` for the angles. It fills the glyph **and** the degrees and minutes beside it, so it is text as well as drawing. |
| `--kerykeion-chart-color-<aspect>` | One per aspect: `conjunction`, `square`, `trine`, … Colours the line and the symbol at its midpoint. |
| `--kerykeion-chart-color-zodiac-icon-<n>` | The twelve sign glyphs, `0` = Aries. |
| `--kerykeion-modern-zodiac-bg-<n>` | The twelve bands behind them, plus `--kerykeion-modern-zodiac-bg-opacity`. |
| `--kerykeion-modern-*` | The modern wheel's own structure: `planet-ring`, `house-ring`, `stroke` (the ring outlines), `cusp` (the house boundaries, which carry 3:1 because they are read), `indicator`, `retrograde`, `stationary`. |
| `--kerykeion-chart-color-paper-0` / `-1` | Foreground and background of the sheet. |
| `--kerykeion-chart-color-<element>-percentage` | The element and quality lines in the side panel. |

Two of these deserve a warning. A point's colour is **text**, not just a glyph,
so a shade that looks fine on a symbol may be unreadable on the minutes next to
it. And `--kerykeion-modern-cusp` is deliberately darker than
`--kerykeion-modern-stroke`: the ring outlines are decoration, a house boundary
is information.

### Measure what you make

A palette that pleases the eye on a big screen can still lose a reader. Before
shipping your own, put it through the same measurement the built-in themes are
held to — every mark against the surface it is actually drawn on, at the
threshold its role demands. That check exists as a tool, not only as an internal
guard, precisely so that a custom palette can be held to it.
