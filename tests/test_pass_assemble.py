import sys
from nose.tools import (
    assert_equal,
    assert_false,
    assert_raises)
from jeff65.gold import asm, ast, storage, types

sys.stderr = sys.stdout


def assemble(node):
    backup = node.clone()
    result = node.transform(asm.AssembleWithRelocations())
    assert_equal(1, len(result))
    assert_equal(backup, node)  # check that the previous AST wasn't mutated
    return result[0]


def flatten(unit):
    backup = unit.clone()
    result = unit.transform(asm.FlattenSymbol())
    assert_equal(backup, unit)  # check that the previous AST wasn't mutated
    return result


def test_assemble_rts():
    a = asm.rts(None)
    assert_equal('rts', a.t)
    assert_equal(1, a.attrs['size'])
    b = assemble(a)
    assert_equal(bytes([0x60]), b.data)


def test_assemble_jmp_abs():
    a = asm.jmp(None, storage.AbsoluteStorage(0xbeef, 0))
    assert_equal('jmp', a.t)
    assert_equal(3, a.attrs['size'])
    b = assemble(a)
    assert_equal(bytes([0x4c, 0xef, 0xbe]), b.data)


def test_assemble_lda_imm():
    a = asm.lda(None, storage.ImmediateStorage(0x42, 1))
    assert_equal('lda', a.t)
    assert_equal(2, a.attrs['size'])
    b = assemble(a)
    assert_equal(bytes([0xa9, 0x42]), b.data)


def test_assemble_lda_imm_too_wide():
    a = asm.lda(None, storage.ImmediateStorage(0xcafe, 2))
    assert_raises(asm.AssemblyError, assemble, a)


def test_assemble_sta_abs():
    a = asm.sta(None, storage.AbsoluteStorage(0xbeef, 1))
    assert_equal('sta', a.t)
    assert_equal(3, a.attrs['size'])
    b = assemble(a)
    assert_equal(bytes([0x8d, 0xef, 0xbe]), b.data)


def test_assemble_sta_abs_too_wide():
    a = asm.sta(None, storage.AbsoluteStorage(0xbeef, 2))
    assert_raises(asm.AssemblyError, assemble, a)


def test_flatten_symbol():
    a = ast.AstNode('unit', None, attrs={
        'known_names': {},
    }, children=[
        ast.AstNode('fun', None, attrs={
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
    assert_false('return_addr' in sym.attrs)


def test_flatten_symbol_with_return_addr():
    a = ast.AstNode('unit', None, attrs={
        'known_names': {},
    }, children=[
        ast.AstNode('fun', None, attrs={
            'name': 'meaning-of-life',
            'type': types.FunctionType(types.u8),
            'return_addr': '.+3',
        }, children=[
            asm.AsmRun(bytes([0xa9, 0x42])),
            asm.AsmRun(bytes([0x4c, 0xff, 0xff])),
        ])
    ])
    b = flatten(a)
    assert_equal(1, len(b.children))
    sym = b.children[0]
    assert_equal(0, len(sym.children))
    assert_equal('meaning-of-life', sym.attrs['name'])
    assert_equal(types.FunctionType(types.u8), sym.attrs['type'])
    assert_equal(bytes([0xa9, 0x42, 0x4c, 0xff, 0xff]), sym.attrs['text'])
    assert_equal('.+3', sym.attrs['return_addr'])
