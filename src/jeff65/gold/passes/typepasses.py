# jeff65 gold-syntax type-related passes
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

from . import binding
from ... import ast
from ...blum import types


class ConstructTypes(ast.TranslationPass):
    builtin_types = {
        'u8': types.u8, 'u16': types.u16, 'u24': types.u24, 'u32': types.u32,
        'i8': types.i8, 'i16': types.i16, 'i24': types.i24, 'i32': types.i32,
    }

    def enter_unit(self, node):
        # TODO scoping for when we import types from other units
        self.known_types = self.builtin_types
        return node

    def enter_type_ref(self, node):
        inner_type = self.known_types[node.attrs['type']]
        return types.RefType(inner_type)


class PropagateTypes(binding.ScopedPass):
    def enter_identifier(self, node):
        t = self.look_up_name(node.attrs['name'])
        return node.update_attrs({"type": t})

    def exit_deref(self, node):
        return node.update_attrs({
            "type": node.select("address", "type")[0].target,
        })

    def exit_set(self, node):
        return node.update_attrs({
            "type": node.select("lvalue", "type")[0],
        })

    def enter_fun(self, node):
        attrs = node.attrs.asbuilder()
        attrs['type'] = types.FunctionType(
            node.attrs['return'] or types.void,
            *node.select("args", "arg"))
        del attrs['return']
        return node.replace_attrs(attrs)
