# -*- coding: utf-8 -*-
"""
rdreilib.rst_formatting
~~~~~~~~~~~~~~~~~~~~~~~

Provides formatting helpers for ReSTructured text.

:copyright: 2009, Pascal Hartig <phartig@rdrei.net>
:license: BSD, see doc/LICENSE for more details.
"""

try:
    from docutils.core import publish_parts
except ImportError:
    _docutils_present = False
else:
    _docutils_present = True

def format_rst(text, inline=True, silent=True):
    """
    Format RST markup.

    :param inline: Specify whether to spit out a single fragment or the whole
    generated HTML document.
    :param silent: Set to ignore missing docutil dependency and return the
    unformatted input string.

    :return: str
    """

    if not _docutils_present:
        if silent:
            return text
        else:
            raise RuntimeError("RST processing requires docutils installed.")

    key = 'whole'
    if inline:
        key = 'fragment'

    return publish_parts(text, writer_name='html')[key]


__all__ = ('format_rst',)
