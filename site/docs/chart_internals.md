---
title: 'Chart Internals'
category: 'Reference'
description: 'Internal utilities for SVG rendering and coordinate conversion.'
tags: ['docs', 'charts', 'svg', 'internal', 'kerykeion']
order: 18
---

# Chart Internals

This section documents the low-level functions used by `ChartDrawer` to render SVG elements. These are generally considered internal API but are documented here for completeness and for users who wish to implement custom drawing logic.

## Chart Utilities (`kerykeion.charts.charts_utils`)

Import from: `kerykeion.charts.charts_utils`

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

### Calculation & Formatting Utilities

| Function                                           | Description                                                         |
| :------------------------------------------------- | :------------------------------------------------------------------ |
| `calculate_element_points(...)`                    | Internal calculation for element distribution.                      |
| `calculate_quality_points(...)`                    | Internal calculation for quality distribution.                      |
| `calculate_synastry_element_points(...)`           | Internal calculation for synastry element comparison.               |
| `calculate_synastry_quality_points(...)`           | Internal calculation for synastry quality comparison.               |
| `calculate_moon_phase_chart_params(...)`           | Calculates lunar phase icon parameters.                             |
| `convert_decimal_to_degree_string(dec)`            | Converts a float degree (e.g., 12.5) to a string (e.g., "12° 30'"). |
| `convert_longitude_coordinate_to_string(lng)`      | Converts a longitude coordinate to a readable string.               |
| `convert_latitude_coordinate_to_string(lat)`       | Converts a latitude coordinate to a readable string.                |
| `decHourJoin(h, m, s)`                             | Combines hours, minutes, seconds into a decimal hour.               |
| `format_datetime_with_timezone(dt, tz)`            | Formats a datetime object with timezone info.                       |
| `format_location_string(city, nation)`             | Standardizes location display strings.                              |
| `get_decoded_kerykeion_celestial_point_name(name)` | Decodes internal point names to human names.                        |
| `offsetToTz(offset)`                               | Converts a time offset (int) to a timezone string.                  |

---

## Planet Rendering (`kerykeion.charts.draw_planets`)

Import from: `kerykeion.charts.draw_planets`

### `draw_planets`

The main function for rendering planetary glyphs on the chart wheel. It handles collision detection and placement adjustment to prevent overlapping symbols.

```python
from kerykeion.charts.draw_planets import draw_planets

svg_elements = draw_planets(
    planets=chart_data.planets,
    r=200,                # Radius
    cx=300, cy=300,      # Center
    classic_chart=True   # Style flag
)
```
