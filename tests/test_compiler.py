import io
import pathlib
import sys
from jeff65.blum import types
from jeff65.gold import compiler

sys.stderr = sys.stdout


def test_compile_empty():
    stdin = sys.stdin
    sys.stdin = io.StringIO("")

    try:
        archive = compiler.translate(pathlib.PurePath("-"))
    except BaseException:
        sys.stdin = stdin
        raise

    assert len(archive.symbols) == 0


def test_compile_simple():
    stdin = sys.stdin
    sys.stdin = io.StringIO(
        """
    fun main()
    endfun
    """
    )

    try:
        archive = compiler.translate(pathlib.PurePath("-"))
    except BaseException:
        sys.stdin = stdin
        raise

    assert len(archive.symbols) == 1
    sym = archive.symbols["-.main"]
    assert sym.section == "text"
    assert sym.data == b"\x60"
    assert len(sym.relocations) == 0
    assert sym.type_info == types.FunctionType(types.void)  # noqa: E721
