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
    along with OpenAstro.org.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
docs at:
	http://www.geonames.org/export/geonames-search.html

preset vars:
	featureClass=P (populated place)
	maxRows=1
"""

from urllib.request import urlopen
from urllib.parse import urlencode
from xml.dom.minidom import parseString
from socket import timeout
from urllib.error import HTTPError, URLError


def _getText(nodelist):
	"""Internal function to return text from nodes
	"""
	rc = ""
	for node in nodelist:
		if node.nodeType == node.TEXT_NODE:
			rc = rc + node.data
	return rc

def search(name='',country=''):
	
	"""Search function for geonames.org api
		name must be supplied
		country is optional, 2 character country code
	"""
	#check name
	if name == '':
		print('No name specified!')
		return None
		
	#open connection and read xml
	params = urlencode({'q': name,'country':country,'maxRows':1,'featureClass':'P','username': 'century.boy'})

	try:
		f = urlopen("http://api.geonames.org/search?%s" % params, timeout=20)

	except (HTTPError, URLError) as error:
		print('Errir: not retrieved because %s\nURL: %s', error, f)

	except timeout:
		print('Timeout on search!')
		return None
	
	data = f.read()
	dom = parseString(data)

	#totalResultsCount
	totalResultsCount = _getText(dom.getElementsByTagName("totalResultsCount")[0].childNodes)
	
	#geoname
	geoname=[]
	for i in dom.getElementsByTagName("geoname"):
		geoname.append({})
		geoname[-1]['name']=_getText(i.getElementsByTagName("name")[0].childNodes)
		geoname[-1]['lat']=_getText(i.getElementsByTagName("lat")[0].childNodes)
		geoname[-1]['lng']=_getText(i.getElementsByTagName("lng")[0].childNodes)
		geoname[-1]['geonameId']=_getText(i.getElementsByTagName("geonameId")[0].childNodes)
		geoname[-1]['countryCode']=_getText(i.getElementsByTagName("countryCode")[0].childNodes)
		geoname[-1]['countryName']=_getText(i.getElementsByTagName("countryName")[0].childNodes)
		geoname[-1]['fcl']=_getText(i.getElementsByTagName("fcl")[0].childNodes)
		geoname[-1]['fcode']=_getText(i.getElementsByTagName("fcode")[0].childNodes)
		#get timezone
		tparams = urlencode({'lat':geoname[-1]['lat'],'lng':geoname[-1]['lng'],'username':'century.boy'})		
		try:
			f = urlopen("http://api.geonames.org/timezone?%s" % tparams, timeout=20)
		except (HTTPError, URLError) as error:
			print('Errir: not retrieved because %s\nURL: %s', error, f)
		except timeout:
			print('Timeout on search!')
			return None

		data = f.read()
		tdom = parseString(data)
		geoname[-1]['timezonestr']=_getText(tdom.getElementsByTagName("timezoneId")[0].childNodes)
		tdom.unlink()
		break
	#close dom
	dom.unlink()
	
	#return results
	if totalResultsCount == "0":
		print("No results!")
		return None
	else:
		return geoname