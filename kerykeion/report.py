from kerykeion import AstrologicalSubjectFactory
from simple_ascii_tables import AsciiTable
from kerykeion.utilities import get_houses_list, get_available_astrological_points_list
from kerykeion.schemas.kr_models import (
    AstrologicalSubjectModel,
    SingleChartDataModel,
    DualChartDataModel,
)
from typing import Optional, Union


class Report:
    """
    Create comprehensive astrological reports for a Kerykeion instance.

    This class generates multiple detailed reports including:
    - Subject data (birth information and settings)
    - Celestial points (planets, nodes, asteroids with positions, speed, and declination)
    - Houses (complete house system information)
    - Lunar phase (moon phase details)
    - Elements and qualities distribution (for chart data models)
    - Aspects (for chart data models)

    The Report class accepts either:
    - AstrologicalSubjectModel: Basic subject with celestial positions
    - SingleChartDataModel: Full chart data with elements, qualities, and aspects
    - DualChartDataModel: Comparison charts with relationship analysis
    """

    def __init__(self, instance: Union[AstrologicalSubjectModel, SingleChartDataModel, DualChartDataModel]):
        """
        Initialize a new Report instance.

        Args:
            instance: The astrological model to create reports for. Can be:
                - AstrologicalSubjectModel for basic subject data
                - SingleChartDataModel for natal/composite charts with distributions
                - DualChartDataModel for synastry/transit charts
        """
        self.instance = instance

        # Extract the subject for data access
        if isinstance(instance, (SingleChartDataModel, DualChartDataModel)):
            # For chart models, get the subject from the chart
            if hasattr(instance, 'subject'):
                self._subject = instance.subject
            elif hasattr(instance, 'first_subject'):
                self._subject = instance.first_subject
            else:
                self._subject = instance
        else:
            # For subject models, use directly
            self._subject = instance

    def get_report_title(self) -> str:
        """Generate the report title based on the subject's name."""
        title = f"Kerykeion Astrological Report for {self._subject.name}"
        separator = "=" * len(title)
        return f"\n{separator}\n{title}\n{separator}\n"

    def get_subject_data_report(self) -> str:
        """
        Creates a comprehensive report of the subject's birth data and settings.

        Returns:
            Formatted ASCII table with birth information and astrological settings.
        """
        # Birth data section
        birth_data = [
            ["Birth Information", "Value"],
            ["Name", self._subject.name],
        ]

        # Add date/time if available (not all subjects have these)
        if hasattr(self._subject, 'day') and hasattr(self._subject, 'month') and hasattr(self._subject, 'year'):
            birth_data.append(["Date", f"{self._subject.day:02d}/{self._subject.month:02d}/{self._subject.year}"])  # type: ignore
        if hasattr(self._subject, 'hour') and hasattr(self._subject, 'minute'):
            birth_data.append(["Time", f"{self._subject.hour:02d}:{self._subject.minute:02d}"])  # type: ignore
        if hasattr(self._subject, 'city'):
            birth_data.append(["City", self._subject.city])  # type: ignore
        if hasattr(self._subject, 'nation'):
            birth_data.append(["Nation", self._subject.nation])  # type: ignore
        if hasattr(self._subject, 'lat'):
            birth_data.append(["Latitude", f"{self._subject.lat:.4f}°"])  # type: ignore
        if hasattr(self._subject, 'lng'):
            birth_data.append(["Longitude", f"{self._subject.lng:.4f}°"])  # type: ignore
        if hasattr(self._subject, 'tz_str'):
            birth_data.append(["Timezone", self._subject.tz_str])  # type: ignore
        if hasattr(self._subject, 'day_of_week'):
            birth_data.append(["Day of Week", self._subject.day_of_week])  # type: ignore

        # Settings section
        settings_data = [
            ["Astrological Settings", "Value"],
        ]

        if hasattr(self._subject, 'zodiac_type'):
            settings_data.append(["Zodiac Type", self._subject.zodiac_type])  # type: ignore
        if hasattr(self._subject, 'houses_system_name'):
            settings_data.append(["Houses System", self._subject.houses_system_name])  # type: ignore
        if hasattr(self._subject, 'perspective_type'):
            settings_data.append(["Perspective Type", self._subject.perspective_type])  # type: ignore
        if hasattr(self._subject, 'julian_day'):
            settings_data.append(["Julian Day", f"{self._subject.julian_day:.6f}"])  # type: ignore
        if hasattr(self._subject, 'sidereal_mode') and self._subject.sidereal_mode:
            settings_data.append(["Sidereal Mode", self._subject.sidereal_mode])  # type: ignore

        birth_table = AsciiTable(birth_data, title="Birth Data")
        settings_table = AsciiTable(settings_data, title="Settings")

        return f"{birth_table.table}\n\n{settings_table.table}"

    def get_celestial_points_report(self) -> str:
        """
        Creates a detailed report of all celestial points (planets, nodes, asteroids, etc.).

        Includes:
        - Sign and position
        - Speed (daily motion)
        - Declination
        - Retrograde status
        - House placement

        Returns:
            Formatted ASCII table with complete celestial point data.
        """
        points = get_available_astrological_points_list(self._subject)  # type: ignore

        if not points:
            return "No celestial points data available."

        # Main planets first, then nodes, then others
        main_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        nodes = ["Mean_North_Lunar_Node", "True_North_Lunar_Node"]
        angles = ["Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli"]

        # Sort points: angles, main planets, nodes, then others
        sorted_points = []

        # Add angles first
        for name in angles:
            sorted_points.extend([p for p in points if p.name == name])

        # Add main planets
        for name in main_planets:
            sorted_points.extend([p for p in points if p.name == name])

        # Add nodes
        for name in nodes:
            sorted_points.extend([p for p in points if p.name == name])

        # Add remaining points
        used_names = set(angles + main_planets + nodes)
        sorted_points.extend([p for p in points if p.name not in used_names])

        # Build table
        celestial_data = [["Point", "Sign", "Position", "Speed", "Decl.", "Ret.", "House"]]

        for point in sorted_points:
            speed_str = f"{point.speed:+.4f}°/d" if point.speed is not None else "N/A"
            decl_str = f"{point.declination:+.2f}°" if point.declination is not None else "N/A"
            ret_str = "R" if point.retrograde else "-"
            house_str = point.house.replace("_", " ") if point.house else "-"

            celestial_data.append([
                point.name.replace("_", " "),
                f"{point.sign} {point.emoji}",
                f"{point.position:.2f}°",
                speed_str,
                decl_str,
                ret_str,
                house_str,
            ])

        return AsciiTable(celestial_data, title="Celestial Points").table

    def get_houses_report(self) -> str:
        """
        Creates a detailed report of the houses system.

        Returns:
            Formatted ASCII table with house cusps and their positions.
        """
        houses = get_houses_list(self._subject)  # type: ignore

        if not houses:
            return "No houses data available."

        houses_data = [["House", "Sign", "Position", "Absolute Position"]]

        for house in houses:
            houses_data.append([
                house.name.replace("_", " "),
                f"{house.sign} {house.emoji}",
                f"{house.position:.2f}°",
                f"{house.abs_pos:.2f}°",
            ])

        return AsciiTable(houses_data, title=f"Houses ({self._subject.houses_system_name})").table  # type: ignore

    def get_lunar_phase_report(self) -> str:
        """
        Creates a report of the lunar phase information.

        Returns:
            Formatted ASCII table with lunar phase details.
        """
        if not hasattr(self._subject, 'lunar_phase') or not self._subject.lunar_phase:
            return "No lunar phase data available."

        lunar = self._subject.lunar_phase  # type: ignore

        lunar_data = [
            ["Lunar Phase Information", "Value"],
            ["Phase Name", f"{lunar.moon_phase_name} {lunar.moon_emoji}"],
            ["Sun-Moon Angle", f"{lunar.degrees_between_s_m:.2f}°"],
            ["Moon Phase", f"{lunar.moon_phase}"],
            ["Sun Phase", f"{lunar.sun_phase}"],
        ]

        return AsciiTable(lunar_data, title="Lunar Phase").table

    def get_elements_report(self) -> str:
        """
        Creates a report of element distribution (Fire, Earth, Air, Water).

        Note: Elements distribution is only available when using SingleChartDataModel
        or DualChartDataModel (from ChartDataFactory). Basic AstrologicalSubjectModel
        instances do not have element distributions calculated.

        Returns:
            Formatted ASCII table with element distribution percentages.
        """
        if not hasattr(self.instance, 'element_distribution') or not self.instance.element_distribution:  # type: ignore
            return "No element distribution data available."

        elem = self.instance.element_distribution  # type: ignore
        total = elem.fire + elem.earth + elem.air + elem.water

        if total == 0:
            return "No element distribution data available."

        element_data = [
            ["Element", "Count", "Percentage"],
            ["Fire 🔥", elem.fire, f"{(elem.fire / total * 100):.1f}%"],
            ["Earth 🌍", elem.earth, f"{(elem.earth / total * 100):.1f}%"],
            ["Air 💨", elem.air, f"{(elem.air / total * 100):.1f}%"],
            ["Water 💧", elem.water, f"{(elem.water / total * 100):.1f}%"],
            ["Total", total, "100%"],
        ]

        return AsciiTable(element_data, title="Element Distribution").table

    def get_qualities_report(self) -> str:
        """
        Creates a report of quality distribution (Cardinal, Fixed, Mutable).

        Note: Quality distribution is only available when using SingleChartDataModel
        or DualChartDataModel (from ChartDataFactory). Basic AstrologicalSubjectModel
        instances do not have quality distributions calculated.

        Returns:
            Formatted ASCII table with quality distribution percentages.
        """
        if not hasattr(self.instance, 'quality_distribution') or not self.instance.quality_distribution:  # type: ignore
            return "No quality distribution data available."

        qual = self.instance.quality_distribution  # type: ignore
        total = qual.cardinal + qual.fixed + qual.mutable

        if total == 0:
            return "No quality distribution data available."

        quality_data = [
            ["Quality", "Count", "Percentage"],
            ["Cardinal", qual.cardinal, f"{(qual.cardinal / total * 100):.1f}%"],
            ["Fixed", qual.fixed, f"{(qual.fixed / total * 100):.1f}%"],
            ["Mutable", qual.mutable, f"{(qual.mutable / total * 100):.1f}%"],
            ["Total", total, "100%"],
        ]

        return AsciiTable(quality_data, title="Quality Distribution").table

    def get_aspects_report(self, max_aspects: Optional[int] = None) -> str:
        """
        Creates a report of astrological aspects.

        Note: Aspects are only available when using SingleChartDataModel or DualChartDataModel
        (from ChartDataFactory). The report will show relevant aspects (filtered by orb).

        Args:
            max_aspects: Maximum number of aspects to display. If None, show all.

        Returns:
            Formatted ASCII table with aspects information.
        """
        # Check for aspects in chart data models
        if not hasattr(self.instance, 'aspects'):  # type: ignore
            return "No aspects data available."

        aspects_model = self.instance.aspects  # type: ignore

        # Get relevant aspects (filtered by orb)
        if not hasattr(aspects_model, 'relevant_aspects') or not aspects_model.relevant_aspects:  # type: ignore
            return "No aspects data available."

        aspects = aspects_model.relevant_aspects  # type: ignore
        total_aspects = len(aspects)

        if max_aspects:
            aspects = aspects[:max_aspects]

        aspects_data = [["Point 1", "Aspect", "Point 2", "Orb", "Movement"]]

        for aspect in aspects:
            # Format aspect type symbol
            aspect_symbol = {
                "conjunction": "☌",
                "opposition": "☍",
                "trine": "△",
                "square": "□",
                "sextile": "⚹",
                "quincunx": "⚻",
                "semisquare": "∠",
                "sesquisquare": "⚼",
                "quintile": "Q",
            }.get(aspect.aspect.lower(), aspect.aspect)

            # Format movement with symbols
            movement_symbol = {
                "Applying": "→",
                "Separating": "←",
                "Exact": "✓"
            }.get(aspect.aspect_movement, "")

            aspects_data.append([
                aspect.p1_name.replace("_", " "),
                f"{aspect.aspect} {aspect_symbol}",
                aspect.p2_name.replace("_", " "),
                f"{aspect.orbit:.2f}°",
                f"{aspect.aspect_movement} {movement_symbol}",
            ])

        title = "Aspects" + (f" (showing {len(aspects)} of {total_aspects})" if max_aspects else "")
        return AsciiTable(aspects_data, title=title).table

    def get_full_report(self, include_aspects: bool = True, max_aspects: Optional[int] = 20) -> str:
        """
        Returns the complete comprehensive report with all sections.

        Args:
            include_aspects: Whether to include the aspects report.
            max_aspects: Maximum number of aspects to show. If None, show all.

        Returns:
            Complete formatted report as a string.
        """
        sections = [
            self.get_report_title(),
            self.get_subject_data_report(),
            "\n",
            self.get_celestial_points_report(),
            "\n",
            self.get_houses_report(),
            "\n",
            self.get_lunar_phase_report(),
            "\n",
            self.get_elements_report(),
            "\n",
            self.get_qualities_report(),
        ]

        if include_aspects:
            aspects = self.get_aspects_report(max_aspects=max_aspects)
            if aspects != "No aspects data available.":
                sections.extend(["\n", aspects])

        return "\n".join(sections)

    def print_report(self, include_aspects: bool = True, max_aspects: Optional[int] = None) -> None:
        """
        Print the complete comprehensive report.

        Args:
            include_aspects: Whether to include the aspects report.
            max_aspects: Maximum number of aspects to show. If None, show all.
        """
        print(self.get_full_report(include_aspects=include_aspects, max_aspects=max_aspects))


