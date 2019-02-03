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

from . import asm
from ... import ast, pattern
from ...pattern import Predicate as P


@pattern.transform(pattern.Order.Any)
class LowerAssignment:
    @pattern.match(
        ast.AstNode("block", {
            "stmt": ast.AstNode("set", span=P("span"), attrs={
                "type": P("ty"),
                "lvalue": P("lvalue"),
                "rvalue": P("rvalue"),
            }),
            "next": P("nxt"),
        }))
    def lower_set(self, span, ty, lvalue, rvalue, nxt):
        assert ty.width == lvalue.attrs["width"]
        assert ty.width == rvalue.attrs["width"]
        return ast.AstNode.make_sequence("block", "stmt", [
            asm.lda(rvalue, span),
            asm.sta(lvalue, span),
        ], rest=nxt)


class LowerFunctions(ast.TranslationPass):
    def exit_fun(self, node):
        children = node.select("body", "stmt")
        children.append(asm.rts(node.span))
        return node.update_attrs({
            "body": ast.AstNode.make_sequence("block", "stmt", children),
        })
