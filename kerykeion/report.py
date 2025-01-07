from kerykeion import AstrologicalSubject, TransitAnalysis
from kerykeion.kr_types.kr_models import AstrologicalSubjectModel, TransitAnalysisModel, AspectModel
from kerykeion.kr_types.kr_literals import AngularHouses
from terminaltables import AsciiTable
from kerykeion.utilities import get_houses_list, get_available_planets_list
from typing import Union
import json
import logging


class Report:
    """
    Create a report for a Kerykeion instance.
    """

    report_title: str
    data_table: str
    planets_table: str
    houses_table: str

    def __init__(self, instance: Union[AstrologicalSubject, AstrologicalSubjectModel]):
        self.instance = instance

        self.get_report_title()
        self.get_data_table()
        self.get_planets_table()
        self.get_houses_table()

    def get_report_title(self) -> None:
        self.report_title = f"\n+- Kerykeion report for {self.instance.name} -+"

    def get_data_table(self) -> None:
        """
        Creates the data table of the report.
        """

        main_data = [["Date", "Time", "Location", "Longitude", "Latitude"]] + [
            [
                f"{self.instance.day}/{self.instance.month}/{self.instance.year}",
                f"{self.instance.hour}:{self.instance.minute}",
                f"{self.instance.city}, {self.instance.nation}",
                self.instance.lng,
                self.instance.lat,
            ]
        ]
        self.data_table = AsciiTable(main_data).table

    def get_planets_table(self) -> None:
        """
        Creates the planets table.
        """

        planets_data = [["Planet", "Sign", "Pos.", "Ret.", "House"]] + [
            [
                planet.name,
                planet.sign,
                round(float(planet.position), 2),
                ("R" if planet.retrograde else "-"),
                planet.house,
            ]
            for planet in get_available_planets_list(self.instance)
        ]

        self.planets_table = AsciiTable(planets_data).table

    def get_houses_table(self) -> None:
        """
        Creates the houses table.
        """

        houses_data = [["House", "Sign", "Position"]] + [
            [house.name, house.sign, round(float(house.position), 2)] for house in get_houses_list(self.instance)
        ]

        self.houses_table = AsciiTable(houses_data).table

    def get_full_report(self) -> str:
        """
        Returns the full report.
        """

        return f"{self.report_title}\n{self.data_table}\n{self.planets_table}\n{self.houses_table}"

    def print_report(self) -> None:
        """
        Print the report.
        """

        print(self.get_full_report())


