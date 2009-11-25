# -*- coding: utf-8 -*-
"""
    rdreilib.api
    ~~~~~~~~~~~~

    Provides basic helpers for the API.

    :copyright: (c) 2009 by Plurk Inc., Pascal Hartig <phartig@rdrei.net>
    :license: BSD, see LICENSE for more details.
"""
import re
import os
import inspect
import logging
import simplejson
import suds.client
from xml.sax.saxutils import quoteattr
from suds import WebFault
from urllib2 import URLError
from functools import update_wrapper
from babel import Locale, UnknownLocaleError
from werkzeug.exceptions import MethodNotAllowed, BadRequest
from werkzeug import Response, escape, Request

from glashammer.utils.local import get_app
from glashammer.utils.wrappers import render_template
from glashammer.utils.lazystring import make_lazy_string

from glashammer.bundles.i18n2 import _, has_section
from .remoting import remote_export_primitive
from .formatting import format_creole
from .decorators import on_method


# If this is included too early, eager loading raises a KeyError.
XML_NS = make_lazy_string(lambda: get_app().cfg['api/xml_ns'])


_escaped_newline_re = re.compile(r'(?:(?:\\r)?\\n)')
log = logging.getLogger('rdreilib.api')


def debug_dump(obj):
    """Dumps the data into a HTML page for debugging."""
    dump = _escaped_newline_re.sub('\n',
        simplejson.dumps(obj, ensure_ascii=False, indent=2))
    return render_template('api/debug_dump.html', dump=dump)


def dump_xml(obj):
    """Dumps data into a simple XML format."""
    def _dump(obj):
        if isinstance(obj, dict):
            d = dict(obj)
            obj_type = d.pop('#type', None)
            key = start = 'dict'
            if obj_type is not None:
                if obj_type.startswith('solace.'):
                    key = start = obj_type[7:]
                else:
                    start += ' type=%s' % quoteattr(obj_type)
            return u'<%s>%s</%s>' % (
                start,
                u''.join((u'<%s>%s</%s>' % (key, _dump(value), key)
                         for key, value in d.iteritems())),
                key
            )
        if isinstance(obj, (tuple, list)):
            def _item_dump(obj):
                if not isinstance(obj, (tuple, list, dict)):
                    return u'<item>%s</item>' % _dump(obj)
                return _dump(obj)
            return u'<list>%s</list>' % (u''.join(map(_item_dump, obj)))
        if isinstance(obj, bool):
            return obj and u'yes' or u'no'
        return escape(unicode(obj))
    return (
        u'<?xml version="1.0" encoding="utf-8"?>'
        u'<result xmlns="%s">%s</result>'
    ) % (XML_NS, _dump(obj))


def get_serializer(request):
    """Returns the serializer for the given API request."""
    format = request.args.get('format')
    if format is not None:
        rv = _serializer_map.get(format)
        if rv is None:
            raise BadRequest(_(u'Unknown format "%s"') % escape(format))
        return rv

    # webkit sends useless accept headers. They accept XML over
    # HTML or have no preference at all. We spotted them, so they
    # are obviously not regular API users, just ignore the accept
    # header and return the debug serializer.
    if request.user_agent.browser in ('chrome', 'safari'):
        return _serializer_map['debug']

    best_match = (None, 0)
    for mimetype, serializer in _serializer_for_mimetypes.iteritems():
        quality = request.accept_mimetypes[mimetype]
        if quality > best_match[1]:
            best_match = (serializer, quality)

    if best_match[0] is None:
        raise BadRequest(_(u'Could not detect format.  You have to specify '
                           u'the format as query argument or in the accept '
                           u'HTTP header.'))

    # special case.  If the best match is not html and the quality of
    # text/html is the same as the best match, we prefer HTML.
    if best_match[0] != 'text/html' and \
       best_match[1] == request.accept_mimetypes['text/html']:
        return _serializer_map['debug']

    return _serializer_map[best_match[0]]


def prepare_api_request(request):
    """Prepares the request for API usage."""
    request.in_api = True
    lang = request.args.get('lang')
    if lang is not None:
        if not has_section(lang):
            raise BadRequest(_(u'Unknown language'))
        request.locale = lang

    locale = request.args.get('locale')
    if locale is not None:
        try:
            locale = Locale.parse(locale)
            if not has_locale(locale):
                raise UnknownLocaleError()
        except UnknownLocaleError:
            raise BadRquest(_(u'Unknown locale'))
        request.view_lang = locale


