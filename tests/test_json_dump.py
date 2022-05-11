from kerykeion import KrInstance
from json import loads

class TestJsonDump:
    def setup_class(self):
        self.instance = KrInstance(
            "Test", 1993, 10, 10, 12, 12, "London", "GB")
        json = self.instance.json()
        self.dictionary = loads(json)

    def test_json_dump_data(self):
        assert self.dictionary['name'] == "Test"
        assert self.dictionary['year'] == 1993
        assert self.dictionary['month'] == 10
        assert self.dictionary['day'] == 10
        assert self.dictionary['hour'] == 12
        assert self.dictionary['minute'] == 12
        assert self.dictionary['city'] == "London"
        assert self.dictionary['nation'] == "GB"
        assert self.dictionary['lat'] == 51.50853
        assert self.dictionary['lng'] == -0.12574
        assert self.dictionary['tz_str'] == 'Europe/London'
        assert self.dictionary['local_time'] == 12.2
        assert self.dictionary['utc_time'] == 11.2
        assert self.dictionary['zodiac_type'] == "Tropic"
        assert self.dictionary['julian_day'] == 2449270.966666667


    def test_json_dump_sun(self):
        assert self.dictionary['sun']['name'] == "Sun"
        assert self.dictionary['sun']['quality'] == "Cardinal"
        assert self.dictionary['sun']['element'] == "Air"
        assert self.dictionary['sun']['sign'] == "Lib"
        assert self.dictionary['sun']['sign_num'] == 6
        assert self.dictionary['sun']['position'] == 17.16206089113507
        assert self.dictionary['sun']['abs_pos'] == 197.16206089113507
        assert self.dictionary['sun']['emoji'] == "♎️"
        assert self.dictionary['sun']['house'] == "Tenth House"
        assert self.dictionary['sun']['retrograde'] == False
        assert self.dictionary['sun']['point_type'] == "Planet"

    def test_json_dump_moon(self):
        assert self.dictionary['moon']['name'] == "Moon"

    def test_json_dump_mercury(self):
        assert self.dictionary['mercury']['name'] == "Mercury"

    def test_json_dump_venus(self):
        assert self.dictionary['venus']['name'] == "Venus"

    def test_json_dump_mars(self):
        assert self.dictionary['mars']['name'] == "Mars"

    def test_json_dump_jupiter(self):
        assert self.dictionary['jupiter']['name'] == "Jupiter"

    def test_json_dump_saturn(self):
        assert self.dictionary['saturn']['name'] == "Saturn"

    def test_json_dump_uranus(self):
        assert self.dictionary['uranus']['name'] == "Uranus"

    def test_json_dump_neptune(self):
        assert self.dictionary['neptune']['name'] == "Neptune"

    def test_json_dump_pluto(self):
        assert self.dictionary['pluto']['name'] == "Pluto"

    def test_json_dump_first_house(self):
        assert self.dictionary['first_house']['name'] == "First House"

    def test_json_dump_second_house(self):
        assert self.dictionary['second_house']['name'] == "Second House"
    
    def test_json_dump_third_house(self):
        assert self.dictionary['third_house']['name'] == "Third House"

    def test_json_dump_fourth_house(self):
        assert self.dictionary['fourth_house']['name'] == "Fourth House"

    def test_json_dump_fifth_house(self):
        assert self.dictionary['fifth_house']['name'] == "Fifth House"
    
    def test_json_dump_sixth_house(self):
        assert self.dictionary['sixth_house']['name'] == "Sixth House"
    
    def test_json_dump_seventh_house(self):
        assert self.dictionary['seventh_house']['name'] == "Seventh House"

    def test_json_dump_eighth_house(self):
        assert self.dictionary['eighth_house']['name'] == "Eighth House"

    def test_json_dump_ninth_house(self):
        assert self.dictionary['ninth_house']['name'] == "Ninth House"
    
    def test_json_dump_tenth_house(self):
        assert self.dictionary['tenth_house']['name'] == "Tenth House"

    def test_json_dump_eleventh_house(self):
        assert self.dictionary['eleventh_house']['name'] == "Eleventh House"
    
    def test_json_dump_twelfth_house(self):
        assert self.dictionary['twelfth_house']['name'] == "Twelfth House"
    
    def test_lunar_phase(self):
        print('------')
        print(self.dictionary['lunar_phase']['moon_emoji'])
        assert self.dictionary['lunar_phase']['moon_emoji'] == '🌘'

if __name__ == "__main__":
    test = TestJsonDump()
    test.setup_class()
    test.test_json_dump_data()
    test.test_lunar_phase()