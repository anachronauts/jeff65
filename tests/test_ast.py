import io
import sys
from nose.tools import assert_equal, assert_raises, nottest
from hypothesis import given, strategies as st
from jeff65 import ast, gold, parsing

sys.stderr = sys.stdout


def parse(source):
    with io.StringIO(source) as s:
        ast = gold.parse(s, "<test>")
        print(ast.pretty())
        return ast


def test_empty_file():
    a = parse("")
    assert_equal("unit", a.t)
    assert_equal(0, len(a.select("toplevels", "stmt")))


def test_whitespace_only_file():
    a = parse("\n")
    assert_equal("unit", a.t)
    assert_equal(0, len(a.select("toplevels", "stmt")))


def test_comments_newline():
    a = parse("/* a comment */\n")
    assert_equal("unit", a.t)
    assert_equal(0, len(a.select("toplevels", "stmt")))


def test_comments_no_newline():
    a = parse("/* a comment */")
    assert_equal("unit", a.t)
    assert_equal(0, len(a.select("toplevels", "stmt")))


def test_comments_multiline():
    a = parse(
        """
    /*
     * a multiline comment
     * with multiple lines
     */
    """
    )
    assert_equal("unit", a.t)
    assert_equal(0, len(a.select("toplevels", "stmt")))


def test_comments_unclosed():
    assert_raises(parsing.ParseError, parse, "/* oh no")


def test_comments_unopened():
    assert_raises(parsing.ParseError, parse, "oh no */")


def test_nested_comment():
    a = parse("/* a /* nested */ comment */")
    assert_equal("unit", a.t)
    assert_equal(0, len(a.select("toplevels", "stmt")))


def test_nested_comments_unclosed():
    assert_raises(parsing.ParseError, parse, "/* /* oh no")


def test_comment_before_statement():
    expected = parse("constant x: u8 = 1")
    actual = parse("/* a comment */ constant x: u8 = 1")
    assert_equal(expected, actual)


def test_comment_after_statement():
    expected = parse("constant x: u8 = 1")
    actual = parse("constant x: u8 = 1 /* a comment */")
    assert_equal(expected, actual)


def test_comment_within_statement():
    expected = parse("constant x: u8 = 1")
    actual = parse("constant x: u8 = /* a comment */ 1")
    assert_equal(expected, actual)


def test_associativity():
    a = parse("constant x: u8 = 1 + 2 * 3")
    assert_equal(
        [
            ast.AstNode(
                "add",
                {
                    "lhs": ast.AstNode("numeric", {"value": 1}),
                    "rhs": ast.AstNode(
                        "mul",
                        {
                            "lhs": ast.AstNode("numeric", {"value": 2}),
                            "rhs": ast.AstNode("numeric", {"value": 3}),
                        },
                    ),
                },
            )
        ],
        a.select("toplevels", "stmt", "value"),
    )


def test_sign():
    a = parse("constant x: u8 = -1 + 2")
    assert_equal(
        [
            ast.AstNode(
                "add",
                {
                    "lhs": ast.AstNode(
                        "negate", {"value": ast.AstNode("numeric", {"value": 1})}
                    ),
                    "rhs": ast.AstNode("numeric", {"value": 2}),
                },
            )
        ],
        a.select("toplevels", "stmt", "value"),
    )


def test_parentheses():
    a = parse("constant x: u8 = (1 + 2) * 3")
    assert_equal(
        [
            ast.AstNode(
                "mul",
                {
                    "lhs": ast.AstNode(
                        "add",
                        {
                            "lhs": ast.AstNode("numeric", {"value": 1}),
                            "rhs": ast.AstNode("numeric", {"value": 2}),
                        },
                    ),
                    "rhs": ast.AstNode("numeric", {"value": 3}),
                },
            )
        ],
        a.select("toplevels", "stmt", "value"),
    )


