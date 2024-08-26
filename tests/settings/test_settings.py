from kerykeion.settings import get_settings
from kerykeion.kr_types import KerykeionSettingsModel
import pathlib  
import json

file_path = pathlib.Path(__file__).parent / "test-settings.json"

def test_file_settings():
    settings = get_settings(file_path)

    assert settings["language_settings"]['EN']['info'] == "This is a test file"

def test_dict_settings():

    with open(file_path, 'r') as file:
        settings = json.load(file)

    settings = get_settings(settings)

    assert settings["language_settings"]['EN']['info'] == "This is a test file"    

def test_model_settings():
    with open(file_path, 'r') as file:
        settings = json.load(file)
    
    settings_model = KerykeionSettingsModel(**settings)
    settings = get_settings(settings_model)

    assert settings.language_settings['EN']['info'] == "This is a test file"

if __name__ == "__main__":
    test_file_settings()
    test_dict_settings()
    test_model_settings()