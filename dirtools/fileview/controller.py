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


from typing import List, Dict, Any, Optional

import logging
import os
import subprocess
import io

from PyQt5.QtWidgets import QFileDialog, QTextEdit
from PyQt5.QtCore import QObject

from dirtools.fileview.actions import Actions
from dirtools.fileview.file_collection import FileCollection
from dirtools.fileview.file_view_window import FileViewWindow
from dirtools.fileview.filter import Filter
from dirtools.fileview.sorter import Sorter
from dirtools.fileview.directory_watcher import DirectoryWatcher
from dirtools.fileview.filter_parser import FilterParser
from dirtools.fileview.settings import settings
from dirtools.fileview.filelist_stream import FileListStream

logger = logging.getLogger(__name__)


class Controller(QObject):

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.location: Optional[str] = None
        self.file_collection = FileCollection()
        self.actions = Actions(self)
        self.window = FileViewWindow(self)
        self.filter = Filter()
        self.sorter = Sorter(self)
        self.history: List[str] = []
        self.history_index = 0

        self.directory_watcher = None
        self.filelist_stream: Optional[FileListStream] = None

        self.window.file_view.set_file_collection(self.file_collection)
        self.window.thumb_view.set_file_collection(self.file_collection)

        self.filter_help = QTextEdit()

        self.app.metadata_collector.sig_metadata_ready.connect(self.receive_metadata)

        self._apply_settings()

    def close(self):
        if self.directory_watcher is not None:
            self.directory_watcher.close()

    def _apply_settings(self):
        v = settings.value("globals/crop_thumbnails", False, bool)
        self.actions.crop_thumbnails.setChecked(v)
        self.actions.crop_thumbnails.triggered.emit()

    def save_as(self):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        filename, kind = QFileDialog.getSaveFileName(
            self.window,
            "QFileDialog.getSaveFileName()",
            "",  # dir
            "URL List (*.urls);;Path List (*.txt);;NUL Path List (*.nlst)",
            options=options)

        if filename != "":
            self.file_collection.save_as(filename)

    def on_exit(self):
        self.app.close_controller(self)

    def show_hidden(self):
        self.filter.show_hidden = not self.filter.show_hidden
        self.apply_filter()

    def show_filtered(self):
        self.window.thumb_view.set_show_filtered(not self.window.thumb_view.show_filtered)

    def show_abspath(self):
        self.window.file_view.show_abspath()

    def show_basename(self):
        self.window.file_view.show_basename()

    def view_detail_view(self):
        self.window.show_file_view()

    def show_thumb_view(self):
        self.window.show_thumb_view()

    def view_icon_view(self):
        pass

    def view_small_icon_view(self):
        pass

    def zoom_in(self):
        self.window.thumb_view.zoom_in()

    def zoom_out(self):
        self.window.thumb_view.zoom_out()

    def less_details(self):
        self.window.thumb_view.less_details()

    def show_filter_help(self):
        parser = FilterParser(self.filter)

        fout = io.StringIO()
        parser.print_help(fout)

        self.filter_help.setText(fout.getvalue())
        self.filter_help.resize(480, 800)
        self.filter_help.show()

    def more_details(self):
        self.window.thumb_view.more_details()

    def set_filter(self, pattern):
        parser = FilterParser(self.filter)
        parser.parse(pattern)
        self.apply_filter()

    def go_forward(self):
        if self.history != []:
            self.history_index = min(self.history_index + 1, len(self.history) - 1)
            self.history[self.history_index]
            self.set_location(self.history[self.history_index], track_history=False)
            if self.history_index == len(self.history) - 1:
                self.actions.forward.setEnabled(False)
            self.actions.back.setEnabled(True)

    def go_back(self):
        if self.history != []:
            self.history_index = max(self.history_index - 1, 0)
            self.set_location(self.history[self.history_index], track_history=False)
            if self.history_index == 0:
                self.actions.back.setEnabled(False)
            self.actions.forward.setEnabled(True)

    def go_home(self):
        home = os.path.expanduser("~")
        self.set_location(home)

    def set_location(self, location, track_history=True):
        self.app.location_history.append(location)

        if track_history:
            self.history = self.history[0:self.history_index + 1]
            self.history_index = len(self.history)
            self.history.append(location)
            self.actions.back.setEnabled(True)
            self.actions.forward.setEnabled(False)

        self.window.show_loading()
        self.file_collection.clear()

        if self.directory_watcher is not None:
            self.directory_watcher.close()
        self.directory_watcher = DirectoryWatcher(location)
        self.directory_watcher.sig_file_added.connect(self.file_collection.add_fileinfo)
        self.directory_watcher.sig_file_removed.connect(self.file_collection.remove_file)
        self.directory_watcher.sig_file_changed.connect(self.file_collection.change_file)
        self.directory_watcher.sig_scandir_finished.connect(self.on_scandir_finished)
        self.directory_watcher.start()

        self.location = os.path.abspath(location)
        self.window.set_location(self.location)

        # files = expand_file(self.location, recursive=False)
        # self.set_files(files, self.location)

    def on_scandir_finished(self, fileinfos):
        self.window.hide_loading()
        self.file_collection.set_fileinfos(fileinfos)
        self.apply_sort()
        self.apply_filter()

    def set_files(self, files, location=None):
        if location is None:
            self.window.set_file_list()
        self.location = location
        self.file_collection.set_files(files)
        self.apply_sort()
        self.apply_filter()

    def set_filelist_stream(self, stream: FileListStream, location: Optional[str]=None):
        if location is None:
            self.window.set_file_list()
        self.location = location

        self.window.show_loading()

        self.filelist_stream = stream
        self.filelist_stream.sig_file_added.connect(self.file_collection.add_fileinfo)
        self.filelist_stream.sig_end_of_stream.connect(lambda: self.window.hide_loading())
        self.filelist_stream.start()

    def apply_sort(self):
        logger.debug("Controller.apply_sort")
        self.sorter.apply(self.file_collection)

    def apply_filter(self):
        logger.debug("Controller.apply_filter")
        self.file_collection.filter(self.filter)
        self._update_info()

    def _update_info(self):
        fileinfos = self.file_collection.get_fileinfos()

        filtered_count = 0
        hidden_count = 0
        for fileinfo in fileinfos:
            if fileinfo.is_hidden:
                hidden_count += 1
            elif fileinfo.is_excluded:
                filtered_count += 1

        total = self.file_collection.size()

        self.window.show_info("{} visible, {} filtered, {} hidden, {} total".format(
            total - filtered_count - hidden_count,
            filtered_count,
            hidden_count,
            total))

        self.window.thumb_view.set_filtered(filtered_count > 0)

    def toggle_timegaps(self):
        self.window.file_view.toggle_timegaps()

    def parent_directory(self, new_window=False):
        if self.location is not None:
            if new_window:
                self.app.show_location(os.path.dirname(os.path.abspath(self.location)))
            else:
                self.set_location(os.path.dirname(os.path.abspath(self.location)))

    def on_click(self, fileinfo, new_window=False):
        self.window.thumb_view.set_cursor_to_fileinfo(fileinfo)

        if not fileinfo.isdir():
            self.app.file_history.append(fileinfo.abspath())

            argv = ["xdg-open", fileinfo.abspath()]
            logger.info("Controller.on_click: launching: %s", argv)
            subprocess.Popen(argv)
        else:
            if self.location is None or new_window:
                logger.info("Controller.on_click: app.show_location: %s", fileinfo)
                self.app.show_location(fileinfo.abspath())
            else:
                logger.info("Controller.on_click: self.set_location: %s", fileinfo)
                self.set_location(fileinfo.abspath())

    def show_current_filename(self, filename):
        self.window.show_current_filename(filename)

    def add_files(self, files):
        for f in files:
            self.file_collection.add_file(f)

    def set_crop_thumbnails(self, v):
        settings.set_value("globals/crop_thumbnails", v)
        self.window.thumb_view.set_crop_thumbnails(v)

    def request_metadata(self, fileinfo):
        self.app.metadata_collector.request_metadata(fileinfo.abspath())

    def receive_metadata(self, filename: str, metadata: Dict[str, Any]):
        logger.debug("Controller.receive_metadata: %s %s", filename, metadata)
        fileinfo = self.file_collection.get_fileinfo(filename)
        if fileinfo is None:
            logger.error("Controller.receive_metadata: not found fileinfo for %s", filename)
        else:
            fileinfo.metadata().update(metadata)
            self.file_collection.update_file(fileinfo)

    def request_thumbnail(self, fileinfo, flavor):
        self.app.thumbnailer.request_thumbnail(fileinfo.abspath(), flavor,
                                               self.receive_thumbnail)

    def prepare(self):
        self.window.thumb_view.prepare()

    def reload(self):
        self.set_location(self.location)

    def receive_thumbnail(self, filename, flavor, pixmap, error_code, message):
        self.window.thumb_view.receive_thumbnail(filename, flavor, pixmap, error_code, message)

    def reload_thumbnails(self):
        self.app.dbus_thumbnail_cache.delete(
            [f.abspath()
             for f in self.file_collection.get_fileinfos()])
        self.window.thumb_view.reload_thumbnails()


# EOF #