def test_nested_parentheses():
    a = parse("constant x: u8 = ((1 + 2) / 3) + 4")
    assert_equal(
        [
            ast.AstNode(
                "add",
                {
                    "lhs": ast.AstNode(
                        "div",
                        {
                            "lhs": ast.AstNode(
                                "add",
                                {
                                    "lhs": ast.AstNode("numeric", {"value": 1}),
                                    "rhs": ast.AstNode("numeric", {"value": 2}),
                                },
                            ),
                            "rhs": ast.AstNode("numeric", {"value": 3}),
                        },
                    ),
                    "rhs": ast.AstNode("numeric", {"value": 4}),
                },
            )
        ],
        a.select("toplevels", "stmt", "value"),
    )


def test_parentheses_with_sign():
    a = parse("constant x: u8 = -(1 + 2)")
    e = a.select("toplevels", "stmt", "value")[0]
    assert_equal("negate", e.t)
    assert_equal("add", e.attrs["value"].t)
    assert_equal(
        [
            ast.AstNode(
                "negate",
                {
                    "value": ast.AstNode(
                        "add",
                        {
                            "lhs": ast.AstNode("numeric", {"value": 1}),
                            "rhs": ast.AstNode("numeric", {"value": 2}),
                        },
                    )
                },
            )
        ],
        a.select("toplevels", "stmt", "value"),
    )


def test_unmatched_open_parentheses():
    assert_raises(parsing.ParseError, parse, "constant x: u8 = (1 + 2")


def test_unmatched_close_parentheses():
    assert_raises(parsing.ParseError, parse, "constant x: u8 = 1 + 2)")


def test_member_access():
    a = parse("let a: u8 = foo.bar")
    assert_equal(
        [
            ast.AstNode(
                "let",
                {
                    "name": "a",
                    "type": "u8",
                    "storage": None,
                    "value": ast.AstNode(
                        "member_access",
                        {
                            "namespace": ast.AstNode("identifier", {"name": "foo"}),
                            "member": "bar",
                        },
                    ),
                },
            )
        ],
        a.select("toplevels", "stmt"),
    )


def test_let_with_mut_storage_class():
    a = parse("let mut a: u8 = 7")
    assert_equal(
        [
            ast.AstNode(
                "let",
                {
                    "name": "a",
                    "type": "u8",
                    "storage": "mut",
                    "value": ast.AstNode("numeric", {"value": 7}),
                },
            )
        ],
        a.select("toplevels", "stmt"),
    )


def test_let_with_stash_storage_class():
    a = parse("let stash a: u8 = 7")
    assert_equal(
        [
            ast.AstNode(
                "let",
                {
                    "name": "a",
                    "type": "u8",
                    "storage": "stash",
                    "value": ast.AstNode("numeric", {"value": 7}),
                },
            )
        ],
        a.select("toplevels", "stmt"),
    )


def test_let_without_storage_class():
    a = parse("let a: u8 = 7")
    assert_equal(
        [
            ast.AstNode(
                "let",
                {
                    "name": "a",
                    "type": "u8",
                    "storage": None,
                    "value": ast.AstNode("numeric", {"value": 7}),
                },
            )
        ],
        a.select("toplevels", "stmt"),
    )


def test_complex_type():
    a = parse("let a: &u8 = 0")
    assert_equal(
        [
            ast.AstNode(
                "let",
                {
                    "name": "a",
                    "storage": None,
                    "type": ast.AstNode("type_ref", {"storage": None, "type": "u8"}),
                    "value": ast.AstNode("numeric", {"value": 0}),
                },
            )
        ],
        a.select("toplevels", "stmt"),
    )


@given(
    st.characters(("Lu", "Ll", "Lt", "Lm", "Lo")),
    st.text(
        st.characters(
            blacklist_characters='()[]{}:;.,"@&',
            blacklist_categories=("Zs", "Zl", "Zp", "Cc"),
        )
    ),
)
def test_identifiers(name0, name):
    name = name0 + name
    a = parse(f"let a: u8 = {name}")
    assert_equal(
        [ast.AstNode("identifier", {"name": name})],
        a.select("toplevels", "stmt", "value"),
    )


@given(st.integers())
def test_numeric_hex_valid(n):
    a = parse(f"let a: u8 = 0x{n:x}")
    assert_equal(
        [ast.AstNode("numeric", {"value": n})], a.select("toplevels", "stmt", "value")
    )


def test_numeric_hex_invalid():
    assert_raises(parsing.ParseError, parse, "let a: u8 = 0xcage")


