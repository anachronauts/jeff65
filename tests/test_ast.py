import io
import sys
from nose.tools import (
    assert_equal,
    assert_is_instance,
    assert_is_none,
    assert_raises)
from hypothesis import given, strategies as st
from jeff65 import ast, gold, parsing

sys.stderr = sys.stdout


def parse(source):
    with io.StringIO(source) as s:
        a = gold.parse(s, '<test>')
        print(a.pretty())
        return a


def parse_expr(source):
    source = f"let a: u8 = {source}"
    with io.StringIO(source) as s:
        a = gold.parse(s, '<test>').children[0]
        print(a.pretty())
        return a


def parse_block(source):
    source = f"fun a() {source} endfun"
    with io.StringIO(source) as s:
        a = gold.parse(s, '<test>').children[0]
        print(a.pretty())
        return a


def test_empty_file():
    a = parse("")
    assert_equal('unit', a.t)
    assert_equal(0, len(a.children))


def test_whitespace_only_file():
    a = parse("\n")
    assert_equal('unit', a.t)
    assert_equal(0, len(a.children))


def test_comments_newline():
    a = parse("/* a comment */\n")
    assert_equal('unit', a.t)
    assert_equal(0, len(a.children))


def test_comments_no_newline():
    a = parse("/* a comment */")
    assert_equal('unit', a.t)
    assert_equal(0, len(a.children))


def test_comments_multiline():
    a = parse("""
    /*
     * a multiline comment
     * with multiple lines
     */
    """)
    assert_equal('unit', a.t)
    assert_equal(0, len(a.children))


def test_comments_unclosed():
    assert_raises(parsing.ParseError, parse, "/* oh no")


def test_comments_unopened():
    assert_raises(parsing.ParseError, parse, "oh no */")


def test_nested_comment():
    a = parse("/* a /* nested */ comment */")
    assert_equal('unit', a.t)
    assert_equal(0, len(a.children))


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
    a = parse_expr("1 + 2 * 3")
    e = a.children[0]
    assert_equal('add', e.t)
    assert_equal('mul', e.children[1].t)


def test_sign():
    a = parse_expr("-1 + 2")
    e = a.children[0]
    assert_equal('add', e.t)
    assert_equal('negate', e.children[0].t)


def test_parentheses():
    a = parse_expr("(1 + 2) * 3")
    e = a.children[0]
    assert_equal('mul', e.t)
    assert_equal('add', e.children[0].t)


def test_nested_parentheses():
    a = parse_expr("((1 + 2) / 3) + 4")
    e = a.children[0]
    assert_equal('add', e.t)
    assert_equal('div', e.children[0].t)
    assert_equal('add', e.children[0].children[0].t)


def test_parentheses_with_sign():
    a = parse_expr("-(1 + 2)")
    e = a.children[0]
    assert_equal('negate', e.t)
    assert_equal('add', e.children[0].t)


def test_unmatched_open_parentheses():
    assert_raises(parsing.ParseError, parse_expr, "(1 + 2")


def test_unmatched_close_parentheses():
    assert_raises(parsing.ParseError, parse_expr, "1 + 2)")


def test_comparison_not_equals():
    a = parse_expr("1 != 2")
    assert_equal(1, len(a.children))
    assert_equal(
        ast.AstNode('cmp_ne', children=[
            ast.AstNode('numeric', attrs={'value': 1}),
            ast.AstNode('numeric', attrs={'value': 2}),
        ]),
        a.children[0])


def test_comparison_equals():
    a = parse_expr("2 == 1 + 1")
    assert_equal(1, len(a.children))
    assert_equal(
        ast.AstNode('cmp_eq', children=[
            ast.AstNode('numeric', attrs={'value': 2}),
            ast.AstNode('add', children=[
                ast.AstNode('numeric', attrs={'value': 1}),
                ast.AstNode('numeric', attrs={'value': 1}),
            ]),
        ]),
        a.children[0])


