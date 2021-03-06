# -*- coding: utf-8 -*-
"""
 rdreilib.jsonlib
 ~~~~~~~~~~~~~~~~
 Provides basic functions and decorators to work with JSON.


 :copyright: 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: BSD, see doc/LICENSE for more details.
"""

from glashammer.utils.json import JsonResponse
from glashammer.utils.local import get_app
from glashammer.bundles.i18n import LazyString
from glashammer.utils.lazystring import LazyString
from werkzeug.wrappers import Response
from werkzeug.exceptions import HTTPException
from simplejson import dumps as dump_json, JSONEncoder
from functools import wraps
import traceback, logging

log = logging.getLogger("json")

class JSONException(HTTPException):
    code = 500
    description = "A server side error occured."

    def get_headers(self, environ):
        """Get a list of headers"""
        return [('Content-Type', 'application/json')]

    def get_body(self, environ):
        """Get the body."""

        return dump_json({'error': self.get_description(environ)})

    def __repr__(self):
        return self.description

class LazyEncoder(JSONEncoder):
    """Provides a simple wrapper for lazy gettext strings that aren't
    json-able with the default encoder."""

    def default(self, o):
        if isinstance(o, _LazyString):
            return unicode(o)
        elif hasattr(o, '__json__'):
            return o.__json__()
        else:
            super(LazyEncoder, self).default(o)

class JsonResponse(Response):
    default_mimetype = 'application/json'

    def __init__(self, data, *args, **kw):
        #default = kw.get("json_encoder", None)
        #if default:
        #    del kw['json_encoder']
        Response.__init__(self, dump_json(data, cls=LazyEncoder), *args, **kw)

def json_view(f, encoder=None):
    """
    Decorator to jsonify responses. Catches exceptions and wraps them into a
    JsonResponse. Decides whether to set the status code to 500 or 200 depending
    on current debug settings.
    """
    @wraps(f)
    def _wrapped(*args, **kw):
        try:
            res = f(*args, **kw)
        except HTTPException, err:
            log.error("View error: %s" % traceback.format_exc())
            resp = JsonResponse({'error': repr(err), 'description':
                                 err.description})
            resp.status_code = err.code
            return resp
        if callable(res):
            return res
        else:
            return JsonResponse(res)
    return _wrapped

