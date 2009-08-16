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

    def index(self, request):
        assert False
        return self.render("index.html")

    def _get_downloader(self):
        return Downloader.from_config(get_app().updater_config)

    @json_view
    def ajax_check_update(self, request):
        dl = self._get_downloader()
        rev = dl.get_version()
        cur = UpdateLog.query.get_latest().version.revision

        return [rev, cur]

