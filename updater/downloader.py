# -*- coding: utf-8 -*-
"""
 rdreilib.updater.downloader
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~
 Download module for r3u.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
 """

import yaml
import httplib
import base64

import __version__

class Downloader(object):
    def __init__(self, host, path, credentials=None, port=80):
        """Creates a download helper for a specific repository. The repository
        currently must be a WebDAV style http server with HTTP Basic
        authorization. Consider box.net for that.

        :param host: Hostname like 'box.net'
        :param path: Absolute path containing the root dir of up
        :param credentials dict: A dictionary containing a 'username' and
                                'password' attribute.
        """

        self.host = host
        self.path = path
        self.port = port
        self.credentials = credentials

    def _authorize_headers(self):
        """Formats ``self.credentials`` into a HTTP Basic Authorization
        header."""

        if self.credentials is None:
            return dict()

        base64str = base64.encodestring("%(username)s:%(password)s" % (self.credentials))
        return {'Authorization': "Basic %s" % base64str}


    def _request(self, filename):
        """Opens a request to the server, sends credentials if provided and
        fetches the file.

        :param filename: Filename relative to ``self.repo_url``.

        :return: string"""

        http = httplib.HTTPConnection(self.host, self.port)
        http.request('GET', "http://%s/%s/%s" % (self.host, self.path,
                                                 filename),
                     headers=self._authorize_headers())
        response = http.getresponse()
        if response.status != 200:
            raise httplib.HTTPException("Server responded with code %d" % \
                                        response.status)
        resp_str = str()

        while True:
            text = response.read(2048)
            if not text:
                break
            resp_str += text

        return resp_str

    def _get_repo_meta(self):
        """Fetches and parses the meta data on the server."""
        repometa = self._request("repository.yaml")
        repoyaml = yaml.load(repometa)

        if repoyaml['version'] > __version__:
            raise DownloaderError("Unsupported server "
                                  "version! Update your client!")


class DownloaderError(Exception):
    pass
