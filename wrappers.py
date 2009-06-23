# -*- coding: utf-8 -*-
"""
 rdreilib.wrappers
 ~~~~~~~~~~~~~~~~
 Better wrapper modules


 :copyright: 2008 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL, see doc/LICENSE for more details.
 """

from eauth.models import AnonymousUser

from glashammer.utils.wrappers import Request as GHRequest
from glashammer.utils.wrappers import Response as GHResponse
from glashammer.bundles.sessions import get_session

class Request(GHRequest):

    _user = None

    @property
    def session(self):
        return get_session()
        
    @property
    def cache(self):
        return self.app.cache

    @property
    def repo_user(self):
        """Returns an instance of the current logged in user model or None
        if middleware is not present or user not logged in."""
        if 'repoze.who.identity' in self.environ:
            return self.environ['repoze.who.identity'].get('user')

    @property
    def user(self):
        """Returns a user object or a django-style AnonymousUser object."""
        if self._user:
            return self._user
        else:
            return AnonymousUser()

    def set_user(self, user):
        self._user = user

    def unset_user(self):
        self._user = None

class Response(GHResponse):
    pass

