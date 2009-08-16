# -*- coding: utf-8 -*-
"""
rdreilib.updater.config
~~~~~~~~~~~~~~~~~~~~~~~
Configuration module.

:copyright: 2009, Pascal Hartig <phartig@rdrei.net>
:license: GPL v3, see doc/LICENSE for more details.
"""

from glashammer.utils.config import Configuration
from glashammer.utils.local import local

from version import __version__
import logging
import os


log = logging.getLogger('rdreilib.updater.config')

class UpdaterConfig(Configuration):
    """Config storage for the updater."""
    def __init__(self, filename):
        super(UpdaterConfig, self).__init__(filename)
        self._setup_vars()

    def _setup_vars(self):
        """Sets up some config variables to use in R3U."""

        config = dict()

        # Base path to app to update
        config['general/path'] = (str, '')

        # Application name
        config['general/appname'] = (str, 'r3updater')
        config['general/version'] = (int, __version__)

        # Host settings
        config['server/host'] = (str, str())
        config['server/port'] = (int, 80)
        config['server/path'] = (str, str())

        config['server/username'] = (str, str())
        config['server/password'] = (str, str())

        self.config_vars.update(config)


def get_config(filename):
    """Gets a configuration object from local storage or creates a new one on
    the fly."""
    if not hasattr(local, 'updater_config'):
        log.debug("Setting up UpdaterConfig")
        local.updater_config = UpdaterConfig(filename)
        if not os.path.exists(filename):
            # Forces to rewrite
            local.updater_config.change_single('general/version', __version__)

    return local.updater_config

