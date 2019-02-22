# jeff65 graph manipulation
# Copyright (C) 2019  jeff65 maintainers
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
import random


class TopologyError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@attr.s(slots=True, cmp=False)
class Node:
    # N.B. we use a list of links to guarantee stable order; a set would result
    # in different output each run.
    value = attr.ib()
    links = attr.ib(factory=list, converter=list)


class Graph:
    def __init__(self, nodes=None, stable=True):
        # Keep track of order; by traversing nodes in a consistent order, we
        # can ensure consistent output (if we need to).

        self._nodelist = [] if nodes is None else list(nodes)
        self._nodes = set(self._nodelist)
        self._stable = stable
        self._sorted = None

    @property
    def nodes(self):
        return set(self._nodes)

    def __iter__(self):
        return iter(self._nodelist)

    def add_node(self, node):
        if node not in self.nodes:
            self._nodelist.append(node)
            self._nodes.add(node)
        for n in node.links:
            self.add_node(n)

    def add_edge(self, start, end):
        if start not in self._nodes:
            raise TopologyError("start node not in graph")
        if end not in self._nodes:
            raise TopologyError("end node not in graph")
        start.links.append(end)
        self._sorted = None

    def _sort(self):
        # DFS topological sort per Tarjan (1976). All nodes start out in the
        # white set. We perform a recursive DFS, marking nodes grey on the way
        # down and black on the way up, emitting them as we mark them black.

        # If we end up having to work with graphs so big that we end up blowing
        # out the stack, consider switching to the Kahn (1962) algorithm, which
        # is non-recursive, but more irritating to implement as it requires
        # making a copy of the graph to modify destructively.

        white = list(self._nodelist)
        if not self._stable:
            random.shuffle(white)

        black = set()
        grey = set()

        def darken(n):
            if n in black:
                return
            if n in grey:
                raise TopologyError("Not a DAG")

            grey.add(n)
            for m in n.links:
                yield from darken(m)
            grey.remove(n)
            black.add(n)
            yield n

        while len(white) > 0:
            yield from darken(white.pop())

    def sorted(self):
        if self._sorted is None:
            self._sorted = list(self._sort())
        return self._sorted
