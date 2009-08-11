# -*- coding: utf-8 -*-
"""
 rdreilib.updater.meta
 ~~~~~~~~~~~~~~~~
 Meta data loader and processor


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
 """
import yaml
import hashlib
import copy

class Meta(object):
    REQUIRED_FIELDS = (
        'version.revision',
        'meta.email',
        'meta.fingerprint',
        'meta.hash',
        'meta.signature',
        'package.hash',
        'package.type',
        'package.signature',
        'package.filename',
    )

    def __init__(self, filename):
        config_content = open(filename, 'r').read()
        self.data = yaml.load(config_content)
        self.check()
        self._verify_hash()

    def check(self):
        """Checks for required data in config, but only on two dimensions."""
        for field in self.REQUIRED_FIELDS:
            key1, key2 = field.split('.')
            try:
                self.data[key1][key2]
            except KeyError:
                raise MetaConfigError("Required field '%s' missing!" % field)

    def _verify_hash(self):
        """Verifies meta integrity by its hash."""
        exp = self._build_validation_hash()
        got = self.data['meta']['hash']

        if got != exp:
            raise MetaIntegrityError("Meta verification hash failed! "
                                     "Excpected %r, got %r." %
                                     (exp, got))

    def _build_validation_hash(self):
        """Builds the hash to verify meta signature."""

        hdata = copy.deepcopy(self.data)
        # Deleting data not used to build hash.
        del(hdata['meta']['hash'])
        del(hdata['meta']['signature'])

        return hashlib.sha1(str(hdata)).hexdigest()

class MetaConfigError(Exception):
    pass

class MetaIntegrityError(Exception):
    pass