if __name__ == "__main__":
    from kerykeion.utilities import setup_logging
    from kerykeion import ChartDataFactory
    setup_logging(level="info")

    # Example 1: Basic natal chart report with subject only
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Subject Report (no elements/qualities)")
    print("="*60)

    john = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB"
    )
    report_subject = Report(john)

    # You can print individual sections
    print("\n--- Subject Data ---")
    print(report_subject.get_subject_data_report())

    print("\n--- Celestial Points (with Speed & Declination!) ---")
    print(report_subject.get_celestial_points_report())

    print("\n--- Elements (not available for subject only) ---")
    print(report_subject.get_elements_report())

    # Example 2: Full chart report with elements, qualities, and aspects
    print("\n" + "="*60)
    print("EXAMPLE 2: Complete Chart Report with Elements & Qualities")
    print("="*60)

    # Create chart data - this calculates elements, qualities, and aspects
    chart = ChartDataFactory.create_chart_data(
        "Natal",
        first_subject=john,
    )

    # Create report with the chart (not just the subject)
    report_chart = Report(chart)

    print("\n--- Elements Distribution ---")
    print(report_chart.get_elements_report())

    print("\n--- Qualities Distribution ---")
    print(report_chart.get_qualities_report())

    print("\n--- Aspects ---")
    print(report_chart.get_aspects_report(max_aspects=10))

    # Example 3: Print complete report
    print("\n" + "="*60)
    print("EXAMPLE 3: Full Comprehensive Report")
    print("="*60)
    report_chart.print_report(include_aspects=True)
