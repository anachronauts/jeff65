import sys
import pytest
from jeff65 import ast
from jeff65.blum import types
from jeff65.gold.passes import asm

sys.stderr = sys.stdout


def assemble(node):
    backup = node.pretty()
    result = node.transform(asm.AssembleWithRelocations())
    # check that the previous AST wasn't mutated
    assert node.pretty() == backup
    return result.attrs["bin"]


def flatten(unit):
    backup = unit.pretty()
    result = unit.transform(asm.FlattenSymbol())
    # check that the previous AST wasn't mutated
    assert unit.pretty() == backup
    return result


def test_assemble_rts():
    assert assemble(asm.rts(None)) == b"\x60"


def test_assemble_jmp_abs():
    assert (
        assemble(
            asm.jmp(
                ast.AstNode("absolute_storage", attrs={"address": 0xBEEF, "width": 0}),
                None,
            )
        )
        == b"\x4c\xef\xbe"
    )


def test_assemble_lda_imm():
    assert (
        assemble(
            asm.lda(
                ast.AstNode("immediate_storage", attrs={"value": 0x42, "width": 1}),
                None,
            )
        )
        == b"\xa9\x42"
    )


def test_assemble_lda_imm_too_wide():
    with pytest.raises(asm.AssemblyError):
        assemble(
            asm.lda(
                ast.AstNode("immediate_storage", attrs={"value": 0xCAFE, "width": 2}),
                None,
            )
        )


def test_assemble_sta_abs():
    assert (
        assemble(
            asm.sta(
                ast.AstNode("absolute_storage", attrs={"address": 0xBEEF, "width": 1}),
                None,
            )
        )
        == b"\x8d\xef\xbe"
    )


def test_assemble_sta_abs_too_wide():
    with pytest.raises(asm.AssemblyError):
        assemble(
            asm.sta(
                ast.AstNode("absolute_storage", attrs={"address": 0xBEEF, "width": 2}),
                None,
            )
        )


def test_flatten_symbol():
    assert flatten(
        ast.AstNode(
            "unit",
            {
                "toplevels": ast.AstNode.make_sequence(
                    "toplevel",
                    "stmt",
                    [
                        ast.AstNode(
                            "fun",
                            attrs={
                                "name": "meaning-of-life",
                                "type": types.FunctionType(types.u8),
                                "body": ast.AstNode.make_sequence(
                                    "block",
                                    "stmt",
                                    [
                                        ast.AstNode(
                                            "asmrun", attrs={"bin": b"\xa9\x42"}
                                        ),
                                        ast.AstNode("asmrun", attrs={"bin": b"\x60"}),
                                    ],
                                ),
                            },
                        )
                    ],
                )
            },
        )
    ) == ast.AstNode(
        "unit",
        {
            "toplevels": ast.AstNode.make_sequence(
                "toplevel",
                "stmt",
                [
                    ast.AstNode(
                        "fun_symbol",
                        attrs={
                            "name": "meaning-of-life",
                            "type": types.FunctionType(types.u8),
                            "text": b"\xa9\x42\x60",
                        },
                    )
                ],
            )
        },
    )
