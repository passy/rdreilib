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
from ..jsonlib import json_view

import datetime
import logging


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
        return UpdateLog.query.get_latest().version.revision

    @json_view
    def ajax_check_update(self, req):
        dl = self._get_downloader(req)
        rev = dl.get_version()
        cur = self._get_current()

        return [rev, cur]

    def ajax_update_skeleton(self, req):
        # TODO: Get this from session or cache
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


