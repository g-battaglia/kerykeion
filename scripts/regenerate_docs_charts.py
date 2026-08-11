#!/usr/bin/env python3
"""
Regenerate the chart SVGs used in docs/charts/ (README showcase grid).

Generates one natal chart for John Lennon per file in docs/charts/ — every
style x theme combination the README showcases. See CHARTS below.

All SVGs are saved with inlined CSS variables (remove_css_variables=True)
so they render correctly on GitHub without external stylesheets.

Usage:
    python scripts/regenerate_docs_charts.py
"""

from pathlib import Path
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.chart_data.factory import ChartDataFactory
from kerykeion.charts.drawer import ChartDrawer

# Every file in docs/charts/, not a subset. The README embeds these by raw URL,
# so one left behind is a documentation image showing a chart the library no
# longer draws — which is what happened to eleven of them when the info panel
# gained a row and only these four were listed here.
CHARTS = [
    ("classic_default_natal", "classic", "classic"),
    ("classic_dark_natal", "classic", "dark"),
    ("classic_light_natal", "classic", "light"),
    ("classic_dark_high_contrast_natal", "classic", "dark-high-contrast"),
    ("classic_strawberry_natal", "classic", "strawberry"),
    ("classic_black_and_white_natal", "classic", "black-and-white"),
    # Same style and theme, so these two render byte-identically. Both filenames
    # were already committed and the README links `modern_classic_natal`, so
    # neither is dropped here; listing both is what keeps them in step. Retiring
    # one is a docs change, not a regeneration one.
    ("modern_default_natal", "modern", "classic"),
    ("modern_classic_natal", "modern", "classic"),
    ("modern_dark_natal", "modern", "dark"),
    ("modern_light_natal", "modern", "light"),
    ("modern_black_and_white_natal", "modern", "black-and-white"),
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
