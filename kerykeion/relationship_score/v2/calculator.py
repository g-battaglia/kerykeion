"""Pure numerical Discepolo scorer: validate → recognize → award → aggregate.

Only five tropical longitudes per subject are needed. No ephemeris, display
settings, v1 scorer, or general synastry engine is consulted. The fixed scoring
profile is deliberately separate from configurable chart-aspect settings.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from math import floor, isfinite

from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.schemas.literals import RelationshipScoreDescription
from kerykeion.schemas.models import RelationshipScoreAspectModel, ScoreBreakdownItemModel

from .models import RelationshipScoreV2Model, ScoreContactV2Model, ScoreMetadataV2Model

LUMINARIES = ("Sun", "Moon", "Ascendant")
REQUIRED_POINTS = (*LUMINARIES, "Venus", "Mars")
VENUS_MARS_DIRECTIONS = (("Venus", "Mars"), ("Mars", "Venus"))
TIGHT_ORB = 2
WRAP_THRESHOLD = 190
LUMINARY_POINTS = 4
DESTINY_POINTS = 5
VENUS_MARS_POINTS = 4
SPECIAL_STANDARD_POINTS = 8
SPECIAL_TIGHT_POINTS = 11


@dataclass(frozen=True)
class AspectDefinition:
    """An exact aspect angle and its fixed scoring orb, both in degrees."""

    name: str
    angle: int
    orb: float


# First qualifying aspect wins. Minors are included; quintile/quincunx are not.
# In particular, the scoring sextile orb is 3°, not the chart-display orb.
SCORING_ASPECTS = (
    AspectDefinition("conjunction", 0, 8),
    AspectDefinition("semi-sextile", 30, 2),
    AspectDefinition("semi-square", 45, 2),
    AspectDefinition("sextile", 60, 3),
    AspectDefinition("square", 90, 5),
    AspectDefinition("trine", 120, 7),
    AspectDefinition("sesquiquadrate", 135, 2),
    AspectDefinition("opposition", 180, 8),
)

# Public category vocabulary stays compatible with v1; it does not affect points.
SCORE_BANDS: tuple[tuple[int, RelationshipScoreDescription], ...] = (
    (5, "Minimal"),
    (10, "Medium"),
    (15, "Important"),
    (20, "Very Important"),
    (30, "Exceptional"),
)


@dataclass(frozen=True)
class AngularSeparation:
    """Unrounded circular distance and the integer distance used for scoring."""

    physical: float
    scoring: int


@dataclass(frozen=True)
class RecognizedAspect:
    """A qualifying aspect, retaining both physical and scoring residuals."""

    definition: AspectDefinition
    separation: AngularSeparation

    @property
    def scoring_orbit(self) -> float:
        return abs(self.separation.scoring - self.definition.angle)

    @property
    def physical_orbit(self) -> float:
        return abs(self.separation.physical - self.definition.angle)


@dataclass(frozen=True)
class PointAward:
    """One rule's point award. Special awards replace generic +4, never stack."""

    rule: str
    points: int


def validate_positions(values: Mapping[str, float]) -> dict[str, float]:
    """Copy five canonical longitudes; missing/non-finite values fail closed.

    Extra points do not participate. Inputs are not normalized modulo 360: an
    invalid longitude should produce an error, not a plausible altered score.
    """
    if not isinstance(values, Mapping):
        raise KerykeionException("Discepolo v2 positions must map point names to degrees.")
    positions: dict[str, float] = {}
    for point in REQUIRED_POINTS:
        if point not in values:
            raise KerykeionException(f"Discepolo v2 requires {point} in both subjects.")
        value = values[point]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise KerykeionException(f"Invalid {point} longitude: {value!r}.")
        # Check range before isfinite: huge Python integers must not overflow.
        if not 0 <= value < 360 or not isfinite(value):
            raise KerykeionException(f"Invalid {point} longitude: {value!r}; expected finite degrees in [0, 360).")
        positions[point] = float(value)
    return positions


