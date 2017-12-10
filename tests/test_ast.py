import io
from nose.tools import *
from jeff65.gold import ast, lexer


def parse(source):
    with io.StringIO(source) as s:
        l = list(lexer.lex(s))
        a = ast.parse_all(l)
        assert_is_instance(a, ast.UnitNode)
        return a


def test_empty_file():
    a = parse("")
    assert_equal(0, len(a.statements))


def test_whitespace_only_file():
    a = parse("\n")
    print(a.statements[0])
    print(type(a.statements[0]))
    assert_equal(0, len(a.statements))


def test_comments_newline():
    a = parse("--[[ a comment ]]\n")
    assert_equal(0, len(a.statements))


def test_comments_no_newline():
    a = parse("--[[ a comment ]]")
    assert_equal(0, len(a.statements))


def test_nested_comment():
    a = parse("--[[ a --[[ nested ]] comment ]]")
    assert_equal(0, len(a.statements))


def test_comment_before_expression():
    a = parse("--[[ a comment ]] 1 + 2")
    assert_equal(1, len(a.statements))
    c = a.statements[0]
    assert_is_instance(c, ast.OperatorAddNode)
    assert_is_instance(c.lhs, ast.NumericNode)
    assert_is_instance(c.rhs, ast.NumericNode)


def test_comment_after_expression():
    a = parse("1 + 2 --[[ a comment ]]")
    assert_equal(1, len(a.statements))
    c = a.statements[0]
    assert_is_instance(c, ast.OperatorAddNode)
    assert_is_instance(c.lhs, ast.NumericNode)
    assert_is_instance(c.rhs, ast.NumericNode)


def test_comment_within_expression():
    a = parse("1 + --[[ a comment ]] 2")
    assert_equal(1, len(a.statements))
    c = a.statements[0]
    assert_is_instance(c, ast.OperatorAddNode)
    assert_is_instance(c.lhs, ast.NumericNode)
    assert_is_instance(c.rhs, ast.NumericNode)


def test_associativity():
    a = parse("1 + 2 * 3")
    assert_equal(1, len(a.statements))
    e1 = a.statements[0]
    assert_is_instance(e1, ast.OperatorAddNode)
    assert_is_instance(e1.rhs, ast.OperatorMultiplyNode)


def test_let_with_storage_class():
    a = parse("let mut a: u8 = 7")
    assert_equal(1, len(a.statements))
    t = a.statements[0]
    assert_is_instance(t, ast.StatementLetNode)
    s = t.binding
    assert_is_instance(s, ast.StorageClassNode)
    assert_equal(s.text, "mut")
    b = s.binding
    assert_is_instance(b, ast.OperatorAssignNode)
    assert_is_instance(b.rhs, ast.NumericNode)
    assert_equal("7", b.rhs.text)
    assert_is_instance(b.lhs, ast.PunctuationValueTypeNode)
    assert_is_instance(b.lhs.lhs, ast.IdentifierNode)
    assert_equal("a", b.lhs.lhs.text)
    assert_is_instance(b.lhs.rhs, ast.IdentifierNode)
    assert_equal("u8", b.lhs.rhs.text)


def test_let_without_storage_class():
    a = parse("let a: u8 = 7")
    assert_equal(1, len(a.statements))
    t = a.statements[0]
    assert_is_instance(t, ast.StatementLetNode)
    b = t.binding
    assert_is_instance(b, ast.OperatorAssignNode)
    assert_is_instance(b.rhs, ast.NumericNode)
    assert_equal("7", b.rhs.text)
    assert_is_instance(b.lhs, ast.PunctuationValueTypeNode)
    assert_is_instance(b.lhs.lhs, ast.IdentifierNode)
    assert_equal("a", b.lhs.lhs.text)
    assert_is_instance(b.lhs.rhs, ast.IdentifierNode)
    assert_equal("u8", b.lhs.rhs.text)
