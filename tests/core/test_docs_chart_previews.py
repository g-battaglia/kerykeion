"""README preview links and conversion options, without requiring CairoSVG."""

from html.parser import HTMLParser
from pathlib import Path
import re
import struct
import sys
from unittest.mock import Mock
import xml.etree.ElementTree as ET

import pytest

from scripts import convert_docs_charts as converter


@pytest.fixture
def svg(tmp_path):
    source = tmp_path / "chart.svg"
    source.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" '
        'viewBox="0 -15 890 580" style="background-color: #0f172a; color: white"/>'
    )
    return source


def test_viewport_background_and_original_bytes(svg):
    options = converter.svg_options(svg, 1780)
    assert options == {
        "bytestring": svg.read_bytes(),
        "parent_width": 890,
        "parent_height": 580,
        "output_width": 1780,
        "output_height": 1160,
        "background_color": "#0f172a",
    }
    assert ET.fromstring(options["bytestring"]).get("viewBox") == "0 -15 890 580"


def test_default_background_is_transparent(svg):
    svg.write_text('<svg viewBox="0, -15, 890, 580"/>')
    assert converter.svg_options(svg, 890)["background_color"] is None


@pytest.mark.parametrize("width, height", [(890, 580), (445, 290), (1, 1)])
def test_custom_width_keeps_aspect_ratio(svg, width, height):
    options = converter.svg_options(svg, width)
    assert options["output_width"] == width
    assert options["output_height"] == height


@pytest.mark.parametrize("width", [0, -1])
def test_invalid_width(svg, width):
    with pytest.raises(ValueError, match="positive integer"):
        converter.svg_options(svg, width)


@pytest.mark.parametrize("viewbox", ["", "0 0 890", "0 0 0 580", "0 0 890 -580", "0 0 nan 580", "0 0 inf 580"])
def test_invalid_viewbox(svg, viewbox):
    svg.write_text(f'<svg viewBox="{viewbox}"/>')
    with pytest.raises(ValueError, match="viewBox"):
        converter.svg_options(svg, 1780)


def test_missing_viewbox(svg):
    svg.write_text("<svg/>")
    with pytest.raises(ValueError, match="viewBox"):
        converter.svg_options(svg, 1780)


def test_sources_are_relative_to_checkout(monkeypatch, tmp_path):
    render = Mock()
    monkeypatch.setattr(converter, "load_renderer", lambda: render)
    monkeypatch.chdir(tmp_path)
    outputs = converter.convert_previews(Path("previews"), width=890)
    assert len(outputs) == render.call_count == 6
    assert outputs == [Path("previews") / f"{name}.png" for name in converter.PREVIEW_NAMES]
    assert converter.CHARTS_DIR.is_absolute()
    assert Path("previews").is_dir()
    for call in render.call_args_list:
        assert call.kwargs["output_width"] == 890
        assert call.kwargs["output_height"] == 580
        assert b"<svg" in call.kwargs["bytestring"]


def test_default_destination_is_chart_directory(monkeypatch, tmp_path):
    render = Mock()
    monkeypatch.setattr(converter, "load_renderer", lambda: render)
    monkeypatch.chdir(tmp_path)
    outputs = converter.convert_previews()
    assert all(path.parent == converter.CHARTS_DIR for path in outputs)


def test_missing_input_fails_before_writing(monkeypatch, tmp_path):
    monkeypatch.setattr(converter, "CHARTS_DIR", tmp_path / "missing")
    render = Mock()
    monkeypatch.setattr(converter, "load_renderer", lambda: render)
    output = tmp_path / "output"
    with pytest.raises(FileNotFoundError):
        converter.convert_previews(output)
    render.assert_not_called()
    assert not output.exists()


def test_missing_renderer_gives_installation_hint(monkeypatch):
    monkeypatch.setitem(sys.modules, "cairosvg", None)
    with pytest.raises(RuntimeError, match="uv run --with cairosvg"):
        converter.load_renderer()


def test_cli_help_does_not_load_renderer(monkeypatch, capsys):
    loader = Mock(side_effect=AssertionError("must not import CairoSVG"))
    monkeypatch.setattr(converter, "load_renderer", loader)
    with pytest.raises(SystemExit) as exc:
        converter.main(["--help"])
    assert exc.value.code == 0
    assert "--width" in capsys.readouterr().out
    loader.assert_not_called()


@pytest.mark.parametrize("width", ["0", "-10", "not-a-number"])
def test_cli_rejects_invalid_width(width, capsys):
    with pytest.raises(SystemExit) as exc:
        converter.main(["--width", width])
    assert exc.value.code == 2
    assert "error:" in capsys.readouterr().err


def test_cli_reports_conversion_errors(monkeypatch, capsys):
    monkeypatch.setattr(converter, "convert_previews", Mock(side_effect=OSError("missing source.svg")))
    with pytest.raises(SystemExit) as exc:
        converter.main([])
    assert exc.value.code == 1
    assert "missing source.svg" in capsys.readouterr().err


def test_optional_rendering_preserves_background_and_dimensions(tmp_path):
    try:
        converter.load_renderer()
    except RuntimeError as exc:
        pytest.skip(str(exc))
    image_module = pytest.importorskip("PIL.Image")
    outputs = converter.convert_previews(tmp_path, width=445)
    for output in outputs:
        source = converter.CHARTS_DIR / output.with_suffix(".svg").name
        color = converter.svg_options(source, 445)["background_color"]
        expected_rgb = tuple(int(color[index:index + 2], 16) for index in (1, 3, 5))
        with image_module.open(output) as image:
            assert image.size == (445, 290)
            rgb = image.convert("RGB")
            assert rgb.getpixel((0, 0)) == expected_rgb
            assert any(low != high for low, high in rgb.getextrema())
            assert image.convert("RGBA").getextrema()[3] == (255, 255)


class PreviewParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.link = None
        self.images = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            self.link = attrs.get("href")
        elif tag == "img":
            self.images.append((self.link, attrs))

    def handle_endtag(self, tag):
        if tag == "a":
            self.link = None


def test_readme_grid_links_to_six_existing_pngs():
    readme = (converter.PROJECT_ROOT / "README.md").read_text()
    grid = readme.split("## Chart styles and themes\n", 1)[1].split("## Table of contents", 1)[0]
    parser = PreviewParser()
    parser.feed(grid)
    assert len(parser.images) == 6
    for (link, attrs), name in zip(parser.images, converter.PREVIEW_NAMES, strict=True):
        assert link == f"https://github.com/g-battaglia/kerykeion/blob/main/docs/charts/{name}.png"
        assert attrs["src"] == f"https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/docs/charts/{name}.png"
        assert attrs["width"] == "250"
        assert attrs["alt"]
        data = (converter.CHARTS_DIR / f"{name}.png").read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        assert struct.unpack(">II", data[16:24]) == (1780, 1160)


def test_readme_internal_links_still_resolve():
    readme = (converter.PROJECT_ROOT / "README.md").read_text()
    anchors = set()
    counts = {}
    for title in re.findall(r"^#{1,6} (.+)$", readme, re.MULTILINE):
        slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        anchors.add(f"{slug}-{count}" if count else slug)
        counts[slug] = count + 1
    assert set(re.findall(r"\]\(#([^)]*)\)", readme)) <= anchors
