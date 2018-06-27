# jeff65 gold-syntax assembler passes
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

import struct
from .. import ast, pattern


class AssemblyError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def asmrun(pos, fmt, *args):
    return ast.AstNode('asmrun', pos, attrs={
        'bin': struct.pack(fmt, *args)
    })


@pattern.transform(pattern.Order.Any)
def AssembleWithRelocations(p):
    yield (
        ast.AstNode('lda', p.any('pos'), children=[
            ast.AstNode('immediate_storage', p.any(), attrs={
                'value': p.any('value'),
                'width': p.require(1, AssemblyError),
            })
        ]),
        lambda m: asmrun(m['pos'], '<BB', 0xa9, m['value'])
    )

    yield (
        ast.AstNode('sta', p.any('pos'), children=[
            ast.AstNode('absolute_storage', p.any(), attrs={
                'address': p.any('address'),
                'width': p.require(1, AssemblyError),
            })
        ]),
        lambda m: asmrun(m['pos'], '<BH', 0x8d, m['address'])
    )

    yield (
        ast.AstNode('jmp', p.any('pos'), children=[
            ast.AstNode('absolute_storage', p.any(), attrs={
                'address': p.any('address'),
            })
        ]),
        lambda m: asmrun(m['pos'], '<BH', 0x4c, m['address'])
    )

    yield (ast.AstNode('rts', p.any('pos')),
           lambda m: asmrun(m['pos'], '<B', 0x60))


@pattern.transform(pattern.Order.Any)
def FlattenSymbol(p):
    yield (
        ast.AstNode('fun', p.any('pos'), attrs={
            'name': p.any('name'),
            'type': p.any('type'),
        }, children=[
            p.zero_or_more_nodes('asmruns', allow='asmrun')
        ]),
        lambda m: ast.AstNode('fun_symbol', m['pos'], attrs={
            'name': m['name'],
            'type': m['type'],
            'text': b"".join(r.attrs['bin'] for r in m['asmruns']),
        })
    )


def lda(position, arg):
    return ast.AstNode('lda', position, attrs={
        'size': 2,
    }, children=[arg])


def sta(position, arg):
    return ast.AstNode('sta', position, attrs={
        'size': 3,
    }, children=[arg])


def jmp(position, arg):
    return ast.AstNode('jmp', position, attrs={
        'size': 3,
    }, children=[arg])


def rts(position):
    return ast.AstNode('rts', position, attrs={
        'size': 1,
    })
