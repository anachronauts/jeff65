# jeff65 pass scheduler
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

"""Automatic pass scheduler

Each pass is annotated with a list of tags it introduces, uses, and deletes.
Tags should include AST node names and metadata introduced. Even if the pass
does not delete all instances of an AST node, it should still list it as
deleted.

Passes are ordered such that all introductions of a node precede all uses and
deletions of it, and all uses precede all deletions.
"""

import collections.abc
import jeff65
from .graph import Graph, Node


def create_schedule(passes):
    g = Graph(
        (Node(p) for p in passes), stable=jeff65.debugopts["unstable_pass_schedule"]
    )
    assert all(
        isinstance(n.value.introduces, collections.abc.Set)
        and isinstance(n.value.uses, collections.abc.Set)
        and isinstance(n.value.deletes, collections.abc.Set)
        for n in g
    )
    for nf in g:
        for n0 in g:
            if n0 is not nf and _depends(n0.value, nf.value):
                g.add_edge(nf, n0)
    return [n.value for n in g.sorted()]


def _depends(p0, pf):
    """Tests whether pf depends on p0."""
    return (
        any(p0.introduces & pf.uses)
        or any(p0.introduces & pf.deletes)
        or any(p0.uses & pf.deletes)
    )
