---
title: 'Chart Internals'
category: 'Reference'
description: 'Internal utilities for SVG rendering and coordinate conversion.'
tags: ['docs', 'charts', 'svg', 'internal', 'kerykeion']
order: 20
---

# Chart Internals

This section documents the low-level functions used by `ChartDrawer` to render SVG elements. These are generally considered internal API but are documented here for completeness and for users who wish to implement custom drawing logic.

## Chart Utilities (`kerykeion.charts.utils`)

Import from: `kerykeion.charts.utils`

### Drawing Functions

These functions return SVG string elements.

| Function                                 | Description                                                            |
| :--------------------------------------- | :--------------------------------------------------------------------- |
| `draw_aspect_grid(...)`                  | Renders the complete triangular grid of aspects.                       |
| `draw_aspect_line(...)`                  | Draws a single line connecting two planets in the center of the wheel. |
| `draw_background_circle(...)`            | Draws the main background circle of the chart.                         |
| `draw_cusp_comparison_grid(...)`         | Renders the grid for comparing house cusps between two charts.         |
| `draw_degree_ring(...)`                  | Draws the ring of tick marks representing degrees.                     |
| `draw_first_circle(...)`                 | Draws the inner/primary circle structure.                              |
| `draw_second_circle(...)`                | Draws the secondary circle structure (e.g. for Synastry).              |
| `draw_third_circle(...)`                 | Draws the tertiary circle structure.                                   |
| `draw_house_comparison_grid(...)`        | Renders the grid comparing planet placements in houses.                |
| `draw_houses_cusps_and_text_number(...)` | Draws lines for house cusps and their numbers.                         |
| `draw_main_house_grid(...)`              | Draws the listing of house positions.                                  |
| `draw_main_planet_grid(...)`             | Draws the listing of planet positions.                                 |
| `draw_secondary_house_grid(...)`         | Draws the house list for the second subject.                           |
| `draw_secondary_planet_grid(...)`        | Draws the planet list for the second subject.                          |
| `draw_single_cusp_comparison_grid(...)`  | Draws a specific part of the cusp comparison grid.                     |
| `draw_single_house_comparison_grid(...)` | Draws a specific part of the house comparison grid.                    |
| `draw_transit_aspect_grid(...)`          | Renders aspects grid for transit charts.                               |
| `draw_transit_aspect_list(...)`          | Renders a list view of transit aspects.                                |
| `draw_transit_ring(...)`                 | Draws the outer ring used in transit charts.                           |
| `draw_transit_ring_degree_steps(...)`    | Draws degree markings for the transit ring.                            |
| `draw_zodiac_slice(...)`                 | Draws the colored wedge/arc for a zodiac sign.                         |
| `draw_house_sectors(...)`                | Transparent house wedges, so a viewer can highlight a house.           |
| `draw_gauquelin_sectors(...)`            | The 36 Gauquelin sector divisions, replacing the 12-house ring.        |
| `draw_gauquelin_sector_hit_areas(...)`   | The matching 36 transparent wedges for interactive highlighting.       |
| `draw_gauquelin_unified_grid(...)`       | One Gauquelin table in place of both the planet grid and the cusp grid. |
| `make_lunar_phase(degrees_between, latitude)` | The SVG fragment rendering the Moon's illuminated phase.           |
| `out_of_bounds_badge_svg(point, text_color)` | The `OOB` badge for a point, or nothing when it is inside the bounds. |

### Calculation & Formatting Utilities

| Function                                           | Description                                                         |
| :------------------------------------------------- | :------------------------------------------------------------------ |
| `calculate_element_points(...)`                    | Internal calculation for element distribution.                      |
| `calculate_quality_points(...)`                    | Internal calculation for quality distribution.                      |
| `calculate_synastry_element_points(...)`           | Internal calculation for synastry element comparison.               |
| `calculate_synastry_quality_points(...)`           | Internal calculation for synastry quality comparison.               |
| `calculate_moon_phase_chart_params(...)`           | Calculates lunar phase icon parameters.                             |
| `convert_decimal_to_degree_string(dec, format_type="3")` | Converts a float degree (e.g. 12.5) to a string (e.g. "12° 30'"). `format_type` selects the `"1"` / `"2"` / `"3"` layout. |
| `convert_longitude_coordinate_to_string(coord, east_label, west_label)` | Converts a longitude coordinate to a readable string. |
| `convert_latitude_coordinate_to_string(coord, north_label, south_label)` | Converts a latitude coordinate to a readable string. |
| `hms_to_decimal_hours(hours, minutes, seconds)`    | Combines hours, minutes, seconds into a decimal hour.               |
| `format_datetime_with_timezone(iso_datetime_string)` | Formats an ISO datetime string with timezone info.                |
| `format_location_string(location, max_length=35)` | Truncates a location string to fit within a max length. |
| `get_decoded_kerykeion_celestial_point_name(name)` | Decodes internal point names to human names.                        |
| `timedelta_to_decimal_hours(datetime_offset)`      | Converts a `timedelta` offset to a float in hours.                  |
| `escape_svg_text(value)`                           | Escapes a plain-text value for safe embedding in SVG markup.        |
| `label_separation_degrees(label_width_px, radius_px, gutter_px=3.0)` | The degrees two labels of that width need at that radius for their ink to clear. |
| `separate_collapsed_wedges(boundaries, spans, reversed_wedges, minimum)` | Gives every wedge at least `minimum` degrees, taken from what the widest can spare. |
| `planet_grid_column_width(names=(), show_out_of_bounds=False, font_size=10.0)` | Column stride wide enough that a name never lands on the row before it. |
| `gauquelin_column_width(with_out_of_bounds=False)` | Width of one Gauquelin column, wider when it carries OOB badges.     |
| `abbreviate_point_name(name, max_width=56.0, font_size=10.0)` | Shortens a name with a full stop until its ink fits `max_width`. |

