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


class UpdateController(BaseController):
    endpoint = "updater"

    def __init__(self):
        self.config = get_app().updater_config

    def index(self, request):
        return self.render("index.html", app_name=self.config['general/appname'])

    def _get_downloader(self):
        return Downloader.from_config(self.config)

    def _get_current(self):
        return UpdateLog.query.get_latest().version.revision

    @json_view
    def ajax_check_update(self, request):
        dl = self._get_downloader()
        rev = dl.get_version()
        cur = self._get_current()

        return [rev, cur]

    def ajax_update_skeleton(self, request):
        # TODO: Get this from session or cache
        cur = self._get_current
        diff = (self._get_downloader().get_version()-cur)
        assert diff > 0, "Server is not up-to-date!"

        updates = list()
        for i in xrange(diff):
            updates.append({
                'revision': cur+i+1,
            })

        #TODO: Continue here. Get the real meta data and somehow format this.

        return self.render("update_list.html", _path="partials",
                           updates=updates)


