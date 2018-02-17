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


import os
import sys
import argparse

from dirtools.fileview.application import FileViewApplication
from dirtools.fileview.filelist_stream import FileListStream
from dirtools.util import expand_directories

import logging

logger = logging.getLogger(__name__)


def parse_args(args):
    parser = argparse.ArgumentParser(description="Display files graphically")
    parser.add_argument("FILE", nargs='*')
    parser.add_argument("-t", "--timespace", action='store_true',
                        help="Space items appart given their mtime")
    parser.add_argument("-0", "--null", action='store_true',
                        help="Read \\0 separated lines")
    parser.add_argument("-r", "--recursive", action='store_true', default=False,
                        help="Be recursive")
    parser.add_argument("-e", "--empty", action='store_true', default=False,
                        help="Start with a empty workbench instead of the current directory")
    parser.add_argument("-d", "--debug", action='store_true', default=False,
                        help="Print lots of debugging output")
    return parser.parse_args(args)


def main(argv):
    args = parse_args(argv[1:])

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    app = FileViewApplication()

    if args.FILE == []:
        app.show_location(os.getcwd())
    elif args.FILE == ["-"]:
        if args.null:
            app.show_filelist_stream(FileListStream(sys.stdin, "\0"))
        else:
            app.show_filelist_stream(FileListStream(sys.stdin, "\n"))
    elif len(args.FILE) == 1 and os.path.isdir(args.FILE[0]):
        app.show_location(args.FILE[0])
    elif args.recursive:
        files = expand_directories(args.FILE, args.recursive)
        app.show_files(files)
    else:
        app.show_files(args.FILE)

    sys.exit(app.run())


def main_entrypoint():
    main(sys.argv)


# EOF #