---

## Planet Rendering (`kerykeion.charts.draw_planets`)

Import from: `kerykeion.charts.draw_planets`

### `draw_planets`

The main function for rendering planetary glyphs on the chart wheel. It handles collision detection and placement adjustment to prevent overlapping symbols.

> **Note:** This function has a complex internal signature with many positional parameters (radius, celestial points settings, circle radii, house degree references, chart type, etc.). It is intended for internal use by `ChartDrawer`. Refer to the source code at `kerykeion/charts/draw_planets.py` for the full parameter list if building custom renderers.

---

## Modern Renderer (`kerykeion.charts.draw_modern`)

The modern style draws the wheel as five concentric rings inside a `0 0 100 100`
viewBox centred on `(50, 50)`, positioning everything by rotation
(`rotate(-angle 50 50)`):

1. House cusps with sign glyphs and degree/minute data
2. A graduated ruler scale (1° / 5° / 10° ticks)
3. Planet data clusters with their indicator/tether lines
4. House numbers 1-12
5. Aspect lines at the core, with small glyphs at their midpoints

| Entry point | Description |
| :---------- | :---------- |
| `draw_modern_horoscope(...)` | The single-subject wheel; emits the `<g kr:node="ModernHoroscope">` root. |
| `draw_modern_dual_horoscope(...)` | The two-ring wheel for Transit, Synastry, DualReturnChart and Progression; emits `<g kr:node="ModernDualHoroscope" kr:charttype="...">`. |
| `motion_marker(...)` | The `RX` / `SR` / `SD` marker for a point's marker row. |
| `ClusterProfile` | The measured geometry of one planet cluster (row heights, offsets) that the layout works from. |

## SVG Metadata (`kerykeion.charts.svg_metadata`)

Both ends of the `kr:` vocabulary described in
[Charts](/content/docs/charts#machine-readable-svg-point-metadata): the emitter
and the parser that reads the markup back. Three serializers draw celestial
points (classic primary, classic secondary, modern), and one sentence spoken by
all three is what makes an absent attribute mean "no such state" rather than "a
style that forgot to say so".

| Name | Description |
| :--- | :---------- |
| `point_state_attributes(point) -> str` | The `kr:` attributes describing a point's physical state. The single emitter all three serializers call. |
| `parse_chart_points(svg) -> list[ChartPointTag]` | Every ChartPoint group in the markup, in document order. |
| `parse_indicators(svg) -> list[IndicatorTag]` | Every Indicator (tether line) group, in document order. |
| `ChartPointTag` | One rendered point: `slug`, `horoscope`, `display_angle`, `sign`, `sign_position`, `retrograde`, `motion_state`, `speed`, `declination`, `out_of_bounds`, `angularities`, `stellium`, `magnitude`, `near_point`, `orb`. |
| `IndicatorTag` | One tether line: `slug`, `horoscope`, `true_angle` — the point's **true** wheel angle, before decluttering moved the glyph. |

The parsing grammar tolerates attribute order and either quote style.

## Label Spreading (`kerykeion.charts.spreading`)

Two things close together in the sky are close together on the page, and at some
point their ink meets. This module holds the mathematics both the planet
clusters and the house numbers use to avoid that.

| Function | Description |
| :------- | :---------- |
| `isotonic_non_decreasing(values)` | The pool-adjacent-violators algorithm. |
| `spread_around_wheel(angles, min_separation, half_extents=None)` | The complete answer for labels of one uniform size, such as a house number. |

Isotonic regression rather than pushing each collision aside: it is the
placement that minimises total movement subject to the separation, so a tight
cluster is *centred* on where it really is instead of sliding off in whichever
direction the sweep happened to run — and the order is preserved by
construction, which for numbers running 1 to 12 is not a nicety.

## Glyph Measurements (`glyph_metrics`, `glyph_ink_metrics`)

Two generated data modules. They are data files that happen to be Python, kept
apart from the renderer so a re-measurement's diff lands here.

- **`kerykeion.charts.glyph_metrics`** — per-character advance widths as a
  fraction of the em, taken as the widest each character reaches across Times,
  Helvetica and Arial Unicode. `estimate_text_width` is its only consumer, and
  the info panel's row guard is what it serves. Regenerated by
  `scripts/regenerate_glyph_widths.py`.
- **`kerykeion.charts.glyph_ink_metrics`** — the measured **ink** extents of
  everything a modern planet cluster draws, produced by rasterizing the symbols
  in a browser rather than reading layout boxes (half the glyphs are
  stroke-only, and `getBBox` excludes stroke width). `*_HALF_WIDTH` /
  `*_HALF_HEIGHT` give the widest reach of real ink from an element's anchor;
  `*_INK_CENTRE` gives how far the ink's midpoint sits from that anchor, which
  is what keeps a cluster's rows from reading as a crooked skewer. Regenerated
  by `poe regenerate:glyph-ink`.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
