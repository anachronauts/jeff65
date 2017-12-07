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
    'bitand': NotImplemented,
    'bitor': NotImplemented,
    'bitxor': NotImplemented,

    # bitwise operators
    '>>': NotImplemented,
    '<<': NotImplemented,

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

    # reserved for possible line comment
    '--': NotImplemented,

    # assorted punctuation
    ':': ast.PunctuationValueTypeNode,
    ',': ast.PunctuationCommaNode,
    '.': NotImplemented,
    '->': NotImplemented,

    # statement leaders
    'constant': ast.StatementConstantNode,
    'for': NotImplemented,
    'if': NotImplemented,
    'isr': NotImplemented,
    'let': ast.StatementLetNode,
    'return': NotImplemented,
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
    'endfun': NotImplemented,
    'endisr': NotImplemented,
    'in': NotImplemented,
    'then': NotImplemented,
    'to': NotImplemented,
}

delimiters = {
    '(': NotImplemented,
    ')': NotImplemented,
    '[': NotImplemented,
    ']': NotImplemented,
    '{': NotImplemented,
    '}': NotImplemented,
    "\"": NotImplemented,
    '--[[': NotImplemented,
    '--]]': NotImplemented,
}

# non-whitespace characters which can end words.
specials = "()[]{}:.,\"\\"


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


def scanWhitespace(source, c):
    return _scan(source, c, lambda v, _: v.isspace())


def scanNumeric(source, c):
    # TODO: actually make sure its a valid number
    return _scan(source, c, lambda v, _: not v.isspace() and v not in specials)


def scanWord(source, c):
    return _scan(source, c, lambda v, _: not v.isspace() and v not in specials)


def valid_identifier(word):
    # TODO
    return True


def lex(stream):
    source = Redo(annotate_chars(stream))
    yield ast.UnitNode()
    while True:
        try:
            c, position = next(source)
        except StopIteration:
            break
        if c in specials:
            # TODO
            yield ast.MysteryNode(position, c)
        elif c.isspace():
            ws = scanWhitespace(source, c)
            yield ast.WhitespaceNode(position, ws)
        elif c.isdigit():
            num = scanNumeric(source, c)
            yield ast.NumericNode(position, num)
        else:
            word = scanWord(source, c)
            if word in known_words:
                cls = known_words[word]
                if cls is NotImplemented:
                    yield ast.MysteryNode(position, word)
                else:
                    yield cls(position, word)
            elif valid_identifier(word):
                yield ast.IdentifierNode(position, word)
            else:
                yield ast.MysteryNode(position, word)
    yield ast.EofNode()
