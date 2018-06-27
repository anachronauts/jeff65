# jeff65 s-expression parser
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

import io
import re
from enum import Enum, auto
import attr
from . import ast


class T(Enum):
    EOF = auto()
    SOF = auto()
    MYSTERY = auto()
    PAREN_OPEN = auto()
    PAREN_CLOSE = auto()
    ATOM = auto()
    STRING = auto()
    NUMERIC = auto()
    BOOLEAN = auto()


@attr.s(frozen=True, slots=True)
class Token:
    t = attr.ib()
    position = attr.ib(cmp=False)
    text = attr.ib()

    @classmethod
    def is_t(cls, v, *ts):
        return isinstance(v, cls) and v.t in ts


terminators = re.escape('()[]"')
str_delim = '"'
m_str_escape = re.compile(r'\\.', re.M)
m_str_delim = re.compile(re.escape(str_delim))
m_str_control = re.compile(fr'{m_str_escape.pattern}|{m_str_delim.pattern}')
m_whitespace = re.compile(r'\s+', re.M)
m_numeric = re.compile(fr'[+-]?\d[^\s{terminators}]*')
m_atom = re.compile(fr'[^\s{terminators}]+')
m_bool = re.compile(r'#[tf]')
singles = {
    '(': T.PAREN_OPEN,
    ')': T.PAREN_CLOSE,
    '[': T.PAREN_OPEN,
    ']': T.PAREN_CLOSE,
}


def lexer(stream, line=0, column=0):
    current = None
    string_value = None
    string_line = 0
    string_column = 0

    def make_token(t, text):
        return Token(t, (line, column), text)

    # our parser needs a start-of-file token for anchoring.
    yield make_token(T.SOF, '<sof>')
    while True:
        if current is None or column >= len(current):
            try:
                current = next(stream)
                line += 1
                column = 0
            except StopIteration:
                # If we're in string mode, we are NOT expecting this kind of
                # behavior and will kick up a fuss.
                # TODO: check this
                yield make_token(T.EOF, '<eof>')
                break

        # String collects a string until it's done, then emits a single STRING
        # token.
        if string_value is not None:
            m = m_str_control.search(current, column)
            if not m:
                # the rest of the line is a string
                string_value.append(current[column:])
                column = len(current)
            elif m.start() == column:
                # the string control character is right here!
                if m.group() in set(str_delim):
                    # the string has ended
                    yield Token(T.STRING, (string_line, string_column),
                                ''.join(string_value))
                    string_value = None
                else:
                    # it must be an escaped character
                    string_value.append(m.group()[1])
                column = m.end()
            else:
                # string the text before the control
                string_value.append(current[column:m.start()])
                column = m.start()
            continue
        if current[column] == '"':
            string_value = []
            string_line = line
            string_column = column
            column += 1
            continue

        # Whitespace is discarded
        m = m_whitespace.match(current, column)
        if m:
            column = m.end()
            continue
        m = m_bool.match(current, column)
        if m:
            yield make_token(T.BOOLEAN, m.group())
            column = m.end()
            continue
        # This has to be run before the word match, since the word regex
        # matches numbers as well.
        m = m_numeric.match(current, column)
        if m:
            yield make_token(T.NUMERIC, m.group())
            column = m.end()
            continue
        m = m_atom.match(current, column)
        if m:
            yield make_token(T.ATOM, m.group())
            column = m.end()
            continue
        # match the special characters. If it isn't one of those, this is the
        # last stop on the match train, so get rid of the character by emitting
        # it as an OFFICIAL TOKEN OF MYSTERY for one lucky winner. Mystery
        # tokens are a surefire way of putting the parser into FABULOUS PRIZES
        # MODE.
        yield make_token(singles.get(current[column], T.MYSTERY),
                         current[column])
        column += 1
        # (note that the prizes in question are parse errors. If you don't like
        # parse errors, then you may not enjoy this mode very much.)

    # end while, in case you forgot


