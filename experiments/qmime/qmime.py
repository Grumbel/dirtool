#!/usr/bin/env python3

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
import sys
from PyQt5.QtCore import QCoreApplication, QMimeDatabase


def directory_changed(path: str) -> None:
    print("directory_changed: {}".format(path))


def file_changed(path: str) -> None:
    print("file_changed: {}".format(path))


def main(argv: List[str]) -> None:
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QCoreApplication([])  # noqa: F841
    mime_db = QMimeDatabase()
    mt = mime_db.mimeTypeForName("application/x-rar")
    print("name:", mt.name())
    print("iconName:", mt.iconName())
    print("genericIconName:", mt.genericIconName())
    print("aliases:", ", ".join(mt.aliases()))

    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)


# EOF #
