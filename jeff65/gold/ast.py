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
    delimiter_endfun = auto()
    delimiter_close = auto()
    statement = auto()
    storage_class = auto()
    term = auto()
    operator_assign = auto()
    punctuation_array_range = auto()
    punctuation_comma = auto()
    operator_range = auto()
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
    delimiter_open = auto()
    punctuation_return_type = auto()
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


class AstNode:
    def __init__(self, position, text):
        self.position = position
        self.text = text
        self.children = None

    def traverse(self, visit):
        for k in range(len(self.children)):
            self.children[k] = self.children[k].traverse(visit)
        return visit(self)


class TokenNode(AstNode):
    def __init__(self, lbp, position, text, right=False, end=False):
        super().__init__(position, text)
        self.lbp = lbp
        self.right = right
        self.end = end

    def nud(self, right):
        msg = (f"nud not implemented for {str(type(self))}"
               f" ('{repr(self)}' at {self.position})")
        raise NotImplementedError(msg)

    def led(self, left, right):
        msg = (f"led not implemented for {str(type(self))}"
               f" ('{repr(self)}' at {self.position})")
        raise NotImplementedError(msg)

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


class InfixNode(TokenNode):
    def led(self, left, right):
        self.children = [left, self.parse(right)]
        return self

    @property
    def lhs(self):
        return self.children[0]

    @property
    def rhs(self):
        return self.children[1]

    def describe(self):
        if self.children is None:
            return None
        if len(self.children) == 1:
            return f"({self.text} {self.children[0]})"
        return f"({self.children[0]} {self.text} {self.children[1]})"


class TermNode(TokenNode):
    def __init__(self, position, text):
        super().__init__(Power.term, position, text)

    def nud(self, right):
        self.children = []
        return self

    def describe(self):
        return self.text


class PrefixNode(TokenNode):
    def nud(self, right):
        self.children = [self.parse(right)]
        return self

    @property
    def rhs(self):
        return self.children[0]

    def describe(self):
        return self.children and f"({self.text} {self.children[0]})"


class UnitNode(TokenNode):
    def __init__(self):
        super().__init__(Power.unit, None, "UNIT")

    def nud(self, right):
        self.children = []
        while right.current.lbp > self.rbp:
            self.children.append(self.parse(right, Power.statement))
        self.children = [s for s in self.children if type(s) is not EofNode]
        return self

    @property
    def statements(self):
        return self.children

    def describe(self):
        if self.children is None:
            return "<UNIT>"
        lines = "\n".join(repr(s) for s in self.children)
        return lines


class WhitespaceNode(TokenNode):
    def __init__(self, position, text):
        super().__init__(Power.whitespace, position, text)

    def nud(self, right):
        return self.parse(right)

    def led(self, left, right):
        return left


class EofNode(TokenNode):
    def __init__(self):
        super().__init__(Power.eof, None, "EOF", end=True)

    def describe(self):
        return "<EOF>"


class NumericNode(TermNode):
    pass


class StringNode(TermNode):
    def __init__(self, position, text):
        super().__init__(position, text)
        self.string = None

    def eat_string(self, right):
        spans = []
        escaped = False
        while True:
            if type(right.current) is StringNode and not escaped:
                right.next()
                break
            if right.current.text == "\\":
                escaped = True
            spans.append(right.current.text)
            right.next()
        return "".join(spans)

    def nud(self, right):
        self.string = self.eat_string(right)
        return self

    def describe(self):
        return f'"{self.string}"'


class DelimiterOpenParenNode(TokenNode):
    def __init__(self, position, text):
        super().__init__(Power.delimiter_open, position, text)

    def nud(self, right):
        expression = self.parse(right, Power.delimiter_close)
        if type(right.current) is not DelimiterCloseParenNode:
            raise ParseError("unmatched open parentheses", self)
        right.next()
        return expression

    def led(self, left, right):
        if type(right.current) is DelimiterCloseParenNode:
            args = None
        else:
            args = self.parse(right, Power.delimiter_close)

        if type(right.current) is not DelimiterCloseParenNode:
            raise ParseError("expected ')'", self)
        right.next()

        return FunctionCallNode(self.position, self.text, left, args)


