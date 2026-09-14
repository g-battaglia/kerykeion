"""Retrograde spans of 2026: where each planet turns back, and where it turns forward.

``RetrogradeStationFactory.retrograde_periods_from_iso_range`` pairs the
retrograde and direct stations into spans. A span that was already running when
the window opened, or still running when it closed, is flagged as clipped — the
station itself lies outside the range, so its bound is the window edge.

Chiron is opt-in: pass it in ``planets`` to have it searched as well.
"""

from kerykeion import RetrogradeStationFactory

DEFAULT_PLANETS = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]


def main() -> None:
    result = RetrogradeStationFactory.retrograde_periods_from_iso_range(
        "2026-01-01",
        "2026-12-31",
        planets=[*DEFAULT_PLANETS, "Chiron"],
    )

    print(f"Retrograde periods in 2026 ({len(result.periods)} spans)")
    print("-" * 78)
    for period in result.periods:
        start_mark = " (clipped)" if period.start_clipped else ""
        end_mark = " (clipped)" if period.end_clipped else ""
        print(f"{period.planet:<10} {period.start[:10]}{start_mark}  ->  {period.end[:10]}{end_mark}")


if __name__ == "__main__":
    main()
