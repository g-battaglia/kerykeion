"""Human-readable ASCII report generation for astrological data."""

from __future__ import annotations

from typing import Mapping, Optional, Sequence, Union, Literal

from simple_ascii_tables import AsciiTable

from kerykeion.fixed_stars.catalog import FixedStarCatalog

from kerykeion.utilities.core import (
    get_available_astrological_points_list,
    get_houses_list,
    format_degrees_below_bound,
    format_iso_display,
    format_timedelta_hhmm,
    strip_illegal_control_chars,
)
from kerykeion.schemas.models import (
    AngularityModel,
    AstrologicalSubjectModel,
    ChartDataModel,
    CompositeSubjectModel,
    DominantScoreModel,
    DominantsModel,
    DualChartDataModel,
    FirdariaModel,
    HoraryIndicatorsModel,
    MoonPhaseOverviewModel,
    MutualReceptionModel,
    MutualReceptionsModel,
    PlanetReturnModel,
    PointInHouseModel,
    ProfectionsModel,
    RelationshipScoreModel,
    SingleChartDataModel,
    StelliumModel,
    KerykeionPointModel,
    ZRPeriodModel,
    ZodiacalReleasingModel,
)
from kerykeion.settings.config_constants import (
    AXIAL_POINTS,
    LUNAR_NODES,
    MAIN_PLANETS,
    return_label_keys,
    subject_states_a_diurnality,
)


# Keys must match the ``AspectName`` literal values in kerykeion.schemas.literals.
ASPECT_SYMBOLS = {
    "conjunction": "☌",
    "opposition": "☍",
    "trine": "△",
    "square": "□",
    "sextile": "⚹",
    "quincunx": "⚻",
    "semi-sextile": "⚺",
    "semi-square": "∠",
    "sesquiquadrate": "⚼",
    "quintile": "Q",
    "biquintile": "bQ",
    "parallel": "∥",
    "contra-parallel": "⋕",
}

MOVEMENT_SYMBOLS = {
    "Applying": "→",
    "Separating": "←",
    "Static": "=",
}


SubjectLike = Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel]
LiteralReportKind = Literal[
    "subject",
    "single_chart",
    "dual_chart",
    "moon_phase_overview",
    "profections",
    "firdaria",
    "horary_indicators",
    "mutual_receptions",
    "dominants",
    "zodiacal_releasing",
]

# The horary model carries stable keys, not prose. These labels restate the
# FACT each key stands for and nothing else — the doctrinal reading travels
# in the model's own ``status`` field, so no tradition is asserted here.
HORARY_CONSIDERATION_LABELS = {
    "asc_early_degree": "Ascendant below 3°",
    "asc_late_degree": "Ascendant at or past 27°",
    "asc_judgeable": "Ascendant in the judgeable degrees",
    "moon_void": "Moon void of course",
    "moon_not_void": "Moon not void of course",
    "saturn_in_first": "Saturn in the 1st house",
    "saturn_in_seventh": "Saturn in the 7th house",
}

# Ordering constants for celestial point reports.
# Canonical definitions live in `kerykeion.settings.config_constants`; the module-private
# aliases below are kept so downstream code referring to them keeps working unchanged.
_MAIN_PLANETS = list(MAIN_PLANETS)
_NODES = list(LUNAR_NODES)
_ANGLES = list(AXIAL_POINTS)

# The Arabic Parts (lots). They are calculated points, not bodies, and get a
# table of their own for the same reason fixed stars and midpoints do — in the
# Celestial Points table they used to trail off the end unlabelled.
_LOTS = ["Pars_Fortunae", "Pars_Spiritus", "Pars_Amoris", "Pars_Fidei"]


def _humanize(name: str) -> str:
    """Replace underscores with spaces for display."""
    return name.replace("_", " ")


def _san(value: object) -> str:
    """Sanitize an untrusted subject-provided string for terminal-safe output.

    Strips XML-1.0-illegal / terminal-control characters (ESC, BEL, OSC, ...)
    so a birth ``name``/``city``/``nation`` cannot rewrite the window title,
    clear the screen, or drive OSC-52 clipboard writes. Ordinary printable
    content renders identically. Mirrors context_serializer's sanitization.
    """
    return strip_illegal_control_chars(value)


def _sign_emoji(emoji: str) -> str:
    """Zodiac sign emoji without the trailing VS16 variation selector.

    The sign emoji (e.g. '♋️' = U+264B + U+FE0F) carries a U+FE0F the ASCII-table
    width helper counts as one column, while a conformant terminal renders VS16
    as zero-width. Dropping it makes the reported width match the rendered width,
    so the Celestial Points / Houses tables' column separators line up.
    """
    return emoji.replace("️", "")


def _return_type_label(subject: object) -> str:
    """Human label for a return subject's return_type.

    Reuses the chart panel's mapping rather than deriving its own. Deriving from
    the enum agreed on three of the four types and produced "Lunar Node Crossing"
    where the chart says "Node Return" — the same chart, two names, depending on
    which surface the reader is looking at. The report has no i18n, so it takes
    the English defaults.

    No local guard for the missing or empty case: the mapping now falls through
    to the neutral "Return" itself. This function used to repeat that rule, and
    the copy quietly stopped agreeing — the mapping was returning the *lunar*
    label for a duck-typed subject, so the check here only looked like it was
    covering the case it named. One rule, one place, is what keeps it true.
    """
    _, english_label = return_label_keys(subject)
    return english_label


