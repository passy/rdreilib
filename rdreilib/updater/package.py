# -*- coding: utf-8 -*-
"""
 rdreilib.updater.package
 ~~~~~~~~~~~~~~~~~~~~~~~~
 Represents an update package.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
"""

import hashlib
from os.path import join

class Package(object):
    signature = None

    def __init__(self, meta):
        self.meta = meta
        self.filename = self.meta.data['package']['filename']

    def check(self):
        """Checks for package integrity and authentity."""
        self._verify_hash()
        self._verify_signature()

    def build_hash(self, _blocksize=128):
        """Builds a sha-1 hex digest for the package file referenced in the meta
        config"""
        with open(join(self.meta.basedir, self.filename), 'r') as file:
            hash = hashlib.sha1()
            while True:
                content = file.read(_blocksize)
                if content == '':
                    # EOF
                    break

                hash.update(content)

        return hash.hexdigest()

    def _verify_hash(self, _blocksize=128):
        """Verifies hash specified in meta config"""

        expected = self.build_hash()
        got = self.meta.data['package']['hash']
        #assert expected == got, "Package hash invalid!"
        if expected != got:
            raise PackageIntegrityError("Package SHA-1 check failed. "
                                        "Expected %r, got %r." %
                                        (expected, got))

    def _verify_signature(self):
        """Verifies the package authenticity."""

        verify = self.meta.gpg.verify_detached(join(
            self.meta.basedir,
            self.filename,
        ),
            self.meta.data['package']['signature']
        )

        if not verify.valid:
            raise PackageIntegrityError("Package signature is invalid!")
        if verify.fingerprint != self.meta.data['meta']['fingerprint']:
            raise PackageIntegrityError("Package signature's fingerprint "
                                        "invalid! Expected %r, got %r." %
                                        (self.meta.data['meta']['fingerprint'],
                                         verify.fingerprint))
        self.signature = verify

class PackageCreator(Package):
    """Helper class for package and corresponding meta data creation."""

    def __init__(self, meta):
        super(PackageCreator, self).__init__(meta)

    def sign_package(self, keyid=None):
        """Returns a signature for the package file.
        :param keyid str Overrides default GnuPG key.
        :return string"""

        filename = join(
                self.meta.basedir,
                self.filename
        )

        with open(filename, 'r') as file:
            result = self.meta.gpg.sign_file(
                file,
                keyid=keyid,
                detached=True,
                clearsign=False
            )

        return result

class PackageIntegrityError(Exception):
    pass

