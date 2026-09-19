#!/usr/bin/env python3
"""Convert the six README theme previews to PNG without recalculating charts.

Run with the optional renderer installed:
    uv run --with cairosvg python scripts/convert_docs_charts.py
"""

import argparse
import math
from pathlib import Path
import xml.etree.ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHARTS_DIR = PROJECT_ROOT / "docs" / "charts"
PREVIEW_NAMES = (
    "modern_classic_natal",
    "modern_dark_natal",
    "modern_black_and_white_natal",
    "classic_default_natal",
    "classic_dark_natal",
    "classic_black_and_white_natal",
)
DEFAULT_WIDTH = 1780


def svg_options(source: Path, width: int) -> dict:
    """Read the SVG viewport and page color for CairoSVG.

    CairoSVG does not paint the root's CSS background-color. Pass it as the
    canvas color so dark previews retain their background on GitHub.
    """
    if width <= 0:
        raise ValueError("PNG width must be a positive integer")
    data = source.read_bytes()
    root = ET.fromstring(data)
    try:
        x, y, svg_width, svg_height = (
            float(value) for value in root.attrib["viewBox"].replace(",", " ").split()
        )
    except (KeyError, ValueError) as exc:
        raise ValueError(f"{source}: expected a viewBox with four numbers") from exc
    if not all(math.isfinite(value) for value in (x, y, svg_width, svg_height)) or min(svg_width, svg_height) <= 0:
        raise ValueError(f"{source}: viewBox dimensions must be positive and finite")

    background = None
    for declaration in root.get("style", "").split(";"):
        name, separator, value = declaration.partition(":")
        if separator and name.strip().lower() == "background-color":
            background = value.strip() or None

    return {
        "bytestring": data,
        "parent_width": svg_width,
        "parent_height": svg_height,
        "output_width": width,
        "output_height": max(1, round(width * svg_height / svg_width)),
        "background_color": background,
    }


def load_renderer():
    """Load CairoSVG only when converting, not for --help or unit tests."""
    try:
        from cairosvg import svg2png
    except (ImportError, OSError) as exc:
        raise RuntimeError(
            "CairoSVG and the Cairo system library are required. Run "
            "`uv run --with cairosvg python scripts/convert_docs_charts.py`. "
            "If Cairo cannot be loaded, see scripts/README.md for system setup."
        ) from exc
    return svg2png


def convert_previews(output_dir: Path = CHARTS_DIR, width: int = DEFAULT_WIDTH) -> list[Path]:
    """Write PNGs beside the SVGs, or into a caller-selected directory."""
    # Validate all sources before writing any output. Preserve the SVG bytes,
    # including negative viewBox origins and the embedded glyph definitions.
    sources = [(name, svg_options(CHARTS_DIR / f"{name}.svg", width)) for name in PREVIEW_NAMES]
    render = load_renderer()
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for name, options in sources:
        destination = output_dir / f"{name}.png"
        render(**options, write_to=str(destination))
        outputs.append(destination)
    return outputs


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help="PNG width in pixels, default: 1780")
    parser.add_argument(
        "--output-dir", type=Path, default=CHARTS_DIR,
        help="Destination directory, default: docs/charts in this checkout",
    )
    args = parser.parse_args(argv)
    if args.width <= 0:
        parser.error("--width must be a positive integer")
    try:
        outputs = convert_previews(args.output_dir, args.width)
    except (OSError, ValueError, RuntimeError, ET.ParseError) as exc:
        parser.exit(1, f"error: {exc}\n")
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
