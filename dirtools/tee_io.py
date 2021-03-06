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


from typing import IO


class TeeIO:
    """TeeIO wraps 'input_fd' and records all data read from it to 'output_fd'"""

    def __init__(self, input_fd: IO, output_fd: IO) -> None:
        self._input_fd = input_fd
        self._output_fd = output_fd

    def close(self):
        self._input_fd.close()
        self._output_fd.close()

    @property
    def closed(self):
        return self._input_fd.closed

    def fileno(self):
        return self._input_fd.fileno()

    def flush(self):
        self._input_fd.flush()
        self._output_fd.flush()

    def isatty(self):
        return self._input_fd.isatty()

    def readable(self):
        return self._input_fd.readable()

    def readline(self, size=-1):
        line = self._input_fd.readline(size)
        self._output_fd.write(line)
        return line

    def readlines(self, hint=-1):
        lines = self._input_fd.readline(hint)
        for line in lines:
            self._output_fd.write(line)
        return line

    def read(self, n=-1):
        buf = self._input_fd.read(n)
        self._output_fd.write(buf)
        return buf

    def tell(self):
        return self._input_fd.tell()

    def writable(self):
        return False

    def __enter__(self):
        self._input_fd.__enter__()
        self._output_fd.__enter__()
        return self

    def __exit__(self, exc_type, value, tb):
        self._input_fd.__exit__(exc_type, value, tb)
        self._output_fd.__exit__(exc_type, value, tb)


# EOF #
