# jeff65 pattern-based AST transformation
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

"""Pattern-based AST transformation system.

This module provides something similar to Scheme R5RS syntax-rules, on top of
procedural DFS transform system.
"""

import attr
import enum
import inspect
from . import ast


class Order(enum.Enum):
    """Denotes the order that nodes are matched.

    'Descending' results in nodes being matched from outermost to innermost,
    i.e. during the descent of the DFS traversal. 'Ascending' results in the
    opposite.

    Use 'Any' if the order does not matter for the transform to work correctly.
    """
    Descending = 0
    Ascending = 1

    # given a choice, prefer descending, so that if the transform prunes the
    # tree, the pruned nodes won't have to be traversed.
    Any = Descending


_marker = object()


def match(pattern):
    """Marks a method as a pattern transformer."""

    return lambda method: (_marker, pattern, method)


def transform(order):
    """Converts the decorated class into a transform."""

    def _decorate_transform(cls):
        analyser = PatternAnalyser()
        ptpairs = []
        m_dict = {'ptpairs': ptpairs}

        if order == Order.Descending:
            m_dict['transform_enter'] = transform_handler
            m_dict['transform_exit'] = dummy_handler
        else:
            m_dict['transform_enter'] = dummy_handler
            m_dict['transform_exit'] = transform_handler

        for member, value in vars(cls).items():
            if not (isinstance(value, tuple)
                    and len(value) == 3
                    and value[0] == _marker):
                # copy across non-pattern stuff unchanged
                m_dict[member] = value
            else:
                _, pattern, template = value
                if isinstance(pattern, ast.AstNode):
                    predicates = pattern.transform(analyser)
                else:
                    # do the non-recursive transform
                    predicates = analyser.make_predicate(pattern)
                m_dict[member] = template
                ptpairs.append((predicates, template))
        return type(cls.__name__, cls.__bases__, m_dict)

    return _decorate_transform


class MatchError(Exception):
    pass


def dummy_handler(self, t, node):
    return node


def transform_handler(self, t, node):
    for predicate, template in self.ptpairs:
        captures = {}
        if predicate._match(node, captures):
            f = template.__get__(self, type)
            n = f(**captures)
            if isinstance(n, ast.AstNode) and n.span is None:
                return attr.evolve(n, span=node.span)
            return n
    return node


class PatternAnalyser:
    """Converts a pattern into a bound predicate."""

    def make_predicate(self, obj):
        if isinstance(obj, Predicate):
            # objects which are already predicates are just passed on
            return obj
        # fallback case: check for equality without capturing.
        return Predicate.eq(obj)

    def make_span_predicate(self, span):
        if span is None:
            return Predicate.any()
        return self.make_predicate(span)

    def make_attrs_predicate(self, attrs):
        if isinstance(attrs, Predicate):
            return attrs

        pas = {}
        exhaustive = False
        for k, v in attrs.items():
            if k == "exhaustive!":
                # yeah, the in-band signaling is a little weird, but I'm not
                # really sure where else to put this flag.
                exhaustive = v
            else:
                pas[k] = self.make_predicate(v)
        keys = set(pas.keys())

        def _attrs_predicate(attrs, captures):
            if exhaustive and set(attrs.keys()) != keys:
                return False
            for k, v in pas.items():
                if not v._match(attrs[k], captures):
                    return False
            return True
        return Predicate(None, _attrs_predicate)

    def transform_enter(self, t, node):
        return node

    def transform_exit(self, t, node):
        return Predicate.node(
            self.make_predicate(node.t),
            self.make_attrs_predicate(node.attrs),
            self.make_span_predicate(node.span))


class Predicate:
    def __init__(self, key, predicate=True):
        self.key = key
        if not callable(predicate):
            self.predicate = lambda _1, _2: predicate
        else:
            self.predicate = predicate

    def _match(self, value, captures):
        if not self.predicate(value, captures):
            return False
        if self.key is not None and not self.key.startswith('!'):
            captures[self.key] = value
        return True

    @classmethod
    def any(cls):
        return cls(None)

    @classmethod
    def any_node(cls, key=None, with_attrs=None):
        if with_attrs is None:
            attrs = cls.any()
        else:
            # this is goofy but the children have to be transformed now or it's
            # not happening...
            analyser = PatternAnalyser()
            attrs = analyser.make_attrs_predicate(with_attrs)

        return cls.node(
            cls.any(),
            attrs,
            cls.any(),
            key=key)

    @classmethod
    def node(cls, pt, pa, pn, key=None):
        def _node_predicate(node, captures):
            return (isinstance(node, ast.AstNode)
                    and pt._match(node.t, captures)
                    and pa._match(node.attrs, captures)
                    and pn._match(node.span, captures))
        return cls(key, _node_predicate)

    @classmethod
    def require(cls, value_or_predicate, exc=None):
        exc = exc or MatchError

        if callable(value_or_predicate):
            predicate = value_or_predicate
            try:
                value = inspect.getsource(value_or_predicate)
            except OSError:
                value = '<predicate>'
        else:
            def predicate(v, c):
                return v == value_or_predicate
            value = value_or_predicate

        def _p_require(v, captures):
            if not predicate(v, captures):
                raise exc(f"Expected {value} got {v}")
            return True
        return cls(None, _p_require)

    @classmethod
    def eq(cls, value, key=None, require=False):
        def _p_eq(v, captures):
            if v == value:
                return True
            if require:
                raise MatchError(f"Expected {value}, got {v}")
            return False
        return cls(key, _p_eq)

    @classmethod
    def lt(cls, value, key=None, require=False):
        def _p_lt(v, captures):
            if v < value:
                return True
            if require:
                raise MatchError(f"Expected value <{value}, got {v}")
            return False
        return cls(key, _p_lt)
