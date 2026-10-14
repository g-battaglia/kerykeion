"""Data contracts for Discepolo scoring v2; no interpretation or presentation."""

from pydantic import Field

from kerykeion.schemas.models import RelationshipScoreModel, SubscriptableBaseModel


class ScoreContactV2Model(SubscriptableBaseModel):
    """One contributing contact from subject A to subject B.

    Physical values are never rounded. ``orbit`` retains v1's meaning: the
    physical distance from the exact aspect angle. The separate ``scoring_*``
    values record the quantization used by the numerical scoring rules.
    """

    p1_name: str
    p2_name: str
    aspect: str
    distance: float
    orbit: float
    scoring_distance: int
    scoring_orbit: float
    orb_limit: float
    rule: str
    points: int


class ScoreMetadataV2Model(SubscriptableBaseModel):
    """Machine-readable calculation policy, sufficient to audit the score.

    ``reference_verified`` stays false until complete reference-output fixtures
    establish end-to-end parity. Passing unit tests alone must not set it true.
    """

    algorithm: str = "discepolo-score-v2"
    aspect_orbs: dict[str, float]
    point_awards: dict[str, int]
    tight_orb: int
    quantization: str = "floor_absolute_difference_before_wrap"
    wrap_threshold: int
    orb_boundary: str = "inclusive"
    special_awards: str = "replace_generic_award"
    venus_mars_counting: str = "per_direction"
    evaluated_pairs: int
    zodiac_type: str = "Tropical"
    perspective_type: str = "Apparent Geocentric"
    reference_verified: bool = False


class RelationshipScoreV2Model(RelationshipScoreModel):
    """v1 fields plus input positions, numerical contacts and policy metadata.

    ``is_destiny_sign`` records the sign match, not whether it earned points.
    The bonus flags make award/suppression explicit without changing that v1
    field. ``aspects[].orbit`` is physical; ``contacts[].scoring_orbit`` is the
    value actually used to award points. No text interpretations are generated.
    Standard Pydantic ``model_dump``/``model_dump_json`` serialize these data.
    """

    contacts: list[ScoreContactV2Model] = Field(default_factory=list)
    destiny_bonus_awarded: bool
    destiny_bonus_suppressed: bool
    metadata: ScoreMetadataV2Model
    positions: list[dict[str, float]]
    subject_names: list[str]
