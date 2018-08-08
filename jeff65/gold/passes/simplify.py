# jeff64 gold-syntax CST -> AST simplification
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

from ..grammar import T
from ... import ast, parsing, pattern
from ...pattern import Predicate as P


def require_token(t):
    return P.require(lambda n, c: n.t == t)


def token(t, key=None):
    return P(key, lambda n, c: n.t == t)


def unop(operator, sym):
    @pattern.match(
        ast.AstNode('expr', P('position'), children=[
            token(operator), P('rhs'),
        ]))
    def name_unop(self, position, rhs):
        return ast.AstNode(sym, position, children=[rhs])

    return name_unop


def binop(operator, sym):
    @pattern.match(
        ast.AstNode('expr', P('position'), children=[
            P('lhs'), token(operator), P('rhs'),
        ]))
    def name_binop(self, position, lhs, rhs):
        return ast.AstNode(sym, position, children=[lhs, rhs])

    return name_binop


def left_recursion(sym):
    @pattern.match(
        ast.AstNode(sym, P('position'), children=[
            ast.AstNode(sym, P.any(), children=[
                P.zero_or_more_nodes('children0')
            ]),
            P.zero_or_more_nodes('children1'),
        ]))
    def collapse_left_recursion(self, position, children0, children1):
        return ast.AstNode(sym, position, children=children0+children1)

    return collapse_left_recursion