def _measure_separation(first: float, second: float) -> AngularSeparation:
    """Round the absolute difference DOWN to a whole degree BEFORE wrapping.

    raw = abs(first - second); scoring = floor(raw).
    If scoring > 190, scoring = 360 - scoring.

    Do not replace this with floor(min(raw, 360 - raw)): a difference of 359.9°
    scores as 1°, not 0°. The 190° threshold is intentional. Physical distance
    is returned separately, without quantization, for v1-compatible orbit data.
    """
    absolute_difference = abs(first - second)
    scoring_distance = floor(absolute_difference)
    if scoring_distance > WRAP_THRESHOLD:
        scoring_distance = 360 - scoring_distance
    physical_distance = min(absolute_difference, 360 - absolute_difference)
    return AngularSeparation(physical=physical_distance, scoring=scoring_distance)


def _recognize_aspect(first: float, second: float) -> RecognizedAspect | None:
    """Apply inclusive orb tests in the profile's explicit recognition order."""
    separation = _measure_separation(first, second)
    for definition in SCORING_ASPECTS:
        if abs(separation.scoring - definition.angle) <= definition.orb:
            return RecognizedAspect(definition=definition, separation=separation)
    return None


def _luminary_award(first_point: str, second_point: str, aspect: RecognizedAspect) -> PointAward:
    """Select EXACTLY one rule for a recognized luminary contact.

    Sun–Sun square/opposition and cross Sun–Moon conjunction score 8/11.
    Sun–Sun conjunction is an ordinary +4 contact in this profile. The upgrade
    uses the scoring residual (<=2), not the unrounded physical residual.
    """
    is_sun_sun_special = first_point == second_point == "Sun" and aspect.definition.angle in (90, 180)
    is_sun_moon_conjunction = {first_point, second_point} == {"Sun", "Moon"} and aspect.definition.angle == 0
    if is_sun_sun_special or is_sun_moon_conjunction:
        points = SPECIAL_TIGHT_POINTS if aspect.scoring_orbit <= TIGHT_ORB else SPECIAL_STANDARD_POINTS
        rule = "sun_sun_major" if is_sun_sun_special else "sun_moon_conjunction"
        return PointAward(rule=rule, points=points)
    return PointAward(rule="luminary_aspect", points=LUMINARY_POINTS)


def _make_contact(
    first_point: str, second_point: str, aspect: RecognizedAspect, award: PointAward
) -> ScoreContactV2Model:
    """Convert the recognized geometry and award into one auditable data row."""
    return ScoreContactV2Model(
        p1_name=first_point,
        p2_name=second_point,
        aspect=aspect.definition.name,
        distance=aspect.separation.physical,
        orbit=aspect.physical_orbit,
        scoring_distance=aspect.separation.scoring,
        scoring_orbit=aspect.scoring_orbit,
        orb_limit=aspect.definition.orb,
        rule=award.rule,
        points=award.points,
    )


def _luminary_contacts(first: dict[str, float], second: dict[str, float]) -> list[ScoreContactV2Model]:
    """All nine A→B luminary pairs, including Moon–Moon and Ascendant–Ascendant."""
    contacts = []
    for first_point in LUMINARIES:
        for second_point in LUMINARIES:
            aspect = _recognize_aspect(first[first_point], second[second_point])
            if aspect is None:
                continue
            award = _luminary_award(first_point, second_point, aspect)
            contacts.append(_make_contact(first_point, second_point, aspect, award))
    return contacts


def _venus_mars_contacts(first: dict[str, float], second: dict[str, float]) -> list[ScoreContactV2Model]:
    """Each direction independently earns +4; two contacts therefore earn +8."""
    contacts = []
    for first_point, second_point in VENUS_MARS_DIRECTIONS:
        aspect = _recognize_aspect(first[first_point], second[second_point])
        if aspect is None:
            continue
        award = PointAward(rule="venus_mars", points=VENUS_MARS_POINTS)
        contacts.append(_make_contact(first_point, second_point, aspect, award))
    return contacts


