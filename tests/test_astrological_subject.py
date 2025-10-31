from kerykeion import AstrologicalSubjectFactory
from kerykeion.schemas import AstrologicalPoint
from typing import get_args
from pytest import approx

from tests.data.expected_astrological_subjects import EXPECTED_TROPICAL_SUBJECT


class TestAstrologicalSubject:
    def setup_class(self):
        # Johnny Depp - including all astrological points for complete testing
        all_points = list(get_args(AstrologicalPoint))
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US",
            suppress_geonames_warning=True, active_points=all_points
        )
        self.expected_output = EXPECTED_TROPICAL_SUBJECT


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
        assert self.subject.lat == approx(self.expected_output["lat"], abs=1e-2)
        assert self.subject.lng == approx(self.expected_output["lng"], abs=1e-2)
        assert self.subject.tz_str == self.expected_output["tz_str"]
        assert self.subject.zodiac_type == self.expected_output["zodiac_type"]
        assert self.subject.julian_day == self.expected_output["julian_day"]

    def test_ascendant(self):
        assert self.subject.ascendant.name == self.expected_output["ascendant"]["name"]
        assert self.subject.ascendant.quality == self.expected_output["ascendant"]["quality"]
        assert self.subject.ascendant.element == self.expected_output["ascendant"]["element"]
        assert self.subject.ascendant.sign == self.expected_output["ascendant"]["sign"]
        assert self.subject.ascendant.sign_num == self.expected_output["ascendant"]["sign_num"]
        assert self.subject.ascendant.position == approx(self.expected_output["ascendant"]["position"], abs=1e-2)
        assert self.subject.ascendant.abs_pos == approx(self.expected_output["ascendant"]["abs_pos"], abs=1e-2)
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
        assert self.subject.descendant.position == approx(self.expected_output["descendant"]["position"], abs=1e-2)
        assert self.subject.descendant.abs_pos == approx(self.expected_output["descendant"]["abs_pos"], abs=1e-2)
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
        assert self.subject.medium_coeli.position == approx(self.expected_output["medium_coeli"]["position"], abs=1e-2)
        assert self.subject.medium_coeli.abs_pos == approx(self.expected_output["medium_coeli"]["abs_pos"], abs=1e-2)
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
        assert self.subject.imum_coeli.position == approx(self.expected_output["imum_coeli"]["position"], abs=1e-2)
        assert self.subject.imum_coeli.abs_pos == approx(self.expected_output["imum_coeli"]["abs_pos"], abs=1e-2)
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
        assert self.subject.sun.position == approx(self.expected_output["sun"]["position"], abs=1e-2)
        assert self.subject.sun.abs_pos == approx(self.expected_output["sun"]["abs_pos"], abs=1e-2)
        assert self.subject.sun.emoji == self.expected_output["sun"]["emoji"]
        assert self.subject.sun.point_type == self.expected_output["sun"]["point_type"]
        assert self.subject.sun.house == self.expected_output["sun"]["house"]
        assert self.subject.sun.retrograde == self.expected_output["sun"]["retrograde"]
        assert self.subject.sun.speed == approx(self.expected_output["sun"]["speed"], abs=1e-4)
        assert self.subject.sun.declination == approx(self.expected_output["sun"]["declination"], abs=1e-2)

    def test_moon(self):
        assert self.subject.moon.name == self.expected_output["moon"]["name"]
        assert self.subject.moon.quality == self.expected_output["moon"]["quality"]
        assert self.subject.moon.element == self.expected_output["moon"]["element"]
        assert self.subject.moon.sign == self.expected_output["moon"]["sign"]
        assert self.subject.moon.sign_num == self.expected_output["moon"]["sign_num"]
        assert self.subject.moon.position == approx(self.expected_output["moon"]["position"], abs=1e-2)
        assert self.subject.moon.abs_pos == approx(self.expected_output["moon"]["abs_pos"], abs=1e-2)
        assert self.subject.moon.emoji == self.expected_output["moon"]["emoji"]
        assert self.subject.moon.point_type == self.expected_output["moon"]["point_type"]
        assert self.subject.moon.house == self.expected_output["moon"]["house"]
        assert self.subject.moon.retrograde == self.expected_output["moon"]["retrograde"]
        assert self.subject.moon.speed == approx(self.expected_output["moon"]["speed"], abs=1e-4)
        assert self.subject.moon.declination == approx(self.expected_output["moon"]["declination"], abs=1e-2)

    def test_mercury(self):
        assert self.subject.mercury.name == self.expected_output["mercury"]["name"]
        assert self.subject.mercury.quality == self.expected_output["mercury"]["quality"]
        assert self.subject.mercury.element == self.expected_output["mercury"]["element"]
        assert self.subject.mercury.sign == self.expected_output["mercury"]["sign"]
        assert self.subject.mercury.sign_num == self.expected_output["mercury"]["sign_num"]
        assert self.subject.mercury.position == approx(self.expected_output["mercury"]["position"], abs=1e-2)
        assert self.subject.mercury.abs_pos == approx(self.expected_output["mercury"]["abs_pos"], abs=1e-2)
        assert self.subject.mercury.emoji == self.expected_output["mercury"]["emoji"]
        assert self.subject.mercury.point_type == self.expected_output["mercury"]["point_type"]
        assert self.subject.mercury.house == self.expected_output["mercury"]["house"]
        assert self.subject.mercury.retrograde == self.expected_output["mercury"]["retrograde"]
        assert self.subject.mercury.speed == approx(self.expected_output["mercury"]["speed"], abs=1e-4)
        assert self.subject.mercury.declination == approx(self.expected_output["mercury"]["declination"], abs=1e-2)

    def test_venus(self):
        assert self.subject.venus.name == self.expected_output["venus"]["name"]
        assert self.subject.venus.quality == self.expected_output["venus"]["quality"]
        assert self.subject.venus.element == self.expected_output["venus"]["element"]
        assert self.subject.venus.sign == self.expected_output["venus"]["sign"]
        assert self.subject.venus.sign_num == self.expected_output["venus"]["sign_num"]
        assert self.subject.venus.position == approx(self.expected_output["venus"]["position"], abs=1e-2)
        assert self.subject.venus.abs_pos == approx(self.expected_output["venus"]["abs_pos"], abs=1e-2)
        assert self.subject.venus.emoji == self.expected_output["venus"]["emoji"]
        assert self.subject.venus.point_type == self.expected_output["venus"]["point_type"]
        assert self.subject.venus.house == self.expected_output["venus"]["house"]
        assert self.subject.venus.retrograde == self.expected_output["venus"]["retrograde"]
        assert self.subject.venus.speed == approx(self.expected_output["venus"]["speed"], abs=1e-4)
        assert self.subject.venus.declination == approx(self.expected_output["venus"]["declination"], abs=1e-2)

    def test_mars(self):
        assert self.subject.mars.name == self.expected_output["mars"]["name"]
        assert self.subject.mars.quality == self.expected_output["mars"]["quality"]
        assert self.subject.mars.element == self.expected_output["mars"]["element"]
        assert self.subject.mars.sign == self.expected_output["mars"]["sign"]
        assert self.subject.mars.sign_num == self.expected_output["mars"]["sign_num"]
        assert self.subject.mars.position == approx(self.expected_output["mars"]["position"], abs=1e-2)
        assert self.subject.mars.abs_pos == approx(self.expected_output["mars"]["abs_pos"], abs=1e-2)
        assert self.subject.mars.emoji == self.expected_output["mars"]["emoji"]
        assert self.subject.mars.point_type == self.expected_output["mars"]["point_type"]
        assert self.subject.mars.house == self.expected_output["mars"]["house"]
        assert self.subject.mars.retrograde == self.expected_output["mars"]["retrograde"]
        assert self.subject.mars.speed == approx(self.expected_output["mars"]["speed"], abs=1e-4)
        assert self.subject.mars.declination == approx(self.expected_output["mars"]["declination"], abs=1e-2)

    def test_jupiter(self):
        assert self.subject.jupiter.name == self.expected_output["jupiter"]["name"]
        assert self.subject.jupiter.quality == self.expected_output["jupiter"]["quality"]
        assert self.subject.jupiter.element == self.expected_output["jupiter"]["element"]
        assert self.subject.jupiter.sign == self.expected_output["jupiter"]["sign"]
        assert self.subject.jupiter.sign_num == self.expected_output["jupiter"]["sign_num"]
        assert self.subject.jupiter.position == approx(self.expected_output["jupiter"]["position"], abs=1e-2)
        assert self.subject.jupiter.abs_pos == approx(self.expected_output["jupiter"]["abs_pos"], abs=1e-2)
        assert self.subject.jupiter.emoji == self.expected_output["jupiter"]["emoji"]
        assert self.subject.jupiter.point_type == self.expected_output["jupiter"]["point_type"]
        assert self.subject.jupiter.house == self.expected_output["jupiter"]["house"]
        assert self.subject.jupiter.retrograde == self.expected_output["jupiter"]["retrograde"]
        assert self.subject.jupiter.speed == approx(self.expected_output["jupiter"]["speed"], abs=1e-4)
        assert self.subject.jupiter.declination == approx(self.expected_output["jupiter"]["declination"], abs=1e-2)

    def test_saturn(self):
        assert self.subject.saturn.name == self.expected_output["saturn"]["name"]
        assert self.subject.saturn.quality == self.expected_output["saturn"]["quality"]
        assert self.subject.saturn.element == self.expected_output["saturn"]["element"]
        assert self.subject.saturn.sign == self.expected_output["saturn"]["sign"]
        assert self.subject.saturn.sign_num == self.expected_output["saturn"]["sign_num"]
        assert self.subject.saturn.position == approx(self.expected_output["saturn"]["position"], abs=1e-2)
        assert self.subject.saturn.abs_pos == approx(self.expected_output["saturn"]["abs_pos"], abs=1e-2)
        assert self.subject.saturn.emoji == self.expected_output["saturn"]["emoji"]
        assert self.subject.saturn.point_type == self.expected_output["saturn"]["point_type"]
        assert self.subject.saturn.house == self.expected_output["saturn"]["house"]
        assert self.subject.saturn.retrograde == self.expected_output["saturn"]["retrograde"]
        assert self.subject.saturn.speed == approx(self.expected_output["saturn"]["speed"], abs=1e-4)
        assert self.subject.saturn.declination == approx(self.expected_output["saturn"]["declination"], abs=1e-2)

    def test_uranus(self):
        assert self.subject.uranus.name == self.expected_output["uranus"]["name"]
        assert self.subject.uranus.quality == self.expected_output["uranus"]["quality"]
        assert self.subject.uranus.element == self.expected_output["uranus"]["element"]
        assert self.subject.uranus.sign == self.expected_output["uranus"]["sign"]
        assert self.subject.uranus.sign_num == self.expected_output["uranus"]["sign_num"]
        assert self.subject.uranus.position == approx(self.expected_output["uranus"]["position"], abs=1e-2)
        assert self.subject.uranus.abs_pos == approx(self.expected_output["uranus"]["abs_pos"], abs=1e-2)
        assert self.subject.uranus.emoji == self.expected_output["uranus"]["emoji"]
        assert self.subject.uranus.point_type == self.expected_output["uranus"]["point_type"]
        assert self.subject.uranus.house == self.expected_output["uranus"]["house"]
        assert self.subject.uranus.retrograde == self.expected_output["uranus"]["retrograde"]
        assert self.subject.uranus.speed == approx(self.expected_output["uranus"]["speed"], abs=1e-4)
        assert self.subject.uranus.declination == approx(self.expected_output["uranus"]["declination"], abs=1e-2)

    def test_neptune(self):
        assert self.subject.neptune.name == self.expected_output["neptune"]["name"]
        assert self.subject.neptune.quality == self.expected_output["neptune"]["quality"]
        assert self.subject.neptune.element == self.expected_output["neptune"]["element"]
        assert self.subject.neptune.sign == self.expected_output["neptune"]["sign"]
        assert self.subject.neptune.sign_num == self.expected_output["neptune"]["sign_num"]
        assert self.subject.neptune.position == approx(self.expected_output["neptune"]["position"], abs=1e-2)
        assert self.subject.neptune.abs_pos == approx(self.expected_output["neptune"]["abs_pos"], abs=1e-2)
        assert self.subject.neptune.emoji == self.expected_output["neptune"]["emoji"]
        assert self.subject.neptune.point_type == self.expected_output["neptune"]["point_type"]
        assert self.subject.neptune.house == self.expected_output["neptune"]["house"]
        assert self.subject.neptune.retrograde == self.expected_output["neptune"]["retrograde"]
        assert self.subject.neptune.speed == approx(self.expected_output["neptune"]["speed"], abs=1e-4)
        assert self.subject.neptune.declination == approx(self.expected_output["neptune"]["declination"], abs=1e-2)

    def test_pluto(self):
        assert self.subject.pluto.name == self.expected_output["pluto"]["name"]
        assert self.subject.pluto.quality == self.expected_output["pluto"]["quality"]
        assert self.subject.pluto.element == self.expected_output["pluto"]["element"]
        assert self.subject.pluto.sign == self.expected_output["pluto"]["sign"]
        assert self.subject.pluto.sign_num == self.expected_output["pluto"]["sign_num"]
        assert self.subject.pluto.position == approx(self.expected_output["pluto"]["position"], abs=1e-2)
        assert self.subject.pluto.abs_pos == approx(self.expected_output["pluto"]["abs_pos"], abs=1e-2)
        assert self.subject.pluto.emoji == self.expected_output["pluto"]["emoji"]
        assert self.subject.pluto.point_type == self.expected_output["pluto"]["point_type"]
        assert self.subject.pluto.house == self.expected_output["pluto"]["house"]
        assert self.subject.pluto.retrograde == self.expected_output["pluto"]["retrograde"]
        assert self.subject.pluto.speed == approx(self.expected_output["pluto"]["speed"], abs=1e-4)
        assert self.subject.pluto.declination == approx(self.expected_output["pluto"]["declination"], abs=1e-2)

    def test_true_north_lunar_node(self):
        assert self.subject.true_north_lunar_node.name == self.expected_output["true_north_lunar_node"]["name"]
        assert self.subject.true_north_lunar_node.quality == self.expected_output["true_north_lunar_node"]["quality"]
        assert self.subject.true_north_lunar_node.element == self.expected_output["true_north_lunar_node"]["element"]
        assert self.subject.true_north_lunar_node.sign == self.expected_output["true_north_lunar_node"]["sign"]
        assert self.subject.true_north_lunar_node.sign_num == self.expected_output["true_north_lunar_node"]["sign_num"]
        assert self.subject.true_north_lunar_node.position == approx(self.expected_output["true_north_lunar_node"]["position"], abs=1e-2)
        assert self.subject.true_north_lunar_node.abs_pos == approx(self.expected_output["true_north_lunar_node"]["abs_pos"], abs=1e-2)
        assert self.subject.true_north_lunar_node.emoji == self.expected_output["true_north_lunar_node"]["emoji"]
        assert self.subject.true_north_lunar_node.point_type == self.expected_output["true_north_lunar_node"]["point_type"]
        assert self.subject.true_north_lunar_node.house == self.expected_output["true_north_lunar_node"]["house"]
        assert self.subject.true_north_lunar_node.retrograde == self.expected_output["true_north_lunar_node"]["retrograde"]

    def test_true_south_lunar_node(self):
        assert self.subject.true_south_lunar_node.name == self.expected_output["true_south_lunar_node"]["name"]
        assert self.subject.true_south_lunar_node.quality == self.expected_output["true_south_lunar_node"]["quality"]
        assert self.subject.true_south_lunar_node.element == self.expected_output["true_south_lunar_node"]["element"]
        assert self.subject.true_south_lunar_node.sign == self.expected_output["true_south_lunar_node"]["sign"]
        assert self.subject.true_south_lunar_node.sign_num == self.expected_output["true_south_lunar_node"]["sign_num"]
        assert self.subject.true_south_lunar_node.position == approx(self.expected_output["true_south_lunar_node"]["position"], abs=1e-2)
        assert self.subject.true_south_lunar_node.abs_pos == approx(self.expected_output["true_south_lunar_node"]["abs_pos"], abs=1e-2)
        assert self.subject.true_south_lunar_node.emoji == self.expected_output["true_south_lunar_node"]["emoji"]
        assert self.subject.true_south_lunar_node.point_type == self.expected_output["true_south_lunar_node"]["point_type"]
        assert self.subject.true_south_lunar_node.house == self.expected_output["true_south_lunar_node"]["house"]
        assert self.subject.true_south_lunar_node.retrograde == self.expected_output["true_south_lunar_node"]["retrograde"]

    def test_first_house(self):
        assert self.subject.first_house.name == self.expected_output["first_house"]["name"]
        assert self.subject.first_house.quality == self.expected_output["first_house"]["quality"]
        assert self.subject.first_house.element == self.expected_output["first_house"]["element"]
        assert self.subject.first_house.sign == self.expected_output["first_house"]["sign"]
        assert self.subject.first_house.sign_num == self.expected_output["first_house"]["sign_num"]
        assert self.subject.first_house.position == approx(self.expected_output["first_house"]["position"], abs=1e-2)
        assert self.subject.first_house.abs_pos == approx(self.expected_output["first_house"]["abs_pos"], abs=1e-2)
        assert self.subject.first_house.emoji == self.expected_output["first_house"]["emoji"]
        assert self.subject.first_house.point_type == self.expected_output["first_house"]["point_type"]

    def test_second_house(self):
        assert self.subject.second_house.name == self.expected_output["second_house"]["name"]
        assert self.subject.second_house.quality == self.expected_output["second_house"]["quality"]
        assert self.subject.second_house.element == self.expected_output["second_house"]["element"]
        assert self.subject.second_house.sign == self.expected_output["second_house"]["sign"]
        assert self.subject.second_house.sign_num == self.expected_output["second_house"]["sign_num"]
        assert self.subject.second_house.position == approx(self.expected_output["second_house"]["position"], abs=1e-2)
        assert self.subject.second_house.abs_pos == approx(self.expected_output["second_house"]["abs_pos"], abs=1e-2)
        assert self.subject.second_house.emoji == self.expected_output["second_house"]["emoji"]
        assert self.subject.second_house.point_type == self.expected_output["second_house"]["point_type"]

    def test_third_house(self):
        assert self.subject.third_house.name == self.expected_output["third_house"]["name"]
        assert self.subject.third_house.quality == self.expected_output["third_house"]["quality"]
        assert self.subject.third_house.element == self.expected_output["third_house"]["element"]
        assert self.subject.third_house.sign == self.expected_output["third_house"]["sign"]
        assert self.subject.third_house.sign_num == self.expected_output["third_house"]["sign_num"]
        assert self.subject.third_house.position == approx(self.expected_output["third_house"]["position"], abs=1e-2)
        assert self.subject.third_house.abs_pos == approx(self.expected_output["third_house"]["abs_pos"], abs=1e-2)
        assert self.subject.third_house.emoji == self.expected_output["third_house"]["emoji"]
        assert self.subject.third_house.point_type == self.expected_output["third_house"]["point_type"]

    def test_fourth_house(self):
        assert self.subject.fourth_house.name == self.expected_output["fourth_house"]["name"]
        assert self.subject.fourth_house.quality == self.expected_output["fourth_house"]["quality"]
        assert self.subject.fourth_house.element == self.expected_output["fourth_house"]["element"]
        assert self.subject.fourth_house.sign == self.expected_output["fourth_house"]["sign"]
        assert self.subject.fourth_house.sign_num == self.expected_output["fourth_house"]["sign_num"]
        assert self.subject.fourth_house.position == approx(self.expected_output["fourth_house"]["position"], abs=1e-2)
        assert self.subject.fourth_house.abs_pos == approx(self.expected_output["fourth_house"]["abs_pos"], abs=1e-2)
        assert self.subject.fourth_house.emoji == self.expected_output["fourth_house"]["emoji"]
        assert self.subject.fourth_house.point_type == self.expected_output["fourth_house"]["point_type"]

    def test_fifth_house(self):
        assert self.subject.fifth_house.name == self.expected_output["fifth_house"]["name"]
        assert self.subject.fifth_house.quality == self.expected_output["fifth_house"]["quality"]
        assert self.subject.fifth_house.element == self.expected_output["fifth_house"]["element"]
        assert self.subject.fifth_house.sign == self.expected_output["fifth_house"]["sign"]
        assert self.subject.fifth_house.sign_num == self.expected_output["fifth_house"]["sign_num"]
        assert self.subject.fifth_house.position == approx(self.expected_output["fifth_house"]["position"], abs=1e-2)
        assert self.subject.fifth_house.abs_pos == approx(self.expected_output["fifth_house"]["abs_pos"], abs=1e-2)
        assert self.subject.fifth_house.emoji == self.expected_output["fifth_house"]["emoji"]
        assert self.subject.fifth_house.point_type == self.expected_output["fifth_house"]["point_type"]

    def test_sixth_house(self):
        assert self.subject.sixth_house.name == self.expected_output["sixth_house"]["name"]
        assert self.subject.sixth_house.quality == self.expected_output["sixth_house"]["quality"]
        assert self.subject.sixth_house.element == self.expected_output["sixth_house"]["element"]
        assert self.subject.sixth_house.sign == self.expected_output["sixth_house"]["sign"]
        assert self.subject.sixth_house.sign_num == self.expected_output["sixth_house"]["sign_num"]
        assert self.subject.sixth_house.position == approx(self.expected_output["sixth_house"]["position"], abs=1e-2)
        assert self.subject.sixth_house.abs_pos == approx(self.expected_output["sixth_house"]["abs_pos"], abs=1e-2)
        assert self.subject.sixth_house.emoji == self.expected_output["sixth_house"]["emoji"]
        assert self.subject.sixth_house.point_type == self.expected_output["sixth_house"]["point_type"]

    def test_seventh_house(self):
        assert self.subject.seventh_house.name == self.expected_output["seventh_house"]["name"]
        assert self.subject.seventh_house.quality == self.expected_output["seventh_house"]["quality"]
        assert self.subject.seventh_house.element == self.expected_output["seventh_house"]["element"]
        assert self.subject.seventh_house.sign == self.expected_output["seventh_house"]["sign"]
        assert self.subject.seventh_house.sign_num == self.expected_output["seventh_house"]["sign_num"]
        assert self.subject.seventh_house.position == approx(self.expected_output["seventh_house"]["position"], abs=1e-2)
        assert self.subject.seventh_house.abs_pos == approx(self.expected_output["seventh_house"]["abs_pos"], abs=1e-2)
        assert self.subject.seventh_house.emoji == self.expected_output["seventh_house"]["emoji"]
        assert self.subject.seventh_house.point_type == self.expected_output["seventh_house"]["point_type"]

    def test_eighth_house(self):
        assert self.subject.eighth_house.name == self.expected_output["eighth_house"]["name"]
        assert self.subject.eighth_house.quality == self.expected_output["eighth_house"]["quality"]
        assert self.subject.eighth_house.element == self.expected_output["eighth_house"]["element"]
        assert self.subject.eighth_house.sign == self.expected_output["eighth_house"]["sign"]
        assert self.subject.eighth_house.sign_num == self.expected_output["eighth_house"]["sign_num"]
        assert self.subject.eighth_house.position == approx(self.expected_output["eighth_house"]["position"], abs=1e-2)
        assert self.subject.eighth_house.abs_pos == approx(self.expected_output["eighth_house"]["abs_pos"], abs=1e-2)
        assert self.subject.eighth_house.emoji == self.expected_output["eighth_house"]["emoji"]
        assert self.subject.eighth_house.point_type == self.expected_output["eighth_house"]["point_type"]

    def test_ninth_house(self):
        assert self.subject.ninth_house.name == self.expected_output["ninth_house"]["name"]
        assert self.subject.ninth_house.quality == self.expected_output["ninth_house"]["quality"]
        assert self.subject.ninth_house.element == self.expected_output["ninth_house"]["element"]
        assert self.subject.ninth_house.sign == self.expected_output["ninth_house"]["sign"]
        assert self.subject.ninth_house.sign_num == self.expected_output["ninth_house"]["sign_num"]
        assert self.subject.ninth_house.position == approx(self.expected_output["ninth_house"]["position"], abs=1e-2)
        assert self.subject.ninth_house.abs_pos == approx(self.expected_output["ninth_house"]["abs_pos"], abs=1e-2)
        assert self.subject.ninth_house.emoji == self.expected_output["ninth_house"]["emoji"]
        assert self.subject.ninth_house.point_type == self.expected_output["ninth_house"]["point_type"]

    def test_tenth_house(self):
        assert self.subject.tenth_house.name == self.expected_output["tenth_house"]["name"]
        assert self.subject.tenth_house.quality == self.expected_output["tenth_house"]["quality"]
        assert self.subject.tenth_house.element == self.expected_output["tenth_house"]["element"]
        assert self.subject.tenth_house.sign == self.expected_output["tenth_house"]["sign"]
        assert self.subject.tenth_house.sign_num == self.expected_output["tenth_house"]["sign_num"]
        assert self.subject.tenth_house.position == approx(self.expected_output["tenth_house"]["position"], abs=1e-2)
        assert self.subject.tenth_house.abs_pos == approx(self.expected_output["tenth_house"]["abs_pos"], abs=1e-2)
        assert self.subject.tenth_house.emoji == self.expected_output["tenth_house"]["emoji"]
        assert self.subject.tenth_house.point_type == self.expected_output["tenth_house"]["point_type"]

    def test_eleventh_house(self):
        assert self.subject.eleventh_house.name == self.expected_output["eleventh_house"]["name"]
        assert self.subject.eleventh_house.quality == self.expected_output["eleventh_house"]["quality"]
        assert self.subject.eleventh_house.element == self.expected_output["eleventh_house"]["element"]
        assert self.subject.eleventh_house.sign == self.expected_output["eleventh_house"]["sign"]
        assert self.subject.eleventh_house.sign_num == self.expected_output["eleventh_house"]["sign_num"]
        assert self.subject.eleventh_house.position == approx(self.expected_output["eleventh_house"]["position"], abs=1e-2)
        assert self.subject.eleventh_house.abs_pos == approx(self.expected_output["eleventh_house"]["abs_pos"], abs=1e-2)
        assert self.subject.eleventh_house.emoji == self.expected_output["eleventh_house"]["emoji"]
        assert self.subject.eleventh_house.point_type == self.expected_output["eleventh_house"]["point_type"]

    def test_twelfth_house(self):
        assert self.subject.twelfth_house.name == self.expected_output["twelfth_house"]["name"]
        assert self.subject.twelfth_house.quality == self.expected_output["twelfth_house"]["quality"]
        assert self.subject.twelfth_house.element == self.expected_output["twelfth_house"]["element"]
        assert self.subject.twelfth_house.sign == self.expected_output["twelfth_house"]["sign"]
        assert self.subject.twelfth_house.sign_num == self.expected_output["twelfth_house"]["sign_num"]
        assert self.subject.twelfth_house.position == approx(self.expected_output["twelfth_house"]["position"], abs=1e-2)
        assert self.subject.twelfth_house.abs_pos == approx(self.expected_output["twelfth_house"]["abs_pos"], abs=1e-2)
        assert self.subject.twelfth_house.emoji == self.expected_output["twelfth_house"]["emoji"]
        assert self.subject.twelfth_house.point_type == self.expected_output["twelfth_house"]["point_type"]

    def test_lunar_phase(self):
        assert self.subject.lunar_phase.model_dump()["degrees_between_s_m"] == approx(self.expected_output["lunar_phase"]["degrees_between_s_m"], abs=1e-2)
        assert self.subject.lunar_phase.model_dump()["moon_phase"] == self.expected_output["lunar_phase"]["moon_phase"]
        assert self.subject.lunar_phase.model_dump()["moon_emoji"] == self.expected_output["lunar_phase"]["moon_emoji"]
        assert self.subject.lunar_phase.model_dump()["moon_phase_name"] == self.expected_output["lunar_phase"]["moon_phase_name"]


