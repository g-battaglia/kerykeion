#!/usr/bin/env python3
"""
Regenerate expected natal aspects (tests/data/expected_natal_aspects.py).

Uses the same subject parameters as tests/core/conftest.py::johnny_depp fixture:
  Johnny Depp — June 9, 1963, 00:00, Owensboro (37.7742, -87.1133), America/Chicago

Called by: poe regenerate:aspects:natal
"""

import subprocess
import sys
from pathlib import Path
from pprint import pformat

from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.aspects.aspects_factory import AspectsFactory


def regenerate_natal_aspects():
    print("Regenerating natal aspects...")

    # Match tests/core/conftest.py::johnny_depp fixture exactly
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Johnny Depp",
        1963,
        6,
        9,
        0,
        0,
        lat=37.7742,
        lng=-87.1133,
        tz_str="America/Chicago",
        online=False,
        suppress_geonames_warning=True,
    )

    natal_aspects = AspectsFactory.single_chart_aspects(subject)

    # Convert to dict format (full model_dump)
    all_aspects = [a.model_dump() for a in natal_aspects.aspects]

    print(f"Aspects: {len(all_aspects)}")

    # Generate file
    # Note: AspectsFactory.single_chart_aspects().aspects already returns filtered
    # (relevant) aspects, so ALL and RELEVANT are the same dataset.
    aspects_literal = pformat(all_aspects, width=100, sort_dicts=False)
    content = f"EXPECTED_ALL_ASPECTS = {aspects_literal}\n\n"
    content += f"EXPECTED_RELEVANT_ASPECTS = {aspects_literal}\n"

    output_path = Path(__file__).parent.parent / "tests" / "data" / "expected_natal_aspects.py"
    output_path.write_text(content)

    # Format with ruff for consistent style (adds trailing commas, etc.)
    subprocess.run(
        [sys.executable, "-m", "ruff", "format", str(output_path)],
        check=True,
    )

    print(f"✓ Created {output_path.name}")


if __name__ == "__main__":
    regenerate_natal_aspects()
    print("✅ Expected natal aspects file updated!")