def _solar_sign_index(longitude: float) -> int:
    """Zero-based sign index from canonical longitude, without label lookup."""
    return int(longitude // 30)


def _breakdown(contacts: list[ScoreContactV2Model], destiny_awarded: bool) -> list[ScoreBreakdownItemModel]:
    """The total will be summed from these rows, preventing accounting drift."""
    rows = [
        ScoreBreakdownItemModel(
            rule=contact.rule,
            description=f"{contact.p1_name}-{contact.p2_name} {contact.aspect}",
            points=contact.points,
            details=f"scoring_orbit={contact.scoring_orbit:g}; orbit={contact.orbit:.10f}; direction=A->B",
        )
        for contact in contacts
    ]
    if destiny_awarded:
        rows.append(
            ScoreBreakdownItemModel(rule="destiny_sign", description="Matching solar modality", points=DESTINY_POINTS)
        )
    return rows


def _score_description(total: int) -> RelationshipScoreDescription:
    """Use v1's half-open bands and its >=30 category; labels never add points."""
    return next((label for upper_limit, label in SCORE_BANDS if total < upper_limit), "Rare Exceptional")


def score_positions(
    first: Mapping[str, float],
    second: Mapping[str, float],
    *,
    subject_names: tuple[str, str] = ("A", "B"),
) -> RelationshipScoreV2Model:
    """Calculate score and data from longitudes, with no interpretation or I/O.

    A special Sun–Sun square/opposition suppresses the destiny +5. All other
    matching solar modalities earn +5 once. No contact is counted twice, and
    there is no arbitrary score cap. The same inputs always produce fresh data.
    """
    first_positions = validate_positions(first)
    second_positions = validate_positions(second)
    if len(subject_names) != 2 or not all(isinstance(name, str) for name in subject_names):
        raise KerykeionException("Exactly two string subject names are required.")

    contacts = _luminary_contacts(first_positions, second_positions)
    contacts.extend(_venus_mars_contacts(first_positions, second_positions))

    first_sign = _solar_sign_index(first_positions["Sun"])
    second_sign = _solar_sign_index(second_positions["Sun"])
    destiny_match = (first_sign - second_sign) % 3 == 0
    sun_sun_special_scored = any(contact.rule == "sun_sun_major" for contact in contacts)
    destiny_suppressed = destiny_match and sun_sun_special_scored
    destiny_awarded = destiny_match and not destiny_suppressed

    breakdown = _breakdown(contacts, destiny_awarded)
    total = sum(row.points for row in breakdown)
    metadata = ScoreMetadataV2Model(
        aspect_orbs={aspect.name: aspect.orb for aspect in SCORING_ASPECTS},
        point_awards={
            "luminary_aspect": LUMINARY_POINTS,
            "destiny_sign": DESTINY_POINTS,
            "venus_mars": VENUS_MARS_POINTS,
            "special_standard": SPECIAL_STANDARD_POINTS,
            "special_tight": SPECIAL_TIGHT_POINTS,
        },
        tight_orb=TIGHT_ORB,
        wrap_threshold=WRAP_THRESHOLD,
        evaluated_pairs=len(LUMINARIES) ** 2 + len(VENUS_MARS_DIRECTIONS),
    )
    return RelationshipScoreV2Model(
        score_value=total,
        score_description=_score_description(total),
        is_destiny_sign=destiny_match,
        destiny_bonus_awarded=destiny_awarded,
        destiny_bonus_suppressed=destiny_suppressed,
        contacts=contacts,
        metadata=metadata,
        score_breakdown=breakdown,
        aspects=[
            RelationshipScoreAspectModel(p1_name=row.p1_name, p2_name=row.p2_name, aspect=row.aspect, orbit=row.orbit)
            for row in contacts
        ],
        subjects=[],
        positions=[first_positions, second_positions],
        subject_names=list(subject_names),
    )
