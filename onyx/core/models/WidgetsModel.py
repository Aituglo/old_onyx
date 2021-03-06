# -*- coding: utf-8 -*-
"""
Onyx Project
https://onyxlabs.fr
Software under licence Creative Commons 3.0 France
http://creativecommons.org/licenses/by-nc-sa/3.0/fr/
You may not use this software for commercial purposes.
@author :: Cassim Khouani
"""
from onyx.extensions import db

class Widget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    color = db.Column(db.String(256))
    url = db.Column(db.String(256))
    user = db.Column(db.Integer())
    name = db.Column(db.String(256))
    see_more = db.Column(db.String(256))
    param = db.Column(db.String())