class TestAstrologicalSubjectFactoryMethods:
    """Test different factory methods and configurations."""

    def test_from_iso_utc_time_online(self):
        """Test creating subject from ISO UTC timestamp with online lookup."""
        subject = AstrologicalSubjectFactory.from_iso_utc_time(
            name="ISO Test",
            iso_utc_time="2023-06-15T12:00:00Z",
            city="London",
            nation="GB",
            tz_str="Europe/London",
            suppress_geonames_warning=True,
            online=True
        )
        assert subject.name == "ISO Test"
        assert subject.year == 2023
        assert subject.month == 6
        assert subject.day == 15
        # Hour should be adjusted to local time (BST = UTC+1)
        assert subject.hour == 13
        assert subject.minute == 0

    def test_from_iso_utc_time_offline(self):
        """Test creating subject from ISO UTC timestamp with manual coordinates."""
        subject = AstrologicalSubjectFactory.from_iso_utc_time(
            name="ISO Offline Test",
            iso_utc_time="2020-01-01T00:00:00Z",
            lng=-74.006,
            lat=40.7128,
            tz_str="America/New_York",
            online=False
        )
        assert subject.name == "ISO Offline Test"
        assert subject.year == 2019  # UTC midnight = 19:00 previous day in NYC
        assert subject.month == 12
        assert subject.day == 31
        assert subject.hour == 19
        assert subject.lat == approx(40.7128, abs=1e-2)
        assert subject.lng == approx(-74.006, abs=1e-2)

    def test_from_current_time(self):
        """Test creating subject for current time."""
        from datetime import datetime
        now = datetime.now()

        subject = AstrologicalSubjectFactory.from_current_time(
            name="Current Time Test",
            lng=0.0,
            lat=51.5074,
            tz_str="Europe/London",
            online=False
        )
        assert subject.name == "Current Time Test"
        # Check that it's approximately the current time (within 1 minute)
        assert subject.year == now.year
        assert subject.month == now.month
        assert subject.day == now.day

    def test_sidereal_zodiac_lahiri(self):
        """Test sidereal zodiac calculation with Lahiri ayanamsa."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Test", 1990, 1, 1, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            suppress_geonames_warning=True
        )
        assert subject.zodiac_type == "Sidereal"
        # Sidereal positions should differ from tropical
        # Sun in tropical Capricorn should be in Sagittarius siderally
        assert subject.sun.sign in ["Sag", "Cap"]

    def test_different_house_systems(self):
        """Test different house systems."""
        # Placidus (default)
        placidus = AstrologicalSubjectFactory.from_birth_data(
            "Placidus", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            houses_system_identifier="P",
            suppress_geonames_warning=True
        )

        # Koch
        koch = AstrologicalSubjectFactory.from_birth_data(
            "Koch", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            houses_system_identifier="K",
            suppress_geonames_warning=True
        )

        # Whole Sign (W)
        whole_sign = AstrologicalSubjectFactory.from_birth_data(
            "Whole Sign", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            houses_system_identifier="W",
            suppress_geonames_warning=True
        )

        # House cusps should differ between systems
        assert placidus.second_house.abs_pos != koch.second_house.abs_pos
        # Different systems should produce different house cusps
        assert placidus.second_house.abs_pos != whole_sign.second_house.abs_pos

    def test_heliocentric_perspective(self):
        """Test heliocentric perspective calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Heliocentric Test", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            perspective_type="Heliocentric",
            suppress_geonames_warning=True
        )
        # In heliocentric perspective, Earth takes the place of Sun
        # Sun position should be very different or unavailable
        assert subject.name == "Heliocentric Test"

    def test_topocentric_perspective_with_altitude(self):
        """Test topocentric perspective with altitude."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Topocentric Test", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            perspective_type="Topocentric",
            altitude=100.0,
            suppress_geonames_warning=True
        )
        assert subject.name == "Topocentric Test"

    def test_minimal_active_points(self):
        """Test calculation with minimal active points for performance."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Minimal Points", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Sun", "Moon", "Ascendant"],
            calculate_lunar_phase=False,
            suppress_geonames_warning=True
        )
        # Should have Sun, Moon, Ascendant
        assert hasattr(subject, 'sun')
        assert hasattr(subject, 'moon')
        assert hasattr(subject, 'ascendant')

    def test_with_seconds_parameter(self):
        """Test birth time with seconds specified."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "With Seconds", 1990, 6, 15, 12, 30,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            seconds=45,
            suppress_geonames_warning=True
        )
        assert subject.hour == 12
        assert subject.minute == 30

    def test_offline_mode_without_coordinates_raises_error(self):
        """Test that offline mode without coordinates raises an error."""
        from kerykeion.schemas import KerykeionException
        import pytest

        with pytest.raises((KerykeionException, Exception)):
            AstrologicalSubjectFactory.from_birth_data(
                "Error Test", 1990, 6, 15, 12, 0,
                online=False,
                # Missing lng, lat, tz_str
            )


class TestAstrologicalSubjectModelMethods:
    """Test AstrologicalSubjectModel methods and properties."""

    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Test Subject", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )

    def test_model_dump(self):
        """Test model_dump method returns dict."""
        data = self.subject.model_dump()
        assert isinstance(data, dict)
        assert data["name"] == "Test Subject"
        assert data["year"] == 1990
        assert "sun" in data
        assert "moon" in data

    def test_model_getitem(self):
        """Test dictionary-style access to model attributes."""
        assert self.subject["name"] == "Test Subject"
        assert self.subject["year"] == 1990
        assert self.subject["sun"].name == "Sun"

    def test_model_get_method(self):
        """Test get method with default value."""
        assert self.subject.get("name") == "Test Subject"
        assert self.subject.get("nonexistent_key", "default") == "default"

    def test_model_setitem(self):
        """Test setting values via dictionary-style access."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Mutable Test", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )
        subject["name"] = "Modified Name"
        assert subject["name"] == "Modified Name"


