# -*- coding: utf-8 -*-
"""
 rdreilib.updater.meta
 ~~~~~~~~~~~~~~~~
 Meta data loader and processor


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
 """

from thirdparty import gnupg

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

    def __init__(self, filename, gnupghome=None):
        config_content = open(filename, 'r').read()
        self.data = yaml.load(config_content)
        if not self.data:
            raise MetaConfigError("Loading config file %r failed!" % filename)
        self.check()
        self._verify_hash()
        self.gpg = gnupg.GPG(gnupghome=gnupghome)

    def check(self):
        """Checks for required data in config, but only on two dimensions."""
        for field in self.REQUIRED_FIELDS:
            key1, key2 = field.split('.')
            try:
                self.data[key1][key2]
            except KeyError:
                raise MetaConfigError("Required field '%s' missing!" % field)

    def _get_package(self):
        """Returns a read-only file objects of the referenced package."""

        return open(self.data['package']['filename'], 'r')

    def _verify_hash(self):
        """Verifies meta integrity by its hash."""
        exp = self._build_validation_hash()
        got = self.data['meta']['hash']

        if got != exp:
            raise MetaIntegrityError("Meta verification hash failed! "
                                     "Excpected %r, got %r." %
                                     (exp, got))

    def _build_meta_string(self):
        """Returns string of all hashable attributes of meta file."""

        hdata = copy.deepcopy(self.data)
        # Deleting data not used to build hash.
        del(hdata['meta']['hash'])
        del(hdata['meta']['signature'])

        return str(hdata)

    def _build_validation_hash(self):
        """Builds the hash to verify meta signature."""

        hdata = self._build_meta_string()
        return hashlib.sha1(hdata).hexdigest()

class MetaCreator(Meta):
    """Helper class for creation of meta config files."""

    def __init__(self, filename, gnupghome=None):
        super(MetaCreator, self).__init__(filename, gnupghome)
        self.file = open(filename, 'rw')

    def make_signatures(self):
        """Creates package signature, package hash, meta signature and meta
        hash."""
        data = {
            'meta': {
                'hash': self._build_validation_hash(),
                'signature': self._sign_meta(),
            }, 'package': {}
        }

        return data

    def _sign_meta(self, keyid=None):
        """Signs the meta data with GnuPG.
        :param keyid str Overrides default GnuPG key.

        :return string
        """

        hdata = self._build_validation_hash()
        return self.gpg.sign(hdata, detached=True)


class MetaConfigError(Exception):
    pass

class MetaIntegrityError(Exception):
    pass
