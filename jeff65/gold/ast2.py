# jeff65 gold-syntax AST transformer stage 2
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

from . import ast


class FlatLetNode:
    def __init__(self, position, text):
        self.position = position
        self.text = text
        self.storage = None
        self.name = None
        self.t = None
        self.value = None

    def __repr__(self):
        return f"(let' {self.storage} {self.name}: {self.t} = {self.value})"

    @classmethod
    def visit(cls, node):
        if type(node) is not ast.StatementLetNode:
            return node

        let = cls(node.position, node.text)
        n = node.rhs
        if type(n) is ast.StorageClassNode:
            let.storage = n.text
            n = n.rhs
        if type(n) is not ast.OperatorAssignNode:
            raise ast.ParseError("expected =", n.position)
        let.value = n.rhs
        n = n.lhs
        if type(n) is not ast.PunctuationValueTypeNode:
            raise ast.ParseError("expected variable type", n.position)
        let.name = n.lhs
        let.t = n.rhs
        return let

    def traverse(self, visit):
        self.value = self.value.traverse(visit)
        return visit(self)


transformations = [
    FlatLetNode.visit,
]


def transform2(tree):
    for xform in transformations:
        tree = tree.traverse(xform)
    return tree
