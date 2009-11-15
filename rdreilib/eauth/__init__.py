# -*- coding: utf-8 -*-
"""
 rdreilib.eauth
 ~~~~~~~~~~~~~~~~
 An Easy Authentication WSGI middleware inspired by the django
 auth system.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: BSD, see doc/LICENSE for more details.
"""

from models import User, Group, Permission, AnonymousUser
from ..database import session
from sqlalchemy import and_, or_
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import eagerload
from glashammer.utils import url_for, get_request, get_application
from werkzeug.utils import redirect

import datetime, cPickle as pickle

SESSION_KEY = '_auth_user_id'
REDIRECT_FIELD_NAME = 'came_from'

def authenticate(login, password):
    """If the given login (username or email) and password
    are valid, return a User object."""

    #user = User.query.filter(or_(User.user_name==login,
    #                             User.email==login))
    try:
        user = User.query.\
                filter(User.user_name==login).\
                one()
    except NoResultFound:
        return None
    if user.validate_password(password):
        return user

def login(req, user):
    """Persist a user id in the request."""

    user.profile.last_login = datetime.datetime.now()
    session.commit()

    req.session[SESSION_KEY] = user.user_id
    req.set_user(user)

def logout(req):
    """Removes the session values."""
    if SESSION_KEY in req.session:
        del req.session[SESSION_KEY]

    req.unset_user()

def invalidate(req, user_id=None):
    """Invalidates the user cache. Call this after changing anything in the
    user object or profile.

    :param user_id: User ID to invalidate. Defaults to currently logged in
    user.

    TODO: Consider calling this automatically on save.
    """

    app = get_application()
    if app.cfg['cache/enabled'] and app.cfg['cache/user_key']:
        cache = req.cache.get_cache(app.cfg['cache/user_key'])
        cache.remove(req.user.user_id)
        cache.remove('perm_{0}'.format(req.user.user_id))

def _redirect_unauthorized(resp):
    if resp.status_code == 401:
        # We need the request for later redirecting.
        req = get_request()
        resp.headers['Location'] = url_for("auth/login", **{REDIRECT_FIELD_NAME:
                                                            req.url})
        resp.status_code = 302

def _get_user(user_id, cache=None):
    """Gets a user from cache if provided or database if cache does not
    provide it."""

    def _query_db():
        return User.query.\
                options(eagerload('profile')).\
                filter_by(user_id=user_id).\
                one()

    # Either query cache or directly query db if no cache is present.
    if cache is not None:
        # Beaker handles the pickling not correctly
        try:
            user = pickle.loads(cache.get(user_id))
        except KeyError:
            user = _query_db()
            # Looks stupid, but is really useful. It triggers the
            # cached_property decorator and saves the permission query result
            # to user's __dict__. It's important this is done before pickling.
            user.permissions = user.permissions
            cache.put(user_id, pickle.dumps(user))

        return user

    else:
        return _query_db()

def setup_eauth(app, auth_realm=None, session_based=True, cache_key=None):
    """Sets up eauth in the glashammer application.

    :param digest_auth: Boolean that indicates whether to store an optional MD5
    hash of username:password:realm.
    :param session_based: Boolean indicating whether to use a store login
    information is session. If False, you have to take care of the user's login
    state yourself.
    :param cache_key: ``None`` disables caching, any string is taken as
    beaker cache key. Keep this to invalidate the cache on any update to the
    user.
    """
    # Add config variables
    app.add_config_var('general/auth_realm', str, auth_realm)
    # How long may a user stay in cache before getting invalidated?
    app.add_config_var('cache/user_timeout', int, 300)

    # This should not be configurable via INI, because the string is used
    # internally by your application. You better define a constant for that.
    app.add_config_var('cache/user_key', str, cache_key)

    if cache_key:
        if not app.cfg['cache/enabled']:
            raise RuntimeError("You have to enable beaker caching in order to"
                               " use eauth user caching!")

    def _tag_request(req):
        """Closure that hands the user over the request object."""
        assert hasattr(req, 'session'), "We require the request object to provide "\
                "a valid session."

        cache = None
        if cache_key is not None:
            # Create a new beaker cache object
            cache = req.cache.get_cache(cache_key,
                                        expire=app.cfg['cache/user_timeout'])

        if SESSION_KEY in req.session:
            user = _get_user(req.session[SESSION_KEY], cache)
            if user:
                req.set_user(user)

    if session_based:
        app.connect_event('request-start', _tag_request)
        app.connect_event('response-start', _redirect_unauthorized)

