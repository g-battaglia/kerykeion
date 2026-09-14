"""Technique reports: render profections, firdaria, horary and dominants as text."""

from kerykeion import (
    AstrologicalSubjectFactory,
    DominantsFactory,
    FirdariaFactory,
    HoraryIndicatorsFactory,
    MutualReceptionsFactory,
    ProfectionsFactory,
    ReportGenerator,
    ZodiacalReleasingFactory,
)


def main() -> None:
    natal = AstrologicalSubjectFactory.from_birth_data(
        name="Grace Hopper",
        year=1906,
        month=12,
        day=9,
        hour=11,
        minute=30,
        lng=-73.9857,
        lat=40.7484,
        tz_str="America/New_York",
        city="New York",
        nation="US",
        online=False,
        calculate_dignities=True,
    )
    target = "2026-06-04"

    # The generator only renders: compute each technique first, then hand the
    # result over. Every model below is a report input in its own right.
    reports = [
        ProfectionsFactory.from_subject(natal, target_date=target),
        FirdariaFactory.from_subject(natal, target_date=target),
        MutualReceptionsFactory.from_subject(natal),
        HoraryIndicatorsFactory.from_subject(natal, is_moon_void=False),
        DominantsFactory.from_subject(natal, strategy="modern"),
        ZodiacalReleasingFactory.from_subject(natal, lot="fortune", levels=2, target_date=target),
    ]

    for result in reports:
        ReportGenerator(result).print_report()
        print()


if __name__ == "__main__":
    main()