class ReportGenerator:
    """
    Generate textual reports for astrological data models with a structure that mirrors the
    chart-specific dispatch logic used in :class:`~kerykeion.charts.drawer.ChartDrawer`.

    The generator accepts any of the chart data models handled by ``ChartDrawer`` as well as
    raw ``AstrologicalSubjectModel`` instances. The ``print_report`` method automatically
    selects the appropriate layout and sections depending on the underlying chart type.
    """

    def __init__(
        self,
        model: Union[
            ChartDataModel,
            AstrologicalSubjectModel,
            MoonPhaseOverviewModel,
            ProfectionsModel,
            FirdariaModel,
            HoraryIndicatorsModel,
            MutualReceptionsModel,
            DominantsModel,
            ZodiacalReleasingModel,
        ],
        *,
        include_aspects: bool = True,
        max_aspects: Optional[int] = None,
    ) -> None:
        self.model = model
        self._include_aspects_default = include_aspects
        self._max_aspects_default = max_aspects

        self.chart_type: Optional[str] = None
        self._model_kind: LiteralReportKind
        self._chart_data: Optional[ChartDataModel] = None
        self._primary_subject: Optional[SubjectLike] = None
        self._secondary_subject: Optional[SubjectLike] = None
        self._active_points: list[str] = []
        self._active_aspects: list[dict] = []

        self._resolve_model()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def generate_report(
        self,
        *,
        include_aspects: Optional[bool] = None,
        max_aspects: Optional[int] = None,
    ) -> str:
        """
        Build the report content without printing it.

        Args:
            include_aspects: Override the default setting for including the aspects section.
            max_aspects: Override the default limit for the number of aspects displayed.
        """
        include_aspects = self._include_aspects_default if include_aspects is None else include_aspects
        max_aspects = self._max_aspects_default if max_aspects is None else max_aspects

        if self._model_kind == "moon_phase_overview":
            sections = self._build_moon_phase_overview_report()
        elif self._model_kind == "profections":
            sections = self._build_profections_report()
        elif self._model_kind == "firdaria":
            sections = self._build_firdaria_report()
        elif self._model_kind == "horary_indicators":
            sections = self._build_horary_indicators_report()
        elif self._model_kind == "mutual_receptions":
            sections = self._build_mutual_receptions_report()
        elif self._model_kind == "dominants":
            sections = self._build_dominants_report()
        elif self._model_kind == "zodiacal_releasing":
            sections = self._build_zodiacal_releasing_report()
        elif self._model_kind == "subject":
            sections = self._build_subject_report()
        elif self._model_kind == "single_chart":
            sections = self._build_single_chart_report(include_aspects=include_aspects, max_aspects=max_aspects)
        else:
            sections = self._build_dual_chart_report(include_aspects=include_aspects, max_aspects=max_aspects)

        title = self._build_title().strip("\n")
        full_sections = [title, *[section for section in sections if section]]
        return "\n\n".join(full_sections)

    def print_report(
        self,
        *,
        include_aspects: Optional[bool] = None,
        max_aspects: Optional[int] = None,
    ) -> None:
        """
        Print the generated report to stdout.
        """
        print(self.generate_report(include_aspects=include_aspects, max_aspects=max_aspects))

    # ------------------------------------------------------------------ #
    # Internal initialisation helpers
    # ------------------------------------------------------------------ #

    def _resolve_model(self) -> None:
        # Technique results are subject-less like the moon-phase overview: the
        # factory has already read the chart, and what survives is the
        # technique's own timeline. They carry no points and no aspects.
        standalone_kinds: tuple[tuple[type, LiteralReportKind, str], ...] = (
            (ProfectionsModel, "profections", "Profections"),
            (FirdariaModel, "firdaria", "Firdaria"),
            (HoraryIndicatorsModel, "horary_indicators", "HoraryIndicators"),
            (MutualReceptionsModel, "mutual_receptions", "MutualReceptions"),
            (DominantsModel, "dominants", "Dominants"),
            (ZodiacalReleasingModel, "zodiacal_releasing", "ZodiacalReleasing"),
        )

        if isinstance(self.model, MoonPhaseOverviewModel):
            self._model_kind = "moon_phase_overview"
            self.chart_type = "MoonPhaseOverview"
            self._primary_subject = None
            self._secondary_subject = None
            self._active_points = []
            self._active_aspects = []
        elif any(isinstance(self.model, model_type) for model_type, _, _ in standalone_kinds):
            # A plain for-loop, not ``next()`` over a generator expression: pyright
            # (1.1.408, the declared floor) widens the unpacked literal to ``str``
            # inside a genexpr, which then cannot be assigned to ``_model_kind``.
            # Unpacking in a real loop keeps the ``LiteralReportKind`` narrowing.
            for model_type, kind, chart_type in standalone_kinds:
                if isinstance(self.model, model_type):
                    self._model_kind = kind
                    self.chart_type = chart_type
                    break
            self._primary_subject = None
            self._secondary_subject = None
            self._active_points = []
            self._active_aspects = []
        elif isinstance(self.model, (AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel)):
            # Raw composite/return models are accepted like natal subjects:
            # every internal helper is SubjectLike-based, and to_context()
            # already takes them — the two entry points must agree.
            self._model_kind = "subject"
            self.chart_type = "Subject"
            self._primary_subject = self.model
            self._secondary_subject = None
            self._active_points = list(self.model.active_points)
            self._active_aspects = []
        elif isinstance(self.model, SingleChartDataModel):
            self._model_kind = "single_chart"
            self.chart_type = self.model.chart_type
            self._chart_data = self.model
            self._primary_subject = self.model.subject
            self._active_points = list(self.model.active_points)
            self._active_aspects = [dict(aspect) for aspect in self.model.active_aspects]
        elif isinstance(self.model, DualChartDataModel):
            self._model_kind = "dual_chart"
            self.chart_type = self.model.chart_type
            self._chart_data = self.model
            self._primary_subject = self.model.first_subject
            self._secondary_subject = self.model.second_subject
            self._active_points = list(self.model.active_points)
            self._active_aspects = [dict(aspect) for aspect in self.model.active_aspects]
        else:
            supported = (
                "AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel, "
                "SingleChartDataModel, DualChartDataModel, MoonPhaseOverviewModel, "
                "ProfectionsModel, FirdariaModel, HoraryIndicatorsModel, MutualReceptionsModel, "
                "DominantsModel, ZodiacalReleasingModel"
            )
            raise TypeError(f"Unsupported model type {type(self.model)!r}. Supported models: {supported}.")

    # ------------------------------------------------------------------ #
    # Report builders
    # ------------------------------------------------------------------ #

    def _build_subject_report(self) -> list[str]:
        assert self._primary_subject is not None
        sections = [
            self._subject_data_report(self._primary_subject, "Astrological Subject"),
            self._celestial_points_report(self._primary_subject, "Celestial Points"),
            self._lots_report(self._primary_subject, "Arabic Parts"),
            self._fixed_stars_report(self._primary_subject, "Fixed Stars"),
            self._midpoints_report(self._primary_subject, "Midpoints"),
            self._houses_report(self._primary_subject, "Houses"),
            self._dignities_report(self._primary_subject, "Essential Dignities"),
            self._nakshatra_report(self._primary_subject, "Nakshatras"),
            self._gauquelin_report(self._primary_subject, "Gauquelin Sectors"),
            self._lunar_phase_report(self._primary_subject),
        ]
        return sections

    def _build_moon_phase_overview_report(self) -> list[str]:
        """Build a detailed report from a MoonPhaseOverviewModel."""
        assert isinstance(self.model, MoonPhaseOverviewModel)
        overview = self.model
        sections: list[str] = []

        # -- Moon Summary --
        moon = overview.moon
        moon_data: list[list[str]] = [["Field", "Value"]]
        if moon.phase_name is not None:
            moon_data.append(["Phase Name", f"{moon.phase_name} {moon.emoji or ''}".strip()])
        if moon.major_phase is not None:
            moon_data.append(["Major Phase", moon.major_phase])
        if moon.stage is not None:
            moon_data.append(["Stage", moon.stage.capitalize()])
        if moon.illumination is not None:
            moon_data.append(["Illumination", moon.illumination])
        if moon.age_days is not None:
            moon_data.append(["Age (days)", str(moon.age_days)])
        if moon.age_days_precise is not None:
            moon_data.append(["Age (exact days)", f"{moon.age_days_precise:.4f}"])
        if moon.lunar_cycle is not None:
            moon_data.append(["Lunar Cycle", moon.lunar_cycle])
        if moon.zodiac is not None:
            moon_data.append(["Sun Sign", moon.zodiac.sun_sign])
            moon_data.append(["Moon Sign", moon.zodiac.moon_sign])
        if len(moon_data) > 1:
            sections.append(AsciiTable(moon_data, title="Moon Summary").table)

        # -- Illumination Details --
        if moon.detailed and moon.detailed.illumination_details:
            illum = moon.detailed.illumination_details
            illum_data: list[list[str]] = [["Field", "Value"]]
            if illum.percentage is not None:
                illum_data.append(["Percentage", f"{illum.percentage}%"])
            if illum.visible_fraction is not None:
                illum_data.append(["Visible Fraction", f"{illum.visible_fraction:.4f}"])
            if illum.phase_angle is not None:
                illum_data.append(["Phase Angle", f"{illum.phase_angle:.2f}°"])
            if len(illum_data) > 1:
                sections.append(AsciiTable(illum_data, title="Illumination Details").table)

        # -- Upcoming Phases --
        if moon.detailed and moon.detailed.upcoming_phases:
            phases = moon.detailed.upcoming_phases
            phases_data: list[list[str]] = [["Phase", "Last", "Next"]]
            for label, window in [
                ("New Moon", phases.new_moon),
                ("First Quarter", phases.first_quarter),
                ("Full Moon", phases.full_moon),
                ("Last Quarter", phases.last_quarter),
            ]:
                if window is not None:
                    last_str = window.last.datestamp if window.last and window.last.datestamp else "N/A"
                    next_str = window.next.datestamp if window.next and window.next.datestamp else "N/A"
                    phases_data.append([label, last_str, next_str])
            if len(phases_data) > 1:
                sections.append(AsciiTable(phases_data, title="Upcoming Phases").table)

        # -- Next Lunar Eclipse --
        if moon.next_lunar_eclipse:
            eclipse = moon.next_lunar_eclipse
            ecl_data: list[list[str]] = [["Field", "Value"]]
            if eclipse.datestamp:
                ecl_data.append(["Date", eclipse.datestamp])
            if eclipse.type:
                ecl_data.append(["Type", eclipse.type])
            if len(ecl_data) > 1:
                sections.append(AsciiTable(ecl_data, title="Next Lunar Eclipse").table)

        # -- Sun Info --
        sun = overview.sun
        if sun is not None:
            sun_data: list[list[str]] = [["Field", "Value"]]
            if sun.sunrise is not None:
                sun_data.append(["Sunrise", sun.sunrise.strftime("%H:%M")])
            if sun.sunset is not None:
                sun_data.append(["Sunset", sun.sunset.strftime("%H:%M")])
            if sun.solar_noon is not None:
                sun_data.append(["Solar Noon", sun.solar_noon.strftime("%H:%M")])
            if sun.day_length is not None:
                sun_data.append(["Day Length", format_timedelta_hhmm(sun.day_length)])
            if sun.position is not None:
                if sun.position.altitude is not None:
                    sun_data.append(["Sun Altitude", f"{sun.position.altitude:.2f}°"])
                if sun.position.azimuth is not None:
                    sun_data.append(["Sun Azimuth", f"{sun.position.azimuth:.2f}°"])
            if len(sun_data) > 1:
                sections.append(AsciiTable(sun_data, title="Sun Info").table)

            # -- Next Solar Eclipse --
            if sun.next_solar_eclipse:
                se = sun.next_solar_eclipse
                se_data: list[list[str]] = [["Field", "Value"]]
                if se.datestamp:
                    se_data.append(["Date", se.datestamp])
                if se.type:
                    se_data.append(["Type", se.type])
                if len(se_data) > 1:
                    sections.append(AsciiTable(se_data, title="Next Solar Eclipse").table)

        # -- Location --
        loc = overview.location
        if loc is not None:
            loc_data: list[list[str]] = [["Field", "Value"]]
            if loc.latitude is not None:
                loc_data.append(["Latitude", loc.latitude])
            if loc.longitude is not None:
                loc_data.append(["Longitude", loc.longitude])
            if loc.using_default_location is not None:
                loc_data.append(["Default Location", "Yes" if loc.using_default_location else "No"])
            if len(loc_data) > 1:
                sections.append(AsciiTable(loc_data, title="Location").table)

        return sections

    def _build_profections_report(self) -> list[str]:
        """Build a report from a ProfectionsModel."""
        assert isinstance(self.model, ProfectionsModel)
        profections = self.model
        current = profections.current

        summary = [
            ["Field", "Value"],
            ["Age", str(current.age)],
            ["Profected House", str(current.house)],
            ["Sign", str(current.sign)],
            ["Lord of the Year", _humanize(str(current.lord))],
            ["Year Begins", current.year_start],
            ["Year Ends", current.year_end],
        ]
        sections = [AsciiTable(summary, title="Current Profection Year").table]

        if profections.years:
            years_data: list[list[str]] = [["", "Age", "House", "Sign", "Lord", "Begins", "Ends"]]
            for year in profections.years:
                years_data.append(
                    [
                        "*" if year.age == current.age else "",
                        str(year.age),
                        str(year.house),
                        str(year.sign),
                        _humanize(str(year.lord)),
                        year.year_start,
                        year.year_end,
                    ]
                )
            sections.append(AsciiTable(years_data, title="Profection Years").table)

        return sections

    def _build_firdaria_report(self) -> list[str]:
        """Build a report from a FirdariaModel."""
        assert isinstance(self.model, FirdariaModel)
        firdaria = self.model

        summary = [
            ["Field", "Value"],
            ["Sect", "Diurnal" if firdaria.is_diurnal else "Nocturnal"],
        ]
        if firdaria.current is not None:
            summary.append(["Current Lord", _humanize(str(firdaria.current.lord))])
            summary.append(["Ages", f"{firdaria.current.age_start}–{firdaria.current.age_end}"])
        if firdaria.current_sub is not None:
            summary.append(["Current Sub-Lord", _humanize(str(firdaria.current_sub.lord))])
        sections = [AsciiTable(summary, title="Firdaria Summary").table]

        if firdaria.periods:
            periods_data: list[list[str]] = [["", "Lord", "Years", "Ages", "Begins", "Ends"]]
            current_start = firdaria.current.start if firdaria.current is not None else None
            for period in firdaria.periods:
                periods_data.append(
                    [
                        "*" if period.start == current_start else "",
                        _humanize(str(period.lord)),
                        str(period.years),
                        f"{period.age_start}–{period.age_end}",
                        period.start,
                        period.end,
                    ]
                )
            sections.append(AsciiTable(periods_data, title="Firdaria Periods").table)

        # Only the running period's sub-lords: unrolling all of them would bury
        # the timeline under seven rows per period for no added meaning.
        if firdaria.current is not None and firdaria.current.sub_periods:
            current_sub_start = firdaria.current_sub.start if firdaria.current_sub is not None else None
            sub_data: list[list[str]] = [["", "Sub-Lord", "Begins", "Ends"]]
            for sub_period in firdaria.current.sub_periods:
                sub_data.append(
                    [
                        "*" if sub_period.start == current_sub_start else "",
                        _humanize(str(sub_period.lord)),
                        sub_period.start,
                        sub_period.end,
                    ]
                )
            title = f"Sub-Periods of the {_humanize(str(firdaria.current.lord))} Period"
            sections.append(AsciiTable(sub_data, title=title).table)

        return sections

    def _build_horary_indicators_report(self) -> list[str]:
        """Build a report from a HoraryIndicatorsModel."""
        assert isinstance(self.model, HoraryIndicatorsModel)
        indicators = self.model

        significator_data: list[list[str]] = [
            ["Role", "House", "Sign", "Ruler", "Ruler Sign", "Ruler House", "Dignity", "Ret."]
        ]
        for role, significator in (("Querent", indicators.querent), ("Quesited", indicators.quesited)):
            significator_data.append(
                [
                    role,
                    str(significator.house),
                    str(significator.sign) if significator.sign else "-",
                    _humanize(str(significator.ruler)) if significator.ruler else "-",
                    str(significator.ruler_sign) if significator.ruler_sign else "-",
                    str(significator.ruler_house_number) if significator.ruler_house_number else "-",
                    str(significator.essential_dignity) if significator.essential_dignity else "-",
                    "R" if significator.ruler_retrograde else "-",
                ]
            )
        sections = [AsciiTable(significator_data, title="Significators").table]

        if indicators.ascendant_degree is not None:
            ascendant_data = [
                ["Field", "Value"],
                ["Ascendant Degree", f"{indicators.ascendant_degree:.2f}°"],
            ]
            sections.append(AsciiTable(ascendant_data, title="Ascendant").table)

        if indicators.considerations:
            considerations_data: list[list[str]] = [["Consideration", "Status"]]
            for consideration in indicators.considerations:
                label = HORARY_CONSIDERATION_LABELS.get(consideration.key, _humanize(consideration.key))
                considerations_data.append([label, str(consideration.status).capitalize()])
            sections.append(AsciiTable(considerations_data, title="Considerations Before Judgment").table)

        receptions_table = self._receptions_table(indicators.mutual_receptions)
        if receptions_table:
            sections.append(receptions_table)

        return sections

    def _build_mutual_receptions_report(self) -> list[str]:
        """Build a report from a MutualReceptionsModel."""
        assert isinstance(self.model, MutualReceptionsModel)
        table = self._receptions_table(self.model.receptions)
        if not table:
            return ["No mutual receptions between the classical planets."]
        return [table]

    def _build_dominants_report(self) -> list[str]:
        """Build a report from a DominantsModel."""
        assert isinstance(self.model, DominantsModel)
        dominants = self.model

        summary: list[list[str]] = [["Field", "Value"], ["Strategy", _humanize(dominants.strategy_name)]]
        if dominants.method:
            summary.append(["Method", _humanize(str(dominants.method))])
        for label, winner in (
            ("Dominant Planet", dominants.dominant_planet),
            ("Dominant Sign", dominants.dominant_sign),
            ("Dominant Element", dominants.dominant_element),
            ("Dominant Quality", dominants.dominant_quality),
            ("Dominant House", dominants.dominant_house),
        ):
            if winner:
                summary.append([label, _humanize(str(winner))])
        sections = [AsciiTable(summary, title="Dominants Summary").table]

        # Every category is always present on the model; a school that does not
        # compute one leaves it empty, so render only what was actually scored.
        for title, entries in (
            ("Planets", dominants.planets),
            ("Signs", dominants.signs),
            ("Elements", dominants.elements),
            ("Qualities", dominants.qualities),
            ("Houses", dominants.houses),
            ("Polarities", dominants.polarities),
            ("Hemispheres", dominants.hemispheres),
            ("Quadrants", dominants.quadrants),
        ):
            table = self._dominant_category_table(entries, title)
            if table:
                sections.append(table)

        return sections

    @staticmethod
    def _dominant_category_table(entries: Sequence[DominantScoreModel], title: str) -> str:
        """One ranked dominant category; empty string when the school skipped it."""
        if not entries:
            return ""

        category_data: list[list[str]] = [["Rank", "Name", "Score", "Share"]]
        for entry in entries:
            percentage = getattr(entry, "percentage", None)
            category_data.append(
                [
                    str(getattr(entry, "rank", "-")),
                    _humanize(str(entry.name)),
                    f"{entry.score:.2f}",
                    f"{percentage:.1f}%" if percentage is not None else "-",
                ]
            )
        return AsciiTable(category_data, title=f"Dominant {title}").table

    def _build_zodiacal_releasing_report(self) -> list[str]:
        """Build a report from a ZodiacalReleasingModel."""
        assert isinstance(self.model, ZodiacalReleasingModel)
        releasing = self.model

        summary = [
            ["Field", "Value"],
            ["Lot", releasing.lot.capitalize()],
            ["Lot Sign", str(releasing.lot_sign)],
            ["Lot Degree", f"{format_degrees_below_bound(releasing.lot_degree, 360.0)}°"],
        ]
        # Short on purpose: AsciiTable DROPS a title wider than the table, and
        # the banner above already names the technique and the lot.
        sections = [AsciiTable(summary, title="Releasing Summary").table]

        if releasing.periods:
            sections.append(self._zr_periods_table(releasing.periods, "Level 1 Periods"))

        # The chain of periods active at the target date, one row per level —
        # the answer to "where am I now" that the nested tree makes hard to read.
        if releasing.current_path:
            sections.append(self._zr_periods_table(releasing.current_path, "Current Period Chain"))

        return sections

    @staticmethod
    def _zr_periods_table(periods: Sequence[ZRPeriodModel], title: str) -> str:
        """Render zodiacal-releasing periods, flagging peak and bond-loosing ones."""
        if not periods:
            return ""

        period_data: list[list[str]] = [["Level", "Sign", "Ruler", "Years", "Begins", "Ends", "Peak", "LB"]]
        for period in periods:
            period_data.append(
                [
                    f"L{period.level}",
                    str(period.sign),
                    _humanize(str(period.ruler)) if period.ruler else "-",
                    f"{period.years:.2f}",
                    period.start,
                    period.end,
                    "*" if period.is_angular else "",
                    "*" if period.is_loosing_the_bond else "",
                ]
            )
        return AsciiTable(period_data, title=title).table

    @staticmethod
    def _receptions_table(receptions: Sequence[MutualReceptionModel]) -> str:
        """Render mutual receptions; empty string when the chart has none."""
        if not receptions:
            return ""

        reception_data: list[list[str]] = [["First Planet", "Second Planet", "Type"]]
        for reception in receptions:
            reception_data.append(
                [
                    _humanize(str(reception.first_planet)),
                    _humanize(str(reception.second_planet)),
                    str(reception.reception_type).capitalize(),
                ]
            )
        return AsciiTable(reception_data, title="Mutual Receptions").table

    def _build_single_chart_report(self, *, include_aspects: bool, max_aspects: Optional[int]) -> list[str]:
        assert isinstance(self._chart_data, SingleChartDataModel)
        assert self._primary_subject is not None
        chart_data = self._chart_data
        sections: list[str] = [
            self._subject_data_report(self._primary_subject, self._primary_subject_label()),
        ]

        if isinstance(self._primary_subject, CompositeSubjectModel):
            sections.append(
                self._subject_data_report(
                    self._primary_subject.first_subject,
                    "Composite – First Subject",
                )
            )
            sections.append(
                self._subject_data_report(
                    self._primary_subject.second_subject,
                    "Composite – Second Subject",
                )
            )

        sections.extend(
            [
                self._celestial_points_report(
                    self._primary_subject, f"{self._primary_subject_label()} Celestial Points"
                ),
                self._lots_report(self._primary_subject, f"{self._primary_subject_label()} Arabic Parts"),
                self._fixed_stars_report(self._primary_subject, f"{self._primary_subject_label()} Fixed Stars"),
                self._midpoints_report(self._primary_subject, f"{self._primary_subject_label()} Midpoints"),
                self._houses_report(self._primary_subject, f"{self._primary_subject_label()} Houses"),
                self._dignities_report(
                    self._primary_subject, f"{self._primary_subject_label()} Essential Dignities"
                ),
                self._nakshatra_report(self._primary_subject, f"{self._primary_subject_label()} Nakshatras"),
                self._gauquelin_report(
                    self._primary_subject, f"{self._primary_subject_label()} Gauquelin Sectors"
                ),
                self._lunar_phase_report(self._primary_subject),
                self._elements_report(),
                self._qualities_report(),
                self._angularities_report(chart_data.angularities, "Angularities"),
                self._stelliums_report(chart_data.stelliums, "Stelliums"),
                self._active_configuration_report(),
            ]
        )

        if include_aspects:
            sections.append(self._aspects_report(max_aspects=max_aspects))

        return sections

    def _build_dual_chart_report(self, *, include_aspects: bool, max_aspects: Optional[int]) -> list[str]:
        assert isinstance(self._chart_data, DualChartDataModel)
        assert self._primary_subject is not None
        chart_data = self._chart_data
        primary_label, secondary_label = self._subject_role_labels()

        sections: list[str] = [
            self._subject_data_report(self._primary_subject, primary_label),
        ]

        if self._secondary_subject is not None:
            sections.append(self._subject_data_report(self._secondary_subject, secondary_label))

        sections.extend(
            [
                self._celestial_points_report(self._primary_subject, f"{primary_label} Celestial Points"),
                self._lots_report(self._primary_subject, f"{primary_label} Arabic Parts"),
                self._fixed_stars_report(self._primary_subject, f"{primary_label} Fixed Stars"),
                self._midpoints_report(self._primary_subject, f"{primary_label} Midpoints"),
            ]
        )

        if self._secondary_subject is not None:
            sections.append(
                self._celestial_points_report(self._secondary_subject, f"{secondary_label} Celestial Points")
            )
            sections.append(self._lots_report(self._secondary_subject, f"{secondary_label} Arabic Parts"))
            sections.append(self._fixed_stars_report(self._secondary_subject, f"{secondary_label} Fixed Stars"))
            sections.append(self._midpoints_report(self._secondary_subject, f"{secondary_label} Midpoints"))

        sections.append(self._houses_report(self._primary_subject, f"{primary_label} Houses"))

        if self._secondary_subject is not None:
            sections.append(self._houses_report(self._secondary_subject, f"{secondary_label} Houses"))

        sections.append(self._dignities_report(self._primary_subject, f"{primary_label} Essential Dignities"))
        sections.append(self._nakshatra_report(self._primary_subject, f"{primary_label} Nakshatras"))
        sections.append(self._gauquelin_report(self._primary_subject, f"{primary_label} Gauquelin Sectors"))

        if self._secondary_subject is not None:
            sections.append(
                self._dignities_report(self._secondary_subject, f"{secondary_label} Essential Dignities")
            )
            sections.append(self._nakshatra_report(self._secondary_subject, f"{secondary_label} Nakshatras"))
            sections.append(
                self._gauquelin_report(self._secondary_subject, f"{secondary_label} Gauquelin Sectors")
            )

        sections.extend(
            [
                self._lunar_phase_report(self._primary_subject),
                self._elements_report(),
                self._qualities_report(),
                # Per subject, and labelled with the same role names the
                # Celestial Points and Houses tables above already use.
                self._angularities_report(
                    chart_data.first_subject_angularities, f"{primary_label} Angularities"
                ),
                self._stelliums_report(chart_data.first_subject_stelliums, f"{primary_label} Stelliums"),
                self._angularities_report(
                    chart_data.second_subject_angularities, f"{secondary_label} Angularities"
                ),
                self._stelliums_report(chart_data.second_subject_stelliums, f"{secondary_label} Stelliums"),
                self._house_comparison_report(),
                self._relationship_score_report(),
                self._active_configuration_report(),
            ]
        )

        if include_aspects:
            sections.append(self._aspects_report(max_aspects=max_aspects))

        return sections

    # ------------------------------------------------------------------ #
    # Section helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _banner(base_title: str) -> str:
        separator = "=" * len(base_title)
        return f"\n{separator}\n{base_title}\n{separator}\n"

    def _build_title(self) -> str:
        if self._model_kind == "moon_phase_overview":
            assert isinstance(self.model, MoonPhaseOverviewModel)
            return self._banner(f"Moon Phase Overview — {self.model.datestamp}")

        if self._model_kind == "profections":
            assert isinstance(self.model, ProfectionsModel)
            return self._banner(f"Annual Profections — Age {self.model.current.age}")

        if self._model_kind == "firdaria":
            assert isinstance(self.model, FirdariaModel)
            sect = "Day" if self.model.is_diurnal else "Night"
            return self._banner(f"Firdaria — {sect} Chart")

        if self._model_kind == "horary_indicators":
            return self._banner("Horary Indicators")

        if self._model_kind == "mutual_receptions":
            return self._banner("Mutual Receptions")

        if self._model_kind == "dominants":
            assert isinstance(self.model, DominantsModel)
            return self._banner(f"Chart Dominants — {_humanize(self.model.strategy_name)}")

        if self._model_kind == "zodiacal_releasing":
            assert isinstance(self.model, ZodiacalReleasingModel)
            return self._banner(f"Zodiacal Releasing — Lot of {self.model.lot.capitalize()}")

        assert self._primary_subject is not None

        # Subject name is untrusted free text: strip terminal-control chars so it
        # cannot rewrite the window title / clear the screen when the report is
        # printed. Done before the separator is sized so the underline width
        # matches the visible title.
        primary_name = _san(self._primary_subject.name)

        if self._model_kind == "subject":
            base_title = f"{primary_name} — Subject Report"
        elif self.chart_type == "Natal":
            base_title = f"{primary_name} — Natal Chart Report"
        elif self.chart_type == "Composite":
            if isinstance(self._primary_subject, CompositeSubjectModel):
                first = _san(self._primary_subject.first_subject.name)
                second = _san(self._primary_subject.second_subject.name)
                base_title = f"{first} & {second} — Composite Report"
            else:
                base_title = f"{primary_name} — Composite Report"
        elif self.chart_type == "SingleReturnChart":
            year = self._extract_year(self._primary_subject.iso_formatted_local_datetime)
            label = _return_type_label(self._primary_subject)
            base_title = f"{primary_name} — {label} {year or ''}".strip()
        elif self.chart_type == "Transit":
            date_str = self._format_date_iso(
                self._secondary_subject.iso_formatted_local_datetime if self._secondary_subject else None
            )
            base_title = f"{primary_name} — Transit {date_str}".strip()
        elif self.chart_type == "Synastry":
            second_name = _san(self._secondary_subject.name) if self._secondary_subject is not None else "Unknown"
            base_title = f"{primary_name} & {second_name} — Synastry Report"
        elif self.chart_type == "DualReturnChart":
            year = self._extract_year(
                self._secondary_subject.iso_formatted_local_datetime if self._secondary_subject else None
            )
            label = _return_type_label(self._secondary_subject)
            base_title = f"{primary_name} — {label} Comparison {year or ''}".strip()
        elif self.chart_type == "Progression":
            # The progressed subject's iso datetime is the INTERNAL day-for-a-year
            # ephemeris instant (~a few weeks after birth), not the target year
            # the user progressed to — showing it in the title is misleading, and
            # the target year isn't stored on the model. The progressed subject's
            # name already carries "(Progressed YYYY-MM-DD)", so title by name.
            base_title = f"{primary_name} — Secondary Progression".strip()
        else:
            base_title = f"{primary_name} — Chart Report"

        return self._banner(base_title)

    def _primary_subject_label(self) -> str:
        if self.chart_type == "Composite":
            return "Composite Chart"
        if self.chart_type == "SingleReturnChart":
            return f"{_return_type_label(self._primary_subject)} Chart"
        return f"{self.chart_type or 'Chart'}"

    def _subject_role_labels(self) -> tuple[str, str]:
        if self.chart_type == "Transit":
            return "Natal Subject", "Transit Subject"
        if self.chart_type == "Synastry":
            return "First Subject", "Second Subject"
        if self.chart_type == "DualReturnChart":
            return "Natal Subject", "Return Subject"
        if self.chart_type == "Progression":
            return "Natal Subject", "Progressed Subject"
        return "Primary Subject", "Secondary Subject"

    def _subject_data_report(self, subject: SubjectLike, label: str) -> str:
        # name/city/nation are untrusted free text: strip terminal-control chars
        # (ESC/BEL/OSC) before they reach stdout. Printable content is unchanged.
        birth_data = [["Field", "Value"], ["Name", _san(subject.name)]]

        if isinstance(subject, CompositeSubjectModel):
            composite_members = f"{_san(subject.first_subject.name)} & {_san(subject.second_subject.name)}"
            birth_data.append(["Composite Members", composite_members])
            birth_data.append(["Composite Type", subject.composite_chart_type])

        if isinstance(subject, PlanetReturnModel):
            birth_data.append(["Return Type", subject.return_type])

        if isinstance(subject, AstrologicalSubjectModel):
            birth_data.append(["Date", f"{subject.day:02d}/{subject.month:02d}/{subject.year}"])
            birth_data.append(["Time", f"{subject.hour:02d}:{subject.minute:02d}"])

        city = getattr(subject, "city", None)
        if city:
            birth_data.append(["City", _san(city)])

        nation = getattr(subject, "nation", None)
        if nation:
            birth_data.append(["Nation", _san(nation)])

        lat = getattr(subject, "lat", None)
        if lat is not None:
            birth_data.append(["Latitude", f"{lat:.4f}°"])

        lng = getattr(subject, "lng", None)
        if lng is not None:
            birth_data.append(["Longitude", f"{lng:.4f}°"])

        tz_str = getattr(subject, "tz_str", None)
        if tz_str:
            birth_data.append(["Timezone", str(tz_str)])

        day_of_week = getattr(subject, "day_of_week", None)
        if day_of_week:
            birth_data.append(["Day of Week", str(day_of_week)])

        iso_local = getattr(subject, "iso_formatted_local_datetime", None)
        if iso_local:
            birth_data.append(["ISO Local Datetime", iso_local])

        # Whether the Sun stood above or below the horizon, on the same rule the
        # chart panel uses — shared as ``subject_states_a_diurnality`` so the two
        # cannot drift. The report has no ``show_diurnality`` equivalent, so a
        # caller who switches the chart's line off still gets it here.
        if subject_states_a_diurnality(subject):
            birth_data.append(["Diurnality", "Diurnal" if subject.is_diurnal else "Nocturnal"])

        settings_data = [["Setting", "Value"]]
        settings_data.append(["Zodiac Type", str(subject.zodiac_type)])
        if getattr(subject, "sidereal_mode", None):
            settings_data.append(["Sidereal Mode", str(subject.sidereal_mode)])
        # The system actually used, so a polar chart is not tabulated as the
        # one that was asked for but could not be cast.
        settings_data.append(["Houses System", str(subject.effective_houses_system_name)])
        settings_data.append(["Perspective Type", str(subject.perspective_type)])

        julian_day = getattr(subject, "julian_day", None)
        if julian_day is not None:
            settings_data.append(["Julian Day", f"{julian_day:.6f}"])

        active_points = getattr(subject, "active_points", None)
        if active_points:
            settings_data.append(["Active Points Count", str(len(active_points))])

        birth_table = AsciiTable(birth_data, title=f"{label} — Birth Data").table
        settings_table = AsciiTable(settings_data, title=f"{label} — Settings").table
        return f"{birth_table}\n\n{settings_table}"

    def _celestial_points_report(self, subject: SubjectLike, title: str) -> str:
        points = [
            point for point in self._collect_celestial_points(subject) if str(point.name) not in _LOTS
        ]
        if not points:
            return "No celestial points data available."

        ordered_names = set(_ANGLES + _MAIN_PLANETS + _NODES)
        grouped_points: dict[str, list] = {}
        remaining_points: list = []
        for point in points:
            if point.name in ordered_names:
                grouped_points.setdefault(point.name, []).append(point)
            else:
                remaining_points.append(point)

        sorted_points: list = []
        for name in _ANGLES + _MAIN_PLANETS + _NODES:
            sorted_points.extend(grouped_points.get(name, []))
        sorted_points.extend(remaining_points)

        return self._points_table(sorted_points, title)

    def _lots_report(self, subject: SubjectLike, title: str) -> str:
        """Render the active Arabic Parts; empty string when none are active."""
        by_name = {str(point.name): point for point in self._collect_celestial_points(subject)}
        lots = [by_name[name] for name in _LOTS if name in by_name]
        if not lots:
            return ""
        return self._points_table(lots, title)

    def _dignities_report(self, subject: SubjectLike, title: str) -> str:
        """Essential dignities; empty string unless the chart computed them."""
        points = [
            point
            for point in self._collect_celestial_points(subject)
            if getattr(point, "essential_dignity", None)
        ]
        if not points:
            return ""

        dignity_data: list[list[str]] = [["Point", "Sign", "Dignity"]]
        for point in points:
            dignity_data.append(
                [
                    _humanize(str(point.name)),
                    f"{point.sign} {_sign_emoji(point.emoji)}",
                    str(point.essential_dignity),
                ]
            )
        return AsciiTable(dignity_data, title=title).table

    def _nakshatra_report(self, subject: SubjectLike, title: str) -> str:
        """Vedic lunar mansions; empty string unless the chart computed them."""
        points = [
            point for point in self._collect_celestial_points(subject) if getattr(point, "nakshatra", None)
        ]
        if not points:
            return ""

        nakshatra_data: list[list[str]] = [["Point", "Nakshatra", "#", "Pada", "Lord"]]
        for point in points:
            number = getattr(point, "nakshatra_number", None)
            pada = getattr(point, "nakshatra_pada", None)
            lord = getattr(point, "nakshatra_lord", None)
            nakshatra_data.append(
                [
                    _humanize(str(point.name)),
                    str(point.nakshatra),
                    str(number) if number is not None else "-",
                    str(pada) if pada is not None else "-",
                    _humanize(str(lord)) if lord else "-",
                ]
            )
        return AsciiTable(nakshatra_data, title=title).table

    def _gauquelin_report(self, subject: SubjectLike, title: str) -> str:
        """Gauquelin 36-sector positions; empty string unless computed."""
        points = [
            point
            for point in self._collect_celestial_points(subject)
            if getattr(point, "gauquelin_sector", None) is not None
        ]
        if not points:
            return ""

        gauquelin_data: list[list[str]] = [["Point", "Sector"]]
        for point in points:
            gauquelin_data.append([_humanize(str(point.name)), f"{point.gauquelin_sector:.2f}"])
        return AsciiTable(gauquelin_data, title=title).table

    def _points_table(
        self,
        points: Sequence[KerykeionPointModel],
        title: str,
        *,
        constellations: Optional[Mapping[str, str]] = None,
    ) -> str:
        """Render a table of points, widening only for data that is present.

        Every optional column follows the rule the magnitude column has always
        followed: it appears only when at least one row can fill it. A chart
        that computes none of them keeps the original seven-column layout, so
        adding columns here cannot reshape reports that have no such data.
        """
        show_mag = any(getattr(point, "magnitude", None) is not None for point in points)
        show_motion = any(getattr(point, "motion_state", None) is not None for point in points)
        # Only when a point IS out of bounds: a column of "-" states nothing the
        # reader did not already know, and out-of-bounds is the exception.
        show_oob = any(getattr(point, "is_out_of_bounds", None) for point in points)
        show_constellation = bool(constellations)

        header: list[str] = ["Point"]
        if show_constellation:
            header.append("Constellation")
        header.extend(["Sign", "Position"])
        if show_mag:
            header.append("Mag.")
        header.append("Speed")
        if show_motion:
            header.append("Motion")
        header.append("Decl.")
        if show_oob:
            header.append("OOB")
        header.extend(["Ret.", "House"])

        celestial_data: list[list[str]] = [header]
        for point in points:
            name = str(point.name)
            row: list[str] = [_humanize(name)]
            if show_constellation:
                row.append((constellations or {}).get(name, "-"))
            row.append(f"{point.sign} {_sign_emoji(point.emoji)}")
            row.append(f"{format_degrees_below_bound(point.position, 30.0)}°")
            if show_mag:
                mag = getattr(point, "magnitude", None)
                row.append(f"{mag:+.2f}" if mag is not None else "N/A")
            row.append(f"{point.speed:+.4f}°/d" if point.speed is not None else "N/A")
            if show_motion:
                motion = getattr(point, "motion_state", None)
                row.append(str(motion).capitalize() if motion else "-")
            row.append(f"{point.declination:+.2f}°" if point.declination is not None else "N/A")
            if show_oob:
                row.append("Y" if getattr(point, "is_out_of_bounds", None) else "-")
            row.append("R" if point.retrograde else "-")
            row.append(_humanize(point.house) if point.house else "-")
            celestial_data.append(row)

        return AsciiTable(celestial_data, title=title).table

    def _fixed_stars_report(self, subject: SubjectLike, title: str) -> str:
        """Render the v6 ``subject.fixed_stars`` array; empty string when no star is active."""
        stars = list(getattr(subject, "fixed_stars", None) or [])
        if not stars:
            return ""
        # The constellation is catalog metadata, not a field of the point model:
        # look it up per star so the table can name the sky region it belongs to.
        constellations: dict[str, str] = {}
        for star in stars:
            metadata = FixedStarCatalog.find(str(star.name))
            if metadata is not None and metadata.constellation:
                constellations[str(star.name)] = metadata.constellation
        return self._points_table(stars, title, constellations=constellations)

    def _midpoints_report(self, subject: SubjectLike, title: str) -> str:
        """Render the v6 ``subject.active_midpoints`` array; empty string when none are active."""
        midpoints = list(getattr(subject, "active_midpoints", None) or [])
        if not midpoints:
            return ""
        return self._points_table(midpoints, title)

    def _collect_celestial_points(self, subject: SubjectLike) -> list[KerykeionPointModel]:
        if isinstance(subject, AstrologicalSubjectModel):
            return get_available_astrological_points_list(subject)

        points: list[KerykeionPointModel] = []
        active_points: Optional[Sequence[str]] = getattr(subject, "active_points", None)
        if not active_points:
            return points

        for point_name in active_points:
            attr_name = str(point_name).lower()
            attr = getattr(subject, attr_name, None)
            if attr is not None:
                points.append(attr)

        return points

    def _houses_report(self, subject: SubjectLike, title: str) -> str:
        try:
            houses = get_houses_list(subject)  # type: ignore[arg-type]
        except Exception:
            return "No houses data available."

        if not houses:
            return "No houses data available."

        houses_data: list[list[str]] = [["House", "Sign", "Position", "Absolute Position"]]
        for house in houses:
            houses_data.append(
                [
                    _humanize(house.name),
                    f"{house.sign} {_sign_emoji(house.emoji)}",
                    f"{format_degrees_below_bound(house.position, 30.0)}°",
                    f"{format_degrees_below_bound(house.abs_pos, 360.0)}°",
                ]
            )

        # Effective, so the houses table title cannot disagree with the
        # settings row above it in the same report.
        system_name = getattr(subject, "effective_houses_system_name", "") or getattr(subject, "houses_system_name", "")
        table_title = f"{title} ({system_name})" if system_name else title
        return AsciiTable(houses_data, title=table_title).table

    def _lunar_phase_report(self, subject: SubjectLike) -> str:
        lunar = getattr(subject, "lunar_phase", None)
        if not lunar:
            return ""

        lunar_data = [
            ["Lunar Phase Information", "Value"],
            ["Phase Name", f"{lunar.moon_phase_name} {lunar.moon_emoji}"],
            ["Sun-Moon Angle", f"{lunar.degrees_between_s_m:.2f}°"],
            ["Lunation Day", str(lunar.moon_phase)],
        ]
        return AsciiTable(lunar_data, title="Lunar Phase").table

    def _elements_report(self) -> str:
        if not self._chart_data or not getattr(self._chart_data, "element_distribution", None):
            return ""

        elem = self._chart_data.element_distribution
        total = elem.fire + elem.earth + elem.air + elem.water
        if total == 0:
            return ""

        element_data = [
            ["Element", "Count", "Percentage"],
            ["Fire 🔥", elem.fire, f"{elem.fire_percentage}%"],
            ["Earth 🌍", elem.earth, f"{elem.earth_percentage}%"],
            ["Air 💨", elem.air, f"{elem.air_percentage}%"],
            ["Water 💧", elem.water, f"{elem.water_percentage}%"],
            ["Total", total, "100%"],
        ]
        return AsciiTable(element_data, title="Element Distribution").table

    def _qualities_report(self) -> str:
        if not self._chart_data or not getattr(self._chart_data, "quality_distribution", None):
            return ""

        qual = self._chart_data.quality_distribution
        total = qual.cardinal + qual.fixed + qual.mutable
        if total == 0:
            return ""

        quality_data = [
            ["Quality", "Count", "Percentage"],
            ["Cardinal", qual.cardinal, f"{qual.cardinal_percentage}%"],
            ["Fixed", qual.fixed, f"{qual.fixed_percentage}%"],
            ["Mutable", qual.mutable, f"{qual.mutable_percentage}%"],
            ["Total", total, "100%"],
        ]
        return AsciiTable(quality_data, title="Quality Distribution").table

    @staticmethod
    def _angularities_report(angularities: Sequence[AngularityModel], title: str) -> str:
        """Planets standing on an angle. Empty string when the chart has none."""
        if not angularities:
            return ""

        angularity_data: list[list[str]] = [["Point", "Angle", "Distance"]]
        for item in angularities:
            angularity_data.append(
                [
                    _humanize(item.point),
                    _humanize(item.angle),
                    f"{item.distance:.2f}°",
                ]
            )
        return AsciiTable(angularity_data, title=title).table

    @staticmethod
    def _stelliums_report(stelliums: Sequence[StelliumModel], title: str) -> str:
        """Houses holding a cluster of planets. Empty string when the chart has none."""
        if not stelliums:
            return ""

        stellium_data: list[list[str]] = [["House", "Count", "Points"]]
        for item in stelliums:
            stellium_data.append(
                [
                    str(item.house),
                    str(len(item.points)),
                    ", ".join(_humanize(point) for point in item.points),
                ]
            )
        return AsciiTable(stellium_data, title=title).table

    def _active_configuration_report(self) -> str:
        if not self._active_points and not self._active_aspects:
            return ""

        sections: list[str] = []

        if self._active_points:
            points_table = [["#", "Active Point"]]
            for idx, point in enumerate(self._active_points, start=1):
                points_table.append([str(idx), str(point)])
            sections.append(AsciiTable(points_table, title="Active Celestial Points").table)

        if self._active_aspects:
            aspects_table = [["Aspect", "Orb (°)"]]
            for aspect in self._active_aspects:
                name = str(aspect.get("name", ""))
                orb = aspect.get("orb")
                orbit_str = f"{orb}" if orb is not None else "-"
                aspects_table.append([name, orbit_str])
            sections.append(AsciiTable(aspects_table, title="Active Aspects Configuration").table)

        return "\n\n".join(sections)

    def _aspects_report(self, *, max_aspects: Optional[int]) -> str:
        if not self._chart_data or not getattr(self._chart_data, "aspects", None):
            return ""

        aspects_list = list(self._chart_data.aspects)

        if not aspects_list:
            return "No aspects data available."

        total_aspects = len(aspects_list)
        if max_aspects is not None:
            aspects_list = aspects_list[:max_aspects]

        is_dual = isinstance(self._chart_data, DualChartDataModel)
        if is_dual:
            table_header: list[str] = ["Point 1", "Owner 1", "Aspect", "Point 2", "Owner 2", "Orb", "Movement"]
        else:
            table_header = ["Point 1", "Aspect", "Point 2", "Orb", "Movement"]

        aspects_table: list[list[str]] = [table_header]
        for aspect in aspects_list:
            aspect_name = str(aspect.aspect)
            symbol = ASPECT_SYMBOLS.get(aspect_name.lower(), "")
            movement_symbol = MOVEMENT_SYMBOLS.get(aspect.aspect_movement, "")
            movement = f"{aspect.aspect_movement} {movement_symbol}".strip()

            if is_dual:
                aspects_table.append(
                    [
                        _humanize(aspect.p1_name),
                        _san(aspect.p1_owner),
                        f"{aspect.aspect} {symbol}".strip(),
                        _humanize(aspect.p2_name),
                        _san(aspect.p2_owner),
                        f"{aspect.orbit:.2f}°",
                        movement,
                    ]
                )
            else:
                aspects_table.append(
                    [
                        _humanize(aspect.p1_name),
                        f"{aspect.aspect} {symbol}".strip(),
                        _humanize(aspect.p2_name),
                        f"{aspect.orbit:.2f}°",
                        movement,
                    ]
                )

        suffix = f" (showing {len(aspects_list)} of {total_aspects})" if max_aspects is not None else ""
        title = f"Aspects{suffix}"
        return AsciiTable(aspects_table, title=title).table

    def _house_comparison_report(self) -> str:
        if not isinstance(self._chart_data, DualChartDataModel) or not self._chart_data.house_comparison:
            return ""

        comparison = self._chart_data.house_comparison
        # Subject names are user-controlled and flow into every table title below;
        # sanitize once here so a control-char name cannot rewrite the terminal.
        first_name = _san(comparison.first_subject_name)
        second_name = _san(comparison.second_subject_name)
        sections = []

        sections.append(
            self._render_point_in_house_table(
                comparison.first_points_in_second_houses,
                f"{first_name} points in {second_name} houses",
            )
        )
        sections.append(
            self._render_point_in_house_table(
                comparison.second_points_in_first_houses,
                f"{second_name} points in {first_name} houses",
            )
        )

        # Add cusp comparison sections
        if comparison.first_cusps_in_second_houses:
            sections.append(
                self._render_cusp_in_house_table(
                    comparison.first_cusps_in_second_houses,
                    f"{first_name} cusps in {second_name} houses",
                )
            )

        if comparison.second_cusps_in_first_houses:
            sections.append(
                self._render_cusp_in_house_table(
                    comparison.second_cusps_in_first_houses,
                    f"{second_name} cusps in {first_name} houses",
                )
            )

        return "\n\n".join(section for section in sections if section)

    def _render_point_in_house_table(self, points: Sequence[PointInHouseModel], title: str) -> str:
        if not points:
            return ""

        table_data: list[list[str]] = [["Point", "Owner House", "Projected House", "Sign", "Degree"]]
        for point in points:
            owner_house = "-"
            if point.point_owner_house_number is not None or point.point_owner_house_name:
                _owner_name = _humanize(point.point_owner_house_name) if point.point_owner_house_name else "-"
                owner_house = f"{point.point_owner_house_number or '-'} ({_owner_name})"

            projected_house = f"{point.projected_house_number} ({_humanize(point.projected_house_name)})"
            table_data.append(
                [
                    f"{_san(point.point_owner_name)} – {_humanize(point.point_name)}",
                    owner_house,
                    projected_house,
                    point.point_sign,
                    f"{point.point_degree:.2f}°",
                ]
            )

        return AsciiTable(table_data, title=title).table

    def _render_cusp_in_house_table(self, points: Sequence[PointInHouseModel], title: str) -> str:
        if not points:
            return ""

        table_data: list[list[str]] = [["Point", "Projected House", "Sign", "Degree"]]
        for point in points:
            projected_house = f"{point.projected_house_number} ({_humanize(point.projected_house_name)})"
            table_data.append(
                [
                    f"{_san(point.point_owner_name)} – {_humanize(point.point_name)}",
                    projected_house,
                    point.point_sign,
                    f"{point.point_degree:.2f}°",
                ]
            )

        return AsciiTable(table_data, title=title).table

    def _relationship_score_report(self) -> str:
        if not isinstance(self._chart_data, DualChartDataModel):
            return ""

        score: Optional[RelationshipScoreModel] = getattr(self._chart_data, "relationship_score", None)
        if not score:
            return ""

        summary_table = [
            ["Metric", "Value"],
            ["Score", str(score.score_value)],
            ["Description", str(score.score_description)],
            ["Destiny Signature", "Yes" if score.is_destiny_sign else "No"],
        ]

        sections = [AsciiTable(summary_table, title="Relationship Score Summary").table]

        if score.aspects:
            aspects_table: list[list[str]] = [["Point 1", "Aspect", "Point 2", "Orb"]]
            for aspect in score.aspects:
                aspects_table.append(
                    [
                        _humanize(aspect.p1_name),
                        aspect.aspect,
                        _humanize(aspect.p2_name),
                        f"{aspect.orbit:.2f}°",
                    ]
                )
            sections.append(AsciiTable(aspects_table, title="Score Supporting Aspects").table)

        return "\n\n".join(sections)

    # ------------------------------------------------------------------ #
    # Utility helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_year(iso_datetime: Optional[str]) -> Optional[str]:
        if not iso_datetime:
            return None
        try:
            return format_iso_display(iso_datetime, "%Y")
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _format_date_iso(iso_datetime: Optional[str]) -> str:
        """
        Format datetime in ISO 8601 format (YYYY-MM-DD).

        This format is internationally unambiguous and follows the ISO 8601 standard.
        """
        if not iso_datetime:
            return ""
        try:
            return format_iso_display(iso_datetime, "%Y-%m-%d")
        except (ValueError, IndexError):
            return iso_datetime


