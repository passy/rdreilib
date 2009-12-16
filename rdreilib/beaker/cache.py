# -*- coding: utf-8 -*-
"""
rdreilib.beaker.cache
~~~~~~~~~~~~~~~~~~~~~
Glashammer bundle for beaker cache.

:copyright: 2009, Pascal Hartig <phartig@rdrei.net>
:license: BSD, see doc/LICENSE for more details.
"""

from .utils import make_beaker_dict_from_config
from beaker.middleware import CacheMiddleware

def _enhance_request(req):
    """Make cache object available in request object."""

    req.set_cache(req.environ['beaker.cache'])

def setup_cache(app):
    app.add_config_var("cache/enabled", bool, False)
    app.add_config_var("cache/expire", int, None)
    #TODO: Make regions Work!
    app.add_config_var("cache/regions", str, None)
    app.add_config_var("cache/regions_config", str, None)

    app.add_config_var("cache/data_dir", str, None)
    app.add_config_var("cache/lock_dir", str, None)
    app.add_config_var("cache/type", str, None)
    app.add_config_var("cache/url", str, None)

    config = make_beaker_dict_from_config(app.cfg, "cache/", "cache.")

    app.add_middleware(CacheMiddleware, config)
    app.connect_event('request-start', _enhance_request)

__all__ = ('setup_cache',)
