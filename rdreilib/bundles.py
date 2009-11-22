# -*- coding: utf-8 -*-
"""
 rdrei.lib.bundles
 ~~~~~~~~~~~~~~~~
 Additional glashammer bundles.


 :copyright: 2008 by Pascal Hartig <phartig@rdrei.net>
 :license: BSD, see doc/LICENSE for more details.
 """

from werkzeug.contrib.cache import SimpleCache
from glashammer.bundles.sqlalchdb import session
from glashammer.utils import get_app

from rdreilib.eauth import setup_eauth
from rdreilib.eauth.facebook import setup_facebook_connect
from rdreilib.middleware.csrf_protection import setup_csrf_protection

def setup_repozewhat(app, user_class, group_class, permission_class, **repozekw):
    """
    Add repoze.what support to your Glashammer application.
    """
    from repoze.what.plugins.quickstart import setup_sql_auth

    app.add_middleware(setup_sql_auth, user_class, group_class, permission_class,
                       session, **repozekw)

def setup_caching(app, **kwargs):
    """
    Add the werkzeug SimpleCache to application.
    """
    
    cache = SimpleCache(**kwargs)
    setattr(app, 'cache', cache)

def get_cache():
    return get_app().cache

__all__ = ['setup_repozewhat', 'setup_caching', 'get_cache',
           'setup_csrf_protection']
