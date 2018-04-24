import io
import pathlib
import sys
from nose.tools import (
    assert_equal)
from jeff65.gold import compiler, types

sys.stderr = sys.stdout


def test_compile_empty():
    stdin = sys.stdin
    sys.stdin = io.StringIO("")

    try:
        archive = compiler.translate(pathlib.PurePath('-'))
    except BaseException:
        sys.stdin = stdin
        raise

    assert_equal(0, len(archive.symbols))
    assert_equal(0, len(archive.constants))


def test_compile_simple():
    stdin = sys.stdin
    sys.stdin = io.StringIO("""
    fun main()
    endfun
    """)

    try:
        archive = compiler.translate(pathlib.PurePath('-'))
    except BaseException:
        sys.stdin = stdin
        raise

    assert_equal(1, len(archive.symbols))
    assert_equal(0, len(archive.constants))
    sym = archive.symbols['-.main']
    assert_equal('text', sym.section)
    assert_equal(b'\x60', sym.data)
    assert_equal(0, len(sym.relocations))
    assert_equal(types.FunctionType(None), sym.attrs['type'])