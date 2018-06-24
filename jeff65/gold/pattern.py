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
import functools
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


def transform(order):
    """Converts the decorated generator function into a transform.

    The decorated generator function will be passed a single argument of type
    PatternFactory. It should yield one or more pairs of (pattern, template),
    where pattern is some mixture of AstNode, Predicate, and SequencePredicate
    instances, and template is a function which, when called with a
    dictionary-like of captures, returns an object to replace the matched node.
    """
    def _decorate_transform(f):
        def _make_transform():
            transform = PatternPass(f.__name__, order)
            pf = PredicateFactory(transform.captures)
            analyser = PatternAnalyser(pf)
            for pattern, template in f(pf):
                # Convert the pattern into a predicate
                if isinstance(pattern, ast.AstNode):
                    predicates = pattern.transform(analyser)
                else:
                    # do the non-recursive transform
                    predicates = [analyser.make_predicate(pattern)]
                assert 1 == len(predicates)
                transform.ptpairs.append((predicates[0], template))
            return transform
        functools.update_wrapper(_make_transform, f)
        return _make_transform
    return _decorate_transform


class MatchError(Exception):
    pass


class PatternPass:
    """A pattern based-translation pass.

    Use the pattern.transform function to define instances of this. Instances
    store pairs of patterns and templates. If the transform finds a node which
    matches the pattern, the node is replaced with the result of calling the
    corresponding template function with a dictionary-like of values captured
    by the match.
    """

    transform_attrs = False

    def __init__(self, name, order):
        self.__name__ = name
        self.order = order
        self.ptpairs = []
        self.captures = {}

    def __getitem__(self, key):
        return self.captures[key]

    def transform_enter(self, t, node):
        if self.order == Order.Descending:
            for predicate, template in self.ptpairs:
                self.captures.clear()
                if predicate._match(node):
                    return template(self)
        return node

    def transform_exit(self, t, node):
        if self.order == Order.Ascending:
            for predicate, template in self.ptpairs:
                self.captures.clear()
                if predicate._match(node):
                    return template(self)
        return [node]


class PatternAnalyser:
    """Converts a pattern into a bound predicate."""

    transform_attrs = False

    def __init__(self, pf):
        self.pf = pf

    def make_predicate(self, obj):
        if isinstance(obj, Predicate):
            # objects which are already predicates are just passed on
            return obj
        elif hasattr(obj, '_to_predicate'):
            # some objects know how to turn themselves into predicates
            return obj._to_predicate(self, self.pf)
        # fallback case: check for equality without capturing.
        return self.pf.eq(obj)

    def make_attrs_predicate(self, attrs):
        if isinstance(attrs, Predicate):
            return attrs

        pas = {}
        for k, v in attrs.items():
            pas[k] = self.make_predicate(v)

        def _attrs_predicate(attrs):
            for k, v in pas.items():
                if not v._match(attrs[k]):
                    return False
            return True
        return self.pf.predicate(_attrs_predicate)

    def transform_enter(self, t, node):
        return node

    def transform_exit(self, t, node):
        return self.pf.node(
            self.make_predicate(node.t),
            self.make_predicate(node.position),
            self.make_attrs_predicate(node.attrs),
            node.children)


class PredicateFactory:
    def __init__(self, context):
        self.context = context

    def predicate(self, predicate, key=None):
        return Predicate(self.context, key, predicate)

    def any(self, key=None):
        return Predicate(self.context, key, lambda _: True)

    def any_node(self, with_children=None, key=None):
        if with_children is None:
            children = [self.zero_or_more_nodes()]
        else:
            analyser = PatternAnalyser(self)
            # this is goofy but the children have to be transformed now or it's
            # not happening...
            children = []
            for c in with_children:
                if isinstance(c, ast.AstNode):
                    children.extend(c.transform(analyser))
                else:
                    children.append(c)

        return self.node(
            self.any(),
            self.any(),
            self.any(),
            children,
            key=key)

    def node(self, pt, pp, pa, pcs, key=None):
        def _node_predicate(node):
            if not pt._match(node.t):
                return False
            if not pp._match(node.position):
                return False
            if not pa._match(node.attrs):
                return False
            cq = deque(node.children)
            pcq = deque(pcs)
            while len(pcq) > 0:
                pc = pcq.popleft()
                if not pc._seq_match(cq):
                    return False
            # we expect all items to have been consumed
            return len(cq) == 0
        return Predicate(self.context, key, _node_predicate)

    def require(self, value, exc=None):
        exc = exc or MatchError

        def _p_require(v):
            if value != v:
                raise exc(f"Expected {value} got {v}")
            return True
        return Predicate(self.context, None, _p_require)

    def eq(self, value, key=None, require=False):
        def _p_eq(v):
            if v == value:
                return True
            if require:
                raise MatchError(f"Expected {value}, got {v}")
            return False
        return Predicate(self.context, key, _p_eq)

    def lt(self, value, key=None, require=False):
        def _p_lt(v):
            if v < value:
                return True
            if require:
                raise MatchError(f"Expected value <{value}, got {v}")
            return False
        return Predicate(self.context, key, _p_lt)

    def zero_or_more_nodes(self, key=None, allow=None, exclude=None):
        return SequencePredicate(
            self.context, key,
            lambda v: ((allow is None or v.t in allow)
                       and (exclude is None or v.t not in exclude)))


class Predicate:
    def __init__(self, context, key, predicate):
        self.context = context
        self.key = key
        self.predicate = predicate

    def _seq_match(self, vq: deque) -> bool:
        return (len(vq) > 0
                and self._match(vq.popleft()))

    def _match(self, value):
        if not self.predicate(value):
            return False
        if self.key is not None and not self.key.startswith('!'):
            self.context[self.key] = value
        return True


class SequencePredicate(Predicate):
    def __init__(self, context, key, predicate, min_count=0, max_count=None):
        super().__init__(context, key, predicate)
        self.min_count = min_count
        self.max_count = max_count

    def _seq_match(self, vq: deque) -> bool:
        # we get passed a queue, and we're expected to consume items (from the
        # left) from it as long as our predicates are satisfied. If we stop
        # matching and we haven't reached min_count, we return false to fail
        # the match. If we reach the max_count or our predicate stops matching,
        # we return True.

        matched = []
        if self.key is not None:
            self.context[self.key] = matched

        while self.max_count is None or len(matched) < self.max_count:
            if len(vq) == 0:
                break
            v = vq.popleft()
            if not self.predicate(v):
                # backtrack
                vq.appendleft(v)
                break
            matched.append(v)

        return len(matched) >= self.min_count

    def _match(self, value):
        raise ValueError("Cannot single-match a sequence")
