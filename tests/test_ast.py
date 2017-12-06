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
    assert_is_instance(b.rvalue, ast.NumericNode)
    assert_equal("7", b.rvalue.text)
    assert_is_instance(b.lvalue, ast.PunctuationValueTypeNode)
    assert_is_instance(b.lvalue.name, ast.IdentifierNode)
    assert_equal("a", b.lvalue.name.text)
    assert_is_instance(b.lvalue.type, ast.IdentifierNode)
    assert_equal("u8", b.lvalue.type.text)

def test_let_without_storage_class():
    a = parse("let a: u8 = 7")
    assert_equal(1, len(a.statements))
    t = a.statements[0]
    assert_is_instance(t, ast.StatementLetNode)
    b = t.binding
    assert_is_instance(b, ast.OperatorAssignNode)
    assert_is_instance(b.rvalue, ast.NumericNode)
    assert_equal("7", b.rvalue.text)
    assert_is_instance(b.lvalue, ast.PunctuationValueTypeNode)
    assert_is_instance(b.lvalue.name, ast.IdentifierNode)
    assert_equal("a", b.lvalue.name.text)
    assert_is_instance(b.lvalue.type, ast.IdentifierNode)
    assert_equal("u8", b.lvalue.type.text)
