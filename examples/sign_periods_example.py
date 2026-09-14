"""Where every planet sits, sign by sign, across one month.

``SignIngressFactory.sign_periods_from_iso_range`` turns the ingress moments
into stays: one row per planet per sign, with the entry and exit instants. A
stay already under way when the window opens (or still under way when it closes)
is flagged as clipped, because the ingress itself falls outside the range.

The Moon is opt-in — it changes sign every two and a half days, so it is only
searched when named in ``planets``.
"""

from kerykeion import SignIngressFactory

PLANETS = ["Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]


def main() -> None:
    result = SignIngressFactory.sign_periods_from_iso_range("2026-03-01", "2026-04-01", planets=PLANETS)

    print(f"Sign stays, 2026-03-01 to 2026-04-01 ({len(result.periods)} stays)")
    print("-" * 78)
    for period in result.periods:
        start_mark = "<" if period.start_clipped else " "
        end_mark = ">" if period.end_clipped else " "
        print(f"{period.planet:<10} {period.sign:<4} {start_mark}{period.start[:10]}  ..  {period.end[:10]}{end_mark}")


if __name__ == "__main__":
    main()
