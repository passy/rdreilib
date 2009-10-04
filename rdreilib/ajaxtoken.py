# -*- coding: utf-8 -*-
"""
 marksman.lib.ajaxtoken
 ~~~~~~~~~~~~~~~~
 Library to prevent CSRF


 :copyright: 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
"""


from glashammer.utils import get_app, Request
from glashammer.bundles.i18n import _

from jsonlib import JSONException

from functools import wraps
from hashlib import sha1
from time import time
import logging

log = logging.getLogger("rdreilib.ajaxtoken")

def _generate_token():
    return sha1("%s#%s" % (time(), get_app().cfg['sessions/secret'])).hexdigest()

def set_ajax_token(func):
    """Generates a new ajax token and pins it at the session."""
    if callable(func):
        @wraps(func)
        def decorate(self, req, *args, **kwargs):
            req.session['security.ajax_token'] = _generate_token()
            return func(self, req, *args, **kwargs)

        return decorate
    elif isinstance(func, Request):
        # We have an instance of a glashammer request, not a function to
        # decorate, but we still need a session.
        func.session['security.ajax_token'] = _generate_token()
    else:
        raise TypeError("Func is not a function or a request object.")

def require_ajax_token_factory(reset):
    """Creates a new decorator for ajax token validation.
    :param reset {bool}: Sets whether to automatically generate a new one or
    keep the old.
    :return: func
    """
    def outer(func):
        """Decorator that throws a JSONException if a _ajax_token is not set in 
        POST and sets a new token if it was found."""
        @wraps(func)
        def decorate(self, req, *args, **kwargs):
            if '_ajax_token' not in req.form or \
               'security.ajax_token' not in req.session or \
               req.form['_ajax_token'] != req.session['security.ajax_token']:
                try:
                    log.debug("Expected: %r, got %r.",
                              req.session['security.ajax_token'],
                              req.form['_ajax_token'])
                except KeyError, err:
                    log.warn("Encountered key error while retrieving ajax"
                              "debug information. Probably broken session.")

                raise JSONException(_("Invalid AJAX token!"
                                      " Please reload this page."))
            else:
                if reset:
                    token = _generate_token()
                    req.session['security.ajax_token'] = token
                return func(self, req, *args, **kwargs)
        return decorate
    return outer

# Default decorator.
require_ajax_token = require_ajax_token_factory(True)

def enhance_ajax_token(req, dic):
    """Enhances a response dictionary be a '_ajax_token' value."""
    if type(dic) != dict:
        raise TypeError("Expected a dictionary.")

    dic.update({'_ajax_token': req.session['security.ajax_token']})
    return dic

__all__ = ('set_ajax_token', 'require_ajax_token', 'enhance_ajax_token')
