from datetime import datetime, timedelta
from kerykeion import (
    TransitsTimeRangeFactory,
    EphemerisDataFactory,
    AstrologicalSubject,
)

# Create a natal chart for the subject
person = AstrologicalSubjectFactory.from_birth_data(
    "Johnny Depp", 1963, 6, 9, 20, 15, 0, "Owensboro", "US"
)

# Define the time period for transit calculation
start_date = datetime.now()
end_date = datetime.now() + timedelta(days=30)

# Create ephemeris data for the specified time period
ephemeris_factory = EphemerisDataFactory(
    start_datetime=start_date,
    end_datetime=end_date,
    step_type="days",
    step=1,
    lat=person.lat,
    lng=person.lng,
    tz_str=person.tz_str,
)

ephemeris_data_points = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()

# Calculate transits for the subject
transit_factory = TransitsTimeRangeFactory(
    natal_chart=person,
    ephemeris_data_points=ephemeris_data_points,
)

transit_results = transit_factory.get_transit_moments()

# Print example data
print(transit_results.model_dump()["dates"][2])
print(transit_results.model_dump()["transits"][2]['date'])
print(transit_results.model_dump()["transits"][2]['aspects'][0])
