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


import argparse
import sys
import os

from dirtools.xdg_mime_associations import XdgMimeAssociations
from dirtools.xdg_desktop import get_desktop_file

def parse_args(args):
    parser = argparse.ArgumentParser(description="Query the systems mime associations")
    parser.add_argument("MIMETYPE", nargs=1)
    return parser.parse_args(args)


def main(argv):
    args = parse_args(argv[1:])
    mimeasc = XdgMimeAssociations.system()

    mimetype = args.MIMETYPE[0]

    defaults = mimeasc.get_default_apps(mimetype)
    assocs = mimeasc.get_associations(mimetype)

    print("mime-type: {}".format(mimetype))
    print()

    print("default applications:")
    for desktop in defaults:
        print("  {}".format(get_desktop_file(desktop) or "{} (file not found)".format(desktop)))
    print()

    print("associated applications:")
    for desktop in assocs:
        print("  {}".format(get_desktop_file(desktop) or "{} (file not found)".format(desktop)))
    print()

def main_entrypoint():
    exit(main(sys.argv))


# EOF #