"""Compare deterministic output hashes before and after a performance change.

Run on the base checkout first, then on the candidate using the same hash file:
    uv run python scripts/compare_performance_outputs.py /tmp/kerykeion-outputs.json
A missing hash file is created; an existing one is checked byte for byte through
SHA-256 digests. Uses offline inputs and the current backend/tier throughout.
"""

import hashlib
import itertools
import json
import logging
import argparse
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory as S, ChartDataFactory as C, ChartDrawer as D
from kerykeion.astro_cartography import AstroCartographyFactory
from kerykeion.composite_subject import CompositeSubjectFactory
from kerykeion.planetary_returns import PlanetaryReturnFactory
from kerykeion.secondary_progressions import SecondaryProgressionFactory
from kerykeion.settings.translation_strings import LANGUAGE_SETTINGS


def subject(name="John", **kwargs):
    return S.from_birth_data(
        name,
        1940,
        10,
        9,
        18,
        30,
        lat=53.41058,
        lng=-2.97794,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
        **kwargs,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hash_file", type=Path)
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)

    a = subject()
    b = S.from_birth_data(
        "Paul",
        1942,
        6,
        18,
        15,
        30,
        lat=53.41058,
        lng=-2.97794,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
    )
    r = PlanetaryReturnFactory(
        a, lat=53.41058, lng=-2.97794, tz_str="Europe/London", online=False
    ).next_return_from_iso_formatted_time("2026-01-01T00:00:00+00:00", return_type="Solar")
    charts = [
        C.create_chart_data("Natal", a),
        C.create_chart_data("Synastry", a, b),
        C.create_chart_data("Transit", a, b),
        C.create_composite_chart_data(CompositeSubjectFactory(a, b).get_midpoint_composite_subject_model()),
        C.create_chart_data("SingleReturnChart", r),
        C.create_chart_data("DualReturnChart", a, r),
        C.create_progression_chart_data(a, SecondaryProgressionFactory.compute(a, target_year=2026)),
    ]

    charts += [
        C.create_chart_data("Natal", subject(calculate_gauquelin=True)),
        C.create_chart_data("Natal", subject(zodiac_type="Sidereal", sidereal_mode="LAHIRI")),
    ]
    results = {}

    def save(key, obj):
        text = obj if isinstance(obj, str) else json.dumps(obj, sort_keys=True)
        results[str(key)] = hashlib.sha256(text.encode()).hexdigest()

    for i, data in enumerate(charts):
        for style, language, size in itertools.product(
            ("classic", "modern"), LANGUAGE_SETTINGS, ("small", "medium", "large")
        ):
            drawer = D(
                data, chart_language=language, glyph_size=size, show_motion_state=True, show_aspect_movement=True
            )
            for kind, method in [
                ("full", drawer.generate_svg_string),
                ("wheel", drawer.generate_wheel_only_svg_string),
            ]:
                save((i, style, language, size, kind), method(style=style))
            if style == "modern":
                save((i, language, size, "grid"), drawer.generate_aspect_grid_only_svg_string())
        for theme, inline, minify in itertools.product(
            ("classic", "dark", "black-and-white"), (False, True), (False, True)
        ):
            drawer = D(data, theme=theme, transparent_background=True)
            save((i, theme, inline, minify), drawer.generate_svg_string(remove_css_variables=inline, minify=minify))
        save((i, "data"), data.model_dump(mode="json"))
    for step, lat_range in [(1, (-66, 66)), (0.1, (-66, 66)), (0.7, (-89.9, 89.9))]:
        save(
            ("acg", step, lat_range),
            [x.model_dump() for x in AstroCartographyFactory.compute(a, step=step, lat_range=lat_range)],
        )
    path = args.hash_file
    if path.exists():
        before = json.loads(path.read_text())
        diffs = sorted(k for k in before.keys() | results.keys() if before.get(k) != results.get(k))
        print(f"{len(results)} comparisons, {len(diffs)} mismatches")
        print(diffs[:20])
        if diffs:
            raise SystemExit(1)
    else:
        path.write_text(json.dumps(results))
        print(f"Saved {len(results)} baseline hashes")


if __name__ == "__main__":
    main()