def test_comparison_lt():
    a = parse_expr("3 < (1 + 1) * 2")
    assert_equal(1, len(a.children))
    assert_equal(
        ast.AstNode('cmp_lt', children=[
            ast.AstNode('numeric', attrs={'value': 3}),
            ast.AstNode('mul', children=[
                ast.AstNode('add', children=[
                    ast.AstNode('numeric', attrs={'value': 1}),
                    ast.AstNode('numeric', attrs={'value': 1}),
                ]),
                ast.AstNode('numeric', attrs={'value': 2}),
            ]),
        ]),
        a.children[0])


def test_comparison_gt():
    a = parse_expr("5 > (1 + 1) * 2")
    assert_equal(1, len(a.children))
    assert_equal(
        ast.AstNode('cmp_gt', children=[
            ast.AstNode('numeric', attrs={'value': 5}),
            ast.AstNode('mul', children=[
                ast.AstNode('add', children=[
                    ast.AstNode('numeric', attrs={'value': 1}),
                    ast.AstNode('numeric', attrs={'value': 1}),
                ]),
                ast.AstNode('numeric', attrs={'value': 2}),
            ]),
        ]),
        a.children[0])


def test_comparison_lte():
    a = parse_expr("x <= 5")
    assert_equal(1, len(a.children))
    assert_equal(
        ast.AstNode('cmp_le', children=[
            ast.AstNode('identifier', attrs={'name': 'x'}),
            ast.AstNode('numeric', attrs={'value': 5}),
        ]),
        a.children[0])


def test_comparison_gte():
    a = parse_expr("5 >= x")
    assert_equal(1, len(a.children))
    assert_equal(
        ast.AstNode('cmp_ge', children=[
            ast.AstNode('numeric', attrs={'value': 5}),
            ast.AstNode('identifier', attrs={'name': 'x'}),
        ]),
        a.children[0])


def test_member_access():
    a = parse_expr("foo.bar")
    print(a.pretty())
    assert_equal(
        ast.AstNode('member_access', attrs={
            'member': 'bar',
        }, children=[
            ast.AstNode('identifier', attrs={
                'name': 'foo',
            }),
        ]),
        a.children[0])


def test_let_with_mut_storage_class():
    a = parse("let mut a: u8 = 7")
    assert_equal(1, len(a.children))
    s = a.children[0]
    assert_equal('let', s.t)
    assert_equal(3, len(s.attrs))
    assert_equal('a', s.attrs['name'])
    assert_equal('mut', s.attrs['storage'])
    assert_equal('u8', s.attrs['type'])
    assert_equal(1, len(s.children))
    n = s.children[0]
    assert_equal('numeric', n.t)
    assert_equal(7, n.attrs['value'])


def test_let_with_stash_storage_class():
    a = parse("let stash a: u8 = 7")
    assert_equal(1, len(a.children))
    s = a.children[0]
    assert_equal('let', s.t)
    assert_equal(3, len(s.attrs))
    assert_equal('a', s.attrs['name'])
    assert_equal('stash', s.attrs['storage'])
    assert_equal('u8', s.attrs['type'])
    assert_equal(1, len(s.children))
    n = s.children[0]
    assert_equal('numeric', n.t)
    assert_equal(7, n.attrs['value'])


def test_let_without_storage_class():
    a = parse("let a: u8 = 7")
    assert_equal(1, len(a.children))
    s = a.children[0]
    assert_equal('let', s.t)
    assert_equal(2, len(s.attrs))
    assert_equal('a', s.attrs['name'])
    assert_equal('u8', s.attrs['type'])
    assert_equal(1, len(s.children))
    n = s.children[0]
    assert_equal('numeric', n.t)
    assert_equal(7, n.attrs['value'])


def test_complex_type():
    a = parse("let a: &u8 = 0")
    print(a.pretty())
    assert_equal(
        ast.AstNode('let', attrs={
            'name': 'a',
            'type': ast.AstNode('type_ref', attrs={
                'type': 'u8',
            }),
        }, children=[
            ast.AstNode('numeric', attrs={
                'value': 0,
            }),
        ]),
        a.children[0])


