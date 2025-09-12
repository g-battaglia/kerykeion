"""Backward compatibility shims for legacy Kerykeion v4 public API.

This module provides wrapper classes and aliases that emulate the old
(v4 and earlier) interfaces while internally delegating to the new v5
factory/data oriented architecture.

Import pattern supported (legacy):
    from kerykeion import AstrologicalSubject, KerykeionChartSVG, SynastryAspects

New architecture summary:
    - AstrologicalSubjectFactory.from_birth_data(...) returns an AstrologicalSubjectModel
    - ChartDataFactory + ChartDrawer replace KerykeionChartSVG direct chart building
    - AspectsFactory provides both single and dual chart aspects

Classes provided here:
    AstrologicalSubject (wrapper around AstrologicalSubjectFactory)
    KerykeionChartSVG (wrapper producing SVGs via ChartDataFactory + ChartDrawer)
    SynastryAspects (wrapper over AspectsFactory.dual_chart_aspects)

Deprecation: Each class issues a DeprecationWarning guiding users to the
replacement APIs. They are intentionally minimal; only the most used
attributes / methods from the README master branch examples are reproduced.

Note: This file name is intentionally spelled 'backword.py' per user request.
"""
from __future__ import annotations

from typing import Any, Iterable, List, Optional, Sequence, Union, Literal
import warnings

from .astrological_subject_factory import AstrologicalSubjectFactory
from .chart_data_factory import ChartDataFactory
from .charts.chart_drawer import ChartDrawer
from .aspects import AspectsFactory
from .settings.config_constants import DEFAULT_ACTIVE_POINTS
from .schemas.kr_models import AstrologicalSubjectModel, CompositeSubjectModel, ActiveAspect
from .schemas.kr_literals import (
    KerykeionChartLanguage,
    KerykeionChartTheme,
    ChartType,
    AstrologicalPoint,
)
from .schemas import ZodiacType, SiderealMode, HousesSystemIdentifier, PerspectiveType
from pathlib import Path
from .settings import KerykeionSettingsModel
from .report import Report

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deprecated(old: str, new: str) -> None:
    warnings.warn(
        f"'{old}' is deprecated and will be removed in a future major release. "
        f"Please migrate to: {new}",
        DeprecationWarning,
        stacklevel=2,
    )


def _normalize_active_points(points: Optional[Iterable[Union[str, AstrologicalPoint]]]) -> Optional[List[AstrologicalPoint]]:
    """Best-effort normalization of legacy string active points list.

    - Accepts None -> None
    - Accepts iterable of strings / AstrologicalPoint literals
    - Filters only those present in DEFAULT_ACTIVE_POINTS to avoid invalid entries
    - Returns None if result would be empty (to let downstream use defaults)
    """
    if points is None:
        return None
    normalized: List[AstrologicalPoint] = []
    valid: Sequence[AstrologicalPoint] = DEFAULT_ACTIVE_POINTS  # type: ignore[assignment]
    for p in points:
        if isinstance(p, str):
            # Match case-insensitive exact name in default list
            match = next((vp for vp in valid if vp.lower() == p.lower()), None)  # type: ignore[attr-defined]
            if match:
                normalized.append(match)  # type: ignore[arg-type]
        else:
            if p in valid:
                normalized.append(p)
    return normalized or None

