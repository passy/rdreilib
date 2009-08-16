# -*- coding: utf-8 -*-
"""
rdreilib.updater.models
~~~~~~~~~~~~~~~~~~~~~~~
Persistance layer for R3U

:copyright: 2009, Pascal Hartig <phartig@rdrei.net>
:license: GPL v3, see doc/LICENSE for more details.
"""

from ..database import ModelBase
from ..p2lib import P2Mixin

import logging


log = logging.getLogger("rdreilib.updater.models")


class VersionLog(ModelBase):
    """Stores information on installed versions and their installation state."""

    __tablename__ = "updater_versionlog"


class UpdateLog(ModelBase):
    """Contains live data about current updating progress."""

    __tablename__ "updater_updatelog"

