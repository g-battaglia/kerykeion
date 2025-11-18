from kerykeion import (
    AstrologicalSubjectFactory,
    MoonPhaseDetailsFactory,
    MoonPhaseOverviewModel,
)


def test_lunar_phase_details_factory_produces_overview_model():
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Test",
        1993,
        10,
        10,
        12,
        12,
        "London",
        "GB",
        suppress_geonames_warning=True,
    )

    overview = MoonPhaseDetailsFactory.from_subject(subject)

    assert isinstance(overview, MoonPhaseOverviewModel)
    assert overview.moon.phase is not None
    assert overview.moon.phase_name == subject.lunar_phase.moon_phase_name  # type: ignore[union-attr]
    assert overview.moon.emoji == subject.lunar_phase.moon_emoji  # type: ignore[union-attr]
    assert overview.moon.detailed is not None
    assert overview.moon.detailed.illumination_details is not None  # type: ignore[union-attr]
    assert overview.moon.detailed.upcoming_phases is not None  # type: ignore[union-attr]
    assert overview.moon.detailed.upcoming_phases.full_moon is not None  # type: ignore[union-attr]

    # Eclipses: ensure that Swiss Ephemeris is used to populate next events
    assert overview.moon.next_lunar_eclipse is not None
    assert isinstance(overview.moon.next_lunar_eclipse.timestamp, int)
    assert overview.moon.next_lunar_eclipse.type is not None

    assert overview.location is not None
    assert overview.sun is not None
    assert overview.sun.next_solar_eclipse is not None
    assert isinstance(overview.sun.next_solar_eclipse.timestamp, int)  # type: ignore[union-attr]
    assert overview.sun.next_solar_eclipse.type is not None  # type: ignore[union-attr]

    # Basic solar timing and position fields should be populated
    assert overview.sun.sunrise is not None  # type: ignore[union-attr]
    assert overview.sun.sunrise_timestamp is not None  # type: ignore[union-attr]
    assert overview.sun.sunset is not None  # type: ignore[union-attr]
    assert overview.sun.sunset_timestamp is not None  # type: ignore[union-attr]
    assert overview.sun.solar_noon is not None  # type: ignore[union-attr]
    assert overview.sun.day_length is not None  # type: ignore[union-attr]
    assert overview.sun.position is not None  # type: ignore[union-attr]
