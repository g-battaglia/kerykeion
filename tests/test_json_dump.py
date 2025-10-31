from kerykeion import AstrologicalSubjectFactory
from json import loads


class TestJsonDump:
    def setup_class(self):
        self.instance = AstrologicalSubjectFactory.from_birth_data("Test", 1993, 10, 10, 12, 12, "London", "GB", suppress_geonames_warning=True)
        self.dictionary = loads(self.instance.model_dump_json())

    def test_json_dump_data(self):
        assert self.dictionary["name"] == "Test"
        assert self.dictionary["year"] == 1993
        assert self.dictionary["month"] == 10
        assert self.dictionary["day"] == 10
        assert self.dictionary["hour"] == 12
        assert self.dictionary["minute"] == 12
        assert self.dictionary["city"] == "London"
        assert self.dictionary["nation"] == "GB"
        assert round(self.dictionary["lat"], 2) == 51.51
        assert round(self.dictionary["lng"], 2) == -0.13
        assert self.dictionary["tz_str"] == "Europe/London"
        assert self.dictionary["zodiac_type"] == "Tropical"
        assert round(self.dictionary["julian_day"], 2) == 2449270.97

    def test_json_dump_sun(self):
        assert self.dictionary["sun"]["name"] == "Sun"
        assert self.dictionary["sun"]["quality"] == "Cardinal"
        assert self.dictionary["sun"]["element"] == "Air"
        assert self.dictionary["sun"]["sign"] == "Lib"
        assert self.dictionary["sun"]["sign_num"] == 6
        assert round(self.dictionary["sun"]["position"], 2) == 17.16
        assert round(self.dictionary["sun"]["abs_pos"], 2) == 197.16
        assert self.dictionary["sun"]["emoji"] == "♎️"
        assert self.dictionary["sun"]["house"] == "Tenth_House"
        assert not self.dictionary["sun"]["retrograde"]
        assert self.dictionary["sun"]["point_type"] == "AstrologicalPoint"

    def test_json_dump_moon(self):
        assert self.dictionary["moon"]["name"] == "Moon"

    def test_json_dump_mercury(self):
        assert self.dictionary["mercury"]["name"] == "Mercury"

    def test_json_dump_venus(self):
        assert self.dictionary["venus"]["name"] == "Venus"

    def test_json_dump_mars(self):
        assert self.dictionary["mars"]["name"] == "Mars"

    def test_json_dump_jupiter(self):
        assert self.dictionary["jupiter"]["name"] == "Jupiter"

    def test_json_dump_saturn(self):
        assert self.dictionary["saturn"]["name"] == "Saturn"

    def test_json_dump_uranus(self):
        assert self.dictionary["uranus"]["name"] == "Uranus"

    def test_json_dump_neptune(self):
        assert self.dictionary["neptune"]["name"] == "Neptune"

    def test_json_dump_pluto(self):
        assert self.dictionary["pluto"]["name"] == "Pluto"

    def test_json_dump_first_house(self):
        assert self.dictionary["first_house"]["name"] == "First_House"

    def test_json_dump_second_house(self):
        assert self.dictionary["second_house"]["name"] == "Second_House"

    def test_json_dump_third_house(self):
        assert self.dictionary["third_house"]["name"] == "Third_House"

    def test_json_dump_fourth_house(self):
        assert self.dictionary["fourth_house"]["name"] == "Fourth_House"

    def test_json_dump_fifth_house(self):
        assert self.dictionary["fifth_house"]["name"] == "Fifth_House"

    def test_json_dump_sixth_house(self):
        assert self.dictionary["sixth_house"]["name"] == "Sixth_House"

    def test_json_dump_seventh_house(self):
        assert self.dictionary["seventh_house"]["name"] == "Seventh_House"

    def test_json_dump_eighth_house(self):
        assert self.dictionary["eighth_house"]["name"] == "Eighth_House"

    def test_json_dump_ninth_house(self):
        assert self.dictionary["ninth_house"]["name"] == "Ninth_House"

    def test_json_dump_tenth_house(self):
        assert self.dictionary["tenth_house"]["name"] == "Tenth_House"

    def test_json_dump_eleventh_house(self):
        assert self.dictionary["eleventh_house"]["name"] == "Eleventh_House"

    def test_json_dump_twelfth_house(self):
        assert self.dictionary["twelfth_house"]["name"] == "Twelfth_House"

    def test_lunar_phase(self):
        assert self.dictionary["lunar_phase"]["moon_emoji"] == "🌘"
