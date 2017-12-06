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


sprinkles = {
    # arithmetic operators
    '+': ast.OperatorAddNode,
    '-': ast.OperatorSubtractNode,
    '*': ast.OperatorMultiplyNode,
    '/': ast.OperatorDivideNode,

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

    # comment statement
    '--': ast.CommentNode,

    # assorted punctuation
    ':': ast.PunctuationValueTypeNode,
    ',': NotImplemented,
    '.': NotImplemented,
    '->': NotImplemented,
}

delimiters = {
    '(': NotImplemented,
    ')': NotImplemented,
    '[': NotImplemented,
    ']': NotImplemented,
    '{': NotImplemented,
    '}': NotImplemented,
}

sprinkle_chars = set("".join(sprinkles.keys()))

# non-whitespace characters which can end words.
specials = "()[]{}:.,\"\\"

keywords = {
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


def scan(source, c, cond):
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


def lex(stream):
    source = Redo(annotate_chars(stream))
    yield ast.UnitNode()
    while True:
        try:
            c, position = next(source)
        except StopIteration:
            break
        if c.isspace():
            ws = scan(source, c, lambda v, _: v.isspace())
            yield ast.WhitespaceNode(position, ws)
        elif c.isdigit():
            num = scan(source, c,
                       lambda v, _: not v.isspace() and v not in specials)
            yield ast.NumericNode(position, num)
        elif c in sprinkle_chars:
            sprinkle = scan(source, c, lambda v, _: v in sprinkle_chars)
            if sprinkle in sprinkles:
                cls = sprinkles[sprinkle]
                if cls is NotImplemented:
                    yield ast.MysteryNode(position, sprinkle)
                else:
                    # TODO maybe pass text here after all, so that the same
                    #      token type can be used for multiple things
                    yield cls(position)
            else:
                yield ast.SprinkleNode(position, sprinkle)
        elif c.isalpha():
            word = scan(source, c,
                        lambda v, _: not v.isspace() and v not in specials)
            if word in keywords:
                cls = keywords[word]
                if cls is NotImplemented:
                    yield ast.MysteryNode(position, word)
                elif cls is ast.StorageClassNode:
                    # TODO hacky special case; see following TODO
                    yield cls(position, word)
                else:
                    # TODO maybe pass text here after all, so that the same
                    #      token type can be used for multiple things
                    yield cls(position)
            else:
                yield ast.IdentifierNode(position, word)
        else:
            yield ast.MysteryNode(position, c)
    yield ast.EofNode()
