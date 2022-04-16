from kerykeion.fetch_geonames import FetchGeonames
from kerykeion import KrInstance, MakeSvgInstance, RelationshipScore
from logging import basicConfig

basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=10,
    force=True
)

def test_geonames():
    geonames = FetchGeonames("Roma", "IT")
    data = geonames.get_serialized_data()

    assert data["countryCode"] == "IT"
    assert data["timezonestr"] == "Europe/Rome"
    assert data["lat"] == '41.89193'
    assert data["lng"] == '12.51133'


def test_kerykeion_instace():
    object = KrInstance("Test", 1993, 10, 10, 12, 12, "London", "UK")

    assert object.sun['name'] == "Sun"
    assert object.sun['quality'] == "Cardinal"
    assert object.sun['element'] == "Air"
    assert object.sun['sign'] == "Lib"
    assert object.sun['sign_num'] == 6
    assert object.sun['position'] == 17.16206089113507
    assert object.sun['abs_pos'] == 197.16206089113507
    assert object.sun['emoji'] == "♎️"
    assert object.sun['house'] == "10th House"
    assert object.sun['retrograde'] == False


def test_birthchart_instance():
    subject = KrInstance("Test", 1993, 10, 10, 12, 12, "London", "UK")
    birthchart_svg = MakeSvgInstance(subject).makeTemplate()

    assert birthchart_svg.startswith('<?xml version="1.0" encoding="UTF-8"?>')


def test_relationship_score():
    first_subject = KrInstance("John", 1975, 10, 10, 21, 15, 'Roma', 'IT')
    second_subject = KrInstance("Sarah", 1978, 2, 9, 15, 50, 'Roma', 'IT')

    score = RelationshipScore(first_subject, second_subject)
    assert score.__dict__()['score'] == 20
    assert score.__dict__()['is_destiny_sign'] == False
    assert score.__dict__()['relevant_aspects'][0] == {
        'points': 4,
        'p1_name': 'Sun',
        'p2_name': 'Sun',
        'aspect': 'conjunction',
        'orbit': 3.6029094171302063
    }


if __name__ == "__main__":
    test_geonames()
    test_kerykeion_instace()
    test_birthchart_instance()
    test_relationship_score()
