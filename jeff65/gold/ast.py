# jeff65 gold-syntax parser
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

from enum import IntEnum, auto

# see http://effbot.org/zone/simple-top-down-parsing.htm
#
# - "nud" means "null denotation", which defines its behavior at the beginning
#   of a language construct.
# - "led" means "left denotation", which defines its behavior inside a language
#   construct.
# - "lbp" means "left binding power", which controls precedence.


class Power(IntEnum):
    def _generate_next_value_(name, start, count, last_values):
        return count * 10

    eof = auto()
    operator_or = auto()
    operator_and = auto()
    operator_not = auto()
    operator_compare = auto()
    operator_add_subtract = auto()
    operator_multiply_divide = auto()
    operator_bitshift = auto()
    operator_bitxor = auto()
    operator_bitor = auto()
    operator_bitand = auto()
    operator_bitnot = auto()
    operator_sign = auto()
    whitespace = auto()


class MemIter:
    def __init__(self, source):
        self.source = iter(source)
        self.current = next(self.source)

    def next(self):
        self.current = next(self.source)


def parse_all(stream):
    s = MemIter(stream)
    return _parse(s, 0)


def _parse(stream, rbp):
    t = stream.current
    stream.next()
    left = t.nud(stream)
    while rbp < stream.current.lbp:
        t = stream.current
        stream.next()
        left = t.led(left, stream)
    return left


class Node:
    def __init__(self, lbp, position, text, right=False):
        self.lbp = lbp
        self.position = position
        self.text = text
        self.right = right

    def nud(self, right):
        return NotImplemented

    def led(self, left, right):
        return NotImplemented

    @property
    def rbp(self):
        if self.right:
            return self.lbp - 1
        return self.lbp

    def parse(self, right, rbp=None):
        return _parse(right, rbp or self.rbp)

    def __repr__(self):
        return self.describe() or f"<{repr(self.text)}>"

    def describe(self):
        return None


class WhitespaceNode(Node):
    def __init__(self, position, text):
        super().__init__(Power.whitespace, position, text)

    def nud(self, right):
        return self.parse(right)

    def led(self, left, right):
        return left


class EofNode(Node):
    def __init__(self):
        super().__init__(Power.eof, None, "EOF")


class NumericNode(Node):
    def __init__(self, position, text):
        super().__init__(None, position, text)

    def nud(self, right):
        return self

    def describe(self):
        return self.text


class StringNode(Node):
    def __init__(self, position, text):
        super().__init__(None, position, text)

    def nud(self, right):
        return self


class OperatorAddNode(Node):
    def __init__(self, position):
        super().__init__(Power.operator_add_subtract, position, "+")
        self.first = None
        self.second = None

    def nud(self, right):
        """ unary plus """
        self.first = self.parse(right, Power.operator_sign)
        self.second = None
        return self

    def led(self, left, right):
        self.first = left
        self.second = self.parse(right)
        return self

    def describe(self):
        return self.first and f"(+ {self.first} {self.second})"


class OperatorSubtractNode(Node):
    def __init__(self, position):
        super().__init__(Power.operator_add_subtract, position, "-")
        self.first = None
        self.second = None

    def nud(self, right):
        """ unary minus """
        self.first = self.parse(right, Power.operator_sign)
        self.second = None

    def led(self, left, right):
        self.first = left
        self.second = self.parse(right)
        return self

    def describe(self):
        return self.first and f"(- {self.first} {self.second})"


class OperatorMultiplyNode(Node):
    def __init__(self, position):
        super().__init__(Power.operator_multiply_divide, position, "*")
        self.first = None
        self.second = None

    def led(self, left, right):
        self.first = left
        self.second = self.parse(right)
        return self

    def describe(self):
        return self.first and f"(* {self.first} {self.second})"


class OperatorDivideNode(Node):
    def __init__(self, position):
        super().__init__(Power.operator_multiply_divide, position, "/")
        self.first = None
        self.second = None

    def led(self, left, right):
        self.first = left
        self.second = self.parse(right)
        return self

    def describe(self):
        return self.first and f"(/ {self.first} {self.second})"
