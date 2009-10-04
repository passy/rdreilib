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
from version import __version__
from . import config

from .urls import make_urls
from os.path import dirname, join, exists


def setup_updater(app, configfile, app_path='/_updater'):
    setup_config(app, configfile)
    app.add_template_searchpath(join(dirname(__file__), 'templates'))
    app.add_shared('updater', join(dirname(__file__), join(dirname(__file__),
                                                           'shared')))
    app.add_url_rules([Submount(app_path, make_urls())])
    app.add_views_controller(UpdateController.endpoint, UpdateController())

def setup_config(app, filename):
    """Creates a new configuration object and binds it to the module."""
    setattr(app, 'updater_config', config.UpdaterConfig(filename))
    if not exists(filename):
        # Forces to rewrite
        app.updater_config.change_single('general/version', __version__)

__all__ = ('setup_updater',)
