# jeff65 AST structure manipulation
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


@attr.s(slots=True, repr=False)
class AstNode:
    t = attr.ib()
    position = attr.ib(default=None, cmp=False, hash=False)
    attrs = attr.ib(factory=dict)
    children = attr.ib(factory=list)

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

        if not always_list and self.t == 'unit':
            assert len(nodes) == 1
            return nodes[0]
        return nodes

    def __repr__(self):
        if self.position is None:
            return "<ast {}>".format(self.t)
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
        for a, value in self.attrs.items():
            if type(value) is AstNode:
                pp.append("{}:{} ".format(i(2), a))
                pp.append(value._pretty(indent + 4 + len(a),
                                        no_position).lstrip())
            else:
                pp.append("{}:{} {}\n".format(i(2), a, repr(value)))
        for child in self.children:
            if type(child) is AstNode:
                pp.append(child._pretty(indent + 2, no_position))
            else:
                pp.append("{}{}\n".format(i(2), repr(child)))
        return "".join(pp)

    def dump(self, f):
        from . import sexp
        sexp.dump(f, self._il_serialize())

    def dumps(self):
        from . import sexp
        return sexp.dumps(self._il_serialize())

    def _il_serialize(self):
        nodes = self.transform(IlSerializer(), always_list=True)
        assert len(nodes) == 1
        return nodes[0]


class IlSerializer:
    transform_attrs = True

    def transform_enter(self, t, node):
        return node

    def transform_exit(self, t, node):
        from . import sexp
        at = sexp.satom('@' + t)
        if node.position is None:
            pos = sexp.snil()
        else:
            pos = sexp.slist(
                children=[sexp.snumeric(v) for v in node.position])

        attrs = []
        for k, v in node.attrs.items():
            attrs.append(sexp.slist(children=[
                sexp.satom(k),
                self._convert(v)]))
        return sexp.slist(children=[
            at,
            pos,
            sexp.slist(children=attrs),
            *node.children,
        ])

    @classmethod
    def _convert(cls, value):
        from . import sexp
        try:
            return value._il_serialize()
        except AttributeError:
            pass

        if isinstance(value, dict):
            return sexp.slist(children=[
                sexp.satom('dict'),
                *(sexp.slist(children=[
                    sexp.satom('list'),
                    sexp.sstring(k),
                    cls._convert(v),
                ]) for k, v in value.items())
            ])
        elif isinstance(value, bytes):
            return sexp.slist(children=[
                sexp.satom('bytes'),
                *(sexp.snumeric(v) for v in value)
            ])
        elif value is None:
            return sexp.snil()
        elif isinstance(value, int):
            return sexp.snumeric(value)
        elif isinstance(value, bool):
            return sexp.sboolean(value)
        elif isinstance(value, str):
            return sexp.sstring(value)
        elif isinstance(value, list):
            return sexp.slist(children=value)
        else:
            raise Exception(f"Don't know how to cope with {value}")
