import sys
from nose.tools import (
    assert_equal,
    assert_raises)
from jeff65 import ast
from jeff65.blum import types
from jeff65.gold.passes import asm

sys.stderr = sys.stdout


def assemble(node):
    backup = node.pretty()
    result = node.transform(asm.AssembleWithRelocations())
    assert_equal(1, len(result))
    # check that the previous AST wasn't mutated
    assert_equal(backup, node.pretty())
    return result[0].attrs['bin']


def flatten(unit):
    backup = unit.pretty()
    result = unit.transform(asm.FlattenSymbol())
    # check that the previous AST wasn't mutated
    assert_equal(backup, unit.pretty())
    return result


def test_assemble_rts():
    assert_equal(b'\x60', assemble(asm.rts(None)))


def test_assemble_jmp_abs():
    assert_equal(b'\x4c\xef\xbe', assemble(
        asm.jmp(ast.AstNode('absolute_storage', attrs={
            'address': 0xbeef,
            'width': 0,
        }), None)
    ))


def test_assemble_lda_imm():
    assert_equal(b'\xa9\x42', assemble(
        asm.lda(ast.AstNode('immediate_storage', attrs={
            'value': 0x42,
            'width': 1,
        }), None)
    ))


def test_assemble_lda_imm_too_wide():
    assert_raises(
        asm.AssemblyError, assemble,
        asm.lda(ast.AstNode('immediate_storage', attrs={
            'value': 0xcafe,
            'width': 2,
        }), None)
    )


def test_assemble_sta_abs():
    assert_equal(b'\x8d\xef\xbe', assemble(
        asm.sta(ast.AstNode('absolute_storage', attrs={
            'address': 0xbeef,
            'width': 1,
        }), None)
    ))


def test_assemble_sta_abs_too_wide():
    assert_raises(
        asm.AssemblyError, assemble,
        asm.sta(ast.AstNode('absolute_storage', attrs={
            'address': 0xbeef,
            'width': 2,
        }), None)
    )


def test_flatten_symbol():
    assert_equal(
        ast.AstNode('unit', children=[
            ast.AstNode('fun_symbol', attrs={
                'name': 'meaning-of-life',
                'type': types.FunctionType(types.u8),
                'text': b'\xa9\x42\x60',
            })
        ]), flatten(ast.AstNode('unit', children=[
            ast.AstNode('fun', attrs={
                'name': 'meaning-of-life',
                'type': types.FunctionType(types.u8),
            }, children=[
                ast.AstNode('asmrun', attrs={'bin': b'\xa9\x42'}),
                ast.AstNode('asmrun', attrs={'bin': b'\x60'}),
            ])
        ]))
    )