class TransitAnalysisReport(Report):
    """Create a formatted report comparing natal and transit charts."""

    def __init__(self, transit_analysis: TransitAnalysis,
                 max_orb: float = 8.0,
                 include_minor_aspects: bool = True,
                 traditional_aspects_only: bool = False,
                 max_aspects: int = None,
                 include_auxiliary_points: bool = True):
        self.transit_analysis = transit_analysis
        self.include_house_aspects = transit_analysis.model.include_house_aspects  # Get from model
        super().__init__(transit_analysis.natal)

        # Store the raw data as class attributes
        self.summary_data = self._gather_summary_data()
        self.planetary_data = self._gather_planetary_data()
        self.houses_data = self._gather_houses_data()
        self.aspects_data = self._gather_aspects_data()

        # Generate the formatted tables from the data
        self.get_summary_section()
        self.get_combined_planets_table()
        self.get_combined_houses_table()
        self.get_filtered_aspects_table(
            max_orb=max_orb,
            include_minor_aspects=include_minor_aspects,
            traditional_aspects_only=traditional_aspects_only,
            max_aspects=max_aspects,
            include_auxiliary_points=include_auxiliary_points
        )

    HOUSE_MEANINGS = {
        "First_House": "Identity/Self",
        "Second_House": "Values/Resources",
        "Third_House": "Communication/Learning",
        "Fourth_House": "Home/Foundations",
        "Fifth_House": "Creativity/Pleasure",
        "Sixth_House": "Work/Health",
        "Seventh_House": "Relationships",
        "Eighth_House": "Transformation",
        "Ninth_House": "Philosophy/Travel",
        "Tenth_House": "Career/Status",
        "Eleventh_House": "Groups/Hopes",
        "Twelfth_House": "Spirituality/Hidden"
    }

    ASPECT_MEANINGS = {
        "major": {
            "conjunction": ("0°", "Blending/intensifying of energies"),
            "opposition": ("180°", "Awareness, tension, or balance"),
            "trine": ("120°", "Harmony, flow, and ease"),
            "square": ("90°", "Challenge, growth, and action"),
            "sextile": ("60°", "Opportunity and cooperation")
        },
        "minor": {
            "quincunx": ("150°", "Adjustment and adaptation"),
            "semi_sextile": ("30°", "Subtle connection"),
            "quintile": ("72°", "Creative potential"),
            "bi_quintile": ("144°", "Unique talents")
        }
    }

    PLANET_ORDER = [
        'Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
        'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto',
        'Mean_Node', 'True_Node', 'Mean_South_Node', 'True_South_Node',
        'Chiron', 'Mean_Lilith'
    ]

    ASPECT_NATURES = {
        "conjunction": "Emphasizing",
        "sextile": "Supportive",
        "square": "Challenging",
        "trine": "Harmonious",
        "opposition": "Awareness",
        "quincunx": "Adjustment"
    }

    SIGN_NAMES = {
        'Ari': 'Aries',
        'Tau': 'Taurus',
        'Gem': 'Gemini',
        'Can': 'Cancer',
        'Leo': 'Leo',
        'Vir': 'Virgo',
        'Lib': 'Libra',
        'Sco': 'Scorpio',
        'Sag': 'Sagittarius',
        'Cap': 'Capricorn',
        'Aqu': 'Aquarius',
        'Pis': 'Pisces'
    }

    def _gather_summary_data(self) -> dict:
        """Gather raw summary data before formatting"""
        return {
            "chart_type": f"{self.transit_analysis.natal.zodiac_type} / {self.transit_analysis.natal.houses_system_name}",
            "natal_ascendant": {
                "sign": self.transit_analysis.natal.first_house.sign,
                "position": round(float(self.transit_analysis.natal.first_house.position), 2)
            },
            "transit_ascendant": {
                "sign": self.transit_analysis.transit.first_house.sign,
                "position": round(float(self.transit_analysis.transit.first_house.position), 2)
            },
            "natal_midheaven": {
                "sign": self.transit_analysis.natal.tenth_house.sign,
                "position": round(float(self.transit_analysis.natal.tenth_house.position), 2)
            },
            "transit_midheaven": {
                "sign": self.transit_analysis.transit.tenth_house.sign,
                "position": round(float(self.transit_analysis.transit.tenth_house.position), 2)
            },
            "lunar_phase_natal": str(self.transit_analysis.natal.lunar_phase.moon_phase_name),
            "lunar_phase_transit": str(self.transit_analysis.transit.lunar_phase.moon_phase_name),
            "current_retrogrades": self._get_retrograde_summary(),
            "major_transits": self._get_major_transits_summary()
        }

    def _gather_planetary_data(self) -> list:
        """Gather raw planetary data before formatting"""
        data = []
        natal_planets = {p.name: p for p in get_available_planets_list(self.transit_analysis.natal)}
        transit_planets = {p.name: p for p in get_available_planets_list(self.transit_analysis.transit)}

        for planet_name in self.PLANET_ORDER:
            if planet_name in natal_planets:
                natal_planet = natal_planets[planet_name]
                transit_planet = transit_planets[planet_name]

                data.append({
                    "planet": planet_name,
                    "natal": {
                        "sign": natal_planet.sign,
                        "position": round(float(natal_planet.position), 2),
                        "house": natal_planet.house
                    },
                    "transit": {
                        "sign": transit_planet.sign,
                        "position": round(float(transit_planet.position), 2),
                        "house": transit_planet.house
                    },
                    "transit_status": {
                        "retrograde": transit_planet.retrograde,
                        "different_sign": natal_planet.sign != transit_planet.sign,
                        "different_house": natal_planet.house != transit_planet.house
                    }
                })
        return data

    def _gather_houses_data(self) -> list:
        """Gather raw house data before formatting"""
        data = []
        natal_houses = get_houses_list(self.transit_analysis.natal)
        transit_houses = get_houses_list(self.transit_analysis.transit)

        for natal_house, transit_house in zip(natal_houses, transit_houses):
            data.append({
                "house": natal_house.name,
                "meaning": self.HOUSE_MEANINGS.get(natal_house.name, ""),
                "natal": {
                    "sign": natal_house.sign,
                    "position": round(float(natal_house.position), 2)
                },
                "transit": {
                    "sign": transit_house.sign,
                    "position": round(float(transit_house.position), 2)
                },
                "different_sign": natal_house.sign != transit_house.sign
            })
        return data

    def _gather_aspects_data(self) -> dict:
        """Gather raw aspect data before formatting"""
        traditional_aspects = ['conjunction', 'opposition', 'trine', 'square', 'sextile']
        auxiliary_points = ['Mean_Node', 'True_Node', 'Mean_South_Node', 'True_South_Node', 'Mean_Lilith']

        major_aspects = []
        minor_aspects = []

        # Use already filtered aspects from model
        for aspect in self.transit_analysis.model.aspects:
            aspect_data = {
                "natal_planet": aspect.p2_name,
                "transit_planet": aspect.p1_name,
                "aspect_type": aspect.aspect,
                "orbit": round(float(aspect.orbit), 2),
                "nature": self._get_aspect_nature(aspect.aspect),
                "is_major": aspect.is_major,
                "is_traditional": aspect.aspect.lower() in traditional_aspects,
                "involves_auxiliary": (aspect.p1_name in auxiliary_points or
                                       aspect.p2_name in auxiliary_points)
            }

            if aspect.is_major:
                major_aspects.append(aspect_data)
            else:
                minor_aspects.append(aspect_data)

        return {
            "explanations": self.ASPECT_MEANINGS,
            "major_aspects": major_aspects,
            "minor_aspects": minor_aspects,
            "total_count": len(major_aspects) + len(minor_aspects)
        }

    def _get_aspect_nature(self, aspect_type: str) -> str:
        """Returns the nature/quality of an aspect."""
        return self.ASPECT_NATURES.get(aspect_type.lower(), "Other")

    def _get_retrograde_summary(self) -> str:
        """Summarizes current retrograde planets."""
        retrograde_planets = [
            planet.name for planet in get_available_planets_list(self.transit_analysis.transit)
            if planet.retrograde
        ]
        return ", ".join(retrograde_planets) if retrograde_planets else "None"

    def _get_significant_transits(self) -> str:
        """Summarizes major transit_status between natal and transit charts."""
        transit_status = []

        # Check for sign differences in outer planets
        for planet in self.planetary_data:
            if planet["planet"] in ['Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']:
                if planet["transit_status"]["different_sign"]:
                    transit_status.append(
                        f"{planet['planet']} is in {self.SIGN_NAMES[planet['transit']['sign']]}"
                        f"(natal: {self.SIGN_NAMES[planet['natal']['sign']]})"
                    )
                if planet["transit_status"]["retrograde"]:
                    transit_status.append(f"{planet['planet']} is retrograde in {self.SIGN_NAMES[planet['transit']['sign']]}")
                if planet["transit_status"]["different_house"]:
                    transit_status.append(
                        f"{planet['planet']} is in the {planet['transit']['house']} "
                        f"(natal: {planet['natal']['house']})"
                    )

        # Check for multiple planets in the same house
        house_occupants = {}
        for planet in self.planetary_data:
            house = planet["transit"]["house"]
            if house not in house_occupants:
                house_occupants[house] = []
            house_occupants[house].append(planet["planet"])

        for house, planets in house_occupants.items():
            if len(planets) >= 3:  # If 3 or more planets in same house
                transit_status.append(f"Concentration of planets in {house}: {', '.join(planets)}")

        if not transit_status:
            return ""

        return "SIGNIFICANT TRANSITS:\n• " + "\n• ".join(transit_status) + "\n"

    def _get_major_transits_summary(self) -> str:
        """Summarizes most significant current transits with their nature."""
        major_transits = []
        for aspect in self.transit_analysis.aspects.all_aspects:
            # Focus on outer planet transits and tight orbs
            if (aspect.p1_name in ['Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'] and
                    aspect.is_major and aspect.orbit < 2):
                nature = self._get_aspect_nature(aspect.aspect)
                major_transits.append(
                    f"{aspect.p1_name}-{aspect.p2_name} {aspect.aspect} ({nature})"
                )
        return "; ".join(major_transits[:5])  # Show top 5 major transits

    def _get_interpretation_summary(self) -> str:
        """Generates a brief interpretation summary focusing on key transits."""
        # Get the most significant transits (outer planets in major aspects with tight orbs)
        key_transits = []
        for aspect in self.transit_analysis.aspects.all_aspects:
            if (aspect.p1_name in ['Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'] and
                    aspect.is_major and abs(aspect.orbit) <= 1):
                key_transits.append({
                    'transit_planet': aspect.p1_name,
                    'natal_planet': aspect.p2_name,
                    'aspect': aspect.aspect,
                    'nature': self._get_aspect_nature(aspect.aspect),
                    'orbit': aspect.orbit
                })

        if not key_transits:
            return "KEY TRANSITS:\nNo major outer planet transits with tight orbs (< 1°) at this time."

        summary = "KEY TRANSITS:\n"
        summary += "The following significant transits are currently active (orb < 1°):\n"

        # First sort by orbit
        key_transits.sort(key=lambda x: abs(x['orbit']))

        # Then group by planet but maintain orbit-based ordering within each group
        summary = "KEY TRANSITS:\n"
        summary += "The following significant transits are currently active (orb < 1°):\n\n"

        for planet in ['Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']:
            planet_transits = [t for t in key_transits if t['transit_planet'] == planet]
            if planet_transits:
                summary += f"{planet} Transits:\n"
                for transit in planet_transits:
                    summary += f"• {transit['aspect']} natal {transit['natal_planet']}"
                    summary += f" ({transit['nature']} - orb: {round(transit['orbit'], 2)}°)\n"
                summary += "\n"

        return summary

    def get_summary_section(self) -> None:
        """Creates summary section of the report using gathered data."""
        major_transits = self.summary_data["major_transits"].split("; ")

        summary_data = [
            ["SUMMARY INFORMATION", ""],
            ["Chart Type", self.summary_data["chart_type"]],
            ["Natal Ascendant", f"{self.summary_data['natal_ascendant']['sign']} {self.summary_data['natal_ascendant']['position']}°"],
            ["Transit Ascendant", f"{self.summary_data['transit_ascendant']['sign']} {self.summary_data['transit_ascendant']['position']}°"],
            ["Natal Midheaven", f"{self.summary_data['natal_midheaven']['sign']} {self.summary_data['natal_midheaven']['position']}°"],
            ["Transit Midheaven", f"{self.summary_data['transit_midheaven']['sign']} {self.summary_data['transit_midheaven']['position']}°"],
            ["Lunar Phase (Natal)", self.summary_data["lunar_phase_natal"]],
            ["Lunar Phase (Transit)", self.summary_data["lunar_phase_transit"]],
            ["Current Retrogrades", self.summary_data["current_retrogrades"]],
            ["Major Transits:", ""]
        ]
        # Add each major transit on its own line, indented
        for transit in major_transits:
            summary_data.append(["  " + transit, ""])

        table = AsciiTable(summary_data)
        table.inner_heading_row_border = False
        table.inner_row_border = False
        table.padding_left = 1
        table.padding_right = 1
        table.justify_columns = {0: 'left', 1: 'left'}
        self.summary_table = table.table

    def get_combined_planets_table(self) -> None:
        planets_data = [
            ["PLANETARY POSITIONS", "", "", "", "", ""],
            ["", "NATAL", "NATAL", "TRANSIT", "TRANSIT", ""],
            ["Planet", "Position", "House", "Position", "House", "Transit Status"],
            ["=" * 10, "=" * 12, "=" * 12, "=" * 12, "=" * 12, "=" * 10]
        ]

        # Define planet groups
        groups = [
            ("Luminaries", ['Sun', 'Moon']),
            ("Personal Planets", ['Mercury', 'Venus', 'Mars']),
            ("Social Planets", ['Jupiter', 'Saturn']),
            ("Outer Planets", ['Uranus', 'Neptune', 'Pluto']),
            ("Nodes & Points", ['Mean_Node', 'True_Node', 'Mean_South_Node', 'True_South_Node', 'Chiron', 'Mean_Lilith'])
        ]

        # Add each group with a header
        first_group = True
        for group_name, group_planets in groups:
            if not first_group:
                planets_data.append(["-" * 10, "-" * 12, "-" * 12, "-" * 12, "-" * 12, "-" * 10])  # Separator
            planets_data.append([f"-- {group_name} --", "", "", "", "", ""])

            for planet in self.planetary_data:
                if planet["planet"] in group_planets:
                    # Format status string
                    status_parts = []
                    if planet["transit_status"]["retrograde"]:
                        status_parts.append("R")
                    if planet["transit_status"]["different_sign"]:
                        status_parts.append("→")
                    if planet["transit_status"]["different_house"]:
                        status_parts.append("↕")
                    status = " ".join(status_parts)

                    planets_data.append([
                        planet["planet"],
                        f"{planet['natal']['sign']} {planet['natal']['position']}°",
                        planet["natal"]["house"],
                        f"{planet['transit']['sign']} {planet['transit']['position']}°",
                        planet["transit"]["house"],
                        status
                    ])
            first_group = False

        table = AsciiTable(planets_data)
        table.inner_row_border = False
        table.padding_left = 1
        table.padding_right = 1
        table.justify_columns = {0: 'left', 1: 'right', 2: 'left', 3: 'right', 4: 'left', 5: 'center'}
        self.combined_planets_table = table.table

    def get_filtered_aspects_table(self,
                                   max_orb: float = 8.0,
                                   include_minor_aspects: bool = True,
                                   traditional_aspects_only: bool = False,
                                   max_aspects: int = None,
                                   include_auxiliary_points: bool = True) -> None:
        """Creates aspects table using gathered data."""
        # Create aspect explanation from the stored meanings
        aspect_explanation = "ASPECT EXPLANATIONS:\nMajor aspects (strongest influence):\n"
        for aspect, (angle, meaning) in self.ASPECT_MEANINGS["major"].items():
            aspect_explanation += f"  {aspect.title()} ({angle}):   {meaning}\n"

        aspect_explanation += "\nMinor aspects (subtle influence):\n"
        for aspect, (angle, meaning) in self.ASPECT_MEANINGS["minor"].items():
            aspect_explanation += f"  {aspect.title()} ({angle}):   {meaning}\n"

        aspect_explanation += "\nOrb: Distance from exact aspect angle (smaller = stronger influence)"

        aspects_data = [
            ["SIGNIFICANT ASPECTS", "", "", "", "", ""],
            ["=" * 20, "=" * 15, "=" * 15, "=" * 8, "=" * 12, "=" * 12],  # Top border
            ["Natal Planet", "Aspect Type", "Transit Planet", "Orb", "Nature", "Significance"]
        ]

        filtered_major = [
            aspect for aspect in self.aspects_data["major_aspects"]
            if (aspect["orbit"] < max_orb and
                (not traditional_aspects_only or aspect["is_traditional"]) and
                (include_auxiliary_points or not aspect["involves_auxiliary"]))
        ]

        filtered_minor = []
        if include_minor_aspects:
            filtered_minor = [
                aspect for aspect in self.aspects_data["minor_aspects"]
                if (aspect["orbit"] < max_orb and
                    (not traditional_aspects_only or aspect["is_traditional"]) and
                    (include_auxiliary_points or not aspect["involves_auxiliary"]))
            ]

        if max_aspects:
            major_count = min(len(filtered_major), max_aspects // 2)
            minor_count = min(len(filtered_minor), max_aspects - major_count)
            filtered_major = filtered_major[:major_count]
            filtered_minor = filtered_minor[:minor_count]

        if filtered_major:
            aspects_data.append(["-" * 20, "-" * 15, "-" * 15, "-" * 8, "-" * 12, "-" * 12])  # Add separator
            aspects_data.append(["MAJOR ASPECTS:", "", "", "", "", ""])
            for aspect in filtered_major:
                aspects_data.append([
                    aspect["natal_planet"],
                    aspect["aspect_type"],
                    aspect["transit_planet"],
                    aspect["orbit"],
                    aspect["nature"],
                    "Major"
                ])

        if filtered_minor:
            aspects_data.append(["-" * 20, "-" * 15, "-" * 15, "-" * 8, "-" * 12, "-" * 12])  # Add separator
            aspects_data.append(["MINOR ASPECTS:", "", "", "", "", ""])
            for aspect in filtered_minor:
                aspects_data.append([
                    aspect["natal_planet"],
                    aspect["aspect_type"],
                    aspect["transit_planet"],
                    aspect["orbit"],
                    aspect["nature"],
                    "Minor"
                ])

        table = AsciiTable(aspects_data)
        table.inner_row_border = False
        table.padding_left = 1
        table.padding_right = 1
        self.aspects_explanation = aspect_explanation
        self.aspects_table = table.table

    def get_combined_houses_table(self) -> None:
        """Creates combined houses table using gathered data."""
        houses_data = [
            ["HOUSE CUSPS (Starting degrees of each house)", "", "", ""],
            ["House", "Natal Position", "Transit Position", "Transit Status"],
            ["-" * 45, "-" * 20, "-" * 20, "-" * 6],
            ["Note: Each house begins at its listed degree and extends to the next house", "", "", ""],
        ]

        for house in self.houses_data:
            house_name = f"{house['house']} ({house['meaning']})" if house['meaning'] else house['house']
            houses_data.append([
                house_name,
                f"{house['natal']['sign']} ({house['natal']['position']}°)",
                f"{house['transit']['sign']} ({house['transit']['position']}°)",
                "→" if house["different_sign"] else ""
            ])

        table = AsciiTable(houses_data)
        table.inner_row_border = False
        table.padding_left = 1
        table.padding_right = 1
        # Make the explanation row span all columns
        table.justify_columns = {0: 'left', 1: 'left', 2: 'left', 3: 'left'}
        self.combined_houses_table = table.table

    def generate_json_report(self) -> str:
        """Generate JSON directly from stored data"""
        try:
            # Add full sign names to existing data structures
            def add_full_sign_names(data: dict) -> dict:
                if "sign" in data:
                    return {
                        **data,
                        "sign": {
                            "abbr": data["sign"],
                            "full": self.SIGN_NAMES[data["sign"]]
                        }
                    }
                return data

            # Enhance summary data with full sign names
            summary_data = {
                **self.summary_data,
                "natal_ascendant": add_full_sign_names(self.summary_data["natal_ascendant"]),
                "transit_ascendant": add_full_sign_names(self.summary_data["transit_ascendant"]),
                "natal_midheaven": add_full_sign_names(self.summary_data["natal_midheaven"]),
                "transit_midheaven": add_full_sign_names(self.summary_data["transit_midheaven"])
            }

            # Group planetary positions
            planetary_positions = {
                "by_group": {
                    "luminaries": [],
                    "personal_planets": [],
                    "social_planets": [],
                    "outer_planets": [],
                    "nodes_and_points": []
                },
                "all": self.planetary_data
            }

            # Group planets
            for planet in self.planetary_data:
                planet_data = {
                    **planet,
                    "natal": add_full_sign_names(planet["natal"]),
                    "transit": add_full_sign_names(planet["transit"])
                }
                if planet["planet"] in ['Sun', 'Moon']:
                    planetary_positions["by_group"]["luminaries"].append(planet_data)
                elif planet["planet"] in ['Mercury', 'Venus', 'Mars']:
                    planetary_positions["by_group"]["personal_planets"].append(planet_data)
                elif planet["planet"] in ['Jupiter', 'Saturn']:
                    planetary_positions["by_group"]["social_planets"].append(planet_data)
                elif planet["planet"] in ['Uranus', 'Neptune', 'Pluto']:
                    planetary_positions["by_group"]["outer_planets"].append(planet_data)
                else:
                    planetary_positions["by_group"]["nodes_and_points"].append(planet_data)

            # Add full sign names to house data
            house_cusps = [
                {
                    **house,
                    "natal": add_full_sign_names(house["natal"]),
                    "transit": add_full_sign_names(house["transit"])
                }
                for house in self.houses_data
            ]

            # Add angles to aspects
            aspects_data = {
                **self.aspects_data,
                "major_aspects": [
                    {**aspect}  # Just use the aspect data as is
                    for aspect in self.aspects_data["major_aspects"]
                ],
                "minor_aspects": [
                    {**aspect}  # Just use the aspect data as is
                    for aspect in self.aspects_data["minor_aspects"]
                ]
            }

            report_data = {
                "title": self.report_title.strip(),
                "natal_birth_data": {
                    "date": f"{self.transit_analysis.natal.day}/{self.transit_analysis.natal.month}/{self.transit_analysis.natal.year}",
                    "time": f"{self.transit_analysis.natal.hour}:{self.transit_analysis.natal.minute}",
                    "location": f"{self.transit_analysis.natal.city}, {self.transit_analysis.natal.nation}",
                    "longitude": self.transit_analysis.natal.lng,
                    "latitude": self.transit_analysis.natal.lat
                },
                "current_analysis_time": self.transit_analysis.transit_time.strftime('%Y-%m-%d %H:%M'),
                "current_location": (
                    f"{self.transit_analysis.transit.city}, {self.transit_analysis.transit.nation}"
                    if self.transit_analysis.transit.city != self.transit_analysis.natal.city
                    else None
                ),
                "significant_transits": {
                    "major_planet_transits": [
                        planet for planet in self.planetary_data
                        if planet["planet"] in ['Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
                        and (planet["transit_status"]["different_sign"] or
                             planet["transit_status"]["retrograde"] or
                             planet["transit_status"]["different_house"])
                    ],
                    "house_concentrations": {
                        house: [p["planet"] for p in self.planetary_data if p["transit"]["house"] == house]
                        for house in set(p["transit"]["house"] for p in self.planetary_data)
                        if len([p for p in self.planetary_data if p["transit"]["house"] == house]) >= 3
                    }
                },
                "summary_information": summary_data,
                "planetary_positions": planetary_positions,
                "house_cusps": house_cusps,
                "aspects": aspects_data
            }

            return json.dumps(report_data, indent=4)
        except Exception as e:
            logging.error(f"Error generating JSON report: {e}")
            raise

    def get_full_report(self) -> str:
        """Returns the complete transit analysis report."""
        transit_status_legend = (
            "COMPARISON TO NATAL POSITIONS:\n"
            "R = Retrograde (currently moving backwards)\n"
            "→ = New Sign (transit position in different sign than natal)\n"
            "↕ = New House (transit position in different house than natal)"
        )

        report_explanation = (
            "ABOUT THIS REPORT:\n"
            f"Chart calculated using {self.transit_analysis.natal.zodiac_type} zodiac "
            f"and {self.transit_analysis.natal.houses_system_name} house system.\n"
            "Positions are shown as degrees within each sign (0-30°).\n"
            "Aspects show relationships between natal and transit positions, "
            "with smaller orbs (differences from exact) indicating stronger influences."
        )
        current_location = (f"\nCURRENT LOCATION: {self.transit_analysis.transit.city}, {self.transit_analysis.transit.nation}"
                            if self.transit_analysis.transit.city != self.transit_analysis.natal.city else "")

        interpretation_summary = self._get_interpretation_summary()
        significant_transits = self._get_significant_transits()
        return (
            f"{self.report_title}\n\n"
            f"{interpretation_summary}\n"  # Add interpretation at top
            f"{significant_transits}"
            f"NATAL BIRTH DATA:\n"
            f"{self.data_table}\n\n"
            f"TRANSIT ANALYSIS TIME: {self.transit_analysis.transit_time.strftime('%Y-%m-%d %H:%M')}"
            f"{current_location}\n\n"
            f"{self.summary_table}\n\n"
            f"{self.combined_planets_table}\n"
            f"{transit_status_legend}\n\n"
            f"{self.combined_houses_table}\n\n"
            f"{self.aspects_explanation}\n\n"  # Add aspect explanation before the table
            f"NATAL-TRANSIT RELATIONSHIPS:\n"
            f"{self.aspects_table}\n\n"
            f"{report_explanation}"
        )


if __name__ == "__main__":
    # from kerykeion.utilities import setup_logging
    # setup_logging(level="debug")

    # # Test basic natal report
    # john = AstrologicalSubject("John", 1975, 10, 10, 21, 15, "Roma", "IT")
    # report = Report(john)
    # report.print_report()

    # Test transit analysis report
    transit_analysis = TransitAnalysis("John", 1975, 10, 10, 21, 15,
                                       birth_city="Roma", birth_country="IT",
                                       transit_city="London", transit_country="GB"
                                       )
    analysis_report = TransitAnalysisReport(transit_analysis, include_minor_aspects=True, traditional_aspects_only=False)
    # Only traditional aspects (conjunction, opposition, trine, square, sextile)
    analysis_report = TransitAnalysisReport(
        transit_analysis,
        traditional_aspects_only=True
    )
    print(analysis_report.get_full_report())

    # All aspects but with tight orbs
    analysis_report = TransitAnalysisReport(
        transit_analysis,
        max_orb=5.0
    )
    text_report = analysis_report.get_full_report()

    # Save output to a text file
    output_file_path = "transit_analysis_report.txt"  # Specify the file name
    with open(output_file_path, "w", encoding="utf-8") as file:
        file.write(text_report)
    print(f"Text report saved to: {output_file_path}")

    # Traditional aspects with tight orbs
    analysis_report = TransitAnalysisReport(
        transit_analysis,
        max_orb=5.0,
        traditional_aspects_only=True
    )
    print(analysis_report.get_full_report())

    # Generate JSON output
    json_output = analysis_report.generate_json_report()

    # # Save JSON output to a text file
    # output_file_path = "transit_analysis_report.json"  # Specify the file name
    # with open(output_file_path, "w", encoding="utf-8") as file:
    #     file.write(json_output)
    # print(f"JSON report saved to: {output_file_path}")
