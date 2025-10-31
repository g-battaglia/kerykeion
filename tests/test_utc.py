from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory


def test_utc_constructor():
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", suppress_geonames_warning=True)

    subject2 = AstrologicalSubjectFactory.from_iso_utc_time(
        "Johnny Depp", "1963-06-09T05:00:00+00:00", "Owensboro", "US", online=True)

    assert subject.julian_day == subject2.julian_day
    assert subject.sun == subject2.sun
    assert subject.moon == subject2.moon
    assert subject.mercury == subject2.mercury
    assert subject.venus == subject2.venus
    assert subject.mars == subject2.mars
    assert subject.jupiter == subject2.jupiter
    assert subject.saturn == subject2.saturn
    assert subject.uranus == subject2.uranus
    assert subject.neptune == subject2.neptune
    assert subject.pluto == subject2.pluto
    assert subject.chiron == subject2.chiron
    assert subject.mean_lilith == subject2.mean_lilith

    assert subject.first_house == subject2.first_house
    assert subject.second_house == subject2.second_house
    assert subject.third_house == subject2.third_house
    assert subject.fourth_house == subject2.fourth_house
    assert subject.fifth_house == subject2.fifth_house
    assert subject.sixth_house == subject2.sixth_house
    assert subject.seventh_house == subject2.seventh_house
    assert subject.eighth_house == subject2.eighth_house
    assert subject.ninth_house == subject2.ninth_house
    assert subject.tenth_house == subject2.tenth_house
    assert subject.eleventh_house == subject2.eleventh_house
    assert subject.twelfth_house == subject2.twelfth_house
    assert subject.mean_north_lunar_node == subject2.mean_north_lunar_node
    assert subject.true_north_lunar_node == subject2.true_north_lunar_node
    assert subject.lunar_phase == subject2.lunar_phase


    assert subject.active_points == subject2.active_points
    assert subject.houses_names_list == subject2.houses_names_list
