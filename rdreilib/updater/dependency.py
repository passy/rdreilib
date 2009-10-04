# -*- coding: utf-8 -*-
"""
updater.dependency
~~~~~~~~~~~~~~~~~~
Basic dependencies for update packages.

:copyright: 2009, Pascal Hartig <phartig@rdrei.net>
:license: GPL v3, see doc/LICENSE for more details.
"""

class Dependency(object):
    """Base class for package dependencies."""

    def __init__(self, requirement):
        """Accepts a string for the requirement, parsed by the subclasses."""
        self.requirement = requirement

    def check(self):
        """Checks whether the dependency is fulfilled or not.

        :return: boolean
        """

        raise NotImplementedError()

    @staticmethod
    def get_instance(key, value):
        """Creates a new dependency for the given key (like 'package') and the
        value (e.g. the requirement)."""
        if key == 'application':
            return ApplicationDependency(value)
        elif key == 'package':
            return PackageDenpendency(value)
        else:
            raise TypeError("Unsupported dependency type %r." % key)


class PackageDenpendency(Dependency):
    """A dependency requiring a python package with a specific version to be
    installed."""

    def check(self):
        """Check via pkg_resources, if the required package is installed."""
        from pkg_resources import require, DistributionNotFound

        try:
            require(self.requirement)
        except DistributionNotFound:
            return False

        return True

class ApplicationDependency(Dependency):
    """Specified a specific requirement on the application. Currently only
    comparisions to its current revision are implemented."""

    def check(self):
        if self.requirement.startswith("revision"):
            return self.check_revision()
        else:
            raise NotImplementedError("Only revision checks are implemented "
                                      "yet.")

    def check_revision(self):
        from .models import UpdateLog
        current = UpdateLog.query.get_latest().version.revision

        # Get the part after revision
        bits = self.requirement.split("revision")[1:][0]

        # Mini-lexing
        comparison, revision = '', ''

        for char in bits:
            if char in ('>', '<', '=', '!'):
                comparison += char
            else:
                revision += char

        try:
            revision = int(revision, 10)
        except ValueError:
            raise ValueError("ApplicationDependency is not well-formed: %r" %
                             self.requirement)

        if comparison == "==":
            return current == revision
        elif comparison == ">":
            return current > revision
        elif comparison == "<":
            return current < revision
        elif comparison == ">=":
            return current >= revision
        elif comparison == "<=":
            return current <= revision
        elif comparison == "!=":
            return current != revision
        else:
            raise ValueError("Unsupported comparison operator: %r" % comparison)

