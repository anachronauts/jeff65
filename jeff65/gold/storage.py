# jeff65 gold-syntax storage classes
# Copyright (C) 2018  jeff65 maintainers
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

from ..pattern import Predicate


class AbsoluteStorage:
    def __init__(self, address, width):
        self.address = address
        self.width = width

    def __repr__(self):
        return "<{} bytes at ${:x}>".format(self.width, self.address)

    def _to_predicate(self, a):
        pa = a.make_predicate(self.address)
        pw = a.make_predicate(self.width)

        def _storage_predicate(s, c):
            return (pa._match(s.address, c)
                    and pw._match(s.width, c))
        return Predicate(None, _storage_predicate)


class ImmediateStorage:
    def __init__(self, value, width):
        self.value = value
        self.width = width

    def __repr__(self):
        return "<immediate {} bytes = ${:x}>".format(self.width, self.value)

    def _to_predicate(self, a):
        pv = a.make_predicate(self.value)
        pw = a.make_predicate(self.width)

        def _storage_predicate(s, c):
            return (pv._match(s.value, c)
                    and pw._match(s.width, c))
        return Predicate(None, _storage_predicate)
