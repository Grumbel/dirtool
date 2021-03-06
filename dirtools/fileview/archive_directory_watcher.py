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


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dirtools.fileview.directory_watcher import DirectoryWatcher  # noqa: F401
    from dirtools.fileview.archive_extractor import ArchiveExtractor  # noqa: F401


class ArchiveDirectoryWatcher:

    def __init__(self,
                 directory_watcher: 'DirectoryWatcher',
                 archive_extractor: 'ArchiveExtractor') -> None:
        self._directory_watcher = directory_watcher
        self._archive_extractor = archive_extractor

    def close(self) -> None:
        self._directory_watcher.close()

    def start(self) -> None:
        self._directory_watcher.start()

    @property
    def sig_file_added(self):
        return self._directory_watcher.sig_file_added

    @property
    def sig_file_removed(self):
        return self._directory_watcher.sig_file_removed

    @property
    def sig_file_modified(self):
        return self._directory_watcher.sig_file_modified

    @property
    def sig_file_closed(self):
        return self._directory_watcher.sig_file_closed

    @property
    def sig_scandir_finished(self):
        return self._directory_watcher.sig_scandir_finished

    @property
    def sig_finished(self):
        return self._archive_extractor.sig_finished

    @property
    def sig_message(self):
        return self._directory_watcher.sig_message


# EOF #
