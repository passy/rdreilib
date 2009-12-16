# -*- coding: utf-8 -*-
"""
rdreilib.beaker.decorators
~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides some decorators for easier use.

:copyright: 2009, Pascal Hartig <phartig@rdrei.net>
:license: BSD, see doc/LICENSE for more details.
"""

from functools import wraps
from werkzeug.wrappers import Request
import inspect


class CachedView(object):
    """Decorator class that caches either a function based view or a class
    based action for a specified amount of time."""

    def __init__(self, namespace, cache_args=None, **kwargs):
        """
        Creates a new cache decorator overriding the default expire and
        namespace values specified in the config.ini.

        :param namespace: `thing` to cache. Keep for invaliation.
        :param cache_args: function arguments used to generate the key from.
        Accepts a list of argument names. String representation of arguments
        is used, so make sure you properly implemented __str__.

        Additional arguments are passed to :class:`beaker.Cache`.
        """

        self.namespace = namespace
        self.cache_args = cache_args
        self.extra_kwargs = kwargs

    def __call__(self, func):
        """The real decorator call."""

        @wraps(func)
        def _inner(*args, **kwargs):
            req = self.get_request(args)
            cache = self.get_cache(req)
            key = self.generate_key(func, args, kwargs)

            return cache.get(key, createfunc=lambda: func(*args, **kwargs))

        return _inner


    def _get_argument_value(self, index, args, kwargs):
        """Returns the value on a list of arguments and keywords arguments on
        a specific index."""

        args_len = len(args)

        if index <= args_len:
            return str(args[index])
        else:
            return str(kwargs[index - args_len])


    def generate_key(self, func, args, kwargs):
        """Generate the key used to store and retrieve objects from cache.
        Function module, name and arguments specified in ``extra_kwargs`` are
        used."""

        key = [func.__module__, func.__name__]

        if self.cache_args is not None:
            arg_spec = inspect.getargspec(func).args
            for cachable_arg in self.cache_args:
                # Get index of argument in total list of arguments
                index = None
                for i, arg in enumerate(arg_spec):
                    if arg == cachable_arg:
                        index = i
                        break

                if index:
                    key.append(self._get_argument_value(index, args, kwargs))

        return '.'.join(key)


    def get_request(self, args):
        """Tries to retrieve the request object from a list of arguments.
        Returns the first argument in the list that looks like a request
        object."""

        for arg in args:
            if isinstance(arg, Request):
                return arg

        raise TypeError("No request object found in function call!")

    def get_cache(self, req):
        """Get a cache instance from a request object using the settings
        provided in the constructor."""

        kwargs = {'name': self.namespace}
        kwargs.update(self.extra_kwargs)

        return req.cache.get_cache(**kwargs)


    def cached_action(self, func):
        """Wrapper for a controller based action, i.e. a function with a self
        parameter aka method."""

        assert False

    def cached_view(self, func):
        """Wrapper for a view, i.e. a pure function."""

        assert False
