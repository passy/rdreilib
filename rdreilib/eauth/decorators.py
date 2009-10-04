# -*- coding: utf-8 -*-
"""
 eauth.decorators
 ~~~~~~~~~~~~~~~~
 Controller/View decorators for easy authentication.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
 """

from werkzeug.exceptions import Forbidden, Unauthorized
from functools import wraps

def require_login(func):
    @wraps(func)
    def _deco(self, req, *args, **kwargs):
        if req.user.is_authenticated():
            return func(self, req, *args, **kwargs)
        else:
            raise Unauthorized("Login required!")
    return _deco

def require_logout(func):
    "Same as require_login, but the opposite and no redirect."
    @wraps(func)
    def _deco(self, req, *args, **kwargs):
        if not req.user.is_authenticated():
            return func(self, req, *args, **kwargs)
        else:
            raise Forbidden("Only accessible without login.")
    return _deco

def require_perm(perms):
    def _outer(func):
        @wraps(func)
        def _deco(self, req, *args, **kwargs):
            if type(perms) is list:
                if req.user.has_perms(perms):
                    return func(self, req, *args, **kwargs)
            else:
                if req.user.has_perm(perms):
                    return func(self, req, *args, **kwargs)
            raise Forbidden("Permission(s) %r required!" % perms)
        return _deco
    return _outer