@given(st.characters(('Lu', 'Ll', 'Lt', 'Lm', 'Lo')),
       st.text(st.characters(blacklist_characters='()[]{}:;.,"\@&',
                             blacklist_categories=('Zs', 'Zl', 'Zp', 'Cc'))))
def test_identifiers(name0, name):
    name = name0 + name
    a = parse(f"let a: u8 = {name}")
    print(a.pretty())
    assert_equal(ast.AstNode('let', attrs={
        'name': 'a',
        'type': 'u8',
    }, children=[
        ast.AstNode('identifier', attrs={
            'name': name,
        })
    ]), a.children[0])


@given(st.integers())
def test_numeric_hex_valid(n):
    a = parse(f"let a: u8 = 0x{n:x}")
    print(a.pretty())
    assert_equal(ast.AstNode('let', attrs={
        'name': 'a',
        'type': 'u8',
    }, children=[
        ast.AstNode('numeric', attrs={
            'value': n,
        })
    ]), a.children[0])


def test_numeric_hex_invalid():
    assert_raises(parsing.ParseError, parse, "let a: u8 = 0xcage")


@given(st.integers())
def test_numeric_oct_valid(n):
    a = parse(f"let a: u8 = 0o{n:o}")
    print(a.pretty())
    assert_equal(ast.AstNode('let', attrs={
        'name': 'a',
        'type': 'u8',
    }, children=[
        ast.AstNode('numeric', attrs={
            'value': n,
        })
    ]), a.children[0])


def test_numeric_oct_invalid():
    assert_raises(parsing.ParseError, parse, "let a: u8 = 0o18")


@given(st.integers())
def test_numeric_bin_valid(n):
    a = parse(f"let a: u8 = 0b{n:b}")
    print(a.pretty())
    assert_equal(ast.AstNode('let', attrs={
        'name': 'a',
        'type': 'u8',
    }, children=[
        ast.AstNode('numeric', attrs={
            'value': n,
        })
    ]), a.children[0])


def test_numeric_bin_invalid():
    assert_raises(parsing.ParseError, parse, "let a: u8 = 0b012")


def test_let_with_invalid_storage_class():
    assert_raises(parsing.ParseError, parse, "let bogus a: u8 = 7")


def test_let_multistatement():
    a = parse("""
    let a: u8 = 0
    let b: u8 = 0
    """)
    assert_equal(2, len(a.children))
    assert_equal('let', a.children[0].t)
    assert_equal('let', a.children[1].t)


def test_array_declaration():
    a = parse("let x: [u8; 0 to 3] = [0, 1, 2]")
    assert_equal(1, len(a.children))
    s = a.children[0]
    assert_equal('let', s.t)
    t = s.attrs['type']
    assert_equal('type_array', t.t)
    assert_equal({'type': 'u8'}, t.attrs)
    assert_equal(2, len(t.children))
    assert_equal('numeric', t.children[0].t)
    assert_equal({'value': 0}, t.children[0].attrs)
    assert_equal('numeric', t.children[1].t)
    assert_equal({'value': 3}, t.children[1].attrs)

    assert False, "TODO: create a node for the RHS list"
    values = s.binding.rhs.contents
    assert_is_instance(values, ast.PunctuationCommaNode)
    assert_equal(values.lhs.text, "0")
    assert_is_instance(values.rhs, ast.PunctuationCommaNode)
    assert_equal(values.rhs.lhs.text, "1")
    assert_equal(values.rhs.rhs.text, "2")