# ---------------------------------------------------------------------------
# Legacy AstrologicalSubject wrapper
# ---------------------------------------------------------------------------
class AstrologicalSubject:
    """Backward compatible wrapper implementing the requested __init__ signature."""

    from datetime import datetime as _dt
    NOW = _dt.utcnow()

    def __init__(
        self,
        name: str = "Now",
        year: int = NOW.year,  # type: ignore[misc]
        month: int = NOW.month,  # type: ignore[misc]
        day: int = NOW.day,  # type: ignore[misc]
        hour: int = NOW.hour,  # type: ignore[misc]
        minute: int = NOW.minute,  # type: ignore[misc]
        city: Union[str, None] = None,
        nation: Union[str, None] = None,
        lng: Union[int, float, None] = None,
        lat: Union[int, float, None] = None,
        tz_str: Union[str, None] = None,
        geonames_username: Union[str, None] = None,
        zodiac_type: Union[ZodiacType, None] = None,  # default resolved below
        online: bool = True,
        disable_chiron: Union[None, bool] = None,  # deprecated
        sidereal_mode: Union[SiderealMode, None] = None,
        houses_system_identifier: Union[HousesSystemIdentifier, None] = None,
        perspective_type: Union[PerspectiveType, None] = None,
        cache_expire_after_days: Union[int, None] = None,
        is_dst: Union[None, bool] = None,
        disable_chiron_and_lilith: bool = False,  # currently not forwarded (not in factory)
    ) -> None:
        from .astrological_subject_factory import (
            DEFAULT_ZODIAC_TYPE,
            DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
            DEFAULT_PERSPECTIVE_TYPE,
            DEFAULT_GEONAMES_CACHE_EXPIRE_AFTER_DAYS,
        )

        _deprecated("AstrologicalSubject", "AstrologicalSubjectFactory.from_birth_data")

        if disable_chiron is not None:
            warnings.warn("'disable_chiron' è deprecato e ignorato.", DeprecationWarning, stacklevel=2)
        if disable_chiron_and_lilith:
            warnings.warn(
                "'disable_chiron_and_lilith' non è supportato da from_birth_data in questa versione ed è ignorato.",
                UserWarning,
                stacklevel=2,
            )

        zodiac_type = DEFAULT_ZODIAC_TYPE if zodiac_type is None else zodiac_type
        houses_system_identifier = (
            DEFAULT_HOUSES_SYSTEM_IDENTIFIER if houses_system_identifier is None else houses_system_identifier
        )
        perspective_type = DEFAULT_PERSPECTIVE_TYPE if perspective_type is None else perspective_type
        cache_expire_after_days = (
            DEFAULT_GEONAMES_CACHE_EXPIRE_AFTER_DAYS if cache_expire_after_days is None else cache_expire_after_days
        )

        self._model = AstrologicalSubjectFactory.from_birth_data(
            name=name,
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            seconds=0,
            city=city,
            nation=nation,
            lng=float(lng) if lng is not None else None,
            lat=float(lat) if lat is not None else None,
            tz_str=tz_str,
            geonames_username=geonames_username,
            online=online,
            zodiac_type=zodiac_type,  # type: ignore[arg-type]
            sidereal_mode=sidereal_mode,  # type: ignore[arg-type]
            houses_system_identifier=houses_system_identifier,  # type: ignore[arg-type]
            perspective_type=perspective_type,  # type: ignore[arg-type]
            cache_expire_after_days=cache_expire_after_days,
            is_dst=is_dst,  # type: ignore[arg-type]
        )

    # Provide attribute passthrough for planetary points / houses used in README
    def __getattr__(self, item: str) -> Any:  # pragma: no cover - dynamic proxy
        try:
            return getattr(self._model, item)
        except AttributeError:
            raise AttributeError(f"AstrologicalSubject has no attribute '{item}'") from None

    def __repr__(self) -> str:
        return f"AstrologicalSubject({self._model.name!r}, {self._model.iso_formatted_utc_datetime})"

    # Provide json() similar convenience
    def json(self, dump: bool = False, indent: int = 2) -> Any:
        # model_dump does not support indent parameter; replicate simple formatting
        if dump:
            return self._model.model_dump_json()
        return self._model.model_dump()

    # Factory method compatibility (class method in old API)
    @classmethod
    def get_from_iso_utc_time(
        cls,
        name: str,
        iso_utc: str,
        city: Optional[str] = None,
        nation: Optional[str] = None,
        *,
        online: bool = True,
        geonames_username: Optional[str] = None,
        **kwargs: Any,
    ) -> "AstrologicalSubject":
        _deprecated("AstrologicalSubject.get_from_iso_utc_time", "AstrologicalSubjectFactory.from_iso_utc_time")
        model = AstrologicalSubjectFactory.from_iso_utc_time(
            name=name,
            iso_utc_time=iso_utc,
            city=city or "Greenwich",
            nation=nation or "GB",
            online=online,
            geonames_username=geonames_username or "demo",
            **kwargs,
        )
        obj = cls.__new__(cls)  # bypass __init__
        obj._model = model
        return obj

