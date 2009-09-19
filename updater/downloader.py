# -*- coding: utf-8 -*-
"""
 rdreilib.updater.downloader
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~
 Download module for r3u.


 :copyright: 2008, 2009 by Pascal Hartig <phartig@rdrei.net>
 :license: GPL v3, see doc/LICENSE for more details.
 """

from __future__ import division

import yaml
import urllib2
import base64
import tempfile
import logging
import time

from os import path
from httplib import HTTPException
from .version import __version__
from .models import UpdateLog, UPDATE_STATES, VersionLog
from ..database import session


log = logging.getLogger('rdreilib.updater.downloader')


class Downloader(object):
    PACKACKE_PATTERN = "update_%d.r3u"
    _repoyaml = None


    def __init__(self, url, credentials=None, cache=None):
        """Creates a download helper for a specific repository. The repository
        currently must be a WebDAV style http server with HTTP Basic
        authorization. Consider box.net for that.

        :param url: Full URL including protocol, host name, port (optional) and
            path. Like: http://box.net:80/webdav/myfolder
        :param credentials dict: A dictionary containing a ``username`` and
            ``password`` attribute.
        :param cache: Optional caching object to store yaml data in.
        """

        self.url = url
        self.credentials = credentials
        self.cache = cache

        # Tracks current download's progress as rounded int in percent.
        self.last_progress = 0
        # Last DB write for tracking
        self.last_track = 0

    @property
    def repoyaml(self):
        """Property for either cached or uncached access of repoyaml depending
        on whether a Cache instance is present or not."""
        if self.cache is not None:
            if 'repoyaml' in self.cache:
                log.debug("Using repoyaml from cache.")
                return self.cache['repoyaml']

        return self._repoyaml

    @repoyaml.setter
    def repoyaml(self, value):
        if self.cache is not None:
            self.cache['repoyaml'] = value

        else:
            self._repoyaml = value

    @classmethod
    def from_config(cls, cfg, cache=None):
        """Creates an instance of Downloader from a config object."""
        credentials = None
        if cfg['server/username'] and cfg['server/password']:
            credentials = {'username': cfg['server/username'],
                           'password': cfg['server/password']}
        return cls(
            cfg['server/url'],
            credentials,
            cache
        )

    def _authorize_headers(self):
        """Formats ``self.credentials`` into a HTTP Basic Authorization
        header."""

        if self.credentials is None:
            return dict()

        base64str = base64.encodestring("%(username)s:%(password)s" %
                                        (self.credentials))
        return {'Authorization': "Basic %s" % base64str}

    def _authorize_opener(self):
        """Builds a :class:``urllib2.HTTPBasicAuthHandler`` upon
        self.crendentials to build an opener from.

        :return: urllib2 opener"""

        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None,
                                  self.url,
                                  self.credentials['username'],
                                  self.credentials['password'])
        auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        return urllib2.build_opener(auth_handler)

    def _request(self, filename, track=None, buffer=None):
        """Opens a request to the server, sends credentials if provided and
        fetches the file.

        :param filename: Filename relative to ``self.repo_url``.
        :param track: (opt.) An instance of :class:``updater.models.VersionLog``
            to be updated on regular base for the progress of the download.
        :param buffer: For large files, it is useful to directly write to a
            buffer instead of using memory as a cache. This parameter accepts a
            file-like object with a write method.

        :return: string
        """

        # We constantly track the status of this function if track is enabled.
        self._track(track, 0, "Resolving host")
        # Build the full url including the path
        request = urllib2.Request(self.url+"/"+filename)
        # Add a User agent just for fun.
        request.add_header('User-agent', "rDREI updater v%s" % __version__)

        # This allows us to use basic authentication
        opener = self._authorize_opener()

        # Track all kinds of HTTP Errors, including 404
        try:
            # XXX: The timeout is fixed. This could be placed in the config.
            http = opener.open(request, None, 10)
        except IOError as err:
            self._track(track, -1, "Download failed with error: %s" % err,
                        'failure')
            raise

        # Check the status code, but be aware of stupid services like OpenDNS
        # not raising a NX_DOMAIN, but a redirection.
        status = http.getcode()
        if status != 200:
            self._track(track, -1, "Download server returned status %d" % status,
                        'failure')
            raise HTTPException("Server responded with code %d" % \
                                        status)
        # Track the OpenDNS case here
        if http.url != request.get_full_url():
            self._track(track, -1, "Got an unexpected redirection. Probably a "
                        "misconfigured DNS server.",
                       'failure')
            raise HTTPException("Server not found.")

        resp_str = str()
        cur_len = 0
        try:
            content_len = int(http.headers.get('Content-length', 0))
        except ValueError:
            self._track(track, -1, "Invalid Content-Length received!")
            raise HTTPException("Invalid headers received!",
                               'failure')

        self._track(track, 0, u"Initializing download")
        while True:
            text = http.read(4096)
            if not text:
                break
            # Calculate download progress
            cur_len += len(text)
            prog = round((cur_len/content_len)*100)
            self._track(track, prog, "Download in progress")
            if buffer is None:
                resp_str += text
            else:
                buffer.write(text)

        # Check if the download was complete.
        if cur_len == content_len:
            self._track(track, 100, u"Download complete.",
                       'download_success')
        else:
            self._track(track, -1, u"Download incomplete.",
                       'failure')
            raise HTTPException("Content-Length does not match downloaded "
                                "size.")

        return resp_str

    def _track(self, version, progress, message, state=None):
        """Tracks the progress of a download action.
        :param version: An instance of :class:``updater.models.VersionLog``
        :param progress: An integer, usually a percent value.
        :param message: Message for the version log entry.
        :param state: Optional state. Defaults to 'downloading'.
        """
        if progress == 'download' and (\
               progress == self.last_progress or\
               (0 < (self.last_track-time.time()) < 2)
            ):
            # Spam protection
            return

        if state is not None:
            state = UPDATE_STATES[state]
        else:
            state = UPDATE_STATES['download']

        log.debug("Tracking download state at progress=%d, message=%r, state=%d"
                  % (progress, message, state))

        # Update internal progress tracker.
        self.last_progress = progress
        self.last_track = time.time()

        if version is None:
            # This is needed for saving to database, but can be omitted to just
            # dump to log.
            return

        ul = UpdateLog(version, state, message,
                       progress)
        session.add(ul)
        session.commit()

    def get_repo_meta(self):
        """Fetches and parses the meta data on the server."""
        if self.repoyaml is None:
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

        # Create a new version log entry. Long version is updated after the
        # download is finished and meta is validated.
        vlog = VersionLog(revision)

        # Open the output file.
        if destination:
            if path.isdir(destination):
                out = tempfile.NamedTemporaryFile(delete=False, dir=destination)
            else:
                out = open(destination, 'wb')
        else:
            out = tempfile.NamedTemporaryFile(delete=False)

        self._request(filename, buffer=out, track=vlog)

        return out.name


class DownloaderError(Exception):
    pass
