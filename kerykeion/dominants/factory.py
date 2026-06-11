# -*- coding: utf-8 -*-
"""
Public entry point for the dominants calculator.
=================================================

:class:`DominantsFactory` is the one class users touch. It resolves which
calculation *school* to run — either a built-in method selected by name
(``"modern"``, ``"almuten_figuris"``, ``"elemental"``) or a user-supplied custom
strategy object — and returns a :class:`DominantsModel`.

Built-in schools are stateless and shared via a small registry; a custom school
is any object satisfying the :class:`~kerykeion.dominants.base.DominantStrategy`
protocol (a ``name`` attribute and a ``compute(subject, config)`` method), so no
registration step is required:

    >>> class MySchool(BaseDominantStrategy):
    ...     name = "my_school"
    ...     def compute(self, subject, config):
    ...         ...  # build and return a DominantsModel
    >>> DominantsFactory.from_subject(subject, strategy=MySchool())

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

from kerykeion.dominants.base import DistributionMethod, DominantsConfig, DominantStrategy
from kerykeion.dominants.strategies import (
    AlmutenFigurisStrategy,
    ElementalBalanceStrategy,
    ModernDominantStrategy,
)
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_literals import DominantMethod
from kerykeion.schemas.kr_models import AstrologicalSubjectModel, DominantsModel

#: Registry of built-in schools. Instances are stateless and safe to share.
_BUILTIN_STRATEGIES: Dict[str, DominantStrategy] = {
    "modern": ModernDominantStrategy(),
    "almuten_figuris": AlmutenFigurisStrategy(),
    "elemental": ElementalBalanceStrategy(),
}


class DominantsFactory:
    """Compute the dominants of a chart with a built-in or custom school.

    Example:
        >>> from kerykeion import AstrologicalSubjectFactory, DominantsFactory
        >>> subject = AstrologicalSubjectFactory.from_birth_data(
        ...     "John Lennon", 1940, 10, 9, 18, 30,
        ...     lat=53.4084, lng=-2.9916, tz_str="Europe/London", online=False)
        >>> dominants = DominantsFactory.from_subject(subject, strategy="modern")
        >>> dominants.dominant_planet, dominants.dominant_element  # doctest: +SKIP
        ('Mars', 'Earth')
    """

    @classmethod
    def from_subject(
        cls,
        subject: AstrologicalSubjectModel,
        *,
        strategy: Union[DominantMethod, DominantStrategy] = "modern",
        active_points: Optional[list[str]] = None,
        distribution_method: DistributionMethod = "weighted",
        custom_weights: Optional[Dict[str, float]] = None,
        include_accidental_dignities: bool = False,
        include_score_breakdown: bool = False,
    ) -> DominantsModel:
        """Compute the dominants of an already-calculated subject.

        Args:
            subject: The natal/event chart to analyse.
            strategy: Either a built-in method name (``"modern"``,
                ``"almuten_figuris"`` or ``"elemental"``) or a custom object
                implementing the :class:`DominantStrategy` protocol.
            active_points: Optional explicit subset of point names to consider
                (used by the ``elemental`` school). When ``None``, the subject's
                own active points are used.
            distribution_method: ``"weighted"`` (default) or ``"pure_count"`` for
                the element/modality tally.
            custom_weights: Optional per-point weight overrides for the
                element/modality tally (case-insensitive point names).
            include_accidental_dignities: When ``True``, the Almuten Figuris adds
                its optional accidental-dignity layer.
            include_score_breakdown: When ``True``, the result's
                ``score_breakdown`` is populated with a per-rule audit trail.

        Returns:
            A :class:`DominantsModel` for the chosen school.

        Raises:
            KerykeionException: If ``strategy`` is neither a known built-in name
                nor a valid :class:`DominantStrategy` instance.
        """
        config = DominantsConfig(
            active_points=active_points,
            distribution_method=distribution_method,
            custom_weights=custom_weights,
            include_accidental_dignities=include_accidental_dignities,
            include_score_breakdown=include_score_breakdown,
        )
        resolved = cls._resolve_strategy(strategy)
        return resolved.compute(subject, config)

    @classmethod
    def from_birth_data(
        cls,
        name: str,
        year: int,
        month: int,
        day: int,
        hour: int = 12,
        minute: int = 0,
        *,
        strategy: Union[DominantMethod, DominantStrategy] = "modern",
        active_points: Optional[list[str]] = None,
        distribution_method: DistributionMethod = "weighted",
        custom_weights: Optional[Dict[str, float]] = None,
        include_accidental_dignities: bool = False,
        include_score_breakdown: bool = False,
        **subject_kwargs: Any,
    ) -> DominantsModel:
        """Build a subject from birth data, then compute its dominants.

        A thin convenience over :meth:`from_subject`. The positional birth
        arguments and any extra keyword arguments (``lat``, ``lng``, ``tz_str``,
        ``online``, …) are forwarded verbatim to
        :meth:`AstrologicalSubjectFactory.from_birth_data`.

        Args:
            name: Subject name.
            year, month, day, hour, minute: Birth date and time.
            strategy: See :meth:`from_subject`.
            active_points, distribution_method, custom_weights,
                include_accidental_dignities, include_score_breakdown:
                See :meth:`from_subject`.
            **subject_kwargs: Forwarded to ``AstrologicalSubjectFactory``
                (e.g. ``lat``, ``lng``, ``tz_str``, ``city``, ``nation``,
                ``online``, ``zodiac_type``).

        Returns:
            A :class:`DominantsModel` for the chosen school.
        """
        # Local import avoids an import-time dependency on the subject factory.
        from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

        subject = AstrologicalSubjectFactory.from_birth_data(name, year, month, day, hour, minute, **subject_kwargs)
        return cls.from_subject(
            subject,
            strategy=strategy,
            active_points=active_points,
            distribution_method=distribution_method,
            custom_weights=custom_weights,
            include_accidental_dignities=include_accidental_dignities,
            include_score_breakdown=include_score_breakdown,
        )

    @staticmethod
    def available_methods() -> list[str]:
        """Return the names of the built-in dominant-calculation methods."""
        return sorted(_BUILTIN_STRATEGIES)

    @staticmethod
    def _resolve_strategy(strategy: Union[DominantMethod, DominantStrategy]) -> DominantStrategy:
        """Resolve a method name or custom strategy to a concrete strategy.

        Args:
            strategy: A built-in method name or a :class:`DominantStrategy`.

        Returns:
            The strategy instance to run.

        Raises:
            KerykeionException: For an unknown name or an invalid object.
        """
        if isinstance(strategy, str):
            try:
                return _BUILTIN_STRATEGIES[strategy]
            except KeyError:
                valid = ", ".join(sorted(_BUILTIN_STRATEGIES))
                raise KerykeionException(
                    f"Unknown dominant method {strategy!r}. Valid built-in methods: {valid}. "
                    f"Alternatively pass a custom DominantStrategy instance."
                ) from None

        if isinstance(strategy, DominantStrategy):
            return strategy

        raise KerykeionException(
            "strategy must be a built-in method name (str) or a DominantStrategy instance "
            "(an object with a 'name' attribute and a 'compute(subject, config)' method)."
        )
