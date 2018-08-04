# jeff65 gold-syntax pattern-based AST transformation
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

import enum
import inspect
from collections import deque
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
                    predicates = pattern.transform(analyser, always_list=True)
                else:
                    # do the non-recursive transform
                    predicates = [analyser.make_predicate(pattern)]
                assert 1 == len(predicates)
                m_dict[member] = template
                ptpairs.append((predicates[0], template))
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
            return f(**captures)
    return node


class PatternAnalyser:
    """Converts a pattern into a bound predicate."""

    transform_attrs = False

    def make_predicate(self, obj):
        if isinstance(obj, Predicate):
            # objects which are already predicates are just passed on
            return obj
        elif hasattr(obj, '_to_predicate'):
            # some objects know how to turn themselves into predicates
            return obj._to_predicate(self)
        # fallback case: check for equality without capturing.
        return Predicate.eq(obj)

    def make_attrs_predicate(self, attrs):
        if isinstance(attrs, Predicate):
            return attrs

        pas = {}
        for k, v in attrs.items():
            pas[k] = self.make_predicate(v)

        def _attrs_predicate(attrs, captures):
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
            self.make_predicate(node.position),
            self.make_attrs_predicate(node.attrs),
            node.children)


class Predicate:
    def __init__(self, key, predicate=True):
        self.key = key
        if not callable(predicate):
            self.predicate = lambda _1, _2: predicate
        else:
            self.predicate = predicate

    def _seq_match(self, vq: deque, captures) -> bool:
        return (len(vq) > 0
                and self._match(vq.popleft(), captures))

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
    def any_node(cls, key=None, with_children=None):
        if with_children is None:
            children = [cls.zero_or_more_nodes()]
        else:
            analyser = PatternAnalyser()
            # this is goofy but the children have to be transformed now or it's
            # not happening...
            children = []
            for c in with_children:
                if isinstance(c, ast.AstNode):
                    children.extend(c.transform(analyser))
                else:
                    children.append(c)

        return cls.node(
            cls.any(),
            cls.any(),
            cls.any(),
            children,
            key=key)

    @classmethod
    def node(cls, pt, pp, pa, pcs, key=None):
        def _node_predicate(node, captures):
            if not pt._match(node.t, captures):
                return False
            if not pp._match(node.position, captures):
                return False
            if not pa._match(node.attrs, captures):
                return False
            cq = deque(node.children)
            pcq = deque(pcs)
            while len(pcq) > 0:
                pc = pcq.popleft()
                if not pc._seq_match(cq, captures):
                    return False
            # we expect all items to have been consumed
            return len(cq) == 0
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

    @staticmethod
    def zero_or_more_nodes(key=None, allow=None, exclude=None):
        return SequencePredicate(
            key, lambda v, c: ((allow is None or v.t in allow)
                               and (exclude is None or v.t not in exclude)))


class SequencePredicate(Predicate):
    def __init__(self, key, predicate, min_count=0, max_count=None):
        super().__init__(key, predicate)
        self.min_count = min_count
        self.max_count = max_count

    def _seq_match(self, vq: deque, captures) -> bool:
        # we get passed a queue, and we're expected to consume items (from the
        # left) from it as long as our predicates are satisfied. If we stop
        # matching and we haven't reached min_count, we return false to fail
        # the match. If we reach the max_count or our predicate stops matching,
        # we return True.

        matched = []
        if self.key is not None:
            captures[self.key] = matched

        while self.max_count is None or len(matched) < self.max_count:
            if len(vq) == 0:
                break
            v = vq.popleft()
            if not self.predicate(v, captures):
                # backtrack
                vq.appendleft(v)
                break
            matched.append(v)

        return len(matched) >= self.min_count

    def _match(self, value, captures):
        raise ValueError("Cannot single-match a sequence")