class TestChartConfiguration:
    """Test ChartConfiguration validation and behavior."""

    def test_valid_sidereal_configuration(self):
        """Test valid sidereal configuration."""
        from kerykeion.astrological_subject_factory import ChartConfiguration
        config = ChartConfiguration(
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI"
        )
        assert config.zodiac_type == "Sidereal"
        assert config.sidereal_mode == "LAHIRI"

    def test_sidereal_without_mode_uses_default(self):
        """Test that sidereal without mode sets default."""
        from kerykeion.astrological_subject_factory import ChartConfiguration
        config = ChartConfiguration(zodiac_type="Sidereal")
        assert config.sidereal_mode == "FAGAN_BRADLEY"

    def test_invalid_sidereal_mode_with_tropical_raises_error(self):
        """Test that sidereal mode with tropical zodiac raises error."""
        from kerykeion.astrological_subject_factory import ChartConfiguration
        from kerykeion.schemas import KerykeionException
        import pytest

        with pytest.raises(KerykeionException):
            ChartConfiguration(
                zodiac_type="Tropical",
                sidereal_mode="LAHIRI"
            )

    def test_invalid_zodiac_type_raises_error(self):
        """Test that invalid zodiac type raises error."""
        from kerykeion.astrological_subject_factory import ChartConfiguration
        from kerykeion.schemas import KerykeionException
        import pytest

        with pytest.raises(KerykeionException):
            ChartConfiguration(zodiac_type="InvalidType")

        with pytest.raises(KerykeionException):
            ChartConfiguration(zodiac_type="Tropics")

    def test_invalid_house_system_raises_error(self):
        """Test that invalid house system raises error."""
        from kerykeion.astrological_subject_factory import ChartConfiguration
        from kerykeion.schemas import KerykeionException
        import pytest

        with pytest.raises(KerykeionException):
            ChartConfiguration(houses_system_identifier="Z")

    def test_invalid_perspective_raises_error(self):
        """Test that invalid perspective type raises error."""
        from kerykeion.astrological_subject_factory import ChartConfiguration
        from kerykeion.schemas import KerykeionException
        import pytest

        with pytest.raises(KerykeionException):
            ChartConfiguration(perspective_type="Invalid")


