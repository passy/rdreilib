# -*- coding: utf-8 -*-
"""
rdreilib.middleware.csrf_protection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides a simple middleware to secure against Cross Site Remote Forgery
attacks by setting cookies on every request and validate them on post
requests.

:copyright: 2009, Pascal Hartig <phartig@rdrei.net>
:license: GPL v3, see doc/LICENSE for more details.
"""

from hashlib import sha1
from glashammer.utils import get_app
from time import time


class CSRFProtectionMiddleware(object):
    """Data structure that emulates a WSGI middleware object, but relies on
    glashammer's event infrastructure to avoid the overhead of generating
    request objects over and over again.

    Please use :func:`setup_csrf_protection` and don't use this directly!"""

    def __init__(self, app, cookie_name):
        self.app = app
        self.cookie_name = cookie_name

        app.connect_event('response-start', self.set_cookie)

    def set_cookie(self, response):
        response.set_cookie(self.cookie_name, self._generate_token())

    def _generate_token(self):
        """Generate a new random string based on time and secret set in the
        options."""
        return sha1("%s#%s" % (time(), self.app.cfg['sessions/secret'])).hexdigest()

def setup_csrf_protection(app, cookie_name='r3csrfprot'):
    """Sets up the csrf protection middleware.

    :param cookie_name: Cookie to store the secret key in.
    """

    middleware = CSRFProtectionMiddleware(app, cookie_name)
