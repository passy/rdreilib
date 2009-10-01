# -*- coding: utf-8 -*-
"""
rdreilib.utils
~~~~~~~~~~~~~~

Various, useful utilities.

:copyright: 2009, Pascal Hartig <phartig@rdrei.net>
:license: GPL v3, see doc/LICENSE for more details.
"""

class LazySettings(object):
    """A lazy settings store that is filled on application setup. Used as
    singleton."""

    def __getattr__(self, name):
        print "Looking for %r" % name
        value = self.__dict__.get(name, None)
        if value is None:
            raise RuntimeError("Configuration was not set up properly.")

        return value

    def __setattribute__(self, name, value):
        if value is None:
            raise RuntimeError("A LazySetting value cannot be None.")

        self.__dict__[name] = value
