# -*- coding: utf-8 -*-
"""
 eauth.facebook
 ~~~~~~~~~~~~~~~~
 Middleware for facebook connect.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
 """

from .models import User, Profile
from ..database import session
from . import login
from glashammer.utils import emit_event

import hashlib
import logging

log = logging.getLogger('eauth.facebook')

class FacebookMiddleware(object):
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key

    def check_cookie(self, req):
        """Check for a valid facebook cookie and set try to get
        the user from DB or create a new one."""

        if not req.user.is_authenticated():
           log.debug("User not logged in. Let's get the party started!")
           if self.api_key in req.cookies:
               log.debug("API cookie found.")
               signature_hash = self._get_facebook_signature(req.cookies, True)
               if signature_hash == req.cookies[self.api_key]:
                   log.debug("Hash key is valid! Assuming the user is valid!")
                   self._login_or_create(req, req.cookies["%s_%s" %
                                         (self.api_key, "user")])

               else:
                   log.info("Hash invalid! Expected: %s, got: %s!" %
                            (signature_hash, req.cookies[self.api_key]))

    def _login_or_create(self, req, username, _recursive=False):
        """Trying to find the user based on the ID we get from the
        cookie and set the session cookie or, if the user is not yet
        in the database, create a new one."""
        USERNAME_SCHEMA = u"FBConnect_%s"
        user = User.query.filter(User.user_name==USERNAME_SCHEMA %
                                 username).first()
        if user:
            log.debug("Logging in user via facebook connect: %r" % user)
            emit_event("fconnect-login", user)
            login(req, user)
        else:
            # Creating a new user
            user = User()
            user.user_name = USERNAME_SCHEMA % username
            user.set_unusable_password()
            profile = Profile()
            profile.user = user
            profile.uses_facebook_connect = True
            #TODO: Get first and last name from FB!
            emit_event("fconnect-create-user", user, profile)
            session.add_all([user, profile])
            session.commit()
            if not _recursive:
                # Make sure we don't loop because of some weird
                # database failures.
                return self._login_or_create(req, user.user_name, True)

    def _get_facebook_signature(self, values_dict, is_cookie_check=False):
        signature_keys = []
        for key in sorted(values_dict.keys()):
            if (is_cookie_check and key.startswith(self.api_key + '_')):
                signature_keys.append(key)
            elif (is_cookie_check is False):
                signature_keys.append(key)

        if (is_cookie_check):
            signature_string = ''.join(['%s=%s' % (x.replace(self.api_key + '_',''), values_dict[x]) for x in signature_keys])
        else:
            signature_string = ''.join(['%s=%s' % (x, values_dict[x]) for x in signature_keys])
        signature_string = signature_string + self.secret_key

        log.debug("Generated string: %r" % signature_string)
        return hashlib.md5(signature_string).hexdigest()


def setup_facebook_connect(app):
    app.add_config_var('facebook/api_key', str, '')
    app.add_config_var('facebook/secret_key', str, '')

    FM = FacebookMiddleware(app.cfg['facebook/api_key'],
                            app.cfg['facebook/secret_key'])

    app.connect_event('request-start', FM.check_cookie)