@given(st.integers())
def test_numeric_oct_valid(n):
    a = parse(f"let a: u8 = 0o{n:o}")
    assert_equal(
        [ast.AstNode("numeric", {"value": n})], a.select("toplevels", "stmt", "value")
    )


def test_numeric_oct_invalid():
    assert_raises(parsing.ParseError, parse, "let a: u8 = 0o18")


@given(st.integers())
def test_numeric_bin_valid(n):
    a = parse(f"let a: u8 = 0b{n:b}")
    assert_equal(
        [ast.AstNode("numeric", {"value": n})], a.select("toplevels", "stmt", "value")
    )


def test_numeric_bin_invalid():
    assert_raises(parsing.ParseError, parse, "let a: u8 = 0b012")


def test_let_with_invalid_storage_class():
    assert_raises(parsing.ParseError, parse, "let bogus a: u8 = 7")


def test_let_multistatement():
    a = parse(
        """
    let a: u8 = 0
    let b: u8 = 0
    """
    )
    assert_equal(["let", "let"], [n.t for n in a.select("toplevels", "stmt")])


@nottest
def test_array_declaration():
    # a = parse("let x: [u8; 0 to 3] = [0, 1, 2]")
    # assert_equal(1, len(a.statements))
    # t = a.statements[0]
    # assert_is_instance(t, ast.StatementLetNode)
    # assert_is_instance(t.binding, ast.OperatorAssignNode)
    # assert_is_instance(t.binding.lhs, ast.PunctuationValueTypeNode)
    # assert_is_instance(t.binding.lhs.rhs, ast.BracketsNode)
    # assert_is_instance(t.binding.rhs, ast.BracketsNode)

    # signature = t.binding.lhs.rhs.contents
    # assert_is_instance(signature, ast.PunctuationArrayRangeNode)
    # assert_equal(signature.lhs.text, "u8")
    # assert_is_instance(signature.rhs, ast.OperatorRangeNode)
    # assert_equal(signature.rhs.lhs.text, "0")
    # assert_equal(signature.rhs.rhs.text, "3")

    # values = t.binding.rhs.contents
    # assert_is_instance(values, ast.PunctuationCommaNode)
    # assert_equal(values.lhs.text, "0")
    # assert_is_instance(values.rhs, ast.PunctuationCommaNode)
    # assert_equal(values.rhs.lhs.text, "1")
    # assert_equal(values.rhs.rhs.text, "2")
    pass


@nottest
def test_array_declaration_shorthand():
    # a = parse("let x: [u8; 3] = [0, 1, 2]")
    # assert_equal(1, len(a.statements))
    # t = a.statements[0]
    # assert_is_instance(t, ast.StatementLetNode)
    # assert_is_instance(t.binding, ast.OperatorAssignNode)
    # assert_is_instance(t.binding.lhs, ast.PunctuationValueTypeNode)
    # assert_is_instance(t.binding.lhs.rhs, ast.BracketsNode)
    # assert_is_instance(t.binding.rhs, ast.BracketsNode)

    # signature = t.binding.lhs.rhs.contents
    # assert_is_instance(signature, ast.PunctuationArrayRangeNode)
    # assert_equal(signature.lhs.text, "u8")
    # assert_equal(signature.rhs.text, "3")

    # values = t.binding.rhs.contents
    # assert_is_instance(values, ast.PunctuationCommaNode)
    # assert_equal(values.lhs.text, "0")
    # assert_is_instance(values.rhs, ast.PunctuationCommaNode)
    # assert_equal(values.rhs.lhs.text, "1")
    # assert_equal(values.rhs.rhs.text, "2")
    pass


