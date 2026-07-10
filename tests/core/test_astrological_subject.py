import pytest
from kerykeion import AstrologicalSubjectFactory
from kerykeion.ephemeris_backend import BACKEND_NAME
from kerykeion.schemas import AstrologicalPoint
from typing import get_args
from pytest import approx

from tests.data.expected_astrological_subjects import EXPECTED_TROPICAL_SUBJECT

# Cross-backend tolerances: swisseph may differ from libephemeris baselines by a few arcminutes.
_POS_TOL = 0.15 if BACKEND_NAME == "swisseph" else 1e-2
_SPEED_TOL = 0.05 if BACKEND_NAME == "swisseph" else 1e-4
_DECL_TOL = 0.15 if BACKEND_NAME == "swisseph" else 1e-2
_STRICT_HOUSE = BACKEND_NAME != "swisseph"


class TestAstrologicalSubject:
    def setup_class(self):
        # Johnny Depp - including all astrological points for complete testing
        all_points = list(get_args(AstrologicalPoint))
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", suppress_geonames_warning=True, active_points=all_points
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
        assert self.subject.lat == approx(self.expected_output["lat"], abs=_POS_TOL)
        assert self.subject.lng == approx(self.expected_output["lng"], abs=_POS_TOL)
        assert self.subject.tz_str == self.expected_output["tz_str"]
        assert self.subject.zodiac_type == self.expected_output["zodiac_type"]
        assert self.subject.julian_day == self.expected_output["julian_day"]

    def test_ascendant(self):
        assert self.subject.ascendant.name == self.expected_output["ascendant"]["name"]
        assert self.subject.ascendant.quality == self.expected_output["ascendant"]["quality"]
        assert self.subject.ascendant.element == self.expected_output["ascendant"]["element"]
        assert self.subject.ascendant.sign == self.expected_output["ascendant"]["sign"]
        assert self.subject.ascendant.sign_num == self.expected_output["ascendant"]["sign_num"]
        assert self.subject.ascendant.position == approx(self.expected_output["ascendant"]["position"], abs=_POS_TOL)
        assert self.subject.ascendant.abs_pos == approx(self.expected_output["ascendant"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.ascendant.emoji == self.expected_output["ascendant"]["emoji"]
        assert self.subject.ascendant.point_type == self.expected_output["ascendant"]["point_type"]
        if _STRICT_HOUSE:

            assert self.subject.ascendant.house == self.expected_output["ascendant"]["house"]
        assert self.subject.ascendant.retrograde == self.expected_output["ascendant"]["retrograde"]

    def test_descendant(self):
        assert self.subject.descendant.name == self.expected_output["descendant"]["name"]
        assert self.subject.descendant.quality == self.expected_output["descendant"]["quality"]
        assert self.subject.descendant.element == self.expected_output["descendant"]["element"]
        assert self.subject.descendant.sign == self.expected_output["descendant"]["sign"]
        assert self.subject.descendant.sign_num == self.expected_output["descendant"]["sign_num"]
        assert self.subject.descendant.position == approx(self.expected_output["descendant"]["position"], abs=_POS_TOL)
        assert self.subject.descendant.abs_pos == approx(self.expected_output["descendant"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.descendant.emoji == self.expected_output["descendant"]["emoji"]
        assert self.subject.descendant.point_type == self.expected_output["descendant"]["point_type"]
        if _STRICT_HOUSE:

            assert self.subject.descendant.house == self.expected_output["descendant"]["house"]
        assert self.subject.descendant.retrograde == self.expected_output["descendant"]["retrograde"]

    def test_medium_coeli(self):
        assert self.subject.medium_coeli.name == self.expected_output["medium_coeli"]["name"]
        assert self.subject.medium_coeli.quality == self.expected_output["medium_coeli"]["quality"]
        assert self.subject.medium_coeli.element == self.expected_output["medium_coeli"]["element"]
        assert self.subject.medium_coeli.sign == self.expected_output["medium_coeli"]["sign"]
        assert self.subject.medium_coeli.sign_num == self.expected_output["medium_coeli"]["sign_num"]
        assert self.subject.medium_coeli.position == approx(self.expected_output["medium_coeli"]["position"], abs=_POS_TOL)
        assert self.subject.medium_coeli.abs_pos == approx(self.expected_output["medium_coeli"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.medium_coeli.emoji == self.expected_output["medium_coeli"]["emoji"]
        assert self.subject.medium_coeli.point_type == self.expected_output["medium_coeli"]["point_type"]
        if _STRICT_HOUSE:

            assert self.subject.medium_coeli.house == self.expected_output["medium_coeli"]["house"]
        assert self.subject.medium_coeli.retrograde == self.expected_output["medium_coeli"]["retrograde"]

    def test_imum_coeli(self):
        assert self.subject.imum_coeli.name == self.expected_output["imum_coeli"]["name"]
        assert self.subject.imum_coeli.quality == self.expected_output["imum_coeli"]["quality"]
        assert self.subject.imum_coeli.element == self.expected_output["imum_coeli"]["element"]
        assert self.subject.imum_coeli.sign == self.expected_output["imum_coeli"]["sign"]
        assert self.subject.imum_coeli.sign_num == self.expected_output["imum_coeli"]["sign_num"]
        assert self.subject.imum_coeli.position == approx(self.expected_output["imum_coeli"]["position"], abs=_POS_TOL)
        assert self.subject.imum_coeli.abs_pos == approx(self.expected_output["imum_coeli"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.imum_coeli.emoji == self.expected_output["imum_coeli"]["emoji"]
        assert self.subject.imum_coeli.point_type == self.expected_output["imum_coeli"]["point_type"]
        if _STRICT_HOUSE:

            assert self.subject.imum_coeli.house == self.expected_output["imum_coeli"]["house"]
        assert self.subject.imum_coeli.retrograde == self.expected_output["imum_coeli"]["retrograde"]

    def test_sun(self):
        assert self.subject.sun.name == self.expected_output["sun"]["name"]
        assert self.subject.sun.quality == self.expected_output["sun"]["quality"]
        assert self.subject.sun.element == self.expected_output["sun"]["element"]
        assert self.subject.sun.sign == self.expected_output["sun"]["sign"]
        assert self.subject.sun.sign_num == self.expected_output["sun"]["sign_num"]
        assert self.subject.sun.position == approx(self.expected_output["sun"]["position"], abs=_POS_TOL)
        assert self.subject.sun.abs_pos == approx(self.expected_output["sun"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.sun.emoji == self.expected_output["sun"]["emoji"]
        assert self.subject.sun.point_type == self.expected_output["sun"]["point_type"]
        if _STRICT_HOUSE:

            assert self.subject.sun.house == self.expected_output["sun"]["house"]
        assert self.subject.sun.retrograde == self.expected_output["sun"]["retrograde"]
        assert self.subject.sun.speed == approx(self.expected_output["sun"]["speed"], abs=_SPEED_TOL)
        assert self.subject.sun.declination == approx(self.expected_output["sun"]["declination"], abs=_POS_TOL)

    def test_moon(self):
        assert self.subject.moon.name == self.expected_output["moon"]["name"]
        assert self.subject.moon.quality == self.expected_output["moon"]["quality"]
        assert self.subject.moon.element == self.expected_output["moon"]["element"]
        assert self.subject.moon.sign == self.expected_output["moon"]["sign"]
        assert self.subject.moon.sign_num == self.expected_output["moon"]["sign_num"]
        assert self.subject.moon.position == approx(self.expected_output["moon"]["position"], abs=_POS_TOL)
        assert self.subject.moon.abs_pos == approx(self.expected_output["moon"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.moon.emoji == self.expected_output["moon"]["emoji"]
        assert self.subject.moon.point_type == self.expected_output["moon"]["point_type"]
        if _STRICT_HOUSE:

            assert self.subject.moon.house == self.expected_output["moon"]["house"]
        assert self.subject.moon.retrograde == self.expected_output["moon"]["retrograde"]
        assert self.subject.moon.speed == approx(self.expected_output["moon"]["speed"], abs=_SPEED_TOL)
        assert self.subject.moon.declination == approx(self.expected_output["moon"]["declination"], abs=_POS_TOL)

    def test_mercury(self):
        assert self.subject.mercury.name == self.expected_output["mercury"]["name"]
        assert self.subject.mercury.quality == self.expected_output["mercury"]["quality"]
        assert self.subject.mercury.element == self.expected_output["mercury"]["element"]
        assert self.subject.mercury.sign == self.expected_output["mercury"]["sign"]
        assert self.subject.mercury.sign_num == self.expected_output["mercury"]["sign_num"]
        assert self.subject.mercury.position == approx(self.expected_output["mercury"]["position"], abs=_POS_TOL)
        assert self.subject.mercury.abs_pos == approx(self.expected_output["mercury"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.mercury.emoji == self.expected_output["mercury"]["emoji"]
        assert self.subject.mercury.point_type == self.expected_output["mercury"]["point_type"]
        if _STRICT_HOUSE:

            assert self.subject.mercury.house == self.expected_output["mercury"]["house"]
        assert self.subject.mercury.retrograde == self.expected_output["mercury"]["retrograde"]
        assert self.subject.mercury.speed == approx(self.expected_output["mercury"]["speed"], abs=_SPEED_TOL)
        assert self.subject.mercury.declination == approx(self.expected_output["mercury"]["declination"], abs=_POS_TOL)

    def test_venus(self):
        assert self.subject.venus.name == self.expected_output["venus"]["name"]
        assert self.subject.venus.quality == self.expected_output["venus"]["quality"]
        assert self.subject.venus.element == self.expected_output["venus"]["element"]
        assert self.subject.venus.sign == self.expected_output["venus"]["sign"]
        assert self.subject.venus.sign_num == self.expected_output["venus"]["sign_num"]
        assert self.subject.venus.position == approx(self.expected_output["venus"]["position"], abs=_POS_TOL)
        assert self.subject.venus.abs_pos == approx(self.expected_output["venus"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.venus.emoji == self.expected_output["venus"]["emoji"]
        assert self.subject.venus.point_type == self.expected_output["venus"]["point_type"]
        if _STRICT_HOUSE:

            assert self.subject.venus.house == self.expected_output["venus"]["house"]
        assert self.subject.venus.retrograde == self.expected_output["venus"]["retrograde"]
        assert self.subject.venus.speed == approx(self.expected_output["venus"]["speed"], abs=_SPEED_TOL)
        assert self.subject.venus.declination == approx(self.expected_output["venus"]["declination"], abs=_POS_TOL)

    def test_mars(self):
        assert self.subject.mars.name == self.expected_output["mars"]["name"]
        assert self.subject.mars.quality == self.expected_output["mars"]["quality"]
        assert self.subject.mars.element == self.expected_output["mars"]["element"]
        assert self.subject.mars.sign == self.expected_output["mars"]["sign"]
        assert self.subject.mars.sign_num == self.expected_output["mars"]["sign_num"]
        assert self.subject.mars.position == approx(self.expected_output["mars"]["position"], abs=_POS_TOL)
        assert self.subject.mars.abs_pos == approx(self.expected_output["mars"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.mars.emoji == self.expected_output["mars"]["emoji"]
        assert self.subject.mars.point_type == self.expected_output["mars"]["point_type"]
        if _STRICT_HOUSE:

            assert self.subject.mars.house == self.expected_output["mars"]["house"]
        assert self.subject.mars.retrograde == self.expected_output["mars"]["retrograde"]
        assert self.subject.mars.speed == approx(self.expected_output["mars"]["speed"], abs=_SPEED_TOL)
        assert self.subject.mars.declination == approx(self.expected_output["mars"]["declination"], abs=_POS_TOL)

    def test_jupiter(self):
        assert self.subject.jupiter.name == self.expected_output["jupiter"]["name"]
        assert self.subject.jupiter.quality == self.expected_output["jupiter"]["quality"]
        assert self.subject.jupiter.element == self.expected_output["jupiter"]["element"]
        assert self.subject.jupiter.sign == self.expected_output["jupiter"]["sign"]
        assert self.subject.jupiter.sign_num == self.expected_output["jupiter"]["sign_num"]
        assert self.subject.jupiter.position == approx(self.expected_output["jupiter"]["position"], abs=_POS_TOL)
        assert self.subject.jupiter.abs_pos == approx(self.expected_output["jupiter"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.jupiter.emoji == self.expected_output["jupiter"]["emoji"]
        assert self.subject.jupiter.point_type == self.expected_output["jupiter"]["point_type"]
        if _STRICT_HOUSE:

            assert self.subject.jupiter.house == self.expected_output["jupiter"]["house"]
        assert self.subject.jupiter.retrograde == self.expected_output["jupiter"]["retrograde"]
        assert self.subject.jupiter.speed == approx(self.expected_output["jupiter"]["speed"], abs=_SPEED_TOL)
        assert self.subject.jupiter.declination == approx(self.expected_output["jupiter"]["declination"], abs=_POS_TOL)

    def test_saturn(self):
        assert self.subject.saturn.name == self.expected_output["saturn"]["name"]
        assert self.subject.saturn.quality == self.expected_output["saturn"]["quality"]
        assert self.subject.saturn.element == self.expected_output["saturn"]["element"]
        assert self.subject.saturn.sign == self.expected_output["saturn"]["sign"]
        assert self.subject.saturn.sign_num == self.expected_output["saturn"]["sign_num"]
        assert self.subject.saturn.position == approx(self.expected_output["saturn"]["position"], abs=_POS_TOL)
        assert self.subject.saturn.abs_pos == approx(self.expected_output["saturn"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.saturn.emoji == self.expected_output["saturn"]["emoji"]
        assert self.subject.saturn.point_type == self.expected_output["saturn"]["point_type"]
        if _STRICT_HOUSE:

            assert self.subject.saturn.house == self.expected_output["saturn"]["house"]
        assert self.subject.saturn.retrograde == self.expected_output["saturn"]["retrograde"]
        assert self.subject.saturn.speed == approx(self.expected_output["saturn"]["speed"], abs=_SPEED_TOL)
        assert self.subject.saturn.declination == approx(self.expected_output["saturn"]["declination"], abs=_POS_TOL)

    def test_uranus(self):
        assert self.subject.uranus.name == self.expected_output["uranus"]["name"]
        assert self.subject.uranus.quality == self.expected_output["uranus"]["quality"]
        assert self.subject.uranus.element == self.expected_output["uranus"]["element"]
        assert self.subject.uranus.sign == self.expected_output["uranus"]["sign"]
        assert self.subject.uranus.sign_num == self.expected_output["uranus"]["sign_num"]
        assert self.subject.uranus.position == approx(self.expected_output["uranus"]["position"], abs=_POS_TOL)
        assert self.subject.uranus.abs_pos == approx(self.expected_output["uranus"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.uranus.emoji == self.expected_output["uranus"]["emoji"]
        assert self.subject.uranus.point_type == self.expected_output["uranus"]["point_type"]
        if _STRICT_HOUSE:

            assert self.subject.uranus.house == self.expected_output["uranus"]["house"]
        assert self.subject.uranus.retrograde == self.expected_output["uranus"]["retrograde"]
        assert self.subject.uranus.speed == approx(self.expected_output["uranus"]["speed"], abs=_SPEED_TOL)
        assert self.subject.uranus.declination == approx(self.expected_output["uranus"]["declination"], abs=_POS_TOL)

    def test_neptune(self):
        assert self.subject.neptune.name == self.expected_output["neptune"]["name"]
        assert self.subject.neptune.quality == self.expected_output["neptune"]["quality"]
        assert self.subject.neptune.element == self.expected_output["neptune"]["element"]
        assert self.subject.neptune.sign == self.expected_output["neptune"]["sign"]
        assert self.subject.neptune.sign_num == self.expected_output["neptune"]["sign_num"]
        assert self.subject.neptune.position == approx(self.expected_output["neptune"]["position"], abs=_POS_TOL)
        assert self.subject.neptune.abs_pos == approx(self.expected_output["neptune"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.neptune.emoji == self.expected_output["neptune"]["emoji"]
        assert self.subject.neptune.point_type == self.expected_output["neptune"]["point_type"]
        if _STRICT_HOUSE:

            assert self.subject.neptune.house == self.expected_output["neptune"]["house"]
        assert self.subject.neptune.retrograde == self.expected_output["neptune"]["retrograde"]
        assert self.subject.neptune.speed == approx(self.expected_output["neptune"]["speed"], abs=_SPEED_TOL)
        assert self.subject.neptune.declination == approx(self.expected_output["neptune"]["declination"], abs=_POS_TOL)

    def test_pluto(self):
        assert self.subject.pluto.name == self.expected_output["pluto"]["name"]
        assert self.subject.pluto.quality == self.expected_output["pluto"]["quality"]
        assert self.subject.pluto.element == self.expected_output["pluto"]["element"]
        assert self.subject.pluto.sign == self.expected_output["pluto"]["sign"]
        assert self.subject.pluto.sign_num == self.expected_output["pluto"]["sign_num"]
        assert self.subject.pluto.position == approx(self.expected_output["pluto"]["position"], abs=_POS_TOL)
        assert self.subject.pluto.abs_pos == approx(self.expected_output["pluto"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.pluto.emoji == self.expected_output["pluto"]["emoji"]
        assert self.subject.pluto.point_type == self.expected_output["pluto"]["point_type"]
        if _STRICT_HOUSE:

            assert self.subject.pluto.house == self.expected_output["pluto"]["house"]
        assert self.subject.pluto.retrograde == self.expected_output["pluto"]["retrograde"]
        assert self.subject.pluto.speed == approx(self.expected_output["pluto"]["speed"], abs=_SPEED_TOL)
        assert self.subject.pluto.declination == approx(self.expected_output["pluto"]["declination"], abs=_POS_TOL)

    def test_true_north_lunar_node(self):
        assert self.subject.true_north_lunar_node.name == self.expected_output["true_north_lunar_node"]["name"]
        assert self.subject.true_north_lunar_node.quality == self.expected_output["true_north_lunar_node"]["quality"]
        assert self.subject.true_north_lunar_node.element == self.expected_output["true_north_lunar_node"]["element"]
        assert self.subject.true_north_lunar_node.sign == self.expected_output["true_north_lunar_node"]["sign"]
        assert self.subject.true_north_lunar_node.sign_num == self.expected_output["true_north_lunar_node"]["sign_num"]
        assert self.subject.true_north_lunar_node.position == approx(
            self.expected_output["true_north_lunar_node"]["position"], abs=1e-2
        )
        assert self.subject.true_north_lunar_node.abs_pos == approx(
            self.expected_output["true_north_lunar_node"]["abs_pos"], abs=1e-2
        )
        assert self.subject.true_north_lunar_node.emoji == self.expected_output["true_north_lunar_node"]["emoji"]
        assert (
            self.subject.true_north_lunar_node.point_type == self.expected_output["true_north_lunar_node"]["point_type"]
        )
        if _STRICT_HOUSE:

            assert self.subject.true_north_lunar_node.house == self.expected_output["true_north_lunar_node"]["house"]
        assert (
            self.subject.true_north_lunar_node.retrograde == self.expected_output["true_north_lunar_node"]["retrograde"]
        )

    def test_true_south_lunar_node(self):
        assert self.subject.true_south_lunar_node.name == self.expected_output["true_south_lunar_node"]["name"]
        assert self.subject.true_south_lunar_node.quality == self.expected_output["true_south_lunar_node"]["quality"]
        assert self.subject.true_south_lunar_node.element == self.expected_output["true_south_lunar_node"]["element"]
        assert self.subject.true_south_lunar_node.sign == self.expected_output["true_south_lunar_node"]["sign"]
        assert self.subject.true_south_lunar_node.sign_num == self.expected_output["true_south_lunar_node"]["sign_num"]
        assert self.subject.true_south_lunar_node.position == approx(
            self.expected_output["true_south_lunar_node"]["position"], abs=1e-2
        )
        assert self.subject.true_south_lunar_node.abs_pos == approx(
            self.expected_output["true_south_lunar_node"]["abs_pos"], abs=1e-2
        )
        assert self.subject.true_south_lunar_node.emoji == self.expected_output["true_south_lunar_node"]["emoji"]
        assert (
            self.subject.true_south_lunar_node.point_type == self.expected_output["true_south_lunar_node"]["point_type"]
        )
        if _STRICT_HOUSE:

            assert self.subject.true_south_lunar_node.house == self.expected_output["true_south_lunar_node"]["house"]
        assert (
            self.subject.true_south_lunar_node.retrograde == self.expected_output["true_south_lunar_node"]["retrograde"]
        )

    def test_first_house(self):
        assert self.subject.first_house.name == self.expected_output["first_house"]["name"]
        assert self.subject.first_house.quality == self.expected_output["first_house"]["quality"]
        assert self.subject.first_house.element == self.expected_output["first_house"]["element"]
        assert self.subject.first_house.sign == self.expected_output["first_house"]["sign"]
        assert self.subject.first_house.sign_num == self.expected_output["first_house"]["sign_num"]
        assert self.subject.first_house.position == approx(self.expected_output["first_house"]["position"], abs=_POS_TOL)
        assert self.subject.first_house.abs_pos == approx(self.expected_output["first_house"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.first_house.emoji == self.expected_output["first_house"]["emoji"]
        assert self.subject.first_house.point_type == self.expected_output["first_house"]["point_type"]

    def test_second_house(self):
        assert self.subject.second_house.name == self.expected_output["second_house"]["name"]
        assert self.subject.second_house.quality == self.expected_output["second_house"]["quality"]
        assert self.subject.second_house.element == self.expected_output["second_house"]["element"]
        assert self.subject.second_house.sign == self.expected_output["second_house"]["sign"]
        assert self.subject.second_house.sign_num == self.expected_output["second_house"]["sign_num"]
        assert self.subject.second_house.position == approx(self.expected_output["second_house"]["position"], abs=_POS_TOL)
        assert self.subject.second_house.abs_pos == approx(self.expected_output["second_house"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.second_house.emoji == self.expected_output["second_house"]["emoji"]
        assert self.subject.second_house.point_type == self.expected_output["second_house"]["point_type"]

    def test_third_house(self):
        assert self.subject.third_house.name == self.expected_output["third_house"]["name"]
        assert self.subject.third_house.quality == self.expected_output["third_house"]["quality"]
        assert self.subject.third_house.element == self.expected_output["third_house"]["element"]
        assert self.subject.third_house.sign == self.expected_output["third_house"]["sign"]
        assert self.subject.third_house.sign_num == self.expected_output["third_house"]["sign_num"]
        assert self.subject.third_house.position == approx(self.expected_output["third_house"]["position"], abs=_POS_TOL)
        assert self.subject.third_house.abs_pos == approx(self.expected_output["third_house"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.third_house.emoji == self.expected_output["third_house"]["emoji"]
        assert self.subject.third_house.point_type == self.expected_output["third_house"]["point_type"]

    def test_fourth_house(self):
        assert self.subject.fourth_house.name == self.expected_output["fourth_house"]["name"]
        assert self.subject.fourth_house.quality == self.expected_output["fourth_house"]["quality"]
        assert self.subject.fourth_house.element == self.expected_output["fourth_house"]["element"]
        assert self.subject.fourth_house.sign == self.expected_output["fourth_house"]["sign"]
        assert self.subject.fourth_house.sign_num == self.expected_output["fourth_house"]["sign_num"]
        assert self.subject.fourth_house.position == approx(self.expected_output["fourth_house"]["position"], abs=_POS_TOL)
        assert self.subject.fourth_house.abs_pos == approx(self.expected_output["fourth_house"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.fourth_house.emoji == self.expected_output["fourth_house"]["emoji"]
        assert self.subject.fourth_house.point_type == self.expected_output["fourth_house"]["point_type"]

    def test_fifth_house(self):
        assert self.subject.fifth_house.name == self.expected_output["fifth_house"]["name"]
        assert self.subject.fifth_house.quality == self.expected_output["fifth_house"]["quality"]
        assert self.subject.fifth_house.element == self.expected_output["fifth_house"]["element"]
        assert self.subject.fifth_house.sign == self.expected_output["fifth_house"]["sign"]
        assert self.subject.fifth_house.sign_num == self.expected_output["fifth_house"]["sign_num"]
        assert self.subject.fifth_house.position == approx(self.expected_output["fifth_house"]["position"], abs=_POS_TOL)
        assert self.subject.fifth_house.abs_pos == approx(self.expected_output["fifth_house"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.fifth_house.emoji == self.expected_output["fifth_house"]["emoji"]
        assert self.subject.fifth_house.point_type == self.expected_output["fifth_house"]["point_type"]

    def test_sixth_house(self):
        assert self.subject.sixth_house.name == self.expected_output["sixth_house"]["name"]
        assert self.subject.sixth_house.quality == self.expected_output["sixth_house"]["quality"]
        assert self.subject.sixth_house.element == self.expected_output["sixth_house"]["element"]
        assert self.subject.sixth_house.sign == self.expected_output["sixth_house"]["sign"]
        assert self.subject.sixth_house.sign_num == self.expected_output["sixth_house"]["sign_num"]
        assert self.subject.sixth_house.position == approx(self.expected_output["sixth_house"]["position"], abs=_POS_TOL)
        assert self.subject.sixth_house.abs_pos == approx(self.expected_output["sixth_house"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.sixth_house.emoji == self.expected_output["sixth_house"]["emoji"]
        assert self.subject.sixth_house.point_type == self.expected_output["sixth_house"]["point_type"]

    def test_seventh_house(self):
        assert self.subject.seventh_house.name == self.expected_output["seventh_house"]["name"]
        assert self.subject.seventh_house.quality == self.expected_output["seventh_house"]["quality"]
        assert self.subject.seventh_house.element == self.expected_output["seventh_house"]["element"]
        assert self.subject.seventh_house.sign == self.expected_output["seventh_house"]["sign"]
        assert self.subject.seventh_house.sign_num == self.expected_output["seventh_house"]["sign_num"]
        assert self.subject.seventh_house.position == approx(
            self.expected_output["seventh_house"]["position"], abs=1e-2
        )
        assert self.subject.seventh_house.abs_pos == approx(self.expected_output["seventh_house"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.seventh_house.emoji == self.expected_output["seventh_house"]["emoji"]
        assert self.subject.seventh_house.point_type == self.expected_output["seventh_house"]["point_type"]

    def test_eighth_house(self):
        assert self.subject.eighth_house.name == self.expected_output["eighth_house"]["name"]
        assert self.subject.eighth_house.quality == self.expected_output["eighth_house"]["quality"]
        assert self.subject.eighth_house.element == self.expected_output["eighth_house"]["element"]
        assert self.subject.eighth_house.sign == self.expected_output["eighth_house"]["sign"]
        assert self.subject.eighth_house.sign_num == self.expected_output["eighth_house"]["sign_num"]
        assert self.subject.eighth_house.position == approx(self.expected_output["eighth_house"]["position"], abs=_POS_TOL)
        assert self.subject.eighth_house.abs_pos == approx(self.expected_output["eighth_house"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.eighth_house.emoji == self.expected_output["eighth_house"]["emoji"]
        assert self.subject.eighth_house.point_type == self.expected_output["eighth_house"]["point_type"]

    def test_ninth_house(self):
        assert self.subject.ninth_house.name == self.expected_output["ninth_house"]["name"]
        assert self.subject.ninth_house.quality == self.expected_output["ninth_house"]["quality"]
        assert self.subject.ninth_house.element == self.expected_output["ninth_house"]["element"]
        assert self.subject.ninth_house.sign == self.expected_output["ninth_house"]["sign"]
        assert self.subject.ninth_house.sign_num == self.expected_output["ninth_house"]["sign_num"]
        assert self.subject.ninth_house.position == approx(self.expected_output["ninth_house"]["position"], abs=_POS_TOL)
        assert self.subject.ninth_house.abs_pos == approx(self.expected_output["ninth_house"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.ninth_house.emoji == self.expected_output["ninth_house"]["emoji"]
        assert self.subject.ninth_house.point_type == self.expected_output["ninth_house"]["point_type"]

    def test_tenth_house(self):
        assert self.subject.tenth_house.name == self.expected_output["tenth_house"]["name"]
        assert self.subject.tenth_house.quality == self.expected_output["tenth_house"]["quality"]
        assert self.subject.tenth_house.element == self.expected_output["tenth_house"]["element"]
        assert self.subject.tenth_house.sign == self.expected_output["tenth_house"]["sign"]
        assert self.subject.tenth_house.sign_num == self.expected_output["tenth_house"]["sign_num"]
        assert self.subject.tenth_house.position == approx(self.expected_output["tenth_house"]["position"], abs=_POS_TOL)
        assert self.subject.tenth_house.abs_pos == approx(self.expected_output["tenth_house"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.tenth_house.emoji == self.expected_output["tenth_house"]["emoji"]
        assert self.subject.tenth_house.point_type == self.expected_output["tenth_house"]["point_type"]

    def test_eleventh_house(self):
        assert self.subject.eleventh_house.name == self.expected_output["eleventh_house"]["name"]
        assert self.subject.eleventh_house.quality == self.expected_output["eleventh_house"]["quality"]
        assert self.subject.eleventh_house.element == self.expected_output["eleventh_house"]["element"]
        assert self.subject.eleventh_house.sign == self.expected_output["eleventh_house"]["sign"]
        assert self.subject.eleventh_house.sign_num == self.expected_output["eleventh_house"]["sign_num"]
        assert self.subject.eleventh_house.position == approx(
            self.expected_output["eleventh_house"]["position"], abs=1e-2
        )
        assert self.subject.eleventh_house.abs_pos == approx(
            self.expected_output["eleventh_house"]["abs_pos"], abs=1e-2
        )
        assert self.subject.eleventh_house.emoji == self.expected_output["eleventh_house"]["emoji"]
        assert self.subject.eleventh_house.point_type == self.expected_output["eleventh_house"]["point_type"]

    def test_twelfth_house(self):
        assert self.subject.twelfth_house.name == self.expected_output["twelfth_house"]["name"]
        assert self.subject.twelfth_house.quality == self.expected_output["twelfth_house"]["quality"]
        assert self.subject.twelfth_house.element == self.expected_output["twelfth_house"]["element"]
        assert self.subject.twelfth_house.sign == self.expected_output["twelfth_house"]["sign"]
        assert self.subject.twelfth_house.sign_num == self.expected_output["twelfth_house"]["sign_num"]
        assert self.subject.twelfth_house.position == approx(
            self.expected_output["twelfth_house"]["position"], abs=1e-2
        )
        assert self.subject.twelfth_house.abs_pos == approx(self.expected_output["twelfth_house"]["abs_pos"], abs=_POS_TOL)
        assert self.subject.twelfth_house.emoji == self.expected_output["twelfth_house"]["emoji"]
        assert self.subject.twelfth_house.point_type == self.expected_output["twelfth_house"]["point_type"]

    def test_lunar_phase(self):
        assert self.subject.lunar_phase.model_dump()["degrees_between_s_m"] == approx(
            self.expected_output["lunar_phase"]["degrees_between_s_m"], abs=1e-2
        )
        assert self.subject.lunar_phase.model_dump()["moon_phase"] == self.expected_output["lunar_phase"]["moon_phase"]
        assert self.subject.lunar_phase.model_dump()["moon_emoji"] == self.expected_output["lunar_phase"]["moon_emoji"]
        assert (
            self.subject.lunar_phase.model_dump()["moon_phase_name"]
            == self.expected_output["lunar_phase"]["moon_phase_name"]
        )


@pytest.mark.xdist_group(name="geonames")
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
            online=True,
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
            online=False,
        )
        assert subject.name == "ISO Offline Test"
        assert subject.year == 2019  # UTC midnight = 19:00 previous day in NYC
        assert subject.month == 12
        assert subject.day == 31
        assert subject.hour == 19
        assert subject.lat == approx(40.7128, abs=_POS_TOL)
        assert subject.lng == approx(-74.006, abs=_POS_TOL)

    @pytest.mark.parametrize("bad_iso", ["", "not-a-date", "2023-06-15T25:00:00Z", None])
    def test_from_iso_utc_time_malformed_raises_kerykeion(self, bad_iso):
        """Round 19/20: a malformed ISO timestamp (including a non-string like
        None) must surface as KerykeionException — the library's error contract —
        not a raw ValueError/AttributeError."""
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException):
            AstrologicalSubjectFactory.from_iso_utc_time(
                name="Bad", iso_utc_time=bad_iso,
                lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
            )

    @pytest.mark.parametrize(
        "iso_utc, tz_str",
        [
            ("9999-12-31T23:59:59-14:00", "Etc/GMT-14"),  # overflow past datetime.max
            ("0001-01-01T00:00:00Z", "America/New_York"),  # underflow past datetime.min
            ("0001-01-01T00:00:00Z", "Etc/GMT+10"),
        ],
    )
    def test_from_iso_utc_time_extreme_boundary_raises_kerykeion(self, iso_utc, tz_str):
        """Round 26: an instant near datetime.max/min whose local wall time
        overflows the representable range during the UTC->local conversion must
        surface as KerykeionException (raw OverflowError before), matching
        from_birth_data's contract at the same boundary."""
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException):
            AstrologicalSubjectFactory.from_iso_utc_time(
                name="Edge", iso_utc_time=iso_utc,
                lng=0.0, lat=0.0, tz_str=tz_str, online=False,
            )

    def test_from_current_time(self):
        """Test creating subject for current time."""
        from datetime import datetime, timezone

        import pytz

        # Compare against the current instant IN the chart's timezone, not the
        # host's local clock: near midnight a host in a zone ahead of London
        # would already be on the next calendar day and flake this check.
        now = datetime.now(timezone.utc).astimezone(pytz.timezone("Europe/London"))

        subject = AstrologicalSubjectFactory.from_current_time(
            name="Current Time Test", lng=0.0, lat=51.5074, tz_str="Europe/London", online=False
        )
        assert subject.name == "Current Time Test"
        # Check that it's approximately the current time (within 1 minute)
        assert subject.year == now.year
        assert subject.month == now.month
        assert subject.day == now.day

    def test_sidereal_zodiac_lahiri(self):
        """Test sidereal zodiac calculation with Lahiri ayanamsa."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Test",
            1990,
            1,
            1,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            suppress_geonames_warning=True,
        )
        assert subject.zodiac_type == "Sidereal"
        # Sidereal positions should differ from tropical
        # Sun in tropical Capricorn should be in Sagittarius siderally
        assert subject.sun.sign in ["Sag", "Cap"]

    def test_different_house_systems(self):
        """Test different house systems."""
        # Placidus (default)
        placidus = AstrologicalSubjectFactory.from_birth_data(
            "Placidus",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            houses_system_identifier="P",
            suppress_geonames_warning=True,
        )

        # Koch
        koch = AstrologicalSubjectFactory.from_birth_data(
            "Koch",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            houses_system_identifier="K",
            suppress_geonames_warning=True,
        )

        # Whole Sign (W)
        whole_sign = AstrologicalSubjectFactory.from_birth_data(
            "Whole Sign",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            houses_system_identifier="W",
            suppress_geonames_warning=True,
        )

        # House cusps should differ between systems
        assert placidus.second_house.abs_pos != koch.second_house.abs_pos
        # Different systems should produce different house cusps
        assert placidus.second_house.abs_pos != whole_sign.second_house.abs_pos

    def test_heliocentric_perspective(self):
        """Test heliocentric perspective calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Heliocentric Test",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            perspective_type="Heliocentric",
            suppress_geonames_warning=True,
        )
        # In heliocentric perspective, Earth takes the place of Sun
        # Sun position should be very different or unavailable
        assert subject.name == "Heliocentric Test"

    def test_topocentric_perspective_with_altitude(self):
        """Test topocentric perspective with altitude."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Topocentric Test",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            perspective_type="Topocentric",
            altitude=100.0,
            suppress_geonames_warning=True,
        )
        assert subject.name == "Topocentric Test"

    def test_minimal_active_points(self):
        """Test calculation with minimal active points for performance."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Minimal Points",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Sun", "Moon", "Ascendant"],
            calculate_lunar_phase=False,
            suppress_geonames_warning=True,
        )
        # Should have Sun, Moon, Ascendant
        assert hasattr(subject, "sun")
        assert hasattr(subject, "moon")
        assert hasattr(subject, "ascendant")

    def test_with_seconds_parameter(self):
        """Test birth time with seconds specified."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "With Seconds",
            1990,
            6,
            15,
            12,
            30,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            seconds=45,
            suppress_geonames_warning=True,
        )
        assert subject.hour == 12
        assert subject.minute == 30

    def test_offline_mode_without_coordinates_raises_error(self):
        """Test that offline mode without coordinates raises an error."""
        from kerykeion.schemas import KerykeionException
        import pytest

        with pytest.raises((KerykeionException, Exception)):
            AstrologicalSubjectFactory.from_birth_data(
                "Error Test",
                1990,
                6,
                15,
                12,
                0,
                online=False,
                # Missing lng, lat, tz_str
            )


class TestAstrologicalSubjectModelMethods:
    """Test AstrologicalSubjectModel methods and properties."""

    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Test Subject",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
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
            "Mutable Test",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )
        subject["name"] = "Modified Name"
        assert subject["name"] == "Modified Name"


class TestChartConfiguration:
    """Test ChartConfiguration validation and behavior."""

    def test_valid_sidereal_configuration(self):
        """Test valid sidereal configuration."""
        from kerykeion.astrological_subject_factory import ChartConfiguration

        config = ChartConfiguration(zodiac_type="Sidereal", sidereal_mode="LAHIRI")
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
            ChartConfiguration(zodiac_type="Tropical", sidereal_mode="LAHIRI")

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

    def test_prepare_for_calculation_preserves_polar_latitudes(self):
        """prepare_for_calculation validates but does NOT clamp polar latitudes.

        The real observer latitude must survive into the persisted model, the
        topocentric observer, and every latitude-agnostic house system. Polar
        clamping is applied locally only at the houses call for quadrant systems
        undefined inside the polar circle.
        """
        from kerykeion.astrological_subject_factory import LocationData

        # North Pole: latitude is preserved, not clamped to 66.
        location = LocationData(lat=90.0)
        location.prepare_for_calculation()
        assert location.lat == 90.0

        # South Pole
        location = LocationData(lat=-90.0)
        location.prepare_for_calculation()
        assert location.lat == -90.0

        # A geometrically-impossible latitude is still rejected.
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException):
            LocationData(lat=100.0).prepare_for_calculation()

    def test_check_and_adjust_polar_latitude_still_clamps(self):
        """The clamp helper itself still clamps (used as the houses fallback)."""
        from kerykeion.utilities import check_and_adjust_polar_latitude, validate_latitude

        assert check_and_adjust_polar_latitude(90.0) == 66.0
        assert check_and_adjust_polar_latitude(-90.0) == -66.0
        assert check_and_adjust_polar_latitude(45.0) == 45.0
        # validate_latitude preserves the value but rejects impossible ones.
        assert validate_latitude(78.2232) == 78.2232
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException):
            validate_latitude(100.0)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_midnight_birth(self):
        """Test birth at exactly midnight."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Midnight",
            1990,
            1,
            1,
            0,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )
        assert subject.hour == 0
        assert subject.minute == 0

    def test_leap_year_february_29(self):
        """Test birth on February 29 (leap year)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Leap Year",
            2000,
            2,
            29,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )
        assert subject.year == 2000
        assert subject.month == 2
        assert subject.day == 29

    def test_southern_hemisphere_coordinates(self):
        """Test with southern hemisphere coordinates."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Southern Hemisphere",
            1990,
            12,
            25,
            12,
            0,
            lng=151.2093,
            lat=-33.8688,  # Sydney
            tz_str="Australia/Sydney",
            online=False,
            suppress_geonames_warning=True,
        )
        assert subject.lat == approx(-33.8688, abs=_POS_TOL)
        assert subject.lng == approx(151.2093, abs=_POS_TOL)

    def test_western_hemisphere_coordinates(self):
        """Test with western hemisphere (negative longitude)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Western Hemisphere",
            1990,
            7,
            4,
            12,
            0,
            lng=-118.2437,
            lat=34.0522,  # Los Angeles
            tz_str="America/Los_Angeles",
            online=False,
            suppress_geonames_warning=True,
        )
        assert subject.lat == approx(34.0522, abs=_POS_TOL)
        assert subject.lng == approx(-118.2437, abs=_POS_TOL)

    def test_near_date_line(self):
        """Test with coordinates near international date line."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Date Line",
            1990,
            6,
            15,
            12,
            0,
            lng=179.0,
            lat=-16.5,  # Near Fiji
            tz_str="Pacific/Fiji",
            online=False,
            suppress_geonames_warning=True,
        )
        assert subject.lng == approx(179.0, abs=_POS_TOL)

    def test_without_lunar_phase_calculation(self):
        """Test subject creation without lunar phase."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "No Lunar Phase",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            calculate_lunar_phase=False,
            suppress_geonames_warning=True,
        )
        assert subject.lunar_phase is None


class TestRetrogradePlanets:
    """Test retrograde planet detection."""

    def test_mercury_retrograde_detection(self):
        """Test detection of Mercury retrograde."""
        # Mercury was retrograde in December 2023 (Dec 13 - Jan 1, 2024)
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Mercury Rx",
            2023,
            12,
            20,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )
        # Mercury should be retrograde (negative speed)
        assert subject.mercury.speed < 0
        assert subject.mercury.retrograde is True

    def test_direct_planet_speed(self):
        """Test that direct planets have positive speed."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Direct Test",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )
        # Sun is never retrograde
        assert subject.sun.speed > 0
        assert subject.sun.retrograde is False


class TestDifferentYears:
    """Test calculations for different historical periods."""

    def test_early_20th_century(self):
        """Test calculation for early 1900s."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "1900s",
            1920,
            5,
            10,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )
        assert subject.year == 1920
        assert subject.sun.sign == "Tau"

    def test_future_date(self):
        """Test calculation for future date."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Future",
            2030,
            12,
            25,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )
        assert subject.year == 2030
        assert subject.sun.sign == "Cap"


class TestPerspectiveTypes:
    """Test all perspective types comprehensively."""

    def test_true_geocentric_perspective(self):
        """Test True Geocentric perspective (line 120)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "True Geocentric",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            perspective_type="True Geocentric",
            suppress_geonames_warning=True,
        )
        assert subject.perspective_type == "True Geocentric"
        assert hasattr(subject, "sun")


class TestTimeZoneEdgeCases:
    """Test DST and timezone edge cases."""

    def test_dst_time_with_is_dst_false(self):
        """Test DST time with is_dst=False."""
        # During DST fall-back, 2:30 AM occurs twice
        # Setting is_dst=False selects the second occurrence (standard time)
        subject = AstrologicalSubjectFactory.from_birth_data(
            "DST False",
            2023,
            11,
            5,
            2,
            30,
            lng=-74.006,
            lat=40.7128,
            tz_str="America/New_York",
            online=False,
            is_dst=False,
            suppress_geonames_warning=True,
        )
        assert subject.hour == 2

    def test_dst_time_with_is_dst_true(self):
        """Test DST time with is_dst=True."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "DST True",
            2023,
            11,
            5,
            2,
            30,
            lng=-74.006,
            lat=40.7128,
            tz_str="America/New_York",
            online=False,
            is_dst=True,
            suppress_geonames_warning=True,
        )
        assert subject.hour == 2

    def test_from_iso_utc_time_dst_fold_constructs_both_sides(self):
        """v6 regression: from_iso_utc_time must not raise "Ambiguous time"
        for UTC instants whose local wall time falls inside the DST fall-back
        fold. Europe/Rome, 2024-10-27: 02:30 wall time occurs twice — as CEST
        (00:30Z) and as CET (01:30Z). The factory must derive is_dst from the
        unambiguous UTC->local conversion and round-trip both instants to
        their distinct original UTC julian days."""
        common = dict(
            city="Rome",
            nation="IT",
            tz_str="Europe/Rome",
            online=False,
            lng=12.4964,
            lat=41.9028,
            suppress_geonames_warning=True,
        )
        first = AstrologicalSubjectFactory.from_iso_utc_time(
            "Fold CEST", "2024-10-27T00:30:00Z", **common
        )
        second = AstrologicalSubjectFactory.from_iso_utc_time(
            "Fold CET", "2024-10-27T01:30:00Z", **common
        )

        # Both UTC instants map to the same ambiguous local wall time...
        assert (first.hour, first.minute) == (2, 30)
        assert (second.hour, second.minute) == (2, 30)
        assert first.iso_formatted_local_datetime.startswith("2024-10-27T02:30:00")
        assert second.iso_formatted_local_datetime.startswith("2024-10-27T02:30:00")
        assert first.iso_formatted_local_datetime.endswith("+02:00")  # CEST (DST side)
        assert second.iso_formatted_local_datetime.endswith("+01:00")  # CET (standard side)

        # ...but must round-trip to the two distinct original UTC instants.
        assert first.iso_formatted_utc_datetime.startswith("2024-10-27T00:30:00")
        assert second.iso_formatted_utc_datetime.startswith("2024-10-27T01:30:00")
        assert first.julian_day == approx(2460610.5208333335, abs=1e-8)
        assert second.julian_day == approx(2460610.5625, abs=1e-8)
        assert second.julian_day - first.julian_day == approx(1.0 / 24.0, abs=1e-8)

    def test_pre_standardization_uses_birth_longitude_lmt(self):
        """Pre-standardization births (IANA zone still in its 'LMT' period) must
        derive UTC from the *birth longitude*'s Local Mean Time, not the zone's
        reference meridian. Einstein (1879-03-14 11:30, Ulm 9.99 E, tz
        Europe/Berlin): astro.com uses Ulm's longitude (+00:39:58 -> 10:50 UTC),
        not Berlin's meridian (+00:53 -> 10:37). Asserts only the time
        conversion, so it is independent of the ephemeris kernel (DE440/DE441)."""
        einstein = AstrologicalSubjectFactory.from_birth_data(
            "Einstein", 1879, 3, 14, 11, 30,
            city="Ulm", nation="DE", lng=9.9916, lat=48.3984,
            tz_str="Europe/Berlin", online=False, suppress_geonames_warning=True,
        )
        assert einstein.iso_formatted_utc_datetime.startswith("1879-03-14T10:50:02")
        assert einstein.iso_formatted_local_datetime.endswith("+00:39:58")

    def test_lmt_offset_follows_longitude_not_zone_meridian(self):
        """Same IANA zone, different birth longitudes -> different LMT offsets.
        Berlin (13.4 E) and Ulm (9.99 E) both use tz Europe/Berlin, but a
        pre-standardization birth must resolve to each city's own solar time."""
        common = dict(
            year=1879, month=3, day=14, hour=11, minute=30,
            nation="DE", tz_str="Europe/Berlin", online=False,
            lat=50.0, suppress_geonames_warning=True,
        )
        berlin = AstrologicalSubjectFactory.from_birth_data("B", city="Berlin", lng=13.4, **common)
        ulm = AstrologicalSubjectFactory.from_birth_data("U", city="Ulm", lng=9.9916, **common)
        assert berlin.iso_formatted_local_datetime.endswith("+00:53:36")
        assert ulm.iso_formatted_local_datetime.endswith("+00:39:58")
        # Same clock time, different solar longitudes -> different UTC instants.
        assert berlin.iso_formatted_utc_datetime != ulm.iso_formatted_utc_datetime

    def test_modern_date_unaffected_by_longitude_lmt(self):
        """Modern births (standardized time, zone NOT in its 'LMT' period) must
        be unchanged: UTC comes from the IANA zone offset, not longitude/15."""
        modern = AstrologicalSubjectFactory.from_birth_data(
            "Modern", 1990, 1, 15, 14, 30,
            city="Sydney", nation="AU", lng=151.2073, lat=-33.8678,
            tz_str="Australia/Sydney", online=False, suppress_geonames_warning=True,
        )
        # AEDT (+11:00) applied as a whole-hour zone offset, not longitude-based.
        assert modern.iso_formatted_local_datetime.endswith("+11:00")
        assert modern.iso_formatted_utc_datetime.startswith("1990-01-15T03:30:00")

    def test_from_iso_utc_time_pre_standardization_round_trips(self):
        """from_iso_utc_time must round-trip a pre-standardization UTC instant.
        UTC->local has to use the same birth-longitude LMT as from_birth_data,
        otherwise the wall time is double-interpreted (zone meridian then
        longitude) and the round-trip guard rejects the ~13-min shift. Einstein:
        UTC 10:50:02 -> Ulm local 11:30:00 (+00:39:58) -> back to UTC 10:50:02."""
        s = AstrologicalSubjectFactory.from_iso_utc_time(
            "Einstein UTC", "1879-03-14T10:50:02+00:00",
            city="Ulm", nation="DE", lng=9.9916, lat=48.3984,
            tz_str="Europe/Berlin", online=False, suppress_geonames_warning=True,
        )
        assert s.iso_formatted_utc_datetime.startswith("1879-03-14T10:50:02")
        assert s.iso_formatted_local_datetime.startswith("1879-03-14T11:30:00")
        assert s.iso_formatted_local_datetime.endswith("+00:39:58")

    def test_from_iso_utc_time_lmt_transition_boundary_round_trips(self):
        """A UTC instant in the LMT period whose birth-longitude wall time lands
        just past the IANA LMT->standard transition must still round-trip.
        Africa/Nairobi leaves LMT ~1908-05-01; UTC 1908-04-30T21:20Z (still LMT)
        maps to local 1908-05-01T00:07:36 at lng 41.9 — i.e. past the boundary.
        The offset is passed explicitly so from_birth_data does not re-localize
        that wall time as the post-transition +02:30 zone (which broke the
        round-trip guard before the fix)."""
        s = AstrologicalSubjectFactory.from_iso_utc_time(
            "Nairobi LMT", "1908-04-30T21:20:00+00:00",
            city="Nairobi", nation="KE", lng=41.9, lat=0.0,
            tz_str="Africa/Nairobi", online=False, suppress_geonames_warning=True,
        )
        assert s.iso_formatted_utc_datetime.startswith("1908-04-30T21:20:00")
        assert s.iso_formatted_local_datetime.endswith("+02:47:36")


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
                sidereal_mode="INVALID_MODE",  # type: ignore
            )

    def test_model_rejects_sidereal_without_mode(self):
        """The model validator enforces Sidereal => a concrete sidereal_mode.

        Factory-built subjects always carry a mode; this guards direct/manual
        model construction (the previously-masked ambiguous case).
        """
        from kerykeion.schemas.kr_models import AstrologicalSubjectModel
        from pydantic import ValidationError
        import pytest

        subj = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Validator",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
        )
        data = subj.model_dump()
        data["sidereal_mode"] = None
        with pytest.raises(ValidationError, match="sidereal_mode is required"):
            AstrologicalSubjectModel.model_validate(data)


class TestAdditionalPlanets:
    """Test additional planets and points that require special ephemeris files."""

    def test_trans_neptunian_objects(self):
        """Test trans-Neptunian objects calculation attempts."""
        # These will log warnings but should not crash
        subject = AstrologicalSubjectFactory.from_birth_data(
            "TNO Test",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Sun", "Moon", "Ixion", "Orcus", "Quaoar"],
            suppress_geonames_warning=True,
        )
        # Sun and Moon should always be calculated
        assert hasattr(subject, "sun")
        assert hasattr(subject, "moon")
        # TNOs may or may not be present depending on ephemeris files


class TestDefaultTimeParameters:
    """Test default time parameters (lines 555-561)."""

    def test_defaults_to_current_time_when_none(self):
        """Test that None time parameters default to current time."""
        from datetime import datetime, timezone

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
            suppress_geonames_warning=True,
        )

        # The factory resolves "now" in the subject's own timezone (Etc/GMT = UTC
        # here), so compare against UTC now — not naive local time, which can
        # differ from the GMT day near midnight in a non-UTC local timezone.
        now = datetime.now(timezone.utc)
        assert subject.year == now.year
        assert subject.month == now.month
        assert subject.day == now.day


@pytest.mark.xdist_group(name="geonames")
class TestGeonamesUsernameWarning:
    """Test geonames username warning (lines 594-595)."""

    def test_online_mode_without_username_uses_default(self):
        """Test that online mode without username triggers warning."""

        # This should use default username and log warning
        subject = AstrologicalSubjectFactory.from_birth_data(
            "No Username",
            1990,
            6,
            15,
            12,
            0,
            city="London",
            nation="GB",
            online=True,
            geonames_username=None,  # Will trigger default
        )

        assert subject.name == "No Username"


class TestExceptionHandlingInPlanetCalculation:
    """Test exception handling in planet calculation (lines 1184-1187)."""

    def test_error_in_planet_calculation_removes_from_active_points(self):
        """Test that calculation errors are handled gracefully."""
        # This is already partially covered by the Eris/Sedna warnings
        # We need to verify the mechanism works
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Error Handling",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Sun", "Moon", "Eris"],  # Eris will fail
            suppress_geonames_warning=True,
        )

        # Sun and Moon should be calculated, Eris should fail gracefully
        assert hasattr(subject, "sun")
        assert hasattr(subject, "moon")
        # Eris is not calculated due to missing ephemeris file

    def test_auto_activated_luminary_backend_error_raises_kerykeion_exception(self, monkeypatch):
        """v6 regression: when an Arabic part auto-activates Sun/Moon and the
        backend cannot compute them, _ensure_point_calculated must apply the
        same typed-error policy as _calculate_single_planet and raise
        KerykeionException — not leak the raw backend exception (e.g.
        libephemeris.EphemerisRangeError). The backend gap is simulated with
        monkeypatch: extreme years are in range on a full DE441 install."""
        from kerykeion.ephemeris_backend import ephe
        from kerykeion.schemas import KerykeionException

        real_calc_ut = ephe.calc_ut

        def fake_calc_ut(jd, ipl, flags):
            if ipl == 0:  # Sun: simulate an ephemeris-range gap in the backend
                raise RuntimeError("jd outside ephemeris range")
            return real_calc_ut(jd, ipl, flags)

        monkeypatch.setattr(ephe, "calc_ut", fake_calc_ut)

        # Pars_Fortunae auto-activates Ascendant, Sun and Moon; with Sun absent
        # from active_points the Sun is computed via _ensure_point_calculated.
        with pytest.raises(KerykeionException, match="Sun"):
            AstrologicalSubjectFactory.from_birth_data(
                "Range Gap Luminary",
                1990,
                6,
                15,
                12,
                0,
                lng=0.0,
                lat=51.5074,
                tz_str="Etc/GMT",
                online=False,
                active_points=["Pars_Fortunae"],
                suppress_geonames_warning=True,
            )

    def test_auto_activated_optional_point_backend_error_degrades_gracefully(self, monkeypatch):
        """Auto-activated NON-luminary prerequisites (e.g. Venus for
        Pars_Amoris) must degrade gracefully on backend errors: the dependent
        Arabic part is skipped and no raw backend exception escapes."""
        from kerykeion.ephemeris_backend import ephe
        from kerykeion.astrological_subject_factory import STANDARD_PLANETS

        venus_id = STANDARD_PLANETS["Venus"]
        real_calc_ut = ephe.calc_ut

        def fake_calc_ut(jd, ipl, flags):
            if ipl == venus_id:  # simulate a backend gap for Venus only
                raise RuntimeError("jd outside ephemeris range")
            return real_calc_ut(jd, ipl, flags)

        monkeypatch.setattr(ephe, "calc_ut", fake_calc_ut)

        subject = AstrologicalSubjectFactory.from_birth_data(
            "Range Gap Optional",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Sun", "Moon", "Pars_Amoris"],
            suppress_geonames_warning=True,
        )

        assert subject.sun is not None
        assert subject.venus is None
        assert subject.pars_amoris is None
        assert "Venus" not in subject.active_points
        assert "Pars_Amoris" not in subject.active_points


class TestEnrichmentSessionContainment:
    """v6 regression: the optional enrichments (Gauquelin sectors, local
    space, OOB obliquity, nutation) call ephe.* functions, so they must run
    INSIDE the factory's ephemeris session — under EPHEMERIS_LOCK with the
    session's ephemeris path configured — never after the session reset."""

    def test_enrichment_swe_calls_run_before_session_reset(self, monkeypatch):
        import kerykeion.ephemeris_backend as eb

        events = []

        real_reset = eb.reset_ephemeris_session
        real_azalt = eb.ephe.azalt
        real_gauquelin = eb.ephe.gauquelin_sector
        real_calc_ut = eb.ephe.calc_ut
        ecl_nut = eb.ephe.ECL_NUT

        def tracking_reset():
            events.append("session_reset")
            real_reset()

        def tracking_azalt(*args, **kwargs):
            events.append("azalt")
            return real_azalt(*args, **kwargs)

        def tracking_gauquelin(*args, **kwargs):
            events.append("gauquelin_sector")
            return real_gauquelin(*args, **kwargs)

        def tracking_calc_ut(jd, ipl, flags):
            if ipl == ecl_nut:  # OOB obliquity + nutation calls
                events.append("calc_ut_ecl_nut")
            return real_calc_ut(jd, ipl, flags)

        # ephemeris_session resolves reset_ephemeris_session from its module
        # globals at exit time, so patching the module attribute intercepts
        # the session teardown.
        monkeypatch.setattr(eb, "reset_ephemeris_session", tracking_reset)
        monkeypatch.setattr(eb.ephe, "azalt", tracking_azalt)
        monkeypatch.setattr(eb.ephe, "gauquelin_sector", tracking_gauquelin)
        monkeypatch.setattr(eb.ephe, "calc_ut", tracking_calc_ut)

        AstrologicalSubjectFactory.from_birth_data(
            "Session Containment",
            1990,
            6,
            15,
            14,
            30,
            lng=12.4964,
            lat=41.9028,
            tz_str="Europe/Rome",
            online=False,
            calculate_gauquelin=True,
            calculate_local_space=True,
            calculate_nutation=True,
            suppress_geonames_warning=True,
        )

        assert "azalt" in events
        assert "gauquelin_sector" in events
        assert "calc_ut_ecl_nut" in events
        assert "session_reset" in events

        first_reset = events.index("session_reset")
        escaped = [e for e in events[first_reset:] if e != "session_reset"]
        assert not escaped, f"ephe enrichment calls escaped the ephemeris session: {escaped}"


class TestArabicParts:
    """Test Arabic Parts calculations (lines 1582-1787)."""

    def test_pars_fortunae_calculation(self):
        """Test Part of Fortune calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Pars Fortunae Test",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Fortunae", "Sun", "Moon", "Ascendant"],
            suppress_geonames_warning=True,
        )

        assert hasattr(subject, "pars_fortunae")
        assert subject.pars_fortunae.name == "Pars_Fortunae"
        assert subject.pars_fortunae.retrograde is False

    def test_pars_fortunae_auto_activates_required_points(self):
        """Test that Pars Fortunae auto-activates required points."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Auto Activate",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Fortunae"],  # Only Pars, should auto-add Sun, Moon, Ascendant
            suppress_geonames_warning=True,
        )

        assert hasattr(subject, "pars_fortunae")
        assert hasattr(subject, "sun")
        assert hasattr(subject, "moon")
        assert hasattr(subject, "ascendant")

    def test_pars_spiritus_calculation(self):
        """Test Part of Spirit calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Pars Spiritus Test",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Spiritus", "Sun", "Moon", "Ascendant"],
            suppress_geonames_warning=True,
        )

        assert hasattr(subject, "pars_spiritus")
        assert subject.pars_spiritus.name == "Pars_Spiritus"

    def test_pars_amoris_calculation(self):
        """Test Part of Eros/Love calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Pars Amoris Test",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Amoris", "Venus", "Sun", "Ascendant"],
            suppress_geonames_warning=True,
        )

        assert hasattr(subject, "pars_amoris")
        assert subject.pars_amoris.name == "Pars_Amoris"

    def test_pars_fidei_calculation(self):
        """Test Part of Faith calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Pars Fidei Test",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Fidei", "Jupiter", "Saturn", "Ascendant"],
            suppress_geonames_warning=True,
        )

        assert hasattr(subject, "pars_fidei")
        assert subject.pars_fidei.name == "Pars_Fidei"


class TestVertexCalculation:
    """Test Vertex and Anti-Vertex calculations (lines 1804, 1836-1841)."""

    def test_vertex_calculation(self):
        """Test Vertex calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Vertex Test",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Vertex"],
            suppress_geonames_warning=True,
        )

        assert hasattr(subject, "vertex")
        assert subject.vertex.name == "Vertex"
        assert subject.vertex.retrograde is False

    def test_anti_vertex_calculation(self):
        """Test Anti-Vertex calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Anti-Vertex Test",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Anti_Vertex"],
            suppress_geonames_warning=True,
        )

        assert hasattr(subject, "anti_vertex")
        assert subject.anti_vertex.name == "Anti_Vertex"

    def test_both_vertex_and_anti_vertex(self):
        """Test calculating both Vertex and Anti-Vertex."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Both Vertex",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Vertex", "Anti_Vertex"],
            suppress_geonames_warning=True,
        )

        assert hasattr(subject, "vertex")
        assert hasattr(subject, "anti_vertex")
        # Anti-Vertex should be 180 degrees from Vertex
        expected_anti = (subject.vertex.abs_pos + 180) % 360
        assert subject.anti_vertex.abs_pos == approx(expected_anti, abs=_POS_TOL)


class TestFixedStars:
    """Test Fixed Stars calculations (lines 1754-1787)."""

    def test_regulus_calculation(self):
        """Test Regulus (fixed star) calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Regulus Test",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_fixed_stars=["Regulus"],
            suppress_geonames_warning=True,
        )

        regulus = subject.find_fixed_star("Regulus")
        assert regulus is not None
        assert regulus.name == "Regulus"
        assert regulus.retrograde is False  # Fixed stars are never retrograde

    def test_spica_calculation(self):
        """Test Spica (fixed star) calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Spica Test",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_fixed_stars=["Spica"],
            suppress_geonames_warning=True,
        )

        spica = subject.find_fixed_star("Spica")
        assert spica is not None
        assert spica.name == "Spica"
        assert spica.retrograde is False


class TestNightChartCalculations:
    """Test night chart calculations for Arabic Parts."""

    def test_night_chart_pars_fortunae(self):
        """Test Part of Fortune for night chart (Sun below horizon)."""
        # Birth at night - Sun below the horizon
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Night Chart",
            1990,
            6,
            15,
            0,
            0,  # Midnight
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Fortunae", "Sun", "Moon", "Ascendant"],
            suppress_geonames_warning=True,
        )

        assert hasattr(subject, "pars_fortunae")
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
                    "geonames_username": "century.boy",
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
        from kerykeion.ephemeris_backend import ephe

        # Mock ephe.calc_ut to raise an exception for a specific planet
        original_calc = ephe.calc_ut

        def mock_calc_ut(jd, planet_num, flags):
            # Raise exception for Mercury (planet 2)
            if planet_num == 2:
                raise Exception("Mock ephemeris error")
            return original_calc(jd, planet_num, flags)

        with patch("kerykeion.ephemeris_backend.ephe.calc_ut", side_effect=mock_calc_ut):
            # This should handle the error gracefully
            subject = AstrologicalSubjectFactory.from_birth_data(
                "Error Test",
                1990,
                6,
                15,
                12,
                0,
                lng=0.0,
                lat=51.5074,
                tz_str="Etc/GMT",
                online=False,
                active_points=["Sun", "Mercury", "Moon"],
                suppress_geonames_warning=True,
            )

            # Sun and Moon should be calculated, Mercury should fail
            assert hasattr(subject, "sun")
            assert hasattr(subject, "moon")
            # Mercury may not be in active_points due to error

    def test_ambiguous_time_error_with_pytz_exception(self):
        """Test ambiguous DST time error (lines 972-978)."""
        from unittest.mock import patch, MagicMock
        from kerykeion.schemas import KerykeionException
        import pytz
        import pytest

        # Mock the localize method to raise AmbiguousTimeError
        with patch("pytz.timezone") as mock_tz:
            mock_tz_instance = MagicMock()
            mock_tz_instance.localize.side_effect = pytz.exceptions.AmbiguousTimeError("Test ambiguous")
            mock_tz.return_value = mock_tz_instance

            with pytest.raises(KerykeionException, match="Ambiguous time error"):
                AstrologicalSubjectFactory.from_birth_data(
                    "Ambiguous",
                    2023,
                    11,
                    5,
                    2,
                    30,
                    lng=-74.006,
                    lat=40.7128,
                    tz_str="America/New_York",
                    online=False,
                    suppress_geonames_warning=True,
                )

    def test_nonexistent_time_error(self):
        """Test non-existent DST time error."""
        from unittest.mock import patch, MagicMock
        from kerykeion.schemas import KerykeionException
        import pytz
        import pytest

        # Mock the localize method to raise NonExistentTimeError
        with patch("pytz.timezone") as mock_tz:
            mock_tz_instance = MagicMock()
            mock_tz_instance.localize.side_effect = pytz.exceptions.NonExistentTimeError("Test nonexistent")
            mock_tz.return_value = mock_tz_instance

            with pytest.raises(KerykeionException, match="Non-existent time error"):
                AstrologicalSubjectFactory.from_birth_data(
                    "Nonexistent",
                    2023,
                    3,
                    12,
                    2,
                    30,
                    lng=-74.006,
                    lat=40.7128,
                    tz_str="America/New_York",
                    online=False,
                    suppress_geonames_warning=True,
                )

    def test_day_chart_vs_night_chart(self):
        """Test day vs night chart calculation for Arabic Parts (line 1589)."""
        # Day chart - Sun above the horizon
        day_subject = AstrologicalSubjectFactory.from_birth_data(
            "Day Chart",
            1990,
            6,
            15,
            12,
            0,  # Noon
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Fortunae", "Sun", "Moon", "Ascendant"],
            suppress_geonames_warning=True,
        )

        # Night chart - Sun below the horizon
        night_subject = AstrologicalSubjectFactory.from_birth_data(
            "Night Chart",
            1990,
            6,
            15,
            0,
            0,  # Midnight
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Fortunae", "Sun", "Moon", "Ascendant"],
            suppress_geonames_warning=True,
        )

        # Both should have Pars Fortunae calculated
        assert hasattr(day_subject, "pars_fortunae")
        assert hasattr(night_subject, "pars_fortunae")
        # Values should differ due to different formula
        assert day_subject.pars_fortunae.abs_pos != night_subject.pars_fortunae.abs_pos

    def test_day_night_formula_correctness(self):
        """Verify that the correct formula is applied for day and night charts.

        Day formula:   Pars Fortunae = Asc + Moon - Sun
        Night formula: Pars Fortunae = Asc + Sun - Moon
        """
        import math

        # Noon in London on June 15, 1990 — Sun is above the horizon (day chart)
        day_subject = AstrologicalSubjectFactory.from_birth_data(
            "Day Formula Check",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Fortunae", "Sun", "Moon", "Ascendant"],
            suppress_geonames_warning=True,
        )

        asc = day_subject.ascendant.abs_pos
        sun = day_subject.sun.abs_pos
        moon = day_subject.moon.abs_pos

        # Day chart: Pars Fortunae = Asc + Moon - Sun
        expected_day = math.fmod(asc + moon - sun, 360)
        if expected_day < 0:
            expected_day += 360

        assert day_subject.pars_fortunae.abs_pos == approx(expected_day, abs=0.01), (
            f"Day chart formula mismatch: got {day_subject.pars_fortunae.abs_pos}, "
            f"expected Asc({asc}) + Moon({moon}) - Sun({sun}) = {expected_day}"
        )

        # Midnight in London on June 15, 1990 — Sun is below the horizon (night chart)
        night_subject = AstrologicalSubjectFactory.from_birth_data(
            "Night Formula Check",
            1990,
            6,
            15,
            0,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Fortunae", "Sun", "Moon", "Ascendant"],
            suppress_geonames_warning=True,
        )

        asc = night_subject.ascendant.abs_pos
        sun = night_subject.sun.abs_pos
        moon = night_subject.moon.abs_pos

        # Night chart: Pars Fortunae = Asc + Sun - Moon
        expected_night = math.fmod(asc + sun - moon, 360)
        if expected_night < 0:
            expected_night += 360

        assert night_subject.pars_fortunae.abs_pos == approx(expected_night, abs=0.01), (
            f"Night chart formula mismatch: got {night_subject.pars_fortunae.abs_pos}, "
            f"expected Asc({asc}) + Sun({sun}) - Moon({moon}) = {expected_night}"
        )

    def test_arabic_parts_missing_required_points_auto_activation(self):
        """Test that Arabic Parts auto-activate missing required points (line 1625)."""
        # Test with Pars Fortunae but no Ascendant - should auto-activate
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Auto Activate Test",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Pars_Fortunae"],  # Only this, should add Sun, Moon, Ascendant
            suppress_geonames_warning=True,
        )

        # All required points should be present
        assert hasattr(subject, "pars_fortunae")
        assert hasattr(subject, "sun")
        assert hasattr(subject, "moon")
        assert hasattr(subject, "ascendant")

    def test_pars_fortunae_sidereal_with_auto_activation(self):
        """Test Pars Fortunae with sidereal zodiac and auto-activation (line 1589)."""
        # This should trigger the sidereal branch in Pars Fortunae auto-activation
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Pars",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            active_points=["Pars_Fortunae"],  # Only this - will auto-add and trigger sidereal path
            suppress_geonames_warning=True,
        )

        assert hasattr(subject, "pars_fortunae")
        assert subject.zodiac_type == "Sidereal"

    def test_pars_spiritus_sidereal_with_auto_activation(self):
        """Test Pars Spiritus with sidereal zodiac and auto-activation (line 1625+)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Spiritus",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            active_points=["Pars_Spiritus"],  # Will trigger sidereal branch in auto-activation
            suppress_geonames_warning=True,
        )

        assert hasattr(subject, "pars_spiritus")

    def test_pars_amoris_sidereal_with_auto_activation(self):
        """Test Pars Amoris with sidereal zodiac."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Amoris",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            active_points=["Pars_Amoris"],
            suppress_geonames_warning=True,
        )

        assert hasattr(subject, "pars_amoris")

    def test_pars_fidei_sidereal_with_auto_activation(self):
        """Test Pars Fidei with sidereal zodiac."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Fidei",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            active_points=["Pars_Fidei"],
            suppress_geonames_warning=True,
        )

        assert hasattr(subject, "pars_fidei")

    def test_vertex_sidereal(self):
        """Test Vertex with sidereal zodiac (line 1804)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Vertex",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            active_points=["Vertex", "Anti_Vertex"],
            suppress_geonames_warning=True,
        )

        assert hasattr(subject, "vertex")
        assert hasattr(subject, "anti_vertex")


@pytest.mark.xdist_group(name="geonames")
class TestAllDwarfPlanetsAndFixedStars:
    """Test all dwarf planets and fixed stars to trigger exception branches."""

    def test_all_trans_neptunian_objects_attempt(self):
        """Test ALL TNOs to trigger their exception handling."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "All TNOs",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Sun", "Moon", "Eris", "Sedna", "Haumea", "Makemake", "Ixion", "Orcus", "Quaoar"],
            suppress_geonames_warning=True,
        )

        # Sun and Moon should always work
        assert hasattr(subject, "sun")
        assert hasattr(subject, "moon")
        # Others will fail gracefully with warnings

    def test_all_fixed_stars_attempt(self):
        """v6: stars are populated via active_fixed_stars and accessed via find_fixed_star."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Fixed Stars",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Sun"],
            active_fixed_stars=["Regulus", "Spica"],
            suppress_geonames_warning=True,
        )

        assert subject.sun is not None
        assert subject.find_fixed_star("Regulus") is not None
        assert subject.find_fixed_star("Spica") is not None

    def test_vertex_calculation_with_exception_mock(self):
        """Test Vertex exception handling (line 1836-1841)."""
        from unittest.mock import patch
        from kerykeion.ephemeris_backend import ephe

        # First create subject normally to ensure houses work
        # Then mock only the Vertex calculation part
        original_houses = ephe.houses_ex

        def conditional_mock(*args, **kwargs):
            # Check if this is being called with 'V' house system (for Vertex)
            if kwargs.get("hsys") == b"V":
                raise Exception("Mock vertex error")
            return original_houses(*args, **kwargs)

        with patch("kerykeion.ephemeris_backend.ephe.houses_ex", side_effect=conditional_mock):
            subject = AstrologicalSubjectFactory.from_birth_data(
                "Vertex Error",
                1990,
                6,
                15,
                12,
                0,
                lng=0.0,
                lat=51.5074,
                tz_str="Etc/GMT",
                online=False,
                active_points=["Vertex", "Anti_Vertex", "Sun"],
                suppress_geonames_warning=True,
            )

            # Vertex should be None due to exception, but subject created successfully
            assert subject is not None
            assert hasattr(subject, "sun")

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
            "altitude": 0,
        }

        with patch("kerykeion.astrological_subject_factory.FetchGeonames", return_value=mock_geonames):
            try:
                AstrologicalSubjectFactory.from_birth_data(
                    "Geonames Error",
                    1990,
                    1,
                    1,
                    12,
                    0,
                    city="TestCity",
                    nation="TestNation",
                    online=True,
                    suppress_geonames_warning=True,
                )
                # Should raise exception before reaching here
                assert False, "Expected KerykeionException"
            except Exception as e:
                # Should be KerykeionException with "Missing data from geonames"
                assert "Missing data from geonames" in str(e)

    def test_tno_successful_calculations_with_real_ephemeris(self):
        """Test successful TNO calculations with real ephemeris files (lines 1456-1531)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "TNO Success",
            1990,
            1,
            1,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Eris", "Sedna", "Haumea", "Makemake", "Ixion", "Orcus", "Quaoar", "Sun"],
            suppress_geonames_warning=True,
        )

        # All TNOs should be present with real ephemeris files
        assert hasattr(subject, "sun")
        assert hasattr(subject, "eris")
        assert subject.eris is not None
        assert hasattr(subject.eris, "abs_pos")
        assert hasattr(subject.eris, "retrograde")

        assert hasattr(subject, "sedna")
        assert subject.sedna is not None

        assert hasattr(subject, "haumea")
        assert subject.haumea is not None

        assert hasattr(subject, "makemake")
        assert subject.makemake is not None

        assert hasattr(subject, "ixion")
        assert subject.ixion is not None

        assert hasattr(subject, "orcus")
        assert subject.orcus is not None

        assert hasattr(subject, "quaoar")
        assert subject.quaoar is not None

    def test_fixed_stars_successful_calculations_with_real_ephemeris(self):
        """Test successful fixed star calculations with real ephemeris (lines 1552-1570)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Fixed Stars Success",
            1990,
            1,
            1,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            active_points=["Sun"],
            active_fixed_stars=["Regulus", "Spica"],
            suppress_geonames_warning=True,
        )

        # Sun (planet) reaches the model as a typed field
        assert subject.sun is not None

        # Fixed stars (v6) live in the unified array, accessed via find_fixed_star
        regulus = subject.find_fixed_star("Regulus")
        assert regulus is not None
        assert hasattr(regulus, "abs_pos")
        assert not regulus.retrograde  # Fixed stars are never retrograde

        spica = subject.find_fixed_star("Spica")
        assert spica is not None
        assert hasattr(spica, "abs_pos")
        assert not spica.retrograde


# =============================================================================
# ISO UTC TIME EQUIVALENCE (from factories/test_utc.py)
# =============================================================================


class TestIsoUtcTimeEquivalence:
    """Test that from_iso_utc_time produces identical results to from_birth_data."""

    @pytest.mark.online
    @pytest.mark.xdist_group(name="geonames")
    def test_utc_constructor_equivalence(self):
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", suppress_geonames_warning=True
        )
        subject2 = AstrologicalSubjectFactory.from_iso_utc_time(
            "Johnny Depp", "1963-06-09T05:00:00+00:00", "Owensboro", "US", online=True
        )

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
        assert subject.seventh_house == subject2.seventh_house
        assert subject.tenth_house == subject2.tenth_house
        assert subject.mean_north_lunar_node == subject2.mean_north_lunar_node
        assert subject.true_north_lunar_node == subject2.true_north_lunar_node
        assert subject.lunar_phase == subject2.lunar_phase
        assert subject.active_points == subject2.active_points


class TestDayOfWeekAnteCommonEra:
    """For year<1 the weekday must be computed from the LOCAL date (like the
    year>=1 path, which uses iso_formatted_local_datetime), not the UT julian
    day — near local midnight the LMT offset changes the calendar day."""

    @staticmethod
    def _weekday(year, month, day, hour, minute, lng):
        from kerykeion.ephemeris_backend import ephe
        from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

        dec_hour = hour + minute / 60.0
        jd_local = ephe.julday(year, month, day, dec_hour, ephe.JUL_CAL)
        data = {
            "year": year,
            "lng": lng,
            "julian_day": jd_local - (lng / 15.0) / 24.0,
        }
        AstrologicalSubjectFactory._calculate_day_of_week(data)
        return data["day_of_week"]

    def test_weekday_matches_local_date_near_midnight(self):
        # 00:30 local at 120E: the UT date is still the previous day; the
        # weekday must follow the local date.
        just_after_midnight = self._weekday(-100, 6, 15, 0, 30, lng=120.0)
        midday_same_date = self._weekday(-100, 6, 15, 12, 0, lng=120.0)
        assert just_after_midnight == midday_same_date

    def test_weekday_advances_across_local_midnight(self):
        _DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        before = self._weekday(-100, 6, 14, 23, 30, lng=120.0)
        after = self._weekday(-100, 6, 15, 0, 30, lng=120.0)
        assert (_DAYS.index(before) + 1) % 7 == _DAYS.index(after)


class TestOnlineGeonamesGating:
    """Regression tests for the online-mode GeoNames gating fixes: explicit
    inputs must never be overwritten by the city centroid, from_current_time
    must capture the target-timezone instant, and a failed fetch must raise
    KerykeionException, not KeyError."""

    _ROME = {"countryCode": "IT", "timezonestr": "Europe/Rome", "lat": "41.89193", "lng": "12.51133"}

    @pytest.fixture
    def _mock_geonames(self, monkeypatch):
        from kerykeion import fetch_geonames

        data = dict(self._ROME)
        monkeypatch.setattr(
            fetch_geonames.FetchGeonames, "get_serialized_data", lambda self: dict(data)
        )
        return data

    def test_explicit_coordinates_survive_online_fetch(self, _mock_geonames):
        from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

        s = AstrologicalSubjectFactory.from_birth_data(
            "Precise", 1990, 6, 15, 12, 0,
            city="Rome", nation="IT", online=True,
            lat=45.999, lng=7.111,  # explicit, more precise than the centroid
            suppress_geonames_warning=True,
        )
        assert s.lat == pytest.approx(45.999)
        assert s.lng == pytest.approx(7.111)
        assert s.tz_str == "Europe/Rome"  # missing field filled from the fetch

    def test_from_current_time_uses_target_timezone_instant(self, monkeypatch):
        from datetime import datetime, timedelta, timezone
        from kerykeion import fetch_geonames
        from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

        auckland = {"countryCode": "NZ", "timezonestr": "Pacific/Auckland", "lat": "-36.85", "lng": "174.76"}
        monkeypatch.setattr(
            fetch_geonames.FetchGeonames, "get_serialized_data", lambda self: dict(auckland)
        )
        before = datetime.now(timezone.utc)
        s = AstrologicalSubjectFactory.from_current_time(
            "Now Test", city="Auckland", nation="NZ", online=True,
            suppress_geonames_warning=True,
        )
        after = datetime.now(timezone.utc)
        got = datetime.fromisoformat(s.iso_formatted_utc_datetime)
        # The captured instant must be the real current UTC moment, not the
        # host wall clock re-interpreted in the target timezone.
        assert before - timedelta(seconds=5) <= got <= after + timedelta(seconds=5)

    @pytest.mark.parametrize(
        "kwargs,fetched",
        [
            # Default path (no city/nation): Greenwich/GB -> Europe/London.
            ({}, {"countryCode": "GB", "timezonestr": "Europe/London", "lat": "51.48", "lng": "0.0"}),
            # City without nation: still must resolve the tz before capturing.
            ({"city": "Tokyo"}, {"countryCode": "JP", "timezonestr": "Asia/Tokyo", "lat": "35.68", "lng": "139.69"}),
        ],
    )
    def test_from_current_time_resolves_tz_on_every_online_path(self, monkeypatch, kwargs, fetched):
        """The timezone must be resolved before capturing the instant on ALL
        online paths — not only when both city and nation are explicit — or the
        default / city-only chart is shifted by the host-city offset."""
        from datetime import datetime, timedelta, timezone
        from kerykeion import fetch_geonames
        from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

        monkeypatch.setattr(
            fetch_geonames.FetchGeonames, "get_serialized_data", lambda self: dict(fetched)
        )
        before = datetime.now(timezone.utc)
        s = AstrologicalSubjectFactory.from_current_time(
            "Now Default", online=True, suppress_geonames_warning=True, **kwargs
        )
        after = datetime.now(timezone.utc)
        got = datetime.fromisoformat(s.iso_formatted_utc_datetime)
        assert before - timedelta(seconds=5) <= got <= after + timedelta(seconds=5)
        assert s.tz_str == fetched["timezonestr"]

    def test_from_iso_utc_time_failed_fetch_raises_kerykeion_exception(self, monkeypatch):
        from kerykeion import fetch_geonames
        from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
        from kerykeion.schemas import KerykeionException

        monkeypatch.setattr(
            fetch_geonames.FetchGeonames, "get_serialized_data", lambda self: {}
        )
        with pytest.raises(KerykeionException, match="Missing data from geonames"):
            AstrologicalSubjectFactory.from_iso_utc_time(
                "Fail Test", "2020-06-15T12:00:00Z",
                city="Rome", nation="IT", tz_str="Europe/Rome", online=True,
                suppress_geonames_warning=True,
            )

    def test_explicit_coordinates_without_city_resolve_tz_from_coordinates(self, monkeypatch):
        """online=True + explicit lat/lng + no tz_str + no city: the timezone
        must be resolved from the coordinates (timezoneJSON endpoint), NOT from
        the default city "Greenwich" (which silently produced a chart in the
        wrong zone)."""
        from kerykeion import fetch_geonames
        from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

        captured = {}

        def fake_tz_lookup(self, lat, lng):
            captured["coords"] = (lat, lng)
            return {"timezonestr": "Europe/Rome"}

        def fail_city_lookup(self):
            raise AssertionError(
                "the city-based lookup must not run when lat/lng are explicit and city is missing"
            )

        monkeypatch.setattr(
            fetch_geonames.FetchGeonames, "get_timezone_for_coordinates", fake_tz_lookup
        )
        monkeypatch.setattr(
            fetch_geonames.FetchGeonames, "get_serialized_data", fail_city_lookup
        )

        s = AstrologicalSubjectFactory.from_birth_data(
            "Coords Only", 1990, 6, 15, 12, 0,
            lat=41.9028, lng=12.4964, online=True,
            suppress_geonames_warning=True,
        )
        assert captured["coords"] == (41.9028, 12.4964)
        assert s.tz_str == "Europe/Rome"
        assert s.lat == pytest.approx(41.9028)
        assert s.lng == pytest.approx(12.4964)

    def test_explicit_coordinates_without_city_missing_timezone_id_raises(self, monkeypatch):
        """A timezoneJSON response without a timezoneId must raise a clear
        KerykeionException, not fall back to a default timezone."""
        from kerykeion import fetch_geonames
        from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
        from kerykeion.schemas import KerykeionException

        monkeypatch.setattr(
            fetch_geonames.FetchGeonames,
            "get_timezone_for_coordinates",
            lambda self, lat, lng: {},
        )
        with pytest.raises(KerykeionException, match="timezoneId"):
            AstrologicalSubjectFactory.from_birth_data(
                "Coords Fail", 1990, 6, 15, 12, 0,
                lat=41.9028, lng=12.4964, online=True,
                suppress_geonames_warning=True,
            )

    def test_from_iso_utc_time_explicit_coordinates_win(self, monkeypatch):
        """Explicit lng/lat must never be overwritten by the city centroid in
        from_iso_utc_time (and the GeoNames lookup is skipped entirely)."""
        from kerykeion import fetch_geonames
        from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

        def fail_city_lookup(self):
            raise AssertionError("no GeoNames lookup should run when lng/lat are explicit")

        monkeypatch.setattr(
            fetch_geonames.FetchGeonames, "get_serialized_data", fail_city_lookup
        )
        s = AstrologicalSubjectFactory.from_iso_utc_time(
            "ISO Precise", "1990-06-15T12:00:00Z",
            city="Rome", nation="IT", tz_str="Europe/Rome", online=True,
            lat=45.999, lng=7.111,  # explicit, more precise than the centroid
            suppress_geonames_warning=True,
        )
        assert s.lat == pytest.approx(45.999)
        assert s.lng == pytest.approx(7.111)

    def test_from_iso_utc_time_city_centroid_fills_missing_coordinates(self, _mock_geonames):
        """Without explicit lng/lat, from_iso_utc_time still resolves them from
        the city centroid (legacy behavior preserved)."""
        from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

        s = AstrologicalSubjectFactory.from_iso_utc_time(
            "ISO City", "1990-06-15T12:00:00Z",
            city="Rome", nation="IT", tz_str="Europe/Rome", online=True,
            suppress_geonames_warning=True,
        )
        assert s.lat == pytest.approx(41.89193)
        assert s.lng == pytest.approx(12.51133)

    def test_from_iso_utc_time_defaults_remain_greenwich_offline(self):
        """With no location at all and online=False, the historical Greenwich
        defaults still apply."""
        from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

        s = AstrologicalSubjectFactory.from_iso_utc_time(
            "ISO Default", "1990-06-15T12:00:00Z", online=False,
        )
        assert s.lat == pytest.approx(51.5074)
        assert s.lng == pytest.approx(0.0)
        assert s.tz_str == "Etc/GMT"

    def test_malformed_geonames_coordinates_raise_kerykeion_exception(self, monkeypatch):
        """A GeoNames payload with non-numeric lat/lng must surface as
        KerykeionException, not a raw ValueError from float()."""
        from kerykeion import fetch_geonames
        from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
        from kerykeion.schemas import KerykeionException

        bad = {"countryCode": "IT", "timezonestr": "Europe/Rome", "lat": "not-a-number", "lng": "12.5"}
        monkeypatch.setattr(
            fetch_geonames.FetchGeonames, "get_serialized_data", lambda self: dict(bad)
        )
        with pytest.raises(KerykeionException, match="Invalid coordinates from geonames"):
            AstrologicalSubjectFactory.from_birth_data(
                "Bad Coords", 1990, 6, 15, 12, 0,
                city="Rome", nation="IT", online=True,
                suppress_geonames_warning=True,
            )

    def test_partial_date_defaults_use_target_timezone_instant(self):
        """Missing date/time components must be filled from the current instant
        rendered in the SUBJECT's resolved timezone, not from the host's naive
        wall clock re-interpreted in that timezone (which shifted the moment by
        the full host-target offset)."""
        from datetime import datetime, timedelta, timezone
        from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

        before = datetime.now(timezone.utc)
        s = AstrologicalSubjectFactory.from_birth_data(
            "Partial Now", lat=-36.85, lng=174.76, tz_str="Pacific/Auckland",
            online=False, suppress_geonames_warning=True,
        )
        after = datetime.now(timezone.utc)
        got = datetime.fromisoformat(s.iso_formatted_utc_datetime)
        # `seconds` has a plain 0 default (it is not filled from "now"), so the
        # captured instant may lag by up to a minute; anything larger means the
        # instant was captured in the wrong timezone (offsets are >= 1 hour).
        assert before - timedelta(seconds=65) <= got <= after + timedelta(seconds=5)


class TestYear1CEBoundaryRound7:
    """Round-7 regression: a year-1-CE local time east of UTC that converts to a
    UTC instant in year 0 must raise a clean KerykeionException, not a raw
    OverflowError (matching every adjacent input)."""

    def test_year1_ce_east_of_utc_raises_kerykeion_exception(self):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException):
            AstrologicalSubjectFactory.from_birth_data(
                "x", 1, 1, 1, 0, 30, lng=45.0, lat=41.9,
                tz_str="Etc/GMT-3", online=False, suppress_geonames_warning=True)


class TestInputValidationRound8:
    """Round-8 regressions: input validation surfaces KerykeionException (not raw
    ValueError/CoordinateError/OverflowError) and normalizes longitude."""

    def _base(self, **kw):
        from kerykeion import AstrologicalSubjectFactory
        base = dict(name="t", year=1990, month=6, day=15, hour=12, minute=0,
                    lat=51.5, lng=10.0, tz_str="Etc/GMT", online=False,
                    suppress_geonames_warning=True)
        base.update(kw)
        return AstrologicalSubjectFactory.from_birth_data(**base)

    def test_impossible_latitude_raises(self):
        from kerykeion.schemas import KerykeionException
        with pytest.raises(KerykeionException):
            self._base(lat=100.0)

    def test_valid_polar_latitude_preserved(self):
        # The real polar latitude is preserved on the model (no global clamp);
        # only the quadrant house cusps fall back to the ±66° limit internally.
        s = self._base(lat=78.0)
        assert s.lat == 78.0

    @pytest.mark.parametrize("kw", [{"month": 13}, {"day": 32}, {"hour": 25}, {"minute": 99}])
    def test_out_of_range_date_raises_kerykeion(self, kw):
        from kerykeion.schemas import KerykeionException
        with pytest.raises(KerykeionException):
            self._base(**kw)

    def test_longitude_normalized(self):
        s = self._base(lng=370.0)
        s10 = self._base(lng=10.0)
        assert s.lng == 10.0
        assert abs(s.ascendant.abs_pos - s10.ascendant.abs_pos) < 1e-9

    def test_year1_ce_iana_zone_raises_kerykeion(self):
        """Round-7 regression follow-up: real IANA zones (not just static
        Etc/GMT) at year 1 CE raise KerykeionException, not raw OverflowError."""
        from kerykeion.schemas import KerykeionException
        for tz in ("Asia/Tokyo", "America/New_York"):
            with pytest.raises(KerykeionException):
                self._base(year=1, month=1, day=1, hour=0, minute=30, lng=40.0, tz_str=tz)


class TestStandardOffsetFoldRound10:
    """Round-10 regression: a fall-back fold caused by a STANDARD-time change
    (UK 1971 BST->GMT, Portugal 1976) must round-trip correctly, not raise a
    spurious 'double summer time' error, and an invalid tz raises KerykeionException."""

    def test_uk_1971_bst_gmt_fold_builds(self):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.utilities import datetime_to_julian
        from datetime import datetime, timezone
        s = AstrologicalSubjectFactory.from_iso_utc_time(
            name="x", iso_utc_time="1971-10-31T01:30:00Z", tz_str="Europe/London",
            lng=-0.1, lat=51.5, online=False, suppress_geonames_warning=True)
        exp = datetime_to_julian(datetime(1971, 10, 31, 1, 30, 0, tzinfo=timezone.utc))
        assert abs(s.julian_day - exp) < 2 / 86400.0

    def test_invalid_timezone_raises_kerykeion(self):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.schemas import KerykeionException
        with pytest.raises(KerykeionException):
            AstrologicalSubjectFactory.from_birth_data(
                "x", 2000, 1, 1, 12, 0, lng=10.0, lat=45.0,
                tz_str="+05:00", online=False, suppress_geonames_warning=True)


class TestExplicitDerivedOppositeRound12:
    """Round-12 regression: a derived opposite point (South Node, Priapus)
    explicitly requested WITHOUT its primary must still be computed (the primary
    is auto-activated), not silently dropped."""

    def test_south_node_without_north_node(self):
        from kerykeion import AstrologicalSubjectFactory
        s = AstrologicalSubjectFactory.from_birth_data(
            "V", 1990, 6, 15, 12, 0, lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True,
            active_points=["Sun", "Moon", "True_South_Lunar_Node"])
        assert "True_South_Lunar_Node" in s.active_points
        assert s.true_south_lunar_node is not None
        # the auto-activated primary must NOT leak into active_points
        assert "True_North_Lunar_Node" not in s.active_points

    def test_priapus_without_lilith(self):
        from kerykeion import AstrologicalSubjectFactory
        s = AstrologicalSubjectFactory.from_birth_data(
            "P", 1990, 6, 15, 12, 0, lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True,
            active_points=["Sun", "Moon", "True_Priapus"])
        assert s.true_priapus is not None


class TestTzWrapAndNodeParityRound13:
    """Round-13: invalid tz raises KerykeionException across entry points;
    lunar nodes excluded in non-geocentric perspectives; day_of_week is English."""

    def test_from_iso_invalid_tz_raises_kerykeion(self):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.schemas import KerykeionException
        with pytest.raises(KerykeionException):
            AstrologicalSubjectFactory.from_iso_utc_time(
                "E", "2020-06-15T12:00:00Z", tz_str="Bad/Zone",
                online=False, lng=0.0, lat=51.0, suppress_geonames_warning=True)

    def test_nodes_excluded_in_heliocentric(self):
        from kerykeion import AstrologicalSubjectFactory
        h = AstrologicalSubjectFactory.from_birth_data(
            "H", 1940, 10, 9, 18, 30, lng=-2.99, lat=53.4, tz_str="Europe/London",
            online=False, suppress_geonames_warning=True, perspective_type="Heliocentric")
        assert h.true_north_lunar_node is None
        assert "True_North_Lunar_Node" not in h.active_points

    def test_day_of_week_is_english_literal(self):
        from kerykeion import AstrologicalSubjectFactory
        s = AstrologicalSubjectFactory.from_birth_data(
            "D", 1990, 6, 15, 12, 0, lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True)
        assert s.day_of_week in ("Monday", "Tuesday", "Wednesday", "Thursday",
                                 "Friday", "Saturday", "Sunday")


class TestSiderealDeclinationRound16:
    """Round-16: declination is a physical equatorial coordinate — it must be
    zodiac-independent (equatorial fetch strips FLG_SIDEREAL)."""

    def test_sidereal_declination_matches_tropical(self):
        kw = dict(lat=51.5, lng=-0.12, tz_str="Europe/London", online=False,
                  suppress_geonames_warning=True)
        trop = AstrologicalSubjectFactory.from_birth_data("T", 1990, 6, 15, 12, 0, **kw)
        sid = AstrologicalSubjectFactory.from_birth_data(
            "S", 1990, 6, 15, 12, 0, zodiac_type="Sidereal", sidereal_mode="LAHIRI", **kw)
        for body in ("sun", "moon", "mars", "jupiter"):
            assert abs(getattr(trop, body).declination - getattr(sid, body).declination) < 1e-6


class TestPolarLatitudePreserved:
    """Round-22: the polar-latitude clamp must be applied ONLY where a quadrant
    house system is undefined inside the polar circle — never globally. The real
    observer latitude must reach the persisted model, the topocentric observer,
    and every house system that is defined at all latitudes."""

    _KW = dict(
        year=1995, month=1, day=15, hour=2, minute=0,
        city="Longyearbyen", nation="NO", lng=15.6467,
        tz_str="Arctic/Longyearbyen", online=False, suppress_geonames_warning=True,
    )

    def _mk(self, **kw):
        base = dict(name="Polar", lat=78.2232)
        base.update(self._KW)
        base.update(kw)
        return AstrologicalSubjectFactory.from_birth_data(**base)

    def test_persisted_latitude_is_real_not_clamped(self):
        # Latitude-agnostic system (Whole Sign): nothing forces a clamp.
        s = self._mk(houses_system_identifier="W")
        assert s.lat == 78.2232

    def test_persisted_latitude_real_even_with_placidus(self):
        # Even when the quadrant houses fall back internally, the model keeps the
        # real latitude — only the house cusps use the clamped value.
        s = self._mk(houses_system_identifier="P")
        assert s.lat == 78.2232

    def test_topocentric_uses_real_latitude(self):
        # A topocentric polar subject must NOT be bit-identical to a 66°-clamped
        # one, and must match a direct backend call at the real latitude.
        from kerykeion.ephemeris_backend import ephe, ephemeris_session

        s = self._mk(perspective_type="Topocentric", houses_system_identifier="W")
        s66 = self._mk(perspective_type="Topocentric", houses_system_identifier="W", lat=66.0)
        assert abs(s.moon.abs_pos - s66.moon.abs_pos) * 60 > 1.0  # arcmin

        with ephemeris_session(perspective_type="Topocentric", topo=(15.6467, 78.2232, 0.0)) as iflag:
            direct_moon = ephe.calc_ut(s.julian_day, 1, iflag)[0][0]
        assert abs(direct_moon - s.moon.abs_pos) * 3600 < 1.0  # arcsec

    def test_latitude_agnostic_houses_use_real_latitude(self):
        # Whole Sign ASC at the real polar latitude must match an independent
        # backend call at that latitude — NOT the 66°-clamped one.
        from kerykeion.ephemeris_backend import ephe, ephemeris_session

        s = self._mk(houses_system_identifier="W")
        with ephemeris_session() as iflag:
            _, ascmc_real, _, _ = ephe.houses_ex2(s.julian_day, 78.2232, 15.6467, b"W", iflag)
            _, ascmc_66, _, _ = ephe.houses_ex2(s.julian_day, 66.0, 15.6467, b"W", iflag)
        assert abs(s.ascendant.abs_pos - ascmc_real[0]) < 1e-6
        assert abs(ascmc_real[0] - ascmc_66[0]) > 1.0  # real vs clamped differ

    def test_placidus_falls_back_with_warning(self, caplog):
        # A quadrant system undefined inside the polar circle falls back to the
        # ±66° clamp and emits a WARNING naming the system.
        import logging

        with caplog.at_level(logging.WARNING, logger="kerykeion.ephemeris_backend"):
            s = self._mk(houses_system_identifier="P")
        assert s.lat == 78.2232
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING and "'P'" in r.getMessage()]
        assert warnings, "expected a WARNING about the Placidus polar fallback"

    def test_whole_sign_does_not_warn(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING, logger="kerykeion.ephemeris_backend"):
            self._mk(houses_system_identifier="W")
        polar_warnings = [
            r for r in caplog.records
            if r.levelno == logging.WARNING and "undefined inside the polar circle" in r.getMessage()
        ]
        assert not polar_warnings


class TestPolarFallbackErrorHandling:
    """R23 regression for houses_ex2_with_polar_fallback: (F3) a houses failure at
    a NON-polar latitude must be re-raised unchanged (no spurious polar warning /
    retry) and a retry failure must surface the ORIGINAL real-latitude error;
    (F2) the warning must name the clamped outputs accurately (cusps AND angles,
    since the ascmc angles also come from the clamped retry)."""

    def _polar_error_type(self):
        from kerykeion import ephemeris_backend as eb

        if not eb.POLAR_HOUSES_ERROR_TYPES:
            pytest.skip("backend exposes no polar houses error type")
        return eb.POLAR_HOUSES_ERROR_TYPES[0]

    def test_normal_latitude_error_reraised_without_polar_warning(self, monkeypatch, caplog):
        import logging
        from kerykeion import ephemeris_backend as eb
        from kerykeion.ephemeris_backend import houses_ex2_with_polar_fallback

        err_type = self._polar_error_type()

        def always_fail(jd, lat, lon, hsys, flags):
            raise err_type(f"forced at lat={lat}")

        monkeypatch.setattr(eb.ephe, "houses_ex2", always_fail)
        with caplog.at_level(logging.WARNING, logger="kerykeion.ephemeris_backend"):
            # 41.9 is NOT inside the polar circle → not a polar-undefined error.
            with pytest.raises(err_type, match="forced at lat=41.9"):
                houses_ex2_with_polar_fallback(2451545.0, 41.9, 12.5, b"P", 0)
        assert not [
            r for r in caplog.records if "undefined inside the polar circle" in r.getMessage()
        ]

    def test_polar_latitude_retry_failure_surfaces_original(self, monkeypatch, caplog):
        import logging
        from kerykeion import ephemeris_backend as eb
        from kerykeion.ephemeris_backend import houses_ex2_with_polar_fallback

        err_type = self._polar_error_type()

        def always_fail(jd, lat, lon, hsys, flags):
            raise err_type(f"forced at lat={lat}")

        monkeypatch.setattr(eb.ephe, "houses_ex2", always_fail)
        with caplog.at_level(logging.WARNING, logger="kerykeion.ephemeris_backend"):
            # 78.0 IS inside the polar circle → warn, clamp+retry; the retry also
            # fails, so the ORIGINAL (lat=78) error surfaces with the clamped
            # retry (lat=66) chained as its cause.
            with pytest.raises(err_type, match="forced at lat=78.0") as excinfo:
                houses_ex2_with_polar_fallback(2451545.0, 78.0, 12.5, b"P", 0)
        assert "forced at lat=66" in str(excinfo.value.__cause__)
        assert any(
            "undefined inside the polar circle" in r.getMessage() for r in caplog.records
        )

    def test_warning_names_cusps_and_angles(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING, logger="kerykeion.ephemeris_backend"):
            AstrologicalSubjectFactory.from_birth_data(
                "Polar Wording", 1995, 1, 15, 2, 0,
                lat=78.2232, lng=15.6467, city="Longyearbyen", nation="NO",
                tz_str="Arctic/Longyearbyen", online=False,
                suppress_geonames_warning=True, houses_system_identifier="P",
            )
        polar = [
            r.getMessage() for r in caplog.records
            if "undefined inside the polar circle" in r.getMessage()
        ]
        assert polar
        assert any("house cusps and angles" in m for m in polar)
        assert all("house cusps only" not in m for m in polar)


class TestNonIntDateComponents:
    """R23 regression: from_birth_data on the CE path (year >= 1) must normalize a
    non-int date/time component (str/float, e.g. month='06' from JSON/form data)
    to KerykeionException, not leak a raw TypeError. The `year < 1` comparison is
    guarded too, since a str year raised before ever reaching the datetime()
    wrap."""

    _KW = dict(
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False, suppress_geonames_warning=True,
    )

    @pytest.mark.parametrize(
        "component_override",
        [
            {"month": "06"},   # str component from JSON/form data
            {"day": "15"},
            {"hour": 12.0},    # float component -> TypeError from datetime()
            {"year": "1990"},  # str year -> TypeError at the `year < 1` comparison
        ],
        ids=lambda kw: next(iter(kw.items()))[0] + "=" + repr(next(iter(kw.items()))[1]),
    )
    def test_non_int_component_raises_kerykeion_exception(self, component_override):
        from kerykeion.schemas import KerykeionException

        base = dict(name="CE Invalid", year=1990, month=6, day=15, hour=12, minute=0)
        base.update(self._KW)
        base.update(component_override)
        with pytest.raises(KerykeionException, match="Invalid birth date/time component"):
            AstrologicalSubjectFactory.from_birth_data(**base)

    def test_valid_int_components_unchanged(self):
        s = AstrologicalSubjectFactory.from_birth_data(
            name="CE Valid", year=1990, month=6, day=15, hour=12, minute=0, **self._KW
        )
        assert s.year == 1990 and s.month == 6 and s.sun is not None


class TestAncientJulianDayValidation:
    """The pre-1 CE (Julian-calendar) path must reject an out-of-range
    day-of-month symmetrically with the CE datetime() path. ``ephe.julday(...,
    JUL_CAL)`` would otherwise silently roll e.g. Feb-30 into the next month and
    compute a wrong Julian Day. Validation raises BEFORE any ephemeris call, so
    these tests run on any tier without the extended kernel.

    (Kept in this module, not test_bce_dates.py, because the tier gate skips any
    node whose id contains "bce" unless the extended kernel is loaded — and the
    validation this exercises is kernel-independent. The class/method names avoid
    that substring on purpose.)"""

    _KW = dict(
        lng=0.0, lat=0.0, tz_str="UTC", city="X", nation="XX",
        online=False, suppress_geonames_warning=True,
    )

    @pytest.mark.parametrize(
        "year, month, day",
        [
            (-99, 2, 30),   # Feb never has 30 days
            (-99, 4, 31),   # April has 30
            (-1, 2, 29),    # 2 BCE is NOT a proleptic-Julian leap year (-1 % 4 != 0)
            (-99, 13, 1),   # month out of range — must raise, NOT IndexError
        ],
        ids=lambda v: str(v),
    )
    def test_invalid_julian_day_raises_validation_error(self, year, month, day):
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException, match="Invalid birth date/time component"):
            AstrologicalSubjectFactory.from_birth_data(
                name="Ancient Invalid", year=year, month=month, day=day,
                hour=12, minute=0, **self._KW
            )

    def test_valid_leap_feb29_passes_validation(self):
        """1 BCE (year 0) IS a proleptic-Julian leap year (0 % 4 == 0), so Feb-29
        is a valid day and must get PAST validation. Without the extended kernel
        the subsequent ephemeris call fails with a range error — that is fine and
        still proves the validation accepted the day (the message differs)."""
        from kerykeion.schemas import KerykeionException

        try:
            AstrologicalSubjectFactory.from_birth_data(
                name="Ancient Valid Leap", year=0, month=2, day=29,
                hour=12, minute=0, **self._KW
            )
        except KerykeionException as exc:
            assert "Invalid birth date/time component" not in str(exc)


class TestActivePointsValidation:
    """Unknown names must raise (they used to silently vanish from the chart);
    an explicit empty list must raise (it used to invert into a FULL chart)."""


    COMMON = dict(
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        online=False, suppress_geonames_warning=True,
    )

    def test_typoed_point_name_raises(self):
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException, match="Sunn"):
            AstrologicalSubjectFactory.from_birth_data(
                "T", 1990, 6, 15, 12, 0, active_points=["Sunn", "Moon"], **self.COMMON
            )

    def test_empty_active_points_raises(self):
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException, match="empty"):
            AstrologicalSubjectFactory.from_birth_data(
                "T", 1990, 6, 15, 12, 0, active_points=[], **self.COMMON
            )

    def test_star_names_still_redirected(self):
        subject = AstrologicalSubjectFactory.from_birth_data(
            "T", 1990, 6, 15, 12, 0,
            active_points=["Sun", "Moon", "Regulus"], **self.COMMON
        )
        assert [star.name for star in (subject.fixed_stars or [])] == ["Regulus"]
        assert "Regulus" not in subject.active_points
