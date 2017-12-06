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
    unit = auto()
    statement = auto()
    term = auto()
    storage_class = auto()
    operator_assign = auto()
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
    punctuation_value_type = auto()
    whitespace = auto()


class MemIter:
    def __init__(self, source):
        self.source = iter(source)
        self.current = next(self.source)

    def next(self):
        self.current = next(self.source)


def parse_all(stream):
    s = MemIter(stream)
    return _parse(s, Power.statement)


def _parse(stream, rbp):
    t = stream.current
    stream.next()
    left = t.nud(stream)
    if left is NotImplemented:
        raise ParseError(f"nud not implemented on {type(t)} {t}", t)
    while True:
        if stream.current.lbp is None:
            raise ParseError(
                f"token type {type(stream.current)} is non-binding",
                stream.current)
        if rbp >= stream.current.lbp:
            break
        t = stream.current
        stream.next()
        left = t.led(left, stream)
        if left is NotImplemented:
            raise ParseError(f"led not implemented on {type(t)} {t}", t)
    return left


class ParseError(Exception):
    def __init__(self, message, token):
        super().__init__(message)
        self.token = token

    def __str__(self):
        msg = super().__str__()
        return f"{msg} (at {self.token.position})"


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

    def transmute(self, other):
        return other(self.position, self.text)


class UnitNode(Node):
    def __init__(self):
        super().__init__(Power.unit, None, "UNIT")
        self.statements = None

    def nud(self, right):
        self.statements = []
        while right.current.lbp > self.rbp:
            self.statements.append(self.parse(right, Power.statement))
            print(self.statements[-1])
        return self

    def describe(self):
        if self.statements is None:
            return "<UNIT>"
        lines = "\n".join(repr(s) for s in self.statements)
        return lines


class WhitespaceNode(Node):
    def __init__(self, position, text):
        super().__init__(Power.whitespace, position, text)

    def nud(self, right):
        return self.parse(right)

    def led(self, left, right):
        return left


class EofNode(Node):
    def __init__(self):
        # putting a newline in the text field allows this token to terminate
        # line-comments naturally, instead of special-casing the token in the
        # comment code.
        super().__init__(Power.eof, None, "EOF\n")

    def describe(self):
        return "<EOF>"


class NumericNode(Node):
    def __init__(self, position, text):
        super().__init__(Power.term, position, text)

    def nud(self, right):
        return self

    def describe(self):
        return self.text


class StringNode(Node):
    def __init__(self, position, text):
        super().__init__(Power.term, position, text)

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
        return self

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


class IdentifierNode(Node):
    def __init__(self, position, text):
        super().__init__(Power.term, position, text)

    def nud(self, right):
        return self

    def describe(self):
        return self.text


class StorageClassNode(Node):
    def __init__(self, position, text):
        super().__init__(Power.storage_class, position, text)

    def describe(self):
        return self.text


class OperatorAssignNode(Node):
    def __init__(self, position):
        super().__init__(Power.operator_assign, position, "=")
        self.lvalue = None
        self.rvalue = None

    def led(self, left, right):
        self.lvalue = left
        self.rvalue = self.parse(right)
        return self

    def describe(self):
        return self.lvalue and f"({self.lvalue} = {self.rvalue})"


class MysteryNode(Node):
    def __init__(self, position, text):
        super().__init__(-1000, position, text)


class PunctuationValueTypeNode(Node):
    def __init__(self, position):
        super().__init__(Power.punctuation_value_type, position, ":")
        self.name = None
        self.type = None

    def led(self, left, right):
        self.name = left
        self.type = self.parse(right)
        return self

    def describe(self):
        return self.name and f"({self.name} : {self.type})"


class CommentNode(Node):
    def __init__(self, position):
        super().__init__(Power.statement, position, "--")
        self.comment = None

    def nud(self, right):
        # TODO maybe implement this in the lexer instead
        spans = []
        while '\n' not in right.current.text:
            spans.append(right.current.text)
            right.next()
        self.comment = "".join(spans).strip()
        return self

    def describe(self):
        return self.comment and f"-- {self.comment}"


class StatementUseNode(Node):
    def __init__(self, position):
        super().__init__(Power.statement, position, "use")
        self.unit = None

    def nud(self, right):
        self.unit = self.parse(right)
        return self

    def describe(self):
        return self.unit and f"(use {self.unit})"


class StatementConstantNode(Node):
    def __init__(self, position):
        super().__init__(Power.statement, position, "constant")
        self.binding = None

    def nud(self, right):
        self.binding = self.parse(right)
        return self

    def describe(self):
        return self.binding and f"(constant {self.binding})"


class StatementLetNode(Node):
    def __init__(self, position):
        super().__init__(Power.statement, position, "let")
        self.storage = None
        self.binding = None

    def nud(self, right):
        self.storage = self.parse(right, Power.storage_class - 1)
        self.binding = self.parse(right)
        return self

    def describe(self):
        return self.storage and f"(let {self.storage} {self.binding})"
