from kerykeion.fetch_geonames import FetchGeonames

def test_geonames():
    geonames = FetchGeonames("Roma", "Italy")
    data = geonames.get_serialized_data()
    assert data["timezone"] == "Europe/Rome"

if __name__ == "__main__":
    test_geonames()