# ---------------------------------------------------------------------------
# Legacy KerykeionChartSVG wrapper
# ---------------------------------------------------------------------------
class KerykeionChartSVG:
    """Wrapper emulating the v4 chart generation interface.

    Old usage:
        chart = KerykeionChartSVG(subject, chart_type="ExternalNatal", second_subject)
        chart.makeSVG(minify_svg=True, remove_css_variables=True)

    Replaced by ChartDataFactory + ChartDrawer.
    """

    def __init__(
        self,
        first_obj: Union[AstrologicalSubject, AstrologicalSubjectModel, CompositeSubjectModel],
        chart_type: ChartType = "Natal",
        second_obj: Union[AstrologicalSubject, AstrologicalSubjectModel, None] = None,
        new_output_directory: Union[str, None] = None,
        new_settings_file: Union[Path, None, KerykeionSettingsModel, dict] = None,  # retained for signature compatibility (unused)
        theme: Union[KerykeionChartTheme, None] = "classic",
        double_chart_aspect_grid_type: Literal["list", "table"] = "list",
        chart_language: KerykeionChartLanguage = "EN",
        active_points: List[AstrologicalPoint] = DEFAULT_ACTIVE_POINTS,  # type: ignore[assignment]
        active_aspects: Optional[List[ActiveAspect]] = None,
    ) -> None:
        _deprecated("KerykeionChartSVG", "ChartDataFactory + ChartDrawer")

        # Resolve first model
        if isinstance(first_obj, AstrologicalSubject):
            subject_model: Union[AstrologicalSubjectModel, CompositeSubjectModel] = first_obj._model  # type: ignore[assignment]
        else:
            subject_model = first_obj

        # Resolve second model
        if isinstance(second_obj, AstrologicalSubject):
            second_model: Optional[Union[AstrologicalSubjectModel, CompositeSubjectModel]] = second_obj._model  # type: ignore[assignment]
        else:
            second_model = second_obj

        # Normalize active aspects (if None fallback to DEFAULT_ACTIVE_ASPECTS)
        if active_aspects is None:
            from .settings.config_constants import DEFAULT_ACTIVE_ASPECTS as _DAA
            active_aspects = list(_DAA)

        # Assign internal state
        self._chart_type = chart_type
        self._subject_model = subject_model
        self._second_model = second_model
        # Copy active points to avoid accidental external mutation and normalize legacy values
        self._active_points = _normalize_active_points(list(active_points) if active_points else None)
        self._active_aspects = active_aspects
        self._theme = theme  # type: ignore[assignment]
        self._chart_language = chart_language  # type: ignore[assignment]
        self._output_directory = new_output_directory
        self._double_chart_aspect_grid_type = double_chart_aspect_grid_type
        self._chart_drawer: Optional[ChartDrawer] = None

    def _ensure_chart(self) -> None:
        if self._chart_drawer is not None:
            return
        ct = self._chart_type.lower()  # type: ignore[union-attr]
        active_points = self._active_points
        if ct in ("natal", "birth"):
            data = ChartDataFactory.create_natal_chart_data(self._subject_model, active_points=active_points, active_aspects=self._active_aspects)
        elif ct in ("externalnatal", "external_natal"):
            data = ChartDataFactory.create_natal_chart_data(self._subject_model, active_points=active_points, active_aspects=self._active_aspects)
        elif ct == "synastry" and self._second_model is not None:
            # Cast second model to natal subject type for synastry if composite accidentally passed
            data = ChartDataFactory.create_synastry_chart_data(self._subject_model, self._second_model, active_points=active_points, active_aspects=self._active_aspects)  # type: ignore[arg-type]
        elif ct == "transit" and self._second_model is not None:
            data = ChartDataFactory.create_transit_chart_data(self._subject_model, self._second_model, active_points=active_points, active_aspects=self._active_aspects)  # type: ignore[arg-type]
        elif ct == "composite" and isinstance(self._subject_model, CompositeSubjectModel):
            data = ChartDataFactory.create_composite_chart_data(self._subject_model)
        else:
            raise ValueError(f"Unsupported or improperly configured chart_type '{self._chart_type}'")
        self._chart_drawer = ChartDrawer(chart_data=data, theme=self._theme, chart_language=self._chart_language)  # type: ignore[arg-type]

    # Legacy method names --------------------------------------------------
    def makeSVG(self, minify: bool = False, remove_css_variables: bool = False) -> str:
        self._ensure_chart()
        assert self._chart_drawer is not None
        path = self._chart_drawer.save_svg(
            output_path=self._output_directory,
            minify=minify,
            remove_css_variables=remove_css_variables,
        )
        return path or ""

    def makeWheelOnlySVG(self, wheel_only: bool = True, wheel_only_external: bool = False) -> str:
        self._ensure_chart()
        assert self._chart_drawer is not None
        # save_wheel_only_svg_file in v5 does not require wheel_only flag; emulate external flag by ignoring
        path = self._chart_drawer.save_wheel_only_svg_file(output_path=self._output_directory)
        return path or ""

    def makeGridOnlySVG(self) -> str:
        self._ensure_chart()
        assert self._chart_drawer is not None
        path = self._chart_drawer.save_aspect_grid_only_svg_file(output_path=self._output_directory)
        return path or ""

    # Aliases for new naming in README next (optional convenience)
    save_svg = makeSVG
    save_wheel_only_svg_file = makeWheelOnlySVG
    save_aspect_grid_only_svg_file = makeGridOnlySVG

# ---------------------------------------------------------------------------
# Legacy SynastryAspects wrapper
# ---------------------------------------------------------------------------
class SynastryAspects:
    """Wrapper replicating old synastry aspects interface.

    Replacement: AspectsFactory.dual_chart_aspects(first, second)
    """

    def __init__(self, first: Union[AstrologicalSubject, AstrologicalSubjectModel], second: Union[AstrologicalSubject, AstrologicalSubjectModel]):
        _deprecated("SynastryAspects", "AspectsFactory.dual_chart_aspects")
        self._first = first._model if isinstance(first, AstrologicalSubject) else first
        self._second = second._model if isinstance(second, AstrologicalSubject) else second

    def get_relevant_aspects(self):
        return AspectsFactory.dual_chart_aspects(self._first, self._second)

# ---------------------------------------------------------------------------
# Convenience exports (mirroring old implicit surface API)
# ---------------------------------------------------------------------------
__all__ = [
    "AstrologicalSubject",
    "KerykeionChartSVG",
    "SynastryAspects",
]
