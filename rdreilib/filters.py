# -*- coding: utf-8 -*-
"""
 rdreilib.filters
 ~~~~~~~~~~~~~~~~
 Additional template filters


 :copyright: 2008 by Pascal Hartig <phartig@rdrei.net>
 :license: BSD, see doc/LICENSE for more details.
"""

import re, logging

log = logging.getLogger("rdreilib.filters")

def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    """Formats a date with strftime properyly. With no parameter supplied,
    :func:``datetimeformat`` chooses a default display."""
    return value.strftime(format)

def highlight(value, hl, markup='<strong class="highlight">%s</strong>'):
    if not hl:
        return value

    # duck typing hl
    if hasattr(hl, 'upper'):
        repl_re = re.compile(re.escape(hl), re.I)
    elif type(hl) is list:
        repl_re = re.compile("|".join([re.escape(val) for val in hl]), re.I)
    else:
        raise TypeError("Unsupported highlight type. Expected string type or "\
                        "list.")

    log.debug("Markup: %r", type(value))
    return repl_re.sub(markup % r"\g<0>", unicode(value))

def highlight_legacy(value, hl, markup='<strong class="highlight">%s</strong>'):
    """Sorrounds a given value with markup.
    This is DEPRECATED in favor of a regular expression solution."""

    if not hl:
        # There could be an empty filter string.
        return value

    ## Escape it, so we can display our HTML safely.
    # No longer, escape it before, plx.
    #value = escape(value) 

    # Ducktyping this, with SafeUnicode and stuff everything else gets way to
    # complex. Tell me if there's a better way.
    if hasattr(hl, 'upper'):
        value = (markup % hl).join(value.split(hl))
    elif type(hl) is list:
        for single_hl in hl:
            value = (markup % single_hl).join(value.split(single_hl))

    return value

def intdisplay(value):
    """Simple method to display a float value as rounded integer."""
    return "%d" % round(value)
