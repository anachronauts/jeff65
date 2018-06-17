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


def pairwise(t):
    it = iter(t)
    return zip(it, it)


def create():
    pass


def transform(*args):
    matcher = PatternMatcher()
    for pattern, template in pairwise(args):
        # Construct the prototype tree
        prototype = pattern(Predicate)
        analyser = PatternAnalyser(matcher.captures)
        predicates = prototype.transform(analyser)
        assert 1 == len(predicates)
        matcher.ptpairs.append((predicates[0], template))
    return matcher


class MatchError(Exception):
    pass


class PatternMatcher:
    transform_attrs = False

    def __init__(self):
        self.ptpairs = []
        self.captures = {}

    def __call__(self):
        return self

    def __getitem__(self, key):
        return self.captures[key]

    def __getattr__(self, attr):
        if attr.startswith('enter_'):
            return self._enter
        elif attr.startswith('exit_'):
            return self._exit
        raise NotImplementedError()

    def _enter(self, node):
        return node

    def _exit(self, node):
        for predicate, template in self.ptpairs:
            self.captures.clear()
            if predicate._match(node):
                return template(self)
        return node


class PatternAnalyser:
    """Converts a pattern into a bound predicate."""
    transform_attrs = False

    def __init__(self, context):
        self.context = context

    def __getattr__(self, attr):
        if attr.startswith('enter_'):
            return self._enter
        elif attr.startswith('exit_'):
            return self._exit
        raise NotImplementedError(attr)

    def make_predicate(self, obj):
        if isinstance(obj, Predicate):
            # objects which are already predicates are just bound
            return obj._bind(self.context)
        elif hasattr(obj, '_to_predicate'):
            # some objects know how to turn themselves into predicates
            return obj._to_predicate(self)
        # fallback case: check for equality without capturing.
        return Predicate(self.context, None, lambda v: v == obj)

    def make_attrs_predicate(self, attrs):
        pas = {}
        for k, v in attrs.items():
            pas[k] = self.make_predicate(v)

        def _attrs_predicate(attrs):
            for k, v in pas.items():
                if not v._match(attrs[k]):
                    return False
            return True
        return Predicate(self.context, None, _attrs_predicate)

    def make_node_predicate(self, pt, pp, pa):
        def _node_predicate(node):
            return (pt._match(node.t)
                    and pp._match(node.position)
                    and pa._match(node.attrs))
        return Predicate(self.context, None, _node_predicate)

    def _enter(self, node):
        return node

    def _exit(self, node):
        return self.make_node_predicate(
            self.make_predicate(node.t),
            self.make_predicate(node.position),
            self.make_attrs_predicate(node.attrs))


class Predicate:
    def __init__(self, context, key, predicate):
        self.context = context
        self.key = key
        self.predicate = predicate

    @classmethod
    def any(cls, key=None):
        return cls(None, key, lambda _: True)

    @classmethod
    def require(cls, value, exc=None):
        exc = exc or MatchError

        def _p_require(v):
            if value != v:
                raise exc(f"Expected {value} got {v}")
            return True
        return cls(None, None, _p_require)

    def _bind(self, context):
        return Predicate(context, self.key, self.predicate)

    def _match(self, value):
        if not self.predicate(value):
            return False
        if self.key is not None:
            self.context[self.key] = value
        return True
