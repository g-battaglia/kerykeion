from kerykeion import KrInstance, MakeSvgInstance
from pathlib import Path

CURRENT_DIR = Path(__file__).parent


def main():
    first = KrInstance("Jack", 1990, 6, 15, 15, 15, "Roma", zodiac_type="Tropic")
    second = KrInstance("Jane", 1991, 10, 25, 21, 00, "Roma", zodiac_type="Tropic")

    # Set the type, it can be Natal, Composite or Transit

    name = MakeSvgInstance(
        first, chart_type="Composite", second_obj=second, new_settings_file=CURRENT_DIR / "new-kr.config.json"
    )

    name.makeSVG()
    print(len(name.aspects_list))


if __name__ == "__main__":
    main()
