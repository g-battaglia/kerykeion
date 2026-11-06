"""The opt-in footer must disclose limitations without changing the drawing."""

import xml.etree.ElementTree as ET
from types import SimpleNamespace

import pytest

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
from kerykeion.charts.ephemeris_notes import NOTE_LABELS, collect_ephemeris_notes
from kerykeion.charts.glyph_metrics import estimate_text_width
from kerykeion.schemas.models import EphemerisWarningModel
from kerykeion.settings.translation_strings import LANGUAGE_SETTINGS
from kerykeion.settings.chart_defaults import DEFAULT_CHART_COLORS


NS = {"s": "http://www.w3.org/2000/svg"}
KR = "{https://www.kerykeion.net/}node"
VARIANTS = ("generate_svg_string", "generate_wheel_only_svg_string", "generate_aspect_grid_only_svg_string")


@pytest.fixture(scope="module")
def complete_subject():
    """Build a deterministic subject without optional-point limitations."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Notes", 1990, 7, 21, 12, 0, lat=51.5, lng=0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, calculate_lunar_phase=False,
        active_points=["Sun", "Moon", "Chiron"],
    )


@pytest.fixture
def limited_subject(complete_subject):
    """Copy a subject with one omitted and one approximate point."""
    subject = complete_subject.model_copy(deep=True)
    subject.chiron = None
    subject.active_points.remove("Chiron")
    subject.ephemeris_warnings = [EphemerisWarningModel(
        point_name="Chiron", body_id=15, requested_jd=subject.julian_day,
        code="ephemeris_calculation_failed", message="Optional point omitted.",
    )]
    subject.moon.precision_class = "approximate"
    subject.sun.precision_class = "unverified-local"
    return subject


def render(subject, style, variant, **options):
    """Render the selected export with explicit note options."""
    drawer = ChartDrawer(ChartDataFactory.create_natal_chart_data(subject), style=style, **options)
    return getattr(drawer, variant)()


@pytest.mark.parametrize("style", ["classic", "modern"])
@pytest.mark.parametrize("variant", VARIANTS)
def test_default_and_explicit_false_preserve_bytes(complete_subject, limited_subject, style, variant):
    """Default exports remain byte-identical when provenance notes are disabled."""
    for subject in (complete_subject, limited_subject):
        assert render(subject, style, variant) == render(subject, style, variant, show_ephemeris_notes=False)
    assert render(complete_subject, style, variant) == render(
        complete_subject, style, variant, show_ephemeris_notes=True
    )


@pytest.mark.parametrize("style", ["classic", "modern"])
@pytest.mark.parametrize("variant", VARIANTS)
def test_footer_keeps_geometry_and_identifies_both_limitations(limited_subject, style, variant):
    """Notes preserve original drawing geometry and the input model."""
    before_model = limited_subject.model_dump()
    original = ET.fromstring(render(limited_subject, style, variant))
    annotated = ET.fromstring(render(limited_subject, style, variant, show_ephemeris_notes=True))
    original_box = original.attrib["viewBox"].split()
    updated_box = annotated.attrib["viewBox"].split()
    assert list(map(float, original_box[:3])) == list(map(float, updated_box[:3]))
    assert float(updated_box[3]) > float(original_box[3])
    footer = next(node for node in annotated if node.get(KR) == "Ephemeris_Notes")
    text = " ".join(footer.itertext())
    assert "Unavailable points: Chiron" in text
    assert "Approximate positions: Moon" in text
    assert "Sun" not in text  # Unreviewed does not mean approximate.
    assert "Unavailable points: Chiron" in annotated.find("s:desc", NS).text
    for row in footer:
        assert float(row.get("y")) > float(original_box[1]) + float(original_box[3])
    annotated.remove(footer)
    annotated.set("viewBox", original.attrib["viewBox"])
    annotated.find("s:desc", NS).text = original.find("s:desc", NS).text
    assert ET.tostring(annotated) == ET.tostring(original)
    assert limited_subject.model_dump() == before_model


@pytest.mark.parametrize("variant", VARIANTS)
def test_footer_uses_custom_chart_text_color(limited_subject, variant):
    """A custom palette must apply to provenance text as well as chart labels."""
    root = ET.fromstring(render(limited_subject, "classic", variant,
                               show_ephemeris_notes=True,
                               colors_settings={**DEFAULT_CHART_COLORS, "paper_0": "#abcdef"}))
    footer = next(node for node in root if node.get(KR) == "Ephemeris_Notes")
    assert footer.get("fill") == "#abcdef"


@pytest.mark.parametrize("language", LANGUAGE_SETTINGS)
def test_notes_use_chart_translations(limited_subject, language):
    """Every chart language translates the two provenance categories."""
    root = ET.fromstring(render(limited_subject, "modern", VARIANTS[0],
                               show_ephemeris_notes=True, chart_language=language))
    footer = next(node for node in root if node.get(KR) == "Ephemeris_Notes")
    text = " ".join(footer.itertext())
    assert NOTE_LABELS[language][0] in text
    assert NOTE_LABELS[language][1] in text


@pytest.mark.parametrize("theme", ["classic", "dark", "black-and-white"])
@pytest.mark.parametrize("variant", VARIANTS)
def test_long_untrusted_text_wraps_and_survives_minification(limited_subject, theme, variant):
    """Untrusted notes remain wrapped, escaped and intact after minification."""
    limited_subject.name = '<script>alert("&")</script> ' + "W" * 200
    drawer = ChartDrawer(ChartDataFactory.create_natal_chart_data(limited_subject),
                         theme=theme, show_ephemeris_notes=True, transparent_background=True)
    raw = ET.fromstring(getattr(drawer, variant)())
    compact = ET.fromstring(getattr(drawer, variant)(minify=True, remove_css_variables=True))
    footer = next(node for node in raw if node.get(KR) == "Ephemeris_Notes")
    compact_footer = next(node for node in compact if node.get(KR) == "Ephemeris_Notes")
    assert [row.text for row in footer] == [row.text for row in compact_footer]
    assert raw.findall(".//s:script", NS) == []
    assert compact.findall(".//s:script", NS) == []
    width = float(raw.attrib["viewBox"].split()[2])
    font_size = float(footer.get("font-size"))
    assert all(estimate_text_width(row.text, font_size) <= width - 4 * font_size + 1e-6 for row in footer)
    assert all("var(" not in value for node in compact_footer.iter() for value in node.attrib.values())


def test_dual_chart_and_composite_inputs_keep_subject_identity(limited_subject, complete_subject):
    """Dual and composite notes retain subject ownership without duplicates."""
    other = complete_subject.model_copy(deep=True)
    other.name = "Second"
    other.moon.precision_class = "approximate"
    data = ChartDataFactory.create_synastry_chart_data(limited_subject, other)
    root = ET.fromstring(ChartDrawer(data, show_ephemeris_notes=True).generate_svg_string())
    text = " ".join(next(node for node in root if node.get(KR) == "Ephemeris_Notes").itertext())
    assert "Notes — Unavailable points" in text and "Second — Approximate positions" in text
    composite = SimpleNamespace(name="Composite", first_subject=limited_subject, second_subject=other)
    notes = collect_ephemeris_notes([composite, other], lambda key, fallback: fallback)
    assert len(notes) == 3
    assert sum(note.startswith("Second") for note in notes) == 1


def test_custom_translation_and_repeated_exports(limited_subject):
    """Custom labels survive repeated exports without changing drawer state."""
    drawer = ChartDrawer(ChartDataFactory.create_natal_chart_data(limited_subject), show_ephemeris_notes=True,
                         language_pack={"ephemeris_omitted_points": "Missing locally"})
    first = drawer.generate_svg_string()
    drawer.generate_wheel_only_svg_string()
    drawer.generate_aspect_grid_only_svg_string()
    assert drawer.generate_svg_string() == first
    assert "Missing locally" in first


def test_cli_render_option_reaches_drawer(limited_subject):
    """The CLI note flag reaches the shared chart renderer."""
    from kerykeion_cli.commands._shared import _render_options, _RENDER_FLAGS
    from kerykeion_cli.rendering import render_svg

    flags = dict.fromkeys(_RENDER_FLAGS)
    flags["show_ephemeris_notes"] = True
    options = _render_options(flags)
    assert options.chart_kwargs()["show_ephemeris_notes"] is True
    result = render_svg(ChartDataFactory.create_natal_chart_data(limited_subject), options)
    assert "Ephemeris_Notes" in result


def test_custom_note_label_must_be_text(complete_subject):
    """Non-text translation overrides fail at chart construction."""
    with pytest.raises(ValueError, match="ephemeris_omitted_points must be a string"):
        ChartDrawer(ChartDataFactory.create_natal_chart_data(complete_subject),
                    language_pack={"ephemeris_omitted_points": 42})


@pytest.mark.parametrize("note,expected", [("Missing\x01 point", "Missing point"), ("Literal var(--paper_0)", "Literal var(--paper_0)")])
def test_note_text_stays_xml_safe_and_literal_during_css_inlining(note, expected):
    """XML controls are removed while literal CSS-looking note text survives."""
    from kerykeion.charts.ephemeris_notes import append_ephemeris_notes
    from kerykeion.utilities.core import inline_css_variables_in_svg

    svg = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:kr="https://www.kerykeion.net/" viewBox="0 0 500 500"><style>:root { --paper_0: #123456; }</style><desc>Chart</desc></svg>'
    annotated = append_ephemeris_notes(svg, [note], "var(--paper_0)")
    root = ET.fromstring(inline_css_variables_in_svg(annotated))
    footer = next(node for node in root if node.get(KR) == "Ephemeris_Notes")
    assert " ".join(footer.itertext()) == expected
    assert expected in root.find("s:desc", NS).text
    assert footer.get("fill") == "#123456"


def test_approximate_active_midpoints_are_disclosed_without_mutation():
    """The optional footer includes approximate midpoint provenance once."""
    midpoint = SimpleNamespace(name="Sun_Moon", precision_class="approximate")
    subject = SimpleNamespace(name="Midpoint subject", active_midpoints=[midpoint, midpoint])
    assert collect_ephemeris_notes([subject], lambda key, fallback: fallback) == [
        "Midpoint subject — Approximate positions: Sun Moon."
    ]
    assert subject.active_midpoints == [midpoint, midpoint]


@pytest.mark.parametrize("inline", [False, True])
@pytest.mark.parametrize("variant", VARIANTS[1:])
@pytest.mark.parametrize("style", ["classic", "modern"])
def test_minified_partial_footer_remains_inside_viewbox_with_its_text_color(limited_subject, inline, variant, style):
    """Transparent partial exports keep footer baselines and configured fill."""
    drawer = ChartDrawer(ChartDataFactory.create_natal_chart_data(limited_subject),
                         style=style, transparent_background=True, show_ephemeris_notes=True,
                         colors_settings={**DEFAULT_CHART_COLORS, "paper_0": "#abcdef"})
    root = ET.fromstring(getattr(drawer, variant)(minify=True, remove_css_variables=inline))
    footer = next(node for node in root if node.get(KR) == "Ephemeris_Notes")
    left, top, width, height = map(float, root.attrib["viewBox"].split())
    assert footer.get("fill") == "#abcdef"
    for row in footer:
        assert top < float(row.get("y")) < top + height
        assert left <= float(row.get("x")) < left + width
