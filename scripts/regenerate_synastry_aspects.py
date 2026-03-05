#!/usr/bin/env python3
"""
Regenerate expected synastry aspects (tests/data/expected_synastry_aspects.py).

Uses the same subject parameters as tests/core/conftest.py fixtures:
  John Lennon — October 9, 1940, 18:30, Liverpool (53.4084, -2.9916), Europe/London
  Yoko Ono   — February 18, 1933, 20:30, Tokyo (35.6762, 139.6503), Asia/Tokyo

Called by: poe regenerate:aspects:synastry
"""

import subprocess
import sys
from pathlib import Path
from pprint import pformat

from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.aspects.aspects_factory import AspectsFactory


def regenerate_synastry_aspects():
    print("Regenerating synastry aspects...")

    # Match tests/core/conftest.py::john_lennon fixture exactly
    john = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon",
        1940,
        10,
        9,
        18,
        30,
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
    )

    # Match tests/core/conftest.py::yoko_ono fixture exactly
    yoko = AstrologicalSubjectFactory.from_birth_data(
        "Yoko Ono",
        1933,
        2,
        18,
        20,
        30,
        lat=35.6762,
        lng=139.6503,
        tz_str="Asia/Tokyo",
        online=False,
        suppress_geonames_warning=True,
    )

    synastry_aspects = AspectsFactory.dual_chart_aspects(john, yoko)

    # Convert to dict format (full model_dump for completeness)
    all_aspects = [a.model_dump() for a in synastry_aspects.aspects]

    print(f"Aspects: {len(all_aspects)}")

    # Generate file (EXPECTED_RELEVANT_ASPECTS first to match existing layout)
    # Note: AspectsFactory.dual_chart_aspects().aspects already returns filtered
    # (relevant) aspects, so ALL and RELEVANT are the same dataset.
    aspects_literal = pformat(all_aspects, width=100, sort_dicts=False)
    content = f"EXPECTED_RELEVANT_ASPECTS = {aspects_literal}\n\n"
    content += f"EXPECTED_ALL_ASPECTS = {aspects_literal}\n"

    output_path = Path(__file__).parent.parent / "tests" / "data" / "expected_synastry_aspects.py"
    output_path.write_text(content, encoding="utf-8")

    # Format with ruff for consistent style (adds trailing commas, etc.)
    subprocess.run(
        [sys.executable, "-m", "ruff", "format", str(output_path)],
        check=True,
    )

    print(f"✓ Created {output_path.name}")


if __name__ == "__main__":
    regenerate_synastry_aspects()
    print("✅ Expected synastry aspects file updated!")
