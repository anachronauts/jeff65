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
        ast.AstNode('expr', children=[token(operator), P('rhs')]))
    def name_unop(self, rhs):
        return ast.AstNode(sym, children=[rhs])

    return name_unop


def binop(operator, sym):
    @pattern.match(
        ast.AstNode('expr', children=[P('lhs'), token(operator), P('rhs')]))
    def name_binop(self, lhs, rhs):
        return ast.AstNode(sym, children=[lhs, rhs])

    return name_binop


def left_recursion(sym):
    @pattern.match(
        ast.AstNode(sym, children=[
            ast.AstNode(sym, children=[
                P.zero_or_more_nodes('children0')
            ]),
            P.zero_or_more_nodes('children1'),
        ]))
    def collapse_left_recursion(self, children0, children1):
        return ast.AstNode(sym, children=children0+children1)

    return collapse_left_recursion


@pattern.transform(pattern.Order.Ascending)
class Simplify:
    transform_attrs = False

    @pattern.match(ast.AstNode('expr', children=[P.any_node('node')]))
    def remove_single_expr(self, node):
        return node

    collapse_unit = left_recursion('unit')
    collapse_block = left_recursion('block')

    @pattern.match(
        ast.AstNode('alist_inner', children=[
            ast.AstNode('alist_inner', children=[
                P.zero_or_more_nodes('children0')
            ]),
            require_token(T.PUNCT_COMMA),
            P.zero_or_more_nodes('children1'),
        ]))
    def collapse_alist_inner(self, children0, children1):
        return ast.AstNode('alist_inner', children=children0+children1)

    @pattern.match(
        ast.AstNode('alist', children=[
            ast.AstNode('alist_inner', children=[
                P.zero_or_more_nodes('children'),
            ])
        ]))
    def collapse_alist(self, children):
        return ast.AstNode('alist', children=children)

    @pattern.match(
        ast.AstNode('stmt_use', children=[
            require_token(T.STMT_USE),
            P('unit_name'),
        ]))
    def collapse_stmt_use(self, unit_name):
        return ast.AstNode('use', attrs={
            'name': unit_name.text,
        })

    @pattern.match(
        ast.AstNode('stmt_constant', children=[
            require_token(T.STMT_CONSTANT),
            ast.AstNode('declaration', children=[
                P('name'),
                require_token(T.PUNCT_COLON),
                P('ty'),
            ]),
            require_token(T.OPERATOR_ASSIGN),
            P('rhs'),
        ]))
    def collapse_stmt_constant(self, name, ty, rhs):
        return ast.AstNode('constant', attrs={
            'name': name.text,
            'type': ty,
        }, children=[rhs])

    @pattern.match(
        ast.AstNode('stmt_let', children=[
            require_token(T.STMT_LET),
            ast.AstNode('storage', children=[
                P.zero_or_more_nodes('storage'),
            ]),
            ast.AstNode('declaration', children=[
                P('name'),
                require_token(T.PUNCT_COLON),
                P('ty'),
            ]),
            require_token(T.OPERATOR_ASSIGN),
            P('rhs'),
        ]))
    def collapse_stmt_let(self, storage, name, ty, rhs):
        return ast.AstNode('let', attrs={
            'name': name.text,
            'type': ty,
            **{'storage': s.text for s in storage},
        }, children=[rhs])

    @pattern.match(
        ast.AstNode('stmt_assign', children=[
            P('lhs'),
            require_token(T.OPERATOR_ASSIGN),
            P('rhs'),
        ]))
    def collapse_stmt_assign(self, lhs, rhs):
        return ast.AstNode('set', children=[lhs, rhs])

    # TODO: handle arguments, return values
    @pattern.match(
        ast.AstNode('stmt_fun', children=[
            require_token(T.STMT_FUN),
            P('name'),
            require_token(T.PAREN_OPEN),
            P.any(),  # plist
            require_token(T.PAREN_CLOSE),
            ast.AstNode('block', children=[
                P.zero_or_more_nodes('body'),
            ]),
            require_token(T.PUNCT_ENDFUN),
        ]))
    def collapse_stmt_fun(self, name, body):
        return ast.AstNode('fun', attrs={
            'name': name.text,
            'return': None,
            'args': [],
        }, children=body)

    @pattern.match(ast.AstNode('type_id', children=[P('ty')]))
    def simple_type(self, ty):
        return ty.text

    @pattern.match(
        ast.AstNode('type_id', children=[
            token(T.OPERATOR_REF),
            ast.AstNode('storage', children=[
                P.zero_or_more_nodes('storage'),
            ]),
            P('ty'),
        ]))
    def ref_type(self, storage, ty):
        return ast.AstNode('type_ref', attrs={
            'type': ty,
            **{'storage': s.text for s in storage},
        })

    @pattern.match(ast.AstNode('expr', children=[token(T.NUMERIC, 'n')]))
    def numeric(self, n):
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

        return ast.AstNode('numeric', attrs={'value': value})

    @pattern.match(ast.AstNode('expr', children=[token(T.IDENTIFIER, 'id')]))
    def identifier(self, id):
        return ast.AstNode('identifier', attrs={
            'name': id.text,
        })

    @pattern.match(
        ast.AstNode('expr', children=[
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
        ast.AstNode('expr', children=[
            P('namespace'),
            token(T.OPERATOR_DOT),
            ast.AstNode('member', children=[
                P('member'),
            ]),
        ]))
    def name_member_access(self, namespace, member):
        return ast.AstNode('member_access', attrs={
            'member': member.text,
        }, children=[namespace])

    @pattern.match(
        ast.AstNode('expr', children=[
            P('function'),
            token(T.PAREN_OPEN),
            ast.AstNode('alist', children=[
                P.zero_or_more_nodes('args'),
            ]),
            token(T.PAREN_CLOSE),
        ]))
    def name_call(self, function, args):
        return ast.AstNode('call', attrs={
            'target': function,
        }, children=args)

    # Collapse left-recursion on strings. Note that the list we use to build
    # the string is wrapped in another list to protect it from being spliced
    # directly into the node children.
    @pattern.match(ast.AstNode('string_inner', children=[]))
    def string_inner_empty(self):
        return [[]]

    @pattern.match(
        ast.AstNode('string_inner', children=[
            P('string0'),
            token(T.STRING, 'string1'),
        ]))
    def string_inner_segment(self, string0, string1):
        string0.append(string1.text)
        return [string0]

    @pattern.match(
        ast.AstNode('string_inner', children=[
            P('string0'),
            token(T.STRING_ESCAPE, 'string1'),
        ]))
    def string_inner_escape(self, string0, string1):
        string0.append(string1.text[1])
        return [string0]

    @pattern.match(
        ast.AstNode('string', children=[
            require_token(T.STRING_DELIM),
            P('value'),
            require_token(T.STRING_DELIM),
        ]))
    def collapse_string(self, value):
        return ast.AstNode('string', attrs={'value': "".join(value)})
