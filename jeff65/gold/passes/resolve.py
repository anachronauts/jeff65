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
from .. import ast, mem, pattern
from ..storage import AbsoluteStorage, ImmediateStorage


@pattern.transform(pattern.Order.Descending)
def ResolveStorage(p):
    yield (
        ast.AstNode('deref', p.any(), attrs={
            'type': p.any('type'),
        }, children=[
            ast.AstNode(p.require('numeric'), p.any(), attrs={
                'value': p.any('address'),
            })
        ]),
        lambda m: AbsoluteStorage(m['address'], m['type'].width)
    )

    yield (
        ast.AstNode('numeric', p.any(), attrs={
            'value': p.lt(256, 'value', require=True)
        }),
        lambda m: ImmediateStorage(m['value'], 1)
    )


class ResolveUnits(binding.ScopedPass):
    """Resolves external units identified in 'use' statements."""

    builtin_units = {
        'mem': mem.MemUnit(),
    }

    def exit_use(self, node):
        name = node.attrs['name']
        unit = self.builtin_units[name]
        self.bind_name(name, unit)
        return []


class ResolveMembers(binding.ScopedPass):
    """Resolves members to functions."""

    transform_attrs = True

    def exit_member_access(self, node):
        member = node.attrs['member']
        name = node.children[0].attrs['name']
        unit = self.look_up_name(name)
        return unit.member(member)
