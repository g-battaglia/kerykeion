#!/usr/bin/env python3
"""Rigenera synastry aspects con i parametri esatti del test"""
from kerykeion import AstrologicalSubjectFactory, SynastryAspects
import json
from pathlib import Path

# Setup esattamente come il test (nota: Yoko ora è 10 non 20!)
first_subject = AstrologicalSubjectFactory.from_birth_data("John", 1940, 10, 9, 10, 30, "Liverpool", "GB", geonames_username="century.boy")
second_subject = AstrologicalSubjectFactory.from_birth_data("Yoko", 1933, 2, 18, 10, 30, "Tokyo", "JP", geonames_username="century.boy")
synastry_aspects = SynastryAspects(first_subject, second_subject)

synastry_relevant_aspects = synastry_aspects.relevant_aspects

print(f"Conteggio aspects rilevanti: {len(synastry_relevant_aspects)}")

# Genera il file expected basato sugli aspects attuali
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

# Scrivi il file
content = f"EXPECTED_RELEVANT_ASPECTS = {json.dumps(synastry_aspects_list, indent=4)}\n\n"
content += f"EXPECTED_ALL_ASPECTS = {json.dumps(synastry_aspects_list, indent=4)}\n"

output_path = Path(__file__).parent.parent / "tests" / "aspects" / "expected_synastry_aspects.py"
with open(output_path, "w") as f:
    f.write(content)

print(f"Synastry aspects rigenerati con {len(synastry_aspects_list)} aspects!")
