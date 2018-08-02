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

from .. import ast, pattern
from ..grammar import T


def parse_numeric(text):
    if text.startswith('0x'):
        return int(text[2:], 16)
    elif text.startswith('0o'):
        return int(text[2:], 8)
    elif text.startswith('0b'):
        return int(text[2:], 2)
    return int(text)


def unop(p, operator, sym):
    yield (
        ast.AstNode('expr', p.any('position'), children=[
            p.predicate(lambda t: t.t == operator),
            p.any('rhs'),
        ]),
        lambda m: ast.AstNode(sym, m['position'], children=[
            m['rhs'],
        ])
    )


def binop(p, operator, sym):
    yield (
        ast.AstNode('expr', p.any('position'), children=[
            p.any('lhs'),
            p.predicate(lambda t: t.t == operator),
            p.any('rhs'),
        ]),
        lambda m: ast.AstNode(sym, m['position'], children=[
            m['lhs'],
            m['rhs'],
        ])
    )


def collapse_left_recursion(p, sym):
    yield (
        ast.AstNode(sym, p.any('position'), children=[
            ast.AstNode(p.require(sym), p.any(), children=[
                p.zero_or_more_nodes('children0'),
            ]),
            p.zero_or_more_nodes('children1'),
        ]),
        lambda m: ast.AstNode(sym, m['position'], children=[
            *m['children0'],
            *m['children1'],
        ])
    )


