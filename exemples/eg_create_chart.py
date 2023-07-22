from kerykeion import AstrologicalSubject, KerykeionChartSVG
from pathlib import Path

CURRENT_DIR = Path(__file__).parent


def main():
    first = AstrologicalSubject("Jack", 1990, 6, 15, 15, 15, "Roma", zodiac_type="Tropic")
    second = AstrologicalSubject("Jane", 1991, 10, 25, 21, 00, "Roma", zodiac_type="Tropic")

    # Set the type, it can be Natal, Synastry or Transit

    name = KerykeionChartSVG(
        first, chart_type="Synastry", second_obj=second,
    )

    name.makeSVG()
    print(len(name.aspects_list))


if __name__ == "__main__":
    main()
