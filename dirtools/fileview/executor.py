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


from typing import List, Optional

import logging
import subprocess
import shlex

from dirtools.xdg_desktop import get_desktop_entry
from dirtools.fileview.location import Location

logger = logging.getLogger(__name__)


class Executor:

    def __init__(self, app) -> None:
        self.app = app

    def launch_terminal(self, working_directory: Optional[Location] = None) -> None:
        if working_directory is None:
            self.launch_exo_terminal()
        else:
            self.launch_exo_terminal(self.app.vfs.get_stdio_name(working_directory))

    def launch_exo_terminal(self, working_directory: Optional[str] = None) -> None:
        argv = ["exo-open", "--launch", "TerminalEmulator"]
        if working_directory is not None:
            argv += ["--working-directory", working_directory]
        self.launch(argv)

    def open(self, location: Location) -> bool:
        mimetype = self.app.mime_database.get_mime_type(location).name()
        default_apps = self.app.mime_associations.get_default_apps(mimetype)

        for app in default_apps:
            entry = get_desktop_entry(app)
            if entry is not None:
                break
        else:
            return False

        self.launch_single_from_exec(entry.getExec(), location)

        return True

    def launch_single_from_exec(self, exec_str: str, location: Location) -> None:
        filename = self.app.vfs.get_stdio_name(location)

        def replace(lst: List[str], filename):
            result: List[str] = []
            for x in lst:
                if x in ["%f", "%u", "%F", "%U"]:
                    result.append(filename)
                else:
                    result.append(x)
            return result

        # FIXME: quick&dirty implementation, that doesn't follow the spec
        argv = shlex.split(exec_str)
        argv = replace(argv, filename)
        self.launch(argv)

    def launch_multi_from_exec(self, exec_str: str, locations: List[Location]) -> None:
        files = [self.app.vfs.get_stdio_name(location) for location in locations]

        def expand_multi(exe: List[str], files: List[str]) -> List[str]:
            result: List[str] = []
            for x in exe:
                if x == "%F" or x == "%U":
                    result += files
                else:
                    result.append(x)
            return result

        def expand_single(exe: List[str], filename: str) -> List[str]:
            result: List[str] = []
            for x in exe:
                if x == "%f" or x == "%u":
                    result.append(filename)
                else:
                    result.append(x)
            return result

        # FIXME: quick&dirty implementation, that doesn't follow the spec
        argv = shlex.split(exec_str)
        if "%F" in argv or "%U" in argv:
            argv = expand_multi(argv, files)
            self.launch(argv)
        elif "%f" in argv or "%u" in argv:
            for filename in files:
                argv = expand_single(argv, filename)
                self.launch(argv)
        else:
            logger.error("unhandled .desktop Exec: %s", exec_str)

    def launch(self, argv: List[str]) -> None:
        logger.info("Launching: %s", argv)
        subprocess.Popen(argv)


# EOF #
