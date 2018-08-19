# jeff65 gold-syntax grammar
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

import enum
import re
from ..parsing import Grammar, Lexer, Parser, ReStream, Rule


@enum.unique
class Mode(enum.IntEnum):
    NORMAL = Parser.NORMAL_MODE
    COMMENT = 1
    STRING = 2


T = enum.Enum('T', [
    # control tokens -- these tend to cause lexer mode switches
    'EOF', 'MYSTERY', 'STRING_DELIM', 'COMMENT_OPEN', 'COMMENT_CLOSE',

    # literals tokens
    'IDENTIFIER', 'NUMERIC', 'STRING', 'STRING_ESCAPE', 'WHITESPACE',
    'COMMENT_TEXT',

    # arithmetic operators
    'OPERATOR_PLUS', 'OPERATOR_MINUS', 'OPERATOR_TIMES', 'OPERATOR_DIVIDE',

    # logical operators
    'OPERATOR_NOT', 'OPERATOR_AND', 'OPERATOR_OR',

    # bitwise operators
    'OPERATOR_SHR', 'OPERATOR_SHL', 'OPERATOR_BITNOT', 'OPERATOR_BITAND',
    'OPERATOR_BITOR', 'OPERATOR_BITXOR',

    # comparison operators
    'OPERATOR_NE', 'OPERATOR_EQ', 'OPERATOR_LE', 'OPERATOR_GE', 'OPERATOR_LT',
    'OPERATOR_GT',

    # assignment operators
    'OPERATOR_ASSIGN', 'OPERATOR_ASSIGN_INC', 'OPERATOR_ASSIGN_DEC',

    # member access operators
    'OPERATOR_DOT',

    # pointer operators
    'OPERATOR_DEREF', 'OPERATOR_REF',

    # statement keywords
    'STMT_CONSTANT', 'STMT_FOR', 'STMT_FUN', 'STMT_IF', 'STMT_ISR', 'STMT_LET',
    'STMT_RETURN', 'STMT_USE', 'STMT_WHILE',

    # storage classes
    'STORAGE_MUT', 'STORAGE_STASH',

    # assorted punctuation
    'PUNCT_DO', 'PUNCT_ELSE', 'PUNCT_ELSEIF', 'PUNCT_END', 'PUNCT_ENDFUN',
    'PUNCT_ENDISR', 'PUNCT_IN', 'PUNCT_THEN', 'PUNCT_TO', 'PUNCT_COLON',
    'PUNCT_SEMICOLON', 'PUNCT_COMMA', 'PUNCT_ARROWR',

    # delimiters
    'PAREN_OPEN', 'PAREN_CLOSE', 'BRACKET_OPEN', 'BRACKET_CLOSE', 'BRACE_OPEN',
    'BRACE_CLOSE',
])


# precedences. Note that these are in order of lowest precedence to highest
# precedence. Has to be an IntEnum for comparisons to work.
P = enum.IntEnum('P', [
    # Statements
    'STATEMENTS',
    'RETURN_VALUE',
    'ASSIGNMENTS',

    # Statement elements
    'TYPES',
    'STORAGE',

    # Expressions
    'LITERALS',
    'COMPARISONS',
    'SUMS',
    'PRODUCTS',
    'BITSHIFTS',
    'BITXOR',
    'BITOR',
    'BITAND',
    'PREFIX_UNARY',
    'CALLS',
    'SUBSCRIPTS',
    'MEMBERS',
    'PARENTHESES',
])


# non-whitespace characters which can end tokens
specials = re.escape(r'()[]{}:;.,"\@&')


# creates a regex that matches the given word as long as it is followed by
# something that can end a token. Useful for defining keywords.
def _w(word):
    return r'(?m){}(?=[\s{}]|$)'.format(re.escape(word), specials)


