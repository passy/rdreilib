# -*- coding: utf-8 -*-
"""
 manage.py
 ~~~~~~~~~
 rdrei updater management script


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
 """

from werkzeug import script
from meta import Meta, MetaCreator, MetaIntegrityError
from package import Package, PackageCreator

from os import path, listdir
import zipfile

def action_makepkg(directory=('d', '')):
    """Create a update package from ``directory``."""

    if not path.exists(directory):
        raise RuntimeError("Directory %r does not exist!" % directory)

    print("* Checking config file")
    metapath = path.join(directory, "meta.yaml")
    if not path.exists(metapath):
        raise RuntimeError("Config file %r not present!" % metapath)

    meta = Meta(metapath)
    valid = True
    try:
        meta.check()
    except MetaIntegrityError:
        valid = False

    if not valid:
        _build_meta(metapath)
    else:
        meta = Meta(metapath)
        if _check_dir(directory, meta.data):
            _pack_files(directory, meta.data)

def _build_meta(config):
    """Creates required signatures and hashes."""

    print("* Generating hashes/signatures")
    print("*** YOU WILL BE ASKED FOR YOUR GPG PASSWORD TWICE! ***")

    metac = MetaCreator(config)
    data = metac.make_signatures()
    metac.write_data(data)

    print("* Updated signatures. Reformat %r now and restart!" % config)

def _check_dir(directory, mdata):
    """Makes sure the directory contains the required files only."""

    for fname in listdir(directory):
        if fname == "meta.yaml":
            pass
        elif fname == mdata['package']['filename']:
            pass
        else:
            print("! ERROR: Unnecessary file in %s: %s!" % (directory, fname))
            return False
    return True

def _pack_files(directory, mdata):
    """Creates meta archive."""

    # Generate filename from meta data revision. This generic scheme is used to
    # make accessing the correct file on the update server is easy.
    filename = 'update_%d.r3u' % mdata['version']['revision']

    print("* Creating archive %s" % filename)
    if path.exists(filename):
        print("! ERROR: File %r already exists!" % filename)
        return

    arc = zipfile.ZipFile(filename, 'w')

    for fname in listdir(directory):
        arc.write(path.join(directory, fname), fname)

    arc.close()
    print("* Done.")

if __name__ == '__main__':
    script.run()
