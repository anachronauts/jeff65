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
from .. import storage
from ... import ast, pattern
from ...pattern import Predicate as P


class AssemblyError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AsmRun:
    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return "<asm {}>".format(self.data)


@pattern.transform(pattern.Order.Any)
class AssembleWithRelocations:
    transform_attrs = False

    @pattern.match(
        ast.AstNode('lda', attrs={
            'storage': storage.ImmediateStorage(
                P('value'), P.require(1, AssemblyError)),
        }))
    def lda_imm(self, value):
        return AsmRun(struct.pack('<BB', 0xa9, value))

    @pattern.match(
        ast.AstNode('sta', attrs={
            'storage': storage.AbsoluteStorage(
                P('address'), P.require(1, AssemblyError)),
        }))
    def sta_abs(self, address):
        return AsmRun(struct.pack('<BH', 0x8d, address))

    @pattern.match(
        ast.AstNode('jmp', attrs={
            'storage': storage.AbsoluteStorage(P('address'), P.any()),
        }))
    def jmp(self, address):
        return AsmRun(struct.pack('<BH', 0x4c, address))

    @pattern.match(ast.AstNode('rts'))
    def rts(self):
        return AsmRun(b'\x60')


class FlattenSymbol(ast.TranslationPass):
    def exit_fun(self, node):
        return ast.AstNode('fun_symbol', span=node.span, attrs={
            'name': node.attrs['name'],
            'type': node.attrs['type'],
            'text': b"".join(c.data for c in node.children)
        })


def lda(arg, span):
    assert type(arg) is storage.ImmediateStorage
    return ast.AstNode('lda', span=span, attrs={
        'storage': arg,
        'size': 2,
    })


def sta(arg, span):
    assert type(arg) is storage.AbsoluteStorage
    return ast.AstNode('sta', span=span, attrs={
        'storage': arg,
        'size': 3,
    })


def jmp(arg, span):
    assert type(arg) is storage.AbsoluteStorage
    return ast.AstNode('jmp', span=span, attrs={
        'storage': arg,
        'size': 3,
    })


def rts(span):
    return ast.AstNode('rts', span=span, attrs={
        'size': 1,
    })
