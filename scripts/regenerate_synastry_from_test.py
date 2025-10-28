#!/usr/bin/env python3
"""Regenerate synastry aspects with exact test parameters"""
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.aspects.aspects_factory import AspectsFactory
import json
from pathlib import Path

# Setup exactly like test (note: Yoko hour is 10 not 20!)
first_subject = AstrologicalSubjectFactory.from_birth_data("John", 1940, 10, 9, 10, 30, "Liverpool", "GB", suppress_geonames_warning=True)
second_subject = AstrologicalSubjectFactory.from_birth_data("Yoko", 1933, 2, 18, 10, 30, "Tokyo", "JP", suppress_geonames_warning=True)
synastry_aspects = AspectsFactory.dual_chart_aspects(first_subject, second_subject)

synastry_relevant_aspects = synastry_aspects.aspects

print(f"Relevant aspects count: {len(synastry_relevant_aspects)}")

# Generate expected file based on current aspects
synastry_aspects_list = []
for aspect in synastry_relevant_aspects:
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

# Write file
content = f"EXPECTED_RELEVANT_ASPECTS = {json.dumps(synastry_aspects_list, indent=4)}\n\n"
content += f"EXPECTED_ALL_ASPECTS = {json.dumps(synastry_aspects_list, indent=4)}\n"

output_path = Path(__file__).parent.parent / "tests" / "aspects" / "expected_synastry_aspects.py"
with open(output_path, "w") as f:
    f.write(content)

print(f"Synastry aspects regenerated with {len(synastry_aspects_list)} aspects!")
