from kerykeion.fetch_geonames import FetchGeonames
from kerykeion import KrInstance


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


if __name__ == "__main__":
    test_geonames()
    test_kerykeion_instace()
