"""Example: Generate a basic subject report with ReportGenerator."""

from __future__ import annotations

from kerykeion import ReportGenerator, AstrologicalSubjectFactory

JOHN_LOCATION = {
    "city": "Liverpool",
    "nation": "GB",
    "lat": 53.4084,
    "lng": -2.9916,
    "tz_str": "Europe/London",
    "online": False,
    "suppress_geonames_warning": True,
}


if __name__ == "__main__":
    subject = AstrologicalSubjectFactory.from_birth_data(
        name="John Lennon",
        year=1940,
        month=10,
        day=9,
        hour=18,
        minute=30,
        **JOHN_LOCATION,
    )

    report = ReportGenerator(subject, include_aspects=False)
    report.print_report(include_aspects=False)
