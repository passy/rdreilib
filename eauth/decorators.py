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

def require_perm(func, perms):
    @wraps(func)
    def _deco(self, req, *args, **kwargs):
        if type(perms) is list:
            if req.user.has_perms(perms):
                return func(self, req, *args, **kwargs)
        else:
            if requ.user.has_perm(perms):
                return func(self, req, *args, **kwargs)
        raise Forbidden("Permission(s) %r required!" % perms)
    return _deco

