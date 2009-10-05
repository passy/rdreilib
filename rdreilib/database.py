# -*- coding: utf-8 -*-
"""
 rdrei.database
 ~~~~~~~~~~~~~~~~
 Reusable data structures for database access.


 :copyright: 2008 by Pascal Hartig <phartig@rdrei.net>
 :license: BSD, see doc/LICENSE for more details.
"""

from p2lib import p2_to_int
from glashammer.bundles.database import metadata, session, Query as _Query
from glashammer.bundles.database import MetaModel, ModelBaseMeta
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.exceptions import NotFound
from sqlalchemy import orm

class Query(_Query):
    """Enhanced default query class."""

    def getp2(self, p2id):
        """Returns the row where the pk has the given p2id."""
        try:
            return orm.Query.get(self, p2_to_int(p2id))
        except ValueError:
            return None


class _ModelBase(MetaModel):
    query = session.query_property(Query)

ModelBase = declarative_base(metadata=metadata, cls=_ModelBase,
                             metaclass=ModelBaseMeta)

