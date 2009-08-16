# -*- coding: utf-8 -*-
"""
 rdreilib.updater.controller
 ~~~~~~~~~~~~~~~~
 Update controller.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
 """

from .downloader import Downloader
from .config import get_config

from werkzeug.wrappers import BaseResponse
from ..controller import BaseController
from ..jsonlib import json_view


class UpdateController(BaseController):
    endpoint = "updater"

    def index(self, request):
        return self.render("index.html")

    def _get_downloader(self):
        return Downloader.from_config(get_config())

    @json_view
    def ajax_check_update(self, request):
        dl = self._get_downloader()
        rev = dl.get_version()

        return [rev, 0]


