from kerykeion import AstrologicalSubject
from terminaltables import AsciiTable

class Report:
    """
    Create a report for a Kerykeion instance.
    """

    report_title: str
    data_table: str
    planets_table: str
    houses_table: str

    def __init__(self, instance: AstrologicalSubject):
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
            for planet in self.instance.planets_list
        ]

        self.planets_table = AsciiTable(planets_data).table

    def get_houses_table(self) -> None:
        """
        Creates the houses table.
        """

        houses_data = [["House", "Sign", "Position"]] + [
            [house.name, house.sign, round(float(house.position), 2)] for house in self.instance.houses_list
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


if __name__ == "__main__":
    from kerykeion.utilities import setup_logging
    setup_logging(level="debug")

    john = AstrologicalSubject("John", 1975, 10, 10, 21, 15, "Roma", "IT")
    report = Report(john)
    report.print_report()
