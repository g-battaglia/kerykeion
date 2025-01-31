import json
from kerykeion.utilities import setup_logging
from kerykeion import AstrologicalSubject

setup_logging(level="debug")

# With Chiron enabled
johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US")
print(json.loads(johnny.json(dump=True)))

print('\n')
print(johnny.chiron)

# With Chiron disabled
johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", disable_chiron=True)
print(json.loads(johnny.json(dump=True)))

print('\n')
print(johnny.chiron)

# With Sidereal Zodiac
johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", zodiac_type="Sidereal", sidereal_mode="LAHIRI")
print(johnny.json(dump=True, indent=2))

# With Morinus Houses
johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", houses_system_identifier="M")
print(johnny.json(dump=True, indent=2))

# With True Geocentric Perspective
johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", perspective_type="True Geocentric")
print(johnny.json(dump=True, indent=2))

# With Heliocentric Perspective
johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", perspective_type="Heliocentric")
print(johnny.json(dump=True, indent=2))

# With Topocentric Perspective
johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", perspective_type="Topocentric")

# Test Mean Lilith
johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", disable_chiron_and_lilith=True)
print(johnny.mean_lilith)

# Offline mode
johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", online=False, tz_str="America/New_York", lng=-87.1111, lat=37.7711, sidereal_mode="FAGAN_BRADLEY", zodiac_type="Sidereal")
print(johnny.json(dump=True, indent=2))
