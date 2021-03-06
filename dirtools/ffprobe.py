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


import subprocess
import json


class FFProbe:

    def __init__(self, filename: str) -> None:
        proc = subprocess.Popen(
            ['ffprobe',
             '-v', 'error',
             '-print_format', 'json',
             '-show_format',
             '-show_streams',
             filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        try:
            out, err = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = proc.communicate()
            out = out.decode()
            err = err.decode()
            raise Exception("FFProbe: timeout: {}".format(filename))

        out = out.decode()
        err = err.decode()

        if proc.returncode != 0:
            raise Exception("FFProbe: {}: {}: {}".format(filename, proc.returncode, err))

        self.js = json.loads(out)
        self.streams = self.js['streams']
        self.format = self.js['format']

    def duration(self):
        return float(self.format['duration']) * 1000

    def width(self):
        return int(self.streams[0]['width'])

    def height(self):
        return int(self.streams[0]['height'])

    def framerate(self):
        text = self.streams[0]['avg_frame_rate']
        numerator, denominator = text.split("/")
        return int(numerator) / int(denominator)


# EOF #
