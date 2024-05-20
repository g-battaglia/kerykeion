# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2024 Giacomo Battaglia
"""


from json import load
import logging
from pathlib import Path
from typing import Dict, Union
from kerykeion.kr_types import KerykeionSettingsModel


def get_settings(new_settings_file: Union[Path, None] = None) -> KerykeionSettingsModel:
    """
    This function is used to get the settings dict from the settings file.
    If no settings file is passed as argument, or the file is not found, it will fallback to:
    - The system wide config file, located in ~/.config/kerykeion/kr.config.json
    - The default config file, located in the package folder
    
    Args:
        new_settings_file (Union[Path, None], optional): The path of the settings file. Defaults to None.
        
    Returns:
        Dict: The settings dict
    """

    # Config path we passed as argument
    if new_settings_file is not None:
        settings_file = new_settings_file

        if not settings_file.exists():
            raise FileNotFoundError(f"File {settings_file} does not exist")

    # System wide config path
    else:
        home_folder = Path.home()
        settings_file = home_folder / ".config" / "kerykeion" / "kr.config.json"

    # Fallback to the default config in the package
    if not settings_file.exists():
        settings_file = Path(__file__).parent / "kr.config.json"

    logging.debug(f"Kerykeion config file path: {settings_file}")
    with open(settings_file, "r", encoding="utf8") as f:
        settings_dict = load(f)

    return KerykeionSettingsModel(**settings_dict)


def merge_settings(settings: KerykeionSettingsModel, new_settings: Dict) -> KerykeionSettingsModel:
    """
    This function is used to merge the settings file with the default settings,
    it's useful to add new settings to the config file without breaking the old ones.
    
    Args:
        settings (KerykeionSettingsModel): The default settings
        new_settings (Dict): The new settings to add to the default ones
        
    Returns:
        KerykeionSettingsModel: The new settings
    """
    new_settings_dict = settings.model_dump() | new_settings
    return KerykeionSettingsModel(**new_settings_dict)


if __name__ == "__main__":
    from kerykeion.utilities import setup_logging
    setup_logging(level="debug")

    print(get_settings())
