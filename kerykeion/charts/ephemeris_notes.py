"""Optional SVG notes derived from existing subject provenance, without calculations."""

from collections.abc import Callable, Iterable
from html import escape
import re
from typing import Any

from kerykeion.charts.glyph_metrics import estimate_text_width


def collect_ephemeris_notes(subjects: Iterable[Any], translate: Callable[[str, str], str]) -> list[str]:
    """Describe omitted and approximate points without changing their models.

    Args:
        subjects: Subjects represented by the chart, including composite parents.
        translate: The drawer's translation lookup with an English fallback.

    Returns:
        Ordered, subject-labelled notes. Unknown precision classes imply nothing.
    """
    notes: list[str] = []
    seen: set[int] = set()

    def point_label(name: str) -> str:
        return translate(f"celestial_points.{name}", name.replace("_", " "))

    def visit(subject: Any) -> None:
        if subject is None or id(subject) in seen:
            return
        seen.add(id(subject))
        missing = list(dict.fromkeys(w.point_name for w in getattr(subject, "ephemeris_warnings", ())))
        points = [getattr(subject, name.lower(), None) for name in getattr(subject, "active_points", ())]
        points.extend(getattr(subject, "fixed_stars", ()))
        approximate = list(dict.fromkeys(
            point.name for point in points
            if point is not None and point.precision_class == "approximate"
        ))
        for names, key, fallback in (
            (missing, "ephemeris_omitted_points", "Unavailable points"),
            (approximate, "ephemeris_approximate_positions", "Approximate positions"),
        ):
            if names:
                label = translate(key, fallback)
                notes.append(f"{subject.name} — {label}: {', '.join(map(point_label, names))}.")
        # A composite may retain its inputs' limitations only on its parents.
        for attribute in ("first_subject", "second_subject"):
            visit(getattr(subject, attribute, None))

    for subject in subjects:
        visit(subject)
    return notes


def _wrap_note(text: str, width: float, font_size: float) -> list[str]:
    """Wrap all text to measured width, splitting even a single overlong name."""
    lines: list[str] = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}" if line else word
        if estimate_text_width(candidate, font_size) <= width:
            line = candidate
            continue
        if line:
            lines.append(line)
        line = ""
        for character in word:
            if line and estimate_text_width(line + character, font_size) > width:
                lines.append(line)
                line = ""
            line += character
    if line:
        lines.append(line)
    return lines


def append_ephemeris_notes(svg: str, notes: list[str]) -> str:
    """Append an accessible footer while preserving every original drawing element.

    Args:
        svg: A complete, unminified SVG emitted by a chart renderer.
        notes: Plain-text provenance notes; an empty list leaves the bytes intact.

    Returns:
        SVG with a taller viewBox, a footer and an expanded accessible description.
        Font size follows the viewBox scale, including the modern 100-unit wheel.
    """
    if not notes:
        return svg
    root = re.search(r"<svg\b[^>]*>", svg)
    if root is None:
        raise ValueError("Chart SVG has no root element")
    box = re.search(r"\bviewBox=([\"'])([^\"']+)\1", root.group())
    if box is None:
        raise ValueError("Chart SVG has no viewBox")
    coordinates = box[2].split()
    left, top, width, height = map(float, coordinates)
    # Keep notes readable in both full sheets and tight partial exports.
    font_size = min(10.0, width / 40.0)
    margin = font_size * 2
    line_height = font_size * 1.5
    lines = [line for note in notes for line in _wrap_note(note, width - 2 * margin, font_size)]
    new_height = height + 2 * margin + line_height * len(lines)
    updated_root = root.group()[:box.start(2)] + " ".join((*coordinates[:3], str(new_height))) + root.group()[box.end(2):]
    svg = svg[:root.start()] + updated_root + svg[root.end():]
    description = escape(" ".join(notes), quote=True)
    svg = re.sub(r"(</desc\s*>)", lambda match: " " + description + match[0], svg, count=1)
    rows = "".join(
        f'<text x="{left + margin:g}" y="{top + height + margin + line_height * (index + 1):g}">'
        f'{escape(line, quote=True)}</text>'
        for index, line in enumerate(lines)
    )
    footer = (
        f'<g kr:node="Ephemeris_Notes" font-size="{font_size:g}" '
        f'fill="var(--kerykeion-chart-color-paper-0)">{rows}</g>'
    )
    closing = svg.rfind("</svg>")
    if closing < 0:
        raise ValueError("Chart SVG has no closing root element")
    return svg[:closing] + footer + svg[closing:]