lex = Lexer(T.EOF, [
    # whitespace -> hidden channel
    (Mode.NORMAL, r'(?m)\s+', T.WHITESPACE, ReStream.CHANNEL_HIDDEN),

    # keywords. Must come before the identifier match
    (_w('and'), T.OPERATOR_AND),
    (_w('bitand'), T.OPERATOR_BITAND),
    (_w('bitor'), T.OPERATOR_BITOR),
    (_w('bitxor'), T.OPERATOR_BITXOR),
    (_w('constant'), T.STMT_CONSTANT),
    (_w('do'), T.PUNCT_DO),
    (_w('else'), T.PUNCT_ELSE),
    (_w('elseif'), T.PUNCT_ELSEIF),
    (_w('end'), T.PUNCT_END),
    (_w('endfun'), T.PUNCT_ENDFUN),
    (_w('endisr'), T.PUNCT_ENDISR),
    (_w('for'), T.STMT_FOR),
    (_w('fun'), T.STMT_FUN),
    (_w('if'), T.STMT_IF),
    (_w('in'), T.PUNCT_IN),
    (_w('isr'), T.STMT_ISR),
    (_w('let'), T.STMT_LET),
    (_w('mut'), T.STORAGE_MUT),
    (_w('not'), T.OPERATOR_NOT),
    (_w('or'), T.OPERATOR_OR),
    (_w('return'), T.STMT_RETURN),
    (_w('stash'), T.STORAGE_STASH),
    (_w('then'), T.PUNCT_THEN),
    (_w('to'), T.PUNCT_TO),
    (_w('use'), T.STMT_USE),
    (_w('while'), T.STMT_WHILE),

    # Numeric tokens. Must come before the word match
    (r'\d[^\s{}]*'.format(specials), T.NUMERIC),

    # Identifiers. Matches a letter, followed by zero or more non-token-ending
    # characters. As written, this will actually match numbers as well, but
    # because that one is run first we don't have to worry about that.
    (r'\w[^\s{}]*'.format(specials), T.IDENTIFIER),

    # comment opener. When the lexer comes back, it will be in comment mode
    (Mode.NORMAL, re.escape('/*'), T.COMMENT_OPEN, ReStream.CHANNEL_HIDDEN),

    # comment delimiers, but for comment mode.
    (Mode.COMMENT, re.escape('/*'), T.COMMENT_OPEN, ReStream.CHANNEL_HIDDEN),
    (Mode.COMMENT, re.escape('*/'), T.COMMENT_CLOSE, ReStream.CHANNEL_HIDDEN),

    # This is necessary because the next pattern matches up to, but not
    # including, the newline; however, it will happily match zero characters,
    # causing an infinite loop. This matches that last newline.
    (Mode.COMMENT, r'\n', T.COMMENT_TEXT, ReStream.CHANNEL_HIDDEN),

    # Matches either to the next comment-control token, or the end of the line,
    # whichever happens first.
    (Mode.COMMENT, r'.*?(?=\/\*|\*\/|$)', T.COMMENT_TEXT,
     ReStream.CHANNEL_HIDDEN),

    # String delimiter. When the lexer comes back, it will be in string mode
    (re.escape('"'), T.STRING_DELIM),

    # String control tokens
    (Mode.STRING, r'\\.', T.STRING_ESCAPE),
    (Mode.STRING, re.escape('"'), T.STRING_DELIM),

    # Matches non-special text inside a string. The newline-matching pattern is
    # for the same reason as for comments.
    (Mode.STRING, r'\n', T.STRING),
    (Mode.STRING, r'.*?(?=\\|"|$)', T.STRING),

    # operators & punctuation. These must be ordered such that if A is a prefix
    # of B, then B comes before A. The easiest way to do this is to order them
    # by length.
    (re.escape('->'), T.PUNCT_ARROWR),
    (re.escape('>>'), T.OPERATOR_SHR),
    (re.escape('<<'), T.OPERATOR_SHL),
    (re.escape('!='), T.OPERATOR_NE),
    (re.escape('=='), T.OPERATOR_EQ),
    (re.escape('<='), T.OPERATOR_LE),
    (re.escape('>='), T.OPERATOR_GE),
    (re.escape('+='), T.OPERATOR_ASSIGN_INC),
    (re.escape('-='), T.OPERATOR_ASSIGN_DEC),
    (re.escape('+'), T.OPERATOR_PLUS),
    (re.escape('-'), T.OPERATOR_MINUS),
    (re.escape('*'), T.OPERATOR_TIMES),
    (re.escape('/'), T.OPERATOR_DIVIDE),
    (re.escape('<'), T.OPERATOR_LT),
    (re.escape('>'), T.OPERATOR_GT),
    (re.escape('='), T.OPERATOR_ASSIGN),
    (re.escape('.'), T.OPERATOR_DOT),
    (re.escape('@'), T.OPERATOR_DEREF),
    (re.escape('&'), T.OPERATOR_REF),
    (re.escape(':'), T.PUNCT_COLON),
    (re.escape(';'), T.PUNCT_SEMICOLON),
    (re.escape(','), T.PUNCT_COMMA),
    (re.escape('('), T.PAREN_OPEN),
    (re.escape(')'), T.PAREN_CLOSE),
    (re.escape('['), T.BRACKET_OPEN),
    (re.escape(']'), T.BRACKET_CLOSE),
    (re.escape('{'), T.BRACE_OPEN),
    (re.escape('}'), T.BRACE_CLOSE),

    # If we fail to match anything, consume one character, and move on.
    (r'.', T.MYSTERY),
])


