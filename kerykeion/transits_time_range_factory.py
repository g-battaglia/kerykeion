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

Sampling resolution:
    Transit detection is sample-based: an aspect is only seen if at least one
    ephemeris step falls inside its orb window. Fast movers — above all the
    Moon (~13.2°/day) — stay within a tight 3° predictive orb for only a few
    hours, so daily sampling can skip entire lunar aspects or merge distinct
    passes. As a rule of thumb the step should not exceed half the in-orb
    window of the fastest active point (orb / speed); for the Moon with a 3°
    orb that means steps of ~5 hours or less. A ``logging.warning`` is
    emitted when the configured ephemeris step exceeds this threshold.

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

import logging

from typing import Union, List, Optional, cast
from datetime import datetime, timedelta
from kerykeion.schemas.kr_models import AstrologicalSubjectModel
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.aspects import AspectsFactory
from kerykeion.schemas.kr_literals import AstrologicalPoint
from kerykeion.schemas.kr_models import ActiveAspect, TransitEventModel, TransitEventsTimeRangeModel, TransitMomentModel, TransitsTimeRangeModel
from kerykeion.schemas.settings_models import KerykeionSettingsModel
from kerykeion.settings.config_constants import (
    DEFAULT_ACTIVE_POINTS,
    PREDICTIVE_ACTIVE_ASPECTS,
)
from pathlib import Path

