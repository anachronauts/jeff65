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

from . import ast


class ScopedPass(ast.TranslationPass):
    """Base class for translation passes which understand binding scope.
    """

    def __init__(self):
        self.scopes = []

    def bind_name(self, name, value):
        known_names = self.scopes[-1].get_attr_default('known_names', {})
        known_names[name] = value

    def look_up_name(self, name):
        for scope in reversed(self.scopes):
            known_names = scope.get_attr_default('known_names', {})
            if name in known_names:
                return known_names[name]
        return None

    def bind_constant(self, name, value):
        known_constants = self.scopes[-1].get_attr_default('known_constants',
                                                           {})
        known_constants[name] = value

    def look_up_constant(self, name):
        for scope in reversed(self.scopes):
            known_constants = scope.get_attr_default('known_constants', {})
            if name in known_constants:
                return known_constants[name]
        return None

    def enter__scope(self, node):
        # we MUST clone the node here in order to deal with the fact that the
        # children could be altered either by the transform function or by the
        # pass itself. By cloning once, we assure that changes made will be to
        # the same object.
        node = node.clone()
        self.scopes.append(node)
        return node

    def exit__scope(self, node):
        self.scopes.pop()
        return node

    def enter_unit(self, node):
        return self.enter__scope(node)

    def exit_unit(self, node):
        return self.exit__scope(node)

    def enter_fun(self, node):
        return self.enter__scope(node)

    def exit_fun(self, node):
        return self.exit__scope(node)


class ExplicitScopes(ast.TranslationPass):
    """Translation pass to make lexical scopes explicit.

    Introducing a binding inside a function results in a new implicit scope
    being introduced, which continues to the end of the explicit scope, i.e.
    let-bindings, constant-bindings, and use-bindings are not valid before they
    are mentioned inside function scope. For example, the following tree:

    fun
      :name 'foo'
      call
        :target 'spam'
      let
        :name 'bar'
        :type u8
        42
      call
        :target 'eggs'
        'bar'

    should be transformed into

    fun
      :name 'foo'
      call
        :target 'spam'
      let_s
        :name 'bar'
        :type u8
        42
        call
          :target 'eggs'
          'bar'

    Note that the call to 'eggs' now explicitly has 'bar' in-scope.

    This does not apply to toplevel declarations; all toplevel declarations are
    in scope throughout the unit.

    """
    pass  # TODO implement me


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
        self.bind_constant(node.attrs['name'], node.children[0])
        return []

    def exit_call(self, node):
        target = node.attrs['target']
        return target(*node.children)


class ResolveConstants(ScopedPass):
    def exit_identifier(self, node):
        value = self.look_up_constant(node.attrs['name'])
        if not value:
            return node
        return value

    def exit__scope(self, node):
        node = node.clone()
        del node.attrs['known_constants']
        return node
