# -*- coding: utf-8 -*-
"""
 rdrei.lib.auth
 ~~~~~~~~~~~~~~~~
 Enhancemend functionality of repoze.what.
 Also a great place to put some predicates in.


 :copyright: 2008 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL, see doc/LICENSE for more details.
 """

from werkzeug import exceptions as w_exc
from glashammer.utils.local import get_request
from functools import wraps

from repoze.what.predicates import not_anonymous, in_group

def require(predicate):
    "Decorates a view method to requre a specific predicate."
    def _outer(func):
        "Returns the real decorator."

        @wraps(func)
        def _inner(self, req, *args, **kwargs):
            if not predicate.is_met(req.environ):
                raise w_exc.Unauthorized()
            return func(self, req, *args, **kwargs)
        return _inner

    return _outer

class TemplateUser(object):
    """A singleton object, that allows easy access on common
    methods and attributes of a logged in user like checks whether
    he's actually logged in or if he's an admin. Used for templates."""

    def __init__(self):
        self.environ = get_request().environ

    @property
    def user_name(self):
        return self.environ['REMOTE_USER']

    def is_authorized(self):
        return not_anonymous().is_met(self.environ)

    def is_admin(self):
        return in_group('admins').is_met(self.environ)

    def get_object(self):
        """Returns the SQLAlchemy object for this user. Only use this if you
        really have to!
        @returns rdrei.models:User object or None if not logged in."""

        if hasattr(self.environ, 'repoze.who.identity'):
            return self.environ['repoze.who.identity']['user']

__all__ = ('require_auth', 'has_login', 'TemplateUser')
