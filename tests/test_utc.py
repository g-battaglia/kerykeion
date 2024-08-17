from kerykeion.astrological_subject import AstrologicalSubject
from datetime import datetime


def test_utc_constructor():
    subject = AstrologicalSubject(
        "Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", geonames_username="century.boy")

    subject2 = AstrologicalSubject.get_from_iso_utc_time(
        "Johnny Depp", "1963-06-09T05:00:00Z", "Owensboro", "US", online=True)

    assert subject.julian_day == subject2.julian_day
    assert subject._houses_list == subject2._houses_list
    assert subject.planets_list == subject2.planets_list


if __name__ == "__main__":
    from kerykeion.utilities import setup_logging
    setup_logging(level="debug")
    test_utc_constructor()
