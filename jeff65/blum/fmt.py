# jeff65 disk format helper functions
# Copyright (C) 2017  jeff65 maintainers
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import struct


class Fmt:
    _bool = 0
    _u8 = 1
    _u16 = 2
    _u32 = 3
    _i8 = 4
    _i16 = 5
    _i32 = 6
    _str = 7
    _blob = 8
    _array = 10
    _table = 11
    _struct = 12
    _union = 13

    bool = (_bool,)  # pay attention to scope!
    u8 = (_u8,)
    u16 = (_u16,)
    u32 = (_u32,)
    i8 = (_i8,)
    i16 = (_i16,)
    i32 = (_i32,)
    str = (_str,)  # pay attention to scope!
    blob = (_blob,)

    @staticmethod
    def make_cc(code):
        cc, = struct.unpack('<H', code.encode('ascii'))
        return cc

    @classmethod
    def array(cls, item):
        return (cls._array, item)

    @classmethod
    def table(cls, key, value):
        return (cls._table, key, value)

    @classmethod
    def struct(cls, ty):
        return (cls._struct, ty)

    @classmethod
    def union(cls, tys):
        return (cls._union, tys)

    @classmethod
    def find_blobs(cls, obj):
        """Find all blobs for an object in traversal (DFS) order."""
        for name, fmt, _, pack in obj.fields:
            if not pack:
                continue

            # internal function so that we can recursively investigate arrays
            # and tables.
            def search(fmt, val):
                if fmt[0] == cls._blob:
                    yield val
                elif fmt[0] == cls._array:
                    for v in val:
                        yield from search(fmt[1], v)
                elif fmt[0] == cls._table:
                    for _, v in val.items():
                        yield from search(fmt[2], v)
                elif fmt[0] == cls._struct or fmt[0] == cls._union:
                    yield from cls.find_blobs(val)

            yield from search(fmt, getattr(obj, name))
