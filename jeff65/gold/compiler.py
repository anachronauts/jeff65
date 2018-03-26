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
    if unit == "-":
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
                print(obj.pretty())

    archive = blum.Archive()
    for node in obj.children:
        if node.t is 'fun_symbol':
            sym_name = '{}.{}'.format(unit.stem, node.attrs['name'])
            sym = blum.Symbol('text', node.attrs['text'], attrs={
                'type': node.attrs['type'],
            })
            archive.symbols[sym_name] = sym
            if 'return_addr' in node.attrs:
                const_name = '{}/return_addr'.format(sym_name)
                const_reloc = '{}+{}'.format(sym_name,
                                             node.attrs['return_addr'])
                const = blum.Constant(const_reloc, 2)
                archive.constants[const_name] = const

    return archive
