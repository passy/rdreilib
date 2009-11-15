# -*- coding: utf-8 -*-
"""
 rdreilib.controller
 ~~~~~~~~~~~~~~~~
 BaseController to use for your application.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: BSD, see doc/LICENSE for more details.
 """

from glashammer.utils.wrappers import render_response
from glashammer.utils.local import get_request
from glashammer.bundles.sessions import get_session
from eauth.template import TemplateUser

class BaseController(object):
    """Base class for controllers"""
    helpers = {}

    @property
    def session(self):
        """Get current glashammer/securecookie session"""
        # TODO: This has to be refactored! This is in Request, too!
        req = get_request()
        if 'beaker.session' in req.environ:
            return req.environ['beaker.session']
        else:
            return get_session()

    @classmethod
    def register(cls, app):
        "Registers the loaded subclass controllers in the WSGI application."
        for subcls in cls.__subclasses__():
            # Ignores subclasses that don't contain a endpoint definition
            if hasattr(subcls, 'endpoint'):
                app.add_views_controller(subcls.endpoint, subcls())

    def render(self, template, *args, **kwargs):
        """Shortcut for render_to_response.
        @param kwargs dict: May contain an element _path to override path
        building."""

        if '_path' in kwargs:
            template = "%s/%s" % (kwargs.pop('_path'), template)
        else:
            template = "%s/%s" % (self.endpoint, template)

        kwargs.update(user=TemplateUser())
        kwargs.update(helpers=self.helpers)
        kwargs.update(flash=self._get_flash())
        kwargs.update(session=self.session)

        return render_response(template, *args, **kwargs)

    def register_helper(self, func, funcname):
        """Register a new helper method. Can be called with
        {{ helpers.funcname() }}
        in template.
        """
        self.helpers[funcname] = func

    def set_flash(self, level, message, instant=False):
        """Sets a flash that is displayed in the next view."""
        key = instant and 'flash' or '_flash'
        self.session[key] = {'message': message,
                             'level': level,
                             'id': id(self)}

    def _get_flash(self):
        "Get the last flash and push current to session."
        # Show flash and flush
        flash = self.session.get('flash', {})
        self.session['flash'] = {}

        # Update 'cached' flash for next view
        if '_flash' in self.session:
            self.session['flash'] = self.session['_flash']
            del(self.session['_flash'])

        return flash

