# dirtool.py - diff tool for directories
# Copyright (C) 2018 Ingo Ruhnke <grumbel@gmail.com>
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


from typing import List

import signal
import dbus

from PyQt5.QtWidgets import QApplication
from dbus.mainloop.pyqt5 import DBusQtMainLoop

from dirtools.fileview.controller import Controller
from dirtools.dbus_thumbnailer import DBusThumbnailer
from dirtools.fileview.thumbnail_cache import ThumbnailCache, ThumbnailCacheListener


class FileViewApplication:

    def __init__(self):
        # Allow Ctrl-C killing of the Qt app, see:
        # http://stackoverflow.com/questions/4938723/
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        self.qapp = QApplication([])
        self.dbus_loop = DBusQtMainLoop(set_as_default=True)
        self.session_bus = dbus.SessionBus()
        self.thumbnailer = DBusThumbnailer(self.session_bus)

        self.thumbnail_cache = ThumbnailCache(self.thumbnailer)
        self.thumbnailer.listener = ThumbnailCacheListener(self.thumbnail_cache)

        self.controllers: List[Controller] = []

    def run(self):
        return self.qapp.exec()

    def show_files(self, files):
        controller = Controller(self)
        self.thumbnail_cache.sig_thumbnail.connect(controller.receive_thumbnail)
        controller.set_files(files)
        controller.window.show()
        self.controllers.append(controller)

    def show_location(self, path):
        controller = Controller(self)
        self.thumbnail_cache.sig_thumbnail.connect(controller.receive_thumbnail)
        controller.set_location(path)
        controller.window.show()
        self.controllers.append(controller)


# EOF #
