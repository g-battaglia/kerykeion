from kerykeion import AstrologicalSubjectFactory
from kerykeion.kr_types.kr_models import AstrologicalSubjectModel
from kerykeion.utilities import get_houses_list, get_available_astrological_points_list
from kerykeion.astrological_subject_factory import DEFAULT_HOUSES_SYSTEM_IDENTIFIER, DEFAULT_PERSPECTIVE_TYPE, DEFAULT_ZODIAC_TYPE
from kerykeion.kr_types import EphemerisDictModel
from kerykeion.kr_types import SiderealMode, HousesSystemIdentifier, PerspectiveType, ZodiacType
from datetime import datetime, timedelta
from typing import Literal, Union, List
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
        zodiac_type: ZodiacType = DEFAULT_ZODIAC_TYPE,
        sidereal_mode: Union[SiderealMode, None] = None,
        houses_system_identifier: HousesSystemIdentifier = DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
        perspective_type: PerspectiveType = DEFAULT_PERSPECTIVE_TYPE,
        max_days: Union[int, None] = 730,
        max_hours: Union[int, None] = 8760,
        max_minutes: Union[int, None] = 525600,
    ):
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.step_type = step_type
        self.step = step
        self.lat = lat
        self.lng = lng
        self.tz_str = tz_str
        self.is_dst = is_dst
        self.zodiac_type = zodiac_type
        self.sidereal_mode = sidereal_mode
        self.houses_system_identifier = houses_system_identifier
        self.perspective_type = perspective_type
        self.max_days = max_days
        self.max_hours = max_hours
        self.max_minutes = max_minutes

        self.dates_list = []
        if self.step_type == "days":
            self.dates_list = [self.start_datetime + timedelta(days=i * self.step) for i in range((self.end_datetime - self.start_datetime).days // self.step + 1)]
            if max_days and (len(self.dates_list) > max_days):
                raise ValueError(f"Too many days: {len(self.dates_list)} > {self.max_days}. To prevent this error, set max_days to a higher value or reduce the date range.")

        elif self.step_type == "hours":
            hours_diff = (self.end_datetime - self.start_datetime).total_seconds() / 3600
            self.dates_list = [self.start_datetime + timedelta(hours=i * self.step) for i in range(int(hours_diff) // self.step + 1)]
            if max_hours and (len(self.dates_list) > max_hours):
                raise ValueError(f"Too many hours: {len(self.dates_list)} > {self.max_hours}. To prevent this error, set max_hours to a higher value or reduce the date range.")

        elif self.step_type == "minutes":
            minutes_diff = (self.end_datetime - self.start_datetime).total_seconds() / 60
            self.dates_list = [self.start_datetime + timedelta(minutes=i * self.step) for i in range(int(minutes_diff) // self.step + 1)]
            if max_minutes and (len(self.dates_list) > max_minutes):
                raise ValueError(f"Too many minutes: {len(self.dates_list)} > {self.max_minutes}. To prevent this error, set max_minutes to a higher value or reduce the date range.")

        else:
            raise ValueError(f"Invalid step type: {self.step_type}")

        if not self.dates_list:
            raise ValueError("No dates found. Check the date range and step values.")

        if len(self.dates_list) > 1000:
            logging.warning(f"Large number of dates: {len(self.dates_list)}. The calculation may take a while.")

    def get_ephemeris_data(self, as_model: bool = False) -> list:
        """
        Generate ephemeris data for the specified date range.
        The data is structured as a list of dictionaries, where each dictionary contains the date, planets, and houses data.
        Example:
        [
            {
                "date": "2020-01-01T00:00:00",
                "planets": [{...}, {...}, ...],
                "houses": [{...}, {...}, ...]
            },
            ...
        ]

        Args:
        - as_model (bool): If True, the ephemeris data will be returned as model instances. Default is False.

        Returns:
        - list: A list of dictionaries representing the ephemeris data. If as_model is True, a list of EphemerisDictModel instances is returned.
        """
        ephemeris_data_list = []
        for date in self.dates_list:
            subject = AstrologicalSubjectFactory.from_birth_data(
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
                zodiac_type=self.zodiac_type,
                sidereal_mode=self.sidereal_mode,
                houses_system_identifier=self.houses_system_identifier,
                perspective_type=self.perspective_type,
                is_dst=self.is_dst,
            )

            houses_list = get_houses_list(subject)
            available_planets = get_available_astrological_points_list(subject)

            ephemeris_data_list.append({"date": date.isoformat(), "planets": available_planets, "houses": houses_list})

        if as_model:
            return [EphemerisDictModel(**data) for data in ephemeris_data_list]

        return ephemeris_data_list

    def get_ephemeris_data_as_astrological_subjects(self, as_model: bool = False) -> List[AstrologicalSubjectModel]:
        """
        Generate ephemeris data for the specified date range as AstrologicalSubject instances.

        This method creates a complete AstrologicalSubject object for each date in the date range,
        allowing direct access to all properties and methods of the AstrologicalSubject class.

        Args:
        - as_model (bool): If True, the AstrologicalSubject instances will be returned as model instances. Default is False.

        Returns:
        - List[AstrologicalSubject]: A list of AstrologicalSubject instances, one for each date in the date range.

        Example usage:
            subjects = factory.get_ephemeris_data_as_astrological_subjects()
            # Access methods and properties of the first subject
            sun_position = subjects[0].get_sun()
            all_points = subjects[0].get_all_points()
            chart_drawing = subjects[0].draw_chart()
        """
        subjects_list = []
        for date in self.dates_list:
            subject = AstrologicalSubjectFactory.from_birth_data(
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
                zodiac_type=self.zodiac_type,
                sidereal_mode=self.sidereal_mode,
                houses_system_identifier=self.houses_system_identifier,
                perspective_type=self.perspective_type,
                is_dst=self.is_dst,
            )

            if as_model:
                subjects_list.append(subject.model())
            else:
                subjects_list.append(subject)

        return subjects_list


if "__main__" == __name__:
    start_date = datetime.fromisoformat("2020-01-01")
    end_date = datetime.fromisoformat("2020-01-03")

    factory = EphemerisDataFactory(
        start_datetime=start_date,
        end_datetime=end_date,
        step_type="minutes",
        step=60,  # One hour intervals to make the example more manageable
        lat=37.9838,
        lng=23.7275,
        tz_str="Europe/Athens",
        is_dst=False,
        max_hours=None,
        max_minutes=None,
        max_days=None,
    )

    # Test original method
    ephemeris_data = factory.get_ephemeris_data(as_model=True)
    print(f"Number of ephemeris data points: {len(ephemeris_data)}")
    print(f"First data point date: {ephemeris_data[0].date}")

    # Test new method
    subjects = factory.get_ephemeris_data_as_astrological_subjects()
    print(f"Number of astrological subjects: {len(subjects)}")
    print(f"First subject sun position: {subjects[0].sun}")

    # Example of accessing more data from the first subject
    first_subject = subjects[0]
    print(f"Sun sign: {first_subject.sun['sign']}")

    # Compare sun positions from both methods
    for i in range(min(3, len(subjects))):
        print(f"Date: {ephemeris_data[i].date}")
        print(f"Sun position from dict: {ephemeris_data[i].planets[0]['abs_pos']}")
        print("---")
