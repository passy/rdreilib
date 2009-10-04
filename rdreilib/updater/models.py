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
from werkzeug.utils import cached_property

from ..database import ModelBase, session
from ..p2lib import P2Mixin

import logging
import datetime
import os


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
    'failure': 20,
    'rollback': 30
}

PACKACKE_PATTERN = "update_%d.r3u"


class VersionLog(ModelBase):
    """Stores information on installed versions and their installation state."""

    __tablename__ = "updater_versionlog"
    __mapper_args = {'polymorphic_identity': 'updater_versionlog'}
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    revision = db.Column(db.Integer, unique=True)
    long_version = db.Column(db.Unicode(15), nullable=True, unique=True)


    def __init__(self, revision, long_version=None, state='pending'):
        self.revision = revision
        self.long_version = long_version
        self.state = state

    def __repr__(self):
        if self.id:
            return u"<VersionLog(%d, revision=%d, 'long_version='%s'"\
                    ")>" % (self.id, self.revision,
                            self.long_version or 'unknown')

        else:
            return u"<VersionLog(unsafed)>"

    @cached_property
    def update(self):
        """Get the last entry of :class:``UpdateLog`` for this version entry."""
        return self.update_log.order_by('-id').limit(1).first()

    def clean_updatelog(self, keep_status=None):
        """Removes all redundant update log entries. Used after a successful
        installtion. The data is kept until than for in-depth debug
        possibilities.

        :param keep_status: A value of UPDATE_STATES that is *not* deleted.
        :return: int, affected rows"""
        keep_status = keep_status or UPDATE_STATES['success']
        result = self.update_log.filter(UpdateLog.state!=keep_status).delete()

        # TODO: Get affected rows. Consider using
        # :class:``sqlalchemy.engine.base.ResultProxy``

    def get_package(self, path):
        """Get the pacakge path for this version if it exists or ``None``.

        :param path: Path to download folder.
        """
        fullpath = os.path.join(path, PACKACKE_PATTERN % self.revision)
        if os.path.exists(fullpath):
            return fullpath


class UpdateLogQuery(orm.Query):
    def get_latest(self):
        """Get the latest successful installed version."""
        entry = self.filter(UpdateLog._state==UPDATE_STATES['success'])\
                .order_by(UpdateLog.id.desc())\
                .first()

        return entry

    def get_current(self, version):
        """Get the most recent log entry for update to :class:``Version``.
        :param: The version upgrading to."""
        entry = self.filter(UpdateLog.version==version)\
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
    version = orm.relation(VersionLog, backref=orm.backref(
            'update_log',
            lazy='dynamic',
        ),
        cascade='all')

    message = db.Column(db.Unicode(140))
    progress = db.Column(db.Integer, default=-1)
    _state = db.Column(db.SmallInteger)

    def __init__(self, version, state, message=None, progress=-1):
        self.version = version
        self.state = state
        self.message = message and message or ''
        self.progress = int(round(progress))
        self.updated = datetime.datetime.now()

    def __repr__(self):
        return u"<UpdateLog(%d, '%s')>" % (self.state, self.message)

    def _get_state(self):
        index = UPDATE_STATES.values().index(self._state)
        return UPDATE_STATES.keys()[index]

    def _set_state(self, value):
        if value in UPDATE_STATES.values():
            self._state = value

        elif value in UPDATE_STATES.keys():
            self._state = UPDATE_STATES[value]

        else:
            raise ValueError("State must be an integer or string specified "
                             "in UPDATE_STATES, not %r!" % value)

    state = orm.synonym('_state', descriptor=property(_get_state,
                                                     _set_state))
