import io
from nose.tools import (assert_equal, assert_is_instance, assert_raises,
                        assert_is_none)
from jeff65.gold import ast, lexer


def parse(source):
    with io.StringIO(source) as s:
        x = list(lexer.lex(s))
        a = ast.parse_all(x)
        assert_is_instance(a, ast.UnitNode)
        return a


def test_empty_file():
    a = parse("")
    assert_equal(0, len(a.statements))


def test_whitespace_only_file():
    a = parse("\n")
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


def test_sign():
    a = parse("-1 + 2")
    assert_equal(1, len(a.statements))
    e1 = a.statements[0]
    assert_is_instance(e1, ast.OperatorAddNode)
    assert_is_instance(e1.lhs, ast.OperatorSubtractNode)
    assert_is_instance(e1.rhs, ast.NumericNode)


def test_parentheses():
    a = parse("(1 + 2) * 3")
    assert_equal(1, len(a.statements))
    e1 = a.statements[0]
    assert_is_instance(e1, ast.OperatorMultiplyNode)
    assert_is_instance(e1.lhs, ast.OperatorAddNode)


def test_nested_parentheses():
    a = parse("((1 + 2) / 3) + 4")
    assert_equal(1, len(a.statements))
    e1 = a.statements[0]
    assert_is_instance(e1, ast.OperatorAddNode)
    assert_is_instance(e1.lhs, ast.OperatorDivideNode)
    assert_is_instance(e1.lhs.lhs, ast.OperatorAddNode)


def test_parentheses_with_sign():
    a = parse("(-1 + 2)")
    e1 = a.statements[0]
    assert_is_instance(e1, ast.OperatorAddNode)
    assert_is_instance(e1.lhs, ast.OperatorSubtractNode)
    assert_is_instance(e1.rhs, ast.NumericNode)


def test_unmatched_open_parentheses():
    assert_raises(ast.ParseError, parse, "(1 + 2")


def test_unmatched_close_parentheses():
    assert_raises(ast.ParseError, parse, "1 + 2)")


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


def test_string_literal():
    a = parse('"this is a string"')
    assert_equal(1, len(a.statements))
    t = a.statements[0]
    assert_is_instance(t, ast.StringNode)
    assert_equal(t.string, "this is a string")


def test_string_escaped():
    a = parse('"this is a \\"string"')
    assert_equal(1, len(a.statements))
    t = a.statements[0]
    assert_is_instance(t, ast.StringNode)
    assert_equal(t.string, 'this is a \\"string')


def test_fun_call_empty():
    a = parse("foo()")
    assert_equal(1, len(a.statements))
    c = a.statements[0]
    assert_is_instance(c, ast.FunctionCallNode)
    assert_equal("foo", c.fun.text)
    assert_is_none(c.args)


def test_fun_call_one():
    a = parse("foo(1)")
    assert_equal(1, len(a.statements))
    c = a.statements[0]
    assert_is_instance(c, ast.FunctionCallNode)
    assert_equal("foo", c.fun.text)
    assert_equal("1", c.args.text)


def test_fun_call_many():
    a = parse("foo(1, 2, 3)")
    assert_equal(1, len(a.statements))
    c = a.statements[0]
    assert_is_instance(c, ast.FunctionCallNode)
    print(c)
    assert_equal("foo", c.fun.text)
    assert_equal("1", c.args.lhs.text)
    assert_equal("2", c.args.rhs.lhs.text)
    assert_equal("3", c.args.rhs.rhs.text)
