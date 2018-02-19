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


import time


profile_active = False


if profile_active:
    class Profiler:

        def __init__(self, name):
            self.name = name

        def __enter__(self):
            self.start_time = time.time()

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.stop_time = time.time()
            print("executing {} took {:3.0f}msec".format(
                self.name, (self.stop_time - self.start_time) * 1000))

    def profile(func):
        def wrap(*args, **kwargs):
            with Profiler(func.__qualname__):
                result = func(*args, **kwargs)
                return result

        return wrap
else:
    class Profiler:
        def __init__(self, name):
            pass

        def __enter__(self):
            pass

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    def profile(func):
        return func


# EOF #
