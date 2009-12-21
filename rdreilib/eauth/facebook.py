# -*- coding: utf-8 -*-
"""
 eauth.facebook
 ~~~~~~~~~~~~~~~~
 Middleware for facebook connect.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: BSD, see doc/LICENSE for more details.
 """

from .models import User, Profile, Group
from ..database import session
from . import login
from glashammer.utils import emit_event

import hashlib
import logging
import datetime

log = logging.getLogger('eauth.facebook')

class FacebookMiddleware(object):
    # Wrapping map for profile attributes
    PROFILE_ATTRIBUTE_WRAPPER = {
        'first_name': 'first_name',
        'last_name': 'last_name',
        'proxied_email': 'email',
        'pic_square_with_logo': 'fb_pic_url',
        'website': 'fb_website',
        'username': 'fb_username',
        'profile_url': 'fb_profile'
    }

    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
        self.group_id = None

    def set_group_id(self, group_id):
        self.group_id = group_id

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
                   self._set_fbsession(req, req.cookies)
                   self._login_or_create(req, req.cookies["%s_%s" %
                                         (self.api_key, "user")])

               else:
                   log.info("Hash invalid! Expected: %s, got: %s!" %
                            (signature_hash, req.cookies[self.api_key]))

            # Check for new 'mu' facebook connect alpha cookies
           elif 'fbs_'+self.api_key in req.cookies:

               log.debug("Connect-JS API Cookie found.")
               cookiedict = \
                       self._decode_connectjs_cookie(req.cookies['fbs_'+self.api_key])

               # We should probably check for more attributes, but this is
               # most important.
               if 'sig' in cookiedict:
                   signature_hash = self._get_connectjs_signature(cookiedict)

                   if signature_hash == cookiedict['sig']:
                       log.debug("ConnectJS key is valid. Assuming the user is "
                                 "as well.")
                       self._set_fbsession(req, cookiedict, version=2)
                       self._login_or_create(req, cookiedict['uid'])
                   else:
                       log.info("Hash invalid. Expected %s, got %s!" % (
                           signature_hash, cookiedict['sig']))

    def check_profile(self, req, user):
        """Checks the user profile and fetches missing data from facebook."""
        # First name is mandatory on facebook, so if this is missing, the
        # data has not been fetched yet.
        if user.profile.first_name is None:
            self.update_profile(req, user)

    def update_profile(self, req, user):
        """Updates the profile data from facebook."""
        if not req.facebook:
            log.warn("Updating profile failed, because facebook request "
                     "object was not present.")
            return

        #! This can raise an exception!
        user_data = req.facebook.users.getInfo(req.facebook.uid,
                                               self.PROFILE_ATTRIBUTE_WRAPPER.keys())

        assert (len(user_data) == 1), "Invalid response from facebook while "\
            "fetching user data!"

        profile = user.profile
        for (key, value) in user_data[0].iteritems():
            if key in self.PROFILE_ATTRIBUTE_WRAPPER:
                setattr(profile, self.PROFILE_ATTRIBUTE_WRAPPER[key], value)

        # Update the time stamp
        profile.fb_last_update = datetime.datetime.now()
        log.debug("Updated facebook profile data for user %r." % user)

        session.add(profile)
        session.commit()

    def _set_fbsession(self, req, cookies, version=1):
        """Make facebook user id and session id available in the session.
        Respects the version changes between facebook connect version 1 and
        connectJS."""

        session_dict = {}

        if version == 1:
            session_dict = {
                'fb_user_id': cookies['%s_user' % self.api_key],
                'fb_session_id': cookies['%s_session_key' % self.api_key]
            }
        elif version == 2:
            session_dict = {
                'fb_user_id': cookies['uid'],
                'fb_session_id': cookies['session_key']
            }
        else:
            raise TypeError("Facebook Connect API version %r is not supported "
                            "yet." % version)

        req.session.update(session_dict)

    def _set_user_group(self, user):
        """Set the user group using the group id specified."""

        if self.group_id:
            group = Group.query.get(self.group_id)
            user.groups.append(group)

    def _login_or_create(self, req, username, _recursive=False):
        """Trying to find the user based on the ID we get from the
        cookie and set the session cookie or, if the user is not yet
        in the database, create a new one."""
        USERNAME_SCHEMA = u"FBConnect_%s"
        user = User.query.filter(User.user_name==USERNAME_SCHEMA %
                                 username).first()
        if user:
            log.debug("Logging in user via facebook connect: %r" % user)
            emit_event("fconnect-login-start", req, user)
            login(req, user)
            emit_event("fconnect-login-end", req, user)
        else:
            # Creating a new user
            user = User(USERNAME_SCHEMA % username, '')
            # Make sure the user can only log in via facebook. Ha, we are
            # smarter than pinax was. :D
            user.set_unusable_password()
            self._set_user_group(user)

            # Initializing an empty profile. It's getting populated on first
            # login.
            profile = Profile()
            profile.user = user
            profile.uses_facebook_connect = True

            emit_event("fconnect-create-user", user, profile)
            session.add_all([user, profile])
            session.commit()
            if not _recursive:
                # Make sure we don't loop because of some weird
                # database failures.
                log.debug("New user created. Logging in now.")
                # Don't use user.user_name here, because it includes the
                # FBConnect_ prefix!
                return self._login_or_create(req, username, True)

    def _decode_connectjs_cookie(self, cookie):
        """
        Expects a cookie string and turns it into a dict.
            >>> _decode_connectjs_cookie(u"expires=1234&secret=abcdert")
            {'expires': 1234, 'secret': abcdert'}

            >>> _decode_connectjs_cookie(u"blablanotvalid")
            {}

        """

        # It's enclosed in useless quotes
        cookie = cookie.replace('"', '')
        try:
            return dict(bit.split('=') for bit in cookie.split('&'))
        except ValueError:
            return {}



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

    def _get_connectjs_signature(self, cookiedict):
        """
        Calculates a md5 signature from the cookie dict we have.
        This is not documented by facebook, but I seems to work.
        """

        sorted_keys = sorted(cookiedict.keys())

        # 'sig' is the comparison value. It's not included
        signature = ''.join(['%s=%s' % (key, cookiedict[key]) for key
                             in sorted_keys if key != 'sig'])

        # Append the secret
        signature += self.secret_key

        return hashlib.md5(signature).hexdigest()

def setup_facebook_connect(app, fetch_profile=False, group_id=None):
    """
    Enables facebook connect support. If a user has the correct cookies
    regarding the api and secret keys you provided, the user will be
    registered ie. a User object will be created. If ``fetch_profile`` is
    enabled, a user profile is created, too.

    :param group_id: Optional integer parameter. New facebook connect users
    will join this group.
    """
    app.add_config_var('facebook/api_key', str, '')
    app.add_config_var('facebook/secret_key', str, '')

    FM = FacebookMiddleware(app.cfg['facebook/api_key'],
                            app.cfg['facebook/secret_key'])
    FM.set_group_id(group_id)

    app.connect_event('request-start', FM.check_cookie)

    if fetch_profile:
        log.info('Saving Facebook profile information is not compatible with their '
                 'Storable Data Guidelines.')
        # If this extra option is set, the profile is checked for existence and
        # missing data is fetched via FQL
        app.connect_event('fconnect-login-end', FM.check_profile)

# vim: set ts=8 sw=4 tw=78 ft=python: 
