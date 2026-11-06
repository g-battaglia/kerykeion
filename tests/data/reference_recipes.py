"""Reference-production recipes without importing or reading model baselines."""

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ReportGenerator
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS, ALL_ACTIVE_ASPECTS
from tests.data.test_subjects_matrix import TEMPORAL_SUBJECTS, GEOGRAPHIC_SUBJECTS

_ARABIC_GOLDEN_ACTIVE = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
    "True_North_Lunar_Node",
    "Chiron",
    "Mean_Lilith",
    "Ascendant",
    "Pars_Fortunae",
    "Pars_Spiritus",
    "Pars_Amoris",
    "Pars_Fidei",
]


def create_subject_from_id(subject_id: str, house_system: str = "P"):
    """Create an astrological subject from its ID in the test matrix."""
    # Check temporal subjects first
    for data in TEMPORAL_SUBJECTS:
        if data["id"] == subject_id:
            return AstrologicalSubjectFactory.from_birth_data(
                name=data["name"],
                year=data["year"],
                month=data["month"],
                day=data["day"],
                hour=data["hour"],
                minute=data["minute"],
                lat=data["lat"],
                lng=data["lng"],
                tz_str=data["tz_str"],
                online=False,
                suppress_geonames_warning=True,
                houses_system_identifier=house_system,
            )

    # Check geographic subjects
    for data in GEOGRAPHIC_SUBJECTS:
        if data["id"] == subject_id:
            return AstrologicalSubjectFactory.from_birth_data(
                name=f"Test_{data['id']}",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lat=data["lat"],
                lng=data["lng"],
                tz_str=data["tz_str"],
                online=False,
                suppress_geonames_warning=True,
                houses_system_identifier=house_system,
            )

    raise ValueError(f"Subject ID '{subject_id}' not found in test matrix")


def _create_arabic_subject(subject_id: str):
    """Build a subject with Arabic Parts active, matching the golden generator."""
    for data in TEMPORAL_SUBJECTS:
        if data["id"] == subject_id:
            return AstrologicalSubjectFactory.from_birth_data(
                name=data["name"],
                year=data["year"],
                month=data["month"],
                day=data["day"],
                hour=data["hour"],
                minute=data["minute"],
                lat=data["lat"],
                lng=data["lng"],
                tz_str=data["tz_str"],
                online=False,
                suppress_geonames_warning=True,
                active_points=_ARABIC_GOLDEN_ACTIVE,
            )
    for data in GEOGRAPHIC_SUBJECTS:
        if data["id"] == subject_id:
            return AstrologicalSubjectFactory.from_birth_data(
                name=f"Test_{data['id']}",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lat=data["lat"],
                lng=data["lng"],
                tz_str=data["tz_str"],
                online=False,
                suppress_geonames_warning=True,
                active_points=_ARABIC_GOLDEN_ACTIVE,
            )
    raise ValueError(f"Subject ID '{subject_id}' not found in test matrix")


def print_ancient_rome_report() -> None:
    """Render the historical report independently of any saved reference."""
    subject = AstrologicalSubjectFactory.from_birth_data(
        name="Ancient Rome Subject",
        year=100,
        month=1,
        day=1,
        hour=12,
        minute=0,
        lat=41.9028,
        lng=12.4964,
        tz_str="Europe/Rome",
        online=False,
        suppress_geonames_warning=True,
        active_points=ALL_ACTIVE_POINTS,
    )
    chart = ChartDataFactory.create_natal_chart_data(
        subject,
        active_aspects=ALL_ACTIVE_ASPECTS,
    )
    ReportGenerator(chart).print_report()
