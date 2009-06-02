# -*- coding: utf-8 -*-
"""
 rdrei.database
 ~~~~~~~~~~~~~~~~
 Reusable data structures for database access.


 :copyright: 2008 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL, see doc/LICENSE for more details.
"""

from p2lib import p2_to_int
from glashammer.bundles.sqlalchdb import metadata, session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm

class Query(orm.Query):
    """Default query class."""

    def first(self, raise_if_missing=False):
        """Return the first result of this `Query` or None if the result
        doesn't contain any row.  If `raise_if_missing` is set to `True`
        a `NotFound` exception is raised if no row is found.
        """
        rv = orm.Query.first(self)
        if rv is None and raise_if_missing:
            raise NotFound()
        return rv
    
    def getp2(self, p2id):
        """Returns the row where the pk has the given p2id."""
        try:
            return orm.Query.get(self, p2_to_int(p2id))
        except ValueError:
            return None

from werkzeug.exceptions import NotFound

class _ModelBase(object):
    query = session.query_property(Query)

ModelBase = declarative_base(metadata=metadata, cls=_ModelBase)