if __name__ == "__main__":
    from kerykeion.astrological_subject.factory import AstrologicalSubjectFactory
    from kerykeion.chart_data.factory import ChartDataFactory
    from kerykeion.composite_subject.factory import CompositeSubjectFactory
    from kerykeion.planetary_returns.factory import PlanetaryReturnFactory

    # Shared offline location configuration (Liverpool, GB)
    demo_city = "Liverpool"
    demo_nation = "GB"
    demo_lat = 53.4084
    demo_lng = -2.9916
    demo_tz = "Europe/London"
    offline_online = False

    # Base natal subject (AstrologicalSubjectModel)
    natal_subject = AstrologicalSubjectFactory.from_birth_data(
        name="Sample Natal Subject",
        year=1990,
        month=7,
        day=21,
        hour=14,
        minute=45,
        city=demo_city,
        nation=demo_nation,
        lat=demo_lat,
        lng=demo_lng,
        tz_str=demo_tz,
        online=offline_online,
    )

    # Partner subject for synastry/composite examples
    partner_subject = AstrologicalSubjectFactory.from_birth_data(
        name="Yoko Ono",
        year=1933,
        month=2,
        day=18,
        hour=20,
        minute=30,
        city="Tokyo",
        nation="JP",
        lat=35.6762,
        lng=139.6503,
        tz_str="Asia/Tokyo",
        online=offline_online,
    )

    # Transit subject (John's 1980 New York snapshot)
    transit_subject = AstrologicalSubjectFactory.from_birth_data(
        name="1980 Transit",
        year=1980,
        month=12,
        day=8,
        hour=22,
        minute=50,
        city="New York",
        nation="US",
        lat=40.7128,
        lng=-74.0060,
        tz_str="America/New_York",
        online=offline_online,
    )

    # Planetary return subject (Solar Return)
    return_factory = PlanetaryReturnFactory(
        natal_subject,
        city=natal_subject.city,
        nation=natal_subject.nation,
        lat=natal_subject.lat,
        lng=natal_subject.lng,
        tz_str=natal_subject.tz_str,
        online=False,
    )
    solar_return_subject = return_factory.next_return_from_iso_formatted_time(
        natal_subject.iso_formatted_local_datetime,
        "Solar",
    )
    # Derive a composite subject representing the pair's midpoint configuration
    composite_subject = CompositeSubjectFactory(
        natal_subject,
        partner_subject,
        chart_name="Sample & Yoko Composite Chart",
    ).get_midpoint_composite_subject_model()

    # Build chart data models mirroring ChartDrawer inputs
    natal_chart_data = ChartDataFactory.create_natal_chart_data(natal_subject)
    composite_chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
    single_return_chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return_subject)
    transit_chart_data = ChartDataFactory.create_transit_chart_data(natal_subject, transit_subject)
    synastry_chart_data = ChartDataFactory.create_synastry_chart_data(natal_subject, partner_subject)
    dual_return_chart_data = ChartDataFactory.create_return_chart_data(natal_subject, solar_return_subject)

    # Demonstrate each report/model type
    print("\n" + "=" * 54)
    print("AstrologicalSubjectModel Report — Sample Natal Subject")
    print("=" * 54)
    ReportGenerator(natal_subject, include_aspects=False).print_report(include_aspects=False)

    print("\n" + "=" * 57)
    print("SingleChartDataModel Report (Natal) — Sample Natal Subject")
    print("=" * 57)
    ReportGenerator(natal_chart_data).print_report()

    print("\n" + "=" * 65)
    print("SingleChartDataModel Report (Composite) — Sample & Yoko")
    print("=" * 65)
    ReportGenerator(composite_chart_data).print_report()

    print("\n" + "=" * 63)
    print("SingleChartDataModel Report (Single Return) — Sample Natal Subject")
    print("=" * 63)
    ReportGenerator(single_return_chart_data).print_report()

    print("\n" + "=" * 58)
    print("DualChartDataModel Report (Transit) — Sample Natal Subject")
    print("=" * 58)
    ReportGenerator(transit_chart_data).print_report()

    print("\n" + "=" * 60)
    print("DualChartDataModel Report (Synastry) — Sample & Yoko")
    print("=" * 60)
    ReportGenerator(synastry_chart_data).print_report()

    print("\n" + "=" * 58)
    print("DualChartDataModel Report (Dual Return) — Sample Natal Subject")
    print("=" * 58)
    ReportGenerator(dual_return_chart_data).print_report()
