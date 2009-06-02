# -*- coding: utf-8 -*-
"""
 rdreilib.jsonlib
 ~~~~~~~~~~~~~~~~
 Provides basic functions and decorators to work with JSON.


 :copyright: 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL, see doc/LICENSE for more details.
"""

from glashammer.utils.json import JsonResponse
from glashammer.bundles.i18n import _TranslationProxy
from werkzeug.wrappers import Response
from simplejson import dumps as dump_json, JSONEncoder
from functools import wraps
import traceback, logging

log = logging.getLogger("json")

class JSONException(Exception):
    pass

class LazyEncoder(JSONEncoder):
    """Provides a simple wrapper for lazy gettext strings that aren't
    json-able with the default encoder."""
    
    def default(self, o):
        if isinstance(o, _TranslationProxy):
            return unicode(o)
        elif hasattr(o, '__json__'):
            return o.__json__()
        else:
            super(LazyEncoder, self).default(o)

class JsonResponse(Response):
    default_mimetype = 'text/javascript'

    def __init__(self, data, *args, **kw):
        #default = kw.get("json_encoder", None)
        #if default:
        #    del kw['json_encoder']
        Response.__init__(self, dump_json(data, cls=LazyEncoder), *args, **kw)

def json_view(f, encoder=None):
    """
    Decorator to jsonify responses
    """
    @wraps(f)
    def _wrapped(*args, **kw):
        try:
            res = f(*args, **kw)
        except Exception, err:
            log.error("View error: %s" % traceback.format_exc())
            return JsonResponse({'error': repr(err)})
        if callable(res):
            return res
        else:
            return JsonResponse(res)
    return _wrapped