def send_api_response(request, result):
    """Sends the API response."""
    status = 200
    if type(result) is dict and 'error' in result:
        status = 500

    ro = remote_export_primitive(result)
    serializer, mimetype = get_serializer(request)
    return Response(serializer(ro), mimetype=mimetype, status=status)


def api_method(methods=('GET',)):
    """Helper decorator for API methods."""
    def decorator(f):
        def wrapper(self, *args, **kwargs):
            # Check whether self is an request object or the bound instance
            if isinstance(self, Request):
                request = self
            else:
                request = args[0]

            if request.method not in methods:
                raise MethodNotAllowed(methods)
            prepare_api_request(request)
            rv = f(self, *args, **kwargs)
            return send_api_response(request, rv)
        f.is_api_method = True
        f.valid_methods = tuple(methods)
        return update_wrapper(wrapper, f)
    return decorator

def soap_api_method(methods=('GET',)):
    """Helper decorator for SOAP API methods that use suds. Tries to prepare
    results and catches WebFaults. Also invokes the :func:``api_method``
    decorator."""
    def decorator(f):
        @api_method(methods)
        def wrapper(request, *args, **kwargs):
            try:
                result = f(request, *args, **kwargs)
            except (WebFault,URLError) as exc:
                # TODO: Look out how other REST services handle errors!
                log.error('SOAP request failed: %r' % exc)
                return {'error': str(exc)}

            return result

        return update_wrapper(wrapper, f)
    return decorator

def list_api_methods():
    """List all API methods."""
    result = []
    application = get_app()
    for rule in application.map.iter_rules():
        if rule.build_only:
            continue
        view = application.find_view(rule.endpoint)
        if not getattr(view, 'is_api_method', False):
            continue
        handler = view.__name__
        if handler.startswith('api_'):
            handler = handler[4:]
        result.append(dict(
            handler=handler,
            valid_methods=view.valid_methods,
            doc=format_creole((inspect.getdoc(view) or '').decode('utf-8')),
            url=unicode(rule)
        ))
    result.sort(key=lambda x: (x['url'], x['handler']))
    return result

def SOAPActionFactory(client, service, options=None):
    """Creates a single action for a SOAP-enabled controller for an action taken
    from a subs-WSDL object.

    :param options: Dictionary with options::
        extra_kwargs: Add additional kwargs to every extracted method.
        methods: tuple of allowed HTTP methods. Defaults to ('GET',)

    :return: function or None"""

    options = options or {}

    func = getattr(client.service, service)
    methods = options.get('methods', ('GET',))

    def _method(self, request, *args, **kwargs):
        """Closure for SOAPActionFactory-generated methods."""
        kwargs.update(options.get('extra_kwargs', {}))
        return func(*args, **kwargs)

    # on_method makes the api_method decorator work for 'methods'
    _method = soap_api_method(methods)(_method)

    # Suds does not set a value by itself.
    _method.__name__ = str(service)
    # Provides undecorated access to the function
    _method._func = func

    return _method

def SOAPControllerFactory(wsdl, map=None):
    """Creates a Mixin including all methods specified in the WSDL supplied.
    They are valid api methods that can be overridden.

    :param wsdl: path to wsdl file.
    :param map: dictionary with method name as key and options to be passed to
    SOAPActionFactory. Key _all matches all methods.
    :return: class that can either be used as mixin or standalone base.
    """

    map = map or {}
    client = suds.client.Client(wsdl, cache=None)

    class _ControllerMixin(object):
        pass

    method_list = []
    # This seems quite intensive, but most times there's only one element
    # per loop.
    for definition in client.sd:
        for port in definition.service.ports:
            for method in port.methods.iterkeys():
                method_list.append(method)

                # Find global options and update with method specific
                options = map.get('_all', {})
                options.update(map.get(method, {}))
                func = SOAPActionFactory(client, method, options)
                setattr(_ControllerMixin, method, func)

    # Make the list available as protected attribute
    _ControllerMixin._soap_methods = method_list
    _ControllerMixin._wsdl_path = wsdl

    return _ControllerMixin



_serializer_for_mimetypes = {
    'application/json':     'json',
    'application/xml':      'xml',
    'text/xml':             'xml',
    'text/html':            'debug',
}
_serializer_map = {
    'json':     (simplejson.dumps, 'application/json'),
    'xml':      (dump_xml, 'application/xml'),
    'debug':    (debug_dump, 'text/html')
}

def setup_api(app):
    """Glashammer setup. Use this if you want to use this module."""
    app.add_config_var('api/xml_ns', str, 'http://rdrei.net/api')
    app.add_template_searchpath(os.path.join(
        os.path.dirname(__file__),
        'templates/'
    ))
