# jeff65 AST manipulation
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

import attr
from .immutable import FrozenDict


@attr.s(slots=True, frozen=True, repr=False)
class AstNode:
    t = attr.ib()
    attrs = attr.ib(factory=FrozenDict.empty, converter=FrozenDict.create)
    children = attr.ib(factory=tuple, converter=tuple)
    span = attr.ib(default=None, cmp=False)

    def evolve(self, update_attrs=None, with_attrs=None, with_children=None):
        if update_attrs is not None and with_attrs is not None:
            raise ValueError("both update_attrs and with_attrs were provided")

        attrs = self.attrs
        if update_attrs is not None:
            attrs = attrs.update(update_attrs)
        elif with_attrs is not None:
            attrs = FrozenDict.create(with_attrs)

        children = self.children
        if with_children is not None:
            children = with_children

        return attr.evolve(self, attrs=attrs, children=children)

    def transform(self, transformer, always_list=False):
        node = transformer.transform_enter(self.t, self)

        if transformer.transform_attrs and isinstance(node, AstNode):
            attrs = FrozenDict.Builder.empty()

            # because we're iterating over a FrozenDict, we'll get the
            # attributes in sorted order. Therefore, we can use the faster
            # unsafeset to put them into the builder.
            dirty = False
            for n, v in node.attrs.items():
                if type(v) is AstNode:
                    tv = v.transform(transformer)
                    if not tv:
                        dirty = True
                        continue
                    assert len(tv) == 1
                    attrs.unsafeset(n, tv[0])
                    if v is not tv[0]:
                        dirty = True
                else:
                    attrs.unsafeset(n, v)

            if dirty:
                node = attr.evolve(node, attrs=attrs)

        if type(node) is AstNode:
            dirty = False
            children = []
            for child in node.children:
                if not hasattr(child, "transform"):
                    children.append(child)
                    continue
                transformed = child.transform(transformer, always_list)
                children.extend(transformed)
                if len(transformed) != 1 or transformed[0] is not child:
                    dirty = True
            if dirty:
                node = attr.evolve(node, children=children)

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
        return f"<ast {self.t} at {self.span}>"

    def pretty(self, indent=0, no_position=False):
        return self._pretty(indent, no_position).strip()

    def _pretty(self, indent, no_position):
        def i(n=0):
            return " " * (indent + n)

        pp = []

        if no_position:
            pp.append("{}{}\n".format(i(), self.t))
        else:
            pp.append("{}{:<{}} {}\n".format(i(), self.t, 70 - indent,
                                             self.span))
        for name, value in self.attrs.items():
            if hasattr(value, "_pretty"):
                pp.append("{}:{} ".format(i(2), name))
                pp.append(value._pretty(indent + 4 + len(name),
                                        no_position).lstrip())
            else:
                pp.append("{}:{} {!r}\n".format(i(2), name, value))
        for child in self.children:
            if hasattr(child, "_pretty"):
                pp.append(child._pretty(indent + 2, no_position))
            else:
                pp.append("{}{!r}\n".format(i(2), child))
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