# Typical mean daily motion (degrees/day) of the transiting bodies, used to
# detect undersampling (steps larger than half the in-orb window of the
# fastest active point). Static values are enough for an order-of-magnitude
# check; the Moon dominates in practice.
_TYPICAL_DAILY_MOTION_DEGREES: dict[str, float] = {
    "Moon": 13.2,
    "Mercury": 1.4,
    "Venus": 1.2,
    "Sun": 1.0,
    "Mars": 0.52,
    "Jupiter": 0.083,
    "Saturn": 0.033,
    "Uranus": 0.012,
    "Neptune": 0.006,
    "Pluto": 0.004,
}


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
            Defaults to PREDICTIVE_ACTIVE_ASPECTS (tight 3° predictive orbs).
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

        >>> custom_points = ["Sun", "Moon"]
        >>> custom_aspects = [
        ...     {"name": "conjunction", "degree": 0, "orb": 8},
        ...     {"name": "opposition", "degree": 180, "orb": 8},
        ... ]
        >>> factory = TransitsTimeRangeFactory(
        ...     natal_chart, ephemeris_data,
        ...     active_points=custom_points,
        ...     active_aspects=custom_aspects
        ... )

    Note:
        - Calculation time scales with the number of ephemeris data points
        - More active points and aspects increase computational requirements
        - The natal chart's coordinate system should match the ephemeris data:
          a mismatch in zodiac_type / sidereal_mode / perspective_type is
          detected at construction time and reported via ``logging.warning``
    """

    def __init__(
        self,
        natal_chart: AstrologicalSubjectModel,
        ephemeris_data_points: List[AstrologicalSubjectModel],
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: Optional[List[ActiveAspect]] = None,
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
                PREDICTIVE_ACTIVE_ASPECTS (tight 3° predictive orbs).
            settings_file (Union[Path, KerykeionSettingsModel, dict, None], optional):
                Configuration settings for orb tolerances, calculation methods, and
                other parameters. Defaults to None (uses system defaults).
            axis_orb_limit (float | None, optional): Optional orb threshold for
                chart axes applied during aspect calculations.

        Note:
            - All ephemeris data points should use the same coordinate system as
              the natal chart: a ``logging.warning`` is emitted when the points'
              frame metadata (zodiac_type / sidereal_mode / perspective_type)
              differs from the natal chart's
            - The order of ephemeris_data_points determines the chronological sequence
            - Settings affect orb tolerances and calculation precision
        """
        self.natal_chart = natal_chart
        self.ephemeris_data_points = ephemeris_data_points
        self.active_points = list(active_points) if active_points is not None else list(DEFAULT_ACTIVE_POINTS)
        # Transits are a predictive technique — default to the tight 3°
        # Ptolemaic orbs, not the wide natal orbs.
        # The dict(...) copies keep callers' TypedDicts unshared; cast restores the ActiveAspect type.
        self.active_aspects: List[ActiveAspect] = cast(
            List[ActiveAspect],
            [dict(a) for a in active_aspects] if active_aspects is not None else [dict(a) for a in PREDICTIVE_ACTIVE_ASPECTS],
        )
        self.settings_file = settings_file
        self.axis_orb_limit = axis_orb_limit
        self._warn_if_frame_mismatch()
        self._warn_if_unordered()

    def _warn_if_unordered(self) -> None:
        """Warn when the ephemeris series is not in chronological order.

        Edge/truncation detection in ``get_transit_moments`` keys off
        ``transits[0]`` / ``transits[-1]`` as the first/last sampled instants,
        which is only valid when ``ephemeris_data_points`` are chronologically
        non-decreasing (a documented precondition). Out-of-order input would
        silently mis-flag truncation and the refinement bracket extension, so
        surface it loudly. Unparseable timestamps (e.g. BCE extended-year
        strings) are skipped rather than treated as a violation.
        """
        prev = None
        for point in self.ephemeris_data_points:
            try:
                current = datetime.fromisoformat(point.iso_formatted_utc_datetime)
            except (TypeError, ValueError):
                prev = None  # can't compare across an unparseable boundary
                continue
            if prev is not None and current < prev:
                logging.warning(
                    "ephemeris_data_points are not in chronological order "
                    "(found %s after %s). Transit edge detection and exact-moment "
                    "refinement assume a non-decreasing time series; reorder the "
                    "points or rebuild the series with a forward time range.",
                    current.isoformat(),
                    prev.isoformat(),
                )
                return
            prev = current

    def _warn_if_frame_mismatch(self) -> None:
        """Warn when the natal chart and the ephemeris series disagree on frame.

        Aspects are computed by directly comparing longitudes, so the two
        sides must share the same reference frame. A Sidereal natal chart
        matched against a Tropical ephemeris series (or vice versa) silently
        yields cross-frame aspects offset by the ayanamsha (~24°), and a
        perspective mismatch (e.g. heliocentric vs geocentric) is equally
        meaningless — the exact-moment refinement, which always recomputes in
        the natal frame, would then disagree with the coarse track. The frame
        is read from the models' metadata (``zodiac_type`` /
        ``sidereal_mode`` / ``perspective_type``).
        """
        natal_frame = (
            getattr(self.natal_chart, "zodiac_type", None),
            getattr(self.natal_chart, "sidereal_mode", None),
            getattr(self.natal_chart, "perspective_type", None),
            # A USER sidereal mode is only fully specified by its custom
            # ayanamsha epoch/offset: two charts both "USER" but with different
            # custom_ayanamsa values are different frames and must not compare equal.
            getattr(self.natal_chart, "custom_ayanamsa_t0", None),
            getattr(self.natal_chart, "custom_ayanamsa_ayan_t0", None),
        )
        for point in self.ephemeris_data_points:
            point_frame = (
                getattr(point, "zodiac_type", None),
                getattr(point, "sidereal_mode", None),
                getattr(point, "perspective_type", None),
                getattr(point, "custom_ayanamsa_t0", None),
                getattr(point, "custom_ayanamsa_ayan_t0", None),
            )
            if point_frame != natal_frame:
                logging.warning(
                    "Natal chart and ephemeris data points use different calculation "
                    "frames (natal: zodiac_type=%s, sidereal_mode=%s, "
                    "perspective_type=%s, custom_ayanamsa_t0=%s, custom_ayanamsa_ayan_t0=%s; "
                    "ephemeris: zodiac_type=%s, sidereal_mode=%s, perspective_type=%s, "
                    "custom_ayanamsa_t0=%s, custom_ayanamsa_ayan_t0=%s). Cross-frame "
                    "aspects are offset by the frame difference (a sidereal/tropical "
                    "mismatch shifts every aspect by the ayanamsha, ~24°) — rebuild the "
                    "ephemeris series with the natal chart's settings.",
                    *natal_frame,
                    *point_frame,
                )
                return

    def _sampling_gaps_days(self) -> "list[float]":
        """Return the positive gaps (in days) between consecutive ephemeris samples.

        This is the raw spacing of the series; each caller reduces it to the
        statistic that fits its job (the typical cadence for event splitting,
        the coarsest gap for the undersampling warning). Parsing the ISO
        timestamps is the dominant cost here and happens exactly once per call,
        so the two callers together do the same amount of work as the previous
        single ``_sampling_step_days`` did. Returns an empty list when fewer
        than two parseable data points are available.
        """
        if len(self.ephemeris_data_points) < 2:
            return []
        try:
            dates = [datetime.fromisoformat(p.iso_formatted_utc_datetime) for p in self.ephemeris_data_points]
        except (TypeError, ValueError):
            return []
        return [
            (later - earlier).total_seconds() / 86400.0
            for earlier, later in zip(dates, dates[1:])
            if (later - earlier).total_seconds() > 0
        ]

    def _representative_step_days(self) -> Optional[float]:
        """Return the *typical* sample spacing (the median gap, in days).

        Used to split a single aspect track into per-pass events and to size
        the refinement brackets. Taking the median — rather than the smallest
        gap — is deliberate: on a non-uniform series (e.g. one tight hourly
        pair amid otherwise daily samples) the minimum would report the densest
        interval, and ``_split_track_into_runs`` would then treat every ordinary
        daily step as a between-pass gap (it exceeds ``1.5 * min_gap``) and
        shatter a single transit pass into many phantom events. The median
        tracks the bulk cadence of the series and stays robust to a few outlier
        gaps in either direction. On a uniform series median == min == max, so
        behaviour (and every golden snapshot) is unchanged. Returns None when
        fewer than two samples are available.
        """
        gaps = self._sampling_gaps_days()
        if not gaps:
            return None
        # Single O(n log n) sort over the gaps (n-1 floats); negligible next to
        # the timestamp parsing already done in _sampling_gaps_days.
        ordered = sorted(gaps)
        mid = len(ordered) // 2
        if len(ordered) % 2:
            return ordered[mid]
        return (ordered[mid - 1] + ordered[mid]) / 2.0

    def _warn_if_undersampled(self) -> None:
        """Warn when the ephemeris step risks skipping fast-moving aspects.

        An aspect with orb ``o`` on a point moving ``v`` degrees/day stays in
        orb for ``2*o/v`` days. If the sampling step exceeds half that window
        (``o/v``), whole passes can fall between samples — for the Moon
        (~13.2°/day) with a 3° orb that is anything coarser than ~5.5 hours.

        Undersampling is measured against the *coarsest* gap (``max``), not the
        typical cadence: it is a property of the widest hole in the series,
        since that is where a whole fast pass can fall between two samples. On a
        non-uniform series a single dense patch must not mask the sparse
        remainder — using the smallest gap (the previous behaviour) would wrongly
        silence the warning whenever any one pair happened to be tightly spaced.
        """
        gaps = self._sampling_gaps_days()
        if not gaps:
            return
        step_days = max(gaps)

        fastest_speed = max(
            (
                _TYPICAL_DAILY_MOTION_DEGREES[point]
                for point in self.active_points
                if point in _TYPICAL_DAILY_MOTION_DEGREES
            ),
            default=None,
        )
        if fastest_speed is None:
            return

        # Size the window with the TIGHTEST configured orb: it has the
        # shortest in-orb window, so it is the first aspect the sampling
        # step starts missing.
        min_orb = min((float(a["orb"]) for a in self.active_aspects if float(a["orb"]) > 0), default=0.0)
        if min_orb <= 0:
            return

        half_window_days = min_orb / fastest_speed
        if step_days > half_window_days:
            fastest_point = max(
                (p for p in self.active_points if p in _TYPICAL_DAILY_MOTION_DEGREES),
                key=lambda p: _TYPICAL_DAILY_MOTION_DEGREES[p],
            )
            logging.warning(
                "Transit sampling step (%.2f days) exceeds half the in-orb window "
                "(%.2f days) of the fastest active point (%s, ~%.1f°/day at the "
                "tightest %.1f° orb). Fast aspects may be missed or merged; use a "
                "finer ephemeris step (e.g. hours instead of days).",
                step_days,
                half_window_days,
                fastest_point,
                _TYPICAL_DAILY_MOTION_DEGREES[fastest_point],
                min_orb,
            )

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
        self._warn_if_undersampled()

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

    def get_transit_events(
        self, *, refine_exact_moments: bool = False, refinement_iterations: int = 21
    ) -> TransitEventsTimeRangeModel:
        """Group transit moments into discrete transit events.

        Unlike ``get_transit_moments()`` which returns raw snapshots, this
        method identifies when aspects begin applying, reach exactness (minimum
        orb), and finish separating — producing a timeline of transit events.

        Algorithm:
            1. Get all transit moments via get_transit_moments()
            2. Track each unique (p1, p2, aspect) combination
            3. Split each track into separate events whenever the in-orb
               samples are not consecutive (gap > ~1.5x the sampling step),
               so recurring aspects (e.g. monthly lunar conjunctions or the
               multiple passes of a retrograde transit) yield one event per
               pass instead of one merged event
            4. Find the moment with minimum orb as the "exact" moment of each event
            5. Calculate orb rate of change at exact moment (degrees/day)
            6. (Optional) Refine exact_moment via ternary search for sub-step precision

        Events truncated by the analysed range report ``applying_start`` /
        ``separating_end`` as ``None``: the applying phase (or the separating
        phase) happened outside the sampled window, so its boundary is unknown.

        Args:
            refine_exact_moments: If True, uses a ternary search between the
                two ephemeris steps bracketing the minimum orb to refine the
                exact moment to sub-minute precision. Each iteration shrinks
                the uncertainty interval to two-thirds. Added in v6.0.
            refinement_iterations: Number of ternary-search iterations
                (default 21, equivalent to 12 exact halvings — sub-minute
                precision for daily steps). Added in v6.0.

        Returns:
            TransitEventsTimeRangeModel with sorted transit events.
        """

        transit_data = self.get_transit_moments()

        # Track active aspects across time steps
        # Key: (p1_name, p2_name, aspect) -> list of (date, orb, movement)
        active_tracks: dict[tuple[str, str, str], list[tuple[str, float, str]]] = {}

        for moment in transit_data.transits:
            for asp in moment.aspects:
                key = (asp.p1_name, asp.p2_name, asp.aspect)
                if key not in active_tracks:
                    active_tracks[key] = []
                active_tracks[key].append((moment.date, asp.orbit, asp.aspect_movement))

        # Range edges (used to flag truncated events) and sampling step
        # (used to split a track into separate per-pass events).
        first_moment_date = transit_data.transits[0].date if transit_data.transits else None
        last_moment_date = transit_data.transits[-1].date if transit_data.transits else None
        # The TYPICAL cadence (median gap), so a non-uniform series does not
        # over-split: see _representative_step_days and _split_track_into_runs.
        step_days = self._representative_step_days()

        # Convert tracks to events (one event per consecutive in-orb run)
        events: list[TransitEventModel] = []

        for (p1, p2, aspect_name), track in active_tracks.items():
            if not track:
                continue

            for run in self._split_track_into_runs(track, step_days):
                # Find minimum orb moment (exact)
                min_orb_idx = min(range(len(run)), key=lambda i: run[i][1])
                exact_date = run[min_orb_idx][0]
                min_orb = run[min_orb_idx][1]

                # Estimate orb rate after the exact moment (degrees per day),
                # from the coarse samples (before any refinement).
                orb_rate = None
                if min_orb_idx < len(run) - 1:
                    after_date, orb_after, _ = run[min_orb_idx + 1]
                    try:
                        dt_days = (
                            datetime.fromisoformat(after_date) - datetime.fromisoformat(exact_date)
                        ).total_seconds() / 86400.0
                    except ValueError:
                        dt_days = 0.0
                    if dt_days > 0:
                        orb_rate = round((orb_after - min_orb) / dt_days, 6)

                # Ternary-search refinement (v6.0): refine exact_moment between
                # bracketing steps. With tight orbs and fast bodies (Moon at
                # multi-hour steps) a run often has only 1-3 samples and the
                # minimum sits at a run EDGE — bracket one sampling step
                # beyond the edge in that case, otherwise the very events
                # that need refinement most would silently keep coarse values.
                if refine_exact_moments and step_days:
                    # Never extend past the analysed range itself: for an
                    # event truncated at the range edge the orb is monotonic
                    # there (the true exact lies outside the window), and the
                    # trisection would converge onto the artificial bracket
                    # edge — fabricating an exact_moment outside [start, end].
                    # At a range edge the bracket bound is the edge sample
                    # itself: in-range minima still refine, truncated events
                    # honestly converge to the range boundary.
                    if min_orb_idx > 0:
                        left_bracket = run[min_orb_idx - 1][0]
                    elif run[0][0] == first_moment_date:
                        left_bracket = run[0][0]
                    else:
                        try:
                            left_bracket = (
                                datetime.fromisoformat(run[0][0]) - timedelta(days=step_days)
                            ).isoformat()
                        except ValueError:
                            left_bracket = None
                    if min_orb_idx < len(run) - 1:
                        right_bracket = run[min_orb_idx + 1][0]
                    elif run[-1][0] == last_moment_date:
                        right_bracket = run[-1][0]
                    else:
                        try:
                            right_bracket = (
                                datetime.fromisoformat(run[-1][0]) + timedelta(days=step_days)
                            ).isoformat()
                        except ValueError:
                            right_bracket = None
                    if left_bracket is not None and right_bracket is not None:
                        refined = self._refine_exact_moment(
                            p1_name=p1,
                            p2_name=p2,
                            aspect_name=aspect_name,
                            left_date_str=left_bracket,
                            right_date_str=right_bracket,
                            iterations=refinement_iterations,
                        )
                        # Accept only genuine improvements: for an event
                        # truncated at the range edge the orb is monotonic and
                        # the probe points can never land exactly on the edge
                        # sample, so the "refined" orb comes back marginally
                        # worse — keep the coarse values then.
                        if refined is not None and refined[1] < min_orb:
                            exact_date, min_orb = refined

                # Event edges. None when the event is truncated by the range:
                # a run that starts on the first sample (or whose first in-orb
                # sample is already Separating) never showed its applying
                # phase; symmetrically for the separating side.
                first_date, _, first_movement = run[0]
                last_date, _, last_movement = run[-1]
                applying_start = (
                    first_date
                    if first_date != first_moment_date and first_movement != "Separating"
                    else None
                )
                separating_end = (
                    last_date
                    if last_date != last_moment_date and last_movement != "Applying"
                    else None
                )

                events.append(
                    TransitEventModel(
                        p1_name=p1,
                        p2_name=p2,
                        aspect=aspect_name,
                        applying_start=applying_start,
                        exact_moment=exact_date,
                        separating_end=separating_end,
                        min_orb=round(min_orb, 6),
                        orb_rate=orb_rate,
                    )
                )

        # Sort by exact_moment
        events.sort(key=lambda e: e.exact_moment)

        return TransitEventsTimeRangeModel(
            events=events,
            subject=self.natal_chart,
        )

    @staticmethod
    def _split_track_into_runs(
        track: "list[tuple[str, float, str]]",
        step_days: Optional[float],
    ) -> "list[list[tuple[str, float, str]]]":
        """Split a (date, orb, movement) track into consecutive in-orb runs.

        A track keyed only by (p1, p2, aspect) merges every recurrence of the
        aspect in the range (e.g. ~13 lunar conjunctions per year, or the
        triple pass of a retrograde transit). Whenever two successive in-orb
        samples are separated by more than ~1.5x the sampling step, the aspect
        left orb in between, so a new run (event) starts there.

        ``step_days`` here is the *representative* (median) cadence of the
        series, not its smallest gap — so an occasional tight pair in a
        non-uniform series does not drag the threshold down and split a single
        in-orb run into spurious per-sample events.
        """
        if not track:
            return []
        if step_days is None or step_days <= 0:
            return [list(track)]

        gap_threshold_seconds = 1.5 * step_days * 86400.0
        runs: list[list[tuple[str, float, str]]] = []
        current_run = [track[0]]
        for previous, current in zip(track, track[1:]):
            try:
                gap_seconds = (
                    datetime.fromisoformat(current[0]) - datetime.fromisoformat(previous[0])
                ).total_seconds()
            except ValueError:
                gap_seconds = 0.0
            if gap_seconds > gap_threshold_seconds:
                runs.append(current_run)
                current_run = [current]
            else:
                current_run.append(current)
        runs.append(current_run)
        return runs

    def _refine_exact_moment(
        self,
        p1_name: str,
        p2_name: str,
        aspect_name: str,
        left_date_str: str,
        right_date_str: str,
        iterations: int = 21,
    ) -> "tuple[str, float] | None":
        """Ternary-search the interval [left, right] for the sub-step exact moment.

        At each iteration, evaluates the aspect orb at two probe points placed
        1/3 and 2/3 of the way through the current interval. For a unimodal
        orb curve the minimum can never lie beyond the worse probe, so that
        outer third is discarded, shrinking the interval to 2/3 each time.

        (Comparing probes and then cutting at the *midpoint* — as a naive
        bisection would — is NOT safe here: with an asymmetric orb curve,
        e.g. near a station where the transiting body's speed changes across
        the bracket, the minimum can sit just past the midpoint on the
        discarded side.)

        Args:
            p1_name: Transit planet name.
            p2_name: Natal planet name.
            aspect_name: Aspect being refined (e.g. "conjunction").
            left_date_str: ISO datetime of the step before minimum orb.
            right_date_str: ISO datetime of the step after minimum orb.
            iterations: Number of ternary-search steps. Each step keeps 2/3
                of the interval, so 21 steps shrink it by (2/3)**21 ~ 1/4990
                — at least the precision of 12 exact halvings (sub-minute
                for daily sampling steps).

        Returns:
            Tuple of (refined_iso_datetime, refined_orb) or None if refinement fails.

        Notes:
            The natal positions are expressed in the natal chart's zodiac and
            perspective, so the bisection MUST recompute the transiting
            position with a matching configuration (``ephemeris_session`` with
            the natal sidereal mode). Refinement is skipped (returning None,
            keeping the coarse values) for non-geocentric perspectives, where
            a plain ``calc_ut`` would not reproduce the ephemeris positions.
        """
        from kerykeion.ephemeris_backend import swe, ephemeris_session
        from kerykeion.aspects.aspects_utils import difdeg2n
        from kerykeion.utilities import datetime_to_julian
        from kerykeion.settings.chart_defaults import DEFAULT_CHART_ASPECTS_SETTINGS

        # Non-geocentric perspectives (Heliocentric, Topocentric, Barycentric,
        # planetocentric...) need observer state this refinement does not
        # replicate — keep the coarse sample values instead of degrading them.
        if self.natal_chart.perspective_type not in ("Apparent Geocentric", "True Geocentric"):
            return None

        try:
            left_dt = datetime.fromisoformat(left_date_str)
            right_dt = datetime.fromisoformat(right_date_str)

            # Get the natal planet's fixed position
            natal_point = getattr(self.natal_chart, p2_name.lower(), None)
            if natal_point is None:
                return None
            natal_pos = natal_point.abs_pos

            # Determine the transit planet's Swiss Ephemeris ID
            from kerykeion.astrological_subject_factory import STANDARD_PLANETS, TNO_PLANETS

            # Transit point names come from aspect results, which use the AstrologicalPoint vocabulary.
            transit_point_name = cast(AstrologicalPoint, p1_name)
            planet_id = STANDARD_PLANETS.get(transit_point_name)
            if planet_id is None:
                tno_num = TNO_PLANETS.get(transit_point_name)
                if tno_num is not None:
                    planet_id = swe.AST_OFFSET + tno_num
            if planet_id is None:
                return None

            # Resolve the target angle of the aspect being refined. The orb
            # window is irrelevant here: the objective below is the plain
            # angular deviation from exactness, which is exactly what
            # get_aspect_from_two_points reports as ``orbit`` for in-orb
            # positions — so no per-aspect orb settings are needed.
            matching_setting = next(
                (s for s in DEFAULT_CHART_ASPECTS_SETTINGS if s["name"] == aspect_name),
                None,
            )
            if matching_setting is None:
                return None
            target_degree = float(matching_setting["degree"])

            best_date = left_dt
            best_orb = 999.0

            # Match the natal chart's zodiac configuration so the recomputed
            # transiting longitudes are comparable with the natal abs_pos
            # (sidereal vs sidereal, tropical vs tropical).
            with ephemeris_session(
                zodiac_type=self.natal_chart.zodiac_type,
                sidereal_mode=self.natal_chart.sidereal_mode,
                custom_ayanamsa_t0=self.natal_chart.custom_ayanamsa_t0,
                custom_ayanamsa_ayan_t0=self.natal_chart.custom_ayanamsa_ayan_t0,
                perspective_type=self.natal_chart.perspective_type,
            ) as iflag:
                def orb_at(moment: datetime) -> float:
                    """Angular deviation from exactness at ``moment``, in degrees."""
                    position = swe.calc_ut(datetime_to_julian(moment), planet_id, iflag)[0][0]
                    return abs(abs(difdeg2n(position, natal_pos)) - target_degree)

                for _ in range(iterations):
                    third = (right_dt - left_dt) / 3
                    m1_dt = left_dt + third
                    m2_dt = right_dt - third

                    try:
                        m1_orb = orb_at(m1_dt)
                        m2_orb = orb_at(m2_dt)
                    except Exception:
                        return None

                    if m1_orb < best_orb:
                        best_orb, best_date = m1_orb, m1_dt
                    if m2_orb < best_orb:
                        best_orb, best_date = m2_orb, m2_dt

                    # Unimodal elimination: the minimum can never lie beyond
                    # the worse probe, so drop that outer third.
                    if m1_orb < m2_orb:
                        right_dt = m2_dt
                    else:
                        left_dt = m1_dt

                # One last sample at the centre of the converged bracket: for
                # a unimodal curve it is at most half the final bracket away
                # from the true minimum, tightening the best probe seen.
                mid_dt = left_dt + (right_dt - left_dt) / 2
                try:
                    mid_orb = orb_at(mid_dt)
                except Exception:
                    return None
                if mid_orb < best_orb:
                    best_orb, best_date = mid_orb, mid_dt

            return (best_date.isoformat(), round(best_orb, 6))

        except (OSError, ValueError):
            return None


if __name__ == "__main__":
    from datetime import timedelta
    from kerykeion.ephemeris_data_factory import EphemerisDataFactory

    # Create a natal chart for the subject
    person = AstrologicalSubjectFactory.from_birth_data("Johnny Depp", 1963, 6, 9, 20, 15, "Owensboro", "US")

    # Define the time period for transit calculation
    start_date = datetime.now()
    end_date = datetime.now() + timedelta(days=30)

    # Create ephemeris data for the specified time period.
    # 4-hour steps keep the Moon (~13.2°/day) safely sampled within the tight
    # 3° predictive orb window (in-orb half-window ≈ 5.5 hours).
    ephemeris_factory = EphemerisDataFactory(
        start_datetime=start_date,
        end_datetime=end_date,
        step_type="hours",
        step=4,
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
