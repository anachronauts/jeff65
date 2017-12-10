from nose.tools import *
from jeff65.gold import ast2
from test_ast import parse


def test_flatten_let_sc():
    a = parse("let mut foo : u8 = 7")
    a2 = ast2.transform2(a)
    assert_equal(1, len(a.statements))
    n = a.statements[0]
    assert_is_instance(n, ast2.FlatLetNode)
    assert_equal("mut", n.storage)
    assert_equal("foo", n.name.text)
    assert_equal("u8", n.t.text)
    assert_equal("7", n.value.text)


def test_flatten_let():
    a = parse("let foo : u8 = 7")
    a2 = ast2.transform2(a)
    assert_equal(1, len(a.statements))
    n = a.statements[0]
    assert_is_instance(n, ast2.FlatLetNode)
    assert_equal(None, n.storage)
    assert_equal("foo", n.name.text)
    assert_equal("u8", n.t.text)
    assert_equal("7", n.value.text)

