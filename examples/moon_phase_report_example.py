"""Example: Generate a Moon Phase Overview report (MoonPhaseOverviewModel)."""

from __future__ import annotations

from kerykeion import AstrologicalSubjectFactory, MoonPhaseDetailsFactory, ReportGenerator

if __name__ == "__main__":
    subject = AstrologicalSubjectFactory.from_birth_data(
        name="John Lennon",
        year=1940,
        month=10,
        day=9,
        hour=18,
        minute=30,
        city="Liverpool",
        nation="GB",
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
    )

    overview = MoonPhaseDetailsFactory.from_subject(subject)
    report = ReportGenerator(overview)
    report.print_report()
