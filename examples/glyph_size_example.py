"""The same modern natal chart at all three glyph sizes.

``glyph_size`` (``"small"``, ``"medium"``, ``"large"``) scales the planet
cluster of the modern wheel — the glyph and the degree/sign/minute rows that
travel with it. The wheel itself does not change size; what changes is how much
of it the readings occupy, and therefore how crowded a busy chart looks.

Writes three SVGs into ``examples/output/``.
"""

from pathlib import Path

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer

GLYPH_SIZES = ["small", "medium", "large"]


def main() -> None:
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    lennon = AstrologicalSubjectFactory.from_birth_data(
        name="John Lennon",
        year=1940,
        month=10,
        day=9,
        hour=18,
        minute=30,
        lng=-2.9916,
        lat=53.4084,
        tz_str="Europe/London",
        city="Liverpool",
        nation="GB",
        online=False,
    )
    chart_data = ChartDataFactory.create_natal_chart_data(lennon)

    for glyph_size in GLYPH_SIZES:
        drawer = ChartDrawer(chart_data=chart_data, glyph_size=glyph_size)
        drawer.save_svg(output_path=output_dir, filename=f"lennon_natal_{glyph_size}")
        print(f"glyph_size={glyph_size:<6} -> {output_dir / f'lennon_natal_{glyph_size}.svg'}")


if __name__ == "__main__":
    main()
