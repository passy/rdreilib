# -*- coding: utf-8 -*-
"""
 rdreilib.eauth
 ~~~~~~~~~~~~~~~~
 An Easy Authentication WSGI middleware inspired by the django
 auth system.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
"""

from models import User, Group, Permission, AnonymousUser
from ..database import session
from sqlalchemy import and_, or_
from sqlalchemy.orm.exc import NoResultFound
from glashammer.utils import url_for, get_request
from werkzeug.utils import redirect

import datetime

SESSION_KEY = '_auth_user_id'
REDIRECT_FIELD_NAME = 'came_from'

def authenticate(login, password):
    """If the given login (username or email) and password
    are valid, return a User object."""

    #user = User.query.filter(or_(User.user_name==login,
    #                             User.email==login))
    try:
        user = User.query.filter(User.user_name==login).one()
    except NoResultFound:
        return None
    if user.validate_password(password):
        return user

def login(req, user):
    "Persist a user id in the request."

    user.profile.last_login = datetime.datetime.now()
    session.commit()

    req.session[SESSION_KEY] = user.user_id
    req.set_user = user

def logout(req):
    "Removes the session values."
    if SESSION_KEY in req.session:
        del req.session[SESSION_KEY]

    req.unset_user()

def _tag_request(req):
    assert hasattr(req, 'session'), "We require the request object to provide "\
            "a valid session."
    if SESSION_KEY in req.session:
        user = User.query.filter_by(user_id=req.session[SESSION_KEY]).one()
        if user:
            req.set_user(user)

def _redirect_unauthorized(resp):
    if resp.status_code == 401:
        # We need the request for later redirecting.
        req = get_request()
        resp.headers['Location'] = url_for("auth/login", **{REDIRECT_FIELD_NAME: req.path,
                                                            '_external': True})
        resp.status_code = 302

def setup_eauth(app):
    app.connect_event('request-start', _tag_request)
    app.connect_event('response-start', _redirect_unauthorized)

