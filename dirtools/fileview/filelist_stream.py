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


from typing import Optional

import logging
import fcntl
import os

from PyQt5.QtCore import QObject, QSocketNotifier, pyqtSignal

from dirtools.fileview.file_info import FileInfo

logger = logging.getLogger(__name__)


def non_blocking_readline(fp, linesep):
    flag = fcntl.fcntl(fp, fcntl.F_GETFL)
    fcntl.fcntl(fp.fileno(), fcntl.F_SETFL, flag | os.O_NONBLOCK)

    rest = ""
    while True:
        try:
            # The buffer size is chosen to be artificially tiny to not
            # make the GUI unresponsive.
            data = fp.read(16)
        except BlockingIOError:
            yield None
        else:
            if data == "":
                return
            else:
                data = rest + data
                idx = data.find(linesep)
                if idx != -1:
                    rest = data[idx + 1:]
                    yield data[0:idx]
                else:
                    rest = data
                    yield None


class FileListStream(QObject):
    """FileListStream represents a stream of filenames read from stdin or
    from other sources that is visualized in the FileView.
    """

    sig_file_added = pyqtSignal(FileInfo)
    sig_end_of_stream = pyqtSignal()
    sig_error = pyqtSignal()

    def __init__(self, fp, linesep="\n"):
        super().__init__()

        self.fp = fp
        self.linesep = linesep

        self.readliner = non_blocking_readline(self.fp, self.linesep)

        self.socket_notifier: Optional[QSocketNotifier] = None

    def close(self):
        self.fp.close()

    def start(self):
        self.socket_notifier = QSocketNotifier(self.fp.fileno(), QSocketNotifier.Read)
        self.socket_notifier.activated.connect(self._on_activated)

    def _on_activated(self, fd) -> None:
        while True:
            try:
                filename = next(self.readliner)
            except StopIteration:
                self.socket_notifier.setEnabled(False)
                self.socket_notifier = None
                self.sig_end_of_stream.emit()
                return
            else:
                if filename is not None:
                    self.sig_file_added.emit(FileInfo.from_filename(filename))
                else:
                    return


# EOF #