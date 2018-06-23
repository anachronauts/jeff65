# jeff65 gold-syntax unit resolution
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


class ExternalUnit:
    """Represents an external unit."""

    def __init__(self, source):
        self.source = source

    def member(self, name):
        """Gets a member of a unit by name."""
        pass

    def __repr__(self):
        return "ExternalUnit({})".format(repr(self.source))


class UnitSymbol:
    """Represents a symbol exported from a unit."""

    def __init__(self, name, unit, t, is_intrinsic=False):
        self.name = name
        self.unit = unit
        self.type = t
        self.is_intrinsic = is_intrinsic

    def __repr__(self):
        return "<{} {}.{}: {}>".format(
            type(self).__name__, self.unit, self.name, self.type)


class IntrinsicSymbol(UnitSymbol):
    """Represents a compiler intrinsic symbol.

    Compiler intrinsic symbols receive their arguments as AST subtrees at
    translation time, and output a new AST subtree based on them. Intrinsics
    are provided by virtual units.
    """

    def __init__(self, name, unit, t, impl):
        super().__init__(name, unit, t, is_intrinsic=True)
        self.impl = impl

    def __call__(self, *args):
        return self.impl(*args)


def member_type(t):
    def add_to_fun(fun):
        fun.intrinsic_type = t
        return fun

    return add_to_fun
