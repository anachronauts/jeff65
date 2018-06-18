from nose.tools import (
    assert_equal)
from jeff65.gold import ast, types
from jeff65.gold.passes import binding


def transform(node, xform):
    backup = node.clone()
    result = node.transform(xform)
    assert_equal(backup, node)  # check that the previous AST wasn't mutated
    return result


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
