# jeff65 gold-syntax type system
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


class IntType:
    """An integral type."""

    def __init__(self, width, signed):
        self.width = width
        self.signed = signed

    def can_assign_from(self, rtype):
        return (type(rtype) is IntType
                and self.signed == rtype.signed
                and self.width >= rtype.width)

    def __eq__(self, other):
        return (type(other) is IntType
                and self.signed == other.signed
                and self.width == other.width)

    def __repr__(self):
        return "{}{}".format(
            'i' if self.signed else 'u',
            self.width * 8)


class RefType:
    """A reference type."""

    def __init__(self, target):
        self.target = target
        self.width = 2

    def can_assign_from(self, rtype):
        # Pointer assignment has to be equal unless the rhs is a mystery
        # pointer, in which case we just allow it to go through.
        return (self == rtype or
                (type(rtype) is RefType
                 and rtype.target is None))

    def __eq__(self, other):
        return (type(other) is RefType
                and self.target == other.target)

    def __repr__(self):
        if self.target is None:
            return "&?"
        return "&{}".format(repr(self.target))


class FunctionType:
    """A function type."""

    def __init__(self, ret, *args):
        self.ret = ret
        self.args = args
        self.width = None

    def can_assign_from(self, rtype):
        return self == rtype

    def __eq__(self, other):
        return (type(other) is FunctionType
                and self.ret == other.ret
                and self.args == other.args)

    def __repr__(self):
        args = ", ".join(repr(arg) for arg in self.args)
        ret = ""
        if self.ret:
            ret = "-> {}".format(repr(self.ret))
        return "fun({}) {}".format(args, ret)


u8 = IntType(1, signed=False)
u16 = IntType(2, signed=False)
u24 = IntType(3, signed=False)
u32 = IntType(4, signed=False)
i8 = IntType(1, signed=True)
i16 = IntType(2, signed=True)
i24 = IntType(3, signed=True)
i32 = IntType(4, signed=True)
ptr = RefType(None)
