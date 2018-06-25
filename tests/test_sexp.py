import string
from hypothesis import given
import hypothesis.strategies as st
from nose.tools import (
    assert_equal)
from jeff65.brundle.sexp import dumps, loads, Atom


def test_parse_empty():
    assert_equal([], loads('()'))


def test_parse_atom():
    assert_equal(Atom('spam'), loads('spam'))


def test_parse_string():
    assert_equal("spam", loads('"spam"'))


def test_parse_numeric():
    assert_equal(42, loads('42'))


def test_parse_nested():
    assert_equal([
        Atom('let'), [
            [Atom('spam'), 42],
            [Atom('eggs'), "beans"],
        ],
        [Atom('foo'), Atom('bar')],
    ], loads('''
    (let ((spam 42)
          (eggs "beans"))
      (foo bar))
    '''))


@given(d=st.recursive(
    st.integers() | st.text() | st.builds(Atom, st.text(
        min_size=1, alphabet=string.ascii_letters)),
    lambda children: st.lists(children)))
def test_roundtrip(d):
    assert_equal(d, loads(dumps(d)))
