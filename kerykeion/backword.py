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

from typing import Any, Iterable, List, Mapping, Optional, Sequence, Union, Literal, cast
import logging
import warnings
from datetime import datetime
from functools import cached_property

from .astrological_subject_factory import AstrologicalSubjectFactory
from .chart_data_factory import ChartDataFactory
from .charts.chart_drawer import ChartDrawer  # type: ignore[attr-defined]
from .aspects import AspectsFactory
from .settings.config_constants import DEFAULT_ACTIVE_POINTS, DEFAULT_ACTIVE_ASPECTS
from .utilities import normalize_zodiac_type
from .schemas.kr_models import (
    AstrologicalSubjectModel,
    CompositeSubjectModel,
    ActiveAspect,
    SingleChartDataModel,
    DualChartDataModel,
)
from .schemas.kr_literals import (
    KerykeionChartLanguage,
    KerykeionChartTheme,
    ChartType,
    AstrologicalPoint,
)
from .schemas import ZodiacType, SiderealMode, HousesSystemIdentifier, PerspectiveType
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _deprecated(old: str, new: str) -> None:
    warnings.warn(
        f"'{old}' is deprecated and will be removed in a future major release. Please migrate to: {new}",
        DeprecationWarning,
        stacklevel=2,
    )


# Legacy node name mapping for backward compatibility
LEGACY_NODE_NAMES_MAP = {
    "Mean_Node": "Mean_North_Lunar_Node",
    "True_Node": "True_North_Lunar_Node",
    "Mean_South_Node": "Mean_South_Lunar_Node",
    "True_South_Node": "True_South_Lunar_Node",
}


def _normalize_zodiac_type_with_warning(zodiac_type: Optional[Union[str, ZodiacType]]) -> Optional[ZodiacType]:
    """Normalize legacy zodiac type values with deprecation warning.

    Wraps the utilities.normalize_zodiac_type function and adds a deprecation
    warning for legacy formats like "tropic" or case-insensitive variants.

    Args:
        zodiac_type: Input zodiac type (may be legacy format)

    Returns:
        Normalized ZodiacType or None if input was None
    """
    if zodiac_type is None:
        return None

    zodiac_str = str(zodiac_type)

    # Check if this is a legacy format (case-insensitive "tropic" or non-canonical case)
    zodiac_lower = zodiac_str.lower()
    if zodiac_lower in ("tropic", "tropical", "sidereal") and zodiac_str not in ("Tropical", "Sidereal"):
        # Normalize using the utilities function
        normalized = normalize_zodiac_type(zodiac_str)

        # Emit deprecation warning for legacy usage
        warnings.warn(
            f"Zodiac type '{zodiac_str}' is deprecated in Kerykeion v5. Use '{normalized}' instead.",
            DeprecationWarning,
            stacklevel=4,
        )
        return normalized

    # Already in correct format or will be normalized by utilities function
    return cast(ZodiacType, normalize_zodiac_type(zodiac_str))


