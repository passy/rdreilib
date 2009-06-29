# -*- coding: utf-8 -*-
"""
 eauth.facebook
 ~~~~~~~~~~~~~~~~
 Middleware for facebook connect.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
 """

import hashlib
import logging

log = logging.getLogger('eauth.facebook')

class FacebookMiddleware(object):
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key

    def check_cookie(self, req):
        """Check for a valid facebook cookie and set try to get
        the user from DB or create a new one."""

        if not req.user.is_authenticated():
           log.debug("User not logged in. Let's get the party started!")
           if self.api_key in req.cookies:
               log.debug("API cookie found.")
               signature_hash = self._get_facebook_signature(req.cookies, True)
               if signature_hash == req.cookies[self.api_key]:
                   log.debug("Hash key is valid! Assuming the user is valid!")
               else:
                   log.info("Hash invalid! Expected: %s, got: %s!" %
                            (signature_hash, req.cookies[self.api_key]))

    def _get_facebook_signature(self, values_dict, is_cookie_check=False):
        signature_keys = []
        for key in sorted(values_dict.keys()):
            if (is_cookie_check and key.startswith(self.api_key + '_')):
                signature_keys.append(key)
            elif (is_cookie_check is False):
                signature_keys.append(key)

            if (is_cookie_check):
                signature_string = ''.join(['%s=%s' % (x.replace(self.api_key + '_',''), values_dict[x]) for x in signature_keys])
            else:
                signature_string = ''.join(['%s=%s' % (x, values_dict[x]) for x in signature_keys])
                signature_string = signature_string + self.secret_key

            return hashlib.md5(signature_string).hexdigest()


def setup_facebook_connect(app):
    app.add_config_var('facebook/api_key', str, '')
    app.add_config_var('facebook/secret_key', str, '')

    FM = FacebookMiddleware(app.cfg['facebook/api_key'],
                            app.cfg['facebook/secret_key'])

    app.connect_event('request-start', FM.check_cookie)

