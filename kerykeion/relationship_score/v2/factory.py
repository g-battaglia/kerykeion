"""Thin adapter from Kerykeion natal subjects to the pure Discepolo v2 scorer."""

from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.schemas.models import AstrologicalSubjectModel
from kerykeion.utilities.core import require_same_frame

from .calculator import REQUIRED_POINTS, score_positions, validate_positions
from .models import RelationshipScoreV2Model


def _validate_subjects(first: AstrologicalSubjectModel, second: AstrologicalSubjectModel) -> None:
    """Reject incomplete/mixed reference frames before reading any positions."""
    if not isinstance(first, AstrologicalSubjectModel) or not isinstance(second, AstrologicalSubjectModel):
        raise KerykeionException("Discepolo v2 requires two AstrologicalSubjectModel instances.")
    require_same_frame(first, second)
    if first.zodiac_type != "Tropical" or first.perspective_type != "Apparent Geocentric":
        raise KerykeionException("Discepolo v2 requires Tropical, Apparent Geocentric subjects.")


def _subject_positions(subject: AstrologicalSubjectModel) -> dict[str, float]:
    """Extract absolute longitudes only; do not invoke any aspect/score factory."""
    positions = {}
    for point_name in REQUIRED_POINTS:
        point = getattr(subject, point_name.lower(), None)
        if point is None:
            raise KerykeionException(f"Discepolo v2 requires {point_name} in both subjects' active_points.")
        positions[point_name] = point.abs_pos
    return validate_positions(positions)


class RelationshipScoreFactoryV2:
    """Opt-in numerical factory with the familiar v1 get_relationship_score API.

    Both subjects must include Sun, Moon, Ascendant, Venus and Mars, in the
    Tropical/Apparent Geocentric frame. Construction snapshots the subjects;
    repeated calls return fresh results and never accumulate scoring state.
    No interpretations, chart generation, file I/O or report rendering live here.
    """

    def __init__(self, first_subject: AstrologicalSubjectModel, second_subject: AstrologicalSubjectModel):
        _validate_subjects(first_subject, second_subject)
        self._first_subject = first_subject.model_copy(deep=True)
        self._second_subject = second_subject.model_copy(deep=True)
        self._first_positions = _subject_positions(self._first_subject)
        self._second_positions = _subject_positions(self._second_subject)

    @property
    def first_subject(self) -> AstrologicalSubjectModel:
        """A defensive copy: caller mutation cannot desynchronize score inputs."""
        return self._first_subject.model_copy(deep=True)

    @property
    def second_subject(self) -> AstrologicalSubjectModel:
        """A defensive copy, matching the first_subject contract."""
        return self._second_subject.model_copy(deep=True)

    def get_relationship_score(self) -> RelationshipScoreV2Model:
        """Return v1-compatible score fields plus numerical audit metadata."""
        names = (self._first_subject.name, self._second_subject.name)
        result = score_positions(self._first_positions, self._second_positions, subject_names=names)
        result.subjects = [self.first_subject, self.second_subject]
        return result