grammar = Grammar('start', [T.EOF], [
    Rule('alist_inner', ['expr']),
    Rule('alist_inner', ['expr', T.PUNCT_COMMA, 'alist_inner']),
    Rule('alist', []),
    Rule('alist', ['alist_inner']),

    Rule('member', [T.IDENTIFIER]),

    Rule('expr', [T.PAREN_OPEN, 'expr', T.PAREN_CLOSE], prec=P.PARENTHESES),
    Rule('expr', ['expr', T.OPERATOR_DOT, 'member'], prec=P.MEMBERS),
    Rule('expr', ['expr', T.BRACKET_OPEN, 'expr', T.BRACKET_CLOSE],
         prec=P.SUBSCRIPTS),
    Rule('expr', ['stmt_call'], prec=P.CALLS),
    Rule('expr', [(T.OPERATOR_DEREF,
                   T.OPERATOR_MINUS,
                   T.OPERATOR_BITNOT), 'expr'],
         prec=P.PREFIX_UNARY,
         rassoc=True),
    Rule('expr', ['expr', T.OPERATOR_BITAND, 'expr'], prec=P.BITAND),
    Rule('expr', ['expr', T.OPERATOR_BITOR, 'expr'], prec=P.BITOR),
    Rule('expr', ['expr', T.OPERATOR_BITXOR, 'expr'], prec=P.BITXOR),
    Rule('expr', ['expr', (T.OPERATOR_SHL,
                           T.OPERATOR_SHR), 'expr'], prec=P.BITSHIFTS),
    Rule('expr', ['expr', (T.OPERATOR_TIMES,
                           T.OPERATOR_DIVIDE), 'expr'], prec=P.PRODUCTS),
    Rule('expr', ['expr', (T.OPERATOR_PLUS,
                           T.OPERATOR_MINUS), 'expr'], prec=P.SUMS),
    Rule('expr', ['expr', (T.OPERATOR_EQ, T.OPERATOR_NE,
                           T.OPERATOR_LE, T.OPERATOR_GE,
                           T.OPERATOR_LT, T.OPERATOR_GT), 'expr'],
         prec=P.COMPARISONS),
    Rule('expr', [(T.NUMERIC, T.IDENTIFIER, 'string')], prec=P.LITERALS),

    Rule('array', [T.BRACKET_OPEN, 'alist', T.BRACKET_CLOSE]),

    Rule('string', [T.STRING_DELIM, 'string_inner', T.STRING_DELIM],
         prec=P.LITERALS),
    Rule('string_inner', [], mode=Mode.STRING),
    Rule('string_inner', ['string_inner', (T.STRING, T.STRING_ESCAPE)],
         mode=Mode.STRING),

    Rule('storage', [], prec=P.STORAGE),
    Rule('storage', [(T.STORAGE_MUT, T.STORAGE_STASH)]),

    Rule('range_to', ['expr', T.PUNCT_TO, 'expr']),

    Rule('type_id', [T.IDENTIFIER]),
    Rule('type_id', [
        T.OPERATOR_REF, T.BRACKET_OPEN,
        'storage', 'type_id', T.BRACKET_CLOSE], prec=P.TYPES),
    Rule('type_id', [T.OPERATOR_REF, 'storage', 'type_id']),
    Rule('type_id', [T.BRACKET_OPEN, 'storage', 'type_id', T.PUNCT_SEMICOLON,
                     ('expr', 'range_to'), T.BRACKET_CLOSE]),

    Rule('declaration', [T.IDENTIFIER, T.PUNCT_COLON, 'type_id']),

    Rule('stmt_constant', [T.STMT_CONSTANT, 'declaration',
                           T.OPERATOR_ASSIGN, ('expr', 'array')],
         prec=P.STATEMENTS),

    Rule('stmt_use', [T.STMT_USE, T.IDENTIFIER]),

    Rule('stmt_let', [T.STMT_LET, 'storage', 'declaration',
                      T.OPERATOR_ASSIGN, ('expr', 'array')],
         prec=P.STATEMENTS),

    Rule('do_block', [T.PUNCT_DO, 'block', T.PUNCT_END]),

    Rule('stmt_while', [T.STMT_WHILE, 'expr', 'do_block']),

    Rule('stmt_for', [T.STMT_FOR, 'declaration',
                      T.PUNCT_IN, ('range_to', 'expr'), 'do_block']),

    Rule('branch_else_if', [T.PUNCT_ELSEIF, 'expr', T.PUNCT_THEN, 'block']),
    Rule('branch_else', [T.PUNCT_ELSE, 'block']),
    Rule('branch_else_ifs', ['branch_else_ifs', 'branch_else_if']),
    Rule('branch_else_ifs', ['branch_else_if']),
    Rule('stmt_if', [T.STMT_IF, 'expr', T.PUNCT_THEN, 'block', T.PUNCT_END]),
    Rule('stmt_if', [T.STMT_IF, 'expr', T.PUNCT_THEN, 'block',
                     'branch_else', T.PUNCT_END]),
    Rule('stmt_if', [T.STMT_IF, 'expr', T.PUNCT_THEN, 'block',
                     'branch_else_ifs', 'branch_else', T.PUNCT_END]),

    Rule('stmt_isr', [T.STMT_ISR, T.IDENTIFIER, 'block', T.PUNCT_ENDISR]),

    Rule('plist', []),
    Rule('plist', ['plist_inner']),
    Rule('plist_inner', ['declaration']),
    Rule('plist_inner', ['plist_inner', T.PUNCT_COMMA, 'declaration']),
    Rule('stmt_fun', [T.STMT_FUN, T.IDENTIFIER,
                      T.PAREN_OPEN, 'plist', T.PAREN_CLOSE,
                      'block', T.PUNCT_ENDFUN]),
    Rule('stmt_fun', [T.STMT_FUN, T.IDENTIFIER,
                      T.PAREN_OPEN, 'plist', T.PAREN_CLOSE,
                      T.PUNCT_ARROWR, 'type_id',
                      'block', T.PUNCT_ENDFUN]),

    Rule('stmt_return', [T.STMT_RETURN], prec=P.STATEMENTS),
    Rule('stmt_return', [T.STMT_RETURN, 'expr'], prec=P.RETURN_VALUE),

    Rule('stmt_assign', ['expr', (T.OPERATOR_ASSIGN,
                                  T.OPERATOR_ASSIGN_INC,
                                  T.OPERATOR_ASSIGN_DEC), 'expr'],
         prec=P.ASSIGNMENTS),

    Rule('stmt_call', ['expr', T.PAREN_OPEN, 'alist', T.PAREN_CLOSE],
         prec=P.CALLS),

    Rule('block', [], prec=P.STATEMENTS, rassoc=True),
    Rule('block', [('stmt_constant',
                    'stmt_for',
                    'stmt_if',
                    'stmt_let',
                    'stmt_return',
                    'stmt_while',
                    'stmt_assign',
                    'stmt_call'),
                   'block'],
         prec=P.STATEMENTS,
         rassoc=True),

    Rule('toplevel', []),
    Rule('toplevel', [('stmt_constant',
                       'stmt_isr',
                       'stmt_let',
                       'stmt_use',
                       'stmt_fun'),
                      'toplevel']),

    Rule('unit', ['toplevel']),
    Rule('start', ['unit']),
])

comment_grammar = Grammar('start', [T.COMMENT_CLOSE, T.WHITESPACE, T.EOF], [
    # left-recursive definition of a comment
    Rule('comment_inner', [], mode=Mode.COMMENT),
    Rule('comment_inner', ['comment_inner',
                           (T.COMMENT_TEXT, 'comment_nested')],
         mode=Mode.COMMENT),

    # we have to define a rule for nested comments separately to avoid
    # mode/mode conflicts
    Rule('comment_nested', [T.COMMENT_OPEN, 'comment_inner', T.COMMENT_CLOSE],
         mode=Mode.COMMENT),

    # enter/exit mode split
    Rule('comment', [T.COMMENT_OPEN, 'comment_inner', T.COMMENT_CLOSE]),

    # the empty rule handles whitespace
    Rule('hidden', []),
    Rule('hidden', ['comment']),
    Rule('start', ['hidden']),
])

parse = grammar.build_parser({
    ReStream.CHANNEL_HIDDEN: comment_grammar,
})
