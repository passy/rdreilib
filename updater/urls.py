# -*- coding: utf-8 -*-
"""
 rdreilib.updater.urls
 ~~~~~~~~~~~~~~~~
 URL map for rdreilib updater.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
"""

from werkzeug.routing import Rule


def make_urls():
    return [
        Rule('/', endpoint='updater/index'),
        Rule('/ajax/check_update', endpoint='updater/ajax_check_update'), 
    ]

__all__ = ('make_urls')
