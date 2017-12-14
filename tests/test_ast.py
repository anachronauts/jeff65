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
    a = parse("/* a comment */\n")
    assert_equal(0, len(a.statements))


def test_comments_no_newline():
    a = parse("/* a comment */")
    assert_equal(0, len(a.statements))


def test_nested_comment():
    a = parse("/* a /* nested */ comment */")
    assert_equal(0, len(a.statements))


def test_comment_before_expression():
    a = parse("/* a comment */ 1 + 2")
    assert_equal(1, len(a.statements))
    c = a.statements[0]
    assert_is_instance(c, ast.OperatorAddNode)
    assert_is_instance(c.lhs, ast.NumericNode)
    assert_is_instance(c.rhs, ast.NumericNode)


def test_comment_after_expression():
    a = parse("1 + 2 /* a comment */")
    assert_equal(1, len(a.statements))
    c = a.statements[0]
    assert_is_instance(c, ast.OperatorAddNode)
    assert_is_instance(c.lhs, ast.NumericNode)
    assert_is_instance(c.rhs, ast.NumericNode)


def test_comment_within_expression():
    a = parse("1 + /* a comment */ 2")
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


def test_array_declaration():
    a = parse("let x: [u8; 0 to 3] = [0, 1, 2]")
    assert_equal(1, len(a.statements))
    t = a.statements[0]
    assert_is_instance(t, ast.StatementLetNode)
    assert_is_instance(t.binding, ast.OperatorAssignNode)
    assert_is_instance(t.binding.lhs, ast.PunctuationValueTypeNode)
    assert_is_instance(t.binding.lhs.rhs, ast.BracketsNode)
    assert_is_instance(t.binding.rhs, ast.BracketsNode)

    signature = t.binding.lhs.rhs.contents
    assert_is_instance(signature, ast.PunctuationArrayRangeNode)
    assert_equal(signature.lhs.text, "u8")
    assert_is_instance(signature.rhs, ast.OperatorRangeNode)
    assert_equal(signature.rhs.lhs.text, "0")
    assert_equal(signature.rhs.rhs.text, "3")

    values = t.binding.rhs.contents
    assert_is_instance(values, ast.PunctuationCommaNode)
    assert_equal(values.lhs.text, "0")
    assert_is_instance(values.rhs, ast.PunctuationCommaNode)
    assert_equal(values.rhs.lhs.text, "1")
    assert_equal(values.rhs.rhs.text, "2")


def test_array_declaration_shorthand():
    a = parse("let x: [u8; 3] = [0, 1, 2]")
    assert_equal(1, len(a.statements))
    t = a.statements[0]
    assert_is_instance(t, ast.StatementLetNode)
    assert_is_instance(t.binding, ast.OperatorAssignNode)
    assert_is_instance(t.binding.lhs, ast.PunctuationValueTypeNode)
    assert_is_instance(t.binding.lhs.rhs, ast.BracketsNode)
    assert_is_instance(t.binding.rhs, ast.BracketsNode)

    signature = t.binding.lhs.rhs.contents
    assert_is_instance(signature, ast.PunctuationArrayRangeNode)
    assert_equal(signature.lhs.text, "u8")
    assert_equal(signature.rhs.text, "3")

    values = t.binding.rhs.contents
    assert_is_instance(values, ast.PunctuationCommaNode)
    assert_equal(values.lhs.text, "0")
    assert_is_instance(values.rhs, ast.PunctuationCommaNode)
    assert_equal(values.rhs.lhs.text, "1")
    assert_equal(values.rhs.rhs.text, "2")


def test_array_multidiminsional():
    a = parse("let x: [u8; 2, 1 to 3] = [[0, 1], [2, 3]]")
    assert_equal(1, len(a.statements))
    t = a.statements[0]
    assert_is_instance(t, ast.StatementLetNode)
    assert_is_instance(t.binding, ast.OperatorAssignNode)
    assert_is_instance(t.binding.lhs, ast.PunctuationValueTypeNode)
    assert_is_instance(t.binding.lhs.rhs, ast.BracketsNode)
    assert_is_instance(t.binding.rhs, ast.BracketsNode)

    signature = t.binding.lhs.rhs.contents
    assert_is_instance(signature, ast.PunctuationArrayRangeNode)
    assert_equal(signature.lhs.text, "u8")
    assert_is_instance(signature.rhs, ast.PunctuationCommaNode)
    assert_equal(signature.rhs.lhs.text, "2")
    assert_is_instance(signature.rhs.rhs, ast.OperatorRangeNode)
    assert_equal(signature.rhs.rhs.lhs.text, "1")
    assert_equal(signature.rhs.rhs.rhs.text, "3")

    values = t.binding.rhs.contents
    assert_is_instance(values, ast.PunctuationCommaNode)
    assert_is_instance(values.lhs, ast.BracketsNode)
    assert_is_instance(values.rhs, ast.BracketsNode)

    values = [values.lhs.contents, values.rhs.contents]
    assert_is_instance(values[0], ast.PunctuationCommaNode)
    assert_equal(values[0].lhs.text, "0")
    assert_equal(values[0].rhs.text, "1")
    assert_is_instance(values[1], ast.PunctuationCommaNode)
    assert_equal(values[1].lhs.text, "2")
    assert_equal(values[1].rhs.text, "3")


