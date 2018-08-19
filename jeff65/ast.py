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
    span = attr.ib(default=None, cmp=False)

    def update_attrs(self, attrs):
        nn = attr.evolve(self, attrs=self.attrs.update(attrs))
        assert self is not nn
        return nn

    def replace_attrs(self, attrs):
        nn = attr.evolve(self, attrs=FrozenDict.create(attrs))
        assert self is not nn
        return nn

    def transform(self, transformer):
        node = transformer.transform_enter(self.t, self)

        if hasattr(node, "attrs"):
            # because we're iterating over a FrozenDict, we'll get the
            # attributes in sorted order. Therefore, we can use the faster
            # unsafeset to put them into the builder.
            attrs = FrozenDict.Builder.empty()
            dirty = False
            for n, v in node.attrs.items():
                if hasattr(v, "transform"):
                    tv = v.transform(transformer)
                    attrs.unsafeset(n, tv)
                    if v is not tv:
                        dirty = True
                else:
                    attrs.unsafeset(n, v)
            if dirty:
                node = node.replace_attrs(attrs)

        return transformer.transform_exit(self.t, node)

    def __repr__(self):
        return f"<ast {self.t} at {self.span}>"

    def __format__(self, spec):
        if spec == 'p':
            return self.pretty()
        return repr(self)

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
        has_next = False
        for name, value in self.attrs.items():
            if name == 'next':
                has_next = True
                continue  # we'll come back to this one
            if hasattr(value, "_pretty"):
                pp.append("{}:{} ".format(i(), name))
                pp.append(value._pretty(indent + 2 + len(name),
                                        no_position).lstrip())
            else:
                pp.append("{}:{} {!r}\n".format(i(), name, value))
        if has_next:
            # print this at the same level
            nxt = self.attrs['next']
            if hasattr(nxt, "_pretty"):
                pp.append(nxt._pretty(indent, no_position))
            elif nxt is not None:
                pp.append('{}{!r}'.format(i(), nxt))
        return "".join(pp)

    @classmethod
    def make_sequence(cls, t_seq, a_elem, elems, rest=None):
        n = rest
        for e in reversed(elems):
            n = cls(t_seq, {
                a_elem: e,
                'next': n,
            })
        return n

    def select(self, *attrs):
        current = [self]
        for a in attrs:
            found = []
            while len(current) > 0:
                c = current.pop()
                if c is None:
                    continue
                found.append(c.attrs[a])
                if "next" in c.attrs:
                    current.append(c.attrs["next"])
            current = found

        return current


class TranslationPass:
    """Base class for translation passes."""

    def transform_enter(self, t, node):
        return getattr(self, f'enter_{t}', self.__generic_enter)(node)

    def transform_exit(self, t, node):
        return getattr(self, f'exit_{t}', self.__generic_exit)(node)

    def __generic_enter(self, node):
        return node

    def __generic_exit(self, node):
        return node
