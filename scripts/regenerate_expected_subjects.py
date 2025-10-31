#!/usr/bin/env python3
"""
Utility script to regenerate the expected astrological subject data used in tests.

This mirrors the parameters used in TestAstrologicalSubject and
TestAstrologicalSubjectJyotish to keep fixtures in sync with real computations.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from pprint import pformat
from typing import Dict, Iterable
from typing import get_args

from kerykeion import AstrologicalSubjectFactory
from kerykeion.schemas import AstrologicalPoint

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "tests" / "data" / "expected_astrological_subjects.py"

BASE_FIELDS = [
    "name",
    "year",
    "month",
    "day",
    "hour",
    "minute",
    "city",
    "nation",
    "lng",
    "lat",
    "tz_str",
    "zodiac_type",
    "julian_day",
    "local_time",
    "utc_time",
]

POINT_FIELDS = [
    "ascendant",
    "descendant",
    "medium_coeli",
    "imum_coeli",
    "sun",
    "moon",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "pluto",
    "mean_north_lunar_node",
    "true_north_lunar_node",
    "mean_south_lunar_node",
    "true_south_lunar_node",
]

HOUSE_FIELDS = [
    "first_house",
    "second_house",
    "third_house",
    "fourth_house",
    "fifth_house",
    "sixth_house",
    "seventh_house",
    "eighth_house",
    "ninth_house",
    "tenth_house",
    "eleventh_house",
    "twelfth_house",
]


def iso_to_decimal_hours(iso_datetime: str | None) -> float:
    """Convert an ISO formatted datetime string to decimal hours."""
    if not iso_datetime:
        return 0.0
    dt = datetime.fromisoformat(iso_datetime)
    total_seconds = (
        dt.hour * 3600
        + dt.minute * 60
        + dt.second
        + dt.microsecond / 1_000_000
    )
    return round(total_seconds / 3600, 12)


def extract_subject_data(subject) -> Dict[str, object]:
    """Build the expected dictionary structure for a subject."""
    data: Dict[str, object] = {}

    for field in BASE_FIELDS:
        if field == "local_time":
            data[field] = iso_to_decimal_hours(subject.iso_formatted_local_datetime)
        elif field == "utc_time":
            data[field] = iso_to_decimal_hours(subject.iso_formatted_utc_datetime)
        else:
            data[field] = getattr(subject, field)

    def dump_points(names: Iterable[str]) -> None:
        for name in names:
            point = getattr(subject, name, None)
            if point is not None:
                data[name] = point.model_dump(exclude_none=True)

    dump_points(POINT_FIELDS)
    dump_points(HOUSE_FIELDS)

    if getattr(subject, "lunar_phase", None) is not None:
        data["lunar_phase"] = subject.lunar_phase.model_dump(exclude_none=True)

    return data


def regenerate_expected_subjects() -> None:
    """Regenerate both tropical and sidereal expected subject dictionaries."""
    all_points = list(get_args(AstrologicalPoint))

    tropical_subject = AstrologicalSubjectFactory.from_birth_data(
        "Johnny Depp",
        1963,
        6,
        9,
        0,
        0,
        "Owensboro",
        "US",
        suppress_geonames_warning=True,
        active_points=all_points,
    )
    tropical_data = extract_subject_data(tropical_subject)

    jyotish_subject = AstrologicalSubjectFactory.from_birth_data(
        "Johnny Depp",
        1963,
        6,
        9,
        0,
        0,
        "Owensboro",
        "US",
        zodiac_type="Sidereal",
        sidereal_mode="LAHIRI",
        houses_system_identifier="W",
        suppress_geonames_warning=True,
    )
    jyotish_data = extract_subject_data(jyotish_subject)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    content = (
        "# Auto-generated expected subject data for tests.\n"
        "# Generated via scripts/regenerate_expected_subjects.py\n\n"
        "EXPECTED_TROPICAL_SUBJECT = "
        + pformat(tropical_data, width=100, sort_dicts=True)
        + "\n\nEXPECTED_JYOTISH_SUBJECT = "
        + pformat(jyotish_data, width=100, sort_dicts=True)
        + "\n"
    )

    OUTPUT_PATH.write_text(content)
    print(f"✓ Updated {OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    regenerate_expected_subjects()
