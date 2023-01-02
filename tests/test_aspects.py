from kerykeion import (
    KrInstance,
    CompositeAspects,
    NatalAspects,
)


def test_natal_aspects():
    kanye = KrInstance("Kanye", 1977, 6, 8, 8, 45, "New York")
    aspects_instance = NatalAspects(kanye)
    aspects = aspects_instance.get_relevant_aspects()

    assert len(aspects) == 21

    assert aspects[0] == {
        "p1_name": "Sun",
        "p1_abs_pos": 77.59899205977428,
        "p2_name": "Moon",
        "p2_abs_pos": 346.42546949839715,
        "aspect": "square",
        "orbit": 1.1735225613771263,
        "aspect_degrees": 90,
        "color": "#dc0000",
        "aid": 5,
        "diff": 268.8264774386229,
        "p1": 0,
        "p2": 1,
    }


def test_composite_aspects():
    kanye = KrInstance("Kanye", 1977, 6, 8, 8, 45, "New York")
    jack = KrInstance("Jack", 1990, 6, 15, 13, 00, "Montichiari")

    instance = CompositeAspects(kanye, jack)
    aspects = instance.get_relevant_aspects()

    assert len(aspects) == 37
    assert aspects[0] == {
        "p1_name": "Sun",
        "p1_abs_pos": 77.59899205977428,
        "p2_name": "Sun",
        "p2_abs_pos": 84.08913890182518,
        "aspect": "conjunction",
        "orbit": 6.490146842050876,
        "aspect_degrees": 0,
        "color": "#5757e2",
        "aid": 0,
        "diff": 6.490146842050905,
        "p1": 0,
        "p2": 0,
    }