@pattern.transform(pattern.Order.Ascending)
class Simplify:
    transform_attrs = False

    @pattern.match(
        ast.AstNode('expr', P.any(), children=[
            P.any_node('node'),
        ]))
    def remove_single_expr(self, node):
        return node

    collapse_unit = left_recursion('unit')
    collapse_block = left_recursion('block')

    @pattern.match(
        ast.AstNode('alist_inner', P('position'), children=[
            ast.AstNode('alist_inner', P.any(), children=[
                P.zero_or_more_nodes('children0')
            ]),
            require_token(T.PUNCT_COMMA),
            P.zero_or_more_nodes('children1'),
        ]))
    def collapse_alist_inner(self, position, children0, children1):
        return ast.AstNode('alist_inner', position,
                           children=children0+children1)

    @pattern.match(
        ast.AstNode('alist', P('position'), children=[
            ast.AstNode('alist_inner', P.any(), children=[
                P.zero_or_more_nodes('children'),
            ])
        ]))
    def collapse_alist(self, position, children):
        return ast.AstNode('alist', position, children=children)

    @pattern.match(
        ast.AstNode('stmt_use', P('position'), children=[
            require_token(T.STMT_USE),
            P('unit_name'),
        ]))
    def collapse_stmt_use(self, position, unit_name):
        return ast.AstNode('use', position, attrs={
            'name': unit_name.text,
        })

    @pattern.match(
        ast.AstNode('stmt_constant', P('position'), children=[
            require_token(T.STMT_CONSTANT),
            ast.AstNode('declaration', P.any(), children=[
                P('name'),
                require_token(T.PUNCT_COLON),
                P('ty'),
            ]),
            require_token(T.OPERATOR_ASSIGN),
            P('rhs'),
        ]))
    def collapse_stmt_constant(self, position, name, ty, rhs):
        return ast.AstNode('constant', position, attrs={
            'name': name.text,
            'type': ty,
        }, children=[rhs])

    @pattern.match(
        ast.AstNode('stmt_let', P('position'), children=[
            require_token(T.STMT_LET),
            ast.AstNode('storage', P.any(), children=[
                P.zero_or_more_nodes('storage'),
            ]),
            ast.AstNode('declaration', P.any(), children=[
                P('name'),
                require_token(T.PUNCT_COLON),
                P('ty'),
            ]),
            require_token(T.OPERATOR_ASSIGN),
            P('rhs'),
        ]))
    def collapse_stmt_let(self, position, storage, name, ty, rhs):
        return ast.AstNode('let', position, attrs={
            'name': name.text,
            'type': ty,
            **{'storage': s.text for s in storage},
        }, children=[rhs])

    @pattern.match(
        ast.AstNode('stmt_assign', P('position'), children=[
            P('lhs'),
            require_token(T.OPERATOR_ASSIGN),
            P('rhs'),
        ]))
    def collapse_stmt_assign(self, position, lhs, rhs):
        return ast.AstNode('set', position, children=[lhs, rhs])

    # TODO: handle arguments, return values
    @pattern.match(
        ast.AstNode('stmt_fun', P('position'), children=[
            require_token(T.STMT_FUN),
            P('name'),
            require_token(T.PAREN_OPEN),
            P.any(),  # plist
            require_token(T.PAREN_CLOSE),
            ast.AstNode('block', P.any(), children=[
                P.zero_or_more_nodes('body'),
            ]),
            require_token(T.PUNCT_ENDFUN),
        ]))
    def collapse_stmt_fun(self, position, name, body):
        return ast.AstNode('fun', position, attrs={
            'name': name.text,
            'return': None,
            'args': [],
        }, children=body)

    @pattern.match(ast.AstNode('type_id', P.any(), children=[P('ty')]))
    def simple_type(self, ty):
        return ty.text

    @pattern.match(
        ast.AstNode('type_id', P('position'), children=[
            token(T.OPERATOR_REF),
            ast.AstNode('storage', P.any(), children=[
                P.zero_or_more_nodes('storage'),
            ]),
            P('ty'),
        ]))
    def ref_type(self, position, storage, ty):
        return ast.AstNode('type_ref', position, attrs={
            'type': ty,
            **{'storage': s.text for s in storage},
        })

    @pattern.match(
        ast.AstNode('expr', P('position'), children=[token(T.NUMERIC, 'n')]))
    def numeric(self, position, n):
        try:
            if n.text.startswith('0x'):
                value = int(n.text[2:], 16)
            elif n.text.startswith('0o'):
                value = int(n.text[2:], 8)
            elif n.text.startswith('0b'):
                value = int(n.text[2:], 2)
            else:
                value = int(n.text)
        except ValueError as e:
            raise parsing.ParseError(str(e))

        return ast.AstNode('numeric', position, attrs={'value': value})

    @pattern.match(
        ast.AstNode('expr', P('position'), children=[
            token(T.IDENTIFIER, 'id'),
        ]))
    def identifier(self, position, id):
        return ast.AstNode('identifier', position, attrs={
            'name': id.text,
        })

    @pattern.match(
        ast.AstNode('expr', P.any(), children=[
            token(T.PAREN_OPEN), P('inner'), token(T.PAREN_CLOSE),
        ]))
    def drop_expr_parens(self, inner):
        return inner

    name_negate = unop(T.OPERATOR_MINUS, 'negate')
    name_deref = unop(T.OPERATOR_DEREF, 'deref')
    name_add = binop(T.OPERATOR_PLUS, 'add')
    name_sub = binop(T.OPERATOR_MINUS, 'sub')
    name_mul = binop(T.OPERATOR_TIMES, 'mul')
    name_div = binop(T.OPERATOR_DIVIDE, 'div')

    @pattern.match(
        ast.AstNode('expr', P('position'), children=[
            P('namespace'),
            token(T.OPERATOR_DOT),
            ast.AstNode('member', P.any(), children=[
                P('member'),
            ]),
        ]))
    def name_member_access(self, position, namespace, member):
        return ast.AstNode('member_access', position, attrs={
            'member': member.text,
        }, children=[namespace])

    @pattern.match(
        ast.AstNode('expr', P('position'), children=[
            P('function'),
            token(T.PAREN_OPEN),
            ast.AstNode('alist', P.any(), children=[
                P.zero_or_more_nodes('args'),
            ]),
            token(T.PAREN_CLOSE),
        ]))
    def name_call(self, position, function, args):
        return ast.AstNode('call', position, attrs={
            'target': function,
        }, children=args)

    # Collapse left-recursion on strings. Note that the list we use to build
    # the string is wrapped in another list to protect it from being spliced
    # directly into the node children.
    @pattern.match(ast.AstNode('string_inner', P.any(), children=[]))
    def string_inner_empty(self):
        return [[]]

    @pattern.match(
        ast.AstNode('string_inner', P.any(), children=[
            P('string0'),
            token(T.STRING, 'string1'),
        ]))
    def string_inner_segment(self, string0, string1):
        string0.append(string1.text)
        return [string0]

    @pattern.match(
        ast.AstNode('string_inner', P.any(), children=[
            P('string0'),
            token(T.STRING_ESCAPE, 'string1'),
        ]))
    def string_inner_escape(self, string0, string1):
        string0.append(string1.text[1])
        return [string0]

    @pattern.match(
        ast.AstNode('string', P('position'), children=[
            require_token(T.STRING_DELIM),
            P('value'),
            require_token(T.STRING_DELIM),
        ]))
    def collapse_string(self, position, value):
        return ast.AstNode('string', position, attrs={
            'value': "".join(value),
        })
