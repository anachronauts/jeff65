# jeff65 gold-syntax name binding
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

from ... import ast
from ...immutable import FrozenDict


class ScopedPass(ast.TranslationPass):
    """Base class for translation passes which understand binding scope.
    """
    scoped_types = ['unit', 'fun']

    def __init__(self):
        self.scopes = []

    def bind_name(self, name, value):
        self.scopes[-1]['known_names'][name] = value

    def look_up_name(self, name):
        for scope in reversed(self.scopes):
            known_names = scope['known_names']
            if name in known_names:
                return known_names[name]
        return None

    def bind_constant(self, name, value):
        self.scopes[-1]['known_constants'][name] = value

    def look_up_constant(self, name):
        for scope in reversed(self.scopes):
            known_constants = scope['known_constants']
            if name in known_constants:
                return known_constants[name]
        return None

    def transform_enter(self, t, node):
        node = super().transform_enter(t, node)
        if t in self.scoped_types:
            self.scopes.append({
                "known_names": node.attrs.get(
                    "known_names", FrozenDict.empty()).asbuilder(),
                "known_constants": node.attrs.get(
                    "known_constants", FrozenDict.empty()).asbuilder(),
            })
            node = self.enter__scope(node)
        return node

    def transform_exit(self, t, node):
        if t in self.scoped_types:
            node = self.exit__scope(node)
        if t in self.scoped_types:
            node = node.update_attrs(
                {k: v.asfrozen() for k, v in self.scopes.pop().items()})
        node = super().transform_exit(t, node)
        return node

    def enter__scope(self, node):
        return node

    def exit__scope(self, node):
        return node


class ShadowNames(ScopedPass):
    """Binds names to dummy values, to be overridden later.

    This allows us to determine whether module names are shadowed while
    constructing types.
    """

    def exit_constant(self, node):
        self.bind_name(node.attrs['name'], True)
        return node


class BindNamesToTypes(ScopedPass):
    """Binds names to types. These are later overridden by the storage."""

    def exit_constant(self, node):
        self.bind_name(node.attrs['name'], node.attrs['type'])
        return node


class EvaluateConstants(ScopedPass):
    def __init__(self):
        super().__init__()
        self.evaluating = False

    def enter_constant(self, node):
        self.evaluating = True
        return node

    def exit_constant(self, node):
        self.evaluating = False
        self.bind_constant(node.attrs['name'], node.attrs["value"])
        return None

    def exit_toplevel(self, node):
        if node.attrs["stmt"] is None:
            return node.attrs["next"]
        return node

    def exit_call(self, node):
        target = node.attrs['target']
        return target(*node.select("args", "arg"))


class ResolveConstants(ScopedPass):
    def exit_identifier(self, node):
        value = self.look_up_constant(node.attrs['name'])
        if not value:
            return node
        return value
