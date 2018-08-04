# jeff65 gold-syntax AST manipulation
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

from .grammar import ParseListener


class ParseError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AstNode:
    def __init__(self, t, position, attrs=None, children=None):
        self.t = t
        self.position = position
        self.attrs = attrs or {}
        self.children = children or []

    def clone(self, with_attrs=None, with_children=None):
        node = AstNode(self.t, self.position, dict(self.attrs),
                       list(with_children or self.children))
        if with_attrs:
            node.attrs.update(with_attrs)
        return node

    def get_attr_default(self, attr, default_value):
        if attr not in self.attrs:
            self.attrs[attr] = default_value
        return self.attrs[attr]

    def __eq__(self, other):
        return (
            type(other) is AstNode
            and self.t == other.t
            and self.attrs == other.attrs
            and self.children == other.children)

    def transform(self, transformer):
        node = transformer.transform_enter(self.t, self)

        if transformer.transform_attrs and type(node) is AstNode:
            attrs = {}
            for n, v in node.attrs.items():
                if type(v) is AstNode:
                    tv = v.transform(transformer)
                    if tv:
                        assert len(tv) == 1
                        attrs[n] = tv[0]
                else:
                    attrs[n] = v
            if attrs != node.attrs:
                if node is self:
                    node = node.clone()
                node.attrs = attrs

        if type(node) is AstNode:
            children = []
            for child in node.children:
                if type(child) is AstNode:
                    children.extend(child.transform(transformer))
                else:
                    children.append(child)
            if children != node.children:
                if node is self:
                    node = node.clone()
                node.children = children

        nodes = transformer.transform_exit(self.t, node)

        if type(nodes) is None:
            nodes = []
        elif type(nodes) is not list:
            nodes = [nodes]

        if self.t == 'unit':
            assert len(nodes) == 1
            return nodes[0]
        return nodes

    def __repr__(self):
        if self.position is None:
            return f"<ast {self.t} at ???>"
        return "<ast {} at {}:{}>".format(self.t, *self.position)

    def pretty(self, indent=0, no_position=False):
        return self._pretty(indent, no_position).strip()

    def _pretty(self, indent, no_position):
        def i(n=0):
            return " " * (indent + n)

        pp = []

        if no_position:
            pp.append("{}{}\n".format(i(), self.t))
        else:
            pp.append("{}{:<{}} {}:{}\n".format(i(), self.t, 70 - indent,
                                                *self.position))
        for attr, value in self.attrs.items():
            if type(value) is AstNode:
                pp.append("{}:{} ".format(i(2), attr))
                pp.append(value._pretty(indent + 4 + len(attr),
                                        no_position).lstrip())
            else:
                pp.append("{}:{} {}\n".format(i(2), attr, repr(value)))
        for child in self.children:
            if type(child) is AstNode:
                pp.append(child._pretty(indent + 2, no_position))
            else:
                pp.append("{}{}\n".format(i(2), repr(child)))
        return "".join(pp)


class TranslationPass:
    """Base class for translation passes."""

    transform_attrs = False

    def transform_enter(self, t, node):
        return getattr(self, f'enter_{t}', self.__generic_enter)(node)

    def transform_exit(self, t, node):
        return getattr(self, f'exit_{t}', self.__generic_exit)(node)

    def __generic_enter(self, node):
        return node

    def __generic_exit(self, node):
        return [node]


