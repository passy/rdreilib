# -*- coding: utf-8 -*-
"""
 rdreilib.url_converters
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~
 Provides additional url converters for werkzeug routing.


 :copyright: 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
"""

from werkzeug.routing import UnicodeConverter

class P2Converter(UnicodeConverter):
    """This converter accepts p2ids as parameter like
    3a-G7x."""
    
    def __init__(self, *args, **kwargs):
        super(P2Converter, self).__init__(*args, **kwargs)
        self.regex = r'[a-zA-Z0-9-]+'

