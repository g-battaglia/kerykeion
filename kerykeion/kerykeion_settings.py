# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2023 Giacomo Battaglia
"""
from typing import Dict, List, Union
from pydantic import BaseModel
from pathlib import Path
from json import load, dump
from dataclasses import dataclass
import os


class BaseModel(BaseModel):
    def __init__(self, **data):
        super().__init__(**data)

    def __getitem__(self, item):
        return getattr(self, item)

    def get(self, item, default=None):
        return getattr(self, item, default)


## Celestial Points Settings
class KerykeionSettingsCelestialPointModel(BaseModel):
    id: int
    name: str
    color: str
    is_active: bool
    element_points: int
    related_zodiac_signs: List[int]
    label: str


## Chart Colors Settings
class KerykeionSettingsChartColorsModel(BaseModel):
    paper_0: str = "#000000"
    paper_1: str = "#ffffff"
    zodiac_bg_0: str = "#ff7200"
    zodiac_bg_1: str = "#6b3d00"
    zodiac_bg_2: str = "#69acf1"
    zodiac_bg_3: str = "#2b4972"
    zodiac_bg_4: str = "#ff7200"
    zodiac_bg_5: str = "#6b3d00"
    zodiac_bg_6: str = "#69acf1"
    zodiac_bg_7: str = "#2b4972"
    zodiac_bg_8: str = "#ff7200"
    zodiac_bg_9: str = "#6b3d00"
    zodiac_bg_10: str = "#69acf1"
    zodiac_bg_11: str = "#2b4972"
    zodiac_icon_0: str = "#ff7200"
    zodiac_icon_1: str = "#6b3d00"
    zodiac_icon_2: str = "#69acf1"
    zodiac_icon_3: str = "#2b4972"
    zodiac_icon_4: str = "#ff7200"
    zodiac_icon_5: str = "#6b3d00"
    zodiac_icon_6: str = "#69acf1"
    zodiac_icon_7: str = "#2b4972"
    zodiac_icon_8: str = "#ff7200"
    zodiac_icon_9: str = "#6b3d00"
    zodiac_icon_10: str = "#69acf1"
    zodiac_icon_11: str = "#2b4972"
    zodiac_radix_ring_0: str = "#ff0000"
    zodiac_radix_ring_1: str = "#ff0000"
    zodiac_radix_ring_2: str = "#ff0000"
    zodiac_transit_ring_0: str = "#ff0000"
    zodiac_transit_ring_1: str = "#ff0000"
    zodiac_transit_ring_2: str = "#0000ff"
    zodiac_transit_ring_3: str = "#0000ff"
    houses_radix_line: str = "#ff0000"
    houses_transit_line: str = "#0000ff"
    lunar_phase_0: str = "#000000"
    lunar_phase_1: str = "#FFFFFF"
    lunar_phase_2: str = "#CCCCCC"


## Aspect Settings
class KerykeionSettingsAspectModel(BaseModel):
    degree: int
    name: str
    is_active: bool
    visible_grid: bool
    is_major: bool
    is_minor: bool
    orb: int
    color: str


## Language Settings
class KerykeionLanguageCelestialPointModel(BaseModel):
    Sun: str
    Moon: str
    Mercury: str
    Venus: str
    Mars: str
    Jupiter: str
    Saturn: str
    Uranus: str
    Neptune: str
    Pluto: str
    Asc: str
    Mc: str
    Dsc: str
    Ic: str
    North_Node: str
    Mean_Node: str


class KerykeionLanguageModel(BaseModel):
    info: str
    cusp: str
    longitude: str
    latitude: str
    north: str
    east: str
    south: str
    west: str
    fire: str
    earth: str
    air: str
    water: str
    and_word: str
    transits: str
    type: str
    aspects: str
    planets_and_house: str
    transit_name: str
    lunar_phase: str
    day: str
    celestial_points: KerykeionLanguageCelestialPointModel


## Settings Model
class KerykeionSettingsModel(BaseModel):
    axes_orbit: int
    planet_in_zodiac_extra_points: int
    chart_colors: KerykeionSettingsChartColorsModel = KerykeionSettingsChartColorsModel()
    celestial_points: List[KerykeionSettingsCelestialPointModel]
    aspects: List[KerykeionSettingsAspectModel]
    language_settings: dict[str, KerykeionLanguageModel]


def parse_settings_file(new_settings_file: Union[str, Path, None] = None) -> Dict:
    if new_settings_file is not None:
        settings_file = Path(new_settings_file)
        if not settings_file.exists():
            raise FileNotFoundError(f"File {settings_file} does not exist")

    # Check if there is a settings file in windows, linux or mac
    home_folder = Path.home()
    settings_file = home_folder / ".config" / "kerykeion" / "kr.config.json"

    if not settings_file.exists():
        settings_file = Path(__file__).parent / "kr.config.json"

    with open(settings_file, "r") as f:
        settings_dict = load(f)

    return settings_dict


def merge_settings_file(settings: KerykeionSettingsModel, new_settings: Dict) -> KerykeionSettingsModel:
    new_settings_dict = settings.dict() | new_settings
    return KerykeionSettingsModel(**new_settings_dict)


if __name__ == "__main__":
    print(parse_settings_file())
