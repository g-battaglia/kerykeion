from json import loads
from re import sub
from kerykeion.fetch_geonames import FetchGeonames
from kerykeion import KrInstance, MakeSvgInstance, RelationshipScore, NatalAspects, CompositeAspects, Report
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
    object = KrInstance("Test", 1993, 10, 10, 12, 12, "London", "GB")

    assert object.sun.name == "Sun"
    assert object.sun.quality == "Cardinal"
    assert object.sun.element == "Air"
    assert object.sun.sign == "Lib"
    assert object.sun.sign_num == 6
    assert object.sun.position == 17.16206089113507
    assert object.sun.abs_pos == 197.16206089113507
    assert object.sun.emoji == "♎️"
    assert object.sun.house == "Tenth House"
    assert object.sun.retrograde == False
    assert object.sun.point_type == "Planet"

    object = KrInstance("Test", 1993, 10, 10, 12, 12, "Roma", "IT")

    assert object.city == "Roma"
    assert object.nation == "IT"

    object = KrInstance("Test", 1993, 10, 10, 12, 12, lng=2.1, lat=2.1, tz_str='Europe/Rome')

    assert object.lng == 2.1
    assert object.lat == 2.1

def test_composite_aspects():
    kanye = KrInstance("Kanye", 1977, 6, 8, 8, 45, "New York")
    jack = KrInstance("Jack", 1990, 6, 15, 13, 00, "Montichiari")

    instance = CompositeAspects(kanye, jack)
    aspects = instance.get_relevant_aspects()

    assert len(aspects) == 37
    assert aspects[0] == {
        'p1_name': 'Sun',
        'p1_abs_pos': 77.59899205977428,
        'p2_name': 'Sun',
        'p2_abs_pos': 84.08913890182518,
        'aspect': 'conjunction',
        'orbit': 6.490146842050876,
        'aspect_degrees': 0,
        'color': '#5757e2',
        'aid': 0,
        'diff': 6.490146842050905,
        'p1': 0, 'p2': 0
    }


def test_birthchart_instance():
    subject = KrInstance("Test", 1993, 10, 10, 12, 12, "London", "GB")
    birthchart_svg = MakeSvgInstance(subject).makeTemplate()

    assert birthchart_svg.startswith("<?xml version='1.0' encoding='UTF-8'?>")


def test_composite_chart_instance():
    # TODO: Improve with bs4
    first_subject = KrInstance("John", 1975, 10, 10, 21, 15, 'Roma', 'IT')
    second_subject = KrInstance("Sarah", 1978, 2, 9, 15, 50, 'Roma', 'IT')
    birthchart_instance = MakeSvgInstance(
        first_subject, 'Composite', second_subject)
    template = birthchart_instance.makeTemplate()

    assert birthchart_instance.chart_type == 'Composite'
    assert template.startswith("<?xml version='1.0' encoding='UTF-8'?>")


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
        'aspect': 'trine',
        'orbit': 3.6029094171302063
    }

def test_print_report():
    subject = KrInstance("John", 1975, 10, 10, 21, 15, 'Roma', 'IT')
    report = Report(subject)

    assert report.report_title == "\n+- Kerykeion report for John -+"


if __name__ == "__main__":
    test_geonames()
    test_kerykeion_instace()
    test_birthchart_instance()
    test_composite_aspects()
    test_relationship_score()
    test_composite_chart_instance()
    test_print_report()