def test_array_declaration_shorthand():
    a = parse("let x: [u8; 3] = [0, 1, 2]")
    assert_equal(1, len(a.children))
    s = a.children[0]
    assert_equal('let', s.t)
    t = s.attrs['type']
    assert_equal('type_array', t.t)
    assert_equal({'type': 'u8'}, t.attrs)
    assert_equal(1, len(t.children))
    assert_equal('numeric', t.children[0].t)
    assert_equal({'value': 3}, t.children[0].attrs)

    assert False, "TODO: create a node for the RHS list"
    values = t.binding.rhs.contents
    assert_is_instance(values, ast.PunctuationCommaNode)
    assert_equal(values.lhs.text, "0")
    assert_is_instance(values.rhs, ast.PunctuationCommaNode)
    assert_equal(values.rhs.lhs.text, "1")
    assert_equal(values.rhs.rhs.text, "2")


def test_array_multidimensional():
    assert False, "TODO: the syntax file doesn't even support this"
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
    assert_raises(parsing.ParseError, parse, "let x: [u8; 3] = [0, 1, 2")


def test_array_unmatched_close_bracket():
    assert_raises(parsing.ParseError, parse, "let x: [u8; 3] = 0, 1, 2]")


def test_basic_assign():
    a = parse_block("x = 5")
    assert_equal(1, len(a.children))
    assert_equal(
        ast.AstNode('set', children=[
            ast.AstNode('identifier', attrs={'name': 'x'}),
            ast.AstNode('numeric', attrs={'value': 5}),
        ]),
        a.children[0])


def test_multiple_assign():
    a = parse_block("""
    x = 5
    y = 6
    """)
    assert_equal(2, len(a.children))
    assert_equal(
        ast.AstNode('set', children=[
            ast.AstNode('identifier', attrs={'name': 'x'}),
            ast.AstNode('numeric', attrs={'value': 5}),
        ]),
        a.children[0]
    )
    assert_equal(
        ast.AstNode('set', children=[
            ast.AstNode('identifier', attrs={'name': 'y'}),
            ast.AstNode('numeric', attrs={'value': 6}),
        ]),
        a.children[1]
    )


def test_array_member_assign():
    a = parse_block("x[0] = 5")
    assert False, "TODO: handle indexed expressions"
    assert_equal(1, len(a.statements))
    s = a.statements[0]
    assert_is_instance(s, ast.OperatorAssignNode)
    assert_is_instance(s.lhs, ast.IdentifierNode)
    assert_equal(s.lhs.text, "x")
    assert_equal(len(s.lhs.member_index.children), 1)
    member_index = s.lhs.member_index.children[0]
    assert_is_instance(member_index, ast.NumericNode)
    assert_equal(member_index.text, "0")
    assert_is_instance(s.rhs, ast.NumericNode)
    assert_equal(s.rhs.text, "5")


def test_assign_with_array_member():
    a = parse_block("x = y[0]")
    assert False, "TODO: handle indexed expressions"
    assert_equal(1, len(a.statements))
    s = a.statements[0]
    assert_is_instance(s, ast.OperatorAssignNode)
    assert_is_instance(s.lhs, ast.IdentifierNode)
    assert_equal(s.lhs.text, "x")
    assert_is_instance(s.rhs, ast.IdentifierNode)
    assert_equal(s.rhs.text, "y")
    assert_equal(len(s.rhs.member_index.children), 1)
    member_index = s.rhs.member_index.children[0]
    assert_is_instance(member_index, ast.NumericNode)
    assert_equal(member_index.text, "0")


def test_basic_increment():
    a = parse_block("x += 1")
    assert False, "TODO: support increment statements"
    assert_equal(1, len(a.statements))
    s = a.statements[0]
    assert_is_instance(s, ast.OperatorAssignNode)
    assert_is_instance(s.lhs, ast.IdentifierNode)
    assert_equal(s.lhs.text, "x")
    assert_is_instance(s.rhs, ast.OperatorAddNode)
    assert_is_instance(s.rhs.lhs, ast.IdentifierNode)
    assert_equal(s.rhs.lhs.text, "x")
    assert_is_instance(s.rhs.rhs, ast.NumericNode)
    assert_equal(s.rhs.rhs.text, "1")