def test_array_unmatched_open_bracket():
    assert_raises(ast.ParseError, parse, "let x: [u8; 3] = [0, 1, 2")


def test_array_unmatched_close_bracket():
    assert_raises(ast.ParseError, parse, "let x: [u8; 3] = 0, 1, 2]")


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
    assert_equal("foo", c.fun.text)
    assert_equal("1", c.args.lhs.text)
    assert_equal("2", c.args.rhs.lhs.text)
    assert_equal("3", c.args.rhs.rhs.text)


def test_return():
    a = parse("return 1 + 2")
    assert_equal(1, len(a.statements))
    r = a.statements[0]
    assert_is_instance(r, ast.StatementReturnNode)
    assert_is_instance(r.rhs, ast.OperatorAddNode)
    assert_equal("1", r.rhs.lhs.text)
    assert_equal("2", r.rhs.rhs.text)


def test_return_empty():
    a = parse("return")
    assert_equal(1, len(a.statements))
    r = a.statements[0]
    assert_is_none(r.rhs)


def test_fun_def_void_empty():
    a = parse("fun foo() endfun")
    assert_equal(1, len(a.statements))
    f = a.statements[0]
    assert_is_instance(f, ast.StatementFunNode)
    s = f.signature
    assert_is_instance(s, ast.FunctionCallNode)
    assert_equal("foo", s.fun.text)
    assert_is_none(s.args)
    assert_equal(0, len(f.children))


def test_fun_def_void():
    a = parse("""
    fun foo(a: u8, b: u16)
       return
    endfun
    """)
    assert_equal(1, len(a.statements))
    f = a.statements[0]
    assert_is_instance(f, ast.StatementFunNode)
    s = f.signature
    assert_is_instance(s, ast.FunctionCallNode)
    assert_equal("foo", s.fun.text)
    assert_is_instance(s.args, ast.PunctuationCommaNode)
    aa = s.args.lhs
    assert_is_instance(aa, ast.PunctuationValueTypeNode)
    assert_equal("a", aa.lhs.text)
    assert_equal("u8", aa.rhs.text)
    ab = s.args.rhs
    assert_is_instance(ab, ast.PunctuationValueTypeNode)
    assert_equal("b", ab.lhs.text)
    assert_equal("u16", ab.rhs.text)
    assert_equal(1, len(f.children))
    r = f.children[0]
    assert_is_instance(r, ast.StatementReturnNode)
    assert_is_none(r.rhs)


def test_fun_def_nonvoid():
    a = parse("""
    fun id(x: u8) -> u8
        return x
    endfun
    """)
    assert_equal(1, len(a.statements))
    f = a.statements[0]
    assert_is_instance(f, ast.StatementFunNode)
    rt = f.signature
    assert_is_instance(rt, ast.PunctuationReturnTypeNode)
    assert_equal("u8", rt.rhs.text)
    s = rt.lhs
    assert_is_instance(s, ast.FunctionCallNode)
    assert_equal("id", s.fun.text)
    ax = s.args
    assert_is_instance(ax, ast.PunctuationValueTypeNode)
    assert_equal("x", ax.lhs.text)
    assert_equal("u8", ax.rhs.text)
    assert_equal(1, len(f.children))
    r = f.children[0]
    assert_is_instance(r, ast.StatementReturnNode)
    assert_equal("x", r.rhs.text)


def test_isr_def_empty():
    a = parse("isr bar endisr")
    assert_equal(1, len(a.statements))
    f = a.statements[0]
    assert_is_instance(f, ast.StatementIsrNode)
    n = f.name
    assert_is_instance(n, ast.IdentifierNode)
    assert_equal(n.text, "bar")


def test_isr_def():
    a = parse("""
    isr bar
        return
    endisr
    """)
    assert_equal(1, len(a.statements))
    f = a.statements[0]
    assert_is_instance(f, ast.StatementIsrNode)
    n = f.name
    assert_is_instance(n, ast.IdentifierNode)
    assert_equal(n.text, "bar")
    assert_equal(1, len(f.children))
    assert_is_instance(f.children[0], ast.StatementReturnNode)
    assert_is_none(f.children[0].rhs)
