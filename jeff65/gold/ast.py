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
    storage_class = auto()
    term = auto()
    operator_assign = auto()
    punctuation_comma = auto()
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
    mystery = auto()


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
        raise NotImplementedError

    def led(self, left, right):
        raise NotImplementedError

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

    def traverse(self, visit):
        raise NotImplementedError


class InfixNode(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lhs = None
        self.rhs = None

    def led(self, left, right):
        self.lhs = left
        self.rhs = self.parse(right)
        return self

    def describe(self):
        return self.lhs and f"({self.lhs} {self.text} {self.rhs})"

    def traverse(self, visit):
        self.lhs = self.lhs.traverse(visit)
        self.rhs = self.rhs.traverse(visit)
        return visit(self)


class TermNode(Node):
    def __init__(self, position, text):
        super().__init__(Power.term, position, text)

    def nud(self, right):
        return self

    def describe(self):
        return self.text

    def traverse(self, visit):
        return visit(self)


class PrefixNode(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rhs = None

    def nud(self, right):
        self.rhs = self.parse(right)
        return self

    def describe(self):
        return self.rhs and f"({self.text} {self.rhs})"

    def traverse(self, visit):
        self.rhs = self.rhs.traverse(visit)
        return visit(self)


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

    def traverse(self, visit):
        for k in range(len(self.statements)):
            self.statements[k] = self.statements[k].traverse(visit)
        return visit(self)


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


class NumericNode(TermNode):
    pass


class StringNode(TermNode):
    pass


class OperatorAddNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_add_subtract, position, text)

    def nud(self, right):
        """ unary plus """
        self.lhs = self.parse(right, Power.operator_sign)
        return self


class OperatorSubtractNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_add_subtract, position, text)

    def nud(self, right):
        """ unary minus """
        self.lhs = self.parse(right, Power.operator_sign)
        return self


class OperatorMultiplyNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_multiply_divide, position, text)


class OperatorDivideNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_multiply_divide, position, text)


class PunctuationCommaNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.punctuation_comma, position, text)


class IdentifierNode(TermNode):
    pass


class StorageClassNode(PrefixNode):
    def __init__(self, position, text):
        super().__init__(Power.storage_class, position, text)

    @property
    def binding(self):
        return self.rhs


class OperatorAssignNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_assign, position, text)


class MysteryNode(Node):
    def __init__(self, position, text):
        super().__init__(Power.mystery, position, text)

    def describe(self):
        return f"<{repr(self.text)}?>"


class PunctuationValueTypeNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.punctuation_value_type, position, text)


class CommentNode(WhitespaceNode):
    def describe(self):
        return self.text


class StatementUseNode(PrefixNode):
    def __init__(self, position, text):
        super().__init__(Power.statement, position, text)

    @property
    def unit(self):
        return self.rhs


class StatementConstantNode(PrefixNode):
    def __init__(self, position, text):
        super().__init__(Power.statement, position, text)

    @property
    def binding(self):
        return self.rhs


class StatementLetNode(PrefixNode):
    def __init__(self, position, text):
        super().__init__(Power.statement, position, text)

    @property
    def binding(self):
        return self.rhs
