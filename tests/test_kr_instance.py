from kerykeion import KrInstance
from logging import getLogger

logger = getLogger(__name__)


class TestKrInstance:
    def setup_class(self):
        # Johnny Depp
        self.subject = KrInstance("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US")
        self.expected_output = {
            "name": "Johnny Depp",
            "year": 1963,
            "month": 6,
            "day": 9,
            "hour": 0,
            "minute": 0,
            "city": "Owensboro",
            "nation": "US",
            "lng": -87.11333,
            "lat": 37.77422,
            "tz_str": "America/Chicago",
            "zodiac_type": "Tropic",
            "local_time": 0.0,
            "utc_time": 5.0,
            "julian_day": 2438189.7083333335,
            "sun": {
                "name": "Sun",
                "quality": "Mutable",
                "element": "Air",
                "sign": "Gem",
                "sign_num": 2,
                "position": 17.659700723619764,
                "abs_pos": 77.65970072361976,
                "emoji": "♊️",
                "point_type": "Planet",
                "house": "Fourth House",
                "retrograde": False,
            },
            "moon": {
                "name": "Moon",
                "quality": "Cardinal",
                "element": "Earth",
                "sign": "Cap",
                "sign_num": 9,
                "position": 8.735173210893663,
                "abs_pos": 278.73517321089366,
                "emoji": "♑️",
                "point_type": "Planet",
                "house": "Eleventh House",
                "retrograde": False,
            },
            "mercury": {
                "name": "Mercury",
                "quality": "Fixed",
                "element": "Earth",
                "sign": "Tau",
                "sign_num": 1,
                "position": 25.00187700457719,
                "abs_pos": 55.00187700457719,
                "emoji": "♉️",
                "point_type": "Planet",
                "house": "Third House",
                "retrograde": False,
            },
            "venus": {
                "name": "Venus",
                "quality": "Fixed",
                "element": "Earth",
                "sign": "Tau",
                "sign_num": 1,
                "position": 25.603753240224542,
                "abs_pos": 55.60375324022454,
                "emoji": "♉️",
                "point_type": "Planet",
                "house": "Third House",
                "retrograde": False,
            },
            "mars": {
                "name": "Mars",
                "quality": "Mutable",
                "element": "Earth",
                "sign": "Vir",
                "sign_num": 5,
                "position": 3.0116698475575276,
                "abs_pos": 153.01166984755753,
                "emoji": "♍️",
                "point_type": "Planet",
                "house": "Seventh House",
                "retrograde": False,
            },
            "jupiter": {
                "name": "Jupiter",
                "quality": "Cardinal",
                "element": "Fire",
                "sign": "Ari",
                "sign_num": 0,
                "position": 13.910952211401664,
                "abs_pos": 13.910952211401664,
                "emoji": "♈️",
                "point_type": "Planet",
                "house": "Second House",
                "retrograde": False,
            },
            "saturn": {
                "name": "Saturn",
                "quality": "Fixed",
                "element": "Air",
                "sign": "Aqu",
                "sign_num": 10,
                "position": 23.083510999945474,
                "abs_pos": 323.0835109999455,
                "emoji": "♒️",
                "point_type": "Planet",
                "house": "First House",
                "retrograde": True,
            },
            "uranus": {
                "name": "Uranus",
                "quality": "Mutable",
                "element": "Earth",
                "sign": "Vir",
                "sign_num": 5,
                "position": 1.5666373257095927,
                "abs_pos": 151.5666373257096,
                "emoji": "♍️",
                "point_type": "Planet",
                "house": "Seventh House",
                "retrograde": False,
            },
            "neptune": {
                "name": "Neptune",
                "quality": "Fixed",
                "element": "Water",
                "sign": "Sco",
                "sign_num": 7,
                "position": 13.423481419291079,
                "abs_pos": 223.42348141929108,
                "emoji": "♏️",
                "point_type": "Planet",
                "house": "Ninth House",
                "retrograde": True,
            },
            "pluto": {
                "name": "Pluto",
                "quality": "Mutable",
                "element": "Earth",
                "sign": "Vir",
                "sign_num": 5,
                "position": 9.625641361989636,
                "abs_pos": 159.62564136198964,
                "emoji": "♍️",
                "point_type": "Planet",
                "house": "Seventh House",
                "retrograde": False,
            },
            "first_house": {
                "name": "First House",
                "quality": "Fixed",
                "element": "Air",
                "sign": "Aqu",
                "sign_num": 10,
                "position": 20.696672272096748,
                "abs_pos": 320.69667227209675,
                "emoji": "♒️",
                "point_type": "House",
            },
            "second_house": {
                "name": "Second House",
                "quality": "Cardinal",
                "element": "Fire",
                "sign": "Ari",
                "sign_num": 0,
                "position": 6.643247095515116,
                "abs_pos": 6.643247095515116,
                "emoji": "♈️",
                "point_type": "House",
            },
            "third_house": {
                "name": "Third House",
                "quality": "Fixed",
                "element": "Earth",
                "sign": "Tau",
                "sign_num": 1,
                "position": 11.215413957987053,
                "abs_pos": 41.21541395798705,
                "emoji": "♉️",
                "point_type": "House",
            },
            "fourth_house": {
                "name": "Fourth House",
                "quality": "Mutable",
                "element": "Air",
                "sign": "Gem",
                "sign_num": 2,
                "position": 6.587748893878825,
                "abs_pos": 66.58774889387882,
                "emoji": "♊️",
                "point_type": "House",
            },
            "fifth_house": {
                "name": "Fifth House",
                "quality": "Mutable",
                "element": "Air",
                "sign": "Gem",
                "sign_num": 2,
                "position": 28.34219396577589,
                "abs_pos": 88.34219396577589,
                "emoji": "♊️",
                "point_type": "House",
            },
            "sixth_house": {
                "name": "Sixth House",
                "quality": "Cardinal",
                "element": "Water",
                "sign": "Can",
                "sign_num": 3,
                "position": 20.99073151066341,
                "abs_pos": 110.99073151066341,
                "emoji": "♋️",
                "point_type": "House",
            },
            "seventh_house": {
                "name": "Seventh House",
                "quality": "Fixed",
                "element": "Fire",
                "sign": "Leo",
                "sign_num": 4,
                "position": 20.696672272096748,
                "abs_pos": 140.69667227209675,
                "emoji": "♌️",
                "point_type": "House",
            },
            "eighth_house": {
                "name": "Eighth House",
                "quality": "Cardinal",
                "element": "Air",
                "sign": "Lib",
                "sign_num": 6,
                "position": 6.6432470955151075,
                "abs_pos": 186.6432470955151,
                "emoji": "♎️",
                "point_type": "House",
            },
            "ninth_house": {
                "name": "Ninth House",
                "quality": "Fixed",
                "element": "Water",
                "sign": "Sco",
                "sign_num": 7,
                "position": 11.215413957987039,
                "abs_pos": 221.21541395798704,
                "emoji": "♏️",
                "point_type": "House",
            },
            "tenth_house": {
                "name": "Tenth House",
                "quality": "Mutable",
                "element": "Fire",
                "sign": "Sag",
                "sign_num": 8,
                "position": 6.587748893878825,
                "abs_pos": 246.58774889387882,
                "emoji": "♐️",
                "point_type": "House",
            },
            "eleventh_house": {
                "name": "Eleventh House",
                "quality": "Mutable",
                "element": "Fire",
                "sign": "Sag",
                "sign_num": 8,
                "position": 28.34219396577589,
                "abs_pos": 268.3421939657759,
                "emoji": "♐️",
                "point_type": "House",
            },
            "twelfth_house": {
                "name": "Twelfth House",
                "quality": "Cardinal",
                "element": "Earth",
                "sign": "Cap",
                "sign_num": 9,
                "position": 20.99073151066341,
                "abs_pos": 290.9907315106634,
                "emoji": "♑️",
                "point_type": "House",
            },
            "mean_node": {
                "name": "Mean_Node",
                "quality": "Cardinal",
                "element": "Water",
                "sign": "Can",
                "sign_num": 3,
                "position": 22.25322751786969,
                "abs_pos": 112.25322751786969,
                "emoji": "♋️",
                "point_type": "Planet",
                "house": "Sixth House",
                "retrograde": True,
            },
            "true_node": {
                "name": "True_Node",
                "quality": "Cardinal",
                "element": "Water",
                "sign": "Can",
                "sign_num": 3,
                "position": 20.63971940408193,
                "abs_pos": 110.63971940408193,
                "emoji": "♋️",
                "point_type": "Planet",
                "house": "Fifth House",
                "retrograde": True,
            },
            "lunar_phase": {"degrees_between_s_m": 201, "moon_phase": 16, "sun_phase": 15, "moon_emoji": "🌖"},
        }

    def test_basic_input_data(self):
        assert self.subject.name == self.expected_output["name"]
        assert self.subject.year == self.expected_output["year"]
        assert self.subject.month == self.expected_output["month"]
        assert self.subject.day == self.expected_output["day"]
        assert self.subject.hour == self.expected_output["hour"]
        assert self.subject.minute == self.expected_output["minute"]
        assert self.subject.city == self.expected_output["city"]
        assert self.subject.nation == self.expected_output["nation"]

    def test_internal_data(self):
        assert round(self.subject.lat, 3) == round(self.expected_output["lat"], 3)
        assert round(self.subject.lng, 3) == round(self.expected_output["lng"], 3)
        assert self.subject.tz_str == self.expected_output["tz_str"]
        assert self.subject.zodiac_type == self.expected_output["zodiac_type"]
        assert self.subject.julian_day == self.expected_output["julian_day"]

    def test_sun(self):
        assert self.subject.sun.name == self.expected_output["sun"]["name"]
        assert self.subject.sun.quality == self.expected_output["sun"]["quality"]
        assert self.subject.sun.element == self.expected_output["sun"]["element"]
        assert self.subject.sun.sign == self.expected_output["sun"]["sign"]
        assert self.subject.sun.sign_num == self.expected_output["sun"]["sign_num"]
        assert round(self.subject.sun.position, 3) == round(self.expected_output["sun"]["position"], 3)
        assert round(self.subject.sun.abs_pos, 3) == round(self.expected_output["sun"]["abs_pos"], 3)
        assert self.subject.sun.emoji == self.expected_output["sun"]["emoji"]
        assert self.subject.sun.point_type == self.expected_output["sun"]["point_type"]
        assert self.subject.sun.house == self.expected_output["sun"]["house"]
        assert self.subject.sun.retrograde == self.expected_output["sun"]["retrograde"]

    def test_moon(self):
        assert self.subject.moon.name == self.expected_output["moon"]["name"]
        assert self.subject.moon.quality == self.expected_output["moon"]["quality"]
        assert self.subject.moon.element == self.expected_output["moon"]["element"]
        assert self.subject.moon.sign == self.expected_output["moon"]["sign"]
        assert self.subject.moon.sign_num == self.expected_output["moon"]["sign_num"]
        assert round(self.subject.moon.position, 3) == round(self.expected_output["moon"]["position"], 3)
        assert round(self.subject.moon.abs_pos, 3) == round(self.expected_output["moon"]["abs_pos"], 3)
        assert self.subject.moon.emoji == self.expected_output["moon"]["emoji"]
        assert self.subject.moon.point_type == self.expected_output["moon"]["point_type"]
        assert self.subject.moon.house == self.expected_output["moon"]["house"]
        assert self.subject.moon.retrograde == self.expected_output["moon"]["retrograde"]

    def test_lunar_phase(self):
        assert self.subject.lunar_phase == self.expected_output["lunar_phase"]
