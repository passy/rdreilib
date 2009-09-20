# -*- coding: utf-8 -*-
"""
 rdreilib.updater.controller
 ~~~~~~~~~~~~~~~~
 Update controller.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
 """

from .downloader import Downloader
from .models import VersionLog, UpdateLog

from glashammer.utils.local import local, get_app
from ..controller import BaseController
from ..jsonlib import json_view, JSONException

import datetime
import logging
import os
import shutil


log = logging.getLogger('rdreilib.updater.controller')


class UpdateController(BaseController):
    endpoint = "updater"

    def __init__(self):
        self.config = get_app().updater_config

    def index(self, req):
        return self.render("index.html", app_name=self.config['general/appname'])

    def _get_downloader(self, req):
        """Gets a cached instance of Downloader"""
        return Downloader.from_config(self.config,
                                      req.cache.get_cache('downloader', expire=300))

    def _get_current(self):
        try:
            return UpdateLog.query.get_latest().version.revision
        except AttributeError:
            raise RuntimeError("Database is not prepared. Run "
                               "manage.py initdb!")

    @json_view
    def ajax_check_update(self, req):
        dl = self._get_downloader(req)
        rev = dl.get_version()
        cur = self._get_current()

        return [rev, cur]

    def ajax_update_skeleton(self, req):
        cur = self._get_current()
        repometa = self._get_downloader(req).get_repo_meta()
        diff = (self._get_downloader(req).get_version()-cur)
        assert diff > 0, "Client version is ahead of server's!"

        updates = list()
        if diff > 0:
            # Spare the cpu cycles if there is no update available.
            for revision, update in repometa['updates'].iteritems():
                if revision <= cur:
                    continue

                updates.append(dict(
                    revision=revision,
                    level=update['level'],
                    description=update['description'],
                    date=datetime.datetime.now() # Not in repo so far!
                ))

        return self.render("update_list.html", _path="partials",
                           update_list=updates)

    def list(self, req):
        """Lists locally available updates i.e. after download."""
        #TODO: Consider accepting parameter to automatically start verifying
        # downloads.
        versions = VersionLog.query.order_by(VersionLog.id.desc()).all()
        object_list = list()

        return self.render("list.html", version_list=versions)

    @json_view
    def ajax_start_download(self, req):
        """Starts a new download. Checks whether requested revision is not
        already applied or a upgrade to this version is already in progress.
        :param req.POST['revision']: Integer of the revision to install."""

        if 'revision' not in req.form:
            raise JSONException("Insufficient parameters!")

        # May raise an exception.
        revision = int(req.form['revision'])

        # Check the download folder exists
        path = self.config['files/download_path']
        if not os.path.exists(path):
            raise OSError("Download path %r does not exist." % path)
        if not os.path.isdir(path):
            raise OSError("Download path %r is not a directory." % path)

        downloader = self._get_downloader(req)
        #FIXME: Validate revision!
        file = downloader.download_package(revision)
        fullpath = os.path.join(path, downloader.PACKACKE_PATTERN % revision)

        # Download is done, move to download dir. Can fail, but the exception is
        # informative enough.
        shutil.move(file, fullpath)

        return {'success': {'message': "Download ended. Saved to %r." % fullpath}}

    @json_view
    def ajax_status_download(self, req, revision):
        """Checks for current download's progress."""

        rev_object = VersionLog.query.filter_by(revision=revision).one()
        #TODO: Catch misses
        ulog = UpdateLog.query.get_current(rev_object)
        return {'revision': revision,
                'date': ulog.updated.strftime(r"%d.%m.%Y"),
                'progress': ulog.progress,
                'message': ulog.message,
                'state': ulog.state}
