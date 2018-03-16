# jeff65 gold-syntax lowering passes
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


class LowerAssignment(ast.TranslationPass):
    def exit_set(self, node):
        lhs = node.children[0]
        rhs = node.children[1]
        assert node.attrs['type'].width == lhs.width
        assert node.attrs['type'].width == rhs.width

        return [
            ast.AstNode('lda', node.position, attrs={
                'storage': rhs,
                'size': 2,
            }),
            ast.AstNode('sta', node.position, attrs={
                'storage': lhs,
                'size': 3,
            }),
        ]


class LowerFunctions(ast.TranslationPass):
    def exit_fun(self, node):
        body_size = sum(c.attrs['size'] for c in node.children)
        ret = ast.AstNode('jmp', node.position, attrs={
            'storage': storage.ImmediateStorage(0, 2),
            'size': 3,
        })
        node = node.clone(with_attrs={
            'return_addr': body_size + 1,
        })
        node.children.append(ret)
        return node
