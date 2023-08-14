from kerykeion.fetch_geonames import FetchGeonames


def test_geonames():
    geonames = FetchGeonames("Roma", "IT")
    data = geonames.get_serialized_data()
    expected_data = {
        "timezonestr": "Europe/Rome",
        "name": "Rome",
        "lat": "41.89193",
        "lng": "12.51133",
        "countryCode": "IT",
        # Cache is not tested
        "from_tz_cache": True,
        "from_country_cache": True,
    }

    assert data["timezonestr"] == expected_data["timezonestr"]
    assert data["name"] == expected_data["name"]
    assert data["lat"] == expected_data["lat"]
    assert data["lng"] == expected_data["lng"]
    assert data["countryCode"] == expected_data["countryCode"]
