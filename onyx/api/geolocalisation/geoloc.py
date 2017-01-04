# -*- coding: utf-8 -*-
"""
Onyx Project
http://onyxproject.fr
Software under licence Creative Commons 3.0 France
http://creativecommons.org/licenses/by-nc-sa/3.0/fr/
You may not use this software for commercial purposes.
@author :: Cassim Khouani
"""

from onyx.api.assets import decodeJSON

def get_geoloc():
	result = decodeJSON.decodeURL("http://ip-api.com/json")
	return result

def get_string():
	result = get_geoloc()
	return "Vous êtes aux coordonnées " + str(result['lat']) + ' | ' + str(result['lon'])