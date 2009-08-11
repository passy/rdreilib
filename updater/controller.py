# -*- coding: utf-8 -*-
"""
 rdreilib.updater.controller
 ~~~~~~~~~~~~~~~~
 Update controller.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
 """

from werkzeug.wrappers import BaseResponse
from ..controller import BaseController


class UpdateController(BaseController):
    endpoint = "updater"

    def index(self, request):
        return self.render("index.html")

