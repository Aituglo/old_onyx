#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Onyx Project
http://onyxproject.fr
Software under licence Creative Commons 3.0 France
http://creativecommons.org/licenses/by-nc-sa/3.0/fr/
You may not use this software for commercial purposes.
@author :: Cassim Khouani
"""

import sys
import os

from flask import json
from flask_script import Manager, Command, Option

from onyx.extensions import db
from onyx.api.server import *
from onyx.flask_config import *
from onyx.util.log import getLogger
from onyx import *

app = create_app()

manager = Manager(app, with_default_commands=False)
server = Server()

LOG = getLogger(__name__)

class Run(Command):

    option_list = (
        Option('--host', '-h', dest='host', default="0.0.0.0"),
        Option('--port', '-p', dest='port', default=8080),
        Option('--debug', '-d', dest='debug', default=False, action="store_true"),
        Option('--reload', '-r', dest='reload', default=False, action="store_true")
    )

    def run(self, host='0.0.0.0', port=8080, debug=False, reload=False):
        self.runserver(host, port, debug, reload)

    def sync_blueprints(self, app):
        blueprints_fabrics(app, get_blueprints(app))
        error_pages(app)

    def runserver(self, host, port, debug, reload):
        print(' _____   __   _  __    __ __    __ ')
        print('/  _  \ |  \ | | \ \  / / \ \  / / ')
        print('| | | | |   \| |  \ \/ /   \ \/ /')
        print('| | | | | |\   |   \  /     }  {')
        print('| |_| | | | \  |   / /     / /\ \ ')
        print('\_____/ |_|  \_|  /_/     /_/  \_\ ')
        print('')
        print('-------------------------------------------------------')
        print('')
        LOG.info('Environment: ' + "Debug" if debug else "Production" )
        LOG.info('Port: '+ str(port))
        print('')
        print('-------------------------------------------------------')
        from datetime import datetime
        LOG.info(datetime.utcnow())
        print('')
        print('-------------------------------------------------------')
        LOG.info('You can access to Onyx with : http://'+host+':'+str(port))
        LOG.info('You can close Onyx at any time with Ctrl-C')
        print('')
        print('-------------------------------------------------------')
        self.sync_blueprints(app)
        app.run(host, int(port), debug=debug, use_reloader=reload, threaded=True)


manager.add_command('run', Run())

if __name__=='__main__':
    manager.run()
