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
from ... import ast, pattern
from ...pattern import Predicate as P


class AssemblyError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def asmrun(fmt, *args):
    return ast.AstNode('asmrun', attrs={
        'bin': struct.pack(fmt, *args)
    })


@pattern.transform(pattern.Order.Any)
class AssembleWithRelocations:
    transform_attrs = False

    @pattern.match(
        ast.AstNode('lda', children=[
            ast.AstNode('immediate_storage', attrs={
                'value': P('value'),
                'width': P.require(1, AssemblyError),
            })
        ]))
    def lda_imm(self, value):
        return asmrun('<BB', 0xa9, value)

    @pattern.match(
        ast.AstNode('sta', children=[
            ast.AstNode('absolute_storage', attrs={
                'address': P('address'),
                'width': P.require(1, AssemblyError),
            })
        ]))
    def sta_abs(self, address):
        return asmrun('<BH', 0x8d, address)

    @pattern.match(
        ast.AstNode('jmp', children=[
            ast.AstNode('absolute_storage', attrs={
                'address': P('address'),
            })
        ]))
    def jmp(self, address):
        return asmrun('<BH', 0x4c, address)

    @pattern.match(ast.AstNode('rts'))
    def rts(self):
        return asmrun('<B', 0x60)


@pattern.transform(pattern.Order.Any)
class FlattenSymbol:
    transform_attrs = False

    @pattern.match(
        ast.AstNode('fun', attrs={
            'name': P('name'),
            'type': P('ty'),
        }, children=[
            P.zero_or_more_nodes('asmruns', allow='asmrun')
        ]))
    def fun(self, name, ty, asmruns):
        return ast.AstNode('fun_symbol', attrs={
            'name': name,
            'type': ty,
            'text': b"".join(r.attrs['bin'] for r in asmruns)
        })


def lda(arg, span):
    return ast.AstNode('lda', span=span, attrs={
        'size': 2,
    }, children=[arg])


def sta(arg, span):
    return ast.AstNode('sta', span=span, attrs={
        'size': 3,
    }, children=[arg])


def jmp(arg, span):
    return ast.AstNode('jmp', span=span, attrs={
        'size': 3,
    }, children=[arg])


def rts(span):
    return ast.AstNode('rts', span=span, attrs={
        'size': 1,
    })
