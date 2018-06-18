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

import re
from . import ast
from .grammar import Parser
from antlr4.CommonTokenFactory import CommonTokenFactory
from antlr4.Token import Token


known_words = {
    # arithmetic operators
    '+': Parser.OPERATOR_PLUS,
    '-': Parser.OPERATOR_MINUS,
    '*': Parser.OPERATOR_TIMES,
    '/': Parser.OPERATOR_DIVIDE,

    # logical operators
    'not': Parser.OPERATOR_NOT,
    'and': Parser.OPERATOR_AND,
    'or': Parser.OPERATOR_OR,

    # bitwise operators
    '>>': Parser.OPERATOR_SHR,
    '<<': Parser.OPERATOR_SHL,
    'bitand': Parser.OPERATOR_BITAND,
    'bitor': Parser.OPERATOR_BITOR,
    'bitxor': Parser.OPERATOR_BITXOR,

    # comparison operators
    '!=': Parser.OPERATOR_NE,
    '==': Parser.OPERATOR_EQ,
    '<=': Parser.OPERATOR_LE,
    '>=': Parser.OPERATOR_GE,
    '<': Parser.OPERATOR_LT,
    '>': Parser.OPERATOR_GT,

    # assignment operators
    '=': Parser.OPERATOR_ASSIGN,
    '+=': Parser.OPERATOR_ASSIGN_INC,
    '-=': Parser.OPERATOR_ASSIGN_DEC,

    # member access operators
    '.': Parser.OPERATOR_DOT,

    # pointer operators
    '@': Parser.OPERATOR_DEREF,
    '&': Parser.OPERATOR_REF,

    # statement leaders
    'constant': Parser.STMT_CONSTANT,
    'for': Parser.STMT_FOR,
    'fun': Parser.STMT_FUN,
    'if': Parser.STMT_IF,
    'isr': Parser.STMT_ISR,
    'let': Parser.STMT_LET,
    'return': Parser.STMT_RETURN,
    'use': Parser.STMT_USE,
    'while': Parser.STMT_WHILE,

    # storage classes
    'mut': Parser.STORAGE_MUT,
    'stash': Parser.STORAGE_STASH,

    # assorted punctuation
    'do': Parser.PUNCT_DO,
    'else': Parser.PUNCT_ELSE,
    'elseif': Parser.PUNCT_ELSEIF,
    'end': Parser.PUNCT_END,
    'endfun': Parser.PUNCT_ENDFUN,
    'endisr': Parser.PUNCT_ENDISR,
    'in': Parser.PUNCT_IN,
    'then': Parser.PUNCT_THEN,
    'to': Parser.PUNCT_TO,
    ':': Parser.PUNCT_COLON,
    ';': Parser.PUNCT_SEMICOLON,
    ',': Parser.PUNCT_COMMA,
    '->': Parser.PUNCT_ARROWR,

    # delimiters
    '/*': Parser.COMMENT_OPEN,  # see also Lexer.__m_comment_open
    '*/': Parser.COMMENT_CLOSE,  # see also Lexer.__m_comment_close
    '"': Parser.STRING_DELIM,  # see also Lexer.__m_string_delim
    '(': Parser.PAREN_OPEN,
    ')': Parser.PAREN_CLOSE,
    '[': Parser.BRACKET_OPEN,
    ']': Parser.BRACKET_CLOSE,
    '{': Parser.BRACE_OPEN,
    '}': Parser.BRACE_CLOSE,
}