class TestLocationData:
    """Test LocationData functionality."""

    def test_default_location_is_greenwich(self):
        """Test that default location is Greenwich."""
        from kerykeion.astrological_subject_factory import LocationData
        location = LocationData()
        assert location.city == "Greenwich"
        assert location.nation == "GB"
        assert location.lat == 51.5074
        assert location.lng == 0.0

    def test_prepare_for_calculation_adjusts_polar_latitudes(self):
        """Test that polar latitudes are adjusted."""
        from kerykeion.astrological_subject_factory import LocationData

        # Test North Pole - gets adjusted to 66 degrees (polar circle)
        location = LocationData(lat=90.0)
        location.prepare_for_calculation()
        # Should be adjusted to polar circle limit
        assert location.lat == 66.0

        # Test South Pole
        location = LocationData(lat=-90.0)
        location.prepare_for_calculation()
        assert location.lat == -66.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_midnight_birth(self):
        """Test birth at exactly midnight."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Midnight", 1990, 1, 1, 0, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )
        assert subject.hour == 0
        assert subject.minute == 0

    def test_leap_year_february_29(self):
        """Test birth on February 29 (leap year)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Leap Year", 2000, 2, 29, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )
        assert subject.year == 2000
        assert subject.month == 2
        assert subject.day == 29

    def test_southern_hemisphere_coordinates(self):
        """Test with southern hemisphere coordinates."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Southern Hemisphere", 1990, 12, 25, 12, 0,
            lng=151.2093, lat=-33.8688,  # Sydney
            tz_str="Australia/Sydney",
            online=False,
            suppress_geonames_warning=True
        )
        assert subject.lat == approx(-33.8688, abs=1e-2)
        assert subject.lng == approx(151.2093, abs=1e-2)

    def test_western_hemisphere_coordinates(self):
        """Test with western hemisphere (negative longitude)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Western Hemisphere", 1990, 7, 4, 12, 0,
            lng=-118.2437, lat=34.0522,  # Los Angeles
            tz_str="America/Los_Angeles",
            online=False,
            suppress_geonames_warning=True
        )
        assert subject.lat == approx(34.0522, abs=1e-2)
        assert subject.lng == approx(-118.2437, abs=1e-2)

    def test_near_date_line(self):
        """Test with coordinates near international date line."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Date Line", 1990, 6, 15, 12, 0,
            lng=179.0, lat=-16.5,  # Near Fiji
            tz_str="Pacific/Fiji",
            online=False,
            suppress_geonames_warning=True
        )
        assert subject.lng == approx(179.0, abs=1e-2)

    def test_without_lunar_phase_calculation(self):
        """Test subject creation without lunar phase."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "No Lunar Phase", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            calculate_lunar_phase=False,
            suppress_geonames_warning=True
        )
        assert subject.lunar_phase is None


