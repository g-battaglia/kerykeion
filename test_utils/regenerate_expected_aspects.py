#!/usr/bin/env python3
"""
Script per rigenerare gli expected aspects files
con i nuovi punti attivi (Descendant, Imum_Coeli, entrambi i tipi di nodi)
"""

from kerykeion import AstrologicalSubjectFactory, NatalAspects, SynastryAspects
import json
from pathlib import Path

def regenerate_natal_aspects():
    print("Rigenerando natal aspects...")
    # Usa gli stessi dati del test
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US",
        geonames_username="century.boy"
    )

    natal_aspects = NatalAspects(subject)

    # Converti in dict format
    relevant_aspects = [a.model_dump() for a in natal_aspects.relevant_aspects]
    all_aspects = [a.model_dump() for a in natal_aspects.all_aspects]

    print(f"Relevant aspects: {len(relevant_aspects)}")
    print(f"All aspects: {len(all_aspects)}")

    # Genera il file
    content = f"""EXPECTED_ALL_ASPECTS = {json.dumps(all_aspects, indent=4)}

EXPECTED_RELEVANT_ASPECTS = {json.dumps(relevant_aspects, indent=4)}
"""

    # Usa path relativo
def regenerate_synastry_aspects():
    print("Rigenerando synastry aspects...")

    # Usa gli stessi dati del test synastry (nota: Yoko ora=10, non 20)
    john = AstrologicalSubjectFactory.from_birth_data(
        "John", 1940, 10, 9, 10, 30, "Liverpool", "GB",
        geonames_username="century.boy"
    )
    yoko = AstrologicalSubjectFactory.from_birth_data(
        "Yoko", 1933, 2, 18, 10, 30, "Tokyo", "JP",
        geonames_username="century.boy"
    )

    synastry_aspects = SynastryAspects(john, yoko)

    # Converti in dict format con i campi p1/p2
    relevant_aspects = []
    for aspect in synastry_aspects.relevant_aspects:
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

    all_aspects = relevant_aspects  # Usa gli stessi per entrambi

    print(f"Relevant aspects: {len(relevant_aspects)}")
    print(f"All aspects: {len(all_aspects)}")

    # Genera il file
    content = f"""EXPECTED_ALL_ASPECTS = {json.dumps(all_aspects, indent=4)}

EXPECTED_RELEVANT_ASPECTS = {json.dumps(relevant_aspects, indent=4)}
"""

    # Usa path relativo
    output_path = Path(__file__).parent.parent / "tests" / "aspects" / "expected_synastry_aspects.py"
    with open(output_path, "w") as f:
        f.write(content)

    print("✓ Creato expected_synastry_aspects.py")

if __name__ == "__main__":
    regenerate_natal_aspects()
    regenerate_synastry_aspects()
    print("✅ Tutti i file expected aspects aggiornati!")

    print("✓ Nato expected_synastry_aspects.py")

if __name__ == "__main__":
    regenerate_natal_aspects()
    regenerate_synastry_aspects()
    print("✅ Tutti i file expected aspects aggiornati!")
