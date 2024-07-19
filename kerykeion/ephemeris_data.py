from kerykeion import AstrologicalSubject
from kerykeion.astrological_subject import DEFAULT_HOUSES_SYSTEM_IDENTIFIER, DEFAULT_PERSPECTIVE_TYPE, DEFAULT_ZODIAC_TYPE
from kerykeion.kr_types import EphemerisDictModel
from kerykeion.kr_types import SiderealMode, HousesSystemIdentifier, PerspectiveType, ZodiacType
from datetime import datetime, timedelta
from typing import Literal
import logging


class EphemerisDataFactory:
    """
    This class is used to generate ephemeris data for a given date range.

    Parameters:
    - start_datetime: datetime object representing the start date and time.
    - end_datetime: datetime object representing the end date and time.
    - step_type: string representing the step type. It can be "days", "hours", or "minutes". Default is "days".
    - step: integer representing the step value. Default is 1.
    - lat: float representing the latitude. Default is 51.4769 (Greenwich).
    - lng: float representing the longitude. Default is 0.0005 (Greenwich).
    - tz_str: string representing the timezone. Default is "Etc/UTC".
    - is_dst: boolean representing if daylight saving time is active. Default is False.
    - disable_chiron: boolean representing if Chiron should be disabled. Default is False.
    - zodiac_type: ZodiacType object representing the zodiac type. Default is DEFAULT_ZODIAC_TYPE.
    - sidereal_mode: SiderealMode object representing the sidereal mode. Default is None.
    - houses_system_identifier: HousesSystemIdentifier object representing the houses system identifier. Default is DEFAULT_HOUSES_SYSTEM_IDENTIFIER.
    - perspective_type: PerspectiveType object representing the perspective type. Default is DEFAULT_PERSPECTIVE_TYPE.
    - max_days: integer representing the maximum number of days.
        Set it to None to disable the check. Default is 730.
    - max_hours: integer representing the maximum number of hours.
        Set it to None to disable the check. Default is 8760.
    - max_minutes: integer representing the maximum number of minutes.
        Set it to None to disable the check. Default is 525600.

    Raises:
    - ValueError: if the step type is invalid.
    - ValueError: if the number of days, hours, or minutes is greater than the maximum allowed.
    """

    def __init__(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        step_type: Literal["days", "hours", "minutes"] = "days",
        step: int = 1,
        lat: float = 51.4769,
        lng: float = 0.0005,
        tz_str: str = "Etc/UTC",
        is_dst: bool = False,
        disable_chiron: bool = False,
        zodiac_type: ZodiacType = DEFAULT_ZODIAC_TYPE,
        sidereal_mode: SiderealMode | None = None,
        houses_system_identifier: HousesSystemIdentifier = DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
        perspective_type: PerspectiveType = DEFAULT_PERSPECTIVE_TYPE,
        max_days: int = 730,
        max_hours: int = 8760,
        max_minutes: int = 525600,
    ):
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.step_type = step_type
        self.step = step
        self.lat = lat
        self.lng = lng
        self.tz_str = tz_str
        self.is_dst = is_dst
        self.disable_chiron = disable_chiron
        self.zodiac_type = zodiac_type
        self.sidereal_mode = sidereal_mode
        self.houses_system_identifier = houses_system_identifier
        self.perspective_type = perspective_type
        self.max_days = max_days
        self.max_hours = max_hours
        self.max_minutes = max_minutes

        self.dates_list = []
        if self.step_type == "days":
            self.dates_list = [self.start_datetime + timedelta(days=i) for i in range((self.end_datetime - self.start_datetime).days)]
            if max_days and (len(self.dates_list) > max_days):
                raise ValueError(f"Too many days: {len(self.dates_list)} > {self.max_days}. To prevent this error, set max_days to a higher value or reduce the date range.")

        elif self.step_type == "hours":
            self.dates_list = [self.start_datetime + timedelta(hours=i) for i in range((self.end_datetime - self.start_datetime).days * 24)]
            if max_hours and (len(self.dates_list) > max_hours):
                raise ValueError(f"Too many hours: {len(self.dates_list)} > {self.max_hours}. To prevent this error, set max_hours to a higher value or reduce the date range.")

        elif self.step_type == "minutes":
            self.dates_list = [self.start_datetime + timedelta(minutes=i) for i in range((self.end_datetime - self.start_datetime).days * 24 * 60)]
            if max_minutes and (len(self.dates_list) > max_minutes):
                raise ValueError(f"Too many minutes: {len(self.dates_list)} > {self.max_minutes}. To prevent this error, set max_minutes to a higher value or reduce the date range.")

        else:
            raise ValueError(f"Invalid step type: {self.step_type}")

        if not self.dates_list:
            raise ValueError("No dates found. Check the date range and step values.")

        if len(self.dates_list) > 1000:
            logging.warning(f"Large number of dates: {len(self.dates_list)}. The calculation may take a while.")

    def get_ephemeris_data(self) -> list:
        """
        Generate ephemeris data for the specified date range.
        The data is structured as a list of dictionaries, where each dictionary contains the date, planets, and houses data.
        Eg. [{"date": "2020-01-01T00:00:00", "planets": [{...}, {...}, ...], "houses": [{...}, {...}, ...]}, ...]

        Args:
        - as_model: boolean representing if the ephemeris data should be returned as model instances. Default is False.
        - as_dict: boolean representing if the ephemeris data should be returned as dictionaries. Default is False.

        Returns:
        - list of dictionaries representing the ephemeris data.
        """
        ephemeris_data_list = []
        for date in self.dates_list:
            subject = AstrologicalSubject(
                year=date.year,
                month=date.month,
                day=date.day,
                hour=date.hour,
                minute=date.minute,
                lng=self.lng,
                lat=self.lat,
                tz_str=self.tz_str,
                city="Placeholder",
                nation="Placeholder",
                online=False,
                disable_chiron=self.disable_chiron,
                zodiac_type=self.zodiac_type,
                sidereal_mode=self.sidereal_mode,
                houses_system_identifier=self.houses_system_identifier,
                perspective_type=self.perspective_type,
                is_dst=self.is_dst,
            )

            ephemeris_data_list.append({"date": date.isoformat(), "planets": subject.planets_list, "houses": subject.houses_list})

        return ephemeris_data_list

    def get_ephemeris_data_as_model(self) -> list[EphemerisDictModel]:
        """
        Generate ephemeris data as model instances for the specified date range.
        The data is structured as a list of EphemerisDictModel instances.

        Returns:
        - list of EphemerisDictModel instances representing the ephemeris data.
        """
        return [EphemerisDictModel(**data) for data in self.get_ephemeris_data()]


if "__main__" == __name__:
    start_date = datetime.fromisoformat("2020-01-01")
    end_date = datetime.fromisoformat("2020-01-03")

    factory = EphemerisDataFactory(
        start_datetime=start_date,
        end_datetime=end_date,
        step_type="minutes",
        step=1,
        lat=37.9838,
        lng=23.7275,
        tz_str="Europe/Athens",
        is_dst=False,
        max_hours=None,
        max_minutes=None,
        max_days=None,
    )

    ephemeris_data = factory.get_ephemeris_data_as_model()
    print(ephemeris_data[0])
    print(len(ephemeris_data))

    for ephe in ephemeris_data:
        print(ephe.planets[0]["abs_pos"])