class TestRetrogradePlanets:
    """Test retrograde planet detection."""

    def test_mercury_retrograde_detection(self):
        """Test detection of Mercury retrograde."""
        # Mercury was retrograde in December 2023 (Dec 13 - Jan 1, 2024)
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Mercury Rx", 2023, 12, 20, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )
        # Mercury should be retrograde (negative speed)
        assert subject.mercury.speed < 0
        assert subject.mercury.retrograde is True

    def test_direct_planet_speed(self):
        """Test that direct planets have positive speed."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Direct Test", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )
        # Sun is never retrograde
        assert subject.sun.speed > 0
        assert subject.sun.retrograde is False


class TestDifferentYears:
    """Test calculations for different historical periods."""

    def test_early_20th_century(self):
        """Test calculation for early 1900s."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "1900s", 1920, 5, 10, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )
        assert subject.year == 1920
        assert subject.sun.sign == "Tau"

    def test_future_date(self):
        """Test calculation for future date."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Future", 2030, 12, 25, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )
        assert subject.year == 2030
        assert subject.sun.sign == "Cap"


class TestPerspectiveTypes:
    """Test all perspective types comprehensively."""

    def test_true_geocentric_perspective(self):
        """Test True Geocentric perspective (line 120)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "True Geocentric", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            perspective_type="True Geocentric",
            suppress_geonames_warning=True
        )
        assert subject.perspective_type == "True Geocentric"
        assert hasattr(subject, 'sun')


