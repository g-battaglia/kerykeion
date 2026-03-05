#!/usr/bin/env python3
"""
Regenerate the chart SVGs used in docs/charts/ (README showcase grid).

Generates 4 natal charts for John Lennon:
  - classic_default_natal.svg  (style="classic", theme="classic")
  - classic_dark_natal.svg     (style="classic", theme="dark")
  - modern_default_natal.svg   (style="modern",  theme="classic")
  - modern_dark_natal.svg      (style="modern",  theme="dark")

All SVGs are saved with inlined CSS variables (remove_css_variables=True)
so they render correctly on GitHub without external stylesheets.

Usage:
    python scripts/regenerate_docs_charts.py
"""

from pathlib import Path
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

CHARTS = [
    ("classic_default_natal", "classic", "classic"),
    ("classic_dark_natal", "classic", "dark"),
    ("modern_default_natal", "modern", "classic"),
    ("modern_dark_natal", "modern", "dark"),
]


def main():
    output_dir = Path(__file__).parent.parent / "docs" / "charts"
    output_dir.mkdir(parents=True, exist_ok=True)

    lennon = AstrologicalSubjectFactory.from_birth_data(
        name="John Lennon",
        year=1940,
        month=10,
        day=9,
        hour=18,
        minute=30,
        city="Liverpool",
        nation="GB",
        tz_str="Europe/London",
        lat=53.4084,
        lng=-2.9916,
        online=False,
        suppress_geonames_warning=True,
    )

    natal_data = ChartDataFactory.create_natal_chart_data(lennon)

    for filename, style, theme in CHARTS:
        drawer = ChartDrawer(natal_data, theme=theme)
        drawer.save_svg(
            output_path=str(output_dir),
            filename=filename,
            style=style,
            remove_css_variables=True,
        )

    print(f"\nAll docs charts regenerated in {output_dir}")


if __name__ == "__main__":
    main()
