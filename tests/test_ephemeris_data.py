from kerykeion import EphemerisDataFactory
from datetime import datetime

def test_ephemeris_data():
    start_date = datetime.fromisoformat("2020-01-01")
    end_date = datetime.fromisoformat("2020-01-03")

    factory = EphemerisDataFactory(
        start_datetime=start_date,
        end_datetime=end_date,
        step_type="days",
        step=1,
        lat=37.9838,
        lng=23.7275,
        tz_str="Europe/Athens",
        is_dst=False,
        max_hours=None,
        max_minutes=None,
        max_days=None,
    )

    ephemeris_data = factory.get_ephemeris_data(as_model=True)

    assert ephemeris_data is not None
    assert ephemeris_data[0].planets is not None
    assert ephemeris_data[0].houses is not None
    assert ephemeris_data[0].planets[0].name == "Sun"
    assert ephemeris_data[0].houses[0].name == "First_House"
