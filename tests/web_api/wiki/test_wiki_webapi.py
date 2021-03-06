# -*- coding: utf-8 -*-
"""
Onyx Project
https://onyxlabs.fr
Software under licence Creative Commons 3.0 France
http://creativecommons.org/licenses/by-nc-sa/3.0/fr/
You may not use this software for commercial purposes.
@author :: Cassim Khouani
"""
import json
import pytest
from flask import session

@pytest.mark.usefixtures('db', 'connected_app')
class Test_WikiApi:

    def test_wiki_get(self, connected_app):
        response = connected_app.post('/api/wiki', {"search": "Ada Lovelace", "lang": "en"})
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        assert response.json['status'] == 'success'



