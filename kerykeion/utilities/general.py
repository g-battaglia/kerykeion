from kerykeion.utilities import kr_settings
from os.path import abspath

def print_settings_path():
    path = abspath(kr_settings.__file__)
    print(path)


if __name__ == "__main__":
    print_settings_path()