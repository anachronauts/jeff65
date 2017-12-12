# jeff65 gold-syntax lexer
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

from . import ast


known_words = {
    # arithmetic operators
    '+': ast.OperatorAddNode,
    '-': ast.OperatorSubtractNode,
    '*': ast.OperatorMultiplyNode,
    '/': ast.OperatorDivideNode,

    # logical operators
    'not': NotImplemented,
    'and': NotImplemented,
    'or': NotImplemented,

    # bitwise operators
    '>>': NotImplemented,
    '<<': NotImplemented,
    'bitand': NotImplemented,
    'bitor': NotImplemented,
    'bitxor': NotImplemented,

    # comparison operators
    '!=': NotImplemented,
    '==': NotImplemented,
    '<=': NotImplemented,
    '>=': NotImplemented,
    '<': NotImplemented,
    '>': NotImplemented,

    # assignment operators
    '=': ast.OperatorAssignNode,
    '+=': NotImplemented,
    '-=': NotImplemented,

    # statement leaders
    'constant': ast.StatementConstantNode,
    'for': NotImplemented,
    'fun': ast.StatementFunNode,
    'if': NotImplemented,
    'isr': NotImplemented,
    'let': ast.StatementLetNode,
    'return': ast.StatementReturnNode,
    'use': ast.StatementUseNode,
    'while': NotImplemented,

    # storage classes
    'mut': ast.StorageClassNode,
    'stash': ast.StorageClassNode,

    # assorted punctuation
    'do': NotImplemented,
    'else': NotImplemented,
    'elseif': NotImplemented,
    'end': NotImplemented,
    'endfun': ast.PunctuationEndFunNode,
    'endisr': NotImplemented,
    'in': NotImplemented,
    'then': NotImplemented,
    'to': ast.OperatorRangeNode,
    ':': ast.PunctuationValueTypeNode,
    ';': ast.PunctuationArrayRangeNode,
    ',': ast.PunctuationCommaNode,
    '.': NotImplemented,
    '->': ast.PunctuationReturnTypeNode,

    # delimiters
    '"': ast.StringNode,
    '--[[': ast.CommentNode,
    ']]': ast.CommentEndNode,
    '[': ast.DelimiterOpenBracketNode,
    ']': ast.DelimiterCloseBracketNode,
    '{': NotImplemented,
    '}': NotImplemented,
}

nestable_delimiters = {
    '(': ast.DelimiterOpenParenNode,
    ')': ast.DelimiterCloseParenNode,
}

# non-whitespace characters which can end words.
specials = '()[]{}:;.,"\\@'


class Redo:
    def __init__(self, source):
        self.source = source
        self.current = None
        self.last = None

    def __iter__(self):
        return self

    def __next__(self):
        if self.last is None:
            self.current = next(self.source)
        else:
            self.current = self.last
            self.last = None
        return self.current

    def redo(self):
        self.last = self.current

    def peek(self):
        if self.last is None:
            next(self)
            self.redo()
        return self.last


def annotate_chars(stream):
    line = 1
    column = 0
    while True:
        c = stream.read(1)
        if len(c) == 0:
            break
        yield (c, (line, column))
        if c == '\n':
            line += 1
            column = 0
        else:
            column += 1


def _scan(source, c, cond):
    run = [c]
    while True:
        try:
            c, _ = next(source)
        except StopIteration:
            break
        run.append(c)
        if not cond(c, "".join(run)):
            source.redo()
            run.pop()
            break
    return "".join(run)


def scan_whitespace(source, c):
    return _scan(source, c, lambda v, _: v.isspace())


def scan_numeric(source, c):
    return _scan(source, c,
                 lambda v, _: not v.isspace() and v not in specials)


def scan_word(source, c):
    return _scan(source, c,
                 lambda v, _: not v.isspace() and v not in specials)


def scan_sprinkle(source, c):
    return _scan(source, c, lambda v, _: not v.isspace() and not v.isalnum())


def make_token(position, term, default=ast.MysteryNode):
    if term in known_words:
        cls = known_words[term]
        if cls is NotImplemented:
            cls = ast.MysteryNode
    elif term in nestable_delimiters:
        cls = nestable_delimiters[term]
        if cls is NotImplemented:
            cls = ast.MysteryNode
    else:
        cls = default
    return cls(position, term)


def lex(stream):
    source = Redo(annotate_chars(stream))
    yield ast.UnitNode()
    while True:
        try:
            c, position = next(source)
        except StopIteration:
            break

        # whitespace
        if c.isspace():
            yield ast.WhitespaceNode(position, scan_whitespace(source, c))

        # numeric
        elif c.isdigit():
            yield ast.NumericNode(position, scan_numeric(source, c))

        # word or identifier
        elif c.isalpha():
            yield make_token(
                position, scan_word(source, c), ast.IdentifierNode)

        # nestable delimiters (parentheses)
        elif c in nestable_delimiters:
            yield make_token(position, c)

        # non-alphanumeric word (mostly operators)
        # we call these "sprinkles"
        else:
            yield make_token(position, scan_sprinkle(source, c))

    # end-of-file
    yield ast.EofNode()
