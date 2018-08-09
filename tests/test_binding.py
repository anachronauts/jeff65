import attr
import string
import hypothesis.strategies as st
from hypothesis import assume
from hypothesis.stateful import (
    Bundle,
    RuleBasedStateMachine,
    rule,
    precondition)
from nose.tools import (
    assert_equal,
    assert_not_in)
from jeff65 import ast
from jeff65.blum import types
from jeff65.gold.passes import binding


def transform(node, xform):
    backup = node.pretty()
    result = node.transform(xform)
    # check that the previous AST wasn't mutated
    assert_equal(backup, node.pretty())
    return result


@attr.s
class Frame:
    t = attr.ib()
    node = attr.ib()
    orig = attr.ib()
    names = attr.ib()


class ScopedTransform(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.frames = []
        self.transform = binding.ScopedPass()

    unscoped_types = Bundle('unscoped_types')
    names = Bundle('names')
    constants = Bundle('constants')

    @rule(target=unscoped_types, u=st.text(
        alphabet=string.ascii_letters + '_'))
    def u(self, u):
        return u

    @rule(target=names, n=st.text())
    def n(self, n):
        return n

    @rule(t=st.sampled_from(binding.ScopedPass.scoped_types))
    def enter_scoped_node(self, t):
        orig = ast.AstNode(t)
        node = self.transform.transform_enter(t, orig)
        self.frames.append(Frame(t, node, orig, {}))

    @precondition(lambda self: len(self.frames) > 0)
    @rule(t=st.sampled_from(binding.ScopedPass.scoped_types))
    def exit_scoped_node(self, t):
        # this would probably be more efficient if we could use preconditions
        # somehow?
        assume(self.frames[-1].t == t)
        frame = self.frames.pop()
        node, *nodes = self.transform.transform_exit(t, frame.node)
        assert_equal(0, len(nodes))
        assert_equal(ast.AstNode(t), frame.orig)
        assert_equal(frame.names, node.attrs['known_names'])

    @precondition(lambda self: len(self.frames) > 0)
    @rule(t=unscoped_types)
    def enter_unscoped_node(self, t):
        orig = ast.AstNode(t)
        node = self.transform.transform_enter(t, orig)
        self.frames.append(Frame(t, node, orig, None))

    @precondition(lambda self: len(self.frames) > 0)
    @rule(t=unscoped_types)
    def exit_unscoped_node(self, t):
        # this would probably be more efficient if we could use preconditions
        # somehow?
        assume(self.frames[-1].t == t)
        frame = self.frames.pop()
        node, *nodes = self.transform.transform_exit(t, frame.node)
        assert_equal(0, len(nodes))
        assert_equal(ast.AstNode(t), frame.orig)
        assert_not_in('known_names', node.attrs)

    @precondition(lambda self: len(self.frames) > 0)
    @rule(n=names, v=st.integers())
    def bind_name(self, n, v):
        self.transform.bind_name(n, v)
        frame = next(f for f in reversed(self.frames) if f.names is not None)
        frame.names[n] = v

    @precondition(lambda self: len(self.frames) > 0)
    @rule(n=names)
    def look_up_name(self, n):
        try:
            ev = next(f.names[n]
                      for f in reversed(self.frames)
                      if f.names is not None and n in f.names)
        except StopIteration:
            ev = None
        assert ev == self.transform.look_up_name(n)


TestScopedPass = ScopedTransform.TestCase


def test_explicit_scopes_single():
    a = ast.AstNode('fun', children=[
        ast.AstNode('call', attrs={'target': 'spam'}),
        ast.AstNode('let', children=[
            ast.AstNode('let_set!', attrs={
                'name': 'foo',
                'type': types.u8,
            }, children=[
                ast.AstNode('numeric', attrs={'value': 42}),
            ]),
        ]),
        ast.AstNode('call', attrs={'target': 'eggs'}),
    ])
    b = transform(a, binding.ExplicitScopes())
    expected = ast.AstNode('fun', children=[
        ast.AstNode('call', attrs={'target': 'spam'}),
        ast.AstNode('let_scoped', children=[
            ast.AstNode('let_set!', attrs={
                'name': 'foo',
                'type': types.u8,
            }, children=[
                ast.AstNode('numeric', attrs={'value': 42}),
            ]),
            ast.AstNode('call', attrs={'target': 'eggs'}),
        ]),
    ])
    try:
        assert_equal(expected, b[0])
    except AssertionError:
        print(expected.pretty(no_position=True))
        print('!=')
        print(b[0].pretty(no_position=True))
        raise


def test_explicit_scopes_multiple():
    a = ast.AstNode('fun', children=[
        ast.AstNode('call', attrs={'target': 'spam'}),
        ast.AstNode('let', children=[
            ast.AstNode('let_set!', attrs={
                'name': 'foo',
                'type': types.u8,
            }, children=[
                ast.AstNode('numeric', attrs={'value': 42}),
            ]),
        ]),
        ast.AstNode('call', attrs={'target': 'eggs'}),
        ast.AstNode('let', children=[
            ast.AstNode('let_set!', attrs={
                'name': 'bar',
                'type': types.u8,
            }, children=[
                ast.AstNode('numeric', attrs={'value': 54}),
            ]),
        ]),
        ast.AstNode('call', attrs={'target': 'beans'}),
    ])
    b = transform(a, binding.ExplicitScopes())
    expected = ast.AstNode('fun', children=[
        ast.AstNode('call', attrs={'target': 'spam'}),
        ast.AstNode('let_scoped', children=[
            ast.AstNode('let_set!', attrs={
                'name': 'foo',
                'type': types.u8,
            }, children=[
                ast.AstNode('numeric', attrs={'value': 42}),
            ]),
            ast.AstNode('call', attrs={'target': 'eggs'}),
            ast.AstNode('let_scoped', children=[
                ast.AstNode('let_set!', attrs={
                    'name': 'bar',
                    'type': types.u8,
                }, children=[
                    ast.AstNode('numeric', attrs={'value': 54}),
                ]),
                ast.AstNode('call', attrs={'target': 'beans'}),
            ]),
        ]),
    ])
    try:
        assert_equal(expected, b[0])
    except AssertionError:
        print(expected.pretty(no_position=True))
        print('!=')
        print(b[0].pretty(no_position=True))
        raise
