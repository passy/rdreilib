# -*- coding: utf-8 -*-
"""
 rdreilib.generics
 ~~~~~~~~~~~~~~~~
 Generics views to keep your code DRY.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
"""

from werkzeug.exceptions import BadRequest

# rdreilib imports
from jsonlib import json_view
from sidebar import PermissionError

import logging
log = logging.getLogger("rdreilib.generics")

@json_view
def ajax_load_sidebar_modules(req, smodule):
    """Returns a ajax response that can be parsed by SidebarApplication in
    JavaScript.
    @param req {object}: current request
    @param smodule {class}: the SidebarModule base class to request the modules
    from.
    @returns {object}: A response object containing JSON content.
    """

    if req.method != 'POST':
        raise BadRequest("Invalid request method!")

    if 'modules' not in req.form:
        raise BadRequest("Insufficient parameters!")

    # The modules parameter contains a CSV-list with names of the modules to
    # load.
    modules = req.form['modules'].split(',')
    module_results = list()
    for mod in modules:
        log.debug("Trying to load module %r.", mod)
        try:
            module_results.append(smodule.request_module(mod, req))
        except (LookupError, PermissionError), err:
            log.warning("Requested module %r throws exception %r." % (mod, err))
            if req.app.conf["general.debug"]:
                from traceback import format_exc
                log.debug("Exception on module load: %s" % format_exc())
            continue

    return {'modules': module_results}