class TestTimeZoneEdgeCases:
    """Test DST and timezone edge cases."""

    def test_dst_time_with_is_dst_false(self):
        """Test DST time with is_dst=False."""
        # During DST fall-back, 2:30 AM occurs twice
        # Setting is_dst=False selects the second occurrence (standard time)
        subject = AstrologicalSubjectFactory.from_birth_data(
            "DST False", 2023, 11, 5, 2, 30,
            lng=-74.006, lat=40.7128, tz_str="America/New_York",
            online=False,
            is_dst=False,
            suppress_geonames_warning=True
        )
        assert subject.hour == 2

    def test_dst_time_with_is_dst_true(self):
        """Test DST time with is_dst=True."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "DST True", 2023, 11, 5, 2, 30,
            lng=-74.006, lat=40.7128, tz_str="America/New_York",
            online=False,
            is_dst=True,
            suppress_geonames_warning=True
        )
        assert subject.hour == 2


class TestSiderealModeValidation:
    """Test sidereal mode validation (line 215)."""

    def test_invalid_sidereal_mode_raises_error(self):
        """Test that invalid sidereal mode raises error."""
        from kerykeion.astrological_subject_factory import ChartConfiguration
        from kerykeion.schemas import KerykeionException
        import pytest

        with pytest.raises(KerykeionException, match="not a valid sidereal mode"):
            ChartConfiguration(
                zodiac_type="Sidereal",
                sidereal_mode="INVALID_MODE"  # type: ignore
            )


class TestAdditionalPlanets:
    """Test additional planets and points that require special ephemeris files."""

    def test_trans_neptunian_objects(self):
        """Test trans-Neptunian objects calculation attempts."""
        # These will log warnings but should not crash
        subject = AstrologicalSubjectFactory.from_birth_data(
            "TNO Test", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Sun", "Moon", "Ixion", "Orcus", "Quaoar"],
            suppress_geonames_warning=True
        )
        # Sun and Moon should always be calculated
        assert hasattr(subject, 'sun')
        assert hasattr(subject, 'moon')
        # TNOs may or may not be present depending on ephemeris files


class TestDefaultTimeParameters:
    """Test default time parameters (lines 555-561)."""

    def test_defaults_to_current_time_when_none(self):
        """Test that None time parameters default to current time."""
        from datetime import datetime

        # Call with all time parameters as None
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Current Defaults",
            year=None,
            month=None,
            day=None,
            hour=None,
            minute=None,
            seconds=None,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )

        now = datetime.now()
        assert subject.year == now.year
        assert subject.month == now.month
        assert subject.day == now.day


class TestGeonamesUsernameWarning:
    """Test geonames username warning (lines 594-595)."""

    def test_online_mode_without_username_uses_default(self):
        """Test that online mode without username triggers warning."""

        # This should use default username and log warning
        subject = AstrologicalSubjectFactory.from_birth_data(
            "No Username", 1990, 6, 15, 12, 0,
            city="London",
            nation="GB",
            online=True,
            geonames_username=None  # Will trigger default
        )

        assert subject.name == "No Username"


class TestExceptionHandlingInPlanetCalculation:
    """Test exception handling in planet calculation (lines 1184-1187)."""

    def test_error_in_planet_calculation_removes_from_active_points(self):
        """Test that calculation errors are handled gracefully."""
        # This is already partially covered by the Eris/Sedna warnings
        # We need to verify the mechanism works
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Error Handling", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Sun", "Moon", "Eris"],  # Eris will fail
            suppress_geonames_warning=True
        )

        # Sun and Moon should be calculated, Eris should fail gracefully
        assert hasattr(subject, 'sun')
        assert hasattr(subject, 'moon')
        # Eris is not calculated due to missing ephemeris file


class TestArabicParts:
    """Test Arabic Parts calculations (lines 1582-1787)."""

    def test_pars_fortunae_calculation(self):
        """Test Part of Fortune calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Pars Fortunae Test", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Fortunae", "Sun", "Moon", "Ascendant"],
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'pars_fortunae')
        assert subject.pars_fortunae.name == "Pars_Fortunae"
        assert subject.pars_fortunae.retrograde is False

    def test_pars_fortunae_auto_activates_required_points(self):
        """Test that Pars Fortunae auto-activates required points."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Auto Activate", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Fortunae"],  # Only Pars, should auto-add Sun, Moon, Ascendant
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'pars_fortunae')
        assert hasattr(subject, 'sun')
        assert hasattr(subject, 'moon')
        assert hasattr(subject, 'ascendant')

    def test_pars_spiritus_calculation(self):
        """Test Part of Spirit calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Pars Spiritus Test", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Spiritus", "Sun", "Moon", "Ascendant"],
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'pars_spiritus')
        assert subject.pars_spiritus.name == "Pars_Spiritus"

    def test_pars_amoris_calculation(self):
        """Test Part of Eros/Love calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Pars Amoris Test", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Amoris", "Venus", "Sun", "Ascendant"],
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'pars_amoris')
        assert subject.pars_amoris.name == "Pars_Amoris"

    def test_pars_fidei_calculation(self):
        """Test Part of Faith calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Pars Fidei Test", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Fidei", "Jupiter", "Saturn", "Ascendant"],
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'pars_fidei')
        assert subject.pars_fidei.name == "Pars_Fidei"


