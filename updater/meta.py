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
import os

from package import Package, PackageCreator

from os.path import join, dirname
from tempfile import NamedTemporaryFile

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

    signature = None

    def __init__(self, filename, gnupghome=None):
        config_content = open(filename, 'r').read()
        self.data = yaml.load(config_content)
        self.basedir = dirname(filename)
        if not self.data:
            raise MetaConfigError("Loading config file %r failed!" % filename)
        self.gpg = gnupg.GPG(gnupghome=gnupghome, verbose=True)

    def check(self):
        """Checks for required data in config, but only on two dimensions."""
        # Iterate through all required fields and check if they are present.
        for field in self.REQUIRED_FIELDS:
            key1, key2 = field.split('.')
            try:
                self.data[key1][key2]
            except KeyError:
                raise MetaConfigError("Required field '%s' missing!" % field)
        self._verify_hash()
        self._verify_signature()

    def _get_package(self):
        """Returns a read-only file objects of the referenced package."""

        return open(self.data['package']['filename'], 'r')

    def _verify_hash(self):
        """Verifies meta integrity by its hash."""
        exp = self._build_hash()
        got = self.data['meta']['hash']

        if got != exp:
            raise MetaIntegrityError("Meta SHA-1 check failed! "
                                     "Excpected %r, got %r." %
                                     (exp, got))

    def _verify_signature(self):
        """Verfifies meta integrity by its signature.
        Sets self.signature on success containing additional info."""
        # Creates a temporary file for the meta data

        filename = None
        with NamedTemporaryFile(delete=False) as tmpfile:
            tmpfile.write(self._build_meta_string())
            filename = tmpfile.name

        assert filename is not None, 'Creating temporary file failed!'

        try:
            verify = self.gpg.verify_detached(
                tmpfile.name,
                self.data['meta']['signature'],
                _nodelete=True
            )
        finally:
            pass
            #os.unlink(tmpfile.name)

        if not verify.valid:
            raise MetaIntegrityError("Meta signature is invalid!")
        if verify.fingerprint != self.data['meta']['fingerprint']:
            raise MetaIntegrityError("Meta signature is invalid! "
                                     "Expected %r, got $r." %
                                     (self.data['meta']['fingerprint'],
                                      verify.fingerprint))

        self.signature = verify

    def _build_meta_string(self):
        """Returns string of all hashable attributes of meta file."""

        hdata = copy.deepcopy(self.data)
        # Deleting data not used to build hash.
        del(hdata['meta']['hash'])
        del(hdata['meta']['signature'])

        return str(hdata)

    def _build_hash(self):
        """Builds the hash to verify meta signature."""

        hdata = self._build_meta_string()
        return hashlib.sha1(hdata).hexdigest()

class MetaCreator(Meta):
    """Helper class for creation of meta config files."""

    def __init__(self, filename, gnupghome=None):
        super(MetaCreator, self).__init__(filename, gnupghome)
        self.file = open(filename, 'rw')
        self.package = PackageCreator(self)

    def make_signatures(self):
        """Creates package signature, package hash, meta signature and meta
        hash."""
        data = {
            'meta': {
                'hash': self._build_hash(),
                'signature': self._strip_signature(self._sign_meta()),
            }, 'package': {
                'hash': self.package.build_hash(),
                'signature': self._strip_signature(self.package.sign_package()),
            }
        }

        return data

    def _sign_meta(self, keyid=None):
        """Signs the meta data with GnuPG.
        :param keyid str Overrides default GnuPG key.

        :return string
        """

        hdata = self._build_meta_string()
        return self.gpg.sign(hdata, detached=True, clearsign=False)

    def _strip_signature(self, signature):
        """Strips header and footer off GPG signature"""
        # This is very, very basic and only works for
        # standard header/footer combinations.
        str_sig = str(signature).split('\n')
        return '\n'.join(str_sig[3:-2])

class MetaConfigError(Exception):
    pass

class MetaIntegrityError(Exception):
    pass
