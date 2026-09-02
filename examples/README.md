# examples/

Runnable scripts, one topic each. All of them are **offline**: every subject
carries explicit `lng`, `lat` and `tz_str` with `online=False`, so nothing here
contacts GeoNames or needs an account.

Run any of them with:

```bash
uv run python examples/<script>.py
```

Scripts that render charts write into `examples/output/`, which is gitignored;
the rest print to stdout.

## Charts

| Script | What it shows |
| :-- | :-- |
| `quickstart_natal_chart.py` | The shortest path: subject → chart data → SVG. |
| `modern_chart_john_lennon.py` | The modern style (the v6 default) in all three themes. |
| `glyph_size_example.py` | The same natal wheel at `glyph_size` `small` / `medium` / `large`. |
| `svg_extended_example.py` | The six opt-in chart marks, each on a subject that has its referent. |
| `planetary_return.py` | A solar return, cast and drawn. |

## Data and serialization

| Script | What it shows |
| :-- | :-- |
| `aspects_synastry.py` | Synastry aspects through the unified `AspectsFactory`. |
| `synastry_data_example.py` | A synastry `ChartDataModel` dumped as JSON. |
| `moon_phase_json_example.py` | The Moon Phase Overview model as JSON. |
| `context_serializer_example.py` | `to_context()` over every chart type — the AI/LLM XML export. |
| `house_comparison_context_example.py` | The house-overlay section of the context export, for synastry and transits. |

## Reports

| Script | What it shows |
| :-- | :-- |
| `subject_report_example.py` | A bare subject report (no chart data). |
| `natal_report_example.py` | A natal report from `SingleChartDataModel`. |
| `synastry_report_example.py` | A synastry report from `DualChartDataModel`. |
| `transit_report_example.py` | A transit report from `DualChartDataModel`. |
| `composite_report_example.py` | A composite (midpoint) chart report. |
| `solar_return_report_example.py` | A solar return report, single wheel. |
| `dual_return_report_example.py` | A return report as a dual wheel against the natal. |
| `moon_phase_report_example.py` | The Moon Phase Overview as text. |
| `current_time_report.py` | A full report for the current moment. |
| `technique_reports_example.py` | Profections, firdaria, horary, receptions, releasing and dominants, as text. |

## Techniques

| Script | What it shows |
| :-- | :-- |
| `profections_example.py` | Annual profections: the year-lord and its house. |
| `firdaria_example.py` | Firdaria: the Persian major and minor periods. |
| `horary_example.py` | Horary significators and the considerations before judgment. |
| `mutual_receptions_example.py` | Domicile and exaltation receptions between classical planets. |

## Time series and sky events

| Script | What it shows |
| :-- | :-- |
| `transits_time_range.py` | Weekly transits over a range, via `EphemerisDataFactory` + `TransitsTimeRangeFactory`. |
| `retrograde_periods_example.py` | Retrograde spans for 2026, with the clipped-bound flags; Chiron opt-in. |
| `sign_periods_example.py` | Where every planet sits, sign by sign, across one month. |
| `timing_factories_example.py` | Sun times, planetary hours, void-of-course Moon, lunations and mundane aspects — one call each. |
