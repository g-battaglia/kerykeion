"""
    This is part of Kerykeion (C) 2022 Giacomo Battaglia
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from requests import Request
from requests_cache import CachedSession
from typing import Union

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class FetchGeonames:
    """
    Class to handle requests to the geonames API

    Args:
    city_name (str): Name of the city
    country_code (str): Two letters country code
    username (str, optional): Geonames username, defaults to "century.boy".
    logger (Union[logging.Logger, None], optional): 
        Optional logger, defaults to None. If none provided creates one.
    """

    def __init__(
        self, city_name: str,
        country_code: str,
        username: str = "century.boy",
        logger: Union[logging.Logger, None] = None
    ):

        self.session = CachedSession(
            cache_name='cache/kerykeion_geonames_cache',
            backend='sqlite',
            expire_after=86400
        )

        self.username = username
        self.city_name = city_name
        self.country_code = country_code
        self.base_url = "http://api.geonames.org/searchJSON"
        self.timezone_url = "http://api.geonames.org/timezoneJSON"
        self.__logger = logger or logging.getLogger(self.__class__.__name__)

    def __get_timezone(self, lat: Union[str, float, int], lon: Union[str, float, int]) -> dict[str, str]:
        """
        Get the timezone for a given latitude and longitude
        """
        # Dictionary that will be returned:
        timezone_data = {}

        params = {
            "lat": lat,
            "lng": lon,
            "username": self.username
        }

        prepared_request = Request(
            "GET", self.timezone_url, params=params).prepare()
        self.__logger.debug(
            f"Requesting data from geonames timezones: {prepared_request.url}")

        try:
            response = self.session.send(prepared_request)
            response_json = response.json()

        except Exception as e:
            self.__logger.error(f"Error fetching {self.timezone_url}: {e}")
            return {}

        try:
            timezone_data['timezonestr'] = response_json['timezoneId']

        except Exception as e:
            self.__logger.error(
                f"Error serializing data maybe wrong username? Details: {e}")
            return {}

        if hasattr(response, 'from_cache'):
            timezone_data['from_tz_cache'] = response.from_cache

        return timezone_data

    def __get_contry_data(self, city_name: str, country_code: str) -> dict[str, str]:
        """
        Get the city data *whitout timezone* for a given city and country name
        """
        # Dictionary that will be returned:
        city_data_whitout_tz = {}

        params = {
            "q": city_name,
            "contry": country_code,
            "username": self.username,
            "maxRows": 1,
            "style": "FULL"
        }

        prepared_request = Request(
            "GET", self.base_url, params=params).prepare()
        self.__logger.debug(
            f"Requesting data from geonames basic: {prepared_request.url}")

        try:
            response = self.session.send(prepared_request)
            response_json = response.json()

        except Exception as e:
            self.__logger.error(f"Error in fetching {self.base_url}: {e}")
            return {}

        try:
            city_data_whitout_tz['name'] = response_json['geonames'][0]['name']
            city_data_whitout_tz['lat'] = response_json['geonames'][0]['lat']
            city_data_whitout_tz['lng'] = response_json['geonames'][0]['lng']
            city_data_whitout_tz['countryCode'] = response_json['geonames'][0]['countryCode']

        except Exception as e:
            self.__logger.error(
                f"Error serializing data maybe wrong username? Details: {e}")
            return {}

        if hasattr(response, 'from_cache'):
            city_data_whitout_tz['from_country_cache'] = response.from_cache

        return city_data_whitout_tz

    def get_serialized_data(self) -> dict[str, str]:
        """
        Returns all the data necessary for the Kerykeion calculation.        

        Returns:
            dict[str, str]: _description_
        """
        city_data_response = self.__get_contry_data(
            self.city_name, self.country_code)
        try:
            timezone_response = self.__get_timezone(
                city_data_response['lat'], city_data_response['lng'])

        except Exception as e:
            self.__logger.error(f"Error in fetching timezone: {e}")
            return {}

        return {**timezone_response, **city_data_response}


if __name__ == "__main__":
    geonames = FetchGeonames("Roma", "IT")
    print(geonames.get_serialized_data())
