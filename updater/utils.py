# -*- coding: utf-8 -*-
"""
rdreilib.updater.utils
~~~~~~~~~~~~~~~~~~~~~~
Various little helpers.

:copyright: 2009, Pascal Hartig <phartig@rdrei.net>
:license: GPL v3, see doc/LICENSE for more details.
"""

from functools import wraps

def session_cached(func):
    @wraps
    def _decorate(self, *args, **kwargs):
        key = 'sc_'+func.__name__
        if not hasattr(self.session, key):
            result = func(self, *args, **kwargs)
            self.session[key] = result

        return self.session[key]
    return _decorate