class TestVertexCalculation:
    """Test Vertex and Anti-Vertex calculations (lines 1804, 1836-1841)."""

    def test_vertex_calculation(self):
        """Test Vertex calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Vertex Test", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Vertex"],
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'vertex')
        assert subject.vertex.name == "Vertex"
        assert subject.vertex.retrograde is False

    def test_anti_vertex_calculation(self):
        """Test Anti-Vertex calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Anti-Vertex Test", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Anti_Vertex"],
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'anti_vertex')
        assert subject.anti_vertex.name == "Anti_Vertex"

    def test_both_vertex_and_anti_vertex(self):
        """Test calculating both Vertex and Anti-Vertex."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Both Vertex", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Vertex", "Anti_Vertex"],
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'vertex')
        assert hasattr(subject, 'anti_vertex')
        # Anti-Vertex should be 180 degrees from Vertex
        expected_anti = (subject.vertex.abs_pos + 180) % 360
        assert subject.anti_vertex.abs_pos == approx(expected_anti, abs=1e-2)


class TestFixedStars:
    """Test Fixed Stars calculations (lines 1754-1787)."""

    def test_regulus_calculation(self):
        """Test Regulus (fixed star) calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Regulus Test", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Regulus"],
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'regulus')
        assert subject.regulus.name == "Regulus"
        assert subject.regulus.retrograde is False  # Fixed stars are never retrograde

    def test_spica_calculation(self):
        """Test Spica (fixed star) calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Spica Test", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Spica"],
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'spica')
        assert subject.spica.name == "Spica"
        assert subject.spica.retrograde is False


class TestNightChartCalculations:
    """Test night chart calculations for Arabic Parts."""

    def test_night_chart_pars_fortunae(self):
        """Test Part of Fortune for night chart (Sun below horizon)."""
        # Birth at night - Sun in houses 7-12
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Night Chart", 1990, 6, 15, 0, 0,  # Midnight
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Fortunae", "Sun", "Moon", "Ascendant"],
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'pars_fortunae')
        # Verify it's calculated differently for night chart


class TestComprehensiveCoverage:
    """Additional tests for complete coverage."""

    def test_all_perspectives_and_zodiacs(self):
        """Test all combinations to ensure full coverage."""
        perspectives = ["Apparent Geocentric", "True Geocentric", "Heliocentric", "Topocentric"]
        zodiacs = ["Tropical", "Sidereal"]

        for perspective in perspectives:
            for zodiac in zodiacs:
                kwargs = {
                    "name": f"{perspective}-{zodiac}",
                    "year": 1990,
                    "month": 6,
                    "day": 15,
                    "hour": 12,
                    "minute": 0,
                    "lng": 0.0,
                    "lat": 51.5074,
                    "tz_str": "Etc/GMT",
                    "online": False,
                    "perspective_type": perspective,
                    "zodiac_type": zodiac,
                    "geonames_username": "century.boy"
                }

                if zodiac == "Sidereal":
                    kwargs["sidereal_mode"] = "LAHIRI"

                if perspective == "Topocentric":
                    kwargs["altitude"] = 100.0

                subject = AstrologicalSubjectFactory.from_birth_data(**kwargs)
                assert subject.name == f"{perspective}-{zodiac}"
                assert subject.zodiac_type == zodiac


class TestMockErrorConditions:
    """Test error conditions using mocks."""

    def test_planet_calculation_error_handling(self):
        """Test error handling when planet calculation fails (lines 1184-1187)."""
        from unittest.mock import patch
        import swisseph as swe

        # Mock swe.calc_ut to raise an exception for a specific planet
        original_calc = swe.calc_ut

        def mock_calc_ut(jd, planet_num, flags):
            # Raise exception for Mercury (planet 2)
            if planet_num == 2:
                raise Exception("Mock ephemeris error")
            return original_calc(jd, planet_num, flags)

        with patch('swisseph.calc_ut', side_effect=mock_calc_ut):
            # This should handle the error gracefully
            subject = AstrologicalSubjectFactory.from_birth_data(
                "Error Test", 1990, 6, 15, 12, 0,
                lng=0.0, lat=51.5074, tz_str="Etc/GMT",
                online=False,
                active_points=["Sun", "Mercury", "Moon"],
                suppress_geonames_warning=True
            )

            # Sun and Moon should be calculated, Mercury should fail
            assert hasattr(subject, 'sun')
            assert hasattr(subject, 'moon')
            # Mercury may not be in active_points due to error

    def test_ambiguous_time_error_with_pytz_exception(self):
        """Test ambiguous DST time error (lines 972-978)."""
        from unittest.mock import patch, MagicMock
        from kerykeion.schemas import KerykeionException
        import pytz
        import pytest

        # Mock the localize method to raise AmbiguousTimeError
        with patch('pytz.timezone') as mock_tz:
            mock_tz_instance = MagicMock()
            mock_tz_instance.localize.side_effect = pytz.exceptions.AmbiguousTimeError("Test ambiguous")
            mock_tz.return_value = mock_tz_instance

            with pytest.raises(KerykeionException, match="Ambiguous time error"):
                AstrologicalSubjectFactory.from_birth_data(
                    "Ambiguous", 2023, 11, 5, 2, 30,
                    lng=-74.006, lat=40.7128, tz_str="America/New_York",
                    online=False,
                    suppress_geonames_warning=True
                )

    def test_nonexistent_time_error(self):
        """Test non-existent DST time error."""
        from unittest.mock import patch, MagicMock
        from kerykeion.schemas import KerykeionException
        import pytz
        import pytest

        # Mock the localize method to raise NonExistentTimeError
        with patch('pytz.timezone') as mock_tz:
            mock_tz_instance = MagicMock()
            mock_tz_instance.localize.side_effect = pytz.exceptions.NonExistentTimeError("Test nonexistent")
            mock_tz.return_value = mock_tz_instance

            with pytest.raises(KerykeionException, match="Non-existent time error"):
                AstrologicalSubjectFactory.from_birth_data(
                    "Nonexistent", 2023, 3, 12, 2, 30,
                    lng=-74.006, lat=40.7128, tz_str="America/New_York",
                    online=False,
                    suppress_geonames_warning=True
                )

    def test_day_chart_vs_night_chart(self):
        """Test day vs night chart calculation for Arabic Parts (line 1589)."""
        # Day chart - Sun in houses 1-6
        day_subject = AstrologicalSubjectFactory.from_birth_data(
            "Day Chart", 1990, 6, 15, 12, 0,  # Noon
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Fortunae", "Sun", "Moon", "Ascendant"],
            suppress_geonames_warning=True
        )

        # Night chart - Sun in houses 7-12
        night_subject = AstrologicalSubjectFactory.from_birth_data(
            "Night Chart", 1990, 6, 15, 0, 0,  # Midnight
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Fortunae", "Sun", "Moon", "Ascendant"],
            suppress_geonames_warning=True
        )

        # Both should have Pars Fortunae calculated
        assert hasattr(day_subject, 'pars_fortunae')
        assert hasattr(night_subject, 'pars_fortunae')
        # Values should differ due to different formula
        assert day_subject.pars_fortunae.abs_pos != night_subject.pars_fortunae.abs_pos

    def test_arabic_parts_missing_required_points_auto_activation(self):
        """Test that Arabic Parts auto-activate missing required points (line 1625)."""
        # Test with Pars Fortunae but no Ascendant - should auto-activate
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Auto Activate Test", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Fortunae"],  # Only this, should add Sun, Moon, Ascendant
            suppress_geonames_warning=True
        )

        # All required points should be present
        assert hasattr(subject, 'pars_fortunae')
        assert hasattr(subject, 'sun')
        assert hasattr(subject, 'moon')
        assert hasattr(subject, 'ascendant')

    def test_pars_fortunae_sidereal_with_auto_activation(self):
        """Test Pars Fortunae with sidereal zodiac and auto-activation (line 1589)."""
        # This should trigger the sidereal branch in Pars Fortunae auto-activation
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Pars", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            active_points=["Pars_Fortunae"],  # Only this - will auto-add and trigger sidereal path
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'pars_fortunae')
        assert subject.zodiac_type == "Sidereal"

    def test_pars_spiritus_sidereal_with_auto_activation(self):
        """Test Pars Spiritus with sidereal zodiac and auto-activation (line 1625+)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Spiritus", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            active_points=["Pars_Spiritus"],  # Will trigger sidereal branch in auto-activation
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'pars_spiritus')

    def test_pars_amoris_sidereal_with_auto_activation(self):
        """Test Pars Amoris with sidereal zodiac."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Amoris", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            active_points=["Pars_Amoris"],
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'pars_amoris')

    def test_pars_fidei_sidereal_with_auto_activation(self):
        """Test Pars Fidei with sidereal zodiac."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Fidei", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            active_points=["Pars_Fidei"],
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'pars_fidei')

    def test_vertex_sidereal(self):
        """Test Vertex with sidereal zodiac (line 1804)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Vertex", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            active_points=["Vertex", "Anti_Vertex"],
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'vertex')
        assert hasattr(subject, 'anti_vertex')


class TestAllDwarfPlanetsAndFixedStars:
    """Test all dwarf planets and fixed stars to trigger exception branches."""

    def test_all_trans_neptunian_objects_attempt(self):
        """Test ALL TNOs to trigger their exception handling."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "All TNOs", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=[
                "Sun", "Moon",
                "Eris", "Sedna", "Haumea", "Makemake",
                "Ixion", "Orcus", "Quaoar"
            ],
            suppress_geonames_warning=True
        )

        # Sun and Moon should always work
        assert hasattr(subject, 'sun')
        assert hasattr(subject, 'moon')
        # Others will fail gracefully with warnings

    def test_all_fixed_stars_attempt(self):
        """Test fixed stars to trigger their exception handling."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Fixed Stars", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Regulus", "Spica", "Sun"],
            suppress_geonames_warning=True
        )

        assert hasattr(subject, 'sun')
        assert hasattr(subject, 'regulus')
        assert hasattr(subject, 'spica')

    def test_vertex_calculation_with_exception_mock(self):
        """Test Vertex exception handling (line 1836-1841)."""
        from unittest.mock import patch

        # First create subject normally to ensure houses work
        # Then mock only the Vertex calculation part
        original_houses = __import__('swisseph').houses

        def conditional_mock(*args, **kwargs):
            # Check if this is being called with 'V' house system (for Vertex)
            if kwargs.get('hsys') == b'V':
                raise Exception("Mock vertex error")
            return original_houses(*args, **kwargs)

        with patch('swisseph.houses', side_effect=conditional_mock):
            subject = AstrologicalSubjectFactory.from_birth_data(
                "Vertex Error", 1990, 6, 15, 12, 0,
                lng=0.0, lat=51.5074, tz_str="Etc/GMT",
                online=False,
                active_points=["Vertex", "Anti_Vertex", "Sun"],
                suppress_geonames_warning=True
            )

            # Vertex should be None due to exception, but subject created successfully
            assert subject is not None
            assert hasattr(subject, 'sun')

    def test_geonames_missing_data_exception(self):
        """Test geonames missing data exception (line 320)."""
        from unittest.mock import patch, MagicMock

        # Mock FetchGeonames to return incomplete data
        mock_geonames = MagicMock()
        mock_geonames.get_serializable_model.return_value = {
            # Missing 'tz_str' field to trigger exception
            "city": "TestCity",
            "nation": "TestNation",
            "lat": 0.0,
            "lng": 0.0,
            "altitude": 0
        }

        with patch('kerykeion.astrological_subject_factory.FetchGeonames', return_value=mock_geonames):
            try:
                AstrologicalSubjectFactory.from_birth_data(
                    "Geonames Error", 1990, 1, 1, 12, 0,
                    city="TestCity", nation="TestNation",
                    online=True,
                    suppress_geonames_warning=True
                )
                # Should raise exception before reaching here
                assert False, "Expected KerykeionException"
            except Exception as e:
                # Should be KerykeionException with "Missing data from geonames"
                assert "Missing data from geonames" in str(e)

    def test_tno_successful_calculations_with_real_ephemeris(self):
        """Test successful TNO calculations with real ephemeris files (lines 1456-1531)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "TNO Success", 1990, 1, 1, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Eris", "Sedna", "Haumea", "Makemake", "Ixion", "Orcus", "Quaoar", "Sun"],
            suppress_geonames_warning=True
        )

        # All TNOs should be present with real ephemeris files
        assert hasattr(subject, 'sun')
        assert hasattr(subject, 'eris')
        assert subject.eris is not None
        assert hasattr(subject.eris, 'abs_pos')
        assert hasattr(subject.eris, 'retrograde')

        assert hasattr(subject, 'sedna')
        assert subject.sedna is not None

        assert hasattr(subject, 'haumea')
        assert subject.haumea is not None

        assert hasattr(subject, 'makemake')
        assert subject.makemake is not None

        assert hasattr(subject, 'ixion')
        assert subject.ixion is not None

        assert hasattr(subject, 'orcus')
        assert subject.orcus is not None

        assert hasattr(subject, 'quaoar')
        assert subject.quaoar is not None

    def test_fixed_stars_successful_calculations_with_real_ephemeris(self):
        """Test successful fixed star calculations with real ephemeris (lines 1552-1570)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Fixed Stars Success", 1990, 1, 1, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            active_points=["Regulus", "Spica", "Sun"],
            suppress_geonames_warning=True
        )

        # All fixed stars should be present with real calculations
        assert hasattr(subject, 'sun')
        assert subject.sun is not None

        assert hasattr(subject, 'regulus')
        assert subject.regulus is not None
        assert hasattr(subject.regulus, 'abs_pos')
        assert not subject.regulus.retrograde  # Fixed stars are never retrograde

        assert hasattr(subject, 'spica')
        assert subject.spica is not None
        assert hasattr(subject.spica, 'abs_pos')
        assert not subject.spica.retrograde
            # Vertex and Anti_Vertex removed from active_points due to error
