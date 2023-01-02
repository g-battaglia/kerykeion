from kerykeion import KrInstance
from logging import getLogger

logger = getLogger(__name__)


class TestKrInstance:
    def setup_class(self):
        # Johnny Depp
        self.subject = KrInstance("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US")

    def test_basic_input_data(self):
        assert self.subject.name == "Johnny Depp"
        assert self.subject.year == 1963
        assert self.subject.month == 6
        assert self.subject.day == 9
        assert self.subject.hour == 0
        assert self.subject.minute == 0
        assert self.subject.city == "Owensboro"
        assert self.subject.nation == "US"

    def test_internal_data(self):
        assert round(self.subject.lat, 3) == round(37.774, 3)
        assert round(self.subject.lng, 3) == round(-87.113, 3)
        assert self.subject.tz_str == "America/Chicago"
        assert self.subject.zodiac_type == "Tropic"
        assert round(self.subject.julian_day, 3) == round(2438189.708, 3)

    def test_sun(self):
        assert self.subject.sun.name == "Sun"
        assert self.subject.sun.quality == "Mutable"
        assert self.subject.sun.element == "Air"
        assert self.subject.sun.sign == "Gem"
        assert self.subject.sun.sign_num == 2
        assert round(self.subject.sun.position, 3) == round(17.66, 3)
        assert round(self.subject.sun.abs_pos, 3) == round(77.66, 3)
        assert self.subject.sun.emoji == "♊️"
        assert self.subject.sun.house == "Fourth House"
        assert self.subject.sun.retrograde == False
        assert self.subject.sun.point_type == "Planet"

    def test_moon(self):
        assert self.subject.moon.name == "Moon"
        assert self.subject.moon.quality == "Cardinal"
        assert self.subject.moon.element == "Earth"
        assert self.subject.moon.sign == "Cap"
        assert self.subject.moon.sign_num == 9
        assert round(self.subject.moon.position, 3) == round(8.735, 3)
        assert round(self.subject.moon.abs_pos, 3) == round(278.735, 3)
        assert self.subject.moon.emoji == "♑️"
        assert self.subject.moon.house == "Eleventh House"
        assert self.subject.moon.retrograde == False
        assert self.subject.moon.point_type == "Planet"

    def test_mercury(self):
        assert self.subject.mercury.name == "Mercury"
        assert self.subject.mercury.quality == "Fixed"
        assert self.subject.mercury.element == "Earth"
        assert self.subject.mercury.sign == "Tau"
        assert self.subject.mercury.sign_num == 1
        assert round(self.subject.mercury.position, 3) == round(25.002, 3)
        assert round(self.subject.mercury.abs_pos, 3) == round(55.002, 3)
        assert self.subject.mercury.emoji == "♉️"
        assert self.subject.mercury.house == "Third House"
        assert self.subject.mercury.retrograde == False
        assert self.subject.mercury.point_type == "Planet"

    def test_venus(self):
        assert self.subject.venus.name == "Venus"
        assert self.subject.venus.quality == "Fixed"
        assert self.subject.venus.element == "Earth"
        assert self.subject.venus.sign == "Tau"
        assert self.subject.venus.sign_num == 1
        assert round(self.subject.venus.position, 3) == round(25.604, 3)
        assert round(self.subject.venus.abs_pos, 3) == round(55.604, 3)
        assert self.subject.venus.emoji == "♉️"
        assert self.subject.venus.house == "Third House"
        assert self.subject.venus.retrograde == False
        assert self.subject.venus.point_type == "Planet"