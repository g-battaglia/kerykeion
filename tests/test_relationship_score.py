from kerykeion import (
    KrInstance,
    RelationshipScore,
)


def test_relationship_score():
    first_subject = KrInstance("John", 1975, 10, 10, 21, 15, "Roma", "IT")
    second_subject = KrInstance("Sarah", 1978, 2, 9, 15, 50, "Roma", "IT")

    score = RelationshipScore(first_subject, second_subject)
    assert score.__dict__()["score"] == 20
    assert score.__dict__()["is_destiny_sign"] == False
    assert score.__dict__()["relevant_aspects"][0] == {
        "points": 4,
        "p1_name": "Sun",
        "p2_name": "Sun",
        "aspect": "trine",
        "orbit": 3.6029094171302063,
    }