def _normalize_active_points(
    points: Optional[Iterable[Union[str, AstrologicalPoint]]],
) -> Optional[List[AstrologicalPoint]]:
    """Best-effort normalization of legacy string active points list.

    - Accepts None -> None
    - Accepts iterable of strings / AstrologicalPoint literals
    - Filters only those present in DEFAULT_ACTIVE_POINTS to avoid invalid entries
    - Returns None if result would be empty (to let downstream use defaults)
    - Maps old lunar node names to new names with deprecation warning
    """
    if points is None:
        return None
    normalized: List[AstrologicalPoint] = []
    valid: Sequence[AstrologicalPoint] = DEFAULT_ACTIVE_POINTS  # type: ignore[assignment]
    for p in points:
        if isinstance(p, str):
            # Check if this is a legacy node name and map it
            if p in LEGACY_NODE_NAMES_MAP:
                warnings.warn(
                    f"Active point '{p}' is deprecated in Kerykeion v5. Use '{LEGACY_NODE_NAMES_MAP[p]}' instead.",
                    DeprecationWarning,
                    stacklevel=3,
                )
                p = LEGACY_NODE_NAMES_MAP[p]

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

        # Normalize legacy zodiac type values
        zodiac_type = _normalize_zodiac_type_with_warning(zodiac_type)
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

        # Legacy filesystem attributes
        self.json_dir = Path.home()

    # Backward compatibility properties for v4 lunar node names
    @property
    def mean_node(self):
        """Deprecated: Use mean_north_lunar_node instead."""
        warnings.warn(
            "'mean_node' is deprecated in Kerykeion v5. Use 'mean_north_lunar_node' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._model.mean_north_lunar_node

    @property
    def true_node(self):
        """Deprecated: Use true_north_lunar_node instead."""
        warnings.warn(
            "'true_node' is deprecated in Kerykeion v5. Use 'true_north_lunar_node' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._model.true_north_lunar_node

    @property
    def mean_south_node(self):
        """Deprecated: Use mean_south_lunar_node instead."""
        warnings.warn(
            "'mean_south_node' is deprecated in Kerykeion v5. Use 'mean_south_lunar_node' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._model.mean_south_lunar_node

    @property
    def true_south_node(self):
        """Deprecated: Use true_south_lunar_node instead."""
        warnings.warn(
            "'true_south_node' is deprecated in Kerykeion v5. Use 'true_south_lunar_node' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._model.true_south_lunar_node

    # Provide attribute passthrough for planetary points / houses used in README
    def __getattr__(self, item: str) -> Any:  # pragma: no cover - dynamic proxy
        try:
            return getattr(self._model, item)
        except AttributeError:
            raise AttributeError(f"AstrologicalSubject has no attribute '{item}'") from None

    def __repr__(self) -> str:
        return self.__str__()

    # Provide json() similar convenience
    def json(
        self,
        dump: bool = False,
        destination_folder: Optional[Union[str, Path]] = None,
        indent: Optional[int] = None,
    ) -> str:
        """Replicate legacy json() behaviour returning a JSON string and optionally dumping to disk."""

        json_string = self._model.model_dump_json(exclude_none=True, indent=indent)

        if not dump:
            return json_string

        if destination_folder is not None:
            target_dir = Path(destination_folder)
        else:
            target_dir = self.json_dir

        target_dir.mkdir(parents=True, exist_ok=True)
        json_path = target_dir / f"{self._model.name}_kerykeion.json"

        with open(json_path, "w", encoding="utf-8") as file:
            file.write(json_string)
            logging.info("JSON file dumped in %s.", json_path)

        return json_string

    # Legacy helpers -----------------------------------------------------
    @staticmethod
    def _parse_iso_datetime(value: str) -> datetime:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)

    def model(self) -> AstrologicalSubjectModel:
        """Return the underlying Pydantic model (legacy compatibility)."""

        return self._model

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def __str__(self) -> str:
        return (
            f"Astrological data for: {self._model.name}, {self._model.iso_formatted_utc_datetime} UTC\n"
            f"Birth location: {self._model.city}, Lat {self._model.lat}, Lon {self._model.lng}"
        )

    @cached_property
    def utc_time(self) -> float:
        """Backwards-compatible float UTC time value."""

        dt = self._parse_iso_datetime(self._model.iso_formatted_utc_datetime)
        return dt.hour + dt.minute / 60 + dt.second / 3600 + dt.microsecond / 3_600_000_000

    @cached_property
    def local_time(self) -> float:
        """Backwards-compatible float local time value."""

        dt = self._parse_iso_datetime(self._model.iso_formatted_local_datetime)
        return dt.hour + dt.minute / 60 + dt.second / 3600 + dt.microsecond / 3_600_000_000

    # Factory method compatibility (class method in old API)
    @classmethod
    def get_from_iso_utc_time(
        cls,
        name: str,
        iso_utc_time: str,
        city: str = "Greenwich",
        nation: str = "GB",
        tz_str: str = "Etc/GMT",
        online: bool = False,
        lng: Union[int, float] = 0.0,
        lat: Union[int, float] = 51.5074,
        geonames_username: Optional[str] = None,
        zodiac_type: Optional[ZodiacType] = None,
        disable_chiron_and_lilith: bool = False,
        sidereal_mode: Optional[SiderealMode] = None,
        houses_system_identifier: Optional[HousesSystemIdentifier] = None,
        perspective_type: Optional[PerspectiveType] = None,
        **kwargs: Any,
    ) -> "AstrologicalSubject":
        from .astrological_subject_factory import (
            DEFAULT_ZODIAC_TYPE,
            DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
            DEFAULT_PERSPECTIVE_TYPE,
            DEFAULT_GEONAMES_USERNAME,
            GEONAMES_DEFAULT_USERNAME_WARNING,
        )

        _deprecated("AstrologicalSubject.get_from_iso_utc_time", "AstrologicalSubjectFactory.from_iso_utc_time")

        if disable_chiron_and_lilith:
            warnings.warn(
                "'disable_chiron_and_lilith' is ignored by the new factory pipeline.",
                UserWarning,
                stacklevel=2,
            )

        resolved_geonames = geonames_username or DEFAULT_GEONAMES_USERNAME
        if online and resolved_geonames == DEFAULT_GEONAMES_USERNAME:
            warnings.warn(GEONAMES_DEFAULT_USERNAME_WARNING, UserWarning, stacklevel=2)

        # Normalize legacy zodiac type values
        normalized_zodiac_type = _normalize_zodiac_type_with_warning(zodiac_type)

        model = AstrologicalSubjectFactory.from_iso_utc_time(
            name=name,
            iso_utc_time=iso_utc_time,
            city=city,
            nation=nation,
            tz_str=tz_str,
            online=online,
            lng=float(lng),
            lat=float(lat),
            geonames_username=resolved_geonames,
            zodiac_type=(normalized_zodiac_type or DEFAULT_ZODIAC_TYPE),  # type: ignore[arg-type]
            sidereal_mode=sidereal_mode,
            houses_system_identifier=(houses_system_identifier or DEFAULT_HOUSES_SYSTEM_IDENTIFIER),  # type: ignore[arg-type]
            perspective_type=(perspective_type or DEFAULT_PERSPECTIVE_TYPE),  # type: ignore[arg-type]
            **kwargs,
        )

        obj = cls.__new__(cls)
        obj._model = model
        obj.json_dir = Path.home()
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
        new_settings_file: Union[Path, None, dict] = None,  # retained for signature compatibility (unused)
        theme: Union[KerykeionChartTheme, None] = "classic",
        double_chart_aspect_grid_type: Literal["list", "table"] = "list",
        chart_language: KerykeionChartLanguage = "EN",
        active_points: List[AstrologicalPoint] = DEFAULT_ACTIVE_POINTS,  # type: ignore[assignment]
        active_aspects: Optional[List[ActiveAspect]] = None,
        *,
        language_pack: Optional[Mapping[str, Any]] = None,
    ) -> None:
        _deprecated("KerykeionChartSVG", "ChartDataFactory + ChartDrawer")

        if new_settings_file is not None:
            warnings.warn(
                "'new_settings_file' is deprecated and ignored in Kerykeion v5. Use language_pack instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        if isinstance(first_obj, AstrologicalSubject):
            subject_model: Union[AstrologicalSubjectModel, CompositeSubjectModel] = first_obj.model()
        else:
            subject_model = first_obj

        if isinstance(second_obj, AstrologicalSubject):
            second_model: Optional[Union[AstrologicalSubjectModel, CompositeSubjectModel]] = second_obj.model()
        else:
            second_model = second_obj

        if active_aspects is None:
            active_aspects = list(DEFAULT_ACTIVE_ASPECTS)
        else:
            active_aspects = list(active_aspects)

        self.chart_type = chart_type
        self.language_pack = language_pack
        self.theme = theme  # type: ignore[assignment]
        self.double_chart_aspect_grid_type = double_chart_aspect_grid_type
        self.chart_language = chart_language  # type: ignore[assignment]

        self._subject_model = subject_model
        self._second_model = second_model
        self.user = subject_model
        self.first_obj = subject_model
        self.t_user = second_model
        self.second_obj = second_model

        self.active_points = list(active_points) if active_points is not None else list(DEFAULT_ACTIVE_POINTS)  # type: ignore[list-item]
        self._active_points = _normalize_active_points(self.active_points)
        self.active_aspects = active_aspects
        self._active_aspects = active_aspects

        self.output_directory = Path(new_output_directory) if new_output_directory else Path.home()
        self._output_directory = self.output_directory

        self.template = ""
        self.aspects_list: list[dict[str, Any]] = []
        self.available_planets_setting: list[dict[str, Any]] = []
        self.t_available_kerykeion_celestial_points = None
        self.available_kerykeion_celestial_points: list[dict[str, Any]] = []
        self.chart_colors_settings: dict[str, Any] = {}
        self.planets_settings: list[dict[str, Any]] = []
        self.aspects_settings: list[dict[str, Any]] = []
        self.language_settings: dict[str, Any] = {}
        self.height = None
        self.width = None
        self.location = None
        self.geolat = None
        self.geolon = None

        self._chart_drawer: Optional[ChartDrawer] = None
        self._chart_data: Optional[Union[SingleChartDataModel, DualChartDataModel]] = None
        self._external_view = False

    def _ensure_chart(self) -> None:
        if self._chart_drawer is not None:
            return

        if self._subject_model is None:
            raise ValueError("First object is required to build charts.")

        chart_type_normalized = str(self.chart_type).lower()
        active_points = self._active_points
        active_aspects = self._active_aspects
        external_view = False

        if chart_type_normalized in ("natal", "birth", "externalnatal", "external_natal"):
            data = ChartDataFactory.create_natal_chart_data(
                self._subject_model, active_points=active_points, active_aspects=active_aspects
            )
            if chart_type_normalized in ("externalnatal", "external_natal"):
                external_view = True
        elif chart_type_normalized == "synastry":
            if self._second_model is None:
                raise ValueError("Second object is required for Synastry charts.")
            if not isinstance(self._subject_model, AstrologicalSubjectModel) or not isinstance(
                self._second_model, AstrologicalSubjectModel
            ):
                raise ValueError("Synastry charts require two AstrologicalSubject instances.")
            data = ChartDataFactory.create_synastry_chart_data(
                cast(AstrologicalSubjectModel, self._subject_model),
                cast(AstrologicalSubjectModel, self._second_model),
                active_points=active_points,
                active_aspects=active_aspects,
            )
        elif chart_type_normalized == "transit":
            if self._second_model is None:
                raise ValueError("Second object is required for Transit charts.")
            if not isinstance(self._subject_model, AstrologicalSubjectModel) or not isinstance(
                self._second_model, AstrologicalSubjectModel
            ):
                raise ValueError("Transit charts require natal and transit AstrologicalSubject instances.")
            data = ChartDataFactory.create_transit_chart_data(
                cast(AstrologicalSubjectModel, self._subject_model),
                cast(AstrologicalSubjectModel, self._second_model),
                active_points=active_points,
                active_aspects=active_aspects,
            )
        elif chart_type_normalized == "composite":
            if not isinstance(self._subject_model, CompositeSubjectModel):
                raise ValueError("First object must be a CompositeSubjectModel instance for composite charts.")
            data = ChartDataFactory.create_composite_chart_data(
                self._subject_model, active_points=active_points, active_aspects=active_aspects
            )
        else:
            raise ValueError(f"Unsupported or improperly configured chart_type '{self.chart_type}'")

        self._external_view = external_view
        self._chart_data = data
        self.chart_data = data
        self._chart_drawer = ChartDrawer(
            chart_data=data,
            theme=cast(Optional[KerykeionChartTheme], self.theme),
            double_chart_aspect_grid_type=cast(Literal["list", "table"], self.double_chart_aspect_grid_type),
            chart_language=cast(KerykeionChartLanguage, self.chart_language),
            language_pack=self.language_pack,
            external_view=external_view,
        )

        # Mirror commonly accessed attributes from legacy class
        drawer = self._chart_drawer
        self.available_planets_setting = getattr(drawer, "available_planets_setting", [])
        self.available_kerykeion_celestial_points = getattr(drawer, "available_kerykeion_celestial_points", [])
        self.aspects_list = getattr(drawer, "aspects_list", [])
        if hasattr(drawer, "t_available_kerykeion_celestial_points"):
            self.t_available_kerykeion_celestial_points = getattr(drawer, "t_available_kerykeion_celestial_points")
        self.chart_colors_settings = getattr(drawer, "chart_colors_settings", {})
        self.planets_settings = getattr(drawer, "planets_settings", [])
        self.aspects_settings = getattr(drawer, "aspects_settings", [])
        self.language_settings = getattr(drawer, "language_settings", {})
        self.height = getattr(drawer, "height", self.height)
        self.width = getattr(drawer, "width", self.width)
        self.location = getattr(drawer, "location", self.location)
        self.geolat = getattr(drawer, "geolat", self.geolat)
        self.geolon = getattr(drawer, "geolon", self.geolon)
        for attr in ["main_radius", "first_circle_radius", "second_circle_radius", "third_circle_radius"]:
            if hasattr(drawer, attr):
                setattr(self, attr, getattr(drawer, attr))

    # Legacy method names --------------------------------------------------
    def makeTemplate(self, minify: bool = False, remove_css_variables: bool = False) -> str:
        self._ensure_chart()
        assert self._chart_drawer is not None
        template = self._chart_drawer.generate_svg_string(minify=minify, remove_css_variables=remove_css_variables)
        self.template = template
        return template

    def makeSVG(self, minify: bool = False, remove_css_variables: bool = False) -> None:
        self._ensure_chart()
        assert self._chart_drawer is not None
        self._chart_drawer.save_svg(
            output_path=self.output_directory,
            minify=minify,
            remove_css_variables=remove_css_variables,
        )
        self.template = getattr(self._chart_drawer, "template", self.template)

    def makeWheelOnlyTemplate(self, minify: bool = False, remove_css_variables: bool = False) -> str:
        self._ensure_chart()
        assert self._chart_drawer is not None
        template = self._chart_drawer.generate_wheel_only_svg_string(
            minify=minify,
            remove_css_variables=remove_css_variables,
        )
        self.template = template
        return template

    def makeWheelOnlySVG(self, minify: bool = False, remove_css_variables: bool = False) -> None:
        self._ensure_chart()
        assert self._chart_drawer is not None
        self._chart_drawer.save_wheel_only_svg_file(
            output_path=self.output_directory,
            minify=minify,
            remove_css_variables=remove_css_variables,
        )
        self.template = getattr(self._chart_drawer, "template", self.template)

    def makeAspectGridOnlyTemplate(self, minify: bool = False, remove_css_variables: bool = False) -> str:
        self._ensure_chart()
        assert self._chart_drawer is not None
        template = self._chart_drawer.generate_aspect_grid_only_svg_string(
            minify=minify,
            remove_css_variables=remove_css_variables,
        )
        self.template = template
        return template

    def makeAspectGridOnlySVG(self, minify: bool = False, remove_css_variables: bool = False) -> None:
        self._ensure_chart()
        assert self._chart_drawer is not None
        self._chart_drawer.save_aspect_grid_only_svg_file(
            output_path=self.output_directory,
            minify=minify,
            remove_css_variables=remove_css_variables,
        )
        self.template = getattr(self._chart_drawer, "template", self.template)

    # Aliases for new naming in README next (optional convenience)
    save_svg = makeSVG
    save_wheel_only_svg_file = makeWheelOnlySVG
    save_aspect_grid_only_svg_file = makeAspectGridOnlySVG
    makeGridOnlySVG = makeAspectGridOnlySVG


# ---------------------------------------------------------------------------
# Legacy NatalAspects wrapper
# ---------------------------------------------------------------------------
class NatalAspects:
    """Wrapper replicating the master branch NatalAspects interface.

    Replacement: AspectsFactory.single_subject_aspects(subject)
    """

    def __init__(
        self,
        user: Union[AstrologicalSubject, AstrologicalSubjectModel, CompositeSubjectModel],
        new_settings_file: Union[Path, None, dict] = None,
        active_points: Iterable[Union[str, AstrologicalPoint]] = DEFAULT_ACTIVE_POINTS,
        active_aspects: Optional[List[ActiveAspect]] = None,
        *,
        language_pack: Optional[Mapping[str, Any]] = None,
        axis_orb_limit: Optional[float] = None,
    ) -> None:
        _deprecated("NatalAspects", "AspectsFactory.single_chart_aspects")

        if new_settings_file is not None:
            warnings.warn(
                "'new_settings_file' is deprecated and ignored in Kerykeion v5. Use language_pack instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        self.user = user.model() if isinstance(user, AstrologicalSubject) else user
        self.new_settings_file = new_settings_file

        self.language_pack = language_pack
        self.celestial_points: list[Any] = []
        self.aspects_settings: list[Any] = []
        self.axes_orbit_settings = axis_orb_limit

        self.active_points = list(active_points)
        self._active_points = _normalize_active_points(self.active_points)
        if active_aspects is None:
            active_aspects = list(DEFAULT_ACTIVE_ASPECTS)
        else:
            active_aspects = list(active_aspects)
        self.active_aspects = active_aspects

        self._aspects_model = None
        self._all_aspects_cache = None
        self._relevant_aspects_cache = None

    def _build_aspects_model(self):
        if self._aspects_model is None:
            self._aspects_model = AspectsFactory.single_chart_aspects(
                self.user,
                active_points=self._active_points,
                active_aspects=self.active_aspects,
                axis_orb_limit=self.axes_orbit_settings,
            )
        return self._aspects_model

    @cached_property
    def all_aspects(self):
        """Legacy property - returns the same as aspects for backwards compatibility."""
        if self._all_aspects_cache is None:
            self._all_aspects_cache = list(self._build_aspects_model().aspects)
        return self._all_aspects_cache

    @cached_property
    def relevant_aspects(self):
        """Legacy property - returns the same as aspects for backwards compatibility."""
        if self._relevant_aspects_cache is None:
            self._relevant_aspects_cache = list(self._build_aspects_model().aspects)
        return self._relevant_aspects_cache


# ---------------------------------------------------------------------------
# Legacy SynastryAspects wrapper
# ---------------------------------------------------------------------------
class SynastryAspects:
    """Wrapper replicating the master branch synastry aspects interface."""

    def __init__(
        self,
        kr_object_one: Union[AstrologicalSubject, AstrologicalSubjectModel],
        kr_object_two: Union[AstrologicalSubject, AstrologicalSubjectModel],
        new_settings_file: Union[Path, None, dict] = None,
        active_points: Iterable[Union[str, AstrologicalPoint]] = DEFAULT_ACTIVE_POINTS,
        active_aspects: Optional[List[ActiveAspect]] = None,
        *,
        language_pack: Optional[Mapping[str, Any]] = None,
        axis_orb_limit: Optional[float] = None,
    ) -> None:
        _deprecated("SynastryAspects", "AspectsFactory.dual_chart_aspects")

        if new_settings_file is not None:
            warnings.warn(
                "'new_settings_file' is deprecated and ignored in Kerykeion v5. Use language_pack instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        self.first_user = kr_object_one.model() if isinstance(kr_object_one, AstrologicalSubject) else kr_object_one
        self.second_user = kr_object_two.model() if isinstance(kr_object_two, AstrologicalSubject) else kr_object_two
        self.new_settings_file = new_settings_file

        self.language_pack = language_pack
        self.celestial_points: list[Any] = []
        self.aspects_settings: list[Any] = []
        self.axes_orbit_settings = axis_orb_limit

        self.active_points = list(active_points)
        self._active_points = _normalize_active_points(self.active_points)
        if active_aspects is None:
            active_aspects = list(DEFAULT_ACTIVE_ASPECTS)
        else:
            active_aspects = list(active_aspects)
        self.active_aspects = active_aspects

        self._dual_model = None
        self._all_aspects_cache = None
        self._relevant_aspects_cache = None
        self._all_aspects: Union[list, None] = None
        self._relevant_aspects: Union[list, None] = None

    def _build_dual_model(self):
        if self._dual_model is None:
            self._dual_model = AspectsFactory.dual_chart_aspects(
                self.first_user,
                self.second_user,
                active_points=self._active_points,
                active_aspects=self.active_aspects,
                axis_orb_limit=self.axes_orbit_settings,
                first_subject_is_fixed=True,
                second_subject_is_fixed=True,
            )
        return self._dual_model

    @cached_property
    def all_aspects(self):
        """Legacy property - returns the same as aspects for backwards compatibility."""
        if self._all_aspects_cache is None:
            self._all_aspects_cache = list(self._build_dual_model().aspects)
        return self._all_aspects_cache

    @cached_property
    def relevant_aspects(self):
        """Legacy property - returns the same as aspects for backwards compatibility."""
        if self._relevant_aspects_cache is None:
            self._relevant_aspects_cache = list(self._build_dual_model().aspects)
        return self._relevant_aspects_cache

    def get_relevant_aspects(self):
        """Legacy method for compatibility with master branch."""
        return self.relevant_aspects


# ---------------------------------------------------------------------------
# Convenience exports (mirroring old implicit surface API)
# ---------------------------------------------------------------------------
__all__ = [
    "AstrologicalSubject",
    "KerykeionChartSVG",
    "NatalAspects",
    "SynastryAspects",
]