class AstBuilder(ParseListener):
    def __init__(self):
        self.stack = []

    @property
    def ast(self):
        return self.stack[0]

    def _push(self, node):
        self.stack.append(node)

    def _pop(self):
        c = self.stack.pop()
        self.stack[-1].children.append(c)
        return c

    def _pop_attr(self, attr):
        a = self.stack.pop()
        self.stack[-1].attrs[attr] = a

    def _pos(self, ctx):
        return (ctx.start.line, ctx.start.column)

    def enterUnit(self, ctx):
        self._push(AstNode("unit", self._pos(ctx)))

    def enterStmtUse(self, ctx):
        self._push(AstNode("use", self._pos(ctx), {
            "name": ctx.unitId.text
        }))

    def exitStmtUse(self, ctx):
        self._pop()

    def enterStmtConstant(self, ctx):
        self._push(AstNode("constant", self._pos(ctx), {
            "name": ctx.declaration().name.text
        }))

    def exitStmtConstant(self, ctx):
        self._pop()

    def enterStmtLet(self, ctx):
        node = AstNode("let", self._pos(ctx))
        node.attrs['name'] = ctx.declaration().name.text
        if ctx.storage():
            node.attrs['storage'] = ctx.storage().storage_class.text
        self._push(node)

    def exitStmtLet(self, ctx):
        self._pop()

    def enterStmtFun(self, ctx):
        self._push(AstNode("fun", self._pos(ctx), {
            "name": ctx.name.text,
            'return': None,
            'args': [],
        }))

    def exitStmtFun(self, ctx):
        self._pop()

    def enterStmtAssignVal(self, ctx):
        self._push(AstNode("set", self._pos(ctx)))

    def exitStmtAssignVal(self, ctx):
        self._pop()

    def enterTypePrimitive(self, ctx):
        self.stack[-1].attrs["type"] = ctx.name.text

    def enterTypePointer(self, ctx):
        self._push(AstNode("type_ref", self._pos(ctx)))

    def exitTypePointer(self, ctx):
        self._pop_attr("type")

    def enterTypeArray(self, ctx):
        self._push(AstNode('type_array', self._pos(ctx)))

    def exitTypeArray(self, ctx):
        self._pop_attr('type')

    def enterExprMember(self, ctx):
        self._push(AstNode("member_access", self._pos(ctx), {
            "member": ctx.member.text
        }))

    def exitExprMember(self, ctx):
        self._pop()

    def enterExprId(self, ctx):
        self.stack[-1].children.append(AstNode("identifier", self._pos(ctx), {
            'name': ctx.name.text,
        }))

    def enterExprNumber(self, ctx):
        text = ctx.value.text.lower()
        if text.startswith('0x'):
            value = int(text[2:], 16)
        elif text.startswith('0o'):
            value = int(text[2:], 8)
        elif text.startswith('0b'):
            value = int(text[2:], 2)
        else:
            value = int(text)
        self.stack[-1].children.append(AstNode("numeric", self._pos(ctx), {
            'value': value,
        }))

    def enterExprFunCall(self, ctx):
        self._push(AstNode("call", self._pos(ctx)))

    def exitExprFunCall(self, ctx):
        call = self.stack[-1]
        call.attrs['target'] = call.children[0]
        call.children = call.children[1:]
        self._pop()

    def enterExprDeref(self, ctx):
        self._push(AstNode("deref", self._pos(ctx)))

    def exitExprDeref(self, ctx):
        self._pop()

    def enterExprSum(self, ctx):
        if ctx.op.text == '+':
            self._push(AstNode("add", self._pos(ctx)))
        elif ctx.op.text == '-':
            self._push(AstNode("sub", self._pos(ctx)))
        else:
            assert False

    def exitExprSum(self, ctx):
        self._pop()

    def enterExprProduct(self, ctx):
        if ctx.op.text == '*':
            self._push(AstNode("mul", self._pos(ctx)))
        elif ctx.op.text == '/':
            self._push(AstNode("div", self._pos(ctx)))
        else:
            assert False

    def exitExprProduct(self, ctx):
        self._pop()

    def enterExprNegation(self, ctx):
        self._push(AstNode("negate", self._pos(ctx)))

    def exitExprNegation(self, ctx):
        self._pop()

    def enterString(self, ctx):
        self.stack[-1].children.append(AstNode('string', self._pos(ctx), {
            'value': "".join(s.text for s in ctx.s),
        }))