# this class is way over-encapulated for a normal Python class, mostly as a
# safeguard against antlr4 doing weird things like accessing members beginning
# with underscores.
class Lexer:
    # non-whitespace characters which can end tokens.
    __specials = re.escape(r'()[]{}:;.,"\@&')

    # matches one or more whitespace characters, including newlines
    __m_whitespace = re.compile(r'\s+', re.M)

    # matches a digit, followed by zero or more non-token-ending characters
    __m_numeric = re.compile(r'\d[^\s{}]*'.format(__specials))

    # matches a letter, followed by zero or more non-token-ending characters.
    # Note that as written, this will actually match numbers as well, but the
    # 'numeric' regex is always run first, which removes tokens beginning with
    # numbers.
    __m_word = re.compile(r'\w[^\s{}]*'.format(__specials))

    # match comment-open and comment-close characters, respectively. This must
    # be a separate rule from the sprinkle rule because a sprinkle prefixed
    # with a comment-open sequence starts a comment.
    # These have to agree with the values in known_words.
    __m_comment_open = re.compile(re.escape('/*'))
    __m_comment_close = re.compile(re.escape('*/'))

    # Matches either comment-open or comment-close
    __m_comment_nest = re.compile(r'{}|{}'.format(__m_comment_open.pattern,
                                                  __m_comment_close.pattern))

    # matches a non-alphanumeric character, including a special, followed by
    # zero or more non-token-ending characters. Note that this means that only
    # one special can ever be consumed at a time, and they will always break
    # off into their own tokens, even when adjacent.
    __m_sprinkle = re.compile(r'[^\w\s][^\w\s{}]*'.format(__specials))

    # match the string escape character followed by one character, and string
    # delimiter, respectively. These have to agree with the values in
    # known_words.
    __m_str_escape = re.compile(r'\\.', re.M)
    __m_str_delim = re.compile(re.escape(r'"'))

    # matches characters that affect lexing of strings
    __m_str_control = re.compile(r'{}|{}'.format(__m_str_escape.pattern,
                                                 __m_str_delim.pattern))

    def __init__(self, stream, name='<unknown>', factory=None):
        self.__stream = stream
        self.__name = name
        self.__current = None
        self.__line = 0
        self.__column = 0
        self.__factory = factory or CommonTokenFactory.DEFAULT
        self.__comments = []
        self.__string_start = None

    # Interface functions for ANTLR4
    @property
    def _factory(self):
        return self.__factory

    def setTokenFactory(self, factory):
        self.__factory = factory  # pragma: no cover

    def getInputStream(self):
        return self.__stream  # pragma: no cover

    def getSourceName(self):
        return self.__name  # pragma: no cover

    @property
    def line(self):
        return self.__line

    @property
    def column(self):
        return self.__column

    def nextToken(self) -> Token:
        # Advance to the next line if necessary
        if self.__current is None or self.__column >= len(self.__current):
            try:
                self.__current = next(self.__stream)
                self.__line += 1
                self.__column = 0
            except StopIteration:
                # If we're in comment mode or string mode, we are NOT expecting
                # this kind of behavior and will kick up a fuss.
                if len(self.__comments) == 1:
                    raise ast.ParseError(
                        "Premature end of input while parsing comment " +
                        "starting at {}:{}".format(*self.__comments[0]))
                elif len(self.__comments) > 1:
                    locs = ", ".join("{}:{}".format(line, column)
                                     for line, column in self.__comments)
                    raise ast.ParseError(
                        "Premature end of input while parsing nested " +
                        "comments, starting at {}".format(locs))
                return self.__make_token(Parser.EOF, '<$EOF>')

        # Comment mode means that we parse until either a begin or end comment
        if len(self.__comments) > 0:
            m = self.__m_comment_nest.search(self.__current, self.__column)
            if not m:
                # the rest of the line is a comment
                token = self.__make_token(Parser.COMMENT_TEXT,
                                          self.__current[self.__column:],
                                          Token.HIDDEN_CHANNEL)
                self.__column = len(self.__current)
                return token
            elif m.start() == self.__column:
                # the comment delimiter is right here!
                here = self.__here()
                token = self.__produce(Parser.MYSTERY, m, Token.HIDDEN_CHANNEL)
                if token.type == Parser.COMMENT_OPEN:
                    self.__comments.append(here)
                elif token.type == Parser.COMMENT_CLOSE:
                    self.__comments.pop()
                return token
            else:
                # comment the text before the delimiter
                token = self.__make_token(Parser.COMMENT_TEXT,
                                          self.__current[self.__column:
                                                         m.start()],
                                          Token.HIDDEN_CHANNEL)
                self.__column = m.start()
                return token

        # String mode emits a sequence of STRING tokens, which will be
        # concatenated by the parser.
        if self.__string_start:
            m = self.__m_str_control.search(self.__current, self.__column)
            if not m:
                # the rest of the line is a string
                token = self.__make_token(Parser.STRING,
                                          self.__current[self.__column:])
                self.__column = len(self.__current)
                return token
            elif m.start() == self.__column:
                # the string control character is right here!
                token = self.__produce(Parser.MYSTERY, m)
                if token.type == Parser.STRING_DELIM:
                    # ending a string produces another empty string token to be
                    # concatenated.
                    self.__string_start = None
                    return self.__make_token(Parser.STRING, "")
                # it must be an escape character
                return self.__recast_token(token, Parser.STRING, token.text[1])
            else:
                # string the text before the control
                token = self.__make_token(Parser.STRING,
                                          self.__current[self.__column:
                                                         m.start()])
                self.__column = m.start()
                return token

        # Whitespace is sent to the hidden channel
        m = self.__match_with(self.__m_whitespace)
        if m:
            return self.__produce(Parser.WHITESPACE, m, Token.HIDDEN_CHANNEL)

        # this MUST be run before the word match, see above
        m = self.__match_with(self.__m_numeric)
        if m:
            return self.__produce(Parser.NUMERIC, m)

        # this MUST be run after the number match, see above
        m = self.__match_with(self.__m_word)
        if m:
            return self.__produce(Parser.IDENTIFIER, m)

        # comments require special handling. They can't be lumped in with
        # sprinkles because if a comment sequence begins what would otherwise
        # be a sprinkle, we switch into comment mode.
        m = self.__match_with(self.__m_comment_open)
        if m:
            self.__comments.append(self.__here())
            return self.__produce(Parser.COMMENT_OPEN, m, Token.HIDDEN_CHANNEL)

        # non-alphanumeric words, mostly operators, delimiters, etc. We call
        # these "sprinkles" for whimsy value.
        m = self.__match_with(self.__m_sprinkle)
        if m:
            token = self.__produce(Parser.MYSTERY, m)
            if token.type == Parser.STRING_DELIM:
                # enter string mode, starting by emitting an empty string
                # token. The parser concatenates sequences of string tokens
                # automatically, so we can do this to allow for the fact that
                # we MUST emit a token but don't want to duplicate logic.
                self.__string_start = (token.line, token.column)
                return self.__recast_token(token, Parser.STRING, "")

            return token

        # We literally didn't match anything (???) so go ahead and emit an
        # OFFICIAL TOKEN OF MYSTERY containing the next character to the lucky
        # winner. Mystery tokens are a surefire way of putting the parser into
        # FABULOUS PRIZES MODE.
        token = self.__make_token(Parser.MYSTERY,
                                  self.__current[self.__column])
        self.__column += 1
        # (note that the prizes in question are parse errors. If you don't like
        # parse errors, then you may not enjoy this mode very much.)
        return token

    # Helper functions
    def __here(self):
        return (self.__line, self.__column)

    def __match_with(self, regex):
        return regex.match(self.__current, self.__column)

    def __produce(self, default_sym, match, channel=None) -> Token:
        # see if the symbol is in the table
        if match.group() in known_words:
            sym = known_words[match.group()]
        else:
            sym = default_sym
        token = self.__make_token(sym, match.group(), channel)
        self.__column = match.end()
        return token

    def __recast_token(self, token: Token, sym, text, channel=None) -> Token:
        return self.__factory.create(
            (self, self.__stream),
            sym,
            text,
            channel or token.channel,
            token.start, token.stop,
            token.line, token.column)

    def __make_token(self, sym, text, channel=None) -> Token:
        return self.__factory.create(
            (self, self.__stream),
            sym,
            text,
            channel or Token.DEFAULT_CHANNEL,
            -1, -1,  # start, stop
            self.__line,
            self.__column)
