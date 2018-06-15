# jeff65 type system
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

import struct
from .fmt import Fmt


# We'll make this empty for now, and use it in class definitions, then mutate
# it at the end of the file, causing classes to "suddenly" know about the other
# classes.
known = []
fmt_type_info = Fmt.union(known)


class PhantomType:
    """An unreferenceable type."""

    discriminator = Fmt.make_cc('Ph')
    fields = []

    def __repr__(self):
        return '???'

    def __eq__(self, other):
        return isinstance(other, PhantomType)

    def validate(self):
        pass

    @classmethod
    def _empty(cls):
        return cls()


class VoidType:
    """A type with no values."""

    discriminator = Fmt.make_cc('Vd')
    fields = []

    def __repr__(self):
        return 'void'

    def __eq__(self, other):
        return isinstance(other, VoidType)

    def validate(self):
        pass

    @classmethod
    def _empty(cls):
        return cls()


class IntType:
    """An integral type."""

    discriminator = Fmt.make_cc('In')
    fields = [
        ('width', Fmt.u8, Fmt.make_cc('wd'), True),
        ('signed', Fmt.bool, Fmt.make_cc('sg'), True),
    ]

    def __init__(self, width, signed):
        self.width = width
        self.signed = signed

    def can_assign_from(self, rtype):
        return (type(rtype) is IntType
                and self.signed == rtype.signed
                and self.width >= rtype.width)

    def encode(self, value):
        if self.signed:
            return struct.pack('<q', value)
        return struct.pack('<Q', value)

    def decode(self, data):
        if self.signed:
            val, = struct.unpack('<q', data)
        else:
            val, = struct.unpack('<Q', data)
        assert val in self, "{} not in range for {}".format(val, repr(self))
        return val

    def __contains__(self, value):
        if not isinstance(value, int):
            return False

        bits = self.width * 8
        if self.signed:
            upper = (1 << (bits - 1))
            lower = -upper
        else:
            upper = (1 << bits)
            lower = 0
        return lower <= value < upper

    def __eq__(self, other):
        return (type(other) is IntType
                and self.signed == other.signed
                and self.width == other.width)

    def __repr__(self):
        return "{}{}".format(
            'i' if self.signed else 'u',
            self.width * 8)

    def validate(self):
        assert isinstance(self.width, int)
        assert self.width in i8
        assert isinstance(self.signed, bool)

    @classmethod
    def _empty(cls):
        return cls(None, None)


class RefType:
    """A reference type."""

    discriminator = Fmt.make_cc('Rf')
    fields = [
        ('target', fmt_type_info, Fmt.make_cc('tg'), True),
    ]

    def __init__(self, target):
        self.target = target
        self.width = 2

    def encode(self, value):
        return struct.pack('<H6x', value)

    def decode(self, data):
        val, = struct.unpack('<H6x', data)
        return val

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
        return "&{}".format(repr(self.target))

    def validate(self):
        assert self.target is not None
        assert self.width == 2

    @classmethod
    def _empty(cls):
        return cls(None)


class FunctionType:
    """A function type."""

    discriminator = Fmt.make_cc('Fn')
    fields = [
        ('ret', fmt_type_info, Fmt.make_cc('rt'), True),
        ('args', Fmt.array(fmt_type_info), Fmt.make_cc('as'), True),
    ]

    def __init__(self, ret, *args):
        self.ret = ret
        self.args = list(args)
        self.width = None

    def can_assign_from(self, rtype):
        return self == rtype

    def __eq__(self, other):
        return (
            isinstance(other, FunctionType)
            and self.ret == other.ret
            and self.args == other.args)

    def __repr__(self):
        args = ", ".join(repr(arg) for arg in self.args)
        ret = ""
        if not isinstance(self.ret, VoidType):
            ret = " -> {}".format(repr(self.ret))
        return "fun({}){}".format(args, ret)

    def validate(self):
        assert self.ret is not None
        assert self.args is not None
        assert self.width is None

    @classmethod
    def _empty(cls):
        obj = cls(None)
        obj.args = None
        return obj


u8 = IntType(1, signed=False)
u16 = IntType(2, signed=False)
u24 = IntType(3, signed=False)
u32 = IntType(4, signed=False)
i8 = IntType(1, signed=True)
i16 = IntType(2, signed=True)
i24 = IntType(3, signed=True)
i32 = IntType(4, signed=True)
void = VoidType()
phantom = PhantomType()
ptr = RefType(phantom)

# Because we mutate this list, everywhere that uses it now knows about these
# types.
known.extend([
    PhantomType,
    VoidType,
    IntType,
    RefType,
    FunctionType,
])
