#!/usr/bin/env python3
"""Regenerate synastry aspects (alternative version with Yoko hour=20)"""
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.aspects.aspects_factory import AspectsFactory
import json
from pathlib import Path

# Create test subjects (as in tests)
john = AstrologicalSubjectFactory.from_birth_data("John", 1940, 10, 9, 10, 30, "Liverpool", "GB", suppress_geonames_warning=True)
yoko = AstrologicalSubjectFactory.from_birth_data("Yoko", 1933, 2, 18, 20, 30, "Tokyo", "JP", suppress_geonames_warning=True)

# Create synastry aspects using the new factory
synastry_aspects = AspectsFactory.dual_chart_aspects(john, yoko)

# Generate relevant aspects
relevant = synastry_aspects.aspects

# Convert to dict format like expected file
synastry_aspects_list = []
for aspect in relevant:
    synastry_aspects_list.append({
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

print(f"Relevant aspects: {len(synastry_aspects_list)}")

# Write file
content = f"EXPECTED_RELEVANT_ASPECTS = {json.dumps(synastry_aspects_list, indent=4)}\n\n"
content += f"EXPECTED_ALL_ASPECTS = {json.dumps(synastry_aspects_list, indent=4)}\n"  # For now, use same

output_path = Path(__file__).parent.parent / "tests" / "aspects" / "expected_synastry_aspects.py"
with open(output_path, "w") as f:
    f.write(content)

print("Expected synastry aspects file regenerated successfully!")
