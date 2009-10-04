# -*- coding: utf-8 -*-
"""
rdreilib.beaker.session
~~~~~~~~~~~~~~~~~~~~~~~
Glashammer bundle for beaker session integration.

:copyright: 2009, Pascal Hartig <phartig@rdrei.net>
:license: GPL v3, see doc/LICENSE for more details.
"""

from beaker.middleware import SessionMiddleware
from .utils import make_dict
from ..exceptions import ConfigError

import logging

log = logging.getLogger("rdreilib.beaker.session")

_REQUIRED_VARS = (
    'session.type',
    'session.lock_dir',
    'session.key',
    'session.secret'
)

def _check_config(config):
    for var in _REQUIRED_VARS:
        if config[var] is None:
            raise ConfigError("Required option %s for Beaker Sessions was not "
                               "set up!" % var)

    if config['session.type'] in ("ext:memcached", "ext:database") and\
       'url' not in config:
        raise ConfigError("Beaker session requires a 'url' config, if 'type' "
                          "is %s!" % config['type'])

def setup_session(app):
    app.add_config_var("sessions/cookie_expires", int, None)
    app.add_config_var("sessions/cookie_domain", str, None)
    app.add_config_var("sessions/key", str, 'beaker.session.id')

    # This must be set by the user!
    app.add_config_var("sessions/secret", str, None)
    app.add_config_var("sessions/secure", bool, False)
    app.add_config_var("sessions/auto", bool, False)
    app.add_config_var("sessions/timeout", int, None)

    # Same for caching
    app.add_config_var("sessions/data_dir", str, None)
    app.add_config_var("sessions/lock_dir", str, None)
    app.add_config_var("sessions/type", str, None)
    app.add_config_var("sessions/url", str, None)

    config = make_dict(app.cfg, "sessions/", "session.")
    _check_config(config)

    app.add_middleware(SessionMiddleware, config)

__all__ = ('setup_session',)
