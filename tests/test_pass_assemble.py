import sys
from nose.tools import (
    assert_equal,
    assert_raises)
from jeff65 import ast
from jeff65.blum import types
from jeff65.gold import storage
from jeff65.gold.passes import asm

sys.stderr = sys.stdout


def assemble(node):
    backup = node.pretty()
    result = node.transform(asm.AssembleWithRelocations())
    assert_equal(1, len(result))
    # check that the previous AST wasn't mutated
    assert_equal(backup, node.pretty())
    return result[0]


def flatten(unit):
    backup = unit.pretty()
    result = unit.transform(asm.FlattenSymbol())
    # check that the previous AST wasn't mutated
    assert_equal(backup, unit.pretty())
    return result


def test_assemble_rts():
    a = asm.rts(None)
    assert_equal('rts', a.t)
    assert_equal(1, a.attrs['size'])
    b = assemble(a)
    assert_equal(bytes([0x60]), b.data)


def test_assemble_jmp_abs():
    a = asm.jmp(storage.AbsoluteStorage(0xbeef, 0), None)
    assert_equal('jmp', a.t)
    assert_equal(3, a.attrs['size'])
    b = assemble(a)
    assert_equal(bytes([0x4c, 0xef, 0xbe]), b.data)


def test_assemble_lda_imm():
    a = asm.lda(storage.ImmediateStorage(0x42, 1), None)
    assert_equal('lda', a.t)
    assert_equal(2, a.attrs['size'])
    b = assemble(a)
    assert_equal(bytes([0xa9, 0x42]), b.data)


def test_assemble_lda_imm_too_wide():
    a = asm.lda(storage.ImmediateStorage(0xcafe, 2), None)
    assert_raises(asm.AssemblyError, assemble, a)


def test_assemble_sta_abs():
    a = asm.sta(storage.AbsoluteStorage(0xbeef, 1), None)
    assert_equal('sta', a.t)
    assert_equal(3, a.attrs['size'])
    b = assemble(a)
    assert_equal(bytes([0x8d, 0xef, 0xbe]), b.data)


def test_assemble_sta_abs_too_wide():
    a = asm.sta(storage.AbsoluteStorage(0xbeef, 2), None)
    assert_raises(asm.AssemblyError, assemble, a)


def test_flatten_symbol():
    a = ast.AstNode('unit', attrs={
        'known_names': {},
    }, children=[
        ast.AstNode('fun', attrs={
            'name': 'meaning-of-life',
            'type': types.FunctionType(types.u8),
        }, children=[
            asm.AsmRun(bytes([0xa9, 0x42])),
            asm.AsmRun(bytes([0x60])),
        ])
    ])
    b = flatten(a)
    assert_equal(1, len(b.children))
    sym = b.children[0]
    assert_equal(0, len(sym.children))
    assert_equal('meaning-of-life', sym.attrs['name'])
    assert_equal(types.FunctionType(types.u8), sym.attrs['type'])
    assert_equal(bytes([0xa9, 0x42, 0x60]), sym.attrs['text'])
