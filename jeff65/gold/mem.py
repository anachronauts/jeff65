# jeff65 gold-syntax 'mem' virtual unit
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

from ..blum import types
from . import units


class MemUnit(units.ExternalUnit):
    """The 'mem' virtual unit.

    This is a built-in virtual unit providing intrinsics for performing direct
    memory access.
    """

    def __init__(self):
        super().__init__("mem")
        self.members = {}
        self.add_member('as-pointer', self._as_pointer)
        self.add_member('as-address', self._as_address)

    def add_member(self, name, impl):
        self.members[name] = units.IntrinsicSymbol(
            name, self, impl.intrinsic_type, impl)

    def member(self, name):
        return self.members[name]

    @units.member_type(types.FunctionType(types.ptr, types.u16))
    def _as_pointer(self, arg):
        # All this does is pass the result back out again -- it's just to get
        # around the type checker.
        return arg

    @units.member_type(types.FunctionType(types.u16, types.ptr))
    def _as_address(self, arg):
        # All this does is pass the result back out again -- it's just to get
        # around the type checker.
        return arg

    def __repr__(self):
        return "MemUnit()"