@pattern.transform(pattern.Order.Ascending)
def Simplify(p):
    # remove dummy node unit_stmt
    yield (
        ast.AstNode('unit_stmt', p.any(), children=[
            p.any_node(key='node'),
        ]),
        lambda m: m['node']
    )

    # remove dummy node block_stmt
    yield (
        ast.AstNode('block_stmt', p.any(), children=[
            p.any_node(key='node'),
        ]),
        lambda m: m['node']
    )

    yield from collapse_left_recursion(p, 'unit')
    yield from collapse_left_recursion(p, 'block')
    yield (
        ast.AstNode('alist_inner', p.any('position'), children=[
            ast.AstNode('alist_inner', p.any(), children=[
                p.zero_or_more_nodes('children0'),
            ]),
            p.zero_or_more_nodes('children1'),
        ]),
        lambda m: ast.AstNode('alist_inner', m['position'], children=[
            *m['children0'],
            *m['children1'],
        ])
    )

    yield (
        ast.AstNode('alist', p.any('position'), children=[
            ast.AstNode('alist_inner', p.any(), children=[
                p.zero_or_more_nodes('children'),
            ])
        ]),
        lambda m: ast.AstNode('alist', m['position'], children=m['children'])
    )

    yield (
        ast.AstNode('stmt_use', p.any('position'), children=[
            p.any(),
            p.any('unit_name'),
        ]),
        lambda m: ast.AstNode('use', m['position'], attrs={
            'name': m['unit_name'].text,
        })
    )

    yield (
        ast.AstNode('stmt_constant', p.any('position'), children=[
            p.any(),
            ast.AstNode('declaration', p.any(), children=[
                p.any('name'),
                p.any(),
                p.any('type'),
            ]),
            p.any(),
            p.any('rhs'),
        ]),
        lambda m: ast.AstNode('constant', m['position'], attrs={
            'name': m['name'].text,
            'type': m['type'],
        }, children=[m['rhs']])
    )

    yield (
        ast.AstNode('stmt_let', p.any('position'), children=[
            p.any(),
            p.zero_or_more_nodes('storage', allow={'storage'}),
            ast.AstNode('declaration', p.any(), children=[
                p.any('name'),
                p.any(),
                p.any('type'),
            ]),
            p.any(),
            p.any('rhs'),
        ]),
        lambda m: ast.AstNode('let', m['position'], attrs={
            'name': m['name'].text,
            'type': m['type'],
            **{'storage': s.children[0].text for s in m['storage']},
        }, children=[m['rhs']])
    )

    yield (
        ast.AstNode('stmt_assign', p.any('position'), children=[
            p.any('lhs'),
            p.any(),
            p.any('rhs'),
        ]),
        lambda m: ast.AstNode('set', m['position'], children=[
            m['lhs'],
            m['rhs'],
        ])
    )

    # TODO: handle arguments, return values
    yield (
        ast.AstNode('stmt_fun', p.any('position'), children=[
            p.any(),
            p.any('name'),
            p.any(),
            p.any(),
            p.any('block'),
            p.any(),
        ]),
        lambda m: ast.AstNode('fun', m['position'], attrs={
            'name': m['name'].text,
            'return': None,
            'args': [],
        }, children=m['block'].children)
    )

    yield (
        ast.AstNode('type_id', p.any(), children=[p.any('type')]),
        lambda m: m['type'].text,
    )

    yield (
        ast.AstNode('type_id', p.any('position'), children=[
            p.predicate(lambda t: t.t == T.OPERATOR_REF),
            p.any('type'),
        ]),
        lambda m: ast.AstNode('type_ref', m['position'], attrs={
            'type': m['type'],
        })
    )

    yield (
        ast.AstNode('expr', p.any('position'), children=[
            p.predicate(lambda t: t.t == T.NUMERIC, 'n'),
        ]),
        lambda m: ast.AstNode('numeric', m['position'], attrs={
            'value': parse_numeric(m['n'].text),
        })
    )

    yield (
        ast.AstNode('expr', p.any('position'), children=[
            p.predicate(lambda t: t.t == T.IDENTIFIER, 'id'),
        ]),
        lambda m: ast.AstNode('identifier', m['position'], attrs={
            'name': m['id'].text,
        })
    )

    yield (
        ast.AstNode('expr', p.any(), children=[
            p.predicate(lambda t: t.t == T.PAREN_OPEN),
            p.any('inner'),
            p.predicate(lambda t: t.t == T.PAREN_CLOSE),
        ]),
        lambda m: m['inner'],
    )

    yield from unop(p, T.OPERATOR_MINUS, 'negate')
    yield from unop(p, T.OPERATOR_DEREF, 'deref')
    yield from binop(p, T.OPERATOR_PLUS, 'add')
    yield from binop(p, T.OPERATOR_MINUS, 'sub')
    yield from binop(p, T.OPERATOR_TIMES, 'mul')
    yield from binop(p, T.OPERATOR_DIVIDE, 'div')

    yield (
        ast.AstNode('expr', p.any('position'), children=[
            p.any('namespace'),
            p.predicate(lambda t: t.t == T.OPERATOR_DOT),
            ast.AstNode('member', p.any(), children=[
                p.any('member'),
            ]),
        ]),
        lambda m: ast.AstNode('member_access', m['position'], attrs={
            'member': m['member'].text,
        }, children=[
            m['namespace'],
        ])
    )

    yield (
        ast.AstNode('expr', p.any('position'), children=[
            p.any('function'),
            p.predicate(lambda t: t.t == T.PAREN_OPEN),
            ast.AstNode('alist', p.any(), children=[
                p.zero_or_more_nodes('args'),
            ]),
            p.predicate(lambda t: t.t == T.PAREN_CLOSE),
        ]),
        lambda m: ast.AstNode('call', m['position'], attrs={
            'target': m['function'],
        }, children=m['args'])
    )

    # Collapse left-recursion on strings. TODO less string concatenation
    yield (
        ast.AstNode('string_inner', p.any(), children=[]),
        lambda m: ""
    )
    yield (
        ast.AstNode('string_inner', p.any(), children=[
            p.any('string0'),
            p.predicate(lambda t: t.t == T.STRING, key='string1'),
        ]),
        lambda m: m['string0'] + m['string1'].text
    )
    yield (
        ast.AstNode('string_inner', p.any(), children=[
            p.any('string0'),
            p.predicate(lambda t: t.t == T.STRING_ESCAPE, key='string1'),
        ]),
        lambda m: m['string0'] + m['string1'].text[1]
    )
    yield (
        ast.AstNode('string_start', p.any(), children=[
            p.any(),
            p.any('value'),
        ]),
        lambda m: m['value']
    )
    yield (
        ast.AstNode('string', p.any('position'), children=[
            p.any('value'),
            p.any(),
        ]),
        lambda m: ast.AstNode('string', m['position'], attrs={
            'value': m['value'],
        })
    )
