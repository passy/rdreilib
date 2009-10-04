# -*- coding: utf-8 -*-
"""
rdreilib.beaker.utils
~~~~~~~~~~~~~~~~~~~~~
Some utilities to better integrate beaker into glashammer.

:copyright: 2009, Pascal Hartig <phartig@rdrei.net>
:license: BSD, see doc/LICENSE for more details.
"""

def make_dict(cfg, org_prefix, new_prefix):
    """Generates a dictionary that is parsable by beaker from prefixed config
    valures stored in the zine/glashammer config."""

    result = dict()
    for key, value in cfg.iteritems():
        if key.startswith(org_prefix):
            new_key = new_prefix+key.split(org_prefix)[1]
            result[new_key] = value

    return result

