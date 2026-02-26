"""Example: Generate the Moon Phase Overview JSON (MoonPhaseOverviewModel)."""

from __future__ import annotations

from kerykeion import AstrologicalSubjectFactory, MoonPhaseDetailsFactory

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

    # Full JSON (exclude None fields for readability)
    print(overview.model_dump_json(exclude_none=True, indent=2))
