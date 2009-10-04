# -*- coding: utf-8 -*-
"""
 rdreilib.updater.r3upackage
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~
 A meta zip-package containing the config and the data package.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
 """

from meta import Meta

from zipfile import ZipFile, BadZipfile

class R3UPackage(object):
    def __init__(self, filename):
        try:
            self.arc = ZipFile(filename, 'r')
            # Could raise exception
            mdata = self.arc.read("meta.yaml")
        except BadZipfile, IOError:
            raise InvalidR3UError("%r is not a valid R3U package!" % filename)

        self.meta = Meta(content=mdata)

    def check(self, signature=True):
        """Basic check if meta file is valid.
        :param signature: Boolean whether to make a signature check or not.
        :return: True. Raises exceptions on failure.
        """

        self.meta.check(signature=signature)
        self._check_package()
        return True

    def _check_package(self):
        """Basic check if referenced package is available."""

        fname = self.meta.data['package']['filename']
        try:
            self.arc.getinfo(fname)
        except KeyError:
            raise InvalidR3UError("Referenced data package %r not in R3U!" %
                                  fname)

class InvalidR3UError(Exception):
    pass

