import string
from hypothesis import given
import hypothesis.strategies as st
from nose.tools import (
    assert_equal)
from jeff65.brundle.ast import AstNode
from jeff65.brundle.sexp import dumps, loads


def test_parse_empty():
    assert_equal(AstNode('unit'), loads(''))


def test_parse_nil():
    assert_equal(
        AstNode('unit', children=[
            AstNode('nil')
        ]),
        loads('nil'))


def test_parse_bool():
    assert_equal(
        AstNode('unit', children=[
            AstNode('boolean', attrs={'value': True})
        ]),
        loads('#t'))
    assert_equal(
        AstNode('unit', children=[
            AstNode('boolean', attrs={'value': False})
        ]),
        loads('#f'))


def test_parse_atom():
    assert_equal(
        AstNode('unit', children=[
            AstNode('atom', attrs={'name': 'spam'})
        ]),
        loads('spam'))


def test_parse_string():
    assert_equal(
        AstNode('unit', children=[
            AstNode('string', attrs={'value': 'spam'})
        ]),
        loads('"spam"'))


def test_parse_numeric():
    assert_equal(
        AstNode('unit', children=[
            AstNode('numeric', attrs={'value': 42})
        ]),
        loads('42'))


def test_parse_nested():
    assert_equal(
        AstNode('unit', children=[
            AstNode('list', children=[
                AstNode('atom', attrs={'name': 'let'}),
                AstNode('list', children=[
                    AstNode('list', children=[
                        AstNode('atom', attrs={'name': 'spam'}),
                        AstNode('numeric', attrs={'value': 42}),
                    ]),
                    AstNode('list', children=[
                        AstNode('atom', attrs={'name': 'eggs'}),
                        AstNode('string', attrs={'value': "beans"}),
                    ])
                ]),
                AstNode('list', children=[
                    AstNode('atom', attrs={'name': 'foo'}),
                    AstNode('atom', attrs={'name': 'bar'}),
                ])
            ])
        ]),
        loads('''
        (let [(spam 42)
            (eggs "beans")]
        (foo bar))
        '''))


@st.composite
def sbooleans(draw):
    return AstNode('boolean', attrs={'value': draw(st.booleans())})


@st.composite
def snumerics(draw):
    return AstNode('numeric', attrs={'value': draw(st.integers())})


@st.composite
def sstrings(draw):
    return AstNode('string', attrs={'value': draw(st.text())})


@st.composite
def satoms(draw):
    return AstNode('atom', attrs={'name': draw(st.text(
        min_size=1, alphabet=string.ascii_letters))})


@st.composite
def slists(draw):
    return draw(st.recursive(
        st.just(AstNode('nil'))
        | sbooleans()
        | snumerics()
        | sstrings()
        | satoms(),
        lambda children: st.builds(
            AstNode, st.just('list'), children=st.lists(children))))


@st.composite
def sunits(draw):
    return AstNode('unit', children=draw(
        st.lists(
            st.just(AstNode('nil'))
            | sbooleans()
            | snumerics()
            | sstrings()
            | satoms()
            | slists())))


@given(d=sunits())
def test_roundtrip(d):
    print(d.pretty(no_position=True))
    s = dumps(d)
    print(s)
    assert_equal(d, loads(s))