def test_basic_decrement():
    a = parse_block("x -= 1")
    assert False, "TODO: support decrement statements"
    assert_equal(1, len(a.statements))
    s = a.statements[0]
    assert_is_instance(s, ast.OperatorAssignNode)
    assert_is_instance(s.lhs, ast.IdentifierNode)
    assert_equal(s.lhs.text, "x")
    assert_is_instance(s.rhs, ast.OperatorSubtractNode)
    assert_is_instance(s.rhs.lhs, ast.IdentifierNode)
    assert_equal(s.rhs.lhs.text, "x")
    assert_is_instance(s.rhs.rhs, ast.NumericNode)
    assert_equal(s.rhs.rhs.text, "1")


def test_string_literal():
    a = parse('let a: [u8; 5] = "this is a string"')
    assert_equal(1, len(a.children))
    print(a.pretty())
    s = a.children[0].children[0]
    assert_equal('string', s.t)
    assert_equal("this is a string", s.attrs['value'])


def test_string_literal_with_space_after():
    a = parse('let a: [u8; 5] = "this is a string" ')
    assert_equal(1, len(a.children))
    print(a.pretty())
    s = a.children[0].children[0]
    assert_equal('string', s.t)
    assert_equal("this is a string", s.attrs['value'])


def test_string_multiline():
    a = parse('''
    let a: [u8; 5] = "this is a
very long
string"
    ''')
    assert_equal(1, len(a.children))
    print(a.pretty())
    s = a.children[0].children[0]
    assert_equal('string', s.t)
    assert_equal("this is a\nvery long\nstring", s.attrs['value'])


def test_string_escaped():
    a = parse(r'let a: [u8; 5] = "this is a \"string"')
    assert_equal(1, len(a.children))
    print(a.pretty())
    s = a.children[0].children[0]
    assert_equal('string', s.t)
    assert_equal(r'this is a "string', s.attrs['value'])
    pass


def test_fun_call_empty():
    a = parse_block("foo()")
    assert_equal(1, len(a.children))
    assert_equal(
        ast.AstNode('call', attrs={
            'target': ast.AstNode('identifier', attrs={'name': 'foo'})
        }),
        a.children[0])


def test_fun_call_one():
    a = parse_block("foo(7)")
    print(a.pretty())
    assert_equal(
        ast.AstNode('call', attrs={
            'target': ast.AstNode('identifier', attrs={
                'name': 'foo',
            }),
        }, children=[
            ast.AstNode('numeric', attrs={
                'value': 7,
            }),
        ]),
        a.children[0])


def test_fun_call_many():
    a = parse_block('foo(7, "hello")')
    assert_equal(1, len(a.children))
    assert_equal(
        ast.AstNode('call', attrs={
            'target': ast.AstNode('identifier', attrs={
                'name': 'foo',
            }),
        }, children=[
            ast.AstNode('numeric', attrs={
                'value': 7,
            }),
            ast.AstNode('string', attrs={
                'value': "hello",
            }),
        ]),
        a.children[0])


def test_member_access_function():
    a = parse_block("foo.bar(baz)")
    assert_equal(1, len(a.children))
    assert_equal(
        ast.AstNode('call', attrs={
            'target': ast.AstNode(
                'member_access', attrs={'member': 'bar'}, children=[
                    ast.AstNode('identifier', attrs={'name': 'foo'}),
                ]),
        }, children=[
            ast.AstNode('identifier', attrs={'name': 'baz'}),
        ]),
        a.children[0])


def test_return():
    a = parse_block("return 1 + 2")
    assert False, "TODO: AST support return statements"
    assert_equal(1, len(a.statements))
    r = a.statements[0]
    assert_is_instance(r, ast.StatementReturnNode)
    assert_is_instance(r.rhs, ast.OperatorAddNode)
    assert_equal("1", r.rhs.lhs.text)
    assert_equal("2", r.rhs.rhs.text)


def test_return_empty():
    a = parse_block("return")
    assert False, "TODO: AST support return statements"
    assert_equal(1, len(a.statements))
    r = a.statements[0]
    assert_is_none(r.rhs)


