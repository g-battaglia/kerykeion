#!/usr/bin/env python3
"""
Generate reference data from Python Kerykeion for comparison with Dart implementation.
"""
import sys
sys.path.insert(0, '../..')

from kerykeion import AstrologicalSubject
import json

def test_basic_chart():
    """Test basic chart calculation."""
    subject = AstrologicalSubject(
        name="Test",
        year=2000,
        month=1,
        day=1,
        hour=12,
        minute=0,
        city="Greenwich",
        nation="GB",
        lng=0.0,
        lat=51.48,
        tz_str="UTC",
        online=False
    )
    
    result = {
        "name": subject.name,
        "julian_day": subject.julian_day,
        "sun": {
            "name": subject.sun.name,
            "abs_pos": subject.sun.abs_pos,
            "sign": subject.sun.sign,
            "position": subject.sun.position,
            "quality": subject.sun.quality,
            "element": subject.sun.element,
        },
        "moon": {
            "name": subject.moon.name,
            "abs_pos": subject.moon.abs_pos,
            "sign": subject.moon.sign,
            "position": subject.moon.position,
        },
        "ascendant": {
            "name": subject.ascendant.name,
            "abs_pos": subject.ascendant.abs_pos,
            "sign": subject.ascendant.sign,
            "position": subject.ascendant.position,
        },
        "first_house": {
            "abs_pos": subject.first_house.abs_pos,
        },
        "houses": [
            subject.first_house.abs_pos,
            subject.second_house.abs_pos,
            subject.third_house.abs_pos,
            subject.fourth_house.abs_pos,
            subject.fifth_house.abs_pos,
            subject.sixth_house.abs_pos,
            subject.seventh_house.abs_pos,
            subject.eighth_house.abs_pos,
            subject.ninth_house.abs_pos,
            subject.tenth_house.abs_pos,
            subject.eleventh_house.abs_pos,
            subject.twelfth_house.abs_pos,
        ]
    }
    
    return result

if __name__ == "__main__":
    result = test_basic_chart()
    print(json.dumps(result, indent=2))