# character-to-predicate mappings to support matches local function of the
# parse function
_parser_predicates = {
    '(': lambda v: v == Token(T.PAREN_OPEN, None, '('),
    ')': lambda v: v == Token(T.PAREN_CLOSE, None, ')'),
    '[': lambda v: v == Token(T.PAREN_OPEN, None, '['),
    ']': lambda v: v == Token(T.PAREN_CLOSE, None, ']'),
    'a': lambda v: Token.is_t(v, T.ATOM),
    'n': lambda v: Token.is_t(v, T.NUMERIC),
    '?': lambda v: Token.is_t(v, T.BOOLEAN),
    's': lambda v: Token.is_t(v, T.STRING),
    'u': lambda v: isinstance(v, ast.AstNode) and v.t == 'unit',
    'e': lambda v: isinstance(v, ast.AstNode) and v.t == 'list',
    '$': lambda v: Token.is_t(v, T.EOF),
    '^': lambda v: Token.is_t(v, T.SOF),
    '<': lambda v: Token.is_t(v, T.PAREN_OPEN),
}


def sunit(position=None, children=None):
    return ast.AstNode('unit', position, children=children or [])


def slist(position=None, children=None):
    return ast.AstNode('list', position, children=children or [])


def snil(position=None):
    return ast.AstNode('nil', position)


def satom(name, position=None):
    return ast.AstNode('atom', position, attrs={'name': name})


def snumeric(value, position=None):
    return ast.AstNode('numeric', position, attrs={'value': value})


def sboolean(value, position=None):
    return ast.AstNode('boolean', position, attrs={'value': value})


def sstring(value, position=None):
    return ast.AstNode('string', position, attrs={'value': value})


def parse(tokens):
    """Parses a stream of tokens """
    stack = []

    def matches(pattern):
        if len(stack) < len(pattern):
            return False
        ps = (_parser_predicates[c] for c in reversed(pattern))
        return all(p(v) for p, v in zip(ps, reversed(stack)))

    def unshift(count):
        vals = stack[-count:]
        del stack[-count:]
        return vals

    def lift(v):
        stack[-1].children.append(v)

    while True:
        stack.append(next(tokens))
        if matches('^'):
            stack.append(sunit(stack[-1].position))
        elif matches('<'):
            stack.append(slist(stack[-1].position))
        elif matches('a'):
            a, = unshift(1)
            if a.text == 'nil':
                lift(snil(a.position))
            else:
                lift(satom(a.text, a.position))
        elif matches('n'):
            n, = unshift(1)
            lift(snumeric(int(n.text), n.position))
        elif matches('?'):
            b, = unshift(1)
            lift(sboolean(b.text == '#t', b.position))
        elif matches('s'):
            s, = unshift(1)
            lift(sstring(s.text, s.position))
        elif matches('(e)') or matches('[e]'):
            _, e, _ = unshift(3)
            lift(e)
        elif matches('^u$'):
            break
        else:
            tok = stack[-1]
            raise Exception(f"Unexpected '{tok.text}' at {tok.position}")

    assert len(stack) == 3
    return stack[1]


def load(stream):
    return parse(lexer(stream))


def loads(s):
    with io.StringIO(s) as f:
        return load(f)


def dump(f, node, indent=0):
    it = ' '*indent
    if node.t == 'nil':
        f.write('nil')
    elif node.t == 'boolean':
        f.write('#t' if node.attrs['value'] else '#f')
    elif node.t == 'numeric':
        f.write(repr(node.attrs['value']))
    elif node.t == 'string':
        f.write('"{}"'.format(node.attrs['value'].replace('"', r'\"')))
    elif node.t == 'atom':
        f.write(node.attrs['name'])
    elif node.t == 'list':
        if len(node.children) == 0:
            f.write('()')
        elif len(node.children) == 1:
            f.write('(')
            dump(f, node.children[0], indent+1)
            f.write(')')
        elif not any(n.t == 'list' and len(n.children) > 0
                     for n in node.children):
            f.write('('.format(it))
            for n in node.children[:-1]:
                dump(f, n, indent)
                f.write(' ')
            dump(f, node.children[-1], indent)
            f.write(')')
        else:
            f.write('('.format(it))
            dump(f, node.children[0], 0)
            f.write('\n{} '.format(it))
            for n in node.children[1:-1]:
                dump(f, n, indent+1)
                f.write('\n{} '.format(it))
            dump(f, node.children[-1], indent+1)
            f.write(')'.format(it))
    elif node.t == 'unit':
        for n in node.children:
            dump(f, n, indent)
            f.write('\n{}'.format(it))
    else:
        raise Exception(f"don't know what to do with '{node}'")


def dumps(data):
    with io.StringIO() as f:
        dump(f, data)
        return f.getvalue()
