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
from glashammer.utils.local import get_app
from glashammer.bundles.sessions import get_session
from werkzeug.utils import cached_property

import logging

log = logging.getLogger('rdreilib.wrappers')

class Request(GHRequest):

    _user = None
    _cache = None

    @property
    def session(self):
        if 'beaker.session' in self.environ:
            return self.environ['beaker.session']
        else:
            return get_session()

    @property
    def cache(self):
        if self._cache is not None:
            return self._cache

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

    @cached_property
    def facebook(self):
        """Get a facebook object, if pyfacebook is present, the user is logged
        in and is a facebook connect user. Otherwise this is None."""
        try:
            from facebook import Facebook
        except ImportError:
            log.warning("PyFacebook is not installed!")
        else:
            if self.user and self.user.profile.uses_facebook_connect:
                # This implies, that the correct cookies must be set. We don't
                # double check for that.
                api_key = get_app().cfg['facebook/api_key']
                secret_key = get_app().cfg['facebook/secret_key']
                facebook = Facebook(api_key, secret_key)
                # Settings the cookie values
                # It's so cool to have no private attributes. (;
                facebook.uid = self.cookies["%s_user" % api_key]
                facebook.session_key = self.cookies["%s_session_key" % api_key]
                return facebook

    def set_user(self, user):
        self._user = user

    def unset_user(self):
        self._user = None

    def set_cache(self, cache):
        self._cache = cache

class Response(GHResponse):
    pass

