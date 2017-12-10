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
    try:
        stream.next()
    except StopIteration:
        return t
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


class TermNode(Node):
    def __init__(self, position, text):
        super().__init__(Power.term, position, text)

    def nud(self, right):
        return self

    def describe(self):
        return self.text


class PrefixNode(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rhs = None

    def nud(self, right):
        self.rhs = self.parse(right)
        return self

    def describe(self):
        return self.rhs and f"({self.text} {self.rhs})"


class UnitNode(Node):
    def __init__(self):
        super().__init__(Power.unit, None, "UNIT")
        self.statements = None

    def nud(self, right):
        self.statements = []
        while right.current.lbp > self.rbp:
            self.statements.append(self.parse(right, Power.statement))
        self.statements = [s for s in self.statements if type(s) is not EofNode]
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
        super().__init__(Power.eof, None, "EOF")

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
    def __init__(self, position, text):
        super().__init__(position, text)
        self.comment = None

    def eat_comment(self, right):
        spans = []
        depth = 1
        while depth > 0:
            # the depth counter is so that we can have nested comments
            if type(right.current) is CommentNode:
                depth += 1
            elif type(right.current) is CommentEndNode:
                depth -= 1
            spans.append(right.current.text)
            right.next()
        # return all of the text except the last "]]"
        return "".join(spans[:-1])

    def nud(self, right):
        self.comment = self.eat_comment(right)
        return self.parse(right)

    def led(self, left, right):
        self.comment = self.eat_comment(right)
        return left

    def describe(self):
        return self.comment and f"--[[{self.comment}]]"


class CommentEndNode(WhitespaceNode):
    # this is a lexer-only node. it gets eaten during the first parse pass.
    pass


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
