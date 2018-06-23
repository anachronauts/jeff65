# jeff65 gold-syntax compiler sequence
# Copyright (C) 2018  jeff65 maintainers
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import antlr4
from .lexer import Lexer
from .grammar import Parser
from . import asm, ast, binding, lower, storage, typepasses, units
from .. import blum


passes = [
    # binding.ExplicitScopes,
    units.ResolveUnits,
    binding.ShadowNames,
    typepasses.ConstructTypes,
    binding.BindNamesToTypes,
    units.ResolveMembers,
    typepasses.PropagateTypes,
    binding.EvaluateConstants,
    binding.ResolveConstants,
    storage.ResolveStorage,
    lower.LowerAssignment,
    lower.LowerFunctions,
    asm.AssembleWithRelocations,
    asm.FlattenSymbol,
]


def open_unit(unit):
    if str(unit) == "-":
        return sys.stdin
    return open(unit, 'r')


def _make_parser(fileobj, name):
    lexer = Lexer(fileobj, name=name)
    tokens = antlr4.CommonTokenStream(lexer)
    return Parser(tokens)


def parse(fileobj, name):
    parser = _make_parser(fileobj, name)
    tree = parser.unit()
    if parser._syntaxErrors > 0:
        raise ast.ParseError("Unit {} had errors; terminating".format(name))
    builder = ast.AstBuilder()
    return builder.walk(tree)


def parse_expr(fileobj, name):
    parser = _make_parser(fileobj, name)
    tree = parser.expr()
    if parser._syntaxErrors > 0:
        raise ast.ParseError("Expression had errors; terminating")
    builder = ast.AstBuilder()
    builder._push(ast.AstNode('<expr>', (0, 0)))
    return builder.walk(tree)


def parse_block(fileobj, name):
    parser = _make_parser(fileobj, name)
    tree = parser.block()
    if parser._syntaxErrors > 0:
        raise ast.ParseError("Block had errors; terminating")
    builder = ast.AstBuilder()
    builder._push(ast.AstNode('<block>', (0, 0)))
    return builder.walk(tree)


def translate(unit, verbose=False):
    with open_unit(unit) as input_file:
        obj = parse(input_file, name=unit.name)
        for p in passes:
            obj = obj.transform(p())
            if (verbose):
                print(p.__name__)
                print(obj.pretty())

    archive = blum.Archive()
    for node in obj.children:
        if node.t is 'fun_symbol':
            sym_name = '{}.{}'.format(unit.stem, node.attrs['name'])
            sym = blum.Symbol(
                section='text',
                data=node.attrs['text'],
                type_info=node.attrs['type'])
            archive.symbols[sym_name] = sym

    return archive
