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
from . import ast
from .. import blum
from .grammar import Parser
from .lexer import Lexer
from .passes import asm, binding, lower, resolve, typepasses


passes = [
    binding.ExplicitScopes,
    resolve.ResolveUnits,
    binding.ShadowNames,
    typepasses.ConstructTypes,
    binding.BindNamesToTypes,
    resolve.ResolveMembers,
    typepasses.PropagateTypes,
    binding.EvaluateConstants,
    binding.ResolveConstants,
    resolve.ResolveStorage,
    lower.LowerAssignment,
    lower.LowerFunctions,
    asm.AssembleWithRelocations,
    asm.FlattenSymbol,
]


def open_unit(unit):
    if str(unit) == "-":
        return sys.stdin
    return open(unit, 'r')


def parse(fileobj, name):
    lexer = Lexer(fileobj, name=name)
    tokens = antlr4.CommonTokenStream(lexer)
    parser = Parser(tokens)
    tree = parser.unit()
    if parser._syntaxErrors > 0:
        raise ast.ParseError("Unit {} had errors; terminating".format(name))
    builder = ast.AstBuilder()
    antlr4.ParseTreeWalker.DEFAULT.walk(builder, tree)
    return builder.ast


def translate(unit, verbose=False):
    with open_unit(unit) as input_file:
        obj = parse(input_file, name=unit.name)
        for p in passes:
            obj = obj.transform(p())
            if (verbose):
                print(p.__name__)
                print(obj.dumps())

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
