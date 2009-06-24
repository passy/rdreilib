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

    ALLOWED_ATTR = ('is_authenticated', 'has_perm', 'has_perms',
                    'is_active', 'is_active', 'is_superuser')
    
    def __init__(self):
        self.user = get_request().user

        # Reference allowed attributes/methods from user to this
        # wrapper class.
        for attr in self.ALLOWED_ATTR:
            setattr(self, attr, getattr(self.user, attr))