def test_fun_def_void_empty():
    a = parse("fun foo() endfun")
    f = a.children[0]
    assert_equal('fun', f.t)
    assert_equal('foo', f.attrs['name'])
    assert_is_none(f.attrs['return'])
    assert_equal(0, len(f.attrs['args']))
    assert_equal(0, len(f.children))


def test_fun_def_void():
    a = parse("""
    fun foo(a: u8, b: u16)
       return
    endfun
    """)
    assert False, "TODO: AST support function args, return statements"
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
    assert False, "TODO: AST support function args, return types, return stmts"
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
    assert False, "TODO: AST support isrs"
    assert_equal(1, len(a.statements))
    f = a.statements[0]
    assert_is_instance(f, ast.StatementIsrNode)
    n = f.name
    assert_is_instance(n, ast.IdentifierNode)
    assert_equal(n.text, "bar")


def test_isr_def():
    a = parse("""
    isr bar
        let a: u8 = 0
        let b: u8 = 0
    endisr
    """)
    assert False, "TODO: AST support isrs"
    assert_equal(1, len(a.statements))
    f = a.statements[0]
    assert_is_instance(f, ast.StatementIsrNode)
    n = f.name
    assert_is_instance(n, ast.IdentifierNode)
    assert_equal(n.text, "bar")
    assert_equal(2, len(f.children))
    assert_is_instance(f.children[0], ast.StatementLetNode)
    assert_is_instance(f.children[1], ast.StatementLetNode)


def test_while_single_statement():
    a = parse_block("""
    while x < 5 do
        x = x + 1
    end
    """)
    assert False, "TODO: AST support while, comparisons"
    assert_equal(1, len(a.statements))
    s = a.statements[0]
    assert_is_instance(s, ast.StatementWhileNode)
    c = s.condition
    assert_is_instance(c, ast.OperatorLessThanNode)
    assert_is_instance(c.lhs, ast.IdentifierNode)
    assert_is_instance(c.rhs, ast.NumericNode)
    b = s.children
    assert_equal(1, len(b))
    assert_is_instance(b[0], ast.OperatorAssignNode)
    assert_is_instance(b[0].lhs, ast.IdentifierNode)
    assert_is_instance(b[0].rhs, ast.OperatorAddNode)


def test_while_multistatement():
    a = parse_block("""
    while x < 5 do
        x = x + 1
        y = 2 * x
    end
    """)
    assert False, "TODO: AST support while, comparisons"
    assert_equal(1, len(a.statements))
    s = a.statements[0]
    assert_is_instance(s, ast.StatementWhileNode)
    c = s.condition
    assert_is_instance(c, ast.OperatorLessThanNode)
    assert_is_instance(c.lhs, ast.IdentifierNode)
    assert_is_instance(c.rhs, ast.NumericNode)
    b = s.children
    assert_equal(2, len(b))
    assert_is_instance(b[0], ast.OperatorAssignNode)
    assert_is_instance(b[0].lhs, ast.IdentifierNode)
    assert_is_instance(b[0].rhs, ast.OperatorAddNode)
    assert_is_instance(b[1], ast.OperatorAssignNode)
    assert_is_instance(b[1].lhs, ast.IdentifierNode)
    assert_is_instance(b[1].rhs, ast.OperatorAddNode)


def test_while_missing_do():
    assert_raises(parsing.ParseError, parse, "while x < 5 x = x + 1 end")


def test_while_missing_end():
    assert_raises(parsing.ParseError, parse, "while x < 5 do x = x + 1")


def test_use():
    a = parse("use mem")
    print(a.pretty())
    assert_equal(1, len(a.children))
    u = a.children[0]
    assert_equal('use', u.t)
    assert_equal("mem", u.attrs['name'])


def test_assign():
    a = parse("fun foo() a = 7 endfun")
    print(a.pretty())
    assert_equal(
        ast.AstNode('set', children=[
            ast.AstNode('identifier', attrs={'name': 'a'}),
            ast.AstNode('numeric', attrs={'value': 7}),
        ]),
        a.children[0].children[0])
