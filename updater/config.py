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

import logging
import os


log = logging.getLogger('rdreilib.updater.config')

class UpdaterConfig(Configuration):
    """Config storage for the updater."""
    def __init__(self, filename):
        super(UpdaterConfig, self).__init__(filename)

    def _setup_vars(self):
        """Sets up some config variables to use in R3U."""

        # Base path to app to update
        self.config_vars['updater/path'] = (str, '')

        # Application name
        self.config_vars['updater/appname'] = str(str, 'r3updater')


def setup_config(filename):
    if not hasattr(local, 'updater_config'):
        log.debug("Setting up UpdaterConfig")
        local.updater_config = UpdaterConfig(filename)
        if not os.path.exists(filename):
            log.debug("Creating config file %r" % filename)
            local.updater_config.touch()

