# -*- coding: utf-8 -*-
"""
rdreilib.permissions
~~~~~~~~~~~~~~~~~~~~

Provides a PermissionLoader class that can be used to ease permission creation
in your application across multiple modules or independent controllers.

:copyright: 2009, Pascal Hartig <phartig@rdrei.net>
:license: BSD
"""

from rdreilib.eauth.models import Group, Permission
from rdreilib.decorators import timed
from glashammer.bundles.database import session
import logging

log = logging.getLogger('rdreilib.permission_loader')


class PermissionLoader(object):
    """Used by the database initialization script to load permissions and
    groups initially into the database. Provides an infrastructure
    modules can hook into to provide custom permissions."""

    # Contains a {'group': ['permission1', 'permissions2']} structure
    permissions = {}

    _group_cache = {}
    _permission_cache = {}

    def __init__(self):
        """Creates the group entries."""

        self.add_group('admins')
        self.add_group('users')

    @timed
    def create(self):
        """Creates the entries in the database."""

        _permission_cache = {}
        log.info("Starting permission creation.")

        self._create_missing_groups()
        self._create_missing_permissions()

        for group_name, permissions in self.permissions.iteritems():
            group = self._group_cache[group_name]

            for permission_name in permissions:
                permission = _permission_cache.get(permission_name)

                if permission not in group.permissions:
                    group.permissions.append(permission)

        session.commit()
        log.info("Successfully created permissions.")

    def add(self, group_name, permission_name):
        """Adds a new permission if the permission does not exist yet. Use
        :func:`create` to commit to database."""

        self.permissions[group_name].append(permission_name)

    def add_group(self, group_name):
        """Adds a new group if it does not exist yet. Use :func:`create` to
        commit to database."""

        if group_name not in self.permissions:
            self.permissions[group_name] = []

    def _get_existing_groups(self):
        """Get a list of groups already present in the database."""

        # Saving queries is not important because this is run only directly
        # before deployment.

        group_names = (group_name.decode('utf-8') for group_name in
                       self.permissions.keys())
        return Group.query.filter(Group.group_name.in_(group_names)).all()

    def _get_permission_names(self):
        """Gets a flat list/set of all permission names used in
        self.permissions."""

        permission_names = set()

        for permissions in self.permissions.values():
            permission_names.update(permissions)

        return permission_names

    def _get_existing_permissions(self):
        """Get permissions already present in the database."""

        permission_names = (permission_name.decode('utf-8') for permission_name in
                            self._get_permission_names())

        return Permission.query.filter(
            Permission.permission_name.in_(permission_names)).all()

    def _create_missing_groups(self):
        """Create groups not created yet."""

        for group_name in self._get_missing_groups():
            group = Group(group_name.decode('utf-8'))
            self._group_cache[group_name] = group
            session.add(group)

    def _get_missing_groups(self):
        """Get groups not available in the database."""

        self._group_cache = dict((group.group_name, group) for group in
                                 self._get_existing_groups())
        missing = []

        for group_name in self.permissions:
            if group_name not in self._group_cache:
                missing.append(group_name)

        return missing

    def _create_missing_permissions(self):
        """Create permissions not created yet."""

        for permission_name in self._get_missing_permissions():
            perm = Permission(permission_name.decode('utf-8'))
            self._permission_cache[permission_name] = perm
            session.add(perm)

    def _get_missing_permissions(self):
        """Get permissions not yet comitted to the database."""

        self._permission_cache = dict((permission.permission_name, permission) for
                                  permission in
                                  self._get_existing_permissions())
        missing = []

        for permission_name in self._get_permission_names():
            if permission_name not in self._permission_cache:
                missing.append(permission_name)

        return missing


def setup_permission_loader(app):
    """Creates a ``permissions`` object accessible via the application
    object."""

    setattr(app, 'permissions', PermissionLoader())
