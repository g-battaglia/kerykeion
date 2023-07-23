from kerykeion import AstrologicalSubject, RelationshipScore


# TODO: Extend this test to cover all
def test_relationship_score():
    first_subject = AstrologicalSubject("John", 1975, 10, 10, 21, 15, "Roma", "IT")
    second_subject = AstrologicalSubject("Sarah", 1978, 2, 9, 15, 50, "Roma", "IT")

    score = RelationshipScore(first_subject, second_subject)
    assert score.__dict__()["score"] == 20
    assert score.__dict__()["is_destiny_sign"] == False
    assert score.__dict__()["relevant_aspects"][0]["points"] == 4
    assert score.__dict__()["relevant_aspects"][0]["p1_name"] == "Sun"
    assert score.__dict__()["relevant_aspects"][0]["p2_name"] == "Sun"
    assert score.__dict__()["relevant_aspects"][0]["aspect"] == "trine"
    assert round(score.__dict__()["relevant_aspects"][0]["orbit"], 2) == 3.60


if __name__ == "__main__":
    test_relationship_score()
