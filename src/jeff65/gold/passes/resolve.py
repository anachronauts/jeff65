# jeff65 gold-syntax resolution passes
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

from . import binding
from .. import mem
from ... import ast, pattern
from ...pattern import Predicate as P


@pattern.transform(pattern.Order.Descending)
class ResolveStorage:
    @pattern.match(
        ast.AstNode('deref', attrs={
            'type': P('ty'),
            'address': ast.AstNode(P.require('numeric'), attrs={
                'value': P('address'),
            }),
        }))
    def deref_to_absolute(self, ty, address):
        return ast.AstNode('absolute_storage', attrs={
            'address': address,
            'width': ty.width
        })

    @pattern.match(
        ast.AstNode('numeric', attrs={
            'value': P.lt(256, 'value', require=True),
        }))
    def numeric_to_immediate(self, value):
        return ast.AstNode('immediate_storage', attrs={
            'value': value,
            'width': 1,
        })


class ResolveUnits(binding.ScopedPass):
    """Resolves external units identified in 'use' statements."""

    builtin_units = {
        'mem': mem.MemUnit(),
    }

    def exit_use(self, node):
        name = node.attrs['name']
        unit = self.builtin_units[name]
        self.bind_name(name, unit)
        return None

    def exit_toplevel(self, node):
        if node.attrs["stmt"] is None:
            return node.attrs["next"]
        return node


class ResolveMembers(binding.ScopedPass):
    """Resolves members to functions."""

    def exit_member_access(self, node):
        member = node.attrs['member']
        name = node.attrs['namespace'].attrs['name']
        unit = self.look_up_name(name)
        return unit.member(member)
