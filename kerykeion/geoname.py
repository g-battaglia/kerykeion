# -*- coding: utf-8 -*-
"""
    This file is part of openastro.org.

    OpenAstro.org is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenAstro.org is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with OpenAstro.org.  If not, see <https://www.gnu.org/licenses/>.
"""

"""
docs at:
    https://www.geonames.org/export/geonames-search.html

preset vars:
    featureClass=P (populated place)
    maxRows=1
"""

from urllib.request import urlopen
from urllib.parse import urlencode
from xml.dom.minidom import parseString
from socket import timeout
from urllib.error import HTTPError, URLError
from os import mkdir, path, getcwd, remove
import json
import logging


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def _getText(nodelist):
    """"
    Internal function to return text from nodes
    """
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc


def geonames_proxy(operation: str, params: str):
    # directory to store cache files in
    cache_directory = '.geonames_cache'

    # supported API calls and their corresponding file cache names
    cache_file_name = {
        'search': 'geonames_search_cache.json',
        'timezone': 'geonames_timezone_cache.json'
    }
    # supported API calls and their corresponding API endpoints
    api_endpoints = {
        'search': "http://api.geonames.org/search?%s",
        'timezone': "http://api.geonames.org/timezone?%s"
    }
    cache_file_name = cache_file_name[operation]
    cache_file_path = path.join(cache_directory, cache_file_name)
    api_endpoint = api_endpoints[operation]

    try:
        # try to create a directory to store the cache in
        # might fail under wrong permission settings
        if not path.exists(cache_directory):
            # mkdir if it doesn't already exist
            mkdir(cache_directory)
    except:
        logging.error(f'Failed to create directory: {cache_directory}')
        logging.error(f'Maybe check permissions in: "{getcwd()}"?')
        raise Exception(f'Error: failed to create {cache_directory} directory.')

    # dict to store the cache data in the program
    cache_dict = dict()
    try:
        # check if file exists
        if path.exists(cache_file_path) and path.getsize(cache_file_path) > 0:
            # then open it for reading with ability to write
            # an empty file is definitely not useful to json.load() so we'll just skip that and create a new one
            cache_file = open(cache_file_path, 'r+', encoding='utf-8')
            # then load data from it
            try:
                # this can fail if json file is corrupted
                cache_dict = json.load(cache_file)
                logging.debug(f'Loaded proxy cache file: "{cache_file_path}" and parsed as JSON.')

            except:
                logging.error(f'Failed to parse JSON file: "{cache_file_path}"!')
                cache_file.seek(0)
                logging.error(f'Contents: {cache_file.read()}')
                logging.error(f'Try removing: {path.join(getcwd(),cache_directory)}')
                raise Exception('Error: Failed to parse JSON file!')
        else:
            # if file doesn't exist or is empty create it for writing with ability to read
            cache_file = open(cache_file_path, 'w+', encoding='utf-8')

    except:
        logging.debug(f'Failed to access: {cache_file_path}')
        raise Exception('Error: failed to access Geonames cache file.')

    if params not in cache_dict or cache_dict[params] == "":
        # if the file does not contain the key with the parameters proceed into the branch
        # if the file does contain the key with the param but it's empty then we'll replace it
        # if the file does already contain the API response then this branch is skipped and data from the file is
        # returned instead
        if params in cache_dict and cache_dict[params] == "":
            logging.warning(f'Proxy cache file has an empty value for key:"{params}".')
        elif params not in cache_dict:
            logging.debug(f'Params: "{params}" not found in proxy cache file.')
        try:
            # try to query geonames
            logging.debug(f'Calling Geonames API endpoint: "{api_endpoint}" with params: "{params}".')
            http_response = urlopen(api_endpoint % params, timeout=20)

        except (HTTPError, URLError) as error:
            logging.error(f'Not retrieved because {error}\nURL: {cache_dict[params]}')
            raise Exception('Error: failed to access Geonames service.')

        except timeout:
            logging.error('Timeout on search in Geonames API!')
            raise Exception('Error: Timeout on connection with Geonames.')

        # store the response in the dict
        data = http_response.read()
        cache_dict[params] = data.decode('UTF-8')

        # empty the file. Without this json.dump() will append to the existing data
        cache_file.close()
        cache_file = open(cache_file_path, 'w', encoding='utf-8')

        # dump the dict in JSON format into the file
        json.dump(cache_dict, cache_file)
        cache_file.close()
        logging.debug('Saved new proxy cache file.')

    return cache_dict[params], cache_file_path


def search(name='', country=''):
    """Search function for geonames.org api
            name must be supplied
            country is optional, 2 character country code
    """
    # check name
    if name == '':
        logging.error('No name specified for Geonames search!')
        return None

    # open connection and read xml
    params = urlencode({'q': name, 'country': country, 'maxRows': 1,
                        'featureClass': 'P', 'username': 'century.boy'})

    try:
        data, cache_file_path = geonames_proxy('search', params)
        dom = parseString(data)
    except Exception:
        return None

    # totalResultsCount
    try:
        totalResultsCount = _getText(
            dom.getElementsByTagName("totalResultsCount")[0].childNodes)
    except:
        logging.error("Geonames API response could not be parsed! Maybe you exceeded API hourly limit?")
        logging.error(f"String that failed to parse: {data}")
        # remove the cache_file since it now contains the hourly limit error message
        remove(cache_file_path)
        return None


    # geoname
    geoname = []
    for i in dom.getElementsByTagName("geoname"):
        geoname.append({})
        geoname[-1]['name'] = _getText(
            i.getElementsByTagName("name")[0].childNodes)
        geoname[-1]['lat'] = _getText(i.getElementsByTagName("lat")
                                      [0].childNodes)
        geoname[-1]['lng'] = _getText(i.getElementsByTagName("lng")
                                      [0].childNodes)
        geoname[-1]['geonameId'] = _getText(
            i.getElementsByTagName("geonameId")[0].childNodes)
        geoname[-1]['countryCode'] = _getText(
            i.getElementsByTagName("countryCode")[0].childNodes)
        geoname[-1]['countryName'] = _getText(
            i.getElementsByTagName("countryName")[0].childNodes)
        geoname[-1]['fcl'] = _getText(i.getElementsByTagName("fcl")
                                      [0].childNodes)
        geoname[-1]['fcode'] = _getText(
            i.getElementsByTagName("fcode")[0].childNodes)
        # get timezone
        tparams = urlencode(
            {'lat': geoname[-1]['lat'], 'lng': geoname[-1]['lng'], 'username': 'century.boy'})
        try:
            data, cache_file_path = geonames_proxy('timezone', tparams)
        except Exception:
            return None

        tdom = parseString(data)

        try:
            geoname[-1]['timezonestr'] = _getText(tdom.getElementsByTagName("timezoneId")[0].childNodes)
        except:
            logging.error("Geonames API response could not be parsed! Maybe you exceeded API hourly limit?")
            logging.error(f"String that failed to parse: {data}")
            # remove the cache_file since it now contains the hourly limit error message
            remove(cache_file_path)
            return None

        tdom.unlink()
        break
    # close dom
    dom.unlink()

    # return results
    if totalResultsCount == "0":
        logging.error("No results found using Geonames API!")
        return None
    else:
        return geoname
