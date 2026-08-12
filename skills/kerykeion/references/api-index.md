# API Index

Map of every name this skill documents to the reference file that covers it:
the 120 root exports, the literals and presets, the env vars, and every API
the references mark as a **Subpackage import**. Names are importable from
bare `kerykeion` unless the Kind column says otherwise. Use this file to
answer "where is X documented?"; the domain file is always the richer source.

| Name | Kind | Primary reference |
|---|---|---|
| `ACGLineModel` | model | `references/locational.md` |
| `ACGLinePointModel` | model | `references/locational.md` |
| `ActiveAspect` | literal — `kerykeion.schemas` | `references/aspects-and-orbs.md` |
| `ALL_ACTIVE_ASPECTS` | subpackage import — `kerykeion.settings.config_constants` | `references/aspects-and-orbs.md` |
| `ALL_ACTIVE_POINTS` | constant/function — `kerykeion.settings` | `references/subjects.md` |
| `AlmutenFigurisStrategy` | subpackage import — `kerykeion.dominants` | `references/analysis.md` |
| `AngularityModel` | model | `references/charts-and-drawing.md` |
| `aspect_to_context` | subpackage import — `kerykeion.context` | `references/reports-and-ai-context.md` |
| `AspectModel` | model | `references/aspects-and-orbs.md` |
| `AspectMovementType` | literal — `kerykeion.schemas` | `references/aspects-and-orbs.md` |
| `AspectName` | literal — `kerykeion.schemas` | `references/aspects-and-orbs.md` |
| `AspectsFactory` | factory | `references/aspects-and-orbs.md` |
| `AstroCartographyFactory` | factory | `references/locational.md` |
| `astrological_subject_to_context` | subpackage import — `kerykeion.context` | `references/reports-and-ai-context.md` |
| `AstrologicalPoint` | literal — `kerykeion.schemas` | `references/subjects.md` |
| `AstrologicalSubjectFactory` | factory | `references/subjects.md` |
| `AstrologicalSubjectModel` | model | `references/subjects.md` |
| `BACKEND_NAME` | constant | `references/backends-and-provenance.md` |
| `BaseDominantStrategy` | model | `references/analysis.md` |
| `BEHENIAN_FIXED_STARS` | subpackage import — `kerykeion.settings.config_constants` | `references/subjects.md` |
| `BreakdownItem` | subpackage import — `kerykeion.dominants` | `references/analysis.md` |
| `calculate_essential_dignity` | subpackage import — `kerykeion.dignities` | `references/traditional.md` |
| `calculate_moon_phase` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `calculate_nakshatra` | subpackage import — `kerykeion.vedic` | `references/predictive.md` |
| `Category` | subpackage import — `kerykeion.dominants` | `references/analysis.md` |
| `ChartDataFactory` | factory | `references/charts-and-drawing.md` |
| `ChartDataModel` | alias | `references/charts-and-drawing.md` |
| `ChartDrawer` | class | `references/charts-and-drawing.md` |
| `ChartPointTag` | subpackage import — `kerykeion.charts.svg_metadata` | `references/charts-and-drawing.md` |
| `ChartType` | literal — `kerykeion.schemas` | `references/charts-and-drawing.md` |
| `check_and_adjust_polar_latitude` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `circular_mean` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `circular_sort` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `civil_jd` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `civil_leap_year` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `classify_motion_state` | subpackage import — `kerykeion.motion` | `references/utilities.md` |
| `CompositeChartType` | literal — `kerykeion.schemas` | `references/subjects.md` |
| `CompositeSubjectFactory` | factory | `references/subjects.md` |
| `CompositeSubjectModel` | model | `references/subjects.md` |
| `datetime_to_julian` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `DEFAULT_ACTIVE_ASPECTS` | constant/function — `kerykeion.settings` | `references/aspects-and-orbs.md` |
| `DEFAULT_ACTIVE_POINTS` | constant/function — `kerykeion.settings` | `references/subjects.md` |
| `DEFAULT_CELESTIAL_POINTS_SETTINGS` | constant/function — `kerykeion.settings` | `references/charts-and-drawing.md` |
| `DEFAULT_CHART_ASPECTS_SETTINGS` | constant/function — `kerykeion.settings` | `references/charts-and-drawing.md` |
| `DEFAULT_CHART_COLORS` | constant/function — `kerykeion.settings` | `references/charts-and-drawing.md` |
| `DEFAULT_FIXED_STARS` | subpackage import — `kerykeion.settings.config_constants` | `references/subjects.md` |
| `DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS` | subpackage import — `kerykeion.settings.config_constants` | `references/aspects-and-orbs.md` |
| `DEFAULT_SWEPH_DOWNLOAD_DIR` | subpackage import — `kerykeion.ephemeris_backend` | `references/backends-and-provenance.md` |
| `DISCEPOLO_SCORE_ACTIVE_ASPECTS` | subpackage import — `kerykeion.settings.config_constants` | `references/aspects-and-orbs.md` |
| `distribute_percentages_to_100` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `DistributionMethod` | subpackage import — `kerykeion.dominants.base` | `references/analysis.md` |
| `DominantBreakdownItemModel` | model | `references/analysis.md` |
| `DominantMethod` | function | `references/analysis.md` |
| `DominantsConfig` | subpackage import — `kerykeion.dominants` | `references/analysis.md` |
| `DominantScoreModel` | model | `references/analysis.md` |
| `DominantsFactory` | factory | `references/analysis.md` |
| `DominantsModel` | model | `references/analysis.md` |
| `DominantStrategy` | model | `references/analysis.md` |
| `dual_chart_data_to_context` | subpackage import — `kerykeion.context` | `references/reports-and-ai-context.md` |
| `DualChartAspectsModel` | model | `references/aspects-and-orbs.md` |
| `DualChartDataModel` | model | `references/charts-and-drawing.md` |
| `EclipseFactory` | factory | `references/mundane-events.md` |
| `EclipseSearchResultModel` | model | `references/mundane-events.md` |
| `Element` | literal — `kerykeion.schemas` | `references/subjects.md` |
| `element_distribution_to_context` | subpackage import — `kerykeion.context` | `references/reports-and-ai-context.md` |
| `ElementalBalanceStrategy` | subpackage import — `kerykeion.dominants` | `references/analysis.md` |
| `ElementDistributionModel` | model | `references/charts-and-drawing.md` |
| `ElementQualityDistributionMethod` | subpackage import — `kerykeion.charts.utils` | `references/charts-and-drawing.md` |
| `ephe` | subpackage import — `kerykeion.ephemeris_backend` | `references/backends-and-provenance.md` |
| `EPHE_DATA_PATH` | subpackage import — `kerykeion.ephemeris_backend` | `references/backends-and-provenance.md` |
| `EPHEMERIS_LOCK` | subpackage import — `kerykeion.ephemeris_backend` | `references/backends-and-provenance.md` |
| `ephemeris_session` | subpackage import — `kerykeion.ephemeris_backend` | `references/backends-and-provenance.md` |
| `EphemerisDataFactory` | factory | `references/predictive.md` |
| `EphemerisDictModel` | model | `references/predictive.md` |
| `EphemerisRangeError` | exception — raised by libephemeris, not re-exported | `references/backends-and-provenance.md` |
| `EphemerisWarningModel` | model | `references/backends-and-provenance.md` |
| `EVENING_FIRST` | subpackage import — `kerykeion.heliacal` | `references/mundane-events.md` |
| `extract_year_from_iso` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `FetchGeonames` | subpackage import — `kerykeion.geonames` | `references/subjects.md` |
| `find_common_active_points` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `FirdariaFactory` | factory | `references/traditional.md` |
| `FirdariaModel` | model | `references/traditional.md` |
| `FirdariaPeriodModel` | model | `references/traditional.md` |
| `FirdariaSubPeriodModel` | model | `references/traditional.md` |
| `FixedStarCatalog` | subpackage import — `kerykeion.fixed_stars` | `references/mundane-events.md` |
| `FixedStarDiscoveryFactory` | factory | `references/mundane-events.md` |
| `FixedStarMetadataModel` | model | `references/mundane-events.md` |
| `format_ancient_iso` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `format_astronomical_iso_date` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `format_degrees_below_bound` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `format_iso_display` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `format_timedelta_hhmm` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `get_available_astrological_points_list` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `get_domicile_ruler` | subpackage import — `kerykeion.dignities` | `references/traditional.md` |
| `get_exaltation_ruler` | subpackage import — `kerykeion.dignities` | `references/traditional.md` |
| `get_house_name` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `get_house_number` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `get_houses_list` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `get_kerykeion_point_from_degree` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `get_moon_emoji_from_phase_int` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `get_moon_phase_name_from_phase_int` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `get_number_from_name` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `get_planet_house` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `get_translations` | constant/function — `kerykeion.settings` | `references/charts-and-drawing.md` |
| `get_triplicity_lords` | subpackage import — `kerykeion.dignities` | `references/analysis.md` |
| `has_terrestrial_frame` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `HELIACAL_RISING` | subpackage import — `kerykeion.heliacal` | `references/mundane-events.md` |
| `HELIACAL_SETTING` | subpackage import — `kerykeion.heliacal` | `references/mundane-events.md` |
| `HeliacalEventModel` | model | `references/mundane-events.md` |
| `HeliacalFactory` | factory | `references/mundane-events.md` |
| `HoraryConsiderationModel` | model | `references/traditional.md` |
| `HoraryIndicatorsFactory` | factory | `references/traditional.md` |
| `HoraryIndicatorsModel` | model | `references/traditional.md` |
| `HorarySignificatorModel` | model | `references/traditional.md` |
| `house_comparison_to_context` | subpackage import — `kerykeion.context` | `references/reports-and-ai-context.md` |
| `HOUSE_FIELD_NAMES` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `HouseComparisonFactory` | factory | `references/analysis.md` |
| `HouseComparisonModel` | model | `references/analysis.md` |
| `HouseNumbers` | literal — `kerykeion.schemas` | `references/subjects.md` |
| `Houses` | literal — `kerykeion.schemas` | `references/subjects.md` |
| `houses_ex2_with_polar_fallback` | subpackage import — `kerykeion.ephemeris_backend` | `references/backends-and-provenance.md` |
| `houses_ex2_with_polar_fallback_ex` | subpackage import — `kerykeion.ephemeris_backend` | `references/backends-and-provenance.md` |
| `HousesSystemIdentifier` | literal — `kerykeion.schemas` | `references/zodiac-houses-perspectives.md` |
| `IndicatorTag` | subpackage import — `kerykeion.charts.svg_metadata` | `references/charts-and-drawing.md` |
| `IngressModel` | model | `references/mundane-events.md` |
| `inline_css_variables_in_svg` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `is_ambiguous` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `is_nonexistent` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `is_point_between` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `jd_to_iso_date` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `jd_to_iso_datetime` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `julian_to_datetime` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `KERYKEION_BACKEND` | env-var | `references/backends-and-provenance.md` |
| `KERYKEION_EPHE_PATH` | env-var | `references/backends-and-provenance.md` |
| `KERYKEION_GEONAMES_CACHE_NAME` | env-var | `references/subjects.md` |
| `KERYKEION_GEONAMES_USERNAME` | env-var | `references/subjects.md` |
| `KERYKEION_LEB_MODE` | env-var | `references/backends-and-provenance.md` |
| `kerykeion_point_to_context` | subpackage import — `kerykeion.context` | `references/reports-and-ai-context.md` |
| `KerykeionChartLanguage` | literal — `kerykeion.schemas` | `references/charts-and-drawing.md` |
| `KerykeionChartStyle` | literal — `kerykeion.schemas` | `references/charts-and-drawing.md` |
| `KerykeionChartTheme` | literal — `kerykeion.schemas` | `references/charts-and-drawing.md` |
| `KerykeionException` | exception | `references/subjects.md` |
| `KerykeionPointModel` | model | `references/subjects.md` |
| `KerykeionSettingsModel` | model | `references/charts-and-drawing.md` |
| `LANGUAGE_SETTINGS` | constant/function — `kerykeion.settings` | `references/charts-and-drawing.md` |
| `load_language_pair` | constant/function — `kerykeion.settings` | `references/charts-and-drawing.md` |
| `load_language_settings` | constant/function — `kerykeion.settings` | `references/charts-and-drawing.md` |
| `localize_naive` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `LotName` | subpackage import — `kerykeion.zodiacal_releasing.factory` | `references/traditional.md` |
| `lunar_phase_to_context` | subpackage import — `kerykeion.context` | `references/reports-and-ai-context.md` |
| `LunarEclipseModel` | model | `references/mundane-events.md` |
| `LunarPhaseEmoji` | literal — `kerykeion.schemas` | `references/calendars-hours-moon.md` |
| `LunarPhaseName` | literal — `kerykeion.schemas` | `references/calendars-hours-moon.md` |
| `LunationFinderFactory` | factory | `references/mundane-events.md` |
| `LunationModel` | model | `references/mundane-events.md` |
| `LunationsCollectionModel` | model | `references/mundane-events.md` |
| `MidpointAspectModel` | model | `references/analysis.md` |
| `MidpointFactory` | factory | `references/analysis.md` |
| `MidpointModel` | model | `references/analysis.md` |
| `midpoints_to_context` | subpackage import — `kerykeion.context` | `references/reports-and-ai-context.md` |
| `ModernDominantStrategy` | subpackage import — `kerykeion.dominants` | `references/analysis.md` |
| `moon_phase_overview_to_context` | subpackage import — `kerykeion.context` | `references/reports-and-ai-context.md` |
| `MoonPhaseDetailsFactory` | factory | `references/calendars-hours-moon.md` |
| `MoonPhaseOverviewModel` | model | `references/calendars-hours-moon.md` |
| `MORNING_LAST` | subpackage import — `kerykeion.heliacal` | `references/mundane-events.md` |
| `MotionState` | literal — `kerykeion.schemas` | `references/subjects.md` |
| `MundaneAspectFactory` | factory | `references/mundane-events.md` |
| `MundaneAspectModel` | model | `references/mundane-events.md` |
| `MundaneAspectsCollectionModel` | model | `references/mundane-events.md` |
| `MutualReceptionModel` | model | `references/traditional.md` |
| `MutualReceptionsFactory` | factory | `references/traditional.md` |
| `MutualReceptionsModel` | model | `references/traditional.md` |
| `NO_POINT_ORB_ADJUSTMENTS` | subpackage import — `kerykeion.settings.config_constants` | `references/aspects-and-orbs.md` |
| `normalize_longitude` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `normalize_zodiac_type` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `OccultationFactory` | factory | `references/mundane-events.md` |
| `OccultationModel` | model | `references/mundane-events.md` |
| `OrbAdjustmentStrategy` | subpackage import — `kerykeion.aspects.orb_utils` | `references/aspects-and-orbs.md` |
| `parse_astronomical_iso_moment` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `parse_chart_points` | subpackage import — `kerykeion.charts.svg_metadata` | `references/charts-and-drawing.md` |
| `parse_indicators` | subpackage import — `kerykeion.charts.svg_metadata` | `references/charts-and-drawing.md` |
| `PerspectiveType` | literal — `kerykeion.schemas` | `references/zodiac-houses-perspectives.md` |
| `PlanetaryHourModel` | model | `references/calendars-hours-moon.md` |
| `PlanetaryHoursFactory` | factory | `references/calendars-hours-moon.md` |
| `PlanetaryHoursModel` | model | `references/calendars-hours-moon.md` |
| `PlanetaryNodeModel` | model | `references/mundane-events.md` |
| `PlanetaryNodesCollectionModel` | model | `references/mundane-events.md` |
| `PlanetaryNodesFactory` | factory | `references/mundane-events.md` |
| `PlanetaryPhenomenaCollectionModel` | model | `references/mundane-events.md` |
| `PlanetaryPhenomenaFactory` | factory | `references/mundane-events.md` |
| `PlanetaryPhenomenaModel` | model | `references/mundane-events.md` |
| `PlanetaryReturnFactory` | factory | `references/predictive.md` |
| `PlanetReturnModel` | model | `references/predictive.md` |
| `point_in_house_to_context` | subpackage import — `kerykeion.context` | `references/reports-and-ai-context.md` |
| `PointOrbAdjustment` | subpackage import — `kerykeion.aspects.orb_utils` | `references/aspects-and-orbs.md` |
| `PointType` | literal — `kerykeion.schemas` | `references/subjects.md` |
| `POLAR_HOUSES_ERROR_TYPES` | subpackage import — `kerykeion.ephemeris_backend` | `references/backends-and-provenance.md` |
| `PREDICTIVE_ACTIVE_ASPECTS` | subpackage import — `kerykeion.settings.config_constants` | `references/aspects-and-orbs.md` |
| `PrimaryDirectionModel` | model | `references/traditional.md` |
| `PrimaryDirectionsFactory` | factory | `references/traditional.md` |
| `ProfectionsFactory` | factory | `references/traditional.md` |
| `ProfectionsModel` | model | `references/traditional.md` |
| `ProfectionYearModel` | model | `references/traditional.md` |
| `ProgressedPointModel` | model | `references/predictive.md` |
| `ProgressedToNatalAspectModel` | model | `references/predictive.md` |
| `PTOLEMAIC_ASPECTS` | constant | `references/aspects-and-orbs.md` |
| `Quality` | literal — `kerykeion.schemas` | `references/subjects.md` |
| `quality_distribution_to_context` | subpackage import — `kerykeion.context` | `references/reports-and-ai-context.md` |
| `QualityDistributionModel` | model | `references/charts-and-drawing.md` |
| `RelationshipScoreDescription` | literal — `kerykeion.schemas` | `references/analysis.md` |
| `RelationshipScoreFactory` | factory | `references/analysis.md` |
| `RelationshipScoreModel` | model | `references/analysis.md` |
| `RelocatedChartFactory` | factory | `references/locational.md` |
| `ReportGenerator` | class | `references/reports-and-ai-context.md` |
| `require_same_frame` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `reset_ephemeris_session` | subpackage import — `kerykeion.ephemeris_backend` | `references/backends-and-provenance.md` |
| `resolve_pair_orb_adjustment` | subpackage import — `kerykeion.aspects.orb_utils` | `references/aspects-and-orbs.md` |
| `resolve_sect_is_diurnal` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `resolve_subject_birth_datetime` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `resolve_subject_local_moment` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `resolve_subject_local_now` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `RetrogradeStationFactory` | factory | `references/mundane-events.md` |
| `RetrogradeStationsCollectionModel` | model | `references/mundane-events.md` |
| `ReturnType` | literal — `kerykeion.schemas` | `references/predictive.md` |
| `ROYAL_FIXED_STARS` | subpackage import — `kerykeion.settings.config_constants` | `references/subjects.md` |
| `safe_timezone` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `SecondaryProgressionFactory` | factory | `references/predictive.md` |
| `SecondaryProgressionsResultModel` | model | `references/predictive.md` |
| `SettingsSource` | constant/function — `kerykeion.settings` | `references/charts-and-drawing.md` |
| `setup_logging` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `SiderealMode` | literal — `kerykeion.schemas` | `references/zodiac-houses-perspectives.md` |
| `Sign` | literal — `kerykeion.schemas` | `references/subjects.md` |
| `SIGN_CODES` | literal — `kerykeion.schemas` | `references/zodiac-houses-perspectives.md` |
| `SignIngressesCollectionModel` | model | `references/mundane-events.md` |
| `SignIngressFactory` | factory | `references/mundane-events.md` |
| `SignNumbers` | literal — `kerykeion.schemas` | `references/subjects.md` |
| `single_chart_data_to_context` | subpackage import — `kerykeion.context` | `references/reports-and-ai-context.md` |
| `SingleChartAspectsModel` | model | `references/aspects-and-orbs.md` |
| `SingleChartDataModel` | model | `references/charts-and-drawing.md` |
| `solar_arc_to_context` | subpackage import — `kerykeion.context` | `references/reports-and-ai-context.md` |
| `SolarArcDirectedAspectModel` | model | `references/predictive.md` |
| `SolarArcDirectedPointModel` | model | `references/predictive.md` |
| `SolarArcFactory` | factory | `references/predictive.md` |
| `SolarArcSubjectModel` | model | `references/predictive.md` |
| `SolarEclipseModel` | model | `references/mundane-events.md` |
| `SolarLunarReturnType` | subpackage import — `kerykeion.planetary_returns.factory` | `references/predictive.md` |
| `SpeculumEntryModel` | model | `references/traditional.md` |
| `StationModel` | model | `references/mundane-events.md` |
| `StelliumModel` | model | `references/charts-and-drawing.md` |
| `strip_illegal_control_chars` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `SunTimesFactory` | factory | `references/calendars-hours-moon.md` |
| `SunTimesModel` | model | `references/calendars-hours-moon.md` |
| `TERRESTRIAL_PERSPECTIVES` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `to_context` | function | `references/reports-and-ai-context.md` |
| `TRADITIONAL_ASTROLOGY_ACTIVE_POINTS` | subpackage import — `kerykeion.settings.config_constants` | `references/subjects.md` |
| `transit_moment_to_context` | subpackage import — `kerykeion.context` | `references/reports-and-ai-context.md` |
| `TransitEventModel` | model | `references/predictive.md` |
| `TransitEventsTimeRangeModel` | model | `references/predictive.md` |
| `transits_time_range_to_context` | subpackage import — `kerykeion.context` | `references/reports-and-ai-context.md` |
| `TransitsTimeRangeFactory` | factory | `references/predictive.md` |
| `TransitsTimeRangeModel` | model | `references/predictive.md` |
| `TriplicityLordsModel` | model | `references/traditional.md` |
| `URANIAN_ACTIVE_POINTS` | subpackage import — `kerykeion.settings.config_constants` | `references/subjects.md` |
| `V5_DEFAULT_ACTIVE_POINTS` | constant/function — `kerykeion.settings` | `references/migration-and-deprecations.md` |
| `validate_latitude` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `validate_longitude` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `validate_point_orb_adjustments` | subpackage import — `kerykeion.aspects.orb_utils` | `references/aspects-and-orbs.md` |
| `VocAspectName` | literal — `kerykeion.schemas` | `references/calendars-hours-moon.md` |
| `VocTargetPlanet` | literal — `kerykeion.schemas` | `references/calendars-hours-moon.md` |
| `VoidOfCourseAspectModel` | model | `references/calendars-hours-moon.md` |
| `VoidOfCourseMoonFactory` | factory | `references/calendars-hours-moon.md` |
| `VoidOfCourseMoonModel` | model | `references/calendars-hours-moon.md` |
| `VoidOfCourseWindowModel` | model | `references/calendars-hours-moon.md` |
| `VoidOfCourseWindowsCollectionModel` | model | `references/calendars-hours-moon.md` |
| `wrap_180` | subpackage import — `kerykeion.utilities` | `references/utilities.md` |
| `ZodiacalReleasingFactory` | factory | `references/traditional.md` |
| `ZodiacalReleasingModel` | model | `references/traditional.md` |
| `ZodiacType` | literal — `kerykeion.schemas` | `references/zodiac-houses-perspectives.md` |
| `ZRPeriodModel` | model | `references/traditional.md` |
