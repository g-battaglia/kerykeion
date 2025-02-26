from kerykeion import AstrologicalSubject


class TestAstrologicalSubjectJyotish:
    def setup_class(self):

        # Johnny Depp's vedic horoscope: using sidereal zodiac, Lahiri ayanamsha and whole-sign houses
        self.subject = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", \
            zodiac_type="Sidereal", sidereal_mode="LAHIRI", houses_system_identifier="W", geonames_username="century.boy")

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
            "zodiac_type": "Sidereal",
            "julian_day": 2438189.7083333335,
            # Deprecated -->
            "local_time": 0.0,
            "utc_time": 5.0,
            # <-- Deprecated

            "ascendant": {
                "name": "Ascendant",
                "quality": "Cardinal",
                "element": "Earth",
                "sign": "Cap",
                "sign_num": 9,
                "position": 27.35490680258141,
                "abs_pos": 297.3549068025814,
                "emoji": "♑️",
                "point_type": "AxialCusps",
                "house": "First_House",
                "retrograde": False,
            },
            "descendant": {
                "name": "Descendant",
                "quality": "Cardinal",
                "element": "Water",
                "sign": "Can",
                "sign_num": 3,
                "position": 27.35490680258141,
                "abs_pos": 117.35490680258141,
                "emoji": "♋️",
                "point_type": "AxialCusps",
                "house": "Seventh_House",
                "retrograde": False,
            },
            "medium_coeli": {
                "name": "Medium_Coeli",
                "quality": "Fixed",
                "element": "Water",
                "sign": "Sco",
                "sign_num": 7,
                "position": 13.245983424363487,
                "abs_pos": 223.2459834243635,
                "emoji": "♏️",
                "point_type": "AxialCusps",
                "house": "Eleventh_House",
                "retrograde": False,
            },
            "imum_coeli": {
                "name": "Imum_Coeli",
                "quality": "Fixed",
                "element": "Earth",
                "sign": "Tau",
                "sign_num": 1,
                "position": 13.245983424363487,
                "abs_pos": 43.24598342436349,
                "emoji": "♉️",
                "point_type": "AxialCusps",
                "house": "Fifth_House",
                "retrograde": False,
            },
            "sun": {
                "name": "Sun",
                "quality": "Fixed",
                "element": "Earth",
                "sign": "Tau",
                "sign_num": 1,
                "position": 24.31793528253837,
                "abs_pos": 54.31793528253837,
                "emoji": "♉️",
                "point_type": "Planet",
                "house": "Fifth_House",
                "retrograde": False,
            },
            "moon": {
                "name": "Moon",
                "quality": "Mutable",
                "element": "Fire",
                "sign": "Sag",
                "sign_num": 8,
                "position": 15.39340776981174,
                "abs_pos": 255.39340776981174,
                "emoji": "♐️",
                "point_type": "Planet",
                "house": "Twelfth_House",
                "retrograde": False,
            },
            "mercury": {
                "name": "Mercury",
                "quality": "Fixed",
                "element": "Earth",
                "sign": "Tau",
                "sign_num": 1,
                "position": 1.66011156351147,
                "abs_pos": 31.66011156351147,
                "emoji": "♉️",
                "point_type": "Planet",
                "house": "Fifth_House",
                "retrograde": False,
            },
            "venus": {
                "name": "Venus",
                "quality": "Fixed",
                "element": "Earth",
                "sign": "Tau",
                "sign_num": 1,
                "position": 2.261987799142716,
                "abs_pos": 32.261987799142716,
                "emoji": "♉️",
                "point_type": "Planet",
                "house": "Fifth_House",
                "retrograde": False,
            },
            "mars": {
                "name": "Mars",
                "quality": "Fixed",
                "element": "Fire",
                "sign": "Leo",
                "sign_num": 4,
                "position": 9.6699044063961,
                "abs_pos": 129.6699044063961,
                "emoji": "♌️",
                "point_type": "Planet",
                "house": "Eighth_House",
                "retrograde": False,
            },
            "jupiter": {
                "name": "Jupiter",
                "quality": "Mutable",
                "element": "Water",
                "sign": "Pis",
                "sign_num": 11,
                "position": 20.5691867703156,
                "abs_pos": 350.5691867703156,
                "emoji": "♓️",
                "point_type": "Planet",
                "house": "Third_House",
                "retrograde": False,
            },
            "saturn": {
                "name": "Saturn",
                "quality": "Cardinal",
                "element": "Earth",
                "sign": "Cap",
                "sign_num": 9,
                "position": 29.74174555889493,
                "abs_pos": 299.74174555889493,
                "emoji": "♑️",
                "point_type": "Planet",
                "house": "First_House",
                "retrograde": True,
            },
            "uranus": {
                "name": "Uranus",
                "quality": "Fixed",
                "element": "Fire",
                "sign": "Leo",
                "sign_num": 4,
                "position": 8.2248718846302,
                "abs_pos": 128.2248718846302,
                "emoji": "♌️",
                "point_type": "Planet",
                "house": "Eighth_House",
                "retrograde": False,
            },
            "neptune": {
                "name": "Neptune",
                "quality": "Cardinal",
                "element": "Air",
                "sign": "Lib",
                "sign_num": 6,
                "position": 20.08171597826217,
                "abs_pos": 200.08171597826217,
                "emoji": "♎️",
                "point_type": "Planet",
                "house": "Tenth_House",
                "retrograde": True,
            },
            "pluto": {
                "name": "Pluto",
                "quality": "Fixed",
                "element": "Fire",
                "sign": "Leo",
                "sign_num": 4,
                "position": 16.283875921047326,
                "abs_pos": 136.28387592104733,
                "emoji": "♌️",
                "point_type": "Planet",
                "house": "Eighth_House",
                "retrograde": False,
            },
            "first_house": {
                "name": "First_House",
                "quality": "Cardinal",
                "element": "Earth",
                "sign": "Cap",
                "sign_num": 9,
                "position": 0.0,
                "abs_pos": 270.0,
                "emoji": "♑️",
                "point_type": "House",
            },
            "second_house": {
                "name": "Second_House",
                "quality": "Fixed",
                "element": "Air",
                "sign": "Aqu",
                "sign_num": 10,
                "position": 0.0,
                "abs_pos": 300.0,
                "emoji": "♒️",
                "point_type": "House",
            },
            "third_house": {
                "name": "Third_House",
                "quality": "Mutable",
                "element": "Water",
                "sign": "Pis",
                "sign_num": 11,
                "position": 0.0,
                "abs_pos": 330.0,
                "emoji": "♓️",
                "point_type": "House",
            },
            "fourth_house": {
                "name": "Fourth_House",
                "quality": "Cardinal",
                "element": "Fire",
                "sign": "Ari",
                "sign_num": 0,
                "position": 0.0,
                "abs_pos": 0.0,
                "emoji": "♈️",
                "point_type": "House",
            },
            "fifth_house": {
                "name": "Fifth_House",
                "quality": "Fixed",
                "element": "Earth",
                "sign": "Tau",
                "sign_num": 1,
                "position": 0.0,
                "abs_pos": 30.0,
                "emoji": "♉️",
                "point_type": "House",
            },
            "sixth_house": {
                "name": "Sixth_House",
                "quality": "Mutable",
                "element": "Air",
                "sign": "Gem",
                "sign_num": 2,
                "position": 0.0,
                "abs_pos": 60.0,
                "emoji": "♊️",
                "point_type": "House",
            },
            "seventh_house": {
                "name": "Seventh_House",
                "quality": "Cardinal",
                "element": "Water",
                "sign": "Can",
                "sign_num": 3,
                "position": 0.0,
                "abs_pos": 90.0,
                "emoji": "♋️",
                "point_type": "House",
            },
            "eighth_house": {
                "name": "Eighth_House",
                "quality": "Fixed",
                "element": "Fire",
                "sign": "Leo",
                "sign_num": 4,
                "position": 0.0,
                "abs_pos": 120.0,
                "emoji": "♌️",
                "point_type": "House",
            },
            "ninth_house": {
                "name": "Ninth_House",
                "quality": "Mutable",
                "element": "Earth",
                "sign": "Vir",
                "sign_num": 5,
                "position": 0.0,
                "abs_pos": 150.0,
                "emoji": "♍️",
                "point_type": "House",
            },
            "tenth_house": {
                "name": "Tenth_House",
                "quality": "Cardinal",
                "element": "Air",
                "sign": "Lib",
                "sign_num": 6,
                "position": 0.0,
                "abs_pos": 180.0,
                "emoji": "♎️",
                "point_type": "House",
            },
            "eleventh_house": {
                "name": "Eleventh_House",
                "quality": "Fixed",
                "element": "Water",
                "sign": "Sco",
                "sign_num": 7,
                "position": 0.0,
                "abs_pos": 210.0,
                "emoji": "♏️",
                "point_type": "House",
            },
            "twelfth_house": {
                "name": "Twelfth_House",
                "quality": "Mutable",
                "element": "Fire",
                "sign": "Sag",
                "sign_num": 8,
                "position": 0.0,
                "abs_pos": 240.0,
                "emoji": "♐️",
                "point_type": "House",
            },
            "mean_node": {
                "name": "Mean_Node",
                "quality": "Mutable",
                "element": "Air",
                "sign": "Gem",
                "sign_num": 2,
                "position": 28.91146207678823,
                "abs_pos": 88.91146207678823,
                "emoji": "♊️",
                "point_type": "Planet",
                "house": "Sixth_House",
                "retrograde": True,
            },
            "true_node": {
                "name": "True_Node",
                "quality": "Mutable",
                "element": "Air",
                "sign": "Gem",
                "sign_num": 2,
                "position": 27.29795395939222,
                "abs_pos": 87.29795395939222,
                "emoji": "♊️",
                "point_type": "Planet",
                "house": "Sixth_House",
                "retrograde": True,
            },
            "mean_south_node": {
                "name": "Mean_South_Node",
                "quality": "Mutable",
                "element": "Fire",
                "sign": "Sag",
                "sign_num": 8,
                "position": 28.91146207678821,
                "abs_pos": 268.9114620767882,
                "emoji": "♐️",
                "point_type": "Planet",
                "house": "Twelfth_House",
                "retrograde": True,
            },
            "true_south_node": {
                "name": "True_South_Node",
                "quality": "Mutable",
                "element": "Fire",
                "sign": "Sag",
                "sign_num": 8,
                "position": 27.2979539593922,
                "abs_pos": 267.2979539593922,
                "emoji": "♐️",
                "point_type": "Planet",
                "house": "Twelfth_House",
                "retrograde": True,
            },
            "lunar_phase": {
                "degrees_between_s_m": 201.07547248727337,
                "moon_phase": 16,
                "sun_phase": 15,
                "moon_emoji": "🌖",
                "moon_phase_name": "Waning Gibbous"
            },
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
        assert round(self.subject.lat, 2) == round(self.expected_output["lat"], 2)
        assert round(self.subject.lng, 2) == round(self.expected_output["lng"], 2)
        assert self.subject.tz_str == self.expected_output["tz_str"]
        assert self.subject.zodiac_type == self.expected_output["zodiac_type"]
        assert self.subject.julian_day == self.expected_output["julian_day"]

    def test_ascendant(self):
        assert self.subject.ascendant.name == self.expected_output["ascendant"]["name"]
        assert self.subject.ascendant.quality == self.expected_output["ascendant"]["quality"]
        assert self.subject.ascendant.element == self.expected_output["ascendant"]["element"]
        assert self.subject.ascendant.sign == self.expected_output["ascendant"]["sign"]
        assert self.subject.ascendant.sign_num == self.expected_output["ascendant"]["sign_num"]
        assert round(self.subject.ascendant.position, 2) == round(self.expected_output["ascendant"]["position"], 2)
        assert round(self.subject.ascendant.abs_pos, 2) == round(self.expected_output["ascendant"]["abs_pos"], 2)
        assert self.subject.ascendant.emoji == self.expected_output["ascendant"]["emoji"]
        assert self.subject.ascendant.point_type == self.expected_output["ascendant"]["point_type"]
        assert self.subject.ascendant.house == self.expected_output["ascendant"]["house"]
        assert self.subject.ascendant.retrograde == self.expected_output["ascendant"]["retrograde"]

    def test_descendant(self):
        assert self.subject.descendant.name == self.expected_output["descendant"]["name"]
        assert self.subject.descendant.quality == self.expected_output["descendant"]["quality"]
        assert self.subject.descendant.element == self.expected_output["descendant"]["element"]
        assert self.subject.descendant.sign == self.expected_output["descendant"]["sign"]
        assert self.subject.descendant.sign_num == self.expected_output["descendant"]["sign_num"]
        assert round(self.subject.descendant.position, 2) == round(self.expected_output["descendant"]["position"], 2)
        assert round(self.subject.descendant.abs_pos, 2) == round(self.expected_output["descendant"]["abs_pos"], 2)
        assert self.subject.descendant.emoji == self.expected_output["descendant"]["emoji"]
        assert self.subject.descendant.point_type == self.expected_output["descendant"]["point_type"]
        assert self.subject.descendant.house == self.expected_output["descendant"]["house"]
        assert self.subject.descendant.retrograde == self.expected_output["descendant"]["retrograde"]

    def test_medium_coeli(self):
        assert self.subject.medium_coeli.name == self.expected_output["medium_coeli"]["name"]
        assert self.subject.medium_coeli.quality == self.expected_output["medium_coeli"]["quality"]
        assert self.subject.medium_coeli.element == self.expected_output["medium_coeli"]["element"]
        assert self.subject.medium_coeli.sign == self.expected_output["medium_coeli"]["sign"]
        assert self.subject.medium_coeli.sign_num == self.expected_output["medium_coeli"]["sign_num"]
        assert round(self.subject.medium_coeli.position, 2) == round(self.expected_output["medium_coeli"]["position"], 2)
        assert round(self.subject.medium_coeli.abs_pos, 2) == round(self.expected_output["medium_coeli"]["abs_pos"], 2)
        assert self.subject.medium_coeli.emoji == self.expected_output["medium_coeli"]["emoji"]
        assert self.subject.medium_coeli.point_type == self.expected_output["medium_coeli"]["point_type"]
        assert self.subject.medium_coeli.house == self.expected_output["medium_coeli"]["house"]
        assert self.subject.medium_coeli.retrograde == self.expected_output["medium_coeli"]["retrograde"]

    def test_imum_coeli(self):
        assert self.subject.imum_coeli.name == self.expected_output["imum_coeli"]["name"]
        assert self.subject.imum_coeli.quality == self.expected_output["imum_coeli"]["quality"]
        assert self.subject.imum_coeli.element == self.expected_output["imum_coeli"]["element"]
        assert self.subject.imum_coeli.sign == self.expected_output["imum_coeli"]["sign"]
        assert self.subject.imum_coeli.sign_num == self.expected_output["imum_coeli"]["sign_num"]
        assert round(self.subject.imum_coeli.position, 2) == round(self.expected_output["imum_coeli"]["position"], 2)
        assert round(self.subject.imum_coeli.abs_pos, 2) == round(self.expected_output["imum_coeli"]["abs_pos"], 2)
        assert self.subject.imum_coeli.emoji == self.expected_output["imum_coeli"]["emoji"]
        assert self.subject.imum_coeli.point_type == self.expected_output["imum_coeli"]["point_type"]
        assert self.subject.imum_coeli.house == self.expected_output["imum_coeli"]["house"]
        assert self.subject.imum_coeli.retrograde == self.expected_output["imum_coeli"]["retrograde"]

    def test_sun(self):
        assert self.subject.sun.name == self.expected_output["sun"]["name"]
        assert self.subject.sun.quality == self.expected_output["sun"]["quality"]
        assert self.subject.sun.element == self.expected_output["sun"]["element"]
        assert self.subject.sun.sign == self.expected_output["sun"]["sign"]
        assert self.subject.sun.sign_num == self.expected_output["sun"]["sign_num"]
        assert round(self.subject.sun.position, 2) == round(self.expected_output["sun"]["position"], 2)
        assert round(self.subject.sun.abs_pos, 2) == round(self.expected_output["sun"]["abs_pos"], 2)
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
        assert round(self.subject.moon.position, 2) == round(self.expected_output["moon"]["position"], 2)
        assert round(self.subject.moon.abs_pos, 2) == round(self.expected_output["moon"]["abs_pos"], 2)
        assert self.subject.moon.emoji == self.expected_output["moon"]["emoji"]
        assert self.subject.moon.point_type == self.expected_output["moon"]["point_type"]
        assert self.subject.moon.house == self.expected_output["moon"]["house"]
        assert self.subject.moon.retrograde == self.expected_output["moon"]["retrograde"]

    def test_mercury(self):
        assert self.subject.mercury.name == self.expected_output["mercury"]["name"]
        assert self.subject.mercury.quality == self.expected_output["mercury"]["quality"]
        assert self.subject.mercury.element == self.expected_output["mercury"]["element"]
        assert self.subject.mercury.sign == self.expected_output["mercury"]["sign"]
        assert self.subject.mercury.sign_num == self.expected_output["mercury"]["sign_num"]
        assert round(self.subject.mercury.position, 2) == round(self.expected_output["mercury"]["position"], 2)
        assert round(self.subject.mercury.abs_pos, 2) == round(self.expected_output["mercury"]["abs_pos"], 2)
        assert self.subject.mercury.emoji == self.expected_output["mercury"]["emoji"]
        assert self.subject.mercury.point_type == self.expected_output["mercury"]["point_type"]
        assert self.subject.mercury.house == self.expected_output["mercury"]["house"]
        assert self.subject.mercury.retrograde == self.expected_output["mercury"]["retrograde"]

    def test_venus(self):
        assert self.subject.venus.name == self.expected_output["venus"]["name"]
        assert self.subject.venus.quality == self.expected_output["venus"]["quality"]
        assert self.subject.venus.element == self.expected_output["venus"]["element"]
        assert self.subject.venus.sign == self.expected_output["venus"]["sign"]
        assert self.subject.venus.sign_num == self.expected_output["venus"]["sign_num"]
        assert round(self.subject.venus.position, 2) == round(self.expected_output["venus"]["position"], 2)
        assert round(self.subject.venus.abs_pos, 2) == round(self.expected_output["venus"]["abs_pos"], 2)
        assert self.subject.venus.emoji == self.expected_output["venus"]["emoji"]
        assert self.subject.venus.point_type == self.expected_output["venus"]["point_type"]
        assert self.subject.venus.house == self.expected_output["venus"]["house"]
        assert self.subject.venus.retrograde == self.expected_output["venus"]["retrograde"]

    def test_mars(self):
        assert self.subject.mars.name == self.expected_output["mars"]["name"]
        assert self.subject.mars.quality == self.expected_output["mars"]["quality"]
        assert self.subject.mars.element == self.expected_output["mars"]["element"]
        assert self.subject.mars.sign == self.expected_output["mars"]["sign"]
        assert self.subject.mars.sign_num == self.expected_output["mars"]["sign_num"]
        assert round(self.subject.mars.position, 2) == round(self.expected_output["mars"]["position"], 2)
        assert round(self.subject.mars.abs_pos, 2) == round(self.expected_output["mars"]["abs_pos"], 2)
        assert self.subject.mars.emoji == self.expected_output["mars"]["emoji"]
        assert self.subject.mars.point_type == self.expected_output["mars"]["point_type"]
        assert self.subject.mars.house == self.expected_output["mars"]["house"]
        assert self.subject.mars.retrograde == self.expected_output["mars"]["retrograde"]

    def test_jupiter(self):
        assert self.subject.jupiter.name == self.expected_output["jupiter"]["name"]
        assert self.subject.jupiter.quality == self.expected_output["jupiter"]["quality"]
        assert self.subject.jupiter.element == self.expected_output["jupiter"]["element"]
        assert self.subject.jupiter.sign == self.expected_output["jupiter"]["sign"]
        assert self.subject.jupiter.sign_num == self.expected_output["jupiter"]["sign_num"]
        assert round(self.subject.jupiter.position, 2) == round(self.expected_output["jupiter"]["position"], 2)
        assert round(self.subject.jupiter.abs_pos, 2) == round(self.expected_output["jupiter"]["abs_pos"], 2)
        assert self.subject.jupiter.emoji == self.expected_output["jupiter"]["emoji"]
        assert self.subject.jupiter.point_type == self.expected_output["jupiter"]["point_type"]
        assert self.subject.jupiter.house == self.expected_output["jupiter"]["house"]
        assert self.subject.jupiter.retrograde == self.expected_output["jupiter"]["retrograde"]

    def test_saturn(self):
        assert self.subject.saturn.name == self.expected_output["saturn"]["name"]
        assert self.subject.saturn.quality == self.expected_output["saturn"]["quality"]
        assert self.subject.saturn.element == self.expected_output["saturn"]["element"]
        assert self.subject.saturn.sign == self.expected_output["saturn"]["sign"]
        assert self.subject.saturn.sign_num == self.expected_output["saturn"]["sign_num"]
        assert round(self.subject.saturn.position, 2) == round(self.expected_output["saturn"]["position"], 2)
        assert round(self.subject.saturn.abs_pos, 2) == round(self.expected_output["saturn"]["abs_pos"], 2)
        assert self.subject.saturn.emoji == self.expected_output["saturn"]["emoji"]
        assert self.subject.saturn.point_type == self.expected_output["saturn"]["point_type"]
        assert self.subject.saturn.house == self.expected_output["saturn"]["house"]
        assert self.subject.saturn.retrograde == self.expected_output["saturn"]["retrograde"]

    def test_uranus(self):
        assert self.subject.uranus.name == self.expected_output["uranus"]["name"]
        assert self.subject.uranus.quality == self.expected_output["uranus"]["quality"]
        assert self.subject.uranus.element == self.expected_output["uranus"]["element"]
        assert self.subject.uranus.sign == self.expected_output["uranus"]["sign"]
        assert self.subject.uranus.sign_num == self.expected_output["uranus"]["sign_num"]
        assert round(self.subject.uranus.position, 2) == round(self.expected_output["uranus"]["position"], 2)
        assert round(self.subject.uranus.abs_pos, 2) == round(self.expected_output["uranus"]["abs_pos"], 2)
        assert self.subject.uranus.emoji == self.expected_output["uranus"]["emoji"]
        assert self.subject.uranus.point_type == self.expected_output["uranus"]["point_type"]
        assert self.subject.uranus.house == self.expected_output["uranus"]["house"]
        assert self.subject.uranus.retrograde == self.expected_output["uranus"]["retrograde"]

    def test_neptune(self):
        assert self.subject.neptune.name == self.expected_output["neptune"]["name"]
        assert self.subject.neptune.quality == self.expected_output["neptune"]["quality"]
        assert self.subject.neptune.element == self.expected_output["neptune"]["element"]
        assert self.subject.neptune.sign == self.expected_output["neptune"]["sign"]
        assert self.subject.neptune.sign_num == self.expected_output["neptune"]["sign_num"]
        assert round(self.subject.neptune.position, 2) == round(self.expected_output["neptune"]["position"], 2)
        assert round(self.subject.neptune.abs_pos, 2) == round(self.expected_output["neptune"]["abs_pos"], 2)
        assert self.subject.neptune.emoji == self.expected_output["neptune"]["emoji"]
        assert self.subject.neptune.point_type == self.expected_output["neptune"]["point_type"]
        assert self.subject.neptune.house == self.expected_output["neptune"]["house"]
        assert self.subject.neptune.retrograde == self.expected_output["neptune"]["retrograde"]

    def test_pluto(self):
        assert self.subject.pluto.name == self.expected_output["pluto"]["name"]
        assert self.subject.pluto.quality == self.expected_output["pluto"]["quality"]
        assert self.subject.pluto.element == self.expected_output["pluto"]["element"]
        assert self.subject.pluto.sign == self.expected_output["pluto"]["sign"]
        assert self.subject.pluto.sign_num == self.expected_output["pluto"]["sign_num"]
        assert round(self.subject.pluto.position, 2) == round(self.expected_output["pluto"]["position"], 2)
        assert round(self.subject.pluto.abs_pos, 2) == round(self.expected_output["pluto"]["abs_pos"], 2)
        assert self.subject.pluto.emoji == self.expected_output["pluto"]["emoji"]
        assert self.subject.pluto.point_type == self.expected_output["pluto"]["point_type"]
        assert self.subject.pluto.house == self.expected_output["pluto"]["house"]
        assert self.subject.pluto.retrograde == self.expected_output["pluto"]["retrograde"]

    def test_mean_node(self):
        assert self.subject.mean_node.name == self.expected_output["mean_node"]["name"]
        assert self.subject.mean_node.quality == self.expected_output["mean_node"]["quality"]
        assert self.subject.mean_node.element == self.expected_output["mean_node"]["element"]
        assert self.subject.mean_node.sign == self.expected_output["mean_node"]["sign"]
        assert self.subject.mean_node.sign_num == self.expected_output["mean_node"]["sign_num"]
        assert round(self.subject.mean_node.position, 2) == round(self.expected_output["mean_node"]["position"], 2)
        assert round(self.subject.mean_node.abs_pos, 2) == round(self.expected_output["mean_node"]["abs_pos"], 2)
        assert self.subject.mean_node.emoji == self.expected_output["mean_node"]["emoji"]
        assert self.subject.mean_node.point_type == self.expected_output["mean_node"]["point_type"]
        assert self.subject.mean_node.house == self.expected_output["mean_node"]["house"]
        assert self.subject.mean_node.retrograde == self.expected_output["mean_node"]["retrograde"]

    def test_true_node(self):
        assert self.subject.true_node.name == self.expected_output["true_node"]["name"]
        assert self.subject.true_node.quality == self.expected_output["true_node"]["quality"]
        assert self.subject.true_node.element == self.expected_output["true_node"]["element"]
        assert self.subject.true_node.sign == self.expected_output["true_node"]["sign"]
        assert self.subject.true_node.sign_num == self.expected_output["true_node"]["sign_num"]
        assert round(self.subject.true_node.position, 2) == round(self.expected_output["true_node"]["position"], 2)
        assert round(self.subject.true_node.abs_pos, 2) == round(self.expected_output["true_node"]["abs_pos"], 2)
        assert self.subject.true_node.emoji == self.expected_output["true_node"]["emoji"]
        assert self.subject.true_node.point_type == self.expected_output["true_node"]["point_type"]
        assert self.subject.true_node.house == self.expected_output["true_node"]["house"]
        assert self.subject.true_node.retrograde == self.expected_output["true_node"]["retrograde"]

    def test_mean_south_node(self):
        assert self.subject.mean_south_node.name == self.expected_output["mean_south_node"]["name"]
        assert self.subject.mean_south_node.quality == self.expected_output["mean_south_node"]["quality"]
        assert self.subject.mean_south_node.element == self.expected_output["mean_south_node"]["element"]
        assert self.subject.mean_south_node.sign == self.expected_output["mean_south_node"]["sign"]
        assert self.subject.mean_south_node.sign_num == self.expected_output["mean_south_node"]["sign_num"]
        assert round(self.subject.mean_south_node.position, 2) == round(self.expected_output["mean_south_node"]["position"], 2)
        assert round(self.subject.mean_south_node.abs_pos, 2) == round(self.expected_output["mean_south_node"]["abs_pos"], 2)
        assert self.subject.mean_south_node.emoji == self.expected_output["mean_south_node"]["emoji"]
        assert self.subject.mean_south_node.point_type == self.expected_output["mean_south_node"]["point_type"]
        assert self.subject.mean_south_node.house == self.expected_output["mean_south_node"]["house"]
        assert self.subject.mean_south_node.retrograde == self.expected_output["mean_south_node"]["retrograde"]

    def test_true_south_node(self):
        assert self.subject.true_south_node.name == self.expected_output["true_south_node"]["name"]
        assert self.subject.true_south_node.quality == self.expected_output["true_south_node"]["quality"]
        assert self.subject.true_south_node.element == self.expected_output["true_south_node"]["element"]
        assert self.subject.true_south_node.sign == self.expected_output["true_south_node"]["sign"]
        assert self.subject.true_south_node.sign_num == self.expected_output["true_south_node"]["sign_num"]
        assert round(self.subject.true_south_node.position, 2) == round(self.expected_output["true_south_node"]["position"], 2)
        assert round(self.subject.true_south_node.abs_pos, 2) == round(self.expected_output["true_south_node"]["abs_pos"], 2)
        assert self.subject.true_south_node.emoji == self.expected_output["true_south_node"]["emoji"]
        assert self.subject.true_south_node.point_type == self.expected_output["true_south_node"]["point_type"]
        assert self.subject.true_south_node.house == self.expected_output["true_south_node"]["house"]
        assert self.subject.true_south_node.retrograde == self.expected_output["true_south_node"]["retrograde"]

    def test_first_house(self):
        assert self.subject.first_house.name == self.expected_output["first_house"]["name"]
        assert self.subject.first_house.quality == self.expected_output["first_house"]["quality"]
        assert self.subject.first_house.element == self.expected_output["first_house"]["element"]
        assert self.subject.first_house.sign == self.expected_output["first_house"]["sign"]
        assert self.subject.first_house.sign_num == self.expected_output["first_house"]["sign_num"]
        assert round(self.subject.first_house.position, 2) == round(self.expected_output["first_house"]["position"], 2)
        assert round(self.subject.first_house.abs_pos, 2) == round(self.expected_output["first_house"]["abs_pos"], 2)
        assert self.subject.first_house.emoji == self.expected_output["first_house"]["emoji"]
        assert self.subject.first_house.point_type == self.expected_output["first_house"]["point_type"]

    def test_second_house(self):
        assert self.subject.second_house.name == self.expected_output["second_house"]["name"]
        assert self.subject.second_house.quality == self.expected_output["second_house"]["quality"]
        assert self.subject.second_house.element == self.expected_output["second_house"]["element"]
        assert self.subject.second_house.sign == self.expected_output["second_house"]["sign"]
        assert self.subject.second_house.sign_num == self.expected_output["second_house"]["sign_num"]
        assert round(self.subject.second_house.position, 2) == round(self.expected_output["second_house"]["position"], 2)
        assert round(self.subject.second_house.abs_pos, 2) == round(self.expected_output["second_house"]["abs_pos"], 2)
        assert self.subject.second_house.emoji == self.expected_output["second_house"]["emoji"]
        assert self.subject.second_house.point_type == self.expected_output["second_house"]["point_type"]

    def test_third_house(self):
        assert self.subject.third_house.name == self.expected_output["third_house"]["name"]
        assert self.subject.third_house.quality == self.expected_output["third_house"]["quality"]
        assert self.subject.third_house.element == self.expected_output["third_house"]["element"]
        assert self.subject.third_house.sign == self.expected_output["third_house"]["sign"]
        assert self.subject.third_house.sign_num == self.expected_output["third_house"]["sign_num"]
        assert round(self.subject.third_house.position, 2) == round(self.expected_output["third_house"]["position"], 2)
        assert round(self.subject.third_house.abs_pos, 2) == round(self.expected_output["third_house"]["abs_pos"], 2)
        assert self.subject.third_house.emoji == self.expected_output["third_house"]["emoji"]
        assert self.subject.third_house.point_type == self.expected_output["third_house"]["point_type"]

    def test_fourth_house(self):
        assert self.subject.fourth_house.name == self.expected_output["fourth_house"]["name"]
        assert self.subject.fourth_house.quality == self.expected_output["fourth_house"]["quality"]
        assert self.subject.fourth_house.element == self.expected_output["fourth_house"]["element"]
        assert self.subject.fourth_house.sign == self.expected_output["fourth_house"]["sign"]
        assert self.subject.fourth_house.sign_num == self.expected_output["fourth_house"]["sign_num"]
        assert round(self.subject.fourth_house.position, 2) == round(self.expected_output["fourth_house"]["position"], 2)
        assert round(self.subject.fourth_house.abs_pos, 2) == round(self.expected_output["fourth_house"]["abs_pos"], 2)
        assert self.subject.fourth_house.emoji == self.expected_output["fourth_house"]["emoji"]
        assert self.subject.fourth_house.point_type == self.expected_output["fourth_house"]["point_type"]

    def test_fifth_house(self):
        assert self.subject.fifth_house.name == self.expected_output["fifth_house"]["name"]
        assert self.subject.fifth_house.quality == self.expected_output["fifth_house"]["quality"]
        assert self.subject.fifth_house.element == self.expected_output["fifth_house"]["element"]
        assert self.subject.fifth_house.sign == self.expected_output["fifth_house"]["sign"]
        assert self.subject.fifth_house.sign_num == self.expected_output["fifth_house"]["sign_num"]
        assert round(self.subject.fifth_house.position, 2) == round(self.expected_output["fifth_house"]["position"], 2)
        assert round(self.subject.fifth_house.abs_pos, 2) == round(self.expected_output["fifth_house"]["abs_pos"], 2)
        assert self.subject.fifth_house.emoji == self.expected_output["fifth_house"]["emoji"]
        assert self.subject.fifth_house.point_type == self.expected_output["fifth_house"]["point_type"]

    def test_sixth_house(self):
        assert self.subject.sixth_house.name == self.expected_output["sixth_house"]["name"]
        assert self.subject.sixth_house.quality == self.expected_output["sixth_house"]["quality"]
        assert self.subject.sixth_house.element == self.expected_output["sixth_house"]["element"]
        assert self.subject.sixth_house.sign == self.expected_output["sixth_house"]["sign"]
        assert self.subject.sixth_house.sign_num == self.expected_output["sixth_house"]["sign_num"]
        assert round(self.subject.sixth_house.position, 2) == round(self.expected_output["sixth_house"]["position"], 2)
        assert round(self.subject.sixth_house.abs_pos, 2) == round(self.expected_output["sixth_house"]["abs_pos"], 2)
        assert self.subject.sixth_house.emoji == self.expected_output["sixth_house"]["emoji"]
        assert self.subject.sixth_house.point_type == self.expected_output["sixth_house"]["point_type"]

    def test_seventh_house(self):
        assert self.subject.seventh_house.name == self.expected_output["seventh_house"]["name"]
        assert self.subject.seventh_house.quality == self.expected_output["seventh_house"]["quality"]
        assert self.subject.seventh_house.element == self.expected_output["seventh_house"]["element"]
        assert self.subject.seventh_house.sign == self.expected_output["seventh_house"]["sign"]
        assert self.subject.seventh_house.sign_num == self.expected_output["seventh_house"]["sign_num"]
        assert round(self.subject.seventh_house.position, 2) == round(self.expected_output["seventh_house"]["position"], 2)
        assert round(self.subject.seventh_house.abs_pos, 2) == round(self.expected_output["seventh_house"]["abs_pos"], 2)
        assert self.subject.seventh_house.emoji == self.expected_output["seventh_house"]["emoji"]
        assert self.subject.seventh_house.point_type == self.expected_output["seventh_house"]["point_type"]

    def test_eighth_house(self):
        assert self.subject.eighth_house.name == self.expected_output["eighth_house"]["name"]
        assert self.subject.eighth_house.quality == self.expected_output["eighth_house"]["quality"]
        assert self.subject.eighth_house.element == self.expected_output["eighth_house"]["element"]
        assert self.subject.eighth_house.sign == self.expected_output["eighth_house"]["sign"]
        assert self.subject.eighth_house.sign_num == self.expected_output["eighth_house"]["sign_num"]
        assert round(self.subject.eighth_house.position, 2) == round(self.expected_output["eighth_house"]["position"], 2)
        assert round(self.subject.eighth_house.abs_pos, 2) == round(self.expected_output["eighth_house"]["abs_pos"], 2)
        assert self.subject.eighth_house.emoji == self.expected_output["eighth_house"]["emoji"]
        assert self.subject.eighth_house.point_type == self.expected_output["eighth_house"]["point_type"]

    def test_ninth_house(self):
        assert self.subject.ninth_house.name == self.expected_output["ninth_house"]["name"]
        assert self.subject.ninth_house.quality == self.expected_output["ninth_house"]["quality"]
        assert self.subject.ninth_house.element == self.expected_output["ninth_house"]["element"]
        assert self.subject.ninth_house.sign == self.expected_output["ninth_house"]["sign"]
        assert self.subject.ninth_house.sign_num == self.expected_output["ninth_house"]["sign_num"]
        assert round(self.subject.ninth_house.position, 2) == round(self.expected_output["ninth_house"]["position"], 2)
        assert round(self.subject.ninth_house.abs_pos, 2) == round(self.expected_output["ninth_house"]["abs_pos"], 2)
        assert self.subject.ninth_house.emoji == self.expected_output["ninth_house"]["emoji"]
        assert self.subject.ninth_house.point_type == self.expected_output["ninth_house"]["point_type"]

    def test_tenth_house(self):
        assert self.subject.tenth_house.name == self.expected_output["tenth_house"]["name"]
        assert self.subject.tenth_house.quality == self.expected_output["tenth_house"]["quality"]
        assert self.subject.tenth_house.element == self.expected_output["tenth_house"]["element"]
        assert self.subject.tenth_house.sign == self.expected_output["tenth_house"]["sign"]
        assert self.subject.tenth_house.sign_num == self.expected_output["tenth_house"]["sign_num"]
        assert round(self.subject.tenth_house.position, 2) == round(self.expected_output["tenth_house"]["position"], 2)
        assert round(self.subject.tenth_house.abs_pos, 2) == round(self.expected_output["tenth_house"]["abs_pos"], 2)
        assert self.subject.tenth_house.emoji == self.expected_output["tenth_house"]["emoji"]
        assert self.subject.tenth_house.point_type == self.expected_output["tenth_house"]["point_type"]

    def test_eleventh_house(self):
        assert self.subject.eleventh_house.name == self.expected_output["eleventh_house"]["name"]
        assert self.subject.eleventh_house.quality == self.expected_output["eleventh_house"]["quality"]
        assert self.subject.eleventh_house.element == self.expected_output["eleventh_house"]["element"]
        assert self.subject.eleventh_house.sign == self.expected_output["eleventh_house"]["sign"]
        assert self.subject.eleventh_house.sign_num == self.expected_output["eleventh_house"]["sign_num"]
        assert round(self.subject.eleventh_house.position, 2) == round(self.expected_output["eleventh_house"]["position"], 2)
        assert round(self.subject.eleventh_house.abs_pos, 2) == round(self.expected_output["eleventh_house"]["abs_pos"], 2)
        assert self.subject.eleventh_house.emoji == self.expected_output["eleventh_house"]["emoji"]
        assert self.subject.eleventh_house.point_type == self.expected_output["eleventh_house"]["point_type"]

    def test_twelfth_house(self):
        assert self.subject.twelfth_house.name == self.expected_output["twelfth_house"]["name"]
        assert self.subject.twelfth_house.quality == self.expected_output["twelfth_house"]["quality"]
        assert self.subject.twelfth_house.element == self.expected_output["twelfth_house"]["element"]
        assert self.subject.twelfth_house.sign == self.expected_output["twelfth_house"]["sign"]
        assert self.subject.twelfth_house.sign_num == self.expected_output["twelfth_house"]["sign_num"]
        assert round(self.subject.twelfth_house.position, 2) == round(self.expected_output["twelfth_house"]["position"], 2)
        assert round(self.subject.twelfth_house.abs_pos, 2) == round(self.expected_output["twelfth_house"]["abs_pos"], 2)
        assert self.subject.twelfth_house.emoji == self.expected_output["twelfth_house"]["emoji"]
        assert self.subject.twelfth_house.point_type == self.expected_output["twelfth_house"]["point_type"]

    def test_lunar_phase(self):
        assert self.subject.lunar_phase.model_dump() == self.expected_output["lunar_phase"]


if __name__ == "__main__":
    import pytest
    import logging

    # Set the log level to CRITICAL
    logging.basicConfig(level=logging.CRITICAL)

    pytest.main(["-vv", "--log-level=CRITICAL", "--log-cli-level=CRITICAL", __file__])
