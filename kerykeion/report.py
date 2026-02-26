from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Sequence, Tuple, Union, Literal

from simple_ascii_tables import AsciiTable

from kerykeion.utilities import get_available_astrological_points_list, get_houses_list
from kerykeion.schemas.kr_models import (
    AstrologicalSubjectModel,
    ChartDataModel,
    CompositeSubjectModel,
    DualChartDataModel,
    PlanetReturnModel,
    PointInHouseModel,
    RelationshipScoreModel,
    SingleChartDataModel,
    KerykeionPointModel,
)


ASPECT_SYMBOLS = {
    "conjunction": "☌",
    "opposition": "☍",
    "trine": "△",
    "square": "□",
    "sextile": "⚹",
    "quincunx": "⚻",
    "semisquare": "∠",
    "sesquisquare": "⚼",
    "quintile": "Q",
}

MOVEMENT_SYMBOLS = {
    "Applying": "→",
    "Separating": "←",
    "Static": "=",
}


SubjectLike = Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel]
LiteralReportKind = Literal["subject", "single_chart", "dual_chart"]


class ReportGenerator:
    """
    Generate textual reports for astrological data models with a structure that mirrors the
    chart-specific dispatch logic used in :class:`~kerykeion.charts.chart_drawer.ChartDrawer`.

    The generator accepts any of the chart data models handled by ``ChartDrawer`` as well as
    raw ``AstrologicalSubjectModel`` instances. The ``print_report`` method automatically
    selects the appropriate layout and sections depending on the underlying chart type.
    """

    def __init__(
        self,
        model: Union[ChartDataModel, AstrologicalSubjectModel],
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
        self._primary_subject: SubjectLike
        self._secondary_subject: Optional[SubjectLike] = None
        self._active_points: List[str] = []
        self._active_aspects: List[dict] = []

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

        if self._model_kind == "subject":
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
        if isinstance(self.model, AstrologicalSubjectModel):
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
            supported = "AstrologicalSubjectModel, SingleChartDataModel, DualChartDataModel"
            raise TypeError(f"Unsupported model type {type(self.model)!r}. Supported models: {supported}.")

    # ------------------------------------------------------------------ #
    # Report builders
    # ------------------------------------------------------------------ #

    def _build_subject_report(self) -> List[str]:
        sections = [
            self._subject_data_report(self._primary_subject, "Astrological Subject"),
            self._celestial_points_report(self._primary_subject, "Celestial Points"),
            self._houses_report(self._primary_subject, "Houses"),
            self._lunar_phase_report(self._primary_subject),
        ]
        return sections

    def _build_single_chart_report(self, *, include_aspects: bool, max_aspects: Optional[int]) -> List[str]:
        assert self._chart_data is not None
        sections: List[str] = [
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
                self._houses_report(self._primary_subject, f"{self._primary_subject_label()} Houses"),
                self._lunar_phase_report(self._primary_subject),
                self._elements_report(),
                self._qualities_report(),
                self._active_configuration_report(),
            ]
        )

        if include_aspects:
            sections.append(self._aspects_report(max_aspects=max_aspects))

        return sections

    def _build_dual_chart_report(self, *, include_aspects: bool, max_aspects: Optional[int]) -> List[str]:
        assert self._chart_data is not None
        primary_label, secondary_label = self._subject_role_labels()

        sections: List[str] = [
            self._subject_data_report(self._primary_subject, primary_label),
        ]

        if self._secondary_subject is not None:
            sections.append(self._subject_data_report(self._secondary_subject, secondary_label))

        sections.extend(
            [
                self._celestial_points_report(self._primary_subject, f"{primary_label} Celestial Points"),
            ]
        )

        if self._secondary_subject is not None:
            sections.append(
                self._celestial_points_report(self._secondary_subject, f"{secondary_label} Celestial Points")
            )

        sections.append(self._houses_report(self._primary_subject, f"{primary_label} Houses"))

        if self._secondary_subject is not None:
            sections.append(self._houses_report(self._secondary_subject, f"{secondary_label} Houses"))

        sections.extend(
            [
                self._lunar_phase_report(self._primary_subject),
                self._elements_report(),
                self._qualities_report(),
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

    def _build_title(self) -> str:
        if self._model_kind == "subject":
            base_title = f"{self._primary_subject.name} — Subject Report"
        elif self.chart_type == "Natal":
            base_title = f"{self._primary_subject.name} — Natal Chart Report"
        elif self.chart_type == "Composite":
            if isinstance(self._primary_subject, CompositeSubjectModel):
                first = self._primary_subject.first_subject.name
                second = self._primary_subject.second_subject.name
                base_title = f"{first} & {second} — Composite Report"
            else:
                base_title = f"{self._primary_subject.name} — Composite Report"
        elif self.chart_type == "SingleReturnChart":
            year = self._extract_year(self._primary_subject.iso_formatted_local_datetime)
            if isinstance(self._primary_subject, PlanetReturnModel) and self._primary_subject.return_type == "Solar":
                base_title = f"{self._primary_subject.name} — Solar Return {year or ''}".strip()
            else:
                base_title = f"{self._primary_subject.name} — Lunar Return {year or ''}".strip()
        elif self.chart_type == "Transit":
            date_str = self._format_date_iso(
                self._secondary_subject.iso_formatted_local_datetime if self._secondary_subject else None
            )
            base_title = f"{self._primary_subject.name} — Transit {date_str}".strip()
        elif self.chart_type == "Synastry":
            second_name = self._secondary_subject.name if self._secondary_subject is not None else "Unknown"
            base_title = f"{self._primary_subject.name} & {second_name} — Synastry Report"
        elif self.chart_type == "DualReturnChart":
            year = self._extract_year(
                self._secondary_subject.iso_formatted_local_datetime if self._secondary_subject else None
            )
            if (
                isinstance(self._secondary_subject, PlanetReturnModel)
                and self._secondary_subject.return_type == "Solar"
            ):
                base_title = f"{self._primary_subject.name} — Solar Return Comparison {year or ''}".strip()
            else:
                base_title = f"{self._primary_subject.name} — Lunar Return Comparison {year or ''}".strip()
        else:
            base_title = f"{self._primary_subject.name} — Chart Report"

        separator = "=" * len(base_title)
        return f"\n{separator}\n{base_title}\n{separator}\n"

    def _primary_subject_label(self) -> str:
        if self.chart_type == "Composite":
            return "Composite Chart"
        if self.chart_type == "SingleReturnChart":
            if isinstance(self._primary_subject, PlanetReturnModel) and self._primary_subject.return_type == "Solar":
                return "Solar Return Chart"
            return "Lunar Return Chart"
        return f"{self.chart_type or 'Chart'}"

    def _subject_role_labels(self) -> Tuple[str, str]:
        if self.chart_type == "Transit":
            return "Natal Subject", "Transit Subject"
        if self.chart_type == "Synastry":
            return "First Subject", "Second Subject"
        if self.chart_type == "DualReturnChart":
            return "Natal Subject", "Return Subject"
        return "Primary Subject", "Secondary Subject"

    def _subject_data_report(self, subject: SubjectLike, label: str) -> str:
        birth_data = [["Field", "Value"], ["Name", subject.name]]

        if isinstance(subject, CompositeSubjectModel):
            composite_members = f"{subject.first_subject.name} & {subject.second_subject.name}"
            birth_data.append(["Composite Members", composite_members])
            birth_data.append(["Composite Type", subject.composite_chart_type])

        if isinstance(subject, PlanetReturnModel):
            birth_data.append(["Return Type", subject.return_type])

        if isinstance(subject, AstrologicalSubjectModel):
            birth_data.append(["Date", f"{subject.day:02d}/{subject.month:02d}/{subject.year}"])
            birth_data.append(["Time", f"{subject.hour:02d}:{subject.minute:02d}"])

        city = getattr(subject, "city", None)
        if city:
            birth_data.append(["City", str(city)])

        nation = getattr(subject, "nation", None)
        if nation:
            birth_data.append(["Nation", str(nation)])

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

        settings_data = [["Setting", "Value"]]
        settings_data.append(["Zodiac Type", str(subject.zodiac_type)])
        if getattr(subject, "sidereal_mode", None):
            settings_data.append(["Sidereal Mode", str(subject.sidereal_mode)])
        settings_data.append(["Houses System", str(subject.houses_system_name)])
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
        points = self._collect_celestial_points(subject)
        if not points:
            return "No celestial points data available."

        main_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        nodes = ["Mean_North_Lunar_Node", "True_North_Lunar_Node"]
        angles = ["Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli"]

        sorted_points = []
        for name in angles + main_planets + nodes:
            sorted_points.extend([p for p in points if p.name == name])

        used_names = set(angles + main_planets + nodes)
        sorted_points.extend([p for p in points if p.name not in used_names])

        celestial_data: List[List[str]] = [["Point", "Sign", "Position", "Speed", "Decl.", "Ret.", "House"]]
        for point in sorted_points:
            speed_str = f"{point.speed:+.4f}°/d" if point.speed is not None else "N/A"
            decl_str = f"{point.declination:+.2f}°" if point.declination is not None else "N/A"
            ret_str = "R" if point.retrograde else "-"
            house_str = point.house.replace("_", " ") if point.house else "-"
            celestial_data.append(
                [
                    point.name.replace("_", " "),
                    f"{point.sign} {point.emoji}",
                    f"{point.position:.2f}°",
                    speed_str,
                    decl_str,
                    ret_str,
                    house_str,
                ]
            )

        return AsciiTable(celestial_data, title=title).table

    def _collect_celestial_points(self, subject: SubjectLike) -> List[KerykeionPointModel]:
        if isinstance(subject, AstrologicalSubjectModel):
            return get_available_astrological_points_list(subject)

        points: List[KerykeionPointModel] = []
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

        houses_data: List[List[str]] = [["House", "Sign", "Position", "Absolute Position"]]
        for house in houses:
            houses_data.append(
                [
                    house.name.replace("_", " "),
                    f"{house.sign} {house.emoji}",
                    f"{house.position:.2f}°",
                    f"{house.abs_pos:.2f}°",
                ]
            )

        system_name = getattr(subject, "houses_system_name", "")
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
            ["Fire 🔥", elem.fire, f"{(elem.fire / total * 100):.1f}%"],
            ["Earth 🌍", elem.earth, f"{(elem.earth / total * 100):.1f}%"],
            ["Air 💨", elem.air, f"{(elem.air / total * 100):.1f}%"],
            ["Water 💧", elem.water, f"{(elem.water / total * 100):.1f}%"],
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
            ["Cardinal", qual.cardinal, f"{(qual.cardinal / total * 100):.1f}%"],
            ["Fixed", qual.fixed, f"{(qual.fixed / total * 100):.1f}%"],
            ["Mutable", qual.mutable, f"{(qual.mutable / total * 100):.1f}%"],
            ["Total", total, "100%"],
        ]
        return AsciiTable(quality_data, title="Quality Distribution").table

    def _active_configuration_report(self) -> str:
        if not self._active_points and not self._active_aspects:
            return ""

        sections: List[str] = []

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
            table_header: List[str] = ["Point 1", "Owner 1", "Aspect", "Point 2", "Owner 2", "Orb", "Movement"]
        else:
            table_header = ["Point 1", "Aspect", "Point 2", "Orb", "Movement"]

        aspects_table: List[List[str]] = [table_header]
        for aspect in aspects_list:
            aspect_name = str(aspect.aspect)
            symbol = ASPECT_SYMBOLS.get(aspect_name.lower(), aspect_name)
            movement_symbol = MOVEMENT_SYMBOLS.get(aspect.aspect_movement, "")
            movement = f"{aspect.aspect_movement} {movement_symbol}".strip()

            if is_dual:
                aspects_table.append(
                    [
                        aspect.p1_name.replace("_", " "),
                        aspect.p1_owner,
                        f"{aspect.aspect} {symbol}",
                        aspect.p2_name.replace("_", " "),
                        aspect.p2_owner,
                        f"{aspect.orbit:.2f}°",
                        movement,
                    ]
                )
            else:
                aspects_table.append(
                    [
                        aspect.p1_name.replace("_", " "),
                        f"{aspect.aspect} {symbol}",
                        aspect.p2_name.replace("_", " "),
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
        sections = []

        sections.append(
            self._render_point_in_house_table(
                comparison.first_points_in_second_houses,
                f"{comparison.first_subject_name} points in {comparison.second_subject_name} houses",
            )
        )
        sections.append(
            self._render_point_in_house_table(
                comparison.second_points_in_first_houses,
                f"{comparison.second_subject_name} points in {comparison.first_subject_name} houses",
            )
        )

        # Add cusp comparison sections
        if comparison.first_cusps_in_second_houses:
            sections.append(
                self._render_cusp_in_house_table(
                    comparison.first_cusps_in_second_houses,
                    f"{comparison.first_subject_name} cusps in {comparison.second_subject_name} houses",
                )
            )

        if comparison.second_cusps_in_first_houses:
            sections.append(
                self._render_cusp_in_house_table(
                    comparison.second_cusps_in_first_houses,
                    f"{comparison.second_subject_name} cusps in {comparison.first_subject_name} houses",
                )
            )

        return "\n\n".join(section for section in sections if section)

    def _render_point_in_house_table(self, points: Sequence[PointInHouseModel], title: str) -> str:
        if not points:
            return ""

        table_data: List[List[str]] = [["Point", "Owner House", "Projected House", "Sign", "Degree"]]
        for point in points:
            owner_house = "-"
            if point.point_owner_house_number is not None or point.point_owner_house_name:
                owner_house = f"{point.point_owner_house_number or '-'} ({point.point_owner_house_name or '-'})"

            projected_house = f"{point.projected_house_number} ({point.projected_house_name})"
            table_data.append(
                [
                    f"{point.point_owner_name} – {point.point_name.replace('_', ' ')}",
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

        table_data: List[List[str]] = [["Point", "Projected House", "Sign", "Degree"]]
        for point in points:
            projected_house = f"{point.projected_house_number} ({point.projected_house_name})"
            table_data.append(
                [
                    f"{point.point_owner_name} – {point.point_name.replace('_', ' ')}",
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
            aspects_table: List[List[str]] = [["Point 1", "Aspect", "Point 2", "Orb"]]
            for aspect in score.aspects:
                aspects_table.append(
                    [
                        aspect.p1_name.replace("_", " "),
                        aspect.aspect,
                        aspect.p2_name.replace("_", " "),
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
            return datetime.fromisoformat(iso_datetime).strftime("%Y")
        except ValueError:
            return None

    @staticmethod
    def _format_date(iso_datetime: Optional[str]) -> str:
        """
        Format datetime in dd/mm/yyyy format.

        .. deprecated::
            Use _format_date_iso() for internationally unambiguous date formatting.
        """
        if not iso_datetime:
            return ""
        try:
            return datetime.fromisoformat(iso_datetime).strftime("%d/%m/%Y")
        except ValueError:
            return iso_datetime

    @staticmethod
    def _format_date_iso(iso_datetime: Optional[str]) -> str:
        """
        Format datetime in ISO 8601 format (YYYY-MM-DD).

        This format is internationally unambiguous and follows the ISO 8601 standard.
        """
        if not iso_datetime:
            return ""
        try:
            return datetime.fromisoformat(iso_datetime).strftime("%Y-%m-%d")
        except ValueError:
            return iso_datetime


if __name__ == "__main__":
    from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
    from kerykeion.chart_data_factory import ChartDataFactory
    from kerykeion.composite_subject_factory import CompositeSubjectFactory
    from kerykeion.planetary_return_factory import PlanetaryReturnFactory

    # Shared offline location configuration (Rome, Italy)
    john_city = "Liverpool"
    john_nation = "GB"
    john_lat = 53.4084
    john_lng = -2.9916
    john_tz = "Europe/London"
    offline_online = False

    # Base natal subject (AstrologicalSubjectModel)
    natal_subject = AstrologicalSubjectFactory.from_birth_data(
        name="Sample Natal Subject",
        year=1990,
        month=7,
        day=21,
        hour=14,
        minute=45,
        city=john_city,
        nation=john_nation,
        lat=john_lat,
        lng=john_lng,
        tz_str=john_tz,
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
        chart_name="John & Yoko Composite Chart",
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
    print("AstrologicalSubjectModel Report — John Lennon")
    print("=" * 54)
    ReportGenerator(natal_subject, include_aspects=False).print_report(include_aspects=False)

    print("\n" + "=" * 57)
    print("SingleChartDataModel Report (Natal) — John Lennon")
    print("=" * 57)
    ReportGenerator(natal_chart_data).print_report()

    print("\n" + "=" * 65)
    print("SingleChartDataModel Report (Composite) — John & Yoko")
    print("=" * 65)
    ReportGenerator(composite_chart_data).print_report()

    print("\n" + "=" * 63)
    print("SingleChartDataModel Report (Single Return) — John Lennon")
    print("=" * 63)
    ReportGenerator(single_return_chart_data).print_report()

    print("\n" + "=" * 58)
    print("DualChartDataModel Report (Transit) — John Lennon")
    print("=" * 58)
    ReportGenerator(transit_chart_data).print_report()

    print("\n" + "=" * 60)
    print("DualChartDataModel Report (Synastry) — John & Yoko")
    print("=" * 60)
    ReportGenerator(synastry_chart_data).print_report()

    print("\n" + "=" * 58)
    print("DualChartDataModel Report (Dual Return) — John Lennon")
    print("=" * 58)
    ReportGenerator(dual_return_chart_data).print_report()
