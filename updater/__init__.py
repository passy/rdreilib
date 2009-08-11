# -*- coding: utf-8 -*-
"""
 rdreilib.updater
 ~~~~~~~~~~~~~~~~
 A library for online updates of WSGI apps.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
"""

from werkzeug.routing import Submount
from .controller import UpdateController

from .urls import make_urls
from os.path import dirname, join


def setup_updater(app, app_path='/_updater'):
    app.add_template_searchpath(join(dirname(__file__), 'templates'))
    app.add_shared('updater', join(dirname(__file__), join(dirname(__file__),
                                                           'shared')))
    app.add_url_rules([Submount(app_path, make_urls())])
    app.add_views_controller(UpdateController.endpoint, UpdateController())
