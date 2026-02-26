"""
Transits Time Range Factory Module

This module provides the TransitsTimeRangeFactory class for calculating astrological
transits over specified time periods. It compares ephemeris data points (planetary
positions at different times) with a natal chart to identify when celestial bodies
form specific angular relationships (aspects).

Key Features:
    - Time-series transit calculations
    - Configurable celestial points and aspect types
    - Structured output models for data analysis
    - Integration with ephemeris data generation
    - Batch processing of multiple time points

The module generates comprehensive transit data by analyzing the angular relationships
between transiting celestial bodies and natal chart positions, creating timestamped
records of when specific geometric configurations occur.

Classes:
    TransitsTimeRangeFactory: Main factory class for generating transit data

Dependencies:
    - kerykeion.AstrologicalSubjectFactory: For creating astrological subjects
    - kerykeion.aspects.AspectsFactory: For calculating angular relationships
    - kerykeion.ephemeris_data_factory: For generating time-series planetary positions
    - kerykeion.schemas: For type definitions and model structures
    - datetime: For date/time handling

Example:
    Basic usage for calculating 30-day transits:

    >>> from datetime import datetime, timedelta
    >>> from kerykeion import AstrologicalSubjectFactory
    >>> from kerykeion.ephemeris_data_factory import EphemerisDataFactory
    >>> from kerykeion.transits_time_range_factory import TransitsTimeRangeFactory
    >>>
    >>> # Create natal chart
    >>> person = AstrologicalSubjectFactory.from_birth_data(
    ...     "Subject", 1990, 1, 1, 12, 0, "New York", "US"
    ... )
    >>>
    >>> # Generate ephemeris data
    >>> start = datetime.now()
    >>> end = start + timedelta(days=30)
    >>> ephemeris_factory = EphemerisDataFactory(start, end)
    >>> ephemeris_data = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()
    >>>
    >>> # Calculate transits
    >>> transit_factory = TransitsTimeRangeFactory(person, ephemeris_data)
    >>> results = transit_factory.get_transit_moments()

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

from typing import Union, List, Optional
from datetime import datetime, timedelta
from kerykeion.schemas.kr_models import AstrologicalSubjectModel
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.aspects import AspectsFactory
from kerykeion.ephemeris_data_factory import EphemerisDataFactory
from kerykeion.schemas.kr_literals import AstrologicalPoint
from kerykeion.schemas.kr_models import ActiveAspect, TransitMomentModel, TransitsTimeRangeModel
from kerykeion.schemas.settings_models import KerykeionSettingsModel
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS, DEFAULT_ACTIVE_ASPECTS
from pathlib import Path


class TransitsTimeRangeFactory:
    """
    Factory class for calculating astrological transits over time periods.

    This class analyzes the angular relationships (aspects) between transiting
    celestial bodies and natal chart positions across multiple time points,
    generating structured transit data for astrological analysis.

    The factory compares ephemeris data points (representing planetary positions
    at different moments) with a natal chart to identify when specific geometric
    configurations occur between transiting and natal celestial bodies.

    Args:
        natal_chart (AstrologicalSubjectModel): The natal chart used as the reference
            point for transit calculations. All transiting positions are compared
            against this chart's planetary positions.
        ephemeris_data_points (List[AstrologicalSubjectModel]): A list of astrological
            subject models representing different moments in time, typically generated
            by EphemerisDataFactory. Each point contains planetary positions for
            a specific date/time.
        active_points (List[AstrologicalPoint], optional): List of celestial bodies
            to include in aspect calculations (e.g., Sun, Moon, planets, asteroids).
            Defaults to DEFAULT_ACTIVE_POINTS.
        active_aspects (List[ActiveAspect], optional): List of aspect types to
            calculate (e.g., conjunction, opposition, trine, square, sextile).
            Defaults to DEFAULT_ACTIVE_ASPECTS.
        settings_file (Union[Path, KerykeionSettingsModel, dict, None], optional):
            Configuration settings for calculations. Can be a file path, settings
            model, dictionary, or None for defaults. Defaults to None.
        axis_orb_limit (float | None, optional): Optional orb threshold applied to chart axes
            during single-chart aspect calculations. Dual-chart calculations ignore this value.

    Attributes:
        natal_chart: The reference natal chart for transit calculations.
        ephemeris_data_points: Time-series planetary position data.
        active_points: Celestial bodies included in calculations.
        active_aspects: Aspect types considered for analysis.
        settings_file: Configuration settings for the calculations.
        axis_orb_limit: Optional orb override used when calculating single-chart aspects.

    Examples:
        Basic transit calculation:

        >>> natal_chart = AstrologicalSubjectFactory.from_birth_data(...)
        >>> ephemeris_data = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()
        >>> factory = TransitsTimeRangeFactory(natal_chart, ephemeris_data)
        >>> transits = factory.get_transit_moments()

        Custom configuration:

        >>> from kerykeion.schemas import AstrologicalPoint, ActiveAspect
        >>> custom_points = ["Sun", "Moon"]
        >>> custom_aspects = [ActiveAspect.CONJUNCTION, ActiveAspect.OPPOSITION]
        >>> factory = TransitsTimeRangeFactory(
        ...     natal_chart, ephemeris_data,
        ...     active_points=custom_points,
        ...     active_aspects=custom_aspects
        ... )

    Note:
        - Calculation time scales with the number of ephemeris data points
        - More active points and aspects increase computational requirements
        - The natal chart's coordinate system should match the ephemeris data
    """

    def __init__(
        self,
        natal_chart: AstrologicalSubjectModel,
        ephemeris_data_points: List[AstrologicalSubjectModel],
        active_points: List[AstrologicalPoint] = DEFAULT_ACTIVE_POINTS,
        active_aspects: List[ActiveAspect] = DEFAULT_ACTIVE_ASPECTS,
        settings_file: Union[Path, KerykeionSettingsModel, dict, None] = None,
        *,
        axis_orb_limit: Optional[float] = None,
    ):
        """
        Initialize the TransitsTimeRangeFactory with calculation parameters.

        Sets up the factory with all necessary data and configuration for calculating
        transits across the specified time period. The natal chart serves as the
        reference point, while ephemeris data points provide the transiting positions
        for comparison.

        Args:
            natal_chart (AstrologicalSubjectModel): Reference natal chart containing
                the baseline planetary positions for transit calculations.
            ephemeris_data_points (List[AstrologicalSubjectModel]): Time-ordered list
                of planetary positions representing different moments in time.
                Typically generated by EphemerisDataFactory.
            active_points (List[AstrologicalPoint], optional): Celestial bodies to
                include in aspect calculations. Determines which planets/points are
                analyzed for aspects. Defaults to DEFAULT_ACTIVE_POINTS.
            active_aspects (List[ActiveAspect], optional): Types of angular relationships
                to calculate between natal and transiting positions. Defaults to
                DEFAULT_ACTIVE_ASPECTS.
            settings_file (Union[Path, KerykeionSettingsModel, dict, None], optional):
                Configuration settings for orb tolerances, calculation methods, and
                other parameters. Defaults to None (uses system defaults).
            axis_orb_limit (float | None, optional): Optional orb threshold for
                chart axes applied during aspect calculations.

        Note:
            - All ephemeris data points should use the same coordinate system as the natal chart
            - The order of ephemeris_data_points determines the chronological sequence
            - Settings affect orb tolerances and calculation precision
        """
        self.natal_chart = natal_chart
        self.ephemeris_data_points = ephemeris_data_points
        self.active_points = active_points
        self.active_aspects = active_aspects
        self.settings_file = settings_file
        self.axis_orb_limit = axis_orb_limit

    def get_transit_moments(self) -> TransitsTimeRangeModel:
        """
        Calculate and generate transit data for all configured time points.

        This method processes each ephemeris data point to identify angular relationships
        (aspects) between transiting celestial bodies and natal chart positions. It
        creates a comprehensive model containing all transit moments with their
        corresponding aspects and timestamps.

        The calculation process:
        1. Iterates through each ephemeris data point chronologically
        2. Compares transiting planetary positions with natal chart positions
        3. Identifies aspects that fall within the configured orb tolerances
        4. Creates timestamped transit moment records
        5. Compiles all data into a structured model for analysis

        Returns:
            TransitsTimeRangeModel: A comprehensive model containing:
                - dates (List[str]): ISO-formatted datetime strings for all data points
                - subject (AstrologicalSubjectModel): The natal chart used as reference
                - transits (List[TransitMomentModel]): Chronological list of transit moments,
                  each containing:
                  * date (str): ISO-formatted timestamp for the transit moment
                  * aspects (List[RelevantAspect]): All aspects formed at this moment
                    between transiting and natal positions

        Examples:
            Basic usage:

            >>> factory = TransitsTimeRangeFactory(natal_chart, ephemeris_data)
            >>> results = factory.get_transit_moments()
            >>>
            >>> # Access specific data
            >>> all_dates = results.dates
            >>> first_transit = results.transits[0]
            >>> aspects_at_first_moment = first_transit.aspects

            Processing results:

            >>> results = factory.get_transit_moments()
            >>> for transit_moment in results.transits:
            ...     print(f"Date: {transit_moment.date}")
            ...     for aspect in transit_moment.aspects:
            ...         print(f"  {aspect.p1_name} {aspect.aspect} {aspect.p2_name}")

        Performance Notes:
            - Calculation time is proportional to: number of time points × active points × active aspects
            - Large datasets may require significant processing time
            - Memory usage scales with the number of aspects found
            - Consider filtering active_points and active_aspects for better performance

        See Also:
            TransitMomentModel: Individual transit moment structure
            TransitsTimeRangeModel: Complete transit dataset structure
            AspectsFactory: Underlying aspect calculation engine
        """
        transit_moments = []

        for ephemeris_point in self.ephemeris_data_points:
            # Calculate aspects between transit positions and natal chart
            aspects = AspectsFactory.dual_chart_aspects(
                ephemeris_point,
                self.natal_chart,
                active_points=self.active_points,
                active_aspects=self.active_aspects,
                axis_orb_limit=self.axis_orb_limit,
                first_subject_is_fixed=False,  # Transit is moving
                second_subject_is_fixed=True,  # Natal is fixed
            ).aspects

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
            subject=self.natal_chart,
            transits=transit_moments,
        )


if __name__ == "__main__":
    # Create a natal chart for the subject
    person = AstrologicalSubjectFactory.from_birth_data("Johnny Depp", 1963, 6, 9, 20, 15, "Owensboro", "US")

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
    print(transit_results.model_dump()["transits"][2]["date"])
    print(transit_results.model_dump()["transits"][2]["aspects"][0])
