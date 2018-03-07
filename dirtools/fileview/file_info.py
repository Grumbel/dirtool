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


from typing import Dict, Any, Optional
import logging

import os
import stat

from dirtools.fileview.location import Location
from dirtools.fileview.filter_expr_parser import VIDEO_EXT, IMAGE_EXT, ARCHIVE_EXT

logger = logging.getLogger(__name__)


class FileInfo:

    @staticmethod
    def from_filename(filename: str) -> 'FileInfo':
        logger.debug("FileInfo.from_filename: %s", filename)

        fi = FileInfo()

        try:
            fi._abspath = os.path.abspath(filename)
            fi._location = Location.from_path(fi._abspath)
            fi._dirname = os.path.dirname(fi._abspath)
            fi._basename = os.path.basename(fi._abspath)
            fi._ext = os.path.splitext(fi._abspath)[1]

            fi._collect_stat()

            fi._isdir = os.path.isdir(fi._abspath)
            fi._isfile = stat.S_ISREG(fi._stat.st_mode)
            fi._issymlink = stat.S_ISLNK(fi._stat.st_mode)
        except FileNotFoundError:
            fi._filenotfound = True

        return fi

    def __init__(self) -> None:
        self._abspath: Optional[str] = None
        self._location: Optional[Location] = None
        self._dirname: Optional[str] = None
        self._basename: Optional[str] = None
        self._ext: Optional[str] = None

        self._isdir: Optional[bool] = None
        self._isfile: Optional[bool] = None
        self._issymlink: Optional[bool] = None

        self._stat: Optional[os.stat_result] = None
        self._have_access: Optional[bool] = None

        self._filenotfound = False

        self._metadata: Dict[str, Any] = {}

        # filter variables
        self.is_excluded: bool = False
        self.is_hidden: bool = False

        # grouper variables
        self.group: Any = None

    def _collect_stat(self) -> None:
        self._stat = os.lstat(self._abspath)
        self._have_access = os.access(self._abspath, os.R_OK)

    @property
    def is_visible(self) -> bool:
        return not self.is_hidden and not self.is_excluded

    def have_access(self) -> bool:
        return self._have_access

    def abspath(self) -> str:
        return self._abspath

    def location(self) -> Location:
        return self._location

    def dirname(self) -> str:
        return self._dirname

    def basename(self) -> str:
        return self._basename

    def isdir(self) -> bool:
        return self._isdir

    def isfile(self) -> bool:
        return self._isfile

    def is_thumbnailable(self) -> bool:
        return self.is_video() or self.is_image()

    def is_video(self) -> bool:
        return self._ext[1:].lower() in VIDEO_EXT

    def is_image(self) -> bool:
        return self._ext[1:].lower() in IMAGE_EXT

    def is_archive(self) -> bool:
        return self._ext[1:].lower() in ARCHIVE_EXT

    def stat(self) -> os.stat_result:
        return self._stat

    def uid(self) -> int:
        return self._stat.st_uid if self._stat else 0

    def gid(self) -> int:
        return self._stat.st_gid if self._stat else 0

    def ext(self) -> str:
        return self._ext

    def size(self) -> int:
        return self._stat.st_size if self._stat is not None else 0

    def mtime(self) -> float:
        return self._stat.st_mtime if self._stat is not None else 0

    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    def __str__(self) -> str:
        return "FileInfo({})".format(self._location)


# EOF #
