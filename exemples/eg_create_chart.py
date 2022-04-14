from kerykeion import KrInstance, MakeSvgInstance
from pathlib import Path


def main():
    first = KrInstance("Jack", 1990, 6, 15, 15, 15,
                       "Roma", zodiactype="Tropic")
    second = KrInstance("Jane", 1991, 10, 25, 21, 00,
                        "Roma", zodiactype="Tropic")

    # Set the type, it can be Natal, Composite or Transit
    CURRENT_DIR = Path(__file__).parent
    name = MakeSvgInstance(
        first, chart_type="Composite",
        second_obj=second,
        new_settings_file=CURRENT_DIR / "new-kr.config.json"
    )

    name.makeSVG()
    print(len(name.aspects_list))


if __name__ == "__main__":
    main()
