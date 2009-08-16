# -*- coding: utf-8 -*-
"""
rdreilib.updater.models
~~~~~~~~~~~~~~~~~~~~~~~
Persistance layer for R3U

:copyright: 2009, Pascal Hartig <phartig@rdrei.net>
:license: GPL v3, see doc/LICENSE for more details.
"""

import sqlalchemy as db
from sqlalchemy import orm

from ..database import ModelBase, session
from ..p2lib import P2Mixin

import logging
import datetime


log = logging.getLogger("rdreilib.updater.models")
# This represents the different states an update can have. Having the 10,
# however, being the success state, feels a bit weird.
UPDATE_STATES = {
    'pending': 0,
    'download': 1,
    'verify': 2,
    'unpack': 3,
    'backup': 4,
    'patch': 5,
    'success': 10,
    'failure': 20
}

class VersionLog(ModelBase):
    """Stores information on installed versions and their installation state."""

    __tablename__ = "updater_versionlog"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    revision = db.Column(db.Integer, unique=True)
    long_version = db.Column(db.Unicode(15), unique=True)


    def __init__(self, revision, long_version):
        self.revision = revision
        self.long_version = long_version

    def __repr__(self):
        if self.id:
            return u"<VersionLog(%d, revision=%d, 'long_version='%s'"\
                    ")>" (self.id, self.revision, self.long_version)

        else:
            return u"<VersionLog(unsafed)>"

class UpdateLogQuery(orm.Query):
    def get_latest(self):
        """Get the latest successful installed version."""
        entry = self.filter(UpdateLog._state==UPDATE_STATES['success'])\
                .order_by(UpdateLog.updated.desc())\
                .first()

        return entry

class UpdateLog(ModelBase):
    """Contains live data about current updating progress."""

    query = session.query_property(UpdateLogQuery)

    __tablename__ = "updater_updatelog"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey('updater_versionlog.id',
                                                     ondelete="CASCADE"))
    updated = db.Column(db.DateTime)
    version = orm.relation(VersionLog, backref='update_log')

    _state = db.Column(db.SmallInteger)
    message = db.Column(db.Unicode(140))

    def _get_state(self):
        return self._state

    def _set_state(self, value):
        if value in UPDATE_STATES.values():
            self._state = value

        elif value in UPDATE_STATES.keys():
            self._state = UPDATE_STATES[value]

        else:
            raise ValueError("State must be an integer or string specified "
                             " in UPDATE_STATES!")

    state = orm.synonym('state', descriptor=property(_get_state,
                                                     _set_state))

    def __init__(self, version, state, message=None):
        self.version = version
        self.state = state
        self.message = message and message or ''
        self.updated = datetime.datetime.now()

    def __repr__(self):
        return u"<UpdateLog(%d, '%s')>" % (self.state, self.message)


