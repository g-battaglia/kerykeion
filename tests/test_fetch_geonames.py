from kerykeion.fetch_geonames import FetchGeonames


def test_geonames():
    geonames = FetchGeonames("Roma", "IT")
    data = geonames.get_serialized_data()

    assert data["countryCode"] == "IT"
    assert data["timezonestr"] == "Europe/Rome"
    assert data["lat"] == "41.89193"
    assert data["lng"] == "12.51133"
