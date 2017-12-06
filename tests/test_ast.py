import io
from nose.tools import *
from jeff65.gold import ast, lexer


def parse(source):
    with io.StringIO(source) as s:
        a = ast.parse_all(lexer.lex(s))
        assert_is_instance(a, ast.UnitNode)
        return a


def test_comments_newline():
    a = parse("-- a comment\n")
    assert_equal(1, len(a.statements))
    c = a.statements[0]
    assert_is_instance(c, ast.CommentNode)
    assert_equal("a comment", c.comment)


def test_comments_no_newline():
    a = parse("-- a comment")
    assert_equal(1, len(a.statements))
    c = a.statements[0]
    assert_is_instance(c, ast.CommentNode)
    assert_equal("a comment", c.comment)


def test_associativity():
    a = parse("1 + 2 * 3")
    assert_equal(1, len(a.statements))
    e1 = a.statements[0]
    assert_is_instance(e1, ast.OperatorAddNode)
    assert_is_instance(e1.second, ast.OperatorMultiplyNode)
