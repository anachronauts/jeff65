import hypothesis.strategies as st
from collections import namedtuple
from hypothesis import assume
from hypothesis.stateful import (
    Bundle,
    RuleBasedStateMachine,
    rule,
    precondition)
from nose.tools import (
    assert_equal)
from jeff65.blum import types
from jeff65.gold import ast
from jeff65.gold.passes import binding


def transform(node, xform):
    backup = node.clone()
    result = node.transform(xform)
    assert_equal(backup, node)  # check that the previous AST wasn't mutated
    return result


Frame = namedtuple('Frame', ['t', 'node', 'orig', 'names'])


class ScopedTransform(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.frames = []
        self.transform = binding.ScopedPass()

    names = Bundle('names')
    constants = Bundle('constants')

    @rule(target=names, n=st.text())
    def n(self, n):
        return n

    @rule(t=st.sampled_from(binding.ScopedPass.scoped_types))
    def enter_node(self, t):
        orig = ast.AstNode(t, None)
        node = self.transform.transform_enter(t, orig)
        self.frames.append(Frame(t, node, orig, {}))

    @precondition(lambda self: len(self.frames) > 0)
    @rule(t=st.sampled_from(binding.ScopedPass.scoped_types))
    def exit_node(self, t):
        # this would probably be more efficient if we could use preconditions
        # somehow?
        assume(self.frames[-1].t == t)
        frame = self.frames.pop()
        node, *nodes = self.transform.transform_exit(t, frame.node)
        assert len(nodes) == 0
        assert frame.orig == ast.AstNode(t, None)
        assert frame.names == node.get_attr_default('known_names', {})

    @precondition(lambda self: len(self.frames) > 0)
    @rule(n=names, v=st.integers())
    def bind_name(self, n, v):
        self.transform.bind_name(n, v)
        self.frames[-1].names[n] = v

    @precondition(lambda self: len(self.frames) > 0)
    @rule(n=names)
    def look_up_name(self, n):
        try:
            ev = next(f.names[n]
                      for f in reversed(self.frames)
                      if n in f.names)
        except StopIteration:
            ev = None
        assert ev == self.transform.look_up_name(n)


TestScopedPass = ScopedTransform.TestCase


def test_explicit_scopes_single():
    a = ast.AstNode('fun', None, children=[
        ast.AstNode('call', None, attrs={'target': 'spam'}),
        ast.AstNode('let', None, children=[
            ast.AstNode('let_set!', None, attrs={
                'name': 'foo',
                'type': types.u8,
            }, children=[
                ast.AstNode('numeric', None, attrs={'value': 42}),
            ]),
        ]),
        ast.AstNode('call', None, attrs={'target': 'eggs'}),
    ])
    b = transform(a, binding.ExplicitScopes())
    expected = ast.AstNode('fun', None, children=[
        ast.AstNode('call', None, attrs={'target': 'spam'}),
        ast.AstNode('let_scoped', None, children=[
            ast.AstNode('let_set!', None, attrs={
                'name': 'foo',
                'type': types.u8,
            }, children=[
                ast.AstNode('numeric', None, attrs={'value': 42}),
            ]),
            ast.AstNode('call', None, attrs={'target': 'eggs'}),
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
    a = ast.AstNode('fun', None, children=[
        ast.AstNode('call', None, attrs={'target': 'spam'}),
        ast.AstNode('let', None, children=[
            ast.AstNode('let_set!', None, attrs={
                'name': 'foo',
                'type': types.u8,
            }, children=[
                ast.AstNode('numeric', None, attrs={'value': 42}),
            ]),
        ]),
        ast.AstNode('call', None, attrs={'target': 'eggs'}),
        ast.AstNode('let', None, children=[
            ast.AstNode('let_set!', None, attrs={
                'name': 'bar',
                'type': types.u8,
            }, children=[
                ast.AstNode('numeric', None, attrs={'value': 54}),
            ]),
        ]),
        ast.AstNode('call', None, attrs={'target': 'beans'}),
    ])
    b = transform(a, binding.ExplicitScopes())
    expected = ast.AstNode('fun', None, children=[
        ast.AstNode('call', None, attrs={'target': 'spam'}),
        ast.AstNode('let_scoped', None, children=[
            ast.AstNode('let_set!', None, attrs={
                'name': 'foo',
                'type': types.u8,
            }, children=[
                ast.AstNode('numeric', None, attrs={'value': 42}),
            ]),
            ast.AstNode('call', None, attrs={'target': 'eggs'}),
            ast.AstNode('let_scoped', None, children=[
                ast.AstNode('let_set!', None, attrs={
                    'name': 'bar',
                    'type': types.u8,
                }, children=[
                    ast.AstNode('numeric', None, attrs={'value': 54}),
                ]),
                ast.AstNode('call', None, attrs={'target': 'beans'}),
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
