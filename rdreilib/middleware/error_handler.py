# -*- coding: utf-8 -*-
"""
rdrei.lib.error_handler
~~~~~~~~~~~~~~~~~~~~~~~

Provides advanced error handling as glashammer middleware.

:copyright: 2009, Pascal Hartig <phartig@rdrei.net>
:license: GPL v3, see doc/LICENSE for more details.
"""

from glashammer.utils import emit_event
import logging
import traceback


class ErrorHandler(object):
    """Middleware-like object that utilizes the URL table to map error pages
    to actual views.

    Use :func:`setup_error_handling` instead of using this directly.

    :internal:"""

    def __init__(self, app):
        self.app = app
        self._setup_config()
        self.log = self._get_logger()
        app.connect_event('request-error', self._handle_request_error)
        app.connect_event('request-fatal', self._handle_request_fatal)

    def _setup_config(self):
        """Set up config variables in the application."""
        self.app.add_config_var('error/logging_enabled', bool, True)
        self.app.add_config_var('error/logging_handler', str, 'http_error')
        self.app.add_config_var('error/log_4xx', bool, False)
        self.app.add_config_var('error/log_5xx', bool, True)

    def _get_logger(self):
        """Get a logger based on config. You can customize the logger by the
        name you chose in ``error/logging_handler``."""

        logging_key = self.app.cfg['error/logging_handler']
        return logging.getLogger(logging_key)

    def _find_view_for_code(self, code):
        """Generates an endpoint and tries to find a corresponding view for
        it."""

        endpoint = "error/error_{0}".format(code)
        return self.app.view_finder.find(endpoint)

    def _handle_request_error(self, request, error):
        """Called by the request-error event."""

        self._log_error(request, error)
        view = self._find_view_for_code(error.code)

        if view:
            emit_event('error-match', error, view)
            data = view(request).data

            # FIXME: This way sucks hard!
            error.get_body = lambda environ: data

    def _handle_request_fatal(self, request, error):
        """Called on the request-fatal event, indicating a fatal error occured
        while processing the current view."""

        self._log_fatal(request, error)
        view = self._find_view_for_code(500)

        # In debug mode, we always prefer the original traceback.
        if view and not self.app.cfg['general/debug']:
            emit_event('error-match', error, view)

            error['response'] = view(request)

    def _log_error(self, request, error):
        """Log errors in different ways."""

        if self.app.cfg['error/logging_enabled']:
            if error.code in range(400, 499) and\
               self.app.cfg['error/log_4xx']:

                self.log.warn(self._format_error(request, error))

    def _log_fatal(self, request, error):
        """Log fatal errors."""

        if self.app.cfg['error/logging_enabled'] and\
           self.app.cfg['error/log_5xx']:
            self.log.error(self._format_fatal(request, error))

    def _format_error(self, request, error):
        """Creates a logging-friendly representation of ``error``."""

        # Should be expanded
        return "{name} ({code}) at {path}. Referrer: {referrer}".format(
            name=error.name,
            code=error.code,
            path=request.path,
            referrer=request.referrer)

    def _format_fatal(self, request, error):
        """Creates a logging-friendly representation of a fatal ``error``."""

        return "Error 500 at {path}. Referrer: {referrer}. Details: "\
                "{traceback}".format(
                    path=request.path,
                    referrer=request.referrer,
                    traceback=self._get_traceback(error))

    def _get_traceback(self, error):
        """Returns a formatted traceback for logging purposes."""

        return "\n".join(traceback.format_exception(
            error['type'],
            error['value'],
            error['traceback']))


def setup_error_handler(app):
    """
    Set up display of custom error pages.
    Expects an endpoint like ``error/error_404`` for every error code you'd
    like to handle.

    Does not support correct handling of 500 errors yet.
    Adds a bunch of new configuration variables:

    * error/logging_enabled: Allows you to disable error logging.
    * error/logging_handler: Name of the error handler to log http errors to.
    * error/log_4xx: Log errors like 400, 401, 402 ...
    * error_log_5xx: Log errors like 500, 501, 502 ...
    """

    ErrorHandler(app)