@nottest
def test_array_multidimensional():
    # a = parse("let x: [u8; 2, 1 to 3] = [[0, 1], [2, 3]]")
    # assert_equal(1, len(a.statements))
    # t = a.statements[0]
    # assert_is_instance(t, ast.StatementLetNode)
    # assert_is_instance(t.binding, ast.OperatorAssignNode)
    # assert_is_instance(t.binding.lhs, ast.PunctuationValueTypeNode)
    # assert_is_instance(t.binding.lhs.rhs, ast.BracketsNode)
    # assert_is_instance(t.binding.rhs, ast.BracketsNode)

    # signature = t.binding.lhs.rhs.contents
    # assert_is_instance(signature, ast.PunctuationArrayRangeNode)
    # assert_equal(signature.lhs.text, "u8")
    # assert_is_instance(signature.rhs, ast.PunctuationCommaNode)
    # assert_equal(signature.rhs.lhs.text, "2")
    # assert_is_instance(signature.rhs.rhs, ast.OperatorRangeNode)
    # assert_equal(signature.rhs.rhs.lhs.text, "1")
    # assert_equal(signature.rhs.rhs.rhs.text, "3")

    # values = t.binding.rhs.contents
    # assert_is_instance(values, ast.PunctuationCommaNode)
    # assert_is_instance(values.lhs, ast.BracketsNode)
    # assert_is_instance(values.rhs, ast.BracketsNode)

    # values = [values.lhs.contents, values.rhs.contents]
    # assert_is_instance(values[0], ast.PunctuationCommaNode)
    # assert_equal(values[0].lhs.text, "0")
    # assert_equal(values[0].rhs.text, "1")
    # assert_is_instance(values[1], ast.PunctuationCommaNode)
    # assert_equal(values[1].lhs.text, "2")
    # assert_equal(values[1].rhs.text, "3")
    pass


def test_array_unmatched_open_bracket():
    assert_raises(parsing.ParseError, parse, "let x: [u8; 3] = [0, 1, 2")


def test_array_unmatched_close_bracket():
    assert_raises(parsing.ParseError, parse, "let x: [u8; 3] = 0, 1, 2]")


def test_string_literal():
    a = parse('let a: [u8; 5] = "this is a string"')
    assert_equal(
        [ast.AstNode("string", {"value": "this is a string"})],
        a.select("toplevels", "stmt", "value"),
    )


def test_string_literal_with_space_after():
    a = parse('let a: [u8; 5] = "this is a string" ')
    assert_equal(
        [ast.AstNode("string", {"value": "this is a string"})],
        a.select("toplevels", "stmt", "value"),
    )


def test_string_multiline():
    a = parse(
        """
    let a: [u8; 5] = "this is a
very long
string"
    """
    )
    assert_equal(
        [ast.AstNode("string", {"value": "this is a\nvery long\nstring"})],
        a.select("toplevels", "stmt", "value"),
    )


def test_string_escaped():
    a = parse(r'let a: [u8; 5] = "this is a \"string"')
    assert_equal(
        [ast.AstNode("string", {"value": 'this is a "string'})],
        a.select("toplevels", "stmt", "value"),
    )


def test_fun_call_empty():
    a = parse("let a: u8 = foo()")
    assert_equal(
        [
            ast.AstNode(
                "call",
                {"target": ast.AstNode("identifier", {"name": "foo"}), "args": None},
            )
        ],
        a.select("toplevels", "stmt", "value"),
    )


def test_fun_call_one():
    a = parse("let a: u8 = foo(7)")
    assert_equal(
        [
            ast.AstNode(
                "call",
                {
                    "target": ast.AstNode("identifier", {"name": "foo"}),
                    "args": ast.AstNode.make_sequence(
                        "alist", "arg", [ast.AstNode("numeric", {"value": 7})]
                    ),
                },
            )
        ],
        a.select("toplevels", "stmt", "value"),
    )


def test_fun_call_many():
    a = parse('let a: u8 = foo(7, "hello")')
    assert_equal(
        [
            ast.AstNode(
                "call",
                {
                    "target": ast.AstNode("identifier", {"name": "foo"}),
                    "args": ast.AstNode.make_sequence(
                        "alist",
                        "arg",
                        [
                            ast.AstNode("numeric", {"value": 7}),
                            ast.AstNode("string", {"value": "hello"}),
                        ],
                    ),
                },
            )
        ],
        a.select("toplevels", "stmt", "value"),
    )


@nottest
def test_return():
    # a = parse("return 1 + 2")
    # assert_equal(1, len(a.statements))
    # r = a.statements[0]
    # assert_is_instance(r, ast.StatementReturnNode)
    # assert_is_instance(r.rhs, ast.OperatorAddNode)
    # assert_equal("1", r.rhs.lhs.text)
    # assert_equal("2", r.rhs.rhs.text)
    pass


