from typing import Optional, Union, List
from datetime import datetime, timedelta
from kerykeion.kr_types.kr_models import AstrologicalSubjectModel
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.aspects import SynastryAspects
from kerykeion.ephemeris_data import EphemerisDataFactory
from kerykeion.kr_types.kr_literals import AstrologicalPoint
from kerykeion.kr_types.kr_models import ActiveAspect, TransitMomentModel, TransitsTimeRangeModel
from kerykeion.kr_types.settings_models import KerykeionSettingsModel
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS, DEFAULT_ACTIVE_ASPECTS
from pathlib import Path


class TransitsTimeRangeFactory:
    """
    Factory class for generating astrological transit data over a period of time.

    This class compares the positions of celestial bodies at different points in time
    with the natal chart of an astrological subject to identify significant aspects
    and produces structured models containing the transit data.

    Attributes:
        natal_chart: The natal chart of the subject for whom transits are calculated.
        ephemeris_data_points: List of ephemeris data points representing planetary positions at different times.
        active_points: List of celestial points to consider when calculating aspects.
        active_aspects: List of aspect types to consider when analyzing planetary relationships.
        settings_file: Path to the settings file or a KerykeionSettingsModel object.
    """

    def __init__(
        self,
        natal_chart: AstrologicalSubjectModel,
        ephemeris_data_points: List[AstrologicalSubjectModel],
        active_points: List[AstrologicalPoint] = DEFAULT_ACTIVE_POINTS,
        active_aspects: List[ActiveAspect] = DEFAULT_ACTIVE_ASPECTS,
        settings_file: Union[Path, KerykeionSettingsModel, dict, None] = None,
    ):
        """
        Initialize the TransitMomentsFactory with the necessary data.

        Args:
            natal_chart: The natal chart of the subject for whom transits are calculated.
            ephemeris_data_points: List of ephemeris data points representing planetary positions at different times.
            active_points: List of celestial points to consider when calculating aspects.
            active_aspects: List of aspect types to consider when analyzing planetary relationships.
            settings_file: Path to the settings file or a KerykeionSettingsModel object.
        """
        self.natal_chart = natal_chart
        self.ephemeris_data_points = ephemeris_data_points
        self.active_points = active_points
        self.active_aspects = active_aspects
        self.settings_file = settings_file

    def get_transit_moments(self) -> TransitsTimeRangeModel:
        """
        Generate a model of transit moments for the given subject across all ephemeris data points.

        This method compares the positions of celestial bodies at different points in time
        with the natal chart of the subject to identify significant aspects and
        compiles them into a structured model for analysis.

        Returns:
            TransitMomentsListModel: A model containing all transit data, including aspects,
                                    dates, and subject information.
        """
        transit_moments = []

        for ephemeris_point in self.ephemeris_data_points:
            # Calculate aspects between transit positions and natal chart
            aspects = SynastryAspects(
                ephemeris_point,
                self.natal_chart,
                active_points=self.active_points,
                active_aspects=self.active_aspects,
                new_settings_file=self.settings_file,
            ).relevant_aspects

            # Create a transit moment for this point in time
            transit_moments.append(
                TransitMomentModel(
                    date=ephemeris_point.iso_formatted_utc_datetime,
                    aspects=aspects,
                )
            )

        # Create and return the complete transits model
        return TransitsTimeRangeModel(
            dates=[point.iso_formatted_utc_datetime for point in self.ephemeris_data_points],
            subject=self.natal_chart.model(),
            transits=transit_moments
        )


if __name__ == "__main__":
    # Create a natal chart for the subject
    person = AstrologicalSubjectFactory.from_birth_data(
        "Johnny Depp", 1963, 6, 9, 20, 15, "Owensboro", "US"
    )

    # Define the time period for transit calculation
    start_date = datetime.now()
    end_date = datetime.now() + timedelta(days=30)

    # Create ephemeris data for the specified time period
    ephemeris_factory = EphemerisDataFactory(
        start_datetime=start_date,
        end_datetime=end_date,
        step_type="days",
        step=1,
        lat=person.lat,
        lng=person.lng,
        tz_str=person.tz_str,
    )

    ephemeris_data_points = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()

    # Calculate transits for the subject
    transit_factory = TransitsTimeRangeFactory(
        natal_chart=person,
        ephemeris_data_points=ephemeris_data_points,
    )

    transit_results = transit_factory.get_transit_moments()

    # Print example data
    print(transit_results.model_dump()["dates"][2])
    print(transit_results.model_dump()["transits"][2]['date'])
    print(transit_results.model_dump()["transits"][2]['aspects'][0])