class FunctionCallNode(AstNode):
    def __init__(self, position, text, fun, args):
        super().__init__(position, text)
        self.children = [fun, args]

    @property
    def fun(self):
        return self.children[0]

    @property
    def args(self):
        return self.children[1]

    def __repr__(self):
        if self.args is None:
            return f"{self.fun}()"
        return f"{self.fun}{self.args}"


class DelimiterCloseParenNode(TokenNode):
    def __init__(self, position, text):
        super().__init__(Power.delimiter_close, position, text)

    def nud(self, right):
        raise ParseError("unmatched close parentheses", self)

    def led(self, left, right):
        raise ParseError("unmatched close parentheses", self)


class DelimiterOpenBracketNode(TokenNode):
    def __init__(self, position, text):
        super().__init__(Power.delimiter_open, position, text)

    def nud(self, right):
        contents = self.parse(right, Power.delimiter_close)
        if type(right.current) is not DelimiterCloseBracketNode:
            raise ParseError("unmatched open bracket", self)
        right.next()
        return BracketsNode(self.position, contents)


class DelimiterCloseBracketNode(TokenNode):
    def __init__(self, position, text):
        super().__init__(Power.delimiter_close, position, text)

    def nud(self, right):
        raise ParseError("unmatched close bracket", self)

    def led(self, left, right):
        raise ParseError("unmatched close bracket", self)


class BracketsNode(AstNode):
    def __init__(self, position, contents):
        super().__init__(position, None)
        self.children = [contents]

    @property
    def contents(self):
        return self.children[0]

    def __repr__(self):
        return f"[{self.contents}]"


class OperatorAddNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_add_subtract, position, text)

    def nud(self, right):
        """ unary plus """
        self.children = [self.parse(right, Power.operator_sign)]
        return self


class OperatorSubtractNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_add_subtract, position, text)

    def nud(self, right):
        """ unary minus """
        self.children = [self.parse(right, Power.operator_sign)]
        return self


class OperatorMultiplyNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_multiply_divide, position, text)


class OperatorDivideNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_multiply_divide, position, text)


class PunctuationCommaNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.punctuation_comma, position, text, right=True)


class IdentifierNode(TermNode):
    def __init__(self, position, text):
        super().__init__(position, text)
        self.member_index = None

    def nud(self, right):
        super().nud(right)
        if type(right.current) == DelimiterOpenBracketNode:
            self.member_index = self.parse(right, Power.delimiter_open)
        return self

    def led(self, left, right):
        super().led(left, right)
        if type(right.current) == DelimiterOpenBracketNode:
            self.member_index = self.parse(right, Power.delimiter_open)
        return self

    def describe(self):
        if self.member_index is None:
            return super().describe()
        else:
            return super().describe() + repr(self.member_index)



class StorageClassNode(PrefixNode):
    def __init__(self, position, text):
        super().__init__(Power.storage_class, position, text)

    @property
    def binding(self):
        return self.rhs


class OperatorEqualsNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_compare, position, text)


class OperatorNotEqualsNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_compare, position, text)


class OperatorLessThanNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_compare, position, text)


class OperatorGreaterThanNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_compare, position, text)


class OperatorLessThanOrEqualNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_compare, position, text)


class OperatorGreaterThanOrEqualNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_compare, position, text)


class OperatorAssignNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_assign, position, text)


class OperatorIncrementNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_assign, position, text)

    def led(self, left, right):
        r = OperatorAddNode(self.position, "+")
        r.children = [left, self.parse(right)]
        node = OperatorAssignNode(self.position, "=")
        node.children = [left, r]
        return node


class OperatorDecrementNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_assign, position, text)

    def led(self, left, right):
        r = OperatorSubtractNode(self.position, "-")
        r.children = [left, self.parse(right)]
        node = OperatorAssignNode(self.position, "=")
        node.children = [left, r]
        return node


class OperatorRangeNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.operator_range, position, text)


class MysteryNode(TokenNode):
    def __init__(self, position, text):
        super().__init__(Power.mystery, position, text)

    def describe(self):
        return f"<{repr(self.text)}?>"


class PunctuationValueTypeNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.punctuation_value_type, position, text)


class PunctuationArrayRangeNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.punctuation_array_range, position, text)


class PunctuationReturnTypeNode(InfixNode):
    def __init__(self, position, text):
        super().__init__(Power.punctuation_return_type, position, text)


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
        return self.comment and f"/*{self.comment}*/"


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


class StatementReturnNode(TokenNode):
    def __init__(self, position, text):
        super().__init__(Power.statement, position, text)

    def nud(self, right):
        if type(right.current) is WhitespaceNode:
            right.next()  # manually eat whitespace
        if right.current.end:
            self.children = []
        else:
            self.children = [self.parse(right)]
        return self

    @property
    def rhs(self):
        if len(self.children) == 0:
            return None
        return self.children[0]

    def describe(self):
        return self.children and f"({self.text} {self.children[0]})"


class PunctuationDoNode(TokenNode):
    def __init__(self, position, text):
        super().__init__(Power.statement, position, text, end=True)

    def nud(self, right):
        raise ParseError(f"unexpected '{self.text}'", self)

    def led(self, left, right):
        raise ParseError(f"unexpected '{self.text}'", self)


class PunctuationEndNode(TokenNode):
    def __init__(self, position, text):
        super().__init__(Power.delimiter_endfun, position, text, end=True)

    def nud(self, right):
        raise ParseError(f"unexpected '{self.text}'", self)

    def led(self, left, right):
        raise ParseError(f"unexpected '{self.text}'", self)


class StatementFunNode(TokenNode):
    def __init__(self, position, text):
        super().__init__(Power.statement, position, text)
        self.signature = None

    def nud(self, right):
        self.signature = self.parse(right)
        self.children = []
        while type(right.current) is not PunctuationEndFunNode:
            self.children.append(self.parse(right))
        right.next()
        return self

    def traverse(self, visit):
        self.signature = self.signature.traverse(visit)
        return super().traverse(visit)

    def describe(self):
        if self.signature is None:
            return None
        stmts = "\n    ".join(repr(c) for c in self.children)
        return self.signature and f"(fun {self.signature}\n    {stmts})"


class PunctuationEndFunNode(PunctuationEndNode):
    pass


class StatementIsrNode(TokenNode):
    def __init__(self, position, text):
        super().__init__(Power.statement, position, text)
        self.name = None

    def nud(self, right):
        self.name = self.parse(right)
        self.children = []
        while type(right.current) is not PunctuationEndIsrNode:
            self.children.append(self.parse(right))
        right.next()
        return self

    def describe(self):
        if self.name is None:
            return None
        stmts = "\n    ".join(repr(c) for c in self.children)
        return f"(isr {repr(self.name)}\n    {stmts})"


class PunctuationEndIsrNode(PunctuationEndNode):
    pass


class StatementWhileNode(TokenNode):
    def __init__(self, position, text):
        super().__init__(Power.statement, position, text)
        self.condition = None

    def nud(self, right):
        self.condition = self.parse(right)
        if type(right.current) is not PunctuationDoNode:
            raise ParseError(f"expected 'do' but found '{right.current.text}'",
                             right.current)
        right.next()
        self.children = []
        while type(right.current) is not PunctuationEndNode:
            if type(right.current) is EofNode:
                raise ParseError(f"unterminated while loop", self)
            self.children.append(self.parse(right))
        right.next()
        return self

    def traverse(self, visit):
        self.condition = self.condition.traverse(visit)
        return super().traverse(visit)

    def describe(self):
        if self.condition is None:
            return None
        stmts = "\n    ".join(repr(c) for c in self.children)
        return self.condition and f"(while {self.condition}\n    {stmts})"
