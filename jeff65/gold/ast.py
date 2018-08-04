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

    def transform(self, transformer, always_list=False):
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
                    children.extend(child.transform(transformer, always_list))
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

        if not always_list and self.t == 'unit':
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
