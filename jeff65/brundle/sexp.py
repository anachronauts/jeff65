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


class T(Enum):
    EOF = auto()
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
    position = attr.ib()
    text = attr.ib()


@attr.s(frozen=True, slots=True)
class Atom:
    text = attr.ib()


terminators = re.escape('()"')
str_delim = '"'
m_str_escape = re.compile(r'\\.', re.M)
m_str_delim = re.compile(re.escape(str_delim))
m_str_control = re.compile(fr'{m_str_escape.pattern}|{m_str_delim.pattern}')
m_whitespace = re.compile(r'\s+', re.M)
m_numeric = re.compile(fr'[+-]?\d[^\s{terminators}]*')
m_atom = re.compile(fr'[\w:][^\s{terminators}]*')
m_bool = re.compile(r'#[tf]')
singles = {
    '(': T.PAREN_OPEN,
    ')': T.PAREN_CLOSE,
}


def lexer(stream, line=0, column=0):
    current = None
    string_value = None
    string_line = 0
    string_column = 0

    def make_token(t, text):
        return Token(t, (line, column), text)

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


def parse(tokens):
    data = [[]]
    for tok in tokens:
        if tok.t == T.PAREN_OPEN:
            data.append([])
        elif tok.t == T.PAREN_CLOSE:
            lst = data.pop()
            data[-1].append(lst)
        elif tok.t == T.NUMERIC:
            data[-1].append(int(tok.text))
        elif tok.t == T.STRING:
            data[-1].append(tok.text)
        elif tok.t == T.BOOLEAN:
            data[-1].append(tok.text == '#t')
        elif tok.t == T.ATOM:
            if tok.text == 'nil':
                data[-1].append(None)
            else:
                data[-1].append(Atom(tok.text))
        else:
            raise Exception(f"Unexpected '{tok.text}' at {tok.position}")
    assert len(data) == 1
    assert len(data[0]) == 1
    return data[0][0]


def load(stream):
    return parse(lexer(stream))


def loads(s):
    with io.StringIO(s) as f:
        return load(f)


def dump(f, data, indent=0):
    it = ' '*indent
    if data is None:
        f.write('nil')
    elif isinstance(data, bool):
        f.write('#t' if data else '#f')
    elif isinstance(data, int):
        f.write('{}'.format(repr(data)))
    elif isinstance(data, str):
        f.write('"{}"'.format(data.replace('"', r'\"')))
    elif isinstance(data, Atom):
        f.write('{}'.format(data.text))
    elif isinstance(data, list):
        if len(data) == 0:
            f.write('()')
        elif len(data) == 1:
            f.write('(')
            dump(f, data[0], indent+1)
            f.write(')')
        elif not any(isinstance(e, list) and len(e) > 0 for e in data):
            f.write('('.format(it))
            for e in data[:-1]:
                dump(f, e, indent)
                f.write(' ')
            dump(f, data[-1], indent)
            f.write(')')
        else:
            f.write('('.format(it))
            dump(f, data[0], 0)
            f.write('\n{} '.format(it))
            for e in data[1:-1]:
                dump(f, e, indent+1)
                f.write('\n{} '.format(it))
            dump(f, data[-1], indent+1)
            f.write(')'.format(it))
    else:
        raise Exception(f"don't know what to do with '{data}'")


def dumps(data):
    with io.StringIO() as f:
        dump(f, data)
        return f.getvalue()