@nottest
def test_return_empty():
    # a = parse("return")
    # assert_equal(1, len(a.statements))
    # r = a.statements[0]
    # assert_is_none(r.rhs)
    pass


def test_fun_def_void_empty():
    a = parse("fun foo() endfun")
    assert_equal(
        [
            ast.AstNode(
                "fun", {"name": "foo", "args": None, "return": None, "body": None}
            )
        ],
        a.select("toplevels", "stmt"),
    )


@nottest
def test_fun_def_void():
    # a = parse("""
    # fun foo(a: u8, b: u16)
    #    return
    # endfun
    # """)
    # assert_equal(1, len(a.statements))
    # f = a.statements[0]
    # assert_is_instance(f, ast.StatementFunNode)
    # s = f.signature
    # assert_is_instance(s, ast.FunctionCallNode)
    # assert_equal("foo", s.fun.text)
    # assert_is_instance(s.args, ast.PunctuationCommaNode)
    # aa = s.args.lhs
    # assert_is_instance(aa, ast.PunctuationValueTypeNode)
    # assert_equal("a", aa.lhs.text)
    # assert_equal("u8", aa.rhs.text)
    # ab = s.args.rhs
    # assert_is_instance(ab, ast.PunctuationValueTypeNode)
    # assert_equal("b", ab.lhs.text)
    # assert_equal("u16", ab.rhs.text)
    # assert_equal(1, len(f.children))
    # r = f.children[0]
    # assert_is_instance(r, ast.StatementReturnNode)
    # assert_is_none(r.rhs)
    pass


@nottest
def test_fun_def_nonvoid():
    # a = parse("""
    # fun id(x: u8) -> u8
    #     return x
    # endfun
    # """)
    # assert_equal(1, len(a.statements))
    # f = a.statements[0]
    # assert_is_instance(f, ast.StatementFunNode)
    # rt = f.signature
    # assert_is_instance(rt, ast.PunctuationReturnTypeNode)
    # assert_equal("u8", rt.rhs.text)
    # s = rt.lhs
    # assert_is_instance(s, ast.FunctionCallNode)
    # assert_equal("id", s.fun.text)
    # ax = s.args
    # assert_is_instance(ax, ast.PunctuationValueTypeNode)
    # assert_equal("x", ax.lhs.text)
    # assert_equal("u8", ax.rhs.text)
    # assert_equal(1, len(f.children))
    # r = f.children[0]
    # assert_is_instance(r, ast.StatementReturnNode)
    # assert_equal("x", r.rhs.text)
    pass


@nottest
def test_isr_def_empty():
    # a = parse("isr bar endisr")
    # assert_equal(1, len(a.statements))
    # f = a.statements[0]
    # assert_is_instance(f, ast.StatementIsrNode)
    # n = f.name
    # assert_is_instance(n, ast.IdentifierNode)
    # assert_equal(n.text, "bar")
    pass


@nottest
def test_isr_def():
    # a = parse("""
    # isr bar
    #     let a: u8 = 0
    #     let b: u8 = 0
    # endisr
    # """)
    # assert_equal(1, len(a.statements))
    # f = a.statements[0]
    # assert_is_instance(f, ast.StatementIsrNode)
    # n = f.name
    # assert_is_instance(n, ast.IdentifierNode)
    # assert_equal(n.text, "bar")
    # assert_equal(2, len(f.children))
    # assert_is_instance(f.children[0], ast.StatementLetNode)
    # assert_is_instance(f.children[1], ast.StatementLetNode)
    pass


def test_use():
    a = parse("use mem")
    assert_equal([ast.AstNode("use", {"name": "mem"})], a.select("toplevels", "stmt"))


def test_assign():
    a = parse("fun foo() a = 7 endfun")
    assert_equal(
        [
            ast.AstNode(
                "set",
                {
                    "lvalue": ast.AstNode("identifier", {"name": "a"}),
                    "rvalue": ast.AstNode("numeric", {"value": 7}),
                },
            )
        ],
        a.select("toplevels", "stmt", "body", "stmt"),
    )
