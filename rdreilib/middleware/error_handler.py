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

    def _handle_request_error(self, request, error):
        """Called by the request-error event."""

        self._log_error(request, error)

        endpoint = "error/error_{0}".format(error.code)
        view = self.app.view_finder.find(endpoint)

        if view:
            emit_event('error-match', error, view)
            data = view(request).data

            # FIXME: This way sucks hard!
            error.get_body = lambda environ: data

    def _log_error(self, request, error):
        """Log errors in different ways."""

        if self.app.cfg['error/logging_enabled']:
            if error.code in range(400, 499) and\
               self.app.cfg['error/log_4xx']:

                self.log.warn(self._format_error(request, error))

            elif error.code in range(500, 599) and\
                 self.app.cfg['error/log_5xx']:

                self.log.error(self._format_error(request, error))

    def _format_error(self, request, error):
        """Creates a logging-friendly representation of ``error``."""

        # Should be expanded
        return "{name} ({code}) at {path}. Referrer: {referrer}".format(
            name=error.name,
            code=error.code,
            path=request.path,
            referrer=request.referrer
        )


def setup_error_handler(app):
    """Set up display of custom error pages."""

    ErrorHandler(app)
