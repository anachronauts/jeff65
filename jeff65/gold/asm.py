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

from . import ast, storage


class AsmRun:
    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return "<asm {}>".format(self.data)


class AssembleWithRelocations(ast.TranslationPass):
    def enter_lda(self, node):
        s = node.attrs['storage']
        assert s.width == 1
        if type(s) is storage.ImmediateStorage:
            return AsmRun(bytes([0xa9, s.value]))
        assert False

    def enter_sta(self, node):
        s = node.attrs['storage']
        assert s.width == 1
        if type(s) is storage.AbsoluteStorage:
            hi = (s.address >> 8) & 0xff
            lo = s.address & 0xff
            return AsmRun(bytes([0x8d, lo, hi]))
        assert False

    def enter_jmp(self, node):
        s = node.attrs['storage']
        assert s.width == 2
        if type(s) is storage.ImmediateStorage:
            hi = (s.value >> 8) & 0xff
            lo = s.value & 0xff
            return AsmRun(bytes([0x4c, lo, hi]))
        assert False


class FlattenSymbol(ast.TranslationPass):
    def exit_fun(self, node):
        data = []
        for c in node.children:
            data.append(c.data)

        return ast.AstNode('fun_symbol', node.position, {
            'name': node.attrs['name'],
            'type': node.attrs['type'],
            'return_addr': node.attrs['return_addr'],
            'data': b"".join(data),
        })

    def exit_unit(self, node):
        node = node.clone()
        del node.attrs['known_names']
        return node
