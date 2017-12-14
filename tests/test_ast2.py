from nose.tools import assert_equal, assert_is_instance
from jeff65.gold import ast2
from test_ast import parse


def test_flatten_let_sc():
    a = ast2.transform2(parse("let mut foo: u8 = 7"))
    assert_equal(1, len(a.statements))
    n = a.statements[0]
    assert_is_instance(n, ast2.FlatLetNode)
    assert_equal("mut", n.storage)
    assert_equal("foo", n.name.text)
    assert_equal("u8", n.t.text)
    assert_equal(1, len(n.children))
    assert_equal("7", n.children[0].text)


def test_flatten_let():
    a = ast2.transform2(parse("let foo: u8 = 7"))
    assert_equal(1, len(a.statements))
    n = a.statements[0]
    assert_is_instance(n, ast2.FlatLetNode)
    assert_equal(None, n.storage)
    assert_equal("foo", n.name.text)
    assert_equal("u8", n.t.text)
    assert_equal(1, len(n.children))
    assert_equal("7", n.children[0].text)
