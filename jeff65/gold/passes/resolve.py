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
from .. import ast, mem
from ..storage import AbsoluteStorage, ImmediateStorage


class ResolveStorage(ast.TranslationPass):
    def enter_deref(self, node):
        assert node.children[0].t == 'numeric'
        return AbsoluteStorage(node.children[0].attrs['value'],
                               node.attrs['type'].width)

    def enter_numeric(self, node):
        assert node.attrs['value'] < 256
        return ImmediateStorage(node.attrs['value'], 1)


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
