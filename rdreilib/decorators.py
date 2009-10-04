# -*- coding: utf-8 -*-
"""
 rdrei.lib.decorators
 ~~~~~~~~~~~~~~~~
 Some useful decorators.


 :copyright: 2008 by Pascal Hartig <phartig@rdrei.net>
 :license: BSD, see doc/LICENSE for more details.
"""

from functools import wraps
from werkzeug.exceptions import BadRequest
import logging

import time

from glashammer.utils import log
#log = logging.getLogger("rdrei.lib.decorators")

def timed(func):
    @wraps(func)
    def _wrap(*args, **kwargs):
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            total_time = time.time() - start_time
            log.debug("timed: function call %r in %r took %f seconds." % (func.__name__,
                                                                          func.__module__,
                                                                          total_time))
    return _wrap

def force_method(method):
    def _outer(func):
        @wraps(func)
        def _inner(self, req, *args, **kwargs):
            if req.method != method:
                raise BadRequest("Invalid request method!")
            return func(self, req, *args, **kwargs)
        return _inner
    return _outer

