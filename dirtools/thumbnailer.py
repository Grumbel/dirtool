# dirtool.py - diff tool for directories
# Copyright (C) 2017 Ingo Ruhnke <grumbel@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# https://dbus.freedesktop.org/doc/dbus-python/doc/tutorial.html
# https://wiki.gnome.org/action/show/DraftSpecs/ThumbnailerSpec
# qdbus org.freedesktop.thumbnails.Thumbnailer1 /org/freedesktop/thumbnails/Thumbnailer1


import os
import hashlib
import urllib
import dbus
import mimetypes
import xdg.BaseDirectory


class ThumbnailerListener:

    def __init__(self):
        pass

    def started(self, handle):
        pass

    def ready(self, handle, urls):
        pass

    def error(self, handle, failed_uris, error_code, message):
        pass

    def finished(self, handle):
        pass

    def idle(self):
        pass


class Thumbnailer:

    def __init__(self, bus, listener=ThumbnailerListener()):
        self.bus = bus
        self.requests = {}
        self.thumbnailer = bus.get_object(
            'org.freedesktop.thumbnails.Thumbnailer1',
            '/org/freedesktop/thumbnails/Thumbnailer1')
        self.listener = listener

        self.thumbnailer.connect_to_signal("Ready", self._receive_ready)
        self.thumbnailer.connect_to_signal("Started", self._receive_started)
        self.thumbnailer.connect_to_signal("Finished", self._receive_finished)
        self.thumbnailer.connect_to_signal("Error", self._receive_error)

    def _add_request(self, handle, urls):
        self.requests[handle] = urls

    def _remove_request(self, handle):
        if handle in self.requests:
            del self.requests[handle]

        if not self.requests:
            self.listener.idle()

    def _receive_started(self, handle):
        self.listener.started(handle)

    def _receive_ready(self, handle, uris):
        self.listener.ready(handle, uris)

    def _receive_finished(self, handle):
        self.listener.finished(handle)
        self._remove_request(handle)

    def _receive_error(self, handle, failed_uris, error_code, message):
        self.listener.error(handle, failed_uris, error_code, message)

    def queue(self, files, flavor="default"):
        urls = ["file://" + urllib.parse.quote(os.path.abspath(f)) for f in files]
        mime_types = [
            mimetypes.guess_type(url)[0] or "application/octet-stream"
            for url in urls
        ]
        handle = self.thumbnailer.Queue(
            urls,  # uris: as
            mime_types,  # mime_types: as
            flavor,  # flavor: s
            "default",  # scheduler: s
            dbus.UInt32(0),  # handle_to_dequeue: u
            # <arg type="u" name="handle" direction="out" />
        )
        self._add_request(handle, urls)

    def dequeue(self, handle):
        self.thumbnailer.Dequeue(handle)
        del self.requests[handle]

    def get_supported(self):
        uri_schemes, mime_types = self.thumbnailer.GetSupported()
        return (uri_schemes, mime_types)

    def get_schedulers(self):
        schedulers = self.thumbnailer.GetSchedulers()
        return schedulers

    def get_flavors(self):
        flavors = self.thumbnailer.GetFlavors()
        return flavors

    @staticmethod
    def thumbnail_from_filename(filename, flavor="normal"):
        url = "file://" + urllib.parse.quote(os.path.abspath(filename))
        digest = hashlib.md5(os.fsencode(url)).hexdigest()
        result = os.path.join(xdg.BaseDirectory.xdg_cache_home, "thumbnails", flavor, digest + ".png")
        return result

    @staticmethod
    def thumbnail_from_url(url, flavor="normal"):
        digest = hashlib.md5(os.fsencode(url)).hexdigest()
        result = os.path.join(xdg.BaseDirectory.xdg_cache_home, "thumbnails", flavor, digest + ".png")
        return result


# EOF #
