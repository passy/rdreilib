# -*- coding: utf-8 -*-
"""
 eauth.template
 ~~~~~~~~~~~~~~~~
 Template helpers for the easy authentification middleware.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
 """

from glashammer.utils import get_request

class TemplateUser(object):
    """Allows restricted access to user attributes via template."""

    ALLOWED_METHODS = ('is_authenticated', 'has_perm', 'has_perms')
    ALLOWED_ATTRS = ('is_active', 'is_active', 'is_superuser', 'profile',
                     'user_name')

    def __init__(self):
        self.user = get_request().user
    
    def __getattr__(self, name):
        if name in self.ALLOWED_METHODS or \
           name in self.ALLOWED_ATTRS:
            return getattr(self.user, name)
        else:
            object.__getattr__(self, name)

