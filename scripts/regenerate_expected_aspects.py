#!/usr/bin/env python3
"""
Script to regenerate expected aspects files
with new active points (Descendant, Imum_Coeli, both node types)
"""

from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.aspects.aspects_factory import AspectsFactory
import json
from pathlib import Path

def regenerate_natal_aspects():
    print("Regenerating natal aspects...")
    # Use same test data
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US",
        suppress_geonames_warning=True
    )

    natal_aspects = AspectsFactory.single_chart_aspects(subject)

    # Convert to dict format
    relevant_aspects = [a.model_dump() for a in natal_aspects.aspects]
    all_aspects = [a.model_dump() for a in natal_aspects.aspects]

    print(f"Relevant aspects: {len(relevant_aspects)}")
    print(f"All aspects: {len(all_aspects)}")

    # Generate file
    content = f"""EXPECTED_ALL_ASPECTS = {json.dumps(all_aspects, indent=4)}

EXPECTED_RELEVANT_ASPECTS = {json.dumps(relevant_aspects, indent=4)}
"""

    # Use relative path
    output_path = Path(__file__).parent.parent / "tests" / "aspects" / "expected_natal_aspects.py"
    with open(output_path, "w") as f:
        f.write(content)

    print("✓ Created expected_natal_aspects.py")

def regenerate_synastry_aspects():
    print("Regenerating synastry aspects...")

    # Use same test synastry data (note: Yoko hour=10, not 20)
    john = AstrologicalSubjectFactory.from_birth_data(
        "John", 1940, 10, 9, 10, 30, "Liverpool", "GB",
        suppress_geonames_warning=True
    )
    yoko = AstrologicalSubjectFactory.from_birth_data(
        "Yoko", 1933, 2, 18, 10, 30, "Tokyo", "JP",
        suppress_geonames_warning=True
    )

    synastry_aspects = AspectsFactory.dual_chart_aspects(john, yoko)

    # Convert to dict format with p1/p2 fields
    relevant_aspects = []
    for aspect in synastry_aspects.aspects:
        relevant_aspects.append({
            "p1_name": aspect.p1_name,
            "p1_abs_pos": aspect.p1_abs_pos,
            "p2_name": aspect.p2_name,
            "p2_abs_pos": aspect.p2_abs_pos,
            "aspect": aspect.aspect,
            "orbit": aspect.orbit,
            "aspect_degrees": aspect.aspect_degrees,
            "diff": aspect.diff,
            "p1": aspect.p1,
            "p2": aspect.p2
        })

    all_aspects = relevant_aspects  # Use same for both

    print(f"Relevant aspects: {len(relevant_aspects)}")
    print(f"All aspects: {len(all_aspects)}")

    # Generate file
    content = f"""EXPECTED_ALL_ASPECTS = {json.dumps(all_aspects, indent=4)}

EXPECTED_RELEVANT_ASPECTS = {json.dumps(relevant_aspects, indent=4)}
"""

    # Use relative path
    output_path = Path(__file__).parent.parent / "tests" / "aspects" / "expected_synastry_aspects.py"
    with open(output_path, "w") as f:
        f.write(content)

    print("✓ Created expected_synastry_aspects.py")

if __name__ == "__main__":
    regenerate_natal_aspects()
    regenerate_synastry_aspects()
    print("✅ All expected aspects files updated!")
