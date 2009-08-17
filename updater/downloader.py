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
import tempfile
import logging

from os import path
from version import __version__


log = logging.getLogger('rdreilib.updater.downloader')


class Downloader(object):
    PACKACKE_PATTERN = "update_%d.r3u"
    repoyaml = None

    def __init__(self, host, path, credentials=None, port=80):
        """Creates a download helper for a specific repository. The repository
        currently must be a WebDAV style http server with HTTP Basic
        authorization. Consider box.net for that.

        :param host: Hostname like 'box.net'
        :param path: Absolute path containing the root dir of up
        :param credentials dict: A dictionary containing a ``username`` and
                                ``password`` attribute.
        """

        self.host = host
        self.path = path
        self.port = port
        self.credentials = credentials

    @classmethod
    def from_config(cls, cfg):
        """Creates an instance of Downloader from a config object."""
        credentials = None
        if cfg['server/username'] and cfg['server/password']:
            credentials = {'username': cfg['server/username'],
                           'password': cfg['server/password']}
        return cls(
            cfg['server/host'],
            cfg['server/path'],
            credentials,
            cfg['server/port']
        )

    def _authorize_headers(self):
        """Formats ``self.credentials`` into a HTTP Basic Authorization
        header."""

        if self.credentials is None:
            return dict()

        base64str = base64.encodestring("%(username)s:%(password)s" %
                                        (self.credentials))
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

    def get_repo_meta(self):
        """Fetches and parses the meta data on the server."""
        if not self.repoyaml:
            log.debug("Requesting repository yaml data.")
            repometa = self._request("repository.yaml")
            self.repoyaml = yaml.load(repometa)

        if self.repoyaml['version'] > __version__:
            raise DownloaderError("Unsupported server "
                                  "version! Update your client!")

        return self.repoyaml

    def get_version(self):
        """Gets the most recent version on the server."""

        repoyaml = self.get_repo_meta()
        return repoyaml['revision']

    def download_package(self, revision, destination=None):
        """Downloads a update package for a specific revision. You're
        responsible to bring out the garbage, when done using this.

        :param revision: revision of package to download.
        :param destination: Path or filename to download to package.

        :return: Absolute path of downloaded package."""

        filename = self.PACKACKE_PATTERN % revision

        # Open the output file.
        if destination:
            if path.isdir(destination):
                out = tempfile.NamedTempFile(delete=False, dir=destination)
            else:
                out = open(destination, 'wb')
        else:
            out = tempfile.NamedTempFile(delete=False)

        out.write(self._request(filename))

        return out.name


class DownloaderError(Exception):
    pass
